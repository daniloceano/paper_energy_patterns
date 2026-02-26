"""
Step 3: Precompute Composites for EP1 & EP2

Computes spatial composites (30°×30° domain) for each EP group:
  - EGR (Eady Growth Rate) from the 250–850 hPa layer
  - PV at 200 hPa (upper-level tropopause dynamics)
  - PV at 850 hPa (low-level PV anomaly)
  - Temperature advection at 850 hPa  (-V · ∇T)
  - SLP (mean sea level pressure)

For each EP, saves a single NetCDF file with composite means on a
regular grid centred on the cyclone.

Output:
  data/era5_ep_structure/precomputed_composites_ep1.nc
  data/era5_ep_structure/precomputed_composites_ep2.nc

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
from datetime import datetime
from tqdm import tqdm

from metpy.calc import (
    potential_temperature,
    potential_vorticity_baroclinic,
    virtual_temperature,
    brunt_vaisala_frequency,
    advection as metpy_advection,
    divergence as metpy_divergence,
    mixing_ratio_from_specific_humidity,
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
    divergence : ndarray (2D)
        Horizontal divergence (s⁻¹)
    """
    lat_1d = u.latitude.values
    lon_1d = u.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # u and v are unit-tagged DataArrays — pass directly.
    result = metpy_divergence(u, v, dx=dx, dy=dy)
    return result.magnitude


def coriolis(lat):
    """Coriolis parameter f = 2Ω sin(φ), returns plain ndarray (s⁻¹)."""
    return 2.0 * OMEGA.m * np.sin(np.deg2rad(lat))


def geopotential_height(phi):
    return phi / G


