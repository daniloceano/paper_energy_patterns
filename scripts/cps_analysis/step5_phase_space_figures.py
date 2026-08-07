"""
Step 5 (CANONICAL): cyclone phase-space diagrams, EPALL and EP1/EP2/EP3.

A 2 x 4 version of the classic two-panel CPS diagram (Hart 2003; e.g. Cavicchia
et al. 2019, their Fig. 4, "Cyclone phase-space diagrams for all cyclones
detected [...] Each dot corresponds to a single cyclone instance detected in a
6-hourly reanalysis time step"):

    row 1   B        vs  -V_T^L      tilted / symmetrical
    row 2   -V_T^U   vs  -V_T^L      cold core / hybrid / warm core

    col 1   EPALL     all cyclones in the subset
    col 2   EP1       high conversions, exports
    col 3   EP2       moderate conversions, imports
    col 4   EP3       weak / background energetics

Two figures are produced from the same layout:

    fig5   every classifiable timestep of every cyclone
    fig6   restricted to the SINGLE-STATE SUBTROPICAL cyclones, i.e. those whose
           only persistent state is SC (the class deliberately not called "pure";
           see cps_criteria.SINGLE_STATE_CLASSES)

Two departures from the reference figure, both deliberate:

  * Density, not raw dots. At ~189,000 classifiable timesteps a scatter
    saturates into a blob and hides exactly the structure the figure is for.
    Each panel is a hexbin of the FRACTION of that column's timesteps per bin,
    on a shared logarithmic colour scale, so the columns are directly
    comparable despite very unequal sample sizes. The single-state SC figure,
    which has far fewer points, additionally shows the individual timesteps.

  * The canonical thresholds are drawn on top, so the reader can see which part
    of the occupied space each class actually claims.

Inputs:
    results/cps_analysis/phase_timesteps.csv        (step 2)
    results/cps_analysis/phase_classification.csv   (step 2)

Outputs:
    figures/cps_analysis/fig5_phase_space_by_ep.png
    figures/cps_analysis/fig6_phase_space_by_ep_single_state_sc.png

Run:
    python scripts/cps_analysis/step5_phase_space_figures.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label
from scripts.cps_analysis.cps_criteria import CANONICAL, PHASE_COLORS
from scripts.cps_analysis.cps_plotting import (
    shade_class_regions,
    region_legend_handles,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis"
TS_FILE = RESULTS_DIR / "phase_timesteps.csv"
CLASS_FILE = RESULTS_DIR / "phase_classification.csv"

# Axis ranges, chosen to contain >99.5% of the sample while keeping the
# thresholds visible.
XLIM = (-700, 400)
YLIM_B = (-130, 170)
YLIM_VTU = (-700, 320)
CMAP = "magma_r"

# Short subtitles: the full EP_DESCRIPTIONS strings are too long to sit side by
# side over four columns without colliding.
SHORT_DESC = {
    1: "high conversions, exports",
    2: "moderate conversions, imports",
    3: "weak / background energetics",
}


def build_columns(df: pd.DataFrame) -> list:
    cols = [("EPALL", df, "0.35", "all cyclones in this subset")]
    for ep in ALL_EPS:
        cols.append((get_ep_label(ep), df[df["ep"] == ep], EP_COLORS[ep],
                     SHORT_DESC[ep]))
    return cols


def shared_norm(subsets: list, gridsize: int) -> LogNorm:
    """One colour scale for every panel, set by the densest column."""
    hi = 0.0
    for _, sub, _, _ in subsets:
        if sub.empty:
            continue
        for xcol, ycol, ylim in (("VTL", "B", YLIM_B), ("VTL", "VTU", YLIM_VTU)):
            h, _, _ = np.histogram2d(sub[xcol], sub[ycol], bins=gridsize,
                                     range=[XLIM, ylim])
            hi = max(hi, (h / len(sub)).max())
    return LogNorm(vmin=hi / 3e3, vmax=hi)


def panel(ax, x, y, norm, ylim, gridsize, show_points, ctx=None, plane=None):
    """Hexbin of the focus timesteps; `ctx` draws the rest as faint context."""
    ax.set_xlim(*XLIM)
    ax.set_ylim(*ylim)
    if plane:
        shade_class_regions(ax, *plane)
    if ctx is not None and len(ctx[0]):
        ax.scatter(ctx[0], ctx[1], s=2.2, c="0.78", alpha=0.30, linewidths=0,
                   zorder=1)
    n = len(x)
    if n == 0:
        return None
    hb = ax.hexbin(x, y, C=np.full(n, 1.0 / n), reduce_C_function=np.sum,
                   gridsize=gridsize, cmap=CMAP, norm=norm,
                   extent=(*XLIM, *ylim), linewidths=0.0, mincnt=1, zorder=2)
    if show_points:
        ax.scatter(x, y, s=1.4, c="0.15", alpha=0.16, linewidths=0, zorder=3)
    return hb


def make_figure(subsets, title, subtitle, out_path, gridsize, show_points,
                contexts=None):
    fig, axes = plt.subplots(2, 4, figsize=(19, 9.6),
                             sharex=True, sharey="row",
                             gridspec_kw=dict(hspace=0.16, wspace=0.07,
                                              left=0.052, right=0.90,
                                              top=0.845,
                                              bottom=0.205 if contexts else 0.185))
    norm = shared_norm(subsets, gridsize)

    b_lo, b_hi = CANONICAL["subtropical"]["B"]
    vtl_lo = CANONICAL["subtropical"]["VTL"][0]
    vtu_sc = CANONICAL["subtropical"]["VTU"][1]

    letters = "abcdefgh"
    hb_last = None

    for col, (label, sub, colour, desc) in enumerate(subsets):
        # ---------------- row 1 : B vs -VTL ----------------
        ax = axes[0, col]
        ctx = contexts[col] if contexts else None
        hb_last = panel(ax, sub["VTL"], sub["B"], norm, YLIM_B, gridsize,
                        show_points,
                        (ctx["VTL"], ctx["B"]) if ctx is not None else None,
                        plane=("VTL", "B")) or hb_last

        ax.axhline(10, color=PHASE_COLORS["EC"], lw=1.5, ls="--", zorder=4)
        ax.axhline(b_hi, color=PHASE_COLORS["SC"], lw=1.4, ls=":", zorder=4)
        ax.axhline(b_lo, color=PHASE_COLORS["SC"], lw=1.4, ls=":", zorder=4)
        ax.axvline(0, color="0.25", lw=1.0, zorder=4)
        ax.axvline(vtl_lo, color=PHASE_COLORS["SC"], lw=1.2, ls="-.", zorder=4)

        if col == 0:
            ax.set_ylabel(r"$B$   [m]", fontsize=13)
            for txt, xy, va in [("Tilted", (0.03, 0.90), "top"),
                                ("Symmetrical", (0.03, 0.06), "bottom")]:
                ax.text(*xy, txt, transform=ax.transAxes, fontsize=11.5,
                        style="italic", color="0.30", va=va, zorder=6,
                        bbox=dict(fc="white", ec="none", alpha=0.72, pad=1.8))

        ax.text(0.5, 1.115, label, transform=ax.transAxes, ha="center",
                va="bottom", fontsize=15, fontweight="bold", color=colour)
        ax.text(0.5, 1.072, desc, transform=ax.transAxes, ha="center",
                va="bottom", fontsize=9.5, color="0.45", style="italic")
        n_txt = f"n = {len(sub):,} timesteps"
        if contexts:
            n_txt += f"  (+{len(contexts[col]):,} other)"
        ax.text(0.5, 1.020, n_txt, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=9, color="0.35")
        ax.text(0.022, 0.955, f"({letters[col]})", transform=ax.transAxes,
                fontsize=11, fontweight="bold", va="top")

        # ---------------- row 2 : -VTU vs -VTL ----------------
        ax = axes[1, col]
        panel(ax, sub["VTL"], sub["VTU"], norm, YLIM_VTU, gridsize, show_points,
              (ctx["VTL"], ctx["VTU"]) if ctx is not None else None,
              plane=("VTL", "VTU"))

        ax.axhline(0, color=PHASE_COLORS["TC"], lw=1.5, ls="--", zorder=4)
        ax.axhline(vtu_sc, color=PHASE_COLORS["SC"], lw=1.4, ls=":", zorder=4)
        ax.axvline(0, color="0.25", lw=1.0, zorder=4)

        ax.set_xlabel(r"$-V_T^{\,L}$   [900–600 hPa]", fontsize=12)
        if col == 0:
            ax.set_ylabel(r"$-V_T^{\,U}$   [600–300 hPa]", fontsize=13)
            for txt, xy, ha, va in [("Cold core", (0.03, 0.05), "left", "bottom"),
                                    ("Hybrid", (0.97, 0.05), "right", "bottom"),
                                    ("Warm core", (0.97, 0.94), "right", "top")]:
                ax.text(*xy, txt, transform=ax.transAxes, fontsize=11.5,
                        style="italic", color="0.30", ha=ha, va=va, zorder=6,
                        bbox=dict(fc="white", ec="none", alpha=0.72, pad=1.8))
        ax.text(0.022, 0.955, f"({letters[col + 4]})", transform=ax.transAxes,
                fontsize=11, fontweight="bold", va="top")

    for ax in axes.ravel():
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=10)
        ax.set_facecolor("white")

    cb_bottom = 0.205 if contexts else 0.185
    cax = fig.add_axes([0.915, cb_bottom, 0.014, 0.845 - cb_bottom])
    cb = fig.colorbar(hb_last, cax=cax)
    cb.set_label("fraction of the column's timesteps per bin", fontsize=11)
    cb.ax.tick_params(labelsize=9)

    handles = region_legend_handles() + [
        plt.Line2D([], [], color=PHASE_COLORS["EC"], ls="--", lw=1.6,
                   label=r"$B=10$ m — frontal / non-frontal"),
        plt.Line2D([], [], color=PHASE_COLORS["SC"], ls=":", lw=1.6,
                   label=r"$B=\pm25$ m and $-V_T^{\,U}=-10$ — subtropical bounds"),
        plt.Line2D([], [], color=PHASE_COLORS["SC"], ls="-.", lw=1.4,
                   label=r"$-V_T^{\,L}=-50$ — subtropical bound"),
        plt.Line2D([], [], color=PHASE_COLORS["TC"], ls="--", lw=1.6,
                   label=r"$-V_T^{\,U}=0$ — tropical bound"),
    ]
    if contexts:
        handles.append(plt.Line2D([], [], ls="", marker="o", ms=6, color="0.78",
                                  label="the same cyclones' non-subtropical timesteps"))
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=9.5, bbox_to_anchor=(0.48, 0.005))

    fig.text(0.48, 0.975, title, ha="center", va="top", fontsize=17,
             fontweight="bold")
    fig.text(0.48, 0.945, subtitle, ha="center", va="top", fontsize=11,
             color="0.35")

    fig.savefig(out_path, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"  {out_path.relative_to(PROJECT_ROOT)}")


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("STEP 5 (CANONICAL): phase-space diagrams by Energy Pattern")
    print("=" * 70)

    for f in (TS_FILE, CLASS_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    ts = pd.read_csv(TS_FILE,
                     usecols=["track_id", "ep", "B", "VTL", "VTU", "cps_class"])
    ts = ts.dropna(subset=["B", "VTL", "VTU"])
    cy = pd.read_csv(CLASS_FILE)
    print(f"\nLoaded {len(ts):,} classifiable timesteps")

    # --- all cyclones ---
    subsets = build_columns(ts)
    for label, sub, _, _ in subsets:
        print(f"  {label:<6s} {len(sub):8,d} timesteps")
    make_figure(
        subsets,
        "Cyclone phase space by Energy Pattern",
        "every classifiable 3-hourly timestep, 1979–2020  ·  "
        "canonical thresholds after de Souza et al. (2026)",
        FIG_DIR / "fig5_phase_space_by_ep.png",
        gridsize=44, show_points=False)

    # --- single-state subtropical cyclones only ---
    # IMPORTANT: class SC means the only PERSISTENT state is subtropical. Such a
    # cyclone still spends a large part of its life in other structures - just
    # never for 36 consecutive hours. Plotting all of its timesteps therefore
    # reproduces something close to the whole-population cloud and hides the
    # very thing the figure is for. The hexbin here is restricted to the
    # SUBTROPICAL-CLASSIFIED timesteps; the rest are drawn as faint grey context.
    single_sc = set(cy.loc[cy["phase_class"] == "SC", "track_id"])
    sc_all = ts[ts["track_id"].isin(single_sc)]
    comp = sc_all["cps_class"].fillna("unclassified").value_counts(normalize=True) * 100
    print(f"\nSingle-state subtropical cyclones: {len(single_sc):,} "
          f"({len(sc_all):,} classifiable timesteps)")
    print("  their own per-timestep composition: "
          + ", ".join(f"{k} {v:.1f}%" for k, v in comp.items()))

    sc_focus = sc_all[sc_all["cps_class"] == "subtropical"]
    sc_ctx = sc_all[sc_all["cps_class"] != "subtropical"]
    subsets_sc = build_columns(sc_focus)
    contexts = [c[1] for c in build_columns(sc_ctx)]
    for label, sub, _, _ in subsets_sc:
        print(f"  {label:<6s} {len(sub):8,d} subtropical timesteps  "
              f"({sub['track_id'].nunique():,} cyclones)")
    make_figure(
        subsets_sc,
        "Cyclone phase space — SINGLE-STATE SUBTROPICAL cyclones",
        f"the {len(single_sc):,} cyclones whose only persistent state is subtropical  ·  "
        f"density shows only their subtropical-classified timesteps "
        f"({comp.get('subtropical', 0):.0f}% of their life); grey dots are the rest",
        FIG_DIR / "fig6_phase_space_by_ep_single_state_sc.png",
        gridsize=30, show_points=True, contexts=contexts)

    print("\nStep 5 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
