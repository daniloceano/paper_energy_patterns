"""
Step 4: Compute Atmospheric Instability Diagnostics (EGR and RK)

This script implements the computation of two fundamental atmospheric instability
diagnostics for EP1 cyclones during their intensification phase, following
established theoretical frameworks and best practices in dynamic meteorology.

EADY GROWTH RATE (EGR) - Baroclinic Instability Diagnostic
RAYLEIGH-KUO (RK) CRITERION - Barotropic Instability Diagnostic

For complete scientific documentation, see README.md

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
from tqdm import tqdm
import warnings

# MetPy for meteorological calculations
from metpy.calc import virtual_temperature, potential_temperature
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

# Directories
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
OUTPUT_DIR = RESULTS_DIR / "instabilities"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Multi-scale analysis domains
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}

print(f"\n{'='*80}")
print("ATMOSPHERIC INSTABILITY DIAGNOSTICS")
print(f"{'='*80}")
print(f"Output: {OUTPUT_DIR}")


def coriolis_parameter(lat):
    """Coriolis: f = 2Ω sin(φ)"""
    return 2.0 * OMEGA * np.sin(np.deg2rad(lat))


def geopotential_height(geopotential):
    """Convert Φ (m² s⁻²) to Z (m): Z = Φ/g"""
    return geopotential / G


def virtual_temperature_field(T, q):
    """
    Virtual temperature: Tv = T(1 + 0.61q)
    Accounts for moisture effect on density.
    Uses MetPy for accurate calculation.
    """
    Tv = virtual_temperature(T * units.kelvin, q * units('kg/kg'))
    return Tv.magnitude


def virtual_potential_temperature_field(T, q, p):
    """Virtual potential temperature: θv = Tv(p₀/p)^κ
    Uses MetPy for accurate calculation.
    """
    Tv = virtual_temperature_field(T, q)
    theta_v = potential_temperature(p * units.pascal, Tv * units.kelvin)
    return theta_v.magnitude


def brunt_vaisala_frequency(T, q, p, z):
    """
    Brunt-Väisälä frequency: N² = (g/θv)(∂θv/∂z)
    
    Uses centered finite differences with 3 vertical levels.
    Returns N (s⁻¹) and N² (s⁻²).
    """
    # Compute θv at 3 levels
    theta_v = np.array([
        virtual_potential_temperature_field(T[i], q[i], p[i])
        for i in range(3)
    ])
    
    # Centered difference: ∂θv/∂z
    dtheta_v = theta_v[0] - theta_v[2]  # upper - lower
    dz = z[0] - z[2]                    # should be positive
    
    # Safe division
    dz_safe = np.where(np.abs(dz) > 1.0, dz, np.nan)
    dtheta_v_dz = dtheta_v / dz_safe
    
    # N² = (g/θv)(∂θv/∂z)
    N_squared = (G / theta_v[1]) * dtheta_v_dz
    N = np.where(N_squared > MIN_N_SQUARED, np.sqrt(N_squared), np.nan)
    
    return N, N_squared, theta_v[1]


def vertical_wind_shear(u, v, z):
    """
    Vertical wind shear: |∂V/∂z| = √[(∂u/∂z)² + (∂v/∂z)²]
    
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
    """
    Eady Growth Rate: σ = 0.31 × (|f|/N) × |∂V/∂z|
    
    Returns:
    --------
    egr : EGR in s⁻¹
    egr_day : EGR in day⁻¹ (standard unit for reporting)
    diagnostics : dict with component fields
    """
    # Components
    f = np.abs(coriolis_parameter(lat))
    N, N_sq, theta_v = brunt_vaisala_frequency(T, q, p, z)
    shear, du_dz, dv_dz = vertical_wind_shear(u, v, z)
    
    # EGR calculation with quality control
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        egr = np.where(
            (N > 0) & (np.abs(lat) > MIN_LAT),
            0.31 * (f / N) * shear,
            np.nan
        )
    
    # Convert to day⁻¹
    egr_day = egr * 86400.0
    egr_day = np.where(egr_day > MAX_EGR_DAY, np.nan, egr_day)
    
    return egr, egr_day, {'f': f, 'N': N, 'N_sq': N_sq, 'shear': shear,
                          'du_dz': du_dz, 'dv_dz': dv_dz, 'theta_v': theta_v}


