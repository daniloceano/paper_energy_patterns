"""
Diagnostic Script: Step 3 Failure Analysis

Runs on the REMOTE SERVER (master.iag.usp.br) where ERA5 files and results live.

PURPOSE
-------
Answers the following questions without rerunning the full composite pipeline:

  1. How many cases fail per EP, and WHY (file_missing, no_timesteps, OOB, exception)?
  2. How many of the failures came from step2b (legacy reuse) vs step2 (fresh download)?
  3. How many skipped_oob instances are caused by 0-360 longitude convention?
  4. Which cases have the most skipped timesteps?
  5. Are there systematic patterns by EP group?

OUTPUT
------
  - Console summary (copy-paste to local)
  - results/ep_structure/diagnose_step3_failures.csv  (per-case breakdown)
  - results/ep_structure/diagnose_step3_summary.txt    (human-readable summary)

USAGE
-----
  # From project root on remote server
  python scripts/ep_structure_analysis/diagnose_step3_failures.py

  # Diagnose only EP1 (faster)
  python scripts/ep_structure_analysis/diagnose_step3_failures.py --ep 1

  # Limit to first N cases per EP (for quick sanity check)
  python scripts/ep_structure_analysis/diagnose_step3_failures.py --limit 50

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path
import argparse
import traceback

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parents[2]
DATA_DIR       = PROJECT_ROOT / "data" / "era5_ep_structure"
LEGACY_DIR     = PROJECT_ROOT / "data" / "era5_ep_structure_legacy"
RESULTS_DIR    = PROJECT_ROOT / "results" / "ep_structure"
TRACKS_FILE    = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"

DOMAIN_SIZE    = 30.0  # degrees
HALF           = DOMAIN_SIZE / 2.0

ALL_EPS = [1, 2, 3]


# ── Track loading ──────────────────────────────────────────────────────────────
_TRACKS_CACHE = None

def load_tracks_local():
    global _TRACKS_CACHE
    if _TRACKS_CACHE is None:
        if TRACKS_FILE.exists():
            print(f"  Loading tracks from local CSV: {TRACKS_FILE.name}")
            _TRACKS_CACHE = pd.read_csv(TRACKS_FILE, parse_dates=["date"])
        else:
            print("  Local tracks CSV not found, loading from GitHub...")
            from scripts.utils.load_data import load_tracks as _gh_load
            df = _gh_load()
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            _TRACKS_CACHE = df
    return _TRACKS_CACHE


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_selected_times(times_str):
    if pd.isna(times_str) or not times_str:
        return []
    return [pd.to_datetime(t.strip()) for t in str(times_str).split(",")]


def is_legacy_reused(track_id):
    """Return True if the canonical file was created by step2b (has 'source' attr)."""
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    if not nc_file.exists():
        return None  # no file at all
    try:
        with xr.open_dataset(nc_file) as ds:
            return ds.attrs.get("source", "").startswith("Reused from legacy")
    except Exception:
        return None


def get_file_lon_convention(track_id):
    """Return 'neg180_180' or '0_360' or 'unknown' for the ERA5 file."""
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    if not nc_file.exists():
        return "no_file"
    try:
        with xr.open_dataset(nc_file) as ds:
            lon_coord = "longitude" if "longitude" in ds.coords else "lon"
            if lon_coord not in ds.coords:
                return "unknown"
            lons = ds[lon_coord].values
            if lons.max() > 180:
                return "0_360"
            return "neg180_180"
    except Exception:
        return "error"


def check_oob(center_lat, center_lon, ds_lat_min, ds_lat_max, ds_lon_min, ds_lon_max):
    """
    Return (is_oob, reason_str).
    Handles both -180/180 and 0-360 longitude conventions.
    """
    file_uses_0_360 = ds_lon_min >= 0 and ds_lon_max > 180
    if file_uses_0_360 and center_lon < 0:
        center_lon_norm = center_lon + 360.0
    else:
        center_lon_norm = center_lon

    req_lat_min = center_lat - HALF
    req_lat_max = center_lat + HALF
    req_lon_min = center_lon_norm - HALF
    req_lon_max = center_lon_norm + HALF

    reasons = []
    if req_lat_min < ds_lat_min - 0.5 or req_lat_max > ds_lat_max + 0.5:
        reasons.append(
            f"lat[{req_lat_min:.1f},{req_lat_max:.1f}] "
            f"vs file[{ds_lat_min:.1f},{ds_lat_max:.1f}]"
        )
    if req_lon_min < ds_lon_min - 0.5 or req_lon_max > ds_lon_max + 0.5:
        reasons.append(
            f"lon[{req_lon_min:.1f},{req_lon_max:.1f}] "
            f"vs file[{ds_lon_min:.1f},{ds_lon_max:.1f}]"
        )

    # Re-check WITHOUT convention normalisation to detect the bug
    req_lon_raw_min = center_lon - HALF
    req_lon_raw_max = center_lon + HALF
    oob_raw_lon = (
        req_lon_raw_min < ds_lon_min - 0.5
        or req_lon_raw_max > ds_lon_max + 0.5
    )
    oob_norm_lon = bool(reasons and any("lon" in r for r in reasons))
    convention_mismatch = oob_raw_lon and not oob_norm_lon

    return bool(reasons), "; ".join(reasons), convention_mismatch


def diagnose_one_case(row, ep_label):
    """
    Analyse a single cyclone case and return a result dict.

    Keys:
      track_id, ep, status (ok/file_missing/no_meta/no_ts/no_valid_ts/oob_only/exception),
      legacy_reused, lon_convention, n_timesteps_in_file,
      n_skipped_no_pos, n_skipped_oob, n_skipped_oob_convention_mismatch,
      n_used, error_msg
    """
    track_id   = row["track_id"]
    nc_file    = DATA_DIR / f"{track_id}_era5.nc"
    meta_file  = DATA_DIR / f"{track_id}_metadata.csv"

    rec = dict(
        track_id=track_id, ep=ep_label,
        status="ok",
        legacy_reused=False, lon_convention="unknown",
        n_timesteps_in_file=0,
        n_skipped_no_pos=0, n_skipped_oob=0,
        n_skipped_oob_convention_mismatch=0,
        n_used=0, error_msg="",
    )

    # ── File existence ──────────────────────────────────────────────────────
    if not nc_file.exists():
        rec["status"] = "no_nc_file"
        rec["error_msg"] = "ERA5 .nc file missing"
        return rec

    if not meta_file.exists():
        rec["status"] = "no_meta_file"
        rec["error_msg"] = "metadata CSV missing (likely from step2b without fix)"
        rec["legacy_reused"] = is_legacy_reused(track_id) or False
        rec["lon_convention"] = get_file_lon_convention(track_id)
        return rec

    # ── Read file ────────────────────────────────────────────────────────────
    try:
        ds = xr.open_dataset(nc_file)
        meta = pd.read_csv(meta_file).iloc[0]

        rec["legacy_reused"] = ds.attrs.get("source", "").startswith("Reused from legacy")
        lon_coord = "longitude" if "longitude" in ds.coords else "lon"
        if lon_coord in ds.coords:
            lons = ds[lon_coord].values
            rec["lon_convention"] = "0_360" if lons.max() > 180 else "neg180_180"

        tc = "valid_time" if "valid_time" in ds.dims else "time"
        era5_times = pd.to_datetime(ds[tc].values)
        n_times = len(era5_times)
        rec["n_timesteps_in_file"] = n_times

        if n_times == 0:
            ds.close()
            rec["status"] = "no_timesteps"
            rec["error_msg"] = "ERA5 file has 0 timesteps"
            return rec

        # ── Position lookup ──────────────────────────────────────────────────
        tracks = load_tracks_local()
        try:
            track_data = tracks[tracks["track_id"] == int(track_id)].copy()
        except (ValueError, TypeError):
            track_data = tracks[tracks["track_id"] == track_id].copy()

        if len(track_data) == 0:
            ds.close()
            rec["status"] = "track_not_found"
            rec["error_msg"] = "track_id not in tracks CSV"
            return rec

        track_data = track_data.copy()
        track_data["time"] = pd.to_datetime(track_data["date"])

        # Get file lat/lon bounds once
        lat_coord = "latitude" if "latitude" in ds.coords else "lat"
        ds_lat_min = float(ds[lat_coord].min())
        ds_lat_max = float(ds[lat_coord].max())
        ds_lon_min = float(ds[lon_coord].min())
        ds_lon_max = float(ds[lon_coord].max())

        n_no_pos = 0
        n_oob    = 0
        n_oob_conv = 0
        n_used   = 0

        for era5_ts in era5_times:
            time_diffs = (track_data["time"] - era5_ts).abs()
            min_diff = time_diffs.min()
            if min_diff > pd.Timedelta(hours=3):
                n_no_pos += 1
                continue

            nearest = track_data.loc[time_diffs.idxmin()]
            clat = float(nearest["lat vor"])
            clon = float(nearest["lon vor"])

            is_oob, reason, conv_mismatch = check_oob(
                clat, clon, ds_lat_min, ds_lat_max, ds_lon_min, ds_lon_max
            )
            if is_oob:
                n_oob += 1
                if conv_mismatch:
                    n_oob_conv += 1
            else:
                n_used += 1

        ds.close()

        rec["n_skipped_no_pos"]                  = n_no_pos
        rec["n_skipped_oob"]                     = n_oob
        rec["n_skipped_oob_convention_mismatch"] = n_oob_conv
        rec["n_used"]                            = n_used

        if n_used == 0:
            rec["status"] = "no_valid_timesteps"
            rec["error_msg"] = (
                f"all {n_times} timesteps skipped "
                f"(no_pos={n_no_pos}, oob={n_oob})"
            )
        else:
            rec["status"] = "ok"

    except Exception as e:
        rec["status"] = "exception"
        rec["error_msg"] = f"{type(e).__name__}: {e}"

    return rec


def main():
    parser = argparse.ArgumentParser(description="Diagnose step3 failures per EP group")
    parser.add_argument("--ep", type=str, choices=["1", "2", "3", "all"],
                        default="all", help="EP group to diagnose (default: all)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit cases per EP (0 = all, useful for quick test)")
    args = parser.parse_args()

    ep_nums = ALL_EPS if args.ep == "all" else [int(args.ep)]

    print("=" * 72)
    print("STEP 3 FAILURE DIAGNOSTIC")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  ERA5 data dir: {DATA_DIR}")
    print(f"  Legacy dir exists: {LEGACY_DIR.exists()}")
    print("=" * 72)

    all_records = []

    for ep_num in ep_nums:
        ep_label = f"EP{ep_num}"
        cases_file = RESULTS_DIR / f"ep{ep_num}_cases.csv"
        if not cases_file.exists():
            print(f"\n⚠  {ep_label}: cases file not found: {cases_file}")
            continue

        df = pd.read_csv(cases_file)
        if args.limit > 0:
            df = df.head(args.limit)
            print(f"\n{ep_label}: processing first {args.limit} of {len(df)} cases (--limit)")
        else:
            print(f"\n{ep_label}: processing {len(df)} cases...")

        records = []
        for _, row in df.iterrows():
            rec = diagnose_one_case(row, ep_label)
            records.append(rec)

        all_records.extend(records)

        # ── Per-EP summary ───────────────────────────────────────────────────
        df_ep = pd.DataFrame(records)
        status_counts = df_ep["status"].value_counts()
        n_total = len(df_ep)
        n_ok = (df_ep["status"] == "ok").sum()
        n_fail = n_total - n_ok

        print(f"\n  {ep_label} ({n_total} cases):")
        print(f"    ✓ ok              : {n_ok}  ({100*n_ok/n_total:.1f}%)")
        print(f"    ✗ failed          : {n_fail} ({100*n_fail/n_total:.1f}%)")
        print(f"    Failure breakdown :")
        for status, cnt in status_counts.items():
            if status != "ok":
                pct = 100 * cnt / n_total
                print(f"      {status:<30}: {cnt}  ({pct:.1f}%)")

        # Legacy reuse breakdown
        n_legacy = df_ep["legacy_reused"].sum()
        n_legacy_fail = df_ep[df_ep["legacy_reused"] & (df_ep["status"] != "ok")].shape[0]
        print(f"    Legacy reused     : {n_legacy}")
        if n_legacy:
            print(f"      of which failed : {n_legacy_fail}")

        # Longitude convention breakdown
        conv_counts = df_ep["lon_convention"].value_counts()
        print(f"    Lon convention    : {dict(conv_counts)}")
        n_oob_conv = df_ep["n_skipped_oob_convention_mismatch"].sum()
        if n_oob_conv:
            print(f"    ⚠  OOB caused by 0-360 vs -180/180 mismatch: {n_oob_conv} timesteps")

        # Timestep stats
        total_ts = df_ep["n_timesteps_in_file"].sum()
        total_oob = df_ep["n_skipped_oob"].sum()
        total_no_pos = df_ep["n_skipped_no_pos"].sum()
        total_used = df_ep["n_used"].sum()
        print(f"    Timestep totals   :")
        print(f"      in files        : {total_ts}")
        print(f"      used            : {total_used}")
        print(f"      skipped no_pos  : {total_no_pos}")
        print(f"      skipped oob     : {total_oob}")

    # ── Global summary ───────────────────────────────────────────────────────
    if not all_records:
        print("\nNo records collected.")
        return

    df_all = pd.DataFrame(all_records)

    print("\n" + "=" * 72)
    print("OVERALL SUMMARY")
    print("=" * 72)

    n_total = len(df_all)
    n_ok = (df_all["status"] == "ok").sum()
    n_fail = n_total - n_ok
    print(f"  Total cases      : {n_total}")
    print(f"  ✓ OK             : {n_ok}  ({100*n_ok/n_total:.1f}%)")
    print(f"  ✗ Failed         : {n_fail} ({100*n_fail/n_total:.1f}%)")
    print()

    status_counts = df_all["status"].value_counts()
    print("  Status breakdown:")
    for status, cnt in status_counts.items():
        pct = 100 * cnt / n_total
        print(f"    {status:<35}: {cnt}  ({pct:.1f}%)")

    print()
    n_legacy_total = df_all["legacy_reused"].sum()
    n_legacy_fail  = df_all[df_all["legacy_reused"] & (df_all["status"] != "ok")].shape[0]
    print(f"  Legacy-reused files : {n_legacy_total}")
    print(f"    of which failed   : {n_legacy_fail}")

    conv_counts = df_all["lon_convention"].value_counts()
    print(f"\n  Longitude conventions in ERA5 files: {dict(conv_counts)}")
    n_oob_conv = df_all["n_skipped_oob_convention_mismatch"].sum()
    print(f"  OOB timesteps caused by 0-360/−180−180 mismatch: {n_oob_conv}")

    total_oob   = df_all["n_skipped_oob"].sum()
    total_nopos = df_all["n_skipped_no_pos"].sum()
    total_used  = df_all["n_used"].sum()
    print(f"\n  Timestep totals:")
    print(f"    in files        : {df_all['n_timesteps_in_file'].sum()}")
    print(f"    used            : {total_used}")
    print(f"    skipped no_pos  : {total_nopos}")
    print(f"    skipped oob     : {total_oob}")

    # ── Examples of each failure category ────────────────────────────────────
    print()
    print("  Example cases by failure type (up to 5 per category):")
    for status in status_counts.index:
        if status == "ok":
            continue
        examples = df_all[df_all["status"] == status]["track_id"].head(5).tolist()
        print(f"    {status}: {examples}")

    # ── Save outputs ──────────────────────────────────────────────────────────
    out_csv = RESULTS_DIR / "diagnose_step3_failures.csv"
    df_all.to_csv(out_csv, index=False)
    print(f"\n  Detailed CSV saved: {out_csv}")

    summary_txt = RESULTS_DIR / "diagnose_step3_summary.txt"
    with open(summary_txt, "w") as f:
        f.write(f"Step3 diagnostic — {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Total: {n_total}  OK: {n_ok}  Failed: {n_fail}\n\n")
        f.write("Status breakdown:\n")
        for status, cnt in status_counts.items():
            f.write(f"  {status}: {cnt}\n")
        f.write(f"\nLegacy-reused failed: {n_legacy_fail} / {n_legacy_total}\n")
        f.write(f"OOB convention mismatch timesteps: {n_oob_conv}\n")
    print(f"  Summary TXT saved: {summary_txt}")
    print()
    print("=" * 72)
    print("Copy results/ep_structure/diagnose_step3_*.* back to local machine.")
    print("=" * 72)


if __name__ == "__main__":
    main()
