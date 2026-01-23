"""
Step 1: Prepare Track Files for LorenzCycleToolkit

This script converts selected EP1 cyclone tracks to LorenzCycleToolkit input format.

Prerequisites:
- Run scripts/ep1_ibc_ibt_analysis/step1_select_cases.py first
- This creates results/ep1_vertical/selected_cases.csv with selected EP1 cyclones

Input:
- results/ep1_vertical/selected_cases.csv - Selected EP1 cyclones
- Main track database (via load_tracks())

Output Format (one file per cyclone):
    time;Lat;Lon
    2005-08-08-0000;-22.5;-45.0
    2005-08-08-0600;-23.0;-44.5
    ...

File naming: track_{track_id}.txt
Output directory: data/ck_analysis/tracks/

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from scripts.utils.load_data import load_tracks

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
SELECTED_CASES_FILE = BASE_DIR / "results" / "ep1_vertical" / "selected_cases.csv"
OUTPUT_DIR = BASE_DIR / "data" / "ck_analysis" / "tracks"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_datetime_for_lec(dt):
    """
    Format datetime for LorenzCycleToolkit input.
    
    Format: YYYY-MM-DD-HHMM (no spaces, dash before time)
    Example: 2005-08-08-0000
    
    Args:
        dt: pandas Timestamp
        
    Returns:
        Formatted string
    """
    return dt.strftime('%Y-%m-%d-%H%M')


def create_track_file(track_id, tracks_df, output_dir):
    """
    Create track file in LorenzCycleToolkit format for a single cyclone.
    
    The track data is resampled to 3-hourly intervals (00, 03, 06, 09, 12, 15, 18, 21)
    to match ERA5 data availability.
    
    Args:
        track_id: Cyclone track ID
        tracks_df: Full tracks dataframe
        output_dir: Directory to save track file
        
    Returns:
        True if successful, False otherwise
    """
    # Filter track data for this cyclone
    track_data = tracks_df[tracks_df['track_id'] == track_id].copy()
    
    if len(track_data) == 0:
        print(f"   ⚠ Warning: No track data found for {track_id}")
        return False, 0
    
    # Convert date to datetime if not already
    track_data['date'] = pd.to_datetime(track_data['date'])
    
    # Sort by date to ensure temporal order
    track_data = track_data.sort_values('date')
    
    # Resample to 3-hourly intervals (ERA5 standard times: 00, 03, 06, 09, 12, 15, 18, 21)
    # Round each timestamp to the nearest 3-hour interval
    track_data['date_3h'] = track_data['date'].dt.floor('3h')
    
    # Remove duplicates (keep first occurrence at each 3-hour interval)
    track_data = track_data.drop_duplicates(subset=['date_3h'], keep='first')
    
    # Use the rounded 3-hourly timestamps
    track_data['date'] = track_data['date_3h']
    
    # Format for LorenzCycleToolkit: time;Lat;Lon (capitalized, Lat before Lon)
    # Important: Use 'lat vor' and 'lon vor' (vorticity center coordinates)
    output_lines = ['time;Lat;Lon']
    
    for _, row in track_data.iterrows():
        time_str = format_datetime_for_lec(row['date'])
        lat = row['lat vor']
        lon = row['lon vor']
        
        # Format: time;Lat;Lon (semicolon delimiter, capitalized)
        output_lines.append(f"{time_str};{lat};{lon}")
    
    # Write to file
    output_file = output_dir / f"track_{track_id}.txt"
    with open(output_file, 'w') as f:
        f.write('\n'.join(output_lines))
    
    return True, len(track_data)


def main():
    """Prepare track files for all selected EP1 cyclones."""
    
    print("=" * 80)
    print("STEP 1: Preparing Track Files for LorenzCycleToolkit")
    print("=" * 80)
    
    # Check if selected cases file exists
    if not SELECTED_CASES_FILE.exists():
        print(f"\n❌ Error: Selected cases file not found: {SELECTED_CASES_FILE}")
        print("\nPlease run scripts/ep1_ibc_ibt_analysis/step1_select_cases.py first.")
        print("This will create the required file with selected EP1 cyclones.")
        return 1
    
    # Load selected cases
    print(f"\n1. Loading selected cases...")
    selected_cases = pd.read_csv(SELECTED_CASES_FILE)
    print(f"   Found {len(selected_cases)} selected EP1 cyclones")
    
    # Load full track database
    print(f"\n2. Loading full track database...")
    tracks = load_tracks()
    print(f"   Loaded {tracks['track_id'].nunique()} unique tracks")
    print(f"   Total track points: {len(tracks)}")
    
    # Create track files for each selected cyclone
    print(f"\n3. Creating track files in LorenzCycleToolkit format...")
    print(f"   Output directory: {OUTPUT_DIR}")
    print(f"\n   Format:")
    print(f"   - Delimiter: semicolon (;)")
    print(f"   - Header: time;Lat;Lon (capitalized)")
    print(f"   - Time format: YYYY-MM-DD-HHMM")
    print(f"   - Coordinates: vorticity center (lat vor, lon vor)")
    print(f"   - Temporal resolution: 3-hourly (resampled to ERA5 times)")
    print(f"   - Valid hours: 00, 03, 06, 09, 12, 15, 18, 21")
    
    successful = 0
    failed = []
    
    for idx, row in selected_cases.iterrows():
        track_id = row['track_id']
        print(f"\n   [{idx+1}/{len(selected_cases)}] Processing {track_id}...")
        
        # Get track points for this cyclone
        track_points = tracks[tracks['track_id'] == track_id]
        n_points_original = len(track_points)
        
        if n_points_original == 0:
            print(f"      ⚠ No track data found")
            failed.append(track_id)
            continue
        
        # Get lifecycle info
        start_date = track_points['date'].min()
        end_date = track_points['date'].max()
        duration_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        
        print(f"      Original track points: {n_points_original}")
        print(f"      Duration: {duration_days} days")
        print(f"      Period: {start_date} to {end_date}")
        
        # Create track file (resampled to 3-hourly)
        result = create_track_file(track_id, tracks, OUTPUT_DIR)
        
        if result and result[0]:
            success, n_points_3h = result
            output_file = OUTPUT_DIR / f"track_{track_id}.txt"
            print(f"      Resampled to 3-hourly: {n_points_3h} points")
            print(f"      ✓ Created: {output_file}")
            successful += 1
        else:
            print(f"      ❌ Failed to create track file")
            failed.append(track_id)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nSuccessfully created: {successful}/{len(selected_cases)} track files")
    
    if failed:
        print(f"\nFailed to create track files for {len(failed)} cyclones:")
        for track_id in failed:
            print(f"   - {track_id}")
    
    if successful > 0:
        print(f"\n✓ Track files saved to: {OUTPUT_DIR}")
        print(f"\nNext step:")
        print(f"   Run step2_run_lec_toolkit.py to compute Lorenz Energy Cycle")
        print(f"   with full term decomposition using LorenzCycleToolkit")
    
    print("\n" + "=" * 80)
    
    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
