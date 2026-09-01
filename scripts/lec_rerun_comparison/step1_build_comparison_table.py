#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step1_build_comparison_table.py — Pair legacy and corrected LEC phase means.

Builds the "before x after" table used by every other step of this analysis:

  * corrected side — phase means recomputed from the rerun at ``--run-root``,
    using exactly the aggregation of
    ``scripts/lec_climatology_rerun/build_corrected_cache.py`` (mean of every
    3-hourly time step inside each frozen lifecycle window), but restricted to
    the cyclones already in state COMPLETE. The rerun is still running, so this
    is a growing subset of the 3,820 target cyclones.
  * legacy side — ``data/energy_cache.parquet``, the article input. It was
    verified to be exactly the same aggregation applied to the archived Zenodo
    results (see ``--verify-sample``), so the pairing is apples to apples: same
    cyclones, same lifecycle windows, same vertical grid, same time steps. The
    only difference is the LorenzCycleToolKit 2.0.0 equation/numeric correction.

Pairs are matched on (track_id, period), so secondary periods (``decay 2``)
match their own counterpart and are folded into the main phase for plotting.
Periods without a phase name (``residual``) are dropped, as in the rerun cache
builder.

Usage
-----
    python scripts/lec_rerun_comparison/step1_build_comparison_table.py
    python scripts/lec_rerun_comparison/step1_build_comparison_table.py --refresh
    python scripts/lec_rerun_comparison/step1_build_comparison_table.py \
        --run-root /p1-swell/danilocs/lec_climatology_corrected_v2 --verify-sample 20

Outputs (results/lec_rerun_comparison/)
---------------------------------------
    corrected_phase_means.parquet  wide table of corrected phase means (cached)
    paired_terms.parquet           long table: track_id, period, phase, term,
                                   legacy, corrected, diff
    coverage.json                  rerun state, population counts, provenance

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    ALL_TERMS,
    COVERAGE_JSON,
    CORRECTED_MEANS,
    DEFAULT_RUN_ROOT,
    LEGACY_CACHE,
    LEGACY_RESULTS,
    NEW_ONLY_TERMS,
    PAIRED_TABLE,
    RESULTS_DIR,
    nested_csv,
    phase_of,
)


# ── corrected side ────────────────────────────────────────────────────────────
def complete_track_ids(run_root: Path) -> tuple[list[str], dict[str, int]]:
    """Track ids in state COMPLETE, plus the full state histogram."""
    database = run_root / "state.sqlite3"
    if not database.is_file():
        raise FileNotFoundError(
            f"rerun state database not found: {database}. This step must run on "
            "the server that hosts the run root."
        )
    conn = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        states = dict(conn.execute("SELECT state, COUNT(*) FROM cyclones GROUP BY state"))
        ids = [
            row[0]
            for row in conn.execute(
                "SELECT track_id FROM cyclones WHERE state='COMPLETE' ORDER BY track_id"
            )
        ]
    finally:
        conn.close()
    return ids, states


