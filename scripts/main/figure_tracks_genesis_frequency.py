#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create publication-ready figure combining:
1. All cyclone tracks colored by region (ARG, SE-BR, LA-PLATA)
2. Sunburst chart showing genesis frequency by region and season

Figure for main paper.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import Wedge
from matplotlib.lines import Line2D

# Add scripts directory to path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / 'scripts'))

from utils.load_data import load_tracks

# Configuration
OUT_DIR = BASE_DIR / 'figures' / 'main'
OUT_DIR.mkdir(parents=True, exist_ok=True)
DPI = 300
ALPHA_TRACKS = 0.15  # Transparency for tracks
LINEWIDTH = 0.3  # Width of track lines

# Region colors (matching user's request)
REGION_COLORS = {
    'ARG': '#1f77b4',       # Blue
    'SE-BR': '#2ca02c',     # Green
    'LA-PLATA': '#ff7f0e'   # Orange/Yellow
}

# Season colors for sunburst
SEASON_COLORS = {
    'DJF': '#d62728',  # Red - Summer
    'MAM': '#ff7f0e',  # Orange - Autumn
    'JJA': '#2ca02c',  # Green - Winter
    'SON': '#1f77b4'   # Blue - Spring
}


def get_season(month):
    """Convert month to season (Southern Hemisphere)"""
    if month in [12, 1, 2]:
        return 'DJF'
    elif month in [3, 4, 5]:
        return 'MAM'
    elif month in [6, 7, 8]:
        return 'JJA'
    else:
        return 'SON'


def create_sunburst_chart(ax, df_genesis):
    """Create sunburst/donut chart for genesis frequency by region and season"""
    
    # Count by region and season
    genesis_counts = df_genesis.groupby(['region', 'season']).size().reset_index(name='count')
    total = genesis_counts['count'].sum()
    
    # Calculate percentages
    genesis_counts['percentage'] = 100 * genesis_counts['count'] / total
    
    # Calculate region totals
    region_totals = genesis_counts.groupby('region')['count'].sum()
    region_pcts = 100 * region_totals / total

    # Plot parameters
    inner_radius = 0.2   # small hole in center
    outer_radius = 0.6
    region_outer_radius = 0.95  # thicker outer ring for regions
    
    # Sort regions for consistent order (ARG, LA-PLATA, SE-BR - clockwise)
    region_order = ['ARG', 'LA-PLATA', 'SE-BR']
    
    # Plot inner ring (by season within each region)
    start_angle = 90  # Start at top

    for region in region_order:
        region_data = genesis_counts[genesis_counts['region'] == region].copy()
        region_total = region_data['count'].sum()
        region_angle = 360 * region_total / total

        # Sort seasons within region
        season_order = ['DJF', 'MAM', 'JJA', 'SON']

        # For each season, compute angle relative to the region sector
        region_start = start_angle
        for season in season_order:
            season_data = region_data[region_data['season'] == season]
            if not season_data.empty:
                count = season_data['count'].values[0]
                frac = count / region_total
                angle = region_angle * frac

                # Plot wedge with slightly reduced opacity for seasons
                wedge = Wedge((0, 0), outer_radius, region_start - angle, region_start,
                              width=outer_radius - inner_radius,
                              facecolor=SEASON_COLORS[season],
                              edgecolor='white', linewidth=0.8, alpha=0.7)
                ax.add_patch(wedge)

                # Add percentage label relative to region total
                if angle > 8:  # Only label if > 8 degrees (~2.2% of region)
                    mid_angle = region_start - angle/2
                    label_radius = (inner_radius + outer_radius) / 2
                    x = label_radius * np.cos(np.radians(mid_angle))
                    y = label_radius * np.sin(np.radians(mid_angle))
                    pct = 100 * count / region_total
                    ax.text(x, y, f'{pct:.0f}%', ha='center', va='center',
                           fontsize=12, fontweight='bold', color='white')
                    # Add season label (small)
                    label_radius_outer = outer_radius - 0.05
                    x_outer = label_radius_outer * np.cos(np.radians(mid_angle))
                    y_outer = label_radius_outer * np.sin(np.radians(mid_angle))
                    ax.text(x_outer, y_outer, season, ha='center', va='center',
                           fontsize=10, fontweight='bold', color='black')

                region_start -= angle

        # advance the global start angle by the whole region angle
        start_angle -= region_angle
    
    # Plot outer ring (by region)
    start_angle = 90
    for region in region_order:
        region_total = region_totals[region]
        region_angle = 360 * region_total / total
        
        # Plot wedge
        wedge = Wedge((0, 0), region_outer_radius, start_angle - region_angle, start_angle,
                    width=region_outer_radius - outer_radius, 
                    facecolor=REGION_COLORS[region],
                    edgecolor='white', linewidth=2, alpha=0.85)
        ax.add_patch(wedge)
        
        # Add region label
        mid_angle = start_angle - region_angle/2
        label_radius = (outer_radius + region_outer_radius) / 2
        x = label_radius * np.cos(np.radians(mid_angle))
        y = label_radius * np.sin(np.radians(mid_angle))
        pct = region_pcts[region]
        
        # Region name
        ax.text(x, y + 0.05, region, ha='center', va='center',
               fontsize=14, fontweight='bold', color='white')
        # Percentage and count
        ax.text(x, y - 0.05, f'{pct:.0f}%\n({region_total})', ha='center', va='center',
               fontsize=12, color='white')
        
        start_angle -= region_angle
    
    # Do not add center text; keep center small and clean
    
    # Set aspect and limits
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect('equal')
    ax.axis('off')


