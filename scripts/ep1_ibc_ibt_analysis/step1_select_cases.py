"""
Step 1: Select EP1 Cyclones for Instability Analysis

This script selects cyclones from Energy Pattern 1 (EP1) that satisfy
spatial criteria for detailed vertical structure and instability analysis.

Selection Criteria:
- Belongs to EP1 (cluster 0)
- Complete lifecycle: incipient → intensification → mature → decay
- Intensification center (temporal midpoint) within specified domain
- Domain ensures environmental homogeneity for instability diagnostics

Current Domain: 60°W-45°W, 45°S-30°S
- Ensures cyclones develop in similar large-scale environments
- Avoids mixing different synoptic regimes
- Guarantees data quality for RK criterion and EGR analysis

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
from scripts.utils.load_data import load_tracks

# Configuration
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = Path(__file__).resolve().parents[2] / "figures" / "ep1_vertical" / "tracks"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1"
DPI = 300


def get_intensification_center(track_id, tracks_df):
    """
    Get the latitude and longitude at the temporal center of the intensification phase.
    Returns the actual track point closest to the temporal midpoint (t_center).
    Returns (lat, lon) tuple or (None, None) if intensification phase not found.
    """
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = lec_dir / "periods.csv" / "periods.csv"
    
    if not periods_file.exists():
        return None, None
    
    periods = pd.read_csv(periods_file, index_col=0)
    intensification = periods.loc['intensification']
    
    if len(intensification) == 0:
        return None, None
    
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
        return None, None
    
    # Find actual track point closest to temporal center
    t_center = start_time + (end_time - start_time) / 2
    time_diffs = np.abs((track_intensification['time'] - t_center).dt.total_seconds())
    closest_idx = time_diffs.idxmin()
    
    center_lat = track_intensification.loc[closest_idx, 'lat vor']
    center_lon = track_intensification.loc[closest_idx, 'lon vor']
    return center_lat, center_lon


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


def plot_selected_tracks(selected_df, tracks_df, domain_lon_min, domain_lon_max, domain_lat_min, domain_lat_max):
    """
    Create overview map with all selected cyclone tracks.
    Shows complete tracks and highlights intensification phase.
    """
    print("\n6. Creating track visualization...")
    
    fig = plt.figure(figsize=(12, 8))
    
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
    
    # Draw domain box (60°W-30°W, 30°S-60°S)
    domain_lons = [domain_lon_min, domain_lon_max, domain_lon_max, domain_lon_min, domain_lon_min]
    domain_lats = [domain_lat_min, domain_lat_min, domain_lat_max, domain_lat_max, domain_lat_min]
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
        Line2D([0], [0], color='b', linewidth=2.5, label='Selection domain\n(60°W-30°W, 30°S-60°S)')
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.95)
    
    n_cyclones = len(selected_df)
    ax.set_title(f'Selected EP1 Cyclones (n={n_cyclones})\nIntensification center in domain: 60°W-30°W, 30°S-60°S',
                 fontsize=13, fontweight='bold', pad=15)
    
    # Save
    output_file = FIGURES_DIR / "selected_tracks_overview.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Saved: {output_file}")
    return output_file


def main():
    """Select EP1 cyclones within specified domain for instability analysis."""
    
    print("=" * 80)
    print("STEP 1: Selecting EP1 Cyclones for Instability Analysis")
    print("=" * 80)
    
    # Load clustered data
    print("\n1. Loading clustered data...")
    cluster_file = Path(__file__).resolve().parents[2] / "results" / "cluster" / "kmeans_clustered_data.csv"
    clustered = pd.read_csv(cluster_file)
    
    # Filter EP1 cyclones (cluster 0)
    ep1_cyclones = clustered[clustered['cluster'] == 0].copy()
    print(f"   Found {len(ep1_cyclones)} EP1 cyclones")
    
    # Load full track data
    print("\n2. Loading track data...")
    tracks = load_tracks()
    
    # Filter tracks with complete lifecycle
    print("\n3. Filtering tracks with complete lifecycle (incipient → intensification → mature → decay)...")
    complete_track_ids = filter_complete_lifecycle_tracks(tracks)
    print(f"   Tracks with complete lifecycle: {len(complete_track_ids)} / {tracks['track_id'].nunique()}")
    
    # Filter to only complete lifecycle tracks
    tracks = tracks[tracks['track_id'].isin(complete_track_ids)].copy()
    
    # Merge to get cluster information for complete lifecycle tracks only
    tracks = tracks.merge(
        ep1_cyclones[['track_id', 'cluster']], 
        on='track_id', 
        how='inner'
    )
    
    print(f"   EP1 cyclones with complete lifecycle: {tracks['track_id'].nunique()}")
    
    # Filter by intensification phase center within domain
    # Domain selection ensures environmental homogeneity:
    # - Same synoptic regime (southwestern Atlantic)
    # - Similar SST gradients and atmospheric baroclinicity
    # - Comparable large-scale flow patterns
    # This is critical for meaningful comparison of instability diagnostics
    domain_lon_min, domain_lon_max = -60, -45
    domain_lat_min, domain_lat_max = -45, -30
    print(f"\n4. Filtering by intensification center within domain ({domain_lon_min}°W-{domain_lon_max}°W, {domain_lat_min}°S-{domain_lat_max}°S)...")
    ep1_track_ids = tracks['track_id'].unique()
    valid_track_ids = []
    
    for track_id in ep1_track_ids:
        center_lat, center_lon = get_intensification_center(track_id, tracks)
        if (center_lat is not None and center_lon is not None and
            domain_lon_min <= center_lon <= domain_lon_max and
            domain_lat_min <= center_lat <= domain_lat_max):
            valid_track_ids.append(track_id)
    
    print(f"   Tracks with intensification center in domain: {len(valid_track_ids)} / {len(ep1_track_ids)}")
    
    # Filter tracks to only those meeting domain criterion
    tracks = tracks[tracks['track_id'].isin(valid_track_ids)].copy()
    
    # Get ALL tracks meeting criteria (domain-based selection, not intensity-based)
    print(f"\n5. Selecting all cyclones meeting criteria...")
    
    # Get maximum vorticity for each track (across all phases)
    max_vor = tracks.groupby('track_id')['vor42'].max().reset_index()
    max_vor.columns = ['track_id', 'max_vorticity']
    
    # Sort by vorticity (descending) but keep ALL
    selected_tracks = max_vor.sort_values('max_vorticity', ascending=False)
    
    # Get additional information for selected cyclones
    selected_info = []
    for track_id in selected_tracks['track_id']:
        track_data = tracks[tracks['track_id'] == track_id]
        
        info = {
            'track_id': track_id,
            'max_vorticity': track_data['vor42'].max(),
            'genesis_region': track_data['region'].iloc[0],
            'genesis_date': track_data['date'].iloc[0],
            'duration_hours': len(track_data),
            'complete_lifecycle': True  # All selected tracks have complete lifecycle
        }
        selected_info.append(info)
    
    selected_df = pd.DataFrame(selected_info)
    selected_df = selected_df.sort_values('max_vorticity', ascending=False)
    
    # Save results
    output_file = OUTPUT_DIR / "selected_cases.csv"
    selected_df.to_csv(output_file, index=False)
    
    print(f"\n5. Selected cyclones (complete lifecycle, intensification in domain 60°W-30°W, 30°S-60°S):")
    print(f"   Total: {len(selected_df)} cyclones")
    print(f"\n   Top 10 by vorticity:")
    print(selected_df.head(10).to_string(index=False))
    
    print(f"\n✅ Results saved to: {output_file}")
    
    # Plot selected tracks
    all_tracks = load_tracks()  # Reload full track data for plotting
    plot_selected_tracks(selected_df, all_tracks, domain_lon_min, domain_lon_max, domain_lat_min, domain_lat_max)
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
