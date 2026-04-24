#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S2: Pairwise Effect Size — LEC Terms (EP1 vs EP2, EP1 vs EP3, EP2 vs EP3)

Layout: 2×3 subplot grid, one panel per physically related LEC group:
  (a) Energies               | (b) Conversions          | (c) Generation & Boundary KE
  (d) Boundary APE           | (e) Residuals             | (f) Tendencies

Each panel is a discrete heatmap of |rank-biserial r| for all three contrasts.

Visual conventions:
  • Colour bins: 0.10 step, grey = negligible (|r| < 0.10)
  • Hatching (///)  : contrast is NOT statistically significant (p_adj ≥ 0.05)
  • No hatching     : contrast IS statistically significant (p_adj < 0.05)
  A grey cell WITHOUT hatching means the effect is negligible but the test
  did find a significant (though practically irrelevant) difference.
  A coloured cell WITH hatching means the magnitude suggests a non-negligible
  effect but the test did not reach significance — interpret with caution.

LEC term ordering follows the canonical Lorenz (1955) physical sequence:
  Energies → Conversions → Generation → Boundary APE → Boundary KE
  → Residuals → Tendencies

Data source: results/lec_field_dependence/step7b_pairwise_table.csv
  (produced by scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py)

Outputs:
  figures/main/S3_pairwise_effectsize_lec_terms.png  (300 DPI)

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_PAIR = BASE_DIR / "results" / "lec_field_dependence" / "step7b_pairwise_table.csv"
FIGURES_DIR = BASE_DIR / "figures" / "main"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = FIGURES_DIR / "S2_pairwise_effectsize_lec_terms.png"

# Statistical threshold
ALPHA = 0.05

# Column order for contrasts
CONTRAST_ORDER = ["EP1 vs EP2", "EP1 vs EP3", "EP2 vs EP3"]

# ---- Configurable font sizes (edit here for publication adjustments) ----
FONT_SIZE_AXIS_LABEL  = 10   # x/y axis label text
FONT_SIZE_TICKS       = 9    # x/y tick labels
FONT_SIZE_LEGEND      = 9    # legend / NS patch text
FONT_SIZE_PANEL_LABEL = 11   # (a), (b), ... panel identifiers
FONT_SIZE_COLORBAR    = 9    # colorbar label and ticks
FONT_SIZE_GROUP_TITLE = 10   # each panel's title (group name)

# ---- Figure layout ----
FIG_WIDTH  = 10.5   # inches
FIG_HEIGHT = 6.5    # inches
DPI        = 300

# ---- Subplot group definitions (2×3 grid, left-to-right, top-to-bottom) ----
# 'separator_after': draw a dashed line after this 0-based row index within the panel.
# Terms must match display_name values in the CSV exactly.
PANEL_GROUPS = [
    {
        "title": "Energies",
        "label": "(a)",
        "terms": ["Az", "Ae", "Kz", "Ke"],
        "separator_after": None,
        "subgroup_labels": None,
    },
    {
        "title": "Conversions",
        "label": "(b)",
        "terms": ["Cz", "Ca", "Ce", "Ck"],
        "separator_after": None,
        "subgroup_labels": None,
    },
    {
        "title": "Generation  &  Boundary KE",
        "label": "(c)",
        "terms": ["Gz", "Ge", "BKz", "BKe"],
        "separator_after": 1,   # dashed line between Ge and BKz
        "subgroup_labels": None,
    },
    {
        "title": "Boundary APE",
        "label": "(d)",
        "terms": ["BAz", "BAe", "B\u03a6Z", "B\u03a6E"],
        "separator_after": 1,   # dashed line between BAe and BΦZ
        "subgroup_labels": None,
    },
    {
        "title": "Residuals",
        "label": "(e)",
        "terms": ["RGz", "RGe", "RKz", "RKe"],
        "separator_after": None,
        "subgroup_labels": None,
    },
    {
        "title": "Tendencies",
        "label": "(f)",
        "terms": [
            "\u2202Az/\u2202t (finite diff.)",
            "\u2202Ae/\u2202t (finite diff.)",
            "\u2202Kz/\u2202t (finite diff.)",
            "\u2202Ke/\u2202t (finite diff.)",
        ],
        "separator_after": None,
        "subgroup_labels": None,
    },
]

# Shorter y-tick aliases for verbose term names
DISPLAY_NAME_ALIASES = {
    "\u2202Az/\u2202t (finite diff.)": "\u2202Az/\u2202t",
    "\u2202Ae/\u2202t (finite diff.)": "\u2202Ae/\u2202t",
    "\u2202Kz/\u2202t (finite diff.)": "\u2202Kz/\u2202t",
    "\u2202Ke/\u2202t (finite diff.)": "\u2202Ke/\u2202t",
}

# ---- Discrete colour scale (0.10 bins) ----
EFFECT_THRESHOLDS = [0.10, 0.20, 0.30, 0.40, 0.50,
                     0.60, 0.70, 0.80, 0.90, 1.01]
EFFECT_COLORS = [
    "#b3b3b3",  # < 0.10   grey — negligible
    "#ffff99",  # 0.10–0.20  light yellow
    "#ffe64d",  # 0.20–0.30  yellow
    "#ffcc00",  # 0.30–0.40  yellow-orange
    "#ffb300",  # 0.40–0.50  amber
    "#ff9900",  # 0.50–0.60  orange
    "#ff7300",  # 0.60–0.70  deep orange
    "#ff4d00",  # 0.70–0.80  orange-red
    "#e62600",  # 0.80–0.90  red-orange
    "#cc0000",  # ≥ 0.90     red
]
BIN_LABELS = [
    "< 0.10  (negligible)",
    "0.10 – 0.20  (small)",
    "0.20 – 0.30",
    "0.30 – 0.40  (medium)",
    "0.40 – 0.50",
    "0.50 – 0.60  (large)",
    "0.60 – 0.70",
    "0.70 – 0.80",
    "0.80 – 0.90",
    "≥ 0.90",
]

NS_CONVENTION = "hatch"   # 'hatch' uses ///  overlay; 'text' uses gray italic 'ns'
HATCH_PATTERN = "///"
HATCH_COLOR   = "#666666"


# ============================================================================
# Helpers
# ============================================================================

def _make_cmap_norm():
    cmap = mcolors.ListedColormap(EFFECT_COLORS)
    norm = mcolors.BoundaryNorm([0.0] + EFFECT_THRESHOLDS, cmap.N)
    return cmap, norm


def _draw_panel(ax, pivot_eff, pivot_sig, group_def, cmap, norm, avail_contrasts):
    """Draw a single group heatmap panel on `ax`."""
    terms = [t for t in group_def["terms"] if t in pivot_eff.index]
    if not terms:
        ax.set_visible(False)
        return

    ytick_labels = [DISPLAY_NAME_ALIASES.get(t, t) for t in terms]

    data_eff = pivot_eff.reindex(index=terms, columns=avail_contrasts).fillna(0.0)
    data_sig = pivot_sig.reindex(index=terms, columns=avail_contrasts).fillna(False)

    n_rows, n_cols = data_eff.shape
    ax.imshow(data_eff.values, aspect="auto", cmap=cmap, norm=norm, zorder=1)

    # NS hatching overlay
    for i in range(n_rows):
        for j in range(n_cols):
            if not bool(data_sig.values[i, j]):
                if NS_CONVENTION == "hatch":
                    rect = mpatches.Rectangle(
                        (j - 0.5, i - 0.5), 1.0, 1.0,
                        facecolor="none", hatch=HATCH_PATTERN,
                        edgecolor=HATCH_COLOR, linewidth=0.0, zorder=3,
                    )
                    ax.add_patch(rect)
                else:
                    ax.text(j, i, "ns", ha="center", va="center",
                            fontsize=6, color="#666666", style="italic", zorder=3)

    # Intra-panel subgroup separator (dashed line)
    sep = group_def.get("separator_after")
    if sep is not None and 0 <= sep < n_rows - 1:
        y = sep + 0.5
        ax.plot([-0.5, n_cols - 0.5], [y, y],
                color="#333333", linewidth=1.2, linestyle="--", zorder=5)

    # Optional subgroup micro-labels (right-margin annotations)
    sg_labels = group_def.get("subgroup_labels")
    if sg_labels:
        for row_start, sg_label in sg_labels.items():
            ax.annotate(
                sg_label,
                xy=(n_cols - 0.5, row_start),
                xycoords="data",
                ha="left", va="center",
                fontsize=max(FONT_SIZE_TICKS - 2, 7),
                color="#555555", style="italic",
                annotation_clip=False,
                zorder=6,
                xytext=(4, 0), textcoords="offset points",
            )

    # Axes ticks
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(
        avail_contrasts, fontsize=FONT_SIZE_TICKS, rotation=20, ha="right",
    )
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(ytick_labels, fontsize=FONT_SIZE_TICKS)
    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True,
                   length=2, pad=2)
    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_ylim(n_rows - 0.5, -0.5)

    # Panel title — label integrated
    ax.set_title(
        f"{group_def['label']} {group_def['title']}",
        fontsize=FONT_SIZE_GROUP_TITLE, fontweight="bold", pad=5, loc="left",
    )


