"""
Reference diagram: what the canonical CPS regions are, with nothing plotted on
top of them.

A schematic, not a result. It carries no data — only the thresholds of
`cps_criteria.CANONICAL` and the vocabulary used to read them — so it is the
figure to look at first, and the one to check a threshold against.

It also makes visible something the tables state but no data figure shows
cleanly: the three class definitions OVERLAP, and the grey region is where they
do. There the timestep precedence (tropical > subtropical > extratropical)
decides the label.

Inputs: none (thresholds only)

Output:
    figures/cps_analysis/fig0_cps_reference.png

Run:
    python scripts/cps_analysis/make_reference_diagram.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    CANONICAL_SOURCE,
    PHASE_COLORS,
    describe_interval,
)
from scripts.cps_analysis.cps_plotting import (
    shade_class_regions,
    region_legend_handles,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis"
OUT = FIG_DIR / "fig0_cps_reference.png"

XLIM = (-400, 250)
YLIM_B = (-80, 130)
YLIM_VTU = (-400, 200)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    b_lo, b_hi = CANONICAL["subtropical"]["B"]
    vtl_lo = CANONICAL["subtropical"]["VTL"][0]
    vtu_sc = CANONICAL["subtropical"]["VTU"][1]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.8))
    fig.subplots_adjust(left=0.065, right=0.985, top=0.745, bottom=0.315,
                        wspace=0.2)

    # ---------------- B vs -VTL ----------------
    ax = axes[0]
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM_B)
    shade_class_regions(ax, "VTL", "B")

    ax.axhline(10, color=PHASE_COLORS["EC"], lw=1.8, ls="--", zorder=3)
    ax.axhline(b_hi, color=PHASE_COLORS["SC"], lw=1.6, ls=":", zorder=3)
    ax.axhline(b_lo, color=PHASE_COLORS["SC"], lw=1.6, ls=":", zorder=3)
    ax.axvline(0, color="0.2", lw=1.1, zorder=3)
    ax.axvline(vtl_lo, color=PHASE_COLORS["SC"], lw=1.4, ls="-.", zorder=3)

    for val, txt, col, va in [(10, r"$B=10$", PHASE_COLORS["EC"], "top"),
                              (b_hi, f"$B={b_hi:g}$", PHASE_COLORS["SC"], "bottom"),
                              (b_lo, f"$B={b_lo:g}$", PHASE_COLORS["SC"], "bottom")]:
        ax.annotate(txt, (XLIM[1] - 6, val), fontsize=9.5, color=col,
                    ha="right", va=va, zorder=7, fontweight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))
    ax.annotate(rf"$-V_T^{{\,L}}={vtl_lo:g}$", (vtl_lo - 5, YLIM_B[0] + 6),
                fontsize=9.5, color=PHASE_COLORS["SC"], ha="right", va="bottom",
                rotation=90, zorder=7, fontweight="bold",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))

    for txt, xy, va in [("Tilted  /  frontal", (0.975, 0.955), "top"),
                        ("Symmetrical  /  non-frontal", (0.975, 0.035), "bottom")]:
        ax.text(*xy, txt, transform=ax.transAxes, fontsize=11.5, style="italic",
                color="0.3", ha="right", va=va, zorder=6,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=2))
    ax.text(0.025, 0.79, "Cold core", transform=ax.transAxes, fontsize=11.5,
            style="italic", color="0.3", ha="left", va="center", zorder=6,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=2))
    ax.text(0.72, 0.20, "Warm core", transform=ax.transAxes, fontsize=11.5,
            style="italic", color="0.3", ha="left", va="center", zorder=6,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=2))

    ax.set_xlabel(r"$-V_T^{\,L}$   [900–600 hPa thermal wind]", fontsize=12.5)
    ax.set_ylabel(r"$B$   [900–600 hPa thickness asymmetry, m]", fontsize=12.5)
    ax.set_title("(a)   thermal asymmetry vs lower thermal wind",
                 fontsize=12, pad=10)

    # ---------------- -VTU vs -VTL ----------------
    ax = axes[1]
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM_VTU)
    shade_class_regions(ax, "VTL", "VTU")

    ax.axhline(0, color=PHASE_COLORS["TC"], lw=1.8, ls="--", zorder=3)
    ax.axhline(vtu_sc, color=PHASE_COLORS["SC"], lw=1.6, ls=":", zorder=3)
    ax.axvline(0, color="0.2", lw=1.1, zorder=3)

    ax.annotate(r"$-V_T^{\,U}=0$", (XLIM[0] + 8, 6), fontsize=9.5,
                color=PHASE_COLORS["TC"], va="bottom", zorder=7, fontweight="bold",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))
    ax.annotate(rf"$-V_T^{{\,U}}={vtu_sc:g}$", (XLIM[0] + 8, vtu_sc - 14),
                fontsize=9.5, color=PHASE_COLORS["SC"], va="top", zorder=7,
                fontweight="bold",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))

    for txt, xy, ha, va in [("Cold core\nthroughout", (0.025, 0.04), "left", "bottom"),
                            ("Hybrid\nlow-level warm core", (0.975, 0.04), "right", "bottom"),
                            ("Warm core\nthroughout", (0.975, 0.955), "right", "top"),
                            ("Cold shallow", (0.025, 0.955), "left", "top")]:
        ax.text(*xy, txt, transform=ax.transAxes, fontsize=11, style="italic",
                color="0.3", ha=ha, va=va, zorder=6,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=2))

    ax.set_xlabel(r"$-V_T^{\,L}$   [900–600 hPa thermal wind]", fontsize=12.5)
    ax.set_ylabel(r"$-V_T^{\,U}$   [600–300 hPa thermal wind]", fontsize=12.5)
    ax.set_title("(b)   upper vs lower thermal wind", fontsize=12, pad=10)

    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(labelsize=10.5)

    # ---------------- legend and captions ----------------
    handles = region_legend_handles()
    handles += [
        plt.Line2D([], [], color=PHASE_COLORS["EC"], ls="--", lw=1.8,
                   label=r"$B=10$ m — frontal / non-frontal (Hart 2003)"),
        plt.Line2D([], [], color=PHASE_COLORS["SC"], ls=":", lw=1.8,
                   label=r"$B=\pm25$ m, $-V_T^{\,U}=-10$ — subtropical bounds"),
        plt.Line2D([], [], color=PHASE_COLORS["SC"], ls="-.", lw=1.6,
                   label=r"$-V_T^{\,L}=-50$ — subtropical bound"),
        plt.Line2D([], [], color=PHASE_COLORS["TC"], ls="--", lw=1.8,
                   label=r"$-V_T^{\,U}=0$ — tropical bound"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=10, bbox_to_anchor=(0.525, 0.008))

    rows = []
    for cls in ("extratropical", "subtropical", "tropical"):
        terms = ",  ".join(describe_interval(iv, p)
                           for p, iv in CANONICAL[cls].items())
        rows.append(f"{cls:<14s}  {terms}")

    fig.text(0.525, 0.975, "Cyclone Phase Space — canonical class regions",
             ha="center", va="top", fontsize=17, fontweight="bold")
    fig.text(0.525, 0.938,
             f"thresholds after {CANONICAL_SOURCE}",
             ha="center", va="top", fontsize=10.5, color="0.35")
    fig.text(0.525, 0.905, "\n".join(rows), ha="center", va="top",
             fontsize=9.5, color="0.25", family="monospace",
             linespacing=1.5)
    fig.text(0.525, 0.185,
             "Each panel is a two-dimensional slice of a three-dimensional "
             "classification; the shading is the projection of each class onto "
             "that slice,\nwith the third parameter left free. Grey marks "
             "where more than one class can claim a point — there the timestep "
             "precedence\n(tropical > subtropical > extratropical) decides. "
             "Blank corners belong to no cyclone type.",
             ha="center", va="top", fontsize=9.5, color="0.45", style="italic",
             linespacing=1.6)

    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Wrote {OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
