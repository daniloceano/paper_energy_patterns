#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 9: Pearson |r| Heatmaps — EPALL, Absolute Fields, Canonical LEC Terms
          (grouped by field type)

Scientific context
------------------
Each panel shows the absolute Pearson correlation between a spatial feature of
one dynamic field (AdvT 850, AFC 250, KE adv 250, PV 200, PV 850) and each of
the seven canonical LEC terms (Ca, Ck, BAe, BKe, Ae, Ke, Ge) for all EP
cyclones (EPALL) using storm-relative absolute fields.

Layout: five subplots in a 3×2 grid, one per field type, with a shared
global colorbar.  Values with |r| < 0.2 are plotted in grey (below the
physically meaningful threshold).

Data source (same as diagnostic figure
  figures/lec_field_dependence/diagnostics/correlation_heatmaps/canonical/
  heatmap_pearson_epall_absolute_canonical.png):
  results/lec_field_dependence/step7_predep_absolute_epall.csv

Output:
  figures/main/9_pearson_epall_by_field_type.png  (300 DPI)

Run from repository root:
  python scripts/main/09_figure_pearson_epall_by_field_type.py

Author: Danilo Couto de Souza
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec

# ---------------------------------------------------------------------------
# Resolve project root so the script works from any cwd
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

# ---------------------------------------------------------------------------
# Configurable visual parameters
# ---------------------------------------------------------------------------
FIGSIZE              = (10.0, 12.0)   # inches (width × height)
DPI                  = 300
FONT_FAMILY          = "DejaVu Sans"
FONT_SIZE_TITLE      = 14             # panel title
FONT_SIZE_AXIS       = 13             # axis labels
FONT_SIZE_TICKS      = 11             # tick labels
FONT_SIZE_CBAR       = 13             # colorbar label
FONT_SIZE_PANEL      = 14            # (a), (b), … labels
XTICKLABEL_ROTATION  = 45            # degrees; change to 90 if labels overlap
GREY_THRESHOLD       = 0.2           # |r| below this → grey
COLORBAR_STEP        = 0.1           # discrete bin width
NCOLS                = 2             # subplot columns

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_CSV   = BASE_DIR / "results" / "lec_field_dependence" / "step7_predep_absolute_epall.csv"
FIGURES_DIR = BASE_DIR / "figures" / "main"
OUTPUT_PNG  = FIGURES_DIR / "9_pearson_epall_by_field_type.png"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Scientific constants (do not modify without justification)
# ---------------------------------------------------------------------------

# Canonical LEC term order — same as the original diagnostic figure and
# step1_normalize_and_pca.py ENERGY_VARS list.
LEC_ORDER = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]

# Field groups present in step7_predep_absolute_epall.csv
# (internal key → panel title)
FIELD_GROUPS = {
    "adv_T_850":  "AdvT 850",
    "afc_250":    "AFC 250",
    "ke_adv_250": "KE adv 250",
    "pv_200":     "PV 200",
    "pv_850":     "PV 850",
}

# Preferred feature display order and labels (X-axis within each panel)
FEATURE_ORDER = [
    "domain_mean", "domain_abs_mean", "centre_value",
    "border_north", "border_south", "border_east", "border_west",
    "contrast_ew", "contrast_sn",
    "sector_north", "sector_south", "sector_east", "sector_west",
]
FEATURE_DISPLAY = {
    "domain_mean":     "domain mean",
    "domain_abs_mean": "|domain mean|",
    "centre_value":    "centre value",
    "border_north":    "border N",
    "border_south":    "border S",
    "border_east":     "border E",
    "border_west":     "border W",
    "contrast_ew":     "E\u2013W contrast",
    "contrast_sn":     "S\u2013N contrast",
    "sector_north":    "sector N",
    "sector_south":    "sector S",
    "sector_east":     "sector E",
    "sector_west":     "sector W",
}

# Original warm palette from diag_correlation_heatmaps.py — preserved exactly
# (grey for |r| < GREY_THRESHOLD, then warm tones in 0.1 steps)
GREY_COLOR  = "#b3b3b3"
WARM_COLORS = [
    "#ffff99",   # 0.20–0.30
    "#ffe64d",   # 0.30–0.40
    "#ffcc00",   # 0.40–0.50
    "#ffb300",   # 0.50–0.60
    "#ff9900",   # 0.60–0.70
    "#ff7300",   # 0.70–0.80
    "#ff4d00",   # 0.80–0.90
    "#e62600",   # 0.90–1.00
    "#cc0000",   # ≥ 1.00
]


# ===========================================================================
# Helper functions
# ===========================================================================

def load_data() -> pd.DataFrame:
    """Load EPALL anomaly predep results (ep == 0, field_type == 'anomaly')."""
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_CSV}\n"
            "The EPALL run of step 7 has not been executed yet.\n"
            "Run the following command from the project root:\n"
            "    python scripts/lec_field_dependence_analysis/step7_compute_predep.py "
            "--field-type absolute --ep 0\n"
            "Then rerun this script."
        )
    df = pd.read_csv(INPUT_CSV)
    df = df[df["lec_term"].isin(LEC_ORDER) & df["pearson_r"].notna()].copy()
    df["abs_r"] = df["pearson_r"].abs()
    return df


