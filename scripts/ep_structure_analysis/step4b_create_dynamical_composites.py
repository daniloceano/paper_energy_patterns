#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4b: Create Multi-Panel Dynamical Composite Figures

Three integrated figures combining the key dynamical diagnostics across EP1,
EP2, EP3, and EPALL in a single publication-quality layout.  These complement
the single-variable figures from ``step4_create_figures.py`` by showing the
joint structure of upper-level and lower-level dynamics simultaneously.

FIGURE 1 — TOTAL FIELDS  (4 columns: EP1 | EP2 | EP3 | EPALL)
  Row 1: PV @ 200 hPa (shading) + EGR (contours ≥ 0.5 day⁻¹) + 250 hPa total wind
  Row 2: PV @ 850 hPa (shading) + T-adv (contours) + 850 hPa total wind + SLP
  Row 3: AFC @ 250 hPa (shading) + 250 hPa wind (≥ 30 m/s) + RK sign-reversal
         hatching + KE-adv contours

FIGURE 2 — CLIMATOLOGY-RELATIVE ANOMALY FIELDS  (4 columns: EP1 | EP2 | EP3 | EPALL)
  Anomaly = departure from the 1991–2020 ERA5 monthly climatology.
  Row 1: PV' @ 200 hPa (shading) + EGR (contours) + 250 hPa anomaly wind (u', v')
  Row 2: PV' @ 850 hPa (shading) + T-adv anomaly (contours) + 850 hPa anomaly wind
  Row 3: AFC (total, shading) + 250 hPa anomaly wind + RK hatching + KE-adv anomaly

FIGURE 3 — EPALL-RELATIVE ANOMALY FIELDS  (3 columns: EP1−EPALL | EP2−EPALL | EP3−EPALL)
  Anomaly = departure from the EPALL composite (all cyclones combined).
  This differs from the climatological anomaly: the reference here is the mean of
  ALL intensifying cyclones, not the multi-year monthly mean.  It isolates what
  distinguishes each EP from a "generic" extratropical cyclone.
  Row 1: PV − EPALL @ 200 hPa + EGR − EPALL contours + 250 hPa EPALL-relative wind
  Row 2: PV − EPALL @ 850 hPa + T-adv − EPALL contours + 850 hPa EPALL-relative wind
         + total SLP thin contours (spatial reference anchor)
  Row 3: AFC − EPALL (shading) + EPALL-relative 250 hPa wind
         + RK total sign-reversal hatching (total composite, not EPALL-relative —
           RK = β − ∂²ū/∂y² is a background-flow diagnostic)
         + KE-adv − EPALL contours
         + total SLP thin contours (spatial reference anchor)

Input (precomputed by step3):
  data/era5_ep_structure/precomputed_composites_ep1.nc
  data/era5_ep_structure/precomputed_composites_ep2.nc
  data/era5_ep_structure/precomputed_composites_ep3.nc
  data/era5_ep_structure/precomputed_composites_epall.nc

Output:
  figures/ep_structure/dynamical_composites/dynamical_composites_total.png
  figures/ep_structure/dynamical_composites/dynamical_composites_anom.png
  figures/ep_structure/dynamical_composites/dynamical_composites_epall_anom.png

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import Rectangle

from scripts.utils.colormaps import CMAP_PV_ANOM, CMAP_PV_TOTAL, CMAP_AFC

# ============================================================================
# CONFIGURABLE PARAMETERS
# ============================================================================

DPI = 300

# Input data
DATA_DIR = PROJECT_ROOT / 'data' / 'era5_ep_structure'

# Output — dedicated subfolder inside figures/ep_structure
FIGURES_DIR = PROJECT_ROOT / 'figures' / 'ep_structure' / 'dynamical_composites'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Unit conversions ─────────────────────────────────────────────────────────
PV_SCALE    = 1e6      # K m² kg⁻¹ s⁻¹ (SI)  →  PVU
ADV_T_SCALE = 3600.0   # K s⁻¹               →  K h⁻¹
SLP_SCALE   = 1e-2     # Pa                  →  hPa

# ── EGR contour levels [day⁻¹] — only ≥ 0.5 day⁻¹ ──────────────────────────
EGR_CONTOUR_LEVELS = np.array([0.50, 0.55, 0.60, 0.65])

# ── EGR EPALL-relative contour levels [day⁻¹] ───────────────────────────────
EGR_EPALL_POS_LEVELS = np.array([0.03, 0.06, 0.09, 0.12])
EGR_EPALL_NEG_LEVELS = np.array([-0.12, -0.09, -0.06, -0.03])

# ── Temperature advection contour levels [K h⁻¹] ────────────────────────────
# Used by Figures 1 & 2 (total and clim-anom)
TADV_NEG_LEVELS = np.array([-0.240, -0.080, -0.040])  # cold advection
TADV_POS_LEVELS = np.array([0.040,  0.080,  0.120])   # warm advection

# ── Figure 3 (EPALL-relative) contour levels ─────────────────────────────────
# T-adv − EPALL [K h⁻¹]: edit step and cap to taste
FIG3_TADV_STEP = 0.050
FIG3_TADV_CAP  = 0.20

# KE-adv − EPALL [m² s⁻³]: edit step and cap to taste
FIG3_KEADV_STEP = 0.005
FIG3_KEADV_CAP  = 0.01

