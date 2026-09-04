#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1: Build the Ck subterm table for every Energy Pattern.

What changed
------------
The barotropic decomposition used to require a dedicated side run of
LorenzCycleToolKit over the EP1 cyclones only (444 cases, ~222 GB of ERA5),
because the archived article results carried just the total ``Ck``. The
corrected climatology rerun writes ``Ck_1`` .. ``Ck_5`` pressure-level files for
all 3,820 cyclones, so the decomposition is now available for **EP1, EP2, EP3
and EPALL at no extra computational cost**. This step therefore reads the rerun
products instead of launching anything.

The five subterms follow the C_K equation of the manuscript::

    Ck_1 (A)  eddy momentum flux against the meridional shear of [u]
    Ck_2 (B)  meridional flux of eddy KE against the meridional gradient of [v]
    Ck_3 (C)  curvature (tan phi) flux of zonal eddy KE
    Ck_4 (D)  vertical flux of zonal eddy momentum against the shear of [u]
    Ck_5 (E)  vertical flux of meridional eddy momentum against the shear of [v]

Sign convention (as in the manuscript): ``C_K < 0`` means K_Z -> K_E, the mean
flow feeding the eddy (barotropic instability). The *dominant* subterm of a
cyclone is the most negative one, i.e. the largest contributor to that transfer.

The subterms are verified to close: ``Ck = sum(Ck_1..Ck_5)`` to round-off, both
per pressure level and after vertical integration. The closure residual is
carried in the output so any drift is visible rather than assumed away.

Inputs
------
    data/corrected/vertical_phase_means_corrected.parquet
        built by scripts/lec_climatology_rerun/build_corrected_vertical_levels.py
    results/cluster/kmeans_clustered_data.csv + cluster_to_ep.json
        Energy Pattern assignment of the corrected clustering

Outputs (results/ck_subterms_corrected/)
----------------------------------------
    subterms_by_cyclone.csv   one row per (track_id, phase): the six integrated
                              Ck quantities, relative contributions, dominant
                              subterm, closure residual, EP label
    subterms_long.csv         tidy form for plotting: one row per
                              (track_id, phase, subterm)
    build_report.md           coverage and validation report

Usage
-----
    python scripts/ck_subterms_analysis/step1_build_subterms_table.py
    python scripts/ck_subterms_analysis/step1_build_subterms_table.py --allow-partial

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import corrected_lec as clec  # noqa: E402
from scripts.utils import ep_mapping as em  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "results" / "ck_subterms_corrected"

CK_TERMS = ["Ck", *clec.CK_SUBTERMS]

#: Relative closure residual above which the decomposition is not trustworthy.
CLOSURE_TOLERANCE = 1e-6


def integrate_profiles(profiles: pd.DataFrame) -> pd.DataFrame:
    """Vertically integrate the phase-mean profiles into W m-2.

    ``profiles`` is the long table of
    ``build_corrected_vertical_levels.py``. Integration is trapezoidal in
    pressure, matching the toolkit, so the result reproduces the phase mean of
    the integrated term.
    """
    def _integrate(group: pd.DataFrame) -> float:
        ordered = group.sort_values("level_hpa")
        pressure_pa = ordered["level_hpa"].to_numpy(dtype=float) * 100.0
        return float(np.trapezoid(ordered["value"].to_numpy(dtype=float), pressure_pa))

    integrated = (
        profiles.groupby(["track_id", "phase", "term"], observed=True)
        .apply(_integrate, include_groups=False)
        .rename("value")
        .reset_index()
    )
    return integrated.pivot_table(
        index=["track_id", "phase"], columns="term", values="value", observed=True
    ).reset_index()


def add_diagnostics(table: pd.DataFrame) -> pd.DataFrame:
    """Closure residual, relative contributions and dominant subterm."""
    subterms = clec.CK_SUBTERMS
    table = table.copy()

    total_from_parts = table[subterms].sum(axis=1)
    scale = table["Ck"].abs().where(lambda s: s > 0, other=np.nan)
    table["ck_closure_residual"] = total_from_parts - table["Ck"]
    table["ck_closure_relative"] = (table["ck_closure_residual"].abs() / scale).fillna(0.0)

    # Share of the total barotropic conversion carried by each subterm. Signed,
    # so a subterm opposing the total shows up as a negative share rather than
    # being hidden by an absolute value.
    for stem in subterms:
        table[f"{stem}_share"] = table[stem] / table["Ck"].where(lambda s: s != 0)

    # Dominant subterm: the most negative one, i.e. the strongest contributor to
    # the mean-flow-to-eddy transfer that defines barotropic instability here.
    dominant = table[subterms].idxmin(axis=1)
    table["dominant_subterm"] = dominant
    table["dominant_label"] = dominant.map(clec.CK_SUBTERM_LABELS)
    table["dominant_value"] = table[subterms].min(axis=1)

    return table


def to_long(table: pd.DataFrame) -> pd.DataFrame:
    """Tidy form: one row per (track_id, phase, subterm)."""
    long = table.melt(
        id_vars=["track_id", "ep", "ep_label", "phase", "Ck"],
        value_vars=clec.CK_SUBTERMS,
        var_name="subterm",
        value_name="value",
    )
    long["subterm_label"] = long["subterm"].map(clec.CK_SUBTERM_LABELS)
    long["subterm_math"] = long["subterm"].map(clec.CK_SUBTERM_MATH)
    long["share"] = long["value"] / long["Ck"].where(lambda s: s != 0)
    long["units"] = "W m-2"
    return long


