"""
Step 2b (OPTIONAL): Reuse Legacy ERA5 Downloads for Eligible Cyclones

This is an OPERATIONAL SHORTCUT to avoid re-downloading ERA5 data that was
already downloaded for the legacy EP1-vs-EP2 analysis.

PURPOSE:
- Reuse existing ERA5 files from data/era5_ep_structure_legacy/ when possible
- Extract only the CENTRAL TIMESTEPS required by the new canonical methodology
- Save substantial download time for EP1 and EP2 cyclones

IMPORTANT:
- This is NOT required for the canonical pipeline
- The canonical flow is: step1 → step2 → step3 → ...
- This script is ONLY a time-saving shortcut when legacy data exists

CANONICAL vs LEGACY DIFFERENCES:
1. Legacy: Downloaded full intensification phase
2. Canonical: Only uses central 2-3 timesteps
3. Legacy: Included cyclones with < 24h intensification
4. Canonical: Only cyclones with >= 24h intensification

STRATEGY:
- Check if legacy ERA5 file exists for each eligible cyclone
- Verify the file contains the required central timesteps
- Extract and save only those timesteps to canonical location
- Report what was reused vs what needs fresh download

OUTPUT:
- Reused files: data/era5_ep_structure/{track_id}_era5.nc (canonical format)
- Report: results/ep_structure/legacy_reuse_report.txt

USAGE:
    python scripts/ep_structure_analysis/step2b_reuse_legacy_era5.py
    
    Optional flags:
    --dry-run    : Only report what would be reused (don't copy files)
    --ep {1,2,3} : Only process specific EP group

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path
import argparse

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import xarray as xr
from datetime import datetime
from tqdm import tqdm

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure_legacy"
CANONICAL_DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
CANONICAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


def parse_selected_times(times_str: str) -> list:
    """Parse selected_times CSV column into list of datetime objects."""
    return [pd.to_datetime(t) for t in times_str.split(',')]


def check_legacy_file_compatibility(legacy_file: Path, required_times: list) -> dict:
    """
    Check if legacy ERA5 file contains required timesteps.
    
    Returns dict with:
        - 'compatible': bool
        - 'reason': str (if not compatible)
        - 'available_times': list of available times
    """
    try:
        ds = xr.open_dataset(legacy_file)
        
        # Check for time dimension (could be 'time' or 'valid_time')
        time_dim = None
        if 'time' in ds.dims:
            time_dim = 'time'
        elif 'valid_time' in ds.dims:
            time_dim = 'valid_time'
        else:
            return {
                'compatible': False,
                'reason': 'No time dimension found',
                'available_times': []
            }
        
        available_times = pd.to_datetime(ds[time_dim].values)
        
        # Check if all required times are present
        missing_times = []
        for req_time in required_times:
            # Allow tolerance for timestamp matching (up to 3 hours for ERA5 resolution)
            matches = [abs((at - req_time).total_seconds()) < 10800  # 3 hours
                      for at in available_times]
            if not any(matches):
                missing_times.append(req_time)
        
        if missing_times:
            return {
                'compatible': False,
                'reason': f'Missing {len(missing_times)} required timesteps',
                'available_times': available_times,
                'missing_times': missing_times
            }
        
        ds.close()
        
        return {
            'compatible': True,
            'reason': 'All required timesteps available',
            'available_times': available_times,
            'time_dim': time_dim
        }
        
    except Exception as e:
        return {
            'compatible': False,
            'reason': f'Error reading file: {str(e)}',
            'available_times': []
        }


def extract_central_timesteps(legacy_file: Path, required_times: list, 
                              output_file: Path, time_dim: str = 'time') -> bool:
    """
    Extract central timesteps from legacy file and save to canonical location.
    
    Returns True if successful, False otherwise.
    """
    try:
        ds = xr.open_dataset(legacy_file)
        
        # Detect time dimension if not provided
        if time_dim not in ds.dims:
            if 'valid_time' in ds.dims:
                time_dim = 'valid_time'
            elif 'time' in ds.dims:
                time_dim = 'time'
            else:
                return False
        
        available_times = pd.to_datetime(ds[time_dim].values)
        
        # Find indices of required times (with tolerance)
        selected_indices = []
        for req_time in required_times:
            time_diffs = [abs((at - req_time).total_seconds()) 
                         for at in available_times]
            closest_idx = time_diffs.index(min(time_diffs))
            if time_diffs[closest_idx] < 10800:  # Within 3 hours
                selected_indices.append(closest_idx)
        
        # Extract subset
        ds_subset = ds.isel({time_dim: selected_indices})
        
        # Rename time dimension to standard 'time' if needed
        if time_dim != 'time':
            ds_subset = ds_subset.rename({time_dim: 'time'})
        
        # Add metadata
        ds_subset.attrs['source'] = 'Reused from legacy analysis'
        ds_subset.attrs['legacy_file'] = str(legacy_file.name)
        ds_subset.attrs['extraction_date'] = datetime.now().isoformat()
        ds_subset.attrs['canonical_methodology'] = 'Central timesteps only (April 2026)'
        
        # Save
        ds_subset.to_netcdf(output_file)
        ds.close()
        ds_subset.close()
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Error extracting timesteps: {e}")
        return False


def process_ep_cases(ep_label: str, dry_run: bool = False):
    """Process all cases for a given EP group."""
    
    cases_file = RESULTS_DIR / f"{ep_label.lower()}_cases.csv"
    
    if not cases_file.exists():
        print(f"\n⚠️  Cases file not found: {cases_file}")
        print(f"   Run step1_select_ep_tracks.py first!")
        return None
    
    df = pd.read_csv(cases_file)
    print(f"\n{'='*70}")
    print(f"{ep_label} - Processing {len(df)} eligible cyclones")
    print(f"{'='*70}")
    
    stats = {
        'total': len(df),
        'legacy_found': 0,
        'compatible': 0,
        'reused': 0,
        'incompatible': 0,
        'not_found': 0,
        'extraction_failed': 0
    }
    
    reuse_details = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {ep_label}"):
        track_id = row['track_id']
        required_times = parse_selected_times(row['selected_times'])
        
        # Check for legacy file
        legacy_file = LEGACY_DATA_DIR / f"{track_id}_era5.nc"
        canonical_file = CANONICAL_DATA_DIR / f"{track_id}_era5.nc"
        
        result = {
            'track_id': track_id,
            'ep': ep_label,
            'n_required_times': len(required_times),
            'legacy_exists': legacy_file.exists(),
            'canonical_exists': canonical_file.exists(),
            'status': '',
            'reason': ''
        }
        
        # Skip if already exists in canonical location
        if canonical_file.exists():
            result['status'] = 'skip'
            result['reason'] = 'Already exists in canonical location'
            reuse_details.append(result)
            continue
        
        # Check if legacy file exists
        if not legacy_file.exists():
            stats['not_found'] += 1
            result['status'] = 'need_download'
            result['reason'] = 'No legacy file found'
            reuse_details.append(result)
            continue
        
        stats['legacy_found'] += 1
        
        # Check compatibility
        compat = check_legacy_file_compatibility(legacy_file, required_times)
        result['compatible'] = compat['compatible']
        result['reason'] = compat['reason']
        
        if not compat['compatible']:
            stats['incompatible'] += 1
            result['status'] = 'need_download'
            reuse_details.append(result)
            continue
        
        stats['compatible'] += 1
        
        # Extract and save (unless dry run)
        if not dry_run:
            time_dim_to_use = compat.get('time_dim', 'time')
            success = extract_central_timesteps(legacy_file, required_times, 
                                               canonical_file, time_dim_to_use)
            if success:
                stats['reused'] += 1
                result['status'] = 'reused'
            else:
                stats['extraction_failed'] += 1
                result['status'] = 'extraction_failed'
        else:
            result['status'] = 'dry_run_compatible'
        
        reuse_details.append(result)
    
    return stats, pd.DataFrame(reuse_details)


def main():
    parser = argparse.ArgumentParser(
        description="Reuse legacy ERA5 downloads for canonical analysis"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Only report what would be reused (no file operations)'
    )
    parser.add_argument(
        '--ep',
        type=str,
        choices=['1', '2', '3', 'all'],
        default='all',
        help='Process specific EP group (default: all)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("STEP 2b (OPTIONAL): REUSE LEGACY ERA5 DOWNLOADS")
    print("=" * 70)
    print()
    print("This is an OPERATIONAL SHORTCUT to reuse ERA5 data already")
    print("downloaded for the legacy EP1-vs-EP2 analysis.")
    print()
    print(f"Legacy data location: {LEGACY_DATA_DIR}")
    print(f"Canonical data location: {CANONICAL_DATA_DIR}")
    print()
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE: No files will be copied/modified")
        print()
    
    if not LEGACY_DATA_DIR.exists():
        print(f"❌ Legacy data directory not found: {LEGACY_DATA_DIR}")
        print("   Nothing to reuse. Use step2_download_era5_parallel.py instead.")
        return
    
    # Determine which EPs to process
    if args.ep == 'all':
        ep_labels = ['EP1', 'EP2', 'EP3']
    else:
        ep_labels = [f'EP{args.ep}']
    
    # Process each EP
    all_stats = {}
    all_details = []
    
    for ep_label in ep_labels:
        result = process_ep_cases(ep_label, dry_run=args.dry_run)
        if result is not None:
            stats, details_df = result
            all_stats[ep_label] = stats
            all_details.append(details_df)
    
    # Combine all details
    if all_details:
        combined_details = pd.concat(all_details, ignore_index=True)
    else:
        print("\n❌ No cases processed")
        return
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for ep_label, stats in all_stats.items():
        print(f"\n{ep_label}:")
        print(f"  Total eligible cyclones: {stats['total']}")
        print(f"  Legacy files found: {stats['legacy_found']} ({100*stats['legacy_found']/stats['total']:.1f}%)")
        print(f"  Compatible: {stats['compatible']} ({100*stats['compatible']/stats['total']:.1f}%)")
        
        if not args.dry_run:
            print(f"  ✓ Successfully reused: {stats['reused']}")
            print(f"  ✗ Extraction failed: {stats['extraction_failed']}")
        else:
            print(f"  Would reuse: {stats['compatible']}")
        
        need_download = stats['not_found'] + stats['incompatible']
        if not args.dry_run:
            need_download += stats['extraction_failed']
        print(f"  Need fresh download: {need_download}")
    
    # Overall summary
    total_eligible = sum(s['total'] for s in all_stats.values())
    total_reused = sum(s['reused'] for s in all_stats.values()) if not args.dry_run else sum(s['compatible'] for s in all_stats.values())
    total_need_download = total_eligible - total_reused
    
    print(f"\nOVERALL:")
    print(f"  Total eligible cyclones: {total_eligible}")
    if not args.dry_run:
        print(f"  ✓ Reused from legacy: {total_reused} ({100*total_reused/total_eligible:.1f}%)")
    else:
        print(f"  Could reuse: {total_reused} ({100*total_reused/total_eligible:.1f}%)")
    print(f"  Need fresh download: {total_need_download} ({100*total_need_download/total_eligible:.1f}%)")
    
    # Save detailed report
    report_file = RESULTS_DIR / "legacy_reuse_report.csv"
    combined_details.to_csv(report_file, index=False)
    print(f"\n✓ Detailed report saved: {report_file}")
    
    # Always print EP3 coverage note (legacy analysis only covered EP1/EP2)
    print()
    print("=" * 70)
    print("NOTE ON EP3 COVERAGE")
    print("=" * 70)
    print("  ⚠  This script CANNOT reuse EP3 cases.")
    print("     Reason: the legacy analysis only covered EP1 and EP2.")
    print("     EP3 has zero legacy ERA5 files available for reuse.")
    print("     All EP3 cases (and any missing EP1/EP2 cases) must be")
    print("     downloaded via step2_download_era5_parallel.py.")
    print()
    print("  To download remaining cases:")
    print("    python scripts/ep_structure_analysis/step2_download_era5_parallel.py --jobs 10")
    print()
    print("  To monitor reuse progress:")
    print("    python scripts/ep_structure_analysis/step2_monitor.py --mode reuse")

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN. Run without --dry-run to actually reuse files.")
    else:
        print("\n✓ Legacy reuse complete!")


if __name__ == "__main__":
    main()
