"""
Step 8b: Significance Summary Figures

Produces publication-quality figures from step 7b outputs:

1. Heatmap of significance (variable × EP pair)
2. Heatmap of effect sizes
3. Effect-size vs -log10(p) scatter (volcano-style)
4. Rankings by effect magnitude

Output:
  figures/lec_field_dependence/significance_heatmap_*.png
  figures/lec_field_dependence/effect_size_heatmap_*.png
  figures/lec_field_dependence/volcano_*.png
  figures/lec_field_dependence/effect_ranking_*.png

Run:
  python scripts/lec_field_dependence_analysis/step8b_significance_figures.py

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
import matplotlib.colors as mcolors

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, FIGURES_DIR, LOG_DIR,
)
from scripts.utils.ep_mapping import EP_LABELS, EP_COLORS, ALL_EPS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DPI = 300
ALPHA = 0.05
CONTRAST_ORDER = ["EP1 vs EP2", "EP1 vs EP3", "EP2 vs EP3"]

INPUT_DIAG = RESULTS_DIR / "step7b_diagnostic_table.csv"
INPUT_PAIR = RESULTS_DIR / "step7b_pairwise_table.csv"


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step8b_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


# ===================================================================
# 1. Significance heatmap (variable × EP pair)
# ===================================================================

def plot_significance_heatmap(pair_df: pd.DataFrame, block: str,
                              block_label: str):
    """
    Binary heatmap: significant / not-significant for each
    variable × pairwise contrast.
    """
    sub = pair_df[pair_df["field_type"] == block].copy() if block != "N/A" \
        else pair_df[pair_df["var_type"] == "LEC term"].copy()
    if len(sub) == 0:
        return

    sub["is_sig"] = (sub["p_value_adjusted"] < ALPHA).astype(int)
    pivot = sub.pivot_table(index="display_name", columns="contrast",
                            values="is_sig", aggfunc="max")
    pivot = pivot.reindex(columns=[c for c in CONTRAST_ORDER if c in pivot.columns])
    pivot = pivot.fillna(0)

    fig, ax = plt.subplots(figsize=(6, max(4, len(pivot) * 0.35)))
    cmap = mcolors.ListedColormap(["#f0f0f0", "#d62728"])
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, fontsize=10)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.set_title(f"Pairwise Significance — {block_label}",
                 fontsize=13, fontweight="bold")

    # Annotate cells
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            txt = "sig" if val == 1 else "ns"
            color = "white" if val == 1 else "#999999"
            ax.text(j, i, txt, ha="center", va="center",
                    fontsize=7, color=color, fontweight="bold")

    fig.tight_layout()
    tag = block_label.lower().replace(" ", "_").replace("/", "_")
    outpath = FIGURES_DIR / f"significance_heatmap_{tag}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


# ===================================================================
# 2. Effect-size heatmap (pairwise)
# ===================================================================

def plot_effect_size_heatmap(pair_df: pd.DataFrame, block: str,
                             block_label: str):
    """
    Continuous heatmap of pairwise effect sizes (|Cohen's d| or
    |rank-biserial r|).
    """
    sub = pair_df[pair_df["field_type"] == block].copy() if block != "N/A" \
        else pair_df[pair_df["var_type"] == "LEC term"].copy()
    if len(sub) == 0:
        return

    sub["abs_effect"] = sub["effect_size"].abs()
    pivot = sub.pivot_table(index="display_name", columns="contrast",
                            values="abs_effect", aggfunc="max")
    pivot = pivot.reindex(columns=[c for c in CONTRAST_ORDER if c in pivot.columns])
    pivot = pivot.fillna(0)

    fig, ax = plt.subplots(figsize=(6, max(4, len(pivot) * 0.35)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", vmin=0)
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, fontsize=10)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=8)

    es_name = sub["effect_size_name"].iloc[0] if len(sub) > 0 else "effect"
    plt.colorbar(im, ax=ax, label=f"|{es_name}|")
    ax.set_title(f"Pairwise Effect Size — {block_label}",
                 fontsize=13, fontweight="bold")

    # Annotate with values
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=6, color="black" if val < 0.5 else "white")

    fig.tight_layout()
    tag = block_label.lower().replace(" ", "_").replace("/", "_")
    outpath = FIGURES_DIR / f"effect_size_heatmap_{tag}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


# ===================================================================
# 3. Volcano-style: effect size vs -log10(p_adj)
# ===================================================================

def plot_volcano(diag_df: pd.DataFrame, block: str, block_label: str):
    """
    Scatter of effect size (x) vs -log10(adjusted p) (y).
    Variables above significance threshold are highlighted.
    """
    if block == "N/A":
        sub = diag_df[diag_df["var_type"] == "LEC term"].copy()
    else:
        sub = diag_df[diag_df["field_type"] == block].copy()
    sub = sub[sub["global_test"] != "SKIPPED"].copy()
    if len(sub) == 0:
        return

    sub["neg_log_p"] = -np.log10(sub["global_p_adjusted"].clip(lower=1e-300))
    sub["is_sig"] = sub["global_p_adjusted"] < ALPHA

    fig, ax = plt.subplots(figsize=(8, 6))
    ns = sub[~sub["is_sig"]]
    sig = sub[sub["is_sig"]]

    ax.scatter(ns["effect_size"], ns["neg_log_p"],
               c="#bbbbbb", s=30, alpha=0.6, edgecolors="none", label="Not significant")
    ax.scatter(sig["effect_size"], sig["neg_log_p"],
               c="#d62728", s=40, alpha=0.8, edgecolors="black", linewidths=0.3,
               label=f"Significant (p_adj < {ALPHA})")

    # Label top 5 by effect size
    top = sig.nlargest(5, "effect_size") if len(sig) > 0 else pd.DataFrame()
    for _, row in top.iterrows():
        ax.annotate(row["display_name"],
                    (row["effect_size"], row["neg_log_p"]),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(5, 3), textcoords="offset points")

    ax.axhline(-np.log10(ALPHA), color="gray", ls="--", lw=0.8,
               label=f"α = {ALPHA}")
    ax.set_xlabel("Effect size", fontsize=11)
    ax.set_ylabel("$-\\log_{10}(p_{adj})$", fontsize=11)
    ax.set_title(f"Volcano Plot — {block_label}", fontsize=13, fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()

    tag = block_label.lower().replace(" ", "_").replace("/", "_")
    outpath = FIGURES_DIR / f"volcano_{tag}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


# ===================================================================
# 4. Effect-size ranking
# ===================================================================

def plot_effect_ranking(diag_df: pd.DataFrame, block: str,
                        block_label: str, top_n: int = 20):
    """Horizontal bar chart ranking variables by global effect size."""
    if block == "N/A":
        sub = diag_df[diag_df["var_type"] == "LEC term"].copy()
    else:
        sub = diag_df[diag_df["field_type"] == block].copy()
    sub = sub[sub["global_test"] != "SKIPPED"].copy()
    if len(sub) == 0:
        return

    top = sub.nlargest(min(top_n, len(sub)), "effect_size")

    fig, ax = plt.subplots(figsize=(9, max(4, len(top) * 0.35)))
    colors = ["#d62728" if p < ALPHA else "#bbbbbb"
              for p in top["global_p_adjusted"]]
    ax.barh(range(len(top)), top["effect_size"].values,
            color=colors, edgecolor="black", linewidth=0.3)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(
        [f"{row['display_name']}  ({row['effect_size_name']})"
         for _, row in top.iterrows()],
        fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Effect Size", fontsize=11)
    ax.set_title(f"Effect Size Ranking — {block_label}",
                 fontsize=13, fontweight="bold")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#d62728", edgecolor="black", linewidth=0.3,
              label=f"p_adj < {ALPHA}"),
        Patch(facecolor="#bbbbbb", edgecolor="black", linewidth=0.3,
              label=f"p_adj ≥ {ALPHA}"),
    ]
    ax.legend(handles=legend_elements, fontsize=8, loc="lower right")
    fig.tight_layout()

    tag = block_label.lower().replace(" ", "_").replace("/", "_")
    outpath = FIGURES_DIR / f"effect_ranking_{tag}.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


# ===================================================================
# Main
# ===================================================================

def main():
    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 8b: SIGNIFICANCE SUMMARY FIGURES")
    logging.info("=" * 70)

    if not INPUT_DIAG.exists():
        logging.error(f"Diagnostic table not found: {INPUT_DIAG}")
        logging.error("Run step7b first.")
        return

    diag_df = pd.read_csv(INPUT_DIAG)
    pair_df = pd.read_csv(INPUT_PAIR) if INPUT_PAIR.exists() else pd.DataFrame()

    logging.info(f"Loaded {len(diag_df)} diagnostic rows, "
                 f"{len(pair_df)} pairwise rows.")

    # Determine blocks present
    blocks = []
    if (diag_df["var_type"] == "LEC term").any():
        blocks.append(("N/A", "LEC Terms"))
    if (diag_df["field_type"] == "absolute").any():
        blocks.append(("absolute", "Absolute Features"))
    if (diag_df["field_type"] == "anomaly").any():
        blocks.append(("anomaly", "Anomaly Features"))

    for block, label in blocks:
        logging.info(f"\n--- {label} ---")

        # Volcano
        plot_volcano(diag_df, block, label)

        # Effect ranking
        plot_effect_ranking(diag_df, block, label)

        # Pairwise heatmaps (only if pairwise data exists)
        if len(pair_df) > 0:
            plot_significance_heatmap(pair_df, block, label)
            plot_effect_size_heatmap(pair_df, block, label)

    logging.info("\n✓ Step 8b complete.")


if __name__ == "__main__":
    main()
