"""
Step 3 (CANONICAL): Energy Pattern x phase class.

Cross-tabulates the canonical phase classification (step 2) against the Energy
Patterns from the K-Means clustering on LEC diagnostics, with the confounding
controls established in the sensitivity work.

Statistics
----------
Chi-square with Cramer's V and Pearson standardised residuals on the full
EP x class table. Where a class has single-digit counts (TC, SD) Fisher's exact
test is used instead for the specific contrast of interest.

Two controls:
  * region stratification - EP2 has a systematically more equatorward genesis
    distribution (median -37.9 deg vs -42.1 for EP1 and -44.0 for EP3), and
    hybrid structure is a subtropical-latitude phenomenon;
  * the `indeterminate` class is split into "too short-lived to classify"
    (lifetime below the 36 h persistence gate plus a classifiable genesis) and
    "structurally ambiguous" (long-lived but never holding one state), because
    the first is a mechanical consequence of the gate and the second is a
    physical statement.

Inputs:
    results/cps_analysis/phase_classification.csv   (step 2)
    results/cps_analysis/phase_timesteps.csv        (step 2)

Outputs:
    results/cps_analysis/ep_phase_crosstab.csv
    results/cps_analysis/ep_phase_summary.csv
    results/cps_analysis/ep_phase_statistics.txt

Run:
    python scripts/cps_analysis/step3_ep_phases.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

from scripts.utils.ep_mapping import ALL_EPS, get_ep_label
from scripts.cps_analysis.cps_criteria import (
    SINGLE_STATE_CLASSES,
    TRANSITIONS,
    TRANSITION_PRECEDENCE,
    INDETERMINATE,
    CHARACTERISTIC_CLASSES,
    UNDETERMINED,
    MIN_PERSISTENCE_HOURS,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
CLASS_FILE = RESULTS_DIR / "phase_classification.csv"
TS_FILE = RESULTS_DIR / "phase_timesteps.csv"

OUT_CROSSTAB = RESULTS_DIR / "ep_phase_crosstab.csv"
OUT_SUMMARY = RESULTS_DIR / "ep_phase_summary.csv"
OUT_STATS = RESULTS_DIR / "ep_phase_statistics.txt"

CLASS_ORDER = (list(SINGLE_STATE_CLASSES) + TRANSITION_PRECEDENCE
               + list(CHARACTERISTIC_CLASSES) + [UNDETERMINED])

# A cyclone shorter than this cannot hold any state for the 36 h persistence
# gate once the unclassifiable genesis timestep is accounted for, so its
# `indeterminate` label carries no structural information.
MIN_CLASSIFIABLE_LIFETIME_H = MIN_PERSISTENCE_HOURS + 3.0


def crosstab(df: pd.DataFrame, column: str = "phase_class") -> pd.DataFrame:
    t = pd.crosstab(df["ep"], df[column])
    t = t.reindex(index=ALL_EPS, columns=CLASS_ORDER, fill_value=0)
    t.index = [get_ep_label(e) for e in ALL_EPS]
    return t


def chi_square_report(table: pd.DataFrame, indent: str = "    ") -> list:
    used = table.loc[:, table.sum(axis=0) > 0]
    if used.shape[1] < 2:
        return [f"{indent}only one populated class — test not applicable"]

    chi2, p, dof, expected = chi2_contingency(used.values)
    n = used.values.sum()
    v = np.sqrt(chi2 / (n * (min(used.shape) - 1)))
    lines = []
    small = int((expected < 5).sum())
    if small / expected.size > 0.2 or (expected < 1).any():
        lines.append(f"{indent}Cochran's condition VIOLATED "
                     f"({small}/{expected.size} expected < 5) — chi-square unreliable")
    lines.append(f"{indent}chi2 = {chi2:.2f}  dof = {dof}  p = {p:.3e}  "
                 f"Cramer's V = {v:.3f}  n = {n:,}")

    resid = (used.values - expected) / np.sqrt(expected)
    flagged = [
        f"{indent}  {ep} x {col}: {used.values[i, j]:,} obs vs {expected[i, j]:.1f} exp "
        f"(z = {resid[i, j]:+.1f})"
        for i, ep in enumerate(used.index) for j, col in enumerate(used.columns)
        if abs(resid[i, j]) > 2
    ]
    lines.append(f"{indent}cells with |z| > 2:" if flagged
                 else f"{indent}no cell with |z| > 2")
    lines.extend(flagged)
    return lines


def fisher_contrast(df: pd.DataFrame, flag: pd.Series, label: str) -> list:
    """Each EP against the other two pooled, on a binary outcome."""
    lines = [f"    {label} — each EP vs the other two pooled (Fisher exact):"]
    for ep in ALL_EPS:
        a = int(flag[df["ep"] == ep].sum())
        na = int((df["ep"] == ep).sum())
        b = int(flag[df["ep"] != ep].sum())
        nb = int((df["ep"] != ep).sum())
        if min(na, nb) == 0:
            continue
        odds, p = fisher_exact([[a, na - a], [b, nb - b]])
        star = " *" if p < 0.05 else ""
        lines.append(f"      {get_ep_label(ep)}: {a:4,d}/{na:5,d} ({100*a/na:5.2f}%)  "
                     f"vs {b:4,d}/{nb:5,d} ({100*b/nb:5.2f}%)   "
                     f"OR = {odds:5.2f}  p = {p:.3e}{star}")
    return lines


def main():
    print("=" * 70)
    print("STEP 3 (CANONICAL): Energy Pattern x phase class")
    print("=" * 70)

    for f in (CLASS_FILE, TS_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    cy = pd.read_csv(CLASS_FILE)
    ts = pd.read_csv(TS_FILE, parse_dates=["datetime"], usecols=["track_id", "datetime"])
    life = (ts.groupby("track_id")["datetime"].max()
            - ts.groupby("track_id")["datetime"].min()).dt.total_seconds() / 3600
    cy["lifetime_h"] = cy["track_id"].map(life)

    # The old indeterminate/too-short split is superseded by the characteristic
    # classes, which say what the cyclone showed. What remains worth flagging is
    # whether it was simply too short-lived to reach the 36 h gate at all.
    cy["too_short"] = cy["lifetime_h"] < MIN_CLASSIFIABLE_LIFETIME_H

    df = cy[cy["ep"].notna()].copy()
    df["ep"] = df["ep"].astype(int)

    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit(f"\nPopulation: {len(df):,} EP-labelled cyclones "
         f"(of {len(cy):,} classified)")
    for ep in ALL_EPS:
        emit(f"  {get_ep_label(ep)}: {(df['ep'] == ep).sum():5,d}")

    # ------------------------------------------------------------------
    emit("\n" + "=" * 70)
    emit("EP x PHASE CLASS")
    emit("=" * 70)
    table = crosstab(df)
    pct = table.div(table.sum(axis=1), axis=0) * 100
    emit("\n" + table.to_string())
    emit("\nwithin-EP percentages:")
    emit(pct.round(1).to_string())
    emit("")
    for l in chi_square_report(table):
        emit(l)
    table.to_csv(OUT_CROSSTAB)

    # ------------------------------------------------------------------
    emit("\n" + "-" * 70)
    emit("TRANSITION RATES (not mutually exclusive)")
    emit("-" * 70)
    for t in TRANSITION_PRECEDENCE:
        col = f"has_{t}"
        if col not in df or df[col].sum() == 0:
            emit(f"\n  {t}: none in the population")
            continue
        emit(f"\n  {t} — {TRANSITIONS[t]}")
        for l in fisher_contrast(df, df[col].astype(bool), t):
            emit(l)

    # ------------------------------------------------------------------
    emit("\n" + "-" * 70)
    emit("HYBRID PROPENSITY  (pure SC or any ST — 'the system was subtropical')")
    emit("-" * 70)
    hybrid = df["phase_class"].isin(["SC"]) | df["has_ST"].astype(bool)
    for l in fisher_contrast(df, hybrid, "subtropical at some persistent stage"):
        emit(l)

    # ------------------------------------------------------------------
    emit("\n" + "-" * 70)
    emit("REGION-STRATIFIED CONTROL")
    emit("-" * 70)
    emit("  EP2 forms further equatorward than EP1/EP3, and hybrid structure is a")
    emit("  subtropical-latitude phenomenon. An association that survives inside")
    emit("  each genesis region is not a geographic artefact.")
    for region in sorted(df["region"].dropna().unique()):
        sub = df[df["region"] == region]
        emit(f"\n  {region}  (n = {len(sub):,})")
        t = crosstab(sub)
        p = t.div(t.sum(axis=1), axis=0) * 100
        for cls in ["SC", "ST"]:
            if cls in p.columns:
                vals = "  ".join(f"{ep}={p.loc[ep, cls]:5.1f}%" for ep in p.index)
                emit(f"    {cls:<4s} {vals}")
        for l in chi_square_report(t, indent="      "):
            emit(l)

    # ------------------------------------------------------------------
    emit("\n" + "-" * 70)
    emit("CHARACTERISTIC CLASSES  (structure shown, but never sustained 36 h)")
    emit("-" * 70)
    emit("  These describe characteristics, not identifications: the 36 h requirement")
    emit("  of Guishard et al. (2009) and Gozzo et al. (2014) is untouched for the")
    emit("  named classes. A cyclone here is NOT being called subtropical, only")
    emit("  'showing hybrid characteristics'.")
    for code, desc in CHARACTERISTIC_CLASSES.items():
        sub = df[df["phase_class"] == code]
        if sub.empty:
            continue
        emit(f"\n  {code} — {desc}")
        for ep in ALL_EPS:
            n = int(((df["ep"] == ep) & (df["phase_class"] == code)).sum())
            tot = int((df["ep"] == ep).sum())
            emit(f"    {get_ep_label(ep)}: {n:5,d} / {tot:,}  ({100*n/tot:.1f}%)")
    n_short = int((df["too_short"] & df["phase_class"].isin(
        list(CHARACTERISTIC_CLASSES) + [UNDETERMINED])).sum())
    emit(f"\n  Of these, {n_short:,} are simply shorter than "
         f"{MIN_CLASSIFIABLE_LIFETIME_H:.0f} h and could not have reached the gate.")
    med = df.groupby("phase_class")["lifetime_h"].median().sort_values()
    emit("\n  median lifetime by phase class [h]:")
    for k, v in med.items():
        emit(f"    {k:<16s} {v:6.0f}")

    # ------------------------------------------------------------------
    rows = []
    for ep_label in table.index:
        for cls in CLASS_ORDER:
            rows.append({"ep": ep_label, "phase_class": cls,
                         "n_cyclones": int(table.loc[ep_label, cls]),
                         "pct_within_ep": round(float(pct.loc[ep_label, cls]), 2)})
    pd.DataFrame(rows).to_csv(OUT_SUMMARY, index=False)

    with open(OUT_STATS, "w") as fh:
        fh.write("Energy Pattern x canonical phase class\n")
        fh.write("\n".join(lines) + "\n")

    print(f"\nWrote {OUT_CROSSTAB.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUT_SUMMARY.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUT_STATS.relative_to(PROJECT_ROOT)}")
    print("\nStep 3 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
