#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploratory: Three Most Intense Cyclones - Individual LPS and Track Figures

Creates individual figures for each of the three most intense cyclones:
- LPS Conversion (Ck vs Ca) - using lorenz-phase-space
- LPS Imports (BAe vs BKe) - using lorenz-phase-space
- Track map with relative vorticity (color) and Ke (marker size)

Each cyclone gets 3 separate figures saved in dedicated folder.

Author: Danilo Couto de Souza
Date: January 2026

Modifications:
- February 2026: Increased label and title font sizes for improved
    readability; increased colorbar and legend font sizes and label padding.
    These edits ensure LPS and track figures are clearer for publication.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    from lorenz_phase_space.phase_diagrams import Visualizer
    HAS_LPS = True
except ImportError:
    HAS_LPS = False
    print("ERROR: lorenz-phase-space not installed")
    print("Install with: pip install lorenz-phase-space")

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
FIGURES_DIR = BASE_DIR / 'figures' / 'exploratory' / 'three_most_intense_cyclones_zoom'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Data sources
DATA_URL = "https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv"
PROCESSED_DATA = BASE_DIR / 'data' / 'tracks_SAt_filtered_with_energetics_processed.csv'

# Figure settings
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
})

# ============================================================================
# Load Data
# ============================================================================

def load_data():
    """Load cyclone tracks and energetics from Zenodo."""
    print("Loading data from Zenodo...")
    print(f"URL: {DATA_URL}")
    # Prefer a preprocessed local CSV for speed. If missing, instruct user
    if PROCESSED_DATA.exists():
        print(f"Loading processed data: {PROCESSED_DATA}")
        df = pd.read_csv(PROCESSED_DATA)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        print(f"✓ Loaded {len(df)} records from processed file")
        print(f"✓ {df['track_id'].nunique()} unique cyclones")
        return df

    msg = (
        "Processed data not found. Run the extractor to create it:\n"
        "python scripts/analysis/extract_tracks_from_zenodo.py"
    )
    raise FileNotFoundError(msg)

def find_most_intense_cyclones(df, n=3):
    """Find n cyclones with maximum vorticity."""
    print(f"\nFinding {n} most intense cyclones...")
    
    # Get maximum vorticity per cyclone
    max_vor = df.groupby('track_id')['vor42'].max().sort_values(ascending=False)
    
    most_intense_ids = max_vor.index[:n].tolist()
    
    tracks = []
    for i, track_id in enumerate(most_intense_ids, 1):
        max_vorticity = max_vor.loc[track_id]
        print(f"  {i}. {track_id}: {max_vorticity:.2f} × 10⁻⁵ s⁻¹")
        
        # Get full track
        track = df[df['track_id'] == track_id].copy()
        track = track.sort_values('date')
        
        tracks.append(track)
    
    return tracks, most_intense_ids

def prepare_lps_data(track):
    """Prepare data for LPS plotting."""
    # Filter to times with energy data (not NaN)
    energy_track = track.dropna(subset=['Ck', 'Ca', 'BAe', 'BKe', 'Ge', 'Ke']).copy()

    # Slice for data each 6 hours (to reduce overplotting)
    energy_track = energy_track.iloc[::2].copy()
    
    if len(energy_track) == 0:
        raise ValueError("No valid energy data for this cyclone")
    
    return energy_track

# ============================================================================
# Plotting Functions
# ============================================================================

