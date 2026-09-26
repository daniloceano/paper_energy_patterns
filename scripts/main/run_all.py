#!/usr/bin/env python3
import os
import sys
import subprocess
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ME = os.path.basename(__file__)

# Execution order is explicit so filenames can remain independent of manuscript
# figure numbering. Update this list only when pipeline dependencies change.
SCRIPT_ORDER = [
    "figure_tracks_genesis_frequency.py",
    "figure_20070643_publication.py",
    "make_phase_density_2x2.py",
    "figure_lps_combined.py",
    "figure_vertical_levels.py",
    "figure_intensity_seasonality_trends.py",
    "figure_genesis_density_kde.py",
    "figure_ep1_ep2_dynamical_composites.py",
    "figure_pearson_epall_by_field_type.py",
    "figure_pca_clustering_validation.py",
    "figure_pairwise_effectsize_lec_terms.py",
    "figure_ck_subterms_vertical_profiles.py",
    "figure_pairwise_effectsize_composite_scalars.py",
]

def main():
    print("\n✨ Running all scripts in 'main' — let's go! ✨\n")
    missing = [fname for fname in SCRIPT_ORDER if not os.path.exists(os.path.join(HERE, fname))]
    if missing:
        print("Missing scripts declared in SCRIPT_ORDER:")
        for fname in missing:
            print(f"   - {fname}")
        return 1

    py_files = SCRIPT_ORDER
    successes = []
    failures = {}

    for i, fname in enumerate(py_files, start=1):
        path = os.path.join(HERE, fname)
        print(f"\n{'='*70}")
        print(f"▶️  [{i}/{len(py_files)}] Running: {fname}")
        print(f"{'='*70}")
        try:
            # Don't capture output - let it flow to terminal (allows user input)
            timeout = 1800  # 30 minutes
            proc = subprocess.run([sys.executable, path], cwd=HERE, timeout=timeout)
            if proc.returncode == 0:
                successes.append(fname)
                print(f"\n✅ Completed successfully: {fname}")
            else:
                failures[fname] = f"Exit code {proc.returncode}"
                print(f"\n❌ Failed with exit code {proc.returncode}: {fname}")
        except subprocess.TimeoutExpired:
            failures[fname] = f"Timeout (>{timeout}s)"
            print(f"\n⏱️  Timeout: {fname}")
        except Exception as e:
            tb = traceback.format_exc()
            failures[fname] = str(e)
            print(f"\n🔥 Error running {fname}: {e}")

    # Final summary
    print("\n\n" + "="*70)
    print("📋 FINAL SUMMARY — main")
    print("="*70)
    
    print(f"\n✅ Successful ({len(successes)}):")
    if successes:
        for s in successes:
            print(f"   ✓ {s}")
    else:
        print("   (none)")
    
    print(f"\n❌ Failed ({len(failures)}):")
    if failures:
        for f in failures.keys():
            print(f"   ✗ {f}")
    else:
        print("   (none)")

    # Error details
    if failures:
        print("\n" + "="*70)
        print("🔎 ERROR DETAILS")
        print("="*70)
        for fname, reason in failures.items():
            print(f"\n📌 {fname}:")
            print(f"   {reason}")

    print("\n" + "="*70)
    print("🎉 Execution finished for 'main'")
    print("="*70 + "\n")
    
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