def write_report(table: pd.DataFrame, source: Path, path: Path) -> Path:
    """Coverage and validation report."""
    worst_closure = float(table["ck_closure_relative"].max())
    lines = [
        "# Ck subterms — build report",
        "",
        f"Source profiles: `{source}`",
        f"Energy cache lineage: `{em.mapping_source()}`",
        "",
        "## Coverage",
        "",
        "| Energy Pattern | cyclones | rows (cyclone x phase) |",
        "|---|---|---|",
    ]
    for label, group in table.groupby("ep_label", observed=True):
        lines.append(f"| {label} | {group['track_id'].nunique()} | {len(group)} |")
    lines += [
        f"| **all** | **{table['track_id'].nunique()}** | **{len(table)}** |",
        "",
        "## Validation",
        "",
        f"- Worst relative closure residual `|sum(Ck_i) - Ck| / |Ck|`: {worst_closure:.3e}",
        f"- Tolerance: {CLOSURE_TOLERANCE:.0e}",
        f"- Verdict: {'PASS' if worst_closure <= CLOSURE_TOLERANCE else 'FAIL'}",
        "",
        "## Dominant subterm during intensification",
        "",
        "| Energy Pattern | " + " | ".join(
            clec.CK_SUBTERM_LABELS[stem] for stem in clec.CK_SUBTERMS
        ) + " |",
        "|---" * (len(clec.CK_SUBTERMS) + 1) + "|",
    ]
    intensifying = table[table["phase"] == "intensification"]
    for label, group in intensifying.groupby("ep_label", observed=True):
        shares = group["dominant_label"].value_counts(normalize=True) * 100
        cells = [
            f"{shares.get(clec.CK_SUBTERM_LABELS[stem], 0.0):.1f}%"
            for stem in clec.CK_SUBTERMS
        ]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the all-EP Ck subterm table.")
    parser.add_argument("--profiles", type=Path, help="vertical phase-mean parquet")
    parser.add_argument(
        "--allow-partial", action="store_true",
        help="accept a partial rerun build; exploratory only",
    )
    args = parser.parse_args()

    source = args.profiles
    if source is None:
        source = clec.corrected_path(clec.VERTICAL_PHASE_MEANS)
        if not source.is_file() and args.allow_partial:
            source = clec.corrected_path(
                clec.VERTICAL_PHASE_MEANS.replace(".parquet", "_partial.parquet")
            )
    if not source.is_file():
        raise SystemExit(
            f"vertical phase means not found: {source}\n"
            "Run scripts/lec_climatology_rerun/build_corrected_vertical_levels.py first."
        )
    if "_partial" in source.name and not args.allow_partial:
        raise SystemExit(
            f"{source.name} is a partial build. Pass --allow-partial to use it "
            "for exploration, and never for an article result."
        )

    print(f"profiles : {source}")
    profiles = pd.read_parquet(source)
    profiles = profiles[profiles["term"].isin(CK_TERMS)]
    if profiles.empty:
        raise SystemExit(
            f"{source} carries no Ck terms. Rebuild it including {CK_TERMS}."
        )

    print("integrating phase-mean profiles ...")
    table = integrate_profiles(profiles)

    missing = [term for term in CK_TERMS if term not in table.columns]
    if missing:
        raise SystemExit(f"the profile table lacks {missing}")

    assignments = em.load_ep_assignments()
    print(f"clustering lineage: {em.mapping_source()}")
    if not em.is_corrected_clustering():
        print(
            "WARNING: the Energy Pattern assignment still comes from the legacy "
            "clustering. Re-run the cluster pipeline on the corrected cache "
            "before using these subterms in the article."
        )

    table = table.merge(assignments[["track_id", "ep"]], on="track_id", how="left")
    unassigned = int(table["ep"].isna().sum())
    if unassigned:
        print(f"  note: {unassigned} rows have no EP assignment and are dropped")
        table = table.dropna(subset=["ep"])
    table["ep"] = table["ep"].astype(int)
    table["ep_label"] = table["ep"].map(em.EP_LABELS)

    table = add_diagnostics(table)

    worst = float(table["ck_closure_relative"].max())
    if worst > CLOSURE_TOLERANCE:
        raise SystemExit(
            f"Ck decomposition does not close: worst relative residual {worst:.3e} "
            f"exceeds {CLOSURE_TOLERANCE:.0e}. Do not use these subterms."
        )
    print(f"closure check: worst relative residual {worst:.3e} — PASS")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    wide_path = RESULTS_DIR / "subterms_by_cyclone.csv"
    long_path = RESULTS_DIR / "subterms_long.csv"
    table.to_csv(wide_path, index=False)
    to_long(table).to_csv(long_path, index=False)
    report = write_report(table, source, RESULTS_DIR / "build_report.md")

    print(f"\ncyclones : {table['track_id'].nunique()}")
    print(f"rows     : {len(table)}")
    for path in (wide_path, long_path, report):
        print(f"  wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
