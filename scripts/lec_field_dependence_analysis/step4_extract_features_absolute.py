"""
Step 4: Extract Scalar Features from Absolute ERA5 Fields

For each eligible cyclone that has per-cyclone ERA5 data, extract
physically interpretable scalar features from the ABSOLUTE dynamic
fields (not anomalies).

The features are computed on a 15°×15° inner box centred on the
cyclone position within the 30°×30° storm-centred domain.

--- REMOTE EXECUTION REQUIRED ---
Per-cyclone ERA5 NetCDFs must be available.

Usage:
  python step4_extract_features_absolute.py --era5-dir /path/to/era5/
  python step4_extract_features_absolute.py --era5-dir /path/to/era5/ --chunk 0 --n-chunks 10

Chunking:
  For parallel execution on HPC, split the work by chunks:
    --chunk i --n-chunks N
  Each chunk processes ~1/N of the eligible cases.
  Results are saved as step4_features_absolute_chunk{i}.csv
  Run step4b_merge_features_absolute.py to merge.

Output:
  results/lec_field_dependence/step4_features_absolute.csv
  (or step4_features_absolute_chunk{i}.csv if chunked)

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
    RESULTS_DIR, LOG_DIR, DYNAMIC_FIELDS_ABSOLUTE,
)
from scripts.lec_field_dependence_analysis.utils_features import (
    extract_all_features, get_feature_names,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_MANIFEST = RESULTS_DIR / "step3_era5_field_manifest.csv"
OUTPUT_BASE = RESULTS_DIR / "step4_features_absolute"
DERIVED_FILE_PATTERN = "{track_id}_era5_derived.nc"
N_WORKERS = 8  # For parallel feature extraction within a chunk

# Variables that MUST be present in the derived file for a result to be valid
REQUIRED_DERIVED_VARS = ["pv_850", "pv_200", "adv_T_850", "ke_adv_250"]
# afc_250 is expected but may be absent if climatology was missing during derivation
OPTIONAL_DERIVED_VARS = ["afc_250"]

# Variables that MUST be present in the derived file for a result to be valid
REQUIRED_DERIVED_VARS = ["pv_850", "pv_200", "adv_T_850", "ke_adv_250"]
# afc_250 is expected but may be absent if climatology was missing during derivation
OPTIONAL_DERIVED_VARS = ["afc_250"]


def setup_logging(chunk_id=None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_chunk{chunk_id}" if chunk_id is not None else ""
    log_file = LOG_DIR / f"lec_field_step4{suffix}_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"Log file: {log_file}")


def extract_features_one_cyclone(track_id: str, derived_dir: Path) -> dict:
    """
    Extract all scalar features from absolute derived fields for one cyclone.

    Reads from the *derived* NetCDF ({track_id}_era5_derived.nc) produced by
    step 3b — NOT from the raw ERA5 file.  All required dynamic fields must
    be present in the derived file; missing required variables are treated as
    hard errors and reported clearly in the status field.

    Returns
    -------
    dict
        {field_name__feature_name: value, ...} plus 'track_id' and '_status'.
        '_status' == 'ok' on success; descriptive error string on failure.
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

    # ── Warn about optional variables ─────────────────────────────────────
    missing_optional = [
        v for v in OPTIONAL_DERIVED_VARS if v not in ds.data_vars
    ]

    row = {"track_id": track_id, "_status": "ok"}
    if missing_optional:
        row["_note"] = f"optional vars absent (no climatology): {missing_optional}"

    for field_key, var_name in DYNAMIC_FIELDS_ABSOLUTE.items():
        if var_name not in ds.data_vars:
            if var_name in missing_required:
                # Already flagged above — should not reach here
                for feat_name in get_feature_names():
                    row[f"{field_key}__{feat_name}"] = np.nan
            else:
                # Optional field absent (e.g. afc_250 without climatology)
                for feat_name in get_feature_names():
                    row[f"{field_key}__{feat_name}"] = np.nan
            continue

        arr = ds[var_name].values
        if arr.ndim == 3:
            arr = np.nanmean(arr, axis=0)
        elif arr.ndim != 2:
            logging.warning(
                f"{track_id}: {var_name} has unexpected shape {arr.shape} — skipping field"
            )
            for feat_name in get_feature_names():
                row[f"{field_key}__{feat_name}"] = np.nan
            continue

        # Detect all-NaN fields in derived file (indicates a derivation failure)
        if np.all(np.isnan(arr)):
            logging.warning(
                f"{track_id}: {var_name} is entirely NaN in derived file — "
                "derivation may have failed for this cyclone"
            )

        features = extract_all_features(arr)
        for feat_name, feat_val in features.items():
            row[f"{field_key}__{feat_name}"] = feat_val

    ds.close()
    return row


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract scalar features from absolute ERA5 derived fields "
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
    parser.add_argument("--chunk", type=int, default=None, help="Chunk index (0-based).")
    parser.add_argument("--n-chunks", type=int, default=None, help="Total number of chunks.")
    parser.add_argument("--workers", type=int, default=N_WORKERS, help="Parallel workers per chunk.")
    args = parser.parse_args()

    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    setup_logging(args.chunk)

    era5_dir = args.era5_dir.resolve()
    derived_dir = (args.derived_dir or era5_dir / "derived").resolve()

    logging.info("=" * 70)
    logging.info("STEP 4: EXTRACT ABSOLUTE FEATURES — LEC–FIELD DEPENDENCE")
    logging.info("=" * 70)
    logging.info(f"ERA5 raw dir  : {era5_dir}")
    logging.info(f"Derived dir   : {derived_dir}")

    # Guard: derived directory must exist (step 3b must have been run)
    if not derived_dir.exists():
        logging.error(
            f"CRITICAL: Derived directory does not exist: {derived_dir}\n"
            f"Step 3b (step3b_derive_era5_fields.py) must be run before step 4.\n"
            f"Run: python step3b_derive_era5_fields.py --era5-dir {era5_dir} "
            f"--derived-dir {derived_dir}"
        )
        sys.exit(1)

    n_derived = len(list(derived_dir.glob("*_era5_derived.nc")))
    if n_derived == 0:
        logging.error(
            f"CRITICAL: Derived directory exists but contains no *_era5_derived.nc files: "
            f"{derived_dir}\n"
            f"Step 3b must be run first to generate derived fields."
        )
        sys.exit(1)
    logging.info(f"Derived files : {n_derived} found in {derived_dir}")

    # 1. Load manifest
    manifest = pd.read_csv(INPUT_MANIFEST)
    # Filter to available cases only (if manifest was built in live mode)
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
    logging.info(f"Total cases in manifest: {len(track_ids)}")

    # 2. Apply chunking
    if args.chunk is not None and args.n_chunks is not None:
        chunks = np.array_split(track_ids, args.n_chunks)
        track_ids = list(chunks[args.chunk])
        logging.info(f"Chunk {args.chunk}/{args.n_chunks}: {len(track_ids)} cases")

    # 3. Check for already-processed files (restart-friendly)
    output_path = Path(f"{OUTPUT_BASE}{chunk_suffix}.csv")
    processed_ids = set()
    if output_path.exists():
        existing = pd.read_csv(output_path)
        processed_ids = set(existing["track_id"].astype(str).tolist())
        logging.info(f"Already processed: {len(processed_ids)} (will skip)")
        track_ids = [tid for tid in track_ids if tid not in processed_ids]
        logging.info(f"Remaining: {len(track_ids)}")

    if len(track_ids) == 0:
        logging.info("Nothing to process. Done.")
        return

    # 4. Extract features
    logging.info(f"\nExtracting features from derived files (workers={args.workers})...")
    results = []

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(extract_features_one_cyclone, tid, derived_dir): tid
                for tid in track_ids
            }
            for i, future in enumerate(as_completed(futures), 1):
                row = future.result()
                results.append(row)
                if i % 100 == 0:
                    logging.info(f"   Processed {i}/{len(track_ids)}...")
    else:
        for i, tid in enumerate(track_ids, 1):
            row = extract_features_one_cyclone(tid, derived_dir)
            results.append(row)
            if i % 100 == 0:
                logging.info(f"   Processed {i}/{len(track_ids)}...")

    # 5. Build DataFrame and save
    new_df = pd.DataFrame(results)
    n_ok = (new_df["_status"] == "ok").sum()
    n_fail = (new_df["_status"] != "ok").sum()
    logging.info(f"\n   Success: {n_ok}")
    logging.info(f"   Failed:  {n_fail}")

    # Log detailed failure breakdown for visibility
    if n_fail > 0:
        logging.info("\n   Failure breakdown:")
        for status, count in new_df["_status"].value_counts().items():
            if status != "ok":
                logging.warning(f"      {status}: {count}")
        # Distinguish between missing derived files vs other errors
        n_missing_derived = (new_df["_status"] == "derived_file_not_found").sum()
        n_missing_vars = new_df["_status"].str.startswith("missing_required_vars").sum()
        if n_missing_derived > 0:
            logging.error(
                f"   ERROR: {n_missing_derived} cyclones have no derived file "
                f"(*_era5_derived.nc) in {derived_dir}.\n"
                f"   Root cause: step 3b was not run for these cyclones.\n"
                f"   Fix: re-run step3b_derive_era5_fields.py --era5-dir {era5_dir} "
                f"--derived-dir {derived_dir}"
            )
        if n_missing_vars > 0:
            logging.error(
                f"   ERROR: {n_missing_vars} cyclones have derived files but are missing "
                f"required variables ({REQUIRED_DERIVED_VARS}).\n"
                f"   Root cause: step 3b failed for these cyclones.\n"
                f"   Fix: delete the invalid derived files and re-run step 3b."
            )

    # Guard: if every single cyclone failed, the derived directory is unusable.
    if n_ok == 0:
        logging.error(
            "CRITICAL: 0 cyclones produced valid features in this chunk.\n"
            f"Derived directory: {derived_dir}\n"
            "Check that step 3b was run and produced *_era5_derived.nc files."
        )
        sys.exit(1)

    # Guard: if all ERA5 features are NaN across ALL ok cyclones, step 3b
    # produced NaN-filled derived files.  This would silently corrupt the
    # downstream analysis, so we abort here with a clear error message.
    # (This happens when compute_pv_at_level / temperature_advection_850
    # returned NaN — check the step 3b logs for the root cause.)
    ok_df = new_df[new_df["_status"] == "ok"]
    era5_cols = [c for c in ok_df.columns if c not in ("track_id", "_status", "_note")]
    if len(era5_cols) > 0 and ok_df[era5_cols].isna().all(axis=None):
        logging.error(
            "CRITICAL: All ERA5 features are NaN for every cyclone in this chunk.\n"
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

    # Drop status and note columns before saving
    drop_cols = [c for c in ["_status", "_note"] if c in new_df.columns]
    save_df = new_df[new_df["_status"] == "ok"].drop(columns=drop_cols)

    # Append to existing if resuming
    if output_path.exists() and len(processed_ids) > 0:
        existing = pd.read_csv(output_path)
        save_df = pd.concat([existing, save_df], ignore_index=True)

    save_df.to_csv(output_path, index=False)
    logging.info(f"\n   Saved: {output_path} ({len(save_df)} total rows)")
    logging.info("\n✓ Step 4 complete.")


if __name__ == "__main__":
    main()
