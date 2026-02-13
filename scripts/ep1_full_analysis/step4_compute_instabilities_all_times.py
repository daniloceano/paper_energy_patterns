"""
Step 4: Compute Atmospheric Instability Diagnostics for ALL Timesteps

Computes atmospheric instability diagnostics (EGR and RK criterion) for ALL
timesteps during the intensification phase of each EP1 cyclone.

Differences from ep1_ibc_ibt_analysis/step4:
- Processes ALL timesteps (not just temporal center)
- Saves complete time series for each case
- Output: NetCDF files with temporal evolution

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
from tqdm import tqdm
import warnings

# Import instability computation functions from ep1_ibc_ibt_analysis
from ep1_ibc_ibt_analysis.step4_compute_instabilities import (
    eady_growth_rate,
    rayleigh_kuo_criterion,
    geopotential_height,
    extract_subdomain
)

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1_full"
RESULTS_DIR = BASE_DIR / "results" / "ep1_full"
OUTPUT_DIR = RESULTS_DIR / "instabilities"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Multi-scale analysis domains
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}


def compute_timeseries_for_case(track_id):
    """
    Compute instability diagnostics for ALL timesteps of a cyclone.
    
    Returns:
    --------
    success : bool
    """
    print(f"\nProcessing {track_id}...")
    
    # Load data
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    meta_file = DATA_DIR / f"{track_id}_metadata.csv"
    
    if not nc_file.exists() or not meta_file.exists():
        print("  ⚠️  Data not found")
        return False
    
    try:
        ds = xr.open_dataset(nc_file)
        meta = pd.read_csv(meta_file).iloc[0]
        
        # Get center coordinates
        center_lat = meta['track_center_lat']
        center_lon = meta['track_center_lon']
        
        # Get pressure levels
        pressure_coord = 'pressure_level' if 'pressure_level' in ds.coords else 'level'
        levels = ds[pressure_coord].values
        
        # Time coordinate
        time_coord = 'valid_time' if 'valid_time' in ds.coords else 'time'
        n_times = len(ds[time_coord])
        
        print(f"  Timesteps: {n_times}")
        print(f"  Pressure levels: {len(levels)}")
        
        # Initialize output arrays (one per domain)
        results_by_domain = {}
        
        for domain_name, domain_size in DOMAIN_SIZES.items():
            print(f"  Domain: {domain_name} ({domain_size}°)")
            
            # Initialize lists to store time series
            time_list = []
            egr_list = []
            rk_satisfied_list = []
            rk_satisfied_zonal_list = []
            
            # Loop over all timesteps
            for t_idx in range(n_times):
                ds_t = ds.isel({time_coord: t_idx})
                time_list.append(pd.to_datetime(ds_t[time_coord].values))
                
                try:
                    # Extract subdomain
                    ds_sub = extract_subdomain(ds_t, center_lat, center_lon, domain_size)
                    
                    # Build 2D lat/lon grids
                    lat_2d, lon_2d = np.meshgrid(
                        ds_sub.latitude.values,
                        ds_sub.longitude.values,
                        indexing='ij'
                    )
                    
                    # For EGR: use 3 levels near surface (950, 975, 1000 hPa)
                    # These are the levels around max Ca identified in step2_vertical_levels_analysis.py
                    lev3_ca = [950, 975, 1000]
                    available_ca = [lv for lv in lev3_ca if lv in levels]
                    
                    if len(available_ca) >= 3:
                        u3 = ds_sub['u'].sel({pressure_coord: available_ca}).values
                        v3 = ds_sub['v'].sel({pressure_coord: available_ca}).values
                        T3 = ds_sub['t'].sel({pressure_coord: available_ca}).values
                        q3 = ds_sub['q'].sel({pressure_coord: available_ca}).values
                        z3 = geopotential_height(ds_sub['z'].sel({pressure_coord: available_ca}).values)
                        p3 = np.array(available_ca) * 100.0  # Pa
                        
                        with warnings.catch_warnings():
                            warnings.filterwarnings('ignore')
                            _, egr_day, _ = eady_growth_rate(u3, v3, T3, q3, p3, z3, lat_2d)
                        
                        egr_list.append(np.nanmean(egr_day))
                    else:
                        egr_list.append(np.nan)
                    
                    # For RK: use level of minimum Ck (350 hPa)
                    # Identified in step2_vertical_levels_analysis.py
                    lev_ck = 350
                    if lev_ck in levels:
                        u_ck = ds_sub['u'].sel({pressure_coord: lev_ck}).values
                        v_ck = ds_sub['v'].sel({pressure_coord: lev_ck}).values
                        
                        with warnings.catch_warnings():
                            warnings.filterwarnings('ignore')
                            rk_sat, rk_sat_zonal, _, _, _ = rayleigh_kuo_criterion(
                                u_ck, v_ck, lat_2d, lon_2d
                            )
                        
                        rk_satisfied_list.append(1 if rk_sat else 0)
                        rk_satisfied_zonal_list.append(1 if rk_sat_zonal else 0)
                    else:
                        rk_satisfied_list.append(np.nan)
                        rk_satisfied_zonal_list.append(np.nan)
                
                except Exception as e:
                    print(f"    Warning: Error at timestep {t_idx}: {e}")
                    egr_list.append(np.nan)
                    rk_satisfied_list.append(np.nan)
                    rk_satisfied_zonal_list.append(np.nan)
            
            # Store results for this domain
            results_by_domain[domain_name] = {
                'time': time_list,
                'egr': np.array(egr_list),
                'rk_satisfied': np.array(rk_satisfied_list),
                'rk_satisfied_zonal': np.array(rk_satisfied_zonal_list)
            }
        
        # Save to NetCDF
        output_file = OUTPUT_DIR / f"{track_id}_timeseries.nc"
        ds_out = xr.Dataset()
        
        for domain_name, results in results_by_domain.items():
            time_dim = f'time_{domain_name}'
            ds_out.coords[time_dim] = pd.DatetimeIndex(results['time'])
            ds_out[f'{domain_name}_egr'] = (time_dim, results['egr'])
            ds_out[f'{domain_name}_rk_satisfied'] = (time_dim, results['rk_satisfied'])
            ds_out[f'{domain_name}_rk_satisfied_zonal'] = (time_dim, results['rk_satisfied_zonal'])
        
        # Add metadata
        ds_out.attrs['track_id'] = track_id
        ds_out.attrs['center_lat'] = center_lat
        ds_out.attrs['center_lon'] = center_lon
        ds_out.attrs['n_timesteps'] = n_times
        
        ds_out.to_netcdf(output_file)
        print(f"  ✓ Saved: {output_file}")
        
        ds.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("STEP 4: COMPUTE INSTABILITY DIAGNOSTICS FOR ALL TIMESTEPS")
    print("=" * 80)
    print(f"\nOutput: {OUTPUT_DIR}\n")
    
    # Load cases
    cases_file = RESULTS_DIR / "all_ep1_cases.csv"
    if not cases_file.exists():
        print(f"❌ Error: {cases_file} not found.")
        print("   Please run step1_select_all_ep1.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"Total cases: {len(cases)}")
    print(f"Total timesteps: {cases['n_timesteps'].sum()}\n")
    
    # Process all cases
    successful = 0
    failed = 0
    
    for idx, row in tqdm(cases.iterrows(), total=len(cases), desc="Processing cases"):
        track_id = row['track_id']
        success = compute_timeseries_for_case(track_id)
        if success:
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"✓ Processing complete!")
    print(f"  Successful: {successful}/{len(cases)}")
    print(f"  Failed: {failed}/{len(cases)}")
    print("=" * 80)
    print(f"\nNext step: python scripts/ep1_full_analysis/step5_create_figures.py")


if __name__ == '__main__':
    main()
