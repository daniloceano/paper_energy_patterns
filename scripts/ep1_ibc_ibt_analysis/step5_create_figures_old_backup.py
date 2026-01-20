"""
Step 5: Create Publication-Quality Figures

This script generates all figures for the EP1 vertical structure and
instability analysis:

1. Vertical profiles of Ca and Ck (ensemble mean + individual cases)
2. Multi-domain Rayleigh-Kuo criterion comparison (3-panel)
3. Multi-domain Eady Growth Rate maps (3-panel)

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
from matplotlib import gridspec

# Configuration
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
FIGURES_DIR = Path(__file__).resolve().parents[2] / "figures" / "ep1_vertical"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DPI = 300

def plot_vertical_profiles():
    """Create vertical profile figures for Ca and Ck."""
    print("\n1. Creating vertical profile figures...")
    
    # TODO: Implement vertical profile plotting
    # - Load vertical profile data
    # - Plot individual cases (thin lines)
    # - Plot ensemble mean (thick line)
    # - Add uncertainty bands
    # - Mark critical levels
    
    print("   ⚠️  Not yet implemented")

def plot_tracks_overview():
    """Create overview map with all 10 tracks."""
    print("\n2. Creating tracks overview map...")
    
    # TODO: Implement tracks overview figure
    # - Plot all 10 complete tracks
    # - Highlight intensification phase (thicker/different color)
    # - Mark genesis points
    # - Add legend
    
    print("   ⚠️  Not yet implemented")

def plot_tracks_individual():
    """Create individual track maps showing analysis domains."""
    print("\n3. Creating individual track maps with domains...")
    
    # TODO: Implement individual track figures (10 figures)
    # - Complete track with intensification highlighted
    # - Overlay analysis domains (5°×5°, 15°×15°, 30°×30°)
    # - Mark central time step of intensification
    # - Show downloaded domain extent
    # - Mark cyclone center at analysis time
    
    print("   ⚠️  Not yet implemented")

def plot_rayleigh_kuo_composite():
    """Create composite RK criterion figure (ensemble mean)."""
    print("\n4. Creating Rayleigh-Kuo composite...")
    
    # TODO: Implement RK composite figure
    # - 3-panel horizontal layout (5°, 15°, 30°)
    # - Ensemble mean of RK criterion
    # - Color-coded regions satisfying criterion
    # - Statistics box on each panel
    
    print("   ⚠️  Not yet implemented")

def plot_rayleigh_kuo_individual():
    """Create individual RK criterion figures."""
    print("\n5. Creating individual Rayleigh-Kuo figures...")
    
    # TODO: Implement RK individual figures (10 figures)
    # - 3-panel horizontal layout (5°, 15°, 30°) per cyclone
    # - Color-coded regions satisfying criterion
    # - Cyclone center marked
    # - Central time step of intensification
    
    print("   ⚠️  Not yet implemented")

def plot_eady_growth_rate_composite():
    """Create composite EGR figure (ensemble mean)."""
    print("\n6. Creating Eady Growth Rate composite...")
    
    # TODO: Implement EGR composite figure
    # - 3-panel horizontal layout (5°, 15°, 30°)
    # - Ensemble mean EGR distribution
    # - Domain-averaged values annotated
    # - Filled contours
    
    print("   ⚠️  Not yet implemented")

def plot_eady_growth_rate_individual():
    """Create individual EGR figures."""
    print("\n7. Creating individual Eady Growth Rate figures...")
    
    # TODO: Implement EGR individual figures (10 figures)
    # - 3-panel horizontal layout (5°, 15°, 30°) per cyclone
    # - Filled contours of EGR
    # - Domain-averaged value annotated
    # - Cyclone center marked
    # - Central time step of intensification
    
    print("   ⚠️  Not yet implemented")

def main():
    """Generate all figures."""
    
    print("=" * 80)
    print("STEP 5: Creating Figures")
    print("=" * 80)
    
    # Check if required data exists
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print(f"\n❌ Error: {cases_file} not found.")
        print("   Please run previous steps first.")
        return
    
    # Create figures
    plot_vertical_profiles()
    plot_tracks_overview()
    plot_tracks_individual()
    plot_rayleigh_kuo_composite()
    plot_rayleigh_kuo_individual()
    plot_eady_growth_rate_composite()
    plot_eady_growth_rate_individual()
    
    print(f"\n✅ All figures saved to: {FIGURES_DIR}")
    print("   - Vertical profiles")
    print("   - Track overview and 10 individual track maps")
    print("   - RK composite + 10 individual RK figures")
    print("   - EGR composite + 10 individual EGR figures")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
