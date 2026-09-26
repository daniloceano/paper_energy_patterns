#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S3: Vertical Profile of C_K (All Cyclones) and Integrated Subterms for EP1
         (Intensification Phase)

Scientific context
------------------
C_K decomposes barotropic kinetic-energy conversion into five subterms (A–E):

  C_K = ∫ (1/g) [ Ck^(A) + Ck^(B) + Ck^(C) + Ck^(D) + Ck^(E) ] dp

Sign convention (authoritative: paper.tex):
  C_K < 0  →  K_Z → K_E  (barotropic instability feeds the eddies)
  C_K > 0  →  K_E → K_Z  (eddies export energy to mean flow)

EP1 cyclones: mean C_K ≈ −16.5 W m⁻² — the strongest barotropic-instability
pattern.  The dominant level is ~350 hPa.

Subterm mapping (toolkit Ck_1…Ck_5 → paper labels A–E):
  Ck_1 → Ck^(A): meridional gradient of zonal wind
  Ck_2 → Ck^(B): meridional flux of eddy KE
  Ck_3 → Ck^(C): curvature (tan-φ) term
  Ck_4 → Ck^(D): vertical shear of zonal wind
  Ck_5 → Ck^(E): vertical shear of meridional wind

Data availability note
----------------------
Per-pressure-level files for the individual Ck subterms (Ck_1_level.csv …
Ck_5_level.csv) reside on the remote server under
  results/ck_analysis/lec_results/<track_id>_ERA5_track/results_vertical_levels/
and are NOT part of the local Zenodo archive.  Therefore this script uses:

  Panel (a) — Vertical profile of TOTAL C_K
    Source: data/temp_lec_zenodo/LEC_Results_energetic-patterns/<id>/Ck_level.csv
    (32 pressure levels, 3-hourly, corrected by /g = /9.8)
    EP1 cyclones only, intensification phase only.
    One boxplot per pressure level aggregating all EP1 cyclones.

  Panel (b) — Vertically integrated C_K subterms (Ck^A … Ck^E)
    Source: results/ck_analysis/ck_subterms_boxplot_input.csv
    EP1 cyclones only; phase-mean vertically integrated values (W m⁻²).

Outputs
-------
  figures/main/ck_subterms_vertical_profiles.png  (300 DPI)

Usage
-----
    # from repository root:
    python scripts/main/S3_figure_ck_subterms_vertical_profiles.py

Author: Danilo Couto de Souza / GitHub Copilot
Date:   April 2026
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scripts.utils import corrected_lec as clec
from scripts.utils.ep_mapping import assert_corrected_clustering

warnings.filterwarnings("ignore")

# ── repository root ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

# ============================================================================
# CONFIGURABLE VISUAL PARAMETERS
# ============================================================================

FIGSIZE             = (12, 7)      # (width, height) in inches
DPI                 = 300
FONT_SIZE_AXIS_LABEL = 11
FONT_SIZE_TICKS      = 9
FONT_SIZE_LEGEND     = 9
FONT_SIZE_PANEL_LABEL = 12
LINEWIDTH            = 1.2
BOXPLOT_WIDTH        = 0.6         # fraction of available slot width

# ============================================================================
# PATHS
# ============================================================================

EP1_CASES_CSV   = BASE_DIR / "results" / "ep_structure" / "ep1_cases.csv"
SUBTERMS_CSV    = BASE_DIR / "results" / "ck_subterms_corrected" / "subterms_long.csv"
FIGURES_DIR     = BASE_DIR / "figures" / "main"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PNG      = FIGURES_DIR / "ck_subterms_vertical_profiles.png"

# ============================================================================
# CONSTANTS
# ============================================================================

