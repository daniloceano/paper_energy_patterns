#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S3: Vertical Distribution of Energy Conversions for EP1 Cyclones

This script creates a two-panel boxplot showing the vertical distribution of:
  • (a) Baroclinic conversion (Ca) across 32 pressure levels (1000–100 hPa)
  • (b) Barotropic conversion (Ck) across 32 pressure levels (1000–100 hPa)

Analysis is restricted to the intensification phase of selected EP1 cyclones.

Key findings:
  • Maximum Ca typically occurs in the mid-troposphere (~350-400 hPa)
  • Minimum Ck typically occurs in the mid-troposphere (~350 hPa)
  • This identifies critical pressure levels for instability diagnostics

Data source: Zenodo (DOI: 10.5281/zenodo.18243447)
  • Complete Lorenz Energy Cycle results with vertical resolution
  • 32 pressure levels from 1000 hPa to 100 hPa
  • 3-hourly temporal resolution during intensification phase

IMPORTANT: This script requires results from the EP1 instability analysis pipeline:
  • Must run: scripts/ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py first
  • Input: results/ep1_vertical/critical_levels_boxplot.png (intermediate)
  • LEC data: data/temp_lec_zenodo/LEC_Results_energetic-patterns/

Outputs:
  • Figure: figures/main/S3_vertical_levels.png (300 DPI)

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
import warnings
warnings.filterwarnings('ignore')
from tqdm import tqdm

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results'
CLUSTER_RESULTS_DIR = RESULTS_DIR / 'cluster'
EP1_RESULTS_DIR = RESULTS_DIR / 'ep1_vertical'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

# Physical constants
GRAVITY = 9.8  # m/s² - Used for Ck correction

# Figure settings
FIG_WIDTH = 10
FIG_HEIGHT = 10
DPI = 300

# Zenodo data source
ZENODO_DOI = "10.5281/zenodo.18243447"

plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 14,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans']
})

# ============================================================================
# Data Loading Functions
# ============================================================================

def get_ep1_cyclones():
    """Load clustered data and filter for EP1 cyclones (cluster 0)."""
    cluster_file = CLUSTER_RESULTS_DIR / "kmeans_clustered_data.csv"
    
    if not cluster_file.exists():
        raise FileNotFoundError(
            f"Cluster file not found: {cluster_file}\n"
            "Please run clustering analysis first"
        )
    
    clustered = pd.read_csv(cluster_file)
    ep1_tracks = clustered[clustered['cluster'] == 0]['track_id'].tolist()
    
    return ep1_tracks


def load_lec_level_data(track_id, variable='Ca'):
    """
    Load LEC level data (Ca or Ck) for a specific cyclone.
    
    Data corrections applied:
    1. Ca: Sign inversion (-Ca_raw)
    2. Ck: Division by gravity (Ck_raw / 9.8)
    
    See step2_vertical_levels_analysis.py for validation details.
    """
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    file_path = lec_dir / f"{variable}_level.csv"
    
    # Check if file_path is actually a directory
    if file_path.is_dir():
        file_path = file_path / f"{variable}_level.csv"
    
    if not file_path.exists():
        return None
    
    # Load raw data
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    
    # Apply data corrections
    if variable == 'Ca':
        df = -df
    elif variable == 'Ck':
        df = df / GRAVITY
    
    return df


def get_intensification_phase_times(track_id):
    """Get time steps for intensification phase from periods.csv."""
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = lec_dir / "periods.csv" / "periods.csv"
    
    if not periods_file.exists():
        return None
    
    periods = pd.read_csv(periods_file, index_col=0)
    
    if 'intensification' not in periods.index:
        return None
    
    intensification_row = periods.loc['intensification']
    start_time = pd.to_datetime(intensification_row['start'])
    end_time = pd.to_datetime(intensification_row['end'])
    
    return start_time, end_time


