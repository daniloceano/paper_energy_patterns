"""
Step 3: Cross-tabulate cyclone thermal type (CPS) against Energy Pattern.

This is the preliminary question this analysis was built to answer: how many
tropical / subtropical / extratropical cyclones fall in each Energy Pattern?

The population is restricted to the 3,812 cyclones that carry BOTH a CPS series
and an EP label from the K-Means clustering on LEC diagnostics (of the 3,820
clustered cyclones, 8 have no CPS file).

Statistics
----------
A chi-square test of independence is run on each EP x type table, with Cramer's
V as the effect size. Pearson standardised residuals identify which cells drive
any departure from independence; |residual| > 2 is flagged as noteworthy. The
test is reported only when Cochran's condition holds (all expected counts >= 5,
or at most 20% of cells between 1 and 5).

Because the EP populations are very unequal (EP1 441, EP2 978, EP3 2,393),
counts are ALWAYS reported alongside within-EP percentages. Only the
percentages are comparable across EPs.

Two confounding controls are run:
  - region stratification (on `type_any`), because EP2 has a systematically
    more equatorward genesis distribution than EP1 and EP3;
  - genesis-band conditioning (on `type_strict`), because that rule gates on
    genesis latitude and the EPs draw unequally from the 20-40 S band. There
    Fisher's exact test replaces chi-square, the counts being single-digit.

Inputs:
    results/cps_analysis/cyclone_types.csv          (step 2)

Outputs:
    results/cps_analysis/ep_type_crosstab_<criterion>_<rule>.csv
    results/cps_analysis/ep_type_summary.csv
    results/cps_analysis/ep_type_statistics.txt
    figures/cps_analysis/ep_type_composition_<criterion>_<rule>.png
    figures/cps_analysis/ep_type_phase_space.png

Run:
    python scripts/cps_analysis/sensitivity/s2_ep_crosstab.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label
from scripts.cps_analysis.cps_criteria import (
    CRITERIA,
    CRITERIA_SOURCES,
    CLASS_PRECEDENCE,
    UNCLASSIFIED,
    MIN_PERSISTENCE_HOURS,
    MAX_ONSET_HOURS,
    PRIMARY_CRITERIA,
    CROSS_BASIN_CRITERIA,
    TYPE_COLORS,
    DEFAULT_CRITERION,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis" / "sensitivity"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis" / "sensitivity"
IN_FILE = RESULTS_DIR / "cyclone_types.csv"
OUT_SUMMARY = RESULTS_DIR / "ep_type_summary.csv"
OUT_STATS = RESULTS_DIR / "ep_type_statistics.txt"

RULES = ["type_any", "type_persistent", "type_protocol", "type_strict"]
TYPE_ORDER = CLASS_PRECEDENCE + [UNCLASSIFIED]

RULE_NOTES = {
    "type_any": "any single timestep",
    "type_persistent": f">= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours",
    "type_protocol": (f">= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours, over ocean, "
                      "genesis 20-40 S"),
    "type_strict": (f">= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours, over ocean, "
                    f"genesis 20-40 S, onset <= {MAX_ONSET_HOURS:.0f} h from genesis"),
}


def crosstab(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """EP x type counts, EP as rows in EP1/EP2/EP3 order."""
    table = pd.crosstab(df["ep"], df[column])
    table = table.reindex(index=ALL_EPS, columns=TYPE_ORDER, fill_value=0)
    table.index = [get_ep_label(ep) for ep in ALL_EPS]
    return table


def chi_square_report(table: pd.DataFrame) -> str:
    """Chi-square independence test with Cramer's V and standardised residuals."""
    used = table.loc[:, table.sum(axis=0) > 0]
    if used.shape[1] < 2:
        return "    only one populated type — test not applicable\n"

    chi2, p, dof, expected = chi2_contingency(used.values)
    n = used.values.sum()
    v = np.sqrt(chi2 / (n * (min(used.shape) - 1)))

    small = (expected < 5).sum()
    frac_small = small / expected.size
    lines = []
    if frac_small > 0.2 or (expected < 1).any():
        lines.append(f"    Cochran's condition VIOLATED ({small}/{expected.size} "
                     f"expected counts < 5) — chi-square unreliable")

    lines.append(f"    chi2 = {chi2:.2f}   dof = {dof}   p = {p:.3e}   "
                 f"Cramer's V = {v:.3f}   n = {n:,}")

    resid = (used.values - expected) / np.sqrt(expected)
    flagged = []
    for i, ep in enumerate(used.index):
        for j, col in enumerate(used.columns):
            if abs(resid[i, j]) > 2:
                direction = "more" if resid[i, j] > 0 else "fewer"
                flagged.append(
                    f"      {ep} x {col}: {used.values[i, j]:,} observed vs "
                    f"{expected[i, j]:.1f} expected ({direction} than chance, "
                    f"z = {resid[i, j]:+.1f})"
                )
    if flagged:
        lines.append("    cells driving the association (|z| > 2):")
        lines.extend(flagged)
    else:
        lines.append("    no individual cell with |z| > 2")

    return "\n".join(lines) + "\n"


