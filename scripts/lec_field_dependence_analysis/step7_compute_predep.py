"""
Step 7: Compute PREDEP for All LEC × Field × Feature Combinations

The core computation of the analysis.  For each combination of:
  - EP group (EP1, EP2, EP3)
  - LEC term (Ca, Ck, Ce, Cz, Ge, Gz, BAe, BKe, Ae, Ke, ...)
  - Dynamic field (pv_850, pv_200, adv_T_850, afc_250, ke_adv_250)
  - Scalar feature (domain_mean, centre_value, contrasts, ...)

estimates PREDEP α_{Y|X} with:
  - X = LEC term (predictor)
  - Y = scalar feature from dynamic field (response)

The primary direction answers: "how much does the dynamic feature help
predict the LEC term?" — which is α_{LEC|feature} = α_{X=feature, Y=LEC}.

Wait — the user specified:
  "LEC | feature dinâmica" means α_{LEC | feature} i.e.
  X = feature, Y = LEC term → "quanto a feature ajuda a prever o LEC"

So the PREDEP direction is:
  predep(x=feature, y=lec_term)

This means: KNOWING the dynamic feature reduces prediction loss of the
LEC term by α%.

Optionally computes Pearson and Spearman as baselines.

Supports chunking by EP or by LEC term for HPC parallelism.

Usage:
  python step7_compute_predep.py --field-type absolute
  python step7_compute_predep.py --field-type anomaly
  python step7_compute_predep.py --field-type absolute --ep 1
  python step7_compute_predep.py --field-type absolute --ep 1 --chunk 0 --n-chunks 10

Output:
  results/lec_field_dependence/step7_predep_absolute.csv
  results/lec_field_dependence/step7_predep_anomaly.csv

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime
from itertools import product

import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

from scripts.lec_field_dependence_analysis.utils_predep import (
    predep, compute_baselines,
)
from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, LOG_DIR, LEC_TERMS_CORE,
    DYNAMIC_FIELDS_ABSOLUTE, DYNAMIC_FIELDS_ANOMALY,
)
from scripts.lec_field_dependence_analysis.utils_features import get_feature_names
from scripts.utils.ep_mapping import EP_LABELS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MIN_SAMPLE_SIZE = 30  # Default minimum (overridable via --min-n)
N_WORKERS = 8
COMPUTE_BASELINES = True  # Also compute Pearson/Spearman


def setup_logging(field_type, chunk_id=None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_chunk{chunk_id}" if chunk_id is not None else ""
    log_file = LOG_DIR / f"lec_field_step7_{field_type}{suffix}_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def _compute_one_pair(args_tuple):
    """
    Worker function: compute PREDEP + baselines for one combination.

    Parameters
    ----------
    args_tuple : tuple
        (ep, lec_term, field_key, feature_name, x_vals, y_vals)

    Returns
    -------
    dict
        Result row for the long-format output table.
    """
    ep, lec_term, field_key, feature_name, x_vals, y_vals = args_tuple

    row = {
        "ep": ep,
        "lec_term": lec_term,
        "field": field_key,
        "feature": feature_name,
        "n_valid": 0,
        "predep": np.nan,
        "pearson_r": np.nan,
        "pearson_p": np.nan,
        "spearman_rho": np.nan,
        "spearman_p": np.nan,
    }

    # Clean paired NaN
    mask = np.isfinite(x_vals) & np.isfinite(y_vals)
    x_clean = x_vals[mask]
    y_clean = y_vals[mask]
    row["n_valid"] = len(x_clean)

    if len(x_clean) < MIN_SAMPLE_SIZE:
        row["exclusion_reason"] = f"n={len(x_clean)} < {MIN_SAMPLE_SIZE}"
        return row

    # Check for degenerate (constant) arrays
    if np.std(x_clean) < 1e-12 or np.std(y_clean) < 1e-12:
        row["exclusion_reason"] = "constant_variable"
        return row

    # PREDEP: X = dynamic feature, Y = LEC term
    # "quanto a feature dinâmica ajuda a prever o termo energético"
    try:
        alpha = predep(x=x_clean, y=y_clean, seed=42)
        row["predep"] = alpha
    except Exception as e:
        row["exclusion_reason"] = f"predep_error: {e}"

    # Baselines
    if COMPUTE_BASELINES:
        baselines = compute_baselines(x_clean, y_clean)
        row.update(baselines)

    return row


def main():
    parser = argparse.ArgumentParser(
        description="Compute PREDEP for all LEC × field × feature combos"
    )
    parser.add_argument("--field-type", choices=["absolute", "anomaly"],
                        required=True, help="Which field type to process")
    parser.add_argument("--ep", type=int, default=None,
                        help="Process only this EP (1, 2, or 3)")
    parser.add_argument("--chunk", type=int, default=None)
    parser.add_argument("--n-chunks", type=int, default=None)
    parser.add_argument("--workers", type=int, default=N_WORKERS)
    parser.add_argument("--no-baselines", action="store_true",
                        help="Skip Pearson/Spearman")
    parser.add_argument("--min-n", type=int, default=None,
                        help="Override MIN_SAMPLE_SIZE (default 30; use 2 for smoke tests)")
    parser.add_argument(
        "--lec-source",
        choices=["full", "central"],
        default="full",
        help=(
            "Which LEC table to use. "
            "'full' = full intensification-phase mean (default). "
            "'central' = \u00b11 timestep central-window mean (step2 --temporal-window central). "
            "The central option reduces temporal mismatch with the ERA5 snapshot."
        ),
    )
    args = parser.parse_args()

    global COMPUTE_BASELINES, MIN_SAMPLE_SIZE
    if args.no_baselines:
        COMPUTE_BASELINES = False
    if args.min_n is not None:
        MIN_SAMPLE_SIZE = args.min_n

    lec_suffix = "_central" if args.lec_source == "central" else ""
    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    setup_logging(args.field_type, args.chunk)

    logging.info("=" * 70)
    logging.info(f"STEP 7: COMPUTE PREDEP ({args.field_type.upper()}) \u2014 LEC\u2013FIELD DEPENDENCE")
    logging.info(f"LEC source : {args.lec_source.upper()} ({'\u00b11 timestep central window' if args.lec_source == 'central' else 'full intensification phase'})")
    logging.info("=" * 70)

    # 1. Load integrated table
    if args.field_type == "absolute":
        input_file = RESULTS_DIR / f"step6_integrated_absolute{lec_suffix}.csv"
    else:
        input_file = RESULTS_DIR / f"step6_integrated_anomaly{lec_suffix}.csv"

    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        logging.error("Run step6 first.")
        return

    df = pd.read_csv(input_file)
    logging.info(f"Loaded: {input_file} ({len(df)} rows)")

    # 2. Determine EPs to process
    eps_to_process = [args.ep] if args.ep else ALL_EPS
    logging.info(f"EPs: {[EP_LABELS[e] for e in eps_to_process]}")

    # 3. Identify LEC columns and feature columns
    lec_cols = [c for c in df.columns if c in LEC_TERMS_CORE or
                any(c.startswith(t) for t in ["Ca", "Ck", "Ce", "Cz", "Ge", "Gz",
                                               "BAe", "BKe", "Ae", "Ke", "Az", "Kz",
                                               "BAz", "BKz"])]
    # Also catch unicode column names from Zenodo
    lec_cols_found = []
    for col in df.columns:
        if col in ["track_id", "ep", "intensification_start", "intensification_end",
                    "duration_hours", "center_lat", "center_lon"]:
            continue
        if "__" in col:
            continue  # These are feature columns
        lec_cols_found.append(col)

    logging.info(f"LEC columns found: {len(lec_cols_found)}")
    for c in lec_cols_found:
        logging.info(f"   {c}")

    feature_names = get_feature_names()
    feature_cols_present = [c for c in df.columns if "__" in c]
    logging.info(f"Feature columns: {len(feature_cols_present)}")

    # Parse feature columns: field_key__feature_name
    field_feature_pairs = []
    for col in feature_cols_present:
        parts = col.rsplit("__", 1)
        if len(parts) == 2:
            field_feature_pairs.append((parts[0], parts[1], col))

    # 4. Build work items
    work_items = []
    for ep in eps_to_process:
        ep_df = df[df["ep"] == ep]
        n_ep = len(ep_df)
        logging.info(f"\n{EP_LABELS[ep]}: {n_ep} cyclones")

        if n_ep < MIN_SAMPLE_SIZE:
            logging.warning(f"   Skipping — too few cases ({n_ep} < {MIN_SAMPLE_SIZE})")
            continue

        for lec_col in lec_cols_found:
            for field_key, feat_name, col_name in field_feature_pairs:
                y_vals = ep_df[lec_col].values.astype(float)
                x_vals = ep_df[col_name].values.astype(float)
                work_items.append((ep, lec_col, field_key, feat_name, x_vals, y_vals))

    logging.info(f"\nTotal work items: {len(work_items)}")

    # 5. Apply chunking
    if args.chunk is not None and args.n_chunks is not None:
        chunks = np.array_split(range(len(work_items)), args.n_chunks)
        indices = chunks[args.chunk]
        work_items = [work_items[i] for i in indices]
        logging.info(f"Chunk {args.chunk}/{args.n_chunks}: {len(work_items)} items")

    # 6. Compute
    logging.info(f"\nComputing PREDEP (workers={args.workers})...")
    results = []

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(_compute_one_pair, item): i
                       for i, item in enumerate(work_items)}
            for i, future in enumerate(as_completed(futures), 1):
                results.append(future.result())
                if i % 500 == 0:
                    logging.info(f"   Computed {i}/{len(work_items)}...")
    else:
        for i, item in enumerate(work_items, 1):
            results.append(_compute_one_pair(item))
            if i % 200 == 0:
                logging.info(f"   Computed {i}/{len(work_items)}...")

    # 7. Save
    if not results:
        logging.warning("No results computed.")
        return

    result_df = pd.DataFrame(results)
    n_valid = result_df["predep"].notna().sum()
    n_excluded = result_df["predep"].isna().sum()
    logging.info(f"\n   Valid PREDEP estimates: {n_valid}")
    logging.info(f"   Excluded:              {n_excluded}")

    output_path = RESULTS_DIR / f"step7_predep_{args.field_type}{lec_suffix}{chunk_suffix}.csv"
    result_df.to_csv(output_path, index=False)
    logging.info(f"   Saved: {output_path}")

    # Summary
    if n_valid > 0:
        logging.info(f"\n   PREDEP summary:")
        logging.info(f"      Mean:   {result_df['predep'].mean():.4f}")
        logging.info(f"      Median: {result_df['predep'].median():.4f}")
        logging.info(f"      Max:    {result_df['predep'].max():.4f}")
        logging.info(f"      Min:    {result_df['predep'].dropna().min():.4f}")

    logging.info("\n✓ Step 7 complete.")


if __name__ == "__main__":
    main()
