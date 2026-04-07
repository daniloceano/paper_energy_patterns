"""
Step 3: Precompute Composites for EP1 & EP2

Computes spatial composites (30°×30° domain centred on the cyclone) for
each EP group and saves a single NetCDF file per group with composite
means on a regular 0.25° grid.

USAGE
-----
  # Standard mode: all cyclones in EP1/EP2, mean over intensification phase
  python step3_precompute_composites.py --mode full_intensification

  # Central-time mode: all cyclones, only central timestep of each
  python step3_precompute_composites.py --mode central_time

  # Intense-10 mode: only the 10 most intense cyclones per EP (from CSV)
  python step3_precompute_composites.py --mode intense_10

  # Parallel processing (recommended on server)
  python step3_precompute_composites.py --mode full_intensification --jobs 4

COMPOSITE MODES
---------------
  full_intensification : Mean over ALL storm-centered timesteps during
                         the intensification phase. Default mode.
  central_time         : Use only the CENTRAL timestep (middle of
                         intensification) for each cyclone.
  intense_10           : Same as full_intensification, but uses only the
                         10 most intense cyclones per EP group.
                         Requires: results/ep_structure/ep1_top10_intense.csv
                                   results/ep_structure/ep2_top10_intense.csv

Total-field diagnostics (computed from instantaneous ERA5 fields):
  - EGR   — Eady Growth Rate, 500–850 hPa layer (Besson et al. 2021)
  - PV    — Potential Vorticity at 200 hPa (upper-level dynamics)
  - PV    — Potential Vorticity at 850 hPa (low-level diabatic PV)
  - advT  — Temperature advection at 850 hPa  (−V·∇T)
  - div_q — Moisture flux divergence at 975 hPa  (∇·(qV))
  - SLP   — Mean sea level pressure
  - KE_adv — KE advection at 250 hPa  (−V·∇(½|V|²))
  - RK    — Rayleigh-Kuo criterion at 250 hPa  (β − ∂²u/∂y²)
  - AFC   — Ageostrophic Flux Convergence at 250 hPa  (−∇·(v_ag' φ'))
            requires ERA5 30-year monthly climatology (step2_1)
  - BtCR  — Barotropic Critical Region diagnostics at 250 hPa
              (Δm = σ_m² − ζ_m², φ_dil = ½ arctan(Sh/St))
            computed from climatological (low-frequency) winds; identifies
            regions where deformation dominates rotation (Rivière 2006)

Anomaly diagnostics (eddy perturbation relative to 30-year WMO monthly
climatology 1991–2020, produced by step2_1_download_era5_monthly_means.py;
skipped gracefully if the files are absent):
  - pv_200_anom     — PV anomaly at 200 hPa  (eddy u′,v′,T′ at 175/200/225 hPa)
  - pv_850_anom     — PV anomaly at 850 hPa  (eddy u′,v′,T′ at 825/850/875 hPa)
  - adv_T_850_anom  — Temperature advection anomaly at 850 hPa  (−V′·∇T′)
  - div_q_975_anom  — Moisture flux divergence anomaly at 975 hPa  (∇·(q′V′))
  - ke_adv_250_anom — KE advection anomaly at 250 hPa  (−V′·∇(½|V′|²))
  - msl_anom        — SLP anomaly  (msl − climatological monthly mean)
  Note: anomaly diagnostics for non-linear fields (PV, div_q) capture only
  the pure-eddy (quadratic) term, omitting cross-terms (e.g. −V_m·∇T′ − V′·∇T_m).

Output:
  data/era5_ep_structure/precomputed_composites_ep1_{mode}.nc
  data/era5_ep_structure/precomputed_composites_ep2_{mode}.nc

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
    coriolis_parameter,
    geostrophic_wind,
    ageostrophic_wind,
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

# Tracks file for per-timestep cyclone positions
TRACKS_FILE = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"

DOMAIN_SIZE = 30.0    # degrees (30° × 30°)
RESOLUTION = 0.25     # degrees

# Composite mode: how to aggregate timesteps within intensification phase
# -------------------------------------------------------------------------
# "full_intensification" : mean over all storm-centered timesteps (all cases)
# "central_time"         : use only the central timestep (all cases)
# "intense_10"           : same as full_intensification, but only top-10 intense cyclones
COMPOSITE_MODE = "full_intensification"  # set via --mode argument in main()

# Module-level cache for tracks DataFrame (loaded once per process)
_TRACKS_CACHE = None

# EGR quality control
MIN_LAT = 5.0
MAX_EGR_DAY = 5.0
MIN_N_SQUARED = 1e-6

# Climatology files produced by step2_1  (one per download group)
# ------------------------------------------------------------------
# 250hPa  : u, v, z at 250 hPa   → AFC  +  KE_adv anomaly
# pv200   : u, v, t at 175/200/225 hPa  → PV@200 anomaly
# pv850   : u, v, t at 825/850/875 hPa  → PV@850 + T_adv@850 anomaly
# mfd975  : u, v, q at 975 hPa          → moisture flux div anomaly
CLIMATOLOGY_FILE        = DATA_DIR / "era5_climatology_250hPa.nc"
CLIMATOLOGY_PV200_FILE  = DATA_DIR / "era5_climatology_pv200.nc"
CLIMATOLOGY_PV850_FILE  = DATA_DIR / "era5_climatology_pv850.nc"
CLIMATOLOGY_MFD975_FILE = DATA_DIR / "era5_climatology_mfd975.nc"
CLIMATOLOGY_SLP_FILE    = DATA_DIR / "era5_climatology_slp.nc"

# Module-level cache: path → xr.Dataset (or None if file absent).
# Populated lazily on first access; shared across all cases in the same process.
_CLIM_CACHE: dict = {}


def _load_clim(path, label, skip_msg):
    """
    Lazy-load a climatology NetCDF file, caching the open Dataset by path.

    Parameters
    ----------
    path : pathlib.Path
        Absolute path to the climatology ``.nc`` file.
    label : str
        Short human-readable name for log/warning messages (e.g. ``"PV850"``)
    skip_msg : str
        Sentence appended to the warning when the file is absent, describing
        which diagnostics will be skipped (e.g. ``"PV@850 anomaly will be
        skipped."``).  May include instructions such as "Run step2_1 first."

    Returns
    -------
    xr.Dataset or None
        The open Dataset, or ``None`` if the file does not exist.
    """
    if path not in _CLIM_CACHE:
        if not path.exists():
            logging.warning(
                f"   {label} climatology not found: {path.name}. {skip_msg}"
            )
            _CLIM_CACHE[path] = None
        else:
            _CLIM_CACHE[path] = xr.open_dataset(path)
            logging.info(f"   Loaded {label} climatology: {path.name}")
    return _CLIM_CACHE[path]


def _load_tracks():
    """
    Lazy-load the tracks DataFrame (cached for the process lifetime).
    
    Returns
    -------
    pd.DataFrame
        Track data with columns: track_id, date, lon vor, lat vor, ...
    """
    global _TRACKS_CACHE
    if _TRACKS_CACHE is None:
        _TRACKS_CACHE = pd.read_csv(TRACKS_FILE, parse_dates=["date"])
    return _TRACKS_CACHE


def get_cyclone_positions_for_case(track_id, era5_times):
    """
    Get cyclone center positions for each timestep in the ERA5 file.
    
    Parameters
    ----------
    track_id : int
        Cyclone track identifier.
    era5_times : array-like of datetime64
        Timestamps from the ERA5 NetCDF file.
    
    Returns
    -------
    dict
        Mapping: time_index → (center_lat, center_lon) or None if not found.
        Also includes 'central_idx' key for the central timestep index.
    """
    tracks = _load_tracks()
    track_data = tracks[tracks["track_id"] == int(track_id)].copy()
    
    if len(track_data) == 0:
        return {}
    
    positions = {}
    for t_idx, era5_time in enumerate(era5_times):
        era5_ts = pd.Timestamp(era5_time)
        
        # Find nearest track time (within 3 hours tolerance)
        time_diffs = (track_data["date"] - era5_ts).abs()
        min_diff = time_diffs.min()
        
        if min_diff <= pd.Timedelta(hours=3):
            nearest_idx = time_diffs.idxmin()
            nearest = track_data.loc[nearest_idx]
            positions[t_idx] = (float(nearest["lat vor"]), float(nearest["lon vor"]))
        else:
            positions[t_idx] = None
    
    # Compute central timestep index
    n_times = len(era5_times)
    if n_times > 0:
        # For odd N: exact middle; for even N: N//2 (just after middle)
        positions["central_idx"] = n_times // 2
    else:
        positions["central_idx"] = None
    
    return positions


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

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has been personally validated by the developer for unit
    consistency and formula correctness.  All intermediate variables are
    kept as pint-backed DataArrays so that unit tracking is automatic and
    physically verifiable.  DO NOT replace DataArray arithmetic with
    bare-ndarray arithmetic, and DO NOT strip units prematurely — see the
    module-level docstring for rationale.
    """
    p_hpa = (np.asarray(p_3lev_pa) / 100.0)

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

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has been personally validated by the developer for unit
    consistency and formula correctness.  All intermediate variables are
    kept as pint-backed DataArrays so that unit tracking is automatic and
    physically verifiable.  DO NOT replace DataArray arithmetic with
    bare-ndarray arithmetic, and DO NOT strip units prematurely — see the
    module-level docstring for rationale.
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

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has been personally validated by the developer for unit
    consistency and formula correctness.  All intermediate variables are
    kept as pint-backed DataArrays so that unit tracking is automatic and
    physically verifiable.  DO NOT replace DataArray arithmetic with
    bare-ndarray arithmetic, and DO NOT strip units prematurely — see the
    module-level docstring for rationale.
    """
    lat_1d = u_250.latitude.values
    lon_1d = u_250.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # u_250 and v_250 are unit-tagged DataArrays (m/s); arithmetic preserves units.
    KE = 0.5 * (u_250 ** 2 + v_250 ** 2)         # DataArray [m² s⁻²]

    # Convert to J kg⁻¹ (same units, different name) for clarity in interpretation.
    KE_Jkg = KE.metpy.convert_units('J/kg')      # [J kg⁻¹]

    # MetPy returns a pint-backed DataArray — preserve it.
    KE_adv = metpy_advection(KE_Jkg, u=u_250, v=v_250, dx=dx, dy=dy) # [m² s⁻³]

    # Convert to W kg⁻¹ (same units, different name) for clarity in interpretation.
    KE_adv_Wkg = KE_adv.metpy.convert_units('W/kg')  # [W kg⁻¹]

    # MetPy returns a pint-backed DataArray — preserve it.
    return KE_adv_Wkg  # [W kg⁻¹]


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

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has been personally validated by the developer for unit
    consistency and formula correctness.  All intermediate variables are
    kept as pint-backed DataArrays so that unit tracking is automatic and
    physically verifiable.  DO NOT replace DataArray arithmetic with
    bare-ndarray arithmetic, and DO NOT strip units prematurely — see the
    module-level docstring for rationale.
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

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has been personally validated by the developer for unit
    consistency and formula correctness.  All intermediate variables are
    kept as pint-backed DataArrays so that unit tracking is automatic and
    physically verifiable.  DO NOT replace DataArray arithmetic with
    bare-ndarray arithmetic, and DO NOT strip units prematurely — see the
    module-level docstring for rationale.
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

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    Geostrophic and ageostrophic eddy winds are computed via MetPy
    (``geostrophic_wind`` / ``ageostrophic_wind``, MetPy ≥ 1.0), which
    handles spherical-geometry derivatives and the Coriolis parameter
    automatically from the DataArray latitude coordinate.  The flux-
    divergence step (∇·F) still uses ``np.gradient`` on the full-
    resolution spherical grid.  This function has been personally
    validated by the developer for unit consistency and formula
    correctness.  DO NOT replace pint-backed DataArray arithmetic with
    bare-ndarray arithmetic — see the module-level docstring for
    rationale.
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

    # ── Grid spacing for AFC divergence ──────────────────────────────────
    dx_full, dy_full, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)

    # ── Geostrophic and ageostrophic eddy winds (MetPy) ──────────────────
    # MetPy derives the Coriolis parameter from the latitude coordinate of
    # phi_prime and computes spatial derivatives using spherical geometry.
    # geostrophic_wind(phi_prime) → (ug', vg')
    # ageostrophic_wind(phi_prime, u', v') → (u_ag', v_ag') = (u' - ug', v' - vg')
    ug_prime, vg_prime = geostrophic_wind(phi_prime)
    uag_prime, vag_prime = ageostrophic_wind(phi_prime, u_prime, v_prime)

    # Extract pint quantities for the divergence computation below.
    phi_vals  = phi_prime.metpy.unit_array   # [m² s⁻²]
    uag_vals  = uag_prime.metpy.unit_array   # [m/s]
    vag_vals  = vag_prime.metpy.unit_array   # [m/s]

    # ── Ageostrophic geopotential flux:  F = v_ag' · φ' ─────────────────
    Fx = uag_vals * phi_vals       # [m³ s⁻³]
    Fy = vag_vals * phi_vals       # [m³ s⁻³]

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


def barotropic_critical_region_250(u_clim, v_clim):
    """
    Barotropic Critical Region (BtCR) diagnostics at 250 hPa.

    Following Rivière (2006, JAS, 63, 1764–1775), the BtCR is the zone
    where the **low-frequency deformation field** of the jet dominates over
    rotation.  A distúrbio traversing such a region is forced into an
    alignment that enables efficient baroclinic energy extraction.

    The low-frequency (background) flow is represented here by the 30-year
    monthly climatology (1991–2020, WMO standard period), used as a
    surrogate for the 8-day running mean that Rivière (2006) employed. This
    choice is dictated by data availability: computing a per-case 8-day
    running mean for hundreds of cyclones from ERA5 is impractical; the
    climatology captures the same large-scale, slowly-varying deformation
    structure.

    **Spherical-geometry formulation (Rivière 2006; btcr technical guide):**

    Relative vorticity of the background flow:
        ζ_m = ∂v_m/∂x − ∂u_m/∂y + u_m tan(φ)/a

    Stretching (St) and shearing (Sh) deformation (with curvature corrections):
        St = ∂u_m/∂x − ∂v_m/∂y − v_m tan(φ)/a
        Sh = ∂v_m/∂x + ∂u_m/∂y − u_m tan(φ)/a

    Total deformation magnitude:
        σ_m = √(St² + Sh²)

    Effective deformation (master BtCR indicator):
        Δm = σ_m² − ζ_m²

        Δm < 0  →  Rotation dominates → distúrbio stays circular; no
                   preferred orientation; barotropic exchanges negligible.
        Δm > 0  →  Deformation dominates → fixed orientation points
                   (stable + unstable) appear; the jet can flatten or tilt
                   the system into a productive or destructive configuration.

    Dilatation axis angle (defined only where Δm > 0):
        φ_dil = ½ arctan2(Sh, St)   [radians]

    The dilatation axis is the direction toward which the background flow
    stretches fluid parcels.  A characteristic **sudden reorientation** of
    φ_dil across the composited BtCR (from SW–NE upstream to NW–SE
    downstream of the jet exit) is the structural signature confirming a
    BtCR.

    Parameters
    ----------
    u_clim, v_clim : xr.DataArray (2D, latitude × longitude)
        Climatological (low-frequency) zonal / meridional wind at 250 hPa
        (m/s). Plain DataArrays without pint units (as returned by
        climatology interpolation in ``_process_single_case``).

    Returns
    -------
    delta_m : ndarray (2D)
        Effective deformation Δm = σ_m² − ζ_m² (s⁻²).
        Positive values mark candidate BtCR regions.
    dil_angle : ndarray (2D)
        Dilatation axis angle φ_dil (radians) where Δm > 0; NaN elsewhere.

    References
    ----------
    - Rivière, G., 2006: Role of the Low-Frequency Deformation Field on the
      Explosive Growth of Extratropical Cyclones at the Jet Exit. Part I:
      Barotropic Critical Region. J. Atmos. Sci., 63, 1764–1775.
      https://doi.org/10.1175/JAS3728.1
    - BtCR Technical Guide (Souza, D., 2026): step-by-step formulation for
      composite identification via climatological base state.

    ⚠ WARNING FOR DEVELOPERS / AI AGENTS:
    This function has not been personally validated by the developer for unit
    consistency and formula correctness.  All spatial derivatives use the
    full-resolution spherical grid spacings from
    ``compute_spherical_grid_spacing``.  DO NOT replace with Cartesian
    (constant dx/dy) derivatives — the curvature-correction terms rely on
    the latitude-dependent grid spacings.  NaN propagation is intentional
    (equatorial singularity in tan φ is handled by clipping).
    """
    lat_1d = u_clim.latitude.values
    lon_1d = u_clim.longitude.values

    # Plain numpy arrays (no pint units needed; all quantities are in SI)
    u_m = u_clim.values   # (ny, nx)  [m s⁻¹]
    v_m = v_clim.values   # (ny, nx)  [m s⁻¹]

    # ── Spherical-geometry grid spacings ─────────────────────────────────
    dx_2d, dy_1d, lat_2d, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)
    # dx_2d : (ny, nx)  [m]    latitude-dependent zonal spacing
    # dy_1d : (ny,)     [m]    meridional spacing (nearly constant)

    # ── Spatial derivatives (spherical geometry) ─────────────────────────
    # ∂/∂x ≈ Δ / dx_2d  (zonal,       axis=1)
    # ∂/∂y ≈ Δ / dy              (meridional,  axis=0)
    du_dx = np.gradient(u_m, axis=1) / dx_2d
    du_dy = np.gradient(u_m, axis=0) / dy_1d[:, np.newaxis]
    dv_dx = np.gradient(v_m, axis=1) / dx_2d
    dv_dy = np.gradient(v_m, axis=0) / dy_1d[:, np.newaxis]

    # ── Curvature corrections ─────────────────────────────────────────────
    # tan(φ) diverges at ±90°; clip at |φ| = 85° to avoid singularity
    lat_clipped = np.clip(lat_2d, -85.0, 85.0)
    tan_phi = np.tan(np.deg2rad(lat_clipped))
    a = R_EARTH.magnitude   # scalar [m]

    # ── Relative vorticity of background flow ────────────────────────────
    # ζ_m = ∂v_m/∂x − ∂u_m/∂y + u_m·tan(φ)/a
    zeta_m = dv_dx - du_dy + u_m * tan_phi / a              # [s⁻¹]

    # ── Deformation components ───────────────────────────────────────────
    # Stretching: St = ∂u_m/∂x − ∂v_m/∂y − v_m·tan(φ)/a
    St = du_dx - dv_dy - v_m * tan_phi / a                  # [s⁻¹]

    # Shearing:   Sh = ∂v_m/∂x + ∂u_m/∂y − u_m·tan(φ)/a
    Sh = dv_dx + du_dy - u_m * tan_phi / a                  # [s⁻¹]

    # Total deformation magnitude: σ_m = √(St² + Sh²)
    sigma_m = np.sqrt(St ** 2 + Sh ** 2)                    # [s⁻¹]

    # ── Effective deformation: Δm = σ_m² − ζ_m² ─────────────────────────
    delta_m = sigma_m ** 2 - zeta_m ** 2                    # [s⁻²]

    # ── Dilatation axis angle (only where Δm > 0) ────────────────────────
    # φ_dil = ½ arctan2(Sh, St)   — full 4-quadrant inverse tangent
    dil_angle_full = 0.5 * np.arctan2(Sh, St)               # [rad]
    dil_angle = np.where(delta_m > 0, dil_angle_full, np.nan)

    return delta_m, dil_angle


# ============================================================================
# SUBDOMAIN EXTRACTION
# ============================================================================

def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """
    Extract and interpolate a subdomain centered on the given coordinates.
    
    The output grid is a RELATIVE (storm-centered) grid where the center
    of the cyclone is at (0, 0) in relative coordinates.
    
    Parameters
    ----------
    ds : xr.Dataset
        Input dataset with latitude/longitude coordinates.
    center_lat : float
        Latitude of the cyclone center (degrees).
    center_lon : float
        Longitude of the cyclone center (degrees).
    domain_size : float
        Size of the domain in degrees (e.g., 30.0 for 30° × 30°).
    
    Returns
    -------
    xr.Dataset
        Interpolated subdomain with latitude/longitude in ABSOLUTE coordinates.
        The center of the grid corresponds to (center_lat, center_lon).
    """
    half = domain_size / 2.0
    n = int(domain_size / RESOLUTION) + 1
    lat_target = np.linspace(center_lat + half, center_lat - half, n)
    lon_target = np.linspace(center_lon - half, center_lon + half, n)

    # Select a slightly larger region to ensure interpolation works
    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1),
    )

    return ds_sub.interp(latitude=lat_target, longitude=lon_target, method="linear")


def check_subdomain_available(ds, center_lat, center_lon, domain_size):
    """
    Check if the requested subdomain is fully within the downloaded data extent.
    
    Returns
    -------
    bool
        True if subdomain can be extracted, False otherwise.
    str or None
        Error message if subdomain cannot be extracted.
    """
    half = domain_size / 2.0
    
    ds_lat_min = float(ds.latitude.min())
    ds_lat_max = float(ds.latitude.max())
    ds_lon_min = float(ds.longitude.min())
    ds_lon_max = float(ds.longitude.max())
    
    req_lat_min = center_lat - half
    req_lat_max = center_lat + half
    req_lon_min = center_lon - half
    req_lon_max = center_lon + half
    
    if req_lat_min < ds_lat_min - 0.5 or req_lat_max > ds_lat_max + 0.5:
        return False, f"lat out of bounds: need [{req_lat_min:.1f}, {req_lat_max:.1f}], have [{ds_lat_min:.1f}, {ds_lat_max:.1f}]"
    if req_lon_min < ds_lon_min - 0.5 or req_lon_max > ds_lon_max + 0.5:
        return False, f"lon out of bounds: need [{req_lon_min:.1f}, {req_lon_max:.1f}], have [{ds_lon_min:.1f}, {ds_lon_max:.1f}]"
    
    return True, None


# ============================================================================
# SINGLE-TIMESTEP DIAGNOSTIC COMPUTATION
# ============================================================================

def _compute_diagnostics_for_timestep(ds_timestep, case_month):
    """
    Compute all diagnostics for a single storm-centered timestep.
    
    Parameters
    ----------
    ds_timestep : xr.Dataset
        Storm-centered dataset for one timestep (no time dimension).
    case_month : int
        Calendar month (1-12) for climatology lookup.
    
    Returns
    -------
    dict
        Dictionary of diagnostic fields (2-D ndarrays).
    """
    pc = "pressure_level" if "pressure_level" in ds_timestep.coords else "level"
    levels = ds_timestep[pc].values

    u_da = ds_timestep["u"]
    v_da = ds_timestep["v"]
    T_da = ds_timestep["t"]
    z_da = ds_timestep["z"]
    q_da = ds_timestep["q"]

    def _idx(target_hPa):
        return int(np.argmin(np.abs(levels - target_hPa)))

    def _sel(da, target_hPa):
        return da.isel({pc: _idx(target_hPa)})

    # 2-D DataArrays with physical units attached
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

    # EGR
    result["egr"] = eady_growth_rate(
        u_500, v_500, u_850, v_850,
        T_500, T_850, z_500, z_850,
    )

    # PV at 200 hPa
    result["pv_200"] = compute_pv_at_level(
        _sel(u_da, 175) * units("m/s"), _sel(u_da, 200) * units("m/s"), _sel(u_da, 225) * units("m/s"),
        _sel(v_da, 175) * units("m/s"), _sel(v_da, 200) * units("m/s"), _sel(v_da, 225) * units("m/s"),
        _sel(T_da, 175) * units.kelvin, _sel(T_da, 200) * units.kelvin, _sel(T_da, 225) * units.kelvin,
        np.array([levels[_idx(175)], levels[_idx(200)], levels[_idx(225)]]) * 100.0,
    )

    # PV at 850 hPa
    result["pv_850"] = compute_pv_at_level(
        _sel(u_da, 825) * units("m/s"), _sel(u_da, 850) * units("m/s"), _sel(u_da, 875) * units("m/s"),
        _sel(v_da, 825) * units("m/s"), _sel(v_da, 850) * units("m/s"), _sel(v_da, 875) * units("m/s"),
        _sel(T_da, 825) * units.kelvin, _sel(T_da, 850) * units.kelvin, _sel(T_da, 875) * units.kelvin,
        np.array([levels[_idx(825)], levels[_idx(850)], levels[_idx(875)]]) * 100.0,
    )

    # Temperature advection at 850 hPa
    result["adv_T_850"] = temperature_advection_850(u_850, v_850, T_850)

    # SLP
    if "msl" in ds_timestep.data_vars:
        msl_data = ds_timestep["msl"]
        if pc in msl_data.dims:
            msl_data = msl_data.isel({pc: 0})
        result["msl"] = msl_data.values.squeeze()

    # Winds / humidity for overlays
    result["u_250"] = u_250.values
    result["u_850"] = u_850.values
    result["u_975"] = u_975.values
    result["v_250"] = v_250.values
    result["v_850"] = v_850.values
    result["v_975"] = v_975.values
    result["q_975"] = q_975.values

    # Moisture flux divergence at 975 hPa
    result["div_q_975"] = moisture_flux_divergence_975(u_975, v_975, q_975)

    # Kinetic energy advection at 250 hPa
    result["ke_adv_250"] = kinetic_energy_advection_250(u_250, v_250)

    # Rayleigh-Kuo criterion at 250 hPa
    result["rk_criterion_250"] = rayleigh_kuo_criterion_250(u_250, v_250)

    # AFC and anomaly fields require climatology
    case_lats = u_250.latitude.values
    case_lons = u_250.longitude.values

    def _interp_clim(ds_c):
        return ds_c.sel(month=case_month).interp(
            latitude=case_lats, longitude=case_lons, method="linear"
        )

    def _clim_prime(clim_2d_raw, ref_da, unit_str):
        clim_da = (
            xr.DataArray(clim_2d_raw.values, coords=ref_da.coords, dims=ref_da.dims)
            * units(unit_str)
        )
        return ref_da - clim_da

    def _prime(clim_ds, lev, da_field, clim_var, unit_str):
        raw = clim_ds[clim_var].sel(pressure_level=float(lev))
        return _clim_prime(raw, da_field, unit_str)

    # AFC at 250 hPa
    ds_clim = _load_clim(
        CLIMATOLOGY_FILE, "250 hPa (AFC/KE adv)",
        "Run step2_1 first. AFC and KE_adv anomaly will be skipped."
    )
    if ds_clim is not None:
        clim_sub = _interp_clim(ds_clim)
        z_250 = _sel(z_da, 250) * units("m**2/s**2")
        result["afc_250"] = ageostrophic_flux_convergence_250(
            u_250, v_250, z_250,
            clim_sub["u_clim"], clim_sub["v_clim"], clim_sub["z_clim"],
        )
        btcr_dm, btcr_da = barotropic_critical_region_250(
            clim_sub["u_clim"], clim_sub["v_clim"]
        )
        result["btcr_delta_m"] = btcr_dm
        result["btcr_dil_angle"] = btcr_da

        # KE advection anomaly
        u_250_p = _clim_prime(clim_sub["u_clim"], u_250, "m/s")
        v_250_p = _clim_prime(clim_sub["v_clim"], v_250, "m/s")
        result["ke_adv_250_anom"] = kinetic_energy_advection_250(u_250_p, v_250_p)
        result["u_250_prime"] = u_250_p.metpy.unit_array.magnitude
        result["v_250_prime"] = v_250_p.metpy.unit_array.magnitude

    # PV anomalies: TRUE ANOMALY = PV_total - PV_clim
    # Note: This is DIFFERENT from PV(u', v', T') which is "eddy PV".
    # PV is nonlinear, so PV(u+u', v+v', T+T') ≠ PV(u) + PV(u', v', T')
    # For cyclones in SH, we expect NEGATIVE anomaly (more cyclonic than clim).
    
    # Helper to get climatological field with proper coordinates
    def _get_clim_field(clim_ds, lev, var, unit_str, ref_da):
        raw = clim_ds[var].sel(pressure_level=float(lev))
        return xr.DataArray(raw.values, coords=ref_da.coords, dims=ref_da.dims) * units(unit_str)
    
    ds_pv200 = _load_clim(
        CLIMATOLOGY_PV200_FILE, "PV200",
        "Run step2_1 first. PV@200 anomaly will be skipped."
    )
    if ds_pv200 is not None:
        c200 = _interp_clim(ds_pv200)
        
        u175_c = _get_clim_field(c200, 175, "u_clim", "m/s", _sel(u_da, 175))
        u200_c = _get_clim_field(c200, 200, "u_clim", "m/s", _sel(u_da, 200))
        u225_c = _get_clim_field(c200, 225, "u_clim", "m/s", _sel(u_da, 225))
        v175_c = _get_clim_field(c200, 175, "v_clim", "m/s", _sel(v_da, 175))
        v200_c = _get_clim_field(c200, 200, "v_clim", "m/s", _sel(v_da, 200))
        v225_c = _get_clim_field(c200, 225, "v_clim", "m/s", _sel(v_da, 225))
        T175_c = _get_clim_field(c200, 175, "t_clim", "K", _sel(T_da, 175))
        T200_c = _get_clim_field(c200, 200, "t_clim", "K", _sel(T_da, 200))
        T225_c = _get_clim_field(c200, 225, "t_clim", "K", _sel(T_da, 225))
        
        # Compute PV from climatological fields
        pv_200_clim = compute_pv_at_level(
            u175_c, u200_c, u225_c, v175_c, v200_c, v225_c, T175_c, T200_c, T225_c,
            np.array([levels[_idx(175)], levels[_idx(200)], levels[_idx(225)]]) * 100.0,
        )
        # True anomaly = PV_total - PV_clim
        result["pv_200_anom"] = result["pv_200"] - pv_200_clim

    ds_pv850 = _load_clim(
        CLIMATOLOGY_PV850_FILE, "PV850",
        "Run step2_1 first. PV@850 and T_adv@850 anomaly will be skipped."
    )
    if ds_pv850 is not None:
        c850 = _interp_clim(ds_pv850)
        # Eddy fields for T advection anomaly (this uses eddy approach, which is appropriate)
        u825_p = _prime(c850, 825, _sel(u_da, 825) * units("m/s"), "u_clim", "m/s")
        u850_p = _prime(c850, 850, _sel(u_da, 850) * units("m/s"), "u_clim", "m/s")
        u875_p = _prime(c850, 875, _sel(u_da, 875) * units("m/s"), "u_clim", "m/s")
        v825_p = _prime(c850, 825, _sel(v_da, 825) * units("m/s"), "v_clim", "m/s")
        v850_p = _prime(c850, 850, _sel(v_da, 850) * units("m/s"), "v_clim", "m/s")
        v875_p = _prime(c850, 875, _sel(v_da, 875) * units("m/s"), "v_clim", "m/s")
        T825_p = _prime(c850, 825, _sel(T_da, 825) * units.kelvin, "t_clim", "K")
        T850_p = _prime(c850, 850, _sel(T_da, 850) * units.kelvin, "t_clim", "K")
        T875_p = _prime(c850, 875, _sel(T_da, 875) * units.kelvin, "t_clim", "K")
        
        # PV 850 TRUE ANOMALY = PV_total - PV_clim
        u825_c = _get_clim_field(c850, 825, "u_clim", "m/s", _sel(u_da, 825))
        u850_c = _get_clim_field(c850, 850, "u_clim", "m/s", _sel(u_da, 850))
        u875_c = _get_clim_field(c850, 875, "u_clim", "m/s", _sel(u_da, 875))
        v825_c = _get_clim_field(c850, 825, "v_clim", "m/s", _sel(v_da, 825))
        v850_c = _get_clim_field(c850, 850, "v_clim", "m/s", _sel(v_da, 850))
        v875_c = _get_clim_field(c850, 875, "v_clim", "m/s", _sel(v_da, 875))
        T825_c = _get_clim_field(c850, 825, "t_clim", "K", _sel(T_da, 825))
        T850_c = _get_clim_field(c850, 850, "t_clim", "K", _sel(T_da, 850))
        T875_c = _get_clim_field(c850, 875, "t_clim", "K", _sel(T_da, 875))
        
        pv_850_clim = compute_pv_at_level(
            u825_c, u850_c, u875_c, v825_c, v850_c, v875_c, T825_c, T850_c, T875_c,
            np.array([levels[_idx(825)], levels[_idx(850)], levels[_idx(875)]]) * 100.0,
        )
        # True anomaly = PV_total - PV_clim
        result["pv_850_anom"] = result["pv_850"] - pv_850_clim
        
        # T advection anomaly uses eddy approach (appropriate for advection)
        result["adv_T_850_anom"] = temperature_advection_850(u850_p, v850_p, T850_p)
        result["u_850_prime"] = u850_p.metpy.unit_array.magnitude
        result["v_850_prime"] = v850_p.metpy.unit_array.magnitude

    ds_mfd975 = _load_clim(
        CLIMATOLOGY_MFD975_FILE, "MFD975",
        "Run step2_1 first. div_q@975 anomaly will be skipped."
    )
    if ds_mfd975 is not None:
        c975 = _interp_clim(ds_mfd975)
        u_975_p = _prime(c975, 975, u_975, "u_clim", "m/s")
        v_975_p = _prime(c975, 975, v_975, "v_clim", "m/s")
        q_975_p = _prime(c975, 975, q_975, "q_clim", "kg/kg")
        result["div_q_975_anom"] = moisture_flux_divergence_975(u_975_p, v_975_p, q_975_p)
        result["u_975_prime"] = u_975_p.metpy.unit_array.magnitude
        result["v_975_prime"] = v_975_p.metpy.unit_array.magnitude

    ds_clim_slp = _load_clim(
        CLIMATOLOGY_SLP_FILE, "SLP",
        "Run step2_1 with --groups slp to download. SLP anomaly will be skipped."
    )
    if "msl" in result and ds_clim_slp is not None:
        c_slp = _interp_clim(ds_clim_slp)
        result["msl_anom"] = result["msl"] - c_slp["msl_clim"].values

    return result


# ============================================================================
# SINGLE-CASE PROCESSING WITH STORM-CENTERED APPROACH
# ============================================================================

def _process_single_case(track_id):
    """
    Process one cyclone case with STORM-CENTERED approach per timestep.
    
    METHODOLOGY (CORRECTED):
    -------------------------
    For each timestep in the ERA5 file:
      1. Get the cyclone center position from the track data
      2. Extract a storm-centered subdomain around that position
      3. Compute diagnostics on the storm-centered grid
    
    Depending on COMPOSITE_MODE:
      - "full_intensification": Return list of ALL storm-centered timesteps
      - "central_time": Return only the CENTRAL timestep (storm-centered)
    
    Parameters
    ----------
    track_id : int
        Cyclone track identifier.
    
    Returns
    -------
    track_id : int
    results : list of dict or None
        List of diagnostic dicts (one per timestep used).
        For central_time mode, this is a single-element list.
        Returns None if no valid timesteps could be processed.
    error : str or None
        Error message if processing failed.
    metadata : dict
        Processing metadata (n_timesteps_total, n_timesteps_used, n_skipped, etc.)
    """
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    meta_file = DATA_DIR / f"{track_id}_metadata.csv"

    if not nc_file.exists() or not meta_file.exists():
        return track_id, None, "file_missing", {}

    try:
        ds = xr.open_dataset(nc_file)
        meta = pd.read_csv(meta_file).iloc[0]
        
        # Get time coordinate
        tc = "valid_time" if "valid_time" in ds.dims else "time"
        era5_times = ds[tc].values
        n_times = len(era5_times)
        
        if n_times == 0:
            ds.close()
            return track_id, None, "no_timesteps", {}
        
        # Get cyclone positions for all timesteps
        positions = get_cyclone_positions_for_case(track_id, era5_times)
        central_idx = positions.get("central_idx", n_times // 2)
        
        # Determine which timesteps to process based on mode
        if COMPOSITE_MODE == "central_time":
            timesteps_to_process = [central_idx]
        else:  # full_intensification
            timesteps_to_process = list(range(n_times))
        
        # Get case month for climatology
        case_month = pd.Timestamp(meta["start_time"]).month
        
        # Process each timestep
        results = []
        n_skipped_no_pos = 0
        n_skipped_out_of_bounds = 0
        
        for t_idx in timesteps_to_process:
            pos = positions.get(t_idx)
            
            if pos is None:
                n_skipped_no_pos += 1
                continue
            
            center_lat, center_lon = pos
            
            # Check if subdomain is within downloaded data
            ok, err_msg = check_subdomain_available(ds, center_lat, center_lon, DOMAIN_SIZE)
            if not ok:
                n_skipped_out_of_bounds += 1
                continue
            
            # Extract storm-centered subdomain for this timestep
            ds_t = ds.isel({tc: t_idx})
            ds_centered = extract_subdomain(ds_t, center_lat, center_lon, DOMAIN_SIZE)
            
            # Compute diagnostics
            diag = _compute_diagnostics_for_timestep(ds_centered, case_month)
            results.append(diag)
        
        ds.close()
        
        proc_metadata = {
            "n_timesteps_total": n_times,
            "n_timesteps_requested": len(timesteps_to_process),
            "n_timesteps_used": len(results),
            "n_skipped_no_position": n_skipped_no_pos,
            "n_skipped_out_of_bounds": n_skipped_out_of_bounds,
        }
        
        if len(results) == 0:
            return track_id, None, "no_valid_timesteps", proc_metadata
        
        return track_id, results, None, proc_metadata

    except Exception as e:
        return track_id, None, f"{type(e).__name__}: {e}", {}


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

    # ── Collect successful results via INCREMENTAL AVERAGING ────────────────
    # NEW: Each case returns a LIST of per-timestep results (storm-centered).
    # The composite is built from ALL storm-centered timesteps across all cases.
    # We use online/incremental mean to avoid memory issues with large N.
    #
    # IMPORTANT: Use per-cell counting to handle NaN values properly.
    # Each timestep may have NaN at different grid locations (e.g., edge cells
    # outside climatology domain). Using simple sum += arr would propagate NaN
    # to ALL cells. Instead, we track valid counts per cell.
    
    # Initialize accumulators as None (will be set to first valid field shape)
    sum_accum: dict[str, np.ndarray | None] = {
        "egr": None, "pv_200": None, "pv_850": None, "adv_T_850": None,
        "div_q_975": None, "ke_adv_250": None, "rk_criterion_250": None,
        "afc_250": None, "msl": None,
        # Anomaly fields
        "ke_adv_250_anom": None, "adv_T_850_anom": None, "div_q_975_anom": None,
        "pv_200_anom": None, "pv_850_anom": None, "msl_anom": None,
        # Eddy winds
        "u_250_prime": None, "v_250_prime": None,
        "u_850_prime": None, "v_850_prime": None,
        "u_975_prime": None, "v_975_prime": None,
        # BtCR diagnostics
        "btcr_delta_m": None, "btcr_dil_angle": None,
    }
    # Per-cell count arrays to handle NaN properly
    count_accum: dict[str, np.ndarray | None] = {k: None for k in sum_accum}
    
    # Wind / humidity at levels - per-cell accumulation
    level_sum: dict[str, dict[int, np.ndarray | None]] = {
        "u": {250: None, 850: None, 975: None},
        "v": {250: None, 850: None, 975: None},
        "q": {975: None},
    }
    # Per-cell count arrays to handle NaN properly
    level_count: dict[str, dict[int, np.ndarray | None]] = {
        "u": {250: None, 850: None, 975: None},
        "v": {250: None, 850: None, 975: None},
        "q": {975: None},
    }
    
    # Statistics for logging
    cases_ok = 0
    cases_failed = 0
    total_timesteps = 0
    total_skipped_no_pos = 0
    total_skipped_oob = 0

    for tid, results_list, error, meta in raw_results:
        if results_list is None:
            if error and error != "file_missing":
                logging.warning(f"      Error {tid}: {error}")
            cases_failed += 1
            continue

        # Update statistics from metadata
        total_timesteps += meta.get("n_timesteps_used", 0)
        total_skipped_no_pos += meta.get("n_skipped_no_position", 0)
        total_skipped_oob += meta.get("n_skipped_out_of_bounds", 0)
        cases_ok += 1

        # Accumulate each storm-centered timestep's results (sum accumulation)
        # CRITICAL: Use per-cell NaN-aware accumulation to avoid NaN propagation.
        # Each timestep may have NaN at different edge cells; simple += would
        # spread NaN to all cells after enough timesteps.
        for result in results_list:
            # Scalars (total fields)
            for key in list(sum_accum.keys()):
                if key in result:
                    arr = result[key]
                    # Handle both ndarray and xarray DataArray
                    if hasattr(arr, 'values'):
                        arr = arr.values  # xarray DataArray
                    if hasattr(arr, 'magnitude'):
                        arr = arr.magnitude  # pint quantity
                    if isinstance(arr, np.ndarray):
                        arr_f64 = arr.astype(np.float64)
                        valid_mask = ~np.isnan(arr_f64)
                        if sum_accum[key] is None:
                            # Initialize sum with NaN replaced by 0, count with valid mask
                            sum_accum[key] = np.where(valid_mask, arr_f64, 0.0)
                            count_accum[key] = valid_mask.astype(np.int32)
                        else:
                            # Add only valid values; increment count only where valid
                            sum_accum[key] += np.where(valid_mask, arr_f64, 0.0)
                            count_accum[key] += valid_mask.astype(np.int32)

            # Winds / humidity at levels
            for var in ("u", "v"):
                for lv in (250, 850, 975):
                    key = f"{var}_{lv}"
                    if key in result:
                        arr = result[key]
                        if hasattr(arr, 'values'):
                            arr = arr.values
                        if hasattr(arr, 'magnitude'):
                            arr = arr.magnitude
                        if isinstance(arr, np.ndarray):
                            arr_f64 = arr.astype(np.float64)
                            valid_mask = ~np.isnan(arr_f64)
                            if level_sum[var][lv] is None:
                                level_sum[var][lv] = np.where(valid_mask, arr_f64, 0.0)
                                level_count[var][lv] = valid_mask.astype(np.int32)
                            else:
                                level_sum[var][lv] += np.where(valid_mask, arr_f64, 0.0)
                                level_count[var][lv] += valid_mask.astype(np.int32)
            if "q_975" in result:
                arr = result["q_975"]
                if hasattr(arr, 'values'):
                    arr = arr.values
                if hasattr(arr, 'magnitude'):
                    arr = arr.magnitude
                if isinstance(arr, np.ndarray):
                    arr_f64 = arr.astype(np.float64)
                    valid_mask = ~np.isnan(arr_f64)
                    if level_sum["q"][975] is None:
                        level_sum["q"][975] = np.where(valid_mask, arr_f64, 0.0)
                        level_count["q"][975] = valid_mask.astype(np.int32)
                    else:
                        level_sum["q"][975] += np.where(valid_mask, arr_f64, 0.0)
                        level_count["q"][975] += valid_mask.astype(np.int32)

    if total_timesteps == 0:
        raise RuntimeError(f"No valid timesteps for {ep_label}")
    
    logging.info(f"      {ep_label}: cases_ok={cases_ok}, cases_failed={cases_failed}")
    logging.info(f"      {ep_label}: total_timesteps={total_timesteps}, "
                 f"skipped_no_pos={total_skipped_no_pos}, skipped_oob={total_skipped_oob}")

    # ── Compute means from sum accumulators ───────────────────────────────
    # Scalar / single-level derived fields specifications
    scalar_specs = {
        "egr":              ("Eady Growth Rate",                            "day-1"),
        "pv_200":           ("Potential Vorticity at 200 hPa",              "K m2 kg-1 s-1"),
        "pv_850":           ("Potential Vorticity at 850 hPa",              "K m2 kg-1 s-1"),
        "adv_T_850":        ("Temperature Advection at 850 hPa",            "K s-1"),
        "div_q_975":        ("Moisture Flux Divergence at 975 hPa",         "g kg-1 s-1"),
        "ke_adv_250":       ("KE Advection at 250 hPa",                     "m2 s-3"),
        "rk_criterion_250": ("Rayleigh-Kuo Criterion at 250 hPa",           "s-1 m-1"),
        "afc_250":          ("Ageostrophic Flux Convergence 250 hPa",        "m2 s-3"),
        "msl":              ("Mean Sea Level Pressure",                      "Pa"),
        # Anomaly fields (eddy inputs relative to 30-yr monthly climatology)
        "ke_adv_250_anom":  ("KE Advection Anomaly at 250 hPa",             "m2 s-3"),
        "adv_T_850_anom":   ("Temperature Advection Anomaly at 850 hPa",    "K s-1"),
        "div_q_975_anom":   ("Moisture Flux Divergence Anomaly at 975 hPa", "g kg-1 s-1"),
        "pv_200_anom":      ("Potential Vorticity Anomaly at 200 hPa",      "K m2 kg-1 s-1"),
        "pv_850_anom":      ("Potential Vorticity Anomaly at 850 hPa",      "K m2 kg-1 s-1"),
        "msl_anom":         ("Sea Level Pressure Anomaly",                   "Pa"),
        # Eddy (primed) winds for anomaly figure overlays  X' = X − X̅_m
        "u_250_prime":      ("Eddy Zonal Wind at 250 hPa (X - Xbar_m)",     "m s-1"),
        "v_250_prime":      ("Eddy Meridional Wind at 250 hPa (X - Xbar_m)","m s-1"),
        "u_850_prime":      ("Eddy Zonal Wind at 850 hPa (X - Xbar_m)",     "m s-1"),
        "v_850_prime":      ("Eddy Meridional Wind at 850 hPa (X - Xbar_m)","m s-1"),
        "u_975_prime":      ("Eddy Zonal Wind at 975 hPa (X - Xbar_m)",     "m s-1"),
        "v_975_prime":      ("Eddy Meridional Wind at 975 hPa (X - Xbar_m)","m s-1"),
        # BtCR diagnostics (from climatological 250 hPa winds; Rivière 2006)
        "btcr_delta_m":    ("BtCR Effective Deformation (sigma_m^2 - zeta_m^2)", "s-2"),
        "btcr_dil_angle":  ("BtCR Dilatation Axis Angle (where delta_m > 0)",    "rad"),
    }
    
    # ── Build output dataset (composite means) ────────────────────────────
    data_vars: dict = {}

    for var, (lname, ustr) in scalar_specs.items():
        if sum_accum[var] is not None and count_accum[var] is not None:
            # Per-cell mean: sum / count, with NaN where count == 0
            cnt = count_accum[var].astype(np.float64)
            mean_arr = np.where(cnt > 0, sum_accum[var] / cnt, np.nan)
            data_vars[var] = (["y", "x"], mean_arr, {"long_name": lname, "units": ustr})

    # Wind / humidity means at each level
    wind_specs = {
        "u": ("Zonal Wind",         "m s-1"),
        "v": ("Meridional Wind",    "m s-1"),
        "q": ("Specific Humidity",  "kg kg-1"),
    }
    for var, (lname, ustr) in wind_specs.items():
        for lv in level_sum[var]:
            if level_sum[var][lv] is not None and level_count[var][lv] is not None:
                key = f"{var}_{lv}"
                cnt = level_count[var][lv].astype(np.float64)
                mean_arr = np.where(cnt > 0, level_sum[var][lv] / cnt, np.nan)
                data_vars[key] = (["y", "x"], mean_arr,
                                  {"long_name": f"{lname} at {lv} hPa", "units": ustr})

    ds_out = xr.Dataset(data_vars, coords={"x": x, "y": y})

    ds_out.attrs["ep_label"] = ep_label
    ds_out.attrs["n_cases"] = cases_ok
    ds_out.attrs["n_cases_failed"] = cases_failed
    ds_out.attrs["n_timesteps"] = total_timesteps
    ds_out.attrs["n_timesteps_skipped_no_position"] = total_skipped_no_pos
    ds_out.attrs["n_timesteps_skipped_out_of_bounds"] = total_skipped_oob
    ds_out.attrs["domain_size_deg"] = DOMAIN_SIZE
    ds_out.attrs["resolution_deg"] = RESOLUTION
    ds_out.attrs["composite_mode"] = COMPOSITE_MODE
    ds_out.attrs["composite_mode_description"] = (
        "full_intensification: mean over ALL storm-centered timesteps from intensification phase" 
        if COMPOSITE_MODE == "full_intensification" 
        else "central_time: only the CENTRAL storm-centered timestep of each cyclone"
    )
    ds_out.attrs["methodology"] = (
        "STORM-CENTERED: Each timestep's domain is centered on the actual cyclone "
        "position at that instant, extracted from the track data."
    )

    return ds_out


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Precompute EP structure composites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard composite (all cases, mean over intensification phase)
  python step3_precompute_composites.py --mode full_intensification

  # Central-time composite (all cases, only central timestep)
  python step3_precompute_composites.py --mode central_time

  # Top-10 most intense cyclones per EP
  python step3_precompute_composites.py --mode intense_10

  # Parallel processing (recommended: 4-8 workers)
  python step3_precompute_composites.py --mode full_intensification --jobs 4
        """,
    )
    parser.add_argument(
        "--jobs", "-j", type=int, default=1,
        help="Number of parallel workers for composite computation. "
             "Default: 1 (sequential). Recommended on remote server: 4-8.",
    )
    parser.add_argument(
        "--mode", "-m", type=str, default="full_intensification",
        choices=["full_intensification", "central_time", "intense_10"],
        help="Composite mode: 'full_intensification' (mean over all timesteps), "
             "'central_time' (use only central timestep), or "
             "'intense_10' (top-10 most intense cyclones). Default: full_intensification",
    )
    args = parser.parse_args()
    n_jobs = args.jobs if args.jobs >= 1 else 1
    
    # Set global COMPOSITE_MODE
    # For intense_10, the timestep aggregation is same as full_intensification
    global COMPOSITE_MODE
    if args.mode == "intense_10":
        COMPOSITE_MODE = "full_intensification"  # timestep aggregation method
    else:
        COMPOSITE_MODE = args.mode

    log_file = setup_logging()
    logging.info(f"   Composite mode: {args.mode}")
    if args.mode == "intense_10":
        logging.info(f"   (Using full_intensification timestep aggregation for intense subset)")
    logging.info(f"   Parallel workers: {n_jobs}")

    # Load cases based on mode
    if args.mode == "intense_10":
        # Use top-10 intense cyclones files
        ep1_file = RESULTS_DIR / "ep1_top10_intense.csv"
        ep2_file = RESULTS_DIR / "ep2_top10_intense.csv"
        if not ep1_file.exists() or not ep2_file.exists():
            logging.error(f"❌ intense_10 mode requires:")
            logging.error(f"   {ep1_file}")
            logging.error(f"   {ep2_file}")
            logging.error("   Run step1 selection first or create these files manually.")
            return
        ep1_cases = pd.read_csv(ep1_file)
        ep2_cases = pd.read_csv(ep2_file)
        logging.info(f"   EP1: {len(ep1_cases)} most intense cases")
        logging.info(f"   EP2: {len(ep2_cases)} most intense cases")
    else:
        # Standard: all cases
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

    # Save with mode suffix (use args.mode for file naming)
    mode_suffix = f"_{args.mode}"
    out1 = DATA_DIR / f"precomputed_composites_ep1{mode_suffix}.nc"
    out2 = DATA_DIR / f"precomputed_composites_ep2{mode_suffix}.nc"
    ds_ep1.to_netcdf(out1)
    ds_ep2.to_netcdf(out2)
    logging.info(f"\n   ✓ Saved: {out1.name} ({out1.stat().st_size/1024**2:.1f} MB)")
    logging.info(f"   ✓ Saved: {out2.name} ({out2.stat().st_size/1024**2:.1f} MB)")

    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 3 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"Log: {log_file}")
    logging.info(f"\nNext: python scripts/ep_structure_analysis/step4_create_figures.py --mode {args.mode}")


if __name__ == "__main__":
    main()
