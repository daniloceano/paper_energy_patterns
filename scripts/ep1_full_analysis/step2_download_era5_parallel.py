"""
Step 2: Download ERA5 Data in Parallel for ALL EP1 Cyclones

Downloads ERA5 reanalysis data for all EP1 cyclones during their entire
intensification phase. Includes all standard pressure levels and SLP.

Features:
- Parallel downloads (customizable --jobs N, default = CPUs - 1)
- Includes Mean Sea Level Pressure (SLP/MSLP)
- All intensification timesteps (not just central time)
- Validation of existing files
- Automatic retry of failed downloads

Variables Downloaded:
- Pressure levels: u, v, t, z, q
- Single level: msl (mean sea level pressure)

Targeted Pressure Levels (hPa):
1000, 975, 950    → EGR at 975 hPa (maximum Ca level)
400, 350, 300     → Diagnostics at 350 hPa (minimum Ck level)
250               → Upper-level jet for plot overlays

Total: 7 levels (based on Ca/Ck vertical analysis)

Author: Danilo Couto de Souza  
Date: February 2026
"""

import sys
from pathlib import Path
import argparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime
import cdsapi
import multiprocessing as mp
from functools import partial
import time
import logging

from scripts.utils.load_data import load_tracks

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1_full"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_full"
LEC_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# CDS API Configuration
# CDS API allows ~2-4 simultaneous requests per user account
# Setting conservative default to avoid rejection
MAX_PARALLEL_JOBS = 10  # Conservative limit for CDS API

# Variables to download (pressure levels)
PRESSURE_VARS = ['u_component_of_wind', 'v_component_of_wind', 'temperature', 
                 'geopotential', 'specific_humidity']

# Single level variables
SINGLE_LEVEL_VARS = ['mean_sea_level_pressure']

# Pressure levels (hPa) - targeted levels based on Ca/Ck analysis
# From step2_vertical_levels_analysis.py:
#   - Maximum Ca (baroclinic): 975 hPa → need 1000, 975, 950 for EGR calculation
#   - Minimum Ck (barotropic): 350 hPa → need 400, 350, 300 for diagnostics
#   - Upper-level jet: 250 hPa → for PV and wind vector overlays in plots
PRESSURE_LEVELS = [
    1000, 975, 950,  # EGR calculation at 975 hPa (max Ca level)
    300, 350, 400,   # Diagnostics at 350 hPa (min Ck level)
    250              # Upper-level jet for plot overlays
]

# Domain buffer (degrees) - allows 30°×30° analysis
DOMAIN_BUFFER = 15


def validate_netcdf_file(nc_file, expected_pressure_vars, expected_single_vars, expected_levels):
    """
    Validate NetCDF file integrity and completeness.
    
    Returns:
    --------
    valid : bool
    issues : list of str (problems found)
    """
    issues = []
    
    if not nc_file.exists():
        issues.append("File does not exist")
        return False, issues
    
    try:
        with xr.open_dataset(nc_file) as ds:
            # Check pressure-level variables
            missing_pvars = set(expected_pressure_vars) - set(ds.data_vars)
            if missing_pvars:
                issues.append(f"Missing pressure vars: {missing_pvars}")
            
            # Check single-level variables
            missing_svars = set(expected_single_vars) - set(ds.data_vars)
            if missing_svars:
                issues.append(f"Missing single-level vars: {missing_svars}")
            
            # Check pressure levels (only for pressure-level vars)
            if expected_pressure_vars:
                pressure_coord = 'pressure_level' if 'pressure_level' in ds.coords else 'level'
                if pressure_coord not in ds.coords:
                    issues.append("No pressure coordinate found")
                    return False, issues
                
                actual_levels = sorted(ds[pressure_coord].values)
                expected_levels_sorted = sorted(expected_levels)
                
                if actual_levels != expected_levels_sorted:
                    missing_levels = set(expected_levels_sorted) - set(actual_levels)
                    if missing_levels:
                        issues.append(f"Missing levels: {missing_levels}")
            
            # Check for excessive NaN values (>50% indicates corruption)
            for var in list(expected_pressure_vars) + list(expected_single_vars):
                if var in ds.data_vars:
                    data = ds[var].values
                    nan_fraction = np.isnan(data).sum() / data.size
                    if nan_fraction > 0.5:
                        issues.append(f"{var}: {nan_fraction*100:.1f}% NaN (corrupted?)")
            
            # Check temporal dimension
            time_coord = 'valid_time' if 'valid_time' in ds.coords else 'time'
            if time_coord in ds.coords and len(ds[time_coord]) == 0:
                issues.append("No time steps found")
    
    except Exception as e:
        issues.append(f"Failed to open/read file: {e}")
        return False, issues
    
    return len(issues) == 0, issues


