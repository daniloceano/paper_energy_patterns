"""
Step 2: Download ERA5 Data in Parallel for EP1 + EP2 Cyclones

Downloads ERA5 reanalysis data for all EP1 and EP2 cyclones during their
entire intensification phase.

Variables Downloaded:
- Pressure levels: u, v, t, z, q
- Single level: msl (mean sea level pressure)

Targeted Pressure Levels (hPa):
  175, 200, 225    → PV at 200 hPa  (centered FD: ∂θ/∂p)
  250              → EGR upper bound + jet diagnostics
  500              → Mid-tropospheric reference
  825, 850, 875    → PV at 850 hPa  (centered FD: ∂θ/∂p)
                     + temperature advection at 850 hPa
                     + EGR lower bound

Total: 8 levels

Domain: 30° × 30° centred on cyclone track centre during intensification.

Logging strategy (for nohup execution):
- Detailed step-by-step → log file (via logging)
- Concise summary + tqdm progress → stdout (visible in nohup.out)

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path
import argparse

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime
import cdsapi
import multiprocessing as mp
import time
import logging

from scripts.utils.load_data import load_tracks
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

MAX_PARALLEL_JOBS = 10  # Conservative CDS API limit

# Variables
PRESSURE_VARS = [
    "u_component_of_wind",
    "v_component_of_wind",
    "temperature",
    "geopotential",
    "specific_humidity",
]

SINGLE_LEVEL_VARS = ["mean_sea_level_pressure"]

# Pressure levels (hPa) — targeted for EGR(250-850), PV@200, PV@850, T_adv@850, moisture flux@975
PRESSURE_LEVELS = [
    175, 200, 225,   # PV at 200 hPa (centred FD)
    250,             # EGR upper bound + jet
    500,             # Mid-troposphere reference
    825, 850, 875,   # PV at 850 hPa (centred FD) + EGR lower bound + T advection
    975,             # Moisture flux divergence (low-level moisture transport)
]

DOMAIN_BUFFER = 15  # degrees → 30° × 30° domain

# NetCDF variable name mapping
NCVAR_PRESSURE = {
    "u_component_of_wind": "u",
    "v_component_of_wind": "v",
    "temperature": "t",
    "geopotential": "z",
    "specific_humidity": "q",
}
NCVAR_SINGLE = {"mean_sea_level_pressure": "msl"}


# ============================================================================
# Logging helpers
# ============================================================================

def _log_and_print(msg, level="info"):
    """Write to log file AND print a concise version to stdout."""
    getattr(logging, level)(msg)


def _print_only(msg):
    """Print to stdout only (visible in nohup.out). No log."""
    print(msg, flush=True)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_netcdf_file(nc_file, expected_pvars, expected_svars, expected_levels):
    """
    Validate NetCDF file integrity and completeness.

    Returns (valid, issues, missing_vars, missing_levels).
    """
    issues = []
    missing_vars = []
    missing_levels = []

    if not nc_file.exists():
        issues.append("File does not exist")
        return False, issues, expected_pvars + expected_svars, expected_levels

    try:
        with xr.open_dataset(nc_file) as ds:
            # Pressure variables
            mp_vars = set(expected_pvars) - set(ds.data_vars)
            if mp_vars:
                issues.append(f"Missing pressure vars: {mp_vars}")
                missing_vars.extend(mp_vars)

            # Single-level variables
            ms_vars = set(expected_svars) - set(ds.data_vars)
            if ms_vars:
                issues.append(f"Missing single-level vars: {ms_vars}")
                missing_vars.extend(ms_vars)

            # Pressure levels
            pc = "pressure_level" if "pressure_level" in ds.coords else "level"
            if pc not in ds.coords:
                issues.append("No pressure coordinate found")
                return False, issues, missing_vars, expected_levels

            actual = sorted(ds[pc].values)
            expected_sorted = sorted(expected_levels)
            ml = set(expected_sorted) - set(actual)
            if ml:
                issues.append(f"Missing levels: {ml}")
                missing_levels.extend(sorted(ml))

            # NaN check
            for var in list(expected_pvars) + list(expected_svars):
                if var in ds.data_vars:
                    data = ds[var].values
                    nan_frac = np.isnan(data).sum() / data.size
                    if nan_frac > 0.5:
                        issues.append(f"{var}: {nan_frac*100:.1f}% NaN")

            tc = "valid_time" if "valid_time" in ds.coords else "time"
            if tc in ds.coords and len(ds[tc]) == 0:
                issues.append("No time steps found")

    except Exception as e:
        issues.append(f"Failed to open/read: {e}")
        return False, issues, missing_vars, expected_levels

    return len(issues) == 0, issues, missing_vars, missing_levels


def check_existing_files(cases, ep_label):
    """Check which files already exist and classify them."""
    expected_pvars = list(NCVAR_PRESSURE.values())
    expected_svars = list(NCVAR_SINGLE.values())

    to_download = []
    to_patch = []
    valid_files = []
    invalid_files = []

    for idx, row in cases.iterrows():
        track_id = row["track_id"]
        nc_file = DATA_DIR / f"{track_id}_era5.nc"

        if not nc_file.exists():
            to_download.append((idx, row))
            continue

        valid, issues, mv, ml = validate_netcdf_file(
            nc_file, expected_pvars, expected_svars, PRESSURE_LEVELS
        )

        if valid:
            valid_files.append(track_id)
        elif mv or ml:
            to_patch.append((idx, row, mv, ml))
        else:
            invalid_files.append((track_id, issues))
            to_download.append((idx, row))

    return to_download, to_patch, valid_files, invalid_files


# ============================================================================
# DOMAIN
# ============================================================================

def compute_domain_bounds(track_id, start_time, end_time):
    """Compute 30°×30° domain centred on the cyclone during intensification."""
    tracks = load_tracks()
    track_data = tracks[tracks["track_id"] == track_id].copy()
    track_data["time"] = pd.to_datetime(track_data["date"])
    track_intens = track_data[
        (track_data["time"] >= start_time) & (track_data["time"] <= end_time)
    ]

    if len(track_intens) == 0:
        return None

    t_center = start_time + (end_time - start_time) / 2
    diffs = np.abs((track_intens["time"] - t_center).dt.total_seconds())
    ci = diffs.idxmin()
    clat = track_intens.loc[ci, "lat vor"]
    clon = track_intens.loc[ci, "lon vor"]

    return {
        "north": min(90, track_intens["lat vor"].max() + DOMAIN_BUFFER),
        "south": max(-90, track_intens["lat vor"].min() - DOMAIN_BUFFER),
        "east": track_intens["lon vor"].max() + DOMAIN_BUFFER,
        "west": track_intens["lon vor"].min() - DOMAIN_BUFFER,
        "track_center_lat": clat,
        "track_center_lon": clon,
    }


# ============================================================================
# DOWNLOAD / PATCH
# ============================================================================

def download_era5_for_case(track_id, start_time, end_time, domain):
    """Download ERA5 pressure-level + single-level data for one case."""
    logging.info(f"      Downloading {track_id}")
    logging.info(f"         Period: {start_time} to {end_time}")

    dates = pd.date_range(start_time, end_time, freq="6h")
    years = dates.year.unique().astype(str).tolist()
    months = dates.month.unique().astype(str).tolist()
    days = dates.day.unique().astype(str).tolist()
    times = dates.strftime("%H:%M").unique().tolist()

    c = cdsapi.Client()

    pf = DATA_DIR / f"{track_id}_era5_pressure.nc"
    sf = DATA_DIR / f"{track_id}_era5_single.nc"
    of = DATA_DIR / f"{track_id}_era5.nc"

    try:
        logging.info("      -> pressure levels...")
        c.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": PRESSURE_VARS,
                "pressure_level": [str(int(p)) for p in PRESSURE_LEVELS],
                "year": years,
                "month": months,
                "day": days,
                "time": times,
                "area": [domain["north"], domain["west"], domain["south"], domain["east"]],
            },
            str(pf),
        )

        logging.info("      -> single level (SLP)...")
        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": SINGLE_LEVEL_VARS,
                "year": years,
                "month": months,
                "day": days,
                "time": times,
                "area": [domain["north"], domain["west"], domain["south"], domain["east"]],
            },
            str(sf),
        )

        logging.info("      -> merging...")
        ds_p = xr.open_dataset(pf)
        ds_s = xr.open_dataset(sf)
        ds_m = xr.merge([ds_p, ds_s])
        ds_m.to_netcdf(of)
        ds_p.close()
        ds_s.close()
        pf.unlink()
        sf.unlink()

        logging.info(f"      ✓ {of}")

        # metadata
        meta = {
            "track_id": track_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "north": domain["north"],
            "south": domain["south"],
            "east": domain["east"],
            "west": domain["west"],
            "track_center_lat": domain["track_center_lat"],
            "track_center_lon": domain["track_center_lon"],
            "pressure_levels_hPa": PRESSURE_LEVELS,
        }
        mf = DATA_DIR / f"{track_id}_metadata.csv"
        pd.DataFrame([meta]).to_csv(mf, index=False)
        return True

    except Exception as e:
        logging.error(f"      ❌ {track_id}: {e}")
        for f in [pf, sf, of]:
            if f.exists():
                f.unlink()
        return False


def patch_era5_file(track_id, start_time, end_time, domain, missing_vars, missing_levels):
    """Download only missing variables/levels and merge with existing file."""
    logging.info(f"      Patching {track_id} (vars={missing_vars}, levels={missing_levels})")

    original = DATA_DIR / f"{track_id}_era5.nc"
    backup = DATA_DIR / f"{track_id}_era5_backup.nc"

    dates = pd.date_range(start_time, end_time, freq="6h")
    years = dates.year.unique().astype(str).tolist()
    months = dates.month.unique().astype(str).tolist()
    days = dates.day.unique().astype(str).tolist()
    times = dates.strftime("%H:%M").unique().tolist()

    c = cdsapi.Client()

    var_rev = {v: k for k, v in NCVAR_PRESSURE.items()}

    try:
        need_pressure = any(v in var_rev for v in missing_vars) or missing_levels
        need_single = "msl" in missing_vars

        temp_files = []

        if need_pressure:
            cds_vars = [var_rev[v] for v in missing_vars if v in var_rev]
            dl_vars = cds_vars if cds_vars else PRESSURE_VARS
            dl_levels = missing_levels if missing_levels else PRESSURE_LEVELS

            ppf = DATA_DIR / f"{track_id}_patch_pressure.nc"
            temp_files.append(ppf)
            logging.info(f"         -> pressure (vars={len(dl_vars)}, levels={len(dl_levels)})...")
            c.retrieve(
                "reanalysis-era5-pressure-levels",
                {
                    "product_type": "reanalysis",
                    "format": "netcdf",
                    "variable": dl_vars,
                    "pressure_level": [str(int(p)) for p in dl_levels],
                    "year": years,
                    "month": months,
                    "day": days,
                    "time": times,
                    "area": [domain["north"], domain["west"], domain["south"], domain["east"]],
                },
                str(ppf),
            )

        if need_single:
            spf = DATA_DIR / f"{track_id}_patch_single.nc"
            temp_files.append(spf)
            logging.info("         -> single-level...")
            c.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "format": "netcdf",
                    "variable": SINGLE_LEVEL_VARS,
                    "year": years,
                    "month": months,
                    "day": days,
                    "time": times,
                    "area": [domain["north"], domain["west"], domain["south"], domain["east"]],
                },
                str(spf),
            )

        logging.info("         -> merging...")
        ds_orig = xr.open_dataset(original)
        ds_orig.load()

        for pf in temp_files:
            if pf.exists():
                ds_patch = xr.open_dataset(pf)
                ds_patch.load()
                ld = "pressure_level" if "pressure_level" in ds_patch.dims else "level"
                if ld in ds_patch.dims:
                    ds_orig = xr.concat([ds_orig, ds_patch], dim=ld).sortby(ld)
                else:
                    ds_orig = xr.merge([ds_orig, ds_patch])
                ds_patch.close()

        original.rename(backup)
        ds_orig.to_netcdf(original)
        ds_orig.close()

        for f in temp_files:
            if f.exists():
                f.unlink()
        if backup.exists():
            backup.unlink()

        logging.info(f"      ✓ Patched: {original}")
        return True

    except Exception as e:
        logging.error(f"      ❌ Patch failed {track_id}: {e}")
        if backup.exists():
            backup.rename(original)
        for f in temp_files:
            if f.exists():
                f.unlink()
        return False


# ============================================================================
# PARALLEL WRAPPERS
# ============================================================================

def _download_wrapper(args):
    idx, row, total = args
    track_id = row["track_id"]
    try:
        start = pd.to_datetime(row["intensification_start"])
        end = pd.to_datetime(row["intensification_end"])
        domain = compute_domain_bounds(track_id, start, end)
        if domain is None:
            return (track_id, False)
        return (track_id, download_era5_for_case(track_id, start, end, domain))
    except Exception as e:
        logging.error(f"      ❌ {track_id}: {e}")
        return (track_id, False)


def _patch_wrapper(args):
    idx, row, mvars, mlevels, total = args
    track_id = row["track_id"]
    try:
        start = pd.to_datetime(row["intensification_start"])
        end = pd.to_datetime(row["intensification_end"])
        mf = DATA_DIR / f"{track_id}_metadata.csv"
        if mf.exists():
            m = pd.read_csv(mf).iloc[0]
            domain = {k: m[k] for k in ["north", "south", "east", "west", "track_center_lat", "track_center_lon"]}
        else:
            domain = compute_domain_bounds(track_id, start, end)
            if domain is None:
                return (track_id, False)
        return (track_id, patch_era5_file(track_id, start, end, domain, mvars, mlevels))
    except Exception as e:
        logging.error(f"      ❌ {track_id}: {e}")
        return (track_id, False)


# ============================================================================
# PROCESS ONE EP GROUP
# ============================================================================

def process_ep_group(ep_label, cases, n_jobs):
    """Validate, patch and download for one EP group. Returns (n_valid, n_failed)."""
    _print_only(f"\n{'─'*60}")
    _print_only(f"  {ep_label}: {len(cases)} cyclones")
    _print_only(f"{'─'*60}")

    logging.info(f"\n{'='*60}")
    logging.info(f"  Processing {ep_label} ({len(cases)} cases)")
    logging.info(f"{'='*60}")

    to_download, to_patch, valid, invalid = check_existing_files(cases, ep_label)

    _print_only(f"  ✓ Complete: {len(valid)}  |  🔧 Patch: {len(to_patch)}  |  ⬇ Download: {len(to_download)}")
    logging.info(f"  Complete={len(valid)}, Patch={len(to_patch)}, Download={len(to_download)}")

    if invalid:
        for tid, iss in invalid[:3]:
            logging.warning(f"  Corrupted {tid}: {'; '.join(iss)}")

    results = []
    n_patched = 0
    n_downloaded = 0

    # 1) Patch
    if to_patch:
        _print_only(f"  Patching {len(to_patch)} incomplete files...")
        logging.info(f"  Patching {len(to_patch)} files...")
        args_list = [(i, r, mv, ml, len(to_patch)) for i, r, mv, ml in to_patch]
        with mp.Pool(processes=n_jobs) as pool:
            for tid, ok in tqdm(
                pool.imap_unordered(_patch_wrapper, args_list),
                total=len(to_patch),
                desc=f"  {ep_label} patch",
                leave=True,
            ):
                results.append((tid, ok))
                if ok:
                    n_patched += 1
        _print_only(f"  Patched: {n_patched}/{len(to_patch)}")

    # 2) Download
    if to_download:
        _print_only(f"  Downloading {len(to_download)} files...")
        logging.info(f"  Downloading {len(to_download)} files...")
        args_list = [(i, r, len(to_download)) for i, r in to_download]
        with mp.Pool(processes=n_jobs) as pool:
            for tid, ok in tqdm(
                pool.imap_unordered(_download_wrapper, args_list),
                total=len(to_download),
                desc=f"  {ep_label} download",
                leave=True,
            ):
                results.append((tid, ok))
                if ok:
                    n_downloaded += 1
        _print_only(f"  Downloaded: {n_downloaded}/{len(to_download)}")

    total_ok = len(valid) + n_patched + n_downloaded
    total_fail = len(cases) - total_ok
    _print_only(f"  {ep_label} result: {total_ok}/{len(cases)} valid ({total_fail} failed)")
    return total_ok, total_fail


# ============================================================================
# COMPLETENESS REPORT
# ============================================================================

def print_completeness_report(all_cases):
    """Print variable/level completeness across all files."""
    expected_pvars = list(NCVAR_PRESSURE.values())
    expected_svars = list(NCVAR_SINGLE.values())

    var_counts = {v: 0 for v in expected_pvars + expected_svars}
    level_counts = {l: 0 for l in PRESSURE_LEVELS}
    total_valid = 0

    for _, row in all_cases.iterrows():
        nc = DATA_DIR / f"{row['track_id']}_era5.nc"
        if not nc.exists():
            continue
        try:
            with xr.open_dataset(nc) as ds:
                for v in expected_pvars + expected_svars:
                    if v in ds.data_vars:
                        var_counts[v] += 1
                pc = "pressure_level" if "pressure_level" in ds.coords else "level"
                if pc in ds.coords:
                    al = ds[pc].values
                    for l in PRESSURE_LEVELS:
                        if l in al:
                            level_counts[l] += 1
                    all_vars = all(v in ds.data_vars for v in expected_pvars + expected_svars)
                    all_levs = all(l in al for l in PRESSURE_LEVELS)
                    if all_vars and all_levs:
                        total_valid += 1
        except Exception:
            pass

    n = len(all_cases)
    _log_and_print("\nCOMPLETENESS REPORT")
    _log_and_print(f"  Variables (n={n}):")
    for v, c in sorted(var_counts.items()):
        pct = c / n * 100 if n else 0
        _log_and_print(f"    {v:4s}: {c:3d}/{n} [{pct:.0f}%]")
    _log_and_print(f"  Levels:")
    for l in sorted(PRESSURE_LEVELS, reverse=True):
        c = level_counts[l]
        pct = c / n * 100 if n else 0
        _log_and_print(f"    {l:4d} hPa: {c:3d}/{n} [{pct:.0f}%]")
    pct_total = total_valid / n * 100 if n else 0
    _log_and_print(f"  Overall: {total_valid}/{n} 100% complete ({pct_total:.1f}%)")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Download ERA5 data for EP structure analysis")
    parser.add_argument("--jobs", type=int, default=None,
                        help=f"Parallel CDS jobs (default: {MAX_PARALLEL_JOBS})")
    parser.add_argument("--log-file", type=str, default=None)
    args = parser.parse_args()

    # Logging setup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(args.log_file) if args.log_file else LOG_DIR / f"ep_structure_download_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)],
    )

    # ── Print header (stdout – visible in nohup.out) ─────────────────────────
    _print_only("=" * 60)
    _print_only("EP STRUCTURE ANALYSIS – ERA5 DOWNLOAD")
    _print_only(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    _print_only(f"  Log: {log_file}")
    _print_only("=" * 60)

    logging.info("=" * 60)
    logging.info("STEP 2: DOWNLOAD ERA5 DATA – EP STRUCTURE ANALYSIS")
    logging.info("=" * 60)

    # ── Load cases ────────────────────────────────────────────────────────────
    ep1_file = RESULTS_DIR / "ep1_cases.csv"
    ep2_file = RESULTS_DIR / "ep2_cases.csv"

    if not ep1_file.exists() or not ep2_file.exists():
        msg = f"❌ Case files not found in {RESULTS_DIR}. Run step1 first."
        _print_only(msg)
        logging.error(msg)
        return

    ep1_cases = pd.read_csv(ep1_file)
    ep2_cases = pd.read_csv(ep2_file)
    all_cases = pd.concat([ep1_cases, ep2_cases], ignore_index=True)

    _print_only(f"\n  EP1: {len(ep1_cases)} cases  |  EP2: {len(ep2_cases)} cases  |  Total: {len(all_cases)}")
    _print_only(f"  Levels: {sorted(PRESSURE_LEVELS)} hPa")
    _print_only(f"  Variables: {list(NCVAR_PRESSURE.values()) + list(NCVAR_SINGLE.values())}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    n_jobs = args.jobs if args.jobs is not None else MAX_PARALLEL_JOBS
    if n_jobs > 4:
        _print_only(f"  ⚠️  {n_jobs} jobs may exceed CDS limits (recommended: 2-4)")
    _print_only(f"  Parallel jobs: {n_jobs}")

    t0 = time.time()

    # ── Process each EP ───────────────────────────────────────────────────────
    ep1_ok, ep1_fail = process_ep_group("EP1", ep1_cases, n_jobs)
    ep2_ok, ep2_fail = process_ep_group("EP2", ep2_cases, n_jobs)

    elapsed = time.time() - t0

    # ── Final report ──────────────────────────────────────────────────────────
    _print_only(f"\n{'='*60}")
    _print_only(f"  DOWNLOAD COMPLETE  ({elapsed/60:.1f} min)")
    _print_only(f"{'='*60}")
    _print_only(f"  EP1: {ep1_ok}/{len(ep1_cases)} valid  ({ep1_fail} failed)")
    _print_only(f"  EP2: {ep2_ok}/{len(ep2_cases)} valid  ({ep2_fail} failed)")
    _print_only(f"  Total: {ep1_ok+ep2_ok}/{len(all_cases)} valid")

    logging.info(f"\nDOWNLOAD COMPLETE ({elapsed/60:.1f} min)")
    logging.info(f"  EP1: {ep1_ok}/{len(ep1_cases)}")
    logging.info(f"  EP2: {ep2_ok}/{len(ep2_cases)}")

    print_completeness_report(all_cases)

    if ep1_fail + ep2_fail == 0:
        _print_only("\n  ✓ All files ready!")
        _print_only("  Next: python scripts/ep_structure_analysis/step3_precompute_composites.py")
    elif ep1_fail + ep2_fail > 0:
        _print_only(f"\n  ⚠️  {ep1_fail+ep2_fail} failed — re-run to retry (or use --jobs 2)")

    _print_only(f"\n  Log: {log_file}")


if __name__ == "__main__":
    main()
