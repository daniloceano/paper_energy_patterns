"""
Step 2: Vertical Distribution of Energy Conversions

This script analyzes Ca (baroclinic conversion) and Ck (barotropic conversion)
at each pressure level using existing LEC results from data/lec_results.

Analysis includes:
- Load Ca_level.csv and Ck_level.csv for ALL cyclones (not just selected cases)
- Compute vertical profiles during intensification phase
- Identify pressure levels with maximum Ca and minimum Ck across all systems
- Generate publication-quality boxplots showing distribution by pressure level
- Save identified critical levels for ERA5 download

NOTE: This step analyzes ALL cyclones in data/lec_results for a more robust
statistical estimate, not just the 10 selected EP1 cases.

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
import seaborn as sns

# Configuration
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "lec_results"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
FIGURES_DIR = Path(__file__).resolve().parents[2] / "figures" / "ep1_vertical"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300


def load_lec_level_data(track_id, variable='Ca'):
    """
    Load LEC level data (Ca or Ck) for a specific cyclone.
    
    Args:
        track_id: Cyclone ID (e.g., '19790135')
        variable: 'Ca' or 'Ck'
    
    Returns:
        DataFrame with time index and pressure levels as columns
    """
    lec_dir = DATA_DIR / f"{track_id}_ERA5_track"
    file_path = lec_dir / f"{variable}_level.csv"
    
    if not file_path.exists():
        print(f"   ⚠️  {variable} data not found for {track_id}")
        return None
    
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    return df


def get_intensification_phase_times(track_id):
    """
    Get time steps for intensification phase from periods.csv.
    
    Args:
        track_id: Cyclone ID
    
    Returns:
        Tuple of (start_time, end_time) datetime objects
    """
    lec_dir = DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = lec_dir / "periods.csv"
    
    if not periods_file.exists():
        return None
    
    periods = pd.read_csv(periods_file, index_col=0)
    
    # Check if intensification phase exists
    if 'intensification' not in periods.index:
        return None
    
    # Get time range for intensification
    intensification_row = periods.loc['intensification']
    start_time = pd.to_datetime(intensification_row['start'])
    end_time = pd.to_datetime(intensification_row['end'])
    
    return start_time, end_time


def analyze_vertical_profiles(cases):
    """
    Analyze vertical profiles of Ca and Ck for all cases.
    
    Returns:
        Dictionary with analysis results
    """
    results = {
        'ca_max_levels': [],
        'ck_min_levels': [],
        'ca_profiles': {},
        'ck_profiles': {},
        'ca_by_level': {},  # Store all values by pressure level
        'ck_by_level': {}   # Store all values by pressure level
    }
    
    print("\n2. Loading and analyzing LEC data...")
    print(f"   Analyzing ALL cyclones in {DATA_DIR}...")
    
    # Get all cyclone directories
    all_cyclones = [d.name.replace('_ERA5_track', '') for d in DATA_DIR.iterdir() 
                   if d.is_dir() and d.name.endswith('_ERA5_track')]
    
    print(f"   Found {len(all_cyclones)} cyclones with LEC data")
    
    successful = 0
    for track_id in all_cyclones:
        
        # Load Ca and Ck data
        ca_data = load_lec_level_data(track_id, 'Ca')
        ck_data = load_lec_level_data(track_id, 'Ck')
        
        if ca_data is None or ck_data is None:
            continue
        
        # Get intensification phase times
        phase_times = get_intensification_phase_times(track_id)
        if phase_times is None:
            continue
        
        start_time, end_time = phase_times
        
        # Filter for intensification phase
        ca_intensification = ca_data[(ca_data.index >= start_time) & (ca_data.index <= end_time)]
        ck_intensification = ck_data[(ck_data.index >= start_time) & (ck_data.index <= end_time)]
        
        if len(ca_intensification) == 0:
            continue
        
        # Compute mean profiles during intensification
        ca_mean = ca_intensification.mean(axis=0)
        ck_mean = ck_intensification.mean(axis=0)
        
        # Convert pressure levels from Pa to hPa
        pressure_levels_pa = ca_mean.index.astype(float)
        pressure_levels_hpa = pressure_levels_pa / 100.0
        
        # Store profiles by level
        for p_hpa, ca_val, ck_val in zip(pressure_levels_hpa, ca_mean.values, ck_mean.values):
            p_key = int(p_hpa)
            if p_key not in results['ca_by_level']:
                results['ca_by_level'][p_key] = []
                results['ck_by_level'][p_key] = []
            results['ca_by_level'][p_key].append(ca_val)
            results['ck_by_level'][p_key].append(ck_val)
        
        # Find levels of maximum Ca and minimum Ck
        ca_max_level = pressure_levels_hpa[ca_mean.argmax()]
        ck_min_level = pressure_levels_hpa[ck_mean.argmin()]
        
        results['ca_max_levels'].append(ca_max_level)
        results['ck_min_levels'].append(ck_min_level)
        results['ca_profiles'][track_id] = ca_mean
        results['ck_profiles'][track_id] = ck_mean
        
        successful += 1
    
    print(f"   Successfully analyzed {successful} cyclones")
    
    return results


def create_boxplots(results):
    """Create publication-quality boxplots showing Ca and Ck distribution by pressure level."""
    
    print("\n3. Creating publication-quality boxplots...")
    
    # Extract data for plotting
    ca_by_level = results['ca_by_level']
    ck_by_level = results['ck_by_level']
    
    # Sort pressure levels
    pressure_levels = sorted(ca_by_level.keys())
    
    # Prepare data for boxplots
    ca_data = [ca_by_level[p] for p in pressure_levels]
    ck_data = [ck_by_level[p] for p in pressure_levels]
    
    # Create figure with Scientific Reports style
    fig, axes = plt.subplots(2, 1, figsize=(10, 12))
    
    # Style settings
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans']
    })
    
    # Panel A: Ca (Baroclinic conversion)
    ax1 = axes[0]
    bp1 = ax1.boxplot(ca_data, positions=pressure_levels, widths=20,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='darkred', linewidth=2),
                      boxprops=dict(facecolor='lightcoral', edgecolor='darkred', alpha=0.7),
                      whiskerprops=dict(color='darkred', linewidth=1.5),
                      capprops=dict(color='darkred', linewidth=1.5))
    
    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Ca (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Baroclinic Conversion (Ca) by Pressure Level', 
                  fontsize=13, fontweight='bold', loc='left')
    ax1.invert_yaxis()
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax1.set_xlim([1020, 80])
    
    # Find and mark maximum Ca level
    ca_medians = [np.median(ca_by_level[p]) for p in pressure_levels]
    max_ca_idx = np.argmax(ca_medians)
    max_ca_level = pressure_levels[max_ca_idx]
    max_ca_value = ca_medians[max_ca_idx]
    
    ax1.plot(max_ca_level, max_ca_value, 'r*', markersize=15, 
             markeredgecolor='darkred', markeredgewidth=1.5, 
             label=f'Maximum Ca at {max_ca_level} hPa')
    ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    
    # Add text with statistics
    n_systems = len(results['ca_profiles'])
    ax1.text(0.98, 0.02, f'n = {n_systems} systems',
             transform=ax1.transAxes, ha='right', va='bottom',
             fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Panel B: Ck (Barotropic conversion)
    ax2 = axes[1]
    bp2 = ax2.boxplot(ck_data, positions=pressure_levels, widths=20,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='darkblue', linewidth=2),
                      boxprops=dict(facecolor='lightblue', edgecolor='darkblue', alpha=0.7),
                      whiskerprops=dict(color='darkblue', linewidth=1.5),
                      capprops=dict(color='darkblue', linewidth=1.5))
    
    ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Pressure Level (hPa)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Ck (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Barotropic Conversion (Ck) by Pressure Level', 
                  fontsize=13, fontweight='bold', loc='left')
    ax2.invert_yaxis()
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax2.set_xlim([1020, 80])
    
    # Find and mark minimum Ck level
    ck_medians = [np.median(ck_by_level[p]) for p in pressure_levels]
    min_ck_idx = np.argmin(ck_medians)
    min_ck_level = pressure_levels[min_ck_idx]
    min_ck_value = ck_medians[min_ck_idx]
    
    ax2.plot(min_ck_level, min_ck_value, 'b*', markersize=15, 
             markeredgecolor='darkblue', markeredgewidth=1.5,
             label=f'Minimum Ck at {min_ck_level} hPa')
    ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    
    # Add text with statistics
    ax2.text(0.98, 0.02, f'n = {n_systems} systems',
             transform=ax2.transAxes, ha='right', va='bottom',
             fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    output_file = FIGURES_DIR / "critical_levels_boxplot.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved boxplot: {output_file}")
    plt.close()
    
    # Also save as PDF for publication
    output_file_pdf = FIGURES_DIR / "critical_levels_boxplot.pdf"
    fig, axes = plt.subplots(2, 1, figsize=(10, 12))
    
    # Recreate for PDF (same code as above)
    ax1 = axes[0]
    bp1 = ax1.boxplot(ca_data, positions=pressure_levels, widths=20,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='darkred', linewidth=2),
                      boxprops=dict(facecolor='lightcoral', edgecolor='darkred', alpha=0.7),
                      whiskerprops=dict(color='darkred', linewidth=1.5),
                      capprops=dict(color='darkred', linewidth=1.5))
    
    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Ca (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Baroclinic Conversion (Ca) by Pressure Level', 
                  fontsize=13, fontweight='bold', loc='left')
    ax1.invert_yaxis()
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax1.set_xlim([1020, 80])
    ax1.plot(max_ca_level, max_ca_value, 'r*', markersize=15, 
             markeredgecolor='darkred', markeredgewidth=1.5, 
             label=f'Maximum Ca at {max_ca_level} hPa')
    ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax1.text(0.98, 0.02, f'n = {n_systems} systems',
             transform=ax1.transAxes, ha='right', va='bottom',
             fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax2 = axes[1]
    bp2 = ax2.boxplot(ck_data, positions=pressure_levels, widths=20,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='darkblue', linewidth=2),
                      boxprops=dict(facecolor='lightblue', edgecolor='darkblue', alpha=0.7),
                      whiskerprops=dict(color='darkblue', linewidth=1.5),
                      capprops=dict(color='darkblue', linewidth=1.5))
    
    ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Pressure Level (hPa)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Ck (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Barotropic Conversion (Ck) by Pressure Level', 
                  fontsize=13, fontweight='bold', loc='left')
    ax2.invert_yaxis()
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax2.set_xlim([1020, 80])
    ax2.plot(min_ck_level, min_ck_value, 'b*', markersize=15, 
             markeredgecolor='darkblue', markeredgewidth=1.5,
             label=f'Minimum Ck at {min_ck_level} hPa')
    ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax2.text(0.98, 0.02, f'n = {n_systems} systems',
             transform=ax2.transAxes, ha='right', va='bottom',
             fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file_pdf, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved PDF: {output_file_pdf}")
    plt.close()
    
    # Calculate statistics
    ca_mean_of_medians = np.mean(ca_medians)
    ck_mean_of_medians = np.mean(ck_medians)
    
    return max_ca_level, max_ca_value, min_ck_level, min_ck_value


def save_critical_levels(max_ca_level, max_ca_value, min_ck_level, min_ck_value, results):
    """Save identified critical levels for ERA5 download."""
    
    print("\n4. Saving critical levels...")
    
    # Round to nearest standard pressure level
    standard_levels = np.array([1000, 975, 950, 925, 900, 850, 800, 750, 700, 
                               650, 600, 550, 500, 450, 400, 350, 300, 250, 
                               200, 150, 100])
    
    ca_level = standard_levels[np.argmin(np.abs(standard_levels - max_ca_level))]
    ck_level = standard_levels[np.argmin(np.abs(standard_levels - min_ck_level))]
    
    # For EGR, need levels above and below
    ca_idx = np.where(standard_levels == ca_level)[0][0]
    if ca_idx > 0:
        ca_level_above = standard_levels[ca_idx - 1]
    else:
        ca_level_above = ca_level
    if ca_idx < len(standard_levels) - 1:
        ca_level_below = standard_levels[ca_idx + 1]
    else:
        ca_level_below = ca_level
    
    ck_idx = np.where(standard_levels == ck_level)[0][0]
    if ck_idx > 0:
        ck_level_above = standard_levels[ck_idx - 1]
    else:
        ck_level_above = ck_level
    if ck_idx < len(standard_levels) - 1:
        ck_level_below = standard_levels[ck_idx + 1]
    else:
        ck_level_below = ck_level
    
    # Save critical levels
    critical_levels = pd.DataFrame({
        'analysis': ['Ca_max', 'Ca_max_above', 'Ca_max_below', 
                    'Ck_min', 'Ck_min_above', 'Ck_min_below'],
        'pressure_level_hPa': [ca_level, ca_level_above, ca_level_below,
                               ck_level, ck_level_above, ck_level_below],
        'median_value': [max_ca_value, max_ca_value, max_ca_value,
                        min_ck_value, min_ck_value, min_ck_value],
        'level_from_data': [max_ca_level, max_ca_level, max_ca_level,
                           min_ck_level, min_ck_level, min_ck_level]
    })
    
    output_file = RESULTS_DIR / "critical_levels.csv"
    critical_levels.to_csv(output_file, index=False)
    print(f"   ✓ Saved critical levels: {output_file}")
    
    # Save detailed results - distribution of levels where max/min occur
    detailed_results = pd.DataFrame({
        'ca_max_level_hPa': results['ca_max_levels'],
        'ck_min_level_hPa': results['ck_min_levels']
    })
    
    output_file = RESULTS_DIR / "critical_levels_all_cases.csv"
    detailed_results.to_csv(output_file, index=False)
    print(f"   ✓ Saved all cases: {output_file}")
    
    print(f"\n   Summary:")
    print(f"   Ca maximum: {max_ca_level:.0f} hPa (median across all systems) → Download level: {ca_level} hPa")
    print(f"   Ca levels for EGR: {ca_level_above}, {ca_level}, {ca_level_below} hPa")
    print(f"   Ck minimum: {min_ck_level:.0f} hPa (median across all systems) → Download level: {ck_level} hPa")
    print(f"   Ck levels for RK: {ck_level_above}, {ck_level}, {ck_level_below} hPa")


def main():
    """Analyze vertical distribution of energy conversions."""
    
    print("=" * 80)
    print("STEP 2: Vertical Levels Analysis - ALL CYCLONES")
    print("=" * 80)
    
    # Note: We don't need selected cases anymore - we use ALL cyclones
    print("\n1. Analyzing ALL cyclones in data/lec_results...")
    print("   This provides a more robust statistical estimate")
    
    # Analyze vertical profiles for all cyclones
    results = analyze_vertical_profiles(None)
    
    if len(results['ca_max_levels']) == 0:
        print("\n❌ Error: No valid data found.")
        print("   Check that LEC results exist in data/lec_results/")
        return
    
    print(f"\n   Successfully analyzed {len(results['ca_max_levels'])} cyclones")
    
    # Create boxplots
    max_ca_level, max_ca_value, min_ck_level, min_ck_value = create_boxplots(results)
    
    # Save critical levels
    save_critical_levels(max_ca_level, max_ca_value, min_ck_level, min_ck_value, results)
    
    print("\n" + "=" * 80)
    print("✓ Analysis complete!")
    print("  Next step: Run step3_download_era5.py to download data at identified levels")
    print("=" * 80)

if __name__ == "__main__":
    main()
