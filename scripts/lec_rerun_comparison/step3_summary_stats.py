#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step3_summary_stats.py — Quantify the legacy vs corrected LEC differences.

Turns the paired table from step 1 into two robust summary tables, one pooled
over the life cycle and one resolved by phase. All statistics use the full
sample (no trimming) and are median-based, because LEC phase means are heavy
tailed.

Columns
-------
    n                      paired cyclone-phase samples
    median_legacy/-corrected, iqr_legacy/-corrected
    median_diff            median of (corrected - legacy)
    median_abs_diff        median of |corrected - legacy|
    normalized_change      median_abs_diff / median|legacy|; 1.0 means the
                           typical change is as large as the term itself
    pearson, spearman      agreement between the two versions; the Spearman
                           value is the one that matters for the downstream
                           PCA / k-means, which depends on ranking
    sign_flip_pct          share of samples whose sign changed
    robust_flip_pct        sign flips restricted to samples where at least one
                           version exceeds median|legacy|, i.e. flips that are
                           not just noise around zero
    median_sign_changed    whether the climatological (median) sign flipped -
                           the case that would rewrite the interpretation

Usage
-----
    python scripts/lec_rerun_comparison/step3_summary_stats.py
    python scripts/lec_rerun_comparison/step3_summary_stats.py --top 12

Outputs (results/lec_rerun_comparison/)
---------------------------------------
    term_change_summary.csv       one row per term (all phases pooled)
    term_change_by_phase.csv      one row per term and phase
    conversion_regime.csv         C_A/C_K regime occupancy per phase, i.e. the
                                  Lorenz Phase Space reading that the article's
                                  interpretation rests on

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    ALL_TERMS,
    PAIRED_TABLE,
    REGIME_SUMMARY,
    PHASE_SUMMARY,
    PHASES,
    RESULTS_DIR,
    TERM_GROUP,
    TERM_UNIT,
    TERM_SUMMARY,
)


def iqr(values: np.ndarray) -> float:
    q75, q25 = np.nanpercentile(values, [75, 25])
    return float(q75 - q25)


def describe(block: pd.DataFrame) -> dict:
    legacy = block["legacy"].to_numpy(dtype=float)
    corrected = block["corrected"].to_numpy(dtype=float)
    difference = corrected - legacy
    scale = float(np.median(np.abs(legacy)))

    nonzero = (legacy != 0) & (corrected != 0)
    flips = nonzero & (np.sign(legacy) != np.sign(corrected))
    material = nonzero & (np.maximum(np.abs(legacy), np.abs(corrected)) >= scale)
    robust_flips = flips & material

    median_legacy = float(np.median(legacy))
    median_corrected = float(np.median(corrected))

    with np.errstate(invalid="ignore"):
        pearson = float(stats.pearsonr(legacy, corrected).statistic) if len(legacy) > 2 else np.nan
        spearman = float(stats.spearmanr(legacy, corrected).statistic) if len(legacy) > 2 else np.nan

    return {
        "n": int(len(block)),
        "median_legacy": median_legacy,
        "median_corrected": median_corrected,
        "iqr_legacy": iqr(legacy),
        "iqr_corrected": iqr(corrected),
        "median_diff": float(np.median(difference)),
        "median_abs_diff": float(np.median(np.abs(difference))),
        "normalized_change": float(np.median(np.abs(difference)) / scale) if scale > 0 else np.nan,
        "pearson": pearson,
        "spearman": spearman,
        "sign_flip_pct": float(100 * flips.sum() / max(nonzero.sum(), 1)),
        "robust_flip_pct": float(100 * robust_flips.sum() / max(material.sum(), 1)),
        "median_sign_changed": bool(np.sign(median_legacy) != np.sign(median_corrected)),
    }


