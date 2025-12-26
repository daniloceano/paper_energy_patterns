"""Step 2: Visualize PCA results.

This script creates comprehensive visualizations of PCA results including:
- Scatter plots of principal components (PC1 vs PC2, PC1 vs PC3, PC2 vs PC3)
- Explained variance plot
- Component loadings heatmap

The layout is similar to the reference figure from ResearchGate.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files (from step 1)
RESULTS_DIR = "results/cluster"
INPUT_PREFIX = "pca"

# Phases to plot (will look for files like pca_scores_incipient.csv)
PHASES = ['incipient', 'intensification', 'mature', 'decay']

# Output settings
FIGURES_DIR = "figures/cluster"
# Three separate figures per phase
OUTPUT_SCATTER_PATTERN = "pca_scatter_{phase}.png"      # PC scatter plots
OUTPUT_LOADINGS_PATTERN = "pca_loadings_{phase}.png"    # Component loadings
OUTPUT_VARIANCE_PATTERN = "pca_variance_{phase}.png"    # Explained variance
DPI = 300

# Plot settings
PLOT_TOP_N_PCS = 5  # Plot first N principal components
POINT_SIZE = 10
POINT_ALPHA = 0.5

# Phase colors (only used if plotting by cyclone lifecycle phase within a PCA phase)
PHASE_COLORS = {
    "incipient": "#1f77b4",        # blue
    "intensification": "#ffbf00",  # yellow/gold
    "mature": "#d62728",           # red
    "decay": "#2ca02c",            # green
}

# ============================================================================


def load_pca_results(results_dir: Path, prefix: str, phase: str) -> tuple:
    """Load PCA results from step 1 for a specific phase.
    
    Args:
        results_dir: Results directory
        prefix: File prefix
        phase: Phase name (incipient, intensification, mature, decay)
        
    Returns:
        Tuple of (df_pca, pca_model, loadings, variance_df)
    """
    phase_suffix = f"_{phase}"
    
    # Load PC scores
    scores_file = results_dir / f"{prefix}_scores{phase_suffix}.csv"
    df_pca = pd.read_csv(scores_file)
    print(f"  ✓ Loaded PC scores: {scores_file.name}")
    print(f"    Shape: {df_pca.shape}")
    
    # Load models
    models_file = results_dir / f"{prefix}_models{phase_suffix}.pkl"
    with open(models_file, 'rb') as f:
        models = pickle.load(f)
    pca = models['pca']
    print(f"  ✓ Loaded PCA model: {models_file.name}")
    print(f"    Components: {pca.n_components_}")
    
    # Load loadings
    loadings_file = results_dir / f"{prefix}_loadings{phase_suffix}.csv"
    loadings = pd.read_csv(loadings_file, index_col=0)
    print(f"  ✓ Loaded component loadings: {loadings_file.name}")
    
    # Load explained variance
    variance_file = results_dir / f"{prefix}_explained_variance{phase_suffix}.csv"
    variance_df = pd.read_csv(variance_file)
    print(f"  ✓ Loaded explained variance: {variance_file.name}")
    
    return df_pca, pca, loadings, variance_df


def plot_pca_scatter(df_pca: pd.DataFrame, variance_df: pd.DataFrame,
                     n_pcs: int, output_file: Path, phase_name: str, dpi: int = 300):
    """Create scatter plots of principal components.
    
    Args:
        df_pca: DataFrame with PC scores
        variance_df: DataFrame with explained variance
        n_pcs: Number of PCs to plot
        output_file: Output file path
        phase_name: Name of the phase (for title and color)
        dpi: DPI for figure
    """
    print(f"  Creating PC scatter plots for {phase_name}...")
    
    # Get PC columns
    pc_cols = [col for col in df_pca.columns if col.startswith('PC')]
    n_pcs = min(n_pcs, len(pc_cols))
    pc_cols = pc_cols[:n_pcs]
    
    # Single color for this phase
    phase_color = PHASE_COLORS.get(phase_name, 'steelblue')
    
    # Number of scatter plot rows/cols (upper triangle matrix)
    n_scatter = n_pcs - 1
    
    # Create figure
    fig, axes = plt.subplots(n_scatter, n_scatter, figsize=(12, 10), dpi=dpi)
    if n_scatter == 1:
        axes = np.array([[axes]])
    
    # Create scatter plots (upper triangle matrix)
    for i in range(n_scatter):
        for j in range(i + 1, n_pcs):
            row = i
            col = j - 1
            
            ax = axes[row, col] if n_scatter > 1 else axes[0, 0]
            
            pc_x = pc_cols[j]  # Column PC
            pc_y = pc_cols[i]  # Row PC
            
            # Plot all points in single color
            ax.scatter(df_pca[pc_x], df_pca[pc_y],
                     c=phase_color, s=POINT_SIZE, alpha=POINT_ALPHA,
                     edgecolors='none', label=phase_name.title())
            
            # Get variance for labels
            var_x = variance_df[variance_df['PC'] == pc_x]['Explained_Variance_Ratio'].values[0]
            var_y = variance_df[variance_df['PC'] == pc_y]['Explained_Variance_Ratio'].values[0]
            
            # Labels
            if col == 0:  # Leftmost column
                ax.set_ylabel(f'{pc_y}\n({var_y*100:.1f}%)', fontsize=10, fontweight='bold')
            else:
                ax.set_ylabel('')
                ax.tick_params(labelleft=False)
            
            if row == n_scatter - 1:  # Bottom row
                ax.set_xlabel(f'{pc_x} ({var_x*100:.1f}%)', fontsize=10, fontweight='bold')
            else:
                ax.set_xlabel('')
                ax.tick_params(labelbottom=False)
            
            ax.grid(True, alpha=0.3)
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
            ax.axvline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
            
            # Legend only in first plot
            if i == 0 and j == 1:
                ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    
    # Hide unused subplots (lower triangle)
    for i in range(n_scatter):
        for j in range(n_scatter):
            if j >= i:  # Keep upper triangle and diagonal
                continue
            axes[i, j].axis('off')
    
    # Main title
    fig.suptitle(f'PCA Scatter Plots - {phase_name.title()} Phase', 
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # Save figure
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"    ✓ Saved: {output_file.name}")


def plot_pca_loadings(loadings: pd.DataFrame, n_pcs: int, 
                      output_file: Path, phase_name: str, dpi: int = 300):
    """Create component loadings heatmap.
    
    Args:
        loadings: DataFrame with component loadings
        n_pcs: Number of PCs to plot
        output_file: Output file path
        phase_name: Name of the phase (for title)
        dpi: DPI for figure
    """
    print(f"  Creating component loadings for {phase_name}...")
    
    # Subset to requested number of PCs
    loadings_subset = loadings.iloc[:, :n_pcs]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(max(8, n_pcs * 1.2), 6), dpi=dpi)
    
    # Create heatmap
    sns.heatmap(loadings_subset, annot=True, fmt='.2f', cmap='RdBu_r',
               center=0, vmin=-1, vmax=1, cbar_kws={'label': 'Loading'},
               ax=ax, square=False, linewidths=0.5, linecolor='gray')
    
    ax.set_xlabel('Principal Component', fontsize=12, fontweight='bold')
    ax.set_ylabel('Energy Variable', fontsize=12, fontweight='bold')
    ax.set_title(f'Component Loadings - {phase_name.title()} Phase', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=10)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
    
    plt.tight_layout()
    
    # Save figure
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"    ✓ Saved: {output_file.name}")


def plot_pca_variance(variance_df: pd.DataFrame, output_file: Path,
                      phase_name: str, n_pcs: int = None, dpi: int = 300):
    """Create explained variance plot (scree plot).
    
    Args:
        variance_df: DataFrame with explained variance
        output_file: Output file path
        phase_name: Name of the phase (for title)
        n_pcs: Number of PCs to annotate (optional)
        dpi: DPI for figure
    """
    print(f"  Creating variance plot for {phase_name}...")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
    
    x = np.arange(1, len(variance_df) + 1)
    
    # Bar plot for individual variance
    ax.bar(x, variance_df['Explained_Variance_Ratio'] * 100,
          color='steelblue', alpha=0.7, label='Individual', width=0.6)
    
    # Line plot for cumulative variance
    ax.plot(x, variance_df['Cumulative_Variance_Ratio'] * 100,
           color='red', marker='o', linewidth=2.5, markersize=8,
           label='Cumulative', zorder=3)
    
    ax.set_xlabel('Principal Component', fontsize=12, fontweight='bold')
    ax.set_ylabel('Explained Variance (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Variance Explained - {phase_name.title()} Phase', 
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right' if len(variance_df) > 5 else 'right', 
             fontsize=11, framealpha=0.95)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_xlim(0.5, len(variance_df) + 0.5)
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    
    # Add cumulative variance values
    n_annotate = n_pcs if n_pcs else len(variance_df)
    for i, (pc, cum_var) in enumerate(zip(variance_df['PC'][:n_annotate], 
                                           variance_df['Cumulative_Variance_Ratio'][:n_annotate]), 1):
        ax.text(i, cum_var * 100 + 2, f'{cum_var*100:.1f}%',
               ha='center', va='bottom', fontsize=9, color='red', fontweight='bold')
    
    plt.tight_layout()
    
    # Save figure
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"    ✓ Saved: {output_file.name}")


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)
    
    print("=" * 70)
    print("Step 2: Creating PCA visualizations for each phase")
    print("=" * 70)
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"Number of phases to process: {len(PHASES)}")
    print(f"Figures per phase: 3 (scatter, loadings, variance)")
    print()
    
    total_figures = 0
    
    for phase in PHASES:
        print(f"\n{'=' * 70}")
        print(f"Processing Phase: {phase.upper()}")
        print(f"{'=' * 70}")
        
        # Load PCA results for this phase
        df_pca, pca, loadings, variance_df = load_pca_results(
            results_dir, INPUT_PREFIX, phase
        )
        
        # Generate output file paths for this phase
        scatter_file = figures_dir / OUTPUT_SCATTER_PATTERN.format(phase=phase)
        loadings_file = figures_dir / OUTPUT_LOADINGS_PATTERN.format(phase=phase)
        variance_file = figures_dir / OUTPUT_VARIANCE_PATTERN.format(phase=phase)
        
        # Create three separate visualizations
        plot_pca_scatter(
            df_pca=df_pca,
            variance_df=variance_df,
            n_pcs=PLOT_TOP_N_PCS,
            output_file=scatter_file,
            phase_name=phase,
            dpi=DPI
        )
        
        plot_pca_loadings(
            loadings=loadings,
            n_pcs=PLOT_TOP_N_PCS,
            output_file=loadings_file,
            phase_name=phase,
            dpi=DPI
        )
        
        plot_pca_variance(
            variance_df=variance_df,
            output_file=variance_file,
            phase_name=phase,
            n_pcs=PLOT_TOP_N_PCS,
            dpi=DPI
        )
        
        total_figures += 3
    
    print("\n" + "=" * 70)
    print("✅ Step 2 complete!")
    print("=" * 70)
    print(f"Generated {total_figures} figures ({len(PHASES)} phases × 3 types) in: {figures_dir}")
    print()
    print("Next step:")
    print("  3. Run step3_optimal_k_analysis.py to determine optimal k")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
