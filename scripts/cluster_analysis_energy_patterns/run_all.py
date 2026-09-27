#!/usr/bin/env python3
import os
import shutil
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ME = os.path.basename(__file__)

def main():
    print("\n✨ Running all scripts in 'cluster' — let's go! ✨\n")
    py_files = sorted([f for f in os.listdir(HERE) if f.endswith('.py') and f not in ('__init__.py', ME)])
    successes = []
    failures = {}
    skipped = []
    default_timeout = 1800
    timeouts = {
        # Reval runs 10 repeated 5-fold CV iterations for every k=3..15 and
        # can legitimately exceed the former global 30-minute limit.
        'step3_optimal_k_analysis.py': 7200,
    }

    for i, fname in enumerate(py_files, start=1):
        path = os.path.join(HERE, fname)
        print(f"\n{'='*70}")
        print(f"🔸 [{i}/{len(py_files)}] Running: {fname}")
        print(f"{'='*70}")
        if fname == 'step6_generate_scientific_notes_pdf.py' and shutil.which('pandoc') is None:
            skipped.append(fname)
            print("⏭️  Skipped optional notes PDF: pandoc is not installed.")
            continue
        try:
            # Don't capture output - let it flow to terminal (allows user input).
            timeout = timeouts.get(fname, default_timeout)
            proc = subprocess.run([sys.executable, path], cwd=HERE, timeout=timeout)
            if proc.returncode == 0:
                successes.append(fname)
                print(f"\n✅ Completed successfully: {fname}")
            else:
                failures[fname] = f"Exit code {proc.returncode}"
                print(f"\n❌ Failed with exit code {proc.returncode}: {fname}")
                print("⛔ Stopping: later steps depend on this output.")
                break
        except subprocess.TimeoutExpired:
            failures[fname] = f"Timeout (>{timeout}s)"
            print(f"\n⏱️  Timeout: {fname}")
            print("⛔ Stopping: later steps must not reuse stale outputs.")
            break
        except Exception as e:
            failures[fname] = str(e)
            print(f"\n🔥 Error running {fname}: {e}")
            print("⛔ Stopping: later steps must not reuse stale outputs.")
            break

    # Final summary
    print("\n\n" + "="*70)
    print("📋 FINAL SUMMARY — cluster")
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

    print(f"\n⏭️  Skipped optional ({len(skipped)}):")
    if skipped:
        for item in skipped:
            print(f"   • {item}")
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
    print("🎉 Execution finished for 'cluster'")
    print("="*70 + "\n")
    
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
