"""
Step 2: Download ERA5 Data for Selected Cases

This script downloads ERA5 reanalysis data for the selected EP1 cyclones
during their intensification phase at the critical pressure levels identified
in step3.

NOTE: This script should be run AFTER step3_vertical_levels_analysis.py
which identifies the critical pressure levels for Ca (BcI) and Ck (BtI).

Required Variables for Diagnostics:
- u, v: Zonal and meridional wind (for vorticity in RK criterion and wind shear for EGR)
- t: Temperature (for Brunt-Väisälä frequency in EGR)
- z: Geopotential height (for vertical derivatives in EGR)

Pressure Levels:
- Ca maximum level + level above and below (for EGR - needs vertical differences)
- Ck minimum level + level above and below (for RK criterion)

Spatial Domain:
- Track extent during intensification phase + 15° buffer on all sides
- Allows for 30°×30° analysis (largest domain)

Temporal Coverage:
- Entire intensification phase (6-hourly data)
- Central time step identified for instability analysis

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import cdsapi
import multiprocessing as mp
from functools import partial

from scripts.utils.load_data import load_tracks

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
LEC_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

# Variables to download
# For Rayleigh-Kuo (RK) criterion: u, v (to compute vorticity)
# For Eady Growth Rate (EGR): u, v, t, z, q (for wind shear, static stability with moisture)
#   - q (specific_humidity): needed to compute virtual temperature (Tv) for accurate 
#     static stability calculation incorporating moisture effects on density
VARIABLES = ['u_component_of_wind', 'v_component_of_wind', 'temperature', 'geopotential', 'specific_humidity']

# Domain buffer (degrees)
# Single domain per cyclone: track extent + this buffer on all sides
DOMAIN_BUFFER = 15  # Allows for 30°×30° analysis (largest domain)

# Domain buffer (degrees)
# Single domain per cyclone: track extent + this buffer on all sides
DOMAIN_BUFFER = 15  # Allows for 30°×30° analysis (largest domain)


def load_critical_levels():
    """Load identified critical pressure levels from step3."""
    
    levels_file = RESULTS_DIR / "critical_levels.csv"
    if not levels_file.exists():
        print(f"❌ Error: {levels_file} not found.")
        print("   Please run step3_vertical_levels_analysis.py first.")
        return None
    
    levels_df = pd.read_csv(levels_file)
    
    # Extract unique pressure levels
    pressure_levels = sorted(levels_df['pressure_level_hPa'].unique())
    
    return pressure_levels, levels_df


def get_intensification_phase_info(track_id):
    """Get intensification phase times and track extent."""
    
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = lec_dir / "periods.csv" / "periods.csv"
    
    if not periods_file.exists():
        return None
    
    periods = pd.read_csv(periods_file, index_col=0)
    intensification = periods.loc['intensification']
    
    if len(intensification) == 0:
        return None
    
    start_time = pd.to_datetime(intensification['start'])
    end_time = pd.to_datetime(intensification['end'])
    
    return start_time, end_time


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
    
    # Find actual track point at temporal center (consistent with step1 and step5)
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


def process_case_wrapper(case_data, pressure_levels):
    """
    Wrapper function for parallel processing.
    Returns: (track_id, success)
    """
    idx, row = case_data
    track_id = row['track_id']
    
    try:
        print(f"\n   [{idx+1}] Processing {track_id}...")
        
        # Get intensification phase times
        lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
        periods_file = lec_dir / "periods.csv" / "periods.csv"
        
        if not periods_file.exists():
            print(f"      ⚠️  No intensification phase found")
            return (track_id, False)
        
        periods = pd.read_csv(periods_file, index_col=0)
        intensification = periods.loc['intensification']
        
        if len(intensification) == 0:
            print(f"      ⚠️  No intensification phase found")
            return (track_id, False)
        
        start_time = pd.to_datetime(intensification['start'])
        end_time = pd.to_datetime(intensification['end'])
        print(f"      Intensification: {start_time} to {end_time}")
        
        # Compute domain bounds
        domain = compute_domain_bounds(track_id, start_time, end_time)
        if domain is None:
            print(f"      ⚠️  Could not compute domain bounds")
            return (track_id, False)
        
        # Download data
        success = download_era5_for_case(track_id, start_time, end_time, domain, pressure_levels)
        return (track_id, success)
        
    except Exception as e:
        print(f"      ❌ Error processing {track_id}: {e}")
        return (track_id, False)


def download_era5_for_case(track_id, start_time, end_time, domain, pressure_levels):
    """Download ERA5 data for a single case."""

    
    print(f"      Downloading ERA5 data...")
    print(f"         Period: {start_time} to {end_time}")
    print(f"         Domain: [{domain['south']:.1f}, {domain['west']:.1f}] to [{domain['north']:.1f}, {domain['east']:.1f}]")
    print(f"         Levels: {pressure_levels}")
    
    # Prepare time range (6-hourly data)
    dates = pd.date_range(start_time, end_time, freq='6H')
    date_list = dates.strftime('%Y-%m-%d').unique().tolist()
    time_list = dates.strftime('%H:%M').unique().tolist()
    
    # Initialize CDS API client
    c = cdsapi.Client()
    
    # Output file
    output_file = DATA_DIR / f"{track_id}_era5.nc"
    
    try:
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': VARIABLES,
                'pressure_level': [str(int(p)) for p in pressure_levels],
                'year': [d.split('-')[0] for d in date_list],
                'month': [d.split('-')[1] for d in date_list],
                'day': [d.split('-')[2] for d in date_list],
                'time': time_list,
                'area': [domain['north'], domain['west'], domain['south'], domain['east']],
            },
            str(output_file)
        )
        
        print(f"      ✓ Downloaded: {output_file}")
        
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
            'pressure_levels_hPa': pressure_levels,
            'variables': VARIABLES
        }
        
        metadata_file = DATA_DIR / f"{track_id}_metadata.csv"
        pd.DataFrame([metadata]).to_csv(metadata_file, index=False)
        print(f"      ✓ Saved metadata: {metadata_file}")
        
        return True
        
    except Exception as e:
        print(f"      ❌ Download failed: {e}")
        return False


def main():
    """Download ERA5 data for selected cases."""
    
    print("=" * 80)
    print("STEP 2: Downloading ERA5 Data at Critical Levels")
    print("=" * 80)
    print("\nNOTE: This script requires:")
    print("  1. step3_vertical_levels_analysis.py to be run first")
    print("  2. CDS API key setup (https://cds.climate.copernicus.eu)")
    print("  3. ~/.cdsapirc file configured\n")
    
    # Load critical levels
    print("1. Loading critical pressure levels...")
    levels_result = load_critical_levels()
    if levels_result is None:
        return
    
    pressure_levels, levels_df = levels_result
    print(f"   Pressure levels to download: {pressure_levels}")
    print(f"\n   Ca max level: {levels_df[levels_df['analysis'] == 'Ca_max']['pressure_level_hPa'].values[0]:.0f} hPa")
    print(f"   Ck min level: {levels_df[levels_df['analysis'] == 'Ck_min']['pressure_level_hPa'].values[0]:.0f} hPa")
    
    # Load selected cases
    print("\n2. Loading selected cases...")
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print(f"❌ Error: {cases_file} not found.")
        print("   Please run step1_select_cases.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"   Found {len(cases)} cases to process")
    
    # Create output directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n3. ERA5 download configuration:")
    print(f"   Variables: {', '.join(VARIABLES)}")
    print(f"   Domain buffer: {DOMAIN_BUFFER}° (allows 30°×30° analysis)")
    print(f"   Temporal resolution: 6-hourly")
    print(f"   Output directory: {DATA_DIR}")
    
    # Process cases in parallel
    n_cores = max(1, mp.cpu_count() - 1)
    print(f"\n4. Processing cases in parallel using {n_cores} cores...")
    
    # Prepare case data with indices
    case_data = [(idx, row) for idx, row in cases.iterrows()]
    
    # Create partial function with pressure_levels
    process_func = partial(process_case_wrapper, pressure_levels=pressure_levels)
    
    # Process in parallel
    with mp.Pool(processes=n_cores) as pool:
        results = pool.map(process_func, case_data)
    
    # Count successes and failures
    successful = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    print("\n" + "=" * 80)
    print(f"✓ Download complete!")
    print(f"  Successful: {successful}/{len(cases)}")
    print(f"  Failed: {failed}/{len(cases)}")
    if successful > 0:
        print(f"\n  Next step: Run step4_compute_instabilities.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
