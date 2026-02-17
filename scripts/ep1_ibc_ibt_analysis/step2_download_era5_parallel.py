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
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
LEC_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# CDS API Configuration
# CDS API allows ~2-4 simultaneous requests per user account
# Setting conservative default to avoid rejection
MAX_PARALLEL_JOBS = 10  # Conservative limit for CDS API

# Variables to download (pressure levels)
PRESSURE_VARS = ['u_component_of_wind', 'v_component_of_wind', 'temperature', 
                 'geopotential', 'specific_humidity', 'vertical_velocity']

# Single level variables
SINGLE_LEVEL_VARS = ['mean_sea_level_pressure']

# Pressure levels (hPa) - targeted levels based on Ca/Ck analysis
# From step2_vertical_levels_analysis.py:
#   - Maximum Ca (baroclinic): 975 hPa → need 1000, 975, 950 for EGR calculation
#   - Minimum Ck (barotropic): 350 hPa → need 400, 350, 300 for diagnostics
#   - Upper-level jet: 200 hPa → for PV and wind vector overlays in plots (updated from 250)
PRESSURE_LEVELS = [
    1000, 975, 950,  # EGR calculation at 975 hPa (max Ca level)
    300, 350, 400,   # Diagnostics at 350 hPa (min Ck level)
    200, 250         # Upper-level jet for plot overlays (200=new PV level, 250=backup)
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
    missing_vars : list of str (variable names that are missing)
    missing_levels : list of int (pressure levels that are missing)
    """
    issues = []
    missing_vars = []
    missing_levels = []
    
    if not nc_file.exists():
        issues.append("File does not exist")
        return False, issues, expected_pressure_vars + expected_single_vars, expected_levels
    
    try:
        with xr.open_dataset(nc_file) as ds:
            # Check pressure-level variables
            missing_pvars = set(expected_pressure_vars) - set(ds.data_vars)
            if missing_pvars:
                issues.append(f"Missing pressure vars: {missing_pvars}")
                missing_vars.extend(missing_pvars)
            
            # Check single-level variables
            missing_svars = set(expected_single_vars) - set(ds.data_vars)
            if missing_svars:
                issues.append(f"Missing single-level vars: {missing_svars}")
                missing_vars.extend(missing_svars)
            
            # Check pressure levels (only for pressure-level vars)
            if expected_pressure_vars:
                pressure_coord = 'pressure_level' if 'pressure_level' in ds.coords else 'level'
                if pressure_coord not in ds.coords:
                    issues.append("No pressure coordinate found")
                    return False, issues, missing_vars, expected_levels
                
                actual_levels = sorted(ds[pressure_coord].values)
                expected_levels_sorted = sorted(expected_levels)
                
                if actual_levels != expected_levels_sorted:
                    missing_lvls = set(expected_levels_sorted) - set(actual_levels)
                    if missing_lvls:
                        issues.append(f"Missing levels: {missing_lvls}")
                        missing_levels.extend(sorted(missing_lvls))
            
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
        return False, issues, missing_vars, expected_levels
    
    return len(issues) == 0, issues, missing_vars, missing_levels


def check_existing_files(cases):
    """
    Check which files already exist and are valid.
    
    Returns:
    --------
    to_download : list of (idx, row) for cases needing full download
    to_patch : list of (idx, row, missing_vars, missing_levels) for cases needing completion
    valid_files : list of track_ids with valid files
    invalid_files : list of (track_id, issues) for corrupted files
    """
    print("\n   Validating existing files...")
    
    to_download = []
    to_patch = []
    valid_files = []
    invalid_files = []
    
    # Map variable names to NetCDF names
    var_map_pressure = {
        'u_component_of_wind': 'u',
        'v_component_of_wind': 'v',
        'temperature': 't',
        'geopotential': 'z',
        'specific_humidity': 'q',
        'vertical_velocity': 'w'
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
        
        valid, issues, missing_vars, missing_levels = validate_netcdf_file(
            nc_file, expected_pvars, expected_svars, PRESSURE_LEVELS
        )
        
        if valid:
            valid_files.append(track_id)
        elif missing_vars or missing_levels:
            # File exists but is incomplete - can be patched
            to_patch.append((idx, row, missing_vars, missing_levels))
        else:
            # File is corrupted - needs full re-download
            invalid_files.append((track_id, issues))
            to_download.append((idx, row))
    
    return to_download, to_patch, valid_files, invalid_files


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


def patch_era5_file(track_id, start_time, end_time, domain, missing_vars, missing_levels):
    """
    Download only missing variables/levels and merge with existing file.
    
    This is more efficient than re-downloading everything when only a few
    variables or pressure levels are missing (e.g., 200 hPa or omega).
    """
    logging.info(f"      Patching {track_id} (missing: {missing_vars if missing_vars else 'none'}, levels: {missing_levels if missing_levels else 'none'})")
    
    original_file = DATA_DIR / f"{track_id}_era5.nc"
    backup_file = DATA_DIR / f"{track_id}_era5_backup.nc"
    
    # Prepare time range
    dates = pd.date_range(start_time, end_time, freq='6h')
    years = dates.year.unique().astype(str).tolist()
    months = dates.month.unique().astype(str).tolist()
    days = dates.day.unique().astype(str).tolist()
    times = dates.strftime('%H:%M').unique().tolist()
    
    c = cdsapi.Client()
    
    try:
        # Determine what to download
        need_pressure = any(v in missing_vars for v in ['u', 'v', 't', 'z', 'q', 'w']) or missing_levels
        need_single = any(v in missing_vars for v in ['msl'])
        
        temp_files = []
        
        # Download missing pressure-level data
        if need_pressure:
            # Map back to CDS variable names
            var_map_reverse = {
                'u': 'u_component_of_wind',
                'v': 'v_component_of_wind',
                't': 'temperature',
                'z': 'geopotential',
                'q': 'specific_humidity',
                'w': 'vertical_velocity'
            }
            
            # Get CDS variable names for missing vars
            missing_cds_vars = []
            for ncvar in missing_vars:
                if ncvar in var_map_reverse:
                    missing_cds_vars.append(var_map_reverse[ncvar])
            
            # If missing levels, need to download all pressure vars for those levels
            # If missing vars, download those vars for all levels
            download_vars = missing_cds_vars if missing_cds_vars else PRESSURE_VARS
            download_levels = missing_levels if missing_levels else PRESSURE_LEVELS
            
            pressure_patch_file = DATA_DIR / f"{track_id}_patch_pressure.nc"
            temp_files.append(pressure_patch_file)
            
            logging.info(f"         -> Downloading pressure data (vars: {len(download_vars)}, levels: {len(download_levels)})...")
            c.retrieve(
                'reanalysis-era5-pressure-levels',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': download_vars,
                    'pressure_level': [str(int(p)) for p in download_levels],
                    'year': years,
                    'month': months,
                    'day': days,
                    'time': times,
                    'area': [domain['north'], domain['west'], domain['south'], domain['east']],
                },
                str(pressure_patch_file)
            )
        
        # Download missing single-level data
        if need_single:
            single_patch_file = DATA_DIR / f"{track_id}_patch_single.nc"
            temp_files.append(single_patch_file)
            
            logging.info(f"         -> Downloading single-level data...")
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
                str(single_patch_file)
            )
        
        # Merge with original file
        logging.info(f"         -> Merging with original file...")
        
        # Load original (force into memory to avoid lazy loading issues)
        ds_original = xr.open_dataset(original_file)
        ds_original.load()
        
        # Load and merge patches
        for patch_file in temp_files:
            if patch_file.exists():
                ds_patch = xr.open_dataset(patch_file)
                ds_patch.load()
                
                # If patching pressure levels, concatenate along level dimension
                if 'pressure_level' in ds_patch.dims or 'level' in ds_patch.dims:
                    level_dim = 'pressure_level' if 'pressure_level' in ds_patch.dims else 'level'
                    ds_original = xr.concat([ds_original, ds_patch], dim=level_dim)
                    # Sort by pressure level
                    ds_original = ds_original.sortby(level_dim)
                else:
                    # Merge new variables
                    ds_original = xr.merge([ds_original, ds_patch])
                
                ds_patch.close()
        
        # Create backup
        original_file.rename(backup_file)
        
        # Save merged file
        ds_original.to_netcdf(original_file)
        ds_original.close()
        
        # Clean up
        for f in temp_files:
            if f.exists():
                f.unlink()
        
        if backup_file.exists():
            backup_file.unlink()
        
        logging.info(f"      ✓ Patched: {original_file}")
        return True
        
    except Exception as e:
        logging.error(f"      ❌ Patch failed for {track_id}: {e}")
        # Restore backup if it exists
        if backup_file.exists():
            backup_file.rename(original_file)
        # Clean up temp files
        for f in temp_files:
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


def process_patch_wrapper(case_data):
    """
    Wrapper function for patching incomplete files.
    Returns: (track_id, success)
    """
    idx, row, missing_vars, missing_levels, total = case_data
    track_id = row['track_id']
    
    try:
        logging.info(f"\n   [{idx+1}/{total}] Patching {track_id}...")
        
        start_time = pd.to_datetime(row['intensification_start'])
        end_time = pd.to_datetime(row['intensification_end'])
        
        # Get domain from metadata if exists, otherwise compute
        metadata_file = DATA_DIR / f"{track_id}_metadata.csv"
        if metadata_file.exists():
            meta = pd.read_csv(metadata_file).iloc[0]
            domain = {
                'north': meta['north'],
                'south': meta['south'],
                'east': meta['east'],
                'west': meta['west'],
                'track_center_lat': meta['track_center_lat'],
                'track_center_lon': meta['track_center_lon']
            }
        else:
            domain = compute_domain_bounds(track_id, start_time, end_time)
            if domain is None:
                logging.warning(f"      ⚠️  Could not compute domain bounds")
                return (track_id, False)
        
        # Patch file
        success = patch_era5_file(track_id, start_time, end_time, domain, missing_vars, missing_levels)
        return (track_id, success)
        
    except Exception as e:
        logging.error(f"      ❌ Error patching {track_id}: {e}")
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
    to_download, to_patch, valid_files, invalid_files = check_existing_files(cases)
    
    logging.info(f"\n   File status:")
    logging.info(f"      ✓ Complete: {len(valid_files)}/{len(cases)}")
    logging.info(f"      🔧 Incomplete (patchable): {len(to_patch)}/{len(cases)}")
    logging.info(f"      ⚠️  Missing/corrupted: {len(to_download)}/{len(cases)}")
    
    if invalid_files:
        logging.warning(f"\n   Found {len(invalid_files)} corrupted/incomplete files:")
        for track_id, issues in invalid_files[:5]:
            logging.warning(f"      {track_id}: {'; '.join(issues)}")
        if len(invalid_files) > 5:
            logging.warning(f"      ... and {len(invalid_files)-5} more")
        logging.warning("\n   These files will be re-downloaded.")
    
    if to_patch:
        logging.info(f"\n   Files to patch (missing data):")
        # Group by what's missing
        missing_summary = {}
        for _, _, mvars, mlevels in to_patch:
            key = (tuple(sorted(mvars)), tuple(sorted(mlevels)))
            missing_summary[key] = missing_summary.get(key, 0) + 1
        
        for (mvars, mlevels), count in sorted(missing_summary.items(), key=lambda x: -x[1]):
            mvars_str = f"{list(mvars)}" if mvars else "none"
            mlevels_str = f"{list(mlevels)}" if mlevels else "none"
            logging.info(f"      {count} files: vars={mvars_str}, levels={mlevels_str}")
    
    if len(to_download) == 0 and len(to_patch) == 0:
        logging.info("\n   ✓ All files are valid and complete!")
        _print_completeness_report(cases)
        logging.info(f"\n   Next step: python scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py")
        return
    
    logging.info(f"\n   Files to download/patch: {len(to_download) + len(to_patch)}/{len(cases)}")
    
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
    
    start_time = time.time()
    results = []
    successful_patches = 0
    successful_downloads = 0
    
    # STEP 1: Patch incomplete files first (faster)
    if to_patch:
        logging.info(f"\n3a. Patching {len(to_patch)} incomplete files...")
        logging.info(f"    Estimated time: {len(to_patch) * 1 / n_jobs:.0f}-{len(to_patch) * 3 / n_jobs:.0f} minutes")
        logging.info("")
        
        to_patch_with_total = [(idx, row, mvars, mlevels, len(to_patch)) 
                               for idx, row, mvars, mlevels in to_patch]
        
        with mp.Pool(processes=n_jobs) as pool:
            patch_results = pool.map(process_patch_wrapper, to_patch_with_total)
        
        results.extend(patch_results)
        
        successful_patches = sum(1 for _, success in patch_results if success)
        logging.info(f"\n   Patching complete: {successful_patches}/{len(to_patch)} successful")
    
    # STEP 2: Download missing files (slower)
    if to_download:
        logging.info(f"\n3b. Downloading {len(to_download)} missing/corrupted files...")
        logging.info(f"    Estimated time: {len(to_download) * 3 / n_jobs:.0f}-{len(to_download) * 5 / n_jobs:.0f} minutes")
        logging.info("")
        
        to_download_with_total = [(idx, row, len(to_download)) for idx, row in to_download]
        
        with mp.Pool(processes=n_jobs) as pool:
            download_results = pool.map(process_case_wrapper, to_download_with_total)
        
        results.extend(download_results)
        
        successful_downloads = sum(1 for _, success in download_results if success)
        logging.info(f"\n   Downloads complete: {successful_downloads}/{len(to_download)} successful")
    
    elapsed = time.time() - start_time
    
    # Count successes and failures
    successful = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    logging.info("\n" + "=" * 80)
    logging.info(f"✓ Processing complete! (elapsed: {elapsed/60:.1f} min)")
    logging.info(f"  Already complete: {len(valid_files)}")
    logging.info(f"  Patched: {successful_patches}/{len(to_patch) if to_patch else 0}")
    logging.info(f"  Downloaded: {successful_downloads}/{len(to_download) if to_download else 0}")
    logging.info(f"  Failed: {failed}")
    logging.info(f"  Total valid: {len(valid_files) + successful}/{len(cases)}")
    if successful > 0:
        logging.info(f"  Average time per case: {elapsed/successful:.1f} seconds")
    
    # Generate completeness report
    _print_completeness_report(cases)
    
    if len(valid_files) + successful == len(cases):
        logging.info(f"\n  ✓ All files ready!")
        logging.info(f"  Next step: python scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py")
    elif failed > 0:
        logging.warning(f"\n  ⚠️  Some operations failed. Re-run this script to retry.")
        logging.warning(f"     If failures persist due to CDS API limits, try: --jobs 2")
    
    logging.info("=" * 80)
    logging.info(f"Log file saved: {log_file}")


def _print_completeness_report(cases):
    """Generate and print a completeness report for all files."""
    logging.info("\n" + "=" * 80)
    logging.info("COMPLETENESS REPORT")
    logging.info("=" * 80)
    
    var_map_pressure = {
        'u': 'u_component_of_wind',
        'v': 'v_component_of_wind',
        't': 'temperature',
        'z': 'geopotential',
        'q': 'specific_humidity',
        'w': 'vertical_velocity (omega)'
    }
    var_map_single = {
        'msl': 'mean_sea_level_pressure (SLP)'
    }
    
    expected_pvars = list(var_map_pressure.keys())
    expected_svars = list(var_map_single.keys())
    
    var_counts = {var: 0 for var in expected_pvars + expected_svars}
    level_counts = {lev: 0 for lev in PRESSURE_LEVELS}
    total_valid = 0
    
    for _, row in cases.iterrows():
        track_id = row['track_id']
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        
        if not nc_file.exists():
            continue
            
        try:
            with xr.open_dataset(nc_file) as ds:
                # Count variables
                for var in expected_pvars + expected_svars:
                    if var in ds.data_vars:
                        var_counts[var] += 1
                
                # Count levels
                pressure_coord = 'pressure_level' if 'pressure_level' in ds.coords else 'level'
                if pressure_coord in ds.coords:
                    actual_levels = ds[pressure_coord].values
                    for lev in PRESSURE_LEVELS:
                        if lev in actual_levels:
                            level_counts[lev] += 1
                
                # Check if complete
                all_vars = all(var in ds.data_vars for var in expected_pvars + expected_svars)
                all_levels = all(lev in ds[pressure_coord].values for lev in PRESSURE_LEVELS) if pressure_coord in ds.coords else False
                if all_vars and all_levels:
                    total_valid += 1
        except:
            pass
    
    logging.info(f"\nVariable Completeness ({len(cases)} total files):")
    logging.info(f"  Pressure-level variables:")
    for var, count in sorted(var_counts.items()):
        if var in var_map_pressure:
            full_name = var_map_pressure[var]
            pct = count / len(cases) * 100
            status = "✓" if count == len(cases) else f"{pct:.0f}%"
            logging.info(f"    {var:3s} ({full_name:30s}): {count:3d}/{len(cases)} [{status}]")
    
    logging.info(f"\n  Single-level variables:")
    for var, count in sorted(var_counts.items()):
        if var in var_map_single:
            full_name = var_map_single[var]
            pct = count / len(cases) * 100
            status = "✓" if count == len(cases) else f"{pct:.0f}%"
            logging.info(f"    {var:3s} ({full_name:30s}): {count:3d}/{len(cases)} [{status}]")
    
    logging.info(f"\nPressure Level Completeness:")
    for lev in sorted(PRESSURE_LEVELS, reverse=True):
        count = level_counts[lev]
        pct = count / len(cases) * 100
        status = "✓" if count == len(cases) else f"{pct:.0f}%"
        logging.info(f"    {lev:4d} hPa: {count:3d}/{len(cases)} [{status}]")
    
    pct_complete = total_valid / len(cases) * 100
    logging.info(f"\nOverall: {total_valid}/{len(cases)} files 100% complete ({pct_complete:.1f}%)")
    logging.info("=" * 80)


if __name__ == "__main__":
    main()
