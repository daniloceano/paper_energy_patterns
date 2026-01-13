"""
Step 4: Compute Instability Diagnostics

This script computes barotropic and baroclinic instability diagnostics
for the selected EP1 cyclones:

1. Rayleigh-Kuo (RK) criterion for barotropic instability
2. Eady Growth Rate (EGR) for baroclinic instability

Both diagnostics are computed at three spatial scales:
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

# Configuration
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"

def compute_rayleigh_kuo(u, v, lat, lon):
    """
    Compute Rayleigh-Kuo criterion for barotropic instability.
    
    The criterion is satisfied when ∂η/∂y < 0, where η = ζ + f
    
    Parameters
    ----------
    u : array
        Zonal wind (m/s)
    v : array
        Meridional wind (m/s)
    lat : array
        Latitude (degrees)
    lon : array
        Longitude (degrees)
    
    Returns
    -------
    rk_criterion : array
        Boolean array where True indicates barotropic instability
    """
    # TODO: Implement RK criterion calculation
    pass

def compute_eady_growth_rate(u, v, t, z, lat):
    """
    Compute Eady Growth Rate for baroclinic instability.
    
    σ_EGR = 0.31 * (f/N) * |∂U/∂z|
    
    Parameters
    ----------
    u : array
        Zonal wind (m/s)
    v : array
        Meridional wind (m/s)
    t : array
        Temperature (K)
    z : array
        Geopotential height (m)
    lat : array
        Latitude (degrees)
    
    Returns
    -------
    egr : array
        Eady Growth Rate (1/day)
    """
    # TODO: Implement EGR calculation
    pass

def main():
    """Compute instability diagnostics for all cases and domains."""
    
    print("=" * 80)
    print("STEP 4: Computing Instability Diagnostics")
    print("=" * 80)
    
    # Load selected cases
    print("\n1. Loading selected cases...")
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print(f"❌ Error: {cases_file} not found.")
        print("   Please run step1_select_cases.py first.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"   Found {len(cases)} cases")
    
    # TODO: Implement instability calculations
    # For each case:
    # 1. Load ERA5 data (single domain per cyclone)
    # 2. Identify central time step of intensification phase
    # 3. Extract data at critical levels (from step3) at central time
    # 4. Extract three nested domains from downloaded data:
    #    - 5°×5° centered on cyclone
    #    - 15°×15° centered on cyclone  
    #    - 30°×30° centered on cyclone
    # 5. Compute RK criterion at level of max Ck for all three domains
    # 6. Compute EGR at level of max Ca for all three domains
    # 7. Save individual results for each case and domain
    # 8. Compute composite (ensemble mean) statistics
    
    print("\n⚠️  Instability diagnostics not yet implemented.")
    print("   Requires:")
    print("   - ERA5 data from step2_download_era5.py")
    print("   - Critical levels from step3_vertical_levels_analysis.py")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
