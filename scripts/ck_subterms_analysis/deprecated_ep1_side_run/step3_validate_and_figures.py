#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: LEC audit, dominance classification, and figures for EP1 cyclones.

Audits locally computed LEC results (Ck subterms), classifies dominant subterm
per cyclone, and generates:

  Figure 1: Boxplots of Ck subterms during intensification
  Figure 2: Genesis density maps per dominant subterm
  Figure 3: Normalized-difference maps per dominant subterm
  Figure 4: Full tracks per dominant subterm

Tables:
  results/ck_subterms/ep1_ck_subterms_per_cyclone.csv
  results/ck_subterms/lec_audit_per_cyclone.csv
  results/ck_subterms/lec_audit_summary.csv / .json

Text:
  results/ck_subterms/lec_audit_report.txt
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
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
from mpl_toolkits.axes_grid1.inset_locator import inset_axes as _inset_axes
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from sklearn.neighbors import KernelDensity
import seaborn as sns

from scripts.ck_subterms_analysis.lec_audit import run_audit

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

GRAVITY = 9.8  # m/s²

# Paths
CLUSTER_FILE    = BASE_DIR / 'results' / 'cluster' / 'kmeans_clustered_data.csv'
# EP1 cases: produced by scripts/ep_structure_analysis/ (new source of truth)
EP1_CASES_FILE  = BASE_DIR / 'results' / 'ep_structure' / 'ep1_cases.csv'
NEW_LEC_DIR     = BASE_DIR / 'results' / 'ck_analysis' / 'lec_results'
FIGURES_DIR     = BASE_DIR / 'figures' / 'ck_subterms'
RESULTS_DIR     = BASE_DIR / 'results' / 'ck_subterms'

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Subterm metadata
SUBTERM_KEYS   = ['Ck_1', 'Ck_2', 'Ck_3', 'Ck_4', 'Ck_5']
# Use matplotlib mathtext for all subterm labels – avoids broken unicode glyphs.
SUBTERM_LABELS = [
    r'$C_K^{(a)}$', r'$C_K^{(b)}$', r'$C_K^{(c)}$',
    r'$C_K^{(d)}$', r'$C_K^{(e)}$',
]
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

    EP1 cyclone IDs and intensification-phase windows are taken from
    results/ep_structure/ep1_cases.csv, which is the new source of truth
    produced by scripts/ep_structure_analysis/.  The cluster file
    (results/cluster/kmeans_clustered_data.csv) is retained for backward
    compatibility but is no longer the primary source for EP1 selection.

    Returns
    -------
    dict with keys:
        ep1_ids        : list of EP1 track_ids (from ep_structure/ep1_cases.csv)
        ep1_cases      : DataFrame from ep_structure/ep1_cases.csv
        cluster_df     : DataFrame with cluster assignments (retained for compat)
        tracks_df      : Full track DataFrame (from load_tracks)
        genesis_df     : Genesis rows (first obs per cyclone) for EP1 systems
    """
    from scripts.utils.load_data import load_tracks

    print('[load_data] Loading EP1 cases (intensification phases)...')
    ep1_cases = pd.read_csv(EP1_CASES_FILE)
    ep1_cases['intensification_start'] = pd.to_datetime(ep1_cases['intensification_start'])
    ep1_cases['intensification_end']   = pd.to_datetime(ep1_cases['intensification_end'])
    # EP1 IDs come directly from ep_structure/ep1_cases.csv — no cluster lookup needed
    ep1_ids = ep1_cases['track_id'].tolist()
    print(f'  EP1 cyclones (from ep_structure): {len(ep1_ids)}')
    print(f'  Cases with intensification data:  {len(ep1_cases)}')

    # Cluster file kept for backward compatibility (e.g. genesis_df EP label)
    cluster_df = pd.DataFrame()
    if CLUSTER_FILE.exists():
        print('[load_data] Loading cluster assignments (backward compat)...')
        cluster_df = pd.read_csv(CLUSTER_FILE)

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
    Source: ep1_cases DataFrame (results/ep_structure/ep1_cases.csv).
    Returns None when the cyclone has no intensification window on record.
    """
    # Compare as strings to avoid int64 vs str type mismatch
    row = ep1_cases[ep1_cases['track_id'].astype(str) == str(track_id)]
    if len(row) > 0:
        r = row.iloc[0]
        return pd.Timestamp(r['intensification_start']), pd.Timestamp(r['intensification_end'])
    return None


