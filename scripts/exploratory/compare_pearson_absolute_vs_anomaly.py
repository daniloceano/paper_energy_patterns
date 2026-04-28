#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploratory: Pearson |r| comparison — Absolute vs Anomaly fields (EPALL, canonical LEC terms)

Three subplots per field type:
  (a) Absolute fields  — Pearson |r| for raw storm-relative fields
  (b) Anomaly fields   — Pearson |r| for (field_i − EPALL_composite)
  (c) Difference (a−b) — signed difference to highlight where anomaly
                          adds or removes signal relative to absolute fields

Run from repository root:
  python scripts/exploratory/compare_pearson_absolute_vs_anomaly.py

Output:
  figures/exploratory/compare_pearson_absolute_vs_anomaly.png
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

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ABS_CSV  = BASE_DIR / "results" / "lec_field_dependence" / "step7_predep_absolute_epall.csv"
ANOM_CSV = BASE_DIR / "results" / "lec_field_dependence" / "step7_predep_anomaly_epall.csv"
OUT_DIR  = BASE_DIR / "figures" / "exploratory"
OUT_PNG  = OUT_DIR / "compare_pearson_absolute_vs_anomaly.png"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Visual parameters
# ---------------------------------------------------------------------------
DPI                 = 150          # exploratory quality
FIGSIZE             = (22, 14)
FONT_FAMILY         = "DejaVu Sans"
FONT_SIZE_TITLE     = 11
FONT_SIZE_TICKS     = 9
FONT_SIZE_CBAR      = 10
FONT_SIZE_PANEL     = 11
XTICKLABEL_ROTATION = 45

# ---------------------------------------------------------------------------
# Scientific constants
# ---------------------------------------------------------------------------
LEC_ORDER = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]

# Absolute field key → display name
FIELD_GROUPS = {
    "adv_T_850":  "AdvT 850",
    "afc_250":    "AFC 250",
    "ke_adv_250": "KE adv 250",
    "pv_200":     "PV 200",
    "pv_850":     "PV 850",
}

FEATURE_ORDER = [
    "domain_mean", "domain_abs_mean", "centre_value",
    "border_north", "border_south", "border_east", "border_west",
    "contrast_ew", "contrast_sn",
    "sector_north", "sector_south", "sector_east", "sector_west",
]
FEATURE_DISPLAY = {
    "domain_mean":     "dom mean",
    "domain_abs_mean": "|dom mean|",
    "centre_value":    "centre",
    "border_north":    "bdr N",
    "border_south":    "bdr S",
    "border_east":     "bdr E",
    "border_west":     "bdr W",
    "contrast_ew":     "EW ctr",
    "contrast_sn":     "SN ctr",
    "sector_north":    "sec N",
    "sector_south":    "sec S",
    "sector_east":     "sec E",
    "sector_west":     "sec W",
}

