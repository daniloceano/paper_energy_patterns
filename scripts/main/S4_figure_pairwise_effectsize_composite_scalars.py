#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S4: Pairwise Effect Size — Composite Scalar Features (EP1 vs EP2, EP1 vs EP3, EP2 vs EP3)

Discrete heatmap of |rank-biserial r| for each EPALL-relative (anomaly) scalar
feature extracted from the ERA5 storm-relative composites, across all three
pairwise EP contrasts. The statistical framework is:

  Global test:  Kruskal–Wallis (applied in step7b)
  Post-hoc:     Dunn test with Holm correction (step7b)
  Effect size:  |rank-biserial r|  (Dunn pairwise output)

Visual conventions:
  • Colour bins: 0.10 step, grey = negligible (|r| < 0.10)
  • Hatching (///)  : contrast is NOT statistically significant (p_adj ≥ 0.05)
  • No hatching     : contrast IS statistically significant (p_adj < 0.05)
  A grey cell WITHOUT hatching means the effect is negligible but the test
  did find a significant (though practically irrelevant) difference.
  A coloured cell WITH hatching means the magnitude suggests a non-negligible
  effect but the test did not reach significance — interpret with caution.
f
Design decisions:
  • Only EPALL-relative (anomaly) features are shown (field_type == 'anomaly').
    These connect directly to Figure 7's EPALL-relative composites and isolate
    EP-specific departures from the common intensifying-cyclone signal.
  • Fields are ordered by atmospheric level (upper → lower):
      PV 200 hPa → AFC 250 hPa → KE adv 250 hPa → AdvT 850 hPa → PV 850 hPa
  • Within each field, features follow a consistent physical ordering:
      domain mean → centre value → border N/S/E/W →
      S–N contrast → E–W contrast → sector_north/south/east/west → domain |mean|
  • Rows with no data for a given contrast are shown as grey (zero effect treated
    as negligible) — this preserves the rectangular layout across fields.

Data source: results/lec_field_dependence/step7b_pairwise_table.csv
  (produced by scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py)

Outputs:
  figures/main/S4_pairwise_effectsize_composite_scalars.png  (300 DPI)

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

OUTPUT_FILE = FIGURES_DIR / "S4_pairwise_effectsize_composite_scalars.png"

# Statistical threshold
ALPHA = 0.05

# Column order for contrasts
CONTRAST_ORDER = ["EP1 vs EP2", "EP1 vs EP3", "EP2 vs EP3"]

# ---- Feature selection ----
FIELD_TYPE_FILTER = "anomaly"

# ---- Configurable font sizes (edit here for publication adjustments) ----
FONT_SIZE_AXIS_LABEL  = 10   # x/y axis label text
FONT_SIZE_TICKS       = 8    # x/y tick labels
FONT_SIZE_LEGEND      = 9    # legend / NS patch text
FONT_SIZE_PANEL_LABEL = 11   # (a), (b), ... panel identifiers
FONT_SIZE_COLORBAR    = 9    # colorbar label and ticks
FONT_SIZE_GROUP_TITLE = 9    # each panel's title (field name)

# ---- Figure layout ----
FIG_WIDTH  = 10.5   # inches
FIG_HEIGHT = 11.5   # inches (2 panel rows × ~13 features/row @ ~0.4"/feature)
DPI        = 300

# ---- Panel definitions (2×3 grid, left-to-right, top-to-bottom) ----
# (field_origin, short_title, panel_label)
# The 6th slot is used for the colorbar/legend.
PANEL_FIELDS = [
    ("pv_200_anom_epall",     "PV 200 hPa (anom.)",    "(a)"),
    ("afc_250_anom_epall",    "AFC 250 hPa (anom.)",   "(b)"),
    ("ke_adv_250_anom_epall", "KE adv 250 hPa (anom.)","(c)"),
    ("adv_T_850_anom_epall",  "AdvT 850 hPa (anom.)",  "(d)"),
    ("pv_850_anom_epall",     "PV 850 hPa (anom.)",    "(e)"),
]

# ---- Discrete colour scale (0.10 bins) — identical to S3 ----
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

# ---- Field ordering (physical: upper → lower atmospheric level) ----
FIELD_ORDER = [
    ("pv_200_anom_epall",     "PV 200 anom"),
    ("afc_250_anom_epall",    "AFC 250 anom"),
    ("ke_adv_250_anom_epall", "KE adv 250 anom"),
    ("adv_T_850_anom_epall",  "AdvT 850 anom"),
    ("pv_850_anom_epall",     "PV 850 anom"),
]

# ---- Feature ordering within every field (suffix after ' — ') ----
FEATURE_SUFFIX_ORDER = [
    "domain mean",
    "centre value",
    "border N",
    "border S",
    "border E",
    "border W",
    "S–N contrast",
    "E–W contrast",
    "sector_north",
    "sector_south",
    "sector_east",
    "sector_west",
    "domain |mean|",
]


# ============================================================================
# Helpers
# ============================================================================

def _make_cmap_norm():
    cmap = mcolors.ListedColormap(EFFECT_COLORS)
    norm = mcolors.BoundaryNorm([0.0] + EFFECT_THRESHOLDS, cmap.N)
    return cmap, norm


def _get_field_suffix_ordered_rows(sub: pd.DataFrame, field_origin: str) -> list:
    """
    Return list of display_names for a given field_origin, sorted by
    FEATURE_SUFFIX_ORDER; unknown suffixes appended at the end.
    """
    field_rows = sub[sub["field_origin"] == field_origin]
    if field_rows.empty:
        return []
    suffix_keys = {s: i for i, s in enumerate(FEATURE_SUFFIX_ORDER)}

    def sort_key(name):
        suffix = name.split(" \u2014 ", 1)[1] if " \u2014 " in name else name
        return suffix_keys.get(suffix, 999)

    return sorted(field_rows["display_name"].unique().tolist(), key=sort_key)


def _ytick_suffix(name: str) -> str:
    """Return only the feature suffix (after ' \u2014 ') for cleaner panel y-labels."""
    return name.split(" \u2014 ", 1)[1] if " \u2014 " in name else name


def _draw_field_panel(
    ax, sub, field_origin, panel_title, panel_label,
    avail_contrasts, cmap, norm,
    show_yticks: bool = True,
):
    """Draw one field panel on `ax`."""
    sorted_names = _get_field_suffix_ordered_rows(sub, field_origin)
    if not sorted_names:
        ax.set_visible(False)
        return

    pivot_eff = sub.pivot_table(
        index="display_name", columns="contrast",
        values="abs_effect", aggfunc="max",
    ).reindex(index=sorted_names, columns=avail_contrasts).fillna(0.0)

    pivot_sig = sub.pivot_table(
        index="display_name", columns="contrast",
        values="is_sig", aggfunc="max",
    ).reindex(index=sorted_names, columns=avail_contrasts).fillna(False)

    n_rows, n_cols = pivot_eff.shape
    ax.imshow(pivot_eff.values, aspect="auto", cmap=cmap, norm=norm, zorder=1)

    # NS hatching overlay
    for i in range(n_rows):
        for j in range(n_cols):
            if not bool(pivot_sig.values[i, j]):
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

    # Axes ticks
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(
        avail_contrasts, fontsize=FONT_SIZE_TICKS, rotation=20, ha="right",
    )
    ax.set_yticks(range(n_rows))
    if show_yticks:
        ytlabels = [_ytick_suffix(n) for n in sorted_names]
        ax.set_yticklabels(ytlabels, fontsize=FONT_SIZE_TICKS)
    else:
        ax.set_yticklabels([])
    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True,
                   length=2, pad=2)
    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_ylim(n_rows - 0.5, -0.5)

    # Panel title — label integrated
    ax.set_title(
        f"{panel_label} {panel_title}",
        fontsize=FONT_SIZE_GROUP_TITLE, fontweight="bold", pad=5, loc="left",
    )


