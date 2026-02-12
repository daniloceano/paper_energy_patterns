#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figura exploratória: Densidade de gênese (KDE) e importância relativa por EP

Gera uma figura 2x2 semelhante à `06_figure_genesis_density_kde.py` mas
com os painéis (b),(c),(d) mostrando a anomalia fracional por EP:

- (a) Densidade absoluta (cyclones / 10^6 km^2 / ano)
- (b)-(d) Anomalia fracional = (densidade_EP / densidade_total) - frac_esperado

As anomalias fracionais usam uma barra de cores divergente centrada em 0
para destacar regiões com participação maior/menor que a esperada.

Salva em `figures/exploratory/ep_analysis/6_ep_genesis_density_relative_kde.png`.

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
FIGURES_DIR = BASE_DIR / 'figures' / 'exploratory' / 'ep_analysis'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Cluster to EP mapping (same lógica do repositório)
CLUSTER_TO_EP = {0: 1, 2: 2, 1: 3}

# Domain
LON_MIN, LON_MAX = -75, -20
LAT_MIN, LAT_MAX = -55, -20

plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 11,
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
    # grid sizes consistent com script original
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
    ax.set_title(title, fontsize=11, fontweight='bold', loc='left')


def plot_absolute(ax, density, longrd, latgrd, title):
    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    density_region = density[np.ix_(lat_idx, lon_idx)]
    lon_region = longrd[lon_idx]
    lat_region = latgrd[lat_idx]

    setup_map_axes(ax, title)

    pos_vals = density_region[density_region > 0]
    if pos_vals.size == 0:
        vmax = 1e-6
    else:
        vmax = np.percentile(pos_vals, 95)

    levels = np.linspace(0.0, vmax, 12)
    cf = ax.contourf(lon_region, lat_region, density_region,
                     levels=levels, cmap='YlOrRd', transform=ccrs.PlateCarree(), extend='max', alpha=0.9)
    cs = ax.contour(lon_region, lat_region, density_region,
                    levels=6, colors='black', linewidths=0.5, transform=ccrs.PlateCarree(), alpha=0.6)
    cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.15, shrink=0.8, aspect=15)
    cbar.ax.tick_params(labelsize=8)
    return vmax


def plot_relative(ax, rel_anom, longrd, latgrd, title, cmap='RdBu_r'):
    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    rel_region = rel_anom[np.ix_(lat_idx, lon_idx)]
    lon_region = longrd[lon_idx]
    lat_region = latgrd[lat_idx]

    setup_map_axes(ax, title)

    # Mask nan
    masked = np.ma.masked_invalid(rel_region)
    maxabs = np.nanmax(np.abs(rel_region))
    if np.isnan(maxabs) or maxabs == 0:
        maxabs = 0.1

    norm = TwoSlopeNorm(vcenter=0.0, vmin=-maxabs, vmax=maxabs)
    levels = np.linspace(-maxabs, maxabs, 13)

    cf = ax.contourf(lon_region, lat_region, masked, levels=levels, cmap=cmap,
                     norm=norm, transform=ccrs.PlateCarree(), extend='both', alpha=0.9)
    cs = ax.contour(lon_region, lat_region, masked, levels=7, colors='black', linewidths=0.4,
                    transform=ccrs.PlateCarree(), alpha=0.6)
    cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.15, shrink=0.8, aspect=20)
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label('Anomalia fracional (fração - fração esperada)', fontsize=9)
    return maxabs


def create_figure():
    df = load_data()
    df['date'] = pd.to_datetime(df['date'])
    years = df['date'].dt.year
    num_years = years.max() - years.min() + 1

    fig = plt.figure(figsize=(8, 6))
    axes = [fig.add_subplot(2, 2, i + 1, projection=ccrs.PlateCarree()) for i in range(4)]

    # All cyclones
    density_all, longrd, latgrd = compute_density(df, num_years)
    vmax_all = plot_absolute(axes[0], density_all, longrd, latgrd, '(a) All Cyclones')

    # For each EP, compute density and relative anomaly
    eps = [1, 2, 3]
    for i, ep in enumerate(eps):
        ep_df = df[df['EP'] == ep]
        density_ep, _, _ = compute_density(ep_df, num_years)

        # Avoid division by zero; compute fraction only where density_all > 0
        with np.errstate(divide='ignore', invalid='ignore'):
            fraction = np.where(density_all > 0, density_ep / density_all, np.nan)

        # Normalizar os KDEs com Min-Max scaler entre 0 e 1 (aplicado a valores positivos)
        # Células com zero (sem eventos) recebem 0.0 no resultado.
        def _minmax_positive(arr):
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

        norm_all = _minmax_positive(density_all)
        norm_ep = _minmax_positive(density_ep)

        # Diferença normalizada (entre -1 e 1, na prática entre -1 e 1 se ambos têm variação):
        rel_anom = norm_ep - norm_all

        plot_relative(axes[i + 1], rel_anom, longrd, latgrd, f'({chr(98 + i)}) EP{ep} (anomaly)')

    plt.tight_layout()
    out_file = FIGURES_DIR / 'ep_genesis_density_relative_kde.png'
    plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Figura salva: {out_file}')


if __name__ == '__main__':
    print('Gerando figura de densidade relativa por EP...')
    create_figure()
    print('Concluído')