# Subterm display order and labels (panel b)
SUBTERM_ORDER = ["Ck_A", "Ck_B", "Ck_C", "Ck_D", "Ck_E"]
SUBTERM_LABELS = {
    "Ck_A": r"$C_K^{(A)}$",
    "Ck_B": r"$C_K^{(B)}$",
    "Ck_C": r"$C_K^{(C)}$",
    "Ck_D": r"$C_K^{(D)}$",
    "Ck_E": r"$C_K^{(E)}$",
}
SUBTERM_DESCS = {
    "Ck_A": "Merid. grad. zonal wind",
    "Ck_B": "Merid. flux eddy KE",
    "Ck_C": "Curvature (tan φ)",
    "Ck_D": "Vert. shear zonal wind",
    "Ck_E": "Vert. shear merid. wind",
}
# Colorblind-friendly palette (Wong 2011)
SUBTERM_COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]

# Standard pressure levels to display (hPa), ordered top → bottom for sorting
# (will be displayed bottom=1000 → top=100 in the figure)
PRESSURE_LEVELS_DISPLAY = [
    100, 125, 150, 175, 200, 225, 250, 300, 350, 400,
    450, 500, 550, 600, 650, 700, 750, 775, 800, 825,
    850, 875, 900, 925, 950, 975, 1000,
]


# ============================================================================
# DATA LOADING
# ============================================================================

def load_vertical_ck_ep1(ep1_cases: pd.DataFrame) -> dict[float, list[float]]:
    """
    Load Ck per pressure level for all EP1 cyclones, filtered to intensification.

    Returns a dict {pressure_Pa: [cyclone-mean values in W m⁻²]}.
    """
    profiles = clec.read_vertical_phase_means(
        terms=["Ck"], phases=["intensification"]
    )
    wanted = set(ep1_cases["track_id"].astype(str))
    profiles = profiles[profiles["track_id"].astype(str).isin(wanted)]
    covered = profiles["track_id"].nunique()
    if covered != len(wanted):
        raise RuntimeError(
            f"corrected Ck profiles cover {covered}/{len(wanted)} EP1 cyclones"
        )
    return {
        float(level): values.dropna().tolist()
        for level, values in profiles.groupby("level_hpa")["value"]
    }


def load_integrated_subterms() -> pd.DataFrame:
    """
    Load vertically integrated Ck subterms from ck_subterms_boxplot_input.csv.

    Returns tidy DataFrame with subterm in ['Ck_A', 'Ck_B', 'Ck_C', 'Ck_D', 'Ck_E']
    for the intensification phase.
    """
    df = pd.read_csv(SUBTERMS_CSV)
    df = df[(df["ep"] == 1) & (df["phase"] == "intensification")].copy()
    df["subterm"] = df["subterm"].map(clec.CK_SUBTERM_LABELS)
    df = df[df["subterm"].isin(SUBTERM_ORDER)]
    return df


# ============================================================================
# FIGURE CONSTRUCTION
# ============================================================================

def _pressure_pa_to_hpa(p_pa: float) -> float:
    """Convert pressure from Pa to hPa; values <= 2000 assumed already in hPa."""
    return p_pa / 100.0 if p_pa > 2000 else p_pa


