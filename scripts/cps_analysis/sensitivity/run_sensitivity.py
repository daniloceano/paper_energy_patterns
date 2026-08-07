"""
Run the CPS SENSITIVITY tests (not the canonical analysis).

These are the exploratory runs that established the methodology: six threshold
sets crossed with four identification rules, the warm-seclusion diagnosis, and
the documented-case check. They are kept for reference and for the paper's
sensitivity section. The canonical classification lives in
`scripts/cps_analysis/step2_classify_phases.py` and downstream.

Requires `results/cps_analysis/cps_timesteps.csv` from step 1 of the canonical
pipeline.

Run:
    python scripts/cps_analysis/sensitivity/run_sensitivity.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

STEPS = [
    ("s1_classify_cyclone_types.py", "Six threshold sets x four identification rules"),
    ("s2_ep_crosstab.py", "Energy Pattern x thermal type"),
    ("s3_lifecycle_timing.py", "Life-cycle timing / warm-seclusion diagnosis"),
    ("s4_distributions.py", "Distributions by type and Energy Pattern"),
    ("s5_episodes_and_cases.py", "Episode dates and documented-case check"),
]


def main():
    for script, description in STEPS:
        print("\n" + "#" * 70)
        print(f"# {script} — {description}")
        print("#" * 70)
        result = subprocess.run([sys.executable, str(SCRIPT_DIR / script)])
        if result.returncode != 0:
            print(f"\n{script} failed (exit {result.returncode}). Stopping.")
            return result.returncode

    print("\n" + "#" * 70)
    print("# Pipeline complete")
    print("#" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
