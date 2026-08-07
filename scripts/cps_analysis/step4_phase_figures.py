"""
Step 4 (CANONICAL): figures for the phase classification.

Produces the figure set for the canonical analysis:

  fig1_phase_composition   phase-class composition of each Energy Pattern
  fig2_phase_space         CPS occupancy by phase class, canonical thresholds drawn
  fig3_transitions         where transitions happen: onset, latitude, season
  fig4_tropical_runs       every persistent tropical run, accepted vs rejected,
                           which is the visual form of the warm-seclusion filter

Inputs:
    results/cps_analysis/phase_timesteps.csv        (step 2)
    results/cps_analysis/phase_classification.csv   (step 2)
    results/cps_analysis/phase_states.csv           (step 2)

Outputs:
    figures/cps_analysis/fig1_phase_composition.png
    figures/cps_analysis/fig2_phase_space.png
    figures/cps_analysis/fig3_transitions.png
    figures/cps_analysis/fig4_tropical_runs.png

Run:
    python scripts/cps_analysis/step4_phase_figures.py

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

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label
from scripts.cps_analysis.cps_plotting import (
    shade_class_regions,
    region_legend_handles,
)
from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    SINGLE_STATE_CLASSES,
    TRANSITIONS,
    TRANSITION_PRECEDENCE,
    INDETERMINATE,
    CHARACTERISTIC_CLASSES,
    UNDETERMINED,
    SECLUSION,
    INDETERMINATE_WARM,
    PHASE_COLORS,
    MIN_PERSISTENCE_HOURS,
    TT_MAX_POLEWARD_LAT,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis"

CLASS_ORDER = (list(SINGLE_STATE_CLASSES) + TRANSITION_PRECEDENCE
               + list(CHARACTERISTIC_CLASSES) + [UNDETERMINED])
SEASON_OF_MONTH = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
                   6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
SEASONS = ["DJF", "MAM", "JJA", "SON"]

# Life-cycle phases in chronological order. A second baroclinic development is
# labelled "... 2" by the tracking; those are folded into the base phase.
PHASES = ["incipient", "intensification", "mature", "decay", "residual"]

# Edge/annotation colour for the latitude band in fig4, a darkened PHASE_COLORS["TC"].
ACCEPT_BAND_EDGE = "#7d2419"


def base_phase(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\s*2$", "", regex=True)


def fig_composition(cy: pd.DataFrame, path: Path):
    ep = cy[cy["ep"].notna()].copy()
    ep["ep"] = ep["ep"].astype(int)
    table = pd.crosstab(ep["ep"], ep["phase_class"]).reindex(
        index=ALL_EPS, columns=CLASS_ORDER, fill_value=0)
    pct = table.div(table.sum(axis=1), axis=0) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4))

    bottom = np.zeros(len(table))
    labels = [get_ep_label(e) for e in ALL_EPS]
    for cls in CLASS_ORDER:
        vals = pct[cls].values
        ax1.bar(labels, vals, bottom=bottom, label=cls,
                color=PHASE_COLORS.get(cls, "#999"), edgecolor="white", linewidth=0.8)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 4:
                ax1.text(i, b + v / 2, f"{v:.1f}", ha="center", va="center",
                         fontsize=9, color="white", fontweight="bold")
        bottom += vals
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("share of the EP (%)")
    ax1.set_title("Phase-class composition of each Energy Pattern")
    ax1.legend(frameon=False, fontsize=8, ncol=4, loc="upper center",
               bbox_to_anchor=(0.5, -0.07))

    # The transitions are the scientifically interesting part and invisible above.
    width = 0.35
    x = np.arange(len(ALL_EPS))
    for k, cls in enumerate(["ST", "SD"]):
        vals = pct[cls].values
        ax2.bar(x + (k - 0.5) * width, vals, width, label=f"{cls} — {TRANSITIONS[cls]}",
                color=PHASE_COLORS[cls], edgecolor="white")
        for xi, v, n in zip(x + (k - 0.5) * width, vals, table[cls].values):
            ax2.text(xi, v, f"{v:.1f}%\n(n={n})", ha="center", va="bottom", fontsize=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("share of the EP (%)")
    ax2.set_ylim(0, max(pct[["ST", "SD"]].values.max() * 1.45, 1))
    ax2.set_title("Phase transitions by Energy Pattern")
    ax2.legend(frameon=False, fontsize=8)

    for a in (ax1, ax2):
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Canonical CPS phase classification by Energy Pattern",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


def fig_phase_space(ts: pd.DataFrame, path: Path):
    d = ts.dropna(subset=["B", "VTL", "VTU", "cps_class"])
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    b_lo, b_hi = CANONICAL["subtropical"]["B"]
    vtu_sc = CANONICAL["subtropical"]["VTU"][1]

    ax = axes[0]
    ax.set_xlim(-700, 400)
    ax.set_ylim(-120, 170)
    shade_class_regions(ax, "VTL", "B")
    ax.hexbin(d["VTL"], d["B"], gridsize=60, bins="log", cmap="Greys", mincnt=1,
              extent=(-700, 400, -120, 170), zorder=2)
    ax.axhline(10, color=PHASE_COLORS["EC"], lw=1.6, ls="--", label="B = 10 (frontal)")
    ax.axhline(b_hi, color=PHASE_COLORS["SC"], lw=1.6, ls=":", label=f"B = {b_hi:g} (SC bound)")
    ax.axhline(b_lo, color=PHASE_COLORS["SC"], lw=1.6, ls=":")
    ax.axvline(0, color="k", lw=0.9)
    ax.axvline(-50, color=PHASE_COLORS["SC"], lw=1.2, ls="-.", label="VTL = -50 (SC bound)")
    ax.set_xlabel(r"$-V_T^L$  [900-600 hPa]")
    ax.set_ylabel("B  [m]")
    ax.set_title("B vs lower thermal wind")
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    ax = axes[1]
    ax.set_xlim(-700, 400)
    ax.set_ylim(-700, 300)
    shade_class_regions(ax, "VTL", "VTU")
    ax.hexbin(d["VTL"], d["VTU"], gridsize=60, bins="log", cmap="Greys", mincnt=1,
              extent=(-700, 400, -700, 300), zorder=2)
    ax.axhline(0, color=PHASE_COLORS["TC"], lw=1.6, ls="--", label="VTU = 0 (TC bound)")
    ax.axhline(vtu_sc, color=PHASE_COLORS["SC"], lw=1.6, ls=":",
               label=f"VTU = {vtu_sc:g} (SC bound)")
    ax.axvline(0, color="k", lw=0.9)
    ax.set_xlabel(r"$-V_T^L$  [900-600 hPa]")
    ax.set_ylabel(r"$-V_T^U$  [600-300 hPa]")
    ax.set_title("Upper vs lower thermal wind")
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
    n = len(d)
    fig.legend(handles=region_legend_handles(), loc="lower center", ncol=4,
               frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(f"CPS occupancy, canonical thresholds  (n = {n:,} classifiable timesteps)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


def fig_transitions(cy: pd.DataFrame, states: pd.DataFrame, ts: pd.DataFrame,
                    path: Path):
    """Where in the LIFE CYCLE subtropical structure appears and lives.

    Timing is expressed in life-cycle phase rather than in hours from genesis:
    the phases are the project's own vorticity-based segmentation, independent
    of the CPS, and they normalise for the very unequal cyclone lifetimes
    (median 42 h for the indeterminate class against 186 h for ST).
    """
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.4))
    sc = states[states["state"] == "SC"].sort_values(["track_id", "start"])
    width = 0.26
    xs = np.arange(len(PHASES))

    # (a) life-cycle phase in which the subtropical state BEGINS
    ax = axes[0, 0]
    first = sc.groupby("track_id").first()
    for k, e in enumerate(ALL_EPS):
        v = base_phase(first.loc[first["ep"] == e, "phase_at_onset"]).dropna()
        v = v[v.isin(PHASES)]
        if len(v) < 5:
            continue
        p = v.value_counts(normalize=True).reindex(PHASES, fill_value=0) * 100
        ax.bar(xs + (k - 1) * width, p.values, width, color=EP_COLORS[e],
               label=f"{get_ep_label(e)} (n={len(v)})", edgecolor="white")
    ax.set_xticks(xs)
    ax.set_xticklabels([p[:6] for p in PHASES], rotation=15)
    ax.set_ylabel("% of the EP's subtropical states")
    ax.set_title("(a)  Life-cycle phase in which\nsubtropical structure first appears",
                 fontsize=11)
    ax.legend(frameon=False, fontsize=8.5)

    # (b) where the subtropical timesteps actually sit in the life cycle
    ax = axes[0, 1]
    sub_ts = ts[ts["cps_class"] == "subtropical"].copy()
    sub_ts["ph"] = base_phase(sub_ts["period"])
    base = ts.assign(ph=base_phase(ts["period"]))["ph"]
    for k, e in enumerate(ALL_EPS):
        v = sub_ts.loc[sub_ts["ep"] == e, "ph"]
        v = v[v.isin(PHASES)]
        if v.empty:
            continue
        p = v.value_counts(normalize=True).reindex(PHASES, fill_value=0) * 100
        ax.bar(xs + (k - 1) * width, p.values, width, color=EP_COLORS[e],
               label=get_ep_label(e), edgecolor="white")
    ref = base[base.isin(PHASES)].value_counts(normalize=True).reindex(PHASES, fill_value=0) * 100
    ax.plot(xs, ref.values, "k--o", lw=1.4, ms=5, label="all timesteps")
    ax.set_xticks(xs)
    ax.set_xticklabels([p[:6] for p in PHASES], rotation=15)
    ax.set_ylabel("% of the EP's subtropical timesteps")
    ax.set_title("(b)  Where subtropical structure lives\nin the life cycle", fontsize=11)
    ax.legend(frameon=False, fontsize=8.5)

    # (c) duration of the subtropical state
    ax = axes[1, 0]
    data, labels, colors = [], [], []
    for e in ALL_EPS:
        v = sc.loc[sc["ep"] == e, "duration_h"].dropna()
        if len(v) >= 5:
            data.append(v.values)
            labels.append(get_ep_label(e))
            colors.append(EP_COLORS[e])
    if data:
        bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.55)
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)
        for m in bp["medians"]:
            m.set_color("black")
        ax.set_xticklabels(labels)
    ax.axhline(MIN_PERSISTENCE_HOURS, color="k", ls="--", lw=1.2)
    ax.set_ylabel("duration [h]")
    ax.set_title("(c)  How long the subtropical state lasts", fontsize=11)

    # (d) season of genesis by phase class
    ax = axes[1, 1]
    cy = cy.copy()
    cy["season"] = cy["genesis_month"].map(SEASON_OF_MONTH)
    xs2 = np.arange(len(SEASONS))
    for k, cls in enumerate(["EC", "SC", "ST"]):
        s_ = cy[cy["phase_class"] == cls]
        if s_.empty:
            continue
        p = s_["season"].value_counts(normalize=True).reindex(SEASONS, fill_value=0) * 100
        ax.bar(xs2 + (k - 1) * width, p.values, width, color=PHASE_COLORS[cls],
               label=f"{cls} (n={len(s_)})", edgecolor="white")
    ax.set_xticks(xs2)
    ax.set_xticklabels(SEASONS)
    ax.set_ylabel("% of the class")
    ax.set_title("(d)  Season of genesis", fontsize=11)
    ax.legend(frameon=False, fontsize=8.5)

    for a in axes.ravel():
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Subtropical structure: where it appears in the life cycle, "
                 "how long it lasts, and when in the year",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


def fig_tropical_runs(states: pd.DataFrame, path: Path):
    """Every persistent tropical run, and why each was accepted or rejected."""
    trop = states[states["tt_verdict"].notna()].copy()
    if trop.empty:
        return False
    trop["lat_median"] = pd.to_numeric(trop["lat_median"], errors="coerce")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.4))

    style = {"TC": ("accepted as tropical", PHASE_COLORS["TC"], "o"),
             SECLUSION: ("rejected: warm seclusion", PHASE_COLORS[SECLUSION], "X"),
             INDETERMINATE_WARM: ("rejected: indeterminate", PHASE_COLORS[INDETERMINATE_WARM], "s")}

    ax = ax1
    for verdict, (lab, col, mk) in style.items():
        s = trop[trop["tt_verdict"] == verdict]
        if s.empty:
            continue
        ax.scatter(s["onset_h_from_genesis"], s["lat_median"], s=110, c=col,
                   marker=mk, edgecolors="k", linewidths=0.6, label=f"{lab} (n={len(s)})",
                   zorder=3)
    # The band is the region where a persistent warm core is ACCEPTED as
    # tropical, so it takes the tropical colour. It used to take the subtropical
    # one, which said the opposite of what it means.
    ax.axhspan(TT_MAX_POLEWARD_LAT, 0, color=PHASE_COLORS["TC"], alpha=0.12, zorder=0)
    ax.axhline(TT_MAX_POLEWARD_LAT, color=ACCEPT_BAND_EDGE, lw=1.2, ls="--", zorder=1)
    ax.text(0.98, TT_MAX_POLEWARD_LAT + 1.5,
            f"equatorward of {-TT_MAX_POLEWARD_LAT:.0f}°S — accepted",
            transform=ax.get_yaxis_transform(), ha="right", va="bottom", fontsize=8,
            color=ACCEPT_BAND_EDGE)
    ax.set_xlabel("hours from genesis to the tropical run")
    ax.set_ylabel("median latitude during the run [deg]")
    ax.set_title("Every persistent tropical run")
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    ax = ax2
    for verdict, (lab, col, mk) in style.items():
        s = trop[trop["tt_verdict"] == verdict]
        if s.empty:
            continue
        ax.scatter(pd.to_numeric(s["vtu_median"], errors="coerce"), s["lat_median"],
                   s=110, c=col, marker=mk, edgecolors="k", linewidths=0.6, zorder=3)
    ax.axhspan(TT_MAX_POLEWARD_LAT, 0, color=PHASE_COLORS["TC"], alpha=0.12, zorder=0)
    ax.axhline(TT_MAX_POLEWARD_LAT, color=ACCEPT_BAND_EDGE, lw=1.2, ls="--", zorder=1)
    ax.axvline(0, color="k", lw=0.9)
    ax.set_xlabel(r"median $-V_T^U$ during the run  (warm-core depth)")
    ax.set_ylabel("median latitude during the run [deg]")
    ax.set_title("Warm-core depth vs latitude")

    for a in (ax1, ax2):
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("The tropical-transition test: which warm cores are tropical, and which are seclusions",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return True


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("STEP 4 (CANONICAL): figures")
    print("=" * 70)

    cy = pd.read_csv(RESULTS_DIR / "phase_classification.csv")
    # NOTE: default NA handling. Reading with keep_default_na=False turns the
    # numeric columns (ep, onset_h_from_genesis, ...) into strings, which
    # silently empties every EP-filtered panel.
    states = pd.read_csv(RESULTS_DIR / "phase_states.csv",
                         parse_dates=["start", "end"])
    ts = pd.read_csv(RESULTS_DIR / "phase_timesteps.csv", parse_dates=["datetime"],
                     usecols=["track_id", "datetime", "ep", "period",
                              "B", "VTL", "VTU", "cps_class"])

    genesis = ts.groupby("track_id")["datetime"].min()
    cy["genesis_month"] = cy["track_id"].map(genesis.dt.month)

    for name, fn in [
        ("fig1_phase_composition.png", lambda p: fig_composition(cy, p)),
        ("fig2_phase_space.png", lambda p: fig_phase_space(ts, p)),
        ("fig3_transitions.png", lambda p: fig_transitions(cy, states, ts, p)),
        ("fig4_tropical_runs.png", lambda p: fig_tropical_runs(states, p)),
    ]:
        path = FIG_DIR / name
        result = fn(path)
        if result is False:
            print(f"  {name}: skipped (nothing to plot)")
        else:
            print(f"  {path.relative_to(PROJECT_ROOT)}")

    print("\nStep 4 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