def filter_complete_lifecycle_tracks(df):
    """
    Filter tracks with complete lifecycle in exact order:
    incipient → intensification → mature → decay
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


def main():
    print('Loading data...')
    df = load_tracks()
    
    # Filter tracks with complete lifecycle
    print('\nFiltering tracks with complete lifecycle (incipient → intensification → mature → decay)...')
    complete_track_ids = filter_complete_lifecycle_tracks(df)
    print(f"Tracks with complete lifecycle: {len(complete_track_ids)} / {df['track_id'].nunique()}")
    
    # Filter dataframe to only include complete lifecycle tracks
    df = df[df['track_id'].isin(complete_track_ids)].copy()
    
    # Get genesis points (first timestep of each track)
    df['date'] = pd.to_datetime(df['date'])
    df_genesis = df.groupby('track_id').first().reset_index()
    df_genesis['season'] = df_genesis['date'].dt.month.apply(get_season)
    
    print(f"\nFiltered cyclones: {len(df_genesis)}")
    print(f"By region:\n{df_genesis['region'].value_counts()}")
    print(f"By season:\n{df_genesis['season'].value_counts()}")
    
    # Create figure with two subplots
    fig = plt.figure(figsize=(12, 8))
    
    # Left subplot: Tracks map with South Polar Stereographic projection
    # Centered at South Pole (like the figure from "A New Perspective on Southern Hemisphere Storm Tracks")
    # This projection naturally emphasizes Atlantic and Indian Oceans while minimizing Pacific
    proj = ccrs.Stereographic(central_latitude=-90, central_longitude=0)
    ax_map = fig.add_subplot(121, projection=proj)
    
    # Set extent to show Southern Hemisphere focusing on Atlantic and Indian Oceans
    # Limiting northern extent to avoid too much white space
    # Longitude range covers Atlantic (-80 to 60) extending through Indian Ocean
    ax_map.set_extent([-80, 120, -90, -20], crs=ccrs.PlateCarree())
    ax_map.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax_map.add_feature(cfeature.OCEAN, facecolor='white')
    ax_map.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='black')
    ax_map.gridlines(linewidth=0.5, linestyle='--', alpha=0.5)
    
    # Determine top 10 most intense cyclones by maximum vor42 (if available)
    if 'vor42' in df.columns:
        top10_ids = df.groupby('track_id')['vor42'].max().nlargest(10).index.tolist()
        print(f"Top 10 tracks by max vor42: {top10_ids}")
    else:
        top10_ids = []

    # Plot all tracks by region
    print('Plotting tracks...')
    for region in ['ARG', 'SE-BR', 'LA-PLATA']:
        df_region = df[df['region'] == region]
        
        # Group by track_id and plot each track
        for track_id, track_data in df_region.groupby('track_id'):
            lons = track_data['lon vor'].values
            lats = track_data['lat vor'].values
            # Highlight top-10 intense tracks
            is_top = track_id in top10_ids
            lw = LINEWIDTH * 3 if is_top else LINEWIDTH
            a = 0.95 if is_top else ALPHA_TRACKS
            z = 3 if is_top else 1

            ax_map.plot(lons, lats,
                       color=REGION_COLORS[region],
                       alpha=a,
                       linewidth=lw,
                       transform=ccrs.PlateCarree(),
                       zorder=z)
    
    # Add legend for regions
    legend_elements = [
        mpatches.Patch(color=REGION_COLORS['ARG'], label='ARG'),
        mpatches.Patch(color=REGION_COLORS['SE-BR'], label='SE-BR'),
        mpatches.Patch(color=REGION_COLORS['LA-PLATA'], label='LA-PLATA')
    ]
    ax_map.legend(handles=legend_elements, loc='lower left', fontsize=10,
                 frameon=True, fancybox=True, shadow=True)
    # Add legend entry for highlighted top-10 tracks
    if len(top10_ids) > 0:
        top_line = Line2D([0], [0], color='black', lw=LINEWIDTH * 3, label='Top 10 intensity')
        ax_map.add_artist(ax_map.legend(handles=legend_elements + [top_line], loc='lower left', fontsize=10,
                                       frameon=True, fancybox=True, shadow=True))
        
    # Right subplot: Sunburst chart
    ax_sun = fig.add_subplot(122)
    create_sunburst_chart(ax_sun, df_genesis)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    out_file = OUT_DIR / 'tracks_genesis_frequency.png'
    plt.savefig(out_file, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f'\n✓ Figure saved: {out_file}')
    print(f'✓ Size: {out_file.stat().st_size / 1024:.1f} KB')


if __name__ == '__main__':
    main()
