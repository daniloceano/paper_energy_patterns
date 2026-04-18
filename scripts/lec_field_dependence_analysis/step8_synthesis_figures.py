"""
Step 8: Generate Synthesis Figures and Summary Tables

Produces interpretable outputs from the PREDEP results:

1. Heatmaps: PREDEP (EP × LEC term) for each field, each field type
2. Rankings: Top features by PREDEP for each LEC term × EP
3. Comparison: EP1 vs EP2 vs EP3 (which features are more predictive)
4. Comparison: Absolute vs Anomaly fields
5. Summary table: highest PREDEP values across all combinations

Output:
  figures/lec_field_dependence/heatmap_predep_*.png
  figures/lec_field_dependence/ranking_*.png
  figures/lec_field_dependence/comparison_*.png
  results/lec_field_dependence/step8_summary_table.csv
  results/lec_field_dependence/step8_top_associations.csv

Run:
  python scripts/lec_field_dependence_analysis/step8_synthesis_figures.py

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
import matplotlib.pyplot as plt
import matplotlib as mpl

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, FIGURES_DIR, LOG_DIR,
)
from scripts.utils.ep_mapping import EP_LABELS, EP_COLORS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DPI = 300
FIGSIZE_HEATMAP = (14, 8)
FIGSIZE_BAR = (12, 6)
TOP_N = 15  # Top N associations to highlight


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step8_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def load_predep_results() -> pd.DataFrame:
    """Load and merge all PREDEP result files (absolute + anomaly, chunks)."""
    frames = []
    for ftype in ["absolute", "anomaly"]:
        base = RESULTS_DIR / f"step7_predep_{ftype}.csv"
        if base.exists():
            df = pd.read_csv(base)
            df["field_type"] = ftype
            frames.append(df)
        # Check for chunk files
        for chunk_f in sorted(RESULTS_DIR.glob(f"step7_predep_{ftype}_chunk*.csv")):
            df = pd.read_csv(chunk_f)
            df["field_type"] = ftype
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    # Drop duplicates (from merged + chunk coexistence)
    combined = combined.drop_duplicates(
        subset=["ep", "lec_term", "field", "feature", "field_type"],
        keep="first",
    )
    return combined


def plot_heatmap_field_vs_lec(df: pd.DataFrame, ep: int, field_type: str):
    """
    Heatmap: rows = LEC terms, columns = field__feature, values = PREDEP.
    One figure per EP × field_type.
    """
    sub = df[(df["ep"] == ep) & (df["field_type"] == field_type) & df["predep"].notna()]
    if len(sub) == 0:
        return

    sub["col_label"] = sub["field"] + "\n" + sub["feature"]
    pivot = sub.pivot_table(index="lec_term", columns="col_label", values="predep")

    if pivot.empty:
        return

    fig, ax = plt.subplots(figsize=FIGSIZE_HEATMAP)
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=90, fontsize=6)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=8)
    plt.colorbar(im, ax=ax, label=r"PREDEP $\alpha_{LEC|feature}$")
    ax.set_title(f"PREDEP: {EP_LABELS[ep]} — {field_type.capitalize()} Fields",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()

    outpath = FIGURES_DIR / f"heatmap_predep_{EP_LABELS[ep].lower()}_{field_type}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def plot_top_associations(df: pd.DataFrame, field_type: str):
    """Bar chart of top PREDEP associations across all EPs."""
    sub = df[(df["field_type"] == field_type) & df["predep"].notna()].copy()
    if len(sub) == 0:
        return

    sub["label"] = (sub["ep"].map(EP_LABELS) + " | " +
                    sub["lec_term"] + " × " +
                    sub["field"] + ":" + sub["feature"])
    top = sub.nlargest(TOP_N, "predep")

    fig, ax = plt.subplots(figsize=FIGSIZE_BAR)
    colors = [EP_COLORS.get(row["ep"], "gray") for _, row in top.iterrows()]
    ax.barh(range(len(top)), top["predep"].values, color=colors, edgecolor="black", linewidth=0.3)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["label"].values, fontsize=7)
    ax.set_xlabel(r"PREDEP $\alpha_{LEC|feature}$", fontsize=11)
    ax.set_title(f"Top {TOP_N} PREDEP Associations — {field_type.capitalize()} Fields",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    fig.tight_layout()

    outpath = FIGURES_DIR / f"top_predep_{field_type}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def plot_ep_comparison(df: pd.DataFrame, field_type: str):
    """
    For each LEC term, bar chart comparing mean PREDEP across EPs.
    """
    sub = df[(df["field_type"] == field_type) & df["predep"].notna()]
    if len(sub) == 0:
        return

    # Mean PREDEP per EP × LEC term (averaging over all field×feature combos)
    summary = sub.groupby(["ep", "lec_term"])["predep"].mean().reset_index()
    pivot = summary.pivot(index="lec_term", columns="ep", values="predep")

    if pivot.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(pivot))
    width = 0.25
    for i, ep in enumerate(ALL_EPS):
        if ep in pivot.columns:
            vals = pivot[ep].values
            ax.bar(x + i * width, vals, width, label=EP_LABELS[ep],
                   color=EP_COLORS[ep], edgecolor="black", linewidth=0.3)

    ax.set_xticks(x + width)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(r"Mean PREDEP $\alpha_{LEC|feature}$")
    ax.set_title(f"EP Comparison — {field_type.capitalize()} Fields", fontsize=13, fontweight="bold")
    ax.legend()
    fig.tight_layout()

    outpath = FIGURES_DIR / f"ep_comparison_{field_type}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def main():
    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 8: SYNTHESIS FIGURES — LEC–FIELD DEPENDENCE ANALYSIS")
    logging.info("=" * 70)

    df = load_predep_results()
    if len(df) == 0:
        logging.error("No PREDEP results found. Run step7 first.")
        return

    logging.info(f"Loaded {len(df)} PREDEP results")
    logging.info(f"Field types: {df['field_type'].unique().tolist()}")
    logging.info(f"EPs: {sorted(df['ep'].unique().tolist())}")

    # 1. Heatmaps per EP × field type
    logging.info("\n1. Generating heatmaps...")
    for ep in ALL_EPS:
        for ftype in df["field_type"].unique():
            plot_heatmap_field_vs_lec(df, ep, ftype)

    # 2. Top associations
    logging.info("\n2. Top association bar charts...")
    for ftype in df["field_type"].unique():
        plot_top_associations(df, ftype)

    # 3. EP comparison
    logging.info("\n3. EP comparison plots...")
    for ftype in df["field_type"].unique():
        plot_ep_comparison(df, ftype)

    # 4. Summary tables
    logging.info("\n4. Summary tables...")

    # Top associations table
    top_all = df[df["predep"].notna()].nlargest(50, "predep")
    top_all.to_csv(RESULTS_DIR / "step8_top_associations.csv", index=False)
    logging.info(f"   Saved: step8_top_associations.csv")

    # Summary: mean PREDEP per EP × field_type
    summary = df[df["predep"].notna()].groupby(
        ["ep", "field_type", "lec_term"]
    )["predep"].agg(["mean", "median", "max", "count"]).reset_index()
    summary.to_csv(RESULTS_DIR / "step8_summary_table.csv", index=False)
    logging.info(f"   Saved: step8_summary_table.csv")

    # 5. Absolute vs Anomaly comparison
    if len(df["field_type"].unique()) > 1:
        logging.info("\n5. Absolute vs Anomaly comparison...")
        abs_mean = df[df["field_type"] == "absolute"].groupby(
            ["ep", "lec_term"])["predep"].mean().reset_index()
        abs_mean.columns = ["ep", "lec_term", "predep_absolute"]
        anom_mean = df[df["field_type"] == "anomaly"].groupby(
            ["ep", "lec_term"])["predep"].mean().reset_index()
        anom_mean.columns = ["ep", "lec_term", "predep_anomaly"]
        comparison = abs_mean.merge(anom_mean, on=["ep", "lec_term"], how="outer")
        comparison.to_csv(RESULTS_DIR / "step8_abs_vs_anom_comparison.csv", index=False)
        logging.info(f"   Saved: step8_abs_vs_anom_comparison.csv")

    logging.info("\n✓ Step 8 complete.")


if __name__ == "__main__":
    main()
