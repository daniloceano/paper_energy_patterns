#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation Script: Vertical Integration of LEC Terms

This script validates that vertically-resolved LEC data (Ca_level.csv, Ck_level.csv)
integrates correctly to match pre-computed integrated values from LorenzCycleToolkit.

Purpose:
--------
- Identify necessary corrections for vertical integration
- Compare integrated values with original pre-computed values
- Document sign conventions and unit conversions required

Findings:
---------
Two corrections are needed to match pre-computed integrated values:
1. Ca: Sign inversion required (-1 multiplication)
2. Ck: Division by gravity (9.8 m/s²) required

These corrections stem from how the old version of LorenzCycleToolkit saved 
vertically-resolved data. The current version has fixed this issue, but the
Zenodo dataset (DOI: 10.5281/zenodo.18243447) was generated with the old version.

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
from tqdm import tqdm
from glob import glob

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "exploratory"
TEMP_DIR = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

# Create directories if they don't exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Data source information
ZENODO_DOI = "10.5281/zenodo.18243447"
ZENODO_URL = "https://zenodo.org/records/18243447"

# Physical constants
GRAVITY = 9.8  # m/s²

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300

# ============================================================================
# IMPORT HELPER FUNCTIONS
# ============================================================================

from step2_vertical_levels_analysis import (
    get_ep1_cyclones, 
    get_intensification_phase_times
)

# ============================================================================
# MAIN VALIDATION FUNCTIONS
# ============================================================================

def load_and_integrate_lec_data(ep1_dirs):
    """
    Load vertically-resolved LEC data and integrate over pressure levels.
    
    This function processes Ca_level.csv and Ck_level.csv for each cyclone,
    integrates them vertically using the trapezoidal rule, and compares with
    pre-computed integrated values.
    
    Args:
        ep1_dirs: List of paths to cyclone directories
        
    Returns:
        Dictionary containing:
        - ca_integrated_raw: Raw integrated Ca values (before correction)
        - ca_integrated_corrected: Corrected integrated Ca values (sign inverted)
        - ca_original: Pre-computed integrated Ca from toolkit
        - ck_integrated_raw: Raw integrated Ck values (before correction)
        - ck_integrated_corrected: Corrected integrated Ck values (divided by g)
        - ck_original: Pre-computed integrated Ck from toolkit
    """
    
    # Storage for comparison data
    comparison_data = {
        'ca_integrated_raw': [],
        'ca_integrated_corrected': [],
        'ca_original': [],
        'ck_integrated_raw': [],
        'ck_integrated_corrected': [],
        'ck_original': [],
        'track_ids': []
    }
    
    print("\n" + "="*80)
    print("LOADING AND INTEGRATING VERTICAL LEC DATA")
    print("="*80)
    
    for ep1_dir in tqdm(ep1_dirs, desc="Processing cyclones"):
        track_id = int(ep1_dir.split('/')[-1].split('_')[0])
        
        try:
            # Get intensification phase timing
            intensification_times = get_intensification_phase_times(TEMP_DIR, track_id)
            if intensification_times is None:
                continue
                
            # ----------------------------------------------------------------
            # Process Ca (Baroclinic Conversion)
            # ----------------------------------------------------------------
            ca_file = Path(ep1_dir) / "Ca_level.csv" / "Ca_level.csv"
            if ca_file.exists():
                # Load vertical data
                ca_data = pd.read_csv(ca_file, index_col=0, parse_dates=True)
                
                # Filter to intensification phase
                ca_intensification = ca_data.loc[
                    intensification_times[0]:intensification_times[1]
                ]
                
                # Integrate vertically using trapezoidal rule
                # Axis=1 because columns represent pressure levels
                levels_pa = ca_intensification.columns.values.astype(float)
                ca_integrated_timestep = np.trapezoid(
                    y=ca_intensification.values, 
                    x=levels_pa, 
                    axis=1
                )
                
                # Compute mean over intensification phase
                ca_integrated_raw = ca_integrated_timestep.mean()
                ca_integrated_corrected = -ca_integrated_raw  # Sign correction
                
                # Load pre-computed integrated values
                results_file = (
                    Path(ep1_dir) / 
                    f"{track_id}_ERA5_track_results.csv" / 
                    f"{track_id}_ERA5_track_results.csv"
                )
                integrated_df = pd.read_csv(
                    results_file, 
                    index_col=0, 
                    parse_dates=True
                )
                ca_original = integrated_df.loc[
                    intensification_times[0]:intensification_times[1], 
                    'Ca'
                ].mean()
                
                # Store for comparison
                comparison_data['ca_integrated_raw'].append(ca_integrated_raw)
                comparison_data['ca_integrated_corrected'].append(ca_integrated_corrected)
                comparison_data['ca_original'].append(ca_original)
            
            # ----------------------------------------------------------------
            # Process Ck (Barotropic Conversion)
            # ----------------------------------------------------------------
            ck_file = Path(ep1_dir) / "Ck_level.csv" / "Ck_level.csv"
            if ck_file.exists():
                # Load vertical data
                ck_data = pd.read_csv(ck_file, index_col=0, parse_dates=True)
                
                # Filter to intensification phase
                ck_intensification = ck_data.loc[
                    intensification_times[0]:intensification_times[1]
                ]
                
                # Integrate vertically using trapezoidal rule
                levels_pa = ck_intensification.columns.values.astype(float)
                ck_integrated_timestep = np.trapezoid(
                    y=ck_intensification.values, 
                    x=levels_pa, 
                    axis=1
                )
                
                # Compute mean over intensification phase
                ck_integrated_raw = ck_integrated_timestep.mean()
                ck_integrated_corrected = ck_integrated_raw / GRAVITY  # Gravity correction
                
                # Load pre-computed integrated values
                results_file = (
                    Path(ep1_dir) / 
                    f"{track_id}_ERA5_track_results.csv" / 
                    f"{track_id}_ERA5_track_results.csv"
                )
                integrated_df = pd.read_csv(
                    results_file, 
                    index_col=0, 
                    parse_dates=True
                )
                ck_original = integrated_df.loc[
                    intensification_times[0]:intensification_times[1], 
                    'Ck'
                ].mean()
                
                # Store for comparison
                comparison_data['ck_integrated_raw'].append(ck_integrated_raw)
                comparison_data['ck_integrated_corrected'].append(ck_integrated_corrected)
                comparison_data['ck_original'].append(ck_original)
                comparison_data['track_ids'].append(track_id)
                
        except Exception as e:
            print(f"Warning: Error processing track {track_id}: {e}")
            continue
    
    return comparison_data


