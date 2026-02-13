#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figura comparativa: Min-Max vs Z-Score (lado a lado)

Gera uma figura com 2 colunas mostrando os 2 métodos recomendados
para facilitar a decisão final.

Author: Danilo Couto de Souza
Date: 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from sklearn.neighbors import KernelDensity
from matplotlib.colors import TwoSlopeNorm
import warnings
warnings.filterwarnings('ignore')

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results' / 'cluster'
FIGURES_DIR = BASE_DIR / 'figures' / 'exploratory' / 'normalization_comparison'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Cluster to EP mapping
CLUSTER_TO_EP = {0: 1, 2: 2, 1: 3}

# Domain
LON_MIN, LON_MAX = -75, -20
LAT_MIN, LAT_MAX = -55, -20

plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 10,
    'font.family': 'sans-serif'
})


def load_data():
    import sys
    scripts_dir = BASE_DIR / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.load_data import load_tracks

    cluster_file = RESULTS_DIR / 'kmeans_clustered_data.csv'
    df_clustered = pd.read_csv(cluster_file, index_col=0)
    df_clustered['EP'] = df_clustered['cluster'].map(CLUSTER_TO_EP)

    df_tracks = load_tracks()
    df_tracks['date'] = pd.to_datetime(df_tracks['date'])
    df_genesis = df_tracks.groupby('track_id').first().reset_index()

    df = df_genesis.merge(
        df_clustered[['EP']],
        left_on='track_id',
        right_index=True,
        how='inner'
    )

    return df


def compute_density(tracks_df, num_time):
    k = 64
    longrd = np.linspace(-180, 180, 2 * k)
    latgrd = np.linspace(-87.863, 87.863, k)
    tx, ty = np.meshgrid(longrd, latgrd)
    mesh = np.vstack((ty.ravel(), tx.ravel())).T
    mesh *= np.pi / 180.

    pos = tracks_df[['lat vor', 'lon vor']].copy()
    x = pos['lon vor'].values
    y = pos['lat vor'].values

    h = np.vstack([y, x]).T
    h *= np.pi / 180.
    bdw = 0.05
    kde = KernelDensity(bandwidth=bdw, metric='haversine',
                        kernel='gaussian', algorithm='ball_tree')
    if h.shape[0] > 0:
        kde.fit(h)
        v = np.exp(kde.score_samples(mesh)).reshape((k, 2 * k))
    else:
        v = np.zeros((k, 2 * k))

    R = 6369345.0 * 1e-3
    factor = (1 / (R * R)) * 1.e6
    density = v * pos.shape[0] * factor / num_time

    return density, longrd, latgrd


def setup_map_axes(ax, title):
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', linewidth=0.8, color='black')
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='black', linestyle=':')
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    ax.set_title(title, fontsize=10, fontweight='bold', loc='left')


def minmax_normalize_positive(arr):
    out = np.full(arr.shape, 0.0, dtype=float)
    pos_mask = arr > 0
    if not np.any(pos_mask):
        return out
    pos = arr[pos_mask]
    mn = pos.min()
    mx = pos.max()
    if mx == mn:
        out[pos_mask] = 1.0
    else:
        out[pos_mask] = (arr[pos_mask] - mn) / (mx - mn)
    return out


def zscore_normalize_positive(arr):
    out = np.zeros_like(arr, dtype=float)
    pos_mask = arr > 0
    if not np.any(pos_mask):
        return out
    pos = arr[pos_mask]
    mean = pos.mean()
    std = pos.std()
    if std == 0:
        out[pos_mask] = 0.0
    else:
        out[pos_mask] = (arr[pos_mask] - mean) / std
    return out


