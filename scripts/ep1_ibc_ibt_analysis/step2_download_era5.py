"""
Step 2: Download ERA5 Data for Selected Cases

This script downloads ERA5 reanalysis data for the selected EP1 cyclones
during their intensification phase. It retrieves 3D atmospheric fields
at multiple pressure levels for three nested domains.

NOTE: This script should be run on a remote server with good internet connection
and sufficient storage capacity. Requires CDS API key setup.

Required Variables:
- Zonal wind (u)
- Meridional wind (v)
- Temperature (T)
- Geopotential height (Z)

Domains:
- 5°×5° (local)
- 15°×15° (mesoscale)
- 30°×30° (synoptic)

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

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep1"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"

# ERA5 pressure levels (hPa)
PRESSURE_LEVELS = [
    1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600,
    550, 500, 450, 400, 350, 300, 250, 200, 150, 100
]

# Variables to download
VARIABLES = ['u', 'v', 't', 'z']

# Domain buffer (degrees)
# Single domain per cyclone: track extent + this buffer on all sides
DOMAIN_BUFFER = 15  # Allows for 30°×30° analysis (largest domain)

def main():
    """Download ERA5 data for selected cases."""
    
    print("=" * 80)
    print("STEP 2: Downloading ERA5 Data")
    print("=" * 80)
    print("\nNOTE: This script requires CDS API key setup.")
    print("Please ensure you have registered at https://cds.climate.copernicus.eu")
    print("and configured your ~/.cdsapirc file.\n")
    
    # Load selected cases
    print("1. Loading selected cases...")
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print(f"❌ Error: {cases_file} not found.")
        print("   Please run step1_select_cases.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"   Found {len(cases)} cases to process")
    
    # Create output directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n2. ERA5 download configuration:")
    print(f"   Pressure levels: {len(PRESSURE_LEVELS)} levels")
    print(f"   Variables: {', '.join(VARIABLES)}")
    print(f"   Domain strategy: Track extent + {DOMAIN_BUFFER}° buffer")
    print(f"   Temporal coverage: Intensification phase only")
    print(f"   Output directory: {DATA_DIR}")
    
    # TODO: Implement actual ERA5 download using cdsapi
    # This is a placeholder - actual implementation requires:
    # 1. Load track data to get cyclone positions during intensification phase only
    # 2. For each case, compute track extent (min/max lat/lon)
    # 3. Add DOMAIN_BUFFER (15°) on all sides
    # 4. Identify central time step of intensification phase
    # 5. Use cdsapi to download data for entire intensification phase
    # 6. Save as NetCDF files organized by case (one file per case)
    # 7. Store metadata (track extent, central time, domain bounds)
    
    print("\n⚠️  ERA5 download not yet implemented.")
    print("   This is a placeholder script. Implementation requires:")
    print("   - cdsapi library")
    print("   - CDS API credentials")
    print("   - Track position data during intensification phase")
    print("   - Nested domain calculations")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