def region_stratified_report(df: pd.DataFrame, criterion: str, rule: str) -> list:
    """Repeat the EP x type test inside each genesis region.

    EP2 has a systematically more equatorward genesis distribution than EP1 and
    EP3, and hybrid structure is a subtropical-latitude phenomenon, so any raw
    EP x type association is partly confounded by geography. Stratifying by
    genesis region (ARG, LA-PLATA, SE-BR) removes most of that confounding: an
    association that survives inside every region is not a geographic artefact.
    """
    lines = [f"\n  Region-stratified check ({rule}, {RULE_NOTES[rule]}):"]
    col = f"{criterion}_{rule}"

    for region in sorted(df["region"].dropna().unique()):
        sub = df[df["region"] == region]
        table = crosstab(sub, col)
        used = table.loc[:, table.sum(axis=0) > 0]
        if used.shape[1] < 2 or used.values.sum() == 0:
            continue
        pct = used.div(used.sum(axis=1), axis=0) * 100
        chi2, p, dof, expected = chi2_contingency(used.values)
        n = used.values.sum()
        v = np.sqrt(chi2 / (n * (min(used.shape) - 1)))
        lines.append(f"    {region:<9s} n = {n:5,d}   chi2 = {chi2:7.1f}   "
                     f"p = {p:.2e}   Cramer's V = {v:.3f}")
        for cls in CLASS_PRECEDENCE:
            if cls in pct.columns:
                vals = "  ".join(f"{ep}={pct.loc[ep, cls]:5.1f}%" for ep in pct.index)
                lines.append(f"      {cls:<14s} {vals}")
    return lines


def genesis_band_conditional(df: pd.DataFrame, criterion: str) -> list:
    """Strict-rule subtropical rate per EP, conditional on genesis in the band.

    The strict rule gates on genesis latitude (20-40 S), and the EPs draw very
    unequally from that band (EP1 44%, EP2 53%, EP3 38% of their populations).
    Comparing raw strict counts across EPs therefore mixes the structural
    signal with the geographic gate. Restricting to cyclones that pass the gate
    removes it, leaving a like-for-like comparison.

    Fisher's exact test is used rather than chi-square because the strict
    subtropical counts for EP1 and EP2 are single digits.
    """
    from scipy.stats import fisher_exact

    lines = ["\n  Genesis-band conditional analysis (strict rule, subtropical):"]
    band = df[df[f"{criterion}_genesis_lat_in_band"] == True]  # noqa: E712
    if band.empty:
        return lines + ["    no cyclones in the genesis band"]

    col = f"{criterion}_type_strict"
    counts = {}
    for ep in ALL_EPS:
        sub = band[band["ep"] == ep]
        n_st = int((sub[col] == "subtropical").sum())
        counts[ep] = (n_st, len(sub))
        pct = 100 * n_st / len(sub) if len(sub) else 0.0
        lines.append(f"    {get_ep_label(ep)}: {n_st:4,d} / {len(sub):5,d} "
                     f"in band  ({pct:5.2f}%)")

    # EP3 against the two high-conversion patterns pooled.
    a, na = counts[3]
    b = counts[1][0] + counts[2][0]
    nb = counts[1][1] + counts[2][1]
    if min(a, b, na - a, nb - b) >= 0 and na and nb:
        odds, p = fisher_exact([[a, na - a], [b, nb - b]])
        lines.append(f"    EP3 vs EP1+EP2 pooled: odds ratio = {odds:.2f}, "
                     f"Fisher exact p = {p:.3e}")

    # Onset timing is the mechanism behind whatever the rates show.
    lines.append("\n    Onset of the persistent hybrid run (hours after genesis, band only):")
    onset = pd.to_numeric(band[f"{criterion}_onset_subtropical"], errors="coerce")
    for ep in ALL_EPS:
        vals = onset[(band["ep"] == ep) & np.isfinite(onset)]
        if len(vals):
            lines.append(f"      {get_ep_label(ep)}: n = {len(vals):4,d}  "
                         f"median = {np.median(vals):5.0f} h  "
                         f"within {MAX_ONSET_HOURS:.0f} h = "
                         f"{100 * (vals <= MAX_ONSET_HOURS).mean():5.1f}%")
    return lines