def analyze_vertical_profiles(ep1_track_ids):
    """
    Analyze vertical profiles of Ca and Ck for EP1 cyclones.
    
    Returns dictionary with analysis results.
    """
    results = {
        'ca_max_levels': [],
        'ck_min_levels': [],
        'ca_profiles': {},
        'ck_profiles': {},
        'ca_by_level': {},
        'ck_by_level': {}
    }
    
    print(f"\n2. Analyzing vertical profiles for {len(ep1_track_ids)} EP1 cyclones...")
    print(f"   Data source: Zenodo (DOI: {ZENODO_DOI})")
    print(f"   Phase: Intensification only")
    print(f"   Pressure levels: 1000–100 hPa (32 levels)")
    
    successful = 0
    missing = 0
    
    for track_id in tqdm(ep1_track_ids, desc="Processing cyclones"):
        
        # Load Ca and Ck data
        ca_data = load_lec_level_data(track_id, 'Ca')
        ck_data = load_lec_level_data(track_id, 'Ck')
        
        if ca_data is None or ck_data is None:
            missing += 1
            continue
        
        # Get intensification phase times
        phase_times = get_intensification_phase_times(track_id)
        if phase_times is None:
            missing += 1
            continue
        
        start_time, end_time = phase_times
        
        # Filter for intensification phase
        ca_intensification = ca_data[(ca_data.index >= start_time) & (ca_data.index <= end_time)]
        ck_intensification = ck_data[(ck_data.index >= start_time) & (ck_data.index <= end_time)]
        
        if len(ca_intensification) == 0:
            missing += 1
            continue
        
        # Compute mean profiles during intensification
        ca_mean = ca_intensification.mean(axis=0)
        ck_mean = ck_intensification.mean(axis=0)
        
        # Convert pressure levels from Pa to hPa and filter >= 100 hPa
        pressure_levels_pa = ca_mean.index.astype(float)
        pressure_levels_hpa = pressure_levels_pa / 100.0
        
        # Filter to only include levels >= 100 hPa
        valid_mask = pressure_levels_hpa >= 100.0
        pressure_levels_hpa = pressure_levels_hpa[valid_mask]
        ca_mean = ca_mean[valid_mask]
        ck_mean = ck_mean[valid_mask]
        
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
    
    print(f"   ✓ Successfully analyzed: {successful} cyclones")
    print(f"   ✗ Missing/incomplete data: {missing} cyclones")
    
    return results


# ============================================================================
# Figure Generation
# ============================================================================

