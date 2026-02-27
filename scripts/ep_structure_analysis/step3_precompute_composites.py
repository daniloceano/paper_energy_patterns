"""
Step 3: Precompute Composites for EP1 & EP2

Computes spatial composites (30°×30° domain) for each EP group:
  - EGR (Eady Growth Rate) from the 500–850 hPa layer (Besson et al. 2021)
  - PV at 200 hPa (upper-level tropopause dynamics)
  - PV at 850 hPa (low-level PV anomaly)
  - Temperature advection at 850 hPa  (-V · ∇T)
  - SLP (mean sea level pressure)

For each EP, saves a single NetCDF file with composite means on a
regular grid centred on the cyclone.

Output:
  data/era5_ep_structure/precomputed_composites_ep1.nc
  data/era5_ep_structure/precomputed_composites_ep2.nc

⚠ IMPORTANT — UNIT CONSISTENCY:
  All diagnostic functions receive xarray DataArrays with pint units attached
  via MetPy (e.g., ``da * units("m/s")``).  Extra care is required when mixing
  MetPy functions, pint quantities, and plain numpy operations:

  1. MetPy calc functions (advection, divergence, potential_temperature, etc.)
     return **pint-backed DataArrays**, NOT pint.Quantity.  To extract the
     plain ndarray use ``.metpy.unit_array.magnitude`` — never ``.magnitude``
     (which only exists on pint.Quantity objects).

  2. ``coriolis_parameter()`` returns a DataArray when given a DataArray
     coordinate, but a pint.Quantity when given ``values * units.degree``.
     Be explicit about the input type.

  3. When using ``np.where`` on pint-backed DataArrays, threshold values
     must carry compatible units (``1.0 * units('m')``, not ``1.0``).

  4. Physical constants from ``metpy.constants`` are pint.Quantity with
     ``.magnitude`` (or ``.m``) for the raw float.  Arithmetic between a
     pint.Quantity constant and a pint-backed DataArray preserves units
     automatically.

  See ``eady_growth_rate()`` for a reference implementation that preserves
  DataArray structure and units throughout all intermediate steps.

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
import warnings
import argparse
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from functools import partial
from tqdm import tqdm

from metpy.calc import (
    potential_temperature,
    potential_vorticity_baroclinic,
    advection as metpy_advection,
    divergence as metpy_divergence,
    lat_lon_grid_deltas,
    coriolis_parameter
)
from metpy.units import units
import metpy.constants as mpconstants

# ============================================================================
# PHYSICAL CONSTANTS  (sourced from metpy.constants for consistency)
# ============================================================================
# All constants are kept as pint.Quantity so that derived expressions
# (e.g. z / G) carry correct units automatically.

G       = mpconstants.earth_gravity            # pint.Quantity  9.80665 m s⁻²
OMEGA   = mpconstants.earth_avg_angular_vel    # pint.Quantity  7.2921e-5 rad s⁻¹
R_d     = mpconstants.dry_air_gas_constant     # pint.Quantity  287.058 J kg⁻¹ K⁻¹
C_p     = mpconstants.dry_air_spec_heat_press  # pint.Quantity  1004.709 J kg⁻¹ K⁻¹
KAPPA   = mpconstants.poisson_exponent         # pint.Quantity  Rd / Cp_d  ≈ 0.2854
P_0     = mpconstants.pot_temp_ref_press       # pint.Quantity  100000 Pa
R_EARTH = mpconstants.earth_avg_radius         # pint.Quantity  6.3712e6 m

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DOMAIN_SIZE = 30.0    # degrees (30° × 30°)
RESOLUTION = 0.25     # degrees

# EGR quality control
MIN_LAT = 5.0
MAX_EGR_DAY = 5.0
MIN_N_SQUARED = 1e-6

# AFC climatology file (produced by step2_1)
CLIMATOLOGY_FILE = DATA_DIR / "era5_climatology_250hPa.nc"

# Module-level cache for climatology (loaded once, shared across cases)
_CLIMATOLOGY_DS = None


def _load_climatology():
    """
    Lazy-load the 250 hPa climatology for AFC computation.

    Returns the xr.Dataset with variables u_clim, v_clim, z_clim and
    dimension ``month`` (1–12).  Loaded once and cached in module global.
    """
    global _CLIMATOLOGY_DS
    if _CLIMATOLOGY_DS is None:
        if not CLIMATOLOGY_FILE.exists():
            logging.warning(
                f"   AFC climatology not found: {CLIMATOLOGY_FILE.name}. "
                "Run step2_1 first.  AFC will be skipped."
            )
            return None
        _CLIMATOLOGY_DS = xr.open_dataset(CLIMATOLOGY_FILE)
        logging.info(f"   Loaded AFC climatology: {CLIMATOLOGY_FILE.name}")
    return _CLIMATOLOGY_DS


# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"ep_structure_composites_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("=" * 70)
    logging.info("STEP 3: PRECOMPUTE COMPOSITES – EP STRUCTURE ANALYSIS")
    logging.info("=" * 70)
    logging.info(f"Log: {log_file}")
    return log_file


# ============================================================================
# DIAGNOSTICS
# ============================================================================

def compute_spherical_grid_spacing(lat_1d, lon_1d):
    """
    Compute grid spacing (dx, dy) on a spherical Earth.
    
    Following spherical geometry:
    - dy = R * Δφ (constant in latitude)
    - dx = R * cos(φ) * Δλ (latitude-dependent)
    
    Parameters
    ----------
    lat_1d : array_like
        1D latitude array in degrees (must be monotonic)
    lon_1d : array_like
        1D longitude array in degrees (must be monotonic)
    
    Returns
    -------
    dx : ndarray (2D)
        Grid spacing in x-direction (meters)
    dy : ndarray (2D)
        Grid spacing in y-direction (meters)
    lat_2d : ndarray (2D)
        2D latitude grid
    lon_2d : ndarray (2D)
        2D longitude grid
    
    Notes
    -----
    Latitude should be monotonically increasing (South to North).
    If decreasing, gradients will have correct sign automatically.
    """
    # Verify monotonicity
    lat_diff = np.diff(lat_1d)
    lon_diff = np.diff(lon_1d)
    
    if not (np.all(lat_diff > 0) or np.all(lat_diff < 0)):
        raise ValueError("Latitude must be monotonic (all increasing or all decreasing)")
    if not (np.all(lon_diff > 0) or np.all(lon_diff < 0)):
        raise ValueError("Longitude must be monotonic (all increasing or all decreasing)")
    
    # Create 2D grids
    lat_2d, lon_2d = np.meshgrid(lat_1d, lon_1d, indexing='ij')
    
    # Compute grid spacing
    # dy: spacing in meridional direction (constant per latitude band)
    dlat = np.gradient(lat_1d)  # degrees
    dy = R_EARTH.m * np.deg2rad(dlat)  # meters

    # dx: spacing in zonal direction (varies with latitude)
    dlon = np.gradient(lon_1d)  # degrees
    dx = R_EARTH.m * np.cos(np.deg2rad(lat_2d)) * np.deg2rad(
        np.broadcast_to(dlon[np.newaxis, :], lat_2d.shape)
    )  # meters
    
    return dx, dy, lat_2d, lon_2d


def _metpy_grid_deltas(lat_1d, lon_1d):
    """
    Return MetPy-compatible 2D grid spacing via metpy.calc.lat_lon_grid_deltas.

    MetPy's divergence / advection require spacing arrays with one element
    *fewer* than the data along the applicable axis:
      dx  →  shape (ny, nx-1)   spacing in the x (longitude) direction
      dy  →  shape (ny-1, nx)   spacing in the y (latitude)  direction

    Using lat_lon_grid_deltas ensures that spherical (ellipsoidal) geometry
    is accounted for consistently with MetPy internals.

    Parameters
    ----------
    lat_1d : array_like, shape (ny,)
        1-D latitude array in degrees.
    lon_1d : array_like, shape (nx,)
        1-D longitude array in degrees.

    Returns
    -------
    dx : pint.Quantity, shape (ny, nx-1)  [metres]
    dy : pint.Quantity, shape (ny-1, nx)  [metres]
    """
    lon_2d, lat_2d = np.meshgrid(lon_1d, lat_1d)   # both (ny, nx)
    return lat_lon_grid_deltas(
        lon_2d * units.degree,
        lat_2d * units.degree,
    )


def spherical_divergence(u, v):
    """
    Compute horizontal divergence on a spherical Earth using MetPy.

    Uses metpy.calc.divergence with grid spacing derived from
    compute_spherical_grid_spacing to account for spherical geometry.

    Parameters
    ----------
    u : xr.DataArray (2D, latitude × longitude)
        Zonal wind component (m/s)
    v : xr.DataArray (2D, latitude × longitude)
        Meridional wind component (m/s)

    Returns
    -------
    divergence : xr.DataArray (2D, pint-backed)
        Horizontal divergence (s⁻¹).  Preserves DataArray structure and
        pint units for downstream unit-safety checks.
    """
    lat_1d = u.latitude.values
    lon_1d = u.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # u and v are unit-tagged DataArrays — pass directly.
    # MetPy returns a pint-backed DataArray — preserve it.
    return metpy_divergence(u, v, dx=dx, dy=dy)


def eady_growth_rate(u_500, v_500, u_850, v_850,
                     T_500, T_850, z_500, z_850):
    """
    Eady Growth Rate (EGR) for the 500–850 hPa layer.

    Following Besson et al. (2021, WCD, 2, 991–1009), Eqs. (4)–(5):

        σ_EGR = 0.31 · |f| / N · |∂V/∂z|     (Lindzen & Farrell, 1980)

    Discretized for the 500–850 hPa layer (Besson et al. 2021, Eq. 5):

        |∂V/∂z| = √((u₅₀₀−u₈₅₀)² + (v₅₀₀−v₈₅₀)²) / (z₅₀₀−z₈₅₀)

    Brunt–Väisälä frequency from finite differences in the same layer:

        N² = (g / θ̄) · (θ₅₀₀ − θ₈₅₀) / (z₅₀₀ − z₈₅₀)

    where θ̄ = (θ₅₀₀ + θ₈₅₀)/2 is the layer-mean dry potential temperature.

    This uses dry potential temperature (no virtual correction), consistent
    with the standard EGR formulation in the literature.

    Parameters
    ----------
    u_500, v_500 : xr.DataArray (2D, latitude × longitude)
        Wind at 500 hPa.  Must carry metpy units (m/s).
    u_850, v_850 : xr.DataArray (2D, latitude × longitude)
        Wind at 850 hPa.  Must carry metpy units (m/s).
    T_500, T_850 : xr.DataArray (2D, latitude × longitude)
        Temperature at 500 and 850 hPa.  Must carry metpy units (K).
    z_500, z_850 : xr.DataArray (2D, latitude × longitude)
        Geopotential at 500 and 850 hPa.  Must carry metpy units (m² s⁻²).

    Returns
    -------
    egr_day : ndarray (2D)
        Eady growth rate in day⁻¹.  NaN where masked.

    References
    ----------
    Lindzen, R. S. and Farrell, B. (1980). J. Atmos. Sci., 37, 1648–1654.
    Besson, P., Fischer, L. J., Schemm, S. and Sprenger, M. (2021).
        Weather Clim. Dynam., 2, 991–1009. doi:10.5194/wcd-2-991-2021

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has been carefully validated for unit consistency.  All
    intermediate variables are kept as pint-backed DataArrays so that unit
    tracking is automatic and physically verifiable.  DO NOT replace
    DataArray arithmetic with bare-ndarray arithmetic, and DO NOT strip
    units prematurely — see the module-level docstring for rationale.
    """
    # ── Coriolis parameter ──────────────────────────────────────────────────
    # Pass plain values with units so coriolis_parameter returns pint.Quantity
    # (passing a DataArray coordinate would return a DataArray without .magnitude).
    f_pint = coriolis_parameter(T_850.latitude * units.degree)
    f_abs = np.abs(f_pint)                                # s⁻¹, 1-D

    # ── Dry potential temperature ───────────────────────────────────────────
    # Standard EGR uses dry θ (Besson et al. 2021; Hoskins & Valdes, 1990).
    theta_500 = potential_temperature(500.0 * units.hPa, T_500)
    theta_850 = potential_temperature(850.0 * units.hPa, T_850)

    # # Extract plain ndarrays (K) for clean numpy arithmetic.
    # theta_500_K = theta_500.metpy.unit_array.magnitude              # 2-D, K
    # theta_850_K = theta_850.metpy.unit_array.magnitude              # 2-D, K

    # ── Geopotential height ─────────────────────────────────────────────────
    z_h_500 = (z_500 / G)                # 2-D, m
    z_h_850 = (z_850 / G)                # 2-D, m

    # ── Layer thickness ─────────────────────────────────────────────────────
    dz = z_h_500 - z_h_850                                          # m (positive)
    dz_safe = np.where(np.abs(dz) > 1.0 * units(str(dz.metpy.units)), dz, np.nan)

    # Revert to DataArrays with units for N² and shear calculations, to preserve units and avoid mistakes in unit conversions.
    dz_safe_da = xr.DataArray(dz_safe * units(str(dz.metpy.units)), coords=theta_500.coords, dims=theta_500.dims)  # m

    # ── Brunt–Väisälä frequency (finite difference 500–850 hPa) ─────────
    # N² = (g / θ̄) · Δθ / Δz   [s⁻²]
    theta_mean = 0.5 * (theta_500 + theta_850)                         # K
    dtheta     = theta_500 - theta_850                                 # K
    N_sq       = (G / theta_mean) * (dtheta / dz_safe_da)              # s⁻²
    N          = np.where(N_sq > MIN_N_SQUARED * units(str(N_sq.metpy.units)),
                          np.sqrt(N_sq), np.nan)                       # s⁻¹
    
    # N to DataArray with units for broadcasting in EGR calculation.
    # Use sqrt(N_sq) to preserve units and avoid mistakes in unit conversions.
    N_da = xr.DataArray(N * units(str(np.sqrt(N_sq).metpy.units)),
                        coords=theta_500.coords, dims=theta_500.dims)

    # ── Vertical wind shear |∂V/∂z| ─────────────────────────────────────────
    du = (u_500 - u_850)                        # m s⁻¹
    dv = (v_500 - v_850)                        # m s⁻¹
    du_dz = du / dz_safe_da                     # s⁻¹
    dv_dz = dv / dz_safe_da                     # s⁻¹
    shear = np.sqrt(du_dz ** 2 + dv_dz ** 2)    # s⁻¹

    # ── EGR = 0.31 · |f| / N · shear ────────────────────────────────────────
    # f_abs is 1-D (nlat,) — broadcast to 2-D with [:, np.newaxis].
    # All other arrays are 2-D (nlat, nlon) plain ndarrays.
    egr = 0.31 * (f_abs / N_da) * shear  # s⁻¹, 2-D

    # Convert s⁻¹ → day⁻¹ and apply upper-bound QC
    egr_day = egr.metpy.convert_units('1/day')
    egr_day = np.where(egr_day > MAX_EGR_DAY * units('1/day'), np.nan, egr_day)
    return egr_day


def compute_pv_at_level(u_low, u_mid, u_high,
                         v_low, v_mid, v_high,
                         T_low, T_mid, T_high,
                         p_3lev_pa):
    """
    Baroclinic PV using MetPy with 3 vertical levels (centred FD).
    Returns PV at the middle level in SI units (K m² kg⁻¹ s⁻¹).

    Parameters
    ----------
    u_low/mid/high, v_low/mid/high, T_low/mid/high : xr.DataArray (2D)
        Fields at the lower, middle, and upper surrounding levels.
    p_3lev_pa : array_like, shape (3,)
        Pressure values [low, mid, high] in Pa.
    """
    p_hpa = np.asarray(p_3lev_pa) / 100.0

    # Build 3-level DataArrays via xr.concat — no .values, no np.stack,
    # preserves xarray structure (lat/lon coords) and pint units from
    # compute_composite.
    level_coord = xr.Variable("level", p_hpa)
    concat_kw   = dict(compat="override", coords="minimal")

    T_da = xr.concat([T_low, T_mid, T_high], dim=level_coord, **concat_kw)
    u_da = xr.concat([u_low, u_mid, u_high], dim=level_coord, **concat_kw)
    v_da = xr.concat([v_low, v_mid, v_high], dim=level_coord, **concat_kw)
    p_da = xr.DataArray(p_hpa, coords={"level": p_hpa}, dims=["level"]) * units.hPa

    theta = potential_temperature(p_da, T_da)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        pv = potential_vorticity_baroclinic(theta, p_da, u_da, v_da)

    return pv.isel(level=1).metpy.unit_array.magnitude


def temperature_advection_850(u_850, v_850, T_850):
    """
    Horizontal temperature advection at 850 hPa via MetPy:
      advT = -V · ∇T = -(u ∂T/∂x + v ∂T/∂y)

    Parameters
    ----------
    u_850, v_850, T_850 : xr.DataArray (2D, latitude × longitude)
        Winds (m/s) and temperature (K) at 850 hPa.

    Returns
    -------
    advT : xr.DataArray (2D, pint-backed)
        Temperature advection (K s⁻¹).  Preserves DataArray structure
        and pint units for downstream unit-safety checks.
        Positive: warm air advection; Negative: cold air advection.
    """
    lat_1d = T_850.latitude.values
    lon_1d = T_850.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # All three are unit-tagged DataArrays — pass directly.
    # MetPy returns a pint-backed DataArray — preserve it.
    return metpy_advection(T_850, u=u_850, v=v_850, dx=dx, dy=dy)


def kinetic_energy_advection_250(u_250, v_250):
    """
    Kinetic energy advection at 250 hPa (jet level) via MetPy.

    KE_adv = -V · ∇(KE) = -V · ∇(0.5·(u² + v²))

    Parameters
    ----------
    u_250, v_250 : xr.DataArray (2D, latitude × longitude)
        Zonal and meridional wind at 250 hPa (m/s).

    Returns
    -------
    ke_adv : xr.DataArray (2D, pint-backed)
        Kinetic energy advection (m² s⁻³ = W kg⁻¹).  Preserves DataArray
        structure and pint units for downstream unit-safety checks.
        Positive: KE increasing; Negative: KE decreasing.
    """
    lat_1d = u_250.latitude.values
    lon_1d = u_250.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # u_250 and v_250 are unit-tagged DataArrays (m/s); arithmetic preserves units.
    KE = 0.5 * (u_250 ** 2 + v_250 ** 2)         # DataArray [m² s⁻²]

    # MetPy returns a pint-backed DataArray — preserve it.
    return metpy_advection(KE, u=u_250, v=v_250, dx=dx, dy=dy)  # [m² s⁻³]


def rayleigh_kuo_criterion_250(u_250, v_250):
    """
    Simplified Rayleigh-Kuo instability criterion at 250 hPa.

    ∂q/∂y ≈ β - ∂²u/∂y²

    where β = 2Ω cosφ / R_earth (meridional gradient of Coriolis).
    Regions where ∂q/∂y < 0 satisfy the necessary condition for instability.

    Parameters
    ----------
    u_250, v_250 : xr.DataArray (2D, latitude × longitude)
        Zonal and meridional wind at 250 hPa (m/s).

    Returns
    -------
    rk_criterion : pint.Quantity (2D)
        ∂q/∂y field.  Carries pint units (s⁻¹ m⁻¹) so that downstream
        arithmetic catches any dimensional inconsistency automatically.
    """
    lat_1d = u_250.latitude.values
    lon_1d = u_250.longitude.values

    # 2-D latitude grid (plain ndarray, degrees)
    lat_2d, _ = np.meshgrid(lat_1d, lon_1d, indexing='ij')

    # Grid spacing with pint units (metres) for dimensional tracking.
    dlat = np.gradient(lat_1d)                       # degrees
    dy = R_EARTH * np.deg2rad(dlat)                   # pint.Quantity [m]

    # Wind as pint.Quantity — preserves units through np.gradient.
    # NOTE: .values strips units in pint-xarray; .metpy.unit_array keeps them.
    u_pint = u_250.metpy.unit_array                   # pint.Quantity [m/s]

    # Beta = df/dy on sphere  [s⁻¹ m⁻¹]  (pint tracks units).
    # OMEGA carries 'rad/s'; use .magnitude × units('1/s') to avoid
    # radian-dimensionless mismatch in pint's unit registry.
    lat_rad = np.deg2rad(lat_2d)
    omega_s = OMEGA.magnitude * units('1/s')
    beta = (2.0 * omega_s * np.cos(lat_rad)) / R_EARTH  # [s⁻¹ m⁻¹]

    # ∂u/∂y  [m s⁻¹ / m] → [s⁻¹]  (pint verifies).
    du_dy = np.gradient(u_pint, axis=0) / dy[:, np.newaxis]

    # ∂²u/∂y²  [s⁻¹ / m] → [s⁻¹ m⁻¹]  (pint verifies).
    d2u_dy2 = np.gradient(du_dy, axis=0) / dy[:, np.newaxis]

    # If units are inconsistent, pint raises DimensionalityError here.
    rk_criterion = beta - d2u_dy2                     # [s⁻¹ m⁻¹]
    return rk_criterion


def moisture_flux_divergence_975(u_975, v_975, q_975):
    """
    Moisture flux divergence at 975 hPa via MetPy:
      div_q = ∇·(q·V) = ∂(q·u)/∂x + ∂(q·v)/∂y

    Parameters
    ----------
    u_975, v_975 : xr.DataArray (2D, latitude × longitude)
        Winds at 975 hPa (m/s).
    q_975 : xr.DataArray (2D, latitude × longitude)
        Specific humidity at 975 hPa (kg/kg).

    Returns
    -------
    div_q_gkg : xr.DataArray (2D, pint-backed)
        Moisture flux divergence (×1000 for g/kg-equivalent scale).
        Preserves DataArray structure and pint units.
        Positive: divergence (drying); Negative: convergence (moistening).
    """
    lat_1d = u_975.latitude.values
    lon_1d = u_975.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # q_975, u_975, v_975 are unit-tagged DataArrays; arithmetic preserves units.
    # Moisture flux components: [kg kg⁻¹ · m s⁻¹]
    qu = q_975 * u_975   # DataArray [kg kg⁻¹ m s⁻¹]
    qv = q_975 * v_975

    # MetPy returns a pint-backed DataArray — preserve it.
    div_q = metpy_divergence(qu, qv, dx=dx, dy=dy)  # [kg kg⁻¹ s⁻¹]

    # Scale ×1000 for g/kg-equivalent magnitude (units still tracked by pint).
    return div_q * 1000.0


def ageostrophic_flux_convergence_250(
    u_250, v_250, z_250,
    u_clim, v_clim, z_clim,
):
    """
    Ageostrophic Geopotential Flux Convergence (AFC) at 250 hPa.

    Following Orlanski & Katzfey (1991, JAS, 48, 1972-1990) and
    Orlanski & Sheldon (1993, MWR, 121, 2929-2952):

    The AFC diagnostic quantifies the redistribution of eddy kinetic
    energy through pressure work by the ageostrophic part of the eddy
    wind.  The temporal decomposition uses a 30-year monthly climatology
    as the base state (Vm, Φm), so that:

        V  = Vm + v'          (wind  = climatological mean + eddy)
        Φ  = Φm + φ'          (geopotential = mean + eddy)

    The eddy geostrophic wind is:
        v_g' = (1/f) k × ∇φ'  →  u_g' = -(1/f)(∂φ'/∂y)
                                   v_g' = +(1/f)(∂φ'/∂x)

    Ageostrophic eddy wind:
        v_ag' = v' - v_g'

    AFC (Ageostrophic Flux Convergence):
        AFC = -∇ · (v_ag' · φ')

    Positive AFC → convergence of ageostrophic geopotential flux
    → source of eddy kinetic energy.

    Parameters
    ----------
    u_250, v_250 : xr.DataArray (2D, latitude × longitude)
        Instantaneous zonal / meridional wind at 250 hPa (m/s),
        pint-backed.
    z_250 : xr.DataArray (2D, latitude × longitude)
        Instantaneous geopotential at 250 hPa (m² s⁻²), pint-backed.
    u_clim, v_clim : xr.DataArray (2D, latitude × longitude)
        Climatological zonal / meridional wind at 250 hPa (m/s).
        Already interpolated to the cyclone subdomain.
    z_clim : xr.DataArray (2D, latitude × longitude)
        Climatological geopotential at 250 hPa (m² s⁻²).
        Already interpolated to the cyclone subdomain.

    Returns
    -------
    afc : xr.DataArray (2D, pint-backed)
        Ageostrophic flux convergence (m² s⁻³ ≡ W kg⁻¹).  Preserves
        DataArray structure and pint units for downstream unit-safety.
        Positive: source of eddy KE.  Negative: sink of eddy KE.

    References
    ----------
    - Orlanski, I. and J. Katzfey, 1991: The Life Cycle of a Cyclone
      Wave in the Southern Hemisphere. Part I: Eddy Energy Budget.
      J. Atmos. Sci., 48, 1972–1990.
    - Orlanski, I. and J. Sheldon, 1993: A Case of Downstream
      Baroclinic Development over Western North America. MWR, 121,
      2929–2952.
    - Solman, S. A. and C. G. Menéndez, 1998: Eddy kinetic energy
      budget in a limited area model. Atmósfera, 11, 163–181.
    """
    lat_1d = u_250.latitude.values
    lon_1d = u_250.longitude.values

    # ── Eddy perturbations ────────────────────────────────────────────────
    # Climatological fields may not carry pint units → attach them.
    u_m = xr.DataArray(u_clim.values, coords=u_250.coords,
                       dims=u_250.dims) * units("m/s")
    v_m = xr.DataArray(v_clim.values, coords=v_250.coords,
                       dims=v_250.dims) * units("m/s")
    z_m = xr.DataArray(z_clim.values, coords=z_250.coords,
                       dims=z_250.dims) * units("m**2/s**2")

    u_prime = u_250 - u_m        # [m/s]
    v_prime = v_250 - v_m        # [m/s]
    phi_prime = z_250 - z_m      # [m² s⁻²]  (geopotential perturbation)

    # ── Grid spacing (MetPy convention) ───────────────────────────────────
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)   # (ny, nx-1), (ny-1, nx)

    # ── Coriolis parameter ────────────────────────────────────────────────
    lat_2d = np.broadcast_to(lat_1d[:, np.newaxis],
                             (len(lat_1d), len(lon_1d)))
    f = coriolis_parameter(lat_2d * units.degree)  # pint.Quantity [s⁻¹]
    # Safety: clip |f| away from zero (equatorial singularity)
    f_safe = np.where(np.abs(f) < 1e-10 * units('1/s'),
                      np.sign(f) * 1e-10 * units('1/s'), f)

    # ── Geostrophic eddy wind from φ' ────────────────────────────────────
    # ∂φ'/∂x and ∂φ'/∂y via central differences on the spherical grid.
    # Use _metpy_grid_deltas (already in metres with pint units).
    # Derivatives with MetPy grid spacing arrays (staggered-size) require
    # using the compute_spherical_grid_spacing function for full-size grids.
    dx_full, dy_full, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)

    # Extract plain ndarray from phi_prime for gradient (avoiding pint/xarray
    # broadcasting issues with np.gradient).
    phi_vals = phi_prime.metpy.unit_array       # pint.Quantity [m² s⁻²]

    dphi_dy = np.gradient(phi_vals, axis=0) / (dy_full[:, np.newaxis] * units.meter)
    dphi_dx = np.gradient(phi_vals, axis=1) / (dx_full * units.meter)

    # Geostrophic eddy wind  (SH: f < 0)
    #   u_g' = -(1/f) ∂φ'/∂y
    #   v_g' = +(1/f) ∂φ'/∂x
    ug_prime = -(1.0 / f_safe) * dphi_dy   # [m/s]
    vg_prime = (1.0 / f_safe) * dphi_dx    # [m/s]

    # ── Ageostrophic eddy wind ────────────────────────────────────────────
    # u_prime, v_prime are pint-backed DataArrays; ug_prime, vg_prime are
    # pint.Quantity.  Extract matching pint quantities.
    uag_prime = u_prime.metpy.unit_array - ug_prime   # [m/s]
    vag_prime = v_prime.metpy.unit_array - vg_prime   # [m/s]

    # ── Ageostrophic geopotential flux:  F = v_ag' · φ' ─────────────────
    Fx = uag_prime * phi_vals       # [m³ s⁻³]
    Fy = vag_prime * phi_vals       # [m³ s⁻³]

    # ── AFC = -∇ · F ─────────────────────────────────────────────────────
    # Use central differences on the full-resolution spherical grid.
    dFx_dx = np.gradient(Fx, axis=1) / (dx_full * units.meter)
    dFy_dy = np.gradient(Fy, axis=0) / (dy_full[:, np.newaxis] * units.meter)

    afc_vals = -(dFx_dx + dFy_dy)   # [m² s⁻³]

    # ── Wrap back into DataArray for unit tracking ────────────────────────
    afc = xr.DataArray(
        afc_vals.magnitude,
        coords=u_250.coords,
        dims=u_250.dims,
        attrs={"long_name": "Ageostrophic Flux Convergence at 250 hPa",
               "units": str(afc_vals.units)},
    )
    return afc


# ============================================================================
# SUBDOMAIN EXTRACTION
# ============================================================================

def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """Interpolate dataset to regular centred grid."""
    half = domain_size / 2.0
    n = int(domain_size / RESOLUTION) + 1
    lat_target = np.linspace(center_lat + half, center_lat - half, n)
    lon_target = np.linspace(center_lon - half, center_lon + half, n)

    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1),
    )

    return ds_sub.interp(latitude=lat_target, longitude=lon_target, method="linear")


# ============================================================================
# SINGLE-CASE PROCESSING (module-level for multiprocessing picklability)
# ============================================================================

def _process_single_case(track_id):
    """
    Process one cyclone case: open ERA5, compute all diagnostics.

    Module-level function so that ``ProcessPoolExecutor`` can pickle it.
    Uses module-level constants DATA_DIR, DOMAIN_SIZE, RESOLUTION and
    all diagnostic functions defined above.

    Parameters
    ----------
    track_id : int
        Cyclone track identifier.

    Returns
    -------
    track_id : int
    result : dict or None
        If successful, a dict with keys:
          'egr', 'pv_200', 'pv_850', 'adv_T_850', 'div_q_975',
          'ke_adv_250', 'rk_criterion_250', 'afc_250' (if climatology available),
          'msl' (optional),
          'u_250', 'u_850', 'u_975', 'v_250', 'v_850', 'v_975', 'q_975'
        All values are 2-D ndarrays (ny, nx).
        If the file is missing or an error occurs, returns None.
    error : str or None
        Error message if processing failed.
    """
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    meta_file = DATA_DIR / f"{track_id}_metadata.csv"

    if not nc_file.exists() or not meta_file.exists():
        return track_id, None, "file_missing"

    try:
        ds = xr.open_dataset(nc_file)
        meta = pd.read_csv(meta_file).iloc[0]
        clat = meta["track_center_lat"]
        clon = meta["track_center_lon"]

        ds_sub = extract_subdomain(ds, clat, clon, DOMAIN_SIZE)

        # Mean over time
        tc = "valid_time" if "valid_time" in ds_sub.dims else "time"
        ds_mean = ds_sub.mean(dim=tc)

        pc = "pressure_level" if "pressure_level" in ds_mean.coords else "level"
        levels = ds_mean[pc].values

        # ── Keep DataArrays so lat/lon coords are visible during debugging ──
        u_da = ds_mean["u"]
        v_da = ds_mean["v"]
        T_da = ds_mean["t"]
        z_da = ds_mean["z"]
        q_da = ds_mean["q"]

        def _idx(target_hPa):
            return int(np.argmin(np.abs(levels - target_hPa)))

        def _sel(da, target_hPa):
            return da.isel({pc: _idx(target_hPa)})

        # ── 2-D DataArrays with physical units attached ───────────────────
        u_250 = _sel(u_da, 250) * units("m/s")
        u_500 = _sel(u_da, 500) * units("m/s")
        u_850 = _sel(u_da, 850) * units("m/s")
        u_975 = _sel(u_da, 975) * units("m/s")
        v_250 = _sel(v_da, 250) * units("m/s")
        v_500 = _sel(v_da, 500) * units("m/s")
        v_850 = _sel(v_da, 850) * units("m/s")
        v_975 = _sel(v_da, 975) * units("m/s")
        T_500 = _sel(T_da, 500) * units.kelvin
        T_850 = _sel(T_da, 850) * units.kelvin
        z_500 = _sel(z_da, 500) * units("m**2/s**2")
        z_850 = _sel(z_da, 850) * units("m**2/s**2")
        q_975 = _sel(q_da, 975) * units("kg/kg")

        result = {}

        # ── EGR (500–850 hPa layer, Besson et al. 2021) ──────────
        result["egr"] = eady_growth_rate(
            u_500, v_500, u_850, v_850,
            T_500, T_850, z_500, z_850,
        )

        # ── PV at 200 hPa (needs 175, 200, 225) ──────────────────
        result["pv_200"] = compute_pv_at_level(
            _sel(u_da, 175) * units("m/s"), _sel(u_da, 200) * units("m/s"), _sel(u_da, 225) * units("m/s"),
            _sel(v_da, 175) * units("m/s"), _sel(v_da, 200) * units("m/s"), _sel(v_da, 225) * units("m/s"),
            _sel(T_da, 175) * units.kelvin, _sel(T_da, 200) * units.kelvin, _sel(T_da, 225) * units.kelvin,
            np.array([levels[_idx(175)], levels[_idx(200)], levels[_idx(225)]]) * 100.0,
        )

        # ── PV at 850 hPa (needs 825, 850, 875) ──────────────────
        result["pv_850"] = compute_pv_at_level(
            _sel(u_da, 825) * units("m/s"), _sel(u_da, 850) * units("m/s"), _sel(u_da, 875) * units("m/s"),
            _sel(v_da, 825) * units("m/s"), _sel(v_da, 850) * units("m/s"), _sel(v_da, 875) * units("m/s"),
            _sel(T_da, 825) * units.kelvin, _sel(T_da, 850) * units.kelvin, _sel(T_da, 875) * units.kelvin,
            np.array([levels[_idx(825)], levels[_idx(850)], levels[_idx(875)]]) * 100.0,
        )

        # ── Temperature advection at 850 hPa ─────────────────────
        result["adv_T_850"] = temperature_advection_850(u_850, v_850, T_850)

        # ── SLP ───────────────────────────────────────────────────
        if "msl" in ds_mean.data_vars:
            msl_data = ds_mean["msl"]
            if pc in msl_data.dims:
                msl_data = msl_data.isel({pc: 0})
            result["msl"] = msl_data.values.squeeze()

        # ── Winds / humidity for overlays ─────────────────────────
        result["u_250"] = u_250.values
        result["u_850"] = u_850.values
        result["u_975"] = u_975.values
        result["v_250"] = v_250.values
        result["v_850"] = v_850.values
        result["v_975"] = v_975.values
        result["q_975"] = q_975.values

        # ── Moisture flux divergence at 975 hPa ──────────────────
        result["div_q_975"] = moisture_flux_divergence_975(u_975, v_975, q_975)

        # ── Kinetic energy advection at 250 hPa ──────────────────
        result["ke_adv_250"] = kinetic_energy_advection_250(u_250, v_250)

        # ── Rayleigh-Kuo criterion at 250 hPa ────────────────────
        result["rk_criterion_250"] = rayleigh_kuo_criterion_250(u_250, v_250)

        # ── AFC at 250 hPa (Orlanski & Katzfey 1991) ─────────────
        ds_clim = _load_climatology()
        if ds_clim is not None:
            # Determine calendar month from case metadata
            case_month = pd.Timestamp(meta["start_time"]).month

            # Extract climatology for this month and interpolate
            # to the cyclone subdomain grid
            clim_month = ds_clim.sel(month=case_month)

            # Subdomain coordinates from the case grid
            case_lats = u_250.latitude.values
            case_lons = u_250.longitude.values

            # Interpolate climatology to case subdomain
            clim_sub = clim_month.interp(
                latitude=case_lats,
                longitude=case_lons,
                method="linear",
            )

            z_250 = _sel(z_da, 250) * units("m**2/s**2")

            result["afc_250"] = ageostrophic_flux_convergence_250(
                u_250, v_250, z_250,
                clim_sub["u_clim"], clim_sub["v_clim"], clim_sub["z_clim"],
            )

        ds.close()
        return track_id, result, None

    except Exception as e:
        return track_id, None, f"{type(e).__name__}: {e}"


# ============================================================================
# COMPOSITE FOR ONE EP GROUP
# ============================================================================

def compute_composite(cases, ep_label, n_jobs=1):
    """
    Compute composite fields for one EP group.

    Per-case 2-D arrays are accumulated into a dict keyed by variable name.
    After all cases are processed, each variable is assembled into an
    xr.DataArray with dimensions (track_id, level, y, x) – or (track_id, y, x)
    for single-level/derived fields – so that the composite mean (and any
    further per-member diagnostics) can be computed or inspected easily.

    Parameters
    ----------
    cases : pd.DataFrame
        Must contain a ``track_id`` column.
    ep_label : str
        Label for logging (e.g. "EP1").
    n_jobs : int
        Number of parallel workers.  1 = sequential (default).

    Returns
    -------
    xr.Dataset with composite means over the track_id dimension.
    """
    logging.info(f"\n   Computing composites for {ep_label} ({len(cases)} cases)"
                 f" with {n_jobs} worker(s)...")

    half = DOMAIN_SIZE / 2.0
    n_pts = int(DOMAIN_SIZE / RESOLUTION) + 1
    x = np.linspace(-half, half, n_pts)
    y = np.linspace(half, -half, n_pts)

    track_ids = cases["track_id"].tolist()

    # ── Process all cases (sequential or parallel) ────────────────────────
    if n_jobs <= 1:
        # Sequential — simple loop with tqdm progress bar
        raw_results = []
        for tid in tqdm(track_ids, desc=f"   {ep_label}", leave=True):
            raw_results.append(_process_single_case(tid))
    else:
        # Parallel — ProcessPoolExecutor with as_completed for live progress
        raw_results = []
        with ProcessPoolExecutor(max_workers=n_jobs) as pool:
            futures = {pool.submit(_process_single_case, tid): tid
                       for tid in track_ids}
            pbar = tqdm(total=len(futures), desc=f"   {ep_label}", leave=True)
            for future in as_completed(futures):
                raw_results.append(future.result())
                pbar.update(1)
            pbar.close()

    # ── Collect successful results into accumulators ──────────────────────
    scalar_accum: dict[str, list] = {
        "egr": [], "pv_200": [], "pv_850": [], "adv_T_850": [],
        "div_q_975": [], "ke_adv_250": [], "rk_criterion_250": [],
        "afc_250": [], "msl": [],
    }
    level_accum: dict[str, dict[int, list]] = {
        "u": {250: [], 850: [], 975: []},
        "v": {250: [], 850: [], 975: []},
        "q": {975: []},
    }
    track_ids_ok: list[int] = []
    processed = 0
    failed = 0

    for tid, result, error in raw_results:
        if result is None:
            if error and error != "file_missing":
                logging.warning(f"      Error {tid}: {error}")
            failed += 1
            continue

        # Scalars
        for key in ("egr", "pv_200", "pv_850", "adv_T_850",
                     "div_q_975", "ke_adv_250", "rk_criterion_250",
                     "afc_250"):
            if key in result:
                scalar_accum[key].append(result[key])
        if "msl" in result:
            scalar_accum["msl"].append(result["msl"])

        # Winds / humidity
        for var in ("u", "v"):
            for lv in (250, 850, 975):
                level_accum[var][lv].append(result[f"{var}_{lv}"])
        level_accum["q"][975].append(result["q_975"])

        track_ids_ok.append(tid)
        processed += 1

    if processed == 0:
        raise RuntimeError(f"No valid cases for {ep_label}")

    logging.info(f"      {ep_label}: processed={processed}, failed={failed}")

    # ── Assemble xr.DataArrays with track_id dimension ────────────────────
    coords_yx = {"track_id": track_ids_ok, "y": y, "x": x}

    def _make_da(arrays, name, long_name, units_str):
        """Stack a list of 2-D (y, x) arrays → DataArray (track_id, y, x)."""
        data = np.stack(arrays, axis=0)          # (n_cases, ny, nx)
        return xr.DataArray(
            data,
            dims=["track_id", "y", "x"],
            coords=coords_yx,
            name=name,
            attrs={"long_name": long_name, "units": units_str},
        )

    # Scalar / single-level derived fields
    scalar_specs = {
        "egr":              ("Eady Growth Rate",                     "day-1"),
        "pv_200":           ("Potential Vorticity at 200 hPa",       "K m2 kg-1 s-1"),
        "pv_850":           ("Potential Vorticity at 850 hPa",       "K m2 kg-1 s-1"),
        "adv_T_850":        ("Temperature Advection at 850 hPa",     "K s-1"),
        "div_q_975":        ("Moisture Flux Divergence at 975 hPa",  "g kg-1 s-1"),
        "ke_adv_250":       ("KE Advection at 250 hPa",              "m2 s-3"),
        "rk_criterion_250": ("Rayleigh-Kuo Criterion at 250 hPa",    "s-1 m-1"),
        "afc_250":          ("Ageostrophic Flux Convergence 250 hPa", "m2 s-3"),
    }
    da_scalars: dict[str, xr.DataArray] = {}
    for var, (lname, ustr) in scalar_specs.items():
        if scalar_accum[var]:
            da_scalars[var] = _make_da(scalar_accum[var], var, lname, ustr)

    # Wind / humidity: build DataArray with an extra "level" dim  (track_id, level, y, x)
    wind_specs = {
        "u": ("Zonal Wind",         "m s-1"),
        "v": ("Meridional Wind",    "m s-1"),
        "q": ("Specific Humidity",  "kg kg-1"),
    }
    da_levels: dict[str, xr.DataArray] = {}
    for var, (lname, ustr) in wind_specs.items():
        lev_dict = level_accum[var]
        levs = sorted(lev_dict.keys())
        stacked = np.stack(
            [np.stack(lev_dict[lv], axis=0) for lv in levs],
            axis=1,
        )   # (n_cases, n_levels, ny, nx)
        da_levels[var] = xr.DataArray(
            stacked,
            dims=["track_id", "level", "y", "x"],
            coords={
                "track_id": track_ids_ok,
                "level": levs,
                "y": y,
                "x": x,
            },
            name=var,
            attrs={"long_name": lname, "units": ustr},
        )

    # ── Build output dataset (composite means) ────────────────────────────
    data_vars: dict = {}

    for var, da in da_scalars.items():
        data_vars[var] = (["y", "x"],
                          da.mean(dim="track_id").values,
                          da.attrs)

    # Wind means at each level stored as e.g. u_250, u_850, u_975
    for var, da in da_levels.items():
        for lv in da.level.values:
            key = f"{var}_{lv}"
            data_vars[key] = (
                ["y", "x"],
                da.sel(level=lv).mean(dim="track_id").values,
                {"long_name": f"{da.attrs['long_name']} at {lv} hPa",
                 "units": da.attrs["units"]},
            )

    ds_out = xr.Dataset(data_vars, coords={"x": x, "y": y})

    if scalar_accum["msl"]:
        msl_da = _make_da(scalar_accum["msl"], "msl",
                          "Mean Sea Level Pressure", "Pa")
        ds_out["msl"] = (["y", "x"], msl_da.mean(dim="track_id").values,
                         msl_da.attrs)

    ds_out.attrs["ep_label"] = ep_label
    ds_out.attrs["n_cases"] = processed
    ds_out.attrs["n_failed"] = failed
    ds_out.attrs["domain_size_deg"] = DOMAIN_SIZE
    ds_out.attrs["resolution_deg"] = RESOLUTION

    return ds_out


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Precompute EP structure composites")
    parser.add_argument(
        "--jobs", "-j", type=int, default=1,
        help="Number of parallel workers for composite computation. "
             "Default: 1 (sequential). Recommended on remote server: 4-8.",
    )
    args = parser.parse_args()
    n_jobs = args.jobs if args.jobs >= 1 else 1

    log_file = setup_logging()
    logging.info(f"   Parallel workers: {n_jobs}")

    # Load cases
    ep1_cases = pd.read_csv(RESULTS_DIR / "ep1_cases.csv")
    ep2_cases = pd.read_csv(RESULTS_DIR / "ep2_cases.csv")
    logging.info(f"   EP1: {len(ep1_cases)} cases")
    logging.info(f"   EP2: {len(ep2_cases)} cases")

    # Check data availability
    avail = 0
    for _, row in pd.concat([ep1_cases, ep2_cases]).iterrows():
        if (DATA_DIR / f"{row['track_id']}_era5.nc").exists():
            avail += 1
    logging.info(f"   Available data files: {avail}/{len(ep1_cases)+len(ep2_cases)}")
    if avail == 0:
        logging.error("❌ No ERA5 files found. Run step2 first.")
        return

    # Compute composites
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        ds_ep1 = compute_composite(ep1_cases, "EP1", n_jobs=n_jobs)
        ds_ep2 = compute_composite(ep2_cases, "EP2", n_jobs=n_jobs)

    # Save
    out1 = DATA_DIR / "precomputed_composites_ep1.nc"
    out2 = DATA_DIR / "precomputed_composites_ep2.nc"
    ds_ep1.to_netcdf(out1)
    ds_ep2.to_netcdf(out2)
    logging.info(f"\n   ✓ Saved: {out1.name} ({out1.stat().st_size/1024**2:.1f} MB)")
    logging.info(f"   ✓ Saved: {out2.name} ({out2.stat().st_size/1024**2:.1f} MB)")

    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 3 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"Log: {log_file}")
    logging.info("\nNext: python scripts/ep_structure_analysis/step4_create_figures.py")


if __name__ == "__main__":
    main()