# ── SLP contour interval [hPa] ──────────────────────────────────────────────
SLP_INTERVAL = 2.0

# ── Wind vectors ─────────────────────────────────────────────────────────────
VECTOR_SKIP = 16

# ── Contour styling ───────────────────────────────────────────────────────────
TADV_KE_COLOR_NEG       = 'steelblue'
TADV_KE_COLOR_POS       = 'firebrick'
CONTOUR_LINEWIDTH_COLORED = 2.0

FIG3_KEADV_COLOR_NEG = TADV_KE_COLOR_NEG
FIG3_KEADV_COLOR_POS = TADV_KE_COLOR_POS

# ── Figure-specific wind parameters ──────────────────────────────────────────
# Structure: {row_name: {scale, key_u, color, alpha, threshold (if applicable)}}
FIG1_WIND_PARAMS = {
    'row0_250': {'scale': 500, 'key_u': 20.0, 'color': 'gray', 'alpha': 0.7},
    'row1_850': {'scale': 200, 'key_u': 5.0,  'color': 'k',    'alpha': 0.7},
    'row2_250': {'scale': 500, 'key_u': 20.0, 'color': 'k',    'alpha': 0.7, 'threshold': 30.0},
}

FIG2_WIND_PARAMS = {
    'row0_250': {'scale': 200, 'key_u': 20.0, 'color': 'k', 'alpha': 0.7},
    'row1_850': {'scale': 100, 'key_u': 5.0,  'color': 'k', 'alpha': 0.7},
    'row2_250': {'scale': 200, 'key_u': 20.0, 'color': 'k', 'alpha': 0.7},
}

FIG3_WIND_PARAMS = {
    'row0_250': {'scale': 100, 'key_u': 5.0, 'color': 'k', 'alpha': 0.7},
    'row1_850': {'scale': 50,  'key_u': 1.0, 'color': 'k', 'alpha': 0.7},
    'row2_250': {'scale': 100, 'key_u': 5.0, 'color': 'k', 'alpha': 0.7},
}

# ── RK meridional sign-reversal hatching ─────────────────────────────────────
RK_HATCH_HALF_WINDOW = 1
HATCH_PATTERN = '///'
HATCH_COLOR   = 'dimgray'
HATCH_LW      = 0.7

# ── Font sizes ───────────────────────────────────────────────────────────────
PANEL_TITLESIZE     = 11
TICK_LABELSIZE      = 8
CBAR_LABELSIZE      = 8
ANNOTATION_FONTSIZE = 11

