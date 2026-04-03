"""
Step 6: Generate Cyclone Explorer Panels (Synoptic + Dynamic Fields)

Creates panel assets for each timestep of each EP1/EP2 cyclone during the
intensification phase, keeping the existing synoptic 2x2 panel and adding
dynamic diagnostics used in the project figures.

Categories
----------
Synoptic fields (existing 2x2 panel):
    - SLP + 850 hPa wind vectors
    - Temperature 850 hPa
    - Specific humidity 975 hPa
    - Geopotential 500 hPa

Dynamic fields (single diagnostic per panel):
    1) SLP + PV850 + wind850
    2) Temperature advection850 + PV850 + wind850
    3) AFC250 + KE advection anomaly250 + wind250 (speed >= 30 m/s)
    4) RK criterion250 map
    5) Barotropic critical region (BtCR) map

Outputs
-------
Legacy synoptic path (kept for backward compatibility):
    figures/cyclone_explorer/{ep_label}/{track_id}/panel_t{index:03d}.png

Explicit category paths:
    figures/cyclone_explorer/{ep_label}/{track_id}/synoptic_fields/panel_t{index:03d}.png
    figures/cyclone_explorer/{ep_label}/{track_id}/dynamic_fields/{product}/panel_t{index:03d}.png

Usage:
    python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py
    python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py --jobs 4
    python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py --subset 10

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import argparse
import logging
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import warnings
from metpy.units import units

from scripts.ep_structure_analysis.step3_precompute_composites import (
    compute_pv_at_level,
    temperature_advection_850,
    kinetic_energy_advection_250,
    rayleigh_kuo_criterion_250,
    ageostrophic_flux_convergence_250,
    barotropic_critical_region_250,
)

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
FIGURES_DIR = PROJECT_ROOT / "figures" / "cyclone_explorer"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DPI = 150  # Lower than paper figures (trade-off size vs quality)
# Panels are a 30°×30° view centered on the cyclone; a 15°×15° box is overlaid
DOMAIN_SIZE = 30.0  # degrees (panel domain)
INNER_BOX_SIZE = 15.0  # degrees (visual box shown inside panel)
INNER_BOX_HALF = INNER_BOX_SIZE / 2.0

# Plotting style
plt.rcParams.update({
    "font.size": 8,
    "font.family": "sans-serif",
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.dpi": 100,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "axes.grid": False,
})

# Vector plot parameters
VECTOR_SKIP = 8
VECTOR_SCALE = 150
VECTOR_WIDTH = 0.003

CLIMATOLOGY_250_FILE = DATA_DIR / "era5_climatology_250hPa.nc"

DYNAMIC_PRODUCTS = [
    "slp_pv850_wind850",
    "tadv_pv850_wind850",
    "afc_keadvanom_wind250",
    "rk_criterion_250",
    "btcr_critical_region",
]

_CLIM_CACHE = {}


# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"step6_cyclone_explorer_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("=" * 70)
    logging.info("STEP 6: GENERATE CYCLONE EXPLORER PANELS")
    logging.info("=" * 70)
    
    return log_file


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """Extract subdomain centered on cyclone."""
    half = domain_size / 2.0
    lat_min, lat_max = center_lat - half, center_lat + half
    lon_min, lon_max = center_lon - half, center_lon + half
    
    return ds.sel(
        latitude=slice(lat_max, lat_min),  # descending
        longitude=slice(lon_min, lon_max)
    )


def _add_cyclone_center_mark(ax, marker_size=100):
    """Add cyclone center marker at origin."""
    ax.scatter([0], [0], marker='x', s=marker_size, c='red', 
               linewidths=2, zorder=10, label='Cyclone center')


def _sel_level(da, levels, pc, target_hpa):
    """Select nearest pressure level from a DataArray."""
    idx = int(np.argmin(np.abs(levels - target_hpa)))
    return da.isel({pc: idx})


def _load_climatology_250():
    """Lazy-load 250 hPa climatology used in dynamic diagnostics."""
    key = str(CLIMATOLOGY_250_FILE)
    if key not in _CLIM_CACHE:
        _CLIM_CACHE[key] = xr.open_dataset(CLIMATOLOGY_250_FILE) if CLIMATOLOGY_250_FILE.exists() else None
    return _CLIM_CACHE[key]


def _interp_clim_250_to_domain(case_month, lat_1d, lon_1d):
    """Interpolate monthly climatology to current storm-relative subdomain."""
    ds_clim = _load_climatology_250()
    if ds_clim is None:
        return None
    return ds_clim.sel(month=case_month).interp(latitude=lat_1d, longitude=lon_1d, method="linear")


def _meridional_sign_reversal_mask(field, half_window=1):
    """Mask where field changes sign meridionally in a local window."""
    ny, nx = field.shape
    mask = np.zeros((ny, nx), dtype=bool)
    for i in range(ny):
        i0 = max(0, i - half_window)
        i1 = min(ny, i + half_window + 1)
        window = field[i0:i1, :]
        col_min = np.nanmin(window, axis=0)
        col_max = np.nanmax(window, axis=0)
        mask[i, :] = (col_min < 0.0) & (col_max > 0.0)
    return mask


# ============================================================================
# PANEL PLOTTING
# ============================================================================

def create_synoptic_panel_figure(ds_timestep, center_lat, center_lon, time_str, track_id):
    """
    Create 2×2 multi-panel figure for one timestep.
    
    Parameters
    ----------
    ds_timestep : xr.Dataset
        ERA5 data for single timestep (no time dimension)
    center_lat, center_lon : float
        Cyclone center coordinates
    time_str : str
        ISO format timestamp
    track_id : str
        Cyclone track ID
        
    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    # Extract subdomain
    ds_sub = extract_subdomain(ds_timestep, center_lat, center_lon, DOMAIN_SIZE)
    
    # Get pressure coordinate name
    pc = "pressure_level" if "pressure_level" in ds_sub.coords else "level"
    levels = ds_sub[pc].values
    
    def _sel(da, target_hPa):
        return _sel_level(da, levels, pc, target_hPa)
    
    # Extract fields - select appropriate pressure levels
    u_850 = _sel(ds_sub["u"], 850).values
    v_850 = _sel(ds_sub["v"], 850).values
    t_850 = _sel(ds_sub["t"], 850).values - 273.15  # K to °C
    q_975 = _sel(ds_sub["q"], 975).values * 1000  # kg/kg to g/kg
    z_500 = _sel(ds_sub["z"], 500).values / 9.81  # m²/s² to m
    # MSL may have pressure_level dim (constant across levels) - take first
    msl_raw = ds_sub["msl"]
    if pc in msl_raw.dims:
        msl_raw = msl_raw.isel({pc: 0})
    msl = msl_raw.values / 100  # Pa to hPa
    
    # Coordinates relative to center
    lats = ds_sub.latitude.values
    lons = ds_sub.longitude.values
    y = lats - center_lat
    x = lons - center_lon
    X, Y = np.meshgrid(x, y)
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    fig.suptitle(f"Track {track_id} — {time_str}", fontsize=11, fontweight='bold')
    
    # ────────────────────────────────────────────────────────────────────────
    # Top-left: SLP + 850 hPa wind vectors
    # Panels are a 30°×30° view centered on the cyclone; an inner 15°×15° box is
    # drawn to indicate the smaller composite region used elsewhere in the repo.
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[0, 0]
    cs = ax.contourf(X, Y, msl, levels=15, cmap='RdYlBu_r', extend='both')
    ax.contour(X, Y, msl, levels=10, colors='black', linewidths=0.5, alpha=0.4)
    
    # Wind vectors (subsample)
    skip = VECTOR_SKIP
    ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
              u_850[::skip, ::skip], v_850[::skip, ::skip],
              scale=VECTOR_SCALE, width=VECTOR_WIDTH, color='black', alpha=0.6)
    
    _add_cyclone_center_mark(ax)
    # draw inner 15°×15° box centered at origin
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("SLP + 850 hPa Winds", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="SLP (hPa)", shrink=0.8)
    
    # ────────────────────────────────────────────────────────────────────────
    # Top-right: Temperature 850 hPa
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[0, 1]
    cs = ax.contourf(X, Y, t_850, levels=15, cmap='RdBu_r', extend='both')
    ax.contour(X, Y, t_850, levels=10, colors='black', linewidths=0.5, alpha=0.4)
    _add_cyclone_center_mark(ax)
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("Temperature 850 hPa", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="T (°C)", shrink=0.8)
    
    # ────────────────────────────────────────────────────────────────────────
    # Bottom-left: Specific Humidity 975 hPa
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[1, 0]
    cs = ax.contourf(X, Y, q_975, levels=15, cmap='YlGnBu', extend='max')
    _add_cyclone_center_mark(ax)
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("Specific Humidity 975 hPa", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="q (g/kg)", shrink=0.8)
    
    # ────────────────────────────────────────────────────────────────────────
    # Bottom-right: Geopotential 500 hPa
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[1, 1]
    cs = ax.contourf(X, Y, z_500, levels=15, cmap='viridis', extend='both')
    ax.contour(X, Y, z_500, levels=10, colors='white', linewidths=0.5, alpha=0.6)
    _add_cyclone_center_mark(ax)
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("Geopotential 500 hPa", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="Z (m)", shrink=0.8)
    
    plt.tight_layout()
    return fig


