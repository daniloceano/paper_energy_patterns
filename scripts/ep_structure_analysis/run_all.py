"""
Run All: Complete EP Structure Analysis Pipeline

Executes the complete analysis comparing EP1 and EP2 cyclone structures.

Steps:
1. Select EP1 and EP2 cyclone tracks
2. Download ERA5 data in parallel (EGR/PV/advection levels + SLP)
2.1. Download ERA5 monthly means and compute climatology (for AFC)
3. Precompute composites for all diagnostic fields
4. Create composite comparison figures (EP1 vs EP2)
5. Update scientific notes

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run_script(script_name, description, extra_args=None):
    """Run a Python script and handle errors."""
    print("\n" + "=" * 80)
    print(f"Running: {description}")
    print("=" * 80)

    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with error code {e.returncode}")
        return False


def main():
    print("=" * 80)
    print("EP STRUCTURE ANALYSIS – COMPLETE PIPELINE")
    print("=" * 80)
    print("\nThis will run all analysis steps comparing EP1 and EP2 cyclone structures.")
    print("Estimated time: Several hours (depending on download speed)")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() != "y":
        print("Aborted.")
        return

    steps = [
        ("step1_select_ep_tracks.py",          "Step 1: Select EP1 + EP2 Cyclone Tracks"),
        ("step2_download_era5_parallel.py",     "Step 2: Download ERA5 Data (Parallel)"),
        ("step2_1_download_era5_monthly_means.py", "Step 2.1: ERA5 Monthly Means → AFC Climatology"),
        ("step3_precompute_composites.py",      "Step 3: Precompute Composites"),
        ("step4_create_figures.py",             "Step 4: Create Composite Figures (EP1 vs EP2)"),
        ("step5_update_scientific_notes.py",    "Step 5: Update Scientific Notes"),
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
    print("\nResults saved in:")
    print("  - data/era5_ep_structure/precomputed_composites_ep1.nc")
    print("  - data/era5_ep_structure/precomputed_composites_ep2.nc")
    print("  - results/ep_structure/")
    print("  - figures/ep_structure/")


if __name__ == "__main__":
    main()
