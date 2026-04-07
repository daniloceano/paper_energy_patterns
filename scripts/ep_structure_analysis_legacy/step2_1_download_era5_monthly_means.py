"""
Step 2.1: Download ERA5 Monthly Means for Anomaly Diagnostics

Downloads ERA5 monthly averaged data on pressure levels and computes
30-year climatological means (1991–2020) for ALL anomaly diagnostics
used in step 3.

Download groups and their purposes
------------------------------------
  "250hPa"  : u, v, z  at 250 hPa
              → AFC (Orlanski & Katzfey 1991)  +  KE advection anomaly
  "pv200"   : u, v, t  at 175 / 200 / 225 hPa
              → PV@200 hPa anomaly
  "pv850"   : u, v, t  at 825 / 850 / 875 hPa
              → PV@850 hPa anomaly  +  temperature advection@850 anomaly
  "mfd975"  : u, v, q  at 975 hPa
              → Moisture flux divergence@975 hPa anomaly
  "slp"     : msl  (single-level, no pressure_level key)
              → Sea level pressure anomaly

Download strategy
-----------------
  12 monthly CDS requests per group (one per calendar month, 30 years
  each).  Per-month raw files are reused across runs — only missing or
  invalid files are downloaded.

  The "250hPa" group reuses existing files (era5_raw_month{MM}.nc) for
  backward compatibility with already-downloaded data.  All other groups
  use group-specific filename prefixes.

Output climatology files (saved to data/era5_ep_structure/)
------------------------------------------------------------
  era5_climatology_250hPa.nc
      Variables : u_clim, v_clim, z_clim
      Dimensions: (month: 12, latitude, longitude)          ← no level dim

  era5_climatology_pv200.nc
      Variables : u_clim, v_clim, t_clim
      Dimensions: (month: 12, pressure_level: 3, latitude, longitude)

  era5_climatology_pv850.nc
      Variables : u_clim, v_clim, t_clim
      Dimensions: (month: 12, pressure_level: 3, latitude, longitude)

  era5_climatology_mfd975.nc
      Variables : u_clim, v_clim, q_clim
      Dimensions: (month: 12, pressure_level: 1, latitude, longitude)

  era5_climatology_slp.nc
      Variables : msl_clim
      Dimensions: (month: 12, latitude, longitude)          ← single-level

Climatological Period: 1991–2020 (WMO standard 30-year normal)
Domain: South Atlantic + buffer  (80°S–5°S, 80°W–40°E)

Usage
-----
  # Smart run — only downloads what is missing
  python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py

  # Force re-download and recompute everything
  python … --force

  # Process specific groups only
  python … --groups pv200 pv850 mfd975 slp

  # Recompute climatologies from existing raw files (skip CDS)
  python … --clim-only

  # Force re-download for specific calendar months (all groups)
  python … --force-months 6 7 8

Author: Danilo Couto de Souza
Date: March 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr
from datetime import datetime
import cdsapi
import logging
import argparse

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR     = PROJECT_ROOT / "data" / "era5_ep_structure"
RAW_DIR      = DATA_DIR / "era5_monthly_raw"
LOG_DIR      = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Climatological period (WMO standard 30-year normal)
CLIM_YEARS  = list(range(1991, 2021))   # 1991–2020 inclusive (30 years)
CLIM_MONTHS = list(range(1, 13))        # All 12 calendar months

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# Domain: generous envelope covering all cyclone 30°×30° subdomains
# Based on cyclone centers: lat ∈ [-63, -21], lon ∈ [-64, +24]
# Plus 15° buffer on each side, rounded outward
DOMAIN = {
    "north": -5,
    "south": -80,
    "west":  -80,
    "east":   40,
}


# ============================================================================
# DOWNLOAD GROUP DEFINITIONS
# ============================================================================
#
# Each entry defines one download group:
#   levels      : pressure levels to request [hPa]  (empty for single-level vars)
#   cds_vars    : CDS API variable names
#   nc_vars     : corresponding short names in the downloaded NetCDF
#   raw_prefix  : per-month raw file prefix  →  raw_prefix{MM}.nc
#   clim_vars   : mapping  nc_short → climatology variable name
#   output      : Path to the final climatology NetCDF file
#   squeeze_lev : if True, squeeze singleton pressure_level dim (backward compat)
#   cds_dataset : CDS dataset name (default: pressure-levels; override for single-level)
#   description : human-readable description for logging
#
# NOTE: "250hPa" uses the legacy prefix (era5_raw_month{MM}.nc) so that
#       already-downloaded files are reused without modification.
# NOTE: "slp" uses the single-level CDS dataset (no pressure_level key in request).

DOWNLOAD_GROUPS: dict = {
    "250hPa": {
        "levels":      [250],
        "cds_vars":    ["u_component_of_wind",
                        "v_component_of_wind",
                        "geopotential"],
        "nc_vars":     ["u", "v", "z"],
        "raw_prefix":  "era5_raw_month",           # legacy — no group tag
        "clim_vars":   {"u": "u_clim", "v": "v_clim", "z": "z_clim"},
        "output":      DATA_DIR / "era5_climatology_250hPa.nc",
        "squeeze_lev": True,                        # backward compat: no level dim
        "description": "u, v, z at 250 hPa  →  AFC + KE_adv anomaly",
    },
    "pv200": {
        "levels":      [175, 200, 225],
        "cds_vars":    ["u_component_of_wind",
                        "v_component_of_wind",
                        "temperature"],
        "nc_vars":     ["u", "v", "t"],
        "raw_prefix":  "era5_raw_pv200_month",
        "clim_vars":   {"u": "u_clim", "v": "v_clim", "t": "t_clim"},
        "output":      DATA_DIR / "era5_climatology_pv200.nc",
        "squeeze_lev": False,
        "description": "u, v, t at 175/200/225 hPa  →  PV@200 anomaly",
    },
    "pv850": {
        "levels":      [825, 850, 875],
        "cds_vars":    ["u_component_of_wind",
                        "v_component_of_wind",
                        "temperature"],
        "nc_vars":     ["u", "v", "t"],
        "raw_prefix":  "era5_raw_pv850_month",
        "clim_vars":   {"u": "u_clim", "v": "v_clim", "t": "t_clim"},
        "output":      DATA_DIR / "era5_climatology_pv850.nc",
        "squeeze_lev": False,
        "description": "u, v, t at 825/850/875 hPa  →  PV@850 + T_adv@850 anomaly",
    },
    "mfd975": {
        "levels":      [975],
        "cds_vars":    ["u_component_of_wind",
                        "v_component_of_wind",
                        "specific_humidity"],
        "nc_vars":     ["u", "v", "q"],
        "raw_prefix":  "era5_raw_mfd975_month",
        "clim_vars":   {"u": "u_clim", "v": "v_clim", "q": "q_clim"},
        "output":      DATA_DIR / "era5_climatology_mfd975.nc",
        "squeeze_lev": False,
        "description": "u, v, q at 975 hPa  →  moisture flux div anomaly",
    },
    "slp": {
        "levels":      [],                           # no pressure_level in request
        "cds_vars":    ["mean_sea_level_pressure"],
        "nc_vars":     ["msl"],
        "raw_prefix":  "era5_raw_slp_month",
        "clim_vars":   {"msl": "msl_clim"},
        "output":      DATA_DIR / "era5_climatology_slp.nc",
        "squeeze_lev": True,                        # no level dim (surface variable)
        "cds_dataset": "reanalysis-era5-single-levels-monthly-means",
        "description": "msl at surface  →  SLP anomaly",
    },
}


# ============================================================================
# HELPERS
# ============================================================================

def _raw_file(group_name: str, month: int) -> Path:
    """Return the per-month raw NetCDF path for a given download group."""
    prefix = DOWNLOAD_GROUPS[group_name]["raw_prefix"]
    return RAW_DIR / f"{prefix}{month:02d}.nc"


def _validate_raw(f: Path, expected_vars: list, expected_levels: list) -> bool:
    """
    Check that a raw file exists, is non-empty, and contains expected content.

    For multi-level groups (len(expected_levels) > 1) the pressure_level
    coordinate is also validated.
    """
    if not f.exists() or f.stat().st_size < 1024:
        return False
    try:
        with xr.open_dataset(f) as ds:
            for v in expected_vars:
                if v not in ds.data_vars:
                    return False
            if len(expected_levels) > 1:
                pc = "pressure_level" if "pressure_level" in ds.dims else "level"
                if pc not in ds.dims:
                    return False
                found = {float(x) for x in ds[pc].values}
                for lv in expected_levels:
                    if float(lv) not in found:
                        return False
        return True
    except Exception:
        return False


def _check_group_status(group_name: str) -> tuple:
    """
    Return (n_valid, missing_months) for a download group.

    n_valid        : months already downloaded and valid.
    missing_months : list of calendar months (1-based) that need downloading.
    """
    cfg     = DOWNLOAD_GROUPS[group_name]
    n_valid = 0
    missing = []
    for month in CLIM_MONTHS:
        f = _raw_file(group_name, month)
        if _validate_raw(f, cfg["nc_vars"], cfg["levels"]):
            n_valid += 1
        else:
            missing.append(month)
    return n_valid, missing


# ============================================================================
# DOWNLOAD — one CDS request per (group, calendar month)
# ============================================================================

def download_group_month(
    group_name: str,
    month: int,
    c: cdsapi.Client,
    force: bool = False,
) -> Path:
    """
    Download ERA5 monthly means for one group and one calendar month.

    Each request: 30 years × N levels × M variables.
    The raw file is saved to era5_monthly_raw/ and reused on subsequent runs.
    """
    cfg      = DOWNLOAD_GROUPS[group_name]
    raw_file = _raw_file(group_name, month)
    mname    = MONTH_NAMES[month - 1]

    if not force and _validate_raw(raw_file, cfg["nc_vars"], cfg["levels"]):
        sz = raw_file.stat().st_size / 1024**2
        logging.info(
            f"   [{group_name}] {mname} ({month:02d}) — already downloaded "
            f"({sz:.1f} MB), skipping."
        )
        return raw_file

    logging.info(
        f"   [{group_name}] {mname} ({month:02d}) — submitting CDS request "
        f"({len(CLIM_YEARS)} years × {len(cfg['cds_vars'])} vars "
        f"× {len(cfg['levels'])} level(s))..."
    )

    cds_dataset = cfg.get(
        "cds_dataset", "reanalysis-era5-pressure-levels-monthly-means"
    )
    request: dict = {
        "product_type": "monthly_averaged_reanalysis",
        "format":        "netcdf",
        "variable":      cfg["cds_vars"],
        "year":          [str(y) for y in CLIM_YEARS],
        "month":         [f"{month:02d}"],
        "time":          "00:00",
        "area": [DOMAIN["north"], DOMAIN["west"],
                 DOMAIN["south"], DOMAIN["east"]],
    }
    # Pressure-level groups include the level list; single-level groups do not.
    if cfg["levels"]:
        request["pressure_level"] = [str(lv) for lv in cfg["levels"]]

    c.retrieve(cds_dataset, request, str(raw_file))

    sz = raw_file.stat().st_size / 1024**2
    logging.info(
        f"   [{group_name}] {mname} ({month:02d}) ✓  {sz:.1f} MB → {raw_file.name}"
    )
    return raw_file


def download_group(
    group_name: str,
    force_months: list | None = None,
) -> list:
    """
    Download all 12 calendar months for one group, skipping valid files.

    Returns list of 12 raw file paths (one per month, in calendar order).
    """
    cfg       = DOWNLOAD_GROUPS[group_name]
    force_set = set(force_months or [])
    n_valid, _ = _check_group_status(group_name)

    logging.info(f"\n   Group '{group_name}': {cfg['description']}")
    logging.info(
        f"   Levels: {cfg['levels']}  |  Vars: {cfg['nc_vars']}  |  "
        f"Already downloaded: {n_valid}/{len(CLIM_MONTHS)} months"
    )

    c = cdsapi.Client()
    raw_files = []
    for month in CLIM_MONTHS:
        raw_files.append(
            download_group_month(group_name, month, c, force=month in force_set)
        )

    total_mb = sum(f.stat().st_size for f in raw_files) / 1024**2
    logging.info(
        f"   ✓ Group '{group_name}': all {len(CLIM_MONTHS)} months ready "
        f"({total_mb:.1f} MB total)."
    )
    return raw_files


# ============================================================================
# COMPUTE CLIMATOLOGY  (generic — works for all groups)
# ============================================================================

def compute_group_climatology(group_name: str, raw_files: list) -> xr.Dataset:
    """
    Compute 30-year monthly climatological means for one download group.

    Strategy
    --------
    Each raw file contains one calendar month across all 30 CLIM_YEARS.
    Steps:
      1. Average over the 30-year time axis → one monthly mean.
      2. Optionally squeeze singleton pressure_level (single-level groups).
      3. Rename variables: u → u_clim, v → v_clim, etc.
      4. Concatenate 12 monthly means along a new ``month`` dimension.

    Output dimensions
    -----------------
    squeeze_lev=True  (250hPa group): (month, latitude, longitude)
    squeeze_lev=False (all others)  : (month, pressure_level, latitude, longitude)
    """
    cfg = DOWNLOAD_GROUPS[group_name]
    logging.info(
        f"\n   Computing 30-year climatology for group '{group_name}'..."
    )

    monthly_means = []
    for month, f in zip(CLIM_MONTHS, raw_files):
        mname = MONTH_NAMES[month - 1]
        ds    = xr.open_dataset(f)
        tc    = "valid_time" if "valid_time" in ds.dims else "time"

        ds_mean = ds.mean(dim=tc)   # average over 30-year time axis

        # Squeeze singleton pressure_level for single-level backward-compat groups
        if cfg["squeeze_lev"]:
            pc = "pressure_level" if "pressure_level" in ds_mean.dims else "level"
            if pc in ds_mean.dims and ds_mean.sizes[pc] == 1:
                ds_mean = ds_mean.squeeze(pc, drop=True)

        # Rename variables to climatology names (u → u_clim, etc.)
        rename_map = {
            v: cfg["clim_vars"][v]
            for v in cfg["nc_vars"]
            if v in ds_mean
        }
        ds_mean = ds_mean.rename(rename_map)
        ds_mean = ds_mean.expand_dims({"month": [month]})

        logging.info(f"     {mname} ({month:02d}): mean over {ds.sizes[tc]} years ✓")
        ds.close()
        monthly_means.append(ds_mean)

    ds_clim = xr.concat(monthly_means, dim="month")

    ds_clim.attrs.update({
        "description": (
            f"ERA5 30-year monthly climatological means — {cfg['description']} "
            f"({CLIM_YEARS[0]}–{CLIM_YEARS[-1]})"
        ),
        "climatological_period": f"{CLIM_YEARS[0]}-{CLIM_YEARS[-1]}",
        "pressure_levels_hPa":   str(cfg["levels"]),
        "purpose":                cfg["description"],
        "created":                datetime.now().isoformat(),
    })
    return ds_clim


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Download ERA5 monthly means (1991–2020) and compute 30-year "
            "climatologies for all anomaly diagnostics used in step 3."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Groups and output files:
  250hPa  → era5_climatology_250hPa.nc   (u, v, z at 250 hPa)
  pv200   → era5_climatology_pv200.nc    (u, v, t at 175/200/225 hPa)
  pv850   → era5_climatology_pv850.nc    (u, v, t at 825/850/875 hPa)
  mfd975  → era5_climatology_mfd975.nc   (u, v, q at 975 hPa)
  slp     → era5_climatology_slp.nc      (msl at surface)
        """,
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-download and re-computation for ALL groups.",
    )
    parser.add_argument(
        "--force-months", type=int, nargs="+", metavar="M",
        help="Force re-download for specific calendar months (all groups).",
    )
    parser.add_argument(
        "--groups", nargs="+", choices=list(DOWNLOAD_GROUPS),
        default=list(DOWNLOAD_GROUPS),
        help="Process only these groups (default: all four).",
    )
    parser.add_argument(
        "--clim-only", action="store_true",
        help="Skip CDS download; recompute climatologies from existing raw files.",
    )
    args = parser.parse_args()

    # ── Logging ───────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file  = LOG_DIR / f"era5_monthly_means_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.info("=" * 70)
    logging.info("STEP 2.1: ERA5 MONTHLY MEANS → CLIMATOLOGIES FOR ANOMALY DIAGNOSTICS")
    logging.info("=" * 70)
    logging.info(f"   Log: {log_file}")

    groups_to_process = args.groups
    force_months      = list(CLIM_MONTHS) if args.force else (args.force_months or [])

    # ── Status report ─────────────────────────────────────────────────────
    logging.info("\n   CURRENT STATUS:")
    any_missing = False
    for gname in groups_to_process:
        cfg          = DOWNLOAD_GROUPS[gname]
        n_valid, missing_m = _check_group_status(gname)
        clim_exists  = cfg["output"].exists()
        status       = "✓" if (n_valid == 12 and clim_exists) else "⚠"
        missing_str  = f"  missing months: {missing_m}" if missing_m else ""
        sz_str       = (f" ({cfg['output'].stat().st_size/1024**2:.1f} MB)"
                        if clim_exists else "")
        logging.info(
            f"   {status} {gname:12s}: "
            f"{n_valid}/12 raw months valid  |  "
            f"clim={'yes' if clim_exists else 'NO'}{sz_str}{missing_str}"
        )
        if n_valid < 12 or not clim_exists:
            any_missing = True

    if not any_missing and not args.force and not args.force_months:
        logging.info(
            "\n   ✓ All groups complete.  "
            "Use --force to re-download or --clim-only to recompute."
        )
        return

    # ── Process each group ────────────────────────────────────────────────
    completed: list = []
    failed:    list = []

    for gname in groups_to_process:
        cfg = DOWNLOAD_GROUPS[gname]
        logging.info(f"\n{'='*60}")
        logging.info(f"   Group: {gname}  ({cfg['description']})")
        logging.info(f"{'='*60}")

        try:
            # Download (or use existing)
            if not args.clim_only:
                raw_files = download_group(gname, force_months=force_months)
            else:
                raw_files = [_raw_file(gname, m) for m in CLIM_MONTHS]
                missing   = [
                    m for m, f in zip(CLIM_MONTHS, raw_files)
                    if not _validate_raw(f, cfg["nc_vars"], cfg["levels"])
                ]
                if missing:
                    logging.error(
                        f"   ❌ [{gname}] Missing/invalid raw files for months: {missing}"
                    )
                    logging.error("   Run without --clim-only to download them.")
                    failed.append(gname)
                    continue
                logging.info(f"   [{gname}] --clim-only: using existing raw files.")

            # Compute and save climatology
            ds_clim = compute_group_climatology(gname, raw_files)
            ds_clim.to_netcdf(cfg["output"])
            sz = cfg["output"].stat().st_size / 1024**2
            logging.info(f"\n   ✓ [{gname}] Saved: {cfg['output'].name} ({sz:.1f} MB)")
            for var in ds_clim.data_vars:
                d = ds_clim[var].values
                logging.info(
                    f"     {var}: shape={d.shape}, "
                    f"range=[{np.nanmin(d):.4g}, {np.nanmax(d):.4g}]"
                )
            completed.append(gname)

        except Exception as exc:
            logging.error(f"   ❌ [{gname}] Failed: {exc}")
            failed.append(gname)

    # ── Final summary ─────────────────────────────────────────────────────
    logging.info("\n" + "=" * 70)
    logging.info("STEP 2.1 " + ("COMPLETE" if not failed else "PARTIALLY COMPLETE"))
    logging.info("=" * 70)
    logging.info(f"   Log: {log_file}")
    if completed:
        logging.info(f"\n   Completed ({len(completed)}):")
        for g in completed:
            logging.info(f"     ✓ {g:12s} → {DOWNLOAD_GROUPS[g]['output'].name}")
    if failed:
        logging.warning(f"\n   Failed groups: {failed}")
    logging.info(
        f"\n   Raw files kept in: {RAW_DIR}\n"
        "   (Delete manually if disk space is a concern.)"
    )
    logging.info(
        "\n   Next step:  "
        "python scripts/ep_structure_analysis/step3_precompute_composites.py"
    )


if __name__ == "__main__":
    main()