def _legend_patches():
    patches = [
        mpatches.Patch(facecolor=EFFECT_COLORS[i], edgecolor="#888888",
                       linewidth=0.4, label=BIN_LABELS[i])
        for i in range(len(EFFECT_COLORS))
    ]
    ns_patch = mpatches.Patch(
        facecolor="white", edgecolor="#888888", linewidth=0.4,
        hatch=HATCH_PATTERN if NS_CONVENTION == "hatch" else None,
        label="Not significant (p$_{adj}$ ≥ 0.05)"
    )
    patches.append(ns_patch)
    return patches


# ============================================================================
# Main figure function
# ============================================================================

def build_figure(pair_df: pd.DataFrame) -> Path:
    sub = pair_df[
        (pair_df["var_type"] == "dynamic feature") &
        (pair_df["field_type"] == FIELD_TYPE_FILTER)
    ].copy()
    sub["abs_effect"] = sub["effect_size"].abs()
    sub["is_sig"]     = sub["p_value_adjusted"] < ALPHA

    avail_contrasts = [c for c in CONTRAST_ORDER if c in sub["contrast"].unique()]
    cmap, norm = _make_cmap_norm()

    # ---- Layout: 2 panel rows + 1 colorbar row, 3 cols ----
    # Panel mapping (left-to-right, top-to-bottom):
    #   (0,0) PV 200  | (0,1) AFC 250      | (0,2) KE adv 250
    #   (1,0) AdvT 850| (1,1) PV 850       | (1,2) [empty]
    #   row 2 (full width): horizontal colorbar
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    gs = gridspec.GridSpec(
        3, 3,
        figure=fig,
        height_ratios=[1, 1, 0.04],
        hspace=0.25,
        wspace=0.35,
    )
    panel_positions = [(r, c) for r in range(2) for c in range(3)]
    axes = [fig.add_subplot(gs[r, c]) for r, c in panel_positions]
    ax_cbar = fig.add_subplot(gs[2, :])

    for idx, (field_origin, panel_title, panel_label) in enumerate(PANEL_FIELDS):
        ax = axes[idx]
        row, col = panel_positions[idx]
        show_yticks = (col == 0)
        _draw_field_panel(
            ax, sub, field_origin, panel_title, panel_label,
            avail_contrasts, cmap, norm,
            show_yticks=show_yticks,
        )

    # Hide unused 6th panel slot
    axes[5].set_visible(False)

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
    print("Figure S4: Pairwise Effect Size — Composite Scalar Features (2×3 layout)")
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

    sub = pair_df[
        (pair_df["var_type"] == "dynamic feature") &
        (pair_df["field_type"] == FIELD_TYPE_FILTER)
    ]
    print(f"   Anomaly feature rows: {len(sub)}")
    print(f"   Unique display names: {sub['display_name'].nunique()}")
    print(f"   Fields: {sorted(sub['field_origin'].unique())}")
    print(f"   Contrasts: {sorted(sub['contrast'].unique())}")

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