# ============================================================================
# Main figure function
# ============================================================================

def build_figure(pair_df: pd.DataFrame) -> Path:
    sub = pair_df[pair_df["var_type"] == "LEC term"].copy()
    sub["abs_effect"] = sub["effect_size"].abs()
    sub["is_sig"]     = sub["p_value_adjusted"] < ALPHA

    avail_contrasts = [c for c in CONTRAST_ORDER if c in sub["contrast"].unique()]

    pivot_eff = sub.pivot_table(
        index="display_name", columns="contrast",
        values="abs_effect", aggfunc="max",
    ).reindex(columns=avail_contrasts).fillna(0.0)

    pivot_sig = sub.pivot_table(
        index="display_name", columns="contrast",
        values="is_sig", aggfunc="max",
    ).reindex(columns=avail_contrasts).fillna(False)

    cmap, norm = _make_cmap_norm()

    # ---- Layout: 2 panel rows + 1 colorbar row, 3 cols ----
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    gs = gridspec.GridSpec(
        3, 3,
        figure=fig,
        height_ratios=[1, 1, 0.06],
        hspace=0.70,
        wspace=0.60,
    )
    axes    = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
    ax_cbar = fig.add_subplot(gs[2, :])

    for ax, group_def in zip(axes, PANEL_GROUPS):
        _draw_panel(ax, pivot_eff, pivot_sig, group_def, cmap, norm, avail_contrasts)

    # ---- Shared discrete colorbar (horizontal, bottom) ----
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(
        sm, cax=ax_cbar,
        orientation="horizontal",
        ticks=[0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00],
    )
    cbar.set_label("|rank-biserial r|", fontsize=FONT_SIZE_COLORBAR, labelpad=4)
    cbar.ax.tick_params(labelsize=FONT_SIZE_COLORBAR, length=2, rotation=45)

    fig.savefig(OUTPUT_FILE, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return OUTPUT_FILE


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 70)
    print("Figure S3: Pairwise Effect Size — LEC Terms (2×3 subplot layout)")
    print("=" * 70)

    if not INPUT_PAIR.exists():
        raise FileNotFoundError(
            f"Pairwise table not found: {INPUT_PAIR}\n"
            "Run scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py first."
        )

    print(f"\n1. Loading pairwise table: {INPUT_PAIR}")
    pair_df = pd.read_csv(INPUT_PAIR)
    pair_df["effect_size"]      = pd.to_numeric(pair_df["effect_size"],      errors="coerce")
    pair_df["p_value_adjusted"] = pd.to_numeric(pair_df["p_value_adjusted"], errors="coerce")

    lec_sub = pair_df[pair_df["var_type"] == "LEC term"]
    print(f"   LEC term rows: {len(lec_sub)}")
    print(f"   LEC terms:     {sorted(lec_sub['display_name'].unique())}")
    print(f"   Contrasts:     {sorted(lec_sub['contrast'].unique())}")

    print("\n2. Building figure (2×3 grouped subplot grid)...")
    out = build_figure(pair_df)

    try:
        from PIL import Image
        with Image.open(out) as img:
            print(f"\n✅ Figure saved: {out}")
            print(f"   Dimensions:    {img.size[0]} × {img.size[1]} px")
            print(f"   File size:     {out.stat().st_size / 1024:.1f} KB")
    except ImportError:
        print(f"\n✅ Figure saved: {out}")
        print(f"   File size:     {out.stat().st_size / 1024:.1f} KB")

    print("=" * 70)


if __name__ == "__main__":
    main()
