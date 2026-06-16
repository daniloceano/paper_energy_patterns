#!/usr/bin/env python3
"""
Run the explosive-cyclone analysis pipeline.

Split between machines:
    REMOTE (heavy): step2 (CDS download, light parallelism) + step3 (A+B, ~100 cores)
    LIGHT (anywhere): step1, step4, step5

By default this runner executes only the LIGHT steps (1, 4, 5), so it is safe to run
locally after `sync_from_remote.sh`. The heavy steps are opt-in to avoid accidentally
launching a 3,820-cyclone download/compute on the wrong machine.

Usage:
    python scripts/explosive_cyclones_analysis/run_all.py                 # step1, 4, 5
    python scripts/explosive_cyclones_analysis/run_all.py --download      # + step2
    python scripts/explosive_cyclones_analysis/run_all.py --process       # + step3
    python scripts/explosive_cyclones_analysis/run_all.py --download --process --workers 100
    python scripts/explosive_cyclones_analysis/run_all.py --download --process --sample 5  # smoke test
"""

import sys
import argparse
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parents[1]
RES = PROJECT_ROOT / "results" / "explosive_cyclones"


def run(script, extra=None):
    cmd = [sys.executable, str(HERE / script)] + (extra or [])
    print(f"\n{'=' * 80}\n▶ {' '.join(cmd[1:])}\n{'=' * 80}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="include step2 (CDS MSLP download)")
    ap.add_argument("--process", action="store_true", help="include step3 (central pressure)")
    ap.add_argument("--jobs", type=int, default=6, help="step2 parallel CDS jobs (keep light)")
    ap.add_argument("--workers", type=int, default=8, help="step3 CPU workers (heavy)")
    ap.add_argument("--sample", type=int, default=0, help="limit cyclones (smoke test)")
    args = ap.parse_args()

    sample = ["--sample", str(args.sample)] if args.sample else []
    plan = [("step1_select_ep_populations.py", [])]
    if args.download:
        plan.append(("step2_download_mslp_tracks.py", ["--jobs", str(args.jobs)] + sample))
    if args.process:
        plan.append(("step3_assign_central_pressure.py", ["--workers", str(args.workers)] + sample))
    plan += [("step4_compute_ndr_classify.py", []),
             ("step5_figures_tables.py", [])]

    failures = {}
    for script, extra in plan:
        # Skip light post-processing if their inputs are absent (e.g. before remote run)
        if script == "step4_compute_ndr_classify.py" and not (RES / "central_pressure_timeseries.csv").exists():
            print(f"\n⚠ Skipping {script}: central_pressure_timeseries.csv not found "
                  "(run step3 on the remote, then sync).")
            continue
        if script == "step5_figures_tables.py" and not (RES / "ndr_by_cyclone.csv").exists():
            print(f"\n⚠ Skipping {script}: ndr_by_cyclone.csv not found.")
            continue
        rc = run(script, extra)
        if rc != 0:
            failures[script] = rc
            print(f"❌ {script} exited with code {rc}")
            break

    print("\n" + "=" * 80)
    print("PIPELINE FINISHED" if not failures else "PIPELINE STOPPED ON ERROR")
    print("=" * 80)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
