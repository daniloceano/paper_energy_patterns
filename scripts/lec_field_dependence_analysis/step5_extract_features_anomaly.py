"""
Step 5: Extract Scalar Features from EPALL-Relative Anomaly Fields

Same as step4 but for EPALL-relative anomaly fields.

The per-cyclone EPALL-relative anomaly is computed as:
    field_cyclone_i - EPALL_composite_mean

This requires both:
  1. The per-cyclone ERA5 field (from remote server)
  2. The EPALL composite (from data/era5_ep_structure/precomputed_composites_epall.nc)

--- REMOTE EXECUTION REQUIRED ---

Usage:
  python step5_extract_features_anomaly.py --era5-dir /path/to/era5/
  python step5_extract_features_anomaly.py --era5-dir /path/to/era5/ --chunk 0 --n-chunks 10

Output:
  results/lec_field_dependence/step5_features_anomaly.csv
  (or step5_features_anomaly_chunk{i}.csv if chunked)

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr
from concurrent.futures import ProcessPoolExecutor, as_completed

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, LOG_DIR, ERA5_EP_DIR,
    DYNAMIC_FIELDS_ABSOLUTE,
)
from scripts.lec_field_dependence_analysis.utils_features import (
    extract_all_features, get_feature_names,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_MANIFEST = RESULTS_DIR / "step3_era5_field_manifest.csv"
OUTPUT_BASE = RESULTS_DIR / "step5_features_anomaly"
DERIVED_FILE_PATTERN = "{track_id}_era5_derived.nc"
EPALL_COMPOSITE = ERA5_EP_DIR / "precomputed_composites_epall.nc"
N_WORKERS = 8

# Variables that MUST be in the derived file
REQUIRED_DERIVED_VARS = ["pv_850", "pv_200", "adv_T_850", "ke_adv_250"]
OPTIONAL_DERIVED_VARS = ["afc_250"]

# Global reference: EPALL composite fields (loaded once per process)
_EPALL_FIELDS = {}


def _load_epall_composite():
    """Load EPALL composite fields into memory (called once)."""
    global _EPALL_FIELDS
    if _EPALL_FIELDS:
        return
    logging.info(f"Loading EPALL composite from {EPALL_COMPOSITE}")
    ds = xr.open_dataset(EPALL_COMPOSITE)
    for field_key, var_name in DYNAMIC_FIELDS_ABSOLUTE.items():
        if var_name in ds.data_vars:
            _EPALL_FIELDS[field_key] = ds[var_name].values
        else:
            logging.warning(f"   {var_name} not found in EPALL composite")
    ds.close()
    logging.info(f"   Loaded {len(_EPALL_FIELDS)} EPALL fields")


def setup_logging(chunk_id=None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_chunk{chunk_id}" if chunk_id is not None else ""
    log_file = LOG_DIR / f"lec_field_step5{suffix}_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def extract_anomaly_features_one_cyclone(track_id: str, derived_dir: Path) -> dict:
    """
    Extract scalar features from (field_i - EPALL_composite) for one cyclone.

    Reads from the *derived* NetCDF ({track_id}_era5_derived.nc) produced by
    step 3b.  Required variables must be present; missing required variables
    are hard errors reported clearly in the status field (not silent NaN fill).
    """
    fname = DERIVED_FILE_PATTERN.format(track_id=track_id)
    fpath = derived_dir / fname

    if not fpath.exists():
        return {
            "track_id": track_id,
            "_status": "derived_file_not_found",
            "_note": (
                f"Derived file missing: {fpath}. "
                "Step 3b (step3b_derive_era5_fields.py) must be run first."
            ),
        }

    try:
        ds = xr.open_dataset(fpath)
    except Exception as e:
        return {"track_id": track_id, "_status": f"open_error: {e}"}

    # ── Hard validation: required variables must be present ───────────────
    missing_required = [
        v for v in REQUIRED_DERIVED_VARS if v not in ds.data_vars
    ]
    if missing_required:
        ds.close()
        return {
            "track_id": track_id,
            "_status": f"missing_required_vars: {missing_required}",
            "_note": (
                f"Derived file {fpath.name} is missing required variables. "
                "Re-run step 3b for this cyclone."
            ),
        }

    row = {"track_id": track_id, "_status": "ok"}

    for field_key, var_name in DYNAMIC_FIELDS_ABSOLUTE.items():
        anom_key = f"{field_key}_anom_epall"

        if var_name not in ds.data_vars:
            # Optional field absent (e.g. afc_250 without climatology)
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        if field_key not in _EPALL_FIELDS:
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        # Per-cyclone derived field
        arr = ds[var_name].values
        if arr.ndim == 3:
            arr = np.nanmean(arr, axis=0)
        elif arr.ndim != 2:
            logging.warning(
                f"{track_id}: {var_name} has unexpected shape {arr.shape} — skipping field"
            )
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        # Detect all-NaN fields in derived file
        if np.all(np.isnan(arr)):
            logging.warning(
                f"{track_id}: {var_name} is entirely NaN in derived file — "
                "derivation may have failed for this cyclone"
            )

        # Compute anomaly: cyclone_i - EPALL
        epall_arr = _EPALL_FIELDS[field_key]
        if arr.shape != epall_arr.shape:
            logging.warning(
                f"{track_id}: shape mismatch for {var_name}: "
                f"derived={arr.shape}, EPALL={epall_arr.shape}"
            )
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        anomaly = arr - epall_arr
        features = extract_all_features(anomaly)
        for feat_name, feat_val in features.items():
            row[f"{anom_key}__{feat_name}"] = feat_val

    ds.close()
    return row


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract scalar features from EPALL-relative anomaly fields "
            "(requires step 3b output: *_era5_derived.nc)."
        )
    )
    parser.add_argument(
        "--era5-dir", type=Path, required=True,
        help="Directory with raw per-cyclone ERA5 NetCDFs (used for manifest reference).",
    )
    parser.add_argument(
        "--derived-dir", type=Path, default=None,
        help=(
            "Directory with derived per-cyclone NetCDFs (*_era5_derived.nc). "
            "Default: {era5-dir}/derived/  (same default as step 3b)."
        ),
    )
    parser.add_argument("--chunk", type=int, default=None)
    parser.add_argument("--n-chunks", type=int, default=None)
    parser.add_argument("--workers", type=int, default=N_WORKERS)
    args = parser.parse_args()

    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    setup_logging(args.chunk)

    era5_dir = args.era5_dir.resolve()
    derived_dir = (args.derived_dir or era5_dir / "derived").resolve()

    logging.info("=" * 70)
    logging.info("STEP 5: EXTRACT ANOMALY FEATURES — LEC–FIELD DEPENDENCE")
    logging.info("=" * 70)
    logging.info(f"ERA5 raw dir  : {era5_dir}")
    logging.info(f"Derived dir   : {derived_dir}")

    # Guard: derived directory must exist (step 3b must have been run)
    if not derived_dir.exists():
        logging.error(
            f"CRITICAL: Derived directory does not exist: {derived_dir}\n"
            f"Step 3b (step3b_derive_era5_fields.py) must be run before step 5.\n"
            f"Run: python step3b_derive_era5_fields.py --era5-dir {era5_dir} "
            f"--derived-dir {derived_dir}"
        )
        sys.exit(1)

    n_derived = len(list(derived_dir.glob("*_era5_derived.nc")))
    if n_derived == 0:
        logging.error(
            f"CRITICAL: Derived directory exists but contains no *_era5_derived.nc files: "
            f"{derived_dir}\nStep 3b must be run first to generate derived fields."
        )
        sys.exit(1)
    logging.info(f"Derived files : {n_derived} found in {derived_dir}")

    # Load EPALL composite
    _load_epall_composite()

    # 1. Load manifest
    manifest = pd.read_csv(INPUT_MANIFEST)
    if "era5_available" in manifest.columns:
        n_available = manifest["era5_available"].sum()
        n_total = len(manifest)
        if n_available == 0:
            logging.warning(
                f"Manifest has {n_total} cases but ALL are marked era5_available=False. "
                "This usually means step3 ran in dry-run mode (without --era5-dir). "
                "Proceeding without filtering — missing files will be handled individually."
            )
        else:
            manifest = manifest[manifest["era5_available"]]
    track_ids = manifest["track_id"].astype(str).tolist()
    logging.info(f"Total cases: {len(track_ids)}")

    # 2. Chunking
    if args.chunk is not None and args.n_chunks is not None:
        chunks = np.array_split(track_ids, args.n_chunks)
        track_ids = list(chunks[args.chunk])
        logging.info(f"Chunk {args.chunk}/{args.n_chunks}: {len(track_ids)} cases")

    # 3. Resume support
    output_path = Path(f"{OUTPUT_BASE}{chunk_suffix}.csv")
    processed_ids = set()
    if output_path.exists():
        existing = pd.read_csv(output_path)
        processed_ids = set(existing["track_id"].astype(str).tolist())
        track_ids = [tid for tid in track_ids if tid not in processed_ids]
        logging.info(f"Already processed: {len(processed_ids)}, remaining: {len(track_ids)}")

    if len(track_ids) == 0:
        logging.info("Nothing to process.")
        return

    # 4. Extract features (serial — EPALL fields are in global memory,
    #    not safe for ProcessPoolExecutor without explicit init_worker)
    if args.workers > 1:
        logging.warning(
            f"--workers={args.workers} was requested but step 5 runs serially "
            "because _EPALL_FIELDS is in global memory. Use orchestrator chunking "
            "for parallelism (--chunk / --n-chunks)."
        )
    logging.info(f"\nExtracting anomaly features from derived files...")
    results = []
    for i, tid in enumerate(track_ids, 1):
        row = extract_anomaly_features_one_cyclone(tid, derived_dir)
        results.append(row)
        if i % 100 == 0:
            logging.info(f"   Processed {i}/{len(track_ids)}...")

    # 5. Save
    new_df = pd.DataFrame(results)
    n_ok = (new_df["_status"] == "ok").sum()
    n_fail = (new_df["_status"] != "ok").sum()
    logging.info(f"\n   Success: {n_ok}, Failed: {n_fail}")

    if n_fail > 0:
        logging.info("\n   Failure breakdown:")
        for status, count in new_df["_status"].value_counts().items():
            if status != "ok":
                logging.warning(f"      {status}: {count}")
        n_missing_derived = (new_df["_status"] == "derived_file_not_found").sum()
        n_missing_vars = new_df["_status"].str.startswith("missing_required_vars").sum()
        if n_missing_derived > 0:
            logging.error(
                f"   ERROR: {n_missing_derived} cyclones have no derived file "
                f"(*_era5_derived.nc) in {derived_dir}.\n"
                f"   Root cause: step 3b was not run for these cyclones."
            )
        if n_missing_vars > 0:
            logging.error(
                f"   ERROR: {n_missing_vars} cyclones have derived files but are missing "
                f"required variables ({REQUIRED_DERIVED_VARS}).\n"
                f"   Root cause: step 3b failed for these cyclones."
            )

    # Guard: empty chunk → derived directory non-functional
    if n_ok == 0:
        logging.error(
            "CRITICAL: 0 cyclones produced valid anomaly features in this chunk.\n"
            f"Derived directory: {derived_dir}\n"
            "Check that step 3b was run and produced *_era5_derived.nc files."
        )
        sys.exit(1)

    ok_df = new_df[new_df["_status"] == "ok"]
    era5_cols = [c for c in ok_df.columns if c not in ("track_id", "_status", "_note")]
    if len(era5_cols) > 0 and ok_df[era5_cols].isna().all(axis=None):
        logging.error(
            "CRITICAL: All ERA5 anomaly features are NaN for every cyclone in this chunk.\n"
            "Root cause: step 3b produced NaN-filled derived files.\n"
            f"Derived directory: {derived_dir}\n"
            "Fix:\n"
            "  1. Delete the NaN-filled derived files:\n"
            f"     rm -rf {derived_dir}\n"
            "  2. Re-run step 3b to recompute them:\n"
            f"     python step3b_derive_era5_fields.py --era5-dir {era5_dir} "
            f"--derived-dir {derived_dir}\n"
            "  3. Check the step 3b logs for the underlying error."
        )
        sys.exit(1)

    drop_cols = [c for c in ["_status", "_note"] if c in new_df.columns]
    save_df = new_df[new_df["_status"] == "ok"].drop(columns=drop_cols)
    if output_path.exists() and len(processed_ids) > 0:
        existing = pd.read_csv(output_path)
        save_df = pd.concat([existing, save_df], ignore_index=True)

    save_df.to_csv(output_path, index=False)
    logging.info(f"   Saved: {output_path} ({len(save_df)} rows)")
    logging.info("\n✓ Step 5 complete.")


if __name__ == "__main__":
    main()
