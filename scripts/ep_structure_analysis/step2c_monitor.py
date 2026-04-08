"""
step2c_monitor.py — Download Progress Monitor for ERA5 EP Structure Data

Scans data/era5_ep_structure/ and reports download completeness at the
finest available granularity: per (case, variable, pressure-level) "slot".

A *slot* is defined as one (variable, pressure-level) pair:
  5 pressure vars  ×  9 levels  =  45 pressure slots
  1 single-level var (msl)      =   1 slot
  ─────────────────────────────────────────────────────
  Total per case                =  46 slots

The monitor opens only the NetCDF header (no data loaded), so scanning
1 000+ files takes only a few seconds.

CANONICAL METHODOLOGY (April 2026):
  • EP1, EP2, EP3 (and EPALL composites) are fully supported
  • Only cyclones with >= 24h intensification are included
  • Only central timesteps (2 or 3) are downloaded per case, not full intensification
  • Domain is 30°×30° centered on selected timestep positions

MODES:
  • download (default): Full slot-level monitoring for step2_download_era5_parallel.py
    - Scans all EPs (EP1, EP2, EP3)
    - Shows per-variable and per-level completeness
    - Tracks download process status
    
  • reuse: Simple file existence check for step2b_reuse_legacy_era5.py
    - EP3 has NO legacy data (legacy analysis was EP1/EP2 only)
    - Use step2_download_era5_parallel.py for EP3 and missing cases

Usage:
    # Monitor download progress (default, all EPs including EP3)
    python scripts/ep_structure_analysis/step2c_monitor.py

    # Monitor legacy reuse progress (EP1/EP2 have legacy, EP3 does not)
    python scripts/ep_structure_analysis/step2c_monitor.py --mode reuse

    # Live refresh every 60 s (run alongside step 2 or step2b)
    python scripts/ep_structure_analysis/step2c_monitor.py --watch

    # Custom refresh interval (30 s)
    python scripts/ep_structure_analysis/step2c_monitor.py --watch --interval 30

    # No terminal clear — safe for nohup / log capture
    python scripts/ep_structure_analysis/step2c_monitor.py --watch --no-clear

Author: Danilo Couto de Souza
Date: February–April 2026
"""

import sys
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import xarray as xr
from tqdm import tqdm

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ============================================================================
# CONFIGURATION  (must stay consistent with step2_download_era5_parallel.py)
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR     = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR  = PROJECT_ROOT / "results" / "ep_structure"

# NetCDF variable short names (as stored in the downloaded files)
PRESSURE_VARS = ["u", "v", "t", "z", "q"]
SINGLE_VARS   = ["msl"]

# Target pressure levels (hPa)
PRESSURE_LEVELS = [175, 200, 225, 250, 500, 825, 850, 875, 975]

# Total download "slots" per case:
#   5 pressure vars × 9 levels  +  1 single-level var  =  46
SLOTS_PER_CASE = len(PRESSURE_VARS) * len(PRESSURE_LEVELS) + len(SINGLE_VARS)

# Human-readable variable labels (padded to equal width for table alignment)
VAR_LABELS = {
    "u":   "u   (u-wind)         ",
    "v":   "v   (v-wind)         ",
    "t":   "t   (temperature)    ",
    "z":   "z   (geopotential)   ",
    "q":   "q   (spec. humidity) ",
    "msl": "msl (sea-level pres.)",
}

# Purpose annotation for each pressure level
LEVEL_PURPOSE = {
    175: "PV@200 FD      ",
    200: "PV@200 FD      ",
    225: "PV@200 FD      ",
    250: "EGR upper      ",
    500: "mid-trop.      ",
    825: "PV@850 FD      ",
    850: "EGR / T_adv    ",
    875: "PV@850 FD      ",
    975: "moisture flux  ",
}

# Step 2.1: ERA5 monthly means climatology — all anomaly diagnostic groups
CLIM_RAW_DIR  = DATA_DIR / "era5_monthly_raw"    # Per-month raw files
CLIM_N_YEARS  = 30    # 1991–2020
CLIM_N_MONTHS = 12
MONTH_NAMES   = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

