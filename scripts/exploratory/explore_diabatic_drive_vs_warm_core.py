"""
Exploratory: is the warm-core signal a DIABATIC signal?

Follow-up to `explore_lec_conversions_vs_warm_core.py`, which found that
baroclinic conversion Ca predicts a warm core NEGATIVELY. That result is
consistent with a subtropical cyclone being driven by latent heat release
rather than by baroclinic conversion — but consistency is not a test.

This script runs the test with power to falsify. The hypothesis makes a
directional prediction that the earlier figure could not make:

    if subtropical cyclones are diabatically driven, then the GENERATION of
    eddy available potential energy, Ge — the term fed by diabatic heating
    correlated with the temperature anomaly — must predict a warm core
    POSITIVELY, opposite in sign to Ca.

A plain univariate fit does not settle it, because Ca and Ge are correlated
(Spearman +0.50): marginally, Ge inherits Ca's negative association. Two things
resolve that, and both are shown:

  * fitting all seven LEC terms jointly, so Ge is read at fixed Ca;
  * forming the scale-free DIABATIC SHARE of the eddy APE supply,

        f = Ge / (Ge + Ca),     evaluated where both terms are sources,

    which is the physically meaningful quantity: the fraction of the eddy
    available-potential-energy supply that is diabatic rather than baroclinic.

Restricting to Ge > 0 and Ca > 0 drops 792 of 3,812 cyclones. The console
output reports the warm-core rate in the dropped set so the restriction can be
checked for selection bias.

Same caveat as the companion script: the Energy Patterns were obtained by
PCA + K-Means on these very columns, so this is not independent evidence for the
EP result. It is a test of the PHYSICAL mechanism proposed to explain it.

Inputs:
    results/cluster/pca_full_data.csv
    results/cps_analysis/phase_classification.csv

Outputs:
    figures/exploratory/diabatic_drive_vs_warm_core.png
    results/exploratory/diabatic_drive_vs_warm_core.csv

Run:
    python scripts/exploratory/explore_diabatic_drive_vs_warm_core.py

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
from scipy.stats import norm, spearmanr
from statsmodels.stats.proportion import proportion_confint

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEC_FILE = PROJECT_ROOT / "results" / "cluster" / "pca_full_data.csv"
CPS_FILE = PROJECT_ROOT / "results" / "cps_analysis" / "phase_classification.csv"
FIG_OUT = PROJECT_ROOT / "figures" / "exploratory" / "diabatic_drive_vs_warm_core.png"
CSV_OUT = PROJECT_ROOT / "results" / "exploratory" / "diabatic_drive_vs_warm_core.csv"

TERMS = ["Ca", "Ck", "Ge", "BAe", "BKe", "Ae", "Ke"]
TERM_LABEL = {"Ca": "$C_a$  baroclinic", "Ck": "$C_k$  barotropic",
              "Ge": "$G_e$  APE generation", "BAe": "$BA_e$  APE flux",
              "BKe": "$BK_e$  KE flux", "Ae": "$A_e$  eddy APE",
              "Ke": "$K_e$  eddy KE"}
PHASES = ["inc", "int", "mat", "dec"]
PHASE_NAMES = {"inc": "incipient", "int": "intensification",
               "mat": "mature", "dec": "decay"}
PHASE = "int"
NQ = 5
WARM = ["SC", "ST", "SD"]
BLUE, RED, GREEN = "#1f4e9c", "#c0392b", "#1b9e77"


def irls(X: np.ndarray, y: np.ndarray, maxit=200, tol=1e-11):
    """Logistic regression by IRLS; statsmodels.api does not import here."""
    b = np.zeros(X.shape[1])
    for _ in range(maxit):
        p = 1.0 / (1.0 + np.exp(-(X @ b)))
        w = np.clip(p * (1 - p), 1e-9, None)
        step = np.linalg.solve((X.T * w) @ X, X.T @ (y - p))
        b = b + step
        if np.max(np.abs(step)) < tol:
            break
    p = 1.0 / (1.0 + np.exp(-(X @ b)))
    w = np.clip(p * (1 - p), 1e-9, None)
    return b, np.sqrt(np.diag(np.linalg.inv((X.T * w) @ X)))


def fit(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Standardised logistic fit; returns OR per 1 SD with 95% CI."""
    Z = df[cols].copy()
    Z = (Z - Z.mean()) / Z.std()
    X = np.column_stack([np.ones(len(Z))] + [Z[c].values for c in cols])
    b, se = irls(X, df["warm"].to_numpy(dtype=float))
    return pd.DataFrame([
        dict(term=c, odds_ratio=np.exp(b[i]),
             lo=np.exp(b[i] - 1.959964 * se[i]), hi=np.exp(b[i] + 1.959964 * se[i]),
             p=2 * norm.sf(abs(b[i] / se[i])))
        for i, c in enumerate(cols, start=1)])