GREY_THRESHOLD = 0.2
GREY_COLOR     = "#b3b3b3"
WARM_COLORS = [
    "#ffff99", "#ffe64d", "#ffcc00", "#ffb300",
    "#ff9900", "#ff7300", "#ff4d00", "#e62600", "#cc0000",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_data():
    abs_df  = pd.read_csv(ABS_CSV)
    anom_df = pd.read_csv(ANOM_CSV)

    # normalise anomaly field keys → strip _anom_epall suffix
    anom_df = anom_df.copy()
    anom_df["field"] = anom_df["field"].str.replace("_anom_epall", "", regex=False)

    for df in (abs_df, anom_df):
        df["abs_r"] = df["pearson_r"].abs()

    # keep canonical terms only
    for df in (abs_df, anom_df):
        df.drop(df[~df["lec_term"].isin(LEC_ORDER)].index, inplace=True)

    return abs_df, anom_df


def make_pivot(df, field_key):
    sub = df[df["field"] == field_key]
    pivot = sub.pivot_table(index="lec_term", columns="feature", values="abs_r")
    for t in LEC_ORDER:
        if t not in pivot.index:
            pivot.loc[t] = np.nan
    pivot = pivot.loc[LEC_ORDER]
    feat_ord = [f for f in FEATURE_ORDER if f in pivot.columns]
    feat_ext = [f for f in pivot.columns if f not in feat_ord]
    return pivot[feat_ord + feat_ext]


def make_diff_pivot(abs_piv, anom_piv):
    """Signed difference (abs |r|) − (anom |r|), aligned on same columns."""
    cols = abs_piv.columns  # same columns guaranteed by FEATURE_ORDER
    return abs_piv[cols] - anom_piv[cols]


def corr_cmap(vmax):
    """Discrete warm colormap for |r|, grey below GREY_THRESHOLD."""
    n_warm = int(round((vmax - GREY_THRESHOLD) / 0.1))
    boundaries = [0.0, GREY_THRESHOLD] + [
        GREY_THRESHOLD + (i + 1) * 0.1 for i in range(n_warm)
    ]
    cmap = mcolors.ListedColormap(
        [GREY_COLOR] + WARM_COLORS[:n_warm], name="corr_warm"
    )
    norm = mcolors.BoundaryNorm(boundaries, ncolors=cmap.N)
    return cmap, norm, boundaries


def diff_cmap(vlim):
    """Diverging discrete colormap for difference panel, symmetric around 0."""
    step  = 0.05
    n_pos = int(np.ceil(vlim / step))
    boundaries = np.concatenate([
        [-n_pos * step - 1e-9],
        np.linspace(-n_pos * step, n_pos * step, 2 * n_pos + 1),
    ]).tolist()
    cmap = plt.get_cmap("RdBu_r", 2 * n_pos)
    norm = mcolors.BoundaryNorm(boundaries[1:], ncolors=cmap.N)
    return cmap, norm, n_pos * step


def draw_corr(ax, mat_vals, columns, label, cmap, norm):
    im = ax.imshow(mat_vals, aspect="auto", cmap=cmap, norm=norm,
                   interpolation="nearest")
    xlabels = [FEATURE_DISPLAY.get(c, c) for c in columns]
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=XTICKLABEL_ROTATION,
                       ha="right", fontsize=FONT_SIZE_TICKS)
    ax.set_yticks(range(len(LEC_ORDER)))
    ax.set_yticklabels(LEC_ORDER, fontsize=FONT_SIZE_TICKS)
    ax.set_title(label, fontsize=FONT_SIZE_TITLE, fontweight="bold", pad=5)
    for x in np.arange(-0.5, mat_vals.shape[1], 1):
        ax.axvline(x, color="white", linewidth=0.3)
    for y in np.arange(-0.5, mat_vals.shape[0], 1):
        ax.axhline(y, color="white", linewidth=0.3)
    ax.tick_params(axis="both", which="both", length=0)
    return im


