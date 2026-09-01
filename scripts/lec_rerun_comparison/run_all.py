#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py — Run the whole legacy vs corrected LEC comparison.

Executes steps 1, 2, 3, 5, 6, 4 and 7 in order, with step 6 repeated for EOF 1
to 4. The report is written after the figures it quotes, and the PDF after the
report. Safe to re-run at any time while the rerun is
still in progress: step 1 picks up the cyclones that have become COMPLETE since
the last call and every downstream product is regenerated from scratch.

Usage
-----
    python scripts/lec_rerun_comparison/run_all.py
    python scripts/lec_rerun_comparison/run_all.py --run-root /path/to/run --refresh

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_DIR = HERE.parents[1]

# (script, extra arguments). Step 6 runs once per EOF mode, reproducing
# Figures 5-8 of the Clim. Dyn. article.
STEPS = [
    ("step1_build_comparison_table.py", []),
    ("step2_plot_split_violins.py", []),
    ("step3_summary_stats.py", []),
    ("step5_plot_lec_diagram.py", []),
    *[("step6_plot_eof_diagram.py", ["--eof", str(mode)]) for mode in (1, 2, 3, 4)],
    ("step4_write_report.py", []),
    ("step7_build_report_pdf.py", []),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    for step, extra in STEPS:
        command = [sys.executable, str(HERE / step), *extra]
        if step.startswith("step1"):
            if args.run_root:
                command += ["--run-root", str(args.run_root)]
            if args.refresh:
                command += ["--refresh"]
        print(f"\n{'=' * 70}\n{' '.join([step, *extra])}\n{'=' * 70}")
        result = subprocess.run(command, cwd=BASE_DIR)
        if result.returncode != 0:
            print(f"\n{step} failed with exit code {result.returncode}")
            return result.returncode
    print("\nAll steps completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