def make_colormap(vmax: float):
    """
    Discrete ListedColormap and BoundaryNorm.

    Bins:  [0, GREY_THRESHOLD)  → grey
           [GREY_THRESHOLD, vmax] in COLORBAR_STEP increments → warm tones
    """
    n_warm = int(round((vmax - GREY_THRESHOLD) / COLORBAR_STEP))
    warm_slice = WARM_COLORS[:n_warm]
    boundaries = (
        [0.0, GREY_THRESHOLD]
        + [GREY_THRESHOLD + (i + 1) * COLORBAR_STEP for i in range(n_warm)]
    )
    cmap = mcolors.ListedColormap([GREY_COLOR] + warm_slice, name="pearson_discrete")
    norm = mcolors.BoundaryNorm(boundaries, ncolors=cmap.N)
    return cmap, norm, boundaries


def pivot_for_field(df: pd.DataFrame, field_key: str) -> pd.DataFrame:
    """Build a (LEC_ORDER × features) pivot table for *field_key*."""
    sub = df[df["field"] == field_key].copy()
    pivot = sub.pivot_table(index="lec_term", columns="feature", values="abs_r")

    # Guarantee all canonical terms appear (fill missing with NaN)
    for t in LEC_ORDER:
        if t not in pivot.index:
            pivot.loc[t] = np.nan
    pivot = pivot.loc[LEC_ORDER]

    feat_ordered  = [f for f in FEATURE_ORDER if f in pivot.columns]
    feat_extra    = [f for f in pivot.columns  if f not in feat_ordered]
    return pivot[feat_ordered + feat_extra]


def draw_panel(ax, pivot, title, cmap, norm, panel_label):
    """Draw one field-type heatmap panel."""
    mat = pivot.values
    im = ax.imshow(mat, aspect="auto", cmap=cmap, norm=norm,
                   interpolation="nearest")

    xlabels = [FEATURE_DISPLAY.get(c, c) for c in pivot.columns]
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=XTICKLABEL_ROTATION,
                       ha="right", fontsize=FONT_SIZE_TICKS,
                       fontfamily=FONT_FAMILY)

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index.tolist(),
                       fontsize=FONT_SIZE_TICKS,
                       fontfamily=FONT_FAMILY)

    ax.set_title(f"{panel_label} {title}", fontsize=FONT_SIZE_TITLE,
                 fontweight="bold", fontfamily=FONT_FAMILY, pad=6)

    for x in np.arange(-0.5, mat.shape[1], 1):
        ax.axvline(x, color="white", linewidth=0.4)
    for y in np.arange(-0.5, mat.shape[0], 1):
        ax.axhline(y, color="white", linewidth=0.4)

    ax.tick_params(axis="both", which="both", length=0)
    return im


# ===========================================================================
# Main
# ===========================================================================

def main():
    matplotlib.rcParams["font.family"] = FONT_FAMILY

    df = load_data()

    # Global vmax: round up to nearest 0.1
    global_max = df["abs_r"].max()
    vmax = np.ceil(global_max * 10) / 10
    print(f"Global max |r| = {global_max:.4f}  →  vmax = {vmax:.1f}")

    cmap, norm, boundaries = make_colormap(vmax)

    fields_present = [f for f in FIELD_GROUPS if f in df["field"].unique()]
    n_panels = len(fields_present)
    nrows = int(np.ceil(n_panels / NCOLS))
    print(f"Field groups: {n_panels}  →  layout {nrows}×{NCOLS}")

    fig = plt.figure(figsize=FIGSIZE)
    gs = gridspec.GridSpec(
        nrows + 1, NCOLS,
        figure=fig,
        hspace=0.8,
        wspace=0.12,
        height_ratios=[1.0] * nrows + [0.06],
    )

    panel_labels = [f"({chr(ord('a') + i)})" for i in range(n_panels)]
    last_im = None

    for idx, (field_key, panel_label) in enumerate(zip(fields_present, panel_labels)):
        row, col = divmod(idx, NCOLS)
        ax = fig.add_subplot(gs[row, col])
        pivot = pivot_for_field(df, field_key)
        last_im = draw_panel(
            ax, pivot, FIELD_GROUPS[field_key],
            cmap, norm, panel_label,
        )

    # Hide any spare axes in the last row
    if n_panels % NCOLS:
        for spare_col in range(n_panels % NCOLS, NCOLS):
            fig.add_subplot(gs[nrows - 1, spare_col]).set_visible(False)

    # Shared colorbar spanning full width at the bottom
    cbar_ax = fig.add_subplot(gs[nrows, :])
    cb = fig.colorbar(last_im, cax=cbar_ax, orientation="horizontal",
                      extend="neither")
    cb.set_label("Pearson |r|", fontsize=FONT_SIZE_CBAR, fontfamily=FONT_FAMILY)

    tick_vals  = boundaries[1:]          # skip 0 (lower bound of grey)
    tick_labels = ["0.2"] + [f"{v:.1f}" for v in tick_vals[1:]]
    cb.set_ticks(tick_vals)
    cb.set_ticklabels(tick_labels, fontsize=FONT_SIZE_TICKS,
                      fontfamily=FONT_FAMILY)
    cb.ax.xaxis.set_tick_params(length=4)

    fig.savefig(OUTPUT_PNG, dpi=DPI, bbox_inches="tight")
    plt.close(fig)

    import os
    size_kb = os.path.getsize(OUTPUT_PNG) / 1024
    try:
        from PIL import Image
        with Image.open(OUTPUT_PNG) as img:
            w, h = img.size
        print(f"\n✓ Saved: {OUTPUT_PNG}")
        print(f"  Dimensions: {w}×{h} px")
        print(f"  File size:  {size_kb:.1f} KB")
    except ImportError:
        print(f"\n✓ Saved: {OUTPUT_PNG}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
