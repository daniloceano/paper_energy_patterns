"""
Step 7 (CANONICAL): individual CPS diagrams, one sampled case per
(phase class x year x genesis region).

The case-study convention of the literature (Hart 2003; Evans and Hart 2003;
Reboita et al. 2024 and de Souza et al. 2026 on Akara): one cyclone, its path
through the phase space drawn as a line through its timesteps, each timestep
marked by the structure it holds at that moment, endpoints labelled A and Z.

Sampling
--------
One cyclone is drawn at random from every non-empty combination of

    phase class  x  year of genesis  x  genesis region

The draw is seeded PER COMBINATION, from a stable hash of (seed, class, year,
region), not from one sequential stream. A single shared stream would make each
pick depend on how many groups came before it, so `--classes ST` would draw
different cyclones than a full run - the seed would reproduce a whole run but
not any individual case. Combinations that do not occur are simply absent. The point is coverage, not completeness: a browsable
sample spanning every class, every year and every region in which that class
occurs, for eyeballing whether the classification behaves sensibly.

The `TC` class has two members, so both appear - each in its own figure, which
is also the reason the combined two-cyclone diagram was retired from step 6.

Output layout
-------------
    figures/cps_analysis/cases/<CLASS>/cps_<CLASS>_<YEAR>_<REGION>_<track_id>.png

The class is in the directory AND in the filename, so a figure remains
identifiable once detached from its folder.

Inputs:
    results/cps_analysis/phase_timesteps.csv        (step 2)
    results/cps_analysis/phase_classification.csv   (step 2)

Outputs:
    figures/cps_analysis/cases/<CLASS>/*.png
    results/cps_analysis/case_diagram_index.csv

Run:
    python scripts/cps_analysis/step7_case_diagrams.py
    python scripts/cps_analysis/step7_case_diagrams.py --classes TC SC ST
    python scripts/cps_analysis/step7_case_diagrams.py --seed 7

Author: Danilo Couto de Souza
Date: August 2026
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import shutil
import sys
import zlib
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from scripts.utils.ep_mapping import get_ep_label
from scripts.cps_analysis.cps_plotting import (
    shade_class_regions,
    region_legend_handles,
)
from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    SINGLE_STATE_CLASSES,
    TRANSITIONS,
    CHARACTERISTIC_CLASSES,
    UNDETERMINED,
    PHASE_COLORS,
    UNCLASSIFIED,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis" / "cases"
TS_FILE = RESULTS_DIR / "phase_timesteps.csv"
CLASS_FILE = RESULTS_DIR / "phase_classification.csv"
OUT_INDEX = RESULTS_DIR / "case_diagram_index.csv"

# Per-timestep structure, in the vocabulary the CPS diagrams use.
MARKER_STYLE = {
    "extratropical": ("cold core / tilted", PHASE_COLORS["EC"]),
    "subtropical": ("hybrid (low-level warm core)", PHASE_COLORS["SC"]),
    "tropical": ("symmetric warm core", PHASE_COLORS["TC"]),
    UNCLASSIFIED: ("unclassified", "0.72"),
}
DRAW_ORDER = ["extratropical", UNCLASSIFIED, "subtropical", "tropical"]

CLASS_DESCRIPTIONS = {**SINGLE_STATE_CLASSES, **TRANSITIONS,
                      **CHARACTERISTIC_CLASSES,
                      UNDETERMINED: "no dominant structure"}


def zoom(values, keep):
    """Data range with padding, always keeping the given thresholds in view."""
    lo, hi = float(np.nanmin(values)), float(np.nanmax(values))
    for k in keep:
        lo, hi = min(lo, k), max(hi, k)
    pad = max((hi - lo) * 0.15, 12.0)
    return lo - pad, hi + pad


def _draw_one(task):
    """Worker: (group, meta, path) -> draws one figure. Top-level so it pickles."""
    g, meta, path = task
    draw_case(g, meta, path)
    return path


def draw_case(g: pd.DataFrame, meta: pd.Series, path: Path):
    """One cyclone, two CPS panels, markers coloured by per-timestep structure."""
    g = g.sort_values("datetime")
    b_lo, b_hi = CANONICAL["subtropical"]["B"]
    vtl_lo = CANONICAL["subtropical"]["VTL"][0]
    vtu_sc = CANONICAL["subtropical"]["VTU"][1]

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.2))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.775, bottom=0.205,
                        wspace=0.2)

    for ax, (ycol, ylab, keep) in zip(
            axes,
            [("B", r"$B$   [m]", [b_lo, b_hi, 10.0]),
             ("VTU", r"$-V_T^{\,U}$   [600–300 hPa]", [0.0, vtu_sc])]):
        ax.set_xlim(*zoom(g["VTL"], [0.0, vtl_lo]))
        ax.set_ylim(*zoom(g[ycol], keep))
        shade_class_regions(ax, "VTL", ycol)

        ax.plot(g["VTL"], g[ycol], "-", color="0.4", lw=1.1, alpha=0.85, zorder=2)
        for cls in DRAW_ORDER:
            sub = g[g["cps_class_filled"] == cls]
            if sub.empty:
                continue
            ax.scatter(sub["VTL"], sub[ycol], s=62, c=MARKER_STYLE[cls][1],
                       edgecolors="k", linewidths=0.45, zorder=4)

        step = max(1, len(g) // 8)
        for i in range(0, len(g), step):
            r = g.iloc[i]
            ax.annotate(f"{r['datetime']:%d/%HZ}", (r["VTL"], r[ycol]),
                        textcoords="offset points", xytext=(7, 6), fontsize=7,
                        color="0.4", zorder=5)
        for pos, lab in ((0, "A"), (len(g) - 1, "Z")):
            r = g.iloc[pos]
            ax.annotate(lab, (r["VTL"], r[ycol]), textcoords="offset points",
                        xytext=(-5, -15), fontsize=13, fontweight="bold",
                        color="k", zorder=6)

        ax.axvline(0, color="0.2", lw=0.9, zorder=3)
        ax.set_xlabel(r"$-V_T^{\,L}$   [900–600 hPa]", fontsize=12)
        ax.set_ylabel(ylab, fontsize=13)
        ax.spines[["top", "right"]].set_visible(False)

    ax = axes[0]
    ax.axhline(10, color=PHASE_COLORS["EC"], lw=1.4, ls="--", zorder=3)
    ax.axhline(b_hi, color=PHASE_COLORS["SC"], lw=1.2, ls=":", zorder=3)
    ax.axhline(b_lo, color=PHASE_COLORS["SC"], lw=1.2, ls=":", zorder=3)
    ax.axvline(vtl_lo, color=PHASE_COLORS["SC"], lw=1.1, ls="-.", zorder=3)
    for txt, xy, va in [("Tilted", (0.975, 0.95), "top"),
                        ("Symmetrical", (0.975, 0.04), "bottom")]:
        ax.text(*xy, txt, transform=ax.transAxes, fontsize=10.5, style="italic",
                color="0.35", ha="right", va=va, zorder=7,
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.6))

    ax = axes[1]
    ax.axhline(0, color=PHASE_COLORS["TC"], lw=1.4, ls="--", zorder=3)
    ax.axhline(vtu_sc, color=PHASE_COLORS["SC"], lw=1.2, ls=":", zorder=3)
    for txt, xy, ha, va in [("Cold core", (0.025, 0.04), "left", "bottom"),
                            ("Hybrid", (0.975, 0.04), "right", "bottom"),
                            ("Warm core", (0.975, 0.95), "right", "top")]:
        ax.text(*xy, txt, transform=ax.transAxes, fontsize=10.5, style="italic",
                color="0.35", ha=ha, va=va, zorder=7,
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.6))

    handles = [plt.Line2D([], [], ls="", marker="o", ms=8, color=c,
                          markeredgecolor="k", markeredgewidth=0.45, label=lab)
               for lab, c in MARKER_STYLE.values()]
    # Keep the ambiguous patch: the panels show grey shading, and the marker
    # legend already has a grey dot meaning "unclassified" — two different greys
    # need two entries.
    handles += region_legend_handles()
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=9, bbox_to_anchor=(0.53, 0.005))

    cls = meta["phase_class"]
    ep = f"EP{int(meta['ep'])}" if pd.notna(meta["ep"]) else "no EP"
    seq = meta["state_sequence"] or "(no persistent state)"
    ante = ""
    if isinstance(meta.get("antecedent_characteristics"), str) and meta["antecedent_characteristics"]:
        ante = (f"  ·  preceded by {meta['antecedent_characteristics']} "
                f"characteristics for {meta['antecedent_hours']:.0f} h")

    fig.text(0.53, 0.975,
             f"{cls}  —  {CLASS_DESCRIPTIONS.get(cls, cls)}",
             ha="center", va="top", fontsize=15, fontweight="bold",
             color=PHASE_COLORS.get(cls, "0.2"))
    fig.text(0.53, 0.932,
             f"track {meta['track_id']}  ·  {meta['region']}  ·  {ep}  ·  "
             f"{g['datetime'].iloc[0]:%d %b %Y %HZ} – {g['datetime'].iloc[-1]:%d %b %Y %HZ}",
             ha="center", va="top", fontsize=11, color="0.3")
    fig.text(0.53, 0.897,
             f"genesis {meta['genesis_lat']:.1f}°, {meta['genesis_lon']:.1f}°  ·  "
             f"persistent states: {seq}{ante}",
             ha="center", va="top", fontsize=9.5, color="0.45", style="italic")
    fig.text(0.53, 0.865, "A = first timestep, Z = last  ·  labels are day/hour UTC",
             ha="center", va="top", fontsize=8.5, color="0.55")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, facecolor="white")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Individual CPS case diagrams")
    ap.add_argument("--classes", nargs="*", default=None,
                    help="restrict to these phase classes (default: all)")
    ap.add_argument("--jobs", "-j", type=int, default=1,
                    help="parallel workers over figures (default 1). Output is "
                         "independent of this value.")
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed for the per-combination draw")
    args = ap.parse_args()

    print("=" * 70)
    print("STEP 7 (CANONICAL): individual CPS case diagrams")
    print("=" * 70)

    for f in (TS_FILE, CLASS_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    cy = pd.read_csv(CLASS_FILE)
    if args.classes:
        cy = cy[cy["phase_class"].isin(args.classes)]
        if cy.empty:
            print(f"No cyclones in classes {args.classes}.")
            return 1

    # One draw per (class, year, region), seeded from the combination itself so
    # a given case is reproducible whatever else is being drawn alongside it.
    def pick_one(d, key):
        token = f"{args.seed}|{key[0]}|{key[1]}|{key[2]}".encode()
        rng = np.random.default_rng(zlib.crc32(token))
        return d.iloc[int(rng.integers(len(d)))]

    grouped = (cy.dropna(subset=["region"])
               .sort_values("track_id")
               .groupby(["phase_class", "year", "region"], sort=True))
    picks = pd.DataFrame([pick_one(d, k) for k, d in grouped]).reset_index(drop=True)

    print(f"\n{len(picks):,} (class x year x region) combinations to draw")
    print(picks["phase_class"].value_counts().to_string())

    # Clear the directories being redrawn. Without this, figures from an earlier
    # draw survive alongside the current one and the folder silently disagrees
    # with the index.
    for cls in picks["phase_class"].unique():
        d = FIG_DIR / cls
        if d.exists():
            shutil.rmtree(d)

    ts = pd.read_csv(TS_FILE, parse_dates=["datetime"],
                     usecols=["track_id", "datetime", "B", "VTL", "VTU", "cps_class"])
    ts = ts.dropna(subset=["B", "VTL", "VTU"])
    ts["cps_class_filled"] = ts["cps_class"].fillna(UNCLASSIFIED)
    by_track = dict(tuple(ts.groupby("track_id")))

    # Each figure is independent, so the drawing is parallel over cases. The
    # index is rebuilt from `tasks` order afterwards, so --jobs does not change
    # the output.
    tasks = []
    for _, meta in picks.iterrows():
        g = by_track.get(meta["track_id"])
        if g is None or len(g) < 3:
            continue
        cls = meta["phase_class"]
        name = (f"cps_{cls}_{int(meta['year'])}_{meta['region']}_"
                f"{meta['track_id']}.png")
        tasks.append((g, meta, FIG_DIR / cls / name))

    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            list(tqdm(ex.map(_draw_one, tasks, chunksize=4),
                      total=len(tasks), unit="fig"))
    else:
        for t in tqdm(tasks, unit="fig"):
            _draw_one(t)

    rows = [{"phase_class": meta["phase_class"], "year": int(meta["year"]),
             "region": meta["region"], "track_id": meta["track_id"],
             "ep": meta["ep"], "state_sequence": meta["state_sequence"],
             "n_timesteps": len(g),
             "figure": str(path.relative_to(PROJECT_ROOT))}
            for g, meta, path in tasks]

    index = pd.DataFrame(rows)

    # A partial run (--classes) must not erase the record of the classes it did
    # not redraw: keep their rows, replace only the ones just drawn.
    if args.classes and OUT_INDEX.exists():
        previous = pd.read_csv(OUT_INDEX)
        kept = previous[~previous["phase_class"].isin(index["phase_class"].unique())]
        index = pd.concat([kept, index], ignore_index=True)

    index = index.sort_values(["phase_class", "year", "region"])
    index.to_csv(OUT_INDEX, index=False)

    print(f"\nWrote {len(index):,} figures under "
          f"{FIG_DIR.relative_to(PROJECT_ROOT)}/<CLASS>/")
    for cls, n in index["phase_class"].value_counts().sort_index().items():
        print(f"  {cls:<14s} {n:4,d}")
    print(f"\nWrote {OUT_INDEX.relative_to(PROJECT_ROOT)}")
    print("\nStep 7 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
