#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: Validate Ck subterms and generate figures for EP1 cyclones.

Validates new LEC results (Ck subterms) against Zenodo dataset,
classifies dominant subterm per cyclone, and generates:

  Figure 1: Boxplots of Ck subterms during intensification
  Figure 2: Genesis density maps per dominant subterm
  Figure 3: Normalized-difference maps per dominant subterm
  Figure 4: Full tracks per dominant subterm

Tables:
  results/ck_subterms/ep1_ck_subterms_per_cyclone.csv
  results/ck_subterms/validation_summary.csv

Text:
  results/ck_subterms/diagnostic_summary.txt

Author: Danilo Couto de Souza / GitHub Copilot
"""

from __future__ import annotations

import sys
import warnings
import subprocess
from pathlib import Path
from collections import defaultdict

# ── project root on path ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from sklearn.neighbors import KernelDensity
import seaborn as sns

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

GRAVITY = 9.8  # m/s²

# Paths
CLUSTER_FILE    = BASE_DIR / 'results' / 'cluster' / 'kmeans_clustered_data.csv'
EP1_CASES_FILE  = BASE_DIR / 'results' / 'ep1_full' / 'all_ep1_cases.csv'
NEW_LEC_DIR     = BASE_DIR / 'results' / 'ck_analysis' / 'lec_results'
ZENODO_DIR      = BASE_DIR / 'data' / 'temp_lec_zenodo' / 'LEC_Results_energetic-patterns'
FIGURES_DIR     = BASE_DIR / 'figures' / 'ck_subterms'
RESULTS_DIR     = BASE_DIR / 'results' / 'ck_subterms'

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Subterm metadata
SUBTERM_KEYS   = ['Ck_1', 'Ck_2', 'Ck_3', 'Ck_4', 'Ck_5']
SUBTERM_LABELS = ['Ck⁽ᴬ⁾', 'Ck⁽ᴮ⁾', 'Ck⁽ᶜ⁾', 'Ck⁽ᴰ⁾', 'Ck⁽ᴱ⁾']
SUBTERM_DESCRIPTIONS = [
    'Term (A): eddy momentum flux / meridional grad. of zonal wind',
    'Term (B): meridional flux of KE with meridional wind',
    'Term (C): meridional flux of zonal KE (tan(phi) term)',
    'Term (D): zonal & vertical flux with vertical shear of U',
    'Term (E): meridional & vertical flux with vertical shear of V',
]

# Tab10 palette for subterms
TAB10 = plt.cm.tab10.colors
SUBTERM_COLORS = [TAB10[i] for i in range(5)]

# Map domain
LON_MIN, LON_MAX = -75, -20
LAT_MIN, LAT_MAX = -55, -20

# Tolerance for validation (percent)
TOLERANCE_PCT = 20.0

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
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _resolve_csv(path: Path) -> Path | None:
    """Handle Zenodo quirk: a *.csv entry can be a directory containing a CSV."""
    if path.is_dir():
        csvs = list(path.glob('*.csv'))
        return csvs[0] if csvs else None
    return path if path.exists() else None


def _get_season(date) -> str:
    """Return DJF/MAM/JJA/SON for Southern Hemisphere (month-based)."""
    m = pd.Timestamp(date).month
    if m in (12, 1, 2):
        return 'DJF'
    elif m in (3, 4, 5):
        return 'MAM'
    elif m in (6, 7, 8):
        return 'JJA'
    else:
        return 'SON'


def _vertically_integrate(df: pd.DataFrame) -> pd.Series:
    """
    Vertically integrate a pressure-level DataFrame.

    Columns = pressure levels in Pa.
    Returns a time series of vertically integrated values (W/m²).
    """
    cols = df.columns.astype(float)
    # compute dp from midpoints
    sorted_cols = np.sort(cols)
    # Use trapezoidal-like dp: difference between adjacent levels / 2
    # Simple approach: dp[i] = (p[i+1] - p[i-1]) / 2 at interior, half-interval at edges
    n = len(sorted_cols)
    dp = np.zeros(n)
    if n == 1:
        dp[0] = sorted_cols[0]
    else:
        dp[0] = (sorted_cols[1] - sorted_cols[0]) / 2.0
        dp[-1] = (sorted_cols[-1] - sorted_cols[-2]) / 2.0
        for i in range(1, n - 1):
            dp[i] = (sorted_cols[i + 1] - sorted_cols[i - 1]) / 2.0

    # Map dp to column order (df.columns may not be sorted)
    col_order = df.columns.astype(float)
    dp_map = dict(zip(sorted_cols, dp))
    dp_vals = np.array([dp_map[c] for c in col_order])

    # Integrate: sum(values * dp / g)
    integrated = (df.values * dp_vals[np.newaxis, :] / GRAVITY).sum(axis=1)
    return pd.Series(integrated, index=df.index)


# ============================================================================
# DENSITY / MAP FUNCTIONS (verbatim from 06_figure_genesis_density_kde.py)
# ============================================================================

def compute_density(tracks_df, num_time):
    """
    Computing track density using KDE following the idea of K. Hodges
    (Hoskins and Hodges, 2005).
    """
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
                        kernel='gaussian', algorithm='ball_tree').fit(h)

    v = np.exp(kde.score_samples(mesh)).reshape((k, 2 * k))

    R = 6369345.0 * 1e-3
    factor = (1 / (R * R)) * 1.e6
    density = v * pos.shape[0] * factor / num_time

    return density, longrd, latgrd


def setup_map_axes(ax, title):
    """Setup map projection and features."""
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', linewidth=0.8, color='black')
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='black', linestyle=':')
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray',
                      alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}
    ax.set_title(title, fontsize=11, fontweight='bold', loc='left')


def plot_density_map(ax, density, longrd, latgrd, title, color,
                     vmin=None, vmax=None, add_colorbar=True):
    """
    Plot density map with contours and coloring.

    Parameters
    ----------
    add_colorbar : bool
        If False, skip adding a per-axes colorbar. Use when the caller
        manages a single shared colorbar for all panels.

    Returns
    -------
    cf : matplotlib.contour.QuadContourSet
        The filled contour object (useful for shared colorbars).
    vmax : float
        Color-scale maximum used.
    """
    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    density_region = density[np.ix_(lat_idx, lon_idx)]
    lon_region = longrd[lon_idx]
    lat_region = latgrd[lat_idx]

    setup_map_axes(ax, title)

    if vmin is None:
        vmin = 0.0
    if vmax is None:
        pos_vals = density_region[density_region > 0]
        vmax = np.percentile(pos_vals, 95) if pos_vals.size > 0 else 1e-6

    levels = np.round(np.linspace(vmin, vmax, 12), 2)

    cf = ax.contourf(lon_region, lat_region, density_region,
                     levels=levels, cmap='YlOrRd',
                     transform=ccrs.PlateCarree(), extend='max', alpha=0.8)
    ax.contour(lon_region, lat_region, density_region,
               levels=6, colors='black', linewidths=0.5,
               transform=ccrs.PlateCarree(), alpha=0.6)

    if add_colorbar:
        cbar = plt.colorbar(cf, ax=ax, orientation='horizontal',
                            pad=0.15, shrink=0.8, aspect=15)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_ticks(levels[::2])
        cbar.set_ticklabels([f'{lev:.1f}' for lev in levels[::2]])

    return cf, vmax


def minmax_normalize_positive(arr):
    """Apply Min-Max normalization (0-1) to positive values only."""
    out = np.full(arr.shape, 0.0, dtype=float)
    pos_mask = arr > 0
    if not np.any(pos_mask):
        return out
    pos = arr[pos_mask]
    mn, mx = pos.min(), pos.max()
    if mx == mn:
        out[pos_mask] = 1.0
    else:
        out[pos_mask] = (arr[pos_mask] - mn) / (mx - mn)
    return out


def plot_relative_anomaly_map(ax, rel_anom, longrd, latgrd, title,
                               add_colorbar=True):
    """
    Plot normalized relative anomaly map with diverging colormap.

    Normalization: norm_EP − norm_All  (see minmax_normalize_positive).
    Positive values = enhanced genesis for this subterm relative to all EP1.
    Negative values = suppressed genesis for this subterm relative to all EP1.

    Parameters
    ----------
    add_colorbar : bool
        If False, skip adding a per-axes colorbar.

    Returns
    -------
    cf : matplotlib.contour.QuadContourSet
    maxabs : float
        Maximum absolute anomaly value used for the color scale.
    """
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

    cf = ax.contourf(lon_region, lat_region, masked,
                     levels=levels, cmap='RdBu_r', norm=norm,
                     transform=ccrs.PlateCarree(), extend='both', alpha=0.8)
    ax.contour(lon_region, lat_region, masked,
               levels=7, colors='black', linewidths=0.4,
               transform=ccrs.PlateCarree(), alpha=0.6)

    if add_colorbar:
        cbar = plt.colorbar(cf, ax=ax, orientation='horizontal',
                            pad=0.15, shrink=0.8, aspect=15)
        cbar.set_ticks(np.linspace(-maxabs, maxabs, 5))
        cbar.set_ticklabels([f'{t:.2f}' for t in np.linspace(-maxabs, maxabs, 5)])
        cbar.ax.tick_params(labelsize=10)

    return cf, maxabs


# ============================================================================
# LOAD DATA
# ============================================================================

def load_data():
    """
    Load all required datasets.

    Returns
    -------
    dict with keys:
        ep1_ids        : list of EP1 track_ids (from cluster file)
        ep1_cases      : DataFrame from all_ep1_cases.csv
        cluster_df     : DataFrame with cluster assignments
        tracks_df      : Full track DataFrame (from load_tracks)
        genesis_df     : Genesis rows (first obs per cyclone) with EP assignment
    """
    from scripts.utils.load_data import load_tracks

    print('[load_data] Loading cluster assignments...')
    cluster_df = pd.read_csv(CLUSTER_FILE)
    ep1_ids = cluster_df.loc[cluster_df['cluster'] == 0, 'track_id'].tolist()
    print(f'  EP1 cyclones (cluster 0): {len(ep1_ids)}')

    print('[load_data] Loading EP1 cases (intensification phases)...')
    ep1_cases = pd.read_csv(EP1_CASES_FILE)
    ep1_cases['intensification_start'] = pd.to_datetime(ep1_cases['intensification_start'])
    ep1_cases['intensification_end']   = pd.to_datetime(ep1_cases['intensification_end'])
    print(f'  Cases with intensification data: {len(ep1_cases)}')

    print('[load_data] Loading full track database...')
    tracks_df = load_tracks()
    tracks_df['date'] = pd.to_datetime(tracks_df['date'])

    # Genesis: first observation per cyclone
    genesis_df = tracks_df.groupby('track_id').first().reset_index()
    # Keep only EP1
    genesis_ep1 = genesis_df[genesis_df['track_id'].isin(ep1_ids)].copy()
    print(f'  EP1 genesis records found in tracks: {len(genesis_ep1)}')

    return {
        'ep1_ids': ep1_ids,
        'ep1_cases': ep1_cases,
        'cluster_df': cluster_df,
        'tracks_df': tracks_df,
        'genesis_df': genesis_ep1,
    }


# ============================================================================
# COMPUTE DOMINANCE (intensification-phase mean of each subterm)
# ============================================================================

def _get_intensif_window(track_id: str, ep1_cases: pd.DataFrame) -> tuple | None:
    """
    Return (t_start, t_end) for intensification phase.
    Primary source: ep1_cases DataFrame.
    Fallback: Zenodo periods.csv.
    """
    row = ep1_cases[ep1_cases['track_id'] == track_id]
    if len(row) > 0:
        r = row.iloc[0]
        return pd.Timestamp(r['intensification_start']), pd.Timestamp(r['intensification_end'])

    # Fallback: Zenodo
    zenodo_lec_dir = ZENODO_DIR / f'{track_id}_ERA5_track'
    fp = _resolve_csv(zenodo_lec_dir / 'periods.csv')
    if fp is None:
        return None
    try:
        periods = pd.read_csv(fp, index_col=0)
        if 'intensification' not in periods.index:
            return None
        row_z = periods.loc['intensification']
        return pd.Timestamp(row_z['start']), pd.Timestamp(row_z['end'])
    except Exception:
        return None


def compute_dominance(ep1_ids: list, ep1_cases: pd.DataFrame) -> pd.DataFrame:
    """
    For each EP1 cyclone with new LEC data, compute:
      - intensification-phase mean of each vertically-integrated subterm
      - dominant subterm (most negative)
      - dominance margin

    Returns DataFrame indexed by track_id.
    """
    records = []
    n_missing = 0
    n_no_window = 0

    for track_id in ep1_ids:
        lec_dir = NEW_LEC_DIR / f'{track_id}_ERA5_track'
        if not lec_dir.exists():
            n_missing += 1
            continue

        # Get intensification window
        window = _get_intensif_window(track_id, ep1_cases)
        if window is None:
            n_no_window += 1
            continue
        t0, t1 = window

        # Load main results for Ck_total
        main_csv = lec_dir / f'{track_id}_ERA5_track_results.csv'
        ck_total_new = np.nan
        if main_csv.exists():
            try:
                df_main = pd.read_csv(main_csv, index_col=0, parse_dates=True)
                sub_main = df_main.loc[(df_main.index >= t0) & (df_main.index <= t1)]
                if 'Ck' in df_main.columns and len(sub_main) > 0:
                    ck_total_new = sub_main['Ck'].mean()
            except Exception as e:
                print(f'  WARNING: could not read main CSV for {track_id}: {e}')

        # Load each subterm
        subterm_means = {}
        subterm_ok = True
        for k in SUBTERM_KEYS:
            csv_path = lec_dir / 'results_vertical_levels' / f'{k}_pressure_level.csv'
            if not csv_path.exists():
                subterm_ok = False
                break
            try:
                df_lev = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                sub = df_lev.loc[(df_lev.index >= t0) & (df_lev.index <= t1)]
                if len(sub) == 0:
                    subterm_ok = False
                    break
                integrated = _vertically_integrate(sub)
                subterm_means[k] = integrated.mean()
            except Exception as e:
                print(f'  WARNING: subterm {k} for {track_id}: {e}')
                subterm_ok = False
                break

        if not subterm_ok:
            n_missing += 1
            continue

        vals = np.array([subterm_means[k] for k in SUBTERM_KEYS])
        subterms_sum = vals.sum()

        # Dominant subterm = the one with the minimum (most negative) value.
        # Sign convention (paper.tex): C_K < 0 → K_E → K_Z (eddies transfer energy
        # to the mean flow).  EP1 cyclones have large negative C_K, so the dominant
        # subterm is the one driving this eddy-to-mean-flow energy export most strongly.
        dom_idx = int(np.argmin(vals))
        dom_key = SUBTERM_KEYS[dom_idx]

        # Second most negative
        sorted_idx = np.argsort(vals)
        margin = abs(vals[sorted_idx[0]] - vals[sorted_idx[1]])

        # Normalized subterms (by absolute sum, for relative comparison)
        abs_sum = np.sum(np.abs(vals))
        norms = vals / abs_sum if abs_sum > 0 else vals * 0.0

        # Zenodo Ck (for validation table)
        ck_zenodo_raw = np.nan
        ck_zenodo_corrected = np.nan
        zenodo_dir = ZENODO_DIR / f'{track_id}_ERA5_track'
        if zenodo_dir.exists():
            zenodo_fp = _resolve_csv(zenodo_dir / f'{track_id}_ERA5_track_results.csv')
            if zenodo_fp is not None:
                try:
                    df_zen = pd.read_csv(zenodo_fp, index_col=0, parse_dates=True)
                    zen_window = _get_intensif_window(track_id, ep1_cases)
                    if zen_window and 'Ck' in df_zen.columns:
                        zt0, zt1 = zen_window
                        sub_zen = df_zen.loc[(df_zen.index >= zt0) & (df_zen.index <= zt1)]
                        if len(sub_zen) > 0:
                            ck_zenodo_raw = sub_zen['Ck'].mean()
                            ck_zenodo_corrected = ck_zenodo_raw / GRAVITY
                except Exception as e:
                    print(f'  WARNING: Zenodo CSV for {track_id}: {e}')

        rec = {
            'track_id': track_id,
            'Ck_total_new': ck_total_new,
            'Ck_total_zenodo': ck_zenodo_raw,
            'Ck_total_zenodo_corrected': ck_zenodo_corrected,
            'dominant_subterm': dom_key,
            'dominance_margin': margin,
            'subterms_sum': subterms_sum,
        }
        for k in SUBTERM_KEYS:
            rec[f'{k}_intensif'] = subterm_means[k]
        for i, k in enumerate(SUBTERM_KEYS):
            rec[f'{k}_norm'] = norms[i]

        records.append(rec)

    print(f'  Dominance computed for {len(records)} cyclones')
    print(f'  Missing LEC data or no window: {n_missing + n_no_window}')
    return pd.DataFrame(records)


# ============================================================================
# VALIDATE Ck
# ============================================================================

def validate_ck(dom_df: pd.DataFrame) -> dict:
    """
    Compare new Ck total vs Zenodo corrected Ck.

    Returns dict with validation statistics.
    """
    valid = dom_df.dropna(subset=['Ck_total_new', 'Ck_total_zenodo_corrected']).copy()
    valid['residual'] = valid['Ck_total_new'] - valid['Ck_total_zenodo_corrected']
    valid['rel_error_pct'] = (
        (valid['residual'].abs() / valid['Ck_total_zenodo_corrected'].abs().replace(0, np.nan)) * 100
    )
    within_tol = (valid['rel_error_pct'] <= TOLERANCE_PCT).sum()
    dominance_counts = dom_df['dominant_subterm'].value_counts().to_dict()

    stats = {
        'n_ep1_total': len(dom_df) + (len(dom_df) - len(dom_df)),  # will be set later
        'n_ep1_with_new_lec': len(dom_df),
        'n_valid': len(valid),
        'n_invalid': len(dom_df) - len(valid),
        'mean_ck_zenodo_corrected': valid['Ck_total_zenodo_corrected'].mean(),
        'mean_ck_new': valid['Ck_total_new'].mean(),
        'mean_subterm_sum': valid['subterms_sum'].mean(),
        'mean_residual': valid['residual'].mean(),
        'mean_rel_error_pct': valid['rel_error_pct'].mean(),
        'tolerance_pct': TOLERANCE_PCT,
        'n_within_tolerance': int(within_tol),
        'dominance_counts_per_subterm': str(dominance_counts),
    }
    return stats


# ============================================================================
# FIGURE 1a: BOXPLOTS — Ck SUBTERMS (shared y-axis)
# ============================================================================

def create_figure_boxplots_subterms(dom_df: pd.DataFrame):
    """
    1×5 boxplot figure: one panel per Ck subterm (A–E), shared y-axis.

    All panels share the same y-axis so inter-subterm magnitude comparisons
    are visually unambiguous.  Values are intensification-phase means
    (vertically integrated, W m⁻²).

    Sign convention (from paper.tex Eq. C_K):
      C_K < 0 → K_E → K_Z  (eddies transfer energy to mean flow)
      C_K > 0 → K_Z → K_E  (mean flow transfers energy to eddies; barotropic instability)
    EP1 cyclones exhibit large negative C_K during intensification.
    """
    print('[Fig 1a] Creating Ck subterms boxplots (shared y-axis)...')

    fig, axes = plt.subplots(1, 5, figsize=(12, 4), sharey=True)

    for i, (key, label, color, desc) in enumerate(
            zip(SUBTERM_KEYS, SUBTERM_LABELS, SUBTERM_COLORS, SUBTERM_DESCRIPTIONS)):
        ax = axes[i]
        col = f'{key}_intensif'
        data = dom_df[col].dropna().values

        if len(data) == 0:
            ax.set_title(label, fontsize=11, fontweight='bold')
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                    ha='center', va='center', fontsize=9, color='gray')
            continue

        ax.boxplot(
            data,
            vert=True,
            patch_artist=True,
            whis=[5, 95],
            showfliers=False,
            medianprops=dict(color='black', linewidth=2),
            boxprops=dict(facecolor=color, alpha=0.75),
            whiskerprops=dict(color='gray', linewidth=1.2),
            capprops=dict(color='gray', linewidth=1.2),
        )

        ax.axhline(0, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.set_ylabel('W m⁻²' if i == 0 else '')
        ax.set_xticks([])
        ax.text(0.95, 0.97, f'n={len(data)}',
                transform=ax.transAxes, ha='right', va='top', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        ax.grid(True, axis='y', alpha=0.3, linestyle=':')

    fig.suptitle(
        'Ck subterms (A–E) during EP1 intensification phase\n'
        '(Shared y-axis; whiskers = 5th–95th percentile)',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()

    out = FIGURES_DIR / 'ck_subterms_boxplots_subterms.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')
    return out


# ============================================================================
# FIGURE 1b: BOXPLOT — Total Ck
# ============================================================================

def create_figure_boxplots_total(dom_df: pd.DataFrame):
    """
    Single boxplot for total C_K during EP1 intensification phase.

    Separated from the subterm figure so the total can be compared at
    a different scale without compressing the subterm view.

    Sign convention: C_K < 0 → K_E → K_Z (eddies export energy to mean flow).
    """
    print('[Fig 1b] Creating total Ck boxplot...')

    data = dom_df['Ck_total_new'].dropna().values

    fig, ax = plt.subplots(1, 1, figsize=(3.5, 4))

    if len(data) > 0:
        ax.boxplot(
            data,
            vert=True,
            patch_artist=True,
            whis=[5, 95],
            showfliers=False,
            medianprops=dict(color='black', linewidth=2),
            boxprops=dict(facecolor='#555555', alpha=0.75),
            whiskerprops=dict(color='gray', linewidth=1.2),
            capprops=dict(color='gray', linewidth=1.2),
        )
        ax.axhline(0, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
        ax.text(0.95, 0.97, f'n={len(data)}',
                transform=ax.transAxes, ha='right', va='top', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    else:
        ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                ha='center', va='center', fontsize=9, color='gray')

    ax.set_ylabel('W m⁻²')
    ax.set_title('C_K total', fontsize=11, fontweight='bold')
    ax.set_xticks([])
    ax.grid(True, axis='y', alpha=0.3, linestyle=':')

    fig.suptitle(
        'Total barotropic conversion (C_K)\nEP1 intensification phase\n'
        '(Whiskers = 5th–95th percentile)',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()

    out = FIGURES_DIR / 'ck_subterms_boxplots_total.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')
    return out


# ============================================================================
# FIGURE 2: GENESIS DENSITY MAPS
# ============================================================================

def create_figure_genesis_density(dom_df: pd.DataFrame, genesis_df: pd.DataFrame,
                                   tracks_df: pd.DataFrame):
    """
    2×3 panels: All EP1 genesis density + one per dominant subterm.

    Layout:
      (a) All EP1  |  (b) Ck⁽ᴬ⁾  |  (c) Ck⁽ᴮ⁾
      (d) Ck⁽ᶜ⁾   |  (e) Ck⁽ᴰ⁾  |  (f) Ck⁽ᴱ⁾

    All panels share a single colorbar (shared vmax = 95th-percentile of all
    valid densities combined). Empty panels (insufficient data) keep the same
    map geometry as populated panels to ensure uniform subplot dimensions.
    """
    print('[Fig 2] Creating genesis density maps...')

    genesis_df = genesis_df.copy()
    genesis_df['date'] = pd.to_datetime(genesis_df['date'])
    years = genesis_df['date'].dt.year
    num_years = int(years.max() - years.min() + 1)
    print(f'  Time span: {years.min()}–{years.max()} ({num_years} years)')

    merged = genesis_df.merge(dom_df[['track_id', 'dominant_subterm']], on='track_id', how='left')
    n_ep1_all = len(merged)

    # --- Pre-compute all densities to determine shared color scale ---
    density_all, longrd, latgrd = compute_density(merged, num_years)
    densities = {'all': density_all}
    sub_gens = {}
    for key in SUBTERM_KEYS:
        sub_ids = dom_df.loc[dom_df['dominant_subterm'] == key, 'track_id']
        sub_gen = merged[merged['track_id'].isin(sub_ids)]
        sub_gens[key] = sub_gen
        if len(sub_gen) >= 2:
            d, _, _ = compute_density(sub_gen, num_years)
            densities[key] = d

    # Shared vmax from 95th percentile across all valid density fields
    p95_vals = []
    for d in densities.values():
        pos = d[d > 0]
        if pos.size > 0:
            p95_vals.append(np.percentile(pos, 95))
    vmax_shared = float(np.max(p95_vals)) if p95_vals else 1.0
    # Ensure levels are strictly increasing after rounding
    raw_levels = np.linspace(0.0, vmax_shared, 12)
    levels_shared = np.unique(np.round(raw_levels, 2))
    if len(levels_shared) < 3:
        levels_shared = raw_levels  # fallback: no rounding

    # --- Create figure with explicit projection subplot grid ---
    fig, axes = plt.subplots(2, 3, figsize=(15, 9),
                             subplot_kw={'projection': ccrs.PlateCarree()},
                             constrained_layout=False)
    fig.subplots_adjust(hspace=0.35, wspace=0.08, bottom=0.12)

    panel_keys   = ['all'] + SUBTERM_KEYS
    panel_labels_alpha = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']
    panel_titles = (
        [f'All EP1 (N={n_ep1_all})']
        + [f'{lbl} dominant (N={len(sub_gens[k])})' for k, lbl in zip(SUBTERM_KEYS, SUBTERM_LABELS)]
    )

    cf_ref = None  # reference contourf for colorbar

    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    lon_r = longrd[lon_idx]
    lat_r = latgrd[lat_idx]

    for i, (pk, alpha, title) in enumerate(zip(panel_keys, panel_labels_alpha, panel_titles)):
        ax = axes.ravel()[i]
        full_title = f'{alpha} {title}'
        d = densities.get(pk)

        # Always set up the map so all panels have identical geometry
        setup_map_axes(ax, full_title)

        if d is None:
            # Insufficient data — blank map, same size
            ax.text(0.5, 0.5, 'Insufficient data', transform=ax.transAxes,
                    ha='center', va='center', fontsize=10, color='gray',
                    bbox=dict(facecolor='white', alpha=0.6, edgecolor='gray', boxstyle='round,pad=0.3'))
        else:
            d_region = d[np.ix_(lat_idx, lon_idx)]
            cf = ax.contourf(lon_r, lat_r, d_region,
                             levels=levels_shared, cmap='YlOrRd',
                             transform=ccrs.PlateCarree(), extend='max', alpha=0.8)
            ax.contour(lon_r, lat_r, d_region,
                       levels=6, colors='black', linewidths=0.5,
                       transform=ccrs.PlateCarree(), alpha=0.6)
            cf_ref = cf

    # Single shared colorbar below all panels
    if cf_ref is not None:
        cbar_ax = fig.add_axes([0.15, 0.05, 0.70, 0.025])
        cbar = fig.colorbar(cf_ref, cax=cbar_ax, orientation='horizontal', extend='max')
        cbar.set_label('Cyclones per 10⁶ km² per year', fontsize=10)
        cbar.set_ticks(levels_shared[::2])
        cbar.set_ticklabels([f'{lev:.1f}' for lev in levels_shared[::2]])
        cbar.ax.tick_params(labelsize=9)

    fig.suptitle('EP1 cyclone genesis density by dominant Ck subterm',
                 fontsize=13, fontweight='bold', y=0.98)

    out = FIGURES_DIR / 'ck_subterms_genesis_density.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')
    return out


# ============================================================================
# FIGURE 3: NORMALIZED DIFFERENCE MAPS
# ============================================================================

def create_figure_normalized_diff(dom_df: pd.DataFrame, genesis_df: pd.DataFrame):
    """
    1×5 panels: normalized genesis density anomaly per dominant subterm.

    Formula: norm_EP − norm_All  (minmax normalization on positive values)
    where norm_All = minmax_normalize_positive(density_all_EP1).

    This is the exact same normalization used in 06_figure_genesis_density_kde.py.
    Positive (red) = enhanced genesis for this subterm; negative (blue) = suppressed.

    Empty panels (insufficient data) render the full map geometry with a blank
    field so that subplot size is identical across all panels.  A single shared
    colorbar spans a symmetric range derived from the largest anomaly across
    all valid panels.
    """
    print('[Fig 3] Creating normalized-difference maps...')

    genesis_df = genesis_df.copy()
    genesis_df['date'] = pd.to_datetime(genesis_df['date'])
    years = genesis_df['date'].dt.year
    num_years = int(years.max() - years.min() + 1)

    merged = genesis_df.merge(dom_df[['track_id', 'dominant_subterm']], on='track_id', how='left')

    density_all, longrd, latgrd = compute_density(merged, num_years)
    norm_all = minmax_normalize_positive(density_all)

    # Pre-compute anomaly fields (or None if insufficient data)
    anomalies = {}
    max_abs_list = []
    for key in SUBTERM_KEYS:
        sub_ids = dom_df.loc[dom_df['dominant_subterm'] == key, 'track_id']
        sub_gen = merged[merged['track_id'].isin(sub_ids)]
        if len(sub_gen) < 2:
            anomalies[key] = None
        else:
            density_ep, _, _ = compute_density(sub_gen, num_years)
            rel_anom = minmax_normalize_positive(density_ep) - norm_all
            anomalies[key] = rel_anom
            max_abs_list.append(np.nanmax(np.abs(rel_anom)))

    # Shared colorbar range
    maxabs_shared = float(np.max(max_abs_list)) if max_abs_list else 0.5

    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    lon_r = longrd[lon_idx]
    lat_r = latgrd[lat_idx]

    fig, axes = plt.subplots(1, 5, figsize=(20, 4),
                             subplot_kw={'projection': ccrs.PlateCarree()},
                             constrained_layout=False)
    fig.subplots_adjust(wspace=0.08, bottom=0.22)

    panel_labels_alpha = ['(a)', '(b)', '(c)', '(d)', '(e)']
    cf_ref = None
    norm_div = TwoSlopeNorm(vcenter=0.0, vmin=-maxabs_shared, vmax=maxabs_shared)
    levels_div = np.linspace(-maxabs_shared, maxabs_shared, 13)

    for i, (key, label) in enumerate(zip(SUBTERM_KEYS, SUBTERM_LABELS)):
        ax = axes[i]
        sub_ids = dom_df.loc[dom_df['dominant_subterm'] == key, 'track_id']
        n_sub = len(sub_ids)
        title = f'{panel_labels_alpha[i]} {label} − All EP1 (N={n_sub})'

        # Always set up map axes to guarantee identical panel geometry
        setup_map_axes(ax, title)

        rel_anom = anomalies[key]
        if rel_anom is None:
            # Blank map — same size as populated panels
            ax.text(0.5, 0.5, 'Insufficient data', transform=ax.transAxes,
                    ha='center', va='center', fontsize=10, color='gray',
                    bbox=dict(facecolor='white', alpha=0.6, edgecolor='gray', boxstyle='round,pad=0.3'))
        else:
            masked = np.ma.masked_invalid(rel_anom[np.ix_(lat_idx, lon_idx)])
            cf = ax.contourf(lon_r, lat_r, masked,
                             levels=levels_div, cmap='RdBu_r', norm=norm_div,
                             transform=ccrs.PlateCarree(), extend='both', alpha=0.8)
            ax.contour(lon_r, lat_r, masked,
                       levels=7, colors='black', linewidths=0.4,
                       transform=ccrs.PlateCarree(), alpha=0.6)
            cf_ref = cf

    # Single shared diverging colorbar below all panels
    if cf_ref is not None:
        cbar_ax = fig.add_axes([0.15, 0.07, 0.70, 0.04])
        cbar = fig.colorbar(cf_ref, cax=cbar_ax, orientation='horizontal', extend='both')
        cbar.set_label('Normalized genesis density anomaly (norm_EP − norm_All)', fontsize=9)
        ticks = np.linspace(-maxabs_shared, maxabs_shared, 5)
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f'{t:.2f}' for t in ticks])
        cbar.ax.tick_params(labelsize=9)

    fig.suptitle('Normalized genesis density anomaly per dominant Ck subterm',
                 fontsize=12, fontweight='bold', y=0.98)

    out = FIGURES_DIR / 'ck_subterms_genesis_normaldiff.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')
    return out
    print(f'  Saved: {out}')
    return out


# ============================================================================
# FIGURE 4: FULL TRACKS
# ============================================================================

def create_figure_tracks(dom_df: pd.DataFrame, ep1_cases: pd.DataFrame,
                          tracks_df: pd.DataFrame):
    """2×3 panels: all EP1 tracks + per dominant subterm."""
    print('[Fig 4] Creating full tracks figure...')

    LON_T_MIN, LON_T_MAX = -80, 10
    LAT_T_MIN, LAT_T_MAX = -65, -15

    # Build intensification windows dict
    win_dict = {}
    for _, row in ep1_cases.iterrows():
        win_dict[row['track_id']] = (
            pd.Timestamp(row['intensification_start']),
            pd.Timestamp(row['intensification_end']),
        )

    fig = plt.figure(figsize=(18, 10))
    panel_labels_alpha = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']
    all_ep1_ids = dom_df['track_id'].unique()

    def _draw_tracks(ax, sel_ids, color_intens, title, show_all=False, all_ids=None):
        ax.set_extent([LON_T_MIN, LON_T_MAX, LAT_T_MIN, LAT_T_MAX], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
        ax.add_feature(cfeature.OCEAN, facecolor='white')
        ax.coastlines(resolution='50m', linewidth=0.5, color='black')
        ax.add_feature(cfeature.BORDERS, linewidth=0.4, edgecolor='black', linestyle=':')
        gl = ax.gridlines(draw_labels=True, linewidth=0.4, color='gray',
                          alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}
        ax.set_title(title, fontsize=11, fontweight='bold', loc='left')

        # Background: all EP1 tracks (gray) if show_all
        bg_ids = all_ids if show_all else []
        if bg_ids is None:
            bg_ids = []
        for tid in bg_ids:
            t = tracks_df[tracks_df['track_id'] == tid].sort_values('date')
            if len(t) == 0:
                continue
            ax.plot(t['lon vor'].values, t['lat vor'].values,
                    color='gray', linewidth=0.5, alpha=0.25,
                    transform=ccrs.PlateCarree(), zorder=1)

        # Highlighted tracks
        for tid in sel_ids:
            t = tracks_df[tracks_df['track_id'] == tid].sort_values('date')
            if len(t) == 0:
                continue
            t['date'] = pd.to_datetime(t['date'])
            ax.plot(t['lon vor'].values, t['lat vor'].values,
                    color=color_intens, linewidth=0.8, alpha=0.5,
                    transform=ccrs.PlateCarree(), zorder=2)

            # Intensification phase
            w = win_dict.get(tid)
            if w:
                t_int = t[(t['date'] >= w[0]) & (t['date'] <= w[1])]
                if len(t_int) > 0:
                    ax.plot(t_int['lon vor'].values, t_int['lat vor'].values,
                            color='gold', linewidth=1.5, alpha=0.85,
                            transform=ccrs.PlateCarree(), zorder=3)

            # Genesis
            ax.plot(t['lon vor'].iloc[0], t['lat vor'].iloc[0],
                    'o', color='green', markersize=3, markeredgecolor='k',
                    markeredgewidth=0.3, transform=ccrs.PlateCarree(), zorder=4)
            # Lysis
            ax.plot(t['lon vor'].iloc[-1], t['lat vor'].iloc[-1],
                    'x', color='red', markersize=3, markeredgewidth=0.8,
                    transform=ccrs.PlateCarree(), zorder=4)

    # Panel 1: All EP1
    ax0 = fig.add_subplot(2, 3, 1, projection=ccrs.PlateCarree())
    _draw_tracks(ax0, all_ep1_ids, 'steelblue',
                 f'{panel_labels_alpha[0]} All EP1 (N={len(all_ep1_ids)})')

    # Panels 2–6: per dominant subterm
    for i, (key, label, color) in enumerate(zip(SUBTERM_KEYS, SUBTERM_LABELS, SUBTERM_COLORS)):
        ax = fig.add_subplot(2, 3, i + 2, projection=ccrs.PlateCarree())
        sub_ids = dom_df.loc[dom_df['dominant_subterm'] == key, 'track_id'].values
        _draw_tracks(ax, sub_ids, color,
                     f'{panel_labels_alpha[i+1]} {label} dominant (N={len(sub_ids)})',
                     show_all=True, all_ids=all_ep1_ids)

    # Legend
    legend_elements = [
        Line2D([0], [0], color='gray', linewidth=1.5, alpha=0.5, label='All EP1 tracks'),
        Line2D([0], [0], color='gold', linewidth=2, label='Intensification phase'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
               markersize=6, markeredgecolor='k', label='Genesis'),
        Line2D([0], [0], marker='x', color='red', markersize=6,
               markeredgewidth=1.5, label='Lysis'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=4,
               fontsize=10, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

    plt.suptitle('EP1 cyclone tracks by dominant Ck subterm', fontsize=13, fontweight='bold')
    plt.tight_layout()

    out = FIGURES_DIR / 'ck_subterms_tracks.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')
    return out


# ============================================================================
# WRITE TABLES
# ============================================================================

def write_tables(dom_df: pd.DataFrame, data: dict, val_stats: dict):
    """Write Table 1 and Table 2."""
    print('[Tables] Writing output tables...')

    ep1_cases = data['ep1_cases']
    genesis_df = data['genesis_df']

    # --- Table 1 ---
    gen_cols = genesis_df[['track_id', 'lat vor', 'lon vor', 'date']].copy()
    gen_cols = gen_cols.rename(columns={'lat vor': 'genesis_lat', 'lon vor': 'genesis_lon',
                                        'date': 'genesis_date'})

    # EP column from cluster (cluster 0 = EP1 = 1)
    gen_cols['EP'] = 1

    # Season
    gen_cols['season'] = gen_cols['genesis_date'].apply(_get_season)

    # Duration and intensification from ep1_cases
    cases_sub = ep1_cases[['track_id', 'duration_hours', 'intensification_start',
                            'intensification_end']].copy()

    table1 = gen_cols.merge(cases_sub, on='track_id', how='left')
    table1 = table1.merge(dom_df, on='track_id', how='left')

    # Reorder columns per spec
    keep = [
        'track_id', 'EP', 'genesis_lat', 'genesis_lon', 'genesis_date',
        'season', 'duration_hours', 'intensification_start', 'intensification_end',
        'Ck_total_new', 'Ck_total_zenodo', 'Ck_total_zenodo_corrected',
        'Ck_1_intensif', 'Ck_2_intensif', 'Ck_3_intensif', 'Ck_4_intensif', 'Ck_5_intensif',
        'subterms_sum', 'dominant_subterm', 'dominance_margin',
        'Ck_1_norm', 'Ck_2_norm', 'Ck_3_norm', 'Ck_4_norm', 'Ck_5_norm',
    ]
    keep = [c for c in keep if c in table1.columns]
    table1 = table1[keep]
    out1 = RESULTS_DIR / 'ep1_ck_subterms_per_cyclone.csv'
    table1.to_csv(out1, index=False)
    print(f'  Table 1 saved: {out1} ({len(table1)} rows)')

    # --- Table 2 ---
    val_stats['n_ep1_total'] = len(data['ep1_ids'])
    table2 = pd.DataFrame([val_stats])
    out2 = RESULTS_DIR / 'validation_summary.csv'
    table2.to_csv(out2, index=False)
    print(f'  Table 2 saved: {out2}')

    return table1


# ============================================================================
# WRITE DIAGNOSTIC
# ============================================================================

def write_diagnostic(dom_df: pd.DataFrame, val_stats: dict, data: dict):
    """Write diagnostic_summary.txt."""
    out = RESULTS_DIR / 'diagnostic_summary.txt'

    dominance_counts = dom_df['dominant_subterm'].value_counts().sort_index()

    lines = [
        '=' * 70,
        'DIAGNOSTIC SUMMARY: Ck Subterms Analysis (EP1 cyclones)',
        '=' * 70,
        '',
        '-- DATA LOADED --',
        f"EP1 cyclones (cluster 0): {val_stats['n_ep1_total']}",
        f"EP1 with new LEC results: {val_stats['n_ep1_with_new_lec']}",
        f"EP1 with intensification phase: {len(data['ep1_cases'])}",
        f"Phase source: results/ep1_full/all_ep1_cases.csv (primary)",
        f"              data/temp_lec_zenodo/.../periods.csv (fallback)",
        '',
        '-- CORRECTIONS APPLIED --',
        'New LEC (results/ck_analysis/lec_results/):',
        '  - Ck_total from *_results.csv: NO gravity correction (already integrated)',
        '  - Ck subterms from results_vertical_levels/: vertical integration',
        '    formula: sum(df.values * dp / g) where g=9.8 m/s²',
        'Zenodo LEC (data/temp_lec_zenodo/):',
        '  - Ck_total: DIVIDE by g=9.8 (gravity correction)',
        '  - Ca: sign inversion (not applied here)',
        '',
        '-- VALIDATION RESULTS --',
        f"Cyclones with both new and Zenodo Ck: {val_stats['n_valid']}",
        f"Mean Ck (Zenodo, corrected): {val_stats['mean_ck_zenodo_corrected']:.4f} W/m²",
        f"Mean Ck (new LEC): {val_stats['mean_ck_new']:.4f} W/m²",
        f"Mean subterm sum: {val_stats['mean_subterm_sum']:.4f} W/m²",
        f"Mean residual (new - zenodo_corrected): {val_stats['mean_residual']:.4f} W/m²",
        f"Mean relative error: {val_stats['mean_rel_error_pct']:.2f}%",
        f"Within {val_stats['tolerance_pct']:.0f}% tolerance: {val_stats['n_within_tolerance']} / {val_stats['n_valid']}",
        '',
        '-- DOMINANCE CLASSIFICATION --',
        'Sign convention (paper.tex): C_K < 0 → K_E → K_Z (eddies transfer energy to mean flow).',
        '                             C_K > 0 → K_Z → K_E (barotropic instability).',
        'EP1 cyclones have large negative C_K (they are strong energy exporters).',
        'Method: dominant subterm = subterm with minimum (most negative) intensification-phase mean',
        '        i.e. the subterm driving eddy-to-mean-flow energy transfer most strongly.',
        'Dominance margin: |dominant value − second most negative value|',
        '',
        'Dominance counts per subterm:',
    ]
    for k, v in dominance_counts.items():
        idx = SUBTERM_KEYS.index(k) if k in SUBTERM_KEYS else -1
        lbl = SUBTERM_LABELS[idx] if idx >= 0 else k
        desc = SUBTERM_DESCRIPTIONS[idx] if idx >= 0 else ''
        lines.append(f"  {k} ({lbl}): {v} cyclones  — {desc}")

    lines += [
        '',
        '-- OUTPUT FILES --',
        f"Table 1: results/ck_subterms/ep1_ck_subterms_per_cyclone.csv",
        f"Table 2: results/ck_subterms/validation_summary.csv",
        f"Fig 1a:  figures/ck_subterms/ck_subterms_boxplots_subterms.png",
        f"Fig 1b:  figures/ck_subterms/ck_subterms_boxplots_total.png",
        f"Fig 2:   figures/ck_subterms/ck_subterms_genesis_density.png",
        f"Fig 3:   figures/ck_subterms/ck_subterms_genesis_normaldiff.png",
        f"Fig 4:   figures/ck_subterms/ck_subterms_tracks.png",
        '=' * 70,
    ]

    with open(out, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'  Diagnostic saved: {out}')


# ============================================================================
# MAIN
# ============================================================================

def main():
    print('=' * 70)
    print('STEP 3: Ck Subterms Validation and Figures')
    print('=' * 70)

    # 1. Load data
    print('\n[1/7] Loading data...')
    data = load_data()

    # 2. Compute dominance
    print('\n[2/7] Computing dominance classification...')
    dom_df = compute_dominance(data['ep1_ids'], data['ep1_cases'])
    if len(dom_df) == 0:
        print('ERROR: No cyclones with complete subterm data. Exiting.')
        return

    # 3. Validate
    print('\n[3/7] Validating Ck...')
    val_stats = validate_ck(dom_df)
    val_stats['n_ep1_total'] = len(data['ep1_ids'])
    print(f"  Mean relative error: {val_stats['mean_rel_error_pct']:.2f}%")
    print(f"  Within {TOLERANCE_PCT:.0f}% tolerance: "
          f"{val_stats['n_within_tolerance']} / {val_stats['n_valid']}")
    print(f"  Dominant subterm distribution:")
    for k, v in dom_df['dominant_subterm'].value_counts().sort_index().items():
        print(f"    {k}: {v}")

    # 4. Figures 1a & 1b: Boxplots
    print('\n[4/7] Figure 1: Boxplots...')
    create_figure_boxplots_subterms(dom_df)
    create_figure_boxplots_total(dom_df)

    # 5. Figures 2 & 3: Genesis density
    print('\n[5/7] Figure 2: Genesis density maps...')
    create_figure_genesis_density(dom_df, data['genesis_df'], data['tracks_df'])

    print('\n[5b/7] Figure 3: Normalized-difference maps...')
    create_figure_normalized_diff(dom_df, data['genesis_df'])

    # 6. Figure 4: Tracks
    print('\n[6/7] Figure 4: Full tracks...')
    create_figure_tracks(dom_df, data['ep1_cases'], data['tracks_df'])

    # 7. Write tables and diagnostic
    print('\n[7/7] Writing tables and diagnostics...')
    write_tables(dom_df, data, val_stats)
    write_diagnostic(dom_df, val_stats, data)

    # Regenerate figures manifest
    print('\nRegenerating figures manifest...')
    subprocess.run(
        ['python3', str(BASE_DIR / 'scripts/web/build_site_manifest.py')],
        check=False
    )

    print('\n' + '=' * 70)
    print('STEP 3 COMPLETE')
    print(f"  Figures: {FIGURES_DIR}")
    print(f"  Results: {RESULTS_DIR}")
    print('=' * 70)


if __name__ == '__main__':
    main()
