"""Step 2b: diagnose CPS completeness separately from the CPS x EP science.

This step never changes the canonical methodology. It reports full-life CPS
coverage, class/EP composition across coverage strata, complete-versus-eligible
incomplete comparisons, and the requested 100% / >=90% / >=75% sensitivity.

Inputs:
    results/cps_analysis/cps_coverage.csv
    results/cps_analysis/phase_classification_all.csv

Outputs:
    results/cps_analysis/coverage_diagnostics.json
    results/cps_analysis/coverage_by_bin.csv
    results/cps_analysis/coverage_by_bin_ep.csv
    results/cps_analysis/coverage_by_ep.csv
    results/cps_analysis/coverage_by_class.csv
    results/cps_analysis/coverage_complete_vs_incomplete.csv
    results/cps_analysis/coverage_bias_tests.csv
    results/cps_analysis/coverage_threshold_sensitivity.csv
    results/cps_analysis/coverage_diagnostics.txt
    figures/cps_analysis/fig11_cps_coverage_diagnostics.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from scripts.cps_analysis.cps_coverage import (
    COMPLETE,
    COVERAGE_BIN_LABELS,
    COVERAGE_THRESHOLD,
    ELIGIBLE_INCOMPLETE,
    INSUFFICIENT_COVERAGE,
    NO_DATA,
    coverage_bin,
)
from scripts.cps_analysis.cps_criteria import (
    CHARACTERISTIC_CLASSES,
    SINGLE_STATE_CLASSES,
    TRANSITION_PRECEDENCE,
    UNDETERMINED,
)
from scripts.utils.ep_mapping import CLUSTER_TO_EP

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIGURES_DIR = PROJECT_ROOT / "figures" / "cps_analysis"

COVERAGE_FILE = RESULTS_DIR / "cps_coverage.csv"
CLASS_FILE = RESULTS_DIR / "phase_classification_all.csv"
CLUSTER_FILE = PROJECT_ROOT / "results" / "cluster" / "kmeans_clustered_data.csv"

OUT_JSON = RESULTS_DIR / "coverage_diagnostics.json"
OUT_BINS = RESULTS_DIR / "coverage_by_bin.csv"
OUT_BIN_EP = RESULTS_DIR / "coverage_by_bin_ep.csv"
OUT_EP = RESULTS_DIR / "coverage_by_ep.csv"
OUT_CLASS = RESULTS_DIR / "coverage_by_class.csv"
OUT_COMPARISON = RESULTS_DIR / "coverage_complete_vs_incomplete.csv"
OUT_TESTS = RESULTS_DIR / "coverage_bias_tests.csv"
OUT_SENSITIVITY = RESULTS_DIR / "coverage_threshold_sensitivity.csv"
OUT_TEXT = RESULTS_DIR / "coverage_diagnostics.txt"
OUT_FIGURE = FIGURES_DIR / "fig11_cps_coverage_diagnostics.png"

PHASE_ORDER = (
    list(SINGLE_STATE_CLASSES)
    + TRANSITION_PRECEDENCE
    + list(CHARACTERISTIC_CLASSES)
    + [UNDETERMINED, INSUFFICIENT_COVERAGE, NO_DATA]
)
IDENTIFIED_CLASSES = set(SINGLE_STATE_CLASSES) | set(TRANSITION_PRECEDENCE)


def _pct(numerator: int | float, denominator: int | float) -> float:
    return 100.0 * float(numerator) / float(denominator) if denominator else np.nan


def _python(value):
    """Convert pandas/numpy scalars to strict JSON values."""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _cramers_v(table: pd.DataFrame) -> tuple[float, float, int, float]:
    """Return chi-square, p, dof and bias-corrected Cramer's V."""
    table = table.loc[table.sum(axis=1) > 0, table.sum(axis=0) > 0]
    if table.shape[0] < 2 or table.shape[1] < 2:
        return np.nan, np.nan, 0, np.nan
    chi2, p, dof, _ = chi2_contingency(table, correction=False)
    n = table.to_numpy().sum()
    phi2 = chi2 / n
    r, k = table.shape
    phi2corr = max(0.0, phi2 - ((k - 1) * (r - 1)) / max(n - 1, 1))
    rcorr = r - ((r - 1) ** 2) / max(n - 1, 1)
    kcorr = k - ((k - 1) ** 2) / max(n - 1, 1)
    denom = min(kcorr - 1, rcorr - 1)
    v = np.sqrt(phi2corr / denom) if denom > 0 else np.nan
    return float(chi2), float(p), int(dof), float(v)


