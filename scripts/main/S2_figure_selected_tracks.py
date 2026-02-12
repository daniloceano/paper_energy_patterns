#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S2: Selected EP1 Cyclones for Instability Analysis

This script creates a map showing the subset of EP1 cyclones selected for 
detailed instability diagnostics (Rayleigh–Kuo, Potential Vorticity, Eady Growth Rate).

Selection Criteria:
  • Belongs to Energy Pattern 1 (cluster 0)
  • Complete lifecycle: incipient → intensification → mature → decay
  • Intensification center (temporal midpoint) within selection domain
  • Domain: 60°W–45°W, 45°S–30°S

The figure shows:
  • Complete cyclone tracks (gray lines)
  • Intensification phase segments (gold, thick lines)
  • Analysis centers (red stars) - temporal center of intensification
  • Genesis locations (green circles)
  • Selection domain box (blue)

IMPORTANT: This script requires results from the EP1 instability analysis pipeline:
  • Must run: scripts/ep1_ibc_ibt_analysis/step1_select_cases.py first
  • Input: results/ep1_vertical/selected_cases.csv
  • LEC data: data/temp_lec_zenodo/LEC_Results_energetic-patterns/

Outputs:
  • Figure: figures/main/S2_selected_tracks.png (300 DPI)

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

from scripts.utils.load_data import load_tracks

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results' / 'ep1_vertical'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

# Selection domain (used in step1_select_cases.py)
DOMAIN_LON_MIN, DOMAIN_LON_MAX = -60, -45
DOMAIN_LAT_MIN, DOMAIN_LAT_MAX = -45, -30

# Figure settings
FIG_WIDTH = 12
FIG_HEIGHT = 8
DPI = 300

plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 14,
    'figure.titlesize': 14,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
})

# ============================================================================
# Load Data
# ============================================================================

def load_selected_cases():
    """Load selected EP1 cases from step1 results."""
    selected_file = RESULTS_DIR / "selected_cases.csv"
    
    if not selected_file.exists():
        raise FileNotFoundError(
            f"Selected cases file not found: {selected_file}\n"
            "Please run scripts/ep1_ibc_ibt_analysis/step1_select_cases.py first"
        )
    
    return pd.read_csv(selected_file)


# ============================================================================
# Main Figure Generation
# ============================================================================