def plot_composition(df: pd.DataFrame, criterion: str, rule: str, path: Path):
    """Stacked within-EP composition, plus the absolute counts as labels."""
    table = crosstab(df, f"{criterion}_{rule}")
    pct = table.div(table.sum(axis=1), axis=0) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))

    bottom = np.zeros(len(table))
    for cls in TYPE_ORDER:
        vals = pct[cls].values
        ax1.bar(table.index, vals, bottom=bottom, label=cls,
                color=TYPE_COLORS[cls], edgecolor="white", linewidth=0.8)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 3:
                ax1.text(i, b + v / 2, f"{v:.1f}%", ha="center", va="center",
                         fontsize=9, color="white", fontweight="bold")
        bottom += vals

    ax1.set_ylabel("Share of cyclones within the EP (%)")
    ax1.set_ylim(0, 100)
    ax1.set_title("Thermal-type composition of each Energy Pattern")
    ax1.legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
               bbox_to_anchor=(0.5, -0.06))

    # Absolute counts for the two non-extratropical classes, which are the
    # scientifically interesting ones and invisible on a percentage plot.
    width = 0.35
    x = np.arange(len(table))
    for k, cls in enumerate(["tropical", "subtropical"]):
        ax2.bar(x + (k - 0.5) * width, table[cls].values, width,
                color=TYPE_COLORS[cls], label=cls, edgecolor="white")
        for xi, val in zip(x + (k - 0.5) * width, table[cls].values):
            ax2.text(xi, val, f"{val:,}", ha="center", va="bottom", fontsize=9)

    ax2.set_xticks(x)
    ax2.set_xticklabels(table.index)
    ax2.set_ylabel("Number of cyclones")
    ax2.set_title("Tropical and subtropical counts")
    ax2.legend(frameon=False, fontsize=9)

    note = RULE_NOTES[rule]
    fig.suptitle(f"CPS thermal type by Energy Pattern — {criterion} ({note})",
                 fontsize=13, fontweight="bold")
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


