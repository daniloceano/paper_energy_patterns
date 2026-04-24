#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ck_subterms_summary.py — Consolidate LEC Ck subterm results into
lightweight summary CSV files ready for local analysis and publication.

Run this script ON THE REMOTE SERVER before running sync_from_remote.sh.

What it does
------------
1. Reads the EP1 cyclone list and phase windows from
   results/ep_structure/ep1_cases.csv.
2. For each cyclone, loads the pressure-level Ck subterm files from
   results/ck_analysis/lec_results/{track_id}_ERA5_track/results_vertical_levels/
   (Ck_pressure_level.csv, Ck_1_pressure_level.csv … Ck_5_pressure_level.csv).
3. Loads per-cyclone lifecycle phase windows.  Primary source: periods.csv
   inside the LEC result directory (produced by CycloPhaser).  Fallback:
   intensification_start / intensification_end from ep1_cases.csv.
4. Vertically integrates each subterm time series (W m⁻²).
5. Outputs:
   results/ck_analysis/subterms_by_cyclone.csv
       One row per cyclone — phase-mean Ck_1..5 and Ck_total during each phase.
   results/ck_analysis/subterms_by_phase.csv
       Same data reshaped: one row per (track_id, phase, subterm).
   results/ck_analysis/ck_subterms_boxplot_input.csv
       Tidy long format: track_id, phase, subterm, value, units.
   results/ck_analysis/summary_build_report.md
       Human-readable validation report.

Usage (on remote server)
------------------------
    cd /path/to/paper_energy_patterns
    python scripts/ck_subterms_analysis/build_ck_subterms_summary.py

    # Verbose mode
    python scripts/ck_subterms_analysis/build_ck_subterms_summary.py --verbose

    # Limit to N cyclones (quick test)
    python scripts/ck_subterms_analysis/build_ck_subterms_summary.py --limit 20

Author: Danilo Couto de Souza / GitHub Copilot
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── project paths ─────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[2]
EP1_FILE    = BASE_DIR / "results" / "ep_structure" / "ep1_cases.csv"
LEC_DIR     = BASE_DIR / "results" / "ck_analysis" / "lec_results"
OUT_DIR     = BASE_DIR / "results" / "ck_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── subterm configuration ─────────────────────────────────────────────────────
GRAVITY = 9.8  # m s⁻²

CK_TOTAL_STEM   = "Ck"
CK_SUBTERM_STEMS = ["Ck_1", "Ck_2", "Ck_3", "Ck_4", "Ck_5"]
ALL_STEMS        = [CK_TOTAL_STEM] + CK_SUBTERM_STEMS

# Physical labels for the five subterms (A–E in paper.tex)
SUBTERM_LABELS = {
    "Ck_1": "Ck_A",
    "Ck_2": "Ck_B",
    "Ck_3": "Ck_C",
    "Ck_4": "Ck_D",
    "Ck_5": "Ck_E",
}

# Phase name variants that CycloPhaser may produce
PHASE_ALIASES: dict[str, str] = {
    # incipient
    "incipient":        "incipient",
    "pre-intensification": "incipient",
    "genesis":          "incipient",
    # intensification
    "intensification":  "intensification",
    "intensifying":     "intensification",
    # mature
    "mature":           "mature",
    "peak":             "mature",
    "maximum":          "mature",
    # decay
    "decay":            "decay",
    "decaying":         "decay",
    "dissipation":      "decay",
    "weakening":        "decay",
    # residual
    "residual":         "residual",
    "remnant":          "residual",
}

ALL_PHASES = ["incipient", "intensification", "mature", "decay", "residual"]


# ============================================================================
# HELPERS
# ============================================================================

def _lec_dir(track_id: str) -> Path:
    return LEC_DIR / f"{track_id}_ERA5_track"


def _vl_dir(track_id: str) -> Path:
    return _lec_dir(track_id) / "results_vertical_levels"


