"""
Step 8b — Discrete Effect-Size Heatmaps (explicit variant)

Produces effect-size heatmaps using discrete 0.1-step colour bins,
saving as *_discrete.png variants alongside the standard step8b outputs.

Colour convention:
  < 0.10               → grey (#b3b3b3)
  [0.10, 0.20)         → light yellow
  [0.20, 0.30)         → yellow
  [0.30, 0.40)         → yellow-orange
  [0.40, 0.50)         → orange-light
  [0.50, 0.60)         → orange
  [0.60, 0.70)         → orange-dark
  [0.70, 0.80)         → dark orange
  [0.80, 0.90)         → red-orange
  ≥ 0.90               → red

Effect sizes used:
  Global test  → epsilon² (Kruskal-Wallis, non-parametric global effect)
  Pairwise     → |rank-biserial r| (Dunn post-hoc)

Output files (in figures/lec_field_dependence/):
  effect_size_heatmap_lec_terms_discrete.png
  effect_size_heatmap_absolute_features_discrete.png
  effect_size_heatmap_anomaly_features_discrete.png

Run:
  python scripts/lec_field_dependence_analysis/step8b_effect_heatmap_discrete.py

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

# Discrete colour scale — 0.1-step bins, grey for < 0.10
# Index 0 covers [0.00, 0.10); indices 1–9 cover [0.10, 0.20) … ≥ 0.90
EFFECT_THRESHOLDS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.01]
EFFECT_COLORS = [
    "#b3b3b3",  # < 0.10   grey — negligible
    "#ffff99",  # 0.10–0.20 light yellow
    "#ffe64d",  # 0.20–0.30 yellow
    "#ffcc00",  # 0.30–0.40 yellow-orange
    "#ffb300",  # 0.40–0.50 amber
    "#ff9900",  # 0.50–0.60 orange
    "#ff7300",  # 0.60–0.70 deep orange
    "#ff4d00",  # 0.70–0.80 orange-red
    "#e62600",  # 0.80–0.90 red-orange
    "#cc0000",  # ≥ 0.90    red
]

BIN_LABELS = [
    "< 0.10",
    "0.10–0.20",
    "0.20–0.30",
    "0.30–0.40",
    "0.40–0.50",
    "0.50–0.60",
    "0.60–0.70",
    "0.70–0.80",
    "0.80–0.90",
    "≥ 0.90",
]

INPUT_DIAG = RESULTS_DIR / "step7b_diagnostic_table.csv"
INPUT_PAIR = RESULTS_DIR / "step7b_pairwise_table.csv"


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step8b_discrete_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def _make_discrete_cmap_norm():
    """Return (cmap, norm) for the 0.1-step discrete colour scale."""
    cmap = mcolors.ListedColormap(EFFECT_COLORS)
    norm = mcolors.BoundaryNorm([0.0] + EFFECT_THRESHOLDS, cmap.N)
    return cmap, norm


def _legend_patches():
    """Return a list of matplotlib Patch objects for the discrete legend."""
    from matplotlib.patches import Patch
    return [
        Patch(facecolor=EFFECT_COLORS[i], edgecolor="black", linewidth=0.4,
              label=BIN_LABELS[i])
        for i in range(len(EFFECT_COLORS))
    ]


# ===================================================================
# 1. Pairwise effect-size heatmap (discrete)
# ===================================================================

def plot_pairwise_effect_heatmap(pair_df: pd.DataFrame, block: str,
                                 block_label: str):
    """
    Discrete heatmap of |rank-biserial r| for each variable × EP pair.
    Significant cells are framed; non-significant cells are annotated 'ns'.
    """
    if block == "N/A":
        sub = pair_df[pair_df["var_type"] == "LEC term"].copy()
    else:
        sub = pair_df[pair_df["field_type"] == block].copy()
    if len(sub) == 0:
        logging.warning(f"No pairwise rows for block={block!r}; skipping.")
        return

    sub["abs_effect"] = sub["effect_size"].abs()
    sub["is_sig"] = sub["p_value_adjusted"] < ALPHA

    pivot_eff = sub.pivot_table(
        index="display_name", columns="contrast",
        values="abs_effect", aggfunc="max",
    )
    pivot_sig = sub.pivot_table(
        index="display_name", columns="contrast",
        values="is_sig", aggfunc="max",
    )

    # Consistent column order
    pivot_eff = pivot_eff.reindex(
        columns=[c for c in CONTRAST_ORDER if c in pivot_eff.columns]
    ).fillna(0.0)
    pivot_sig = pivot_sig.reindex(columns=pivot_eff.columns).fillna(False)

    cmap, norm = _make_discrete_cmap_norm()

    fig, ax = plt.subplots(figsize=(8, max(5, len(pivot_eff) * 0.42)))
    im = ax.imshow(pivot_eff.values, aspect="auto", cmap=cmap, norm=norm)

    ax.set_xticks(range(pivot_eff.shape[1]))
    ax.set_xticklabels(pivot_eff.columns, fontsize=10)
    ax.set_yticks(range(pivot_eff.shape[0]))
    ax.set_yticklabels(pivot_eff.index, fontsize=7)
    ax.set_title(
        f"Pairwise Effect Size (|rank-biserial r|) — {block_label}\n"
        "Discrete bins, 0.1 step · Grey = negligible (< 0.10)",
        fontsize=11, fontweight="bold",
    )

    # Cell annotations: mark non-significant (ns) and highlight sig borders
    for i in range(pivot_eff.shape[0]):
        for j in range(pivot_eff.shape[1]):
            is_sig = bool(pivot_sig.values[i, j])
            if not is_sig:
                ax.text(j, i, "ns", ha="center", va="center",
                        fontsize=6, color="#555555", style="italic")
            else:
                # Draw a subtle border around significant cells
                rect = plt.Rectangle(
                    (j - 0.48, i - 0.48), 0.96, 0.96,
                    linewidth=1.2, edgecolor="black", facecolor="none",
                )
                ax.add_patch(rect)

    # Discrete legend (right side)
    patches = _legend_patches()
    legend = ax.legend(
        handles=patches,
        title="|rank-biserial r|",
        fontsize=7,
        title_fontsize=8,
        loc="lower left",
        bbox_to_anchor=(1.02, 0.0),
        framealpha=0.95,
    )

    ax.set_xlabel("EP pair contrast", fontsize=10)
    fig.tight_layout()

    tag = block_label.lower().replace(" ", "_").replace("/", "_")
    outpath = FIGURES_DIR / f"effect_size_heatmap_{tag}_discrete.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


# ===================================================================
# 2. Global effect-size heatmap (per-variable, discrete)
# ===================================================================

def plot_global_effect_heatmap(diag_df: pd.DataFrame, block: str,
                               block_label: str):
    """
    Single-column heatmap of the global epsilon² (Kruskal-Wallis) for each
    variable within the block.  Sorted descending by effect size.
    """
    if block == "N/A":
        sub = diag_df[diag_df["var_type"] == "LEC term"].copy()
    else:
        sub = diag_df[diag_df["field_type"] == block].copy()
    sub = sub[sub["global_test"] != "SKIPPED"].copy()
    if len(sub) == 0:
        logging.warning(f"No global test rows for block={block!r}; skipping.")
        return

    sub = sub.sort_values("effect_size", ascending=True)  # ascending so top is highest

    cmap, norm = _make_discrete_cmap_norm()

    fig, ax = plt.subplots(figsize=(4, max(4, len(sub) * 0.38)))
    data = sub["effect_size"].values.reshape(-1, 1)
    im = ax.imshow(data, aspect="auto", cmap=cmap, norm=norm)

    ax.set_xticks([0])
    ax.set_xticklabels([sub["effect_size_name"].iloc[0]], fontsize=9)
    ax.set_yticks(range(len(sub)))
    ax.set_yticklabels(sub["display_name"], fontsize=7)
    ax.set_title(
        f"Global Effect Size (ε²) — {block_label}\n"
        "Discrete bins, 0.1 step · Sorted by magnitude",
        fontsize=11, fontweight="bold",
    )

    # Annotate each cell with the numeric value
    for i, val in enumerate(sub["effect_size"].values):
        txt_color = "black" if val < 0.60 else "white"
        ax.text(0, i, f"{val:.3f}", ha="center", va="center",
                fontsize=6.5, color=txt_color)

    patches = _legend_patches()
    ax.legend(
        handles=patches,
        title="ε²",
        fontsize=7,
        title_fontsize=8,
        loc="lower left",
        bbox_to_anchor=(1.02, 0.0),
        framealpha=0.95,
    )

    fig.tight_layout()
    tag = block_label.lower().replace(" ", "_").replace("/", "_")
    outpath = FIGURES_DIR / f"effect_size_global_{tag}_discrete.png"
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


# ===================================================================
# Main
# ===================================================================

def main():
    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 8b — DISCRETE EFFECT-SIZE HEATMAPS (variant)")
    logging.info("=" * 70)

    if not INPUT_DIAG.exists():
        logging.error(f"Diagnostic table not found: {INPUT_DIAG}")
        logging.error("Run step7b first.")
        return

    diag_df = pd.read_csv(INPUT_DIAG)
    pair_df = pd.read_csv(INPUT_PAIR) if INPUT_PAIR.exists() else pd.DataFrame()

    logging.info(f"Loaded {len(diag_df)} diagnostic rows, "
                 f"{len(pair_df)} pairwise rows.")

    blocks = []
    if (diag_df["var_type"] == "LEC term").any():
        blocks.append(("N/A", "LEC Terms"))
    if (diag_df["field_type"] == "absolute").any():
        blocks.append(("absolute", "Absolute Features"))
    if (diag_df["field_type"] == "anomaly").any():
        blocks.append(("anomaly", "Anomaly Features"))

    for block, label in blocks:
        logging.info(f"\n--- {label} ---")
        plot_global_effect_heatmap(diag_df, block, label)
        if len(pair_df) > 0:
            plot_pairwise_effect_heatmap(pair_df, block, label)

    logging.info("\n✓ Discrete heatmaps complete.")
    logging.info(f"Output directory: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