plt.rcParams.update({
    'font.size':         10,
    'axes.labelsize':    10,
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

PANEL_LABELS_4 = [
    ['(a)', '(b)', '(c)', '(d)'],
    ['(e)', '(f)', '(g)', '(h)'],
    ['(i)', '(j)', '(k)', '(l)'],
]
PANEL_LABELS_3 = [
    ['(a)', '(b)', '(c)'],
    ['(d)', '(e)', '(f)'],
    ['(g)', '(h)', '(i)'],
]


# ============================================================================
# DATA LOADING
# ============================================================================

def load_composites():
    """Load canonical central-timestep composites for EP1, EP2, EP3, EPALL."""
    import xarray as xr
    datasets = {}
    for ep in ['ep1', 'ep2', 'ep3', 'epall']:
        f = DATA_DIR / f'precomputed_composites_{ep}.nc'
        if not f.exists():
            print(f"  ❌ File not found: {f}")
            print(f"     Run step3_precompute_composites.py first.")
            return None
        datasets[ep.upper()] = xr.open_dataset(f)
        mb = f.stat().st_size / 1024 ** 2
        print(f"    Loaded {ep.upper()}: {f.name} ({mb:.1f} MB)")
    return datasets


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def meridional_sign_reversal_mask(field, half_window=1):
    """Boolean mask: True where the field has a meridional sign reversal."""
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


def add_wind_vectors(ax, x_2d, y_2d, u, v, scale, key_u,
                     add_key=False, speed_threshold=None, color='gray', alpha=0.7):
    """Subsampled wind vector overlay."""
    sk = VECTOR_SKIP
    u_plot = u[::sk, ::sk].copy()
    v_plot = v[::sk, ::sk].copy()

    if speed_threshold is not None:
        speed  = np.sqrt(u_plot**2 + v_plot**2)
        mask   = speed < speed_threshold
        u_plot = np.where(mask, np.nan, u_plot)
        v_plot = np.where(mask, np.nan, v_plot)

    Q = ax.quiver(
        x_2d[::sk, ::sk], y_2d[::sk, ::sk],
        u_plot, v_plot,
        scale=scale, width=0.004, color=color, alpha=alpha,
        headwidth=3, headlength=4, headaxislength=3.5,
        zorder=8,
    )
    if add_key:
        ax.quiverkey(Q, X=0.97, Y=0.95, U=key_u,
                     label=f'{key_u:.0f} m s$^{{-1}}$',
                     labelpos='W', fontproperties={'size': 9}, zorder=12)
    return Q


def add_lec_box(ax):
    """Dashed 15°×15° rectangle for LEC computation domain."""
    rect = Rectangle((-7.5, -7.5), 15.0, 15.0,
                     linewidth=1.2, edgecolor='k', facecolor='none',
                     linestyle='--', zorder=9)
    ax.add_patch(rect)


def mark_center(ax):
    """Cyclone-centre marker at (0, 0)."""
    ax.plot(0, 0, 'k*', markersize=10,
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


def _make_4col_gridspec(fig):
    """3 rows × 5 columns GridSpec for 4-panel figures (4 data + 1 colorbar)."""
    return gridspec.GridSpec(
        3, 5,
        width_ratios=[1, 1, 1, 1, 0.065],
        hspace=0.06, wspace=0.06,
        left=0.04, right=0.95, top=0.92, bottom=0.04,
    )


def _make_3col_gridspec(fig):
    """3 rows × 4 columns GridSpec for 3-panel figures (3 data + 1 colorbar)."""
    return gridspec.GridSpec(
        3, 4,
        width_ratios=[1, 1, 1, 0.065],
        hspace=0.06, wspace=0.07,
        left=0.05, right=0.95, top=0.92, bottom=0.04,
    )


# ============================================================================
# FIGURE 1: TOTAL FIELDS — 4 columns (EP1, EP2, EP3, EPALL)
# ============================================================================

def create_figure_total(datasets):
    """
    3×4 Dynamical Composites — Total Fields (EP1 | EP2 | EP3 | EPALL)

    Row 1: PV @ 200 hPa (shading) + EGR contours (≥ 0.5 day⁻¹) + 250 hPa total wind
    Row 2: PV @ 850 hPa (shading) + T-adv contours + 850 hPa total wind + SLP
    Row 3: AFC (shading) + 250 hPa wind (≥ 30 m/s) + RK sign-reversal hatching
           + KE-adv contours

    EPALL column shows the all-cyclone composite (reference population).
    """
    print("  Creating total-fields figure (4 columns)...")

    required = ['pv_200', 'pv_850', 'egr', 'adv_T_850', 'msl', 'afc_250',
                'u_250', 'v_250', 'u_850', 'v_850', 'rk_criterion_250', 'ke_adv_250']
    eps = ['EP1', 'EP2', 'EP3', 'EPALL']

    for ep in eps:
        missing = [v for v in required if v not in datasets[ep]]
        if missing:
            print(f"    ⚠ {ep} missing: {missing} — skipping total figure")
            return

    ep_data = {}
    for ep in eps:
        ds = datasets[ep]
        x = ds.x.values
        y = ds.y.values
        x_2d, y_2d = np.meshgrid(x, y)
        ep_data[ep] = dict(
            pv_200      = ds['pv_200'].values * PV_SCALE,
            pv_850      = ds['pv_850'].values * PV_SCALE,
            egr         = ds['egr'].values,
            adv_T_850   = ds['adv_T_850'].values * ADV_T_SCALE,
            msl_hpa     = ds['msl'].values * SLP_SCALE,
            afc_250     = ds['afc_250'].values,
            ke_adv_250  = ds['ke_adv_250'].values,
            u_250       = ds['u_250'].values,
            v_250       = ds['v_250'].values,
            u_850       = ds['u_850'].values,
            v_850       = ds['v_850'].values,
            rk_criterion= ds['rk_criterion_250'].values,
            x=x, y=y, x_2d=x_2d, y_2d=y_2d,
            n_cases=int(ds.attrs.get('n_cases', 0)),
        )

    def _lim(key, pct=98):
        return np.nanpercentile(np.abs(
            np.concatenate([ep_data[ep][key].ravel() for ep in eps])), pct)

    all_pv200 = np.concatenate([ep_data[ep]['pv_200'].ravel() for ep in eps])
    all_pv850 = np.concatenate([ep_data[ep]['pv_850'].ravel() for ep in eps])
    levels_pv200 = np.linspace(np.nanpercentile(all_pv200, 2),
                               np.nanpercentile(all_pv200, 98), 21)
    levels_pv850 = np.linspace(np.nanpercentile(all_pv850, 2),
                               np.nanpercentile(all_pv850, 98), 21)
    lim_afc   = _lim('afc_250')
    lim_keadv = _lim('ke_adv_250')
    levels_afc = np.linspace(-lim_afc, lim_afc, 21)
    keadv_neg  = np.array([-lim_keadv*0.6, -lim_keadv*0.4, -lim_keadv*0.2])
    keadv_pos  = np.array([ lim_keadv*0.2,  lim_keadv*0.4,  lim_keadv*0.6])

    fig = plt.figure(figsize=(20, 13))
    gs  = _make_4col_gridspec(fig)

    # ── ROW 0: PV@200 + EGR + 250 wind ───────────────────────────────────────
    im_r0 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[0, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_200'],
                         levels=levels_pv200, cmap=CMAP_PV_TOTAL, extend='both')
        if col == 0:
            im_r0 = im
        egr_valid = EGR_CONTOUR_LEVELS[
            (EGR_CONTOUR_LEVELS >= np.nanmin(d['egr'])) &
            (EGR_CONTOUR_LEVELS <= np.nanmax(d['egr']))]
        if len(egr_valid):
            cs = ax.contour(d['x_2d'], d['y_2d'], d['egr'],
                            levels=egr_valid, colors='k', linewidths=1.0, alpha=0.85, zorder=5)
            ax.clabel(cs, inline=True, fontsize=7, fmt='%.2f')
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250'], d['v_250'],
                         scale=FIG1_WIND_PARAMS['row0_250']['scale'],
                         key_u=FIG1_WIND_PARAMS['row0_250']['key_u'],
                         add_key=(col == 3),
                         color=FIG1_WIND_PARAMS['row0_250']['color'],
                         alpha=FIG1_WIND_PARAMS['row0_250']['alpha'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_4[0][col])
        col_title = f"{ep} (n={d['n_cases']})"
        if ep == 'EPALL':
            col_title += '\n[all cyclones]'
        ax.set_title(col_title, fontsize=PANEL_TITLESIZE, fontweight='bold', pad=3)
    add_colorbar(fig, gs[0, 4], im_r0, r"PV$_{200}$ (PVU)")

    # ── ROW 1: PV@850 + T-adv + 850 wind + SLP ───────────────────────────────
    im_r1 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[1, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_850'],
                         levels=levels_pv850, cmap=CMAP_PV_TOTAL, extend='both')
        if col == 0:
            im_r1 = im
        tadv   = d['adv_T_850']
        neg_v  = TADV_NEG_LEVELS[TADV_NEG_LEVELS >= np.nanmin(tadv)]
        pos_v  = TADV_POS_LEVELS[TADV_POS_LEVELS <= np.nanmax(tadv)]
        if len(neg_v):
            ax.contour(d['x_2d'], d['y_2d'], tadv, levels=neg_v,
                       colors='steelblue', linewidths=1.6, linestyles='dashed', alpha=0.9, zorder=5)
        if len(pos_v):
            ax.contour(d['x_2d'], d['y_2d'], tadv, levels=pos_v,
                       colors='firebrick', linewidths=1.6, linestyles='solid', alpha=0.9, zorder=5)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_850'], d['v_850'],
                         scale=FIG1_WIND_PARAMS['row1_850']['scale'],
                         key_u=FIG1_WIND_PARAMS['row1_850']['key_u'],
                         add_key=(col == 3),
                         color=FIG1_WIND_PARAMS['row1_850']['color'],
                         alpha=FIG1_WIND_PARAMS['row1_850']['alpha'])
        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_4[1][col])
    add_colorbar(fig, gs[1, 4], im_r1, r"PV$_{850}$ (PVU)")

    # ── ROW 2: AFC + 250 wind + RK hatching + KE-adv ─────────────────────────
    im_r2 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[2, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['afc_250'],
                         levels=levels_afc, cmap=CMAP_AFC, extend='both')
        if col == 0:
            im_r2 = im
        rk_mask = meridional_sign_reversal_mask(d['rk_criterion'], RK_HATCH_HALF_WINDOW)
        with mpl.rc_context({'hatch.color': HATCH_COLOR, 'hatch.linewidth': HATCH_LW}):
            ax.contourf(d['x_2d'], d['y_2d'], rk_mask.astype(float),
                        levels=[0.5, 1.5], colors=['none'], hatches=[HATCH_PATTERN], zorder=6)
        ke     = d['ke_adv_250']
        neg_ke = keadv_neg[keadv_neg >= np.nanmin(ke)]
        pos_ke = keadv_pos[keadv_pos <= np.nanmax(ke)]
        if len(neg_ke):
            ax.contour(d['x_2d'], d['y_2d'], ke, levels=neg_ke,
                       colors=TADV_KE_COLOR_NEG, linewidths=CONTOUR_LINEWIDTH_COLORED,
                       linestyles='dashed', alpha=0.9, zorder=5)
        if len(pos_ke):
            ax.contour(d['x_2d'], d['y_2d'], ke, levels=pos_ke,
                       colors=TADV_KE_COLOR_POS, linewidths=CONTOUR_LINEWIDTH_COLORED,
                       linestyles='solid', alpha=0.9, zorder=5)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250'], d['v_250'],
                         scale=FIG1_WIND_PARAMS['row2_250']['scale'],
                         key_u=FIG1_WIND_PARAMS['row2_250']['key_u'],
                         add_key=(col == 3),
                         speed_threshold=FIG1_WIND_PARAMS['row2_250'].get('threshold'),
                         color=FIG1_WIND_PARAMS['row2_250']['color'],
                         alpha=FIG1_WIND_PARAMS['row2_250']['alpha'])
        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_xlabels=True, show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_4[2][col])
    add_colorbar(fig, gs[2, 4], im_r2, r"AFC$_{250}$ (W m$^{-2}$)")

    fig.suptitle(
        "Dynamical Composites — Total Fields  (EP1 | EP2 | EP3 | EPALL)",
        fontsize=13, fontweight='bold',
    )
    out = FIGURES_DIR / "dynamical_composites_total.png"
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"    ✓ {out.name}")


