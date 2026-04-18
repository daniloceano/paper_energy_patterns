"""
Step 7b: Statistical Significance Tests Between Energy Patterns

For every scalar variable used in this pipeline (LEC terms and dynamic
field features), tests whether EP1, EP2, and EP3 differ significantly
using the decision tree implemented in ``utils_statistical_tests``.

The analysis is fully separated by:
    - LEC terms  (always available from step 2)
    - Dynamic features — absolute fields  (requires step 6)
    - Dynamic features — anomaly fields   (requires step 6)

After variable-by-variable testing, a global Benjamini-Hochberg (FDR)
correction is applied across all variables within each block.

Outputs
-------
  results/lec_field_dependence/step7b_diagnostic_table.csv
  results/lec_field_dependence/step7b_pairwise_table.csv
  results/lec_field_dependence/step7b_significance_report.txt

Run
---
  python scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py

  Optional flags:
    --lec-only     Run only on LEC terms (no feature tables needed)
    --alpha 0.05   Significance level (default 0.05)
    --fdr          Use Benjamini-Hochberg for global correction (default)
    --holm         Use Holm for global correction instead

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, LOG_DIR, LEC_TERMS_FULL,
    DYNAMIC_FIELDS_ABSOLUTE, DYNAMIC_FIELDS_ANOMALY,
)
from scripts.lec_field_dependence_analysis.utils_features import get_feature_names
from scripts.lec_field_dependence_analysis.utils_statistical_tests import (
    run_decision_tree, adjust_global_pvalues, ALPHA,
)
from scripts.utils.ep_mapping import EP_LABELS, ALL_EPS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_CASES = RESULTS_DIR / "step1_eligible_cases.csv"
INPUT_LEC = RESULTS_DIR / "step2_lec_intensification_means.csv"
INPUT_INTEGRATED_ABS = RESULTS_DIR / "step6_integrated_absolute.csv"
INPUT_INTEGRATED_ANOM = RESULTS_DIR / "step6_integrated_anomaly.csv"

OUTPUT_DIAG = RESULTS_DIR / "step7b_diagnostic_table.csv"
OUTPUT_PAIR = RESULTS_DIR / "step7b_pairwise_table.csv"
OUTPUT_REPORT = RESULTS_DIR / "step7b_significance_report.txt"

EP_LABELS_SHORT = {ep: EP_LABELS[ep] for ep in ALL_EPS}


# ===================================================================
# Helpers
# ===================================================================

def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step7b_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def _load_lec_with_ep() -> pd.DataFrame:
    """Load LEC means merged with EP assignment."""
    cases = pd.read_csv(INPUT_CASES)
    lec = pd.read_csv(INPUT_LEC)
    # Ensure track_id is string for merge
    cases["track_id"] = cases["track_id"].astype(str)
    lec["track_id"] = lec["track_id"].astype(str)
    merged = cases[["track_id", "ep"]].merge(lec, on="track_id", how="inner")
    return merged


def _load_integrated(path: Path) -> pd.DataFrame:
    """Load an integrated table (step6), keeping track_id and ep."""
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["track_id"] = df["track_id"].astype(str)
    return df


def _groups_for_variable(df: pd.DataFrame, col: str,
                         eps: list = ALL_EPS) -> Tuple[List[np.ndarray],
                                                        List[str]]:
    """Split column values by EP, returning arrays and labels."""
    groups = []
    labels = []
    for ep in eps:
        vals = df.loc[df["ep"] == ep, col].dropna().values.astype(float)
        groups.append(vals)
        labels.append(EP_LABELS_SHORT[ep])
    return groups, labels


# ===================================================================
# Core analysis
# ===================================================================

def analyse_block(df: pd.DataFrame,
                  columns: List[str],
                  var_type: str,
                  field_origin_map: dict,
                  field_type: str,
                  alpha: float) -> Tuple[List[dict], List[dict]]:
    """
    Run the decision tree on every column in *columns*.

    Returns (diag_rows, pair_rows) for later DataFrame construction.
    """
    diag_rows: List[dict] = []
    pair_rows: List[dict] = []

    for col in columns:
        groups, labels = _groups_for_variable(df, col)
        result = run_decision_tree(groups, labels, alpha=alpha)

        # --- Normality per group ---
        norm_info = {}
        for nr in result["normality"]:
            g = nr["group"]
            norm_info[f"shapiro_stat_{g}"] = nr["statistic"]
            norm_info[f"shapiro_p_{g}"] = nr["p_value"]
            norm_info[f"is_normal_{g}"] = nr["is_normal"]
            norm_info[f"n_{g}"] = nr["n"]

        # --- Global row ---
        gt = result["global_test"]
        ge = result["global_effect"]

        # Determine field_origin from column name
        if "__" in col:
            field_origin = col.split("__")[0]
            feature = col.split("__")[1]
        else:
            field_origin = field_origin_map.get(col, "N/A")
            feature = col

        diag_rows.append({
            "variable": col,
            "display_name": feature,
            "var_type": var_type,
            "field_origin": field_origin,
            "field_type": field_type,
            **{f"n_{EP_LABELS_SHORT[ep]}": int(norm_info.get(f"n_{EP_LABELS_SHORT[ep]}", 0))
               for ep in ALL_EPS},
            **{f"shapiro_p_{EP_LABELS_SHORT[ep]}": norm_info.get(f"shapiro_p_{EP_LABELS_SHORT[ep]}")
               for ep in ALL_EPS},
            "all_normal": all(norm_info.get(f"is_normal_{EP_LABELS_SHORT[ep]}", False)
                              for ep in ALL_EPS),
            "levene_stat": result["homogeneity"]["statistic"],
            "levene_p": result["homogeneity"]["p_value"],
            "equal_var": result["homogeneity"]["is_homogeneous"],
            "global_test": gt["test_name"],
            "global_stat": gt["statistic"],
            "global_p_raw": gt["p_value"],
            "global_p_adjusted": np.nan,  # filled later
            "effect_size_name": ge["name"],
            "effect_size": ge["value"],
            "decision_path": gt.get("decision_path", ""),
            "decision": result["decision"],
            "notes": "; ".join(result["notes"]),
        })

        # --- Pairwise rows ---
        for pw in result["pairwise"]:
            pair_rows.append({
                "variable": col,
                "display_name": feature,
                "var_type": var_type,
                "field_origin": field_origin,
                "field_type": field_type,
                **pw,
            })

    return diag_rows, pair_rows


# ===================================================================
# Report
# ===================================================================

def write_report(diag_df: pd.DataFrame, pair_df: pd.DataFrame,
                 alpha: float, global_method: str):
    lines = [
        "=" * 72,
        "STEP 7b: EP SIGNIFICANCE TESTS — DIAGNOSTIC REPORT",
        f"Generated: {datetime.now().isoformat()}",
        f"Significance level: α = {alpha}",
        f"Global p-value correction: {global_method}",
        "=" * 72, "",
    ]

    for ft in diag_df["field_type"].unique():
        sub = diag_df[diag_df["field_type"] == ft]
        n_vars = len(sub)
        n_sig_raw = (sub["global_p_raw"] < alpha).sum()
        n_sig_adj = (sub["global_p_adjusted"] < alpha).sum()
        n_skip = (sub["global_test"] == "SKIPPED").sum()

        lines.append(f"--- Block: {ft} ---")
        lines.append(f"  Variables tested:  {n_vars}")
        lines.append(f"  Skipped (degenerate): {n_skip}")
        lines.append(f"  Significant (raw p < {alpha}):       {n_sig_raw}")
        lines.append(f"  Significant (adjusted p < {alpha}):  {n_sig_adj}")
        lines.append("")

        # Test selection breakdown
        for test in ["One-way ANOVA", "Welch ANOVA", "Kruskal-Wallis", "SKIPPED"]:
            ct = (sub["global_test"] == test).sum()
            if ct > 0:
                lines.append(f"    {test}: {ct}")
        lines.append("")

        # Top 10 by effect size (excluding skipped)
        valid = sub[sub["global_test"] != "SKIPPED"].copy()
        if len(valid) > 0:
            top = valid.nlargest(10, "effect_size")
            lines.append("  Top 10 by effect size:")
            for _, row in top.iterrows():
                lines.append(
                    f"    {row['variable']:45s}  "
                    f"{row['effect_size_name']}={row['effect_size']:.4f}  "
                    f"p_adj={row['global_p_adjusted']:.2e}  "
                    f"[{row['global_test']}]"
                )
            lines.append("")

    # Pairwise summary
    if len(pair_df) > 0:
        lines.append("=" * 72)
        lines.append("PAIRWISE CONTRASTS SUMMARY")
        lines.append("=" * 72)
        for contrast in pair_df["contrast"].unique():
            sub = pair_df[pair_df["contrast"] == contrast]
            n_sig = (sub["p_value_adjusted"] < alpha).sum()
            lines.append(f"  {contrast}: {n_sig}/{len(sub)} significant")
        lines.append("")

    OUTPUT_REPORT.write_text("\n".join(lines))
    logging.info(f"Report: {OUTPUT_REPORT}")


# ===================================================================
# Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EP significance tests for LEC terms and dynamic features")
    parser.add_argument("--lec-only", action="store_true",
                        help="Analyse LEC terms only (no feature tables needed)")
    parser.add_argument("--alpha", type=float, default=ALPHA,
                        help="Significance level (default 0.05)")
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--fdr", action="store_true", default=True,
                     help="Benjamini-Hochberg FDR correction (default)")
    grp.add_argument("--holm", action="store_true",
                     help="Holm correction instead of FDR")
    args = parser.parse_args()

    global_method = "holm" if args.holm else "fdr_bh"
    alpha = args.alpha

    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 7b: STATISTICAL SIGNIFICANCE BETWEEN EPs")
    logging.info("=" * 70)

    # ------------------------------------------------------------------
    # A.  LEC terms
    # ------------------------------------------------------------------
    logging.info("\n[A] Loading LEC data...")
    lec_df = _load_lec_with_ep()
    logging.info(f"    Merged LEC table: {len(lec_df)} cyclones, "
                 f"EPs: {sorted(lec_df['ep'].unique().tolist())}")

    # Identify available LEC columns
    lec_cols = [c for c in LEC_TERMS_FULL if c in lec_df.columns]
    logging.info(f"    LEC terms found: {len(lec_cols)}")

    all_diag: List[dict] = []
    all_pair: List[dict] = []

    diag, pair = analyse_block(
        lec_df, lec_cols,
        var_type="LEC term",
        field_origin_map={c: "LEC" for c in lec_cols},
        field_type="N/A",
        alpha=alpha,
    )
    all_diag.extend(diag)
    all_pair.extend(pair)
    logging.info(f"    LEC block: {len(diag)} variables tested")

    # ------------------------------------------------------------------
    # B.  Dynamic features — absolute
    # ------------------------------------------------------------------
    if not args.lec_only:
        logging.info("\n[B] Loading absolute features...")
        abs_df = _load_integrated(INPUT_INTEGRATED_ABS)
        if len(abs_df) > 0:
            feature_names = get_feature_names()
            abs_cols = [f"{fk}__{fn}"
                        for fk in DYNAMIC_FIELDS_ABSOLUTE
                        for fn in feature_names
                        if f"{fk}__{fn}" in abs_df.columns]
            logging.info(f"    Absolute feature columns: {len(abs_cols)}")

            diag, pair = analyse_block(
                abs_df, abs_cols,
                var_type="dynamic feature",
                field_origin_map={},
                field_type="absolute",
                alpha=alpha,
            )
            all_diag.extend(diag)
            all_pair.extend(pair)
            logging.info(f"    Absolute block: {len(diag)} variables tested")
        else:
            logging.warning("    step6_integrated_absolute.csv not found — skipping")

        # ------------------------------------------------------------------
        # C.  Dynamic features — anomaly
        # ------------------------------------------------------------------
        logging.info("\n[C] Loading anomaly features...")
        anom_df = _load_integrated(INPUT_INTEGRATED_ANOM)
        if len(anom_df) > 0:
            anom_cols = [f"{fk}__{fn}"
                         for fk in DYNAMIC_FIELDS_ANOMALY
                         for fn in feature_names
                         if f"{fk}__{fn}" in anom_df.columns]
            logging.info(f"    Anomaly feature columns: {len(anom_cols)}")

            diag, pair = analyse_block(
                anom_df, anom_cols,
                var_type="dynamic feature",
                field_origin_map={},
                field_type="anomaly",
                alpha=alpha,
            )
            all_diag.extend(diag)
            all_pair.extend(pair)
            logging.info(f"    Anomaly block: {len(diag)} variables tested")
        else:
            logging.warning("    step6_integrated_anomaly.csv not found — skipping")

    # ------------------------------------------------------------------
    # D.  Global multiple-comparison correction
    # ------------------------------------------------------------------
    logging.info(f"\n[D] Applying global correction ({global_method})...")
    diag_df = pd.DataFrame(all_diag)

    if len(diag_df) > 0:
        raw_pvals = diag_df["global_p_raw"].values.astype(float)
        adj = adjust_global_pvalues(raw_pvals, method=global_method)
        diag_df["global_p_adjusted"] = adj

        n_sig_raw = (diag_df["global_p_raw"] < alpha).sum()
        n_sig_adj = (diag_df["global_p_adjusted"] < alpha).sum()
        logging.info(f"    Total variables: {len(diag_df)}")
        logging.info(f"    Significant (raw):      {n_sig_raw}")
        logging.info(f"    Significant (adjusted):  {n_sig_adj}")

    pair_df = pd.DataFrame(all_pair)

    # ------------------------------------------------------------------
    # E.  Save outputs
    # ------------------------------------------------------------------
    logging.info("\n[E] Saving outputs...")
    diag_df.to_csv(OUTPUT_DIAG, index=False)
    logging.info(f"    {OUTPUT_DIAG}")

    if len(pair_df) > 0:
        pair_df.to_csv(OUTPUT_PAIR, index=False)
        logging.info(f"    {OUTPUT_PAIR}")
    else:
        logging.info("    No pairwise results to save.")

    write_report(diag_df, pair_df, alpha, global_method)

    logging.info("\n✓ Step 7b complete.")


if __name__ == "__main__":
    main()
