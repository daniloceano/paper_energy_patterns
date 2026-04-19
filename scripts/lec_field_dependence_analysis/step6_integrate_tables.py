"""
Step 6: Integrate All Tables into Auditable Datasets

Merges:
- Eligible cases (step1)        → track_id, ep, metadata
- LEC intensification means (step2) → LEC terms per cyclone
- Absolute features (step4)     → scalar features from absolute fields
- Anomaly features (step5)      → scalar features from EPALL-relative fields

Produces a single integrated table per field type:
  - step6_integrated_absolute.csv
  - step6_integrated_anomaly.csv

And a combined superset:
  - step6_integrated_all.csv

Also runs final QA checks.

Output:
  results/lec_field_dependence/step6_integrated_absolute.csv
  results/lec_field_dependence/step6_integrated_anomaly.csv
  results/lec_field_dependence/step6_integrated_all.csv
  results/lec_field_dependence/step6_integration_qa_report.txt

Run:
  python scripts/lec_field_dependence_analysis/step6_integrate_tables.py

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

import argparse

from scripts.lec_field_dependence_analysis.utils_io import RESULTS_DIR, LOG_DIR
from scripts.utils.ep_mapping import EP_LABELS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_CASES = RESULTS_DIR / "step1_eligible_cases.csv"
INPUT_LEC = RESULTS_DIR / "step2_lec_means.csv"
INPUT_ABS = RESULTS_DIR / "step4_features_absolute.csv"
INPUT_ANOM = RESULTS_DIR / "step5_features_anomaly.csv"

OUTPUT_QA = RESULTS_DIR / "step6_integration_qa_report.txt"


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step6_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def merge_chunk_files(base_path: Path) -> pd.DataFrame:
    """
    If chunked execution was used, merge all chunk files into one.
    Looks for base_path (no chunks) or base_path_chunk*.csv files.
    """
    if base_path.exists():
        return pd.read_csv(base_path)

    # Look for chunk files
    pattern = base_path.stem + "_chunk*.csv"
    chunk_files = sorted(base_path.parent.glob(pattern))
    if not chunk_files:
        return pd.DataFrame()

    logging.info(f"   Merging {len(chunk_files)} chunk files for {base_path.name}")
    frames = [pd.read_csv(f) for f in chunk_files]
    merged = pd.concat(frames, ignore_index=True)
    # Save merged file
    merged.to_csv(base_path, index=False)
    logging.info(f"   Merged into {base_path} ({len(merged)} rows)")
    return merged


def main():
    parser = argparse.ArgumentParser(description="Step 6: Integrate all tables.")
    args = parser.parse_args()

    output_abs = RESULTS_DIR / "step6_integrated_absolute.csv"
    output_anom = RESULTS_DIR / "step6_integrated_anomaly.csv"
    output_all = RESULTS_DIR / "step6_integrated_all.csv"

    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 6: INTEGRATE TABLES — LEC–FIELD DEPENDENCE ANALYSIS")
    logging.info("=" * 70)
    logging.info(f"LEC input: {INPUT_LEC.name} (central timesteps, canonical method)")

    # 1. Load source tables
    cases = pd.read_csv(INPUT_CASES)
    cases["track_id"] = cases["track_id"].astype(str)
    logging.info(f"Cases: {len(cases)}")

    lec = pd.read_csv(INPUT_LEC) if INPUT_LEC.exists() else pd.DataFrame()
    if len(lec) > 0:
        lec["track_id"] = lec["track_id"].astype(str)
    logging.info(f"LEC table: {len(lec)} rows")

    abs_feat = merge_chunk_files(INPUT_ABS)
    if len(abs_feat) > 0:
        abs_feat["track_id"] = abs_feat["track_id"].astype(str)
    logging.info(f"Absolute features: {len(abs_feat)} rows")

    anom_feat = merge_chunk_files(INPUT_ANOM)
    if len(anom_feat) > 0:
        anom_feat["track_id"] = anom_feat["track_id"].astype(str)
    logging.info(f"Anomaly features: {len(anom_feat)} rows")

    # 2. Identify key metadata columns to keep from cases
    meta_cols = ["track_id", "ep", "intensification_start", "intensification_end",
                 "duration_hours", "center_lat", "center_lon"]
    meta_cols = [c for c in meta_cols if c in cases.columns]
    cases_meta = cases[meta_cols].copy()

    # 3. Merge: cases + LEC
    if len(lec) > 0:
        base = cases_meta.merge(lec, on="track_id", how="inner")
        logging.info(f"Cases × LEC intersection: {len(base)}")
    else:
        base = cases_meta.copy()
        logging.warning("No LEC data available — using cases only")

    # 4. Merge with absolute features
    if len(abs_feat) > 0:
        integrated_abs = base.merge(abs_feat, on="track_id", how="inner")
        logging.info(f"Integrated (absolute): {len(integrated_abs)} rows")
    else:
        integrated_abs = pd.DataFrame()
        logging.warning("No absolute features available")

    # 5. Merge with anomaly features
    if len(anom_feat) > 0:
        integrated_anom = base.merge(anom_feat, on="track_id", how="inner")
        logging.info(f"Integrated (anomaly): {len(integrated_anom)} rows")
    else:
        integrated_anom = pd.DataFrame()
        logging.warning("No anomaly features available")

    # 6. Save
    if len(integrated_abs) > 0:
        integrated_abs.to_csv(output_abs, index=False)
        logging.info(f"   Saved: {output_abs}")
    if len(integrated_anom) > 0:
        integrated_anom.to_csv(output_anom, index=False)
        logging.info(f"   Saved: {output_anom}")

    # Combined: all features in one table
    if len(abs_feat) > 0 and len(anom_feat) > 0:
        all_feat = abs_feat.merge(anom_feat, on="track_id", how="outer")
        integrated_all = base.merge(all_feat, on="track_id", how="inner")
        integrated_all.to_csv(output_all, index=False)
        logging.info(f"   Saved: {output_all} ({len(integrated_all)} rows)")
    elif len(integrated_abs) > 0:
        integrated_abs.to_csv(output_all, index=False)

    # 7. QA report
    qa = _generate_qa_report(cases, lec, abs_feat, anom_feat,
                             integrated_abs, integrated_anom)
    OUTPUT_QA.write_text(qa)
    logging.info(f"   QA report: {OUTPUT_QA}")
    logging.info("\n✓ Step 6 complete.")


def _generate_qa_report(cases, lec, abs_feat, anom_feat, int_abs, int_anom) -> str:
    lines = [
        "=" * 70,
        "LEC–FIELD DEPENDENCE ANALYSIS — Step 6 Integration QA",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 70,
        "",
        "Source table sizes:",
        f"  Eligible cases:     {len(cases)}",
        f"  LEC table:          {len(lec)}",
        f"  Absolute features:  {len(abs_feat)}",
        f"  Anomaly features:   {len(anom_feat)}",
        "",
        "Integrated table sizes:",
        f"  Absolute integrated: {len(int_abs)}",
        f"  Anomaly integrated:  {len(int_anom)}",
        "",
    ]

    # Coverage per EP
    for df, label in [(int_abs, "Absolute"), (int_anom, "Anomaly")]:
        if len(df) == 0:
            continue
        lines.append(f"Coverage per EP ({label}):")
        for ep in ALL_EPS:
            n = len(df[df["ep"] == ep])
            lines.append(f"  {EP_LABELS[ep]}: {n}")
        lines.append(f"  Total: {len(df)}")
        lines.append("")

    # Feature completeness
    for df, label in [(int_abs, "Absolute"), (int_anom, "Anomaly")]:
        if len(df) == 0:
            continue
        feature_cols = [c for c in df.columns if "__" in c]
        lines.append(f"Feature completeness ({label}, {len(feature_cols)} features):")
        n_all_nan = 0
        for col in feature_cols:
            pct = df[col].notna().mean() * 100
            if pct < 100:
                lines.append(f"  {col}: {pct:.1f}% valid")
            if df[col].isna().all():
                n_all_nan += 1
        lines.append(f"  Features with all NaN: {n_all_nan}")
        lines.append("")

        # Degenerate features (constant or near-constant)
        lines.append(f"Degenerate features ({label}, std < 1e-10):")
        n_degen = 0
        for col in feature_cols:
            if df[col].std() < 1e-10:
                lines.append(f"  ⚠ {col}")
                n_degen += 1
        if n_degen == 0:
            lines.append("  None")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
