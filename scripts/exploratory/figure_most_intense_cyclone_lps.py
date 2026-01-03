#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: Three Most Intense Cyclones - LPS Diagrams and Tracks

Creates a publication-ready 3x3 panel figure with:
- Column 1: Mixed LPS (Ck vs Ca)
- Column 2: Imports LPS (BAe vs BKe)  
- Column 3: Cyclone track map

Each row represents one of the three most intense cyclones.

Track visualization:
- Circle markers at each time step
- Color: vorticity (vor42)
- Size: eddy kinetic energy (Ke)

Author: Danilo Couto de Souza
Date: January 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
FIGURES_DIR = BASE_DIR / 'figures' / 'exploratory'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Data URL
DATA_URL = "https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv"

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
    
    df = pd.read_csv(DATA_URL)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"✓ Loaded {len(df)} records")
    print(f"✓ {df['track_id'].nunique()} unique cyclones")
    print(f"✓ Period: {df['date'].min()} to {df['date'].max()}")
    
    return df

def find_most_intense_cyclones(df, n=3):
    """Find n cyclones with maximum vorticity."""
    print(f"\nFinding {n} most intense cyclones...")
    
    # Get maximum vorticity per cyclone
    max_vor = df.groupby('track_id')['vor42'].max().sort_values(ascending=False)
    
    most_intense_ids = max_vor.index[:n].tolist()
    
    tracks = []
    for i, track_id in enumerate(most_intense_ids, 1):
        max_vorticity = max_vor.loc[track_id]
        print(f"\n  {i}. Cyclone: {track_id}")
        print(f"     Maximum vorticity: {max_vorticity:.2f} × 10⁻⁵ s⁻¹")
        
        # Get full track
        track = df[df['track_id'] == track_id].copy()
        track = track.sort_values('date')
        
        print(f"     Track length: {len(track)} time steps")
        print(f"     Duration: {(track['date'].max() - track['date'].min()).total_seconds() / 3600:.1f} hours")
        
        # Show phase distribution
        if 'period' in track.columns:
            print(f"     Phases: {track['period'].value_counts().to_dict()}")
        
        tracks.append(track)
    
    return tracks, most_intense_ids

def prepare_lps_data(track):
    """Prepare data for LPS plotting (using energy records only)."""
    print("\nPreparing LPS data...")
    
    # Filter to times with energy data (not NaN)
    energy_track = track.dropna(subset=['Ck', 'Ca', 'BAe', 'BKe', 'Ge', 'Ke']).copy()
    
    print(f"✓ Energy records: {len(energy_track)} (from {len(track)} total)")
    
    if len(energy_track) == 0:
        raise ValueError("No valid energy data for this cyclone")
    
    # Extract LPS variables
    lps_data = {
        'mixed': {
            'x': energy_track['Ck'].values,
            'y': energy_track['Ca'].values,
            'color': energy_track['Ge'].values,
            'size': energy_track['Ke'].values
        },
        'imports': {
            'x': energy_track['BAe'].values,
            'y': energy_track['BKe'].values,
            'color': energy_track['Ge'].values,
            'size': energy_track['Ke'].values
        }
    }
    
    return lps_data

# ============================================================================
# Plotting Functions
# ============================================================================

