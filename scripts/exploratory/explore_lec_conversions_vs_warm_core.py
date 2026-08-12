"""
Exploratory: does a cyclone's energetics predict whether it develops a warm core?

Relates the two conversion terms of the Lorenz Energy Cycle — baroclinic (Ca)
and barotropic (Ck) — to the probability that a cyclone reaches a PERSISTENT
subtropical state under the canonical CPS protocol (classes SC, ST or SD).

Sign conventions (project-wide):
    Ca > 0   baroclinic conversion  Az -> Ae  (the classic extratropical driver)
    Ck < 0   barotropic instability Kz -> Ke  (mean flow feeds the eddy)

IMPORTANT — this is NOT independent evidence for the Energy Pattern result.
The EPs were obtained by PCA + K-Means on exactly these columns, so this figure
is the C4 result seen WITHOUT the clustering step. Its value is resolution: it
says which conversion term carries the signal, and whether the relationship is
monotonic or has structure the three-cluster discretisation hides.

Phase choice. The conversions are taken from the INTENSIFICATION phase by
default. Using the decay phase would invite reverse causation: subtropical
structure often appears late, so decay-phase energetics could be a consequence
of the warm core rather than a precursor. Panel (d) repeats the fit for all four
phases precisely so that this can be checked.

Inputs:
    results/cluster/pca_full_data.csv               (Ca/Ck per lifecycle phase)
    results/cps_analysis/phase_classification.csv   (canonical CPS classes)

Outputs:
    figures/exploratory/lec_conversions_vs_warm_core.png
    results/exploratory/lec_conversions_vs_warm_core.csv

Run:
    python scripts/exploratory/explore_lec_conversions_vs_warm_core.py

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
from scipy.stats import norm
from matplotlib.colors import TwoSlopeNorm
from statsmodels.stats.proportion import proportion_confint

from scripts.cps_analysis.cps_criteria import PHASE_COLORS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEC_FILE = PROJECT_ROOT / "results" / "cluster" / "pca_full_data.csv"
CPS_FILE = PROJECT_ROOT / "results" / "cps_analysis" / "phase_classification.csv"
FIG_OUT = PROJECT_ROOT / "figures" / "exploratory" / "lec_conversions_vs_warm_core.png"
CSV_OUT = PROJECT_ROOT / "results" / "exploratory" / "lec_conversions_vs_warm_core.csv"

PHASE = "int"                      # intensification
PHASE_NAMES = {"inc": "incipient", "int": "intensification",
               "mat": "mature", "dec": "decay"}
NBINS = 6                          # quantile bins per axis in the 2-D map
MIN_N = 25                         # a 2-D cell below this is not drawn
NDEC = 8                           # bins for the marginal curves
WARM_CLASSES = ["SC", "ST", "SD"]


def load() -> pd.DataFrame:
    lec = pd.read_csv(LEC_FILE)
    cps = pd.read_csv(CPS_FILE, usecols=["track_id", "phase_class", "ep", "frac_SC"])
    d = lec.merge(cps, on="track_id")
    d["warm"] = d["phase_class"].isin(WARM_CLASSES).astype(int)
    return d


def binned_probability(d: pd.DataFrame, xcol: str, ycol: str):
    """P(warm) on a quantile grid, plus the count in each cell."""
    xq = np.unique(d[xcol].quantile(np.linspace(0, 1, NBINS + 1)).values)
    yq = np.unique(d[ycol].quantile(np.linspace(0, 1, NBINS + 1)).values)
    xi = np.clip(np.digitize(d[xcol], xq[1:-1]), 0, len(xq) - 2)
    yi = np.clip(np.digitize(d[ycol], yq[1:-1]), 0, len(yq) - 2)
    p = np.full((len(yq) - 1, len(xq) - 1), np.nan)
    n = np.zeros_like(p)
    for j in range(len(yq) - 1):
        for i in range(len(xq) - 1):
            m = (xi == i) & (yi == j)
            n[j, i] = m.sum()
            if m.sum() >= MIN_N:
                p[j, i] = d["warm"].to_numpy()[m].mean()
    return xq, yq, p, n


def marginal(d: pd.DataFrame, col: str):
    """P(warm) with Wilson 95% intervals, in equal-count bins of `col`."""
    edges = np.unique(d[col].quantile(np.linspace(0, 1, NDEC + 1)).values)
    idx = np.clip(np.digitize(d[col], edges[1:-1]), 0, len(edges) - 2)
    rows = []
    for i in range(len(edges) - 1):
        m = idx == i
        k, n = int(d["warm"].to_numpy()[m].sum()), int(m.sum())
        if n < 10:
            continue
        lo, hi = proportion_confint(k, n, 0.05, method="wilson")
        rows.append(dict(centre=float(d[col].to_numpy()[m].mean()),
                         k=k, n=n, p=k / n, lo=lo, hi=hi))
    return pd.DataFrame(rows)


def _logit_irls(X: np.ndarray, y: np.ndarray, tol=1e-10, maxit=100):
    """Logistic regression by iteratively reweighted least squares.

    Rolled by hand rather than taken from statsmodels: `statsmodels.api` does not
    import in this environment (it reaches for `scipy._lib._util._lazywhere`,
    removed in the installed scipy). Only the .stats submodules are usable, and
    they carry no GLM. IRLS is the same Newton-Raphson statsmodels would run.

    Returns (beta, standard errors) with the covariance from (X'WX)^-1.
    """
    beta = np.zeros(X.shape[1])
    for _ in range(maxit):
        eta = X @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        w = np.clip(p * (1 - p), 1e-9, None)
        XtW = X.T * w
        H = XtW @ X
        step = np.linalg.solve(H, X.T @ (y - p))
        beta = beta + step
        if np.max(np.abs(step)) < tol:
            break
    eta = X @ beta
    p = 1.0 / (1.0 + np.exp(-eta))
    w = np.clip(p * (1 - p), 1e-9, None)
    cov = np.linalg.inv((X.T * w) @ X)
    return beta, np.sqrt(np.diag(cov))


def logistic(d: pd.DataFrame, phase: str):
    """Odds ratio per standard deviation, Ca and Ck jointly."""
    sub = d[[f"Ca_{phase}", f"Ck_{phase}", "warm"]].dropna()
    Z = sub[[f"Ca_{phase}", f"Ck_{phase}"]]
    Z = (Z - Z.mean()) / Z.std()
    X = np.column_stack([np.ones(len(Z)), Z.values])
    beta, se = _logit_irls(X, sub["warm"].to_numpy(dtype=float))
    out = {}
    for i, term in enumerate(("Ca", "Ck"), start=1):
        z = beta[i] / se[i]
        out[term] = dict(or_=float(np.exp(beta[i])),
                         lo=float(np.exp(beta[i] - 1.959964 * se[i])),
                         hi=float(np.exp(beta[i] + 1.959964 * se[i])),
                         p=float(2 * norm.sf(abs(z))))
    return out, int(len(sub))


def main() -> int:
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    d = load()
    xcol, ycol = f"Ca_{PHASE}", f"Ck_{PHASE}"
    base = d["warm"].mean()

    print("=" * 72)
    print("EXPLORATORY: LEC conversions vs warm-core probability")
    print("=" * 72)
    print(f"\n{len(d):,} cyclones with both LEC terms and a CPS class")
    print(f"base rate P(persistent warm core) = {100 * base:.2f}%  "
          f"({int(d['warm'].sum())} of {len(d):,})")

    fig, axes = plt.subplots(2, 2, figsize=(13.6, 10.4))
    fig.subplots_adjust(left=0.075, right=0.965, top=0.855, bottom=0.115,
                        hspace=0.32, wspace=0.26)

    # ---------------- (a) 2-D probability map ----------------
    ax = axes[0, 0]
    xq, yq, p, n = binned_probability(d, xcol, ycol)
    # Drawn on a RANK axis, not on the physical one. Ca and Ck are strongly
    # skewed, so equal-count bins have wildly unequal widths and the cells
    # collapse into unreadable slivers on a linear axis. Every cell is given the
    # same size; the tick labels carry the real bin edges.
    vmax = np.nanmax(p)
    mesh = ax.pcolormesh(np.arange(len(xq)), np.arange(len(yq)), p * 100,
                         cmap="RdYlBu_r",
                         norm=TwoSlopeNorm(vmin=0, vcenter=base * 100,
                                           vmax=max(vmax * 100, base * 100 * 1.5)),
                         edgecolors="white", linewidth=0.8)
    for j in range(p.shape[0]):
        for i in range(p.shape[1]):
            if np.isnan(p[j, i]):
                ax.text(i + 0.5, j + 0.5, f"$n$={int(n[j, i])}", ha="center",
                        va="center", fontsize=7, color="0.55", style="italic")
                continue
            ax.text(i + 0.5, j + 0.5, f"{100 * p[j, i]:.1f}%\n$n$={int(n[j, i])}",
                    ha="center", va="center", fontsize=8.5, color="0.12")
    cb = fig.colorbar(mesh, ax=ax)
    cb.set_label("P(persistent warm core)  [%]", fontsize=10)
    ax.set_xticks(np.arange(len(xq)))
    ax.set_xticklabels([f"{v:.1f}" for v in xq], fontsize=8.5, rotation=45)
    ax.set_yticks(np.arange(len(yq)))
    ax.set_yticklabels([f"{v:.0f}" for v in yq], fontsize=8.5)
    # Where Ck changes sign, i.e. the barotropic-instability boundary.
    zero = float(np.interp(0.0, yq, np.arange(len(yq))))
    if 0 < zero < len(yq) - 1:
        ax.axhline(zero, color="0.2", lw=1.4, ls="--")
        ax.text(0.015, zero, " $C_k=0$", transform=ax.get_yaxis_transform(),
                fontsize=8.5, color="0.2", va="bottom")
    ax.set_xlabel(r"$C_a$  [W m$^{-2}$]  — baroclinic conversion", fontsize=11)
    ax.set_ylabel(r"$C_k$  [W m$^{-2}$]  — barotropic conversion", fontsize=11)
    ax.set_title("(a)   probability in the conversion plane\n"
                 f"equal-count bins (axes are bin edges), $n<${MIN_N} left blank",
                 fontsize=11, loc="left")

    # ---------------- (b) and (c) marginals ----------------
    for ax, col, lab, colour in [
            (axes[0, 1], xcol, r"$C_a$  [W m$^{-2}$]", "#1f4e9c"),
            (axes[1, 0], ycol, r"$C_k$  [W m$^{-2}$]", "#c0392b")]:
        m = marginal(d, col)
        ax.errorbar(m["centre"], m["p"] * 100,
                    yerr=[100 * (m["p"] - m["lo"]), 100 * (m["hi"] - m["p"])],
                    fmt="o-", color=colour, ms=7, lw=1.6, capsize=3.5)
        ax.axhline(base * 100, color="0.35", ls="--", lw=1.4)
        ax.text(0.985, base * 100, " all cyclones", transform=ax.get_yaxis_transform(),
                ha="right", va="bottom", fontsize=9, color="0.35")
        ax.set_xlabel(lab, fontsize=11)
        ax.set_ylabel("P(persistent warm core)  [%]", fontsize=11)
        ax.set_ylim(bottom=0)
        letter = "b" if col == xcol else "c"
        ax.set_title(f"({letter})   marginal on {lab.split('  ')[0]}, "
                     f"equal-count bins with Wilson 95% intervals",
                     fontsize=11, loc="left")
        ax.spines[["top", "right"]].set_visible(False)

    # ---------------- (d) logistic fit across phases ----------------
    ax = axes[1, 1]
    rows = []
    for k, ph in enumerate(["inc", "int", "mat", "dec"]):
        fit, nfit = logistic(d, ph)
        for term, colour, off in (("Ca", "#1f4e9c", -0.15), ("Ck", "#c0392b", 0.15)):
            f = fit[term]
            ax.errorbar(k + off, f["or_"],
                        yerr=[[f["or_"] - f["lo"]], [f["hi"] - f["or_"]]],
                        fmt="o", color=colour, ms=9, capsize=4, lw=2)
            rows.append(dict(phase=ph, term=term, n=nfit, odds_ratio=f["or_"],
                             ci_lo=f["lo"], ci_hi=f["hi"], p=f["p"]))
    ax.axhline(1.0, color="0.35", ls="--", lw=1.4)
    ax.set_yscale("log")
    ax.set_xticks(range(4))
    ax.set_xticklabels([PHASE_NAMES[p_] for p_ in ["inc", "int", "mat", "dec"]],
                       fontsize=10)
    ax.set_ylabel("odds ratio per 1 SD  (both terms in the model)", fontsize=11)
    ax.set_title("(d)   which term carries the signal, and is it stable in time?",
                 fontsize=11, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", ms=9, color=c, label=t)
                       for t, c in (("$C_a$ baroclinic", "#1f4e9c"),
                                    ("$C_k$ barotropic", "#c0392b"))],
              frameon=False, fontsize=10, loc="best")

    fig.text(0.5, 0.975, "Do the Lorenz conversions predict a warm core?",
             ha="center", va="top", fontsize=17, fontweight="bold")
    fig.text(0.5, 0.938,
             f"{len(d):,} cyclones · conversions from the "
             f"{PHASE_NAMES[PHASE]} phase · outcome = reaching a persistent "
             f"subtropical state (SC, ST or SD) under the canonical protocol",
             ha="center", va="top", fontsize=10.5, color="0.35")
    fig.text(0.5, 0.045,
             "EXPLORATORY, and NOT independent of the Energy Pattern result: the EPs were "
             "obtained by PCA + K-Means on these same conversion terms.\nThis is that result "
             "without the clustering step — useful for seeing which term carries the signal, "
             "not as confirmation of it.",
             ha="center", va="top", fontsize=9, color="0.45", style="italic",
             linespacing=1.6)

    fig.savefig(FIG_OUT, dpi=200, facecolor="white")
    plt.close(fig)

    summary = pd.DataFrame(rows)
    summary.to_csv(CSV_OUT, index=False)

    print("\nLogistic fit — odds ratio per 1 SD, both terms in the model:")
    for ph in ["inc", "int", "mat", "dec"]:
        s = summary[summary.phase == ph]
        bits = "   ".join(
            f"{r.term} OR={r.odds_ratio:.2f} [{r.ci_lo:.2f},{r.ci_hi:.2f}] p={r.p:.1e}"
            for r in s.itertuples())
        print(f"  {PHASE_NAMES[ph]:<16s} {bits}")

    print(f"\nWrote {FIG_OUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {CSV_OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