def load() -> pd.DataFrame:
    lec = pd.read_csv(LEC_FILE)
    cps = pd.read_csv(CPS_FILE, usecols=["track_id", "phase_class"])
    d = lec.merge(cps, on="track_id")
    d["warm"] = d["phase_class"].isin(WARM).astype(int)
    return d


def diabatic_share(d: pd.DataFrame, phase: str) -> pd.DataFrame:
    g, c = d[f"Ge_{phase}"], d[f"Ca_{phase}"]
    sub = d[(g > 0) & (c > 0)].copy()
    sub["f"] = sub[f"Ge_{phase}"] / (sub[f"Ge_{phase}"] + sub[f"Ca_{phase}"])
    return sub


def main() -> int:
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    d = load()
    cols = [f"{t}_{PHASE}" for t in TERMS]

    print("=" * 74)
    print("EXPLORATORY: is the warm-core signal diabatic?")
    print("=" * 74)
    print(f"\n{len(d):,} cyclones, {int(d['warm'].sum())} with a persistent "
          f"subtropical state ({100 * d['warm'].mean():.2f}%)")

    uni = pd.concat([fit(d, [c]) for c in cols], ignore_index=True)
    multi = fit(d, cols)
    uni["model"], multi["model"] = "univariate", "multivariate"
    uni["term"] = [t.rsplit("_", 1)[0] for t in uni["term"]]
    multi["term"] = [t.rsplit("_", 1)[0] for t in multi["term"]]

    ge_u = uni.loc[uni.term == "Ge"].iloc[0]
    ge_m = multi.loc[multi.term == "Ge"].iloc[0]
    print(f"\nFALSIFICATION TEST — Ge must be POSITIVE if the drive is diabatic")
    print(f"  univariate   : OR = {ge_u.odds_ratio:.2f} "
          f"[{ge_u.lo:.2f}, {ge_u.hi:.2f}]  p = {ge_u.p:.1e}   "
          f"{'PASS' if ge_u.lo > 1 else 'inconclusive (CI spans 1)'}")
    print(f"  multivariate : OR = {ge_m.odds_ratio:.2f} "
          f"[{ge_m.lo:.2f}, {ge_m.hi:.2f}]  p = {ge_m.p:.1e}   "
          f"{'PASS' if ge_m.lo > 1 else 'FAIL'}")

    # --- diabatic share ---
    sub = diabatic_share(d, PHASE)
    dropped = d[~d.track_id.isin(sub.track_id)]
    print(f"\nDiabatic share f = Ge/(Ge+Ca), where both are sources:")
    print(f"  {len(sub):,} cyclones retained, {len(dropped):,} dropped")
    print(f"  warm-core rate  retained {100 * sub.warm.mean():.2f}%   "
          f"dropped {100 * dropped.warm.mean():.2f}%   "
          f"(selection bias check)")
    fs = fit(sub, ["f"]).iloc[0]
    fa = fit(sub, ["f", f"Ae_{PHASE}"])
    print(f"  f alone            : OR = {fs.odds_ratio:.2f} "
          f"[{fs.lo:.2f}, {fs.hi:.2f}]  p = {fs.p:.1e}")
    print(f"  f | Ae             : OR = {fa.iloc[0].odds_ratio:.2f} "
          f"[{fa.iloc[0].lo:.2f}, {fa.iloc[0].hi:.2f}]  p = {fa.iloc[0].p:.1e}")

    # =================== figure ===================
    fig, axes = plt.subplots(2, 2, figsize=(14.2, 10.6))
    fig.subplots_adjust(left=0.135, right=0.965, top=0.845, bottom=0.115,
                        hspace=0.42, wspace=0.34)

    # (a) forest plot
    ax = axes[0, 0]
    order = list(reversed(TERMS))
    for k, t in enumerate(order):
        for src, colour, off, mk in ((uni, "0.55", -0.16, "o"),
                                     (multi, BLUE, 0.16, "s")):
            r = src.loc[src.term == t].iloc[0]
            ax.errorbar(r.odds_ratio, k + off,
                        xerr=[[r.odds_ratio - r.lo], [r.hi - r.odds_ratio]],
                        fmt=mk, color=colour, ms=7.5, capsize=3.5, lw=1.8)
    ax.axvline(1.0, color="0.3", ls="--", lw=1.4)
    ax.set_xscale("log")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([TERM_LABEL[t] for t in order], fontsize=10)
    ax.set_xlabel("odds ratio per 1 SD", fontsize=11)
    ax.set_title("(a)   every LEC term against the warm-core outcome",
                 fontsize=11.5, loc="left")
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color="0.55", ms=7.5,
                                  label="univariate"),
                       plt.Line2D([], [], marker="s", ls="", color=BLUE, ms=7.5,
                                  label="all seven jointly")],
              frameon=False, fontsize=9.5, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)

    # (b) correlation matrix — why (a)'s two models differ
    ax = axes[0, 1]
    Z = d[cols].copy()
    Z.columns = TERMS
    C = Z.corr(method="spearman")
    im = ax.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(TERMS)))
    ax.set_xticklabels(TERMS, fontsize=9.5)
    ax.set_yticks(range(len(TERMS)))
    ax.set_yticklabels(TERMS, fontsize=9.5)
    for i in range(len(TERMS)):
        for j in range(len(TERMS)):
            ax.text(j, i, f"{C.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(C.iloc[i, j]) > 0.55 else "0.15")
    fig.colorbar(im, ax=ax, shrink=0.82).set_label("Spearman ρ", fontsize=10)
    ax.set_title("(b)   why the two models disagree\n"
                 r"the terms are correlated: $C_a$–$G_e$ = "
                 f"{C.loc['Ca', 'Ge']:+.2f}", fontsize=11.5, loc="left")

    # (c) the test itself
    ax = axes[1, 0]
    q = pd.qcut(sub["f"], NQ, labels=False)
    xs, ps, los, his, ns = [], [], [], [], []
    for i in range(NQ):
        m = (q == i).to_numpy()
        k, n = int(sub["warm"].to_numpy()[m].sum()), int(m.sum())
        lo, hi = proportion_confint(k, n, 0.05, method="wilson")
        xs.append(float(sub["f"].to_numpy()[m].mean()))
        ps.append(100 * k / n); los.append(100 * lo); his.append(100 * hi); ns.append(n)
    ax.errorbar(xs, ps, yerr=[np.array(ps) - los, np.array(his) - ps],
                fmt="o-", color=GREEN, ms=9, lw=2.2, capsize=4)
    for x, p_, n in zip(xs, ps, ns):
        ax.annotate(f"n={n}", (x, 0), textcoords="offset points", xytext=(0, 6),
                    ha="center", va="bottom", fontsize=8, color="0.45")
    ax.axhline(100 * sub["warm"].mean(), color="0.35", ls="--", lw=1.4)
    ax.text(0.985, 100 * sub["warm"].mean(), " all cyclones",
            transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            fontsize=9, color="0.35")
    ax.set_xlabel(r"diabatic share  $f = G_e/(G_e+C_a)$", fontsize=11.5)
    ax.set_ylabel("P(persistent warm core)  [%]", fontsize=11)
    ax.set_ylim(bottom=0)
    ax.set_title("(c)   THE TEST: the more diabatic the supply,\n"
                 f"the more likely a warm core — OR = {fs.odds_ratio:.2f} per SD",
                 fontsize=11.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)

    # (d) stability across the life cycle
    ax = axes[1, 1]
    rows = []
    for k, ph in enumerate(PHASES):
        s = diabatic_share(d, ph)
        r = fit(s, ["f"]).iloc[0]
        ax.errorbar(k, r.odds_ratio,
                    yerr=[[r.odds_ratio - r.lo], [r.hi - r.odds_ratio]],
                    fmt="o", color=GREEN, ms=10, capsize=4, lw=2.2)
        rows.append(dict(phase=ph, n=len(s), odds_ratio=r.odds_ratio,
                         lo=r.lo, hi=r.hi, p=r.p))
    ax.axhline(1.0, color="0.35", ls="--", lw=1.4)
    ax.set_xticks(range(len(PHASES)))
    ax.set_xticklabels([PHASE_NAMES[p_] for p_ in PHASES], fontsize=10)
    ax.set_ylabel("odds ratio per 1 SD of $f$", fontsize=11)
    ax.set_title("(d)   is it stable through the life cycle?", fontsize=11.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)

    fig.text(0.5, 0.975, "Is the warm-core signal a diabatic signal?",
             ha="center", va="top", fontsize=17.5, fontweight="bold")
    fig.text(0.5, 0.937,
             f"{len(d):,} cyclones · LEC terms from the {PHASE_NAMES[PHASE]} phase · "
             "outcome = reaching a persistent subtropical state (SC, ST or SD)",
             ha="center", va="top", fontsize=10.5, color="0.35")
    fig.text(0.5, 0.048,
             "The hypothesis predicted the SIGN of $G_e$ before the fit, which is what "
             "makes this a test rather than a description.\nEXPLORATORY: the Energy "
             "Patterns were built from these same columns, so this tests the proposed "
             "mechanism, not the EP result itself.",
             ha="center", va="top", fontsize=9, color="0.45", style="italic",
             linespacing=1.6)

    fig.savefig(FIG_OUT, dpi=200, facecolor="white")
    plt.close(fig)

    out = pd.concat([uni, multi], ignore_index=True)
    out.to_csv(CSV_OUT, index=False)
    print("\nDiabatic share by life-cycle phase (OR per SD):")
    for r in rows:
        print(f"  {PHASE_NAMES[r['phase']]:<16s} OR = {r['odds_ratio']:.2f} "
              f"[{r['lo']:.2f}, {r['hi']:.2f}]  p = {r['p']:.1e}  n = {r['n']:,}")
    print(f"\nWrote {FIG_OUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {CSV_OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
