#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: Genesis Track Density using KDE (Hoskins and Hodges method)

This script creates a 2x2 figure showing cyclone genesis density using
Kernel Density Estimation following Hoskins and Hodges (2005) methodology.

Panels:
- Top-left: All cyclones (total density)
- Top-right: EP1
- Bottom-left: EP2
- Bottom-right: EP3

Author: Danilo Couto de Souza
Date: December 2024
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from sklearn.neighbors import KernelDensity
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results' / 'cluster'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Energy Pattern configuration
EP_NAMES = ['All Cyclones', 'EP1', 'EP2', 'EP3']
EP_COLORS = ['#666666', '#1f77b4', '#ff7f0e', '#2ca02c']  # Gray, Blue, Orange, Green

# Cluster to EP mapping (based on Ck energy levels)
CLUSTER_TO_EP = {
    0: 1,  # Cluster 0 → EP1 (lowest Ck)
    2: 2,  # Cluster 2 → EP2 (middle Ck)
    1: 3   # Cluster 1 → EP3 (highest Ck)
}

# Domain configuration
LON_MIN, LON_MAX = -75, -20
LAT_MIN, LAT_MAX = -55, -20

# Figure settings
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 12,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
})

# ============================================================================
# Load Data
# ============================================================================

def load_data():
    """Load cyclone data with EP assignments."""
    # Add parent directory to path for imports
    import sys
    scripts_dir = BASE_DIR / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.load_data import load_tracks
    
    # Load clustering results
    cluster_file = RESULTS_DIR / 'kmeans_clustered_data.csv'
    df_clustered = pd.read_csv(cluster_file, index_col=0)
    df_clustered['EP'] = df_clustered['cluster'].map(CLUSTER_TO_EP)
    
    # Load tracks
    print("Loading track data...")
    df_tracks = load_tracks()
    df_tracks['date'] = pd.to_datetime(df_tracks['date'])
    
    # Get genesis (first observation per cyclone)
    df_genesis = df_tracks.groupby('track_id').first().reset_index()
    
    # Merge with cluster assignments
    df = df_genesis.merge(
        df_clustered[['EP']],
        left_on='track_id',
        right_index=True,
        how='inner'
    )
    
    print(f"Loaded {len(df)} cyclones with EP assignments")
    print(f"EP distribution: {df['EP'].value_counts().sort_index().to_dict()}")
    
    return df

# ============================================================================
# KDE Computation (Hoskins and Hodges method)
# ============================================================================

def compute_density(tracks_df, num_time):
    """
    Computing track density using KDE following the idea of K. Hodges 
    (e.g., Hoskins and Hodges, 2005)
    
    Parameters
    ----------
    tracks_df : pandas.DataFrame
        DataFrame with 'lat vor' and 'lon vor' columns
    num_time : int or float
        Number of time units (months, years) for normalization
    
    Returns
    -------
    density : numpy.ndarray
        2D array with density values (cyclones per 10^6 km^2 per time unit)
    longrd : numpy.ndarray
        Longitude grid
    latgrd : numpy.ndarray
        Latitude grid
    """
    # (1) Creating a global grid with 128 x 64 (lon, lat): 2.5 degree
    k = 64
    longrd = np.linspace(-180, 180, 2 * k)
    latgrd = np.linspace(-87.863, 87.863, k)
    tx, ty = np.meshgrid(longrd, latgrd)
    mesh = np.vstack((ty.ravel(), tx.ravel())).T
    mesh *= np.pi / 180.  # Convert to radians

    # (2) Extract positions
    pos = tracks_df[['lat vor', 'lon vor']].copy()
    x = pos['lon vor'].values
    y = pos['lat vor'].values

    # (3) Building the KDE for the positions
    h = np.vstack([y, x]).T
    h *= np.pi / 180.  # Convert lat/long to radians
    bdw = 0.05
    kde = KernelDensity(bandwidth=bdw, metric='haversine',
        kernel='gaussian', algorithm='ball_tree').fit(h)

    # (4) Evaluate the kde() function on the grid
    v = np.exp(kde.score_samples(mesh)).reshape((k, 2 * k))

    # (5) Converting KDE values to scaled density
    # (a) cyclone number: multiply by total number of genesis (= pos.shape[0])
    # (b) area: divide by R ** 2 (R = Earth Radius)
    # (c) area: scale by 1.e6
    # (d) time: divide by the number of time units
    #
    # --> The final unit is cyclones/10^6 km^2/time
    
    R = 6369345.0 * 1e-3  # Earth radius in km at 40ºS (WGS 84 reference ellipsoid)
    factor = (1 / (R * R)) * 1.e6
    density = v * pos.shape[0] * factor / num_time

    return density, longrd, latgrd