def standardize_lps_plot(lps,
                         title=None,
                         xlabel_fontsize=18,
                         ylabel_fontsize=18,
                         tick_fontsize=14,
                         title_fontsize=18,
                         labelpad=10,
                         cbar_labelsize=16,
                         cbar_labelpad=25,
                         legend_fontsize=16):
    """Apply consistent styling to a lorenz-phase-space `Visualizer` plot.

    Parameters
    ----------
    lps : Visualizer
        Instance returned by `lorenz_phase_space.phase_diagrams.Visualizer`.
    title : str, optional
        Title to set on the axes. If None, title is not changed.
    Other keyword args : int
        Font sizes and paddings for labels, ticks, colorbar and legend.
    """
    ax = lps.ax

    # Ticks
    ax.tick_params(axis='both', which='major', labelsize=tick_fontsize)

    # Axis labels (preserve existing text)
    xlab = ax.get_xlabel()
    ylab = ax.get_ylabel()
    if xlab:
        ax.set_xlabel(xlab, fontsize=xlabel_fontsize, labelpad=labelpad)
    if ylab:
        ax.set_ylabel(ylab, fontsize=ylabel_fontsize, labelpad=labelpad)

    # Colorbar adjustments
    cbar = getattr(lps, 'cbar', None)
    if cbar is not None:
        try:
            for t in cbar.ax.get_yticklabels():
                t.set_fontsize(tick_fontsize)
            cb_text = cbar.ax.get_ylabel()
            cbar.set_label(cb_text if cb_text else ' ', fontsize=cbar_labelsize, labelpad=cbar_labelpad)
        except Exception:
            pass

    # Legend text sizes
    leg = ax.get_legend()
    if leg is not None:
        try:
            for t in leg.get_texts():
                t.set_fontsize(legend_fontsize)
            title_obj = leg.get_title()
            if title_obj is not None:
                title_obj.set_fontsize(legend_fontsize)
        except Exception:
            pass

    # Title (optional)
    if title is not None:
        ax.set_title(title, fontsize=title_fontsize, fontweight='bold', pad=12)


def plot_lps_conversion(track_id, energy_data, output_dir):
    """Create LPS Conversion diagram using lorenz-phase-space."""
    if not HAS_LPS:
        return
    
    print(f"    Creating Conversion LPS...")
    
    # Create Visualizer
    lps = Visualizer(LPS_type='conversion', zoom=True)
    
    # Plot data
    lps.plot_data(
        x_axis=energy_data['Ck'].values,
        y_axis=energy_data['Ca'].values,
        marker_color=energy_data['Ge'].values,
        marker_size=energy_data['Ke'].values,
        alpha=0.9
    )
    
    # Apply standardized styling (labels, ticks, colorbar, legend, title)
    standardize_lps_plot(
        lps,
        title=f'Cyclone {track_id} - Conversion Phase Space',
    )
    
    # Save
    output_file = output_dir / f'{track_id}_lps_conversion_zoom.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(lps.fig)
    
    print(f"      ✓ Saved: {output_file.name}")

def plot_lps_imports(track_id, energy_data, output_dir):
    """Create LPS Imports diagram using lorenz-phase-space."""
    if not HAS_LPS:
        return
    
    print(f"    Creating Imports LPS...")
    
    # Create Visualizer
    lps = Visualizer(LPS_type='imports', zoom=True)
    
    # Plot data
    lps.plot_data(
        x_axis=energy_data['BAe'].values,
        y_axis=energy_data['BKe'].values,
        marker_color=energy_data['Ge'].values,
        marker_size=energy_data['Ke'].values,
        alpha=0.9
    )
    
    # Apply standardized styling (labels, ticks, colorbar, legend, title)
    standardize_lps_plot(
        lps,
        title=f'Cyclone {track_id} - Imports Phase Space',
        )
    
    # Save
    output_file = output_dir / f'{track_id}_lps_imports_zoom.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(lps.fig)
    
    print(f"      ✓ Saved: {output_file.name}")

