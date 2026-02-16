"""
Step 3: Precompute Composites for ALL Variables and Diagnostics

Precomputes spatial composites (domain-mean) for:
1. All downloaded ERA5 variables
2. Diagnostic fields (EGR, PV, ∂η/∂y)

This avoids reprocessing in subsequent analyses.

Features:
- Parallel processing (multiprocessing)
- Robust logging for nohup execution
- Progress tracking
- Automatic error recovery

This step:
- Reads all ERA5 files downloaded in step2
- Computes composites for ALL pressure levels and ALL variables
- Computes instability diagnostics (EGR, PV, Rayleigh-Kuo)
- Saves results in a single NetCDF file for fast access
- Includes SLP (mean sea level pressure)

Output:
- data/era5_ep1/precomputed_composites.nc
- logs/step3_precompute_YYYYMMDD_HHMMSS.log

Usage:
    python step3_precompute_composites.py [--jobs N]
    nohup python step3_precompute_composites.py --jobs 8 &

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
import warnings
import argparse
import logging
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial
from tqdm import tqdm

# MetPy for meteorological calculations
from metpy.calc import virtual_temperature, potential_temperature, potential_vorticity_baroclinic
from metpy.units import units

# Physical constants (SI units)
G = 9.80665              # Standard gravity (m s⁻²)
OMEGA = 7.292e-5         # Earth angular velocity (rad s⁻¹)
R_d = 287.0              # Gas constant dry air (J kg⁻¹ K⁻¹)
C_p = 1004.0             # Specific heat constant pressure (J kg⁻¹ K⁻¹)
KAPPA = R_d / C_p        # Poisson constant ≈ 0.286
P_0 = 100000.0           # Reference pressure 1000 hPa (Pa)
R_EARTH = 6.371e6        # Earth radius (m)

# Quality control
MIN_LAT = 5.0            # Minimum |lat| for EGR (avoid equator)
MAX_EGR_DAY = 5.0        # Maximum reasonable EGR (day⁻¹)
MIN_N_SQUARED = 1e-6     # Minimum N² for stable stratification

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Domain sizes for composites
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}
RESOLUTION = 0.25


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Setup logging to file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"step3_precompute_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("=" * 80)
    logging.info("STEP 3: PRECOMPUTE COMPOSITES + DIAGNOSTICS")
    logging.info("=" * 80)
    logging.info(f"Log file: {log_file}")
    
    return log_file

# Quality control
MIN_LAT = 5.0            # Minimum |lat| for EGR (avoid equator)
MAX_EGR_DAY = 5.0        # Maximum reasonable EGR (day⁻¹)
MIN_N_SQUARED = 1e-6     # Minimum N² for stable stratification

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"

# Domain sizes for composites
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}
RESOLUTION = 0.25


# ============================================================================
# HELPER FUNCTIONS FOR INSTABILITY DIAGNOSTICS
# ============================================================================

def coriolis_parameter(lat):
    """Coriolis: f = 2Ω sin(φ)"""
    return 2.0 * OMEGA * np.sin(np.deg2rad(lat))


def geopotential_height(geopotential):
    """Convert Φ (m² s⁻²) to Z (m): Z = Φ/g"""
    return geopotential / G


def virtual_temperature_field(T, q):
    """Virtual temperature: Tv = T(1 + 0.61q)"""
    Tv = virtual_temperature(T * units.kelvin, q * units('kg/kg'))
    return Tv.magnitude


def virtual_potential_temperature_field(T, q, p):
    """Virtual potential temperature: θv = Tv(p₀/p)^κ"""
    Tv = virtual_temperature_field(T, q)
    theta_v = potential_temperature(p * units.pascal, Tv * units.kelvin)
    return theta_v.magnitude


def brunt_vaisala_frequency(T, q, p, z):
    """Brunt-Väisälä frequency: N² = (g/θv)(∂θv/∂z)
    Uses centered finite differences with 3 vertical levels.
    Returns N (s⁻¹) and N² (s⁻²).
    """
    theta_v = np.array([
        virtual_potential_temperature_field(T[i], q[i], p[i])
        for i in range(3)
    ])
    
    dtheta_v = theta_v[0] - theta_v[2]  # upper - lower
    dz = z[0] - z[2]
    
    dz_safe = np.where(np.abs(dz) > 1.0, dz, np.nan)
    dtheta_v_dz = dtheta_v / dz_safe
    
    N_squared = (G / theta_v[1]) * dtheta_v_dz
    
    # Suppress expected warning for negative N² (statically unstable atmosphere)
    with np.errstate(invalid='ignore'):
        N = np.where(N_squared > MIN_N_SQUARED, np.sqrt(N_squared), np.nan)
    
    return N, N_squared, theta_v[1]


def vertical_wind_shear(u, v, z):
    """Vertical wind shear: |∂V/∂z| = √[(∂u/∂z)² + (∂v/∂z)²]
    Uses centered finite differences with 3 vertical levels.
    """
    du = u[0] - u[2]
    dv = v[0] - v[2]
    dz = z[0] - z[2]
    
    dz_safe = np.where(np.abs(dz) > 1.0, dz, np.nan)
    du_dz = du / dz_safe
    dv_dz = dv / dz_safe
    shear_mag = np.sqrt(du_dz**2 + dv_dz**2)
    
    return shear_mag, du_dz, dv_dz


def eady_growth_rate(u, v, T, q, p, z, lat):
    """Eady Growth Rate: σ = 0.31 × (|f|/N) × |∂V/∂z|
    Returns EGR in day⁻¹
    """
    f = np.abs(coriolis_parameter(lat))
    N, N_sq, theta_v = brunt_vaisala_frequency(T, q, p, z)
    shear, du_dz, dv_dz = vertical_wind_shear(u, v, z)
    
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        egr = np.where(
            (N > 0) & (np.abs(lat) > MIN_LAT),
            0.31 * (f / N) * shear,
            np.nan
        )
    
    egr_day = egr * 86400.0
    egr_day = np.where(egr_day > MAX_EGR_DAY, np.nan, egr_day)
    
    return egr_day


def relative_vorticity(u, v, lat, lon):
    """Relative vorticity: ζ = ∂v/∂x - ∂u/∂y"""
    dlat = np.gradient(lat, axis=0)
    dlon = np.gradient(lon, axis=1)
    
    dx = R_EARTH * np.cos(np.deg2rad(lat)) * np.deg2rad(dlon)
    dy = R_EARTH * np.deg2rad(dlat)
    
    dv_dx = np.gradient(v, axis=1) / dx
    du_dy = np.gradient(u, axis=0) / dy
    
    return dv_dx - du_dy


def compute_rayleigh_kuo_gradient(u, v, lat, lon):
    """Compute ∂η/∂y where η = ζ + f is absolute vorticity.
    Returns both 2D field and zonal mean.
    """
    zeta = relative_vorticity(u, v, lat, lon)
    f = coriolis_parameter(lat)
    eta = zeta + f
    
    # Meridional gradient (2D)
    dlat = np.gradient(lat, axis=0)
    dy = R_EARTH * np.deg2rad(dlat)
    deta_dy = np.gradient(eta, axis=0) / dy
    
    # Zonal mean
    deta_dy_zonal = np.nanmean(deta_dy, axis=1)
    
    return deta_dy, deta_dy_zonal


def compute_baroclinic_pv(u, v, T, q, p, z, lat_2d, lon_2d):
    """Compute baroclinic potential vorticity using MetPy.
    Returns PV at middle level (index 1).
    """
    nlev, nlat, nlon = T.shape
    lat_1d = lat_2d[:, 0]
    lon_1d = lon_2d[0, :]
    pressure_hpa = p / 100.0
    
    temperature_da = xr.DataArray(
        T, coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units.kelvin
    
    u_da = xr.DataArray(
        u, coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units('m/s')
    
    v_da = xr.DataArray(
        v, coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units('m/s')
    
    pressure_da = xr.DataArray(
        pressure_hpa, coords={'level': pressure_hpa}, dims=['level']
    ) * units.hPa
    
    # Calculate potential temperature
    theta = potential_temperature(pressure_da, temperature_da)
    
    # Calculate baroclinic PV (suppress MetPy dimension detection warning)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Vertical dimension number not found')
        pv_baroclinic = potential_vorticity_baroclinic(theta, pressure_da, u_da, v_da)
    
    # Return middle level
    return pv_baroclinic.isel(level=1).metpy.unit_array.magnitude


# ============================================================================
# SUBDOMAIN EXTRACTION
# ============================================================================


def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """
    Interpolate dataset to a regular centered grid.
    Expects variables with dims (time, pressure_level, latitude, longitude) or (time, latitude, longitude).
    Returns an xarray.Dataset with the target regular grid.
    """
    half = domain_size / 2.0
    n_points = int(domain_size / RESOLUTION) + 1
    lat_target = np.linspace(center_lat + half, center_lat - half, n_points)
    lon_target = np.linspace(center_lon - half, center_lon + half, n_points)
    
    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1)
    )
    
    ds_interp = ds_sub.interp(latitude=lat_target, longitude=lon_target, method='linear')
    return ds_interp


def compute_composites_for_domain(cases, domain_name):
    """
    Compute composite means for all variables, diagnostics, and fields for a given domain.
    
    Returns:
    --------
    ds_out : xarray.Dataset with composites
        Contains both raw variables and diagnostic fields:
        - Raw: u, v, t, z, q, msl
        - Diagnostics: egr (at Ca level), deta_dy (at Ck level), deta_dy_zonal, pv_ca, pv_ck
        Dimensions: (level, y_<domain>, x_<domain>) or (y_<domain>, x_<domain>) for 2D fields
    """
    domain_size = DOMAIN_SIZES[domain_name]
    
    # Initialize lists to accumulate data
    var_lists = {}
    egr_list = []
    deta_dy_list = []
    deta_dy_zonal_list = []
    pv_ca_list = []  # PV at Ca level (975 hPa)
    pv_ck_list = []  # PV at Ck level (350 hPa)
    
    logging.info(f"\n   Processing {domain_name} domain ({domain_size}°)...")
    
    # Progress tracking
    processed = 0
    failed = 0
    
    for idx, row in tqdm(cases.iterrows(), total=len(cases), 
                        desc=f"   {domain_name}", 
                        leave=False):
        track_id = row['track_id']
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        meta_file = DATA_DIR / f"{track_id}_metadata.csv"
        
        if not nc_file.exists() or not meta_file.exists():
            failed += 1
            continue
        
        try:
            ds = xr.open_dataset(nc_file)
            meta = pd.read_csv(meta_file).iloc[0]
            
            # Get center coordinates
            center_lat = meta['track_center_lat']
            center_lon = meta['track_center_lon']
            
            # Extract subdomain - average over time dimension
            ds_sub = extract_subdomain(ds, center_lat, center_lon, domain_size)
            
            # Average over time (all intensification timesteps)
            ds_mean = ds_sub.mean(dim='valid_time' if 'valid_time' in ds_sub.dims else 'time')
            
            # Accumulate raw variables
            for var in ds_mean.data_vars:
                if var not in var_lists:
                    var_lists[var] = []
                var_lists[var].append(ds_mean[var].values)
            
            # Prepare data for diagnostics
            pressure_coord = 'pressure_level' if 'pressure_level' in ds_mean.coords else 'level'
            levels = ds_mean[pressure_coord].values
            
            u = ds_mean['u'].values  # (level, lat, lon)
            v = ds_mean['v'].values
            T = ds_mean['t'].values
            q = ds_mean['q'].values
            z_geo = ds_mean['z'].values
            
            z = geopotential_height(z_geo)
            
            # Build 2D lat/lon grids
            lat_1d = ds_mean.latitude.values
            lon_1d = ds_mean.longitude.values
            lat_2d, lon_2d = np.meshgrid(lat_1d, lon_1d, indexing='ij')
            
            # Find levels for Ca (975 hPa) and Ck (350 hPa)
            idx_975 = np.argmin(np.abs(levels - 975))
            idx_350 = np.argmin(np.abs(levels - 350))
            idx_250 = np.argmin(np.abs(levels - 250))
            
            # --- COMPUTE EGR at Ca level (975 hPa) ---
            # Need 3 levels: 950, 975, 1000 hPa
            idx_950 = np.argmin(np.abs(levels - 950))
            idx_1000 = np.argmin(np.abs(levels - 1000))
            
            u_egr = np.array([u[idx_950], u[idx_975], u[idx_1000]])
            v_egr = np.array([v[idx_950], v[idx_975], v[idx_1000]])
            T_egr = np.array([T[idx_950], T[idx_975], T[idx_1000]])
            q_egr = np.array([q[idx_950], q[idx_975], q[idx_1000]])
            p_egr = np.array([levels[idx_950], levels[idx_975], levels[idx_1000]])
            z_egr = np.array([z[idx_950], z[idx_975], z[idx_1000]])
            
            egr = eady_growth_rate(u_egr, v_egr, T_egr, q_egr, p_egr, z_egr, lat_2d)
            egr_list.append(egr)
            
            # --- COMPUTE ∂η/∂y at Ck level (350 hPa) ---
            u_ck = u[idx_350]
            v_ck = v[idx_350]
            
            deta_dy, deta_dy_zonal = compute_rayleigh_kuo_gradient(u_ck, v_ck, lat_2d, lon_2d)
            deta_dy_list.append(deta_dy)
            deta_dy_zonal_list.append(deta_dy_zonal)
            
            # --- COMPUTE PV at Ca level (975 hPa) ---
            # Need 3 levels around 975 hPa
            u_pv_ca = np.array([u[idx_950], u[idx_975], u[idx_1000]])
            v_pv_ca = np.array([v[idx_950], v[idx_975], v[idx_1000]])
            T_pv_ca = np.array([T[idx_950], T[idx_975], T[idx_1000]])
            q_pv_ca = np.array([q[idx_950], q[idx_975], q[idx_1000]])
            p_pv_ca = np.array([levels[idx_950], levels[idx_975], levels[idx_1000]])
            z_pv_ca = np.array([z[idx_950], z[idx_975], z[idx_1000]])
            
            pv_ca = compute_baroclinic_pv(u_pv_ca, v_pv_ca, T_pv_ca, q_pv_ca, p_pv_ca, z_pv_ca, lat_2d, lon_2d)
            pv_ca_list.append(pv_ca)
            
            # --- COMPUTE PV at Ck level (350 hPa) ---
            # Need 3 levels around 350 hPa
            idx_300 = np.argmin(np.abs(levels - 300))
            idx_400 = np.argmin(np.abs(levels - 400))
            
            u_pv_ck = np.array([u[idx_300], u[idx_350], u[idx_400]])
            v_pv_ck = np.array([v[idx_300], v[idx_350], v[idx_400]])
            T_pv_ck = np.array([T[idx_300], T[idx_350], T[idx_400]])
            q_pv_ck = np.array([q[idx_300], q[idx_350], q[idx_400]])
            p_pv_ck = np.array([levels[idx_300], levels[idx_350], levels[idx_400]])
            z_pv_ck = np.array([z[idx_300], z[idx_350], z[idx_400]])
            
            pv_ck = compute_baroclinic_pv(u_pv_ck, v_pv_ck, T_pv_ck, q_pv_ck, p_pv_ck, z_pv_ck, lat_2d, lon_2d)
            pv_ck_list.append(pv_ck)
            
            ds.close()
            processed += 1
            
        except Exception as e:
            logging.warning(f"      Error processing {track_id}: {e}")
            failed += 1
            continue
    
    if not var_lists:
        raise RuntimeError(f"No valid cases found for domain {domain_name}")
    
    logging.info(f"      Completed: {processed}/{len(cases)} cases (failed: {failed})")
    
    # Compute means for raw variables
    logging.info(f"      Computing ensemble means...")
    composites = {}
    for var, data_list in var_lists.items():
        composites[var] = np.nanmean(np.stack(data_list), axis=0)
    
    # Compute means for diagnostics
    egr_mean = np.nanmean(np.stack(egr_list), axis=0)
    deta_dy_mean = np.nanmean(np.stack(deta_dy_list), axis=0)
    deta_dy_zonal_mean = np.nanmean(np.stack(deta_dy_zonal_list), axis=0)
    pv_ca_mean = np.nanmean(np.stack(pv_ca_list), axis=0)
    pv_ck_mean = np.nanmean(np.stack(pv_ck_list), axis=0)
    
    # Create output dataset with domain-specific dimensions
    ds_out = xr.Dataset()
    
    # Determine grid dimensions from first variable
    first_var = list(composites.keys())[0]
    first_data = composites[first_var]
    
    if len(first_data.shape) == 3:  # (level, lat, lon)
        nlev, nlat, nlon = first_data.shape
        half = domain_size / 2.0
        x = np.linspace(-half, half, nlon)
        y = np.linspace(half, -half, nlat)
        
        # Get pressure levels from first file
        sample_file = None
        for idx, row in cases.iterrows():
            sample_file = DATA_DIR / f"{row['track_id']}_era5.nc"
            if sample_file.exists():
                break
        
        if sample_file:
            with xr.open_dataset(sample_file) as ds_sample:
                levels = ds_sample['pressure_level'].values if 'pressure_level' in ds_sample.coords else ds_sample['level'].values
        else:
            levels = np.arange(nlev)
        
        # Domain-specific dimension names
        level_dim = f'level_{domain_name}'
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'
        
        # Add 3D variables (with pressure levels)
        for var, data in composites.items():
            if len(data.shape) == 3:
                ds_out[f'{domain_name}_{var}'] = ((level_dim, y_dim, x_dim), data)
        
        # Add 2D variables (SLP - no pressure dimension)
        for var, data in composites.items():
            if len(data.shape) == 2:
                ds_out[f'{domain_name}_{var}'] = ((y_dim, x_dim), data)
        
        # Add diagnostic fields (2D)
        ds_out[f'{domain_name}_egr'] = ((y_dim, x_dim), egr_mean)
        ds_out[f'{domain_name}_deta_dy'] = ((y_dim, x_dim), deta_dy_mean)
        ds_out[f'{domain_name}_deta_dy_zonal'] = (y_dim, deta_dy_zonal_mean)
        ds_out[f'{domain_name}_pv_ca'] = ((y_dim, x_dim), pv_ca_mean)
        ds_out[f'{domain_name}_pv_ck'] = ((y_dim, x_dim), pv_ck_mean)
        
        # Assign coordinates
        ds_out = ds_out.assign_coords({x_dim: x, y_dim: y, level_dim: levels})
        
    elif len(first_data.shape) == 2:  # (lat, lon) - e.g., single-level only
        nlat, nlon = first_data.shape
        half = domain_size / 2.0
        x = np.linspace(-half, half, nlon)
        y = np.linspace(half, -half, nlat)
        
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'
        
        for var, data in composites.items():
            ds_out[f'{domain_name}_{var}'] = ((y_dim, x_dim), data)
        
        # Add diagnostic fields
        ds_out[f'{domain_name}_egr'] = ((y_dim, x_dim), egr_mean)
        ds_out[f'{domain_name}_deta_dy'] = ((y_dim, x_dim), deta_dy_mean)
        ds_out[f'{domain_name}_deta_dy_zonal'] = (y_dim, deta_dy_zonal_mean)
        ds_out[f'{domain_name}_pv_ca'] = ((y_dim, x_dim), pv_ca_mean)
        ds_out[f'{domain_name}_pv_ck'] = ((y_dim, x_dim), pv_ck_mean)
        
        ds_out = ds_out.assign_coords({x_dim: x, y_dim: y})
    
    return ds_out


def main():
    """Main execution function with logging and progress tracking."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Precompute composites + diagnostics for EP1 cyclones',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default (auto-detect CPUs for domain parallelization)
    python step3_precompute_composites.py
    
    # Specify number of parallel domains
    python step3_precompute_composites.py --jobs 3
    
    # Run with nohup
    nohup python step3_precompute_composites.py --jobs 3 &
        """
    )
    parser.add_argument('--jobs', type=int, default=min(3, cpu_count()),
                       help='Number of domains to process in parallel (default: min(3, CPU count))')
    args = parser.parse_args()
    
    # Setup logging
    log_file = setup_logging()
    
    logging.info(f"Running with {args.jobs} parallel job(s)")
    logging.info(f"Available CPUs: {cpu_count()}")
    
    # Load cases
    logging.info("\n1. Loading EP1 cases...")
    cases_file = RESULTS_DIR / "all_ep1_cases.csv"
    if not cases_file.exists():
        logging.error(f"❌ Error: {cases_file} not found.")
        logging.error("   Please run step1_select_all_ep1.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    logging.info(f"   Found {len(cases)} cases")
    
    # Check if data files exist
    logging.info("\n2. Checking data availability...")
    available = 0
    for _, row in cases.iterrows():
        nc_file = DATA_DIR / f"{row['track_id']}_era5.nc"
        if nc_file.exists():
            available += 1
    
    logging.info(f"   Available data files: {available}/{len(cases)}")
    if available == 0:
        logging.error(f"\n❌ Error: No ERA5 files found in {DATA_DIR}")
        logging.error("   Please run step2_download_era5_parallel.py first.")
        return
    
    # Compute composites for each domain
    logging.info("\n3. Computing composites + diagnostics for all domains...")
    logging.info(f"   Processing {len(DOMAIN_SIZES)} domains: {list(DOMAIN_SIZES.keys())}")
    
    domains = list(DOMAIN_SIZES.keys())
    domain_datasets = {}
    
    if args.jobs == 1 or len(domains) == 1:
        # Sequential processing
        for domain in domains:
            logging.info(f"\n   Processing {domain} domain...")
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')
                ds_domain = compute_composites_for_domain(cases, domain)
            domain_datasets[domain] = ds_domain
    else:
        # Parallel processing of domains
        logging.info(f"   Using {args.jobs} parallel processes for domain computation")
        
        with Pool(processes=min(args.jobs, len(domains))) as pool:
            func = partial(compute_composites_for_domain, cases)
            results = []
            
            for ds_domain in tqdm(pool.imap(func, domains), 
                                 total=len(domains),
                                 desc="Processing domains"):
                results.append(ds_domain)
        
        # Store domain results
        for domain, ds_domain in zip(domains, results):
            domain_datasets[domain] = ds_domain
    
    # Save each domain to a separate file
    logging.info(f"\n4. Saving precomputed composites (one file per domain)...")
    total_size_mb = 0
    
    for domain in domains:
        output_file = DATA_DIR / f"precomputed_composites_{domain}.nc"
        logging.info(f"   Saving {domain} → {output_file.name}")
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            domain_datasets[domain].to_netcdf(output_file)
        
        file_size_mb = output_file.stat().st_size / 1024**2
        total_size_mb += file_size_mb
        logging.info(f"     ✓ {file_size_mb:.1f} MB, {len(domain_datasets[domain].data_vars)} variables")
    
    # Print summary
    logging.info("\n5. Summary:")
    logging.info(f"   Total files: {len(domains)}")
    logging.info(f"   Total size: {total_size_mb:.1f} MB")
    logging.info(f"   Domains: {domains}")
    logging.info("\n   Diagnostics computed per domain:")
    logging.info("   - EGR (Eady Growth Rate) at Ca level (975 hPa)")
    logging.info("   - ∂η/∂y (Rayleigh-Kuo gradient) at Ck level (350 hPa)")
    logging.info("   - ∂η/∂y zonal mean profile")
    logging.info("   - PV at Ca level (975 hPa)")
    logging.info("   - PV at Ck level (350 hPa)")
    
    logging.info("\n" + "=" * 80)
    logging.info("✓ STEP 3 COMPLETE")
    logging.info("=" * 80)
    logging.info(f"\nLog file: {log_file}")
    logging.info("\nNext steps:")
    logging.info("  1. Transfer to local machine:")
    logging.info(f"     rsync -avz user@server:{{remote_path}}/data/era5_ep1/precomputed_composites.nc ./data/era5_ep1/")
    logging.info("  2. Generate figures locally:")
    logging.info("     python scripts/ep1_vertical_analysis/step5_create_figures.py")


if __name__ == '__main__':
    main()