def plot_lps_panel(ax, lps_data, lps_type, track_id, panel_label):
    """Plot LPS diagram on given axis."""
    
    # Extract data
    x = lps_data[lps_type]['x']
    y = lps_data[lps_type]['y']
    c = lps_data[lps_type]['color']
    s = lps_data[lps_type]['size']
    
    # Auto-adjust limits based on data with padding
    x_pad = (x.max() - x.min()) * 0.1
    y_pad = (y.max() - y.min()) * 0.1
    ax.set_xlim(x.min() - x_pad, x.max() + x_pad)
    ax.set_ylim(y.min() - y_pad, y.max() + y_pad)
    
    # Set labels
    if lps_type == 'mixed':
        ax.set_xlabel('Ck (W m$^{-2}$)', fontsize=9)
        ax.set_ylabel('Ca (W m$^{-2}$)', fontsize=9)
    else:  # imports
        ax.set_xlabel('BAe (W m$^{-2}$)', fontsize=9)
        ax.set_ylabel('BKe (W m$^{-2}$)', fontsize=9)
    
    # Draw reference lines
    ax.axhline(0, color='black', linewidth=1, zorder=0)
    ax.axvline(0, color='black', linewidth=1, zorder=0)
    ax.grid(True, alpha=0.3, linestyle='--', zorder=0)
    
    # Normalize sizes for plotting (20-120 points)
    s_norm = 20 + 100 * (s - s.min()) / (s.max() - s.min() + 1e-10)
    
    # Plot trajectory
    ax.plot(x, y, 'k-', linewidth=1.5, alpha=0.6, zorder=1)
    
    # Plot points
    scatter = ax.scatter(x, y, c=c, s=s_norm, cmap='RdBu_r', 
                        vmin=-30, vmax=30, edgecolors='black', 
                        linewidths=0.6, alpha=0.9, zorder=2)
    
    # Mark start and end
    ax.scatter(x[0], y[0], s=120, marker='o', c='limegreen', 
              edgecolors='black', linewidths=1.5, zorder=3)
    ax.scatter(x[-1], y[-1], s=120, marker='X', c='red', 
              edgecolors='black', linewidths=1.5, zorder=3)
    
    # Panel label in upper right
    ax.text(0.98, 0.98, panel_label, transform=ax.transAxes,
           fontsize=11, fontweight='bold', va='top', ha='right',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                    edgecolor='black', linewidth=1))
    
    return scatter, s

def plot_track_map(ax, track, panel_label):
    """Plot cyclone track on map."""
    
    # Get track bounds with padding
    lon_min, lon_max = track['lon vor'].min() - 3, track['lon vor'].max() + 3
    lat_min, lat_max = track['lat vor'].min() - 3, track['lat vor'].max() + 3
    
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
    
    # Add features
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':')
    
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False,
                     linewidth=0.5, alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    # Extract variables
    lons = track['lon vor'].values
    lats = track['lat vor'].values
    vor = track['vor42'].values
    
    # Ke might have NaN at 1h/2h intervals, use forward fill
    ke = track['Ke'].fillna(method='ffill').fillna(method='bfill').values
    
    # Normalize sizes (15-120 points)
    sizes = 15 + 105 * (ke - np.nanmin(ke)) / (np.nanmax(ke) - np.nanmin(ke) + 1e-10)
    
    # Plot track line
    ax.plot(lons, lats, 'k-', linewidth=1.2, alpha=0.6, 
           transform=ccrs.PlateCarree(), zorder=1)
    
    # Plot points
    scatter = ax.scatter(lons, lats, c=vor, s=sizes, cmap='YlOrRd',
                        vmin=vor.min(), vmax=vor.max(),
                        edgecolors='black', linewidths=0.5, alpha=0.8,
                        transform=ccrs.PlateCarree(), zorder=2)
    
    # Mark start/end
    ax.scatter(lons[0], lats[0], s=100, marker='o', c='green',
              edgecolors='black', linewidths=1.5,
              transform=ccrs.PlateCarree(), zorder=3)
    ax.scatter(lons[-1], lats[-1], s=100, marker='X', c='red',
              edgecolors='black', linewidths=1.5,
              transform=ccrs.PlateCarree(), zorder=3)
    
    # Panel label in upper right
    ax.text(0.98, 0.98, panel_label, transform=ax.transAxes,
           fontsize=11, fontweight='bold', va='top', ha='right',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                    edgecolor='black', linewidth=1))
    
    return scatter, vor, ke

# ============================================================================
# Main Figure Creation
# ============================================================================