def relative_vorticity(u, v, lat, lon):
    """
    Relative vorticity: ζ = ∂v/∂x - ∂u/∂y
    
    Uses spherical coordinate metric factors.
    """
    dlat = np.gradient(lat, axis=0)
    dlon = np.gradient(lon, axis=1)
    
    dx = R_EARTH * np.cos(np.deg2rad(lat)) * np.deg2rad(dlon)
    dy = R_EARTH * np.deg2rad(dlat)
    
    dv_dx = np.gradient(v, axis=1) / dx
    du_dy = np.gradient(u, axis=0) / dy
    
    return dv_dx - du_dy


def rayleigh_kuo_criterion(u, v, lat, lon):
    """
    Rayleigh-Kuo criterion: ∂η/∂y must change sign
    where η = ζ + f is absolute vorticity.
    
    Checks criterion in two ways:
    1. Full 2D field (local variations)
    2. Zonal mean (large-scale meridional structure)
    
    Returns:
    --------
    satisfied : bool, True if criterion met in 2D field
    satisfied_zonal : bool, True if criterion met in zonal mean
    deta_dy : meridional gradient of absolute vorticity (2D)
    deta_dy_zonal : zonal-mean meridional gradient
    diagnostics : dict with statistics
    """
    # Components
    zeta = relative_vorticity(u, v, lat, lon)
    f = coriolis_parameter(lat)
    eta = zeta + f
    
    # Meridional gradient (2D)
    dlat = np.gradient(lat, axis=0)
    dy = R_EARTH * np.deg2rad(dlat)
    deta_dy = np.gradient(eta, axis=0) / dy
    
    # Check sign change in 2D field
    valid = deta_dy[~np.isnan(deta_dy)]
    if len(valid) > 0:
        min_g, max_g = np.min(valid), np.max(valid)
        satisfied = (min_g < 0) and (max_g > 0)
        frac_neg = np.sum(valid < 0) / len(valid)
    else:
        min_g, max_g, satisfied, frac_neg = np.nan, np.nan, False, 0.0
    
    # Zonal mean analysis
    eta_zonal = np.nanmean(eta, axis=1)  # Average over longitude
    deta_dy_zonal = np.gradient(eta_zonal) / dy[:, 0]  # Use first column of dy
    
    # Check sign change in zonal mean
    valid_zonal = deta_dy_zonal[~np.isnan(deta_dy_zonal)]
    if len(valid_zonal) > 0:
        min_g_zonal = np.min(valid_zonal)
        max_g_zonal = np.max(valid_zonal)
        satisfied_zonal = (min_g_zonal < 0) and (max_g_zonal > 0)
    else:
        min_g_zonal, max_g_zonal, satisfied_zonal = np.nan, np.nan, False
    
    return satisfied, satisfied_zonal, deta_dy, deta_dy_zonal, {
        'zeta': zeta, 'f': f, 'eta': eta,
        'min': min_g, 'max': max_g, 'frac_neg': frac_neg,
        'min_zonal': min_g_zonal, 'max_zonal': max_g_zonal,
        'eta_zonal': eta_zonal, 'deta_dy_zonal_profile': deta_dy_zonal
    }


def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """
    Extract subdomain centered on cyclone.
    Interpolates to fixed grid to ensure all domains have same dimensions.
    
    Grid resolution: 0.25° (ERA5 native resolution)
    Ensures consistent grid size across all cyclones.
    """
    from scipy.interpolate import griddata
    
    half = domain_size / 2.0
    
    # Define target grid with fixed resolution
    resolution = 0.25  # ERA5 resolution
    n_points = int(domain_size / resolution) + 1
    
    # Create regular grid centered on cyclone
    lat_target = np.linspace(center_lat + half, center_lat - half, n_points)
    lon_target = np.linspace(center_lon - half, center_lon + half, n_points)
    
    # Extract larger region from original data
    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1)
    )
    
    # Interpolate each variable to target grid
    ds_interp = xr.Dataset()
    ds_interp.coords['latitude'] = lat_target
    ds_interp.coords['longitude'] = lon_target
    
    for var in ['u', 'v', 't', 'z', 'q']:
        if var in ds_sub:
            data_interp = ds_sub[var].interp(
                latitude=lat_target,
                longitude=lon_target,
                method='linear'
            )
            ds_interp[var] = data_interp
    
    return ds_interp


