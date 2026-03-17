#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEC Results Audit — Coverage and integrity check of locally computed Ck subterms.

Audits the energetic results calculated by the local LorenzCycleToolkit pipeline,
stored in results/ck_analysis/lec_results/.  For each EP1 cyclone, verifies:
  - presence and readability of LEC output directories and files
  - integrity of Ck pressure-level CSV files (Ck total + Ck_1...Ck_5 subterms)
  - data coverage within the intensification phase
  - eligibility for dominance classification

Outputs (in results/ck_subterms/):
  lec_audit_per_cyclone.csv  — per-cyclone audit rows with status and failure reason
  lec_audit_summary.csv      — aggregate counts
  lec_audit_summary.json     — same summary as JSON (consumed by web manifest)
  lec_audit_report.txt       — human-readable diagnostic report

Usage:
    python scripts/ck_subterms_analysis/lec_audit.py

    # or import and call run_audit() from another script:
    from scripts.ck_subterms_analysis.lec_audit import run_audit
    audit_df, summary = run_audit()

Author: Danilo Couto de Souza / GitHub Copilot
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ── project root on sys.path ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

# ── paths ────────────────────────────────────────────────────────────────────
EP1_CASES_FILE = BASE_DIR / "results" / "ep_structure" / "ep1_cases.csv"
LEC_DIR        = BASE_DIR / "results" / "ck_analysis" / "lec_results"
RESULTS_DIR    = BASE_DIR / "results" / "ck_subterms"

# Expected Ck subterm file stems (prefix before "_pressure_level.csv")
CK_TOTAL_STEM   = "Ck"
CK_SUBTERM_STEMS = ["Ck_1", "Ck_2", "Ck_3", "Ck_4", "Ck_5"]

# Optional: tolerance for consistency check between Ck_total and sum(Ck_1..5).
# Set to None to skip the check.  The comparison may not be exact because
# Ck_total in the results CSV is aggregated differently from the per-level files.
# Only enable this if you are certain the aggregation is identical.
CK_CONSISTENCY_TOLERANCE = None   # e.g. 0.10 = 10 % relative difference

# Exclusion reason codes (ordered from earliest to latest failure in the pipeline)
REASONS = {
    "missing_lec_directory":       "LEC output directory not found",
    "missing_results_csv":         "Main <track_id>_results.csv not found",
    "missing_vertical_levels_dir": "results_vertical_levels/ directory not found",
    "missing_ck_total_file":       "Ck_pressure_level.csv not found",
    "missing_ck_subterm_file":     "One or more Ck_1..5_pressure_level.csv missing",
    "empty_ck_file":               "At least one Ck CSV file is empty (0 bytes or 0 rows)",
    "unreadable_ck_file":          "At least one Ck CSV file cannot be parsed by pandas",
    "all_nan_ck_file":             "At least one Ck CSV has all-NaN numeric data",
    "no_data_in_intensification_phase": "No timesteps fall within the intensification window",
    "cannot_compute_dominance":    "Cannot compute dominance (less than 2 non-NaN subterm values)",
    "missing_intensification_window": "Intensification window not available for this cyclone",
    "missing_track_data":          "Track not found in the main track database",
}


# ============================================================================
# HELPERS
# ============================================================================

def _lec_dir_for(track_id: str) -> Path:
    """Return expected LEC output directory for a given track_id."""
    return LEC_DIR / f"{track_id}_ERA5_track"


def _check_file(path: Path) -> str | None:
    """
    Perform basic file-level checks.

    Returns an exclusion reason code on the first failure, or None if all pass.
    """
    if not path.exists():
        return None  # existence must be checked by the caller
    if path.stat().st_size == 0:
        return "empty_ck_file"
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True, nrows=5)
        if df.empty:
            return "empty_ck_file"
    except Exception:
        return "unreadable_ck_file"
    return None


def _load_csv(path: Path) -> pd.DataFrame | None:
    """Load a pressure-level CSV; return None on failure."""
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df if not df.empty else None
    except Exception:
        return None


