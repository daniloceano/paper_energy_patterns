"""Step 1: Normalize energy data and apply PCA.

This script loads the preprocessed energy cache, normalizes the energy variables,
applies Principal Component Analysis (PCA), and saves the transformed data for
subsequent clustering analysis.
"""

from __future__ import annotations

import sys
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

from scripts.utils.preprocess_data import load_cache, filter_complete_lifecycle_cyclones

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Energy variables to use for clustering (excluding Ce and RKe)
ENERGY_VARS = [
    'Ca', 'Ck',            # Conversion terms
    'BAe', 'BKe',          # Boundary terms
    'Ae', 'Ke',            # Energy reservoirs
    'Ge'                   # Generation term
]

# PCA settings
N_COMPONENTS = None  # None = keep all components, or specify a number (e.g., 5)
EXPLAINED_VARIANCE_THRESHOLD = 0.95  # Keep components explaining 95% variance
DO_PCA_BY_PHASE = True  # Perform separate PCA for each phase

# Output directories
RESULTS_DIR = "results/cluster"
OUTPUT_PREFIX = "pca"  # Prefix for output files

# ============================================================================


def load_and_prepare_data(energy_vars: List[str]) -> pd.DataFrame:
    """Load energy cache and prepare data for PCA.
    
    Only includes cyclones with complete lifecycle (all 4 phases in order).
    
    Args:
        energy_vars: List of energy variable names to use
        
    Returns:
        DataFrame with energy variables and metadata
    """
    print("=" * 70)
    print("Loading and preparing data")
    print("=" * 70)
    
    # Load cache
    df = load_cache()
    print(f"✓ Loaded {len(df)} records from {df['track_id'].nunique()} cyclones")
    
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
        print(f"⚠️  Dropped {n_dropped} rows with missing values ({n_dropped/len(df)*100:.1f}%)")
    
    print(f"✓ Final dataset: {len(df_clean)} records from {df_clean['track_id'].nunique()} cyclones")
    print()
    
    # Display phase distribution
    phase_counts = df_clean['phase'].value_counts()
    print("Phase distribution:")
    for phase in ['incipient', 'intensification', 'mature', 'decay']:
        count = phase_counts.get(phase, 0)
        print(f"  {phase:20s}: {count:6d} records ({count/len(df_clean)*100:5.1f}%)")
    print()
    
    return df_clean


def normalize_and_pca(df: pd.DataFrame, energy_vars: List[str], 
                     n_components: int | None = None,
                     variance_threshold: float = 0.95,
                     by_phase: bool = True) -> dict:
    """Normalize data and apply PCA.
    
    Args:
        df: DataFrame with energy variables
        energy_vars: List of variable names to use
        n_components: Number of components to keep (None = all)
        variance_threshold: Keep components explaining this fraction of variance
        by_phase: If True, perform separate PCA for each phase
        
    Returns:
        Dictionary with results for each phase (if by_phase=True) or single result
    """
    print("=" * 70)
    print("Normalizing data and applying PCA")
    print("=" * 70)
    
    if by_phase:
        print("Mode: SEPARATE PCA FOR EACH PHASE")
        print()
        
        phases = ['incipient', 'intensification', 'mature', 'decay']
        results = {}
        
        for phase in phases:
            print(f"--- Processing phase: {phase.upper()} ---")
            
            # Filter to current phase
            df_phase = df[df['phase'] == phase].copy()
            print(f"Phase data: {len(df_phase)} samples")
            
            # Extract energy variables
            X = df_phase[energy_vars].values
            print(f"Input shape: {X.shape[0]} samples × {X.shape[1]} variables")
            
            # Standardize
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            print(f"✓ Data standardized (mean≈0, std≈1)")
            
            # Apply PCA
            if n_components is None:
                pca = PCA()
                pca.fit(X_scaled)
                
                # Determine number of components
                cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
                n_keep = np.argmax(cumsum_variance >= variance_threshold) + 1
                print(f"✓ Keeping {n_keep} components (explaining {cumsum_variance[n_keep-1]*100:.1f}% variance)")
                
                # Refit with selected components
                pca = PCA(n_components=n_keep)
                X_pca = pca.fit_transform(X_scaled)
            else:
                pca = PCA(n_components=n_components)
                X_pca = pca.fit_transform(X_scaled)
                cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
                print(f"✓ Using {n_components} components (explaining {cumsum_variance[-1]*100:.1f}% variance)")
            
            # Create DataFrame with PC scores
            pc_columns = [f'PC{i+1}' for i in range(X_pca.shape[1])]
            df_pca = pd.DataFrame(X_pca, columns=pc_columns, index=df_phase.index)
            
            # Add metadata (including track_id)
            metadata_cols = ['track_id', 'period', 'phase', 'vorticity_max']
            for col in metadata_cols:
                if col in df_phase.columns:
                    df_pca[col] = df_phase[col].values
            
            # Create full DataFrame
            df_full = df_phase.copy()
            for i, var in enumerate(energy_vars):
                df_full[f'{var}_scaled'] = X_scaled[:, i]
            for col in pc_columns:
                df_full[col] = df_pca[col].values
            
            # Store results
            results[phase] = {
                'df_pca': df_pca,
                'pca': pca,
                'scaler': scaler,
                'df_full': df_full,
                'pc_columns': pc_columns
            }
            
            print(f"✓ Phase {phase} complete: {len(pc_columns)} PCs")
            print()
        
        print("=" * 70)
        print("✅ PCA complete for all phases")
        print("=" * 70)
        print()
        
        return results
    
    else:
        # Single PCA for all data
        print("Mode: SINGLE PCA FOR ALL DATA")
        print()
        
        X = df[energy_vars].values
        print(f"Input shape: {X.shape[0]} samples × {X.shape[1]} variables")
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        if n_components is None:
            pca = PCA()
            pca.fit(X_scaled)
            cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
            n_keep = np.argmax(cumsum_variance >= variance_threshold) + 1
            
            pca = PCA(n_components=n_keep)
            X_pca = pca.fit_transform(X_scaled)
        else:
            pca = PCA(n_components=n_components)
            X_pca = pca.fit_transform(X_scaled)
        
        pc_columns = [f'PC{i+1}' for i in range(X_pca.shape[1])]
        df_pca = pd.DataFrame(X_pca, columns=pc_columns, index=df.index)
        
        metadata_cols = ['track_id', 'period', 'phase', 'vorticity_max']
        for col in metadata_cols:
            if col in df.columns:
                df_pca[col] = df[col].values
        
        df_full = df.copy()
        for i, var in enumerate(energy_vars):
            df_full[f'{var}_scaled'] = X_scaled[:, i]
        for col in pc_columns:
            df_full[col] = df_pca[col].values
        
        return {
            'all': {
                'df_pca': df_pca,
                'pca': pca,
                'scaler': scaler,
                'df_full': df_full,
                'pc_columns': pc_columns
            }
        }