def create_figure():
    """Create the complete 3x3 panel figure."""
    
    # Load data
    df = load_data()
    
    # Find three most intense cyclones
    tracks, track_ids = find_most_intense_cyclones(df, n=3)
    
    # Create figure with 3x3 grid
    print("\nCreating 3x3 panel figure...")
    fig = plt.figure(figsize=(18, 15))
    
    # Create grid spec
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3,
                         left=0.05, right=0.95, top=0.96, bottom=0.06)
    
    # Panel labels
    labels = [
        ['(a)', '(b)', '(c)'],
        ['(d)', '(e)', '(f)'],
        ['(g)', '(h)', '(i)']
    ]
    
    # Storage for creating shared colorbars
    all_scatter_ge = []
    all_scatter_vor = []
    all_ke_values = []
    
    # Plot each cyclone (row)
    for row, (track, track_id) in enumerate(zip(tracks, track_ids)):
        print(f"\n  Processing cyclone {row+1}/3: {track_id}")
        
        # Prepare LPS data
        lps_data = prepare_lps_data(track)
        
        # Column 1: Mixed LPS
        ax_mixed = fig.add_subplot(gs[row, 0])
        scatter_ge, ke_vals = plot_lps_panel(ax_mixed, lps_data, 'mixed', 
                                             track_id, labels[row][0])
        all_scatter_ge.append(scatter_ge)
        all_ke_values.extend(ke_vals)
        
        # Column 2: Imports LPS
        ax_imports = fig.add_subplot(gs[row, 1])
        plot_lps_panel(ax_imports, lps_data, 'imports', 
                      track_id, labels[row][1])
        
        # Column 3: Track map
        ax_map = fig.add_subplot(gs[row, 2], projection=ccrs.PlateCarree())
        scatter_vor, vor_vals, ke_vals_map = plot_track_map(ax_map, track, labels[row][2])
        all_scatter_vor.append(scatter_vor)
    
    # Add shared colorbars and legends
    print("\n  Adding colorbars and legends...")
    
    # Colorbar for Ge (below middle column)
    cbar_ge_ax = fig.add_axes([0.38, 0.02, 0.25, 0.01])
    cbar_ge = fig.colorbar(all_scatter_ge[0], cax=cbar_ge_ax, 
                          orientation='horizontal')
    cbar_ge.set_label('Generation of Eddy APE (Ge - W m$^{-2}$)', 
                     fontsize=10, fontweight='bold')
    
    # Legend for Ke (marker size) - below left column
    legend_ax = fig.add_axes([0.05, 0.02, 0.25, 0.02])
    legend_ax.axis('off')
    
    # Create size legend with representative values
    ke_min, ke_max = np.min(all_ke_values), np.max(all_ke_values)
    ke_range = [ke_min, (ke_min + ke_max) / 2, ke_max]
    size_range = [20, 60, 100]
    
    for i, (ke_val, size) in enumerate(zip(ke_range, size_range)):
        legend_ax.scatter([0.2 + i*0.3], [0.5], s=size, c='gray', 
                         edgecolors='black', linewidths=0.8)
        legend_ax.text(0.2 + i*0.3, 0.1, f'{ke_val/1e5:.1f}', 
                      ha='center', va='top', fontsize=8)
    
    legend_ax.text(0.5, 0.9, 'Eddy Kinetic Energy (Ke - 10$^5$ J m$^{-2}$)', 
                  ha='center', va='top', fontsize=10, fontweight='bold')
    
    # Save figure
    output_file = FIGURES_DIR / 'three_most_intense_cyclones_lps_tracks.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Figure saved: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    plt.close()
    
    return track_ids

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("CREATING FIGURE: Three Most Intense Cyclones - LPS and Tracks")
    print("=" * 70)
    
    track_ids = create_figure()
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"\nCyclones plotted: {', '.join(map(str, track_ids))}")