def read_results(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    time_column = next(
        (c for c in frame.columns if c.lower() in {"time", "date", "datetime", "unnamed: 0"}),
        frame.columns[0],
    )
    frame["_time"] = pd.to_datetime(frame[time_column], errors="coerce")
    if frame["_time"].isna().any():
        raise ValueError(f"unparseable timestamps in {path}")
    return frame.set_index("_time").select_dtypes(include="number")


def phase_means(results: pd.DataFrame, periods: pd.DataFrame, track_id: str) -> list[dict]:
    """Mean of every numeric term over each lifecycle window."""
    records = []
    for period, window in periods.iterrows():
        phase = phase_of(period)
        if phase is None:
            continue
        start = pd.to_datetime(window["start"])
        end = pd.to_datetime(window["end"])
        selected = results.loc[(results.index >= start) & (results.index <= end)]
        if selected.empty:
            raise ValueError(f"no rows inside period {period!r} of {track_id}")
        record = selected.mean().to_dict()
        record.update(
            {
                "track_id": track_id,
                "period": str(period).strip().lower(),
                "phase": phase,
                "n_timesteps": len(selected),
            }
        )
        records.append(record)
    return records


def build_corrected(run_root: Path, track_ids: list[str], refresh: bool) -> pd.DataFrame:
    """Corrected phase means, rebuilt incrementally as the rerun progresses."""
    cached = pd.DataFrame()
    if CORRECTED_MEANS.is_file() and not refresh:
        cached = pd.read_parquet(CORRECTED_MEANS)
        cached["track_id"] = cached["track_id"].astype(str)
    known = set(cached["track_id"]) if not cached.empty else set()
    pending = [track_id for track_id in track_ids if track_id not in known]
    print(f"corrected side: {len(known)} cached, {len(pending)} to read")

    records: list[dict] = []
    for index, track_id in enumerate(pending, start=1):
        directory = run_root / "lec_results" / f"{track_id}_ERA5_track"
        results = read_results(directory / f"{track_id}_ERA5_track_results.csv")
        periods = pd.read_csv(directory / "periods.csv", index_col=0)
        records.extend(phase_means(results, periods, track_id))
        if index % 500 == 0:
            print(f"  ... {index}/{len(pending)}")

    frame = pd.concat([cached, pd.DataFrame(records)], ignore_index=True) if records else cached
    frame = frame[frame["track_id"].isin(set(track_ids))].reset_index(drop=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(CORRECTED_MEANS, index=False)
    return frame


# ── legacy side ───────────────────────────────────────────────────────────────
def load_legacy() -> pd.DataFrame:
    if not LEGACY_CACHE.is_file():
        raise FileNotFoundError(f"legacy cache not found: {LEGACY_CACHE}")
    frame = pd.read_parquet(LEGACY_CACHE)
    frame["track_id"] = frame["track_id"].astype(str)
    frame["period"] = frame["period"].astype(str).str.strip().str.lower()
    frame["phase"] = frame["period"].map(phase_of)
    return frame[frame["phase"].notna()].reset_index(drop=True)


def verify_legacy(legacy: pd.DataFrame, track_ids: list[str], sample: int, seed: int = 0) -> dict:
    """Re-aggregate the archived Zenodo results and confirm they match the cache.

    Guarantees that the legacy side of the comparison was built with the same
    aggregation now applied to the corrected side.
    """
    if sample <= 0 or not LEGACY_RESULTS.is_dir():
        return {"checked": 0, "max_relative_difference": None}
    rng = np.random.default_rng(seed)
    chosen = rng.choice(track_ids, size=min(sample, len(track_ids)), replace=False)
    worst = 0.0
    checked = 0
    for track_id in chosen:
        directory = LEGACY_RESULTS / f"{track_id}_ERA5_track"
        results_file = nested_csv(directory / f"{track_id}_ERA5_track_results.csv")
        periods_file = nested_csv(directory / "periods.csv")
        if not results_file.is_file() or not periods_file.is_file():
            continue
        recomputed = pd.DataFrame(
            phase_means(read_results(results_file), pd.read_csv(periods_file, index_col=0), track_id)
        ).set_index("period")
        reference = legacy[legacy["track_id"] == track_id].set_index("period")
        shared = [t for t in ALL_TERMS if t in recomputed and t in reference]
        for period in recomputed.index.intersection(reference.index):
            left = recomputed.loc[period, shared].astype(float).to_numpy()
            right = reference.loc[period, shared].astype(float).to_numpy()
            scale = np.maximum(np.abs(left), np.abs(right))
            with np.errstate(divide="ignore", invalid="ignore"):
                relative = np.where(scale > 0, np.abs(left - right) / scale, 0.0)
            worst = max(worst, float(np.nanmax(relative)))
        checked += 1
    return {"checked": checked, "max_relative_difference": worst}


# ── pairing ───────────────────────────────────────────────────────────────────
def pair(legacy: pd.DataFrame, corrected: pd.DataFrame) -> pd.DataFrame:
    keys = ["track_id", "period", "phase"]
    terms = [t for t in ALL_TERMS if t in legacy.columns and t in corrected.columns]
    left = legacy[keys + terms].melt(keys, var_name="term", value_name="legacy")
    right = corrected[keys + terms].melt(keys, var_name="term", value_name="corrected")
    merged = left.merge(right, on=keys + ["term"], how="inner")
    merged = merged.dropna(subset=["legacy", "corrected"])
    merged["diff"] = merged["corrected"] - merged["legacy"]
    return merged.reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--refresh", action="store_true", help="ignore the cached corrected means")
    parser.add_argument("--verify-sample", type=int, default=10)
    args = parser.parse_args()

    track_ids, states = complete_track_ids(args.run_root)
    total = sum(states.values())
    print(f"rerun state: {states} ({len(track_ids)}/{total} COMPLETE)")
    if not track_ids:
        raise SystemExit("no COMPLETE cyclones yet; nothing to compare")

    corrected = build_corrected(args.run_root, track_ids, args.refresh)
    legacy = load_legacy()
    verification = verify_legacy(legacy, track_ids, args.verify_sample)
    print(
        f"legacy cache verification: {verification['checked']} cyclones re-aggregated, "
        f"max relative difference {verification['max_relative_difference']}"
    )

    paired = pair(legacy, corrected)
    paired.to_parquet(PAIRED_TABLE, index=False)

    provenance_file = args.run_root / "provenance.json"
    provenance = json.loads(provenance_file.read_text()) if provenance_file.is_file() else {}
    new_only = {
        term: float(corrected[term].median())
        for term in NEW_ONLY_TERMS
        if term in corrected.columns
    }
    coverage = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_root": str(args.run_root),
        "rerun_states": states,
        "population_target": total,
        "cyclones_complete": len(track_ids),
        "completion_fraction": round(len(track_ids) / total, 4) if total else None,
        "paired_cyclones": int(paired["track_id"].nunique()),
        "paired_period_rows": int(paired.groupby(["track_id", "period"]).ngroups),
        "paired_values": int(len(paired)),
        "terms_compared": sorted(paired["term"].unique().tolist()),
        "corrected_only_terms_median": new_only,
        "legacy_cache_verification": verification,
        "provenance": {
            key: provenance.get(key)
            for key in ("toolkit_commit", "repository_commit", "energy_cache_sha256")
            if key in provenance
        },
    }
    COVERAGE_JSON.write_text(json.dumps(coverage, indent=2, ensure_ascii=False))

    print(
        f"paired {coverage['paired_cyclones']} cyclones / "
        f"{coverage['paired_period_rows']} period rows / {coverage['paired_values']} values"
    )
    print(f"wrote {PAIRED_TABLE}")
    print(f"wrote {COVERAGE_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
