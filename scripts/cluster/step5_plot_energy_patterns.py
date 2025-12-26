"""Step 5: Plot energy patterns (cluster centroids).

This script visualizes the cluster centroids as energy patterns using
the lorenz-phase-space package to create Lorenz Energy Cycle diagrams.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files (from step 4)
RESULTS_DIR = "results/cluster"
KMEANS_PREFIX = "kmeans"

# Phases to plot (will create separate figures for each phase)
PHASES = ['incipient', 'intensification', 'mature', 'decay']

# Output settings
FIGURES_DIR = "figures/cluster"
OUTPUT_FILE_PATTERN = "lps_{phase}.png"  # One figure per phase
DPI = 300

# Lorenz cycle settings
USE_LORENZ_PACKAGE = True  # Try to use lorenz-phase-space package
USE_ZOOM = True  # Use zoom in Lorenz Phase Space diagrams
FIGSIZE_PER_CLUSTER = (8, 8)  # Size for each Lorenz diagram

# Cluster colors (will be generated automatically if None)
CLUSTER_COLORS = None  # e.g., ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

# ============================================================================


def load_clustering_results(results_dir: Path, prefix: str, phase: str) -> tuple:
    """Load clustering results from step 4 for a specific phase.
    
    Args:
        results_dir: Results directory
        prefix: File prefix
        phase: Phase name
        
    Returns:
        Tuple of (df_clustered, centroids_energy, centroids_pc, summary)
    """
    print(f"  Loading clustering results for {phase}...")
    
    # Load clustered data
    clustered_file = results_dir / f"{prefix}_clustered_data_{phase}.csv"
    df_clustered = pd.read_csv(clustered_file)
    print(f"    ✓ Clustered data: {clustered_file.name} (shape: {df_clustered.shape})")
    
    # Load centroids (energy space)
    centroids_energy_file = results_dir / f"{prefix}_centroids_energy_{phase}.csv"
    if centroids_energy_file.exists():
        centroids_energy = pd.read_csv(centroids_energy_file)
        print(f"    ✓ Centroids (energy space): {centroids_energy_file.name}")
    else:
        centroids_energy = None
        print(f"    ⚠️  Centroids (energy space) not found")
    
    # Load centroids (PC space)
    centroids_pc_file = results_dir / f"{prefix}_centroids_pc_{phase}.csv"
    centroids_pc = pd.read_csv(centroids_pc_file)
    print(f"    ✓ Centroids (PC space): {centroids_pc_file.name}")
    
    # Load summary
    summary_file = results_dir / f"{prefix}_summary_{phase}.csv"
    if summary_file.exists():
        summary = pd.read_csv(summary_file)
        print(f"    ✓ Summary: {summary_file.name}")
    else:
        summary = None
        print(f"    ⚠️  Summary not found")
    
    print()
    return df_clustered, centroids_energy, centroids_pc, summary
    
    # Load summary
    summary_file = results_dir / f"{prefix}_summary.csv"
    summary = pd.read_csv(summary_file)
    print(f"✓ Loaded clustering summary: {summary_file}")
    print()
    
    return df_clustered, centroids_energy, centroids_pc, summary


def plot_lorenz_cycle_simple(centroids: pd.DataFrame, cluster_id: int, 
                            ax: plt.Axes, color: str = None):
    """Plot a simple Lorenz Energy Cycle diagram.
    
    This is a simplified version without the full lorenz-phase-space package.
    Shows energy reservoirs (Ae, Ke) and conversion terms as arrows.
    
    Args:
        centroids: DataFrame with centroid values
        cluster_id: Cluster ID to plot
        ax: Matplotlib axes
        color: Color for the diagram
    """
    if color is None:
        color = 'steelblue'
    
    # Get centroid values
    centroid = centroids[centroids['cluster'] == cluster_id].iloc[0]
    
    # Energy reservoirs
    Ae = centroid.get('Ae', 0)
    Ke = centroid.get('Ke', 0)
    
    # Conversion terms
    Ca = centroid.get('Ca', 0)
    Ce = centroid.get('Ce', 0)
    Ck = centroid.get('Ck', 0)
    
    # Boundary terms
    BAe = centroid.get('BAe', 0)
    BKe = centroid.get('BKe', 0)
    
    # Generation term
    Ge = centroid.get('Ge', 0)
    
    # Residual
    RKe = centroid.get('RKe', 0)
    
    # Box positions (normalized)
    box_width = 0.15
    box_height = 0.12
    
    # Positions: Ae (left), Ke (right)
    pos_Ae = (0.25, 0.5)
    pos_Ke = (0.75, 0.5)
    
    # Draw boxes for energy reservoirs
    ax.add_patch(plt.Rectangle((pos_Ae[0] - box_width/2, pos_Ae[1] - box_height/2),
                               box_width, box_height, 
                               facecolor='lightblue', edgecolor=color, linewidth=2))
    ax.text(pos_Ae[0], pos_Ae[1], f'Ae\n{Ae:.2e}', 
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.add_patch(plt.Rectangle((pos_Ke[0] - box_width/2, pos_Ke[1] - box_height/2),
                               box_width, box_height,
                               facecolor='lightcoral', edgecolor=color, linewidth=2))
    ax.text(pos_Ke[0], pos_Ke[1], f'Ke\n{Ke:.2e}',
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw arrows for conversion terms
    arrow_props = dict(arrowstyle='->', lw=2, color=color)
    
    # Ck: Ae -> Ke
    if abs(Ck) > 1e-10:
        arrow_style = '->' if Ck > 0 else '<-'
        ax.annotate('', xy=(pos_Ke[0] - box_width/2, pos_Ke[1]), 
                   xytext=(pos_Ae[0] + box_width/2, pos_Ae[1]),
                   arrowprops=dict(arrowstyle=arrow_style, lw=abs(Ck)*10+1, color=color, alpha=0.7))
        ax.text((pos_Ae[0] + pos_Ke[0])/2, pos_Ae[1] + 0.08, 
               f'Ck: {Ck:.2e}', ha='center', fontsize=8, color=color)
    
    # BAe: boundary input to Ae
    if abs(BAe) > 1e-10:
        arrow_style = '->' if BAe > 0 else '<-'
        ax.annotate('', xy=(pos_Ae[0] - box_width/2 - 0.02, pos_Ae[1]),
                   xytext=(pos_Ae[0] - box_width/2 - 0.15, pos_Ae[1]),
                   arrowprops=dict(arrowstyle=arrow_style, lw=abs(BAe)*10+1, color='green', alpha=0.7))
        ax.text(pos_Ae[0] - box_width/2 - 0.08, pos_Ae[1] + 0.08,
               f'BAe: {BAe:.2e}', ha='center', fontsize=8, color='green')
    
    # BKe: boundary input to Ke
    if abs(BKe) > 1e-10:
        arrow_style = '->' if BKe > 0 else '<-'
        ax.annotate('', xy=(pos_Ke[0] + box_width/2 + 0.02, pos_Ke[1]),
                   xytext=(pos_Ke[0] + box_width/2 + 0.15, pos_Ke[1]),
                   arrowprops=dict(arrowstyle=arrow_style, lw=abs(BKe)*10+1, color='purple', alpha=0.7))
        ax.text(pos_Ke[0] + box_width/2 + 0.08, pos_Ke[1] + 0.08,
               f'BKe: {BKe:.2e}', ha='center', fontsize=8, color='purple')
    
    # Ge: generation term (curved arrow at Ae)
    if abs(Ge) > 1e-10:
        arrow_style = '->' if Ge > 0 else '<-'
        ax.annotate('', xy=(pos_Ae[0], pos_Ae[1] - box_height/2 - 0.02),
                   xytext=(pos_Ae[0] - 0.08, pos_Ae[1] - box_height/2 - 0.08),
                   arrowprops=dict(arrowstyle=arrow_style, lw=abs(Ge)*10+1, 
                                 color='orange', alpha=0.7, connectionstyle='arc3,rad=.5'))
        ax.text(pos_Ae[0], pos_Ae[1] - box_height/2 - 0.12,
               f'Ge: {Ge:.2e}', ha='center', fontsize=8, color='orange')
    
    # RKe: residual (curved arrow at Ke)
    if abs(RKe) > 1e-10:
        arrow_style = '->' if RKe > 0 else '<-'
        ax.annotate('', xy=(pos_Ke[0], pos_Ke[1] + box_height/2 + 0.02),
                   xytext=(pos_Ke[0] + 0.08, pos_Ke[1] + box_height/2 + 0.08),
                   arrowprops=dict(arrowstyle=arrow_style, lw=abs(RKe)*10+1,
                                 color='brown', alpha=0.7, connectionstyle='arc3,rad=-.5'))
        ax.text(pos_Ke[0], pos_Ke[1] + box_height/2 + 0.12,
               f'RKe: {RKe:.2e}', ha='center', fontsize=8, color='brown')
    
    # Ca, Ce (if available)
    if 'Ca' in centroid and abs(centroid['Ca']) > 1e-10:
        ax.text(0.05, 0.95, f'Ca: {centroid["Ca"]:.2e}', 
               transform=ax.transAxes, fontsize=8, va='top')
    if 'Ce' in centroid and abs(centroid['Ce']) > 1e-10:
        ax.text(0.05, 0.90, f'Ce: {centroid["Ce"]:.2e}',
               transform=ax.transAxes, fontsize=8, va='top')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'Cluster {cluster_id}', fontsize=12, fontweight='bold', color=color)


def plot_energy_patterns(centroids_energy: pd.DataFrame, summary: pd.DataFrame,
                        output_file: Path, phase_name: str, dpi: int = 300,
                        use_lorenz: bool = True, use_zoom: bool = True, 
                        cluster_colors: list = None):
    """Create Lorenz Phase Space diagrams for cluster centroids.
    
    Args:
        centroids_energy: DataFrame with centroids in energy space
        summary: DataFrame with clustering summary
        output_file: Output file path
        phase_name: Name of the phase (for title)
        dpi: DPI for figure
        use_lorenz: Whether to try using lorenz-phase-space package
        use_zoom: Whether to use zoom in LPS diagrams
        cluster_colors: List of colors for clusters
    """
    
    if centroids_energy is None:
        print("    ❌ Cannot create energy patterns: centroids in energy space not available")
        print("       Make sure step 1 (PCA) was run to save the models.")
        return
    
    n_clusters = len(centroids_energy)
    
    # Try to use lorenz-phase-space package
    use_lorenz_pkg = False
    if use_lorenz:
        try:
            from lorenz_phase_space.phase_diagrams import Visualizer
            use_lorenz_pkg = True
        except ImportError:
            print("    ⚠️  lorenz-phase-space not available")
            return
    
    if not use_lorenz_pkg:
        print("    ❌ lorenz-phase-space package required for energy patterns")
        return
    
    # Create two LPS diagrams: 'mixed' and 'imports'
    lps_types = ['mixed', 'imports']
    
    for idx, lps_type in enumerate(lps_types):
        # Initialize Lorenz Phase Space with proper labels and zoom
        try:
            lps = Visualizer(LPS_type=lps_type, zoom=use_zoom, 
                           labels={'size_label': 'Ke', 'color_label': 'Ge'})
        except (KeyError, TypeError):
            # Fallback for older versions
            try:
                lps = Visualizer(LPS_type=lps_type, zoom=use_zoom)
            except:
                print(f"    ❌ Could not create Visualizer for {lps_type}")
                continue
        
        ax = lps.ax  # Get the axes from the Visualizer
        
        # Plot each cluster centroid
        for cluster_id in range(n_clusters):
            centroid = centroids_energy[centroids_energy['cluster'] == cluster_id].iloc[0]
            
            # Prepare data based on LPS type
            if lps_type == 'mixed':
                x_data = [float(centroid['Ck'])]
                y_data = [float(centroid['Ca'])]
            elif lps_type == 'imports':
                x_data = [float(centroid['BAe'])]
                y_data = [float(centroid['BKe'])]
            
            # Marker color and size
            marker_color = [float(centroid['Ge'])]
            marker_size = [float(centroid['Ke'])]
            
            # Plot data point
            lps.plot_data(
                x_axis=x_data,
                y_axis=y_data,
                marker_color=marker_color,
                marker_size=marker_size
            )
            
            # Add cluster label
            ax.text(x_data[0], y_data[0], f'  C{cluster_id}', 
                   fontsize=10, fontweight='bold', 
                   ha='left', va='center')
        
        # Add cluster size info as text
        info_text = []
        for cluster_id in range(n_clusters):
            size_col = f'cluster_{cluster_id}_size'
            pct_col = f'cluster_{cluster_id}_percentage'
            if size_col in summary.columns:
                size = int(summary[size_col].values[0])
                pct = summary[pct_col].values[0]
                info_text.append(f'C{cluster_id}: n={size} ({pct:.1f}%)')
        
        if info_text:
            ax.text(0.02, 0.98, '\n'.join(info_text),
                   transform=ax.transAxes, fontsize=9,
                   va='top', ha='left',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Set subplot title
        lps_name = 'Mixed Phase Space (Ck vs Ca)' if lps_type == 'mixed' else 'Imports Phase Space (BAe vs BKe)'
        ax.set_title(f'{lps_name} - {phase_name.title()} Phase', fontsize=12, fontweight='bold')
        
        # Save individual figure and close before creating next
        if idx == 0:
            output_file_mixed = output_file.parent / f"lps_{phase_name}_mixed.png"
            plt.savefig(output_file_mixed, dpi=dpi, bbox_inches='tight')
            print(f"    ✓ Mixed LPS saved: {output_file_mixed.name}")
        else:
            output_file_imports = output_file.parent / f"lps_{phase_name}_imports.png"
            plt.savefig(output_file_imports, dpi=dpi, bbox_inches='tight')
            print(f"    ✓ Imports LPS saved: {output_file_imports.name}")
        
        plt.close()


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)
    
    print("=" * 70)
    print("Step 5: Plotting Lorenz Phase Space diagrams for each phase")
    print("=" * 70)
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"Number of phases to plot: {len(PHASES)}")
    print(f"Using zoom: {USE_ZOOM}")
    print()
    
    for phase in PHASES:
        print(f"\n{'=' * 70}")
        print(f"Processing Phase: {phase.upper()}")
        print(f"{'=' * 70}")
        
        # Load clustering results for this phase
        df_clustered, centroids_energy, centroids_pc, summary = load_clustering_results(
            results_dir, KMEANS_PREFIX, phase
        )
        
        # Plot energy patterns
        output_file = figures_dir / OUTPUT_FILE_PATTERN.format(phase=phase)
        print(f"  Creating Lorenz Phase Space diagrams...")
        plot_energy_patterns(centroids_energy, summary, output_file,
                            phase_name=phase, dpi=DPI, use_lorenz=USE_LORENZ_PACKAGE,
                            use_zoom=USE_ZOOM, cluster_colors=CLUSTER_COLORS)
    
    print("\n" + "=" * 70)
    print("✅ Step 5 complete!")
    print("=" * 70)
    print()
    print("All clustering analysis steps complete!")
    print()
    print("Summary of outputs:")
    print(f"  - PCA results: {results_dir}/pca_*")
    print(f"  - Optimal k analysis: {results_dir}/optimal_k_*")
    print(f"  - K-Means results: {results_dir}/kmeans_*")
    print(f"  - LPS diagrams: {figures_dir}/lps_*")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