def check_existing_files(cases):
    """
    Check which files already exist and are valid.
    
    Returns:
    --------
    to_download : list of (idx, row) for cases needing download
    valid_files : list of track_ids with valid files
    invalid_files : list of (track_id, issues) for corrupted files
    """
    print("\n   Validating existing files...")
    
    to_download = []
    valid_files = []
    invalid_files = []
    
    # Map variable names to NetCDF names
    var_map_pressure = {
        'u_component_of_wind': 'u',
        'v_component_of_wind': 'v',
        'temperature': 't',
        'geopotential': 'z',
        'specific_humidity': 'q'
    }
    var_map_single = {
        'mean_sea_level_pressure': 'msl'
    }
    
    expected_pvars = list(var_map_pressure.values())
    expected_svars = list(var_map_single.values())
    
    for idx, row in cases.iterrows():
        track_id = row['track_id']
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        
        if not nc_file.exists():
            to_download.append((idx, row))
            continue
        
        valid, issues = validate_netcdf_file(nc_file, expected_pvars, expected_svars, PRESSURE_LEVELS)
        
        if valid:
            valid_files.append(track_id)
        else:
            invalid_files.append((track_id, issues))
            to_download.append((idx, row))
    
    return to_download, valid_files, invalid_files


def compute_domain_bounds(track_id, start_time, end_time):
    """Compute spatial domain bounds for a cyclone during intensification."""
    
    # Load track data
    tracks = load_tracks()
    
    # Filter for this cyclone during intensification
    track_data = tracks[tracks['track_id'] == track_id].copy()
    track_data['time'] = pd.to_datetime(track_data['date'])
    track_intensification = track_data[
        (track_data['time'] >= start_time) & 
        (track_data['time'] <= end_time)
    ]
    
    if len(track_intensification) == 0:
        return None
    
    # Find temporal center (consistent with step1)
    t_center = start_time + (end_time - start_time) / 2
    time_diffs = np.abs((track_intensification['time'] - t_center).dt.total_seconds())
    closest_idx = time_diffs.idxmin()
    center_lat = track_intensification.loc[closest_idx, 'lat vor']
    center_lon = track_intensification.loc[closest_idx, 'lon vor']
    
    # Compute track extent
    min_lat = track_intensification['lat vor'].min()
    max_lat = track_intensification['lat vor'].max()
    min_lon = track_intensification['lon vor'].min()
    max_lon = track_intensification['lon vor'].max()
    
    # Add buffer
    domain = {
        'north': min(90, max_lat + DOMAIN_BUFFER),
        'south': max(-90, min_lat - DOMAIN_BUFFER),
        'east': max_lon + DOMAIN_BUFFER,
        'west': min_lon - DOMAIN_BUFFER,
        'track_center_lat': center_lat,
        'track_center_lon': center_lon
    }
    
    return domain


