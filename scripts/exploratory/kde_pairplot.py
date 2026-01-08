"""KDE pairwise plot for selected energy terms.

This script samples cyclone energy summaries and produces a scatterplot
matrix-style figure using contour KDEs per life-cycle phase.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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

# Output directories
TYPE = 'exploratory'
RESULTS_DIR = f"results/{TYPE}"  # Change to "results/main" to promote to main analysis
FIGURES_DIR = f"figures/{TYPE}"  # Change to "figures/main" to promote to main analysis

# Figure settings
DPI = 150  # DPI for saved figure (increase to 300+ for publication quality)
SAVE_FIGURE = True  # Set to False to just preview

# Energy variables to analyze
ENERGY_VARS = ["Ca", "Ck", "BAe", "BKe", "Ge", "RKe"]

# Phase colors (Scientific Reports style)
PHASE_COLORS = {
    "incipient": "#1f77b4",        # blue
    "intensification": "#ffbf00",  # yellow/gold
    "mature": "#d62728",           # red
    "decay": "#2ca02c",            # green
}

# ============================================================================


def gather_energy_sample(sample_n: int = 0) -> pd.DataFrame:
    """Load energy data from cache and optionally sample.

    Args:
        sample_n: Number of cyclones to sample (0 = all available)
        
    Returns:
        DataFrame with energy data filtered to main phases
    """
    print("Loading energy data from cache...")
    try:
        df = load_cache()
    except (FileNotFoundError, OSError, Exception) as e:
        print(f"\n❌ Error loading cache: {e}")
        print("\n⚠️  Cache file missing or corrupted!")
        print("Run: python scripts/analysis/preprocess_data.py")
        raise SystemExit(1)
    
    # Filter to main four phases only (exclude residual and other)
    df = df[df['phase'].isin(['incipient', 'intensification', 'mature', 'decay'])]
    
    # Sample cyclones if requested
    if sample_n > 0:
        track_ids = df['track_id'].unique()
        from random import Random
        rng = Random(42)
        sampled_ids = rng.sample(list(track_ids), min(sample_n, len(track_ids)))
        df = df[df['track_id'].isin(sampled_ids)]
        print(f"✓ Sampled {len(sampled_ids)} cyclones")
    
    print(f"✓ Loaded {len(df)} phase records from {df['track_id'].nunique()} cyclones")
    
    return df


def plot_pair_kde(df: pd.DataFrame, vars_list: List[str], out_path: Path, 
                  dpi: int = 200, phase_colors: dict = None):
    """Create and save a PairGrid of contour KDEs for each phase.
    
    Args:
        df: DataFrame with energy variables and 'phase' column
        vars_list: List of variable names to plot
        out_path: Path to save the figure
        dpi: DPI for the figure
        phase_colors: Dictionary mapping phase names to colors
    """
    if phase_colors is None:
        phase_colors = PHASE_COLORS

    sns.set_style("whitegrid")
    # Scientific Reports-ish defaults: compact, legible
    sns.set_context("paper", rc={"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9})

    nvars = len(vars_list)
    
    # Create PairGrid without hue first
    grid = sns.PairGrid(df, vars=vars_list, height=2.5, aspect=1, corner=False)

    # Diagonal: plot KDE for each phase
    def diag_plot(x, **kwargs):
        ax = plt.gca()
        for phase, color in phase_colors.items():
            subset = df[df["phase"] == phase][x.name]
            subset = subset.dropna()
            if len(subset) > 1:
                sns.kdeplot(data=subset, color=color, fill=True, alpha=0.3, linewidth=1.5, ax=ax)

    # Off-diagonal: contour KDE overlays for each phase
    def offdiag_plot(x, y, **kwargs):
        ax = plt.gca()
        for phase, color in phase_colors.items():
            subset = df[df["phase"] == phase][[x.name, y.name]].dropna()
            if len(subset) > 5:  # Need at least a few points for KDE
                try:
                    sns.kdeplot(
                        data=subset, x=x.name, y=y.name,
                        color=color, levels=5, linewidths=1.5, 
                        fill=False, alpha=0.8, ax=ax
                    )
                    # Add black lines on 0
                    ax.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.7)
                    ax.axvline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.7)
                except Exception:
                    # If KDE fails, skip this phase for this pair
                    pass

    # Map the functions
    grid.map_diag(diag_plot)
    grid.map_offdiag(offdiag_plot)

    # Add legend
    handles = [plt.Line2D([0], [0], color=c, lw=2, label=k.title()) 
               for k, c in phase_colors.items()]
    grid.fig.legend(handles=handles, bbox_to_anchor=(0.98, 0.98), 
                    loc="upper right", frameon=True, fontsize=10)

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    grid.fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(grid.fig)


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)

    print("=" * 70)
    print("KDE Pairwise Plot")
    print("=" * 70)
    print(f"Sample size: {SAMPLE_SIZE if SAMPLE_SIZE > 0 else 'ALL'}")
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"DPI: {DPI}")
    print("=" * 70)
    print()

    df = gather_energy_sample(SAMPLE_SIZE)
    
    if df.empty:
        print("❌ No energy data collected. Aborting.")
        return 1

    print()
    
    # Display phase distribution
    phase_counts = df['phase'].value_counts()
    print("Phase distribution:")
    for phase, count in phase_counts.items():
        print(f"  {phase:20s}: {count:6d} records")
    print()

    # Save sample for reproducibility
    results_dir.mkdir(parents=True, exist_ok=True)
    sample_csv = results_dir / "energy_sample.csv"
    df.to_csv(sample_csv, index=False)
    print(f"✓ Saved sample summary to {sample_csv}")
    print()

    if SAVE_FIGURE:
        out_file = figures_dir / "kde_pairplot.png"
        figures_dir.mkdir(parents=True, exist_ok=True)

        print("Creating pairwise KDE figure (this may take a bit)...")
        plot_pair_kde(df, ENERGY_VARS, out_file, dpi=DPI, phase_colors=PHASE_COLORS)
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