def draw_diff(ax, mat_vals, columns, label, cmap, norm):
    im = ax.imshow(mat_vals, aspect="auto", cmap=cmap, norm=norm,
                   interpolation="nearest")
    xlabels = [FEATURE_DISPLAY.get(c, c) for c in columns]
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=XTICKLABEL_ROTATION,
                       ha="right", fontsize=FONT_SIZE_TICKS)
    ax.set_yticks(range(len(LEC_ORDER)))
    ax.set_yticklabels(LEC_ORDER, fontsize=FONT_SIZE_TICKS)
    ax.set_title(label, fontsize=FONT_SIZE_TITLE, fontweight="bold", pad=5)
    for x in np.arange(-0.5, mat_vals.shape[1], 1):
        ax.axvline(x, color="white", linewidth=0.3)
    for y in np.arange(-0.5, mat_vals.shape[0], 1):
        ax.axhline(y, color="white", linewidth=0.3)
    ax.tick_params(axis="both", which="both", length=0)
    return im


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    matplotlib.rcParams["font.family"] = FONT_FAMILY

    abs_df, anom_df = load_data()

    global_max = max(abs_df["abs_r"].max(), anom_df["abs_r"].max())
    vmax = np.ceil(global_max * 10) / 10
    print(f"Global max |r| = {global_max:.4f}  →  vmax = {vmax:.1f}")

    cmap_c, norm_c, bounds_c = corr_cmap(vmax)

    # compute global diff range for symmetric diverging colorbar
    diff_vals_all = []
    for fk in FIELD_GROUPS:
        ap = make_pivot(abs_df, fk)
        np_ = make_pivot(anom_df, fk)
        diff_vals_all.append(make_diff_pivot(ap, np_).values.ravel())
    diff_flat = np.concatenate(diff_vals_all)
    diff_flat = diff_flat[~np.isnan(diff_flat)]
    vlim = np.ceil(np.abs(diff_flat).max() * 20) / 20  # round to nearest 0.05
    cmap_d, norm_d, _ = diff_cmap(vlim)
    print(f"Diff range ±{vlim:.2f}")

    n_fields = len(FIELD_GROUPS)
    # Layout: n_fields rows × 3 cols + 2 colorbar rows
    fig = plt.figure(figsize=FIGSIZE)
    gs = gridspec.GridSpec(
        n_fields + 2, 3,
        figure=fig,
        hspace=0.65, wspace=0.30,
        height_ratios=[1.0] * n_fields + [0.05, 0.05],
    )

    # Column header labels
    col_headers = [
        "(a) Absolute |r|",
        "(b) Anomaly |r|",
        "(c) Difference (a − b)",
    ]

    last_im_c = None
    last_im_d = None

    for row_idx, (field_key, field_title) in enumerate(FIELD_GROUPS.items()):
        abs_piv  = make_pivot(abs_df,  field_key)
        anom_piv = make_pivot(anom_df, field_key)
        diff_piv = make_diff_pivot(abs_piv, anom_piv)
        cols     = abs_piv.columns.tolist()

        for col_idx in range(3):
            ax = fig.add_subplot(gs[row_idx, col_idx])

            # row label on left side of col 0
            if col_idx == 0:
                ax.set_ylabel(field_title, fontsize=FONT_SIZE_TITLE,
                              fontweight="bold", labelpad=6)

            # column header only on first row
            header = col_headers[col_idx] if row_idx == 0 else ""

            if col_idx < 2:
                piv = abs_piv if col_idx == 0 else anom_piv
                last_im_c = draw_corr(ax, piv.values, cols, header,
                                      cmap_c, norm_c)
            else:
                last_im_d = draw_diff(ax, diff_piv.values, cols, header,
                                      cmap_d, norm_d)

    # Shared colorbar — correlation panels
    cbar_ax_c = fig.add_subplot(gs[n_fields, :2])
    cb_c = fig.colorbar(last_im_c, cax=cbar_ax_c, orientation="horizontal")
    cb_c.set_label("Pearson |r|", fontsize=FONT_SIZE_CBAR)
    tick_vals = bounds_c[1:]
    tick_labels = ["grey"] + [f"{v:.1f}" for v in tick_vals[1:]]
    cb_c.set_ticks(tick_vals)
    cb_c.set_ticklabels(tick_labels, fontsize=FONT_SIZE_TICKS - 1)

    # Shared colorbar — difference panel
    cbar_ax_d = fig.add_subplot(gs[n_fields + 1, 2])
    cb_d = fig.colorbar(last_im_d, cax=cbar_ax_d, orientation="horizontal")
    cb_d.set_label("Δ |r|  (abs − anom)", fontsize=FONT_SIZE_CBAR)
    cb_d.ax.xaxis.set_tick_params(labelsize=FONT_SIZE_TICKS - 1)

    fig.suptitle(
        "Pearson |r|: Absolute vs. Anomaly fields — EPALL, canonical LEC terms",
        fontsize=13, fontweight="bold", y=1.005,
    )

    fig.savefig(OUT_PNG, dpi=DPI, bbox_inches="tight")
    plt.close(fig)

    import os
    size_kb = os.path.getsize(OUT_PNG) / 1024
    try:
        from PIL import Image
        with Image.open(OUT_PNG) as img:
            w, h = img.size
        print(f"\n✓ Saved: {OUT_PNG}")
        print(f"  Dimensions: {w}×{h} px  |  {size_kb:.1f} KB")
    except ImportError:
        print(f"\n✓ Saved: {OUT_PNG}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