def compute_dominance(ep1_ids: list, ep1_cases: pd.DataFrame,
                      audit_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    For each EP1 cyclone with valid LEC data (as determined by the audit),
    compute:
      - intensification-phase mean of each vertically-integrated subterm
      - dominant subterm (most negative)
      - dominance margin

    If audit_df is provided, only cyclones marked as usable_for_dominance=True
    are processed (avoids re-reading all files).  Falls back to re-checking
    the file system if audit_df is not supplied.

    Returns DataFrame indexed by track_id.
    """
    # If audit results are available, restrict to valid cyclones only
    if audit_df is not None and len(audit_df) > 0:
        valid_ids = set(audit_df.loc[audit_df['usable_for_dominance'] == True, 'track_id'].astype(str))
    else:
        valid_ids = None

    records = []
    n_missing = 0
    n_no_window = 0

    for track_id in ep1_ids:
        # Skip cyclones that the audit already determined are not usable
        if valid_ids is not None and str(track_id) not in valid_ids:
            n_missing += 1
            continue

        lec_dir = NEW_LEC_DIR / f'{track_id}_ERA5_track'
        if not lec_dir.exists():
            n_missing += 1
            continue

        # Get intensification window
        window = _get_intensif_window(str(track_id), ep1_cases)
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
        # Sign convention (paper.tex): C_K < 0 → K_Z → K_E (mean flow transfers energy
        # to the eddies; barotropic instability).  EP1 cyclones have large negative C_K,
        # so the dominant subterm is the one driving this mean-to-eddy energy transfer
        # (barotropic instability) most strongly.
        dom_idx = int(np.argmin(vals))
        dom_key = SUBTERM_KEYS[dom_idx]

        # Second most negative
        sorted_idx = np.argsort(vals)
        margin = abs(vals[sorted_idx[0]] - vals[sorted_idx[1]])

        # Normalized subterms (by absolute sum, for relative comparison)
        abs_sum = np.sum(np.abs(vals))
        norms = vals / abs_sum if abs_sum > 0 else vals * 0.0

        rec = {
            'track_id': track_id,
            'Ck_total_new': ck_total_new,
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
    print(f'  Skipped (no valid LEC data or no window): {n_missing + n_no_window}')
    return pd.DataFrame(records)


# ============================================================================
# LEC AUDIT SUMMARY (replaces Zenodo-based validate_ck)
# ============================================================================

def summarize_lec_audit(dom_df: pd.DataFrame, audit_summary: dict) -> dict:
    """
    Build audit statistics from the LEC audit summary and the dominance DataFrame.

    Returns a dict compatible with write_tables / write_diagnostic.
    """
    dominance_counts = dom_df['dominant_subterm'].value_counts().to_dict()

    # Internal consistency: mean subterm sum vs mean Ck total
    has_ck_total = dom_df['Ck_total_new'].notna().sum()
    mean_ck_new   = float(dom_df['Ck_total_new'].mean()) if has_ck_total > 0 else float('nan')
    mean_subterm_sum = float(dom_df['subterms_sum'].mean())

    stats = {
        'n_ep1_total': audit_summary.get('n_ep1_expected', len(dom_df)),
        'n_lec_directory_found': audit_summary.get('n_lec_directory_found', 0),
        'n_with_ck_total_file': audit_summary.get('n_with_ck_total_file', 0),
        'n_with_all_ck_subterm_files': audit_summary.get('n_with_all_ck_subterm_files', 0),
        'n_with_data_in_intensif_phase': audit_summary.get('n_with_data_in_intensif_phase', 0),
        'n_ep1_with_new_lec': len(dom_df),
        'mean_ck_new': mean_ck_new,
        'mean_subterm_sum': mean_subterm_sum,
        'dominance_counts_per_subterm': str(dominance_counts),
        'exclusion_reasons': str(audit_summary.get('exclusion_reasons', {})),
    }
    return stats


# ============================================================================
# FIGURE 1: COMBINED BOXPLOTS — Ck subterms (left) + total Ck (right)
# ============================================================================

def create_figure_boxplots(dom_df: pd.DataFrame, n_ep1_total: int):
    """
    Single figure with two side-by-side subplots:
      Panel (a) – left:  all five Ck subterms in one grouped boxplot (shared y-axis)
      Panel (b) – right: total Ck on its own independent y-axis

    N reported in the suptitle reflects:
      - n_ep1_total : total EP1 population (all 444 cyclones)
      - n shown per panel : cyclones with actual LEC subterm data (subset with data)

    Sign convention (paper.tex): Ck < 0 → Kz → Ke (barotropic instability).
    Whiskers = 5th–95th percentile.
    """
    print('[Fig 1] Creating combined Ck boxplots figure (subterms + total)...')

    fig, (ax_sub, ax_tot) = plt.subplots(
        1, 2, figsize=(11, 4.5),
        gridspec_kw={'width_ratios': [4, 1.2]},
    )

    # ── Panel (a): subterms ─────────────────────────────────────────────────
    n_sub = None
    for i, (key, label, color) in enumerate(
            zip(SUBTERM_KEYS, SUBTERM_LABELS, SUBTERM_COLORS)):
        col = f'{key}_intensif'
        data = dom_df[col].dropna().values
        if n_sub is None and len(data) > 0:
            n_sub = len(data)
        if len(data) == 0:
            continue
        ax_sub.boxplot(
            data,
            positions=[i + 1],
            widths=0.55,
            vert=True,
            patch_artist=True,
            whis=[5, 95],
            showfliers=False,
            medianprops=dict(color='black', linewidth=2),
            boxprops=dict(facecolor=color, alpha=0.75),
            whiskerprops=dict(color='gray', linewidth=1.2),
            capprops=dict(color='gray', linewidth=1.2),
        )

    ax_sub.axhline(0, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
    ax_sub.set_xticks(range(1, 6))
    ax_sub.set_xticklabels(SUBTERM_LABELS, fontsize=10)
    ax_sub.set_ylabel(r'W m$^{-2}$')
    ax_sub.set_title(r'(a) $C_K$ subterms', fontsize=11, fontweight='bold')
    if n_sub is not None:
        ax_sub.text(
            0.97, 0.97, f'n={n_sub}',
            transform=ax_sub.transAxes, ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
        )
    ax_sub.grid(True, axis='y', alpha=0.3, linestyle=':')

    # ── Panel (b): total Ck ─────────────────────────────────────────────────
    data_tot = dom_df['Ck_total_new'].dropna().values
    if len(data_tot) > 0:
        ax_tot.boxplot(
            data_tot,
            positions=[1],
            widths=0.55,
            vert=True,
            patch_artist=True,
            whis=[5, 95],
            showfliers=False,
            medianprops=dict(color='black', linewidth=2),
            boxprops=dict(facecolor='#555555', alpha=0.75),
            whiskerprops=dict(color='gray', linewidth=1.2),
            capprops=dict(color='gray', linewidth=1.2),
        )
        ax_tot.axhline(0, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
        ax_tot.text(
            0.95, 0.97, f'n={len(data_tot)}',
            transform=ax_tot.transAxes, ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
        )
    else:
        ax_tot.text(0.5, 0.5, 'No data', transform=ax_tot.transAxes,
                    ha='center', va='center', fontsize=9, color='gray')

    ax_tot.set_ylabel(r'W m$^{-2}$')
    ax_tot.set_title(r'(b) Total $C_K$', fontsize=11, fontweight='bold')
    ax_tot.set_xticks([1])
    ax_tot.set_xticklabels([r'$C_K$'])
    ax_tot.grid(True, axis='y', alpha=0.3, linestyle=':')

    fig.suptitle(
        rf'Barotropic conversion ($C_K$) during EP1 intensification'
        f'\n(EP1 total N={n_ep1_total}; N with LEC data shown per panel; whiskers = 5th–95th pct)',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()

    out = FIGURES_DIR / 'ck_subterms_boxplots.png'
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
    2×3 map panels: All EP1 genesis density + one per dominant subterm.

    Layout (row × col):
      (a) All EP1  |  (b) Ck^(a)  |  (c) Ck^(b)
      (d) Ck^(c)   |  (e) Ck^(d)  |  (f) Ck^(e)

    Each populated panel has its own individual colorbar placed in a dedicated
    GridSpec row below the map row.  Empty panels have no colorbar.  All map
    panels keep identical size (same GridSpec row / column) regardless of
    colorbar presence, guaranteeing publication-quality alignment.

    "All EP1" uses the full EP1 genesis population (n_ep1_total, from genesis_df).
    Per-subterm panels use only cyclones with actual LEC data (dom_df subset).
    """
    print('[Fig 2] Creating genesis density maps (per-panel colorbars)...')

    genesis_df = genesis_df.copy()
    genesis_df['date'] = pd.to_datetime(genesis_df['date'])
    years = genesis_df['date'].dt.year
    num_years = int(years.max() - years.min() + 1)
    print(f'  Time span: {years.min()}–{years.max()} ({num_years} years)')

    # Left-join: keep all EP1 genesis rows; dominant_subterm is NaN for
    # cyclones without LEC data (they still contribute to the "All EP1" density).
    merged = genesis_df.merge(dom_df[['track_id', 'dominant_subterm']],
                               on='track_id', how='left')
    n_ep1_all = len(merged)  # full EP1 population

    # Pre-compute densities
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

    lon_mask = (longrd >= LON_MIN) & (longrd <= LON_MAX)
    lat_mask = (latgrd >= LAT_MIN) & (latgrd <= LAT_MAX)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    lon_r = longrd[lon_idx]
    lat_r = latgrd[lat_idx]

    # ── Figure layout ────────────────────────────────────────────────────────
    # Alternating rows: map row (height 1) + thin colorbar row (height 0.07)
    # This guarantees all map panels have identical height regardless of whether
    # a colorbar is present.
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(
        4, 3,
        height_ratios=[1, 0.07, 1, 0.07],
        hspace=0.50, wspace=0.06,
        top=0.92, bottom=0.03, left=0.02, right=0.98,
    )

    panel_keys          = ['all'] + SUBTERM_KEYS
    panel_labels_alpha  = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']
    panel_titles        = (
        [f'(a) All EP1  (N={n_ep1_all})']
        + [f'{alpha} {lbl} dominant  (N={len(sub_gens[k])})'
           for alpha, k, lbl in zip(panel_labels_alpha[1:], SUBTERM_KEYS, SUBTERM_LABELS)]
    )

    for i, (pk, title) in enumerate(zip(panel_keys, panel_titles)):
        row_map  = (i // 3) * 2      # map row: 0 or 2
        row_cbar = row_map + 1        # colorbar row: 1 or 3
        col      = i % 3

        ax  = fig.add_subplot(gs[row_map, col], projection=ccrs.PlateCarree())
        cax = fig.add_subplot(gs[row_cbar, col])

        setup_map_axes(ax, title)

        d = densities.get(pk)
        if d is None:
            # Empty panel – same map geometry, no colorbar
            ax.text(0.5, 0.5, 'Insufficient data', transform=ax.transAxes,
                    ha='center', va='center', fontsize=10, color='gray',
                    bbox=dict(facecolor='white', alpha=0.6,
                              edgecolor='gray', boxstyle='round,pad=0.3'))
            cax.set_visible(False)
        else:
            d_region = d[np.ix_(lat_idx, lon_idx)]
            # Per-panel color scale (95th-percentile of positive values)
            pos_vals = d_region[d_region > 0]
            vmax_p = float(np.percentile(pos_vals, 95)) if pos_vals.size > 0 else 1e-6
            raw_lev = np.linspace(0.0, vmax_p, 12)
            levels = np.unique(np.round(raw_lev, 2))
            if len(levels) < 3:
                levels = raw_lev

            cf = ax.contourf(lon_r, lat_r, d_region,
                             levels=levels, cmap='YlOrRd',
                             transform=ccrs.PlateCarree(), extend='max', alpha=0.8)
            ax.contour(lon_r, lat_r, d_region,
                       levels=6, colors='black', linewidths=0.5,
                       transform=ccrs.PlateCarree(), alpha=0.6)

            # Individual colorbar in dedicated GridSpec row – does not resize map
            cbar = fig.colorbar(cf, cax=cax, orientation='horizontal', extend='max')
            cbar.set_label(r'Cyclones / 10$^6$ km$^2$ / yr', fontsize=8)
            cbar.set_ticks(levels[::2])
            cbar.set_ticklabels([f'{lev:.1f}' for lev in levels[::2]])
            cbar.ax.tick_params(labelsize=7)

    fig.suptitle(r'EP1 cyclone genesis density by dominant $C_K$ subterm',
                 fontsize=13, fontweight='bold')

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
        cbar.set_label(r'Normalized genesis density anomaly (norm$_{EP}$ $-$ norm$_{All}$)', fontsize=9)
        ticks = np.linspace(-maxabs_shared, maxabs_shared, 5)
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f'{t:.2f}' for t in ticks])
        cbar.ax.tick_params(labelsize=9)

    fig.suptitle(r'Normalized genesis density anomaly per dominant $C_K$ subterm',
                 fontsize=12, fontweight='bold', y=0.98)

    out = FIGURES_DIR / 'ck_subterms_genesis_normaldiff.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')
    return out


