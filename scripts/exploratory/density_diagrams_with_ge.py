"""Exploratory: Density diagrams with mean Ge coloring.

This script creates density diagrams similar to the reference figure,
showing the distribution of cyclones in phase space (Ca×Ck and BAe×BKe)
with mean Ge values indicated by discrete colors.

Creates multiple visualizations:
- All cyclones (2 diagrams: mixed + imports)
- By Energy Pattern (2 diagrams per EP)
- By phase (2 diagrams per phase, all cyclones)
- By phase and EP (2 diagrams per phase per EP)

Each quadrant shows the percentage of occurrences relative to the total
sample being visualized.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm
from scipy.stats import binned_statistic_2d
import cmocean

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files
RESULTS_DIR = "results/cluster"
PCA_FULL_DATA_FILE = "pca_full_data.csv"
CLUSTERED_DATA_FILE = "kmeans_clustered_data.csv"

# Output settings
FIGURES_DIR = "figures/exploratory/density_ge"
DPI = 300

# Energy Pattern mapping (cluster_id → EP_id)
CLUSTER_TO_EP = {
    0: 1,  # Cluster 0 → EP1 (lowest Ck)
    2: 2,  # Cluster 2 → EP2 (middle Ck)
    1: 3   # Cluster 1 → EP3 (highest Ck)
}

# Phases
PHASES = ['inc', 'int', 'mat', 'dec']
PHASE_NAMES = {
    'inc': 'Incipient',
    'int': 'Intensification',
    'mat': 'Mature',
    'dec': 'Decay'
}

# Density calculation settings
N_BINS = 20  # Number of bins for density calculation
MIN_POINTS_PER_BIN = 3  # Minimum points to show a bin

# Ge binning (discrete colors) - using finite values
GE_BINS = [-10, -2, -1, 0, 1, 2, 10]
GE_LABELS = ['< -2', '-2 to -1', '-1 to 0', '0 to 1', '1 to 2', '> 2']

# ============================================================================


def load_data() -> pd.DataFrame:
    """Load and merge energy data with cluster assignments.
    
    Returns:
        DataFrame with energy variables, cluster, and energy_pattern
    """
    print("Loading data...")
    
    results_dir = Path(RESULTS_DIR)
    
    # Load energy data (wide format)
    energy_file = results_dir / PCA_FULL_DATA_FILE
    df_energy = pd.read_csv(energy_file, index_col=0)
    print(f"  ✓ Energy data: {energy_file.name}")
    print(f"    Shape: {df_energy.shape}")
    
    # Load cluster assignments
    clustered_file = results_dir / CLUSTERED_DATA_FILE
    df_clustered = pd.read_csv(clustered_file, index_col=0)
    print(f"  ✓ Clustered data: {clustered_file.name}")
    print(f"    Shape: {df_clustered.shape}")
    
    # Merge
    df = df_energy.merge(
        df_clustered[['cluster']],
        left_index=True,
        right_index=True,
        how='inner'
    )
    
    # Assign Energy Patterns
    df['energy_pattern'] = df['cluster'].map(CLUSTER_TO_EP)
    
    print(f"  ✓ Merged data: {df.shape}")
    print()
    
    return df


def create_density_diagram(df: pd.DataFrame, x_var: str, y_var: str, 
                          color_var: str, ax: plt.Axes, title: str = None,
                          n_bins: int = 50, min_points: int = 3, n_sample: int = None):
    """Create a single density diagram with mean Ge coloring.
    
    Args:
        df: DataFrame with variables
        x_var: X-axis variable name
        y_var: Y-axis variable name
        color_var: Variable for coloring (Ge)
        ax: Matplotlib axes
        title: Plot title
        n_bins: Number of bins for 2D histogram
        min_points: Minimum points per bin to display
        n_sample: Sample size to add to title (optional)
    """
    
    # Get valid data
    valid_mask = df[[x_var, y_var, color_var]].notna().all(axis=1)
    x_data = df.loc[valid_mask, x_var].values
    y_data = df.loc[valid_mask, y_var].values
    color_data = df.loc[valid_mask, color_var].values
    
    n_total = len(x_data)
    
    if n_total < min_points:
        ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_title(title, fontsize=12, fontweight='bold')
        return
    
    # Calculate data-driven limits with some padding
    x_min, x_max = np.percentile(x_data, [1, 99])
    y_min, y_max = np.percentile(y_data, [1, 99])
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_min -= 0.1 * x_range
    x_max += 0.1 * x_range
    y_min -= 0.1 * y_range
    y_max += 0.1 * y_range
    
    # Create 2D histogram bins
    x_bins = np.linspace(x_min, x_max, n_bins + 1)
    y_bins = np.linspace(y_min, y_max, n_bins + 1)
    
    # Calculate mean Ge and count for each bin
    mean_ge, x_edges, y_edges, _ = binned_statistic_2d(
        x_data, y_data, color_data, 
        statistic='mean', bins=[x_bins, y_bins]
    )
    
    count, _, _, _ = binned_statistic_2d(
        x_data, y_data, color_data,
        statistic='count', bins=[x_bins, y_bins]
    )
    
    # Mask bins with too few points
    mean_ge_masked = np.ma.masked_where(count < min_points, mean_ge)
    
    # Create discrete colormap (cmocean curl - divergent)
    cmap = cmocean.cm.curl
    norm = BoundaryNorm(GE_BINS, cmap.N, extend='both')
    
    # Plot as pcolormesh
    X, Y = np.meshgrid(x_edges, y_edges)
    im = ax.pcolormesh(X, Y, mean_ge_masked.T, cmap=cmap, norm=norm,
                       shading='flat', rasterized=True)
    
    # Add contour lines for density
    # Smooth the count data for contours
    from scipy.ndimage import gaussian_filter
    count_smooth = gaussian_filter(count, sigma=1.0)
    
    # Calculate contour levels (similar to reference figure)
    max_count = count_smooth.max()
    levels = [max_count * 0.2, max_count * 0.5, max_count * 0.8]
    
    if len(levels) > 0 and max_count > 0:
        X_centers = (x_edges[:-1] + x_edges[1:]) / 2
        Y_centers = (y_edges[:-1] + y_edges[1:]) / 2
        XX, YY = np.meshgrid(X_centers, Y_centers)
        
        contours = ax.contour(XX, YY, count_smooth.T, levels=levels,
                             colors='black', linewidths=1.5, alpha=0.8)
        # Add contour labels
        ax.clabel(contours, inline=True, fontsize=9, fmt='%d')
    
    # Add reference lines at zero
    ax.axhline(0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=10)
    ax.axvline(0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=10)

    # Diagonal line on Ca×Ck plots marking Ca = - Ck but only for Ck < 0
    if x_var == 'Ck' and y_var == 'Ca':
        ax.plot([0, - x_max], [0, x_max], color='gray', linestyle='--',
                linewidth=1.5, alpha=0.7, zorder=10)
    
    # Calculate quadrant percentages
    q1 = ((x_data > 0) & (y_data > 0)).sum() / n_total * 100  # Top-right
    q2 = ((x_data < 0) & (y_data > 0)).sum() / n_total * 100  # Top-left
    q3 = ((x_data < 0) & (y_data < 0)).sum() / n_total * 100  # Bottom-left
    q4 = ((x_data > 0) & (y_data < 0)).sum() / n_total * 100  # Bottom-right
    
    # Add percentage labels in corners
    text_props = dict(fontsize=10, fontweight='bold', 
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                              edgecolor='black', alpha=0.8))
    
    # Position labels in corners (data coordinates, near edges)
    offset_x = 0.05 * (x_max - x_min)
    offset_y = 0.05 * (y_max - y_min)
    
    # Top-left (Q2)
    ax.text(x_min + offset_x, y_max - offset_y, f'{q2:.1f}%',
            ha='left', va='top', **text_props)
    
    # Top-right (Q1)
    ax.text(x_max - offset_x, y_max - offset_y, f'{q1:.1f}%',
            ha='right', va='top', **text_props)
    
    # Bottom-left (Q3)
    ax.text(x_min + offset_x, y_min + offset_y, f'{q3:.1f}%',
            ha='left', va='bottom', **text_props)
    
    # Bottom-right (Q4)
    ax.text(x_max - offset_x, y_min + offset_y, f'{q4:.1f}%',
            ha='right', va='bottom', **text_props)
    
    # Labels and title
    ax.set_xlabel(x_var, fontsize=12, fontweight='bold')
    ax.set_ylabel(y_var, fontsize=12, fontweight='bold')
    
    # Add sample size to title if provided (set on axes only if a title is given)
    if title is not None:
        if n_sample is not None:
            title_with_n = f"{title}\n(n = {n_sample})"
        else:
            title_with_n = title
        ax.set_title(title_with_n, fontsize=12, fontweight='bold', pad=10)
    
    # Set limits
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    # Grid
    ax.grid(True, alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    
    return im


def plot_all_cyclones(df: pd.DataFrame, output_dir: Path):
    """Plot density diagrams for all cyclones.
    
    Creates 2 diagrams: mixed (Ca×Ck) and imports (BAe×BKe)
    """
    print("\nPlotting all cyclones...")
    
    # Aggregate phases (mean across phases)
    cols_to_agg = {}
    for term in ['Ca', 'Ck', 'BAe', 'BKe', 'Ge']:
        phase_cols = [f'{term}_{phase}' for phase in PHASES]
        cols_to_agg[term] = df[phase_cols].mean(axis=1)
    
    df_agg = pd.DataFrame(cols_to_agg)
    df_agg['track_id'] = df.index
    
    n_cyclones = len(df)
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    # Use a shared suptitle instead of repeating the same title on both axes
    fig.suptitle(f'All Cyclones (n = {n_cyclones})', fontsize=14, fontweight='bold')
    
    # Mixed diagram (Ca×Ck)
    im = create_density_diagram(
        df_agg, 'Ck', 'Ca', 'Ge', axes[0],
        None,
        n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
    )
    
    # Imports diagram (BAe×BKe)
    im = create_density_diagram(
        df_agg, 'BAe', 'BKe', 'Ge', axes[1],
        None,
        n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
    )
    
    # Add colorbar
    if im is not None:
        cbar = fig.colorbar(im, ax=axes, orientation='horizontal', cax=fig.add_axes([0.15, - 0.05, 0.7, 0.05]))
        cbar.set_label('Mean Ge (W/m²)', fontsize=12, fontweight='bold')
        cbar.set_ticks(GE_BINS[1:-1])
        cbar.ax.set_xticklabels(GE_LABELS[:-1])
    
    plt.tight_layout()
    
    # Save
    output_file = output_dir / 'all_cyclones.png'
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")


def plot_by_energy_pattern(df: pd.DataFrame, output_dir: Path):
    """Plot density diagrams by Energy Pattern.
    
    Creates 2 diagrams per EP (mixed + imports)
    """
    print("\nPlotting by Energy Pattern...")
    
    ep_dir = output_dir / 'by_ep'
    ep_dir.mkdir(parents=True, exist_ok=True)
    
    for ep_id in sorted(df['energy_pattern'].unique()):
        df_ep = df[df['energy_pattern'] == ep_id]
        
        n_cyclones = len(df_ep)
        
        # Aggregate phases
        cols_to_agg = {}
        for term in ['Ca', 'Ck', 'BAe', 'BKe', 'Ge']:
            phase_cols = [f'{term}_{phase}' for phase in PHASES]
            cols_to_agg[term] = df_ep[phase_cols].mean(axis=1)
        
        df_agg = pd.DataFrame(cols_to_agg)
        
        # Create figure (shared title instead of repeating on both axes)
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'EP{ep_id} (n = {n_cyclones})', fontsize=14, fontweight='bold')

        # Mixed diagram
        im = create_density_diagram(
            df_agg, 'Ck', 'Ca', 'Ge', axes[0],
            None,
            n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
        )

        # Imports diagram
        im = create_density_diagram(
            df_agg, 'BAe', 'BKe', 'Ge', axes[1],
            None,
            n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
        )
        
        # Add colorbar
        if im is not None:
            cbar = fig.colorbar(im, ax=axes, orientation='horizontal',  cax=fig.add_axes([0.15, - 0.05, 0.7, 0.05]))
            cbar.set_label('Mean Ge (W/m²)', fontsize=12, fontweight='bold')
            cbar.set_ticks(GE_BINS[1:-1])
            cbar.ax.set_xticklabels(GE_LABELS[:-1])
        
        plt.tight_layout()
        
        # Save
        output_file = ep_dir / f'ep{ep_id}.png'
        plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ EP{ep_id}: {output_file.name}")


def plot_by_phase(df: pd.DataFrame, output_dir: Path):
    """Plot density diagrams by phase (all cyclones).
    
    Creates 2 diagrams per phase (mixed + imports)
    """
    print("\nPlotting by phase...")
    
    phase_dir = output_dir / 'by_phase'
    phase_dir.mkdir(parents=True, exist_ok=True)
    
    for phase in PHASES:
        phase_name = PHASE_NAMES[phase]
        
        # Extract phase-specific columns
        cols_to_extract = {}
        for term in ['Ca', 'Ck', 'BAe', 'BKe', 'Ge']:
            cols_to_extract[term] = df[f'{term}_{phase}']
        
        df_phase = pd.DataFrame(cols_to_extract)
        n_cyclones = len(df)
        
        # Create figure with shared title
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'{phase_name}', fontsize=14, fontweight='bold')

        # Mixed diagram
        im = create_density_diagram(
            df_phase, 'Ck', 'Ca', 'Ge', axes[0],
            None,
            n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
        )

        # Imports diagram
        im = create_density_diagram(
            df_phase, 'BAe', 'BKe', 'Ge', axes[1],
            None,
            n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
        )
        
        # Add colorbar
        if im is not None:
            cbar = fig.colorbar(im, ax=axes, orientation='horizontal',  cax=fig.add_axes([0.15, - 0.05, 0.7, 0.05]))
            cbar.set_label('Mean Ge (W/m²)', fontsize=12, fontweight='bold')
            cbar.set_ticks(GE_BINS[1:-1])
            cbar.ax.set_xticklabels(GE_LABELS[:-1])
        
        plt.tight_layout()
        
        # Save
        output_file = phase_dir / f'{phase}.png'
        plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ {phase_name}: {output_file.name}")


def plot_by_phase_and_ep(df: pd.DataFrame, output_dir: Path):
    """Plot density diagrams by phase and Energy Pattern.
    
    Creates 2 diagrams per phase per EP (mixed + imports)
    """
    print("\nPlotting by phase and Energy Pattern...")
    
    phase_ep_dir = output_dir / 'by_phase_ep'
    phase_ep_dir.mkdir(parents=True, exist_ok=True)
    
    for ep_id in sorted(df['energy_pattern'].unique()):
        df_ep = df[df['energy_pattern'] == ep_id]
        
        for phase in PHASES:
            phase_name = PHASE_NAMES[phase]
            
            # Extract phase-specific columns
            cols_to_extract = {}
            for term in ['Ca', 'Ck', 'BAe', 'BKe', 'Ge']:
                cols_to_extract[term] = df_ep[f'{term}_{phase}']
            
            df_phase = pd.DataFrame(cols_to_extract)
            n_cyclones = len(df_ep)
            
            # Create figure with shared suptitle
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            fig.suptitle(f'EP{ep_id} - {phase_name} (n = {n_cyclones})', fontsize=14, fontweight='bold')

            # Mixed diagram
            im = create_density_diagram(
                df_phase, 'Ck', 'Ca', 'Ge', axes[0],
                None,
                n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
            )

            # Imports diagram
            im = create_density_diagram(
                df_phase, 'BAe', 'BKe', 'Ge', axes[1],
                None,
                n_bins=N_BINS, min_points=MIN_POINTS_PER_BIN, n_sample=n_cyclones
            )
            
            # Add colorbar
            if im is not None:
                cbar = fig.colorbar(im, ax=axes, orientation='horizontal',  cax=fig.add_axes([0.15, - 0.05, 0.7, 0.05]))
                cbar.set_label('Mean Ge (W/m²)', fontsize=12, fontweight='bold')
                cbar.set_ticks(GE_BINS[1:-1])
                cbar.ax.set_xticklabels(GE_LABELS[:-1])
            
            plt.tight_layout()
            
            # Save
            output_file = phase_ep_dir / f'ep{ep_id}_{phase}.png'
            plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
            plt.close()
            
            print(f"  ✓ EP{ep_id} - {phase_name}: {output_file.name}")


def main():
    """Main execution function."""
    
    output_dir = Path(FIGURES_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Exploratory: Density Diagrams with Mean Ge")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print(f"Number of bins: {N_BINS}")
    print(f"Min points per bin: {MIN_POINTS_PER_BIN}")
    print(f"Ge bins: {GE_BINS}")
    print()
    
    # Load data
    df = load_data()
    
    # Display distribution
    print("Energy Pattern distribution:")
    for ep_id in sorted(df['energy_pattern'].unique()):
        count = (df['energy_pattern'] == ep_id).sum()
        pct = 100 * count / len(df)
        print(f"  EP{ep_id}: {count:4d} cyclones ({pct:5.1f}%)")
    print()
    
    # Generate all visualizations
    plot_all_cyclones(df, output_dir)
    plot_by_energy_pattern(df, output_dir)
    plot_by_phase(df, output_dir)
    plot_by_phase_and_ep(df, output_dir)
    
    print()
    print("=" * 70)
    print("✅ All density diagrams created!")
    print("=" * 70)
    print()
    print("Summary of outputs:")
    print(f"  • All cyclones: {output_dir}/all_cyclones.png")
    print(f"  • By EP (3 files): {output_dir}/by_ep/ep*.png")
    print(f"  • By phase (4 files): {output_dir}/by_phase/*.png")
    print(f"  • By phase & EP (12 files): {output_dir}/by_phase_ep/*.png")
    print()
    print(f"Total figures: 1 + 3 + 4 + 12 = 20 files")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