def download_era5_for_case(track_id, start_time, end_time, domain):
    """Download ERA5 data (pressure levels + SLP) for a single case."""
    
    logging.info(f"      Downloading ERA5 data for {track_id}")
    logging.info(f"         Period: {start_time} to {end_time}")
    logging.info(f"         Domain: [{domain['south']:.1f}, {domain['west']:.1f}] to [{domain['north']:.1f}, {domain['east']:.1f}]")
    
    # Prepare time range (6-hourly data)
    dates = pd.date_range(start_time, end_time, freq='6h')  # lowercase 'h' (pandas 2.0+)
    years = dates.year.unique().astype(str).tolist()
    months = dates.month.unique().astype(str).tolist()
    days = dates.day.unique().astype(str).tolist()
    times = dates.strftime('%H:%M').unique().tolist()
    
    # Initialize CDS API client
    c = cdsapi.Client()
    
    # Output files
    pressure_file = DATA_DIR / f"{track_id}_era5_pressure.nc"
    single_file = DATA_DIR / f"{track_id}_era5_single.nc"
    output_file = DATA_DIR / f"{track_id}_era5.nc"
    
    try:
        # Download pressure-level data
        logging.info(f"      -> Downloading pressure levels...")
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': PRESSURE_VARS,
                'pressure_level': [str(int(p)) for p in PRESSURE_LEVELS],
                'year': years,
                'month': months,
                'day': days,
                'time': times,
                'area': [domain['north'], domain['west'], domain['south'], domain['east']],
            },
            str(pressure_file)
        )
        
        # Download single-level data (SLP)
        logging.info(f"      -> Downloading single-level (SLP)...")
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': SINGLE_LEVEL_VARS,
                'year': years,
                'month': months,
                'day': days,
                'time': times,
                'area': [domain['north'], domain['west'], domain['south'], domain['east']],
            },
            str(single_file)
        )
        
        # Merge both files into one
        logging.info(f"      -> Merging files...")
        ds_pressure = xr.open_dataset(pressure_file)
        ds_single = xr.open_dataset(single_file)
        ds_merged = xr.merge([ds_pressure, ds_single])
        ds_merged.to_netcdf(output_file)
        ds_pressure.close()
        ds_single.close()
        
        # Remove temporary files
        pressure_file.unlink()
        single_file.unlink()
        
        logging.info(f"      ✓ Downloaded: {output_file}")
        
        # Save metadata
        metadata = {
            'track_id': track_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'north': domain['north'],
            'south': domain['south'],
            'east': domain['east'],
            'west': domain['west'],
            'track_center_lat': domain['track_center_lat'],
            'track_center_lon': domain['track_center_lon'],
            'pressure_levels_hPa': PRESSURE_LEVELS,
            'pressure_variables': PRESSURE_VARS,
            'single_level_variables': SINGLE_LEVEL_VARS
        }
        
        metadata_file = DATA_DIR / f"{track_id}_metadata.csv"
        pd.DataFrame([metadata]).to_csv(metadata_file, index=False)
        
        return True
        
    except Exception as e:
        logging.error(f"      ❌ Download failed for {track_id}: {e}")
        # Clean up partial files
        for f in [pressure_file, single_file, output_file]:
            if f.exists():
                f.unlink()
        return False