def _pressure_level_csv(track_id: str, stem: str) -> Path:
    return _vl_dir(track_id) / f"{stem}_pressure_level.csv"


def _load_pressure_level_csv(path: Path) -> Optional[pd.DataFrame]:
    """Load a pressure-level CSV (rows = time, columns = pressure levels).

    Returns None if the file is absent, empty, or unreadable.
    """
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if df.empty or df.shape[1] == 0:
            return None
        # Ensure column headers are numeric (pressure levels in Pa or hPa)
        df.columns = df.columns.astype(float)
        return df
    except Exception:
        return None


def _vertically_integrate(df: pd.DataFrame) -> pd.Series:
    """Vertically integrate a pressure-level DataFrame.

    Produces a time series in W m⁻² using the trapezoidal approximation
    (same method as lec_audit.py).
    """
    cols = np.sort(df.columns.astype(float))
    n = len(cols)
    dp = np.zeros(n)
    if n == 1:
        dp[0] = cols[0]
    else:
        dp[0]  = (cols[1]  - cols[0])  / 2.0
        dp[-1] = (cols[-1] - cols[-2]) / 2.0
        for i in range(1, n - 1):
            dp[i] = (cols[i + 1] - cols[i - 1]) / 2.0
    dp_map  = dict(zip(cols, dp))
    dp_vals = np.array([dp_map[c] for c in df.columns.astype(float)])
    integrated = (df.values * dp_vals[np.newaxis, :] / GRAVITY).sum(axis=1)
    return pd.Series(integrated, index=df.index, name=df.index.name or "time")


def _parse_periods_csv(periods_path: Path) -> Optional[dict[str, tuple]]:
    """Parse a CycloPhaser periods.csv into {canonical_phase: (start, end)}.

    CycloPhaser can produce different column layouts; we handle the common ones:
      Layout A: columns = [start, end, phase_name]
      Layout B: columns = phase names, rows = [start, end]
      Layout C: index = phase names, columns = [start, end]
    Returns None if the file can't be parsed or is empty.
    """
    if not periods_path.exists() or periods_path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(periods_path)
    except Exception:
        return None

    phases: dict[str, tuple] = {}

    # Layout A: has explicit 'start', 'end', 'phase' columns (most common)
    col_lower = {c.lower().strip(): c for c in df.columns}
    if "phase" in col_lower and "start" in col_lower and "end" in col_lower:
        for _, row in df.iterrows():
            raw = str(row[col_lower["phase"]]).lower().strip()
            canon = PHASE_ALIASES.get(raw, raw)
            try:
                phases[canon] = (
                    pd.Timestamp(row[col_lower["start"]]),
                    pd.Timestamp(row[col_lower["end"]]),
                )
            except Exception:
                pass
        return phases or None

    # Layout B: index holds phase names, columns are 'start'/'end' or similar
    df2 = df.copy()
    try:
        df2 = pd.read_csv(periods_path, index_col=0)
        col2_lower = {c.lower().strip(): c for c in df2.columns}
        if "start" in col2_lower and "end" in col2_lower:
            for raw_phase, row in df2.iterrows():
                raw = str(raw_phase).lower().strip()
                canon = PHASE_ALIASES.get(raw, raw)
                try:
                    phases[canon] = (
                        pd.Timestamp(row[col2_lower["start"]]),
                        pd.Timestamp(row[col2_lower["end"]]),
                    )
                except Exception:
                    pass
            return phases or None
    except Exception:
        pass

    return None


