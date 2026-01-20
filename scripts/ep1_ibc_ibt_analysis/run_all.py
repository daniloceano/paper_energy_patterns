"""
Run All EP1 Vertical Analysis Steps

This script executes all steps of the EP1 vertical structure and instability
analysis in sequence.

Steps:
1. Select EP1 cyclones within specified domain
2. Analyze LEC data to identify critical pressure levels (Ca max, Ck min)
3. Download ERA5 data at identified levels (should be run separately on server)
4. Compute instability diagnostics (EGR and RK)
5. Consolidate instability results into summary tables
6. Create publication-quality figures 

EXECUTION ORDER:
1. step1_select_cases.py
2. step2_vertical_levels_analysis.py (analyzes existing LEC data)
3. step3_download_era5.py (run separately on server with CDS API)
4. step4_compute_instabilities.py
5. consolidate_instability_results.py
6. step5_create_figures.py 

NOTE: Step 3 (ERA5 download) should be run separately on a remote server
      with appropriate resources and CDS API credentials.

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
    print("NOTE: Step 3 (ERA5 download) is skipped by default.")
    print("      Run step3_download_era5.py separately on a remote server")
    print("      AFTER step2 identifies the critical pressure levels.\n")
    
    steps = [
        (1, "step1_select_cases.py", "Select EP1 Cyclones within Specified Domain"),
        (2, "step2_vertical_levels_analysis.py", "Analyze LEC Data - Identify Critical Levels"),
        (3, "step3_download_era5.py", "Download ERA5 Data at Identified Levels"), # Note: This step should be run separately
        (4, "step4_compute_instabilities.py", "Compute Instability Diagnostics (EGR & RK)"),
        (5, "consolidate_instability_results.py", "Consolidate Results into Summary Tables"),
        (6, "step5_create_figures.py", "Create Publication-Quality Figures"),
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
