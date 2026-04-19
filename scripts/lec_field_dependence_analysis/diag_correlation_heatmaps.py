"""
Diagnostic: Pearson and Spearman Correlation Heatmaps

Generates heatmaps analogous to the PREDEP heatmaps but using:
  - Pearson r
  - Spearman ρ

These are purely diagnostic figures for internal inspection.
They reuse the existing step7 PREDEP outputs which already contain
pearson_r and spearman_rho columns — no recomputation needed.

Output:
  figures/lec_field_dependence/diagnostics/correlation_heatmaps/

Run:
  python scripts/lec_field_dependence_analysis/diag_correlation_heatmaps.py
  python scripts/lec_field_dependence_analysis/diag_correlation_heatmaps.py --term-set canonical

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
import matplotlib.colors as mcolors

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, FIGURES_DIR, LOG_DIR,
    LEC_TERMS_CORE, LEC_TERMS_FULL,
    format_display_label,
)
from scripts.utils.ep_mapping import EP_LABELS, ALL_EPS, ALL_EPS_WITH_EPALL

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DPI = 300
FIGSIZE_HEATMAP = (16, 9)

DIAG_DIR = FIGURES_DIR / "diagnostics" / "correlation_heatmaps"

# Discrete colour scale for |correlation|, matching PREDEP visual style:
#   |r| < 0.1  → grey
#   0.1 steps from 0.1 to 1.0
CORR_THRESHOLDS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.01]
CORR_COLORS = [
    "#b3b3b3",   # < 0.10  → grey
    "#ffff99",   # 0.10–0.20  light yellow
    "#ffe64d",   # 0.20–0.30  yellow-light
    "#ffcc00",   # 0.30–0.40  yellow
    "#ffb300",   # 0.40–0.50  yellow-orange
    "#ff9900",   # 0.50–0.60  orange
    "#ff7300",   # 0.60–0.70  orange-dark
    "#ff4d00",   # 0.70–0.80  dark orange
    "#e62600",   # 0.80–0.90  red-orange
    "#cc0000",   # > 0.90     red
]


def _make_corr_cmap():
    """Discrete colormap for |correlation| with grey < 0.1."""
    cmap = mcolors.ListedColormap(CORR_COLORS)
    norm = mcolors.BoundaryNorm([0.0] + CORR_THRESHOLDS, cmap.N)
    return cmap, norm


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"diag_corr_heatmaps_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def load_predep_results() -> pd.DataFrame:
    """Load and merge all PREDEP result files (reuses step8 logic, includes epall)."""
    frames = []
    for ftype in ["absolute", "anomaly"]:
        base = RESULTS_DIR / f"step7_predep_{ftype}.csv"
        if base.exists():
            df = pd.read_csv(base)
            df["field_type"] = ftype
            frames.append(df)
        for chunk_f in sorted(RESULTS_DIR.glob(f"step7_predep_{ftype}_chunk*.csv")):
            df = pd.read_csv(chunk_f)
            df["field_type"] = ftype
            frames.append(df)
        # EPALL file (ep=0)
        epall_f = RESULTS_DIR / f"step7_predep_{ftype}_epall.csv"
        if epall_f.exists():
            df = pd.read_csv(epall_f)
            df["field_type"] = ftype
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["ep", "lec_term", "field", "feature", "field_type"],
        keep="first",
    )
    return combined


def _col_order(labels):
    """Sort column labels: group by field then feature."""
    return sorted(labels, key=lambda s: s)


def plot_correlation_heatmap(
    df: pd.DataFrame,
    ep: int,
    field_type: str,
    metric: str,
    out_dir: Path,
    term_label: str = "all",
):
    """
    Heatmap of |Pearson r| or |Spearman ρ|.

    Parameters
    ----------
    metric : str
        'pearson_r' or 'spearman_rho'
    """
    col_name = metric
    display_metric = "Pearson |r|" if metric == "pearson_r" else "Spearman |ρ|"
    short_metric = "pearson" if metric == "pearson_r" else "spearman"

    sub = df[
        (df["ep"] == ep) & (df["field_type"] == field_type) & df[col_name].notna()
    ].copy()
    if len(sub) == 0:
        return

    sub["col_label"] = sub.apply(
        lambda r: format_display_label(r["field"], r["feature"]), axis=1
    )
    sub["abs_corr"] = sub[col_name].abs()

    pivot = sub.pivot_table(
        index="lec_term", columns="col_label", values="abs_corr"
    )
    if pivot.empty:
        return

    ordered_cols = _col_order(pivot.columns.tolist())
    ordered_cols = [c for c in ordered_cols if c in pivot.columns]
    pivot = pivot[ordered_cols]

    cmap, norm = _make_corr_cmap()

    fig, ax = plt.subplots(figsize=FIGSIZE_HEATMAP)
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, norm=norm)

    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=90, fontsize=6)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=8)

    cbar = plt.colorbar(im, ax=ax, pad=0.02, fraction=0.025)
    cbar.set_label(display_metric, fontsize=10)
    tick_vals = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
    cbar.set_ticks(tick_vals)
    cbar.set_ticklabels(
        ["0 (grey)"] + [f"{v:.1f}" for v in tick_vals[1:]]
    )

    ep_label = EP_LABELS[ep]
    ax.set_title(
        f"{display_metric} — {ep_label} | {field_type.capitalize()} Fields "
        f"({'canonical' if term_label == 'canonical' else 'all terms'})",
        fontsize=13, fontweight="bold", pad=12,
    )
    fig.tight_layout()

    fname = (
        f"heatmap_{short_metric}_{ep_label.lower().replace(' ', '_')}"
        f"_{field_type}_{term_label}.png"
    )
    outpath = out_dir / fname
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def _generate_for_term_set(df: pd.DataFrame, term_set: str, out_dir: Path):
    if term_set == "canonical":
        df = df[df["lec_term"].isin(LEC_TERMS_CORE)].copy()
        logging.info(f"   Canonical filter: {len(df)} rows")
    else:
        logging.info(f"   All-terms set: {len(df)} rows")

    if len(df) == 0:
        logging.warning(f"   No data for '{term_set}'. Skipping.")
        return

    sub_dir = out_dir / term_set
    sub_dir.mkdir(parents=True, exist_ok=True)

    for metric in ["pearson_r", "spearman_rho"]:
        metric_name = "Pearson" if metric == "pearson_r" else "Spearman"
        logging.info(f"\n  --- {metric_name} ({term_set}) ---")
        for ftype in df["field_type"].unique():
            eps_in_data = sorted(df["ep"].unique())
            for ep in [e for e in ALL_EPS_WITH_EPALL if e in eps_in_data]:
                plot_correlation_heatmap(
                    df, ep, ftype, metric, sub_dir, term_label=term_set
                )


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic: Pearson/Spearman correlation heatmaps"
    )
    parser.add_argument(
        "--term-set",
        choices=["all", "canonical", "both"],
        default="both",
    )
    args = parser.parse_args()

    setup_logging()
    logging.info("=" * 70)
    logging.info("DIAGNOSTIC: Pearson / Spearman Correlation Heatmaps")
    logging.info("=" * 70)

    df = load_predep_results()
    if len(df) == 0:
        logging.error("No step7 results found. Run step7 first.")
        return

    # Check that correlation columns exist
    for col in ["pearson_r", "spearman_rho"]:
        if col not in df.columns:
            logging.error(f"Column '{col}' not found in step7 outputs.")
            return

    logging.info(f"Loaded {len(df)} rows with correlation data")

    term_sets = (
        ["all", "canonical"] if args.term_set == "both" else [args.term_set]
    )

    for ts in term_sets:
        logging.info(f"\n{'='*60}")
        logging.info(f"Term set: {ts.upper()}")
        _generate_for_term_set(df, ts, DIAG_DIR)

    logging.info("\n✓ Diagnostic correlation heatmaps complete.")


if __name__ == "__main__":
    main()
