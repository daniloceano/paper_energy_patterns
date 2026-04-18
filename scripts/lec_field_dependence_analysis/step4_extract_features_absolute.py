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
ERA5_FILE_PATTERN = "{track_id}_era5.nc"
N_WORKERS = 8  # For parallel feature extraction within a chunk


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


def extract_features_one_cyclone(track_id: str, era5_dir: Path) -> dict:
    """
    Extract all scalar features from absolute fields for one cyclone.

    Returns
    -------
    dict
        {field_name__feature_name: value, ...} plus 'track_id'.
        Returns {'track_id': track_id, '_status': 'failed'} on failure.
    """
    fname = ERA5_FILE_PATTERN.format(track_id=track_id)
    fpath = era5_dir / fname

    if not fpath.exists():
        return {"track_id": track_id, "_status": "file_not_found"}

    try:
        ds = xr.open_dataset(fpath)
    except Exception as e:
        return {"track_id": track_id, "_status": f"open_error: {e}"}

    row = {"track_id": track_id, "_status": "ok"}

    for field_key, var_name in DYNAMIC_FIELDS_ABSOLUTE.items():
        if var_name not in ds.data_vars:
            # Field not present — fill with NaN
            for feat_name in get_feature_names():
                row[f"{field_key}__{feat_name}"] = np.nan
            continue

        # If multiple timesteps, take the mean first
        arr = ds[var_name].values
        if arr.ndim == 3:
            arr = np.nanmean(arr, axis=0)
        elif arr.ndim != 2:
            for feat_name in get_feature_names():
                row[f"{field_key}__{feat_name}"] = np.nan
            continue

        features = extract_all_features(arr)
        for feat_name, feat_val in features.items():
            row[f"{field_key}__{feat_name}"] = feat_val

    ds.close()
    return row


def main():
    parser = argparse.ArgumentParser(
        description="Extract scalar features from absolute ERA5 fields"
    )
    parser.add_argument("--era5-dir", type=Path, required=True,
                        help="Directory with per-cyclone ERA5 NetCDFs")
    parser.add_argument("--chunk", type=int, default=None,
                        help="Chunk index (0-based)")
    parser.add_argument("--n-chunks", type=int, default=None,
                        help="Total number of chunks")
    parser.add_argument("--workers", type=int, default=N_WORKERS,
                        help="Parallel workers per chunk")
    args = parser.parse_args()

    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    setup_logging(args.chunk)

    logging.info("=" * 70)
    logging.info("STEP 4: EXTRACT ABSOLUTE FEATURES — LEC–FIELD DEPENDENCE")
    logging.info("=" * 70)

    # 1. Load manifest
    manifest = pd.read_csv(INPUT_MANIFEST)
    # Filter to available cases only (if manifest was built in live mode)
    if "era5_available" in manifest.columns:
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
    logging.info(f"\nExtracting features (workers={args.workers})...")
    era5_dir = args.era5_dir.resolve()
    results = []

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(extract_features_one_cyclone, tid, era5_dir): tid
                for tid in track_ids
            }
            for i, future in enumerate(as_completed(futures), 1):
                row = future.result()
                results.append(row)
                if i % 100 == 0:
                    logging.info(f"   Processed {i}/{len(track_ids)}...")
    else:
        for i, tid in enumerate(track_ids, 1):
            row = extract_features_one_cyclone(tid, era5_dir)
            results.append(row)
            if i % 100 == 0:
                logging.info(f"   Processed {i}/{len(track_ids)}...")

    # 5. Build DataFrame and save
    new_df = pd.DataFrame(results)
    n_ok = (new_df["_status"] == "ok").sum()
    n_fail = (new_df["_status"] != "ok").sum()
    logging.info(f"\n   Success: {n_ok}")
    logging.info(f"   Failed:  {n_fail}")

    # Log failure reasons
    if n_fail > 0:
        for status, count in new_df["_status"].value_counts().items():
            if status != "ok":
                logging.info(f"      {status}: {count}")

    # Guard: if every single cyclone has no ERA5 file, the directory is almost
    # certainly wrong.  Fail loudly instead of saving an empty CSV.
    if n_ok == 0:
        logging.error(
            "CRITICAL: 0 cyclones had ERA5 data in this chunk. "
            "Check that --era5-dir points to the directory with per-cyclone "
            f"*_era5.nc files (current value: {args.era5_dir})."
        )
        sys.exit(1)

    # Drop status column before saving
    save_df = new_df[new_df["_status"] == "ok"].drop(columns=["_status"])

    # Append to existing if resuming
    if output_path.exists() and len(processed_ids) > 0:
        existing = pd.read_csv(output_path)
        save_df = pd.concat([existing, save_df], ignore_index=True)

    save_df.to_csv(output_path, index=False)
    logging.info(f"\n   Saved: {output_path} ({len(save_df)} total rows)")
    logging.info("\n✓ Step 4 complete.")


if __name__ == "__main__":
    main()
