"""Exploratory: Plot LPS diagrams for each Energy Pattern.

This script creates Lorenz Phase Space diagrams showing all cyclones
belonging to each Energy Pattern (EP1, EP2, EP3).

Energy Pattern definitions (by mean Ck):
- EP1: Lowest mean Ck (strongest baroclinic conversion)
- EP2: Middle mean Ck
- EP3: Highest mean Ck (weakest baroclinic conversion)

For each EP, creates 4 diagrams:
- Conversion LPS (default limits)
- Conversion LPS (zoom)
- Imports LPS (default limits)
- Imports LPS (zoom)
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

# Input files
RESULTS_DIR = "results/cluster"
CLUSTERED_DATA_FILE = "kmeans_clustered_data.csv"
CENTROIDS_ENERGY_FILE = "kmeans_centroids_energy.csv"

# Output settings
FIGURES_DIR = "figures/exploratory/lps_diagrams_by_ep"
DPI = 300

# Energy Pattern mapping (cluster_id → EP_id)
# Based on mean Ck values:
#   Cluster 0: Mean Ck = -16.48 → EP1 (lowest)
#   Cluster 2: Mean Ck = -3.49  → EP2 (middle)
#   Cluster 1: Mean Ck = -1.71  → EP3 (highest)
CLUSTER_TO_EP = {
    0: 1,  # Cluster 0 → EP1
    2: 2,  # Cluster 2 → EP2
    1: 3   # Cluster 1 → EP3
}

# ============================================================================


def load_data() -> tuple:
    """Load clustering results and original data.
    
    Returns:
        Tuple of (df_clustered, centroids_energy)
    """
    print("Loading data...")
    
    results_dir = Path(RESULTS_DIR)
    
    # Load clustered data (has track_id and cluster assignment)
    clustered_file = results_dir / CLUSTERED_DATA_FILE
    df_clustered = pd.read_csv(clustered_file, index_col=0)
    print(f"  ✓ Clustered data: {clustered_file.name}")
    print(f"    Shape: {df_clustered.shape}")
    print(f"    Clusters: {sorted(df_clustered['cluster'].unique())}")
    
    # Load centroids
    centroids_file = results_dir / CENTROIDS_ENERGY_FILE
    centroids_energy = pd.read_csv(centroids_file)
    print(f"  ✓ Centroids: {centroids_file.name}")
    print(f"    Shape: {centroids_energy.shape}")
    
    # Load original energy data (wide format)
    # Need to reconstruct from PCA scores using inverse transform
    # For now, we'll load the PCA full data which should have the energy terms
    pca_full_file = results_dir / "pca_full_data.csv"
    if pca_full_file.exists():
        df_energy = pd.read_csv(pca_full_file, index_col=0)
        print(f"  ✓ Energy data: {pca_full_file.name}")
        print(f"    Shape: {df_energy.shape}")
    else:
        raise FileNotFoundError(f"Energy data file not found: {pca_full_file}")
    
    # Merge cluster assignments with energy data
    df_merged = df_energy.merge(
        df_clustered[['cluster']],
        left_index=True,
        right_index=True,
        how='inner'
    )
    print(f"  ✓ Merged data: {df_merged.shape}")
    
    print()
    return df_merged, centroids_energy


def assign_energy_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Assign Energy Pattern labels based on cluster.
    
    Args:
        df: DataFrame with 'cluster' column
        
    Returns:
        DataFrame with added 'energy_pattern' column
    """
    df = df.copy()
    df['energy_pattern'] = df['cluster'].map(CLUSTER_TO_EP)
    return df