def _phase_windows_for_cyclone(
    track_id: str,
    ep1_row: pd.Series,
) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """Return {phase: (start, end)} for a given cyclone.

    Tries (in order):
      1. periods.csv inside the LEC result directory
      2. intensification_start / intensification_end from ep1_cases.csv
    """
    windows: dict[str, tuple] = {}

    # 1 — LEC periods.csv (CycloPhaser output)
    periods_path = _lec_dir(track_id) / "periods.csv"
    parsed = _parse_periods_csv(periods_path)
    if parsed:
        windows.update(parsed)

    # 2 — fallback: intensification window from ep1_cases.csv
    if "intensification" not in windows:
        t0 = ep1_row.get("intensification_start")
        t1 = ep1_row.get("intensification_end")
        if pd.notna(t0) and pd.notna(t1):
            windows["intensification"] = (pd.Timestamp(t0), pd.Timestamp(t1))

    return windows


def _phase_mean(
    series: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> float:
    """Mean of a time series within [start, end]; NaN if no data."""
    mask = (series.index >= start) & (series.index <= end)
    sub = series.loc[mask]
    return float(sub.mean()) if len(sub) > 0 else np.nan


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_all(limit: Optional[int], verbose: bool) -> tuple[pd.DataFrame, dict]:
    """Process all EP1 cyclones and return (wide_df, validation_dict)."""

    # ── load EP1 case list ────────────────────────────────────────────────────
    if not EP1_FILE.exists():
        sys.exit(
            f"ERROR: EP1 cases file not found: {EP1_FILE}\n"
            "Run scripts/ep_structure_analysis/ first."
        )
    ep1_cases = pd.read_csv(EP1_FILE, dtype={"track_id": str})
    for col in ("intensification_start", "intensification_end"):
        if col in ep1_cases.columns:
            ep1_cases[col] = pd.to_datetime(ep1_cases[col])

    ep1_cases = ep1_cases.drop_duplicates(subset="track_id").set_index("track_id")

    if limit:
        ep1_cases = ep1_cases.head(limit)

    all_ids    = list(ep1_cases.index)
    n_expected = len(all_ids)

    if verbose:
        print(f"EP1 cyclones to process: {n_expected}")

    # ── per-cyclone processing ────────────────────────────────────────────────
    rows_wide = []        # one row per cyclone (for subterms_by_cyclone.csv)
    rows_tidy = []        # one row per (cyclone, phase, subterm) for boxplot input

    # validation counters
    n_missing_dir       = 0
    n_missing_vl_dir    = 0
    n_missing_ck_files  = 0
    n_processed         = 0
    missing_files: list[str] = []
    found_subterm_names: set[str] = set()

    for tid in all_ids:
        ep1_row = ep1_cases.loc[tid]

        rec: dict = {"track_id": tid}

        # Check LEC directory
        lec_d = _lec_dir(tid)
        if not lec_d.exists():
            n_missing_dir += 1
            missing_files.append(f"{tid}: LEC directory missing")
            rec["status"] = "missing_lec_dir"
            rows_wide.append(rec)
            continue

        vl_d = _vl_dir(tid)
        if not vl_d.exists():
            n_missing_vl_dir += 1
            missing_files.append(f"{tid}: results_vertical_levels/ missing")
            rec["status"] = "missing_vl_dir"
            rows_wide.append(rec)
            continue

        # Load all subterm time series
        ts: dict[str, pd.Series] = {}
        any_missing = False
        for stem in ALL_STEMS:
            csv_path = _pressure_level_csv(tid, stem)
            df_pl = _load_pressure_level_csv(csv_path)
            if df_pl is None:
                # Also try without '_pressure_level' suffix for older naming
                alt_path = vl_d / f"{stem}_level.csv"
                df_pl = _load_pressure_level_csv(alt_path)
            if df_pl is None:
                # Try generic glob search
                matches = list(vl_d.glob(f"{stem}*.csv"))
                if matches:
                    df_pl = _load_pressure_level_csv(matches[0])
            if df_pl is not None:
                ts[stem] = _vertically_integrate(df_pl)
                found_subterm_names.add(stem)
            else:
                if stem != CK_TOTAL_STEM:
                    any_missing = True
                    missing_files.append(f"{tid}: {stem}_pressure_level.csv missing")

        if any_missing or len(ts) == 0:
            n_missing_ck_files += 1
            rec["status"] = "missing_ck_files"
            rows_wide.append(rec)
            continue

        # Phase windows
        phase_wins = _phase_windows_for_cyclone(tid, ep1_row)
        if not phase_wins:
            rec["status"] = "no_phase_info"
            rows_wide.append(rec)
            continue

        # Compute phase means for each subterm
        rec["status"] = "ok"
        for phase, (t0, t1) in phase_wins.items():
            for stem, series in ts.items():
                col = f"{stem}_{phase}"
                rec[col] = _phase_mean(series, t0, t1)
                # Tidy row
                rows_tidy.append({
                    "track_id": tid,
                    "phase": phase,
                    "subterm": SUBTERM_LABELS.get(stem, stem),
                    "subterm_raw": stem,
                    "value": rec[col],
                    "units": "W m-2",
                })

        # Dominant subterm (most negative mean during intensification, if available)
        if "intensification" in phase_wins:
            t0, t1 = phase_wins["intensification"]
            subterm_means = {
                s: _phase_mean(ts[s], t0, t1)
                for s in CK_SUBTERM_STEMS
                if s in ts
            }
            valid = {k: v for k, v in subterm_means.items() if not np.isnan(v)}
            if valid:
                rec["dominant_subterm"] = SUBTERM_LABELS.get(
                    min(valid, key=valid.get),  # most negative
                    min(valid, key=valid.get),
                )

        n_processed += 1
        rows_wide.append(rec)

        if verbose and n_processed % 50 == 0:
            print(f"  … {n_processed} / {n_expected} processed")

    wide_df = pd.DataFrame(rows_wide)
    tidy_df = pd.DataFrame(rows_tidy)

    # ── validation dict ───────────────────────────────────────────────────────
    n_ok     = int((wide_df.get("status", pd.Series()) == "ok").sum())
    n_failed = n_expected - n_ok
    validation = {
        "n_expected":        n_expected,
        "n_processed_ok":    n_ok,
        "n_failed":          n_failed,
        "n_missing_lec_dir": n_missing_dir,
        "n_missing_vl_dir":  n_missing_vl_dir,
        "n_missing_ck_files":n_missing_ck_files,
        "subterms_found":    sorted(found_subterm_names),
        "missing_files_sample": missing_files[:20],
    }

    return wide_df, tidy_df, validation


# ============================================================================
# OUTPUT WRITERS
# ============================================================================

def _write_subterms_by_cyclone(wide_df: pd.DataFrame) -> Path:
    """Save subterms_by_cyclone.csv — one row per cyclone."""
    ok = wide_df[wide_df.get("status", pd.Series(dtype=str)) == "ok"].copy()
    # Keep only per-cyclone summary columns
    out = OUT_DIR / "subterms_by_cyclone.csv"
    ok.to_csv(out, index=False)
    return out


def _write_subterms_by_phase(wide_df: pd.DataFrame) -> Path:
    """Save subterms_by_phase.csv — melt phase-specific columns."""
    ok = wide_df[wide_df.get("status", pd.Series(dtype=str)) == "ok"].copy()

    # Identify phase-mean columns (e.g. Ck_1_intensification)
    phase_cols = [
        c for c in ok.columns
        if any(c.endswith(f"_{ph}") for ph in ALL_PHASES)
    ]
    id_cols = ["track_id", "dominant_subterm"]
    id_cols = [c for c in id_cols if c in ok.columns]

    melted = ok[id_cols + phase_cols].melt(
        id_vars=id_cols,
        value_vars=phase_cols,
        var_name="subterm_phase",
        value_name="value",
    )

    def _split(col: str):
        for ph in sorted(ALL_PHASES, key=len, reverse=True):
            if col.endswith(f"_{ph}"):
                raw_stem = col[: -(len(ph) + 1)]
                return SUBTERM_LABELS.get(raw_stem, raw_stem), ph
        return col, "unknown"

    melted[["subterm", "phase"]] = pd.DataFrame(
        melted["subterm_phase"].map(_split).tolist(), index=melted.index
    )
    melted = melted.drop(columns=["subterm_phase"])
    melted["units"] = "W m-2"

    out = OUT_DIR / "subterms_by_phase.csv"
    melted.to_csv(out, index=False)
    return out


def _write_boxplot_input(tidy_df: pd.DataFrame) -> Path:
    """Save ck_subterms_boxplot_input.csv — tidy long format."""
    tidy_df = tidy_df.dropna(subset=["value"])
    out = OUT_DIR / "ck_subterms_boxplot_input.csv"
    tidy_df.to_csv(out, index=False)
    return out


def _write_report(validation: dict, paths: list[Path]) -> Path:
    """Save summary_build_report.md."""
    v = validation
    lines = [
        "# Ck Subterms Summary — Build Report",
        "",
        f"Generated by `build_ck_subterms_summary.py`",
        "",
        "## Validation",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| EP1 cyclones expected   | {v['n_expected']} |",
        f"| Cyclones processed (ok) | {v['n_processed_ok']} |",
        f"| Failed / skipped        | {v['n_failed']} |",
        f"| Missing LEC directory   | {v['n_missing_lec_dir']} |",
        f"| Missing vertical levels | {v['n_missing_vl_dir']} |",
        f"| Missing Ck CSV files    | {v['n_missing_ck_files']} |",
        "",
        "## Subterms Found",
        "",
    ]
    if v["subterms_found"]:
        for s in v["subterms_found"]:
            label = SUBTERM_LABELS.get(s, s)
            lines.append(f"- `{s}` → `{label}`")
    else:
        lines.append("- *(none)*")

    if v["missing_files_sample"]:
        lines += [
            "",
            "## Missing Files (first 20)",
            "",
        ]
        for mf in v["missing_files_sample"]:
            lines.append(f"- {mf}")

    lines += [
        "",
        "## Output Files",
        "",
    ]
    for p in paths:
        rel = p.relative_to(BASE_DIR)
        lines.append(f"- `{rel}`")

    out = OUT_DIR / "summary_build_report.md"
    out.write_text("\n".join(lines) + "\n")
    return out


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Build Ck subterms summary CSVs from LEC results."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print progress information.",
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Process only first N cyclones (for quick testing).",
    )
    args = parser.parse_args()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" build_ck_subterms_summary.py — Ck Subterms Consolidation")
    print(f" LEC results : {LEC_DIR}")
    print(f" Output      : {OUT_DIR}")
    if args.limit:
        print(f" (limited to first {args.limit} cyclones)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    wide_df, tidy_df, validation = process_all(
        limit=args.limit, verbose=args.verbose
    )

    print(f"  Processed ok  : {validation['n_processed_ok']} / {validation['n_expected']}")
    print(f"  Failed/skipped: {validation['n_failed']}")
    print(f"  Subterms found: {validation['subterms_found']}")
    print()

    written: list[Path] = []

    p1 = _write_subterms_by_cyclone(wide_df)
    print(f"  ✔  {p1.relative_to(BASE_DIR)}")
    written.append(p1)

    p2 = _write_subterms_by_phase(wide_df)
    print(f"  ✔  {p2.relative_to(BASE_DIR)}")
    written.append(p2)

    p3 = _write_boxplot_input(tidy_df)
    print(f"  ✔  {p3.relative_to(BASE_DIR)}")
    written.append(p3)

    p4 = _write_report(validation, written)
    print(f"  ✔  {p4.relative_to(BASE_DIR)}")
    written.append(p4)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if validation["n_failed"] > 0:
        print(f" WARNING: {validation['n_failed']} cyclone(s) could not be processed.")
        print(f"          Check {p4.relative_to(BASE_DIR)} for details.")
    else:
        print(" All cyclones processed successfully.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
