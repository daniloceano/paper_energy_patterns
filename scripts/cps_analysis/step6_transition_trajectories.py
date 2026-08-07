"""
Step 6 (CANONICAL): phase-space trajectories of the transitioning cyclones.

The figure convention of the case-study literature (Hart 2003; Evans and Hart
2003; Reboita et al. 2024 and de Souza et al. 2026 on Akara): a cyclone's path
through the phase space, drawn as a line through its timesteps, with each
timestep marked according to the structure it holds at that moment. Here the
same convention is applied to a whole class of cyclones at once, so the shape of
a transition can be read as a population rather than a single case.

Each marker is coloured by its per-timestep canonical class:
    cold core, tilted    extratropical    B > 10,      VTL < 0,  VTU < 0
    hybrid               subtropical      -25<B<25,    VTL > -50, VTU < -10
    symmetric warm core  tropical         B < 10,      VTL > 0,  VTU > 0
    unclassified         none of the three

Which classes are plotted
-------------------------
Only transitions that exist in the canonical classification:

    ST  subtropical transition   EC -> SC    298 cyclones
    SD  subtropical decay        SC -> EC     47 cyclones

`ET` in its strict sense (TC -> EC; Evans and Hart 2003) has **zero** members
here, and so does `TT`, because the catalogue contains no tropical cyclone to
transition from or to — see the SCIENTIFIC_NOTES. In the earlier draft scheme
`ET` was defined to also cover SC -> EC; that pathway is `SD` in the canonical
naming and is the right-hand column of this figure.

Inputs:
    results/cps_analysis/phase_timesteps.csv        (step 2)
    results/cps_analysis/phase_classification.csv   (step 2)

Single-cyclone diagrams - including the two tropical cyclones, each in its own
figure - are drawn by `step7_case_diagrams.py`.

Outputs:
    figures/cps_analysis/fig7_transition_trajectories.png
    results/cps_analysis/transition_trajectory_summary.csv

Run:
    python scripts/cps_analysis/step6_transition_trajectories.py

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

from scripts.cps_analysis.cps_plotting import (
    shade_class_regions,
    region_legend_handles,
)
from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    TRANSITIONS,
    PHASE_COLORS,
    UNCLASSIFIED,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis"
TS_FILE = RESULTS_DIR / "phase_timesteps.csv"
CLASS_FILE = RESULTS_DIR / "phase_classification.csv"
OUT_FIG = FIG_DIR / "fig7_transition_trajectories.png"
OUT_CSV = RESULTS_DIR / "transition_trajectory_summary.csv"

XLIM = (-700, 400)
YLIM_B = (-130, 170)
YLIM_VTU = (-700, 320)

# Per-timestep structure, in the vocabulary the CPS diagrams use.
MARKER_STYLE = {
    "extratropical": ("cold core / tilted", PHASE_COLORS["EC"], "o"),
    "subtropical": ("hybrid (low-level warm core)", PHASE_COLORS["SC"], "o"),
    "tropical": ("symmetric warm core", PHASE_COLORS["TC"], "o"),
    UNCLASSIFIED: ("unclassified", "0.72", "o"),
}
CLASS_DRAW_ORDER = ["extratropical", UNCLASSIFIED, "subtropical", "tropical"]


def draw_panel(ax, data, xcol, ycol, ylim, max_tracks=None, seed=0):
    """Trajectories plus per-timestep structure markers."""
    ax.set_xlim(*XLIM)
    ax.set_ylim(*ylim)
    shade_class_regions(ax, xcol, ycol)

    tracks = data["track_id"].unique()
    if max_tracks is not None and len(tracks) > max_tracks:
        rng = np.random.default_rng(seed)
        tracks = rng.choice(tracks, max_tracks, replace=False)
        data = data[data["track_id"].isin(tracks)]

    # Trajectory lines: thin and translucent, so the population shape shows
    # without any single cyclone dominating.
    lw = 0.55 if len(tracks) > 100 else 0.9
    alpha = 0.16 if len(tracks) > 100 else 0.32
    for _, g in data.groupby("track_id"):
        g = g.sort_values("datetime")
        ax.plot(g[xcol], g[ycol], "-", color="0.35", lw=lw, alpha=alpha, zorder=2)

    ms = 5 if len(tracks) > 100 else 9
    for cls in CLASS_DRAW_ORDER:
        sub = data[data["cps_class_filled"] == cls]
        if sub.empty:
            continue
        label, colour, marker = MARKER_STYLE[cls]
        ax.scatter(sub[xcol], sub[ycol], s=ms, c=colour, marker=marker,
                   linewidths=0, alpha=0.75, zorder=3)
    return len(tracks)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("STEP 6 (CANONICAL): transition trajectories in the phase space")
    print("=" * 70)

    for f in (TS_FILE, CLASS_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    ts = pd.read_csv(TS_FILE, parse_dates=["datetime"],
                     usecols=["track_id", "datetime", "ep", "B", "VTL", "VTU",
                              "cps_class"])
    cy = pd.read_csv(CLASS_FILE)
    ts = ts.dropna(subset=["B", "VTL", "VTU"])
    ts["cps_class_filled"] = ts["cps_class"].fillna(UNCLASSIFIED)

    present = [t for t in ("TT", "ET", "ST", "SD")
               if (cy["phase_class"] == t).sum() > 0]
    empty = [t for t in ("TT", "ET", "ST", "SD") if t not in present]
    print(f"\nTransition classes present: {', '.join(present) or 'none'}")
    if empty:
        print(f"Transition classes with zero members: {', '.join(empty)}")
        print("  (ET strict sense = TC -> EC; the catalogue holds no tropical")
        print("   cyclone to transition from, so the class is necessarily empty)")

    if not present:
        print("\nNothing to plot.")
        return 0

    b_lo, b_hi = CANONICAL["subtropical"]["B"]
    vtl_lo = CANONICAL["subtropical"]["VTL"][0]
    vtu_sc = CANONICAL["subtropical"]["VTU"][1]

    ncol = len(present)
    fig, axes = plt.subplots(2, ncol, figsize=(7.6 * ncol, 10.2),
                             sharex=True, sharey="row", squeeze=False,
                             gridspec_kw=dict(hspace=0.14, wspace=0.06,
                                              left=0.075, right=0.985,
                                              top=0.855, bottom=0.165))

    rows = []
    for col, code in enumerate(present):
        ids = set(cy.loc[cy["phase_class"] == code, "track_id"])
        data = ts[ts["track_id"].isin(ids)]

        ax = axes[0, col]
        n_drawn = draw_panel(ax, data, "VTL", "B", YLIM_B)
        ax.axhline(10, color=PHASE_COLORS["EC"], lw=1.5, ls="--", zorder=5)
        ax.axhline(b_hi, color=PHASE_COLORS["SC"], lw=1.3, ls=":", zorder=5)
        ax.axhline(b_lo, color=PHASE_COLORS["SC"], lw=1.3, ls=":", zorder=5)
        ax.axvline(0, color="0.2", lw=1.0, zorder=5)
        ax.axvline(vtl_lo, color=PHASE_COLORS["SC"], lw=1.2, ls="-.", zorder=5)

        ax.text(0.5, 1.10, f"{code}", transform=ax.transAxes, ha="center",
                va="bottom", fontsize=17, fontweight="bold",
                color=PHASE_COLORS[code])
        ax.text(0.5, 1.055, TRANSITIONS[code], transform=ax.transAxes,
                ha="center", va="bottom", fontsize=10.5, color="0.4",
                style="italic")
        ax.text(0.5, 1.012, f"{len(ids):,} cyclones · {len(data):,} timesteps",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=9.5,
                color="0.35")
        ax.text(0.978, 0.96, f"({'ac'[col] if ncol == 2 else 'abcd'[col]})",
                transform=ax.transAxes, fontsize=12, fontweight="bold",
                va="top", ha="right")

        if col == 0:
            ax.set_ylabel(r"$B$   [m]", fontsize=14)
            for txt, xy, va in [("Tilted", (0.025, 0.93), "top"),
                                ("Symmetrical", (0.025, 0.05), "bottom")]:
                ax.text(*xy, txt, transform=ax.transAxes, fontsize=12,
                        style="italic", color="0.30", va=va, zorder=7,
                        bbox=dict(fc="white", ec="none", alpha=0.75, pad=2))

        ax = axes[1, col]
        draw_panel(ax, data, "VTL", "VTU", YLIM_VTU)
        ax.axhline(0, color=PHASE_COLORS["TC"], lw=1.5, ls="--", zorder=5)
        ax.axhline(vtu_sc, color=PHASE_COLORS["SC"], lw=1.3, ls=":", zorder=5)
        ax.axvline(0, color="0.2", lw=1.0, zorder=5)
        ax.set_xlabel(r"$-V_T^{\,L}$   [900–600 hPa]", fontsize=13)
        ax.text(0.022, 0.96, f"({'bd'[col] if ncol == 2 else 'efgh'[col]})",
                transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")

        if col == 0:
            ax.set_ylabel(r"$-V_T^{\,U}$   [600–300 hPa]", fontsize=14)
            for txt, xy, ha, va in [("Cold core", (0.025, 0.04), "left", "bottom"),
                                    ("Hybrid", (0.975, 0.04), "right", "bottom"),
                                    ("Warm core", (0.975, 0.95), "right", "top")]:
                ax.text(*xy, txt, transform=ax.transAxes, fontsize=12,
                        style="italic", color="0.30", ha=ha, va=va, zorder=7,
                        bbox=dict(fc="white", ec="none", alpha=0.75, pad=2))

        comp = data["cps_class_filled"].value_counts(normalize=True) * 100
        rows.append({"transition": code, "n_cyclones": len(ids),
                     "n_timesteps": len(data),
                     **{f"pct_{k}": round(float(comp.get(k, 0.0)), 2)
                        for k in MARKER_STYLE}})

    for ax in axes.ravel():
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=11)

    handles = [
        plt.Line2D([], [], ls="", marker="o", ms=9, color=c,
                   label=f"{lab}")
        for cls, (lab, c, _) in MARKER_STYLE.items()
    # The ambiguous patch is kept: these panels DO show grey shading, and the
    # legend already carries a grey MARKER meaning "unclassified". Leaving the
    # patch out invites the reader to merge two different greys.
    ] + region_legend_handles() + [
        plt.Line2D([], [], color="0.35", lw=1.2, alpha=0.6, label="cyclone track"),
        plt.Line2D([], [], color=PHASE_COLORS["EC"], ls="--", lw=1.6,
                   label=r"$B=10$ m"),
        plt.Line2D([], [], color=PHASE_COLORS["SC"], ls=":", lw=1.6,
                   label=r"subtropical bounds"),
        plt.Line2D([], [], color=PHASE_COLORS["TC"], ls="--", lw=1.6,
                   label=r"$-V_T^{\,U}=0$"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=10, bbox_to_anchor=(0.53, 0.005))

    fig.text(0.53, 0.975, "Phase-space trajectories of the transitioning cyclones",
             ha="center", va="top", fontsize=18, fontweight="bold")
    fig.text(0.53, 0.943,
             "each marker is one 3-hourly timestep, coloured by the structure it holds  ·  "
             "lines connect a cyclone's successive timesteps",
             ha="center", va="top", fontsize=11.5, color="0.35")

    fig.savefig(OUT_FIG, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"\nWrote {OUT_FIG.relative_to(PROJECT_ROOT)}")

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print("\nPer-timestep structure composition of each transition class (%):")
    print(summary.to_string(index=False))

    print("\nStep 6 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
