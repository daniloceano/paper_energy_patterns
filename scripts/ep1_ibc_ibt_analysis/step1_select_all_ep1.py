"""
Step 1: Select ALL EP1 Cyclones for Full Analysis

This script selects ALL cyclones from Energy Pattern 1 (EP1) with complete lifecycle
for instability analysis during their entire intensification phase.

Differences from ep1_ibc_ibt_analysis/step1:
- NO spatial filtering (all EP1 cyclones regardless of location)
- Will analyze ALL time steps during intensification (not just central time)
- Larger sample size for comprehensive EP1 characterization

Selection Criteria:
- Belongs to EP1 (cluster 0)
- Complete lifecycle: incipient → intensification → mature → decay
- No spatial restrictions

Output:
- results/ep1_vertical/all_ep1_cases.csv: List of all EP1 cyclone track_ids

Author: Danilo Couto de Souza
Date: February 2026
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
from scripts.utils.load_data import load_tracks

# Configuration
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = Path(__file__).resolve().parents[2] / "figures" / "ep1_vertical" / "tracks"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
DPI = 300


def filter_complete_lifecycle_tracks(df):
    """
    Filter tracks with complete lifecycle in exact order:
    incipient → intensification → mature → decay
    
    Same logic as used in scripts/main/01_figure_tracks_genesis_frequency.py
    """
    complete_tracks = []
    
    for track_id, track_data in df.groupby('track_id'):
        # Get unique periods (dropping NaN) in order of appearance
        periods = track_data['period'].dropna().unique()
        
        # Check if lifecycle matches exactly
        if (len(periods) == 4 and
            periods[0] == 'incipient' and
            periods[1] == 'intensification' and
            periods[2] == 'mature' and
            periods[3] == 'decay'):
            complete_tracks.append(track_id)
    
    return complete_tracks


def get_intensification_info(track_id, tracks_df):
    """
    Get intensification phase information for a track.
    Returns (start_time, end_time, n_timesteps, center_lat, center_lon) or None if not found.
    """
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = lec_dir / "periods.csv" / "periods.csv"
    
    if not periods_file.exists():
        return None
    
    periods = pd.read_csv(periods_file, index_col=0)
    intensification = periods.loc['intensification']
    
    if len(intensification) == 0:
        return None
    
    start_time = pd.to_datetime(intensification['start'])
    end_time = pd.to_datetime(intensification['end'])
    
    # Get track data during intensification
    track_data = tracks_df[tracks_df['track_id'] == track_id].copy()
    track_data['time'] = pd.to_datetime(track_data['date'])
    track_intensification = track_data[
        (track_data['time'] >= start_time) & 
        (track_data['time'] <= end_time)
    ]
    
    if len(track_intensification) == 0:
        return None
    
    n_timesteps = len(track_intensification)
    
    # Temporal center point
    t_center = start_time + (end_time - start_time) / 2
    time_diffs = np.abs((track_intensification['time'] - t_center).dt.total_seconds())
    closest_idx = time_diffs.idxmin()
    
    center_lat = track_intensification.loc[closest_idx, 'lat vor']
    center_lon = track_intensification.loc[closest_idx, 'lon vor']
    
    return start_time, end_time, n_timesteps, center_lat, center_lon


def plot_all_ep1_tracks(selected_df, tracks_df):
    """
    Create overview map with all EP1 cyclone tracks.
    Shows complete tracks and highlights intensification phase.
    """
    print("   Creating track visualization...")
    
    fig = plt.figure(figsize=(14, 10))
    
    # Use South Polar Stereographic projection
    proj = ccrs.Stereographic(central_latitude=-90, central_longitude=0)
    ax = fig.add_subplot(111, projection=proj)
    
    # Set extent to show South Atlantic
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
        
        # Get track data
        track = tracks_df[tracks_df['track_id'] == track_id].copy()
        track = track.sort_values('date') if len(track) > 0 else pd.DataFrame()
        
        # Get intensification period
        lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
        periods_file = lec_dir / "periods.csv" / "periods.csv"
        
        if periods_file.exists() and len(track) > 0:
            periods = pd.read_csv(periods_file, index_col=0)
            intensification = periods.loc['intensification']
            t_start = pd.to_datetime(intensification['start'])
            t_end = pd.to_datetime(intensification['end'])
            
            track['date'] = pd.to_datetime(track['date'])
            track_intens = track[(track['date'] >= t_start) & (track['date'] <= t_end)]
            
            # Plot complete track (gray, thin line)
            ax.plot(track['lon vor'].values, track['lat vor'].values,
                   color='gray', linewidth=0.6, alpha=0.3,
                   transform=ccrs.PlateCarree(), zorder=2)
            
            # Plot intensification phase (yellow, medium line)
            if len(track_intens) > 0:
                ax.plot(track_intens['lon vor'].values, track_intens['lat vor'].values,
                       color='gold', linewidth=1.5, alpha=0.9,
                       transform=ccrs.PlateCarree(), zorder=3)

            
            # Mark genesis
            ax.plot(track['lon vor'].iloc[0], track['lat vor'].iloc[0],
                   'o', color='green', markersize=3, markeredgecolor='k',
                   markeredgewidth=0.3, transform=ccrs.PlateCarree(), zorder=4)
    
    # Create legend
    legend_elements = [
        Line2D([0], [0], color='gray', linewidth=1.5, alpha=0.5, label='Complete track'),
        Line2D([0], [0], color='gold', linewidth=2, alpha=0.9, label='Intensification'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
               markersize=6, markeredgecolor='k', label='Genesis')
    ]
    ax.legend(handles=legend_elements, loc='upper left', framealpha=0.95, fontsize=9)
    
    ax.set_title(f'All EP1 Cyclone Tracks (n={len(selected_df)})', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    out_path = FIGURES_DIR / 'all_ep1_tracks_overview.png'
    plt.savefig(out_path, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"   Saved: {out_path}")


def main():
    print("=" * 70)
    print("STEP 1: SELECT ALL EP1 CYCLONES FOR FULL ANALYSIS")
    print("=" * 70)
    
    # 1. Load cluster assignments
    print("\n1. Loading cluster assignments...")
    cluster_file = Path(__file__).resolve().parents[2] / "results" / "cluster" / "kmeans_clustered_data.csv"
    
    if not cluster_file.exists():
        raise FileNotFoundError(f"Cluster file not found: {cluster_file}")
    
    clustered_df = pd.read_csv(cluster_file)
    ep1_cyclones = clustered_df[clustered_df['cluster'] == 0].copy()
    print(f"   Total EP1 cyclones (cluster 0): {len(ep1_cyclones)}")
    
    # 2. Load tracks
    print("\n2. Loading track data...")
    tracks_df = load_tracks()
    print(f"   Total tracks: {tracks_df['track_id'].nunique()}")
    
    # 3. Filter tracks to only EP1 cyclones
    print("\n3. Filtering for EP1 cyclones...")
    ep1_track_ids = ep1_cyclones['track_id'].unique()
    ep1_tracks = tracks_df[tracks_df['track_id'].isin(ep1_track_ids)].copy()
    print(f"   EP1 tracks in database: {ep1_tracks['track_id'].nunique()}")
    
    # 4. Filter complete lifecycle
    print("\n4. Filtering complete lifecycle tracks...")
    complete_ids = filter_complete_lifecycle_tracks(ep1_tracks)
    print(f"   Complete lifecycle tracks: {len(complete_ids)}")
    
    # 5. Get intensification info for all tracks
    print("\n5. Extracting intensification phase information...")
    selected_cases = []
    
    for track_id in complete_ids:
        info = get_intensification_info(track_id, tracks_df)
        if info is not None:
            start_time, end_time, n_timesteps, center_lat, center_lon = info
            selected_cases.append({
                'track_id': track_id,
                'intensification_start': start_time,
                'intensification_end': end_time,
                'n_timesteps': n_timesteps,
                'center_lat': center_lat,
                'center_lon': center_lon,
                'duration_hours': (end_time - start_time).total_seconds() / 3600
            })
    
    selected_df = pd.DataFrame(selected_cases)
    print(f"   Valid cases with intensification data: {len(selected_df)}")
    
    # 6. Save results
    print("\n6. Saving results...")
    out_csv = OUTPUT_DIR / "all_ep1_cases.csv"
    selected_df.to_csv(out_csv, index=False)
    print(f"   Saved: {out_csv}")
    
    # 7. Print statistics
    print("\n7. Dataset Statistics:")
    print(f"   Total cases: {len(selected_df)}")
    print(f"   Mean timesteps per case: {selected_df['n_timesteps'].mean():.1f}")
    print(f"   Total timesteps: {selected_df['n_timesteps'].sum()}")
    print(f"   Mean duration: {selected_df['duration_hours'].mean():.1f} hours")
    print(f"   Lat range: [{selected_df['center_lat'].min():.1f}, {selected_df['center_lat'].max():.1f}]")
    print(f"   Lon range: [{selected_df['center_lon'].min():.1f}, {selected_df['center_lon'].max():.1f}]")
    
    # 8. Create visualization
    plot_all_ep1_tracks(selected_df, tracks_df)
    
    print("\n" + "=" * 70)
    print("STEP 1 COMPLETE")
    print("=" * 70)
    print(f"\nNext step: python scripts/ep1_vertical_analysis/step2_download_era5_parallel.py")


if __name__ == '__main__':
    main()
