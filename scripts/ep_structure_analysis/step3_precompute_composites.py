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

from metpy.calc import potential_temperature, potential_vorticity_baroclinic
from metpy.units import units
import metpy.constants as mpconstants

# ============================================================================
# PHYSICAL CONSTANTS
# ============================================================================

G = 9.80665           # m s⁻²
OMEGA = 7.292e-5      # rad s⁻¹
R_d = 287.0           # J kg⁻¹ K⁻¹
C_p = 1004.0          # J kg⁻¹ K⁻¹
KAPPA = R_d / C_p
P_0 = 100000.0        # Pa
R_EARTH = 6.371e6     # m

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
    dy = R_EARTH * np.deg2rad(dlat)  # meters
    
    # dx: spacing in zonal direction (varies with latitude)
    dlon = np.gradient(lon_1d)  # degrees
    dx = R_EARTH * np.cos(np.deg2rad(lat_2d)) * np.deg2rad(
        np.broadcast_to(dlon[np.newaxis, :], lat_2d.shape)
    )  # meters
    
    return dx, dy, lat_2d, lon_2d


def spherical_divergence(u, v, lat_1d, lon_1d):
    """
    Compute horizontal divergence on a spherical Earth.
    
    Uses the correct spherical divergence formula:
    ∇·F = (1/(R cos φ)) * ∂Fλ/∂λ + (1/(R cos φ)) * ∂(Fφ cos φ)/∂φ
    
    Simplified for small domains:
    ∇·F ≈ ∂u/∂x + ∂v/∂y
    
    where dx and dy are computed accounting for spherical geometry.
    
    Parameters
    ----------
    u : ndarray (2D)
        Zonal wind component (m/s)
    v : ndarray (2D)
        Meridional wind component (m/s)
    lat_1d : array_like
        1D latitude array (degrees)
    lon_1d : array_like
        1D longitude array (degrees)
    
    Returns
    -------
    divergence : ndarray (2D)
        Horizontal divergence (s⁻¹)
    """
    dx, dy, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)
    
    # Compute derivatives
    du_dx = np.gradient(u, axis=1) / dx
    dv_dy = np.gradient(v, axis=0) / dy[:, np.newaxis]
    
    return du_dx + dv_dy


def coriolis(lat):
    return 2.0 * OMEGA * np.sin(np.deg2rad(lat))


def geopotential_height(phi):
    return phi / G


def eady_growth_rate(u_250, v_250, u_850, v_850, T_250, T_850,
                     q_250, q_850, z_250, z_850, lat_2d):
    """
    Layer-mean EGR between 250 and 850 hPa.

    σ_EGR = 0.31 · |f| / N · |∂V/∂z|
    where the vertical wind shear and static stability are estimated
    from the 250−850 hPa layer.
    """
    f = np.abs(coriolis(lat_2d))

    # Virtual potential temperature at each level
    def _theta_v(T, q, p_pa):
        Tv = T * (1.0 + 0.61 * q)
        return Tv * (P_0 / p_pa) ** KAPPA

    theta_v_250 = _theta_v(T_250, q_250, 25000.0)
    theta_v_850 = _theta_v(T_850, q_850, 85000.0)
    theta_v_mid = 0.5 * (theta_v_250 + theta_v_850)

    dz = z_250 - z_850
    dz_safe = np.where(np.abs(dz) > 1.0, dz, np.nan)

    dtheta_dz = (theta_v_250 - theta_v_850) / dz_safe
    N_sq = (G / theta_v_mid) * dtheta_dz

    with np.errstate(invalid="ignore"):
        N = np.where(N_sq > MIN_N_SQUARED, np.sqrt(N_sq), np.nan)

    du_dz = (u_250 - u_850) / dz_safe
    dv_dz = (v_250 - v_850) / dz_safe
    shear = np.sqrt(du_dz ** 2 + dv_dz ** 2)

    with np.errstate(invalid="ignore"):
        egr = np.where(
            (N > 0) & (np.abs(lat_2d) > MIN_LAT),
            0.31 * (f / N) * shear,
            np.nan,
        )

    egr_day = egr * 86400.0
    egr_day = np.where(egr_day > MAX_EGR_DAY, np.nan, egr_day)
    return egr_day