def plot_lps_for_ep(df_ep: pd.DataFrame, ep_id: int, output_dir: Path, dpi: int = 300):
    """Create LPS diagrams for a single Energy Pattern.
    
    Args:
        df_ep: DataFrame with all cyclones in this EP (wide format)
        ep_id: Energy Pattern ID (1, 2, or 3)
        output_dir: Output directory for figures
        dpi: DPI for figures
    """
    
    try:
        from lorenz_phase_space.phase_diagrams import Visualizer
    except ImportError:
        print("  ❌ lorenz-phase-space not available")
        print("     Install with: pip install lorenz-phase-space>=1.3.0")
        return
    
    n_cyclones = len(df_ep)
    phases = ['inc', 'int', 'mat', 'dec']
    phase_names = {'inc': 'Incipient', 'int': 'Intensification', 
                   'mat': 'Mature', 'dec': 'Decay'}
    
    print(f"\n  Energy Pattern {ep_id} ({n_cyclones} cyclones)")
    print(f"  Phases: {' → '.join([phase_names[p] for p in phases])}")
    
    # Create diagrams for both LPS types
    lps_types = ['conversion', 'imports']
    
    for lps_type in lps_types:
        print(f"\n    Processing {lps_type.upper()} LPS...")
        
        # Extract trajectory data for all cyclones
        all_x_data = []
        all_y_data = []
        all_color_data = []
        all_size_data = []
        
        for idx, row in df_ep.iterrows():
            # Extract sequential phase values
            x_phase = []
            y_phase = []
            color_phase = []
            size_phase = []
            
            for phase in phases:
                if lps_type == 'conversion':
                    x_phase.append(float(row[f'Ck_{phase}']))
                    y_phase.append(float(row[f'Ca_{phase}']))
                elif lps_type == 'imports':
                    x_phase.append(float(row[f'BAe_{phase}']))
                    y_phase.append(float(row[f'BKe_{phase}']))
                
                color_phase.append(float(row[f'Ge_{phase}']))
                size_phase.append(float(row[f'Ke_{phase}']))
            
            all_x_data.append(x_phase)
            all_y_data.append(y_phase)
            all_color_data.append(color_phase)
            all_size_data.append(size_phase)
        
        # Calculate global limits for zoom mode
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
                # Use custom limits for zoom mode
                lps = Visualizer(
                    LPS_type=lps_type,
                    zoom=True,
                    x_limits=[x_min, x_max],
                    y_limits=[y_min, y_max],
                    color_limits=[color_min, color_max],
                    marker_limits=[size_min, size_max]
                )
            else:
                # Use default fixed limits
                lps = Visualizer(LPS_type=lps_type, zoom=False)
            
            ax = lps.ax
            
            # Plot each cyclone trajectory with transparency
            for i in range(len(all_x_data)):
                lps.plot_data(
                    x_axis=all_x_data[i],
                    y_axis=all_y_data[i],
                    marker_color=all_color_data[i],
                    marker_size=all_size_data[i],
                    alpha=0.3  # Low alpha for individual trajectories
                )
            
            # Set title
            lps_name = 'Conversion Phase Space (Ck vs Ca)' if lps_type == 'conversion' else 'Imports Phase Space (BAe vs BKe)'
            zoom_label = ' (Zoom)' if use_zoom_mode else ' (Default)'
            ax.set_title(
                f'EP{ep_id} - {lps_name}{zoom_label}\n{n_cyclones} cyclones',
                fontsize=12,
                fontweight='bold'
            )
            
            # Save figure
            output_filename = f"ep{ep_id}_lps_{lps_type}{zoom_suffix}.png"
            output_path = output_dir / output_filename
            plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            mode_desc = 'zoom' if use_zoom_mode else 'default'
            print(f"      ✓ {lps_type.capitalize()} ({mode_desc}): {output_filename}")


def main():
    """Main execution function."""
    
    figures_dir = Path(FIGURES_DIR)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Exploratory: LPS Diagrams by Energy Pattern")
    print("=" * 70)
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Figures directory: {figures_dir}")
    print()
    print("Energy Pattern definitions (by mean Ck):")
    print("  EP1: Lowest mean Ck  → Strongest baroclinic conversion")
    print("  EP2: Middle mean Ck  → Moderate baroclinic conversion")
    print("  EP3: Highest mean Ck → Weakest baroclinic conversion")
    print()
    print("Cluster to EP mapping:")
    for cluster_id, ep_id in sorted(CLUSTER_TO_EP.items()):
        print(f"  Cluster {cluster_id} → EP{ep_id}")
    print()
    
    # Load data
    df_merged, centroids_energy = load_data()
    
    # Assign Energy Patterns
    print("Assigning Energy Patterns...")
    df_merged = assign_energy_patterns(df_merged)
    
    # Display distribution
    print("\nEnergy Pattern distribution:")
    for ep_id in sorted(df_merged['energy_pattern'].unique()):
        count = (df_merged['energy_pattern'] == ep_id).sum()
        pct = 100 * count / len(df_merged)
        print(f"  EP{ep_id}: {count:4d} cyclones ({pct:5.1f}%)")
    
    # Create LPS diagrams for each EP
    print("\nCreating LPS diagrams...")
    for ep_id in sorted(df_merged['energy_pattern'].unique()):
        df_ep = df_merged[df_merged['energy_pattern'] == ep_id]
        plot_lps_for_ep(df_ep, ep_id, figures_dir, dpi=DPI)
    
    print()
    print("=" * 70)
    print("✅ Exploratory analysis complete!")
    print("=" * 70)
    print()
    print("Generated figures (12 total):")
    print("  For each EP (1, 2, 3):")
    print("    • Conversion LPS (default):  ep{id}_lps_conversion_default.png")
    print("    • Conversion LPS (zoom):     ep{id}_lps_conversion_zoom.png")
    print("    • Imports LPS (default): ep{id}_lps_imports_default.png")
    print("    • Imports LPS (zoom):    ep{id}_lps_imports_zoom.png")
    print()
    print(f"All figures saved in: {figures_dir}/")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