def create_boxplots(results):
    """Create publication-quality boxplots showing Ca and Ck distribution by pressure level."""
    
    print("\n3. Creating Figure S3: Vertical Distribution of Energy Conversions...")
    
    # Extract data for plotting
    ca_by_level = results['ca_by_level']
    ck_by_level = results['ck_by_level']
    
    # Sort pressure levels in descending order (1000 hPa to 100 hPa)
    pressure_levels = sorted(ca_by_level.keys(), reverse=True)
    
    # Prepare data for boxplots
    ca_data = [ca_by_level[p] for p in pressure_levels]
    ck_data = [ck_by_level[p] for p in pressure_levels]
    
    # Create regularly spaced positions for boxplots
    positions = np.arange(len(pressure_levels))
    
    # Create figure
    fig, axes = plt.subplots(2, 1, figsize=(FIG_WIDTH, FIG_HEIGHT))
    
    # Panel A: Ca (Baroclinic conversion)
    ax1 = axes[0]
    bp1 = ax1.boxplot(ca_data, positions=positions, widths=0.6,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='darkred', linewidth=2),
                      boxprops=dict(facecolor='lightcoral', edgecolor='darkred', alpha=0.7),
                      whiskerprops=dict(color='darkred', linewidth=1.5),
                      capprops=dict(color='darkred', linewidth=1.5))
    
    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Ca (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Baroclinic Conversion (Ca) by Pressure Level', 
                  fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    
    # Set x-axis ticks and labels
    ax1.set_xticks(positions)
    ax1.set_xticklabels([f'{int(p)}' for p in pressure_levels], rotation=45, ha='right')
    ax1.set_xlim([positions[0] - 0.5, positions[-1] + 0.5])
    
    # Find and mark maximum Ca level
    ca_medians = [np.median(ca_by_level[p]) for p in pressure_levels]
    max_ca_idx = np.argmax(ca_medians)
    max_ca_level = pressure_levels[max_ca_idx]
    max_ca_value = ca_medians[max_ca_idx]
    
    ax1.plot(positions[max_ca_idx], max_ca_value, 'r*', markersize=15, 
             markeredgecolor='darkred', markeredgewidth=1.5, 
             label=f'Maximum Ca at {max_ca_level} hPa')
    ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    
    # Add text with statistics
    n_systems = len(results['ca_profiles'])
    ax1.text(0.985, 0.97, f'n = {n_systems} systems',
             transform=ax1.transAxes, ha='right', va='top',
             fontsize=12, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Panel B: Ck (Barotropic conversion)
    ax2 = axes[1]
    bp2 = ax2.boxplot(ck_data, positions=positions, widths=0.6,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='darkblue', linewidth=2),
                      boxprops=dict(facecolor='lightblue', edgecolor='darkblue', alpha=0.7),
                      whiskerprops=dict(color='darkblue', linewidth=1.5),
                      capprops=dict(color='darkblue', linewidth=1.5))
    
    ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Pressure Level (hPa)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Ck (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Barotropic Conversion (Ck) by Pressure Level', 
                  fontweight='bold', loc='left')
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    
    # Set x-axis ticks and labels
    ax2.set_xticks(positions)
    ax2.set_xticklabels([f'{int(p)}' for p in pressure_levels], rotation=45, ha='right')
    ax2.set_xlim([positions[0] - 0.5, positions[-1] + 0.5])
    
    # Find and mark minimum Ck level
    ck_medians = [np.median(ck_by_level[p]) for p in pressure_levels]
    min_ck_idx = np.argmin(ck_medians)
    min_ck_level = pressure_levels[min_ck_idx]
    min_ck_value = ck_medians[min_ck_idx]
    
    ax2.plot(positions[min_ck_idx], min_ck_value, 'b*', markersize=15, 
             markeredgecolor='darkblue', markeredgewidth=1.5,
             label=f'Minimum Ck at {min_ck_level} hPa')
    ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    
    # Add text with statistics
    # ax2.text(0.98, 0.02, f'n = {n_systems} systems',
    #          transform=ax2.transAxes, ha='right', va='bottom',
    #          fontsize=12, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Save figure
    output_file = FIGURES_DIR / "S3_vertical_levels.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Figure saved: {output_file}")
    
    # Calculate and print statistics
    ca_mean_of_medians = np.mean(ca_medians)
    ck_mean_of_medians = np.mean(ck_medians)
    
    print(f"\n   Key findings:")
    print(f"   • Maximum Ca: {max_ca_value:.4f} W m⁻² at {max_ca_level} hPa")
    print(f"   • Minimum Ck: {min_ck_value:.4f} W m⁻² at {min_ck_level} hPa")
    print(f"   • Ca mean across levels: {ca_mean_of_medians:.4f} W m⁻²")
    print(f"   • Ck mean across levels: {ck_mean_of_medians:.4f} W m⁻²")
    
    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate Figure S3: Vertical Distribution of Energy Conversions."""
    
    print("=" * 80)
    print("Figure S3: Vertical Distribution of Energy Conversions for EP1 Cyclones")
    print("=" * 80)
    
    # Check if LEC data directory exists
    if not LEC_DATA_DIR.exists():
        raise FileNotFoundError(
            f"LEC data directory not found: {LEC_DATA_DIR}\n"
            "Please run scripts/ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py first\n"
            "This will download and process the required LEC data from Zenodo"
        )
    
    # Load EP1 cyclones
    print("\n1. Loading EP1 cyclones from cluster results...")
    ep1_track_ids = get_ep1_cyclones()
    print(f"   Found {len(ep1_track_ids)} EP1 cyclones (cluster 0)")
    
    # Analyze vertical profiles
    results = analyze_vertical_profiles(ep1_track_ids)
    
    # Create figure
    output_file = create_boxplots(results)
    
    print("\n" + "=" * 80)
    print("✅ Figure S3 generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
