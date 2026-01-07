"""Figure S1: PCA and Clustering Validation.

This script creates a supplementary figure with two panels:
(a) PCA Explained Variance - showing the variance explained by each principal component
(b) Optimal k Selection - showing normalized cluster validity indices

Publication-ready for Scientific Reports.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files
RESULTS_DIR = PROJECT_ROOT / "results" / "cluster"
PCA_VARIANCE_FILE = "pca_explained_variance.csv"
OPTIMAL_K_NORM_FILE = "optimal_k_normalized_indices.csv"
OPTIMAL_K_FILE = "optimal_k.txt"

# Output settings
FIGURES_DIR = PROJECT_ROOT / "figures" / "main"
OUTPUT_FILE = "S1_pca_clustering_validation.png"
DPI = 300

# Plot settings
VARIANCE_THRESHOLD = 0.90  # 90% variance threshold for PCA
N_PCS_TO_SHOW = 30  # Maximum number of PCs to show

# ============================================================================


def load_data():
    """Load PCA variance and clustering validation data.
    
    Returns:
        Tuple of (variance_df, df_norm, optimal_k)
    """
    print("=" * 70)
    print("Loading data")
    print("=" * 70)
    
    # Load PCA variance
    variance_file = RESULTS_DIR / PCA_VARIANCE_FILE
    variance_df = pd.read_csv(variance_file)
    print(f"✓ Loaded PCA variance: {variance_file.name}")
    print(f"  Components: {len(variance_df)}")
    
    # Load normalized indices
    norm_file = RESULTS_DIR / OPTIMAL_K_NORM_FILE
    df_norm = pd.read_csv(norm_file)
    print(f"✓ Loaded normalized indices: {norm_file.name}")
    print(f"  k range: {df_norm['k'].min()} to {df_norm['k'].max()}")
    
    # Load optimal k
    optimal_k_file = RESULTS_DIR / OPTIMAL_K_FILE
    with open(optimal_k_file, 'r') as f:
        optimal_k = int(f.read().strip())
    print(f"✓ Loaded optimal k: {optimal_k}")
    
    print()
    return variance_df, df_norm, optimal_k


def plot_pca_variance(ax, variance_df: pd.DataFrame, 
                     variance_threshold: float = 0.90):
    """Plot PCA explained variance.
    
    Args:
        ax: Matplotlib axis
        variance_df: DataFrame with explained variance
        variance_threshold: Threshold for cumulative variance
    """
    n_pcs = len(variance_df)
    n_plot = min(N_PCS_TO_SHOW, n_pcs)
    
    # Find number of PCs for threshold
    cumvar = variance_df['cumulative_variance_ratio'].values
    n_threshold = np.argmax(cumvar >= variance_threshold) + 1
    
    # Bar colors: highlight the bar at n_threshold
    bar_colors = ['steelblue'] * n_plot
    if n_threshold <= n_plot:
        bar_colors[n_threshold-1] = '#FF6B6B'  # Red highlight
    
    # Plot bars (individual variance)
    ax.bar(range(1, n_plot+1), 
           variance_df['explained_variance_ratio'].iloc[:n_plot] * 100,
           alpha=0.7, color=bar_colors, edgecolor='black', linewidth=0.8,
           zorder=3)
    
    # Plot cumulative variance line on secondary y-axis
    ax2 = ax.twinx()
    ax2.plot(range(1, n_plot+1), 
             variance_df['cumulative_variance_ratio'].iloc[:n_plot] * 100,
             marker='o', markersize=5, linewidth=2.5, color='darkgreen',
             label='Cumulative', zorder=5)
    
    # Horizontal line at threshold
    ax2.axhline(y=variance_threshold*100, color='red', linestyle='--', 
                linewidth=2, alpha=0.7, label=f'{variance_threshold*100:.0f}% threshold',
                zorder=4)
    
    # Vertical line at n_threshold
    if n_threshold <= n_plot:
        ax.axvline(x=n_threshold, color='red', linestyle='--', 
                   linewidth=2, alpha=0.7, zorder=4)
        
        # Add text annotation
        ax2.text(n_threshold - 6, variance_threshold*100 + 4.3, 
                 f'n={n_threshold}\n({cumvar[n_threshold-1]*100:.1f}%)',
                 ha='center', va='bottom', fontsize=10, fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                 zorder=6)
    
    # Labels
    ax.set_xlabel('Principal Component', fontsize=12, fontweight='bold')
    ax.set_ylabel('Individual Variance (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Variance (%)', fontsize=12, fontweight='bold')
    
    # Grid and limits
    ax.grid(True, alpha=0.3, axis='y', zorder=0)
    ax.set_xlim(0, n_plot+1)
    ax.set_ylim(0, max(variance_df['explained_variance_ratio'].iloc[:n_plot] * 100) * 1.1)
    ax2.set_ylim(0, 105)
    
    # Legend for cumulative line (outside plot area)
    ax2.legend(fontsize=10, framealpha=0.9, bbox_to_anchor=(0.94, 0.99), 
               loc='upper right')
    
    # Tick parameters
    ax.tick_params(axis='both', labelsize=10)
    ax2.tick_params(axis='y', labelsize=10)
    
    # Panel label
    ax.text(-0.1, 1.05, '(a)', transform=ax.transAxes, fontsize=14, 
            fontweight='bold', va='top', ha='right')


def plot_optimal_k(ax, df_norm: pd.DataFrame, optimal_k: int):
    """Plot normalized cluster validity indices with mean.
    
    Args:
        ax: Matplotlib axis
        df_norm: DataFrame with normalized indices
        optimal_k: Optimal k value
    """
    # Get metric columns (exclude k and mean_index)
    metric_cols = [col for col in df_norm.columns if col not in ['k', 'mean_index']]
    
    # Plot individual indices
    for col in metric_cols:
        ax.plot(df_norm['k'], df_norm[col], marker='o', label=col, 
                alpha=0.6, linewidth=1.5, markersize=5)
    
    # Plot mean index (prominent)
    ax.plot(df_norm['k'], df_norm['mean_index'], 
            marker='o', linewidth=3, markersize=8, color='black', 
            label='Mean Index', zorder=5)
    
    # Highlight optimal k
    ax.axvline(optimal_k, color='red', linestyle='--', linewidth=2, 
               label=f'Optimal k={optimal_k}', zorder=4)
    
    optimal_mean = df_norm[df_norm['k'] == optimal_k]['mean_index'].values[0]
    ax.scatter([optimal_k], [optimal_mean], color='red', s=200, zorder=6,
               marker='*', edgecolors='darkred', linewidths=2)
    
    # Labels
    ax.set_xlabel('Number of clusters (k)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Normalized index\n(higher is better)', fontsize=12, fontweight='bold')
    
    # Grid and limits
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)
    
    # Legend outside plot area (to the right)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9, 
              framealpha=0.9, ncol=1)
    
    # Tick parameters
    ax.tick_params(axis='both', labelsize=10)
    
    # Panel label
    ax.text(-0.1, 1.05, '(b)', transform=ax.transAxes, fontsize=14, 
            fontweight='bold', va='top', ha='right')


def create_supplementary_figure(variance_df: pd.DataFrame, df_norm: pd.DataFrame,
                                optimal_k: int, output_file: Path):
    """Create supplementary figure with PCA and clustering validation.
    
    Args:
        variance_df: DataFrame with PCA explained variance
        df_norm: DataFrame with normalized clustering indices
        optimal_k: Optimal number of clusters
        output_file: Output file path
    """
    print("=" * 70)
    print("Creating supplementary figure")
    print("=" * 70)
    
    # Create figure with 2 subplots (1 row, 2 columns)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=DPI)
    
    # Plot (a) PCA Variance
    plot_pca_variance(axes[0], variance_df, VARIANCE_THRESHOLD)
    
    # Plot (b) Optimal k
    plot_optimal_k(axes[1], df_norm, optimal_k)
    
    # Adjust layout to accommodate legends outside plot areas
    plt.tight_layout(rect=[0, 0, 0.95, 0.96])
    
    # Save figure
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Saved: {output_file.name}")
    print(f"  Location: {output_file}")
    print()


def main():
    """Main execution function."""
    print("\n" + "=" * 70)
    print("FIGURE S1: PCA AND CLUSTERING VALIDATION")
    print("=" * 70 + "\n")
    
    # Load data
    variance_df, df_norm, optimal_k = load_data()
    
    # Create figure
    output_path = FIGURES_DIR / OUTPUT_FILE
    create_supplementary_figure(variance_df, df_norm, optimal_k, output_path)
    
    print("=" * 70)
    print("COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nFigure saved to: {output_path}")
    print(f"Resolution: {DPI} DPI")
    print(f"Format: PNG\n")


if __name__ == "__main__":
    main()