def plot_selected_tracks(selected_df, tracks_df):
    """
    Create overview map with all selected cyclone tracks.
    Shows complete tracks and highlights intensification phase.
    """
    print("\nCreating Figure S2: Selected EP1 Cyclones...")
    
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    
    # Use South Polar Stereographic projection
    proj = ccrs.Stereographic(central_latitude=-90, central_longitude=0)
    ax = fig.add_subplot(111, projection=proj)
    
    # Set extent to show tracks in South Atlantic
    ax.set_extent([-80, 40, -70, -20], crs=ccrs.PlateCarree())
    
    # Add map features
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax.add_feature(cfeature.OCEAN, facecolor='white')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='black')
    
    # Add gridlines with labels
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', alpha=0.7,
                     color='gray', x_inline=False, y_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}
    
    # Plot each selected track
    for idx, (_, case) in enumerate(selected_df.iterrows()):
        track_id = case['track_id']
        
        # Try to get track data from main database
        track = tracks_df[tracks_df['track_id'] == track_id].copy()
        track = track.sort_values('date') if len(track) > 0 else pd.DataFrame()
        
        # Get metadata for intensification period
        lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
        periods_file = lec_dir / "periods.csv" / "periods.csv"
        
        if periods_file.exists():
            periods = pd.read_csv(periods_file, index_col=0)
            intensification = periods.loc['intensification']
            t_start = pd.to_datetime(intensification['start'])
            t_end = pd.to_datetime(intensification['end'])
            
            if len(track) > 0:
                # Ensure date column is datetime
                track['date'] = pd.to_datetime(track['date'])
                track_intens = track[(track['date'] >= t_start) & (track['date'] <= t_end)]
                
                # Plot complete track (gray, thin line)
                ax.plot(track['lon vor'].values, track['lat vor'].values,
                       color='gray', linewidth=0.8, alpha=0.4,
                       transform=ccrs.PlateCarree(), zorder=2)
                
                # Plot intensification phase (gold, thick line)
                if len(track_intens) > 0:
                    ax.plot(track_intens['lon vor'].values, track_intens['lat vor'].values,
                           color='gold', linewidth=2.5, alpha=0.9,
                           transform=ccrs.PlateCarree(), zorder=3,
                           label=f'{track_id}')
                    
                    # Mark intensification center (temporal center - actual track point)
                    # Find point closest to temporal midpoint (same as selection criterion)
                    t_center = t_start + (t_end - t_start) / 2
                    time_diffs = np.abs((track_intens['date'] - t_center).dt.total_seconds())
                    closest_idx = time_diffs.idxmin()
                    center_lat = track_intens.loc[closest_idx, 'lat vor']
                    center_lon = track_intens.loc[closest_idx, 'lon vor']
                    ax.plot(center_lon, center_lat, 'r*', markersize=10,
                           markeredgecolor='k', markeredgewidth=0.8,
                           transform=ccrs.PlateCarree(), zorder=5)
                
                # Mark genesis
                ax.plot(track['lon vor'].iloc[0], track['lat vor'].iloc[0],
                       'o', color='green', markersize=5, markeredgecolor='k',
                       markeredgewidth=0.5, transform=ccrs.PlateCarree(), zorder=4)
    
    # Draw domain box
    domain_lons = [DOMAIN_LON_MIN, DOMAIN_LON_MAX, DOMAIN_LON_MAX, DOMAIN_LON_MIN, DOMAIN_LON_MIN]
    domain_lats = [DOMAIN_LAT_MIN, DOMAIN_LAT_MIN, DOMAIN_LAT_MAX, DOMAIN_LAT_MAX, DOMAIN_LAT_MIN]
    ax.plot(domain_lons, domain_lats, 'b-', linewidth=2.5, alpha=0.8,
           transform=ccrs.PlateCarree(), zorder=10, label='Selection domain')
    
    # Create custom legend
    legend_elements = [
        Line2D([0], [0], color='gray', linewidth=1.5, alpha=0.6, label='Complete track'),
        Line2D([0], [0], color='gold', linewidth=2.5, label='Intensification phase'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='r', 
               markersize=10, markeredgecolor='k', label='Analysis center'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
               markersize=6, markeredgecolor='k', label='Genesis'),
        Line2D([0], [0], color='b', linewidth=2.5, 
               label=f'Selection domain\n({DOMAIN_LON_MIN}°W–{-DOMAIN_LON_MAX}°W, {DOMAIN_LAT_MIN}°S–{-DOMAIN_LAT_MAX}°S)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=12, framealpha=0.95)
    
    n_cyclones = len(selected_df)
    # ax.set_title(
    #     f'Selected EP1 Cyclones for Instability Analysis (n={n_cyclones})\n'
    #     f'Intensification center in domain: {DOMAIN_LON_MIN}°W–{-DOMAIN_LON_MAX}°W, {DOMAIN_LAT_MIN}°S–{-DOMAIN_LAT_MAX}°S',
    #     fontsize=13, fontweight='bold', pad=15
    # )
    
    # Save
    output_file = FIGURES_DIR / "S2_selected_tracks.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Figure saved: {output_file}")
    print(f"  • Selected cyclones: {n_cyclones}")
    print(f"  • Selection domain: {DOMAIN_LON_MIN}°W–{-DOMAIN_LON_MAX}°W, {DOMAIN_LAT_MIN}°S–{-DOMAIN_LAT_MAX}°S")
    
    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate Figure S2: Selected EP1 Cyclones for Instability Analysis."""
    
    print("=" * 80)
    print("Figure S2: Selected EP1 Cyclones for Instability Analysis")
    print("=" * 80)
    
    # Load selected cases
    print("\n1. Loading selected cases from step1 results...")
    selected_df = load_selected_cases()
    print(f"   Found {len(selected_df)} selected EP1 cyclones")
    
    # Load full track data
    print("\n2. Loading complete track data...")
    tracks = load_tracks()
    print(f"   Loaded {tracks['track_id'].nunique()} cyclone tracks")
    
    # Create figure
    print("\n3. Generating figure...")
    output_file = plot_selected_tracks(selected_df, tracks)
    
    print("\n" + "=" * 80)
    print("✅ Figure S2 generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
