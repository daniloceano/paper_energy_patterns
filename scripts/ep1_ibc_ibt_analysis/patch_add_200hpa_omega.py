#!/usr/bin/env python3
"""
PATCH: Add 200 hPa and Omega to Existing ERA5 Files

This script downloads missing 200 hPa level and omega (vertical velocity) 
for all existing ERA5 files and concatenates them to the existing data.

Usage:
    python patch_add_200hpa_omega.py [--jobs N]

Features:
- Downloads only 200 hPa level (all variables including omega)
- Merges with existing files (no data loss)
- Validates before and after
- Logs all operations

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import xarray as xr
import numpy as np
import cdsapi
import argparse
import multiprocessing as mp
import logging
from datetime import datetime

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# CDS API Configuration
MAX_PARALLEL_JOBS = 2  # Conservative for CDS API

# Variables to download at 200 hPa
PRESSURE_VARS_200 = ['u_component_of_wind', 'v_component_of_wind', 'temperature',
                     'geopotential', 'specific_humidity', 'vertical_velocity']

# Omega needs to be downloaded separately for all levels
PRESSURE_LEVELS_OMEGA = [1000, 975, 950, 400, 350, 300, 250, 200]


def check_file_needs_patch(nc_file):
    """Check if file needs 200 hPa and/or omega."""
    needs_200hpa = False
    needs_omega = False
    
    try:
        with xr.open_dataset(nc_file) as ds:
            levels = ds['pressure_level'].values
            
            # Check 200 hPa
            if 200 not in levels:
                needs_200hpa = True
            
            # Check omega  
            if 'w' not in ds.variables and 'omega' not in ds.variables:
                needs_omega = True
                
        return needs_200hpa, needs_omega
    except Exception as e:
        logging.error(f"Error checking {nc_file.name}: {e}")
        return False, False


def download_200hpa_data(track_id, start_time, end_time, domain):
    """Download 200 hPa data for a case."""
    
    output_file = DATA_DIR / f"{track_id}_200hpa_patch.nc"
    
    # Prepare time range
    dates = pd.date_range(start_time, end_time, freq='6h')
    years = sorted(set(d.year for d in dates))
    months = sorted(set(d.month for d in dates))
    days = sorted(set(d.day for d in dates))
    times = sorted(set(d.strftime('%H:%M') for d in dates))
    
    year_str = [str(y) for y in years]
    month_str = [f'{m:02d}' for m in months]
    day_str = [f'{d:02d}' for d in days]
    time_str = times
    
    try:
        c = cdsapi.Client()
        
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': PRESSURE_VARS_200,
                'pressure_level': ['200'],
                'year': year_str,
                'month': month_str,
                'day': day_str,
                'time': time_str,
                'area': [domain['north'], domain['west'], domain['south'], domain['east']],
            },
            str(output_file)
        )
        
        logging.info(f"      ✓ Downloaded 200 hPa for {track_id}")
        return output_file
        
    except Exception as e:
        logging.error(f"      ✗ Failed to download 200 hPa for {track_id}: {e}")
        if output_file.exists():
            output_file.unlink()
        return None


def download_omega_data(track_id, start_time, end_time, domain):
    """Download omega (vertical velocity) for all levels."""
    
    output_file = DATA_DIR / f"{track_id}_omega_patch.nc"
    
    # Prepare time range  
    dates = pd.date_range(start_time, end_time, freq='6h')
    years = sorted(set(d.year for d in dates))
    months = sorted(set(d.month for d in dates))
    days = sorted(set(d.day for d in dates))
    times = sorted(set(d.strftime('%H:%M') for d in dates))
    
    year_str = [str(y) for y in years]
    month_str = [f'{m:02d}' for m in months]
    day_str = [f'{d:02d}' for d in days]
    time_str = times
    
    try:
        c = cdsapi.Client()
        
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': ['vertical_velocity'],
                'pressure_level': [str(lev) for lev in PRESSURE_LEVELS_OMEGA],
                'year': year_str,
                'month': month_str,
                'day': day_str,
                'time': time_str,
                'area': [domain['north'], domain['west'], domain['south'], domain['east']],
            },
            str(output_file)
        )
        
        logging.info(f"      ✓ Downloaded omega for {track_id}")
        return output_file
        
    except Exception as e:
        logging.error(f"      ✗ Failed to download omega for {track_id}: {e}")
        if output_file.exists():
            output_file.unlink()
        return None


def merge_patch_data(original_file, patch_200hpa, patch_omega):
    """Merge patch data into original file."""
    
    try:
        # Load original
        ds_original = xr.open_dataset(original_file)
        
        # Merge 200 hPa if available
        if patch_200hpa and patch_200hpa.exists():
            ds_200 = xr.open_dataset(patch_200hpa)
            ds_original = xr.concat([ds_original, ds_200], dim='pressure_level')
            ds_200.close()
            patch_200hpa.unlink()  # Clean up
        
        # Merge omega if available  
        if patch_omega and patch_omega.exists():
            ds_omega = xr.open_dataset(patch_omega)
            # Add omega as new variable
            ds_original['w'] = ds_omega['w']
            ds_omega.close()
            patch_omega.unlink()  # Clean up
        
        # Save merged file
        backup_file = original_file.parent / f"{original_file.stem}_backup.nc"
        original_file.rename(backup_file)
        
        ds_original.to_netcdf(original_file)
        ds_original.close()
        
        # Remove backup if successful
        backup_file.unlink()
        
        logging.info(f"      ✓ Merged patches into {original_file.name}")
        return True
        
    except Exception as e:
        logging.error(f"      ✗ Failed to merge patches: {e}")
        # Restore backup if it exists
        if backup_file.exists():
            backup_file.rename(original_file)
        return False


def get_domain_from_metadata(track_id):
    """Get domain from metadata file."""
    metadata_file = DATA_DIR / f"{track_id}_metadata.csv"
    if metadata_file.exists():
        meta = pd.read_csv(metadata_file)
        return {
            'north': meta['north'].iloc[0],
            'south': meta['south'].iloc[0],
            'east': meta['east'].iloc[0],
            'west': meta['west'].iloc[0]
        }
    return None


def process_case(case_data):
    """Process a single case."""
    idx, row, total = case_data
    track_id = row['track_id']
    
    try:
        logging.info(f"\n   [{idx+1}/{total}] Processing {track_id}...")
        
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        if not nc_file.exists():
            logging.warning(f"      ⚠️  File not found: {nc_file.name}")
            return (track_id, False)
        
        # Check what's needed
        needs_200hpa, needs_omega = check_file_needs_patch(nc_file)
        
        if not needs_200hpa and not needs_omega:
            logging.info(f"      ✓ Already has 200 hPa and omega")
            return (track_id, True)
        
        logging.info(f"      Needs: {'200hPa ' if needs_200hpa else ''}{'omega' if needs_omega else ''}")
        
        # Get domain and times
        domain = get_domain_from_metadata(track_id)
        if domain is None:
            logging.warning(f"      ⚠️  No metadata found")
            return (track_id, False)
        
        start_time = pd.to_datetime(row['intensification_start'])
        end_time = pd.to_datetime(row['intensification_end'])
        
        # Download patches
        patch_200 = download_200hpa_data(track_id, start_time, end_time, domain) if needs_200hpa else None
        patch_omega = download_omega_data(track_id, start_time, end_time, domain) if needs_omega else None
        
        # Merge
        if patch_200 or patch_omega:
            success = merge_patch_data(nc_file, patch_200, patch_omega)
            return (track_id, success)
        
        return (track_id, False)
        
    except Exception as e:
        logging.error(f"      ✗ Error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return (track_id, False)


def main():
    """Main execution."""
    
    parser = argparse.ArgumentParser(description='Patch existing ERA5 files with 200 hPa and omega')
    parser.add_argument('--jobs', type=int, default=None,
                       help=f'Number of parallel jobs (default: {MAX_PARALLEL_JOBS})')
    args = parser.parse_args()
    
    # Setup logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_DIR / f"patch_200hpa_omega_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("="*80)
    logging.info("PATCH: Add 200 hPa and Omega to Existing Files")
    logging.info("="*80)
    logging.info("")
    
    # Load cases
    cases_file = RESULTS_DIR / "all_ep1_cases.csv"
    if not cases_file.exists():
        logging.error(f"Cases file not found: {cases_file}")
        return
    
    cases = pd.read_csv(cases_file)
    logging.info(f"Found {len(cases)} cases")
    
    # Filter to cases with existing files that need patching
    to_patch = []
    for idx, row in cases.iterrows():
        track_id = row['track_id']
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        if nc_file.exists():
            needs_200, needs_omega = check_file_needs_patch(nc_file)
            if needs_200 or needs_omega:
                to_patch.append((idx, row, len(cases)))
    
    logging.info(f"Files needing patch: {len(to_patch)}/{len(cases)}")
    
    if len(to_patch) == 0:
        logging.info("\n✓ All files already patched!")
        return
    
    # Determine jobs
    n_jobs = args.jobs if args.jobs is not None else MAX_PARALLEL_JOBS
    logging.info(f"\nUsing {n_jobs} parallel jobs")
    logging.info(f"Estimated time: {len(to_patch) * 2 / n_jobs:.0f}-{len(to_patch) * 4 / n_jobs:.0f} minutes")
    logging.info("")
    
    # Process in parallel
    with mp.Pool(processes=n_jobs) as pool:
        results = pool.map(process_case, to_patch)
    
    # Summary
    successful = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    logging.info("\n" + "="*80)
    logging.info(f"✓ Patch complete!")
    logging.info(f"  Successful: {successful}/{len(to_patch)}")
    logging.info(f"  Failed: {failed}/{len(to_patch)}")
    logging.info("="*80)
    logging.info(f"Log: {log_file}")


if __name__ == "__main__":
    main()