def create_dynamic_panel_figure(ds_timestep, center_lat, center_lon, time_ts, track_id, product_id):
    """Create single-panel dynamic diagnostic figure for one timestep."""
    ds_sub = extract_subdomain(ds_timestep, center_lat, center_lon, DOMAIN_SIZE)
    pc = "pressure_level" if "pressure_level" in ds_sub.coords else "level"
    levels = ds_sub[pc].values

    lats = ds_sub.latitude.values
    lons = ds_sub.longitude.values
    y = lats - center_lat
    x = lons - center_lon
    X, Y = np.meshgrid(x, y)

    u850 = _sel_level(ds_sub["u"], levels, pc, 850) * units("m/s")
    v850 = _sel_level(ds_sub["v"], levels, pc, 850) * units("m/s")
    t850 = _sel_level(ds_sub["t"], levels, pc, 850) * units.kelvin
    u250 = _sel_level(ds_sub["u"], levels, pc, 250) * units("m/s")
    v250 = _sel_level(ds_sub["v"], levels, pc, 250) * units("m/s")
    z250 = _sel_level(ds_sub["z"], levels, pc, 250) * units("m**2/s**2")

    msl_da = ds_sub["msl"]
    if pc in msl_da.dims:
        msl_da = msl_da.isel({pc: 0})
    msl = msl_da.values / 100.0

    pv850 = compute_pv_at_level(
        _sel_level(ds_sub["u"], levels, pc, 825) * units("m/s"),
        _sel_level(ds_sub["u"], levels, pc, 850) * units("m/s"),
        _sel_level(ds_sub["u"], levels, pc, 875) * units("m/s"),
        _sel_level(ds_sub["v"], levels, pc, 825) * units("m/s"),
        _sel_level(ds_sub["v"], levels, pc, 850) * units("m/s"),
        _sel_level(ds_sub["v"], levels, pc, 875) * units("m/s"),
        _sel_level(ds_sub["t"], levels, pc, 825) * units.kelvin,
        _sel_level(ds_sub["t"], levels, pc, 850) * units.kelvin,
        _sel_level(ds_sub["t"], levels, pc, 875) * units.kelvin,
        np.array([
            levels[int(np.argmin(np.abs(levels - 825)))],
            levels[int(np.argmin(np.abs(levels - 850)))],
            levels[int(np.argmin(np.abs(levels - 875)))],
        ]) * 100.0,
    ) * 1e6

    tadv850 = temperature_advection_850(u850, v850, t850).metpy.unit_array.magnitude * 3600.0

    case_month = pd.Timestamp(time_ts).month
    clim250 = _interp_clim_250_to_domain(case_month, lats, lons)

    fig, ax = plt.subplots(1, 1, figsize=(6.6, 6.2))
    ax.set_xlabel("Longitude offset (deg)")
    ax.set_ylabel("Latitude offset (deg)")
    title_time = pd.Timestamp(time_ts).strftime("%Y-%m-%d %H:%M UTC")
    ax.set_title(f"Track {track_id} - {title_time}", fontsize=10, fontweight="bold")

    if product_id == "slp_pv850_wind850":
        vmax = np.nanpercentile(np.abs(pv850), 98)
        vmax = max(vmax, 0.1)
        im = ax.contourf(X, Y, pv850, levels=np.linspace(-vmax, vmax, 21), cmap="RdBu_r", extend="both")
        ax.contour(X, Y, msl, levels=10, colors="black", linewidths=0.8, alpha=0.4)
        skip = VECTOR_SKIP
        ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
                  u850.values[::skip, ::skip], v850.values[::skip, ::skip],
                  scale=120, width=VECTOR_WIDTH, color="gray", alpha=0.8)
        cbar_label = "PV850 (PVU)"
        subtitle = "SLP + PV at 850 hPa + wind at 850 hPa"

    elif product_id == "tadv_pv850_wind850":
        vmax = np.nanpercentile(np.abs(pv850), 98)
        vmax = max(vmax, 0.1)
        im = ax.contourf(X, Y, pv850, levels=np.linspace(-vmax, vmax, 21), cmap="RdBu_r", extend="both")
        neg_levels = np.array([-0.12, -0.08, -0.04])
        pos_levels = np.array([0.04, 0.08, 0.12])
        neg = neg_levels[neg_levels >= np.nanmin(tadv850)]
        pos = pos_levels[pos_levels <= np.nanmax(tadv850)]
        if len(neg):
            ax.contour(X, Y, tadv850, levels=neg, colors="steelblue", linewidths=1.2, linestyles="dashed")
        if len(pos):
            ax.contour(X, Y, tadv850, levels=pos, colors="firebrick", linewidths=1.2, linestyles="solid")
        skip = VECTOR_SKIP
        ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
                  u850.values[::skip, ::skip], v850.values[::skip, ::skip],
                  scale=120, width=VECTOR_WIDTH, color="gray", alpha=0.8)
        ax.contour(X, Y, msl, levels=10, colors="black", linewidths=0.6, alpha=0.25)
        cbar_label = "PV850 (PVU)"
        subtitle = "Temperature advection + PV at 850 hPa + wind"

    elif product_id == "afc_keadvanom_wind250":
        if clim250 is None:
            ax.text(0.5, 0.5, "250 hPa climatology unavailable", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10)
            im = None
            cbar_label = None
            subtitle = "AFC + KE advection anomaly at 250 hPa"
        else:
            u250_p = u250 - (xr.DataArray(clim250["u_clim"].values, coords=u250.coords, dims=u250.dims) * units("m/s"))
            v250_p = v250 - (xr.DataArray(clim250["v_clim"].values, coords=v250.coords, dims=v250.dims) * units("m/s"))
            ke_adv_anom = kinetic_energy_advection_250(u250_p, v250_p).metpy.unit_array.magnitude
            afc = ageostrophic_flux_convergence_250(
                u250, v250, z250,
                clim250["u_clim"], clim250["v_clim"], clim250["z_clim"],
            ).values
            vmax = np.nanpercentile(np.abs(afc), 98)
            vmax = max(vmax, 1e-6)
            im = ax.contourf(X, Y, afc, levels=np.linspace(-vmax, vmax, 21), cmap="RdBu_r", extend="both")
            ka = np.nanpercentile(np.abs(ke_adv_anom), 90)
            ka = max(ka, 1e-8)
            ax.contour(X, Y, ke_adv_anom, levels=[-ka, -0.5 * ka], colors="steelblue", linewidths=1.1, linestyles="dashed")
            ax.contour(X, Y, ke_adv_anom, levels=[0.5 * ka, ka], colors="firebrick", linewidths=1.1, linestyles="solid")

            skip = VECTOR_SKIP
            u_plot = u250.values[::skip, ::skip].copy()
            v_plot = v250.values[::skip, ::skip].copy()
            speed = np.sqrt(u_plot ** 2 + v_plot ** 2)
            mask = speed < 30.0
            u_plot[mask] = np.nan
            v_plot[mask] = np.nan
            ax.quiver(X[::skip, ::skip], Y[::skip, ::skip], u_plot, v_plot,
                      scale=350, width=VECTOR_WIDTH, color="gray", alpha=0.9)
            ax.contour(X, Y, msl, levels=10, colors="black", linewidths=0.6, alpha=0.25)
            cbar_label = "AFC250 (m2 s-3)"
            subtitle = "AFC250 + KE advection anomaly250 + wind > 30 m/s"

    elif product_id == "rk_criterion_250":
        rk = rayleigh_kuo_criterion_250(u250, v250).magnitude
        vmax = np.nanpercentile(np.abs(rk), 98)
        vmax = max(vmax, 1e-11)
        im = ax.contourf(X, Y, rk, levels=np.linspace(-vmax, vmax, 21), cmap="RdBu_r", extend="both")
        ax.contour(X, Y, rk, levels=[0], colors="black", linewidths=1.2)
        skip = VECTOR_SKIP
        ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
                  u250.values[::skip, ::skip], v250.values[::skip, ::skip],
                  scale=300, width=VECTOR_WIDTH, color="gray", alpha=0.7)
        cbar_label = "RK criterion (s-1 m-1)"
        subtitle = "RK criterion at 250 hPa"

    elif product_id == "btcr_critical_region":
        if clim250 is None:
            ax.text(0.5, 0.5, "250 hPa climatology unavailable", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10)
            im = None
            cbar_label = None
            subtitle = "Barotropic critical region (BtCR)"
        else:
            dm, da = barotropic_critical_region_250(clim250["u_clim"], clim250["v_clim"])
            dm_scaled = dm * 1e9
            vmax = np.nanpercentile(np.abs(dm_scaled), 98)
            vmax = max(vmax, 0.1)
            im = ax.contourf(X, Y, dm_scaled, levels=np.linspace(-vmax, vmax, 31), cmap="RdBu_r", extend="both")
            ax.contour(X, Y, dm_scaled, levels=[0], colors="black", linewidths=1.2)

            ws250 = np.sqrt(u250.values ** 2 + v250.values ** 2)
            ax.contour(X, Y, ws250, levels=np.arange(20, 80, 10), colors="dimgray",
                       linewidths=0.8, linestyles="--", alpha=0.6)

            sk = VECTOR_SKIP
            xx = X[::sk, ::sk]
            yy = Y[::sk, ::sk]
            aa = da[::sk, ::sk]
            mask = ~np.isnan(aa)
            if np.any(mask):
                cos_a = np.where(mask, np.cos(aa), np.nan)
                sin_a = np.where(mask, np.sin(aa), np.nan)
                for sign in (+1, -1):
                    ax.quiver(xx, yy, sign * cos_a, sign * sin_a,
                              scale=0.7, scale_units="xy", headwidth=0,
                              headlength=0, headaxislength=0, width=0.002,
                              color="black", alpha=0.65, pivot="middle")

            cbar_label = "Delta_m x 1e9 (s-2)"
            subtitle = "Barotropic critical region (BtCR)"

    else:
        raise ValueError(f"Unknown dynamic product: {product_id}")

    _add_cyclone_center_mark(ax, marker_size=90)
    rect = mpatches.Rectangle(
        (-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
        linewidth=1.0, edgecolor="black", linestyle="--", facecolor="none", zorder=9
    )
    ax.add_patch(rect)
    ax.set_xlim(-DOMAIN_SIZE / 2.0, DOMAIN_SIZE / 2.0)
    ax.set_ylim(-DOMAIN_SIZE / 2.0, DOMAIN_SIZE / 2.0)
    ax.text(0.01, 0.01, subtitle, transform=ax.transAxes, fontsize=8,
            ha="left", va="bottom", bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"})

    if im is not None and cbar_label:
        cb = plt.colorbar(im, ax=ax, shrink=0.82)
        cb.set_label(cbar_label, fontsize=8)

    plt.tight_layout()
    return fig


# ============================================================================
# PROCESSING
# ============================================================================

def process_one_cyclone(task):
    """
    Generate panel figures for all timesteps of one cyclone.

    This function now centers each timestep on the cyclone position at that
    timestep (nearest track point), instead of using a single fixed center for
    the whole intensification phase. This ensures the explorer panels follow
    the cyclone as it evolves.

    Parameters
    ----------
    task : tuple (track_id, ep_label, center_lat, center_lon)

    Returns
    -------
    track_id : str
    n_panels : int
        Number of panels generated
    error : str or None
    """
    track_id, ep_label, center_lat, center_lon = task
    track_id = str(track_id)

    nc_file = DATA_DIR / f"{track_id}_era5.nc"

    if not nc_file.exists():
        return track_id, 0, "missing_nc"

    try:
        # Open NetCDF
        ds = xr.open_dataset(nc_file)
        tc = "valid_time" if "valid_time" in ds.dims else "time"
        n_times = len(ds[tc])

        # Load local tracks file (per-timestep cyclone positions)
        tracks_file = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"
        if not tracks_file.exists():
            # fallback: use fixed center for all timesteps (maintain previous behavior)
            tracks_df = None
            logging.warning(f"Tracks file not found: {tracks_file} — using fixed center")
        else:
            tracks_df = pd.read_csv(tracks_file, parse_dates=["date"])
            tracks_df = tracks_df[tracks_df["track_id"] == int(track_id)] if tracks_df["track_id"].dtype != object else tracks_df[tracks_df["track_id"] == track_id]

        # Create output directory
        out_dir = FIGURES_DIR / ep_label.lower() / track_id
        out_dir.mkdir(parents=True, exist_ok=True)
        syn_dir = out_dir / "synoptic_fields"
        syn_dir.mkdir(parents=True, exist_ok=True)
        dyn_root = out_dir / "dynamic_fields"
        for product in DYNAMIC_PRODUCTS:
            (dyn_root / product).mkdir(parents=True, exist_ok=True)

        # Generate panel for each timestep
        for t_idx in range(n_times):
            ds_t = ds.isel({tc: t_idx})
            # time value in NetCDF may be seconds since epoch
            tval = ds[tc].values[t_idx]
            time_ts = pd.to_datetime(tval)
            time_str = time_ts.strftime("%Y-%m-%d %H:%M UTC")

            # Determine cyclone center for this timestep (nearest track point)
            if tracks_df is not None and not tracks_df.empty:
                # Find nearest time in tracks_df
                diffs = (tracks_df["date"] - time_ts).abs()
                nearest = tracks_df.loc[diffs.idxmin()]
                cur_lat = float(nearest["lat vor"]) if "lat vor" in nearest.index else float(nearest.get("lat", center_lat))
                cur_lon = float(nearest["lon vor"]) if "lon vor" in nearest.index else float(nearest.get("lon", center_lon))
            else:
                # Use fixed center (previous behavior)
                cur_lat, cur_lon = center_lat, center_lon

            fig = create_synoptic_panel_figure(ds_t, cur_lat, cur_lon, time_str, track_id)

            out_path = out_dir / f"panel_t{t_idx:03d}.png"
            fig.savefig(out_path, dpi=DPI, bbox_inches='tight')
            plt.close(fig)

            # Explicit synoptic category path (same content)
            syn_path = syn_dir / f"panel_t{t_idx:03d}.png"
            fig = create_synoptic_panel_figure(ds_t, cur_lat, cur_lon, time_str, track_id)
            fig.savefig(syn_path, dpi=DPI, bbox_inches='tight')
            plt.close(fig)

            # Dynamic products
            for product in DYNAMIC_PRODUCTS:
                fig_dyn = create_dynamic_panel_figure(ds_t, cur_lat, cur_lon, time_ts, track_id, product)
                dyn_path = dyn_root / product / f"panel_t{t_idx:03d}.png"
                fig_dyn.savefig(dyn_path, dpi=DPI, bbox_inches='tight')
                plt.close(fig_dyn)

        ds.close()
        return track_id, n_times, None

    except Exception as e:
        return track_id, 0, str(e)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate cyclone explorer panels")
    parser.add_argument("--jobs", "-j", type=int, default=1,
                       help="Number of parallel workers (default: 1)")
    parser.add_argument("--subset", "-s", type=int, default=None,
                       help="Process only first N cyclones per EP (for testing)")
    parser.add_argument("--track-ids", "-t", type=str, default=None,
                       help="Comma-separated list of specific track IDs to process")
    parser.add_argument("--selection-file", "-f", type=str, default=None,
                       help="CSV file with track_id column to process specific cyclones")
    args = parser.parse_args()
    
    log_file = setup_logging()
    logging.info(f"   Parallel workers: {args.jobs}")
    if args.subset:
        logging.info(f"   Subset mode: {args.subset} cyclones per EP")
    
    # Load cases
    ep1_cases = pd.read_csv(RESULTS_DIR / "ep1_cases.csv")
    ep2_cases = pd.read_csv(RESULTS_DIR / "ep2_cases.csv")
    
    # Filter to only cases with ERA5 data available
    ep1_with_data = []
    for _, row in ep1_cases.iterrows():
        track_id = str(row['track_id'])
        if (DATA_DIR / f"{track_id}_era5.nc").exists():
            ep1_with_data.append(row)
    ep1_cases = pd.DataFrame(ep1_with_data) if ep1_with_data else pd.DataFrame()
    
    ep2_with_data = []
    for _, row in ep2_cases.iterrows():
        track_id = str(row['track_id'])
        if (DATA_DIR / f"{track_id}_era5.nc").exists():
            ep2_with_data.append(row)
    ep2_cases = pd.DataFrame(ep2_with_data) if ep2_with_data else pd.DataFrame()
    
    logging.info(f"   EP1 with ERA5 data: {len(ep1_cases)} cases")
    logging.info(f"   EP2 with ERA5 data: {len(ep2_cases)} cases")
    
    # Filter by specific track IDs if provided
    if args.track_ids:
        target_ids = set(args.track_ids.split(","))
        ep1_cases = ep1_cases[ep1_cases["track_id"].astype(str).isin(target_ids)]
        ep2_cases = ep2_cases[ep2_cases["track_id"].astype(str).isin(target_ids)]
        logging.info(f"   Filtered to {len(target_ids)} specific track IDs")
    elif args.selection_file:
        selection = pd.read_csv(args.selection_file)
        target_ids = set(selection["track_id"].astype(str).tolist())
        ep1_cases = ep1_cases[ep1_cases["track_id"].astype(str).isin(target_ids)]
        ep2_cases = ep2_cases[ep2_cases["track_id"].astype(str).isin(target_ids)]
        logging.info(f"   Filtered to {len(target_ids)} track IDs from {args.selection_file}")
    elif args.subset:
        ep1_cases = ep1_cases.head(args.subset) if not ep1_cases.empty else ep1_cases
        ep2_cases = ep2_cases.head(args.subset) if not ep2_cases.empty else ep2_cases
    
    logging.info(f"   EP1: {len(ep1_cases)} cases")
    logging.info(f"   EP2: {len(ep2_cases)} cases")
    
    # Combine and prepare task list (track_id, ep_label, center_lat, center_lon)
    tasks = []
    for _, row in ep1_cases.iterrows():
        tasks.append((row['track_id'], 'EP1', row['center_lat'], row['center_lon']))
    for _, row in ep2_cases.iterrows():
        tasks.append((row['track_id'], 'EP2', row['center_lat'], row['center_lon']))
    
    logging.info(f"\n   Total tasks: {len(tasks)}")
    logging.info(f"   Output: {FIGURES_DIR}")
    
    # Process
    success = 0
    total_panels = 0
    failed = []
    
    if args.jobs == 1:
        # Sequential
        for task in tqdm(tasks, desc="Generating panels"):
            tid, n_panels, error = process_one_cyclone(task)
            if error:
                failed.append((tid, error))
            else:
                success += 1
                total_panels += n_panels
    else:
        # Parallel
        with ProcessPoolExecutor(max_workers=args.jobs) as executor:
            futures = {executor.submit(process_one_cyclone, task): task[0] 
                      for task in tasks}
            
            for future in tqdm(as_completed(futures), total=len(tasks), 
                             desc="Generating panels"):
                tid, n_panels, error = future.result()
                if error:
                    failed.append((tid, error))
                else:
                    success += 1
                    total_panels += n_panels
    
    # Summary
    logging.info("\n" + "=" * 70)
    logging.info("SUMMARY")
    logging.info("=" * 70)
    logging.info(f"   Success: {success}/{len(tasks)} cyclones")
    logging.info(f"   Total panels generated: {total_panels}")
    logging.info(f"   Failed: {len(failed)}")
    
    if failed and len(failed) <= 20:
        logging.info("\n   Failed cases:")
        for tid, error in failed:
            logging.info(f"     {tid}: {error}")
    
    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 6 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"Log: {log_file}")
    logging.info(f"\nNext: python scripts/web/extract_cyclone_explorer_data.py")


if __name__ == "__main__":
    main()