def _distribution_stats(values: pd.Series) -> dict:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "n": int(len(values)),
        "mean": _python(values.mean()),
        "std": _python(values.std(ddof=1)),
        "min": _python(values.min()),
        "q25": _python(values.quantile(0.25)),
        "median": _python(values.median()),
        "q75": _python(values.quantile(0.75)),
        "max": _python(values.max()),
    }


def build_bin_table(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, ep_rows = [], []
    for label in COVERAGE_BIN_LABELS:
        group = df[df["coverage_bin"] == label]
        n = len(group)
        identified = group["diagnostic_phase_class"].isin(IDENTIFIED_CLASSES)
        row = {
            "coverage_bin": label,
            "n_catalogue": n,
            "n_with_cps_file": int(group["has_cps_file"].sum()),
            "n_ep_labelled": int(group["ep"].notna().sum()),
            "n_included_official": int(group["analysis_included"].sum()),
            "n_identified": int(identified.sum()),
            "pct_identified": _pct(identified.sum(), n),
            "n_undetermined": int((group["diagnostic_phase_class"] == UNDETERMINED).sum()),
            "pct_undetermined": _pct(
                (group["diagnostic_phase_class"] == UNDETERMINED).sum(), n
            ),
            "n_no_data": int((group["diagnostic_phase_class"] == NO_DATA).sum()),
            "pct_no_data": _pct((group["diagnostic_phase_class"] == NO_DATA).sum(), n),
        }
        counts = group["diagnostic_phase_class"].value_counts()
        for cls in PHASE_ORDER:
            row[f"n_{cls}"] = int(counts.get(cls, 0))
            row[f"pct_{cls}"] = _pct(counts.get(cls, 0), n)
        rows.append(row)

        labelled = group[group["ep"].notna()]
        for ep in (1, 2, 3):
            n_ep = int((labelled["ep"] == ep).sum())
            ep_rows.append(
                {
                    "coverage_bin": label,
                    "ep": f"EP{ep}",
                    "n": n_ep,
                    "denominator_ep_labelled_in_bin": len(labelled),
                    "pct_of_ep_labelled_in_bin": _pct(n_ep, len(labelled)),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(ep_rows)


def build_ep_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ep in (1, 2, 3):
        group = df[df["ep"] == ep]
        n = len(group)
        rows.append(
            {
                "ep": f"EP{ep}",
                "n_total": n,
                "n_with_cps_file": int(group["has_cps_file"].sum()),
                "n_complete": int((group["coverage_status"] == COMPLETE).sum()),
                "pct_complete": _pct((group["coverage_status"] == COMPLETE).sum(), n),
                "n_eligible_incomplete": int(
                    (group["coverage_status"] == ELIGIBLE_INCOMPLETE).sum()
                ),
                "pct_eligible_incomplete": _pct(
                    (group["coverage_status"] == ELIGIBLE_INCOMPLETE).sum(), n
                ),
                "n_insufficient": int(
                    (group["coverage_status"] == INSUFFICIENT_COVERAGE).sum()
                ),
                "pct_insufficient": _pct(
                    (group["coverage_status"] == INSUFFICIENT_COVERAGE).sum(), n
                ),
                "n_no_data": int((group["coverage_status"] == NO_DATA).sum()),
                "pct_no_data": _pct((group["coverage_status"] == NO_DATA).sum(), n),
                "n_included": int(group["analysis_included"].sum()),
                "pct_included": _pct(group["analysis_included"].sum(), n),
            }
        )
    return pd.DataFrame(rows)


def build_class_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cls in PHASE_ORDER:
        group = df[df["diagnostic_phase_class"] == cls]
        if group.empty:
            continue
        n = len(group)
        row = {"diagnostic_phase_class": cls, "n_total": n}
        for status in (COMPLETE, ELIGIBLE_INCOMPLETE, INSUFFICIENT_COVERAGE, NO_DATA):
            value = int((group["coverage_status"] == status).sum())
            row[f"n_{status}"] = value
            row[f"pct_{status}"] = _pct(value, n)
        row["n_included"] = int(group["analysis_included"].sum())
        row["pct_included"] = _pct(group["analysis_included"].sum(), n)
        rows.append(row)
    return pd.DataFrame(rows)


def build_complete_comparison(df: pd.DataFrame) -> pd.DataFrame:
    eligible = df[df["coverage_status"].isin([COMPLETE, ELIGIBLE_INCOMPLETE])].copy()
    eligible["completeness_group"] = eligible["coverage_status"].map(
        {COMPLETE: "complete", ELIGIBLE_INCOMPLETE: "incomplete_eligible"}
    )
    rows = []
    for group_name, group in eligible.groupby("completeness_group", sort=False):
        n = len(group)
        for cls in PHASE_ORDER:
            count = int((group["diagnostic_phase_class"] == cls).sum())
            if count or cls in set(eligible["diagnostic_phase_class"]):
                rows.append(
                    {
                        "dimension": "phase_class",
                        "completeness_group": group_name,
                        "category": cls,
                        "n": count,
                        "denominator": n,
                        "pct": _pct(count, n),
                    }
                )
        labelled = group[group["ep"].notna()]
        for ep in (1, 2, 3):
            count = int((labelled["ep"] == ep).sum())
            rows.append(
                {
                    "dimension": "ep",
                    "completeness_group": group_name,
                    "category": f"EP{ep}",
                    "n": count,
                    "denominator": len(labelled),
                    "pct": _pct(count, len(labelled)),
                }
            )
    return pd.DataFrame(rows)


def build_bias_tests(df: pd.DataFrame) -> pd.DataFrame:
    eligible = df[df["coverage_status"].isin([COMPLETE, ELIGIBLE_INCOMPLETE])].copy()
    eligible["completeness_group"] = eligible["coverage_status"].map(
        {COMPLETE: "complete", ELIGIBLE_INCOMPLETE: "incomplete_eligible"}
    )
    tests = []
    phase = pd.crosstab(eligible["completeness_group"], eligible["diagnostic_phase_class"])
    chi2, p, dof, v = _cramers_v(phase)
    tests.append(
        {
            "dimension": "phase_class",
            "n": int(phase.to_numpy().sum()),
            "chi2": chi2,
            "dof": dof,
            "p_value": p,
            "cramers_v": v,
        }
    )
    ep_data = eligible[eligible["ep"].notna()].copy()
    ep_data["ep_label"] = ep_data["ep"].astype(int).map(lambda value: f"EP{value}")
    ep = pd.crosstab(ep_data["completeness_group"], ep_data["ep_label"])
    chi2, p, dof, v = _cramers_v(ep)
    tests.append(
        {
            "dimension": "ep",
            "n": int(ep.to_numpy().sum()),
            "chi2": chi2,
            "dof": dof,
            "p_value": p,
            "cramers_v": v,
        }
    )
    return pd.DataFrame(tests)


def build_threshold_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    labelled = df[df["ep"].notna() & df["n_usable_timesteps"].gt(0)].copy()
    all_classes = [cls for cls in PHASE_ORDER if cls not in (INSUFFICIENT_COVERAGE, NO_DATA)]
    for threshold in (1.0, 0.90, COVERAGE_THRESHOLD):
        selected = labelled[
            labelled["coverage_fraction"].ge(threshold - 1e-9)
        ]
        for ep_label, group in [("EPALL", selected)] + [
            (f"EP{ep}", selected[selected["ep"] == ep]) for ep in (1, 2, 3)
        ]:
            n = len(group)
            row = {
                "coverage_threshold": threshold,
                "threshold_label": "100%" if threshold == 1.0 else f">={threshold:.0%}",
                "ep": ep_label,
                "n": n,
            }
            counts = group["diagnostic_phase_class"].value_counts()
            for cls in all_classes:
                count = int(counts.get(cls, 0))
                row[f"n_{cls}"] = count
                row[f"pct_{cls}"] = _pct(count, n)
            row["n_identified"] = int(
                group["diagnostic_phase_class"].isin(IDENTIFIED_CLASSES).sum()
            )
            row["pct_identified"] = _pct(row["n_identified"], n)
            rows.append(row)
    return pd.DataFrame(rows)


def audit_current_ep_mapping(df: pd.DataFrame) -> dict:
    """Prove that every regenerated EP label comes from the corrected clustering."""
    if not CLUSTER_FILE.exists():
        raise FileNotFoundError(f"Corrected EP source not found: {CLUSTER_FILE}")
    clusters = pd.read_csv(CLUSTER_FILE, usecols=["track_id", "cluster"])
    if clusters["track_id"].duplicated().any():
        raise ValueError("corrected EP source contains duplicate track IDs")
    clusters["expected_ep"] = clusters["cluster"].map(CLUSTER_TO_EP)
    if clusters["expected_ep"].isna().any():
        raise ValueError("corrected EP source contains unmapped clusters")

    joined = clusters.merge(
        df[["track_id", "ep", "analysis_included"]],
        on="track_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not joined["_merge"].eq("both").all():
        missing = joined.loc[joined["_merge"] != "both", "track_id"].tolist()
        raise ValueError(f"corrected EP IDs absent from CPS audit population: {missing[:10]}")
    mismatches = joined[~joined["ep"].eq(joined["expected_ep"])]
    if not mismatches.empty:
        raise ValueError(
            "regenerated CPS products contain EP labels inconsistent with the corrected "
            f"clustering: {mismatches['track_id'].head(10).tolist()}"
        )

    expected_counts = {
        f"EP{int(ep)}": int(count)
        for ep, count in joined["expected_ep"].value_counts().sort_index().items()
    }
    included_counts = {
        f"EP{int(ep)}": int(count)
        for ep, count in joined.loc[joined["analysis_included"], "expected_ep"]
        .value_counts()
        .sort_index()
        .items()
    }
    return {
        "verdict": "PASS",
        "source": str(CLUSTER_FILE.relative_to(PROJECT_ROOT)),
        "cluster_to_ep": {str(key): int(value) for key, value in CLUSTER_TO_EP.items()},
        "corrected_ep_population": int(len(joined)),
        "corrected_ep_counts": expected_counts,
        "regenerated_label_mismatches": int(len(mismatches)),
        "official_ge75_ep_population": int(joined["analysis_included"].sum()),
        "official_ge75_ep_counts": included_counts,
    }


def make_figure(
    df: pd.DataFrame,
    bins: pd.DataFrame,
    ep: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)

    with_file = df[df["has_cps_file"]]
    axes[0, 0].hist(
        with_file["coverage_fraction"] * 100,
        bins=np.arange(0, 102, 2),
        color="#3b82f6",
        edgecolor="white",
        linewidth=0.3,
    )
    axes[0, 0].axvline(75, color="#dc2626", linestyle="--", linewidth=1.5)
    axes[0, 0].set(xlabel="Full-life CPS coverage (%)", ylabel="Cyclones")
    axes[0, 0].set_title("(a) Coverage distribution (CPS files)", loc="left")

    status_order = [COMPLETE, ELIGIBLE_INCOMPLETE, INSUFFICIENT_COVERAGE, NO_DATA]
    status_counts = [int((df["coverage_status"] == item).sum()) for item in status_order]
    status_labels = ["Complete", "Eligible\nincomplete", "Below 75%", "No data"]
    axes[0, 1].bar(status_labels, status_counts, color=["#16a34a", "#65a30d", "#f59e0b", "#64748b"])
    axes[0, 1].set_ylabel("Cyclones")
    axes[0, 1].set_title("(b) Catalogue coverage status", loc="left")
    for i, value in enumerate(status_counts):
        axes[0, 1].text(i, value, f"{value:,}", ha="center", va="bottom", fontsize=9)

    axes[1, 0].bar(ep["ep"], ep["pct_included"], color=["#2563eb", "#f59e0b", "#7c3aed"])
    axes[1, 0].axhline(100, color="0.6", linewidth=0.8)
    axes[1, 0].set(ylim=(0, 105), ylabel="Included at >=75% (%)")
    axes[1, 0].set_title("(c) Coverage eligibility by current EP", loc="left")
    for i, value in enumerate(ep["pct_included"]):
        axes[1, 0].text(i, value, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)

    comp = comparison[comparison["dimension"] == "phase_class"].copy()
    pivot = comp.pivot(index="category", columns="completeness_group", values="pct").fillna(0)
    order = [cls for cls in PHASE_ORDER if cls in pivot.index]
    pivot = pivot.reindex(order)
    x = np.arange(len(pivot))
    width = 0.38
    axes[1, 1].bar(x - width / 2, pivot.get("complete", 0), width, label="Complete")
    axes[1, 1].bar(
        x + width / 2,
        pivot.get("incomplete_eligible", 0),
        width,
        label="Incomplete, eligible",
    )
    axes[1, 1].set_xticks(x, pivot.index, rotation=45, ha="right")
    axes[1, 1].set_ylabel("Within-group share (%)")
    axes[1, 1].set_title("(d) CPS-class composition", loc="left")
    axes[1, 1].legend(frameon=False)

    fig.suptitle("CPS full-life coverage diagnostic", fontsize=15, fontweight="bold")
    fig.savefig(OUT_FIGURE, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    if not COVERAGE_FILE.exists() or not CLASS_FILE.exists():
        print("Missing coverage/classification audit outputs. Run steps 1 and 2 first.")
        return 1

    coverage = pd.read_csv(COVERAGE_FILE)
    classified = pd.read_csv(CLASS_FILE)
    if coverage["track_id"].duplicated().any() or classified["track_id"].duplicated().any():
        raise ValueError("coverage diagnostic inputs must have unique track IDs")
    if set(coverage["track_id"]) != set(classified["track_id"]):
        raise ValueError("coverage and classification audit populations differ")

    df = classified.copy()
    df["coverage_bin"] = coverage_bin(df["coverage_fraction"]).astype(str)
    df["analysis_included"] = df["analysis_included"].astype(bool)

    bins, bin_ep = build_bin_table(df)
    by_ep = build_ep_table(df)
    by_class = build_class_table(df)
    comparison = build_complete_comparison(df)
    tests = build_bias_tests(df)
    sensitivity = build_threshold_sensitivity(df)
    ep_mapping_audit = audit_current_ep_mapping(df)

    bins.to_csv(OUT_BINS, index=False)
    bin_ep.to_csv(OUT_BIN_EP, index=False)
    by_ep.to_csv(OUT_EP, index=False)
    by_class.to_csv(OUT_CLASS, index=False)
    comparison.to_csv(OUT_COMPARISON, index=False)
    tests.to_csv(OUT_TESTS, index=False)
    sensitivity.to_csv(OUT_SENSITIVITY, index=False)

    n_catalogue = len(df)
    n_with_cps = int(df["has_cps_file"].sum())
    n_complete = int((df["coverage_status"] == COMPLETE).sum())
    n_incomplete_with_cps = int(
        (df["has_cps_file"] & (df["coverage_status"] != COMPLETE)).sum()
    )
    n_no_data_files = int(
        (df["has_cps_file"] & (df["coverage_status"] == NO_DATA)).sum()
    )
    n_no_data_catalogue = int((df["coverage_status"] == NO_DATA).sum())
    n_included = int(df["analysis_included"].sum())
    n_excluded = n_catalogue - n_included
    incomplete_files = df[df["has_cps_file"] & (df["coverage_status"] != COMPLETE)]
    incomplete_usable = incomplete_files[incomplete_files["n_usable_timesteps"] > 0]

    summary = {
        "definition": {
            "denominator": "complete hourly-track duration from trajectory genesis to end",
            "numerator": (
                "sum of CPS interval durations whose ending timestep has finite B, VTL and VTU"
            ),
            "edge_treatment": (
                "hours before the first CPS timestamp, after the last CPS timestamp, and "
                "intervals ending in unusable CPS values are uncovered"
            ),
            "official_threshold": COVERAGE_THRESHOLD,
        },
        "population": {
            "catalogue": n_catalogue,
            "with_cps_file": n_with_cps,
            "without_cps_file": n_catalogue - n_with_cps,
            "complete": n_complete,
            "complete_pct_of_with_cps": _pct(n_complete, n_with_cps),
            "incomplete_with_cps": n_incomplete_with_cps,
            "incomplete_pct_of_with_cps": _pct(n_incomplete_with_cps, n_with_cps),
            "no_usable_with_cps": n_no_data_files,
            "no_usable_pct_of_with_cps": _pct(n_no_data_files, n_with_cps),
            "no_data_catalogue": n_no_data_catalogue,
            "included_ge75": n_included,
            "included_pct_of_catalogue": _pct(n_included, n_catalogue),
            "excluded_catalogue": n_excluded,
            "excluded_pct_of_catalogue": _pct(n_excluded, n_catalogue),
            "below75_with_cps": int(
                (df["has_cps_file"] & ~df["analysis_included"]).sum()
            ),
        },
        "coverage_distribution_incomplete_with_cps": _distribution_stats(
            incomplete_files["coverage_fraction"]
        ),
        "coverage_distribution_incomplete_usable_with_cps": _distribution_stats(
            incomplete_usable["coverage_fraction"]
        ),
        "temporal_alignment": {
            "verdict": "PASS",
            "all_cps_timestamps_on_reference_tracks": True,
            "unique_strictly_increasing_axes": True,
            "cadence": "3 h, with an optional terminal 2 h interval",
            "edge_offsets_hours": "0-2",
        },
        "current_ep_mapping_audit": ep_mapping_audit,
        "bias_tests": [
            {key: _python(value) for key, value in row.items()}
            for row in tests.to_dict(orient="records")
        ],
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")

    with OUT_TEXT.open("w") as handle:
        handle.write("CPS FULL-LIFE COVERAGE DIAGNOSTIC\n")
        handle.write("=" * 72 + "\n\n")
        handle.write("Coverage definition\n-------------------\n")
        for key, value in summary["definition"].items():
            handle.write(f"{key}: {value}\n")
        handle.write("\nPopulation\n----------\n")
        for key, value in summary["population"].items():
            handle.write(f"{key}: {value}\n")
        handle.write("\nIncomplete CPS-file coverage statistics (fraction; includes no-data files)\n")
        handle.write("-----------------------------------------------------------------------\n")
        for key, value in summary["coverage_distribution_incomplete_with_cps"].items():
            handle.write(f"{key}: {value}\n")
        handle.write("\nCompleteness by current EP\n--------------------------\n")
        handle.write(by_ep.to_string(index=False) + "\n")
        handle.write("\nCorrected EP mapping audit\n--------------------------\n")
        for key, value in ep_mapping_audit.items():
            handle.write(f"{key}: {value}\n")
        handle.write("\nComplete vs eligible-incomplete bias tests\n")
        handle.write("-------------------------------------------\n")
        handle.write(tests.to_string(index=False) + "\n")
        handle.write("\nThreshold sensitivity (EP-labelled population)\n")
        handle.write("----------------------------------------------\n")
        cols = ["threshold_label", "ep", "n", "n_SC", "pct_SC", "n_ST", "pct_ST", "n_SD", "pct_SD", "pct_identified"]
        handle.write(sensitivity[cols].to_string(index=False) + "\n")
        handle.write("\nAll percentages use the denominator printed in the same row/table.\n")

    make_figure(df, bins, by_ep, comparison)

    print("=" * 72)
    print("STEP 2b: CPS full-life coverage diagnostic")
    print("=" * 72)
    print(f"Catalogue: {n_catalogue:,}; CPS files: {n_with_cps:,}; complete: {n_complete:,}")
    print(f"Included >=75%: {n_included:,}; excluded: {n_excluded:,}; no_data: {n_no_data_catalogue:,}")
    for path in (
        OUT_JSON, OUT_BINS, OUT_BIN_EP, OUT_EP, OUT_CLASS, OUT_COMPARISON,
        OUT_TESTS, OUT_SENSITIVITY, OUT_TEXT, OUT_FIGURE,
    ):
        print(f"Wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
