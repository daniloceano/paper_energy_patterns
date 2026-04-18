"""
Step 3: Map Available Per-Cyclone ERA5 Fields

This step verifies which cyclones have ERA5 fields available on the
remote server.  Because per-cyclone ERA5 data is NOT stored locally
(only group-mean composites exist in data/era5_ep_structure/), this
step provides a **mapping framework** that:

1. Lists expected per-cyclone ERA5 field files
2. Checks whether they exist (on local or remote filesystem)
3. Builds a manifest of available fields per cyclone

--- IMPORTANT: REMOTE EXECUTION REQUIRED ---

The per-cyclone ERA5 fields (storm-centred 30°×30° domains) are produced
by the ep_structure_analysis pipeline (step2_download_era5_parallel.py)
and reside ONLY on the HPC/remote server.  They are NOT in this local
repository.

When running this step on the remote server, set ERA5_FIELDS_DIR to
the directory containing the per-cyclone ERA5 NetCDF files.

When running locally (dry-run mode), the script reports how many
cyclones WOULD need ERA5 fields and generates a manifest template.

Output:
  results/lec_field_dependence/step3_era5_field_manifest.csv
  results/lec_field_dependence/step3_field_mapping_report.txt

Run (local dry-run):
  python scripts/lec_field_dependence_analysis/step3_map_era5_fields.py

Run (remote, with data):
  python scripts/lec_field_dependence_analysis/step3_map_era5_fields.py \\
      --era5-dir /path/to/era5_per_cyclone/

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import pandas as pd

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, LOG_DIR, ERA5_EP_DIR,
    DYNAMIC_FIELDS_ABSOLUTE, DYNAMIC_FIELDS_ANOMALY,
)
from scripts.utils.ep_mapping import EP_LABELS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_CASES = RESULTS_DIR / "step1_eligible_cases.csv"
OUTPUT_MANIFEST = RESULTS_DIR / "step3_era5_field_manifest.csv"
OUTPUT_REPORT = RESULTS_DIR / "step3_field_mapping_report.txt"

# Expected per-cyclone ERA5 file naming convention
# (adapt to match the ep_structure_analysis download output)
ERA5_FILE_PATTERN = "{track_id}_era5.nc"


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step3_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"Log file: {log_file}")


def check_era5_exists(track_id: str, era5_dir: Path) -> bool:
    """Check if era5 field file exists for a cyclone."""
    fname = ERA5_FILE_PATTERN.format(track_id=track_id)
    return (era5_dir / fname).exists()


def main():
    parser = argparse.ArgumentParser(
        description="Map per-cyclone ERA5 field availability"
    )
    parser.add_argument(
        "--era5-dir", type=Path, default=None,
        help="Directory containing per-cyclone ERA5 NetCDFs. "
             "If not provided, runs in dry-run mode."
    )
    args = parser.parse_args()

    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 3: MAP ERA5 FIELDS — LEC–FIELD DEPENDENCE ANALYSIS")
    logging.info("=" * 70)

    # 1. Load eligible cases
    cases = pd.read_csv(INPUT_CASES)
    logging.info(f"Eligible cases: {len(cases)}")

    # 2. Check ERA5 availability
    dry_run = args.era5_dir is None
    if dry_run:
        logging.info("\n⚠  DRY-RUN MODE (no --era5-dir provided)")
        logging.info("   Per-cyclone ERA5 fields are only on the remote server.")
        logging.info("   Generating manifest template with all cases marked as pending.")
        cases["era5_available"] = False
        cases["era5_path"] = ""
    else:
        era5_dir = args.era5_dir.resolve()
        logging.info(f"\nChecking ERA5 fields in: {era5_dir}")
        available = []
        paths = []
        for _, row in cases.iterrows():
            tid = str(row["track_id"])
            exists = check_era5_exists(tid, era5_dir)
            available.append(exists)
            if exists:
                paths.append(str(era5_dir / ERA5_FILE_PATTERN.format(track_id=tid)))
            else:
                paths.append("")
        cases["era5_available"] = available
        cases["era5_path"] = paths

    n_available = cases["era5_available"].sum()
    n_missing = len(cases) - n_available
    logging.info(f"\n   ERA5 available: {n_available} / {len(cases)}")
    logging.info(f"   ERA5 missing:   {n_missing}")

    for ep in ALL_EPS:
        sub = cases[cases["ep"] == ep]
        avail = sub["era5_available"].sum()
        logging.info(f"   {EP_LABELS[ep]}: {avail}/{len(sub)}")

    # 3. Document temporal representation
    logging.info("\n--- Temporal representation decision ---")
    logging.info("The ep_structure_analysis pipeline uses CENTRAL TIMESTEPS")
    logging.info("(2-3 per cyclone) of the intensification phase.")
    logging.info("The per-cyclone ERA5 files contain data for these central")
    logging.info("timesteps only. The features extracted in step4/step5 will")
    logging.info("represent the MEAN over these central timesteps.")
    logging.info("")
    logging.info("The LEC means (step2) represent the FULL intensification")
    logging.info("phase average. This temporal mismatch is documented in")
    logging.info("SCIENTIFIC_NOTES.md as a known limitation.")

    # 4. Document fields of interest
    logging.info("\n--- Dynamic fields of interest ---")
    logging.info("Absolute fields:")
    for key, var in DYNAMIC_FIELDS_ABSOLUTE.items():
        logging.info(f"   {key} → {var}")
    logging.info("EPALL-relative anomaly fields:")
    for key, var in DYNAMIC_FIELDS_ANOMALY.items():
        logging.info(f"   {key} → {var}")

    # 5. Save manifest
    cases.to_csv(OUTPUT_MANIFEST, index=False)
    logging.info(f"\n   Manifest: {OUTPUT_MANIFEST}")

    # 6. Report
    report_lines = [
        "=" * 70,
        "LEC–FIELD DEPENDENCE ANALYSIS — Step 3 Field Mapping Report",
        f"Generated: {datetime.now().isoformat()}",
        f"Mode: {'DRY-RUN (local)' if dry_run else f'LIVE (era5_dir={args.era5_dir})'}",
        "=" * 70,
        "",
        f"Eligible cases: {len(cases)}",
        f"ERA5 available:  {n_available}",
        f"ERA5 missing:    {n_missing}",
        "",
        "Per EP:",
    ]
    for ep in ALL_EPS:
        sub = cases[cases["ep"] == ep]
        avail = sub["era5_available"].sum()
        report_lines.append(f"  {EP_LABELS[ep]}: {avail}/{len(sub)}")

    report_lines += [
        "",
        "Temporal representation:",
        "  ERA5 fields: central timesteps of intensification (2-3 per cyclone)",
        "  LEC means: full intensification phase average",
        "  Note: this temporal mismatch is a known limitation (see SCIENTIFIC_NOTES.md)",
        "",
        "Dynamic fields (absolute):",
    ]
    for key in DYNAMIC_FIELDS_ABSOLUTE:
        report_lines.append(f"  {key}")
    report_lines.append("")
    report_lines.append("Dynamic fields (EPALL-relative anomaly):")
    for key in DYNAMIC_FIELDS_ANOMALY:
        report_lines.append(f"  {key}")

    OUTPUT_REPORT.write_text("\n".join(report_lines))
    logging.info(f"   Report: {OUTPUT_REPORT}")
    logging.info("\n✓ Step 3 complete.")


if __name__ == "__main__":
    main()
