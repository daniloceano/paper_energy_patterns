"""
Step 8 (CANONICAL): subtropical frequency of each Energy Pattern, relative to EPALL.

The candidate manuscript figure for the CPS x Energy Pattern result. It asks one
question and answers it twice, in absolute and in relative terms:

    is a cyclone of a given Energy Pattern more likely than the pooled
    population to be subtropical, or to become subtropical?

Three outcomes, mutually exclusive in the first two:

    SC        subtropical throughout - the only persistent state is SC
    ST        subtropical transition - EC -> SC during the life cycle
    SC or ST  subtropical at some persistent stage (the union)

Denominator
-----------
EPALL here is the union EP1 + EP2 + EP3 = 3,812 cyclones, NOT the 6,776 of the
catalogue. Only the clustered cyclones carry an Energy Pattern, so the pooled
reference has to be the same population that the EPs partition, or the ratio
would compare against cyclones that could never have been assigned an EP.

Statistics
----------
Two different quantities are drawn, and they answer different questions:

  * panel (a) frequency within each EP, with a Wilson 95% score interval. Wilson
    rather than Wald because several cells are small and near-zero proportions
    would otherwise get intervals crossing 0.

  * panel (b) the ratio of that frequency to the EPALL frequency. The interval
    shown is the Wilson interval of the numerator divided by the EPALL point
    estimate, i.e. it carries the sampling uncertainty of the EP only. This is
    a descriptive effect size: the numerator is NESTED in the denominator, so
    the ratio cannot be read as an independent comparison.

    The inferential claim is therefore taken from a different test - Fisher's
    exact test of each EP against the OTHER TWO POOLED, which is a genuine
    independent contrast - with Holm correction across all nine tests. Markers
    are filled when the contrast survives Holm and open when it is only
    nominally significant.

Inputs:
    results/cps_analysis/phase_classification.csv   (step 2)

Outputs:
    figures/cps_analysis/fig8_ep_relative_subtropical.png
    results/cps_analysis/ep_relative_frequency.csv

Run:
    python scripts/cps_analysis/step8_ep_relative_frequency.py

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
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label
from scripts.cps_analysis.cps_criteria import PHASE_COLORS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis"
CLASS_FILE = RESULTS_DIR / "phase_classification.csv"
OUT_FIG = FIG_DIR / "fig8_ep_relative_subtropical.png"
OUT_CSV = RESULTS_DIR / "ep_relative_frequency.csv"

# Outcome label -> (short code, two-line axis label)
OUTCOMES = [
    ("SC", "SC\nsubtropical\nthroughout"),
    ("ST", "ST\nsubtropical\ntransition"),
    ("SC or ST", "SC or ST\nsubtropical at some\npersistent stage"),
]
BAR_W = 0.26
ALPHA = 0.05


def outcome_flags(d: pd.DataFrame) -> dict:
    sc = d["phase_class"] == "SC"
    st = d["phase_class"] == "ST"
    return {"SC": sc, "ST": st, "SC or ST": sc | st}


def build_table(d: pd.DataFrame) -> pd.DataFrame:
    """One row per (outcome, EP): rate, Wilson interval, ratio, Fisher vs rest."""
    rows = []
    for name, flag in outcome_flags(d).items():
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


def make_figure(t: pd.DataFrame, path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.1))
    fig.subplots_adjust(left=0.062, right=0.985, top=0.775, bottom=0.235,
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
        for x, val, n in zip(pos, v, sub["k_ep"].values):
            ax.text(x, 0.45, f"{n}", ha="center", va="bottom", fontsize=8,
                    color="white", fontweight="bold", zorder=4)

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
    ax.set_title("(a)   how common the structure is within each Energy Pattern",
                 fontsize=11.5, pad=9, loc="left")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2)

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
                ax.text(x, sub["ratio_hi"].values[j] + 0.045, s, ha="center",
                        va="bottom", fontsize=11, fontweight="bold",
                        color=EP_COLORS[ep])

    ax.set_yscale("log")
    ticks = [0.5, 0.7, 1.0, 1.4, 2.0]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{v:g}×" for v in ticks], fontsize=10)
    ax.minorticks_off()
    ax.set_ylim(0.45, 2.1)
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

    fig.text(0.5, 0.975,
             "Subtropical structure by Energy Pattern, against the pooled population",
             ha="center", va="top", fontsize=15.5, fontweight="bold")
    n_all = int(t["n_epall"].iloc[0])
    fig.text(0.5, 0.938,
             f"{n_all:,} cyclones with an Energy Pattern, genesis 1979–2020  ·  "
             "canonical CPS classification, 36 h persistence gate  ·  "
             "bars and whiskers are Wilson 95% intervals",
             ha="center", va="top", fontsize=10, color="0.35")
    fig.text(0.5, 0.088,
             "EPALL is the union EP1 + EP2 + EP3, so each EP is NESTED in the "
             "reference: the ratio in (b) is a descriptive effect size,\nnot an "
             "independent test.  "
             "Stars are Fisher's exact test of each EP against the other two pooled "
             "(* p<0.05, ** p<0.01, *** p<0.001).\n"
             "A FILLED marker also survives Holm correction over the nine contrasts; "
             "an OPEN one is nominally significant only.",
             ha="center", va="top", fontsize=9, color="0.45", style="italic",
             linespacing=1.6)

    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("STEP 8 (CANONICAL): subtropical frequency by EP, relative to EPALL")
    print("=" * 70)

    if not CLASS_FILE.exists():
        print(f"Missing {CLASS_FILE}. Run step 2 first.")
        return 1

    cy = pd.read_csv(CLASS_FILE)
    d = cy[cy["ep"].notna()].copy()
    d["ep"] = d["ep"].astype(int)
    print(f"\nEP-labelled population: {len(d):,} of {len(cy):,} catalogue cyclones")
    for ep in ALL_EPS:
        print(f"  {get_ep_label(ep)}: {(d['ep'] == ep).sum():,}")

    t = build_table(d)
    t.to_csv(OUT_CSV, index=False)

    for name, _ in OUTCOMES:
        sub = t[t["outcome"] == name]
        p_all = sub["rate_epall"].iloc[0]
        print(f"\n{name}  —  EPALL {100 * p_all:.2f}% "
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

    make_figure(t, OUT_FIG)
    print(f"\nWrote {OUT_FIG.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print("\nStep 8 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