def make_figure(level_data: dict[float, list[float]],
                subterm_df: pd.DataFrame) -> None:
    """Build and save Figure S3."""

    # ── Convert pressure keys to hPa and sort ─────────────────────────────
    level_hpa: dict[float, list[float]] = {
        _pressure_pa_to_hpa(p): vals for p, vals in level_data.items()
    }

    # Filter to standard display levels and sort ascending (→ top of atm first)
    avail_hpa = set(level_hpa.keys())
    display_levels = sorted(
        [p for p in PRESSURE_LEVELS_DISPLAY if any(abs(p - q) < 15 for q in avail_hpa)],
        reverse=False  # 100 first → will invert axis
    )

    # For each display level, find the closest key in data
    def best_key(target: float) -> float | None:
        candidates = [p for p in avail_hpa if abs(p - target) < 15]
        return min(candidates, key=lambda x: abs(x - target)) if candidates else None

    # Build ordered lists for boxplot
    bp_data   = []  # list of arrays
    bp_labels = []  # pressure labels (hPa)
    for p in display_levels:
        k = best_key(p)
        if k is not None and len(level_hpa[k]) >= 3:
            bp_data.append(level_hpa[k])
            bp_labels.append(int(round(p)))

    n_levels = len(bp_data)

    # ── Plot setup ─────────────────────────────────────────────────────────
    plt.rcParams.update({
        "font.family":        "sans-serif",
        "font.sans-serif":    ["Arial", "DejaVu Sans"],
        "font.size":          FONT_SIZE_TICKS,
        "axes.labelsize":     FONT_SIZE_AXIS_LABEL,
        "xtick.labelsize":    FONT_SIZE_TICKS,
        "ytick.labelsize":    FONT_SIZE_TICKS,
        "legend.fontsize":    FONT_SIZE_LEGEND,
        "axes.linewidth":     LINEWIDTH,
        "xtick.major.width":  LINEWIDTH,
        "ytick.major.width":  LINEWIDTH,
    })

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE,
                             gridspec_kw={"width_ratios": [1.6, 1.0],
                                          "wspace": 0.20})
    ax_vert, ax_sub = axes

    # ── Panel (a): Vertical profile of total C_K ──────────────────────────
    positions = list(range(n_levels))
    bp = ax_vert.boxplot(
        bp_data,
        positions=positions,
        vert=False,
        widths=BOXPLOT_WIDTH,
        patch_artist=True,
        notch=False,
        flierprops=dict(marker=".", markersize=2, alpha=0.4, color="#888888"),
        medianprops=dict(color="#c0392b", linewidth=LINEWIDTH + 0.5),
        whiskerprops=dict(linewidth=LINEWIDTH),
        capprops=dict(linewidth=LINEWIDTH),
        boxprops=dict(linewidth=LINEWIDTH),
    )
    # Shade boxes: negative median → blue (K_Z→K_E); positive → orange
    for patch, data in zip(bp["boxes"], bp_data):
        med = np.median(data)
        patch.set_facecolor("#AED6F1" if med < 0 else "#FAD7A0")
        patch.set_alpha(0.80)

    # y-axis: pressure labels
    ax_vert.set_yticks(positions)
    ax_vert.set_yticklabels([str(p) for p in bp_labels],
                             fontsize=FONT_SIZE_TICKS)
    # Invert so 1000 hPa is at the bottom
    ax_vert.invert_yaxis()

    # Zero line
    ax_vert.axvline(0, color="black", linewidth=LINEWIDTH, linestyle="--", alpha=0.7)

    ax_vert.set_xlabel(r"$C_K$ (W m$^{-2}$)", fontsize=FONT_SIZE_AXIS_LABEL)
    ax_vert.set_ylabel("Pressure (hPa)",        fontsize=FONT_SIZE_AXIS_LABEL)
    ax_vert.text(-0.10, 1.02, "(a)", transform=ax_vert.transAxes,
                 fontsize=FONT_SIZE_PANEL_LABEL, fontweight="bold",
                 va="bottom", ha="left")

    # Shaded negative region
    xlim = ax_vert.get_xlim()
    ax_vert.axvspan(xlim[0], 0, color="#D6EAF8", alpha=0.25, zorder=0)

    ax_vert.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax_vert.tick_params(axis="both", which="major", labelsize=FONT_SIZE_TICKS)
    ax_vert.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.6)

    # ── Panel (b): Integrated subterms ────────────────────────────────────
    present = [s for s in SUBTERM_ORDER if s in subterm_df["subterm"].values]
    n_sub = len(present)
    sub_positions = list(range(n_sub))

    sub_bp_data = []
    for s in present:
        vals = subterm_df.loc[subterm_df["subterm"] == s, "value"].dropna().values
        sub_bp_data.append(vals)

    bp2 = ax_sub.boxplot(
        sub_bp_data,
        positions=sub_positions,
        vert=False,
        widths=BOXPLOT_WIDTH,
        patch_artist=True,
        notch=False,
        flierprops=dict(marker=".", markersize=2, alpha=0.4, color="#888888"),
        medianprops=dict(color="#c0392b", linewidth=LINEWIDTH + 0.5),
        whiskerprops=dict(linewidth=LINEWIDTH),
        capprops=dict(linewidth=LINEWIDTH),
        boxprops=dict(linewidth=LINEWIDTH),
    )
    for i, (patch, data) in enumerate(zip(bp2["boxes"], sub_bp_data)):
        patch.set_facecolor(SUBTERM_COLORS[i % len(SUBTERM_COLORS)])
        patch.set_alpha(0.75)

    # y-axis: subterm labels
    ax_sub.set_yticks(sub_positions)
    ax_sub.set_yticklabels(
        [SUBTERM_LABELS.get(s, s) for s in present],
        fontsize=FONT_SIZE_TICKS
    )
    ax_sub.invert_yaxis()

    ax_sub.axvline(0, color="black", linewidth=LINEWIDTH, linestyle="--", alpha=0.7)
    xlim2 = ax_sub.get_xlim()
    ax_sub.axvspan(xlim2[0], 0, color="#D6EAF8", alpha=0.25, zorder=0)

    ax_sub.set_xlabel(r"Integrated $C_K$ subterm (W m$^{-2}$)",
                      fontsize=FONT_SIZE_AXIS_LABEL)
    ax_sub.text(-0.12, 1.02, "(b)", transform=ax_sub.transAxes,
                fontsize=FONT_SIZE_PANEL_LABEL, fontweight="bold",
                va="bottom", ha="left")

    ax_sub.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax_sub.tick_params(axis="both", which="major", labelsize=FONT_SIZE_TICKS)
    ax_sub.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.6)

    # ── Save ──────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PNG, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    assert_corrected_clustering()
    print("\n=== Figure S3: C_K Vertical Profiles & Subterms (EP1, Intensification) ===\n")

    # 1. EP1 cases
    if not EP1_CASES_CSV.exists():
        print(f"ERROR: EP1 cases file not found:\n  {EP1_CASES_CSV}")
        sys.exit(1)
    ep1_cases = pd.read_csv(EP1_CASES_CSV)
    print(f"  EP1 cyclones loaded: {len(ep1_cases)}")

    # 2. Corrected vertical Ck profiles — EP1 only
    print("  Loading corrected Ck vertical profiles (EP1) …")
    level_data = load_vertical_ck_ep1(ep1_cases)
    n_levels_found = len(level_data)
    n_cyclones_found = max((len(v) for v in level_data.values()), default=0)
    print(f"  Pressure levels found: {n_levels_found}")
    print(f"  Max cyclones per level: {n_cyclones_found}")

    # 3. Integrated subterms — EP1 only
    if not SUBTERMS_CSV.exists():
        print(f"ERROR: Subterms CSV not found:\n  {SUBTERMS_CSV}")
        sys.exit(1)
    subterm_df = load_integrated_subterms()
    found_subterms = sorted(subterm_df["subterm"].unique().tolist())
    print(f"  Integrated subterms found (EP1): {found_subterms}")

    # 4. Build figure
    print(f"\n  Building figure …")
    make_figure(level_data, subterm_df)

    # 5. Report
    sz = OUTPUT_PNG.stat().st_size / 1024
    from PIL import Image
    with Image.open(OUTPUT_PNG) as img:
        w, h = img.size
    print(f"\n  ✅ Saved: {OUTPUT_PNG}")
    print(f"     Dimensions: {w} × {h} px  |  Size: {sz:.1f} KB")

    print("\n─── Data availability note ──────────────────────────────────────────")
    print("  Panel (a): corrected total C_K vertical profile — EP1 only.")
    print("  Panel (b): corrected integrated EP1 subterms from")
    print("  results/ck_subterms_corrected/subterms_long.csv.")
    print("─────────────────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