def save_results(results: dict, energy_vars: List[str],
                output_dir: Path, prefix: str):
    """Save PCA results to files.
    
    Args:
        results: Dictionary with PCA results (by phase or single 'all' key)
        energy_vars: List of energy variable names
        output_dir: Output directory
        prefix: Prefix for output files
    """
    print("=" * 70)
    print("Saving results")
    print("=" * 70)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for phase_name, phase_results in results.items():
        df_pca = phase_results['df_pca']
        pca = phase_results['pca']
        scaler = phase_results['scaler']
        df_full = phase_results['df_full']
        pc_columns = phase_results['pc_columns']
        
        phase_suffix = f"_{phase_name}" if phase_name != 'all' else ""
        
        # Save PC scores (for clustering) - INCLUDES track_id
        pca_scores_file = output_dir / f"{prefix}_scores{phase_suffix}.csv"
        df_pca.to_csv(pca_scores_file, index=False)
        print(f"✓ PC scores ({phase_name}) saved to: {pca_scores_file}")
        
        # Save full data (for reference) - INCLUDES track_id
        full_data_file = output_dir / f"{prefix}_full_data{phase_suffix}.csv"
        df_full.to_csv(full_data_file, index=False)
        print(f"✓ Full data ({phase_name}) saved to: {full_data_file}")
        
        # Save PCA model and scaler (for reproducibility)
        models_file = output_dir / f"{prefix}_models{phase_suffix}.pkl"
        with open(models_file, 'wb') as f:
            pickle.dump({'pca': pca, 'scaler': scaler, 'energy_vars': energy_vars}, f)
        print(f"✓ Models ({phase_name}) saved to: {models_file}")
        
        # Save component loadings
        loadings = pd.DataFrame(
            pca.components_.T,
            columns=pc_columns,
            index=energy_vars
        )
        loadings_file = output_dir / f"{prefix}_loadings{phase_suffix}.csv"
        loadings.to_csv(loadings_file)
        print(f"✓ Component loadings ({phase_name}) saved to: {loadings_file}")
        
        # Save explained variance
        variance_df = pd.DataFrame({
            'PC': pc_columns,
            'Explained_Variance': pca.explained_variance_,
            'Explained_Variance_Ratio': pca.explained_variance_ratio_,
            'Cumulative_Variance_Ratio': np.cumsum(pca.explained_variance_ratio_)
        })
        variance_file = output_dir / f"{prefix}_explained_variance{phase_suffix}.csv"
        variance_df.to_csv(variance_file, index=False)
        print(f"✓ Explained variance ({phase_name}) saved to: {variance_file}")
        print()
    
    print("=" * 70)
    print("✅ Step 1 complete!")
    print("=" * 70)
    print()
    print("Files saved:")
    for phase_name in results.keys():
        phase_suffix = f"_{phase_name}" if phase_name != 'all' else ""
        print(f"  Phase: {phase_name}")
        print(f"    - pca_scores{phase_suffix}.csv (includes track_id)")
        print(f"    - pca_full_data{phase_suffix}.csv (includes track_id)")
        print(f"    - pca_models{phase_suffix}.pkl")
        print(f"    - pca_loadings{phase_suffix}.csv")
        print(f"    - pca_explained_variance{phase_suffix}.csv")
    print()
    print("Next steps:")
    print("  2. Run step2_plot_pca_results.py to visualize PCA results")
    print("  3. Run step3_optimal_k_analysis.py to determine optimal k")
    print()


def main():
    """Main execution function."""
    # Load and prepare data
    df = load_and_prepare_data(ENERGY_VARS)
    
    # Normalize and apply PCA
    results = normalize_and_pca(
        df, ENERGY_VARS, 
        n_components=N_COMPONENTS,
        variance_threshold=EXPLAINED_VARIANCE_THRESHOLD,
        by_phase=DO_PCA_BY_PHASE
    )
    
    # Save results
    output_dir = Path(RESULTS_DIR)
    save_results(results, ENERGY_VARS, output_dir, OUTPUT_PREFIX)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
