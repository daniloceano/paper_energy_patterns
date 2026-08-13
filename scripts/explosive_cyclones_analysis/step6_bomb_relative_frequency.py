"""
Step 6 (CANONICAL): explosive frequency of each Energy Pattern, relative to EPALL.

The candidate manuscript figure for the bomb x Energy Pattern result. It asks one
question and answers it twice, in absolute and in relative terms:

    is a cyclone of a given Energy Pattern more likely than the pooled
    population to undergo explosive deepening?

Built to the same template as the CPS analysis' canonical frequency figure
(`scripts/cps_analysis/step8_ep_relative_frequency.py`), so the two results are
read the same way.

Outcomes
--------
A NESTED severity ladder on the maximum normalized deepening rate, not a
partition:

    bomb                NDR_max >= 1.0 Bergeron   (Sanders & Gyakum 1980)
    moderate or intense NDR_max >= 1.3
    intense             NDR_max >= 1.8

Each is contained in the one before it, so the three panels read as "how far up
the severity ladder does each Energy Pattern reach", and a ratio that grows
along the ladder means the EP is enriched in the SEVERE tail, not merely in the
count of bombs. The thresholds are the class edges of step 4 (AABC 2024), taken
from the code rather than its docstring: the "intense" class there is closed at
the bottom, NDR >= 1.8.

Denominator: the ASSESSABLE population
--------------------------------------
A cyclone whose central-pressure series never supports a full 24 h window has no
NDR at all, and step 4 writes NaN. Such a cyclone is not a non-bomb - it is
unclassifiable - so it is excluded from BOTH numerator and denominator here.

This is the one deliberate difference from step 4, which counts every processed
cyclone in its denominator and so silently reads NaN as "not a bomb". It matters
because the unassessable fraction is not uniform across the EPs (EP3 loses ~3.3%
of its cyclones, EP2 only ~1.2%), and EP3 is the low-frequency pattern: charging
its missing NDRs to the non-bomb column would exaggerate the very contrast this
figure is drawn to show. Both denominators are printed so the difference stays
visible.

EPALL here is the union EP1 + EP2 + EP3 restricted to the assessable cyclones,
NOT the 6,776 of the catalogue: only the clustered cyclones carry an Energy
Pattern, so the pooled reference has to be the same population the EPs partition.

Statistics
----------
Two different quantities are drawn, and they answer different questions:

  * panel (a) frequency within each EP, with a Wilson 95% score interval. Wilson
    rather than Wald because the "intense" cells are small and near-zero
    proportions would otherwise get intervals crossing 0.

  * panel (b) the ratio of that frequency to the EPALL frequency. The interval
    shown is the Wilson interval of the numerator divided by the EPALL point
    estimate, i.e. it carries the sampling uncertainty of the EP only. This is a
    descriptive effect size: the numerator is NESTED in the denominator, so the
    ratio cannot be read as an independent comparison.

    The inferential claim is therefore taken from a different test - Fisher's
    exact test of each EP against the OTHER TWO POOLED, which is a genuine
    independent contrast - with Holm correction across all nine tests. Markers
    are filled when the contrast survives Holm and open when it is only
    nominally significant.

Scope
-----
`--scope lifecycle` (default) uses the maximum NDR anywhere in the life cycle.
`--scope intensification` restricts the window centre to the intensification
phase of the life-cycle classification, which is the stricter reading of "the
cyclone deepened explosively while it was intensifying". The intensification
scope loses more cyclones to NaN (211 vs 99), so its denominator is smaller;
outputs are written with an `_intensification` suffix and never overwrite the
canonical ones.

Inputs:
    results/explosive_cyclones/ndr_by_cyclone.csv    (step 4)

Outputs:
    figures/explosive_cyclones/fig6_bomb_relative_frequency[_intensification].png
    results/explosive_cyclones/bomb_relative_frequency[_intensification].csv

Run:
    python scripts/explosive_cyclones_analysis/step6_bomb_relative_frequency.py
    python scripts/explosive_cyclones_analysis/step6_bomb_relative_frequency.py \
        --scope intensification

Author: Danilo Couto de Souza
Date: August 2026
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "explosive_cyclones"
FIG_DIR = PROJECT_ROOT / "figures" / "explosive_cyclones"
NDR_FILE = RESULTS_DIR / "ndr_by_cyclone.csv"

# Severity ladder: (short code, two-line axis label, NDR threshold).
# Nested, not disjoint — see the module docstring.
OUTCOMES = [
    ("bomb", "bomb\nNDR $\\geq$ 1.0\nexplosive at all", 1.0),
    ("moderate or intense", "moderate or intense\nNDR $\\geq$ 1.3", 1.3),
    ("intense", "intense\nNDR $\\geq$ 1.8", 1.8),
]
BAR_W = 0.26
ALPHA = 0.05

SCOPE_COLUMN = {"lifecycle": "ndr_max_lifecycle",
                "intensification": "ndr_max_intensification"}
SCOPE_NOTE = {
    "lifecycle": "maximum NDR anywhere in the life cycle",
    "intensification": "maximum NDR with the window centred in the "
                       "intensification phase",
}


def outcome_flags(d: pd.DataFrame, col: str) -> dict:
    """Boolean series per outcome, on the severity ladder."""
    return {name: d[col] >= thr for name, _, thr in OUTCOMES}


def build_table(d: pd.DataFrame, col: str) -> pd.DataFrame:
    """One row per (outcome, EP): rate, Wilson interval, ratio, Fisher vs rest."""
    rows = []
    for name, flag in outcome_flags(d, col).items():
        k_all, n_all = int(flag.sum()), len(d)
        p_all = k_all / n_all
        for ep in ALL_EPS:
            m = d["ep"] == ep
            k, n = int(flag[m].sum()), int(m.sum())
            lo, hi = proportion_confint(k, n, ALPHA, method="wilson")
            # Fisher: this EP against the other two pooled — an independent
            # contrast, unlike the nested ratio to EPALL.
            a, na = k, n
            b, nb = int(flag[~m].sum()), int((~m).sum())
            odds, p = fisher_exact([[a, na - a], [b, nb - b]])
            rows.append({
                "outcome": name, "ep": get_ep_label(ep),
                "n_ep": n, "k_ep": k, "rate_ep": k / n,
                "rate_ep_lo": lo, "rate_ep_hi": hi,
                "n_epall": n_all, "k_epall": k_all, "rate_epall": p_all,
                "ratio_to_epall": (k / n) / p_all,
                "ratio_lo": lo / p_all, "ratio_hi": hi / p_all,
                "odds_ratio_vs_rest": odds, "p_fisher_vs_rest": p,
            })
    t = pd.DataFrame(rows)
    reject, p_adj, _, _ = multipletests(t["p_fisher_vs_rest"], alpha=ALPHA,
                                        method="holm")
    t["p_holm"] = p_adj
    t["significant_holm"] = reject
    t["significant_nominal"] = t["p_fisher_vs_rest"] < ALPHA
    return t


def stars(row) -> str:
    """Star level from the RAW Fisher p, the conventional meaning.

    Holm survival is encoded by the marker fill instead, so the two pieces of
    information stay separable: mixing them (stars from the adjusted p where it
    survives, from the raw p where it does not) makes the strongest result look
    weaker than a result that was not corrected at all.
    """
    if not row["significant_nominal"]:
        return ""
    p = row["p_fisher_vs_rest"]
    return "***" if p < 1e-3 else "**" if p < 1e-2 else "*"


def make_figure(t: pd.DataFrame, path: Path, scope: str, n_years: int,
                n_unassessable: int, n_processed: int):
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.6))
    fig.subplots_adjust(left=0.062, right=0.985, top=0.795, bottom=0.265,
                        wspace=0.235)
    xs = np.arange(len(OUTCOMES))
    names = [o[0] for o in OUTCOMES]
    labels = [o[1] for o in OUTCOMES]

    # ---------------- (a) frequency within each EP ----------------
    ax = axes[0]
    for k, ep in enumerate(ALL_EPS):
        lab = get_ep_label(ep)
        sub = t[t["ep"] == lab].set_index("outcome").loc[names]
        v = sub["rate_ep"].values * 100
        err = np.vstack([v - sub["rate_ep_lo"].values * 100,
                         sub["rate_ep_hi"].values * 100 - v])
        pos = xs + (k - 1) * BAR_W
        ax.bar(pos, v, BAR_W, color=EP_COLORS[ep], edgecolor="white",
               linewidth=0.8, label=lab, zorder=2)
        ax.errorbar(pos, v, yerr=err, fmt="none", ecolor="0.25", elinewidth=1.1,
                    capsize=2.6, zorder=3)
        # Count inside the bar where there is room for it, above the whisker
        # where there is not: the "intense" bars are a couple of percent tall
        # and a white label inside them is unreadable.
        for x, val, n, hi in zip(pos, v, sub["k_ep"].values,
                                 sub["rate_ep_hi"].values * 100):
            if val >= 6.0:
                ax.text(x, 0.6, f"{n}", ha="center", va="bottom", fontsize=8,
                        color="white", fontweight="bold", zorder=4)
            else:
                ax.text(x, hi + 0.7, f"{n}", ha="center", va="bottom",
                        fontsize=8, color=EP_COLORS[ep], fontweight="bold",
                        zorder=4)

    # EPALL reference, one segment per outcome group
    for i, name in enumerate(names):
        p_all = t.loc[t["outcome"] == name, "rate_epall"].iloc[0] * 100
        ax.plot([i - 2 * BAR_W, i + 2 * BAR_W], [p_all, p_all], "--",
                color="0.25", lw=1.5, zorder=5,
                label="EPALL (pooled)" if i == 0 else None)
        ax.text(i + 2 * BAR_W, p_all, f" {p_all:.1f}%", ha="left", va="center",
                fontsize=8.5, color="0.25", fontweight="bold")

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("cyclones of the Energy Pattern  [%]", fontsize=11.5)
    ax.set_ylim(0, max(t["rate_ep_hi"]) * 100 * 1.16)
    ax.set_title("(a)   how common explosive deepening is within each Energy Pattern",
                 fontsize=11.5, pad=9, loc="left")
    ax.legend(frameon=False, fontsize=9.5, loc="upper right", ncol=2)

    # ---------------- (b) relative to EPALL ----------------
    ax = axes[1]
    ax.axhline(1.0, color="0.25", ls="--", lw=1.5, zorder=2)
    ax.axhspan(1.0, 10, color="0.55", alpha=0.055, zorder=0)
    # Label sits inside the axes, hard against the left spine: at the right edge
    # it clipped, and next to a marker it read as belonging to that marker.
    ax.text(-0.52, 1.02, "EPALL (pooled)", ha="left", va="bottom", fontsize=9,
            color="0.25", fontweight="bold", zorder=6)

    for k, ep in enumerate(ALL_EPS):
        lab = get_ep_label(ep)
        sub = t[t["ep"] == lab].set_index("outcome").loc[names]
        r = sub["ratio_to_epall"].values
        err = np.vstack([r - sub["ratio_lo"].values, sub["ratio_hi"].values - r])
        pos = xs + (k - 1) * BAR_W
        ax.errorbar(pos, r, yerr=err, fmt="none", ecolor=EP_COLORS[ep],
                    elinewidth=2.0, capsize=3.4, zorder=3)
        for j, (x, y) in enumerate(zip(pos, r)):
            row = sub.iloc[j]
            filled = bool(row["significant_holm"])
            ax.plot(x, y, "o", ms=10, mfc=EP_COLORS[ep] if filled else "white",
                    mec=EP_COLORS[ep], mew=2.0, zorder=4,
                    label=lab if j == 0 else None)
            s = stars(row)
            if s:
                ax.text(x, sub["ratio_hi"].values[j] * 1.045, s, ha="center",
                        va="bottom", fontsize=11, fontweight="bold",
                        color=EP_COLORS[ep])

    ax.set_yscale("log")
    lo = min(t["ratio_lo"].min(), 1 / 1.6)
    hi = max(t["ratio_hi"].max(), 1.6)
    ax.set_ylim(lo / 1.35, hi * 1.3)
    ticks = [x for x in (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.4, 2.0, 3.0, 4.0)
             if lo / 1.3 <= x <= hi * 1.25]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{v:g}×" for v in ticks], fontsize=10)
    ax.minorticks_off()
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_xlim(-0.55, len(OUTCOMES) - 0.45)
    ax.set_ylabel("frequency relative to EPALL", fontsize=11.5)
    ax.set_title("(b)   enrichment or depletion against the pooled population",
                 fontsize=11.5, pad=9, loc="left")

    # No legend here on purpose: the colours are already keyed in (a), and a
    # legend box in this panel collides with the significance marks. The
    # filled/open convention is stated in the footer.

    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(labelsize=10)
        a.set_axisbelow(True)
        a.grid(axis="y", color="0.9", lw=0.7, zorder=0)

    fig.text(0.5, 0.978,
             "Explosive deepening by Energy Pattern, against the pooled population",
             ha="center", va="top", fontsize=15.5, fontweight="bold")
    n_all = int(t["n_epall"].iloc[0])
    fig.text(0.5, 0.944,
             f"{n_all:,} cyclones with an Energy Pattern and an assessable NDR  ·  "
             f"genesis 1979–2020 ({n_years} years)  ·  {SCOPE_NOTE[scope]}\n"
             "Sanders & Gyakum (1980) normalised deepening rate, 24 h centred "
             "window, sin-latitude normalisation (reference 60°)",
             ha="center", va="top", fontsize=9.5, color="0.35", linespacing=1.5)
    fig.text(0.5, 0.105,
             "Outcomes are NESTED thresholds on the same NDR, not disjoint classes: "
             "a ratio that grows along the ladder means enrichment in the SEVERE tail.\n"
             "EPALL is the union EP1 + EP2 + EP3, so each EP is nested in the "
             "reference — the ratio in (b) is a descriptive effect size, not an "
             "independent test.\n"
             "Stars are Fisher's exact test of each EP against the other two pooled "
             "(* p<0.05, ** p<0.01, *** p<0.001); a FILLED marker also survives Holm "
             "correction over the nine contrasts, an OPEN one is nominal only.\n"
             f"{n_unassessable} of {n_processed:,} processed cyclones have no "
             f"assessable NDR and are excluded from both numerator and denominator.",
             ha="center", va="top", fontsize=8.8, color="0.45", style="italic",
             linespacing=1.55)

    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def main(scope: str):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if scope == "lifecycle" else f"_{scope}"
    out_fig = FIG_DIR / f"fig6_bomb_relative_frequency{suffix}.png"
    out_csv = RESULTS_DIR / f"bomb_relative_frequency{suffix}.csv"

    print("=" * 70)
    print("STEP 6 (CANONICAL): explosive frequency by EP, relative to EPALL")
    print(f"  Scope: {scope} — {SCOPE_NOTE[scope]}")
    print("=" * 70)

    if not NDR_FILE.exists():
        print(f"Missing {NDR_FILE}. Run step 4 first.")
        return 1

    nd = pd.read_csv(NDR_FILE)
    col = SCOPE_COLUMN[scope]
    n_processed = len(nd)

    d = nd[nd[col].notna()].copy()
    d["ep"] = d["ep"].astype(int)
    n_unassessable = n_processed - len(d)

    n_years = 2020 - 1979 + 1
    print(f"\nProcessed cyclones:   {n_processed:,}")
    print(f"Assessable NDR:       {len(d):,}  "
          f"({n_unassessable} excluded, {100 * n_unassessable / n_processed:.1f}%)")
    for ep in ALL_EPS:
        n_ep = int((nd["ep"] == ep).sum())
        n_ok = int((d["ep"] == ep).sum())
        print(f"  {get_ep_label(ep)}: {n_ok:5,d} of {n_ep:5,d} processed "
              f"({n_ep - n_ok} unassessable)")

    t = build_table(d, col)
    t.to_csv(out_csv, index=False)

    for name, _, thr in OUTCOMES:
        sub = t[t["outcome"] == name]
        p_all = sub["rate_epall"].iloc[0]
        print(f"\n{name}  (NDR >= {thr})  —  EPALL {100 * p_all:.2f}% "
              f"({int(sub['k_epall'].iloc[0]):,}/{int(sub['n_epall'].iloc[0]):,})")
        for _, r in sub.iterrows():
            mark = "  HOLM" if r["significant_holm"] else \
                   "  nominal" if r["significant_nominal"] else ""
            print(f"  {r['ep']}: {r['k_ep']:4d}/{r['n_ep']:5d} = "
                  f"{100 * r['rate_ep']:5.2f}%  "
                  f"[{100 * r['rate_ep_lo']:.2f}, {100 * r['rate_ep_hi']:.2f}]  "
                  f"ratio {r['ratio_to_epall']:.2f} "
                  f"[{r['ratio_lo']:.2f}, {r['ratio_hi']:.2f}]  "
                  f"OR {r['odds_ratio_vs_rest']:.2f}  "
                  f"p {r['p_fisher_vs_rest']:.2e}  "
                  f"p_holm {r['p_holm']:.2e}{mark}")

    # The step-4 denominator, printed so the difference stays visible.
    print("\nSame bomb rates on the step-4 denominator (every processed cyclone,\n"
          "NaN NDR counted as non-bomb) — the comparison this step deliberately avoids:")
    for ep in ALL_EPS:
        e = nd[nd["ep"] == ep]
        k = int((e[col] >= 1.0).sum())
        print(f"  {get_ep_label(ep)}: {k:4d}/{len(e):5d} = {100 * k / len(e):5.2f}%"
              f"   (assessable: {100 * t.loc[(t['outcome'] == 'bomb') & (t['ep'] == get_ep_label(ep)), 'rate_ep'].iloc[0]:5.2f}%)")

    make_figure(t, out_fig, scope, n_years, n_unassessable, n_processed)
    print(f"\nWrote {out_fig.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {out_csv.relative_to(PROJECT_ROOT)}")
    print("\nStep 6 complete.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Explosive frequency by Energy Pattern, relative to EPALL.")
    ap.add_argument("--scope", default="lifecycle",
                    choices=["lifecycle", "intensification"],
                    help="NDR scope (default: lifecycle, the canonical figure)")
    args = ap.parse_args()
    sys.exit(main(args.scope))