def summarize(paired: pd.DataFrame, by_phase: bool) -> pd.DataFrame:
    keys = ["term", "phase"] if by_phase else ["term"]
    rows = []
    for key, block in paired.groupby(keys, sort=False):
        values = key if isinstance(key, tuple) else (key,)
        row = dict(zip(keys, values))
        row.update(describe(block))
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame["group"] = frame["term"].map(TERM_GROUP)
    frame["unit"] = frame["term"].map(lambda t: TERM_UNIT[t].replace("$", "").replace("^{-2}", "-2"))
    order = {term: index for index, term in enumerate(ALL_TERMS)}
    frame = frame.sort_values(
        ["term"] + (["phase"] if by_phase else []),
        key=lambda column: column.map(order) if column.name == "term"
        else column.map({phase: i for i, phase in enumerate(PHASES)}),
    )
    lead = ["group", "term", "unit"] + (["phase"] if by_phase else [])
    return frame[lead + [c for c in frame.columns if c not in lead]].reset_index(drop=True)


def conversion_regime(paired: pd.DataFrame) -> pd.DataFrame:
    """Occupancy of the conversion Lorenz Phase Space, legacy vs corrected.

    Sign convention: C_A > 0 feeds eddy APE, C_K < 0 feeds eddy KE, so the
    "upper-left" quadrant (C_A > 0 and C_K < 0) is the doubly eddy-feeding
    regime the article reports as dominant.
    """
    wide = paired.pivot_table(
        index=["track_id", "period", "phase"], columns="term", values=["legacy", "corrected"]
    )
    rows = []
    for phase in PHASES + ["all phases"]:
        block = wide if phase == "all phases" else wide[
            wide.index.get_level_values("phase") == phase
        ]
        row = {"phase": phase, "n": int(len(block))}
        for version in ("legacy", "corrected"):
            ca = block[(version, "Ca")].to_numpy(dtype=float)
            ck = block[(version, "Ck")].to_numpy(dtype=float)
            row[f"median_Ca_{version}"] = float(np.median(ca))
            row[f"median_Ck_{version}"] = float(np.median(ck))
            row[f"pct_Ca_positive_{version}"] = float(100 * np.mean(ca > 0))
            row[f"pct_Ck_negative_{version}"] = float(100 * np.mean(ck < 0))
            row[f"pct_upper_left_{version}"] = float(100 * np.mean((ca > 0) & (ck < 0)))
            row[f"pct_barotropic_dominant_{version}"] = float(
                100 * np.mean((ck < 0) & (np.abs(ck) > np.abs(ca)))
            )
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--top", type=int, default=8, help="rows to print on screen")
    args = parser.parse_args()

    if not PAIRED_TABLE.is_file():
        raise SystemExit(f"{PAIRED_TABLE} not found; run step 1 first")
    paired = pd.read_parquet(PAIRED_TABLE)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    pooled = summarize(paired, by_phase=False)
    pooled.to_csv(TERM_SUMMARY, index=False, float_format="%.6g")
    by_phase = summarize(paired, by_phase=True)
    by_phase.to_csv(PHASE_SUMMARY, index=False, float_format="%.6g")

    regime = conversion_regime(paired)
    regime.to_csv(REGIME_SUMMARY, index=False, float_format="%.6g")

    columns = ["term", "normalized_change", "spearman", "sign_flip_pct", "median_sign_changed"]
    print("\nlargest relative changes (all phases pooled)")
    print(
        pooled.sort_values("normalized_change", ascending=False)[columns]
        .head(args.top)
        .to_string(index=False, float_format=lambda v: f"{v:.2f}")
    )
    print("\nmost frequent sign changes")
    print(
        pooled.sort_values("sign_flip_pct", ascending=False)[columns]
        .head(args.top)
        .to_string(index=False, float_format=lambda v: f"{v:.2f}")
    )
    flipped = pooled[pooled["median_sign_changed"]]["term"].tolist()
    print(f"\nterms whose climatological median changed sign: {flipped or 'none'}")
    print("\nconversion regime occupancy (% of cyclone-phases)")
    print(
        regime[
            [
                "phase",
                "median_Ck_legacy",
                "median_Ck_corrected",
                "pct_Ck_negative_legacy",
                "pct_Ck_negative_corrected",
                "pct_upper_left_legacy",
                "pct_upper_left_corrected",
                "pct_barotropic_dominant_legacy",
                "pct_barotropic_dominant_corrected",
            ]
        ].to_string(index=False, float_format=lambda v: f"{v:.1f}")
    )
    print(f"\nwrote {TERM_SUMMARY}\nwrote {PHASE_SUMMARY}\nwrote {REGIME_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