def plot_anomaly(ax, rel_anom, longrd, latgrd, title, cbar_label):
    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    rel_region = rel_anom[np.ix_(lat_idx, lon_idx)]
    lon_region = longrd[lon_idx]
    lat_region = latgrd[lat_idx]

    setup_map_axes(ax, title)

    masked = np.ma.masked_invalid(rel_region)
    maxabs = np.nanmax(np.abs(rel_region))
    if np.isnan(maxabs) or maxabs == 0:
        maxabs = 0.1

    norm = TwoSlopeNorm(vcenter=0.0, vmin=-maxabs, vmax=maxabs)
    levels = np.linspace(-maxabs, maxabs, 13)

    cf = ax.contourf(lon_region, lat_region, masked, levels=levels, cmap='RdBu_r',
                     norm=norm, transform=ccrs.PlateCarree(), extend='both', alpha=0.9)
    cs = ax.contour(lon_region, lat_region, masked, levels=7, colors='black', 
                    linewidths=0.3, transform=ccrs.PlateCarree(), alpha=0.5)
    
    return cf, maxabs


def create_comparison_figure():
    """Generate side-by-side comparison of Min-Max vs Z-Score."""
    df = load_data()
    df['date'] = pd.to_datetime(df['date'])
    years = df['date'].dt.year
    num_years = years.max() - years.min() + 1

    print(f"\nGenerating comparison figure...")
    print(f"Dataset: {len(df)} cyclones ({years.min()}-{years.max()})")
    
    # Compute densities
    density_all, longrd, latgrd = compute_density(df, num_years)
    
    densities = {}
    for ep in [1, 2, 3]:
        ep_df = df[df['EP'] == ep]
        densities[ep], _, _ = compute_density(ep_df, num_years)
    
    # Create figure: 3 rows x 2 columns
    fig = plt.figure(figsize=(12, 10))
    
    # Column headers
    fig.text(0.28, 0.97, 'Min-Max Normalization', fontsize=13, ha='center', fontweight='bold')
    fig.text(0.72, 0.97, 'Z-Score Standardization', fontsize=13, ha='center', fontweight='bold')
    
    # Row labels
    ep_labels = ['EP1', 'EP2', 'EP3']
    
    for i, ep in enumerate([1, 2, 3]):
        # Min-Max (left column)
        ax_left = fig.add_subplot(3, 2, 2*i + 1, projection=ccrs.PlateCarree())
        norm_all = minmax_normalize_positive(density_all)
        norm_ep = minmax_normalize_positive(densities[ep])
        anom_minmax = norm_ep - norm_all
        cf_left, maxabs_left = plot_anomaly(
            ax_left, anom_minmax, longrd, latgrd, 
            f'({chr(97 + 2*i)}) {ep_labels[i]}',
            'Min-Max anomaly'
        )
        
        # Z-Score (right column)
        ax_right = fig.add_subplot(3, 2, 2*i + 2, projection=ccrs.PlateCarree())
        z_all = zscore_normalize_positive(density_all)
        z_ep = zscore_normalize_positive(densities[ep])
        anom_zscore = z_ep - z_all
        cf_right, maxabs_right = plot_anomaly(
            ax_right, anom_zscore, longrd, latgrd,
            f'({chr(97 + 2*i + 1)}) {ep_labels[i]}',
            'Z-score anomaly'
        )
        
        # Add colorbars
        cbar_left = plt.colorbar(cf_left, ax=ax_left, orientation='horizontal',
                                 pad=0.10, shrink=0.7, aspect=15)
        cbar_left.set_label('Normalized anomaly', fontsize=8)
        cbar_left.ax.tick_params(labelsize=7)
        
        cbar_right = plt.colorbar(cf_right, ax=ax_right, orientation='horizontal',
                                  pad=0.10, shrink=0.7, aspect=15)
        cbar_right.set_label('Z-score (σ units)', fontsize=8)
        cbar_right.ax.tick_params(labelsize=7)
        
        print(f"  {ep_labels[i]}: Min-Max range ±{maxabs_left:.3f}, Z-Score range ±{maxabs_right:.2f}σ")
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    out_file = FIGURES_DIR / 'COMPARISON_minmax_vs_zscore.png'
    plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"\n✓ Comparison figure saved: {out_file}")
    print(f"✓ Size: {out_file.stat().st_size / 1024:.1f} KB\n")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("GENERATING COMPARISON: Min-Max vs Z-Score")
    print("="*70)
    create_comparison_figure()
    print("="*70)
    print("COMPLETE!")
    print("="*70 + "\n")