def _vertically_integrate(df: pd.DataFrame, gravity: float = 9.8) -> pd.Series:
    """Vertically integrate a pressure-level DataFrame → time series (W/m²)."""
    cols = df.columns.astype(float)
    sorted_cols = np.sort(cols)
    n = len(sorted_cols)
    dp = np.zeros(n)
    if n == 1:
        dp[0] = sorted_cols[0]
    else:
        dp[0] = (sorted_cols[1] - sorted_cols[0]) / 2.0
        dp[-1] = (sorted_cols[-1] - sorted_cols[-2]) / 2.0
        for i in range(1, n - 1):
            dp[i] = (sorted_cols[i + 1] - sorted_cols[i - 1]) / 2.0
    col_order = df.columns.astype(float)
    dp_map = dict(zip(sorted_cols, dp))
    dp_vals = np.array([dp_map[c] for c in col_order])
    integrated = (df.values * dp_vals[np.newaxis, :] / gravity).sum(axis=1)
    return pd.Series(integrated, index=df.index)


# ============================================================================
# SINGLE-CYCLONE AUDIT
# ============================================================================

def audit_cyclone(
    track_id: str,
    intensif_start: Optional[pd.Timestamp],
    intensif_end: Optional[pd.Timestamp],
) -> dict:
    """
    Audit a single cyclone's LEC results.

    Parameters
    ----------
    track_id : str
        Cyclone identifier (e.g. '19790166').
    intensif_start, intensif_end : pd.Timestamp or None
        Intensification phase window from ep1_cases.csv.

    Returns
    -------
    dict with keys:
        track_id, status ('ok'|'failed'), failure_reason,
        has_lec_dir, has_results_csv, has_vertical_levels_dir,
        has_ck_total_file, has_all_ck_subterm_files, all_ck_files_non_empty,
        all_ck_files_readable, any_ck_all_nan, has_data_in_intensif,
        n_intensif_timesteps, subterm_means (dict), dominant_subterm,
        ck_total_intensif, subterms_sum, ck_consistency_ok,
        usable_for_dominance, usable_for_boxplots, usable_for_genesis_maps,
        usable_for_tracks
    """
    rec: dict = {
        "track_id": track_id,
        "status": "failed",
        "failure_reason": None,
        "has_lec_dir": False,
        "has_results_csv": False,
        "has_vertical_levels_dir": False,
        "has_ck_total_file": False,
        "has_all_ck_subterm_files": False,
        "all_ck_files_non_empty": False,
        "all_ck_files_readable": False,
        "any_ck_all_nan": False,
        "has_data_in_intensif": False,
        "n_intensif_timesteps": 0,
        "ck_total_intensif": np.nan,
        "Ck_1_intensif": np.nan,
        "Ck_2_intensif": np.nan,
        "Ck_3_intensif": np.nan,
        "Ck_4_intensif": np.nan,
        "Ck_5_intensif": np.nan,
        "subterms_sum": np.nan,
        "dominant_subterm": None,
        "ck_consistency_ok": None,
        "usable_for_dominance": False,
        "usable_for_boxplots": False,
        "usable_for_genesis_maps": False,
        "usable_for_tracks": False,
    }

    # ── 1. LEC directory ─────────────────────────────────────────────────────
    lec_dir = _lec_dir_for(track_id)
    rec["has_lec_dir"] = lec_dir.exists()
    if not rec["has_lec_dir"]:
        rec["failure_reason"] = "missing_lec_directory"
        return rec

    # ── 2. Main results CSV ──────────────────────────────────────────────────
    results_csv = lec_dir / f"{track_id}_ERA5_track_results.csv"
    rec["has_results_csv"] = results_csv.exists()
    if not rec["has_results_csv"]:
        rec["failure_reason"] = "missing_results_csv"
        return rec

    # ── 3. results_vertical_levels/ ─────────────────────────────────────────
    vl_dir = lec_dir / "results_vertical_levels"
    rec["has_vertical_levels_dir"] = vl_dir.exists()
    if not rec["has_vertical_levels_dir"]:
        rec["failure_reason"] = "missing_vertical_levels_dir"
        return rec

    # ── 4. Ck total file ─────────────────────────────────────────────────────
    ck_total_path = vl_dir / "Ck_pressure_level.csv"
    rec["has_ck_total_file"] = ck_total_path.exists()
    if not rec["has_ck_total_file"]:
        rec["failure_reason"] = "missing_ck_total_file"
        return rec

    # ── 5. Ck subterm files ──────────────────────────────────────────────────
    subterm_paths = {k: vl_dir / f"{k}_pressure_level.csv" for k in CK_SUBTERM_STEMS}
    missing_subterms = [k for k, p in subterm_paths.items() if not p.exists()]
    rec["has_all_ck_subterm_files"] = len(missing_subterms) == 0
    if not rec["has_all_ck_subterm_files"]:
        rec["failure_reason"] = "missing_ck_subterm_file"
        return rec

    # ── 6. Non-empty and readable ────────────────────────────────────────────
    all_paths = [ck_total_path] + list(subterm_paths.values())
    for p in all_paths:
        err = _check_file(p)
        if err == "empty_ck_file":
            rec["failure_reason"] = "empty_ck_file"
            return rec
        if err == "unreadable_ck_file":
            rec["failure_reason"] = "unreadable_ck_file"
            return rec
    rec["all_ck_files_non_empty"] = True
    rec["all_ck_files_readable"] = True

    # ── 7. All-NaN check ─────────────────────────────────────────────────────
    for p in all_paths:
        df_check = _load_csv(p)
        if df_check is None:
            rec["failure_reason"] = "unreadable_ck_file"
            return rec
        numeric = df_check.select_dtypes(include=[np.number])
        if numeric.empty or numeric.isnull().all().all():
            rec["any_ck_all_nan"] = True
            rec["failure_reason"] = "all_nan_ck_file"
            return rec

    # ── 8. Intensification window availability ───────────────────────────────
    if intensif_start is None or intensif_end is None or pd.isnull(intensif_start) or pd.isnull(intensif_end):
        rec["failure_reason"] = "missing_intensification_window"
        return rec

    # ── 9. Data within intensification window ────────────────────────────────
    subterm_dfs: dict[str, pd.DataFrame] = {}
    for k, p in subterm_paths.items():
        df_k = _load_csv(p)
        if df_k is None:
            rec["failure_reason"] = "unreadable_ck_file"
            return rec
        df_k.index = pd.to_datetime(df_k.index, errors="coerce")
        sub = df_k.loc[(df_k.index >= intensif_start) & (df_k.index <= intensif_end)]
        if len(sub) == 0:
            rec["failure_reason"] = "no_data_in_intensification_phase"
            return rec
        subterm_dfs[k] = sub

    # Use first subterm to count timesteps in the window (all should match)
    first_key = CK_SUBTERM_STEMS[0]
    rec["n_intensif_timesteps"] = len(subterm_dfs[first_key])
    rec["has_data_in_intensif"] = True

    # ── 10. Compute subterm means (vertically integrated) ────────────────────
    subterm_means: dict[str, float] = {}
    for k, sub in subterm_dfs.items():
        try:
            integrated = _vertically_integrate(sub)
            val = float(integrated.mean())
            subterm_means[k] = val
            rec[f"{k}_intensif"] = val
        except Exception:
            rec["failure_reason"] = "cannot_compute_dominance"
            return rec

    vals = np.array([subterm_means[k] for k in CK_SUBTERM_STEMS])
    n_valid_vals = np.sum(~np.isnan(vals))
    if n_valid_vals < 2:
        rec["failure_reason"] = "cannot_compute_dominance"
        return rec

    rec["subterms_sum"] = float(np.nansum(vals))
    dom_idx = int(np.nanargmin(vals))
    rec["dominant_subterm"] = CK_SUBTERM_STEMS[dom_idx]

    # ── 11. Ck total from main results CSV ───────────────────────────────────
    try:
        df_main = pd.read_csv(results_csv, index_col=0, parse_dates=True)
        df_main.index = pd.to_datetime(df_main.index, errors="coerce")
        sub_main = df_main.loc[
            (df_main.index >= intensif_start) & (df_main.index <= intensif_end)
        ]
        if "Ck" in df_main.columns and len(sub_main) > 0:
            rec["ck_total_intensif"] = float(sub_main["Ck"].mean())
    except Exception:
        pass  # ck_total is optional; failure here does not block usability

    # ── 12. Optional consistency check ───────────────────────────────────────
    if CK_CONSISTENCY_TOLERANCE is not None and not np.isnan(rec["ck_total_intensif"]):
        ck_total = rec["ck_total_intensif"]
        ck_sum = rec["subterms_sum"]
        if abs(ck_total) > 1e-12:
            rel_diff = abs(ck_total - ck_sum) / abs(ck_total)
            rec["ck_consistency_ok"] = bool(rel_diff <= CK_CONSISTENCY_TOLERANCE)
        else:
            rec["ck_consistency_ok"] = abs(ck_sum) < 1e-12

    # ── All checks passed ────────────────────────────────────────────────────
    rec["status"] = "ok"
    rec["usable_for_dominance"] = True
    rec["usable_for_boxplots"] = True
    rec["usable_for_genesis_maps"] = True
    rec["usable_for_tracks"] = True

    return rec


