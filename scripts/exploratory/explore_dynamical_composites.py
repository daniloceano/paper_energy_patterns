#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploratory Dynamical Composites: Total and Anomaly Configurations

This script generates exploratory 3×2 EP1 vs EP2 dynamical composite figures
for all three composite modes. Two figure variants are produced per mode:

FIGURE 1 — TOTAL FIELDS:
  Row 1: PV @ 200 hPa (shading) + EGR (contours) + 250 hPa total wind (vectors)
  Row 2: PV @ 850 hPa (shading) + T-adv (contours) + 850 hPa total wind (vectors)
  Row 3: AFC (shading) + 250 hPa wind (vectors) + RK sign-reversal hatching
         + KE advection contours (green positive, yellow negative)

FIGURE 2 — ANOMALY FIELDS:
  Row 1: PV anomaly @ 200 hPa + EGR + 250 hPa anomaly wind
  Row 2: PV anomaly @ 850 hPa + T-adv anomaly + 850 hPa anomaly wind
  Row 3: AFC + 250 hPa anomaly wind + RK hatching + KE-adv anomaly contours

Composite modes processed:
  - full_intensification : mean over all intensification timesteps
  - central_time         : central timestep only
  - intense_10           : top 10 most intense cyclones

Output:
  figures/exploratory/dynamical_composites_total_{mode}.png
  figures/exploratory/dynamical_composites_anom_{mode}.png

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / 'scripts'))

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import xarray as xr
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import Rectangle

# ============================================================================
# CONFIGURABLE PARAMETERS
# ============================================================================

DPI = 300
FIGSIZE = (9, 12)

# Input data
DATA_DIR = BASE_DIR / 'data' / 'era5_ep_structure'

# Output
FIGURES_DIR = BASE_DIR / 'figures' / 'exploratory'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Composite modes to process
COMPOSITE_MODES = ['full_intensification', 'central_time', 'intense_10']

# ── Unit conversions ─────────────────────────────────────────────────────────
PV_SCALE    = 1e6      # K m² kg⁻¹ s⁻¹ (SI)  →  PVU
ADV_T_SCALE = 3600.0   # K s⁻¹               →  K h⁻¹
SLP_SCALE   = 1e-2     # Pa                  →  hPa

# ── EGR contour levels [day⁻¹] — only ≥ 0.5 day⁻¹ ────────────────────────────
EGR_CONTOUR_LEVELS = np.array([0.50, 0.55, 0.60, 0.65])

# ── Temperature advection contour levels [K h⁻¹] ─────────────────────────────
TADV_NEG_LEVELS = np.array([-0.120, -0.080, -0.040])  # cold advection
TADV_POS_LEVELS = np.array([0.040,  0.080,  0.120])   # warm advection

# ── SLP contour interval [hPa] ───────────────────────────────────────────────
SLP_INTERVAL = 2.0

# ── Wind vectors ─────────────────────────────────────────────────────────────
VECTOR_SKIP      = 16
VECTOR_SCALE_250 = 500
QUIVER_KEY_U_250 = 20.0
VECTOR_SCALE_850 = 200
QUIVER_KEY_U_850 = 5.0

# ── RK meridional sign-reversal hatching ─────────────────────────────────────
RK_HATCH_HALF_WINDOW = 1
HATCH_PATTERN = '///'
HATCH_COLOR   = 'dimgray'
HATCH_LW      = 0.7

# ── Colormaps ────────────────────────────────────────────────────────────────
CMAP_PV  = 'RdBu_r'
CMAP_AFC = 'RdBu_r'

# ── Font sizes ───────────────────────────────────────────────────────────────
PANEL_TITLESIZE     = 12
TICK_LABELSIZE      = 9
CBAR_LABELSIZE      = 9
ANNOTATION_FONTSIZE = 12

# Apply globally
plt.rcParams.update({
    'font.size':         11,
    'axes.labelsize':    11,
    'axes.titlesize':    PANEL_TITLESIZE,
    'xtick.labelsize':   TICK_LABELSIZE,
    'ytick.labelsize':   TICK_LABELSIZE,
    'legend.fontsize':   TICK_LABELSIZE,
    'figure.dpi':        100,
    'savefig.dpi':       DPI,
    'savefig.bbox':      'tight',
    'axes.grid':         False,
    'font.family':       'sans-serif',
})


# ============================================================================
# DATA LOADING
# ============================================================================

