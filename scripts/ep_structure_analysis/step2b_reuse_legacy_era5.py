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
- Report: results/ep_structure/legacy_reuse_report.csv

USAGE:
    python scripts/ep_structure_analysis/step2b_reuse_legacy_era5.py

    Optional flags:
    --dry-run    : Only report what would be reused (don't copy files)
    --ep {1,2,3} : Only process specific EP group
    --jobs N     : Number of parallel workers (default: 10, max useful: ~100)

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

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
    if pd.isna(times_str) or not times_str:
        return []
    return [pd.to_datetime(t.strip()) for t in times_str.split(',')]


def compute_required_domain(track_id: str, selected_times: list) -> dict:
    """
    Compute the required spatial domain for central timesteps.

    Returns bounding box that must cover 30°×30° area around each selected position.
    Also includes track_center_lat and track_center_lon (middle selected timestep).

    Parameters
    ----------
    track_id : str
        Cyclone track identifier
    selected_times : list of pd.Timestamp
        Selected central timesteps

    Returns
    -------
    dict or None
        Dictionary with 'north', 'south', 'east', 'west',
        'track_center_lat', 'track_center_lon'
    """
    try:
        from scripts.utils.load_data import load_tracks
        tracks = load_tracks()
        track_data = tracks[tracks["track_id"] == track_id].copy()
        track_data["time"] = pd.to_datetime(track_data["date"])

        # Filter to selected timesteps
        track_selected = track_data[track_data["time"].isin(selected_times)]

        if len(track_selected) == 0:
            return None

        # Each position needs 15° buffer in each direction
        BUFFER = 15.0
        lats = track_selected["lat vor"].values
        lons = track_selected["lon vor"].values

        # Track center: middle of selected timesteps
        center_idx = len(track_selected) // 2
        clat = float(track_selected["lat vor"].iloc[center_idx])
        clon = float(track_selected["lon vor"].iloc[center_idx])

        return {
            'north': lats.max() + BUFFER,
            'south': lats.min() - BUFFER,
            'east': lons.max() + BUFFER,
            'west': lons.min() - BUFFER,
            'track_center_lat': clat,
            'track_center_lon': clon,
        }
    except Exception as e:
        return None


def check_spatial_coverage(legacy_file: Path, required_domain: dict, tolerance: float = 0.5) -> tuple:
    """
    Check if legacy file has sufficient spatial coverage.
    
    Parameters
    ----------
    legacy_file : Path
        Path to legacy ERA5 file
    required_domain : dict
        Required domain bounds ('north', 'south', 'east', 'west')
    tolerance : float, default=0.5
        Tolerance in degrees for domain matching
    
    Returns
    -------
    tuple (bool, str)
        (sufficient_coverage, reason)
    """
    try:
        ds = xr.open_dataset(legacy_file)
        
        # Find latitude coordinate
        lat_coord = None
        for name in ['latitude', 'lat']:
            if name in ds.coords:
                lat_coord = name
                break
        
        # Find longitude coordinate
        lon_coord = None
        for name in ['longitude', 'lon']:
            if name in ds.coords:
                lon_coord = name
                break
        
        if lat_coord is None or lon_coord is None:
            ds.close()
            return False, "Cannot find lat/lon coordinates"
        
        # Get actual domain bounds
        lats = ds[lat_coord].values
        lons = ds[lon_coord].values
        
        actual_north = lats.max()
        actual_south = lats.min()
        actual_east = lons.max()
        actual_west = lons.min()
        
        ds.close()
        
        # Check coverage with tolerance
        coverage_ok = (
            actual_north >= (required_domain['north'] - tolerance) and
            actual_south <= (required_domain['south'] + tolerance) and
            actual_east >= (required_domain['east'] - tolerance) and
            actual_west <= (required_domain['west'] + tolerance)
        )
        
        if not coverage_ok:
            reason = f"Insufficient spatial coverage: "
            reason += f"required [{required_domain['south']:.1f}°S to {required_domain['north']:.1f}°N, "
            reason += f"{required_domain['west']:.1f}°W to {required_domain['east']:.1f}°E], "
            reason += f"actual [{actual_south:.1f}°S to {actual_north:.1f}°N, "
            reason += f"{actual_west:.1f}°W to {actual_east:.1f}°E]"
            return False, reason
        
        return True, "Spatial coverage sufficient"
        
    except Exception as e:
        return False, f"Error checking spatial coverage: {str(e)}"


def check_legacy_file_compatibility(legacy_file: Path, required_times: list, track_id: str) -> dict:
    """
    Check if legacy ERA5 file is compatible with canonical methodology requirements.
    
    Checks both TEMPORAL and SPATIAL coverage.

    Returns dict with:
        - 'compatible': bool
        - 'reason': str (if not compatible)
        - 'available_times': list of available times
        - 'spatial_ok': bool
        - 'temporal_ok': bool
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
                'available_times': [],
                'temporal_ok': False,
                'spatial_ok': False,
            }

        available_times = pd.to_datetime(ds[time_dim].values)

        # ═══ TEMPORAL CHECK ═══
        # Check if all required times are present
        missing_times = []
        for req_time in required_times:
            # Allow tolerance for timestamp matching (up to 3 hours for ERA5 resolution)
            matches = [abs((at - req_time).total_seconds()) < 10800  # 3 hours
                      for at in available_times]
            if not any(matches):
                missing_times.append(req_time)

        temporal_ok = len(missing_times) == 0
        
        # ═══ SPATIAL CHECK ═══
        # Compute required domain based on selected timesteps
        required_domain = compute_required_domain(track_id, required_times)
        
        if required_domain is None:
            ds.close()
            return {
                'compatible': False,
                'reason': 'Cannot compute required domain for track',
                'available_times': available_times,
                'temporal_ok': temporal_ok,
                'spatial_ok': False,
            }
        
        spatial_ok, spatial_reason = check_spatial_coverage(legacy_file, required_domain)
        
        ds.close()
        
        # ═══ COMBINED RESULT ═══
        if not temporal_ok and not spatial_ok:
            reason = f'Missing {len(missing_times)} timesteps AND {spatial_reason}'
        elif not temporal_ok:
            reason = f'Missing {len(missing_times)} required timesteps'
        elif not spatial_ok:
            reason = spatial_reason
        else:
            reason = 'All temporal and spatial requirements met'

        return {
            'compatible': temporal_ok and spatial_ok,
            'reason': reason,
            'available_times': available_times,
            'missing_times': missing_times if not temporal_ok else [],
            'time_dim': time_dim,
            'temporal_ok': temporal_ok,
            'spatial_ok': spatial_ok,
        }

    except Exception as e:
        return {
            'compatible': False,
            'reason': f'Error reading file: {str(e)}',
            'available_times': [],
            'temporal_ok': False,
            'spatial_ok': False,
        }


def _normalize_longitude_0360_to_180(ds: "xr.Dataset") -> "xr.Dataset":
    """
    Convert longitude coordinates from 0–360 convention to -180–180.

    ERA5 files downloaded via the legacy pipeline may use 0–360 longitudes,
    while step3 expects -180–180 (matching the cyclone track data).  Without
    normalisation the OOB check in step3 (`check_subdomain_available`) will
    always fail for South-Atlantic cyclones (center_lon ≈ -50 → req_lon_min
    ≈ -65, but ds.longitude.min() ≈ 295 in 0–360 convention).

    Parameters
    ----------
    ds : xr.Dataset
        Dataset whose longitude coordinate may be in 0–360 range.

    Returns
    -------
    xr.Dataset
        Dataset with longitude coordinate in -180–180, sorted ascending.
        Returned unchanged if longitude is already in -180–180.
    """
    lon_coord = None
    for name in ("longitude", "lon"):
        if name in ds.coords:
            lon_coord = name
            break
    if lon_coord is None:
        return ds

    lons = ds[lon_coord].values
    if lons.max() > 180.0:
        # Shift: values > 180 become negative (e.g., 270 → -90)
        new_lons = (lons + 180.0) % 360.0 - 180.0
        ds = ds.assign_coords({lon_coord: new_lons})
        ds = ds.sortby(lon_coord)
    return ds


def extract_central_timesteps(legacy_file: Path, required_times: list,
                              output_file: Path, time_dim: str = 'time',
                              domain: dict = None) -> bool:
    """
    Extract central timesteps from legacy file and save to canonical location.

    Also:
    - Normalises longitude from 0–360 to -180–180 if needed (Bug 2 fix).
    - Creates a companion ``{track_id}_metadata.csv`` required by step3 (Bug 1 fix).

    Parameters
    ----------
    legacy_file : Path
    required_times : list of pd.Timestamp
    output_file : Path
        Canonical NetCDF destination (e.g. ``{track_id}_era5.nc``).
    time_dim : str
    domain : dict or None
        Spatial domain used for metadata CSV.  Keys: north, south, east, west,
        track_center_lat, track_center_lon.  If None, bounds are derived from
        the extracted subset.

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

        # ── Longitude normalisation (Bug 2 fix) ──────────────────────────────
        # Legacy files may use 0–360 convention; step3 expects -180–180.
        ds_subset = _normalize_longitude_0360_to_180(ds_subset)

        # Add metadata attributes
        ds_subset.attrs['source'] = 'Reused from legacy analysis'
        ds_subset.attrs['legacy_file'] = str(legacy_file.name)
        ds_subset.attrs['extraction_date'] = datetime.now().isoformat()
        ds_subset.attrs['canonical_methodology'] = 'Central timesteps only (April 2026)'

        # Save NetCDF
        ds_subset.to_netcdf(output_file)
        ds.close()

        # ── Create companion metadata CSV (Bug 1 fix) ─────────────────────────
        # step3._process_single_case requires {track_id}_metadata.csv to exist.
        # Without it, every legacy-reused case silently counts as "file_missing"
        # in cases_failed — the primary cause of the large failure count.
        lon_coord = "longitude" if "longitude" in ds_subset.coords else "lon"
        lat_coord = "latitude" if "latitude" in ds_subset.coords else "lat"

        if domain is not None:
            meta_north = domain.get("north", "")
            meta_south = domain.get("south", "")
            meta_east  = domain.get("east", "")
            meta_west  = domain.get("west", "")
            meta_clat  = domain.get("track_center_lat", "")
            meta_clon  = domain.get("track_center_lon", "")
        else:
            # Fallback: derive bounds from the extracted file
            meta_north = float(ds_subset[lat_coord].max()) if lat_coord in ds_subset.coords else ""
            meta_south = float(ds_subset[lat_coord].min()) if lat_coord in ds_subset.coords else ""
            meta_east  = float(ds_subset[lon_coord].max()) if lon_coord in ds_subset.coords else ""
            meta_west  = float(ds_subset[lon_coord].min()) if lon_coord in ds_subset.coords else ""
            meta_clat  = ""
            meta_clon  = ""

        ds_subset.close()

        selected_times_str = ",".join(t.isoformat() for t in required_times)
        meta_record = {
            "track_id": output_file.stem.replace("_era5", ""),
            "n_timesteps_selected": len(required_times),
            "selected_times": selected_times_str,
            "first_time": required_times[0].isoformat() if required_times else "",
            "last_time": required_times[-1].isoformat() if required_times else "",
            "north": meta_north,
            "south": meta_south,
            "east": meta_east,
            "west": meta_west,
            "track_center_lat": meta_clat,
            "track_center_lon": meta_clon,
            "methodology": "Reused from legacy - canonical April 2026",
        }
        meta_file = output_file.parent / output_file.name.replace("_era5.nc", "_metadata.csv")
        pd.DataFrame([meta_record]).to_csv(meta_file, index=False)

        return True

    except Exception as e:
        print(f"   ⚠️  Error extracting timesteps for {output_file.name}: {e}")
        return False


def _write_metadata_from_row(track_id: str, row: pd.Series,
                              required_times: list, meta_file: Path) -> None:
    """
    Create a companion metadata CSV for a canonical ERA5 file that already exists
    on disk but was produced without one (e.g. by an older version of step2b).

    Uses only data from the cases CSV row — no network calls required.

    Parameters
    ----------
    track_id : str
    row : pd.Series
        Row from ep{N}_cases.csv.  Must contain center_lat and center_lon.
    required_times : list of pd.Timestamp
        Selected central timesteps parsed from row['selected_times'].
    meta_file : Path
        Destination path for the metadata CSV.
    """
    clat = float(row['center_lat'])
    clon = float(row['center_lon'])
    BUFFER = 15.0
    selected_times_str = ",".join(t.isoformat() for t in required_times)
    meta_record = {
        "track_id": track_id,
        "n_timesteps_selected": len(required_times),
        "selected_times": selected_times_str,
        "first_time": required_times[0].isoformat() if required_times else "",
        "last_time": required_times[-1].isoformat() if required_times else "",
        "north": clat + BUFFER,
        "south": clat - BUFFER,
        "east": clon + BUFFER,
        "west": clon - BUFFER,
        "track_center_lat": clat,
        "track_center_lon": clon,
        "methodology": "Repaired metadata from cases CSV (April 2026)",
    }
    pd.DataFrame([meta_record]).to_csv(meta_file, index=False)


def _process_one_case(row: pd.Series, ep_label: str, dry_run: bool) -> tuple:
    """
    Process a single cyclone case.

    Designed to be called from a thread pool — no shared mutable state.

    Returns (result_record dict, stats_delta dict).
    """
    track_id = row['track_id']
    required_times = parse_selected_times(row['selected_times'])

    legacy_file = LEGACY_DATA_DIR / f"{track_id}_era5.nc"
    canonical_file = CANONICAL_DATA_DIR / f"{track_id}_era5.nc"
    meta_file = CANONICAL_DATA_DIR / f"{track_id}_metadata.csv"

    result = {
        'track_id': track_id,
        'ep': ep_label,
        'n_required_times': len(required_times),
        'legacy_exists': legacy_file.exists(),
        'canonical_exists': canonical_file.exists(),
        'status': '',
        'reason': ''
    }

    stats_delta = {
        'legacy_found': 0,
        'compatible': 0,
        'reused': 0,
        'repaired_metadata': 0,
        'incompatible': 0,
        'incompatible_temporal': 0,
        'incompatible_spatial': 0,
        'incompatible_both': 0,
        'not_found': 0,
        'extraction_failed': 0,
    }

    # ── Case: canonical NetCDF exists ─────────────────────────────────────────
    if canonical_file.exists():
        if meta_file.exists():
            # Fully complete: nothing to do.
            result['status'] = 'skip'
            result['reason'] = 'Already complete (NetCDF + metadata)'
            return result, stats_delta

        # NetCDF exists but metadata CSV is missing.
        # This happens when files were produced by an older version of step2b
        # that did not create the companion CSV.  Repair it now using the
        # cases CSV row data — no network call required.
        if not dry_run:
            try:
                _write_metadata_from_row(track_id, row, required_times, meta_file)
                result['status'] = 'repaired_metadata'
                result['reason'] = 'Created missing metadata CSV from cases row'
                stats_delta['repaired_metadata'] = 1
            except Exception as e:
                result['status'] = 'repair_failed'
                result['reason'] = f'Failed to write metadata: {e}'
        else:
            result['status'] = 'dry_run_needs_repair'
            result['reason'] = 'NetCDF exists but metadata CSV missing'
        return result, stats_delta

    # Check if legacy file exists
    if not legacy_file.exists():
        stats_delta['not_found'] = 1
        result['status'] = 'need_download'
        result['reason'] = 'No legacy file found'
        return result, stats_delta

    stats_delta['legacy_found'] = 1

    # Check compatibility
    compat = check_legacy_file_compatibility(legacy_file, required_times, track_id)
    result['compatible'] = compat['compatible']
    result['temporal_ok'] = compat.get('temporal_ok', False)
    result['spatial_ok'] = compat.get('spatial_ok', False)
    result['reason'] = compat['reason']

    if not compat['compatible']:
        stats_delta['incompatible'] = 1
        
        # Detailed incompatibility tracking
        temporal_ok = compat.get('temporal_ok', False)
        spatial_ok = compat.get('spatial_ok', False)
        
        if not temporal_ok and not spatial_ok:
            stats_delta['incompatible_both'] = 1
        elif not temporal_ok:
            stats_delta['incompatible_temporal'] = 1
        elif not spatial_ok:
            stats_delta['incompatible_spatial'] = 1
        
        result['status'] = 'need_download'
        return result, stats_delta

    stats_delta['compatible'] = 1

    # Extract and save (unless dry run)
    if not dry_run:
        # Compute domain for the companion metadata CSV (Bug 1 fix).
        # compute_required_domain now also returns track_center_lat/lon.
        domain = compute_required_domain(track_id, required_times)
        time_dim_to_use = compat.get('time_dim', 'time')
        success = extract_central_timesteps(
            legacy_file, required_times, canonical_file,
            time_dim_to_use, domain=domain,
        )
        if success:
            stats_delta['reused'] = 1
            result['status'] = 'reused'
        else:
            stats_delta['extraction_failed'] = 1
            result['status'] = 'extraction_failed'
    else:
        result['status'] = 'dry_run_compatible'

    return result, stats_delta


def process_ep_cases(ep_label: str, dry_run: bool = False, jobs: int = 10):
    """Process all cases for a given EP group using a thread pool."""

    cases_file = RESULTS_DIR / f"{ep_label.lower()}_cases.csv"

    if not cases_file.exists():
        print(f"\n⚠️  Cases file not found: {cases_file}")
        print(f"   Run step1_select_ep_tracks.py first!")
        return None

    df = pd.read_csv(cases_file)
    print(f"\n{'='*70}")
    print(f"{ep_label} - Processing {len(df)} eligible cyclones  (workers={jobs})")
    print(f"{'='*70}")

    stats = {
        'total': len(df),
        'legacy_found': 0,
        'compatible': 0,
        'reused': 0,
        'repaired_metadata': 0,
        'incompatible': 0,
        'incompatible_temporal': 0,
        'incompatible_spatial': 0,
        'incompatible_both': 0,
        'not_found': 0,
        'extraction_failed': 0,
    }

    reuse_details = []

    rows = [row for _, row in df.iterrows()]

    with ProcessPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(_process_one_case, row, ep_label, dry_run): row['track_id']
            for row in rows
        }
        for fut in tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"Processing {ep_label}",
        ):
            result, delta = fut.result()
            reuse_details.append(result)
            for k, v in delta.items():
                stats[k] += v

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
    parser.add_argument(
        '--jobs', '-j',
        type=int,
        default=10,
        metavar='N',
        help='Number of parallel workers (default: 10; set up to 100 for fast I/O storage)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("STEP 2b (OPTIONAL): REUSE LEGACY ERA5 DOWNLOADS")
    print("=" * 70)
    print()
    print("This is an OPERATIONAL SHORTCUT to reuse ERA5 data already")
    print("downloaded for the legacy EP1-vs-EP2 analysis.")
    print()
    print(f"Legacy data location : {LEGACY_DATA_DIR}")
    print(f"Canonical data location: {CANONICAL_DATA_DIR}")
    print(f"Parallel workers     : {args.jobs}")
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
        result = process_ep_cases(ep_label, dry_run=args.dry_run, jobs=args.jobs)
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

        if stats['repaired_metadata'] > 0 or (args.dry_run and any(
            r['status'] == 'dry_run_needs_repair'
            for r in all_details[-1].to_dict('records') if r['ep'] == ep_label
        ) if all_details else False):
            n_rep = stats['repaired_metadata']
            print(f"  ✓ Repaired missing metadata: {n_rep} ({100*n_rep/stats['total']:.1f}%)")

        print(f"  Legacy files found: {stats['legacy_found']} ({100*stats['legacy_found']/stats['total']:.1f}%)")
        print(f"  Compatible: {stats['compatible']} ({100*stats['compatible']/stats['total']:.1f}%)")

        # Detailed incompatibility breakdown
        if stats['incompatible'] > 0:
            print(f"  Incompatible: {stats['incompatible']}")
            if stats['incompatible_temporal'] > 0:
                print(f"    • Missing timesteps only: {stats['incompatible_temporal']}")
            if stats['incompatible_spatial'] > 0:
                print(f"    • Insufficient spatial coverage only: {stats['incompatible_spatial']}")
            if stats['incompatible_both'] > 0:
                print(f"    • Both temporal and spatial issues: {stats['incompatible_both']}")

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
    total_reused = (
        sum(s['reused'] for s in all_stats.values()) if not args.dry_run
        else sum(s['compatible'] for s in all_stats.values())
    )
    total_repaired = sum(s['repaired_metadata'] for s in all_stats.values())
    total_need_download = total_eligible - total_reused - total_repaired

    print(f"\nOVERALL:")
    print(f"  Total eligible cyclones: {total_eligible}")
    if total_repaired:
        print(f"  ✓ Repaired missing metadata: {total_repaired} ({100*total_repaired/total_eligible:.1f}%)")
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
