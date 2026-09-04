#!/usr/bin/env python3
"""
Run the Ck subterms analysis for every Energy Pattern.

The pipeline no longer launches LorenzCycleToolKit: the corrected climatology
rerun already computed ``Ck_1`` .. ``Ck_5`` for all 3,820 cyclones, so the
decomposition is read from its products rather than recomputed for a subset.
The scripts that drove the old EP1-only side run live in
``deprecated_ep1_side_run/`` and must not be executed again -- they write into
``results/ck_analysis/``, which holds superseded results.

Prerequisites
-------------
1. The corrected rerun is COMPLETE, and
   ``scripts/lec_climatology_rerun/build_corrected_vertical_levels.py`` has
   produced ``data/corrected/vertical_phase_means_corrected.parquet``.
2. The clustering has been rebuilt on the corrected energy cache, so
   ``results/cluster/cluster_to_ep.json`` describes the corrected run.

Usage
-----
    python scripts/ck_subterms_analysis/run_all.py
    python scripts/ck_subterms_analysis/run_all.py --allow-partial   # exploratory
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import ep_mapping as em  # noqa: E402

#: Steps in execution order, with the ones that accept --allow-partial.
STEPS = [
    ("step1_build_subterms_table.py", True),
    ("step2_subterm_statistics.py", False),
    ("step3_subterm_figures.py", True),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the all-EP Ck subterms pipeline.")
    parser.add_argument(
        "--allow-partial", action="store_true",
        help="accept a partial rerun build; exploratory only, never for the paper",
    )
    args = parser.parse_args()

    print("=" * 78)
    print(" Ck subterms analysis — all Energy Patterns (corrected climatology)")
    print("=" * 78)

    try:
        lineage = em.mapping_source()
    except em.ClusterMappingMissing as error:
        print(f"\nERROR: {error}")
        return 1
    print(f"\nEnergy Pattern lineage: {lineage}")
    if not em.is_corrected_clustering() and not args.allow_partial:
        print(
            "\nERROR: the clustering on disk was not built from the corrected LEC\n"
            "cache. Rebuild it with\n"
            "  python scripts/cluster_analysis_energy_patterns/run_all.py\n"
            "or pass --allow-partial for an explicitly exploratory run."
        )
        return 1

    failures: dict[str, str] = {}
    for index, (script, supports_partial) in enumerate(STEPS, start=1):
        command = [sys.executable, str(HERE / script)]
        if args.allow_partial and supports_partial:
            command.append("--allow-partial")

        print(f"\n{'=' * 78}\n[{index}/{len(STEPS)}] {script}\n{'=' * 78}")
        result = subprocess.run(command, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            failures[script] = f"exit code {result.returncode}"
            print(f"\nFAILED: {script}")
            break

    print(f"\n{'=' * 78}")
    if failures:
        for script, reason in failures.items():
            print(f"  FAILED  {script}: {reason}")
        return 1
    print("  All steps completed.")
    print("  Results: results/ck_subterms_corrected/")
    print("  Figures: figures/ck_subterms_corrected/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