def compute_pv_at_level(u_3lev, v_3lev, T_3lev, p_3lev, lat_1d, lon_1d):
    """
    Baroclinic PV using MetPy with 3 vertical levels (centred FD).
    Returns PV at the middle level in SI units (K m² kg⁻¹ s⁻¹).
    """
    p_hpa = p_3lev / 100.0

    T_da = xr.DataArray(
        T_3lev,
        coords={"level": p_hpa, "latitude": lat_1d, "longitude": lon_1d},
        dims=["level", "latitude", "longitude"],
    ) * units.kelvin

    u_da = xr.DataArray(
        u_3lev,
        coords={"level": p_hpa, "latitude": lat_1d, "longitude": lon_1d},
        dims=["level", "latitude", "longitude"],
    ) * units("m/s")

    v_da = xr.DataArray(
        v_3lev,
        coords={"level": p_hpa, "latitude": lat_1d, "longitude": lon_1d},
        dims=["level", "latitude", "longitude"],
    ) * units("m/s")

    p_da = xr.DataArray(p_hpa, coords={"level": p_hpa}, dims=["level"]) * units.hPa

    theta = potential_temperature(p_da, T_da)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        pv = potential_vorticity_baroclinic(theta, p_da, u_da, v_da)

    return pv.isel(level=1).metpy.unit_array.magnitude


def temperature_advection_850(u_850, v_850, T_850, lat_1d, lon_1d):
    """
    Horizontal temperature advection at 850 hPa:
      advT = -V · ∇T = -(u ∂T/∂x + v ∂T/∂y)
    
    Parameters
    ----------
    u_850 : ndarray (2D)
        Zonal wind at 850 hPa (m/s)
    v_850 : ndarray (2D)
        Meridional wind at 850 hPa (m/s)
    T_850 : ndarray (2D)
        Temperature at 850 hPa (K)
    lat_1d : array_like
        1D latitude array (degrees)
    lon_1d : array_like
        1D longitude array (degrees)
    
    Returns
    -------
    advT : ndarray (2D)
        Temperature advection (K/s)
        Positive: warm air advection
        Negative: cold air advection
    """
    dx, dy, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)
    
    # Temperature gradients
    dT_dx = np.gradient(T_850, axis=1) / dx
    dT_dy = np.gradient(T_850, axis=0) / dy[:, np.newaxis]
    
    # Advection: -V · ∇T
    advT = -(u_850 * dT_dx + v_850 * dT_dy)
    
    return advT


def kinetic_energy_advection_250(u_250, v_250, lat_1d, lon_1d):
    """
    Kinetic energy advection at 250 hPa (jet level).
    
    KE_adv = -V · ∇(KE) = -V · ∇(0.5 * (u² + v²))
            = -(u * ∂KE/∂x + v * ∂KE/∂y)
    
    Parameters
    ----------
    u_250 : ndarray (2D)
        Zonal wind at 250 hPa (m/s)
    v_250 : ndarray (2D)
        Meridional wind at 250 hPa (m/s)
    lat_1d : array_like
        1D latitude array (degrees)
    lon_1d : array_like
        1D longitude array (degrees)
    
    Returns
    -------
    ke_adv : ndarray (2D)
        Kinetic energy advection (m² s⁻³ = W kg⁻¹)
        Positive: KE increasing (gaining energy)
        Negative: KE decreasing (losing energy)
    """
    dx, dy, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)
    
    # Kinetic energy
    KE = 0.5 * (u_250**2 + v_250**2)
    
    # KE gradients
    dKE_dx = np.gradient(KE, axis=1) / dx
    dKE_dy = np.gradient(KE, axis=0) / dy[:, np.newaxis]
    
    # Advection: -V · ∇KE
    ke_adv = -(u_250 * dKE_dx + v_250 * dKE_dy)
    
    return ke_adv


def rayleigh_kuo_criterion_250(u_250, v_250, lat_1d, lon_1d, lat_2d):
    """
    Simplified Rayleigh-Kuo instability criterion at 250 hPa.
    
    The classical RK criterion states that a necessary condition for
    barotropic/baroclinic instability is:
        ∂q/∂y changes sign in the domain
    
    where q is the quasi-geostrophic potential vorticity.
    
    Simplified version used here:
        q ≈ f + ζ = f + (∂v/∂x - ∂u/∂y)
    
    The criterion is satisfied where:
        ∂q/∂y = β - ∂²u/∂y² + ∂²v/∂x∂y < 0
    
    For simplicity, we compute:
        ∂q/∂y ≈ β - ∂²u/∂y²
    
    where β ≈ 2Ω*cosφ/R_earth (meridional gradient of Coriolis)
    
    Parameters
    ----------
    u_250 : ndarray (2D)
        Zonal wind at 250 hPa (m/s)
    v_250 : ndarray (2D)
        Meridional wind at 250 hPa (m/s)
    lat_1d : array_like
        1D latitude array (degrees)
    lon_1d : array_like
        1D longitude array (degrees)
    lat_2d : ndarray (2D)
        2D latitude field (degrees)
    
    Returns
    -------
    rk_criterion : ndarray (2D)
        ∂q/∂y field (s⁻¹ m⁻¹)
        Regions where RK_criterion < 0 satisfy necessary condition for instability
    """
    dx, dy, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)
    
    # Beta (df/dy on sphere)
    lat_rad = np.deg2rad(lat_2d)
    beta = (2.0 * OMEGA * np.cos(lat_rad)) / R_EARTH  # s⁻¹ m⁻¹
    
    # Relative vorticity: ζ = ∂v/∂x - ∂u/∂y
    dv_dx = np.gradient(v_250, axis=1) / dx
    du_dy = np.gradient(u_250, axis=0) / dy[:, np.newaxis]
    zeta = dv_dx - du_dy
    
    # Second derivative: ∂²u/∂y²
    d2u_dy2 = np.gradient(du_dy, axis=0) / dy[:, np.newaxis]
    
    # RK criterion: ∂q/∂y = β - ∂²u/∂y²
    # Negative values indicate regions where instability condition is satisfied
    rk_criterion = beta - d2u_dy2
    
    return rk_criterion