def compute_for_case(track_id):
    """Main computation for one cyclone case"""
    print(f"\nCase {track_id}:")
    
    # Load data
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    meta_file = DATA_DIR / f"{track_id}_metadata.csv"
    
    if not nc_file.exists() or not meta_file.exists():
        print("  ⚠️  Data not found")
        return False
    
    ds = xr.open_dataset(nc_file)
    meta = pd.read_csv(meta_file).iloc[0]
    
    # Center coordinates (from temporal center of intensification phase)
    # This is the actual track point closest to t_center, not a spatial mean
    center_lat = meta['track_center_lat']
    center_lon = meta['track_center_lon']
    levels_hpa = eval(meta['pressure_levels_hPa'])
    
    # Temporal center index in downloaded data
    t_idx = len(ds.valid_time) // 2
    ds_t = ds.isel(valid_time=t_idx)
    print(f"  Time: {ds.valid_time[t_idx].values}")
    print(f"  Levels: {levels_hpa} hPa")
    
    results = {'track_id': track_id, 'time': str(ds.valid_time[t_idx].values),
               'center_lat': center_lat, 'center_lon': center_lon}
    
    # Multi-scale analysis
    for domain_name, domain_size in DOMAIN_SIZES.items():
        print(f"  {domain_name} ({domain_size}°):")
        
        ds_sub = extract_subdomain(ds_t, center_lat, center_lon, domain_size)
        lat_2d, lon_2d = np.meshgrid(
            ds_sub.latitude.values, ds_sub.longitude.values, indexing='ij'
        )
        
        # EGR (needs 3 levels)
        if len(levels_hpa) >= 3:
            lev3 = levels_hpa[:3]
            u3 = ds_sub['u'].sel(pressure_level=lev3).values
            v3 = ds_sub['v'].sel(pressure_level=lev3).values
            T3 = ds_sub['t'].sel(pressure_level=lev3).values
            q3 = ds_sub['q'].sel(pressure_level=lev3).values
            z3 = geopotential_height(ds_sub['z'].sel(pressure_level=lev3).values)
            p3 = np.array(lev3) * 100.0  # Pa
            
            egr_s, egr_d, egr_diag = eady_growth_rate(u3, v3, T3, q3, p3, z3, lat_2d)
            
            results[f'egr_{domain_name}_mean'] = np.nanmean(egr_d)
            results[f'egr_{domain_name}_max'] = np.nanmax(egr_d)
            results[f'N_{domain_name}'] = np.nanmean(egr_diag['N'])
            results[f'shear_{domain_name}'] = np.nanmean(egr_diag['shear'])
            
            print(f"    EGR: {np.nanmean(egr_d):.3f} day⁻¹ (max: {np.nanmax(egr_d):.3f})")
        
        # RK (single level)
        lev_mid = levels_hpa[len(levels_hpa)//2]
        u_rk = ds_sub['u'].sel(pressure_level=lev_mid).values
        v_rk = ds_sub['v'].sel(pressure_level=lev_mid).values
        
        rk_sat, rk_sat_zonal, deta, deta_zonal, rk_diag = rayleigh_kuo_criterion(u_rk, v_rk, lat_2d, lon_2d)
        
        results[f'rk_{domain_name}_satisfied'] = rk_sat
        results[f'rk_{domain_name}_satisfied_zonal'] = rk_sat_zonal
        results[f'rk_{domain_name}_min'] = rk_diag['min']
        results[f'rk_{domain_name}_max'] = rk_diag['max']
        results[f'rk_{domain_name}_min_zonal'] = rk_diag['min_zonal']
        results[f'rk_{domain_name}_max_zonal'] = rk_diag['max_zonal']
        
        rk_status = 'YES' if rk_sat else 'NO'
        rk_status_zonal = 'YES' if rk_sat_zonal else 'NO'
        rk_min = rk_diag['min']
        rk_max = rk_diag['max']
        print(f"    RK 2D: {rk_status} (∂η/∂y: [{rk_min:.2e}, {rk_max:.2e}])")
        print(f"    RK Zonal: {rk_status_zonal} (∂η/∂y: [{rk_diag['min_zonal']:.2e}, {rk_diag['max_zonal']:.2e}])")
    
    # Save
    output = OUTPUT_DIR / f"{track_id}_instabilities.csv"
    pd.DataFrame([results]).to_csv(output, index=False)
    print(f"  ✓ Saved: {output.name}")
    
    return True


def main():
    print(f"\n{'='*80}")
    print("STEP 4: COMPUTE INSTABILITY DIAGNOSTICS")
    print(f"{'='*80}\n")
    
    # Load cases
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print("❌ Error: selected_cases.csv not found")
        print("   Run step1_select_cases.py first")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"Processing {len(cases)} EP1 cyclones\n")
    
    # Process
    success = sum(compute_for_case(row['track_id']) for _, row in cases.iterrows())
    
    print(f"\n{'='*80}")
    print(f"✓ Complete: {success}/{len(cases)} cases")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