# ============================================================================
# FIGURE 2: CLIMATOLOGY-RELATIVE ANOMALY FIELDS — 4 columns
# ============================================================================

def create_figure_anom(datasets):
    """
    3×4 Dynamical Composites — Climatology-Relative Anomaly Fields
    (EP1 | EP2 | EP3 | EPALL)

    Anomaly = departure from the 1991–2020 ERA5 monthly climatology.
    Row 1: PV' @ 200 hPa + EGR + 250 hPa anomaly wind (u', v')
    Row 2: PV' @ 850 hPa + T-adv anomaly + 850 hPa anomaly wind + SLP
    Row 3: AFC (total, shading) + 250 hPa anomaly wind + RK hatching + KE-adv'
    """
    print("  Creating climatology-relative anomaly figure (4 columns)...")

    required = ['pv_200_anom', 'pv_850_anom', 'egr', 'adv_T_850_anom', 'msl', 'afc_250',
                'u_250_prime', 'v_250_prime', 'u_850_prime', 'v_850_prime',
                'rk_criterion_250', 'ke_adv_250_anom']
    eps = ['EP1', 'EP2', 'EP3', 'EPALL']

    for ep in eps:
        missing = [v for v in required if v not in datasets[ep]]
        if missing:
            print(f"    ⚠ {ep} missing: {missing} — skipping anomaly figure")
            return

    ep_data = {}
    for ep in eps:
        ds = datasets[ep]
        x = ds.x.values
        y = ds.y.values
        x_2d, y_2d = np.meshgrid(x, y)
        ep_data[ep] = dict(
            pv_200_anom     = ds['pv_200_anom'].values * PV_SCALE,
            pv_850_anom     = ds['pv_850_anom'].values * PV_SCALE,
            egr             = ds['egr'].values,
            adv_T_850_anom  = ds['adv_T_850_anom'].values * ADV_T_SCALE,
            msl_hpa         = ds['msl'].values * SLP_SCALE,
            afc_250         = ds['afc_250'].values,
            ke_adv_250_anom = ds['ke_adv_250_anom'].values,
            u_250_prime     = ds['u_250_prime'].values,
            v_250_prime     = ds['v_250_prime'].values,
            u_850_prime     = ds['u_850_prime'].values,
            v_850_prime     = ds['v_850_prime'].values,
            rk_criterion    = ds['rk_criterion_250'].values,
            x=x, y=y, x_2d=x_2d, y_2d=y_2d,
            n_cases=int(ds.attrs.get('n_cases', 0)),
        )

    def _sym_lim(key, pct=98):
        return np.nanpercentile(np.abs(
            np.concatenate([ep_data[ep][key].ravel() for ep in eps])), pct)

    lim_pv200 = _sym_lim('pv_200_anom')
    lim_pv850 = _sym_lim('pv_850_anom')
    lim_afc   = _sym_lim('afc_250')
    lim_tadv  = _sym_lim('adv_T_850_anom')
    lim_keadv = _sym_lim('ke_adv_250_anom')

    levels_pv200 = np.linspace(-lim_pv200, lim_pv200, 21)
    levels_pv850 = np.linspace(-lim_pv850, lim_pv850, 21)
    levels_afc   = np.linspace(-lim_afc,   lim_afc,   21)

    tadv_neg  = np.array([-lim_tadv*0.6,  -lim_tadv*0.4,  -lim_tadv*0.2])
    tadv_pos  = np.array([ lim_tadv*0.2,   lim_tadv*0.4,   lim_tadv*0.6])
    keadv_neg = np.array([-lim_keadv*0.6, -lim_keadv*0.4, -lim_keadv*0.2])
    keadv_pos = np.array([ lim_keadv*0.2,  lim_keadv*0.4,  lim_keadv*0.6])

    fig = plt.figure(figsize=(20, 13))
    gs  = _make_4col_gridspec(fig)

    # ── ROW 0: PV'@200 + EGR + 250 anom wind ─────────────────────────────────
    im_r0 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[0, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_200_anom'],
                         levels=levels_pv200, cmap=CMAP_PV_ANOM, extend='both')
        if col == 0:
            im_r0 = im
        egr_valid = EGR_CONTOUR_LEVELS[
            (EGR_CONTOUR_LEVELS >= np.nanmin(d['egr'])) &
            (EGR_CONTOUR_LEVELS <= np.nanmax(d['egr']))]
        if len(egr_valid):
            cs = ax.contour(d['x_2d'], d['y_2d'], d['egr'],
                            levels=egr_valid, colors='k', linewidths=1.0, alpha=0.85, zorder=5)
            ax.clabel(cs, inline=True, fontsize=7, fmt='%.2f')
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250_prime'], d['v_250_prime'],
                         scale=FIG2_WIND_PARAMS['row0_250']['scale'],
                         key_u=FIG2_WIND_PARAMS['row0_250']['key_u'],
                         add_key=(col == 3),
                         color=FIG2_WIND_PARAMS['row0_250']['color'],
                         alpha=FIG2_WIND_PARAMS['row0_250']['alpha'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_4[0][col])
        col_title = f"{ep} (n={d['n_cases']})"
        if ep == 'EPALL':
            col_title += '\n[all cyclones]'
        ax.set_title(col_title, fontsize=PANEL_TITLESIZE, fontweight='bold', pad=3)
    add_colorbar(fig, gs[0, 4], im_r0, r"PV$'_{200}$ (PVU)")

    # ── ROW 1: PV'@850 + T-adv' + 850 anom wind + SLP ────────────────────────
    im_r1 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[1, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_850_anom'],
                         levels=levels_pv850, cmap=CMAP_PV_ANOM, extend='both')
        if col == 0:
            im_r1 = im
        neg_v = tadv_neg[tadv_neg >= np.nanmin(d['adv_T_850_anom'])]
        pos_v = tadv_pos[tadv_pos <= np.nanmax(d['adv_T_850_anom'])]
        if len(neg_v):
            ax.contour(d['x_2d'], d['y_2d'], d['adv_T_850_anom'], levels=neg_v,
                       colors='steelblue', linewidths=1.6, linestyles='dashed', alpha=0.9, zorder=5)
        if len(pos_v):
            ax.contour(d['x_2d'], d['y_2d'], d['adv_T_850_anom'], levels=pos_v,
                       colors='firebrick', linewidths=1.6, linestyles='solid', alpha=0.9, zorder=5)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_850_prime'], d['v_850_prime'],
                         scale=FIG2_WIND_PARAMS['row1_850']['scale'],
                         key_u=FIG2_WIND_PARAMS['row1_850']['key_u'],
                         add_key=(col == 3),
                         color=FIG2_WIND_PARAMS['row1_850']['color'],
                         alpha=FIG2_WIND_PARAMS['row1_850']['alpha'])
        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_4[1][col])
    add_colorbar(fig, gs[1, 4], im_r1, r"PV$'_{850}$ (PVU)")

    # ── ROW 2: AFC + 250 anom wind + RK hatching + KE-adv' ───────────────────
    im_r2 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[2, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['afc_250'],
                         levels=levels_afc, cmap=CMAP_AFC, extend='both')
        if col == 0:
            im_r2 = im
        rk_mask = meridional_sign_reversal_mask(d['rk_criterion'], RK_HATCH_HALF_WINDOW)
        with mpl.rc_context({'hatch.color': HATCH_COLOR, 'hatch.linewidth': HATCH_LW}):
            ax.contourf(d['x_2d'], d['y_2d'], rk_mask.astype(float),
                        levels=[0.5, 1.5], colors=['none'], hatches=[HATCH_PATTERN], zorder=6)
        neg_ke = keadv_neg[keadv_neg >= np.nanmin(d['ke_adv_250_anom'])]
        pos_ke = keadv_pos[keadv_pos <= np.nanmax(d['ke_adv_250_anom'])]
        if len(neg_ke):
            ax.contour(d['x_2d'], d['y_2d'], d['ke_adv_250_anom'], levels=neg_ke,
                       colors=TADV_KE_COLOR_NEG, linewidths=CONTOUR_LINEWIDTH_COLORED,
                       linestyles='dashed', alpha=0.9, zorder=5)
        if len(pos_ke):
            ax.contour(d['x_2d'], d['y_2d'], d['ke_adv_250_anom'], levels=pos_ke,
                       colors=TADV_KE_COLOR_POS, linewidths=CONTOUR_LINEWIDTH_COLORED,
                       linestyles='solid', alpha=0.9, zorder=5)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250_prime'], d['v_250_prime'],
                         scale=FIG2_WIND_PARAMS['row2_250']['scale'],
                         key_u=FIG2_WIND_PARAMS['row2_250']['key_u'],
                         add_key=(col == 3),
                         speed_threshold=FIG2_WIND_PARAMS['row2_250'].get('threshold'),
                         color=FIG2_WIND_PARAMS['row2_250']['color'],
                         alpha=FIG2_WIND_PARAMS['row2_250']['alpha'])
        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_xlabels=True, show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_4[2][col])
    add_colorbar(fig, gs[2, 4], im_r2, r"AFC$_{250}$ (W m$^{-2}$)")

    fig.suptitle(
        "Dynamical Composites — Climatology-Relative Anomaly Fields  "
        r"(EP1 | EP2 | EP3 | EPALL)   [X' = X − X̄$_{clim}$, 1991–2020]",
        fontsize=13, fontweight='bold',
    )
    out = FIGURES_DIR / "dynamical_composites_anom.png"
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"    ✓ {out.name}")


