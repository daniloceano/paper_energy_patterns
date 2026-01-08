"""Step 5: Plot energy patterns (cluster centroids).

This script visualizes the cluster centroids as energy patterns using
the lorenz-phase-space package to create Lorenz Energy Cycle diagrams.

Now plots sequential phase trajectories for each cluster showing how
energy patterns evolve through: Incipient → Intensification → Mature → Decay
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files (from step 4) - use absolute paths
RESULTS_DIR = PROJECT_ROOT / "results" / "cluster"
KMEANS_PREFIX = "kmeans"

# Output settings - use absolute paths
FIGURES_DIR = PROJECT_ROOT / "figures" / "cluster"
OUTPUT_FILE_PREFIX = "lps"  # LPS diagrams
DPI = 300

# Colorbar label font size
COLORBAR_LABELSIZE = 14

# Lorenz cycle settings
USE_LORENZ_PACKAGE = True  # Try to use lorenz-phase-space package
USE_ZOOM = True  # Use zoom in Lorenz Phase Space diagrams

# ============================================================================


def load_clustering_results(results_dir: Path, prefix: str) -> tuple:
    """Load clustering results from step 4.
    
    Args:
        results_dir: Results directory
        prefix: File prefix
        
    Returns:
        Tuple of (df_clustered, centroids_energy, centroids_pc, summary)
    """
    print("Loading clustering results...")
    
    # Load clustered data
    clustered_file = results_dir / f"{prefix}_clustered_data.csv"
    df_clustered = pd.read_csv(clustered_file, index_col=0)
    print(f"  ✓ Clustered data: {clustered_file.name}")
    print(f"    Shape: {df_clustered.shape}")
    
    # Load centroids (energy space)
    centroids_energy_file = results_dir / f"{prefix}_centroids_energy.csv"
    if centroids_energy_file.exists():
        centroids_energy = pd.read_csv(centroids_energy_file)
        print(f"  ✓ Centroids (energy space): {centroids_energy_file.name}")
    else:
        centroids_energy = None
        print(f"  ⚠️  Centroids (energy space) not found")
    
    # Load centroids (PC space)
    centroids_pc_file = results_dir / f"{prefix}_centroids_pc.csv"
    centroids_pc = pd.read_csv(centroids_pc_file)
    print(f"  ✓ Centroids (PC space): {centroids_pc_file.name}")
    
    # Load summary
    summary_file = results_dir / f"{prefix}_summary.csv"
    if summary_file.exists():
        summary = pd.read_csv(summary_file)
        print(f"  ✓ Summary: {summary_file.name}")
    else:
        summary = None
        print(f"  ⚠️  Summary not found")
    
    print()
    return df_clustered, centroids_energy, centroids_pc, summary


def plot_energy_patterns(centroids_energy: pd.DataFrame, summary: pd.DataFrame,
                        output_file: Path, dpi: int = 300,
                        use_lorenz: bool = True, use_zoom: bool = True):
    """Create Lorenz Phase Space diagrams showing phase trajectories for each cluster.
    
    Args:
        centroids_energy: DataFrame with centroids in energy space (wide format)
        summary: DataFrame with clustering summary
        output_file: Output file path
        dpi: DPI for figure
        use_lorenz: Whether to try using lorenz-phase-space package
        use_zoom: Whether to use zoom in LPS diagrams
    """
    
    if centroids_energy is None:
        print("  ❌ Cannot create energy patterns: centroids in energy space not available")
        print("     Make sure step 1 (PCA) was run to save the models.")
        return
    
    # Try to import lorenz-phase-space package
    try:
        from lorenz_phase_space.phase_diagrams import Visualizer
    except ImportError:
        print("  ⚠️  lorenz-phase-space not available")
        print("     Install with: pip install lorenz-phase-space>=1.3.0")
        return
    
    n_clusters = len(centroids_energy)
    phases = ['inc', 'int', 'mat', 'dec']
    phase_names = {'inc': 'Incipient', 'int': 'Intensification', 
                   'mat': 'Mature', 'dec': 'Decay'}
    
    print(f"  Creating LPS diagrams for {n_clusters} clusters...")
    print(f"  Phases: {' → '.join([phase_names[p] for p in phases])}")
    
    # Create two LPS diagrams: 'conversion' and 'imports'
    lps_types = ['conversion', 'imports']
    
    for lps_type in lps_types:
        print(f"\n  Processing {lps_type.upper()} LPS...")
        
        # Extract trajectory data for all clusters
        all_x_data = []
        all_y_data = []
        all_color_data = []
        all_size_data = []
        
        for cluster_id in range(n_clusters):
            centroid = centroids_energy[centroids_energy['cluster'] == cluster_id].iloc[0]
            
            # Extract sequential phase values
            x_phase = []
            y_phase = []
            color_phase = []
            size_phase = []
            
            for phase in phases:
                if lps_type == 'conversion':
                    x_phase.append(float(centroid[f'Ck_{phase}']))
                    y_phase.append(float(centroid[f'Ca_{phase}']))
                elif lps_type == 'imports':
                    x_phase.append(float(centroid[f'BAe_{phase}']))
                    y_phase.append(float(centroid[f'BKe_{phase}']))
                
                color_phase.append(float(centroid[f'Ge_{phase}']))
                size_phase.append(float(centroid[f'Ke_{phase}']))
            
            all_x_data.append(x_phase)
            all_y_data.append(y_phase)
            all_color_data.append(color_phase)
            all_size_data.append(size_phase)
        
        # Calculate global limits for consistent comparison
        x_min = min([min(x) for x in all_x_data])
        x_max = max([max(x) for x in all_x_data])
        y_min = min([min(y) for y in all_y_data])
        y_max = max([max(y) for y in all_y_data])
        color_min = min([min(c) for c in all_color_data])
        color_max = max([max(c) for c in all_color_data])
        size_min = min([min(s) for s in all_size_data])
        size_max = max([max(s) for s in all_size_data])
        
        # Create two versions: default and zoom
        for use_zoom_mode in [False, True]:
            zoom_suffix = '_zoom' if use_zoom_mode else '_default'
            
            if use_zoom_mode:
                # Adjust limits so that if all values are positive (or negative)
                # we still show a bit of the opposite sign on the axis.
                def adjusted_limits(vmin, vmax):
                    """Return adjusted (vmin_adj, vmax_adj).

                    If vmin > 0 ensure vmin_adj < 0 by adding padding.
                    If vmax < 0 ensure vmax_adj > 0 by adding padding.
                    Otherwise add a small padding around the range.
                    """
                    # Compute a base padding relative to the range
                    rng = vmax - vmin
                    if rng == 0:
                        # If constant, use absolute value or 1.0 as fallback
                        pad = abs(vmax) * 0.1 if vmax != 0 else 1.0
                    else:
                        pad = max(abs(rng) * 0.1, abs(vmax) * 0.01, abs(vmin) * 0.01)

                    vmin_adj = vmin - pad
                    vmax_adj = vmax + pad

                    # If all positive, force a small negative range
                    if vmin > 0 and vmin_adj >= 0:
                        vmin_adj = -abs(pad)
                    # If all negative, force a small positive range
                    if vmax < 0 and vmax_adj <= 0:
                        vmax_adj = abs(pad)

                    return [vmin_adj, vmax_adj]

                x_limits_adj = adjusted_limits(x_min, x_max)
                y_limits_adj = adjusted_limits(y_min, y_max)

                lps = Visualizer(
                    LPS_type=lps_type,
                    zoom=True,
                    x_limits=x_limits_adj,
                    y_limits=y_limits_adj,
                    color_limits=[color_min, color_max],
                    marker_limits=[size_min, size_max]
                )
            else:
                # Use default fixed limits
                lps = Visualizer(LPS_type=lps_type, zoom=False)
            
            ax = lps.ax
            
            # Plot each cluster trajectory
            for cluster_id in range(n_clusters):
                lps.plot_data(
                    x_axis=all_x_data[cluster_id],
                    y_axis=all_y_data[cluster_id],
                    marker_color=all_color_data[cluster_id],
                    marker_size=all_size_data[cluster_id],
                    alpha=0.8
                )
            
            # Set title
            # lps_name = 'Conversion LPS' if lps_type == 'conversion' else 'Imports LPS'
            # ax.set_title(f'{lps_name} - Energy Patterns', fontsize=12, fontweight='bold')

            # Try to increase colorbar label font size (support multiple Visualizer versions)
            try:
                if hasattr(lps, 'cbar') and lps.cbar is not None:
                    lps.cbar.ax.yaxis.label.set_size(COLORBAR_LABELSIZE)
                    lps.cbar.ax.tick_params(labelsize=max(8, COLORBAR_LABELSIZE - 2))
                    # Reduce padding between colorbar label and ticks
                    lps.cbar.ax.yaxis.labelpad = 20
                elif hasattr(lps, 'colorbar') and lps.colorbar is not None:
                    lps.colorbar.ax.yaxis.label.set_size(COLORBAR_LABELSIZE)
                    lps.colorbar.ax.tick_params(labelsize=max(8, COLORBAR_LABELSIZE - 2))
                else:
                    # Fallback: find axes that contain a ylabel and treat them as colorbar axes
                    fig = plt.gcf()
                    for a in fig.axes:
                        try:
                            if a.get_ylabel():
                                a.yaxis.label.set_size(COLORBAR_LABELSIZE)
                                a.tick_params(labelsize=max(8, COLORBAR_LABELSIZE - 2))
                        except Exception:
                            continue
            except Exception:
                pass
            
            # Save figure
            output_filename = f"lps_{lps_type}{zoom_suffix}.png"
            output_path = output_file.parent / output_filename
            plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            mode_desc = 'zoom' if use_zoom_mode else 'default'
            print(f"    ✓ {lps_type.capitalize()} LPS ({mode_desc}): {output_filename}")


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)
    
    print("=" * 70)
    print("Step 5: Plotting Lorenz Phase Space diagrams (Wide Matrix)")
    print("=" * 70)
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"Using zoom: {USE_ZOOM}")
    print(f"Format: Wide matrix (all phases together)")
    print()
    
    # Load clustering results
    df_clustered, centroids_energy, centroids_pc, summary = load_clustering_results(
        results_dir, KMEANS_PREFIX
    )
    
    # Plot energy patterns
    output_file = figures_dir / f"{OUTPUT_FILE_PREFIX}.png"
    print("Creating Lorenz Phase Space diagrams...")
    plot_energy_patterns(centroids_energy, summary, output_file,
                        dpi=DPI, use_lorenz=USE_LORENZ_PACKAGE,
                        use_zoom=USE_ZOOM)
    
    print()
    print("=" * 70)
    print("✅ Step 5 complete!")
    print("=" * 70)
    print()
    print("All clustering analysis steps complete!")
    print()
    print("Summary of outputs:")
    print(f"  - PCA results: {results_dir}/pca_*")
    print(f"  - Optimal k analysis: {results_dir}/optimal_k_*")
    print(f"  - K-Means results: {results_dir}/kmeans_*")
    print(f"  - LPS diagrams (4 files):")
    print(f"      • {figures_dir}/lps_conversion_default.png")
    print(f"      • {figures_dir}/lps_conversion_zoom.png")
    print(f"      • {figures_dir}/lps_imports_default.png")
    print(f"      • {figures_dir}/lps_imports_zoom.png")
    print()
    print("Data format: Wide matrix (28 features = 7 terms × 4 phases)")
    print(f"Total clusters: {len(centroids_energy) if centroids_energy is not None else 'N/A'}")
    print(f"Total samples: {len(df_clustered)}")
    print(f"Phase trajectory: Incipient → Intensification → Mature → Decay")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
