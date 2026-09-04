#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Statistics of the Ck decomposition across Energy Patterns.

Answers, now for every Energy Pattern rather than EP1 alone:

1. Which subterm dominates the barotropic transfer in each EP and phase?
   Dominance = most negative phase mean, i.e. the largest contribution to the
   K_Z -> K_E transfer.
2. How large is each subterm, and what share of the total C_K does it carry?
3. Do the EPs differ significantly in each subterm, or is the decomposition
   essentially the same mechanism at different amplitudes?

Statistics
----------
The subterm distributions are strongly non-normal (heavy tails, sign changes),
so the tests are rank based and no normality is assumed:

* Kruskal-Wallis across EP1/EP2/EP3 per (subterm, phase);
* pairwise Mann-Whitney U for the EP contrasts, with the rank-biserial
  correlation as effect size (|r| < 0.1 negligible, < 0.3 small, < 0.5 medium);
* Benjamini-Hochberg FDR at q = 0.05 over all pairwise tests of a phase, so the
  multiplicity of 5 subterms x 3 contrasts is controlled.

EPALL (every cyclone pooled) is reported descriptively; it is not tested
against its own members.

Inputs
------
    results/ck_subterms_corrected/subterms_by_cyclone.csv   (step 1)

Outputs (results/ck_subterms_corrected/)
----------------------------------------
    subterm_statistics.csv     mean/median/IQR/share per EP, phase and subterm
    dominance_frequency.csv    share of cyclones each subterm dominates
    ep_contrasts.csv           Kruskal-Wallis and FDR-corrected pairwise tests
    statistics_report.md       readable summary of the three questions

Usage
-----
    python scripts/ck_subterms_analysis/step2_subterm_statistics.py

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import corrected_lec as clec  # noqa: E402
from scripts.utils import ep_mapping as em  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "results" / "ck_subterms_corrected"
INPUT_TABLE = RESULTS_DIR / "subterms_by_cyclone.csv"

FDR_ALPHA = 0.05


def descriptive_statistics(table: pd.DataFrame) -> pd.DataFrame:
    """Mean, median, spread and share per EP, phase and subterm."""
    records = []
    groups = [(label, group) for label, group in table.groupby("ep_label", observed=True)]
    groups.append((em.EPALL_LABEL, table))

    for ep_label, ep_frame in groups:
        for phase, phase_frame in ep_frame.groupby("phase", observed=True):
            total = phase_frame["Ck"]
            for stem in ["Ck", *clec.CK_SUBTERMS]:
                values = phase_frame[stem].dropna()
                if values.empty:
                    continue
                record = {
                    "ep_label": ep_label,
                    "phase": phase,
                    "term": stem,
                    "label": clec.CK_SUBTERM_LABELS.get(stem, "Ck_total"),
                    "n": int(values.size),
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "median": float(values.median()),
                    "q25": float(values.quantile(0.25)),
                    "q75": float(values.quantile(0.75)),
                    "units": "W m-2",
                }
                if stem != "Ck":
                    # Share of the ensemble-mean total, which is the quantity the
                    # manuscript reports. A per-cyclone share average would be
                    # dominated by cyclones whose total C_K is near zero.
                    record["share_of_mean_ck"] = float(values.mean() / total.mean())
                records.append(record)
    return pd.DataFrame(records)


def dominance_frequency(table: pd.DataFrame) -> pd.DataFrame:
    """How often each subterm is the dominant one, per EP and phase."""
    records = []
    groups = [(label, group) for label, group in table.groupby("ep_label", observed=True)]
    groups.append((em.EPALL_LABEL, table))

    for ep_label, ep_frame in groups:
        for phase, phase_frame in ep_frame.groupby("phase", observed=True):
            counts = phase_frame["dominant_label"].value_counts()
            total = int(counts.sum())
            for stem in clec.CK_SUBTERMS:
                label = clec.CK_SUBTERM_LABELS[stem]
                count = int(counts.get(label, 0))
                records.append({
                    "ep_label": ep_label,
                    "phase": phase,
                    "term": stem,
                    "label": label,
                    "n_dominant": count,
                    "n_total": total,
                    "fraction": count / total if total else np.nan,
                    "description": clec.CK_SUBTERM_DESCRIPTIONS[stem],
                })
    return pd.DataFrame(records)


def rank_biserial(first: np.ndarray, second: np.ndarray, u_statistic: float) -> float:
    """Rank-biserial correlation from a Mann-Whitney U statistic."""
    return float(2.0 * u_statistic / (first.size * second.size) - 1.0)


