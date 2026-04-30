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
FIGSIZE              = (10.0, 9.0)   # inches (width × height)
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

# Colour palette (grey for |r| < GREY_THRESHOLD; warm for r > 0; blue for r < 0)
GREY_COLOR  = "#b3b3b3"
WARM_COLORS = [
    "#ffff99",   # +0.20–+0.30
    "#ffe64d",   # +0.30–+0.40
    "#ffcc00",   # +0.40–+0.50
    "#ffb300",   # +0.50–+0.60
    "#ff9900",   # +0.60–+0.70
    "#ff7300",   # +0.70–+0.80
    "#ff4d00",   # +0.80–+0.90
    "#e62600",   # +0.90–+1.00
    "#cc0000",   # ≥ +1.00
]
BLUE_COLORS = [
    "#dce4f5",   # -0.20 to -0.30  (lightest, closest to 0)
    "#b9caeb",   # -0.30 to -0.40
    "#8aaad7",   # -0.40 to -0.50
    "#5b84bc",   # ≤ -0.50         (darkest)
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
    Discrete diverging ListedColormap and BoundaryNorm for signed Pearson r.

    Bins:  (−vmax, −GREY_THRESHOLD)  → blue tones (light→dark going negative)
           [−GREY_THRESHOLD, +GREY_THRESHOLD) → grey
           [+GREY_THRESHOLD, +vmax]  → warm tones

    BLUE_COLORS has 4 entries (supports up to 4 negative steps, i.e. vmax ≤ 0.6).
    """
    n_steps = int(round((vmax - GREY_THRESHOLD) / COLORBAR_STEP))
    warm_slice = WARM_COLORS[:n_steps]
    # BLUE_COLORS is ordered lightest→darkest (closest to 0 → most negative);
    # reverse so the most-negative bin comes first in the boundary list.
    blue_slice = list(reversed(BLUE_COLORS[:n_steps]))

    neg_bounds = [-vmax + i * COLORBAR_STEP for i in range(n_steps)]
    boundaries = (
        neg_bounds
        + [-GREY_THRESHOLD, GREY_THRESHOLD]
        + [GREY_THRESHOLD + (i + 1) * COLORBAR_STEP for i in range(n_steps)]
    )
    colors = blue_slice + [GREY_COLOR] + warm_slice
    cmap = mcolors.ListedColormap(colors, name="pearson_diverging")
    norm = mcolors.BoundaryNorm(boundaries, ncolors=cmap.N)
    return cmap, norm, boundaries


def pivot_for_field(df: pd.DataFrame, field_key: str):
    """Return (pivot_r, pivot_rho) for *field_key* — both (LEC_ORDER × features)."""
    sub = df[df["field"] == field_key].copy()

    def _build(col):
        piv = sub.pivot_table(index="lec_term", columns="feature", values=col)
        for t in LEC_ORDER:
            if t not in piv.index:
                piv.loc[t] = np.nan
        piv = piv.loc[LEC_ORDER]
        feat_ordered = [f for f in FEATURE_ORDER if f in piv.columns]
        feat_extra   = [f for f in piv.columns  if f not in feat_ordered]
        return piv[feat_ordered + feat_extra]

    pivot_r   = _build("pearson_r")
    pivot_rho = _build("spearman_rho").reindex(columns=pivot_r.columns)
    return pivot_r, pivot_rho


def draw_panel(ax, pivot_r, pivot_rho, title, cmap, norm, panel_label):
    """Draw one field-type heatmap panel with hatching where |r - rho| > 0.1."""
    import matplotlib.patches as mpatches

    mat = pivot_r.values
    im = ax.imshow(mat, aspect="auto", cmap=cmap, norm=norm,
                   interpolation="nearest")

    xlabels = [FEATURE_DISPLAY.get(c, c) for c in pivot_r.columns]
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=XTICKLABEL_ROTATION,
                       ha="right", fontsize=FONT_SIZE_TICKS,
                       fontfamily=FONT_FAMILY)

    ax.set_yticks(range(len(pivot_r.index)))
    ax.set_yticklabels(pivot_r.index.tolist(),
                       fontsize=FONT_SIZE_TICKS,
                       fontfamily=FONT_FAMILY)

    ax.set_title(f"{panel_label} {title}", fontsize=FONT_SIZE_TITLE,
                 fontweight="bold", fontfamily=FONT_FAMILY, pad=6)

    for x in np.arange(-0.5, mat.shape[1], 1):
        ax.axvline(x, color="white", linewidth=0.4)
    for y in np.arange(-0.5, mat.shape[0], 1):
        ax.axhline(y, color="white", linewidth=0.4)

    # Hatch cells where |pearson_r - spearman_rho| > 0.1
    rho_mat = pivot_rho.values
    nrows_m, ncols_m = mat.shape
    for yi in range(nrows_m):
        for xi in range(ncols_m):
            r_val   = mat[yi, xi]
            rho_val = rho_mat[yi, xi]
            if np.isnan(r_val) or np.isnan(rho_val):
                continue
            if abs(r_val - rho_val) > 0.1:
                rect = mpatches.Rectangle(
                    (xi - 0.5, yi - 0.5), 1.0, 1.0,
                    linewidth=0, fill=False,
                    hatch="///", edgecolor="black", alpha=0.55,
                )
                ax.add_patch(rect)

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
        pivot_r, pivot_rho = pivot_for_field(df, field_key)
        last_im = draw_panel(
            ax, pivot_r, pivot_rho, FIELD_GROUPS[field_key],
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
    cb.set_label("Pearson r", fontsize=FONT_SIZE_CBAR, fontfamily=FONT_FAMILY)

    tick_vals   = boundaries
    tick_labels = [f"{v:.1f}" for v in tick_vals]
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
