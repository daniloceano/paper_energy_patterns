#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploratory figure: Genesis density (KDE) - Normalization methods comparison

Generates multiple versions of a 2x2 figure using different normalization approaches:

1. Min-Max Normalization (default)
2. Z-Score (Standardization)
3. Fractional Weighted Anomaly
4. Kullback-Leibler Divergence
5. Rank-Based (Percentile) Normalization
6. Difference of Gaussians (DoG) Filter
7. Centered Log-Ratio (CLR) - Compositional Data

- (a) Absolute density (cyclones / 10^6 km^2 / year) - common to all
- (b)-(d) Anomaly/divergence computed by each method

Saves all outputs in `figures/exploratory/normalization_comparison/`.

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
from scipy.stats import rankdata
from scipy.ndimage import gaussian_filter
import warnings
warnings.filterwarnings('ignore')

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results' / 'cluster'
FIGURES_DIR = BASE_DIR / 'figures' / 'exploratory' / 'normalization_comparison'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Cluster to EP mapping (same mapping used in the repository)
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


# ============================================================================
# NORMALIZATION METHODS
# ============================================================================

def minmax_normalize_positive(arr):
    """
    1. Min-Max Normalization (0-1 scaling on positive values).
    Zero values remain zero. Preserves spatial structure.
    """
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
    """
    2. Z-Score Normalization (standardization to mean=0, std=1).
    Statistical measure of deviations from mean.
    """
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


def fractional_weighted_anomaly(density_ep, density_all, frac_ep, epsilon=1e-10):
    """
    3. Fractional Weighted Anomaly.
    Considers expected frequency: (prob_EP / prob_All) - frac_expected
    
    Parameters
    ----------
    density_ep : array
        EP density field
    density_all : array
        Total density field
    frac_ep : float
        Expected fraction (e.g., 0.627 for EP3)
    epsilon : float
        Small value to avoid division by zero
    """
    # Convert to probability distributions
    prob_all = density_all / (density_all.sum() + epsilon)
    prob_ep = density_ep / (density_ep.sum() + epsilon)
    
    # Fractional anomaly
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(prob_all > epsilon, prob_ep / prob_all, 0.0)
    
    anom = ratio - frac_ep
    return anom


def kl_divergence_pointwise(density_ep, density_all, epsilon=1e-10):
    """
    4. Kullback-Leibler Divergence (point-wise for visualization).
    Measures "surprise" of seeing EP at location vs overall climatology.
    
    KL(P||Q) = P * log(P/Q)
    """
    # Convert to probability distributions
    prob_all = density_all / (density_all.sum() + epsilon)
    prob_ep = density_ep / (density_ep.sum() + epsilon)
    
    # Point-wise KL
    with np.errstate(divide='ignore', invalid='ignore'):
        kl = prob_ep * np.log((prob_ep + epsilon) / (prob_all + epsilon))
    
    kl = np.nan_to_num(kl, nan=0.0, posinf=0.0, neginf=0.0)
    return kl


def percentile_normalize(arr):
    """
    5. Rank-Based (Percentile) Normalization.
    Convert to percentile ranks [0, 1]. Robust to outliers.
    """
    out = np.zeros_like(arr, dtype=float)
    mask = arr > 0
    if np.any(mask):
        ranks = rankdata(arr[mask], method='average')
        out[mask] = (ranks - 1) / (len(ranks) - 1)
    return out


def difference_of_gaussians(arr, sigma_small=0.5, sigma_large=2.0):
    """
    6. Difference of Gaussians (DoG) - Spatial filter.
    Highlights structures at specific spatial scales.
    
    Parameters
    ----------
    sigma_small : float
        Small Gaussian kernel (fine features)
    sigma_large : float
        Large Gaussian kernel (coarse features)
    """
    smooth_small = gaussian_filter(arr, sigma=sigma_small)
    smooth_large = gaussian_filter(arr, sigma=sigma_large)
    dog = smooth_small - smooth_large
    return dog


def clr_transform_single(density_ep, density_all, density_dict, epsilon=1e-10):
    """
    7. Centered Log-Ratio (CLR) transformation for compositional data.
    
    Parameters
    ----------
    density_ep : array
        Current EP density
    density_all : array
        Total density (for reference)
    density_dict : dict
        Dictionary with all EP densities {'EP1': arr1, 'EP2': arr2, 'EP3': arr3}
    epsilon : float
        Small value to avoid log(0)
    """
    # Stack all EP densities
    stack = np.stack([d for d in density_dict.values()], axis=0)
    
    # Geometric mean at each location
    geom_mean = np.exp(np.mean(np.log(stack + epsilon), axis=0))
    
    # CLR for current EP
    clr = np.log((density_ep + epsilon) / (geom_mean + epsilon))
    
    return clr


# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================


def plot_relative(ax, rel_anom, longrd, latgrd, title, cmap='RdBu_r', cbar_label='Anomaly'):
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
    cbar.set_label(cbar_label, fontsize=9)
    return maxabs