def load_composites(mode):
    """Load precomputed EP1 and EP2 composites for a given mode."""
    datasets = {}
    for ep in ['ep1', 'ep2']:
        f = DATA_DIR / f'precomputed_composites_{ep}_{mode}.nc'
        if not f.exists():
            print(f"  ❌ File not found: {f}")
            print(f"     Run step3_precompute_composites.py --mode {mode} first.")
            return None
        datasets[ep.upper()] = xr.open_dataset(f)
        mb = f.stat().st_size / 1024 ** 2
        print(f"    Loaded {ep.upper()}: {f.name} ({mb:.1f} MB)")
    return datasets


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def meridional_sign_reversal_mask(field, half_window=1):
    """
    Boolean mask: True where the field has a meridional sign reversal within
    a ±half_window-point neighbourhood along the y (latitude) axis.
    """
    ny, nx = field.shape
    mask = np.zeros((ny, nx), dtype=bool)
    for i in range(ny):
        i0 = max(0, i - half_window)
        i1 = min(ny, i + half_window + 1)
        window  = field[i0:i1, :]
        col_min = np.nanmin(window, axis=0)
        col_max = np.nanmax(window, axis=0)
        mask[i, :] = (col_min < 0.0) & (col_max > 0.0)
    return mask


def ax_setup(ax, x, y, show_xlabels=False, show_ylabels=False):
    """Square axes with storm-relative extent."""
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(y.min(), y.max())
    try:
        ax.set_box_aspect(1)
    except AttributeError:
        ax.set_aspect('equal')
    ax.tick_params(length=3)
    if show_xlabels:
        xticks = np.arange(-15, 16, 5)
        ax.set_xticks(xticks)
        ax.set_xticklabels([f'{v:+d}°' for v in xticks], fontsize=TICK_LABELSIZE - 1)
    else:
        ax.set_xticklabels([])
    if show_ylabels:
        yticks = np.arange(-15, 16, 5)
        ax.set_yticks(yticks)
        ax.set_yticklabels([f'{v:+d}°' for v in yticks], fontsize=TICK_LABELSIZE - 1)
    else:
        ax.set_yticklabels([])


def add_slp_contours(ax, x_2d, y_2d, msl_hpa):
    """Thin, semi-transparent SLP contours for spatial reference."""
    slp_min = np.floor(np.nanmin(msl_hpa) / SLP_INTERVAL) * SLP_INTERVAL
    slp_max = np.ceil(np.nanmax(msl_hpa)  / SLP_INTERVAL) * SLP_INTERVAL
    levels = np.arange(slp_min, slp_max + SLP_INTERVAL, SLP_INTERVAL)
    if len(levels) > 1:
        ax.contour(x_2d, y_2d, msl_hpa, levels=levels,
                   colors='k', linewidths=0.45, alpha=0.40, zorder=4)


def add_wind_vectors(ax, x_2d, y_2d, u, v, scale, key_u, add_key=False, speed_threshold=None):
    """Subsampled wind vector overlay."""
    sk = VECTOR_SKIP
    u_plot = u[::sk, ::sk].copy()
    v_plot = v[::sk, ::sk].copy()

    if speed_threshold is not None:
        speed = np.sqrt(u_plot**2 + v_plot**2)
        mask  = speed < speed_threshold
        u_plot = np.where(mask, np.nan, u_plot)
        v_plot = np.where(mask, np.nan, v_plot)

    Q = ax.quiver(
        x_2d[::sk, ::sk], y_2d[::sk, ::sk],
        u_plot, v_plot,
        scale=scale, width=0.004, color='gray',
        headwidth=3, headlength=4, headaxislength=3.5,
        zorder=8,
    )
    if add_key:
        ax.quiverkey(Q, X=0.97, Y=0.95, U=key_u,
                     label=f'{key_u:.0f} m s$^{{-1}}$',
                     labelpos='W', fontproperties={'size': 10}, zorder=12)
    return Q


def add_lec_box(ax):
    """Dashed 15°×15° rectangle for LEC computation domain."""
    rect = Rectangle((-7.5, -7.5), 15.0, 15.0,
                     linewidth=1.2, edgecolor='k', facecolor='none',
                     linestyle='--', zorder=9)
    ax.add_patch(rect)


def mark_center(ax):
    """Cyclone-centre marker at (0, 0)."""
    ax.plot(0, 0, 'k*', markersize=12,
            markeredgecolor='white', markeredgewidth=1.2, zorder=10)


