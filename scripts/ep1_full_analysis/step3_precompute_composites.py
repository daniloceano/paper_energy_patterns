"""
Step 3: Precompute Composites for ALL Variables

Precomputes spatial composites (domain-mean) for all downloaded variables
to avoid reprocessing in subsequent analyses.

This step:
- Reads all ERA5 files downloaded in step2
- Computes composites for ALL pressure levels and ALL variables
- Saves results in a single NetCDF file for fast access
- Includes SLP (mean sea level pressure)

Output:
- data/era5_ep1_full/precomputed_composites.nc

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

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1_full"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_full"

# Domain sizes for composites
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}
RESOLUTION = 0.25


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
    Compute composite means for all variables and all levels for a given domain.
    
    Returns:
    --------
    ds_out : xarray.Dataset with composites
        Contains variables like: u_all, v_all, t_all, z_all, q_all, msl_all
        Dimensions: (level, y_<domain>, x_<domain>) or (y_<domain>, x_<domain>) for SLP
    """
    domain_size = DOMAIN_SIZES[domain_name]
    
    # Initialize lists to accumulate data
    var_lists = {}
    
    print(f"\n   Processing {domain_name} domain ({domain_size}°)...")
    
    for idx, row in cases.iterrows():
        track_id = row['track_id']
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        meta_file = DATA_DIR / f"{track_id}_metadata.csv"
        
        if not nc_file.exists() or not meta_file.exists():
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
            
            # Accumulate all variables
            for var in ds_mean.data_vars:
                if var not in var_lists:
                    var_lists[var] = []
                var_lists[var].append(ds_mean[var].values)
            
            ds.close()
            
        except Exception as e:
            print(f"      Warning: Error processing {track_id}: {e}")
            continue
    
    if not var_lists:
        raise RuntimeError(f"No valid cases found for domain {domain_name}")
    
    print(f"      Processed {len(var_lists[list(var_lists.keys())[0]])} cases")
    
    # Compute means
    composites = {}
    for var, data_list in var_lists.items():
        composites[var] = np.nanmean(np.stack(data_list), axis=0)
    
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
        
        ds_out = ds_out.assign_coords({x_dim: x, y_dim: y})
    
    return ds_out


def main():
    print("=" * 80)
    print("STEP 3: PRECOMPUTE COMPOSITES FOR ALL VARIABLES")
    print("=" * 80)
    
    # Load cases
    print("\n1. Loading EP1 cases...")
    cases_file = RESULTS_DIR / "all_ep1_cases.csv"
    if not cases_file.exists():
        print(f"❌ Error: {cases_file} not found.")
        print("   Please run step1_select_all_ep1.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"   Found {len(cases)} cases")
    
    # Check if data files exist
    print("\n2. Checking data availability...")
    available = 0
    for _, row in cases.iterrows():
        nc_file = DATA_DIR / f"{row['track_id']}_era5.nc"
        if nc_file.exists():
            available += 1
    
    print(f"   Available data files: {available}/{len(cases)}")
    if available == 0:
        print(f"\n❌ Error: No ERA5 files found in {DATA_DIR}")
        print("   Please run step2_download_era5_parallel.py first.")
        return
    
    # Compute composites for each domain
    print("\n3. Computing composites for all domains...")
    domains = list(DOMAIN_SIZES.keys())
    
    ds_all = xr.Dataset()
    
    for domain in domains:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            ds_domain = compute_composites_for_domain(cases, domain)
        ds_all = xr.merge([ds_all, ds_domain])
    
    # Save output
    output_file = DATA_DIR / "precomputed_composites.nc"
    print(f"\n4. Saving precomputed composites...")
    ds_all.to_netcdf(output_file)
    print(f"   ✓ Saved: {output_file}")
    
    # Print summary
    print("\n5. Summary:")
    print(f"   Variables: {list(ds_all.data_vars.keys())[:10]}...")
    print(f"   File size: {output_file.stat().st_size / 1024**2:.1f} MB")
    print(f"   Domains: {domains}")
    
    print("\n" + "=" * 80)
    print("STEP 3 COMPLETE")
    print("=" * 80)
    print(f"\nNext step: python scripts/ep1_full_analysis/step4_compute_instabilities_all_times.py")


if __name__ == '__main__':
    main()
