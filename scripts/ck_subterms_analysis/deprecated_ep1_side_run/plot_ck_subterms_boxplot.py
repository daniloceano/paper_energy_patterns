#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_ck_subterms_boxplot.py — Exploratory boxplot of Ck subterm distributions.

Reads results/ck_analysis/ck_subterms_boxplot_input.csv (produced by
build_ck_subterms_summary.py) and plots the distribution of each Ck subterm
for a given lifecycle phase.

Usage
-----
    # Default: intensification phase
    python scripts/ck_subterms_analysis/plot_ck_subterms_boxplot.py

    # Other phase
    python scripts/ck_subterms_analysis/plot_ck_subterms_boxplot.py --phase mature

    # Custom output directory
    python scripts/ck_subterms_analysis/plot_ck_subterms_boxplot.py \
        --phase intensification \
        --outdir figures/ck_analysis

Available phases: incipient, intensification, mature, decay, residual

Outputs (in figures/ck_analysis/ by default)
-------------------------------------------
    ck_subterms_boxplot_{phase}.png
    ck_subterms_boxplot_{phase}.pdf

Author: Danilo Couto de Souza / GitHub Copilot
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

warnings.filterwarnings("ignore")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parents[2]
INPUT_CSV  = BASE_DIR / "results" / "ck_analysis" / "ck_subterms_boxplot_input.csv"
DEFAULT_OUTDIR = BASE_DIR / "figures" / "ck_analysis"

# ── subterm display order and labels ─────────────────────────────────────────
SUBTERM_ORDER  = ["Ck_A", "Ck_B", "Ck_C", "Ck_D", "Ck_E"]
SUBTERM_LABELS = {
    "Ck_A": r"$C_K^{(A)}$",
    "Ck_B": r"$C_K^{(B)}$",
    "Ck_C": r"$C_K^{(C)}$",
    "Ck_D": r"$C_K^{(D)}$",
    "Ck_E": r"$C_K^{(E)}$",
    # Also handle the raw names in case the CSV uses them
    "Ck_1": r"$C_K^{(A)}$",
    "Ck_2": r"$C_K^{(B)}$",
    "Ck_3": r"$C_K^{(C)}$",
    "Ck_4": r"$C_K^{(D)}$",
    "Ck_5": r"$C_K^{(E)}$",
}

# Descriptions for the legend / annotation
SUBTERM_DESCS = {
    "Ck_A": "Meridional gradient of zonal wind",
    "Ck_B": "Meridional flux of eddy KE",
    "Ck_C": "Curvature (tan φ) term",
    "Ck_D": "Vertical shear of zonal wind",
    "Ck_E": "Vertical shear of meridional wind",
}

# Colorblind-friendly palette (Wong 2011)
COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]

VALID_PHASES = ["incipient", "intensification", "mature", "decay", "residual"]


# ============================================================================
# FIGURE
# ============================================================================