def panel_label(ax, label):
    """Bold panel label at upper-left corner."""
    ax.text(0.01, 0.98, label,
            transform=ax.transAxes,
            fontsize=ANNOTATION_FONTSIZE, fontweight='bold',
            ha='left', va='top', zorder=11)


def add_colorbar(fig, gs_cell, im, label):
    """Add a right-side colorbar in the dedicated GridSpec column."""
    cax = fig.add_subplot(gs_cell)
    cb  = plt.colorbar(im, cax=cax)
    cb.set_label(label, fontsize=CBAR_LABELSIZE)
    cb.ax.tick_params(labelsize=CBAR_LABELSIZE)
    cax.yaxis.set_ticks_position('right')
    return cb


# ============================================================================
# FIGURE 1: TOTAL FIELDS
# ============================================================================

def create_figure_total(datasets, mode):
    """
    3×2 EP1 vs EP2 Dynamical Composites — Total Fields

    Row 1: PV @ 200 hPa (shading) + EGR (contours) + 250 hPa total wind (vectors)
    Row 2: PV @ 850 hPa (shading) + T-adv (contours) + 850 hPa total wind (vectors)
    Row 3: AFC (shading) + 250 hPa wind (vectors) + RK hatching + KE-adv contours
    """
    print(f"    Creating total-fields figure for mode={mode}...")

    # Check required variables
    required_total = ['pv_200', 'pv_850', 'egr', 'adv_T_850', 'msl', 'afc_250',
                      'u_250', 'v_250', 'u_850', 'v_850', 'rk_criterion_250', 'ke_adv_250']
    for ep in ['EP1', 'EP2']:
        missing = [v for v in required_total if v not in datasets[ep]]
        if missing:
            print(f"      ⚠ {ep} missing variables: {missing} — skipping total figure")
            return

    eps = ['EP1', 'EP2']

    # Prepare data dict
    ep_data = {}
    for ep in eps:
        ds = datasets[ep]
        x = ds.x.values
        y = ds.y.values
        x_2d, y_2d = np.meshgrid(x, y)

        ep_data[ep] = {
            'pv_200'      : ds['pv_200'].values * PV_SCALE,
            'pv_850'      : ds['pv_850'].values * PV_SCALE,
            'egr'         : ds['egr'].values,
            'adv_T_850'   : ds['adv_T_850'].values * ADV_T_SCALE,
            'msl_hpa'     : ds['msl'].values * SLP_SCALE,
            'afc_250'     : ds['afc_250'].values,
            'ke_adv_250'  : ds['ke_adv_250'].values,
            'u_250'       : ds['u_250'].values,
            'v_250'       : ds['v_250'].values,
            'u_850'       : ds['u_850'].values,
            'v_850'       : ds['v_850'].values,
            'rk_criterion': ds['rk_criterion_250'].values,
            'x': x, 'y': y, 'x_2d': x_2d, 'y_2d': y_2d,
            'n_cases': int(ds.attrs.get('n_cases', 0)),
        }

    # Global colormap limits
    def _lim(key, percentile=98):
        vals = np.concatenate([ep_data[ep][key].ravel() for ep in eps])
        return np.nanpercentile(np.abs(vals), percentile)

    lim_pv200 = _lim('pv_200')
    lim_pv850 = _lim('pv_850')
    lim_afc   = _lim('afc_250')
    lim_keadv = _lim('ke_adv_250')

    # For PV total, use actual range (not symmetric)
    all_pv200 = np.concatenate([ep_data[ep]['pv_200'].ravel() for ep in eps])
    all_pv850 = np.concatenate([ep_data[ep]['pv_850'].ravel() for ep in eps])
    levels_pv200 = np.linspace(np.nanpercentile(all_pv200, 2), np.nanpercentile(all_pv200, 98), 21)
    levels_pv850 = np.linspace(np.nanpercentile(all_pv850, 2), np.nanpercentile(all_pv850, 98), 21)
    levels_afc   = np.linspace(-lim_afc, lim_afc, 21)

    # KE advection contour levels
    keadv_neg_levels = np.array([-lim_keadv * 0.6, -lim_keadv * 0.4, -lim_keadv * 0.2])
    keadv_pos_levels = np.array([lim_keadv * 0.2, lim_keadv * 0.4, lim_keadv * 0.6])

    # Create figure
    fig = plt.figure(figsize=FIGSIZE)
    gs = gridspec.GridSpec(
        3, 3,
        width_ratios=[1, 1, 0.055],
        hspace=0.07, wspace=0.07,
        left=0.05, right=0.94, top=0.92, bottom=0.04,
    )

    panel_labels_grid = [['(a)', '(b)'], ['(c)', '(d)'], ['(e)', '(f)']]

    # ─────────────────────────────────────────────────────────────────────────
    # ROW 0 — PV @ 200 hPa + EGR + 250 hPa wind
    # ─────────────────────────────────────────────────────────────────────────
    im_r0 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[0, col])

        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_200'],
                         levels=levels_pv200, cmap='RdYlBu_r', extend='both')
        if col == 0:
            im_r0 = im

        # EGR contours ≥ 0.5 day⁻¹
        egr_valid = EGR_CONTOUR_LEVELS[
            (EGR_CONTOUR_LEVELS >= np.nanmin(d['egr'])) &
            (EGR_CONTOUR_LEVELS <= np.nanmax(d['egr']))
        ]
        if len(egr_valid):
            cs_egr = ax.contour(d['x_2d'], d['y_2d'], d['egr'],
                       levels=egr_valid, colors='k', linewidths=1.1, alpha=0.85, zorder=5)
            ax.clabel(cs_egr, inline=True, fontsize=8, fmt='%.2f')

        # 250 hPa wind vectors (total)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250'], d['v_250'],
                         scale=VECTOR_SCALE_250, key_u=QUIVER_KEY_U_250,
                         add_key=(col == 1), speed_threshold=25.0)

        add_lec_box(ax)
        mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, panel_labels_grid[0][col])
        ax.set_title(f"{ep} (n={d['n_cases']})", fontsize=PANEL_TITLESIZE, fontweight='bold', pad=4)

    add_colorbar(fig, gs[0, 2], im_r0, r"PV$_{200}$ (PVU)")

    # ─────────────────────────────────────────────────────────────────────────
    # ROW 1 — PV @ 850 hPa + T-adv + 850 hPa wind
    # ─────────────────────────────────────────────────────────────────────────
    im_r1 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[1, col])

        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_850'],
                         levels=levels_pv850, cmap='RdYlBu_r', extend='both')
        if col == 0:
            im_r1 = im

        tadv = d['adv_T_850']

        # Cold-advection contours (negative): dashed blue
        neg_valid = TADV_NEG_LEVELS[TADV_NEG_LEVELS >= np.nanmin(tadv)]
        if len(neg_valid):
            ax.contour(d['x_2d'], d['y_2d'], tadv, levels=neg_valid,
                       colors='steelblue', linewidths=1.8, linestyles='dashed', alpha=0.9, zorder=5)

        # Warm-advection contours (positive): solid red
        pos_valid = TADV_POS_LEVELS[TADV_POS_LEVELS <= np.nanmax(tadv)]
        if len(pos_valid):
            ax.contour(d['x_2d'], d['y_2d'], tadv, levels=pos_valid,
                       colors='firebrick', linewidths=1.8, linestyles='solid', alpha=0.9, zorder=5)

        # 850 hPa wind vectors (total)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_850'], d['v_850'],
                         scale=VECTOR_SCALE_850, key_u=QUIVER_KEY_U_850,
                         add_key=(col == 1))

        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax)
        mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, panel_labels_grid[1][col])

    add_colorbar(fig, gs[1, 2], im_r1, r"PV$_{850}$ (PVU)")

    # ─────────────────────────────────────────────────────────────────────────
    # ROW 2 — AFC + 250 hPa wind + RK hatching + KE-adv contours
    # ─────────────────────────────────────────────────────────────────────────
    im_r2 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[2, col])

        im = ax.contourf(d['x_2d'], d['y_2d'], d['afc_250'],
                         levels=levels_afc, cmap=CMAP_AFC, extend='both')
        if col == 0:
            im_r2 = im

        # RK meridional sign-reversal hatching
        rk_mask = meridional_sign_reversal_mask(d['rk_criterion'], half_window=RK_HATCH_HALF_WINDOW)
        hatch_field = rk_mask.astype(float)
        with mpl.rc_context({'hatch.color': HATCH_COLOR, 'hatch.linewidth': HATCH_LW}):
            ax.contourf(d['x_2d'], d['y_2d'], hatch_field,
                        levels=[0.5, 1.5], colors=['none'], hatches=[HATCH_PATTERN], zorder=6)

        # KE advection contours: green positive, yellow negative
        ke_adv = d['ke_adv_250']
        neg_keadv_valid = keadv_neg_levels[keadv_neg_levels >= np.nanmin(ke_adv)]
        if len(neg_keadv_valid):
            ax.contour(d['x_2d'], d['y_2d'], ke_adv, levels=neg_keadv_valid,
                       colors='gold', linewidths=1.6, linestyles='dashed', alpha=0.9, zorder=5)

        pos_keadv_valid = keadv_pos_levels[keadv_pos_levels <= np.nanmax(ke_adv)]
        if len(pos_keadv_valid):
            ax.contour(d['x_2d'], d['y_2d'], ke_adv, levels=pos_keadv_valid,
                       colors='forestgreen', linewidths=1.6, linestyles='solid', alpha=0.9, zorder=5)

        # 250 hPa wind vectors — only where speed ≥ 30 m/s
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250'], d['v_250'],
                         scale=VECTOR_SCALE_250, key_u=QUIVER_KEY_U_250,
                         add_key=(col == 1), speed_threshold=30.0)

        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax)
        mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_xlabels=True, show_ylabels=(col == 0))
        panel_label(ax, panel_labels_grid[2][col])

    add_colorbar(fig, gs[2, 2], im_r2, r"AFC$_{250}$ (W m$^{-2}$)")

    # Suptitle
    fig.suptitle(f"Dynamical Composites — Total Fields ({mode})", fontsize=13, fontweight='bold')

    # Save
    out = FIGURES_DIR / f"dynamical_composites_total_{mode}.png"
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"      ✓ {out.name}")