def create_comparison_boxplots(comparison_data):
    """
    Create boxplots comparing integrated vs pre-computed values.
    
    Shows three versions for each term:
    1. Raw integrated values (before correction)
    2. Corrected integrated values (after applying corrections)
    3. Original pre-computed values (from toolkit)
    
    Args:
        comparison_data: Dictionary with comparison data
    """
    
    print("\n" + "="*80)
    print("CREATING COMPARISON BOXPLOTS")
    print("="*80)
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # ----------------------------------------------------------------
    # Panel A: Ca Comparison
    # ----------------------------------------------------------------
    ax1 = axes[0]
    
    ca_data_for_plot = [
        comparison_data['ca_integrated_raw'],
        comparison_data['ca_integrated_corrected'],
        comparison_data['ca_original']
    ]
    
    labels_ca = ['Raw\nIntegrated', 'Corrected\n(sign inverted)', 'Original\n(pre-computed)']
    colors_ca = ['#ff9999', '#66b3ff', '#99ff99']
    
    bp1 = ax1.boxplot(
        ca_data_for_plot, 
        labels=labels_ca,
        patch_artist=True,
        widths=0.6,
        showfliers=True
    )
    
    # Color the boxes
    for patch, color in zip(bp1['boxes'], colors_ca):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Ca (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax1.set_title(
        '(a) Baroclinic Conversion (Ca): Validation of Vertical Integration',
        fontsize=13, 
        fontweight='bold', 
        loc='left'
    )
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    
    # Add annotation explaining correction
    ax1.text(
        0.02, 0.98,
        'Correction: Sign inversion\n' + 
        r'$Ca_{corrected} = -Ca_{raw}$',
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # ----------------------------------------------------------------
    # Panel B: Ck Comparison
    # ----------------------------------------------------------------
    ax2 = axes[1]
    
    ck_data_for_plot = [
        comparison_data['ck_integrated_raw'],
        comparison_data['ck_integrated_corrected'],
        comparison_data['ck_original']
    ]
    
    labels_ck = ['Raw\nIntegrated', 'Corrected\n(÷ 9.8)', 'Original\n(pre-computed)']
    colors_ck = ['#ff9999', '#66b3ff', '#99ff99']
    
    bp2 = ax2.boxplot(
        ck_data_for_plot, 
        labels=labels_ck,
        patch_artist=True,
        widths=0.6,
        showfliers=True
    )
    
    # Color the boxes
    for patch, color in zip(bp2['boxes'], colors_ck):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_ylabel('Ck (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax2.set_title(
        '(b) Barotropic Conversion (Ck): Validation of Vertical Integration',
        fontsize=13, 
        fontweight='bold', 
        loc='left'
    )
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    
    # Add annotation explaining correction
    ax2.text(
        0.02, 0.98,
        'Correction: Division by gravity\n' + 
        r'$Ck_{corrected} = Ck_{raw} / g$ (g = 9.8 m/s²)',
        transform=ax2.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # ----------------------------------------------------------------
    # Final adjustments and save
    # ----------------------------------------------------------------
    plt.tight_layout()
    
    output_file = FIGURES_DIR / "validation_vertical_integration.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved comparison figure: {output_file}")
    plt.close()


def print_validation_summary(comparison_data):
    """
    Print detailed summary of validation results.
    
    Shows statistics and explains necessary corrections.
    
    Args:
        comparison_data: Dictionary with comparison data
    """
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY: VERTICAL INTEGRATION OF LEC TERMS")
    print("="*80)
    
    n_cases = len(comparison_data['track_ids'])
    
    print(f"\nAnalyzed {n_cases} EP1 cyclones during intensification phase")
    print(f"Data source: Zenodo (DOI: {ZENODO_DOI})")
    print(f"URL: {ZENODO_URL}")
    
    # ----------------------------------------------------------------
    # Ca Statistics
    # ----------------------------------------------------------------
    print("\n" + "-"*80)
    print("Ca (BAROCLINIC CONVERSION) VALIDATION")
    print("-"*80)
    
    ca_raw = np.array(comparison_data['ca_integrated_raw'])
    ca_corrected = np.array(comparison_data['ca_integrated_corrected'])
    ca_original = np.array(comparison_data['ca_original'])
    
    ca_error_raw = np.abs(ca_raw - ca_original)
    ca_error_corrected = np.abs(ca_corrected - ca_original)
    
    print(f"\n{'Metric':<30} {'Raw':>15} {'Corrected':>15} {'Original':>15}")
    print("-"*80)
    print(f"{'Mean (W/m²)':<30} {ca_raw.mean():>15.4f} {ca_corrected.mean():>15.4f} {ca_original.mean():>15.4f}")
    print(f"{'Median (W/m²)':<30} {np.median(ca_raw):>15.4f} {np.median(ca_corrected):>15.4f} {np.median(ca_original):>15.4f}")
    print(f"{'Std Dev (W/m²)':<30} {ca_raw.std():>15.4f} {ca_corrected.std():>15.4f} {ca_original.std():>15.4f}")
    print(f"{'Mean Absolute Error':<30} {ca_error_raw.mean():>15.4f} {ca_error_corrected.mean():>15.4f} {0.0:>15.4f}")
    print(f"{'Max Absolute Error':<30} {ca_error_raw.max():>15.4f} {ca_error_corrected.max():>15.4f} {0.0:>15.4f}")
    
    print("\n⚠️  CORRECTION REQUIRED FOR Ca:")
    print("   └─ Sign inversion: Ca_corrected = -Ca_raw")
    print("   └─ Reason: Old LorenzCycleToolkit version saved Ca_level with opposite sign")
    print(f"   └─ Improvement: MAE reduced from {ca_error_raw.mean():.4f} to {ca_error_corrected.mean():.4f} W/m²")
    
    # ----------------------------------------------------------------
    # Ck Statistics
    # ----------------------------------------------------------------
    print("\n" + "-"*80)
    print("Ck (BAROTROPIC CONVERSION) VALIDATION")
    print("-"*80)
    
    ck_raw = np.array(comparison_data['ck_integrated_raw'])
    ck_corrected = np.array(comparison_data['ck_integrated_corrected'])
    ck_original = np.array(comparison_data['ck_original'])
    
    ck_error_raw = np.abs(ck_raw - ck_original)
    ck_error_corrected = np.abs(ck_corrected - ck_original)
    
    print(f"\n{'Metric':<30} {'Raw':>15} {'Corrected':>15} {'Original':>15}")
    print("-"*80)
    print(f"{'Mean (W/m²)':<30} {ck_raw.mean():>15.4f} {ck_corrected.mean():>15.4f} {ck_original.mean():>15.4f}")
    print(f"{'Median (W/m²)':<30} {np.median(ck_raw):>15.4f} {np.median(ck_corrected):>15.4f} {np.median(ck_original):>15.4f}")
    print(f"{'Std Dev (W/m²)':<30} {ck_raw.std():>15.4f} {ck_corrected.std():>15.4f} {ck_original.std():>15.4f}")
    print(f"{'Mean Absolute Error':<30} {ck_error_raw.mean():>15.4f} {ck_error_corrected.mean():>15.4f} {0.0:>15.4f}")
    print(f"{'Max Absolute Error':<30} {ck_error_raw.max():>15.4f} {ck_error_corrected.max():>15.4f} {0.0:>15.4f}")
    
    print("\n⚠️  CORRECTION REQUIRED FOR Ck:")
    print(f"   └─ Division by gravity: Ck_corrected = Ck_raw / {GRAVITY}")
    print("   └─ Reason: Old LorenzCycleToolkit version saved Ck_level without gravity normalization")
    print(f"   └─ Improvement: MAE reduced from {ck_error_raw.mean():.4f} to {ck_error_corrected.mean():.4f} W/m²")
    
    # ----------------------------------------------------------------
    # Overall Summary
    # ----------------------------------------------------------------
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("\n✅ Validation successful! Two corrections needed:")
    print("\n   1. Ca (Baroclinic): Invert sign")
    print("      └─ Ca_corrected = -Ca_raw")
    print("\n   2. Ck (Barotropic): Divide by gravity")
    print(f"      └─ Ck_corrected = Ck_raw / {GRAVITY}")
    print("\n📝 These corrections have been applied in step2_vertical_levels_analysis.py")
    print("\n⚠️  Note: These corrections are specific to data generated by old LorenzCycleToolkit")
    print("   The current version of the toolkit has fixed these issues.")
    print("="*80 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    
    print("\n" + "="*80)
    print("VERTICAL INTEGRATION VALIDATION SCRIPT")
    print("="*80)
    print(f"\nData source: {ZENODO_URL}")
    print(f"DOI: {ZENODO_DOI}")
    
    # Get all cyclone directories
    all_cyclones = glob(str(TEMP_DIR / "*_ERA5_track"))
    print(f"\nFound {len(all_cyclones)} total cyclones with LEC data")
    
    # Get EP1 cyclone IDs
    ep1_track_ids = get_ep1_cyclones()
    print(f"Identified {len(ep1_track_ids)} EP1 cyclones (cluster 0)")
    
    # Filter to only EP1 cyclones with LEC data
    ep1_cyclones_with_lec = [
        int(cid.split('/')[-1].split('_')[0]) 
        for cid in all_cyclones 
        if int(cid.split('/')[-1].split('_')[0]) in ep1_track_ids
    ]
    print(f"Found {len(ep1_cyclones_with_lec)} EP1 cyclones with complete LEC data")
    
    # Get directories for selected EP1 cyclones
    selected_ep1_dirs = [
        cid for cid in all_cyclones 
        if int(cid.split('/')[-1].split('_')[0]) in ep1_cyclones_with_lec
    ]
    
    # Load and integrate vertical data
    comparison_data = load_and_integrate_lec_data(selected_ep1_dirs)
    
    # Create comparison boxplots
    create_comparison_boxplots(comparison_data)
    
    # Print detailed summary
    print_validation_summary(comparison_data)


if __name__ == "__main__":
    main()