# ============================================================================
# FIGURE 3: EPALL-RELATIVE ANOMALY — 3 columns (EP1−EPALL, EP2−EPALL, EP3−EPALL)
# ============================================================================

def create_figure_epall_anom(datasets):
    """
    3×3 Dynamical Composites — EPALL-Relative Anomaly
    (EP1 − EPALL | EP2 − EPALL | EP3 − EPALL)

    Anomaly = departure from the EPALL composite (all cyclones combined).
    The reference is the typical intensifying extratropical cyclone, not the
    multi-year monthly mean.  EPALL column is omitted (identically zero).

    Row 1: (PV@200) − EPALL + (EGR) − EPALL contours + (u,v)_250 − EPALL
    Row 2: (PV@850) − EPALL + (T-adv) − EPALL contours + (u,v)_850 − EPALL
    Row 3: AFC − EPALL (shading) + (u,v)_250 − EPALL
           + RK total sign-reversal hatching (not EPALL-relative — background-
             flow diagnostic)
           + (KE-adv) − EPALL contours
    """
    print("  Creating EPALL-relative anomaly figure (3 columns)...")

    required_minus = [
        'pv_200_minus_epall', 'pv_850_minus_epall',
        'egr_minus_epall',
        'adv_T_850_minus_epall', 'msl',
        'afc_250_minus_epall',
        'u_250_minus_epall', 'v_250_minus_epall',
        'u_850_minus_epall', 'v_850_minus_epall',
        'rk_criterion_250',   # total RK — intentionally NOT minus_epall
        'ke_adv_250_minus_epall',
    ]
    eps = ['EP1', 'EP2', 'EP3']

    for ep in eps:
        missing = [v for v in required_minus if v not in datasets[ep]]
        if missing:
            print(f"    ⚠ {ep} missing: {missing} — skipping EPALL-relative figure")
            return

    ep_data = {}
    for ep in eps:
        ds = datasets[ep]
        x = ds.x.values
        y = ds.y.values
        x_2d, y_2d = np.meshgrid(x, y)
        ep_data[ep] = dict(
            pv_200_mep    = ds['pv_200_minus_epall'].values * PV_SCALE,
            pv_850_mep    = ds['pv_850_minus_epall'].values * PV_SCALE,
            egr_mep       = ds['egr_minus_epall'].values,
            adv_T_850_mep = ds['adv_T_850_minus_epall'].values * ADV_T_SCALE,
            msl_hpa       = ds['msl'].values * SLP_SCALE,
            afc_250_mep   = ds['afc_250_minus_epall'].values,
            ke_adv_250_mep= ds['ke_adv_250_minus_epall'].values,
            u_250_mep     = ds['u_250_minus_epall'].values,
            v_250_mep     = ds['v_250_minus_epall'].values,
            u_850_mep     = ds['u_850_minus_epall'].values,
            v_850_mep     = ds['v_850_minus_epall'].values,
            rk_criterion  = ds['rk_criterion_250'].values,   # total, not EPALL-relative
            x=x, y=y, x_2d=x_2d, y_2d=y_2d,
            n_cases=int(ds.attrs.get('n_cases', 0)),
        )

    def _sym_lim(key, pct=98):
        return np.nanpercentile(np.abs(
            np.concatenate([ep_data[ep][key].ravel() for ep in eps])), pct)

    lim_pv200 = _sym_lim('pv_200_mep')
    lim_pv850 = _sym_lim('pv_850_mep')
    lim_afc   = _sym_lim('afc_250_mep')
    levels_pv200 = np.linspace(-lim_pv200, lim_pv200, 21)
    levels_pv850 = np.linspace(-lim_pv850, lim_pv850, 21)
    levels_afc   = np.linspace(-lim_afc,   lim_afc,   21)

    tadv_pos  = np.arange(FIG3_TADV_STEP,  FIG3_TADV_CAP  + FIG3_TADV_STEP  * 0.5, FIG3_TADV_STEP)
    tadv_neg  = -tadv_pos[::-1]
    keadv_pos = np.arange(FIG3_KEADV_STEP, FIG3_KEADV_CAP + FIG3_KEADV_STEP * 0.5, FIG3_KEADV_STEP)
    keadv_neg = -keadv_pos[::-1]

    fig = plt.figure(figsize=(15, 13))
    gs  = _make_3col_gridspec(fig)

    # ── ROW 0: (PV@200)−EPALL + EGR−EPALL + (u,v)_250−EPALL ────────────────
    im_r0 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[0, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_200_mep'],
                         levels=levels_pv200, cmap=CMAP_PV_ANOM, extend='both')
        if col == 0:
            im_r0 = im
        pos_v = EGR_EPALL_POS_LEVELS[EGR_EPALL_POS_LEVELS <= np.nanmax(d['egr_mep'])]
        neg_v = EGR_EPALL_NEG_LEVELS[EGR_EPALL_NEG_LEVELS >= np.nanmin(d['egr_mep'])]
        if len(pos_v):
            cs = ax.contour(d['x_2d'], d['y_2d'], d['egr_mep'],
                            levels=pos_v, colors='firebrick', linewidths=2.0, alpha=0.90, zorder=5)
            ax.clabel(cs, inline=True, fontsize=7, fmt='%.2f')
        if len(neg_v):
            cs = ax.contour(d['x_2d'], d['y_2d'], d['egr_mep'],
                            levels=neg_v, colors='steelblue', linewidths=2.0,
                            linestyles='dashed', alpha=0.90, zorder=5)
            ax.clabel(cs, inline=True, fontsize=7, fmt='%.2f')
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250_mep'], d['v_250_mep'],
                         scale=FIG3_WIND_PARAMS['row0_250']['scale'],
                         key_u=FIG3_WIND_PARAMS['row0_250']['key_u'],
                         add_key=(col == 2),
                         speed_threshold=FIG3_WIND_PARAMS['row0_250'].get('threshold'),
                         color=FIG3_WIND_PARAMS['row0_250']['color'],
                         alpha=FIG3_WIND_PARAMS['row0_250']['alpha'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_3[0][col])
        ax.set_title(f"{ep} − EPALL  (n={d['n_cases']})",
                     fontsize=PANEL_TITLESIZE, fontweight='bold', pad=3)
    add_colorbar(fig, gs[0, 3], im_r0, r"PV$_{200}$ − EPALL (PVU)")

    # ── ROW 1: (PV@850)−EPALL + T-adv−EPALL + (u,v)_850−EPALL + SLP ────────
    im_r1 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[1, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['pv_850_mep'],
                         levels=levels_pv850, cmap=CMAP_PV_ANOM, extend='both')
        if col == 0:
            im_r1 = im
        neg_v = tadv_neg[tadv_neg >= np.nanmin(d['adv_T_850_mep'])]
        pos_v = tadv_pos[tadv_pos <= np.nanmax(d['adv_T_850_mep'])]
        if len(neg_v):
            ax.contour(d['x_2d'], d['y_2d'], d['adv_T_850_mep'], levels=neg_v,
                       colors='steelblue', linewidths=1.6, linestyles='dashed', alpha=0.9, zorder=5)
        if len(pos_v):
            ax.contour(d['x_2d'], d['y_2d'], d['adv_T_850_mep'], levels=pos_v,
                       colors='firebrick', linewidths=1.6, linestyles='solid', alpha=0.9, zorder=5)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_850_mep'], d['v_850_mep'],
                         scale=FIG3_WIND_PARAMS['row1_850']['scale'],
                         key_u=FIG3_WIND_PARAMS['row1_850']['key_u'],
                         add_key=(col == 2),
                         color=FIG3_WIND_PARAMS['row1_850']['color'],
                         alpha=FIG3_WIND_PARAMS['row1_850']['alpha'])
        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_3[1][col])
    add_colorbar(fig, gs[1, 3], im_r1, r"PV$_{850}$ − EPALL (PVU)")

    # ── ROW 2: AFC−EPALL + (u,v)_250−EPALL + RK total hatching + KE-adv−EPALL
    im_r2 = None
    for col, ep in enumerate(eps):
        d  = ep_data[ep]
        ax = fig.add_subplot(gs[2, col])
        im = ax.contourf(d['x_2d'], d['y_2d'], d['afc_250_mep'],
                         levels=levels_afc, cmap=CMAP_AFC, extend='both')
        if col == 0:
            im_r2 = im
        rk_mask = meridional_sign_reversal_mask(d['rk_criterion'], RK_HATCH_HALF_WINDOW)
        with mpl.rc_context({'hatch.color': HATCH_COLOR, 'hatch.linewidth': HATCH_LW}):
            ax.contourf(d['x_2d'], d['y_2d'], rk_mask.astype(float),
                        levels=[0.5, 1.5], colors=['none'], hatches=[HATCH_PATTERN], zorder=6)
        neg_ke = keadv_neg[keadv_neg >= np.nanmin(d['ke_adv_250_mep'])]
        pos_ke = keadv_pos[keadv_pos <= np.nanmax(d['ke_adv_250_mep'])]
        if len(neg_ke):
            ax.contour(d['x_2d'], d['y_2d'], d['ke_adv_250_mep'], levels=neg_ke,
                       colors=FIG3_KEADV_COLOR_NEG, linewidths=CONTOUR_LINEWIDTH_COLORED,
                       linestyles='dashed', alpha=0.9, zorder=5)
        if len(pos_ke):
            ax.contour(d['x_2d'], d['y_2d'], d['ke_adv_250_mep'], levels=pos_ke,
                       colors=FIG3_KEADV_COLOR_POS, linewidths=CONTOUR_LINEWIDTH_COLORED,
                       linestyles='solid', alpha=0.9, zorder=5)
        add_wind_vectors(ax, d['x_2d'], d['y_2d'], d['u_250_mep'], d['v_250_mep'],
                         scale=FIG3_WIND_PARAMS['row2_250']['scale'],
                         key_u=FIG3_WIND_PARAMS['row2_250']['key_u'],
                         add_key=(col == 2),
                         speed_threshold=FIG3_WIND_PARAMS['row2_250'].get('threshold'),
                         color=FIG3_WIND_PARAMS['row2_250']['color'],
                         alpha=FIG3_WIND_PARAMS['row2_250']['alpha'])
        add_slp_contours(ax, d['x_2d'], d['y_2d'], d['msl_hpa'])
        add_lec_box(ax); mark_center(ax)
        ax_setup(ax, d['x'], d['y'], show_xlabels=True, show_ylabels=(col == 0))
        panel_label(ax, PANEL_LABELS_3[2][col])
    add_colorbar(fig, gs[2, 3], im_r2, r"AFC$_{250}$ − EPALL (m$^2$ s$^{-3}$)")

    fig.suptitle(
        "Dynamical Composites — EPALL-Relative Anomaly  "
        "(EP1−EPALL | EP2−EPALL | EP3−EPALL)",
        fontsize=13, fontweight='bold',
    )
    out = FIGURES_DIR / "dynamical_composites_epall_anom.png"
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"    ✓ {out.name}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate multi-panel dynamical composite figures (canonical pipeline)."""
    print("=" * 70)
    print("STEP 4b: MULTI-PANEL DYNAMICAL COMPOSITE FIGURES")
    print("Canonical method: central-timestep composites (EP1, EP2, EP3, EPALL)")
    print("=" * 70)
    print(f"Output directory: {FIGURES_DIR}\n")

    datasets = load_composites()
    if datasets is None:
        print("❌ Could not load composites — aborting.")
        return

    n_ep1   = int(datasets['EP1'].attrs.get('n_cases', '?'))
    n_ep2   = int(datasets['EP2'].attrs.get('n_cases', '?'))
    n_ep3   = int(datasets['EP3'].attrs.get('n_cases', '?'))
    n_epall = int(datasets['EPALL'].attrs.get('n_cases', '?'))
    print(f"  EP1={n_ep1}  EP2={n_ep2}  EP3={n_ep3}  EPALL={n_epall}\n")

    create_figure_total(datasets)
    create_figure_anom(datasets)
    create_figure_epall_anom(datasets)

    for ds in datasets.values():
        ds.close()

    print(f"\n{'='*70}")
    print("✓ COMPLETE")
    print(f"{'='*70}")
    print(f"Figures saved in: {FIGURES_DIR}")


if __name__ == '__main__':
    main()