# One entry per download group — mirrors step2_1_download_era5_monthly_means.py
CLIM_GROUPS = {
    "250hPa": {
        "raw_prefix":  "era5_raw_month",           # legacy — no group tag
        "clim_file":   DATA_DIR / "era5_climatology_250hPa.nc",
        "nc_vars":     ["u", "v", "z"],
        "levels":      [250],
        "description": "u,v,z @250 hPa  →  AFC + KE_adv anomaly",
    },
    "pv200": {
        "raw_prefix":  "era5_raw_pv200_month",
        "clim_file":   DATA_DIR / "era5_climatology_pv200.nc",
        "nc_vars":     ["u", "v", "t"],
        "levels":      [175, 200, 225],
        "description": "u,v,t @175/200/225 hPa  →  PV@200 anomaly",
    },
    "pv850": {
        "raw_prefix":  "era5_raw_pv850_month",
        "clim_file":   DATA_DIR / "era5_climatology_pv850.nc",
        "nc_vars":     ["u", "v", "t"],
        "levels":      [825, 850, 875],
        "description": "u,v,t @825/850/875 hPa  →  PV@850 + T_adv anomaly",
    },
    "mfd975": {
        "raw_prefix":  "era5_raw_mfd975_month",
        "clim_file":   DATA_DIR / "era5_climatology_mfd975.nc",
        "nc_vars":     ["u", "v", "q"],
        "levels":      [975],
        "description": "u,v,q @975 hPa  →  moisture flux div anomaly",
    },
    "slp": {
        "raw_prefix":  "era5_raw_slp_month",
        "clim_file":   DATA_DIR / "era5_climatology_slp.nc",
        "nc_vars":     ["msl"],
        "levels":      [],
        "description": "msl (surface)  →  SLP anomaly",
    },
}

# ============================================================================
# PROCESS DETECTION
# ============================================================================