# ============================================================================
# FIGURE 2: ANOMALY FIELDS
# ============================================================================

def create_figure_anom(datasets, mode):
    """
    3×2 EP1 vs EP2 Dynamical Composites — Anomaly Fields

    Row 1: PV anom @ 200 hPa (shading) + EGR (contours) + 250 hPa anom wind (vectors)
    Row 2: PV anom @ 850 hPa (shading) + T-adv anom (contours) + 850 hPa anom wind (vectors)
    Row 3: AFC (shading) + 250 hPa anom wind (vectors) + RK hatching + KE-adv anom contours
    """
    print(f"    Creating anomaly-fields figure for mode={mode}...")

    # Check required variables
    required_anom = ['pv_200_anom', 'pv_850_anom', 'egr', 'adv_T_850_anom', 'msl', 'afc_250',
                     'u_250_prime', 'v_250_prime', 'u_850_prime', 'v_850_prime',
                     'rk_criterion_250', 'ke_adv_250_anom']
    for ep in ['EP1', 'EP2']:
        missing = [v for v in required_anom if v not in datasets[ep]]
        if missing:
            print(f"      ⚠ {ep} missing variables: {missing} — skipping anomaly figure")
            return

    eps = ['EP1', 'EP2']

    # Prepare data dict
    ep_data = {}
    for ep in eps:
        ds = datasets[ep]
        x = ds.x.values
        y = ds.y.values
        x_2d, y_2d = np.meshgrid(x, y)

        ep_data[ep] = {
            'pv_200_anom'     : ds['pv_200_anom'].values * PV_SCALE,
            'pv_850_anom'     : ds['pv_850_anom'].values * PV_SCALE,
            'egr'             : ds['egr'].values,
            'adv_T_850_anom'  : ds['adv_T_850_anom'].values * ADV_T_SCALE,
            'msl_hpa'         : ds['msl'].values * SLP_SCALE,
            'afc_250'         : ds['afc_250'].values,
            'ke_adv_250_anom' : ds['ke_adv_250_anom'].values,
            'u_250_prime'     : ds['u_250_prime'].values,
            'v_250_prime'     : ds['v_250_prime'].values,
            'u_850_prime'     : ds['u_850_prime'].values,
            'v_850_prime'     : ds['v_850_prime'].values,
            'rk_criterion'    : ds['rk_criterion_250'].values,
            'x': x, 'y': y, 'x_2d': x_2d, 'y_2d': y_2d,
            'n_cases': int(ds.attrs.get('n_cases', 0)),
        }

    # Global symmetric colormap limits
    def _sym_lim(key, percentile=98):
        vals = np.concatenate([ep_data[ep][key].ravel() for ep in eps])
        return np.nanpercentile(np.abs(vals), percentile)

    lim_pv200_anom = _sym_lim('pv_200_anom')
    lim_pv850_anom = _sym_lim('pv_850_anom')
    lim_afc        = _sym_lim('afc_250')
    lim_tadv_anom  = _sym_lim('adv_T_850_anom')
    lim_keadv_anom = _sym_lim('ke_adv_250_anom')

    levels_pv200_anom = np.linspace(-lim_pv200_anom, lim_pv200_anom, 21)
    levels_pv850_anom = np.linspace(-lim_pv850_anom, lim_pv850_anom, 21)
    levels_afc        = np.linspace(-lim_afc, lim_afc, 21)

    # T-adv anomaly contour levels
    tadv_anom_neg_levels = np.array([-lim_tadv_anom * 0.6, -lim_tadv_anom * 0.4, -lim_tadv_anom * 0.2])
    tadv_anom_pos_levels = np.array([lim_tadv_anom * 0.2, lim_tadv_anom * 0.4, lim_tadv_anom * 0.6])

    # KE advection anomaly contour levels
    keadv_anom_neg_levels = np.array([-lim_keadv_anom * 0.6, -lim_keadv_anom * 0.4, -lim_keadv_anom * 0.2])
    keadv_anom_pos_levels = np.array([lim_keadv_anom * 0.2, lim_keadv_anom * 0.4, lim_keadv_anom * 0.6])

    # Create figure
    fig = plt.figure(figsize=FIGSIZE)
    gs = gridspec.GridSpec(
        3, 3,
        width_ratios=[1, 1, 0.055],
        hspace=0.07, wspace=0.07,
        left=0.05, right=0.94, top=0.92, bottom=0.04,
    )

    panel_labels_grid = [['(a)', '(b)'], ['(c)', '(d)'], ['(e)', '(f)']]

    # ─────────────────────────────────────────────────────────────────────────
    # ROW 0 — PV anom @ 200 hPa + EGR + 250 hPa anom wind
    # ─────────────────────────────────────────────────────────────────────────
    im_r0 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[0, col])

        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_200_anom'],
                         levels=levels_pv200_anom, cmap=CMAP_PV, extend='both')
        if col == 0:
            im_r0 = im

        # EGR contours ≥ 0.5 day⁻¹
        egr_valid = EGR_CONTOUR_LEVELS[
            (EGR_CONTOUR_LEVELS >= np.nanmin(d['egr'])) &
            (EGR_CONTOUR_LEVELS <= np.nanmax(d['egr']))
        ]
        if len(egr_valid):
            cs_egr = ax.contour(d['x_2d'], d['y_2d'], d['egr'],
                       levels=egr_valid, colors='k', linewidths=1.1, alpha=0.85, zorder=5)
            ax.clabel(cs_egr, inline=True, fontsize=8, fmt='%.2f')

        # 250 hPa anomaly wind vectors
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250_prime'], d['v_250_prime'],
                         scale=VECTOR_SCALE_250, key_u=QUIVER_KEY_U_250,
                         add_key=(col == 1))

        add_lec_box(ax)
        mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, panel_labels_grid[0][col])
        ax.set_title(f"{ep} (n={d['n_cases']})", fontsize=PANEL_TITLESIZE, fontweight='bold', pad=4)

    add_colorbar(fig, gs[0, 2], im_r0, r"PV$_{200}$ anom (PVU)")

    # ─────────────────────────────────────────────────────────────────────────
    # ROW 1 — PV anom @ 850 hPa + T-adv anom + 850 hPa anom wind
    # ─────────────────────────────────────────────────────────────────────────
    im_r1 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[1, col])

        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_850_anom'],
                         levels=levels_pv850_anom, cmap=CMAP_PV, extend='both')
        if col == 0:
            im_r1 = im

        tadv_anom = d['adv_T_850_anom']

        # Cold-advection anomaly contours (negative): dashed blue
        neg_valid = tadv_anom_neg_levels[tadv_anom_neg_levels >= np.nanmin(tadv_anom)]
        if len(neg_valid):
            ax.contour(d['x_2d'], d['y_2d'], tadv_anom, levels=neg_valid,
                       colors='steelblue', linewidths=1.8, linestyles='dashed', alpha=0.9, zorder=5)

        # Warm-advection anomaly contours (positive): solid red
        pos_valid = tadv_anom_pos_levels[tadv_anom_pos_levels <= np.nanmax(tadv_anom)]
        if len(pos_valid):
            ax.contour(d['x_2d'], d['y_2d'], tadv_anom, levels=pos_valid,
                       colors='firebrick', linewidths=1.8, linestyles='solid', alpha=0.9, zorder=5)

        # 850 hPa anomaly wind vectors
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_850_prime'], d['v_850_prime'],
                         scale=VECTOR_SCALE_850, key_u=QUIVER_KEY_U_850,
                         add_key=(col == 1))

        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax)
        mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, panel_labels_grid[1][col])

    add_colorbar(fig, gs[1, 2], im_r1, r"PV$_{850}$ anom (PVU)")

    # ─────────────────────────────────────────────────────────────────────────
    # ROW 2 — AFC + 250 hPa anom wind + RK hatching + KE-adv anom contours
    # ─────────────────────────────────────────────────────────────────────────
    im_r2 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[2, col])

        im = ax.contourf(d['x_2d'], d['y_2d'], d['afc_250'],
                         levels=levels_afc, cmap=CMAP_AFC, extend='both')
        if col == 0:
            im_r2 = im

        # RK meridional sign-reversal hatching
        rk_mask = meridional_sign_reversal_mask(d['rk_criterion'], half_window=RK_HATCH_HALF_WINDOW)
        hatch_field = rk_mask.astype(float)
        with mpl.rc_context({'hatch.color': HATCH_COLOR, 'hatch.linewidth': HATCH_LW}):
            ax.contourf(d['x_2d'], d['y_2d'], hatch_field,
                        levels=[0.5, 1.5], colors=['none'], hatches=[HATCH_PATTERN], zorder=6)

        # KE advection anomaly contours: green positive, yellow negative
        ke_adv_anom = d['ke_adv_250_anom']
        neg_keadv_valid = keadv_anom_neg_levels[keadv_anom_neg_levels >= np.nanmin(ke_adv_anom)]
        if len(neg_keadv_valid):
            ax.contour(d['x_2d'], d['y_2d'], ke_adv_anom, levels=neg_keadv_valid,
                       colors='gold', linewidths=1.6, linestyles='dashed', alpha=0.9, zorder=5)

        pos_keadv_valid = keadv_anom_pos_levels[keadv_anom_pos_levels <= np.nanmax(ke_adv_anom)]
        if len(pos_keadv_valid):
            ax.contour(d['x_2d'], d['y_2d'], ke_adv_anom, levels=pos_keadv_valid,
                       colors='forestgreen', linewidths=1.6, linestyles='solid', alpha=0.9, zorder=5)

        # 250 hPa anomaly wind vectors
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250_prime'], d['v_250_prime'],
                         scale=VECTOR_SCALE_250, key_u=QUIVER_KEY_U_250,
                         add_key=(col == 1))

        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax)
        mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_xlabels=True, show_ylabels=(col == 0))
        panel_label(ax, panel_labels_grid[2][col])

    add_colorbar(fig, gs[2, 2], im_r2, r"AFC$_{250}$ (W m$^{-2}$)")

    # Suptitle
    fig.suptitle(f"Dynamical Composites — Anomaly Fields ({mode})", fontsize=13, fontweight='bold')

    # Save
    out = FIGURES_DIR / f"dynamical_composites_anom_{mode}.png"
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"      ✓ {out.name}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate exploratory dynamical composite figures for all modes."""
    print("=" * 70)
    print("EXPLORATORY DYNAMICAL COMPOSITES")
    print("=" * 70)
    print(f"Output directory: {FIGURES_DIR}\n")

    for mode in COMPOSITE_MODES:
        print(f"\n{'─'*70}")
        print(f"Processing mode: {mode}")
        print(f"{'─'*70}")

        # Load composites
        datasets = load_composites(mode)
        if datasets is None:
            print(f"  ⚠ Skipping mode={mode} — data not found")
            continue

        # Create figures
        create_figure_total(datasets, mode)
        create_figure_anom(datasets, mode)

        # Close datasets
        for ds in datasets.values():
            ds.close()

    print(f"\n{'='*70}")
    print("✓ COMPLETE")
    print(f"{'='*70}")
    print(f"Figures saved in: {FIGURES_DIR}")


if __name__ == '__main__':
    main()