def plot_track_map(track_id, track, output_dir):
    """Create track map with Ae (color) and Ke (size)."""
    print(f"    Creating Track map...")
    
    # Create figure
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Get track bounds with padding
    lon_min = track['lon vor'].min() - 5
    lon_max = track['lon vor'].max() + 5
    lat_min = track['lat vor'].min() - 5
    lat_max = track['lat vor'].max() + 5
    
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
    
    # Add features
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':')
    
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False,
                     linewidth=0.5, alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    # Subsample track to Ke temporal resolution (select rows where Ke is present)
    track = track.sort_values('date').copy()

    # Fill vorticity for sampling purposes, but do NOT fill Ke (we want actual 3h values)
    track['vor42'] = track['vor42'].fillna(method='ffill').fillna(method='bfill')

    subsampled = track[track['Ke'].notna()].copy()
    # Fallback: if no Ke timestamps found, sample every 3rd row
    if subsampled.empty:
        subsampled = track.iloc[::3].copy()

    # Extract variables from subsampled (3h) track
    lons = subsampled['lon vor'].values
    lats = subsampled['lat vor'].values
    vor = subsampled['vor42'].values
    ke = subsampled['Ke'].values

    # Normalize sizes (30-300 points) using Ke
    ke_min, ke_max = np.nanmin(ke), np.nanmax(ke)
    sizes = 30 + 270 * (ke - ke_min) / (ke_max - ke_min + 1e-10)
    
    # Plot track line
    ax.plot(lons, lats, 'k-', linewidth=2, alpha=0.7, 
           transform=ccrs.PlateCarree(), zorder=1)
    
    # Plot points (color = vorticity, colormap = YlOrRd)
    scatter = ax.scatter(lons, lats, c=vor, s=sizes, cmap='YlOrRd',
                        vmin=np.nanmin(vor), vmax=np.nanmax(vor),
                        edgecolors='black', linewidths=0.8, alpha=0.9,
                        transform=ccrs.PlateCarree(), zorder=2)
    
    # Mark start/end
    ax.scatter(lons[0], lats[0], s=300, marker='o', c='limegreen',
              edgecolors='black', linewidths=2.5, label='Genesis',
              transform=ccrs.PlateCarree(), zorder=3)
    ax.scatter(lons[-1], lats[-1], s=300, marker='X', c='red',
              edgecolors='black', linewidths=2.5, label='Lysis',
              transform=ccrs.PlateCarree(), zorder=3)
    
    # Add colorbar for vorticity
    cbar = plt.colorbar(scatter, ax=ax, orientation='horizontal', 
                       pad=0.08, aspect=40, shrink=0.8)
    cbar.set_label('Vorticity (-1 $\\times$ 10$^{-5}$ s$^{-1}$)', 
                  fontsize=11, fontweight='bold')
    
    # Add combined legend: size (Ke) entries + genesis/lysis markers in one box
    legend_elements = []
    ke_values = [ke_min, (ke_min + ke_max) / 2, ke_max]
    size_values = [30, 165, 300]

    for ke_val, size in zip(ke_values, size_values):
        legend_elements.append(plt.scatter([], [], s=size, c='gray', 
                                          edgecolors='black', linewidths=0.8,
                                          label=f'Ke={ke_val/1e5:.1f}'))

    # Proxies for genesis and lysis markers
    genesis_proxy = plt.Line2D([], [], marker='o', color='w', markerfacecolor='limegreen',
                               markeredgecolor='black', markeredgewidth=0.8, markersize=10,
                               linestyle='None', label='Genesis')
    lysis_proxy = plt.Line2D([], [], marker='X', color='w', markerfacecolor='red',
                             markeredgecolor='black', markeredgewidth=0.8, markersize=10,
                             linestyle='None', label='Lysis')

    all_handles = legend_elements + [genesis_proxy, lysis_proxy]

    # Add legend (Ke in 10$^5$ J m$^{-2}$)
    ax.legend(handles=all_handles,
              loc='lower left', framealpha=0.95, edgecolor='black', fontsize=12,
              labelspacing=1.4, handletextpad=0.6, markerscale=1.0)
    
    # Title
    ax.set_title(f'Cyclone {track_id} - Track', 
                fontsize=13, fontweight='bold', pad=10)
    
    # Save
    output_file = output_dir / f'{track_id}_track.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"      ✓ Saved: {output_file.name}")

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function."""
    
    print("=" * 70)
    print("Three Most Intense Cyclones - Individual Figures")
    print("=" * 70)
    print(f"Output directory: {FIGURES_DIR}")
    print()
    
    if not HAS_LPS:
        print("ERROR: Cannot proceed without lorenz-phase-space")
        return 1
    
    # Load data
    df = load_data()
    
    # Find three most intense cyclones
    tracks, track_ids = find_most_intense_cyclones(df, n=3)
    
    # Process each cyclone
    print("\nCreating figures for each cyclone...")
    for track_id, track in zip(track_ids, tracks):
        print(f"\n  Processing {track_id}...")
        
        # Prepare energy data
        energy_data = prepare_lps_data(track)
        print(f"    Energy records: {len(energy_data)}")
        
        # Create all three figures
        plot_lps_conversion(track_id, energy_data, FIGURES_DIR)
        plot_lps_imports(track_id, energy_data, FIGURES_DIR)
        plot_track_map(track_id, track, FIGURES_DIR)
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated {len(track_ids) * 3} figures in: {FIGURES_DIR}")
    print(f"Cyclones: {', '.join(map(str, track_ids))}")
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
