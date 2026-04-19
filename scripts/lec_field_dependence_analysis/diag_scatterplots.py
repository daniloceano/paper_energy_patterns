"""
Diagnostic: LEC × Feature Scatterplots

Generates scatter plots showing the relationship between each canonical
LEC term and each spatial feature extracted from the dynamic fields.

Layout: one figure per (LEC term × EP), containing a grid of subplots
  rows = 5 dynamic fields (PV850, PV200, AdvT850, AFC250, KEadv250)
  cols = 13 spatial features

These are purely diagnostic figures for quick visual inspection.
Data source: step6 integrated tables (per-cyclone values) — no recomputation.

Output:
  figures/lec_field_dependence/diagnostics/scatterplots/

Run:
  python scripts/lec_field_dependence_analysis/diag_scatterplots.py
  python scripts/lec_field_dependence_analysis/diag_scatterplots.py --field-type anomaly

Author: Danilo Couto de Souza
Date: April 2026
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, FIGURES_DIR, LOG_DIR,
    LEC_TERMS_CORE, DYNAMIC_FIELDS_ABSOLUTE,
    FIELD_DISPLAY_NAMES, FEATURE_DISPLAY_NAMES,
)
from scripts.lec_field_dependence_analysis.utils_features import get_feature_names
from scripts.utils.ep_mapping import EP_LABELS, EP_COLORS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DPI = 150  # lower DPI for diagnostic figures (smaller files)
DIAG_DIR = FIGURES_DIR / "diagnostics" / "scatterplots"
SCATTER_ALPHA = 0.25
SCATTER_SIZE = 4

INPUT_ABS = RESULTS_DIR / "step6_integrated_absolute.csv"
INPUT_ANOM = RESULTS_DIR / "step6_integrated_anomaly.csv"


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"diag_scatterplots_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def plot_scatter_grid(
    df: pd.DataFrame,
    lec_term: str,
    ep: int,
    field_keys: list,
    feature_names: list,
    field_type: str,
    out_dir: Path,
):
    """
    Grid of scatter plots: one row per field, one column per feature.
    Each panel plots lec_term (y) vs field__feature (x), coloured by EP.
    """
    n_fields = len(field_keys)
    n_features = len(feature_names)

    sub = df[df["ep"] == ep].copy()
    if len(sub) == 0:
        return

    fig, axes = plt.subplots(
        n_fields, n_features,
        figsize=(n_features * 1.8, n_fields * 1.8),
        sharex=False, sharey=True,
    )

    if n_fields == 1:
        axes = axes[np.newaxis, :]
    if n_features == 1:
        axes = axes[:, np.newaxis]

    ep_label = EP_LABELS[ep]
    ep_color = EP_COLORS.get(ep, "gray")

    for i, fk in enumerate(field_keys):
        field_label = FIELD_DISPLAY_NAMES.get(fk, fk)
        for j, feat in enumerate(feature_names):
            ax = axes[i, j]
            col_name = f"{fk}__{feat}"

            if col_name not in sub.columns or lec_term not in sub.columns:
                ax.set_visible(False)
                continue

            x = sub[col_name]
            y = sub[lec_term]
            valid = x.notna() & y.notna()

            if valid.sum() < 5:
                ax.text(
                    0.5, 0.5, "n < 5",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=7, color="gray",
                )
                ax.set_xticks([])
                ax.set_yticks([])
            else:
                ax.scatter(
                    x[valid], y[valid],
                    s=SCATTER_SIZE, alpha=SCATTER_ALPHA,
                    c=ep_color, edgecolors="none", rasterized=True,
                )
                ax.tick_params(labelsize=5)

            # Column header (top row only)
            if i == 0:
                feat_label = FEATURE_DISPLAY_NAMES.get(feat, feat)
                ax.set_title(feat_label, fontsize=6, pad=2)

            # Row label (first column only)
            if j == 0:
                ax.set_ylabel(field_label, fontsize=6)
            else:
                ax.set_ylabel("")

            # Hide spines for cleaner look
            for spine in ax.spines.values():
                spine.set_linewidth(0.3)

    fig.suptitle(
        f"{lec_term} vs features — {ep_label} | "
        f"{field_type.capitalize()} (N={len(sub)})",
        fontsize=11, fontweight="bold", y=1.01,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.99])

    fname = (
        f"scatter_{lec_term}_{ep_label.lower().replace(' ', '_')}"
        f"_{field_type}.png"
    )
    outpath = out_dir / fname
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic: LEC × feature scatterplots"
    )
    parser.add_argument(
        "--field-type",
        choices=["absolute", "anomaly", "both"],
        default="both",
    )
    args = parser.parse_args()

    setup_logging()
    logging.info("=" * 70)
    logging.info("DIAGNOSTIC: LEC × Feature Scatterplots")
    logging.info("=" * 70)

    feature_names = get_feature_names()
    abs_field_keys = list(DYNAMIC_FIELDS_ABSOLUTE.keys())
    # Anomaly field keys use _anom_epall in step6 column names
    anom_field_keys = [f"{fk}_anom_epall" for fk in abs_field_keys]

    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    field_types = (
        ["absolute", "anomaly"] if args.field_type == "both"
        else [args.field_type]
    )

    for ftype in field_types:
        if ftype == "absolute":
            input_file = INPUT_ABS
            field_keys = abs_field_keys
        else:
            input_file = INPUT_ANOM
            field_keys = anom_field_keys

        if not input_file.exists():
            logging.warning(f"File not found: {input_file} — skipping {ftype}")
            continue

        logging.info(f"\nLoading {ftype} data: {input_file}")
        df = pd.read_csv(input_file)
        logging.info(f"  {len(df)} rows, {len(df.columns)} columns")

        for lec_term in LEC_TERMS_CORE:
            if lec_term not in df.columns:
                logging.warning(f"  LEC term '{lec_term}' not in data — skipping")
                continue
            for ep in ALL_EPS:
                plot_scatter_grid(
                    df, lec_term, ep, field_keys, feature_names,
                    ftype, DIAG_DIR,
                )

    logging.info("\n✓ Diagnostic scatterplots complete.")


if __name__ == "__main__":
    main()