# ============================================================================
# Plotting Functions
# ============================================================================

def setup_map_axes(ax, title):
    """Setup map projection and features."""
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    
    # Add coastlines and borders
    ax.coastlines(resolution='50m', linewidth=0.8, color='black')
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='black', linestyle=':')
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                     alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}
    
    # Title
    ax.set_title(title, fontsize=11, fontweight='bold', loc='left')

def plot_density_map(ax, density, longrd, latgrd, title, color, vmax=None):
    """Plot density map with contours and coloring."""
    # Mask domain
    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    
    # Extract regional data
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    
    density_region = density[np.ix_(lat_idx, lon_idx)]
    lon_region = longrd[lon_idx]
    lat_region = latgrd[lat_idx]
    
    # Setup map
    setup_map_axes(ax, title)
    
    # Determine vmax if not provided
    if vmax is None:
        vmax = np.percentile(density_region[density_region > 0], 95)
    
    # Plot filled contours
    levels = np.linspace(0, vmax, 12)
    cf = ax.contourf(lon_region, lat_region, density_region, 
                     levels=levels, cmap='YlOrRd', 
                     transform=ccrs.PlateCarree(), extend='max', alpha=0.8)
    
    # Add contour lines
    cs = ax.contour(lon_region, lat_region, density_region,
                    levels=6, colors='black', linewidths=0.5,
                    transform=ccrs.PlateCarree(), alpha=0.6)
    ax.clabel(cs, inline=True, fontsize=7, fmt='%.1f')
    
    # Add colorbar
    cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', 
                       pad=0.05, shrink=0.8, aspect=15)
    cbar.set_label('Cyclones per 10$^6$ km$^2$ per year', fontsize=9, fontweight='bold')
    cbar.ax.tick_params(labelsize=8)
    
    return vmax

# ============================================================================
# Main Figure Creation
# ============================================================================

def create_figure():
    """Create the 2x2 KDE density figure."""
    # Load data
    df = load_data()
    
    # Calculate time span in years
    df['date'] = pd.to_datetime(df['date'])
    years = df['date'].dt.year
    num_years = years.max() - years.min() + 1
    print(f"Time span: {years.min()}-{years.max()} ({num_years} years)")
    
    # Create figure
    fig = plt.figure(figsize=(14, 12))
    
    # Create 2x2 grid with map projection
    axes = []
    for i in range(4):
        ax = fig.add_subplot(2, 2, i+1, projection=ccrs.PlateCarree())
        axes.append(ax)
    
    # Compute and plot densities
    print("\n" + "="*60)
    
    # Panel 1: All cyclones
    print("Computing density for All Cyclones...")
    density_all, longrd, latgrd = compute_density(df, num_years)
    vmax_all = plot_density_map(axes[0], density_all, longrd, latgrd,
                                '(a) All Cyclones', EP_COLORS[0])
    print(f"  Max density: {density_all.max():.2f} cyclones/10^6 km^2/year")
    
    # Panels 2-4: Individual EPs (use same vmax for comparison)
    ep_labels = ['(b) EP1', '(c) EP2', '(d) EP3']
    for i, (ep_num, label, color) in enumerate(zip([1, 2, 3], ep_labels, EP_COLORS[1:])):
        print(f"\nComputing density for EP{ep_num}...")
        ep_data = df[df['EP'] == ep_num]
        density_ep, _, _ = compute_density(ep_data, num_years)
        plot_density_map(axes[i+1], density_ep, longrd, latgrd,
                        label, color, vmax=vmax_all)
        print(f"  Max density: {density_ep.max():.2f} cyclones/10^6 km^2/year")
        print(f"  N cyclones: {len(ep_data)}")
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    output_file = FIGURES_DIR / 'ep_genesis_density_kde.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n{'='*60}")
    print(f"Figure saved: {output_file}")
    print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    plt.close()

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("CREATING FIGURE: Genesis Density (KDE - Hoskins & Hodges method)")
    print("="*60)
    
    create_figure()
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
