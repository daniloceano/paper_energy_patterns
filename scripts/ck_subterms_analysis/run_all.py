#!/usr/bin/env python3
"""
Run all Ck subterms analysis scripts in sequence.

Prerequisites:
- scripts/ep1_ibc_ibt_analysis/step1_select_cases.py must be run first

Usage:
    python scripts/ck_subterms_analysis/run_all.py
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parents[1]

# Define script execution order
SCRIPTS = [
    'step1_prepare_tracks.py',
    'step2_run_lec_toolkit.py',
    # Add more steps as they are created:
    # 'step3_extract_subterms.py',
    # 'step4_lifecycle_analysis.py',
    # 'step5_statistical_analysis.py',
]


def main():
    print("\n" + "=" * 80)
    print("Running Ck Subterms Analysis Pipeline")
    print("=" * 80)
    
    # Check prerequisites
    required_file = PROJECT_ROOT / "results" / "ep1_vertical" / "selected_cases.csv"
    if not required_file.exists():
        print(f"\n❌ Error: Required file not found: {required_file}")
        print("\nPlease run the EP1 selection analysis first:")
        print("   python scripts/ep1_ibc_ibt_analysis/step1_select_cases.py")
        return 1
    
    successes = []
    failures = {}
    
    for i, script_name in enumerate(SCRIPTS, start=1):
        script_path = HERE / script_name
        
        if not script_path.exists():
            print(f"\n⚠ Skipping {script_name} (not yet implemented)")
            continue
        
        print(f"\n{'='*80}")
        print(f"[{i}/{len(SCRIPTS)}] Running: {script_name}")
        print(f"{'='*80}")
        
        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                timeout=3600  # 1 hour timeout per script
            )
            
            if proc.returncode == 0:
                successes.append(script_name)
                print(f"\n✅ Completed successfully: {script_name}")
            else:
                failures[script_name] = f"Exit code {proc.returncode}"
                print(f"\n❌ Failed with exit code {proc.returncode}: {script_name}")
                
        except subprocess.TimeoutExpired:
            failures[script_name] = "Timeout (>1 hour)"
            print(f"\n⏱️  Timeout: {script_name}")
            
        except Exception as e:
            failures[script_name] = str(e)
            print(f"\n🔥 Error running {script_name}: {e}")
            traceback.print_exc()
    
    # Final summary
    print("\n\n" + "="*80)
    print("FINAL SUMMARY - Ck Subterms Analysis")
    print("="*80)
    
    print(f"\n✅ Successful ({len(successes)}):")
    if successes:
        for s in successes:
            print(f"   ✓ {s}")
    else:
        print("   (none)")
    
    print(f"\n❌ Failed ({len(failures)}):")
    if failures:
        for f, reason in failures.items():
            print(f"   ✗ {f}: {reason}")
    else:
        print("   (none)")
    
    print("\n" + "="*80)
    print("Pipeline finished")
    print("="*80 + "\n")
    
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