def ep_contrasts(table: pd.DataFrame) -> pd.DataFrame:
    """Kruskal-Wallis plus FDR-corrected pairwise Mann-Whitney per phase."""
    records = []
    for phase, phase_frame in table.groupby("phase", observed=True):
        samples = {
            label: group
            for label, group in phase_frame.groupby("ep_label", observed=True)
        }
        for stem in clec.CK_SUBTERMS:
            arrays = {
                label: group[stem].dropna().to_numpy()
                for label, group in samples.items()
            }
            arrays = {label: values for label, values in arrays.items() if values.size > 2}
            if len(arrays) < 2:
                continue

            kruskal = stats.kruskal(*arrays.values())
            for left, right in itertools.combinations(sorted(arrays), 2):
                first, second = arrays[left], arrays[right]
                u_statistic, p_value = stats.mannwhitneyu(
                    first, second, alternative="two-sided"
                )
                records.append({
                    "phase": phase,
                    "term": stem,
                    "label": clec.CK_SUBTERM_LABELS[stem],
                    "contrast": f"{left} vs {right}",
                    "n_left": int(first.size),
                    "n_right": int(second.size),
                    "median_left": float(np.median(first)),
                    "median_right": float(np.median(second)),
                    "kruskal_H": float(kruskal.statistic),
                    "kruskal_p": float(kruskal.pvalue),
                    "mannwhitney_U": float(u_statistic),
                    "p_raw": float(p_value),
                    "effect_size_r": rank_biserial(first, second, u_statistic),
                })

    frame = pd.DataFrame(records)
    if frame.empty:
        return frame

    # FDR within each phase: 5 subterms x 3 contrasts is the family.
    frame["p_fdr"] = np.nan
    for phase, index in frame.groupby("phase", observed=True).groups.items():
        rejected, corrected, _, _ = multipletests(
            frame.loc[index, "p_raw"], alpha=FDR_ALPHA, method="fdr_bh"
        )
        frame.loc[index, "p_fdr"] = corrected
        frame.loc[index, "significant"] = rejected

    frame["effect_magnitude"] = pd.cut(
        frame["effect_size_r"].abs(),
        bins=[-0.001, 0.1, 0.3, 0.5, 1.0],
        labels=["negligible", "small", "medium", "large"],
    )
    return frame


def write_report(
    descriptive: pd.DataFrame,
    dominance: pd.DataFrame,
    contrasts: pd.DataFrame,
    path: Path,
) -> Path:
    """Readable answer to the three research questions."""
    lines = [
        "# Ck subterms — statistics across Energy Patterns",
        "",
        f"Energy cache lineage: `{em.mapping_source()}`",
        "",
        "Sign convention: `C_K < 0` means K_Z -> K_E (the mean flow feeds the",
        "eddy). The dominant subterm is the most negative one.",
        "",
        "## 1. Intensification-phase magnitudes",
        "",
        "| Energy Pattern | term | mean (W m-2) | median | share of mean C_K |",
        "|---|---|---|---|---|",
    ]
    intensifying = descriptive[descriptive["phase"] == "intensification"]
    for _, row in intensifying.iterrows():
        share = row.get("share_of_mean_ck")
        share_text = "—" if pd.isna(share) else f"{100 * share:.1f}%"
        lines.append(
            f"| {row['ep_label']} | {row['label']} | {row['mean']:.3f} | "
            f"{row['median']:.3f} | {share_text} |"
        )

    lines += [
        "",
        "## 2. Dominance during intensification",
        "",
        "| Energy Pattern | " + " | ".join(
            clec.CK_SUBTERM_LABELS[stem] for stem in clec.CK_SUBTERMS
        ) + " |",
        "|---" * (len(clec.CK_SUBTERMS) + 1) + "|",
    ]
    intensifying_dominance = dominance[dominance["phase"] == "intensification"]
    for ep_label, group in intensifying_dominance.groupby("ep_label", observed=True):
        by_term = group.set_index("term")["fraction"]
        cells = [f"{100 * by_term.get(stem, 0):.1f}%" for stem in clec.CK_SUBTERMS]
        lines.append(f"| {ep_label} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## 3. Energy Pattern contrasts (intensification)",
        "",
        f"Benjamini-Hochberg FDR at q = {FDR_ALPHA}, family = all pairwise tests",
        "of the phase. Effect size is the rank-biserial correlation.",
        "",
        "| subterm | contrast | median left | median right | p (FDR) | effect | magnitude |",
        "|---|---|---|---|---|---|---|",
    ]
    if not contrasts.empty:
        intensifying_contrasts = contrasts[contrasts["phase"] == "intensification"]
        for _, row in intensifying_contrasts.iterrows():
            marker = "**" if row.get("significant") else ""
            lines.append(
                f"| {row['label']} | {row['contrast']} | {row['median_left']:.3f} | "
                f"{row['median_right']:.3f} | {marker}{row['p_fdr']:.3g}{marker} | "
                f"{row['effect_size_r']:+.3f} | {row['effect_magnitude']} |"
            )

    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> int:
    if not INPUT_TABLE.is_file():
        raise SystemExit(
            f"missing {INPUT_TABLE}\n"
            "Run scripts/ck_subterms_analysis/step1_build_subterms_table.py first."
        )
    table = pd.read_csv(INPUT_TABLE, dtype={"track_id": str})

    descriptive = descriptive_statistics(table)
    dominance = dominance_frequency(table)
    contrasts = ep_contrasts(table)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "subterm_statistics.csv": descriptive,
        "dominance_frequency.csv": dominance,
        "ep_contrasts.csv": contrasts,
    }
    for name, frame in outputs.items():
        frame.to_csv(RESULTS_DIR / name, index=False)
        print(f"  wrote results/ck_subterms_corrected/{name} ({len(frame)} rows)")

    report = write_report(descriptive, dominance, contrasts, RESULTS_DIR / "statistics_report.md")
    print(f"  wrote {report.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
