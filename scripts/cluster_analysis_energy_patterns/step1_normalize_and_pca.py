"""Step 1: Normalize energy data and apply PCA (Wide Matrix Approach).

This script implements the PCA approach from the exploratory notebook:
1. Load energy cache and filter complete lifecycle cyclones
2. Aggregate by (cyclone, phase): mean of energy terms
3. Pivot to wide format: 1 row per cyclone, columns = term×phase (28 features)
4. Standardize (StandardScaler)
5. Apply PCA to capture patterns across all phases simultaneously

This approach captures correlations between phases and energy terms, providing
a more holistic view of cyclone energetics compared to phase-separated PCAs.

Prerequisites:
    - Energy cache file must exist (data/energy_cache.parquet)
    - If cache is missing or corrupted, run first:
      python scripts/analysis/preprocess_data.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import List
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pickle

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.preprocess_data.preprocess_data import load_cache, filter_complete_lifecycle_cyclones

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Cache file location.
#
# The corrected LEC climatology (scripts/lec_climatology_rerun, toolkit 2.0.0)
# is the only scientific truth for this article. The legacy
# data/energy_cache.parquet carries the superseded equations and is kept solely
# as the "before" side of scripts/lec_rerun_comparison — pointing this pipeline
# at it would silently reintroduce the corrected errors into every Energy
# Pattern, so it is no longer the default and is not an accepted fallback.
CACHE_FILE = Path(
    os.environ.get(
        "PAPER_ENERGY_CACHE",
        PROJECT_ROOT / "data" / "corrected" / "energy_cache_corrected.parquet",
    )
)

# Energy variables to use (7 terms, excluding Ce and RKe)
ENERGY_VARS = [
    'Ca', 'Ck',            # Conversion terms
    'BAe', 'BKe',          # Boundary terms
    'Ae', 'Ke',            # Energy reservoirs
    'Ge'                   # Generation term
]

# Phase configuration
PHASE_ORDER = ['incipient', 'intensification', 'mature', 'decay']
PHASE_ABBR = {
    'incipient': 'inc',
    'intensification': 'int',
    'mature': 'mat',
    'decay': 'dec'
}

# PCA settings
EXPLAINED_VARIANCE_THRESHOLD = 0.90  # Keep PCs explaining 90% variance
RANDOM_STATE = 42

# Output directories (absolute paths from PROJECT_ROOT)
RESULTS_DIR = PROJECT_ROOT / "results" / "cluster"
FIGURES_DIR = PROJECT_ROOT / "figures" / "cluster"
OUTPUT_PREFIX = "pca"

# ============================================================================


def load_and_prepare_data(energy_vars: List[str]) -> pd.DataFrame:
    """Load energy cache and prepare data.
    
    Returns:
        DataFrame with energy variables and metadata
    """
    print("=" * 70)
    print("Step 1.1: Loading and preparing data")
    print("=" * 70)
    
    # Load cache
    try:
        df = load_cache(CACHE_FILE)
    except (FileNotFoundError, OSError, Exception) as e:
        print(f"\n❌ Error loading energy cache: {e}")
        print("\n" + "=" * 70)
        print("⚠️  CACHE FILE MISSING OR CORRUPTED")
        print("=" * 70)
        print("\nThe energy cache file is required but could not be loaded.")
        print("\n📋 To fix this issue, run the preprocessing script:")
        print("\n   python scripts/analysis/preprocess_data.py")
        print("\nThis will generate the cache file at:")
        print(f"   {CACHE_FILE}")
        print("\nEstimated time: ~4-5 minutes with 50 parallel workers")
        print("=" * 70)
        raise SystemExit(1)
    
    print(f"✓ Loaded {len(df):,} records from {df['track_id'].nunique()} cyclones")
    
    # Filter to complete lifecycle cyclones only
    df = filter_complete_lifecycle_cyclones(df)
    
    # Check for missing energy variables
    missing_vars = [var for var in energy_vars if var not in df.columns]
    if missing_vars:
        raise ValueError(f"Missing variables in cache: {missing_vars}")
    
    # Select energy variables and convert to numeric
    for var in energy_vars:
        df[var] = pd.to_numeric(df[var], errors='coerce')
    
    # Remove rows with NaN in energy variables
    df_clean = df.dropna(subset=energy_vars)
    n_dropped = len(df) - len(df_clean)
    if n_dropped > 0:
        print(f"⚠️  Dropped {n_dropped:,} rows with NaN ({n_dropped/len(df)*100:.1f}%)")
    
    print(f"✓ Final dataset: {len(df_clean):,} records from {df_clean['track_id'].nunique()} cyclones")
    print()
    
    # Display phase distribution
    phase_counts = df_clean['phase'].value_counts()
    print("Phase distribution:")
    for phase in PHASE_ORDER:
        count = phase_counts.get(phase, 0)
        print(f"  {phase:20s}: {count:6,} records ({count/len(df_clean)*100:5.1f}%)")
    print()
    
    return df_clean


def aggregate_by_cyclone_phase(df: pd.DataFrame, energy_vars: List[str]) -> pd.DataFrame:
    """Aggregate energy terms by (cyclone, phase).
    
    Calculates mean of energy terms for each cyclone-phase combination.
    
    Args:
        df: DataFrame with raw data (multiple timesteps per cyclone-phase)
        energy_vars: List of energy variable names
        
    Returns:
        DataFrame with 1 row per (cyclone, phase)
    """
    print("=" * 70)
    print("Step 1.2: Aggregating by (cyclone, phase)")
    print("=" * 70)
    
    # Aggregate: mean of energy terms by (track_id, phase)
    agg = (
        df
        .groupby(['track_id', 'phase'])[energy_vars]
        .mean()
        .reset_index()
    )
    
    print(f"✓ Aggregated to {len(agg):,} rows")
    print(f"  Expected: {df['track_id'].nunique()} cyclones × 4 phases = {df['track_id'].nunique() * 4}")
    
    # Verify all cyclones have 4 phases
    phase_counts_per_cyclone = agg.groupby('track_id').size()
    if (phase_counts_per_cyclone == 4).all():
        print(f"✓ All {len(phase_counts_per_cyclone)} cyclones have exactly 4 phases")
    else:
        print(f"⚠️  Some cyclones don't have 4 phases!")
        print(phase_counts_per_cyclone.value_counts())
    
    print()
    return agg


def pivot_to_wide(agg: pd.DataFrame, energy_vars: List[str], 
                 phase_order: List[str], phase_abbr: dict) -> pd.DataFrame:
    """Pivot from long to wide format.
    
    Transforms:
        - Long: 1 row per (cyclone, phase) → n×4 rows
        - Wide: 1 row per cyclone → n rows, columns = term×phase
    
    Args:
        agg: Aggregated data in long format
        energy_vars: List of energy variables
        phase_order: Ordered list of phases
        phase_abbr: Dict mapping phase names to abbreviations
        
    Returns:
        Wide DataFrame (n cyclones × 28 features)
    """
    print("=" * 70)
    print("Step 1.3: Pivoting to wide format")
    print("=" * 70)
    
    # Pivot: transform phases into columns
    wide = agg.pivot(index='track_id', columns='phase', values=energy_vars)
    
    # Ensure consistent order: term × phase
    full_cols = pd.MultiIndex.from_product([energy_vars, phase_order])
    wide = wide.reindex(columns=full_cols)
    
    # Flatten column names: term_phase_abbr (e.g., Ae_inc, Ae_int, ...)
    wide.columns = [f"{var}_{phase_abbr[phase]}" for var, phase in wide.columns]
    
    # Order columns consistently
    ordered_cols = [f"{var}_{phase_abbr[phase]}" 
                   for var in energy_vars for phase in phase_order]
    wide = wide[ordered_cols]
    
    print(f"✓ Wide matrix created: {wide.shape[0]} cyclones × {wide.shape[1]} features")
    print(f"  Features: {len(energy_vars)} terms × {len(phase_order)} phases = {len(ordered_cols)}")
    
    # Check for NaNs
    n_nans = wide.isna().sum().sum()
    if n_nans > 0:
        print(f"\n⚠️  {n_nans} NaNs found in wide matrix")
        print("  Columns with NaNs:")
        nan_cols = wide.columns[wide.isna().any()]
        for col in nan_cols:
            n = wide[col].isna().sum()
            print(f"    {col}: {n} NaNs")
        
        # Remove cyclones with NaNs
        wide = wide.dropna()
        print(f"\n✓ Removed cyclones with NaNs. New shape: {wide.shape}")
    else:
        print(f"✓ No NaNs in wide matrix")
    
    print(f"\nColumn examples:")
    print(f"  First 4: {list(wide.columns[:4])}")
    print(f"  Last 4:  {list(wide.columns[-4:])}")
    print()
    
    return wide


def normalize_and_apply_pca(wide: pd.DataFrame, variance_threshold: float,
                            random_state: int) -> tuple:
    """Standardize data and apply PCA.
    
    Args:
        wide: Wide matrix (n × 28)
        variance_threshold: Cumulative variance threshold for component selection
        random_state: Random seed
        
    Returns:
        Tuple of (X_pca, pca_model, scaler, n_components_kept)
    """
    print("=" * 70)
    print("Step 1.4: Standardization and PCA")
    print("=" * 70)
    
    # Extract matrix and feature names
    X = wide.to_numpy(dtype=float)
    feature_names = wide.columns.tolist()
    
    print(f"Input matrix: {X.shape}")
    
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"✓ Standardization applied (mean≈0, std≈1)")
    print(f"  Sample verification (first 3 features):")
    for i in range(min(3, len(feature_names))):
        print(f"    {feature_names[i]:12s}: mean={X_scaled[:, i].mean():7.4f}, std={X_scaled[:, i].std():7.4f}")
    
    # Apply PCA (full)
    pca_full = PCA(random_state=random_state)
    pca_full.fit(X_scaled)
    
    explained_var = pca_full.explained_variance_ratio_
    cumsum_var = np.cumsum(explained_var)
    
    print(f"\n✓ PCA applied ({len(explained_var)} total components)")
    print(f"\nVariance explained by first 10 PCs:")
    for i in range(min(10, len(explained_var))):
        print(f"  PC{i+1:2d}: {explained_var[i]*100:5.2f}%  (cumulative: {cumsum_var[i]*100:5.2f}%)")
    
    # Determine number of components to keep
    n_keep = np.argmax(cumsum_var >= variance_threshold) + 1
    print(f"\n✓ For {variance_threshold*100:.0f}% variance: keeping {n_keep} components")
    print(f"  Cumulative variance: {cumsum_var[n_keep-1]*100:.2f}%")
    
    # Re-apply PCA with selected number of components
    pca = PCA(n_components=n_keep, random_state=random_state)
    X_pca = pca.fit_transform(X_scaled)
    
    print(f"\n✓ Final PCA:")
    print(f"  Input:  {X_scaled.shape}")
    print(f"  Output: {X_pca.shape}")
    print(f"  Dimensionality reduction: {X_scaled.shape[1]} → {X_pca.shape[1]} ({X_pca.shape[1]/X_scaled.shape[1]*100:.1f}%)")
    print()
    
    return X_pca, pca, scaler, n_keep


def save_results(wide: pd.DataFrame, X_pca: np.ndarray, pca: PCA, 
                scaler: StandardScaler, energy_vars: List[str],
                results_dir: Path, prefix: str):
    """Save PCA results.
    
    Args:
        wide: Wide matrix (original values)
        X_pca: PCA scores
        pca: PCA model
        scaler: StandardScaler model
        energy_vars: List of energy variables
        results_dir: Output directory
        prefix: File prefix
    """
    print("=" * 70)
    print("Step 1.5: Saving results")
    print("=" * 70)
    
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. PCA scores (main output for clustering)
    pc_columns = [f'PC{i+1}' for i in range(X_pca.shape[1])]
    df_pca = pd.DataFrame(
        X_pca,
        index=wide.index,  # track_id as index
        columns=pc_columns
    )
    
    scores_file = results_dir / f"{prefix}_scores.csv"
    df_pca.to_csv(scores_file, index=True)
    print(f"✓ PCA scores: {scores_file.name}")
    print(f"  Shape: {df_pca.shape}")
    
    # 2. Full data (original + scaled + PCs) - optional
    df_full = wide.copy()
    for col in pc_columns:
        df_full[col] = df_pca[col]
    
    full_file = results_dir / f"{prefix}_full_data.csv"
    df_full.to_csv(full_file, index=True)
    print(f"✓ Full data (original + PCs): {full_file.name}")
    
    # 3. PCA models (for inverse transform and reproducibility)
    models_file = results_dir / f"{prefix}_models.pkl"
    with open(models_file, 'wb') as f:
        pickle.dump({
            'pca': pca,
            'scaler': scaler,
            'energy_vars': energy_vars,
            'feature_names': wide.columns.tolist(),
            'n_components': pca.n_components_,
            'explained_variance_ratio': pca.explained_variance_ratio_,
            'random_state': pca.random_state
        }, f)
    print(f"✓ PCA models: {models_file.name}")
    
    # 4. Loadings (feature contributions to each PC)
    loadings_df = pd.DataFrame(
        pca.components_,
        columns=wide.columns,
        index=pc_columns
    )
    
    loadings_file = results_dir / f"{prefix}_loadings.csv"
    loadings_df.to_csv(loadings_file, index=True)
    print(f"✓ Loadings: {loadings_file.name}")
    print(f"  Shape: {loadings_df.shape} ({len(pc_columns)} PCs × {len(wide.columns)} features)")
    
    # 5. Explained variance
    variance_df = pd.DataFrame({
        'PC': pc_columns,
        'explained_variance': pca.explained_variance_,
        'explained_variance_ratio': pca.explained_variance_ratio_,
        'cumulative_variance_ratio': np.cumsum(pca.explained_variance_ratio_)
    })
    
    variance_file = results_dir / f"{prefix}_explained_variance.csv"
    variance_df.to_csv(variance_file, index=False)
    print(f"✓ Explained variance: {variance_file.name}")
    
    print()


def main():
    """Main execution function."""
    print("=" * 70)
    print("STEP 1: Normalize and Apply PCA (Wide Matrix Approach)")
    print("=" * 70)
    print(f"Energy variables: {ENERGY_VARS}")
    print(f"Number of terms: {len(ENERGY_VARS)}")
    print(f"Number of phases: {len(PHASE_ORDER)}")
    print(f"Total features: {len(ENERGY_VARS)} × {len(PHASE_ORDER)} = {len(ENERGY_VARS) * len(PHASE_ORDER)}")
    print(f"Variance threshold: {EXPLAINED_VARIANCE_THRESHOLD*100:.0f}%")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Figures directory: {FIGURES_DIR}")
    print()
    
    # Load and prepare data
    df_clean = load_and_prepare_data(ENERGY_VARS)
    
    # Aggregate by (cyclone, phase)
    agg = aggregate_by_cyclone_phase(df_clean, ENERGY_VARS)
    
    # Pivot to wide format
    wide = pivot_to_wide(agg, ENERGY_VARS, PHASE_ORDER, PHASE_ABBR)
    
    # Normalize and apply PCA
    X_pca, pca, scaler, n_components = normalize_and_apply_pca(
        wide, EXPLAINED_VARIANCE_THRESHOLD, RANDOM_STATE
    )
    
    # Save results
    save_results(wide, X_pca, pca, scaler, ENERGY_VARS, RESULTS_DIR, OUTPUT_PREFIX)
    
    print("=" * 70)
    print("✅ Step 1 complete!")
    print("=" * 70)
    print(f"Processed {len(wide)} cyclones")
    print(f"Reduced {len(wide.columns)} features → {n_components} PCs")
    print(f"Explained variance: {np.cumsum(pca.explained_variance_ratio_)[n_components-1]*100:.2f}%")
    print()
    print("Next step:")
    print("  2. Run step2_plot_pca_results.py to visualize PCA results")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