def make_boxplot(df_phase: pd.DataFrame, phase: str, outdir: Path) -> list[Path]:
    """Create the boxplot figure and save PNG + PDF."""

    # Determine which subterm column to use
    sub_col = "subterm"
    if sub_col not in df_phase.columns and "subterm_raw" in df_phase.columns:
        sub_col = "subterm_raw"

    # Build ordered list of subterms present in data
    present = df_phase[sub_col].unique().tolist()

    # Try canonical order first, then fall back to raw names
    order = [s for s in SUBTERM_ORDER if s in present]
    if not order:
        raw_order = ["Ck_1", "Ck_2", "Ck_3", "Ck_4", "Ck_5"]
        order = [s for s in raw_order if s in present]
    if not order:
        order = sorted(present)

    df_plot = df_phase[df_phase[sub_col].isin(order)].copy()
    df_plot["_label"] = df_plot[sub_col].map(
        lambda x: SUBTERM_LABELS.get(x, x)
    )
    label_order = [SUBTERM_LABELS.get(s, s) for s in order]

    colors = COLORS[: len(order)]

    # ── figure layout ────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7.5, 5.0))

    if HAS_SEABORN:
        sns.boxplot(
            data=df_plot,
            x="_label",
            y="value",
            order=label_order,
            palette=colors,
            width=0.55,
            linewidth=1.0,
            flierprops=dict(marker="o", markersize=2.5, alpha=0.4, linestyle="none"),
            ax=ax,
        )
        # Overlay individual points (jitter)
        sns.stripplot(
            data=df_plot,
            x="_label",
            y="value",
            order=label_order,
            palette=colors,
            size=2.5,
            alpha=0.35,
            jitter=True,
            dodge=False,
            ax=ax,
        )
    else:
        # Matplotlib fallback
        groups = [
            df_plot.loc[df_plot[sub_col] == s, "value"].dropna().values
            for s in order
        ]
        bplot = ax.boxplot(
            groups,
            labels=label_order,
            patch_artist=True,
            widths=0.55,
            flierprops=dict(marker="o", markersize=2.5, alpha=0.4),
            medianprops=dict(color="black", linewidth=1.5),
        )
        for patch, color in zip(bplot["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)

    # ── reference line at zero ───────────────────────────────────────────────
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)

    # ── annotations: n per subterm ───────────────────────────────────────────
    y_min = ax.get_ylim()[0]
    for i, s in enumerate(order):
        n = int(df_plot.loc[df_plot[sub_col] == s, "value"].notna().sum())
        ax.text(
            i, y_min * 1.02, f"n={n}",
            ha="center", va="top",
            fontsize=7.5, color="dimgrey",
        )

    # ── labels and formatting ────────────────────────────────────────────────
    phase_title = phase.capitalize()
    ax.set_title(
        f"Distribution of $C_K$ Subterms — {phase_title} Phase\n"
        f"(EP1 cyclones, vertically integrated, W m$^{{-2}}$)",
        fontsize=11, pad=10,
    )
    ax.set_xlabel("$C_K$ Subterm", fontsize=10)
    ax.set_ylabel("$C_K$ subterm  (W m$^{-2}$)", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:.0f}"
    ))
    ax.tick_params(axis="both", labelsize=9)

    # Sign convention note
    ax.text(
        0.99, 0.01,
        r"$C_K < 0$: K$_Z$ → K$_E$  (barotropic instability)",
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=7.5, color="grey",
        style="italic",
    )

    # Brief description legend
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.75)
        for c in colors
    ]
    legend_labels = [
        f"{SUBTERM_LABELS.get(s, s)}: {SUBTERM_DESCS.get(s, SUBTERM_DESCS.get('Ck_' + s[-1], s))}"
        for s in order
    ]
    ax.legend(
        handles, legend_labels,
        loc="upper right",
        fontsize=7.5,
        framealpha=0.85,
        edgecolor="lightgrey",
        title="Subterm description",
        title_fontsize=8,
    )

    fig.tight_layout()

    # ── save ─────────────────────────────────────────────────────────────────
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"ck_subterms_boxplot_{phase}"
    png_path = outdir / f"{stem}.png"
    pdf_path = outdir / f"{stem}.pdf"
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    return [png_path, pdf_path]


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Plot Ck subterm distributions as a boxplot."
    )
    parser.add_argument(
        "--phase", default="intensification",
        choices=VALID_PHASES,
        help="Lifecycle phase to plot (default: intensification).",
    )
    parser.add_argument(
        "--input", default=str(INPUT_CSV), metavar="CSV",
        help="Path to ck_subterms_boxplot_input.csv.",
    )
    parser.add_argument(
        "--outdir", default=str(DEFAULT_OUTDIR), metavar="DIR",
        help="Output directory for figures.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir     = Path(args.outdir)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" plot_ck_subterms_boxplot.py")
    print(f"  Phase  : {args.phase}")
    print(f"  Input  : {input_path}")
    print(f"  Output : {outdir}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not input_path.exists():
        sys.exit(
            f"ERROR: Input file not found: {input_path}\n"
            "Run build_ck_subterms_summary.py (on remote) first, then sync."
        )

    df = pd.read_csv(input_path)
    required = {"value"}
    if not required.issubset(df.columns):
        sys.exit(f"ERROR: Expected column 'value' in {input_path}.")

    # Filter by phase
    if "phase" not in df.columns:
        sys.exit("ERROR: 'phase' column not found in input CSV.")

    df_phase = df[df["phase"] == args.phase].copy()
    if df_phase.empty:
        available = df["phase"].unique().tolist()
        sys.exit(
            f"ERROR: No data for phase '{args.phase}'.\n"
            f"Available phases: {available}"
        )

    n_cyclones = df_phase["track_id"].nunique() if "track_id" in df_phase.columns else "?"
    print(f"\n  Cyclones with data in '{args.phase}' phase: {n_cyclones}")

    paths = make_boxplot(df_phase, args.phase, outdir)

    print()
    for p in paths:
        rel = p.relative_to(BASE_DIR) if p.is_absolute() else p
        print(f"  ✔  {rel}")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
