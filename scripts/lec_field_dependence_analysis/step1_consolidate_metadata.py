"""
Step 1: Consolidate Metadata and Build Eligible-Cases Table

Inspects the project to identify:
- Cluster assignments (from kmeans_clustered_data.csv)
- EP cases (from results/ep_structure/ep{1,2,3}_cases.csv)
- Available LEC data per cyclone (from data/temp_lec_zenodo/)

Produces a master table of eligible cyclones that have BOTH:
1. An EP assignment with ≥24h intensification (from ep_structure pipeline)
2. Available LEC Zenodo data with valid intensification-phase records

Output:
  results/lec_field_dependence/step1_eligible_cases.csv
  results/lec_field_dependence/step1_metadata_report.txt

Run:
  python scripts/lec_field_dependence_analysis/step1_consolidate_metadata.py

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import pandas as pd

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, LOG_DIR, LEC_ZENODO_DIR,
    load_all_ep_cases, resolve_csv,
)
from scripts.utils.ep_mapping import EP_LABELS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_CASES = RESULTS_DIR / "step1_eligible_cases.csv"
OUTPUT_REPORT = RESULTS_DIR / "step1_metadata_report.txt"


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step1_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"Log file: {log_file}")


def check_lec_availability(track_id: str) -> bool:
    """Check whether LEC Zenodo data exists for a given cyclone."""
    lec_dir = LEC_ZENODO_DIR / f"{track_id}_ERA5_track"
    if not lec_dir.exists():
        return False
    # Check that the results CSV exists
    results_name = f"{track_id}_ERA5_track_results.csv"
    results_path = resolve_csv(lec_dir / results_name)
    return results_path is not None


def main():
    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 1: CONSOLIDATE METADATA — LEC–FIELD DEPENDENCE ANALYSIS")
    logging.info("=" * 70)

    # 1. Load EP cases (already filtered by ≥24h intensification in ep_structure)
    logging.info("\n1. Loading EP cases from ep_structure pipeline...")
    ep_cases = load_all_ep_cases()
    logging.info(f"   Total EP cases (≥24h filter): {len(ep_cases)}")
    for ep in ALL_EPS:
        n = len(ep_cases[ep_cases["ep"] == ep])
        logging.info(f"   {EP_LABELS[ep]}: {n}")

    # 2. Check LEC availability per cyclone
    logging.info("\n2. Checking LEC Zenodo data availability...")
    ep_cases["lec_available"] = ep_cases["track_id"].apply(
        lambda tid: check_lec_availability(str(tid))
    )
    n_available = ep_cases["lec_available"].sum()
    n_missing = len(ep_cases) - n_available
    logging.info(f"   LEC data available: {n_available} / {len(ep_cases)}")
    logging.info(f"   LEC data missing:   {n_missing}")

    for ep in ALL_EPS:
        subset = ep_cases[ep_cases["ep"] == ep]
        avail = subset["lec_available"].sum()
        logging.info(f"   {EP_LABELS[ep]}: {avail}/{len(subset)} available")

    # 3. Filter to eligible cases
    eligible = ep_cases[ep_cases["lec_available"]].copy()
    eligible = eligible.drop(columns=["lec_available"])
    logging.info(f"\n3. Eligible cases (EP cases with LEC data): {len(eligible)}")

    # 4. Save
    eligible.to_csv(OUTPUT_CASES, index=False)
    logging.info(f"\n   Saved: {OUTPUT_CASES}")

    # 5. Generate metadata report
    report_lines = [
        "=" * 70,
        "LEC–FIELD DEPENDENCE ANALYSIS — Step 1 Metadata Report",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 70,
        "",
        "EP cases (from ep_structure, ≥24h intensification filter):",
    ]
    for ep in ALL_EPS:
        n = len(ep_cases[ep_cases["ep"] == ep])
        report_lines.append(f"  {EP_LABELS[ep]}: {n}")
    report_lines.append(f"  Total: {len(ep_cases)}")
    report_lines.append("")
    report_lines.append("LEC Zenodo data availability:")
    for ep in ALL_EPS:
        subset = ep_cases[ep_cases["ep"] == ep]
        avail = subset["lec_available"].sum()
        miss = len(subset) - avail
        report_lines.append(f"  {EP_LABELS[ep]}: {avail} available, {miss} missing")
    report_lines.append(f"  Total: {n_available} available, {n_missing} missing")
    report_lines.append("")
    report_lines.append("Final eligible sample:")
    for ep in ALL_EPS:
        n = len(eligible[eligible["ep"] == ep])
        report_lines.append(f"  {EP_LABELS[ep]}: {n}")
    report_lines.append(f"  Total: {len(eligible)}")
    report_lines.append("")

    # Missing IDs for audit
    if n_missing > 0:
        missing_ids = ep_cases[~ep_cases["lec_available"]]["track_id"].tolist()
        report_lines.append(f"Missing LEC IDs ({n_missing}):")
        for tid in missing_ids[:50]:
            report_lines.append(f"  {tid}")
        if n_missing > 50:
            report_lines.append(f"  ... and {n_missing - 50} more")

    report_text = "\n".join(report_lines)
    OUTPUT_REPORT.write_text(report_text)
    logging.info(f"   Report: {OUTPUT_REPORT}")

    logging.info("\n✓ Step 1 complete.")


if __name__ == "__main__":
    main()
