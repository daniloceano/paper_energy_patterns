"""
Run All: Complete EP1 Analysis Pipeline

Executes the complete analysis pipeline for ALL EP1 cyclones.

Steps:
1. Select all EP1 cyclones
2. Download ERA5 data in parallel (with SLP)
3. Precompute composites AND diagnostic fields
4. Create 4-panel composite figures

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print("\n" + "=" * 80)
    print(f"Running: {description}")
    print("=" * 80)
    
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        print(f"   This step needs to be implemented or adapted from ep1_ibc_ibt_analysis")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with error code {e.returncode}")
        return False


def main():
    print("=" * 80)
    print("EP1 FULL ANALYSIS - COMPLETE PIPELINE")
    print("=" * 80)
    print("\nThis will run all analysis steps for ALL EP1 cyclones.")
    print("Estimated time: Several hours (depending on download speed)")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Core steps
    steps = [
        ("step1_select_all_ep1.py", "Step 1: Select All EP1 Cyclones"),
        ("step2_download_era5_parallel.py", "Step 2: Download ERA5 Data (Parallel)"),
        ("step3_precompute_composites.py", "Step 3: Precompute Composites + Diagnostics"),
        ("step4_create_figures.py", "Step 4: Create 4-Panel Composite Figures"),
    ]
    
    for script, description in steps:
        success = run_script(script, description)
        if not success:
            print(f"\n⚠️  Pipeline stopped at: {description}")
            print("Fix the error and re-run this script to continue.")
            return
    
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nResults saved in:")
    print(f"  - data/era5_ep1/precomputed_composites_*.nc")
    print(f"  - results/ep1_vertical/")
    print(f"  - figures/ep1_vertical/composite/")


if __name__ == '__main__':
    main()