def eady_growth_rate(u_250, v_250, u_850, v_850, T_250, T_850,
                     q_250, q_850, z_250, z_850,
                     T_500, q_500, z_500):
    """
    Layer-mean EGR between 250 and 850 hPa.

    σ_EGR = 0.31 · |f| / N · |∂V/∂z|
    where N is the Brunt–Väisälä frequency (computed on 3 real pressure
    levels: 850, 500, 250 hPa) and the wind shear spans the full 250–850 hPa
    layer.

    Uses MetPy's virtual_temperature, potential_temperature, and
    brunt_vaisala_frequency.

    Parameters
    ----------
    All arguments are xr.DataArray (2D, latitude × longitude).
    The *_500 arguments provide the actual 500 hPa midpoint — no
    linear interpolation needed.
    """
    # ── Coordinates ──────────────────────────────────────────────────────────
    lat_2d = T_250.latitude

    f = coriolis_parameter(T_250.latitude) # plain ndarray, s⁻¹

    # ── Mixing ratio (q → w) ─────────────────────────────────────────────────
    # q is already a unit-tagged DataArray (kg/kg); pass directly.
    # mixing_ratio_from_specific_humidity returns a pint.Quantity.
    w_250 = mixing_ratio_from_specific_humidity(q_250)
    w_500 = mixing_ratio_from_specific_humidity(q_500)
    w_850 = mixing_ratio_from_specific_humidity(q_850)

    # ── Virtual temperature ───────────────────────────────────────────────────
    # T is a unit-tagged DataArray (K); pass directly.
    Tv_250 = virtual_temperature(T_250, w_250)   # pint.Quantity [K]
    Tv_500 = virtual_temperature(T_500, w_500)
    Tv_850 = virtual_temperature(T_850, w_850)

    # ── Virtual potential temperature ─────────────────────────────────────────
    # potential_temperature(pressure, temperature) — both must carry units.
    # Using P_0 (pint.Quantity, 100000 Pa) ensures the reference pressure is
    # in SI; passing 250 hPa as Pa avoids any hPa/Pa mix-up.
    theta_v_250 = potential_temperature(25000.0 * units.pascal, Tv_250)  # [K]
    theta_v_500 = potential_temperature(50000.0 * units.pascal, Tv_500)
    theta_v_850 = potential_temperature(85000.0 * units.pascal, Tv_850)

    # ── Geopotential → geopotential height ───────────────────────────────────
    # z_* arrive as unit-tagged DataArrays in m² s⁻².  Dividing by G
    # (pint.Quantity, m s⁻²) yields metres automatically.
    z_h_250 = z_250 / G   # [m]
    z_h_500 = z_500 / G
    z_h_850 = z_850 / G

    # ── Brunt–Väisälä frequency ───────────────────────────────────────────────
    # Build 3-level xr.DataArrays using xr.concat — preserves xarray structure
    # (lat/lon coords) and pint units.  Real 500 hPa data as the middle level.
    level_hpa = [850.0, 500.0, 250.0]
    concat_kw = dict(compat="override", coords="minimal")

    height_layer = xr.concat(
        [z_h_850, z_h_500, z_h_250],
        dim=xr.Variable("level", level_hpa), **concat_kw,
    )                                                               # (level, lat, lon)
    theta_v_layer = xr.concat(
        [theta_v_850, theta_v_500, theta_v_250],
        dim=xr.Variable("level", level_hpa), **concat_kw,
    )                                                               # (level, lat, lon)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        N_qty = brunt_vaisala_frequency(height_layer, theta_v_layer,
                                        vertical_dim=0)
    # Central (500 hPa) value is the centred-FD estimate for the layer.
    # Extract plain ndarray for the subsequent manual EGR formula.
    N = N_qty.isel(level=1).metpy.unit_array.magnitude              # s⁻¹
    N = np.where(N ** 2 > MIN_N_SQUARED, N, np.nan)

    # ── Vertical wind shear ──────────────────────────────────────────────────
    # Subtraction of unit-tagged DataArrays preserves xarray structure + units;
    # extract magnitudes for numpy operations (np.where).
    dz = (z_h_250 - z_h_850).metpy.unit_array.magnitude             # m
    dz_safe = np.where(np.abs(dz) > 1.0, dz, np.nan)

    du_dz = (u_250 - u_850).metpy.unit_array.magnitude / dz_safe    # s⁻¹
    dv_dz = (v_250 - v_850).metpy.unit_array.magnitude / dz_safe
    shear = np.sqrt(du_dz ** 2 + dv_dz ** 2)                        # s⁻¹

    # f from coriolis_parameter is pint.Quantity — extract plain ndarray
    f_abs = np.abs(f.magnitude) if hasattr(f, 'magnitude') else np.abs(np.asarray(f))

    with np.errstate(invalid="ignore"):
        egr = np.where(
            (N > 0) & (np.abs(lat_2d) > MIN_LAT),
            0.31 * (f_abs / N) * shear,
            np.nan,
        )

    egr_day = egr * 86400.0
    egr_day = np.where(egr_day > MAX_EGR_DAY, np.nan, egr_day)
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
    advT : ndarray (2D)
        Temperature advection (K/s).
        Positive: warm air advection; Negative: cold air advection.
    """
    lat_1d = T_850.latitude.values
    lon_1d = T_850.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # All three are unit-tagged DataArrays — pass directly.
    result = metpy_advection(T_850, u=u_850, v=v_850, dx=dx, dy=dy)
    return result.magnitude


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
    ke_adv : ndarray (2D)
        Kinetic energy advection (m² s⁻³ = W kg⁻¹).
        Positive: KE increasing; Negative: KE decreasing.
    """
    lat_1d = u_250.latitude.values
    lon_1d = u_250.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # u_250 and v_250 are unit-tagged DataArrays (m/s); arithmetic preserves units.
    KE = 0.5 * (u_250 ** 2 + v_250 ** 2)         # DataArray [m² s⁻²]

    result = metpy_advection(KE, u=u_250, v=v_250, dx=dx, dy=dy)  # [m² s⁻³]
    return result.magnitude


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
    rk_criterion : ndarray (2D)
        ∂q/∂y field (s⁻¹ m⁻¹)
    """
    lat_1d = u_250.latitude.values
    lon_1d = u_250.longitude.values
    dx, dy, lat_2d, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)

    # .values: np.gradient operates on plain arrays
    u_np = u_250.values
    v_np = v_250.values

    # Beta (df/dy on sphere) — use .m to keep result as plain ndarray
    lat_rad = np.deg2rad(lat_2d)
    beta = (2.0 * OMEGA.m * np.cos(lat_rad)) / R_EARTH.m  # s⁻¹ m⁻¹

    # Relative vorticity: ζ = ∂v/∂x - ∂u/∂y
    dv_dx = np.gradient(v_np, axis=1) / dx
    du_dy = np.gradient(u_np, axis=0) / dy[:, np.newaxis]

    # Second derivative: ∂²u/∂y²
    d2u_dy2 = np.gradient(du_dy, axis=0) / dy[:, np.newaxis]

    rk_criterion = beta - d2u_dy2
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
    div_q_gkg : ndarray (2D)
        Moisture flux divergence (g kg⁻¹ s⁻¹).
        Positive: divergence (drying); Negative: convergence (moistening).
    """
    lat_1d = u_975.latitude.values
    lon_1d = u_975.longitude.values
    dx, dy = _metpy_grid_deltas(lat_1d, lon_1d)  # (ny, nx-1), (ny-1, nx)

    # q_975, u_975, v_975 are unit-tagged DataArrays; arithmetic preserves units.
    # Moisture flux components: [kg kg⁻¹ · m s⁻¹]
    qu = q_975 * u_975   # DataArray [kg kg⁻¹ m s⁻¹]
    qv = q_975 * v_975

    div_q = metpy_divergence(qu, qv, dx=dx, dy=dy)  # [kg kg⁻¹ s⁻¹]

    # Convert to g kg⁻¹ s⁻¹
    div_q_gkg = (div_q * 1000.0).magnitude
    return div_q_gkg


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
# COMPOSITE FOR ONE EP GROUP
# ============================================================================

