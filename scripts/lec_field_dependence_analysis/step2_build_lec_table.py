"""
Step 2: Build LEC Energetics Table per Cyclone

For each eligible cyclone (from step1), loads the full LEC time series
from Zenodo, filters to the intensification phase, and computes the
mean value of each LEC term over the central timesteps.

Temporal selection follows the canonical ep_structure methodology:
  - Odd  N timesteps → mean of 3 central timesteps
  - Even N timesteps → mean of 2 central timesteps
  - N ≤ 3            → mean of all timesteps

This ensures temporal consistency between LEC values and the ERA5
dynamic fields used in subsequent steps (which are extracted at the
single central timestep of the intensification phase).

The result is a single table:
    track_id × LEC_term

Output:
  results/lec_field_dependence/step2_lec_means.csv
  results/lec_field_dependence/step2_lec_qa_report.txt

Run:
  python scripts/lec_field_dependence_analysis/step2_build_lec_table.py

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, LOG_DIR,
    load_lec_from_zenodo,
    LEC_TERMS_FULL, LEC_TERMS_CORE,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_CASES = RESULTS_DIR / "step1_eligible_cases.csv"
OUTPUT_LEC = RESULTS_DIR / "step2_lec_means.csv"
OUTPUT_QA = RESULTS_DIR / "step2_lec_qa_report.txt"
N_WORKERS = 8   # Adjust for your system; set to 1 for serial


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step2_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"Log file: {log_file}")


def _load_one(track_id: str):
    """Worker: central-timestep mean (canonical ep_structure method)."""
    df = load_lec_from_zenodo(track_id)
    if df is not None:
        return track_id, df
    return track_id, None


def main():
    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 2: BUILD LEC TABLE — LEC–FIELD DEPENDENCE ANALYSIS")
    logging.info("=" * 70)
    logging.info("Temporal method: central timesteps (canonical ep_structure rule)")
    logging.info("  Odd  N → mean of 3 central timesteps")
    logging.info("  Even N → mean of 2 central timesteps")

    # 1. Load eligible cases
    cases = pd.read_csv(INPUT_CASES)
    track_ids = cases["track_id"].astype(str).tolist()
    logging.info(f"Eligible cases: {len(track_ids)}")

    # 2. Load LEC data (parallel)
    logging.info(f"\nLoading LEC central means (workers={N_WORKERS})...")
    results = {}
    failed = []

    if N_WORKERS > 1:
        with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
            futures = {executor.submit(_load_one, tid): tid for tid in track_ids}
            for i, future in enumerate(as_completed(futures), 1):
                tid, df = future.result()
                if df is not None:
                    results[tid] = df
                else:
                    failed.append(tid)
                if i % 200 == 0:
                    logging.info(f"   Loaded {i}/{len(track_ids)}...")
    else:
        for i, tid in enumerate(track_ids, 1):
            _, df = _load_one(tid)
            if df is not None:
                results[tid] = df
            else:
                failed.append(tid)
            if i % 200 == 0:
                logging.info(f"   Loaded {i}/{len(track_ids)}...")

    logging.info(f"   Successfully loaded: {len(results)}")
    logging.info(f"   Failed to load: {len(failed)}")

    # 3. Concatenate
    if len(results) == 0:
        logging.error("No LEC data loaded. Aborting.")
        return

    lec_df = pd.concat(results.values(), ignore_index=False)
    lec_df.index.name = "track_id"
    lec_df = lec_df.reset_index()

    # Identify available LEC terms
    available_terms = [col for col in lec_df.columns if col != "track_id"]
    logging.info(f"\n   Available LEC terms: {len(available_terms)}")
    for t in available_terms:
        n_valid = lec_df[t].notna().sum()
        logging.info(f"      {t}: {n_valid}/{len(lec_df)} valid")

    # 4. Save
    lec_df.to_csv(OUTPUT_LEC, index=False)
    logging.info(f"\n   Saved: {OUTPUT_LEC}")

    # 5. QA report
    qa_lines = [
        "=" * 70,
        "LEC–FIELD DEPENDENCE ANALYSIS — Step 2 QA Report",
        f"Generated: {datetime.now().isoformat()}",
        "Temporal method: central timesteps (canonical ep_structure rule)",
        "=" * 70,
        "",
        f"Input eligible cases: {len(track_ids)}",
        f"Successfully loaded:  {len(results)}",
        f"Failed to load:       {len(failed)}",
        "",
        "Available LEC terms and coverage:",
    ]
    for t in available_terms:
        n_valid = lec_df[t].notna().sum()
        n_nan = lec_df[t].isna().sum()
        mean = lec_df[t].mean()
        std = lec_df[t].std()
        qa_lines.append(f"  {t:30s}  valid={n_valid:5d}  nan={n_nan:4d}  "
                        f"mean={mean:12.4f}  std={std:12.4f}")

    qa_lines.append("")
    qa_lines.append("Core LEC terms (used in original PCA clustering):")
    for t in LEC_TERMS_CORE:
        if t in available_terms:
            qa_lines.append(f"  ✓ {t}")
        else:
            qa_lines.append(f"  ✗ {t} (NOT FOUND)")

    qa_lines.append("")
    qa_lines.append("Constant or degenerate terms (std < 1e-10):")
    for t in available_terms:
        if lec_df[t].std() < 1e-10:
            qa_lines.append(f"  ⚠ {t} is constant — will be excluded from PREDEP")

    if failed:
        qa_lines.append("")
        qa_lines.append(f"Failed track IDs ({len(failed)}):")
        for tid in failed[:30]:
            qa_lines.append(f"  {tid}")
        if len(failed) > 30:
            qa_lines.append(f"  ... and {len(failed) - 30} more")

    OUTPUT_QA.write_text("\n".join(qa_lines))
    logging.info(f"   QA report: {OUTPUT_QA}")
    logging.info("\n✓ Step 2 complete.")


if __name__ == "__main__":
    main()