def detect_download_process():
    """
    Detect if step2_download_era5_parallel.py is currently running.
    
    Returns:
        dict with keys:
            - running: bool
            - pid: int or None
            - cpu_percent: float or None
            - memory_mb: float or None
            - runtime_seconds: float or None
    """
    if not HAS_PSUTIL:
        return {"running": False, "pid": None, "cpu_percent": None, 
                "memory_mb": None, "runtime_seconds": None}
    
    script_name = "step2_download_era5_parallel.py"
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info.get('cmdline') or []
            # Check if this is a Python process running our script
            if any(script_name in arg for arg in cmdline):
                # Get process details
                pid = proc.info['pid']
                runtime = time.time() - proc.info['create_time']
                
                # Get CPU and memory (may take a moment)
                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    mem_mb = proc.memory_info().rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu = None
                    mem_mb = None
                
                return {
                    "running": True,
                    "pid": pid,
                    "cpu_percent": cpu,
                    "memory_mb": mem_mb,
                    "runtime_seconds": runtime,
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return {"running": False, "pid": None, "cpu_percent": None,
            "memory_mb": None, "runtime_seconds": None}


def format_runtime(seconds):
    """Format runtime in human-readable format."""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


# ============================================================================
# FILE SCANNING
# ============================================================================

def _scan_one(nc_file: Path) -> dict:
    """
    Open one ERA5 NetCDF file and return metadata-level statistics.

    Only the file header is read — no data is loaded into memory.
    Returns a dict with:
      slots_done         – int ∈ [0, SLOTS_PER_CASE]
      pressure_vars_found – set of pressure variable names present
      levels_found        – set of pressure levels (float hPa) present
      single_vars_found   – set of single-level variable names present
      status              – 'complete' | 'incomplete' | 'missing' | 'corrupted'
      size_bytes          – file size in bytes (0 if missing)
    """
    if not nc_file.exists():
        return {
            "slots_done": 0,
            "pressure_vars_found": set(),
            "levels_found": set(),
            "single_vars_found": set(),
            "status": "missing",
            "size_bytes": 0,
        }

    size = nc_file.stat().st_size
    try:
        with xr.open_dataset(nc_file, engine="netcdf4") as ds:
            pressure_vars_found = set(PRESSURE_VARS) & set(ds.data_vars)
            single_vars_found   = set(SINGLE_VARS)   & set(ds.data_vars)

            # Detect pressure-level coordinate name
            pc = "pressure_level" if "pressure_level" in ds.coords else "level"
            levels_found = (
                {float(l) for l in ds[pc].values} & {float(l) for l in PRESSURE_LEVELS}
                if pc in ds.coords else set()
            )

            # Count completed slots
            n_pressure = len(pressure_vars_found) * len(levels_found)
            n_single   = len(single_vars_found)
            slots_done = n_pressure + n_single

        status = "complete" if slots_done == SLOTS_PER_CASE else "incomplete"

    except Exception:
        return {
            "slots_done": 0,
            "pressure_vars_found": set(),
            "levels_found": set(),
            "single_vars_found": set(),
            "status": "corrupted",
            "size_bytes": size,
        }

    return {
        "slots_done": slots_done,
        "pressure_vars_found": pressure_vars_found,
        "levels_found": levels_found,
        "single_vars_found": single_vars_found,
        "status": status,
        "size_bytes": size,
    }


def scan_group(cases: pd.DataFrame, desc: str = "") -> dict:
    """
    Scan all ERA5 files for one EP group.

    Returns dict mapping track_id → _scan_one result.
    Shows a tqdm progress bar during scanning.
    """
    results = {}
    for _, row in tqdm(
        cases.iterrows(),
        total=len(cases),
        desc=desc,
        leave=False,
        ncols=72,
        bar_format="  {desc}: {percentage:3.0f}% |{bar}| {n}/{total}",
    ):
        nc_file = DATA_DIR / f"{row['track_id']}_era5.nc"
        results[row["track_id"]] = _scan_one(nc_file)
    return results


def scan_group_simple(cases: pd.DataFrame, desc: str = "") -> dict:
    """
    Simple file existence scan for legacy reuse mode (step2b).
    
    Only checks if file exists, doesn't open NetCDF.
    Used for monitoring step2b_reuse_legacy_era5.py progress.
    
    Returns dict mapping track_id → {'exists': bool, 'size_bytes': int}
    """
    results = {}
    for _, row in tqdm(
        cases.iterrows(),
        total=len(cases),
        desc=desc,
        leave=False,
        ncols=72,
        bar_format="  {desc}: {percentage:3.0f}% |{bar}| {n}/{total}",
    ):
        nc_file = DATA_DIR / f"{row['track_id']}_era5.nc"
        if nc_file.exists():
            size = nc_file.stat().st_size
            results[row["track_id"]] = {'exists': True, 'size_bytes': size}
        else:
            results[row["track_id"]] = {'exists': False, 'size_bytes': 0}
    return results


def aggregate_simple(cases: pd.DataFrame, scan_results: dict) -> dict:
    """
    Aggregate simple scan results (for reuse mode).
    
    Returns dict with:
        n_cases, n_found, n_missing, total_bytes
    """
    n_cases = len(cases)
    n_found = sum(1 for r in scan_results.values() if r['exists'])
    n_missing = n_cases - n_found
    total_bytes = sum(r['size_bytes'] for r in scan_results.values())
    
    return {
        'n_cases': n_cases,
        'n_found': n_found,
        'n_missing': n_missing,
        'total_bytes': total_bytes,
    }


# ============================================================================
# STATISTICS
# ============================================================================

def aggregate(cases: pd.DataFrame, scan_results: dict) -> dict:
    """
    Aggregate per-case scan results into group-level statistics.

    Returned dict keys:
      n_cases, total_slots, slots_done
      n_complete, n_incomplete, n_missing, n_corrupted
      total_bytes
      var_complete   – {var: n_cases_where_var_has_all_levels}
      level_complete – {level: n_cases_where_all_vars_have_that_level}
    """
    n_cases      = len(cases)
    total_slots  = n_cases * SLOTS_PER_CASE
    slots_done   = sum(r["slots_done"]                  for r in scan_results.values())
    n_complete   = sum(r["status"] == "complete"         for r in scan_results.values())
    n_incomplete = sum(r["status"] == "incomplete"       for r in scan_results.values())
    n_missing    = sum(r["status"] == "missing"          for r in scan_results.values())
    n_corrupted  = sum(r["status"] == "corrupted"        for r in scan_results.values())
    total_bytes  = sum(r["size_bytes"]                   for r in scan_results.values())

    # Per-variable completeness:
    #   pressure var "complete" = var present AND all 8 target levels present
    #   single var   "complete" = var present
    var_complete: dict[str, int] = {}
    for v in PRESSURE_VARS:
        var_complete[v] = sum(
            1 for r in scan_results.values()
            if v in r["pressure_vars_found"]
            and len(r["levels_found"]) == len(PRESSURE_LEVELS)
        )
    for v in SINGLE_VARS:
        var_complete[v] = sum(
            1 for r in scan_results.values() if v in r["single_vars_found"]
        )

    # Per-level completeness:
    #   level "complete" = level present AND all pressure vars present
    level_complete: dict[int, int] = {}
    for lvl in PRESSURE_LEVELS:
        fl = float(lvl)
        level_complete[lvl] = sum(
            1 for r in scan_results.values()
            if fl in r["levels_found"]
            and len(r["pressure_vars_found"]) == len(PRESSURE_VARS)
        )

    return {
        "n_cases":       n_cases,
        "total_slots":   total_slots,
        "slots_done":    slots_done,
        "n_complete":    n_complete,
        "n_incomplete":  n_incomplete,
        "n_missing":     n_missing,
        "n_corrupted":   n_corrupted,
        "total_bytes":   total_bytes,
        "var_complete":  var_complete,
        "level_complete": level_complete,
    }


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

BAR_W = 30   # number of block characters in a progress bar


def _bar(n: int, total: int, width: int = BAR_W) -> str:
    """Return a Unicode block progress bar: [████░░░░]  n/total (xx.x%)."""
    frac  = n / total if total else 0.0
    filled = int(width * frac)
    bar   = "█" * filled + "░" * (width - filled)
    pad   = len(str(total))
    return f"[{bar}]  {n:>{pad}}/{total}  ({frac * 100:5.1f}%)"


def _pct(n: int, total: int) -> str:
    """Compact 'n/total (xx.x%)' string."""
    p   = 100.0 * n / total if total else 0.0
    pad = len(str(total))
    return f"{n:>{pad}}/{total} ({p:5.1f}%)"


def _fmt_bytes(n: float) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:6.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


# ============================================================================
# REPORT RENDERING
# ============================================================================

def print_report_simple(
    ep1_cases: pd.DataFrame,
    ep2_cases: pd.DataFrame,
    ep3_cases: pd.DataFrame,
    ep1_stats: dict,
    ep2_stats: dict,
    ep3_stats: dict,
    scan_elapsed: float,
) -> None:
    """Render simple reuse mode report to stdout."""
    
    W = 78
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print()
    print("═" * W)
    print("  ERA5 EP STRUCTURE — LEGACY REUSE MONITOR (step2b)")
    print(f"  Scanned : {now}  ({scan_elapsed:.1f} s)")
    print(f"  Dir     : {DATA_DIR}")
    print("  Mode    : Simple file existence check")
    print("═" * W)
    
    total_cases = sum(s['n_cases'] for s in [ep1_stats, ep2_stats, ep3_stats])
    total_found = sum(s['n_found'] for s in [ep1_stats, ep2_stats, ep3_stats])
    total_bytes = sum(s['total_bytes'] for s in [ep1_stats, ep2_stats, ep3_stats])
    
    for ep_label, stats in [("EP1", ep1_stats), ("EP2", ep2_stats), ("EP3", ep3_stats)]:
        n_cases = stats['n_cases']
        n_found = stats['n_found']
        n_missing = stats['n_missing']
        pct = 100 * n_found / n_cases if n_cases else 0
        
        print()
        print(f"  {ep_label}  files  {_bar(n_found, n_cases)}")
        print(f"       detail  ✓ found: {n_found}  ✗ missing: {n_missing}  "
              f"size: {_fmt_bytes(stats['total_bytes'])}")
    
    print()
    print("  " + "─" * (W - 2))
    overall_pct = 100 * total_found / total_cases if total_cases else 0
    print(f"  OVERALL: {total_found}/{total_cases} files ({overall_pct:.1f}%)  "
          f"Total size: {_fmt_bytes(total_bytes)}")
    print()
    print("  Note: EP3 has NO legacy data (legacy analysis was EP1/EP2 only).")
    print("        Use step2_download_era5_parallel.py for EP3 and missing cases.")
    print("═" * W)


def print_report(
    ep_cases: dict,
    ep_stats: dict,
    scan_elapsed: float,
    proc_info: dict,
) -> None:
    """
    Render the full monitor report to stdout.
    
    Parameters
    ----------
    ep_cases : dict
        Mapping EP label -> DataFrame (e.g., {"EP1": df1, "EP2": df2, "EP3": df3})
    ep_stats : dict
        Mapping EP label -> aggregate stats dict
    scan_elapsed : float
        Time taken for scan
    proc_info : dict
        Download process info
    """
    W   = 78
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine which EPs have data
    active_eps = [ep for ep in ["EP1", "EP2", "EP3"] if ep in ep_stats and ep_stats[ep]["n_cases"] > 0]

    print()
    print("═" * W)
    print("  ERA5 EP STRUCTURE — DOWNLOAD MONITOR (Canonical Methodology)")
    print(f"  Scanned : {now}  ({scan_elapsed:.1f} s)")
    print(f"  Dir     : {DATA_DIR}")
    print(f"  Slots   : {SLOTS_PER_CASE} per case  "
          f"= {len(PRESSURE_VARS)} pressure vars × {len(PRESSURE_LEVELS)} levels "
          f"+ {len(SINGLE_VARS)} SLP")
    print(f"  Method  : Central timesteps only (>=24h intensification)")
    
    # Download process status
    if proc_info["running"]:
        runtime_str = format_runtime(proc_info["runtime_seconds"])
        status = f"  ⬇ DOWNLOAD ACTIVE  PID={proc_info['pid']}  Runtime={runtime_str}"
        if proc_info["cpu_percent"] is not None:
            status += f"  CPU={proc_info['cpu_percent']:.1f}%"
        if proc_info["memory_mb"] is not None:
            status += f"  RAM={proc_info['memory_mb']:.0f}MB"
        print(status)
    elif HAS_PSUTIL:
        print("  ⏸  Download process: not running")
    else:
        print("  ⏸  Download process: unknown (install psutil for detection)")
    
    print("═" * W)

    # ── Per-EP overview: slots bar + cases bar ────────────────────────────
    for ep_label in active_eps:
        stats = ep_stats[ep_label]
        n_c = stats["n_cases"]
        print()
        print(f"  {ep_label}  slots  {_bar(stats['slots_done'], stats['total_slots'])}")
        print(f"       cases  {_bar(stats['n_complete'], n_c)}"
              "  (fully complete)")
        line = (
            f"       detail  "
            f"✓ complete: {stats['n_complete']}  "
            f"⚑ partial: {stats['n_incomplete']}  "
            f"✗ missing: {stats['n_missing']}"
        )
        if stats["n_corrupted"]:
            line += f"  ⚠ corrupted: {stats['n_corrupted']}"
        print(line)
        print(f"       disk    {_fmt_bytes(stats['total_bytes'])}")

    # ── Combined totals ───────────────────────────────────────────────────
    cs = sum(ep_stats[ep]["slots_done"] for ep in active_eps)
    ct = sum(ep_stats[ep]["total_slots"] for ep in active_eps)
    cc = sum(ep_stats[ep]["n_complete"] for ep in active_eps)
    cn = sum(ep_stats[ep]["n_cases"] for ep in active_eps)
    total_bytes = sum(ep_stats[ep]["total_bytes"] for ep in active_eps)

    print()
    print("  " + "─" * (W - 2))
    print(f"  ALL  slots  {_bar(cs, ct)}")
    print(f"       cases  {_bar(cc, cn)}  (fully complete)")
    print(f"       disk   {_fmt_bytes(total_bytes)}")

    # ── Per-variable breakdown ────────────────────────────────────────────
    cV = 22   # variable label column width
    cN = 12   # numeric column width (smaller for 4 columns)

    print()
    print("  " + "─" * (W - 2))
    header = f"  {'Variable':<{cV}}"
    for ep in active_eps:
        header += f"  {ep:>{cN}}"
    header += f"  {'Combined':>{cN}}"
    print(header)
    print("  " + "─" * (W - 2))

    for v in PRESSURE_VARS + SINGLE_VARS:
        line = f"  {VAR_LABELS.get(v, v):<{cV}}"
        total_n, total_t = 0, 0
        for ep in active_eps:
            n = ep_stats[ep]["var_complete"].get(v, 0)
            t = ep_stats[ep]["n_cases"]
            total_n += n
            total_t += t
            line += f"  {_pct(n, t):>{cN}}"
        line += f"  {_pct(total_n, total_t):>{cN}}"
        print(line)

    # ── Per-level breakdown ───────────────────────────────────────────────
    print()
    print("  " + "─" * (W - 2))
    header = f"  {'Level (hPa)':<{cV}}"
    for ep in active_eps:
        header += f"  {ep:>{cN}}"
    header += f"  {'Combined':>{cN}}"
    print(header)
    print("  " + "─" * (W - 2))

    for lvl in sorted(PRESSURE_LEVELS, reverse=True):
        purpose = LEVEL_PURPOSE.get(lvl, "")
        lbl = f"{lvl:>4} hPa  {purpose}"
        line = f"  {lbl:<{cV}}"
        total_n, total_t = 0, 0
        for ep in active_eps:
            n = ep_stats[ep]["level_complete"].get(lvl, 0)
            t = ep_stats[ep]["n_cases"]
            total_n += n
            total_t += t
            line += f"  {_pct(n, t):>{cN}}"
        line += f"  {_pct(total_n, total_t):>{cN}}"
        print(line)

    # ── Step 2.1: ERA5 monthly means — all anomaly climatology groups ─────
    print()
    print("  " + "─" * (W - 2))
    print("  ERA5 MONTHLY MEANS — STEP 2.1 (anomaly climatologies, 5 groups):")
    print(f"   {CLIM_N_YEARS}-year monthly climatologies (1991–2020)  │  "
          f"raw files in era5_monthly_raw/")
    print()

    _missing_groups = []
    for gname, gcfg in CLIM_GROUPS.items():
        raw_files = [
            CLIM_RAW_DIR / f"{gcfg['raw_prefix']}{m:02d}.nc"
            for m in range(1, CLIM_N_MONTHS + 1)
        ]
        good = [m for m, f in enumerate(raw_files, 1)
                if f.exists() and f.stat().st_size > 1024]
        bad  = [m for m in range(1, CLIM_N_MONTHS + 1) if m not in good]
        n_good   = len(good)
        raw_mb   = sum(raw_files[m - 1].stat().st_size for m in good) / 1024 ** 2
        raw_icon = "✓" if n_good == CLIM_N_MONTHS else ("⚑" if n_good > 0 else "✗")
        raw_mb_str = f"{raw_mb:6.1f} MB" if n_good > 0 else "         "

        # Climatology file status
        cf = gcfg["clim_file"]
        if cf.exists():
            try:
                with xr.open_dataset(cf) as _ds:
                    n_mo = _ds.sizes.get("month", 0)
                clim_ok   = n_mo == CLIM_N_MONTHS
                clim_icon = "✓" if clim_ok else "⚑"
                clim_det  = _fmt_bytes(cf.stat().st_size)
            except Exception:
                clim_ok   = False
                clim_icon = "⚠"
                clim_det  = "corrupted"
        else:
            clim_ok   = False
            clim_icon = "✗"
            clim_det  = "not generated"

        if n_good < CLIM_N_MONTHS or not clim_ok:
            _missing_groups.append(gname)

        # Two-line display per group
        print(f"  {gname:<8}  raw  {raw_icon} {_bar(n_good, CLIM_N_MONTHS, 14)}  {raw_mb_str}")
        print(f"           clim {clim_icon} {cf.name:<42}  {clim_det}")

        # Missing-months detail (only when partially downloaded)
        if bad and n_good > 0:
            miss_str = " ".join(MONTH_NAMES[m - 1] for m in bad)
            print(f"                ✗ missing months: {miss_str}")
            last_f = max((raw_files[m - 1] for m in good),
                         key=lambda p: p.stat().st_mtime)
            last_t = datetime.fromtimestamp(last_f.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )
            print(f"                last downloaded: {last_f.name}"
                  f"  ({_fmt_bytes(last_f.stat().st_size)})  at {last_t}")
        elif n_good == 0:
            print(f"                → not started;  run step2_1 --groups {gname}")
        print()

    # Summary line
    if _missing_groups:
        miss_str = " ".join(_missing_groups)
        print(f"   ✗ Incomplete groups: {miss_str}")
        print(f"     python scripts/ep_structure_analysis/"
              "step2_1_download_era5_monthly_means.py"
              f" --groups {miss_str}")
    else:
        print("   ✓ All 5 climatology groups complete.")

    # ── Composite files (step 3 output) ───────────────────────────────────
    print()
    print("  " + "─" * (W - 2))
    print("  PRECOMPUTED COMPOSITES (step 3 output):")

    for ep_tag in ["ep1", "ep2", "ep3", "epall"]:
        cf = DATA_DIR / f"precomputed_composites_{ep_tag}.nc"
        if cf.exists():
            sz   = _fmt_bytes(cf.stat().st_size)
            mtim = datetime.fromtimestamp(cf.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"    ✓  {cf.name:<44}  {sz}   modified {mtim}")
        else:
            print(f"    ✗  {cf.name:<44}  (not yet generated — run step3)")

    print()
    
    # ── Footer notes ──────────────────────────────────────────────────────
    if not HAS_PSUTIL:
        print("  " + "─" * (W - 2))
        print("  Note: Install psutil for download process detection:")
        print("        pip install psutil")
        print()
    
    print("═" * W)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor ERA5 download/reuse progress for the EP structure analysis.\n"
            "\n"
            "CANONICAL METHODOLOGY (April 2026):\n"
            "  • Supports EP1, EP2, EP3 (and EPALL composites)\n"
            "  • Only cyclones with >= 24h intensification\n"
            "  • Only central timesteps (2-3) downloaded per case\n"
            "\n"
            "MODES:\n"
            "  download (default): Full slot-level monitoring for step2_download_era5_parallel.py\n"
            "                      Scans all EPs (EP1, EP2, EP3) with per-variable/level breakdown.\n"
            "\n"
            "  reuse:              Simple file existence check for step2b_reuse_legacy_era5.py\n"
            "                      NOTE: EP3 has NO legacy data (legacy was EP1/EP2 only).\n"
            "                      Use step2_download_era5_parallel.py for EP3.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode", "-m",
        choices=['download', 'reuse'],
        default='download',
        help="Monitoring mode: 'download' for step2 (default), 'reuse' for step2b",
    )
    parser.add_argument(
        "--watch", "-w", action="store_true",
        help="Refresh continuously until Ctrl+C.",
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=60, metavar="SECS",
        help="Refresh interval in seconds for --watch mode (default: 60).",
    )
    parser.add_argument(
        "--no-clear", action="store_true",
        help="Do not clear the terminal between refreshes (safe for nohup/log capture).",
    )
    args = parser.parse_args()

    # ── Load case lists ───────────────────────────────────────────────────
    ep1_file = RESULTS_DIR / "ep1_cases.csv"
    ep2_file = RESULTS_DIR / "ep2_cases.csv"
    ep3_file = RESULTS_DIR / "ep3_cases.csv"

    if not ep1_file.exists():
        print(f"\n❌  EP1 case file not found: {ep1_file}")
        print("    Run step1_select_ep_tracks.py first.\n")
        sys.exit(1)

    ep1_cases = pd.read_csv(ep1_file)
    
    # EP2 and EP3 are optional for some modes
    ep2_cases = pd.read_csv(ep2_file) if ep2_file.exists() else pd.DataFrame()
    ep3_cases = pd.read_csv(ep3_file) if ep3_file.exists() else pd.DataFrame()

    # Default empty stats for when EP data is not available
    EMPTY_SIMPLE_STATS = {'n_cases': 0, 'n_found': 0, 'n_missing': 0, 'total_bytes': 0}
    EMPTY_FULL_STATS = {
        'n_cases': 0, 'total_slots': 0, 'slots_done': 0,
        'n_complete': 0, 'n_incomplete': 0, 'n_missing': 0, 'n_corrupted': 0,
        'total_bytes': 0, 'var_complete': {v: 0 for v in PRESSURE_VARS + SINGLE_VARS},
        'level_complete': {lvl: 0 for lvl in PRESSURE_LEVELS}
    }

    def _run_once() -> None:
        t0 = time.monotonic()
        
        if args.mode == 'reuse':
            # Simple file existence scan for step2b
            ep1_scan = scan_group_simple(ep1_cases, desc="Scanning EP1")
            ep2_scan = scan_group_simple(ep2_cases, desc="Scanning EP2") if len(ep2_cases) > 0 else {}
            ep3_scan = scan_group_simple(ep3_cases, desc="Scanning EP3") if len(ep3_cases) > 0 else {}
            
            ep1_stats = aggregate_simple(ep1_cases, ep1_scan)
            ep2_stats = aggregate_simple(ep2_cases, ep2_scan) if len(ep2_cases) > 0 else EMPTY_SIMPLE_STATS.copy()
            ep3_stats = aggregate_simple(ep3_cases, ep3_scan) if len(ep3_cases) > 0 else EMPTY_SIMPLE_STATS.copy()
            
            elapsed = time.monotonic() - t0
            
            if args.watch and not args.no_clear:
                os.system("clear")
            
            print_report_simple(ep1_cases, ep2_cases, ep3_cases, 
                              ep1_stats, ep2_stats, ep3_stats, elapsed)
        else:
            # Full slot-level scan for step2 (all EPs including EP3)
            proc_info = detect_download_process()
            
            ep1_scan = scan_group(ep1_cases, desc="Scanning EP1")
            ep2_scan = scan_group(ep2_cases, desc="Scanning EP2") if len(ep2_cases) > 0 else {}
            ep3_scan = scan_group(ep3_cases, desc="Scanning EP3") if len(ep3_cases) > 0 else {}
            
            ep1_stats = aggregate(ep1_cases, ep1_scan)
            ep2_stats = aggregate(ep2_cases, ep2_scan) if len(ep2_cases) > 0 else EMPTY_FULL_STATS.copy()
            ep3_stats = aggregate(ep3_cases, ep3_scan) if len(ep3_cases) > 0 else EMPTY_FULL_STATS.copy()
            
            elapsed = time.monotonic() - t0

            if args.watch and not args.no_clear:
                os.system("clear")
            
            # Build dicts for the new print_report signature
            ep_cases = {"EP1": ep1_cases, "EP2": ep2_cases, "EP3": ep3_cases}
            ep_stats = {"EP1": ep1_stats, "EP2": ep2_stats, "EP3": ep3_stats}
            
            print_report(ep_cases, ep_stats, elapsed, proc_info)

    if args.watch:
        mode_label = "reuse" if args.mode == 'reuse' else "download"
        print(f"  Monitoring {mode_label} every {args.interval} s  (Ctrl+C to stop)…", flush=True)
        try:
            while True:
                _run_once()
                print(
                    f"\n  Next refresh in {args.interval} s  (Ctrl+C to stop)",
                    flush=True,
                )
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n  Monitor stopped.")
    else:
        _run_once()


if __name__ == "__main__":
    main()