def compute_composite(cases, ep_label):
    """
    Compute composite fields for one EP group.

    Per-case 2-D arrays are accumulated into a dict keyed by variable name.
    After all cases are processed, each variable is assembled into an
    xr.DataArray with dimensions (track_id, level, y, x) – or (track_id, y, x)
    for single-level/derived fields – so that the composite mean (and any
    further per-member diagnostics) can be computed or inspected easily.

    Returns xr.Dataset with composite means over the track_id dimension.
    """
    logging.info(f"\n   Computing composites for {ep_label} ({len(cases)} cases)...")

    half = DOMAIN_SIZE / 2.0
    n_pts = int(DOMAIN_SIZE / RESOLUTION) + 1
    x = np.linspace(-half, half, n_pts)
    y = np.linspace(half, -half, n_pts)

    # ── Per-case accumulator ──────────────────────────────────────────────
    # Keys that are single-level 2-D fields (y, x):
    #   "egr", "pv_200", "pv_850", "adv_T_850",
    #   "div_q_975", "ke_adv_250", "rk_criterion_250", "msl"
    # Keys that are wind/humidity fields stored with an explicit level label
    # to allow multi-level extension in the future; here we use a dict of
    # {var_name: {level_label: [2-D arrays]}} for wind/q fields and
    # a simple {var_name: [2-D arrays]} for derived scalars.
    scalar_accum: dict[str, list] = {
        "egr":              [],
        "pv_200":           [],
        "pv_850":           [],
        "adv_T_850":        [],
        "div_q_975":        [],
        "ke_adv_250":       [],
        "rk_criterion_250": [],
        "msl":              [],
    }
    # Wind / humidity at specific levels:  {var: {level_hPa: [arrays]}}
    level_accum: dict[str, dict[int, list]] = {
        "u": {250: [], 850: [], 975: []},
        "v": {250: [], 850: [], 975: []},
        "q": {975: []},
    }

    track_ids_ok: list[int] = []
    processed = 0
    failed = 0

    for _, row in tqdm(cases.iterrows(), total=len(cases), desc=f"   {ep_label}", leave=True):
        track_id = row["track_id"]
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        meta_file = DATA_DIR / f"{track_id}_metadata.csv"

        if not nc_file.exists() or not meta_file.exists():
            failed += 1
            continue

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
            # z_da stays as raw geopotential (m² s⁻²); conversion to height
            # happens inside eady_growth_rate via division by G.
            u_da = ds_mean["u"]
            v_da = ds_mean["v"]
            T_da = ds_mean["t"]
            z_da = ds_mean["z"]
            q_da = ds_mean["q"]

            def _idx(target_hPa):
                """Index of the pressure level nearest to target_hPa."""
                return int(np.argmin(np.abs(levels - target_hPa)))

            def _sel(da, target_hPa):
                """2-D DataArray (lat × lon) at the nearest pressure level."""
                return da.isel({pc: _idx(target_hPa)})

            # ── 2-D DataArrays with physical units attached ───────────────────
            # Units are assigned once here so every downstream function receives
            # unit-tagged arrays and never needs to re-attach them internally.
            u_250 = _sel(u_da, 250)  * units("m/s");  u_850 = _sel(u_da, 850) * units("m/s");  u_975 = _sel(u_da, 975) * units("m/s")
            v_250 = _sel(v_da, 250)  * units("m/s");  v_850 = _sel(v_da, 850) * units("m/s");  v_975 = _sel(v_da, 975) * units("m/s")
            T_250 = _sel(T_da, 250)  * units.kelvin;  T_500 = _sel(T_da, 500) * units.kelvin;  T_850 = _sel(T_da, 850) * units.kelvin
            z_250 = _sel(z_da, 250)  * units("m**2/s**2");  z_500 = _sel(z_da, 500) * units("m**2/s**2");  z_850 = _sel(z_da, 850) * units("m**2/s**2")
            q_250 = _sel(q_da, 250)  * units("kg/kg");  q_500 = _sel(q_da, 500) * units("kg/kg");  q_850 = _sel(q_da, 850) * units("kg/kg");  q_975 = _sel(q_da, 975) * units("kg/kg")

            # ── EGR (250–850 hPa layer, N via real 500 hPa midpoint) ─
            scalar_accum["egr"].append(
                eady_growth_rate(u_250, v_250, u_850, v_850,
                                 T_250, T_850, q_250, q_850, z_250, z_850,
                                 T_500, q_500, z_500)
            )

            # ── PV at 200 hPa (needs 175, 200, 225) ──────────────────
            scalar_accum["pv_200"].append(compute_pv_at_level(
                _sel(u_da, 175) * units("m/s"), _sel(u_da, 200) * units("m/s"), _sel(u_da, 225) * units("m/s"),
                _sel(v_da, 175) * units("m/s"), _sel(v_da, 200) * units("m/s"), _sel(v_da, 225) * units("m/s"),
                _sel(T_da, 175) * units.kelvin, _sel(T_da, 200) * units.kelvin, _sel(T_da, 225) * units.kelvin,
                np.array([levels[_idx(175)], levels[_idx(200)], levels[_idx(225)]]) * 100.0,
            ))

            # ── PV at 850 hPa (needs 825, 850, 875) ──────────────────
            scalar_accum["pv_850"].append(compute_pv_at_level(
                _sel(u_da, 825) * units("m/s"), _sel(u_da, 850) * units("m/s"), _sel(u_da, 875) * units("m/s"),
                _sel(v_da, 825) * units("m/s"), _sel(v_da, 850) * units("m/s"), _sel(v_da, 875) * units("m/s"),
                _sel(T_da, 825) * units.kelvin, _sel(T_da, 850) * units.kelvin, _sel(T_da, 875) * units.kelvin,
                np.array([levels[_idx(825)], levels[_idx(850)], levels[_idx(875)]]) * 100.0,
            ))

            # ── Temperature advection at 850 hPa ─────────────────────
            scalar_accum["adv_T_850"].append(
                temperature_advection_850(u_850, v_850, T_850)
            )

            # ── SLP ───────────────────────────────────────────────────
            if "msl" in ds_mean.data_vars:
                msl_data = ds_mean["msl"]
                if pc in msl_data.dims:
                    msl_data = msl_data.isel({pc: 0})
                scalar_accum["msl"].append(msl_data.values.squeeze())

            # ── Winds / humidity for overlays ──────────────────────────────
            # Accumulator holds plain numpy arrays (for np.stack at assembly);
            # .values strips the pint wrapper from the unit-tagged DataArrays.
            level_accum["u"][250].append(u_250.values)
            level_accum["u"][850].append(u_850.values)
            level_accum["u"][975].append(u_975.values)
            level_accum["v"][250].append(v_250.values)
            level_accum["v"][850].append(v_850.values)
            level_accum["v"][975].append(v_975.values)
            level_accum["q"][975].append(q_975.values)

            # ── Moisture flux divergence at 975 hPa ───────────────────
            scalar_accum["div_q_975"].append(
                moisture_flux_divergence_975(u_975, v_975, q_975)
            )

            # ── Kinetic energy advection at 250 hPa ───────────────────
            scalar_accum["ke_adv_250"].append(
                kinetic_energy_advection_250(u_250, v_250)
            )

            # ── Rayleigh-Kuo criterion at 250 hPa ────────────────────
            scalar_accum["rk_criterion_250"].append(
                rayleigh_kuo_criterion_250(u_250, v_250)
            )

            ds.close()
            track_ids_ok.append(track_id)
            processed += 1

        except Exception as e:
            logging.warning(f"      Error {track_id}: {type(e).__name__}: {e}")
            failed += 1

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
    parser.parse_args()   # no special args yet, but keeps interface consistent

    log_file = setup_logging()

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
        ds_ep1 = compute_composite(ep1_cases, "EP1")
        ds_ep2 = compute_composite(ep2_cases, "EP2")

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
