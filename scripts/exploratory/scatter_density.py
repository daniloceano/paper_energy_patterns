"""Scatter plots with density for key energy term relationships.

This script creates scatter plots with density contours for three key
energy term pairs: Ca×Ck, BAe×BKe, and Ge×Ke, separated by life-cycle phase.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

# Ensure project root is importable when running from subfolders
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analysis.preprocess_data import load_cache

# ============================================================================
# CONFIGURATION - Edit these variables to customize the analysis
# ============================================================================

# Sampling
SAMPLE_SIZE = 0  # Number of cyclones to sample (0 = all available)
USE_CACHE = True  # Use preprocessed cache (MUCH faster!)

# Output directories
TYPE = 'exploratory'
RESULTS_DIR = f"results/{TYPE}"
FIGURES_DIR = f"figures/{TYPE}"

# Figure settings
DPI = 150  # DPI for saved figure (increase to 300+ for publication quality)
SAVE_FIGURE = True  # Set to False to just preview

# Variable pairs to analyze
VARIABLE_PAIRS = [
    ("Ca", "Ck"),
    ("BAe", "BKe"),
    ("Ge", "Ke")
]

# Phase colors (Scientific Reports style)
PHASE_COLORS = {
    "incipient": "#1f77b4",        # blue
    "intensification": "#ffbf00",  # yellow/gold
    "mature": "#d62728",           # red
    "decay": "#2ca02c",            # green
}

# ============================================================================


def gather_energy_sample(sample_n: int, use_cache: bool = True) -> pd.DataFrame:
    """Load energy summaries for a sample of cyclones.

    The returned DataFrame contains one row per (track_id, period) with the
    requested energy variables as columns.
    
    Args:
        sample_n: Number of cyclones to sample (0 = all available)
        use_cache: Whether to use preprocessed cache (much faster!)
        
    Returns:
        DataFrame filtered to main phases (incipient, intensification, mature, decay)
    """
    if use_cache:
        print("Loading from preprocessed cache...")
        try:
            df = load_cache()
            print(f"✓ Loaded {len(df)} records from {df['track_id'].nunique()} cyclones")
        except (FileNotFoundError, OSError, Exception) as e:
            print(f"\n❌ Error loading cache: {e}")
            print("\n⚠️  Cache file missing or corrupted!")
            print("Run: python scripts/analysis/preprocess_data.py")
            raise SystemExit(1)
    else:
        # Fallback to direct loading (slow!)
        print("⚠️  Loading directly from GitHub (slow - consider using cache)")
        from scripts.utils.load_data import load_tracks, load_energy_by_cyclone
        from random import Random
        from tqdm import tqdm
        
        tracks = load_tracks()
        track_ids = tracks["track_id"].unique().tolist()
        
        # Shuffle for random sampling
        rng = Random(42)
        rng.shuffle(track_ids)
        
        if sample_n > 0:
            track_ids = track_ids[:sample_n]
        
        all_rows = []
        for tid in tqdm(track_ids, desc="Loading energy"):
            energy_df = load_energy_by_cyclone(str(tid))
            if energy_df is not None and not energy_df.empty:
                energy_df['track_id'] = tid
                all_rows.append(energy_df)
        
        if not all_rows:
            return pd.DataFrame()
            
        df = pd.concat(all_rows, ignore_index=True)
        
        # Add phase column
        def classify_phase(period):
            period = str(period).strip().lower()
            if period.startswith('incipient'):
                return 'incipient'
            elif period.startswith('intensification'):
                return 'intensification'
            elif period.startswith('mature'):
                return 'mature'
            elif period.startswith('decay'):
                return 'decay'
            else:
                return 'other'
        
        df['phase'] = df['period'].apply(classify_phase)
    
    # Filter to main phases only
    df = df[df['phase'].isin(['incipient', 'intensification', 'mature', 'decay'])].copy()
    
    # Sample if requested
    if sample_n > 0:
        unique_ids = df['track_id'].unique()
        if len(unique_ids) > sample_n:
            from random import Random
            rng = Random(42)
            sampled_ids = rng.sample(list(unique_ids), sample_n)
            df = df[df['track_id'].isin(sampled_ids)].copy()
            print(f"✓ Sampled {sample_n} cyclones")
    
    # Ensure numeric columns
    numeric_cols = []
    for var_x, var_y in VARIABLE_PAIRS:
        numeric_cols.extend([var_x, var_y])
    
    for col in set(numeric_cols):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def plot_scatter_density(df: pd.DataFrame, var_pairs: List[tuple], out_path: Path, 
                         dpi: int = 150, phase_colors: dict = None):
    """Create scatter plots with density contours for multiple variable pairs.
    
    Creates a jointplot-style figure with scatter + density in the center and
    histograms on the margins for each variable pair and phase.
    
    Args:
        df: DataFrame with energy variables and 'phase' column
        var_pairs: List of (x_var, y_var) tuples
        out_path: Path to save the figure
        dpi: DPI for the figure
        phase_colors: Dictionary mapping phase names to colors
    """
    if phase_colors is None:
        phase_colors = PHASE_COLORS

    sns.set_style("whitegrid")
    sns.set_context("paper", rc={"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10})

    # Create figure with subplots: 4 rows (phases) x 3 columns (variable pairs)
    n_pairs = len(var_pairs)
    phases = list(phase_colors.keys())
    
    fig = plt.figure(figsize=(6 * n_pairs, 5 * len(phases)), dpi=dpi)
    
    # Create grid for each subplot (jointplot style)
    gs_main = fig.add_gridspec(len(phases), n_pairs, hspace=0.3, wspace=0.3)
    
    # Plot each phase in a row, each variable pair in a column
    for i, phase in enumerate(phases):
        phase_data = df[df["phase"] == phase]
        color = phase_colors[phase]
        
        for j, (var_x, var_y) in enumerate(var_pairs):
            # Create sub-grid for jointplot style (marginal histograms)
            gs_sub = gs_main[i, j].subgridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                                               hspace=0.02, wspace=0.02)
            
            ax_main = fig.add_subplot(gs_sub[1, 0])
            ax_top = fig.add_subplot(gs_sub[0, 0], sharex=ax_main)
            ax_right = fig.add_subplot(gs_sub[1, 1], sharey=ax_main)
            
            # Filter valid data
            valid_data = phase_data[[var_x, var_y]].dropna()
            
            if len(valid_data) > 5:
                # Calculate density for each point using KDE
                from scipy.stats import gaussian_kde
                
                try:
                    # Prepare data for KDE
                    x = valid_data[var_x].values
                    y = valid_data[var_y].values
                    xy = np.vstack([x, y])
                    
                    # Calculate KDE
                    kde = gaussian_kde(xy)
                    density = kde(xy)
                    
                    # Normalize density to [0, 1] for better color mapping
                    density_norm = (density - density.min()) / (density.max() - density.min())
                    
                    # Create colormap based on phase color
                    from matplotlib.colors import LinearSegmentedColormap
                    
                    # Convert hex color to RGB
                    import matplotlib.colors as mcolors
                    rgb = mcolors.hex2color(color)
                    
                    # Create colormap: white (low density) -> phase color (high density)
                    colors = [(1, 1, 1), rgb]
                    n_bins = 100
                    cmap = LinearSegmentedColormap.from_list(f'{phase}_density', colors, N=n_bins)
                    
                    # Scatter plot with density-based coloring
                    scatter = ax_main.scatter(x, y, c=density_norm, cmap=cmap, 
                                            s=20, alpha=0.6, edgecolors='none', 
                                            vmin=0, vmax=1)
                    
                    # Add contour lines for reference
                    sns.kdeplot(data=valid_data, x=var_x, y=var_y, 
                               levels=5, color=color, fill=False, linewidths=1.5, 
                               alpha=0.8, ax=ax_main)
                    
                except Exception as e:
                    # Fallback to simple scatter if KDE fails
                    ax_main.scatter(valid_data[var_x], valid_data[var_y], 
                                  color=color, s=20, alpha=0.4, edgecolors='none')
                
                # Top histogram (x variable)
                ax_top.hist(valid_data[var_x], bins=30, color=color, alpha=0.6, edgecolor='none')
                ax_top.set_ylabel('')
                ax_top.tick_params(labelbottom=False, labelleft=False)
                ax_top.spines['top'].set_visible(False)
                ax_top.spines['right'].set_visible(False)
                ax_top.spines['left'].set_visible(False)
                ax_top.set_yticks([])
                
                # Right histogram (y variable)
                ax_right.hist(valid_data[var_y], bins=30, color=color, alpha=0.6, 
                             edgecolor='none', orientation='horizontal')
                ax_right.set_xlabel('')
                ax_right.tick_params(labelbottom=False, labelleft=False)
                ax_right.spines['top'].set_visible(False)
                ax_right.spines['right'].set_visible(False)
                ax_right.spines['bottom'].set_visible(False)
                ax_right.set_xticks([])
            
            # Add reference lines at zero
            ax_main.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=10)
            ax_main.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=10)
            
            # Labels
            ax_main.set_xlabel(var_x, fontsize=11, fontweight='bold')
            ax_main.set_ylabel(var_y, fontsize=11, fontweight='bold')
            
            # Title with phase name
            title_text = f"{var_x} × {var_y}\n{phase.title()}"
            ax_top.set_title(title_text, fontsize=12, fontweight='bold', color=color, pad=10)
            
            # Grid on main plot
            ax_main.grid(True, alpha=0.3, zorder=0)
            ax_main.set_axisbelow(True)
    
    # Don't use tight_layout with complex gridspec
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)

    print("=" * 70)
    print("Scatter + Density Analysis")
    print("=" * 70)
    print(f"Sample size: {SAMPLE_SIZE if SAMPLE_SIZE > 0 else 'ALL'}")
    print(f"Use cache: {USE_CACHE}")
    print(f"Variable pairs: {', '.join([f'{x}×{y}' for x, y in VARIABLE_PAIRS])}")
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"DPI: {DPI}")
    print("=" * 70)
    print()

    print("Gathering energy data...")
    df = gather_energy_sample(SAMPLE_SIZE, use_cache=USE_CACHE)
    
    if df.empty:
        print("❌ No energy data collected. Aborting.")
        return 1

    print(f"✓ Collected {len(df)} phase records from {df['track_id'].nunique()} cyclones")
    print()
    
    # Display phase distribution
    phase_counts = df['phase'].value_counts()
    print("Phase distribution:")
    for phase, count in phase_counts.items():
        print(f"  {phase:20s}: {count:6d} records")
    print()

    # Save sample for reproducibility
    results_dir.mkdir(parents=True, exist_ok=True)
    sample_csv = results_dir / "scatter_density_sample.csv"
    df.to_csv(sample_csv, index=False)
    print(f"✓ Saved sample summary to {sample_csv}")
    print()

    if SAVE_FIGURE:
        out_file = figures_dir / "scatter_density.png"
        figures_dir.mkdir(parents=True, exist_ok=True)

        print("Creating scatter + density figure...")
        plot_scatter_density(df, VARIABLE_PAIRS, out_file, dpi=DPI, phase_colors=PHASE_COLORS)
        print(f"✓ Figure written to: {out_file}")
    else:
        print("⚠️  SAVE_FIGURE is False, skipping figure generation")

    print()
    print("=" * 70)
    print("✅ Done!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