def create_figure():
    """Generate all normalization method figures."""
    # Load data once
    df = load_data()
    df['date'] = pd.to_datetime(df['date'])
    years = df['date'].dt.year
    num_years = years.max() - years.min() + 1

    print(f"\nLoaded {len(df)} cyclones")
    print(f"Time span: {years.min()}-{years.max()} ({num_years} years)")
    
    # Compute densities for all EPs once
    print("\nComputing densities...")
    density_all, longrd, latgrd = compute_density(df, num_years)
    
    densities = {}
    fractions = {}
    for ep in [1, 2, 3]:
        ep_df = df[df['EP'] == ep]
        densities[f'EP{ep}'], _, _ = compute_density(ep_df, num_years)
        fractions[f'EP{ep}'] = len(ep_df) / len(df)
        print(f"  EP{ep}: {len(ep_df)} cyclones ({fractions[f'EP{ep}']:.1%})")
    
    # Define all methods
    methods = [
        {
            'name': '1_minmax',
            'title': 'Min-Max Normalization',
            'calc': lambda ep: minmax_normalize_positive(densities[ep]) - minmax_normalize_positive(density_all),
            'cbar_label': 'Normalized anomaly (0-1 scale difference)',
            'description': 'Scale each field to [0,1] then subtract'
        },
        {
            'name': '2_zscore',
            'title': 'Z-Score (Standardization)',
            'calc': lambda ep: zscore_normalize_positive(densities[ep]) - zscore_normalize_positive(density_all),
            'cbar_label': 'Z-score anomaly (std units)',
            'description': 'Standardize to mean=0, std=1 then subtract'
        },
        {
            'name': '3_fractional_weighted',
            'title': 'Fractional Weighted Anomaly',
            'calc': lambda ep: fractional_weighted_anomaly(densities[ep], density_all, fractions[ep]),
            'cbar_label': 'Fractional anomaly (ratio - expected fraction)',
            'description': '(P_EP / P_All) - fraction_expected'
        },
        {
            'name': '4_kl_divergence',
            'title': 'Kullback-Leibler Divergence',
            'calc': lambda ep: kl_divergence_pointwise(densities[ep], density_all),
            'cbar_label': 'KL divergence (information bits)',
            'description': 'P * log(P/Q) - information surprise'
        },
        {
            'name': '5_percentile',
            'title': 'Rank-Based (Percentile)',
            'calc': lambda ep: percentile_normalize(densities[ep]) - percentile_normalize(density_all),
            'cbar_label': 'Percentile rank difference',
            'description': 'Convert to percentile ranks [0,1] then subtract'
        },
        {
            'name': '6_dog_filter',
            'title': 'Difference of Gaussians',
            'calc': lambda ep: difference_of_gaussians(densities[ep]) - difference_of_gaussians(density_all),
            'cbar_label': 'DoG filtered difference',
            'description': 'Spatial bandpass filter (σ=0.5 - σ=2.0)'
        },
        {
            'name': '7_clr_compositional',
            'title': 'CLR (Compositional Data)',
            'calc': lambda ep: clr_transform_single(densities[ep], density_all, densities),
            'cbar_label': 'CLR value (log-ratio)',
            'description': 'Centered log-ratio transformation'
        }
    ]
    
    # Generate figure for each method
    print(f"\n{'='*70}")
    print("GENERATING FIGURES FOR ALL NORMALIZATION METHODS")
    print(f"{'='*70}\n")
    
    for method in methods:
        print(f"Processing: {method['title']} ({method['name']})")
        print(f"  Description: {method['description']}")
        
        fig = plt.figure(figsize=(8, 6))
        axes = [fig.add_subplot(2, 2, i + 1, projection=ccrs.PlateCarree()) for i in range(4)]
        
        # Panel (a): All Cyclones (absolute density) - same for all methods
        vmax_all = plot_absolute(axes[0], density_all, longrd, latgrd, '(a) All Cyclones')
        
        # Panels (b)-(d): EP anomalies using current method
        for i, ep in enumerate([1, 2, 3]):
            ep_key = f'EP{ep}'
            try:
                rel_anom = method['calc'](ep_key)
                maxabs = plot_relative(
                    axes[i + 1], 
                    rel_anom, 
                    longrd, 
                    latgrd, 
                    f'({chr(98 + i)}) EP{ep}',
                    cbar_label=method['cbar_label']
                )
                print(f"    EP{ep}: anomaly range [{-maxabs:.4f}, {maxabs:.4f}]")
            except Exception as e:
                print(f"    EP{ep}: ERROR - {e}")
                continue
        
        # Add method title
        fig.suptitle(method['title'], fontsize=13, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save figure
        out_file = FIGURES_DIR / f"{method['name']}_genesis_density.png"
        plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  ✓ Saved: {out_file}")
        print()
    
    # Create summary comparison file
    summary_file = FIGURES_DIR / 'README_comparison.txt'
    with open(summary_file, 'w') as f:
        f.write("NORMALIZATION METHODS COMPARISON\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n")
        f.write(f"Dataset: {len(df)} cyclones ({years.min()}-{years.max()})\n\n")
        
        for method in methods:
            f.write(f"\n{method['name']}: {method['title']}\n")
            f.write(f"  Description: {method['description']}\n")
            f.write(f"  File: {method['name']}_genesis_density.png\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("\nRECOMMENDATIONS:\n\n")
        f.write("1. Min-Max: Best for intuitive interpretation\n")
        f.write("2. Z-Score: Best for statistical rigor\n")
        f.write("3. Fractional Weighted: Best when considering expected frequencies\n")
        f.write("4. KL Divergence: Best for information-theoretic interpretation\n")
        f.write("5. Percentile: Best for robustness to outliers\n")
        f.write("6. DoG Filter: Best for spatial structure analysis\n")
        f.write("7. CLR: Best for compositional data theory\n")
        f.write("\nFor publication, Min-Max or Z-Score are recommended.\n")
    
    print(f"{'='*70}")
    print(f"✓ ALL FIGURES GENERATED!")
    print(f"{'='*70}")
    print(f"\nOutput directory: {FIGURES_DIR}")
    print(f"Summary file: {summary_file}\n")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("GENESIS DENSITY NORMALIZATION COMPARISON")
    print("Generating figures for all 7 normalization methods")
    print("="*70)
    create_figure()
    print("\n" + "="*70)
    print("COMPLETE! Review figures in:")
    print(f"  {FIGURES_DIR}")
    print("="*70 + "\n")
