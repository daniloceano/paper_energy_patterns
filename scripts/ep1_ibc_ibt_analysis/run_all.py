"""
Run All EP1 Vertical Analysis Steps

This script executes all steps of the EP1 vertical structure and instability
analysis in sequence.

Steps:
1. Select 10 most intense EP1 cyclones
2. Download ERA5 data (should be run separately on server)
3. Analyze vertical distribution of Ca and Ck
4. Compute instability diagnostics (RK and EGR)
5. Create publication-quality figures

NOTE: Step 2 (ERA5 download) should be run separately on a remote server
      with appropriate resources.

Author: Danilo Couto de Souza
Date: January 2026
"""

import subprocess
import sys
from pathlib import Path

def run_step(step_number, script_name, description):
    """Run a single analysis step."""
    print("\n" + "=" * 80)
    print(f"RUNNING STEP {step_number}: {description}")
    print("=" * 80)
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        print(f"\n✅ Step {step_number} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Step {step_number} failed with error code {e.returncode}")
        return False

def main():
    """Run all analysis steps."""
    
    print("\n" + "=" * 80)
    print("EP1 VERTICAL STRUCTURE AND INSTABILITY ANALYSIS")
    print("=" * 80)
    print("\nThis script will run all analysis steps in sequence.")
    print("NOTE: Step 2 (ERA5 download) is skipped by default.")
    print("      Run step2_download_era5.py separately on a remote server.\n")
    
    steps = [
        (1, "step1_select_cases.py", "Select Most Intense EP1 Cyclones"),
        # Step 2 skipped - must be run manually on server
        (3, "step3_vertical_levels_analysis.py", "Vertical Levels Analysis"),
        (4, "step4_compute_instabilities.py", "Compute Instability Diagnostics"),
        (5, "step5_create_figures.py", "Create Figures"),
    ]
    
    success_count = 0
    
    for step_number, script_name, description in steps:
        success = run_step(step_number, script_name, description)
        if success:
            success_count += 1
        else:
            print(f"\n⚠️  Stopping execution due to failure in step {step_number}")
            break
    
    print("\n" + "=" * 80)
    print(f"COMPLETED: {success_count}/{len(steps)} steps successful")
    print("=" * 80)
    
    if success_count == len(steps):
        print("\n✅ All steps completed successfully!")
    else:
        print(f"\n⚠️  Analysis incomplete. Please check errors above.")

if __name__ == "__main__":
    main()
