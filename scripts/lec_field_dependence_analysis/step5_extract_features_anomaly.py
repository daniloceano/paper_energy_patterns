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
ERA5_FILE_PATTERN = "{track_id}_era5.nc"
EPALL_COMPOSITE = ERA5_EP_DIR / "precomputed_composites_epall.nc"
N_WORKERS = 8


# Global reference: EPALL composite fields (loaded once, shared across workers)
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


def extract_anomaly_features_one_cyclone(track_id: str, era5_dir: Path) -> dict:
    """
    Extract scalar features from (field_i - EPALL_composite) for one cyclone.
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
        anom_key = f"{field_key}_anom_epall"

        if var_name not in ds.data_vars:
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        if field_key not in _EPALL_FIELDS:
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        # Per-cyclone field
        arr = ds[var_name].values
        if arr.ndim == 3:
            arr = np.nanmean(arr, axis=0)
        elif arr.ndim != 2:
            for feat_name in get_feature_names():
                row[f"{anom_key}__{feat_name}"] = np.nan
            continue

        # Compute anomaly: cyclone_i - EPALL
        epall_arr = _EPALL_FIELDS[field_key]
        # Handle possible shape mismatch (should not happen with canonical data)
        if arr.shape != epall_arr.shape:
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
        description="Extract scalar features from EPALL-relative anomaly fields"
    )
    parser.add_argument("--era5-dir", type=Path, required=True)
    parser.add_argument("--chunk", type=int, default=None)
    parser.add_argument("--n-chunks", type=int, default=None)
    parser.add_argument("--workers", type=int, default=N_WORKERS)
    args = parser.parse_args()

    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    setup_logging(args.chunk)

    logging.info("=" * 70)
    logging.info("STEP 5: EXTRACT ANOMALY FEATURES — LEC–FIELD DEPENDENCE")
    logging.info("=" * 70)

    # Load EPALL composite
    _load_epall_composite()

    # 1. Load manifest
    manifest = pd.read_csv(INPUT_MANIFEST)
    if "era5_available" in manifest.columns:
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

    # 4. Extract features (serial for now — EPALL fields are in global memory)
    logging.info(f"\nExtracting anomaly features...")
    era5_dir = args.era5_dir.resolve()
    results = []
    for i, tid in enumerate(track_ids, 1):
        row = extract_anomaly_features_one_cyclone(tid, era5_dir)
        results.append(row)
        if i % 100 == 0:
            logging.info(f"   Processed {i}/{len(track_ids)}...")

    # 5. Save
    new_df = pd.DataFrame(results)
    n_ok = (new_df["_status"] == "ok").sum()
    n_fail = (new_df["_status"] != "ok").sum()
    logging.info(f"\n   Success: {n_ok}, Failed: {n_fail}")

    if n_fail > 0:
        for status, count in new_df["_status"].value_counts().items():
            if status != "ok":
                logging.info(f"      {status}: {count}")

    # Guard: empty chunk → wrong ERA5 directory
    if n_ok == 0:
        logging.error(
            "CRITICAL: 0 cyclones had ERA5 data in this chunk. "
            "Check that --era5-dir points to the directory with per-cyclone "
            f"*_era5.nc files (current value: {args.era5_dir})."
        )
        sys.exit(1)

    save_df = new_df[new_df["_status"] == "ok"].drop(columns=["_status"])
    if output_path.exists() and len(processed_ids) > 0:
        existing = pd.read_csv(output_path)
        save_df = pd.concat([existing, save_df], ignore_index=True)

    save_df.to_csv(output_path, index=False)
    logging.info(f"   Saved: {output_path} ({len(save_df)} rows)")
    logging.info("\n✓ Step 5 complete.")


if __name__ == "__main__":
    main()
