#!/usr/bin/env python3
"""
Extract the CPS (Cyclone Phase Space) analysis results for the web site.

Writes web/src/content/cps_manifest.json from the canonical pipeline outputs.
No number on the CPS page is typed by hand: counts, percentages, thresholds and
statistics all come from here, so regenerating the analysis and re-running this
script keeps the site in step with the science.

The thresholds are read from `cps_criteria` itself rather than transcribed, so a
change to a threshold propagates to the site the same way it propagates to the
figures.

Inputs (all produced by scripts/cps_analysis/):
    results/cps_analysis/cps_coverage.csv
    results/cps_analysis/coverage_diagnostics.json
    results/cps_analysis/coverage_*.csv
    results/cps_analysis/phase_classification.csv
    results/cps_analysis/phase_states.csv
    results/cps_analysis/ep_relative_frequency.csv
    results/cps_analysis/case_diagram_index.csv
    scripts/cps_analysis/cps_criteria.py

Output:
    web/src/content/cps_manifest.json

Usage:
    python scripts/web/extract_cps_site_data.py

Author: Danilo Couto de Souza
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(REPO_ROOT))

import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

from scripts.cps_analysis.cps_coverage import COVERAGE_THRESHOLD
from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    CANONICAL_SOURCE,
    CANONICAL_PRECEDENCE,
    SINGLE_STATE_CLASSES,
    TRANSITIONS,
    TRANSITION_PRECEDENCE,
    CHARACTERISTIC_CLASSES,
    UNDETERMINED,
    SECLUSION,
    INDETERMINATE_WARM,
    MIN_PERSISTENCE_HOURS,
    GENESIS_LAT_BAND,
    OUT_OF_BAND,
    SC_REQUIRE_GENESIS_BAND,
    SC_MIN_OCEAN_FRACTION,
    SC_MAX_HOURS_PAST_PEAK,
    MIN_DOMINANCE,
    PURE_GENESIS_MAX_ONSET_HOURS,
    TT_MAX_POLEWARD_LAT,
    TT_MIN_OCEAN_FRACTION,
    PHASE_COLORS,
    describe_interval,
)
from scripts.utils.ep_mapping import ALL_EPS, get_ep_label

RESULTS = REPO_ROOT / "results" / "cps_analysis"
OUT = REPO_ROOT / "web" / "src" / "content" / "cps_manifest.json"

# Web-side path. The pipeline writes to figures/cps_analysis/; copy_figures_to_web.py
# publishes them under figures/cps/ so the served URLs stay short.
FIG_DIR = "figures/cps"
FIGURES = {
    "reference":        f"{FIG_DIR}/fig0_cps_reference.png",
    "composition":      f"{FIG_DIR}/fig1_phase_composition.png",
    "phase_space":      f"{FIG_DIR}/fig2_phase_space.png",
    "transitions":      f"{FIG_DIR}/fig3_transitions.png",
    "tropical_runs":    f"{FIG_DIR}/fig4_tropical_runs.png",
    "phase_space_by_ep": f"{FIG_DIR}/fig5_phase_space_by_ep.png",
    "single_state_sc":  f"{FIG_DIR}/fig6_phase_space_by_ep_single_state_sc.png",
    "trajectories":     f"{FIG_DIR}/fig7_transition_trajectories.png",
    "ep_relative":      f"{FIG_DIR}/fig8_ep_relative_subtropical.png",
    "genesis_identified_anomaly": f"{FIG_DIR}/fig9_genesis_density_identified_anomaly.png",
    "genesis_identified_absolute": f"{FIG_DIR}/fig9_genesis_density_identified_absolute.png",
    "genesis_characteristics_anomaly": f"{FIG_DIR}/fig9_genesis_density_characteristics_anomaly.png",
    "genesis_characteristics_absolute": f"{FIG_DIR}/fig9_genesis_density_characteristics_absolute.png",
    "track_identified_anomaly": f"{FIG_DIR}/fig10_track_density_identified_anomaly.png",
    "track_identified_absolute": f"{FIG_DIR}/fig10_track_density_identified_absolute.png",
    "track_characteristics_anomaly": f"{FIG_DIR}/fig10_track_density_characteristics_anomaly.png",
    "track_characteristics_absolute": f"{FIG_DIR}/fig10_track_density_characteristics_absolute.png",
    "coverage":         f"{FIG_DIR}/fig11_cps_coverage_diagnostics.png",
}

# Human-readable label for every class code the classifier can emit.
CLASS_LABELS = {
    **SINGLE_STATE_CLASSES,
    **TRANSITIONS,
    **CHARACTERISTIC_CLASSES,
    UNDETERMINED: "no structure held for the persistence gate, none dominant",
}
CLASS_ORDER = (list(SINGLE_STATE_CLASSES) + TRANSITION_PRECEDENCE
               + list(CHARACTERISTIC_CLASSES) + [UNDETERMINED])


def criteria_block() -> dict:
    return {
        "source": CANONICAL_SOURCE,
        "classes": [
            {
                "name": cls,
                "code": {"tropical": "TC", "subtropical": "SC",
                         "extratropical": "EC"}[cls],
                "color": PHASE_COLORS[{"tropical": "TC", "subtropical": "SC",
                                       "extratropical": "EC"}[cls]],
                "terms": [describe_interval(iv, p)
                          for p, iv in CANONICAL[cls].items()],
            }
            for cls in CANONICAL_PRECEDENCE
        ],
        "precedence": CANONICAL_PRECEDENCE,
        "persistence_hours": MIN_PERSISTENCE_HOURS,
        "pure_genesis_max_onset_hours": PURE_GENESIS_MAX_ONSET_HOURS,
        "min_dominance": MIN_DOMINANCE,
        "tt_max_poleward_lat": TT_MAX_POLEWARD_LAT,
        "tt_min_ocean_fraction": TT_MIN_OCEAN_FRACTION,
        "coverage_threshold": COVERAGE_THRESHOLD,
    }


def json_records(frame: pd.DataFrame) -> list[dict]:
    """Return JSON-safe records (no numpy scalars or NaN literals)."""
    records = []
    for row in frame.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if pd.isna(value):
                clean[key] = None
            elif isinstance(value, (np.integer,)):
                clean[key] = int(value)
            elif isinstance(value, (np.floating,)):
                clean[key] = float(value)
            elif isinstance(value, (np.bool_,)):
                clean[key] = bool(value)
            else:
                clean[key] = value
        records.append(clean)
    return records


def ep_phase_statistics(path: Path) -> dict:
    """Derive the global EP x phase-class test directly from its crosstab."""
    observed = pd.read_csv(path, index_col=0)
    observed = observed.loc[observed.sum(axis=1) > 0, observed.sum(axis=0) > 0]
    chi2, p_value, dof, expected = chi2_contingency(observed, correction=False)
    residuals = (observed.to_numpy() - expected) / np.sqrt(expected)
    n = int(observed.to_numpy().sum())
    cramers_v = float(np.sqrt(chi2 / (n * (min(observed.shape) - 1))))
    drivers = []
    for i, ep_label in enumerate(observed.index):
        for j, phase_class in enumerate(observed.columns):
            value = float(residuals[i, j])
            if abs(value) > 2:
                drivers.append({
                    "ep": ep_label,
                    "phase_class": phase_class,
                    "observed": int(observed.iloc[i, j]),
                    "expected": round(float(expected[i, j]), 1),
                    "standardized_residual": round(value, 1),
                })
    drivers.sort(key=lambda row: abs(row["standardized_residual"]), reverse=True)
    n_lt5 = int((expected < 5).sum())
    return {
        "chi2": round(float(chi2), 2),
        "dof": int(dof),
        "p_value": float(p_value),
        "cramers_v": round(cramers_v, 3),
        "n": n,
        "expected_lt5": n_lt5,
        "expected_cells": int(expected.size),
        "cochran_violated": bool(n_lt5 / expected.size > 0.2),
        "drivers": drivers,
    }


def main() -> int:
    required = (
        "cps_coverage.csv", "coverage_diagnostics.json", "coverage_by_bin.csv",
        "coverage_by_ep.csv", "coverage_complete_vs_incomplete.csv",
        "coverage_bias_tests.csv", "coverage_threshold_sensitivity.csv",
        "phase_classification.csv", "phase_states.csv", "ep_phase_crosstab.csv",
        "ep_relative_frequency.csv",
    )
    for f in required:
        if not (RESULTS / f).exists():
            print(f"Missing {RESULTS / f}. Run the CPS pipeline first.")
            return 1

    cy = pd.read_csv(RESULTS / "phase_classification.csv")
    states = pd.read_csv(RESULTS / "phase_states.csv")
    rel = pd.read_csv(RESULTS / "ep_relative_frequency.csv")
    coverage = pd.read_csv(RESULTS / "cps_coverage.csv")
    coverage_summary = json.loads((RESULTS / "coverage_diagnostics.json").read_text())
    coverage_bins = pd.read_csv(RESULTS / "coverage_by_bin.csv")
    coverage_ep = pd.read_csv(RESULTS / "coverage_by_ep.csv")
    coverage_comparison = pd.read_csv(RESULTS / "coverage_complete_vs_incomplete.csv")
    coverage_tests = pd.read_csv(RESULTS / "coverage_bias_tests.csv")
    coverage_sensitivity = pd.read_csv(RESULTS / "coverage_threshold_sensitivity.csv")

    ep = cy[cy["ep"].notna()].copy()
    ep["ep"] = ep["ep"].astype(int)

    counts = cy["phase_class"].value_counts()
    classes = [
        {
            "code": code,
            "label": CLASS_LABELS.get(code, code),
            "color": PHASE_COLORS.get(code, "#999999"),
            "n": int(counts.get(code, 0)),
            "pct": round(100 * float(counts.get(code, 0)) / len(cy), 1),
            "kind": ("single_state" if code in SINGLE_STATE_CLASSES
                     else "transition" if code in TRANSITIONS
                     else "characteristic" if code in CHARACTERISTIC_CLASSES
                     else "undetermined"),
        }
        for code in CLASS_ORDER
    ]

    verdicts = states["state"].value_counts()
    # Rejected runs keep their original class in `run_code`, so a `warm_seclusion`
    # verdict can be attributed to the tropical or the subtropical guard.
    rej = states[states["state"].isin(["warm_seclusion", "genesis_out_of_band",
                                       "indeterminate_warm_core"])]
    by_guard = (rej.groupby(["run_code", "state"]).size().to_dict()
                if "run_code" in rej else {})
    gallery_n = 0
    gallery_classes = 0
    idx_file = RESULTS / "case_diagram_index.csv"
    if idx_file.exists():
        idx = pd.read_csv(idx_file)
        gallery_n = len(idx)
        gallery_classes = int(idx["phase_class"].nunique())

    # The coverage table already carries the complete reference-track bounds;
    # no fragile dependency on the large phase_timesteps.csv is needed here.
    genesis = pd.to_datetime(cy["track_start"])

    manifest = {
        "title": "Cyclone Phase Space — thermal structure of the Energy Patterns",
        "generated_from": "scripts/cps_analysis/ (canonical pipeline, steps 1–9)",
        "provenance": {
            "cps_computed_by": "Andres Rodriguez (IAG-USP)",
            "note": ("The per-cyclone CPS parameters were computed by a collaborator "
                     "over several months from ERA5 fields that are no longer held. "
                     "The CSV series are the irreplaceable input to this analysis; "
                     "the calculator is preserved unmodified in the repository."),
            "calculator": "scripts/cps_analysis/cps_calculator_era5tocsv.py",
        },
        "population": {
            "catalogue": int(len(coverage)),
            "with_cps": int(coverage["has_cps_file"].sum()),
            "included": int(len(cy)),
            "excluded": int(len(coverage) - len(cy)),
            "no_data": int((coverage["coverage_status"] == "no_data").sum()),
            "ep_labelled": int(len(ep)),
            "by_ep": {get_ep_label(e): int((ep["ep"] == e).sum()) for e in ALL_EPS},
            "genesis_year_min": int(genesis.dt.year.min()),
            "genesis_year_max": int(genesis.dt.year.max()),
            "genesis_first": str(genesis.min().date()),
            "genesis_last": str(genesis.max().date()),
            "timestep_hours": 3,
        },
        "criteria": criteria_block(),
        "classes": classes,
        "runs": {
            "subtropical_accepted": int(verdicts.get("SC", 0)),
            "subtropical_out_of_band": int(by_guard.get(("SC", OUT_OF_BAND), 0)),
            "subtropical_seclusion": int(by_guard.get(("SC", SECLUSION), 0)),
            "tropical_accepted": int(verdicts.get("TC", 0)),
            "tropical_seclusion": int(by_guard.get(("TC", SECLUSION), 0)),
            "tropical_indeterminate": int(by_guard.get(("TC", INDETERMINATE_WARM), 0)),
        },
        "guards": {
            "genesis_band": list(GENESIS_LAT_BAND),
            "require_genesis_band": SC_REQUIRE_GENESIS_BAND,
            "min_ocean_fraction": SC_MIN_OCEAN_FRACTION,
            "max_hours_past_peak": SC_MAX_HOURS_PAST_PEAK,
        },
        "coverage": {
            **coverage_summary,
            "bins": json_records(coverage_bins),
            "by_ep": json_records(coverage_ep),
            "complete_vs_incomplete": json_records(coverage_comparison),
            "bias_tests": json_records(coverage_tests),
            "threshold_sensitivity": json_records(coverage_sensitivity),
        },
        "statistics": {
            "ep_phase": ep_phase_statistics(RESULTS / "ep_phase_crosstab.csv"),
        },
        "ep_relative": [
            {
                "outcome": r["outcome"],
                "ep": r["ep"],
                "k": int(r["k_ep"]),
                "n": int(r["n_ep"]),
                "rate_pct": round(100 * float(r["rate_ep"]), 2),
                "rate_lo_pct": round(100 * float(r["rate_ep_lo"]), 2),
                "rate_hi_pct": round(100 * float(r["rate_ep_hi"]), 2),
                "epall_rate_pct": round(100 * float(r["rate_epall"]), 2),
                "ratio": round(float(r["ratio_to_epall"]), 2),
                "odds_ratio": round(float(r["odds_ratio_vs_rest"]), 2),
                "p": float(r["p_fisher_vs_rest"]),
                "p_holm": float(r["p_holm"]),
                "significant_holm": bool(r["significant_holm"]),
            }
            for _, r in rel.iterrows()
        ],
        "gallery": {"n_figures": gallery_n, "n_classes": gallery_classes},
        "figures": FIGURES,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(manifest, fh, indent=2, allow_nan=False)

    print(f"Wrote {OUT.relative_to(REPO_ROOT)}")
    print(f"  population {manifest['population']['included']:,} eligible of "
          f"{manifest['population']['catalogue']:,} catalogue cyclones "
          f"({manifest['population']['ep_labelled']:,} with an EP)")
    print(f"  {len([c for c in classes if c['n'] > 0])} populated classes, "
          f"{gallery_n} gallery figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
