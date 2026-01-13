"""
Step 3: Vertical Distribution of Energy Conversions

This script computes Ca (baroclinic conversion) and Ck (barotropic conversion)
at each pressure level during the intensification phase of selected EP1 cyclones.

Analysis includes:
- Vertical profiles of Ca(p) and Ck(p)
- Identification of levels with maximum conversions
- Ensemble statistics across all cases

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configuration
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
FIGURES_DIR = Path(__file__).resolve().parents[2] / "figures" / "ep1_vertical"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Analyze vertical distribution of energy conversions."""
    
    print("=" * 80)
    print("STEP 3: Vertical Levels Analysis")
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
    
    # TODO: Implement vertical profile computation
    # This requires:
    # 1. Load ERA5 data for each case
    # 2. Compute Ca and Ck at each pressure level
    # 3. Extract intensification phase data
    # 4. Create vertical profiles
    # 5. Identify critical levels
    # 6. Compute ensemble statistics
    
    print("\n⚠️  Vertical levels analysis not yet implemented.")
    print("   Requires ERA5 data from step2_download_era5.py")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
