"""Step 2: Visualize PCA results (Wide Matrix Approach).

This script creates visualizations for PCA results from the wide matrix:
- Scatter plots of principal components (PC1 vs PC2, etc.)
- Component loadings heatmap (shows which term×phase features contribute to each PC)
- Explained variance plot

The visualizations help interpret the PCA results and understand which
energy patterns (across all phases) are captured by each component.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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

# Output settings
FIGURES_DIR = "figures/cluster"
OUTPUT_SCATTER = "pca_scatter_wide.png"
OUTPUT_LOADINGS = "pca_loadings_wide.png"
OUTPUT_VARIANCE = "pca_variance_wide.png"
OUTPUT_CORRELATION = "pca_correlation_wide.png"
DPI = 300

# Plot settings
PLOT_TOP_N_PCS = 5  # Plot first N principal components in scatter
PLOT_N_PCS_LOADINGS = 10  # Show first N PCs in loadings heatmap
POINT_SIZE = 20
POINT_ALPHA = 0.6

# ============================================================================


def load_pca_results(results_dir: Path, prefix: str) -> tuple:
    """Load PCA results from step 1.
    
    Args:
        results_dir: Results directory
        prefix: File prefix
        
    Returns:
        Tuple of (df_pca, pca_model, loadings, variance_df)
    """
    print("=" * 70)
    print("Loading PCA results")
    print("=" * 70)
    
    # Load PC scores
    scores_file = results_dir / f"{prefix}_scores.csv"
    df_pca = pd.read_csv(scores_file, index_col=0)  # track_id as index
    print(f"✓ Loaded PC scores: {scores_file.name}")
    print(f"  Shape: {df_pca.shape}")
    
    # Load models
    models_file = results_dir / f"{prefix}_models.pkl"
    with open(models_file, 'rb') as f:
        models = pickle.load(f)
    pca = models['pca']
    print(f"✓ Loaded PCA model: {models_file.name}")
    print(f"  Components: {pca.n_components_}")
    
    # Load loadings
    loadings_file = results_dir / f"{prefix}_loadings.csv"
    loadings = pd.read_csv(loadings_file, index_col=0)
    print(f"✓ Loaded loadings: {loadings_file.name}")
    print(f"  Shape: {loadings.shape}")
    
    # Load explained variance
    variance_file = results_dir / f"{prefix}_explained_variance.csv"
    variance_df = pd.read_csv(variance_file)
    print(f"✓ Loaded explained variance: {variance_file.name}")
    
    print()
    return df_pca, pca, loadings, variance_df


def plot_pca_scatter(df_pca: pd.DataFrame, variance_df: pd.DataFrame,
                    n_pcs: int, output_file: Path, dpi: int = 300):
    """Create scatter plots of principal components.
    
    Args:
        df_pca: DataFrame with PC scores
        variance_df: DataFrame with explained variance
        n_pcs: Number of PCs to plot
        output_file: Output file path
        dpi: DPI for figure
    """
    print("=" * 70)
    print("Creating PC scatter plots")
    print("=" * 70)
    
    # Get PC columns
    pc_cols = [col for col in df_pca.columns if col.startswith('PC')]
    n_pcs = min(n_pcs, len(pc_cols))
    pc_cols = pc_cols[:n_pcs]
    
    print(f"Plotting first {n_pcs} PCs")
    
    # Number of scatter plots (upper triangle matrix)
    n_scatter = n_pcs - 1
    
    # Create figure
    fig, axes = plt.subplots(n_scatter, n_scatter, figsize=(14, 12), dpi=dpi)
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
            
            # Plot
            ax.scatter(df_pca[pc_x], df_pca[pc_y],
                      c='steelblue', s=POINT_SIZE, alpha=POINT_ALPHA,
                      edgecolors='k', linewidths=0.5)
            
            # Get variance for labels
            var_x = variance_df[variance_df['PC'] == pc_x]['explained_variance_ratio'].values[0]
            var_y = variance_df[variance_df['PC'] == pc_y]['explained_variance_ratio'].values[0]
            
            # Labels
            if col == 0:  # Leftmost column
                ax.set_ylabel(f'{pc_y} ({var_y*100:.1f}%)', fontsize=11, fontweight='bold')
            else:
                ax.set_ylabel('')
                ax.tick_params(labelleft=False)
            
            if row == n_scatter - 1:  # Bottom row
                ax.set_xlabel(f'{pc_x} ({var_x*100:.1f}%)', fontsize=11, fontweight='bold')
            else:
                ax.set_xlabel('')
                ax.tick_params(labelbottom=False)
            
            ax.grid(True, alpha=0.3)
            ax.axhline(0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
            ax.axvline(0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
    
    # Hide unused subplots (lower triangle)
    for i in range(n_scatter):
        for j in range(n_scatter):
            if j >= i:  # Keep upper triangle
                continue
            axes[i, j].axis('off')
    
    # Main title
    fig.suptitle(f'PCA Scatter Plots: Cyclone Energy Patterns\n(28 features: 7 terms × 4 phases)', 
                fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # Save figure
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Saved: {output_file.name}")
    print()


def plot_pca_loadings(loadings: pd.DataFrame, n_pcs: int, 
                     output_file: Path, dpi: int = 300):
    """Create component loadings heatmap.
    
    Args:
        loadings: DataFrame with component loadings
        n_pcs: Number of PCs to show
        output_file: Output file path
        dpi: DPI for figure
    """
    print("=" * 70)
    print("Creating loadings heatmap")
    print("=" * 70)
    
    # Select first n_pcs
    loadings_subset = loadings.iloc[:n_pcs]
    
    print(f"Showing first {n_pcs} PCs × {loadings.shape[1]} features")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(18, 8), dpi=dpi)
    
    # Heatmap
    im = ax.imshow(loadings_subset, cmap='RdBu_r', aspect='auto', 
                   vmin=-1, vmax=1)
    
    # Axes
    ax.set_xticks(np.arange(len(loadings.columns)))
    ax.set_yticks(np.arange(n_pcs))
    ax.set_xticklabels(loadings.columns, rotation=90, ha='right', fontsize=9)
    ax.set_yticklabels([f'PC{i+1}' for i in range(n_pcs)], fontsize=10)
    
    # Add values in cells (for strong loadings)
    for i in range(n_pcs):
        for j in range(len(loadings.columns)):
            val = loadings_subset.iloc[i, j]
            if abs(val) > 0.3:  # Only show strong loadings
                text_color = 'white' if abs(val) > 0.5 else 'black'
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                       fontsize=7, color=text_color, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Loading', rotation=270, labelpad=20, fontsize=11)
    
    # Title
    ax.set_title(f'Component Loadings: Feature Contributions to Each PC\n'
                f'(28 features: 7 energy terms × 4 lifecycle phases)',
                pad=20, fontsize=13, fontweight='bold')
    
    # Labels
    ax.set_xlabel('Energy Term × Phase', fontsize=11, fontweight='bold')
    ax.set_ylabel('Principal Component', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Saved: {output_file.name}")
    print()


def plot_correlation_matrix(full_data_file: Path, output_file: Path, dpi: int = 300):
    """Create correlation matrix heatmap with discrete colormap.
    
    Shows only upper triangle (no redundant correlations).
    Uses discrete colormap:
    - White: -0.2 to 0.2
    - Positive: yellow (0.2-0.4), orange (0.4-0.6), red (0.6+)
    - Negative: yellow (-0.2 to -0.4), green (-0.4 to -0.6), blue (-0.6-)
    
    Args:
        full_data_file: Path to pca_full_data.csv (contains original 28 features)
        output_file: Output file path
        dpi: DPI for figure
    """
    print("=" * 70)
    print("Creating correlation matrix")
    print("=" * 70)
    
    # Load full data (original 28 features)
    df_full = pd.read_csv(full_data_file, index_col=0)
    
    # Get only the 28 original features (exclude PC columns)
    feature_cols = [col for col in df_full.columns if not col.startswith('PC')]
    df_features = df_full[feature_cols]
    
    print(f"Computing correlation for {len(feature_cols)} features")
    
    # Compute correlation matrix
    corr_matrix = df_features.corr()
    
    # Create mask for upper triangle (to avoid redundancy)
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    
    # Define boundaries for discrete colormap (0.2 intervals)
    boundaries = [-1.0, -0.6, -0.4, -0.2, 0.2, 0.4, 0.6, 1.0]
    
    # Define colors: negative (blue, green, yellow) + white + positive (yellow, orange, red)
    colors = [
        '#0000FF',  # Blue: -1.0 to -0.6
        '#00FF00',  # Green: -0.6 to -0.4
        '#FFFF00',  # Yellow: -0.4 to -0.2
        '#FFFFFF',  # White: -0.2 to 0.2
        '#FFFF00',  # Yellow: 0.2 to 0.4
        '#FFA500',  # Orange: 0.4 to 0.6
        '#FF0000',  # Red: 0.6 to 1.0
    ]
    
    # Create discrete colormap
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(boundaries, cmap.N)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 14), dpi=dpi)
    
    # Mask lower triangle
    corr_masked = corr_matrix.copy()
    corr_masked[~mask] = np.nan
    
    # Plot heatmap
    im = ax.imshow(corr_masked, cmap=cmap, norm=norm, aspect='auto')
    
    # Set ticks
    ax.set_xticks(np.arange(len(feature_cols)))
    ax.set_yticks(np.arange(len(feature_cols)))
    ax.set_xticklabels(feature_cols, rotation=90, ha='right', fontsize=8)
    ax.set_yticklabels(feature_cols, fontsize=8)
    
    # Add correlation values for strong correlations
    for i in range(len(feature_cols)):
        for j in range(len(feature_cols)):
            if mask[i, j]:  # Only upper triangle
                val = corr_matrix.iloc[i, j]
                if abs(val) > 0.4:  # Show values for |r| > 0.4
                    text_color = 'black' if abs(val) < 0.6 else 'white'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                           fontsize=6, color=text_color, fontweight='bold')
    
    # Colorbar with discrete levels
    cbar = plt.colorbar(im, ax=ax, boundaries=boundaries, ticks=boundaries)
    cbar.set_label('Pearson Correlation', rotation=270, labelpad=20, fontsize=11, fontweight='bold')
    
    # Title
    ax.set_title('Correlation Matrix: Energy Terms × Lifecycle Phases\n'
                '(28 features: 7 terms × 4 phases, upper triangle only)',
                pad=20, fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Saved: {output_file.name}")
    print()


def plot_explained_variance(variance_df: pd.DataFrame, output_file: Path, 
                           variance_threshold: float = 0.90, dpi: int = 300):
    """Create explained variance plots with 90% threshold highlighted.
    
    Args:
        variance_df: DataFrame with explained variance
        output_file: Output file path
        variance_threshold: Threshold for cumulative variance (default: 0.90)
        dpi: DPI for figure
    """
    print("=" * 70)
    print("Creating variance explained plots")
    print("=" * 70)
    
    n_pcs = len(variance_df)
    n_plot = min(30, n_pcs)  # Show up to 30 PCs
    
    # Find number of PCs for 90% threshold
    cumvar = variance_df['cumulative_variance_ratio'].values
    n_threshold = np.argmax(cumvar >= variance_threshold) + 1
    
    print(f"Showing first {n_plot} PCs")
    print(f"Number of PCs for {variance_threshold*100:.0f}% variance: {n_threshold}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 6), dpi=dpi)
    
    # Bar colors: highlight the bar at n_threshold
    bar_colors = ['steelblue'] * n_plot
    if n_threshold <= n_plot:
        bar_colors[n_threshold-1] = '#FF6B6B'  # Red highlight
    
    # Plot bars (individual variance)
    bars = ax.bar(range(1, n_plot+1), 
                  variance_df['explained_variance_ratio'].iloc[:n_plot] * 100,
                  alpha=0.7, color=bar_colors, edgecolor='black', linewidth=0.8)
    
    # Plot cumulative variance line on secondary y-axis
    ax2 = ax.twinx()
    ax2.plot(range(1, n_plot+1), 
            variance_df['cumulative_variance_ratio'].iloc[:n_plot] * 100,
            marker='o', markersize=4, linewidth=2.5, color='darkgreen',
            label='Cumulative', zorder=5)
    
    # Horizontal line at 90%
    ax2.axhline(y=variance_threshold*100, color='red', linestyle='--', 
               linewidth=2, alpha=0.7, label=f'{variance_threshold*100:.0f}% threshold',
               zorder=4)
    
    # Vertical line at n_threshold
    if n_threshold <= n_plot:
        ax.axvline(x=n_threshold, color='red', linestyle='--', 
                  linewidth=2, alpha=0.7, zorder=4)
        
        # Add text annotation
        ax2.text(n_threshold, variance_threshold*100 + 3, 
                f'n={n_threshold}\n({cumvar[n_threshold-1]*100:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
    
    # Labels and titles
    ax.set_xlabel('Principal Component', fontsize=12, fontweight='bold')
    ax.set_ylabel('Individual Variance Explained (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Variance Explained (%)', fontsize=12, fontweight='bold')
    
    ax.set_title('PCA Variance Explained (28 features: 7 terms × 4 phases)',
                fontsize=14, fontweight='bold', pad=15)
    
    # Grid and limits
    ax.grid(True, alpha=0.3, axis='y', zorder=0)
    ax.set_xlim(0, n_plot+1)
    ax.set_ylim(0, max(variance_df['explained_variance_ratio'].iloc[:n_plot] * 100) * 1.1)
    ax2.set_ylim(0, 105)
    
    # Legend for cumulative line
    ax2.legend(loc='lower right', fontsize=10, framealpha=0.9)
    
    # Tick parameters
    ax.tick_params(axis='both', labelsize=10)
    ax2.tick_params(axis='y', labelsize=10)
    
    plt.tight_layout()
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Saved: {output_file.name}")
    print()


def plot_explained_variance_OLD(variance_df: pd.DataFrame, output_file: Path, dpi: int = 300):
    """Create explained variance plots.
    
    Args:
        variance_df: DataFrame with explained variance
        output_file: Output file path
        dpi: DPI for figure
    """
    print("=" * 70)
    print("Creating variance explained plots")
    print("=" * 70)
    
    n_pcs = len(variance_df)
    
    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=dpi)
    
    # Plot 1: Individual variance
    axes[0].bar(range(1, n_pcs+1), 
               variance_df['explained_variance_ratio'] * 100,
               alpha=0.7, color='steelblue', edgecolor='black')
    axes[0].axhline(y=5, color='red', linestyle='--', alpha=0.5, 
                   label='5% threshold')
    axes[0].set_xlabel('Principal Component', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('Variance Explained (%)', fontsize=11, fontweight='bold')
    axes[0].set_title('Individual Variance Explained', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].set_xlim(0, n_pcs+1)
    
    # Plot 2: Cumulative variance
    axes[1].plot(range(1, n_pcs+1), 
                variance_df['cumulative_variance_ratio'] * 100,
                marker='o', markersize=5, linewidth=2, color='darkgreen')
    axes[1].axhline(y=90, color='red', linestyle='--', alpha=0.7, 
                   label='90% threshold')
    axes[1].axhline(y=95, color='orange', linestyle='--', alpha=0.7,
                   label='95% threshold')
    axes[1].set_xlabel('Number of Components', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('Cumulative Variance (%)', fontsize=11, fontweight='bold')
    axes[1].set_title('Cumulative Variance Explained', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(0, n_pcs+1)
    axes[1].set_ylim(0, 105)
    
    # Main title
    fig.suptitle('PCA Variance Explained (28 features: 7 terms × 4 phases)',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Saved: {output_file.name}")
    print()


def print_top_loadings(loadings: pd.DataFrame, n_pcs: int = 5, n_top: int = 5):
    """Print top loadings for first n PCs.
    
    Args:
        loadings: DataFrame with loadings
        n_pcs: Number of PCs to analyze
        n_top: Number of top features to show per PC
    """
    print("=" * 70)
    print(f"Top {n_top} Features by PC (highest |loading|)")
    print("=" * 70)
    
    for i in range(min(n_pcs, len(loadings))):
        pc_name = loadings.index[i]
        pc_loadings = loadings.iloc[i]
        top_features = pc_loadings.abs().sort_values(ascending=False).head(n_top)
        
        print(f"\n{pc_name}:")
        for feat in top_features.index:
            val = pc_loadings[feat]
            sign = '+' if val > 0 else ''
            print(f"  {feat:12s}: {sign}{val:7.4f}")
    
    print()


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)
    
    print("=" * 70)
    print("STEP 2: Visualize PCA Results (Wide Matrix)")
    print("=" * 70)
    print()
    
    # Load results
    df_pca, pca, loadings, variance_df = load_pca_results(results_dir, INPUT_PREFIX)
    
    # Print summary
    print("=" * 70)
    print("PCA Summary")
    print("=" * 70)
    print(f"Number of cyclones: {len(df_pca)}")
    print(f"Number of components: {pca.n_components_}")
    print(f"Total variance explained: {variance_df['cumulative_variance_ratio'].iloc[-1]*100:.2f}%")
    print()
    
    # Print top loadings
    print_top_loadings(loadings, n_pcs=5, n_top=5)
    
    # Create visualizations
    plot_pca_scatter(df_pca, variance_df, PLOT_TOP_N_PCS,
                    figures_dir / OUTPUT_SCATTER, DPI)
    
    plot_pca_loadings(loadings, PLOT_N_PCS_LOADINGS,
                     figures_dir / OUTPUT_LOADINGS, DPI)
    
    plot_explained_variance(variance_df, figures_dir / OUTPUT_VARIANCE, 
                           variance_threshold=0.90, dpi=DPI)
    
    # Correlation matrix
    full_data_file = results_dir / f"{INPUT_PREFIX}_full_data.csv"
    plot_correlation_matrix(full_data_file, figures_dir / OUTPUT_CORRELATION, DPI)
    
    print("=" * 70)
    print("✅ Step 2 complete!")
    print("=" * 70)
    print(f"Figures saved to: {figures_dir}/")
    print(f"  - {OUTPUT_SCATTER}")
    print(f"  - {OUTPUT_LOADINGS}")
    print(f"  - {OUTPUT_VARIANCE}")
    print(f"  - {OUTPUT_CORRELATION}")
    print()
    print("Next step:")
    print("  3. Run step3_optimal_k_analysis.py to determine optimal number of clusters")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