def process_case_wrapper(case_data):
    """
    Wrapper function for parallel processing.
    Returns: (track_id, success)
    """
    idx, row, total = case_data
    track_id = row['track_id']
    
    try:
        logging.info(f"\n   [{idx+1}/{total}] Processing {track_id}...")
        
        start_time = pd.to_datetime(row['intensification_start'])
        end_time = pd.to_datetime(row['intensification_end'])
        logging.info(f"      Intensification: {start_time} to {end_time}")
        
        # Compute domain bounds
        domain = compute_domain_bounds(track_id, start_time, end_time)
        if domain is None:
            logging.warning(f"      ⚠️  Could not compute domain bounds")
            return (track_id, False)
        
        # Download data
        success = download_era5_for_case(track_id, start_time, end_time, domain)
        return (track_id, success)
        
    except Exception as e:
        logging.error(f"      ❌ Error processing {track_id}: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return (track_id, False)


def main():
    """Download ERA5 data for all EP1 cases in parallel."""
    
    parser = argparse.ArgumentParser(description='Download ERA5 data in parallel')
    parser.add_argument('--jobs', type=int, default=None,
                       help=f'Number of parallel jobs (default: {MAX_PARALLEL_JOBS}, max recommended: 2-4 for CDS API)')
    parser.add_argument('--log-file', type=str, default=None,
                       help='Log file path (default: logs/step2_download_YYYYMMDD_HHMMSS.log)')
    args = parser.parse_args()
    
    # Setup logging
    if args.log_file:
        log_file = Path(args.log_file)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = LOG_DIR / f"step2_download_{timestamp}.log"
    
    # Configure logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Log file: {log_file}")
    
    logging.info("=" * 80)
    logging.info("STEP 2: Downloading ERA5 Data in Parallel (ALL EP1 CYCLONES)")
    logging.info("=" * 80)
    logging.info("")
    logging.info("NOTE: This script requires:")
    logging.info("  1. step1_select_all_ep1.py to be run first")
    logging.info("  2. CDS API key setup (https://cds.climate.copernicus.eu)")
    logging.info("  3. ~/.cdsapirc file configured")
    logging.info("")
    
    # Load cases
    logging.info("1. Loading EP1 cases...")
    cases_file = RESULTS_DIR / "all_ep1_cases.csv"
    if not cases_file.exists():
        logging.error(f"❌ Error: {cases_file} not found.")
        logging.error("   Please run step1_select_all_ep1.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    logging.info(f"   Found {len(cases)} cases to process")
    logging.info(f"   Total timesteps to download: {cases['n_timesteps'].sum()}")
    
    # Create output directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check existing files
    to_download, valid_files, invalid_files = check_existing_files(cases)
    
    logging.info(f"\n   Valid files: {len(valid_files)}/{len(cases)}")
    
    if invalid_files:
        logging.warning(f"\n   ⚠️  Found {len(invalid_files)} corrupted/incomplete files:")
        for track_id, issues in invalid_files[:5]:
            logging.warning(f"      {track_id}: {'; '.join(issues)}")
        if len(invalid_files) > 5:
            logging.warning(f"      ... and {len(invalid_files)-5} more")
        logging.warning("\n   These files will be re-downloaded.")
    
    if len(to_download) == 0:
        logging.info("\n   ✓ All files are valid and complete!")
        logging.info(f"\n   Next step: python scripts/ep1_full_analysis/step3_precompute_composites.py")
        return
    
    logging.info(f"\n   Files to download: {len(to_download)}/{len(cases)}")
    
    # Determine number of parallel jobs
    # CDS API constraint: ~2-4 simultaneous requests per user
    n_jobs = args.jobs if args.jobs is not None else MAX_PARALLEL_JOBS
    if n_jobs > 4:
        logging.warning(f"   ⚠️  Warning: {n_jobs} parallel jobs may exceed CDS API limits (recommended: 2-4)")
        logging.warning(f"      You may experience request rejections. Consider using --jobs 2")
    
    logging.info(f"\n2. Download configuration:")
    logging.info(f"   Pressure variables: {', '.join(PRESSURE_VARS)}")
    logging.info(f"   Single-level variables: {', '.join(SINGLE_LEVEL_VARS)}")
    logging.info(f"   Pressure levels: {PRESSURE_LEVELS}")
    logging.info(f"   Domain buffer: {DOMAIN_BUFFER}° (allows 30°×30° analysis)")
    logging.info(f"   Temporal resolution: 6-hourly")
    logging.info(f"   Parallel jobs: {n_jobs} (CDS API limit: 2-4 recommended)")
    logging.info(f"   Output directory: {DATA_DIR}")
    
    logging.info(f"\n3. Starting parallel downloads ({n_jobs} workers)...")
    logging.info(f"   Cases to download: {len(to_download)}")
    logging.info(f"   Estimated time: {len(to_download) * 3 / n_jobs:.0f}-{len(to_download) * 5 / n_jobs:.0f} minutes (rough estimate)")
    logging.info("")
    
    start_time = time.time()
    
    # Add total count to case data for progress tracking
    to_download_with_total = [(idx, row, len(to_download)) for idx, row in to_download]
    
    # Process in parallel (but CDS API may throttle)
    # Note: CDS has rate limits, so actual parallelism may be limited by server
    with mp.Pool(processes=n_jobs) as pool:
        results = pool.map(process_case_wrapper, to_download_with_total)
    
    elapsed = time.time() - start_time
    
    # Count successes and failures
    successful = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    logging.info("\n" + "=" * 80)
    logging.info(f"✓ Download complete! (elapsed: {elapsed/60:.1f} min)")
    logging.info(f"  Already valid: {len(valid_files)}")
    logging.info(f"  Downloaded now: {successful}/{len(to_download)}")
    logging.info(f"  Failed: {failed}/{len(to_download)}")
    logging.info(f"  Total valid: {len(valid_files) + successful}/{len(cases)}")
    logging.info(f"  Average time per download: {elapsed/max(1, successful):.1f} seconds")
    
    if len(valid_files) + successful == len(cases):
        logging.info(f"\n  ✓ All files ready!")
        logging.info(f"  Next step: python scripts/ep1_full_analysis/step3_precompute_composites.py")
    elif failed > 0:
        logging.warning(f"\n  ⚠️  Some downloads failed. Re-run this script to retry.")
        logging.warning(f"     If failures persist due to CDS API limits, try: --jobs 2")
    
    logging.info("=" * 80)
    logging.info(f"Log file saved: {log_file}")


if __name__ == "__main__":
    main()