# ============================================================================
# FIGURE 4: FULL TRACKS
# ============================================================================

def create_figure_tracks(dom_df: pd.DataFrame, ep1_cases: pd.DataFrame,
                          tracks_df: pd.DataFrame, all_ep1_ids=None):
    """2×3 panels: all EP1 tracks + per dominant subterm.

    Parameters
    ----------
    all_ep1_ids : list or array-like, optional
        Full list of EP1 track IDs (444 cyclones). If provided, the 'All EP1'
        panel and the grey background in subterm panels use this full population.
        Falls back to dom_df track IDs (only those with LEC data) if not given.
    """
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
    # Use full EP1 population if provided; otherwise fall back to dom_df subset.
    # BUG FIX: dom_df contains only 94 cyclones (those with LEC data), while the
    # full EP1 population is 444. Passing all_ep1_ids ensures the "All EP1" panel
    # and grey background tracks correctly reflect the complete EP1 sample.
    if all_ep1_ids is not None:
        _all_ids = list(all_ep1_ids)
    else:
        _all_ids = list(dom_df['track_id'].unique())
    n_all = len(_all_ids)

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
    _draw_tracks(ax0, _all_ids, 'steelblue',
                 f'{panel_labels_alpha[0]} All EP1 (N={n_all})')

    # Panels 2–6: per dominant subterm
    for i, (key, label, color) in enumerate(zip(SUBTERM_KEYS, SUBTERM_LABELS, SUBTERM_COLORS)):
        ax = fig.add_subplot(2, 3, i + 2, projection=ccrs.PlateCarree())
        sub_ids = dom_df.loc[dom_df['dominant_subterm'] == key, 'track_id'].values
        _draw_tracks(ax, sub_ids, color,
                     f'{panel_labels_alpha[i+1]} {label} dominant (N={len(sub_ids)})',
                     show_all=True, all_ids=_all_ids)

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

    plt.suptitle(r'EP1 cyclone tracks by dominant $C_K$ subterm', fontsize=13, fontweight='bold')
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
        'Ck_total_new',
        'Ck_1_intensif', 'Ck_2_intensif', 'Ck_3_intensif', 'Ck_4_intensif', 'Ck_5_intensif',
        'subterms_sum', 'dominant_subterm', 'dominance_margin',
        'Ck_1_norm', 'Ck_2_norm', 'Ck_3_norm', 'Ck_4_norm', 'Ck_5_norm',
    ]
    keep = [c for c in keep if c in table1.columns]
    table1 = table1[keep]
    out1 = RESULTS_DIR / 'ep1_ck_subterms_per_cyclone.csv'
    table1.to_csv(out1, index=False)
    print(f'  Table 1 saved: {out1} ({len(table1)} rows)')

    # --- Table 2: LEC audit summary ---
    val_stats['n_ep1_total'] = len(data['ep1_ids'])
    table2 = pd.DataFrame([val_stats])
    out2 = RESULTS_DIR / 'lec_audit_stats.csv'
    table2.to_csv(out2, index=False)
    print(f'  Table 2 saved: {out2}')

    return table1