# ============================================================================
# BATCH AUDIT
# ============================================================================

def run_audit(
    ep1_cases_file: Path = EP1_CASES_FILE,
    lec_dir: Path = LEC_DIR,
    results_dir: Path = RESULTS_DIR,
    verbose: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Run the full LEC audit for all EP1 cyclones.

    Parameters
    ----------
    ep1_cases_file : Path
        Path to ep_structure/ep1_cases.csv (source of EP1 track_ids and phases).
    lec_dir : Path
        Root directory of LEC results.
    results_dir : Path
        Output directory for audit files.
    verbose : bool
        If True, print progress.

    Returns
    -------
    audit_df : pd.DataFrame
        Per-cyclone audit results.
    summary : dict
        Aggregate statistics.
    """
    results_dir.mkdir(parents=True, exist_ok=True)

    # ── Load EP1 cases ────────────────────────────────────────────────────────
    if not ep1_cases_file.exists():
        raise FileNotFoundError(f"EP1 cases file not found: {ep1_cases_file}")

    ep1_cases = pd.read_csv(ep1_cases_file)
    ep1_cases["intensification_start"] = pd.to_datetime(ep1_cases["intensification_start"])
    ep1_cases["intensification_end"]   = pd.to_datetime(ep1_cases["intensification_end"])
    n_expected = len(ep1_cases)

    if verbose:
        print(f"\n{'='*70}")
        print("LEC RESULTS AUDIT — coverage and integrity of locally computed Ck subterms")
        print(f"{'='*70}")
        print(f"  EP1 cases file : {ep1_cases_file.relative_to(BASE_DIR)}")
        print(f"  LEC results dir: {lec_dir.relative_to(BASE_DIR)}")
        print(f"  EP1 cyclones expected: {n_expected}")
        print()

    # ── Audit each cyclone ────────────────────────────────────────────────────
    records = []
    for _, row in ep1_cases.iterrows():
        tid = str(row["track_id"])
        t0 = row.get("intensification_start")
        t1 = row.get("intensification_end")
        rec = audit_cyclone(tid, t0, t1)
        records.append(rec)

    audit_df = pd.DataFrame(records)

    # ── Compute summary ───────────────────────────────────────────────────────
    n_lec_dir        = int(audit_df["has_lec_dir"].sum())
    n_results_csv    = int(audit_df["has_results_csv"].sum())
    n_vl_dir         = int(audit_df["has_vertical_levels_dir"].sum())
    n_ck_total       = int(audit_df["has_ck_total_file"].sum())
    n_all_subterms   = int(audit_df["has_all_ck_subterm_files"].sum())
    n_readable       = int(audit_df["all_ck_files_readable"].sum())
    n_intensif       = int(audit_df["has_data_in_intensif"].sum())
    n_usable         = int(audit_df["usable_for_dominance"].sum())
    n_failed         = int((audit_df["status"] == "failed").sum())

    reason_counts = Counter(
        audit_df.loc[audit_df["status"] == "failed", "failure_reason"].dropna().tolist()
    )

    summary = {
        "n_ep1_expected": n_expected,
        "n_lec_directory_found": n_lec_dir,
        "n_with_results_csv": n_results_csv,
        "n_with_vertical_levels_dir": n_vl_dir,
        "n_with_ck_total_file": n_ck_total,
        "n_with_all_ck_subterm_files": n_all_subterms,
        "n_with_readable_ck_files": n_readable,
        "n_with_data_in_intensif_phase": n_intensif,
        "n_usable_for_dominance": n_usable,
        "n_failed": n_failed,
        "exclusion_reasons": dict(reason_counts),
    }

    # ── Write outputs ─────────────────────────────────────────────────────────
    _write_per_cyclone_csv(audit_df, results_dir)
    _write_summary_csv(summary, results_dir)
    _write_summary_json(summary, results_dir)
    _write_report(audit_df, summary, results_dir)

    if verbose:
        _print_summary(summary)

    return audit_df, summary


# ============================================================================
# OUTPUT WRITERS
# ============================================================================

def _write_per_cyclone_csv(audit_df: pd.DataFrame, out_dir: Path) -> None:
    out = out_dir / "lec_audit_per_cyclone.csv"
    audit_df.to_csv(out, index=False)
    print(f"  [audit] Saved: {out.relative_to(BASE_DIR)}")


def _write_summary_csv(summary: dict, out_dir: Path) -> None:
    # Flatten exclusion_reasons into the row
    flat = {k: v for k, v in summary.items() if k != "exclusion_reasons"}
    for reason, count in summary.get("exclusion_reasons", {}).items():
        flat[f"excl_{reason}"] = count
    pd.DataFrame([flat]).to_csv(out_dir / "lec_audit_summary.csv", index=False)
    print(f"  [audit] Saved: {(out_dir / 'lec_audit_summary.csv').relative_to(BASE_DIR)}")


def _write_summary_json(summary: dict, out_dir: Path) -> None:
    out = out_dir / "lec_audit_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  [audit] Saved: {out.relative_to(BASE_DIR)}")


def _write_report(audit_df: pd.DataFrame, summary: dict, out_dir: Path) -> None:
    out = out_dir / "lec_audit_report.txt"
    lines = _build_report_lines(audit_df, summary)
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  [audit] Saved: {out.relative_to(BASE_DIR)}")


def _build_report_lines(audit_df: pd.DataFrame, summary: dict) -> list[str]:
    s = summary
    n_exp  = s["n_ep1_expected"]
    n_lec  = s["n_lec_directory_found"]
    n_vl   = s["n_with_vertical_levels_dir"]
    n_ckt  = s["n_with_ck_total_file"]
    n_cks  = s["n_with_all_ck_subterm_files"]
    n_ok   = s["n_usable_for_dominance"]
    n_fail = s["n_failed"]

    lines = [
        "=" * 70,
        "LEC RESULTS AUDIT REPORT",
        "Coverage and integrity of locally computed Ck subterms",
        "=" * 70,
        "",
        "Source: results/ck_analysis/lec_results/",
        "EP1 cases: results/ep_structure/ep1_cases.csv",
        "",
        "── PIPELINE FUNNEL ──────────────────────────────────────────────────",
        f"  EP1 cyclones expected (ep1_cases.csv)    : {n_exp}",
        f"  LEC directories found                    : {n_lec}  ({_pct(n_lec, n_exp)}%)",
        f"  with results_vertical_levels/            : {n_vl}  ({_pct(n_vl, n_exp)}%)",
        f"  with Ck_pressure_level.csv               : {n_ckt}  ({_pct(n_ckt, n_exp)}%)",
        f"  with all Ck_1..5_pressure_level.csv      : {n_cks}  ({_pct(n_cks, n_exp)}%)",
        f"  with valid data in intensif. phase       : {s['n_with_data_in_intensif_phase']}  ({_pct(s['n_with_data_in_intensif_phase'], n_exp)}%)",
        f"  USABLE for dominance classification      : {n_ok}  ({_pct(n_ok, n_exp)}%)",
        "",
        "── EXCLUSION REASONS ────────────────────────────────────────────────",
    ]

    reason_counts = s.get("exclusion_reasons", {})
    if reason_counts:
        # Sort by count descending
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
            desc = REASONS.get(reason, reason)
            lines.append(f"  {count:4d}  {reason}")
            lines.append(f"         ({desc})")
    else:
        lines.append("  (none — all cyclones passed)")

    lines += [
        "",
        "── USABLE CYCLONES SUMMARY ─────────────────────────────────────────",
        f"  Usable for boxplots (subterms)           : {n_ok}",
        f"  Usable for dominance classification      : {n_ok}",
        f"  Usable for genesis maps (subset panels)  : {n_ok}",
        f"  Usable for track plots (subset panels)   : {n_ok}",
        f"  Full EP1 population (All EP1 panels)     : {n_exp}",
        "",
        "NOTE: 'All EP1' genesis density and track panels use the full EP1",
        f"population (N={n_exp}).  Boxplots, dominance classification, and",
        "per-subterm panels use only the N={n_ok} usable cyclones.".replace("{n_ok}", str(n_ok)),
        "",
        "── ELIGIBILITY CRITERIA ─────────────────────────────────────────────",
        "  A cyclone is considered usable when ALL of the following hold:",
        "  1. LEC output directory exists in results/ck_analysis/lec_results/",
        "  2. <track_id>_ERA5_track_results.csv exists and is readable",
        "  3. results_vertical_levels/ sub-directory exists",
        "  4. Ck_pressure_level.csv exists and is non-empty",
        "  5. Ck_1_pressure_level.csv ... Ck_5_pressure_level.csv all exist",
        "  6. All CSV files are non-empty, readable, and contain numeric data",
        "  7. At least one timestep falls within the intensification window",
        "     (from results/ep_structure/ep1_cases.csv)",
        "  8. At least 2 subterm values are non-NaN (for dominance comparison)",
        "=" * 70,
    ]
    return lines


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "N/A"
    return f"{100.0 * n / total:.1f}"


def _print_summary(summary: dict) -> None:
    print("── LEC AUDIT SUMMARY ────────────────────────────────────────────────")
    print(f"  EP1 cyclones expected          : {summary['n_ep1_expected']}")
    print(f"  LEC directories found          : {summary['n_lec_directory_found']}")
    print(f"  With Ck_pressure_level.csv     : {summary['n_with_ck_total_file']}")
    print(f"  With all Ck_1..5 subterms      : {summary['n_with_all_ck_subterm_files']}")
    print(f"  With data in intensif. phase   : {summary['n_with_data_in_intensif_phase']}")
    print(f"  USABLE for dominance           : {summary['n_usable_for_dominance']}")
    if summary["exclusion_reasons"]:
        print("  Top exclusion reasons:")
        for reason, count in sorted(summary["exclusion_reasons"].items(), key=lambda x: -x[1])[:5]:
            print(f"    {count:4d}  {reason}")
    print()


# ============================================================================
# MAIN (standalone usage)
# ============================================================================

if __name__ == "__main__":
    audit_df, summary = run_audit(verbose=True)
    print(f"Audit complete. {summary['n_usable_for_dominance']} / "
          f"{summary['n_ep1_expected']} EP1 cyclones are usable for dominance classification.")