def moisture_flux_divergence_975(u_975, v_975, q_975, lat_1d, lon_1d):
    """
    Moisture flux divergence at 975 hPa:
      div_q = ∇·(q*V) = ∂(q*u)/∂x + ∂(q*v)/∂y
    
    Parameters
    ----------
    u_975 : ndarray (2D)
        Zonal wind at 975 hPa (m/s)
    v_975 : ndarray (2D)
        Meridional wind at 975 hPa (m/s)
    q_975 : ndarray (2D)
        Specific humidity at 975 hPa (kg/kg)
    lat_1d : array_like
        1D latitude array (degrees)
    lon_1d : array_like
        1D longitude array (degrees)
    
    Returns
    -------
    div_q_gkg : ndarray (2D)
        Moisture flux divergence (g kg⁻¹ s⁻¹)
        Positive: divergence (drying)
        Negative: convergence (moistening)
    
    Notes
    -----
    Uses spherical grid spacing. Units are tracked and converted:
    - Input q in kg/kg
    - Output in g/kg/s for easier interpretation
    """
    dx, dy, _, _ = compute_spherical_grid_spacing(lat_1d, lon_1d)
    
    # Moisture fluxes with MetPy units for tracking
    qu = (q_975 * units('kg/kg')) * (u_975 * units('m/s'))
    qv = (q_975 * units('kg/kg')) * (v_975 * units('m/s'))
    
    # Compute divergence: ∂(qu)/∂x + ∂(qv)/∂y
    dqu_dx = np.gradient(qu.magnitude, axis=1) / dx
    dqv_dy = np.gradient(qv.magnitude, axis=0) / dy[:, np.newaxis]
    
    div_q = (dqu_dx + dqv_dy) * qu.units / units('m')  # kg/kg/m * m/s / m = kg/kg/s
    
    # Convert to g kg⁻¹ s⁻¹
    div_q_gkg = (div_q * 1000.0 * units('g/kg')).magnitude
    
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

    Returns xr.Dataset with composite means.
    """
    logging.info(f"\n   Computing composites for {ep_label} ({len(cases)} cases)...")

    half = DOMAIN_SIZE / 2.0
    n_pts = int(DOMAIN_SIZE / RESOLUTION) + 1
    x = np.linspace(-half, half, n_pts)
    y = np.linspace(half, -half, n_pts)

    # Accumulators
    egr_list = []
    pv200_list = []
    pv850_list = []
    advT_list = []
    slp_list = []
    u250_list = []
    v250_list = []
    u850_list = []
    v850_list = []
    u975_list = []
    v975_list = []
    q975_list = []
    div_q975_list = []
    ke_adv_list = []
    rk_criterion_list = []

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

            u = ds_mean["u"].values
            v = ds_mean["v"].values
            T = ds_mean["t"].values
            z_geo = ds_mean["z"].values
            q = ds_mean["q"].values
            z = geopotential_height(z_geo)

            lat_1d = ds_mean.latitude.values
            lon_1d = ds_mean.longitude.values
            lat_2d, lon_2d = np.meshgrid(lat_1d, lon_1d, indexing="ij")

            # Level indices
            def _idx(target):
                return int(np.argmin(np.abs(levels - target)))

            i250 = _idx(250)
            i850 = _idx(850)
            i975 = _idx(975)

            # ── EGR (250–850 hPa layer) ──────────────────────────────
            egr = eady_growth_rate(
                u[i250], v[i250], u[i850], v[i850],
                T[i250], T[i850], q[i250], q[i850],
                z[i250], z[i850], lat_2d,
            )
            egr_list.append(egr)

            # ── PV at 200 hPa (needs 175, 200, 225) ──────────────────
            i175 = _idx(175)
            i200 = _idx(200)
            i225 = _idx(225)
            u3 = np.array([u[i175], u[i200], u[i225]])
            v3 = np.array([v[i175], v[i200], v[i225]])
            T3 = np.array([T[i175], T[i200], T[i225]])
            p3 = np.array([levels[i175], levels[i200], levels[i225]]) * 100.0  # hPa→Pa
            pv200 = compute_pv_at_level(u3, v3, T3, p3, lat_1d, lon_1d)
            pv200_list.append(pv200)

            # ── PV at 850 hPa (needs 825, 850, 875) ──────────────────
            i825 = _idx(825)
            i875 = _idx(875)
            u3b = np.array([u[i825], u[i850], u[i875]])
            v3b = np.array([v[i825], v[i850], v[i875]])
            T3b = np.array([T[i825], T[i850], T[i875]])
            p3b = np.array([levels[i825], levels[i850], levels[i875]]) * 100.0
            pv850 = compute_pv_at_level(u3b, v3b, T3b, p3b, lat_1d, lon_1d)
            pv850_list.append(pv850)

            # ── Temperature advection at 850 hPa ─────────────────────
            advT = temperature_advection_850(u[i850], v[i850], T[i850], lat_1d, lon_1d)
            advT_list.append(advT)

            # ── SLP ───────────────────────────────────────────────────
            if "msl" in ds_mean.data_vars:
                # MSL is a surface variable - drop pressure dimension if present
                msl_data = ds_mean["msl"]
                if pc in msl_data.dims:
                    msl_data = msl_data.isel({pc: 0})  # Take first level (all should be identical)
                slp_list.append(msl_data.values.squeeze())

            # ── Winds for overlays ────────────────────────────────────
            u250_list.append(u[i250])
            v250_list.append(v[i250])
            u850_list.append(u[i850])
            v850_list.append(v[i850])

            # ── Moisture fields at 975 hPa ────────────────────────────
            u975_list.append(u[i975])
            v975_list.append(v[i975])
            q975_list.append(q[i975])
            
            # ── Moisture flux divergence at 975 hPa ───────────────────
            div_q = moisture_flux_divergence_975(u[i975], v[i975], q[i975], lat_1d, lon_1d)
            div_q975_list.append(div_q)

            # ── Kinetic energy advection at 250 hPa ───────────────────
            ke_adv = kinetic_energy_advection_250(u[i250], v[i250], lat_1d, lon_1d)
            ke_adv_list.append(ke_adv)

            # ── Rayleigh-Kuo criterion at 250 hPa ────────────────────
            rk_crit = rayleigh_kuo_criterion_250(u[i250], v[i250], lat_1d, lon_1d, lat_2d)
            rk_criterion_list.append(rk_crit)

            ds.close()
            processed += 1

        except Exception as e:
            logging.warning(f"      Error {track_id}: {type(e).__name__}: {e}")
            failed += 1

    if processed == 0:
        raise RuntimeError(f"No valid cases for {ep_label}")

    logging.info(f"      {ep_label}: processed={processed}, failed={failed}")

    # ── Build output dataset ──────────────────────────────────────────────
    ds_out = xr.Dataset(
        {
            "egr": (["y", "x"], np.nanmean(np.stack(egr_list), axis=0)),
            "pv_200": (["y", "x"], np.nanmean(np.stack(pv200_list), axis=0)),
            "pv_850": (["y", "x"], np.nanmean(np.stack(pv850_list), axis=0)),
            "adv_T_850": (["y", "x"], np.nanmean(np.stack(advT_list), axis=0)),
            "u_250": (["y", "x"], np.nanmean(np.stack(u250_list), axis=0)),
            "v_250": (["y", "x"], np.nanmean(np.stack(v250_list), axis=0)),
            "u_850": (["y", "x"], np.nanmean(np.stack(u850_list), axis=0)),
            "v_850": (["y", "x"], np.nanmean(np.stack(v850_list), axis=0)),
            "u_975": (["y", "x"], np.nanmean(np.stack(u975_list), axis=0)),
            "v_975": (["y", "x"], np.nanmean(np.stack(v975_list), axis=0)),
            "q_975": (["y", "x"], np.nanmean(np.stack(q975_list), axis=0)),
            "div_q_975": (["y", "x"], np.nanmean(np.stack(div_q975_list), axis=0)),
            "ke_adv_250": (["y", "x"], np.nanmean(np.stack(ke_adv_list), axis=0)),
            "rk_criterion_250": (["y", "x"], np.nanmean(np.stack(rk_criterion_list), axis=0)),
        },
        coords={"x": x, "y": y},
    )

    if slp_list:
        ds_out["msl"] = (["y", "x"], np.nanmean(np.stack(slp_list), axis=0))

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