def plot_phase_space(path: Path):
    """Population density in the two CPS planes, split by EP.

    Reads the classified timestep table so the thresholds can be drawn on top
    of the actual sample the classification acted on.
    """
    ts_file = RESULTS_DIR / "cps_timesteps_classified.csv"
    if not ts_file.exists():
        return False

    df = pd.read_csv(ts_file, usecols=["ep", "B", "VTL", "VTU"])
    df = df.dropna(subset=["ep", "B", "VTL", "VTU"])

    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), sharex=True)
    for col, ep in enumerate(ALL_EPS):
        sub = df[df["ep"] == ep]

        ax = axes[0, col]
        ax.hexbin(sub["VTL"], sub["B"], gridsize=45, bins="log", cmap="Greys",
                  mincnt=1, extent=(-700, 400, -120, 170))
        ax.axhline(10, color=TYPE_COLORS["extratropical"], lw=1, ls="--")
        ax.axhline(25, color=TYPE_COLORS["subtropical"], lw=1, ls=":")
        ax.axvline(0, color="k", lw=0.8)
        ax.set_title(f"{get_ep_label(ep)}  (n = {sub['ep'].size:,} timesteps)",
                     color=EP_COLORS[ep], fontweight="bold")
        if col == 0:
            ax.set_ylabel("B  [m]")

        ax = axes[1, col]
        ax.hexbin(sub["VTL"], sub["VTU"], gridsize=45, bins="log", cmap="Greys",
                  mincnt=1, extent=(-700, 400, -700, 300))
        ax.axhline(0, color="k", lw=0.8)
        ax.axhline(-10, color=TYPE_COLORS["subtropical"], lw=1, ls=":")
        ax.axhline(-50, color=TYPE_COLORS["tropical"], lw=1, ls="-.")
        ax.axvline(0, color="k", lw=0.8)
        ax.set_xlabel(r"$-V_T^L$  [900-600 hPa]")
        if col == 0:
            ax.set_ylabel(r"$-V_T^U$  [600-300 hPa]")

    fig.suptitle("CPS occupancy by Energy Pattern (all classifiable timesteps)\n"
                 "dashed: B = 10 m (frontal) · dotted: B = 25 m and "
                 r"$-V_T^U=-10$ (Gozzo subtropical) · dash-dot: $-V_T^U=-50$ (C03 tropical)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return True


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 2: Energy Pattern x CPS thermal type")
    print("=" * 70)

    if not IN_FILE.exists():
        print(f"Missing {IN_FILE}. Run step 2 first.")
        return 1

    cyclones = pd.read_csv(IN_FILE)
    total = len(cyclones)
    df = cyclones[cyclones["ep"].notna()].copy()
    df["ep"] = df["ep"].astype(int)

    print(f"\nPopulation: {len(df):,} EP-labelled cyclones "
          f"(of {total:,} with a CPS series)")
    for ep in ALL_EPS:
        print(f"  {get_ep_label(ep)}: {(df['ep'] == ep).sum():5,d}")

    stats_lines = []
    summary_rows = []

    for criterion in CRITERIA:
        header = f"\n{'=' * 70}\n{criterion}  [{CRITERIA_SOURCES[criterion]}]\n{'=' * 70}"
        print(header)
        stats_lines.append(header)

        for rule in RULES:
            col = f"{criterion}_{rule}"
            table = crosstab(df, col)
            pct = table.div(table.sum(axis=1), axis=0) * 100

            note = RULE_NOTES[rule]
            block = [f"\n  {rule}  ({note})", "", table.to_string(),
                     "", "  within-EP percentages:", pct.round(1).to_string()]
            print("\n".join(block))
            stats_lines.extend(block)

            report = chi_square_report(table)
            print(report)
            stats_lines.append(report)

            if rule == "type_any":
                strat = region_stratified_report(df, criterion, rule)
                print("\n".join(strat))
                stats_lines.extend(strat)

            if rule == "type_strict":
                cond = genesis_band_conditional(df, criterion)
                print("\n".join(cond))
                stats_lines.extend(cond)

            out = RESULTS_DIR / f"ep_type_crosstab_{criterion}_{rule}.csv"
            table.to_csv(out)

            for ep_label in table.index:
                for cls in TYPE_ORDER:
                    summary_rows.append({
                        "criterion": criterion,
                        "rule": rule,
                        "ep": ep_label,
                        "type": cls,
                        "n_cyclones": int(table.loc[ep_label, cls]),
                        "pct_within_ep": round(float(pct.loc[ep_label, cls]), 2),
                    })


    pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY, index=False)
    print(f"\n\nWrote {OUT_SUMMARY.relative_to(PROJECT_ROOT)}")

    with open(OUT_STATS, "w") as fh:
        fh.write("Energy Pattern x CPS thermal type — contingency analysis\n")
        fh.write(f"Population: {len(df):,} EP-labelled cyclones\n")
        fh.write("\n".join(stats_lines) + "\n")
    print(f"Wrote {OUT_STATS.relative_to(PROJECT_ROOT)}")

    # --- Figures --------------------------------------------------------------
    print("\nGenerating figures ...")
    for rule in RULES:
        path = FIG_DIR / f"ep_type_composition_{DEFAULT_CRITERION}_{rule}.png"
        plot_composition(df, DEFAULT_CRITERION, rule, path)
        print(f"  {path.relative_to(PROJECT_ROOT)}")

    path = FIG_DIR / "ep_type_phase_space.png"
    if plot_phase_space(path):
        print(f"  {path.relative_to(PROJECT_ROOT)}")

    print("\nStep 2 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
