"""
Run the CANONICAL CPS analysis pipeline.

Assumes the per-cyclone CPS CSVs already exist in `csv_output/` (A. Rodriguez).
The sensitivity tests that established this methodology are run separately with
`sensitivity/run_sensitivity.py`.

Run:
    python scripts/cps_analysis/run_all.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Steps that accept --jobs (parallel over cyclones / over figures).
PARALLEL = {"step2_classify_phases.py", "step7_case_diagrams.py"}

STEPS = [
    ("make_reference_diagram.py", "Reference diagram of the class regions"),
    ("step1_build_cps_database.py", "Consolidate per-cyclone CPS CSVs"),
    ("step2_classify_phases.py", "Persistence-gated phase classification"),
    ("step3_ep_phases.py", "Energy Pattern x phase class"),
    ("step4_phase_figures.py", "Figures"),
    ("step5_phase_space_figures.py", "Phase-space diagrams by Energy Pattern"),
    ("step6_transition_trajectories.py", "Transition trajectories in the phase space"),
    ("step7_case_diagrams.py", "Individual CPS case diagrams (sampled gallery)"),
    ("step8_ep_relative_frequency.py", "Subtropical frequency by EP, relative to EPALL"),
]


def main(jobs: int = 1):
    for script, description in STEPS:
        print("\n" + "#" * 70)
        print(f"# {script} — {description}")
        print("#" * 70)
        cmd = [sys.executable, str(SCRIPT_DIR / script)]
        if jobs > 1 and script in PARALLEL:
            cmd += ["--jobs", str(jobs)]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"\n{script} failed (exit {result.returncode}). Stopping.")
            return result.returncode

    print("\n" + "#" * 70)
    print("# Canonical pipeline complete")
    print("#" * 70)
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Run the canonical CPS pipeline.")
    ap.add_argument("--jobs", "-j", type=int, default=1,
                    help="workers for the parallelisable steps (2 and 7). "
                         "Results are identical regardless of this value.")
    sys.exit(main(jobs=ap.parse_args().jobs))