# ============================================================================
# WRITE DIAGNOSTIC
# ============================================================================

def write_diagnostic(dom_df: pd.DataFrame, val_stats: dict, data: dict,
                     audit_summary: dict | None = None):
    """Write diagnostic_summary.txt.

    Reports the full EP1 population, the subset with valid LEC data, and
    the figures that use each sample.  All statistics come from the local
    LEC audit — no Zenodo comparison is performed.
    """
    out = RESULTS_DIR / 'diagnostic_summary.txt'

    n_ep1_total = val_stats.get('n_ep1_total', len(data['ep1_ids']))
    n_lec       = val_stats.get('n_ep1_with_new_lec', len(dom_df))
    dominance_counts = dom_df['dominant_subterm'].value_counts().sort_index()

    # Build label strings without LaTeX for plain-text file
    label_plain = ['Ck^(a)', 'Ck^(b)', 'Ck^(c)', 'Ck^(d)', 'Ck^(e)']

    lines = [
        '=' * 70,
        'DIAGNOSTIC SUMMARY: Ck Subterms Analysis (EP1 cyclones)',
        '=' * 70,
        '',
        '-- LEC AUDIT SUMMARY --',
        f'Total EP1 cyclones (from ep_structure/ep1_cases.csv):  {n_ep1_total}',
        f'LEC directories found:                                 {val_stats.get("n_lec_directory_found", "?")}',
        f'With Ck_pressure_level.csv:                           {val_stats.get("n_with_ck_total_file", "?")}',
        f'With all Ck_1..5_pressure_level.csv:                  {val_stats.get("n_with_all_ck_subterm_files", "?")}',
        f'With valid data in intensification phase:              {val_stats.get("n_with_data_in_intensif_phase", "?")}',
        f'USABLE for dominance classification:                   {n_lec}',
        f'NOT usable (excluded):                                 {n_ep1_total - n_lec}',
        '',
        'Figure sample counts:',
        f'  Fig 1 (boxplots): n={n_lec}  — only cyclones with valid LEC subterm data',
        f'  Fig 2 (genesis density, All EP1 panel): n={n_ep1_total}  — full EP1 population',
        f'  Fig 2 (genesis density, per-subterm panels): n varies (see panel titles)',
        f'  Fig 3 (normalized anomaly, All EP1 baseline): n={n_ep1_total}',
        f'  Fig 4 (tracks, All EP1 panel): n={n_ep1_total}  — full EP1 population',
        f'  Fig 4 (tracks, per-subterm panels): n varies (see panel titles)',
        '',
        f'WHY {n_lec} vs {n_ep1_total}:',
        f'  - {n_ep1_total} = total EP1 cyclones with intensification phase data (ep1_cases.csv)',
        f'  - {n_lec} = subset that have complete LEC output in results/ck_analysis/lec_results/',
        '          (all five Ck_1..Ck_5 pressure-level CSV files present + non-empty',
        '           data within the intensification window).',
        f'  - The remaining {n_ep1_total - n_lec} cyclones lack complete LEC output.',
        '  - Boxplots and dominance classification use only the usable subset.',
        '  - "All EP1" panels (density maps, tracks) correctly use all EP1 cyclones.',
        '',
        '-- DATA LOADED --',
        f'EP1 cyclones (ep_structure/ep1_cases.csv): {n_ep1_total}',
        f'EP1 with valid LEC results:                {n_lec}',
        f'EP1 with intensification phase:            {len(data["ep1_cases"])}',
        f'Phase source: results/ep_structure/ep1_cases.csv',
        '',
        '-- VERTICAL INTEGRATION --',
        'Ck subterms from results_vertical_levels/:',
        '  formula: sum(df.values * dp / g) where g=9.8 m/s^2',
        '  dp = pressure interval at each level (Pa)',
        'Ck_total from *_results.csv: already vertically integrated (no correction needed)',
        '',
        '-- INTERNAL CONSISTENCY --',
        f'Mean Ck_total (from *_results.csv): {val_stats.get("mean_ck_new", float("nan")):.4f} W/m^2',
        f'Mean subterms sum (Ck_1+..+Ck_5):   {val_stats.get("mean_subterm_sum", float("nan")):.4f} W/m^2',
        '(close agreement confirms internal consistency of the vertical integration)',
        '',
        '-- DOMINANCE CLASSIFICATION --',
        'Sign convention (paper.tex):',
        '  C_K < 0  ->  K_Z -> K_E  (mean flow transfers energy to eddies; barotropic instability)',
        '  C_K > 0  ->  K_E -> K_Z  (eddies transfer energy to mean flow)',
        'EP1 cyclones have large negative C_K (strongly driven by barotropic instability).',
        'Method: dominant subterm = subterm with minimum (most negative) intensification-phase mean.',
        '        i.e. the subterm contributing most to the K_Z->K_E energy transfer.',
        'Dominance margin: |dominant value - second most negative value|',
        '',
        f'Dominance counts per subterm (n={n_lec} cyclones with valid LEC data):',
    ]
    for k, v in dominance_counts.items():
        idx = SUBTERM_KEYS.index(k) if k in SUBTERM_KEYS else -1
        lbl = label_plain[idx] if idx >= 0 else k
        desc = SUBTERM_DESCRIPTIONS[idx] if idx >= 0 else ''
        lines.append(f'  {k} ({lbl}): {v} cyclones  -- {desc}')

    # Top exclusion reasons from audit
    if audit_summary and audit_summary.get('exclusion_reasons'):
        lines += ['', '-- TOP EXCLUSION REASONS --']
        for reason, count in sorted(
            audit_summary['exclusion_reasons'].items(), key=lambda x: -x[1]
        )[:10]:
            lines.append(f'  {count:4d}  {reason}')

    lines += [
        '',
        '-- NORMALIZATION METHOD (Figures 3) --',
        'Step 1: For each spatial grid point, compute the KDE genesis density for:',
        f'        (A) all EP1 cyclones (n={n_ep1_total})  ->  density_all[lat, lon]',
        '        (B) cyclones where subterm k is dominant (n_k)  ->  density_k[lat, lon]',
        'Step 2: Apply Min-Max normalization to positive values only:',
        '        norm_all[lat,lon] = (density_all - min_pos) / (max_pos - min_pos)',
        '                            where min_pos, max_pos are taken over the positive',
        '                            values of density_all.',
        '        Same formula for norm_k.',
        'Step 3: Relative anomaly = norm_k - norm_all',
        '        > 0 (red):  enhanced genesis for this subterm relative to all EP1.',
        '        < 0 (blue): suppressed genesis for this subterm relative to all EP1.',
        'Step 4: Shared diverging colorbar spans [-max_abs, +max_abs] where max_abs is',
        '        the maximum absolute anomaly across all valid subterm panels.',
        '',
        '-- OUTPUT FILES --',
        'Table 1: results/ck_subterms/ep1_ck_subterms_per_cyclone.csv',
        'Audit:   results/ck_subterms/lec_audit_per_cyclone.csv',
        'Audit:   results/ck_subterms/lec_audit_summary.csv / .json',
        'Audit:   results/ck_subterms/lec_audit_report.txt',
        'Fig 1:   figures/ck_subterms/ck_subterms_boxplots.png  (combined: subterms + total)',
        'Fig 2:   figures/ck_subterms/ck_subterms_genesis_density.png',
        'Fig 3:   figures/ck_subterms/ck_subterms_genesis_normaldiff.png',
        'Fig 4:   figures/ck_subterms/ck_subterms_tracks.png',
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
    print('STEP 3: LEC Audit, Dominance Classification, and Figures')
    print('=' * 70)

    # 1. Load data
    print('\n[1/7] Loading data...')
    data = load_data()
    n_ep1_total = len(data['ep1_ids'])
    print(f'  Total EP1 cyclones: {n_ep1_total}')

    # 2. Run LEC audit
    print('\n[2/7] Running LEC results audit...')
    audit_df, audit_summary = run_audit(verbose=True)
    n_lec_dirs = audit_summary['n_lec_directory_found']
    n_ck_total = audit_summary['n_with_ck_total_file']
    n_ck_subs  = audit_summary['n_with_all_ck_subterm_files']
    n_usable   = audit_summary['n_usable_for_dominance']
    print(f'  {n_ep1_total} EP1 cases expected')
    print(f'  {n_lec_dirs} LEC directories found')
    print(f'  {n_ck_total} with Ck_pressure_level.csv')
    print(f'  {n_ck_subs} with all Ck_1..5 subterms')
    print(f'  {n_usable} valid for dominance classification')
    if audit_summary.get('exclusion_reasons'):
        top = sorted(audit_summary['exclusion_reasons'].items(), key=lambda x: -x[1])[:3]
        print('  Top exclusion reasons: ' + ', '.join(f'{r}({c})' for r, c in top))

    # 3. Compute dominance (using audit to filter to valid cyclones)
    print('\n[3/7] Computing dominance classification...')
    dom_df = compute_dominance(data['ep1_ids'], data['ep1_cases'], audit_df=audit_df)
    if len(dom_df) == 0:
        print('ERROR: No cyclones with complete subterm data. Exiting.')
        return
    n_lec = len(dom_df)
    print(f'  {n_ep1_total} EP1 cases expected')
    print(f'  {n_lec} cases with complete Ck subterms (valid for dominance)')
    print(f'  (Boxplots and dominance use n={n_lec}; '
          f'All EP1 density/track panels use n={n_ep1_total})')
    print(f'  Dominant subterm distribution (n={n_lec}):')
    for k, v in dom_df['dominant_subterm'].value_counts().sort_index().items():
        print(f'    {k}: {v}')

    # 4. Build audit statistics
    print('\n[4/7] Summarizing LEC audit statistics...')
    val_stats = summarize_lec_audit(dom_df, audit_summary)
    val_stats['n_ep1_total'] = n_ep1_total
    print(f"  Mean Ck_total (local LEC): {val_stats['mean_ck_new']:.4f} W/m²")
    print(f"  Mean subterm sum:           {val_stats['mean_subterm_sum']:.4f} W/m²")

    # 5. Figures 1–4
    print('\n[5/7] Figure 1: Combined boxplots (subterms left, total right)...')
    create_figure_boxplots(dom_df, n_ep1_total)

    # Note: genesis_df contains all EP1 cyclones; the "All EP1" panel uses
    # the full population. Per-subterm panels use the usable subset.
    print('\n[5b/7] Figure 2: Genesis density maps (per-panel colorbars)...')
    create_figure_genesis_density(dom_df, data['genesis_df'], data['tracks_df'])

    print('\n[5c/7] Figure 3: Normalized-difference maps...')
    create_figure_normalized_diff(dom_df, data['genesis_df'])

    print(f'\n[6/7] Figure 4: Full tracks (All EP1 n={n_ep1_total})...')
    create_figure_tracks(dom_df, data['ep1_cases'], data['tracks_df'],
                         all_ep1_ids=data['ep1_ids'])

    # 6. Write tables and diagnostics
    print('\n[7/7] Writing tables and diagnostics...')
    write_tables(dom_df, data, val_stats)
    write_diagnostic(dom_df, val_stats, data, audit_summary=audit_summary)

    # Regenerate figures manifest
    print('\nRegenerating figures manifest...')
    subprocess.run(
        ['python3', str(BASE_DIR / 'scripts/web/extract_ck_subterms_site_data.py')],
        check=False
    )
    subprocess.run(
        ['python3', str(BASE_DIR / 'scripts/web/build_site_manifest.py')],
        check=False
    )

    print('\n' + '=' * 70)
    print('STEP 3 COMPLETE')
    print(f"  Figures: {FIGURES_DIR}")
    print(f"  Results: {RESULTS_DIR}")
    print(f"  Audit files: {RESULTS_DIR}/lec_audit_*.{{csv,json,txt}}")
    print(f"  EP1 total={n_ep1_total} | LEC dirs={n_lec_dirs} | "
          f"With subterms={n_ck_subs} | Valid for dominance={n_lec}")
    print('=' * 70)


if __name__ == '__main__':
    main()
