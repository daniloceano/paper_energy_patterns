"""
Step 2.1: Download ERA5 Monthly Means for AFC Climatology

Downloads ERA5 monthly averaged data on pressure levels and computes
a 30-year climatological mean (1991–2020) for use in the Ageostrophic
Flux Convergence (AFC) diagnostic.

The AFC diagnostic (Orlanski & Katzfey 1991; Orlanski & Chang 1993)
requires a temporal decomposition of the flow into a base state (Vm)
and an eddy perturbation (v'):

    V = Vm + v'       Φ = Φm + φ'

where Vm, Φm are the climatological mean state and v', φ' are the
instantaneous departures.  Using a 30-year monthly climatology as
the base state is standard practice (e.g., Solman & Menéndez 1998;
Decker & Martin 2005; Jiang et al. 2013).

Download strategy — one CDS request per calendar month:
  Instead of a single large request (360 time steps), the download is
  split into 12 smaller requests (one per calendar month, 30 years each,
  ~30 time steps per request).  This avoids CDS queue timeouts,
  enables automatic resume (already-downloaded months are skipped),
  and makes progress easy to track.

  Per-month raw files: data/era5_ep_structure/era5_raw_month{MM}.nc
  Final climatology:   data/era5_ep_structure/era5_climatology_250hPa.nc

Variables Downloaded:
  - u_component_of_wind  (u)  at 250 hPa
  - v_component_of_wind  (v)  at 250 hPa
  - geopotential          (z) at 250 hPa

Climatological Period: 1991–2020 (WMO standard)
Domain: South Atlantic + buffer  (80°S–5°S, 80°W–40°E)

Output:
  data/era5_ep_structure/era5_climatology_250hPa.nc
    → Dimensions: (month: 12, latitude, longitude)
    → Variables:  u_clim, v_clim, z_clim  (30-year monthly means)

Author: Danilo Couto de Souza
Date: February 2026
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
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RAW_DIR  = DATA_DIR / "era5_monthly_raw"      # intermediate per-month files
LOG_DIR  = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Climatological period (WMO standard 30-year normal)
CLIM_YEARS  = list(range(1991, 2021))   # 1991–2020 inclusive (30 years)
CLIM_MONTHS = list(range(1, 13))        # All 12 calendar months

# Pressure level for AFC
PRESSURE_LEVEL = 250   # hPa

# Variables (CDS API names → NetCDF short names)
CDS_VARIABLES = [
    "u_component_of_wind",
    "v_component_of_wind",
    "geopotential",
]
NC_SHORT_NAMES = {
    "u_component_of_wind": "u",
    "v_component_of_wind": "v",
    "geopotential": "z",
}
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

# Final output
OUTPUT_FILE = DATA_DIR / "era5_climatology_250hPa.nc"


# ============================================================================
# HELPERS
# ============================================================================

def _raw_file(month: int) -> Path:
    """Return path for the per-month CDS download file."""
    return RAW_DIR / f"era5_raw_month{month:02d}.nc"


def _validate_raw(f: Path) -> bool:
    """Quick check that a raw file is a complete, readable NetCDF."""
    if not f.exists() or f.stat().st_size < 1024:
        return False
    try:
        with xr.open_dataset(f) as ds:
            return len(ds.data_vars) > 0
    except Exception:
        return False


# ============================================================================
# DOWNLOAD — one request per calendar month
# ============================================================================

def download_month(month: int, c: cdsapi.Client, force: bool = False) -> Path:
    """
    Download ERA5 monthly means for one calendar month across all CLIM_YEARS.

    Each request covers:
      - 1 calendar month  ×  30 years  =  30 time steps
      - 3 variables  ×  1 pressure level  ×  regional domain

    Parameters
    ----------
    month : int
        Calendar month (1–12).
    c : cdsapi.Client
        Authenticated CDS client (shared across calls to avoid repeated auth).
    force : bool
        If True, re-download even if the file already exists.

    Returns
    -------
    raw_file : Path
    """
    raw_file = _raw_file(month)
    mname    = MONTH_NAMES[month - 1]

    if not force and _validate_raw(raw_file):
        logging.info(f"   [{month:02d}/{len(CLIM_MONTHS)}] {mname} — already downloaded"
                     f" ({raw_file.stat().st_size / 1024**2:.1f} MB), skipping.")
        return raw_file

    logging.info(f"   [{month:02d}/{len(CLIM_MONTHS)}] {mname} — submitting CDS request "
                 f"({len(CLIM_YEARS)} years × {len(CDS_VARIABLES)} vars × 1 level)...")

    c.retrieve(
        "reanalysis-era5-pressure-levels-monthly-means",
        {
            "product_type": "monthly_averaged_reanalysis",
            "format":        "netcdf",
            "variable":      CDS_VARIABLES,
            "pressure_level": [str(PRESSURE_LEVEL)],
            "year":          [str(y) for y in CLIM_YEARS],
            "month":         [f"{month:02d}"],
            "time":          "00:00",
            "area": [DOMAIN["north"], DOMAIN["west"],
                     DOMAIN["south"], DOMAIN["east"]],
        },
        str(raw_file),
    )

    sz = raw_file.stat().st_size / 1024**2
    logging.info(f"   [{month:02d}/{len(CLIM_MONTHS)}] {mname} ✓  {sz:.1f} MB → {raw_file.name}")
    return raw_file


def download_all_months(force_months: list[int] | None = None) -> list[Path]:
    """
    Download all 12 calendar months, skipping those already on disk.

    Parameters
    ----------
    force_months : list[int] or None
        If given, force re-download for these specific months (1-based).

    Returns
    -------
    raw_files : list[Path]  — one file per calendar month, in order.
    """
    force_months = set(force_months or [])

    logging.info(f"\n   Downloading {len(CLIM_MONTHS)} months "
                 f"({CLIM_YEARS[0]}–{CLIM_YEARS[-1]}) — one CDS request per month.")
    logging.info(f"   Variables : {CDS_VARIABLES}")
    logging.info(f"   Level     : {PRESSURE_LEVEL} hPa")
    logging.info(f"   Domain    : N={DOMAIN['north']}, S={DOMAIN['south']}, "
                 f"W={DOMAIN['west']}, E={DOMAIN['east']}")
    logging.info(f"   Output dir: {RAW_DIR}")

    # Check which months already exist
    n_exist = sum(1 for m in CLIM_MONTHS if _validate_raw(_raw_file(m)))
    logging.info(f"   Already downloaded: {n_exist}/{len(CLIM_MONTHS)} months")

    c = cdsapi.Client()
    raw_files = []
    for month in CLIM_MONTHS:
        raw_files.append(download_month(month, c, force=month in force_months))

    logging.info(f"\n   ✓ All {len(CLIM_MONTHS)} months downloaded.")
    total_mb = sum(f.stat().st_size for f in raw_files) / 1024**2
    logging.info(f"   Total size: {total_mb:.1f} MB")
    return raw_files


# ============================================================================
# COMPUTE CLIMATOLOGY
# ============================================================================

def compute_climatology(raw_files: list[Path]) -> xr.Dataset:
    """
    Compute 12-month climatological means from the per-month raw files.

    For each calendar month the downloaded file already contains only
    one month's data across all 30 years — average those 30 time steps
    to get the monthly climatological mean, then concatenate along a
    new ``month`` dimension.

    Parameters
    ----------
    raw_files : list[Path]
        12 per-month NetCDF files (one per calendar month), in order 1→12.

    Returns
    -------
    ds_clim : xr.Dataset  — dims (month: 12, latitude, longitude)
    """
    logging.info("\n   Computing 30-year climatological means (12 months)...")

    monthly_means = []
    for month, f in zip(CLIM_MONTHS, raw_files):
        mname = MONTH_NAMES[month - 1]
        ds = xr.open_dataset(f)

        # Identify time coordinate
        tc = "valid_time" if "valid_time" in ds.dims else "time"

        # Mean over the 30-year time axis
        ds_mean = ds.mean(dim=tc)

        # Drop singleton pressure-level dim if present
        pc = "pressure_level" if "pressure_level" in ds_mean.dims else "level"
        if pc in ds_mean.dims and ds_mean.sizes[pc] == 1:
            ds_mean = ds_mean.squeeze(pc, drop=True)

        # Rename: u → u_clim, v → v_clim, z → z_clim
        rename_map = {}
        for nc_name in NC_SHORT_NAMES.values():
            if nc_name in ds_mean:
                rename_map[nc_name] = f"{nc_name}_clim"
        ds_mean = ds_mean.rename(rename_map)

        # Attach month coordinate
        ds_mean = ds_mean.expand_dims({"month": [month]})

        logging.info(f"     {mname} ({month:02d}): mean over {ds.sizes[tc]} years ✓")
        ds.close()
        monthly_means.append(ds_mean)

    ds_clim = xr.concat(monthly_means, dim="month")

    # Global metadata
    ds_clim.attrs.update({
        "description":          (f"ERA5 monthly climatological means at {PRESSURE_LEVEL} hPa "
                                 f"({CLIM_YEARS[0]}–{CLIM_YEARS[-1]})"),
        "climatological_period": f"{CLIM_YEARS[0]}-{CLIM_YEARS[-1]}",
        "pressure_level_hPa":    PRESSURE_LEVEL,
        "purpose":               ("Base state for AFC (Ageostrophic Flux Convergence) "
                                  "temporal decomposition (Orlanski & Katzfey 1991)"),
        "created":               datetime.now().isoformat(),
    })

    # Variable metadata
    var_meta = {
        "u_clim": ("Climatological zonal wind at 250 hPa",      "m s-1"),
        "v_clim": ("Climatological meridional wind at 250 hPa", "m s-1"),
        "z_clim": ("Climatological geopotential at 250 hPa",    "m2 s-2"),
    }
    for var, (lname, ustr) in var_meta.items():
        if var in ds_clim:
            ds_clim[var].attrs.update(long_name=lname, units=ustr)

    return ds_clim


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Download ERA5 monthly means (one CDS request per calendar month) "
            "and compute a 30-year climatology for the AFC diagnostic."
        )
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-download and re-computation of all months.",
    )
    parser.add_argument(
        "--force-months", type=int, nargs="+", metavar="M",
        help="Force re-download for specific months only (e.g. --force-months 3 7).",
    )
    parser.add_argument(
        "--clim-only", action="store_true",
        help="Skip download; recompute climatology from existing raw files.",
    )
    args = parser.parse_args()

    # ── Logging ──────────────────────────────────────────────────────────
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
    logging.info("STEP 2.1: ERA5 MONTHLY MEANS → CLIMATOLOGY FOR AFC")
    logging.info("=" * 70)
    logging.info(f"   Log: {log_file}")

    # ── Check if final output already exists ─────────────────────────────
    if OUTPUT_FILE.exists() and not args.force and not args.force_months and not args.clim_only:
        logging.info(f"\n   ✓ Climatology already exists: {OUTPUT_FILE.name}")
        logging.info("   Use --force to re-download everything, or")
        logging.info("   --force-months M to re-download specific months, or")
        logging.info("   --clim-only to recompute from existing raw files.")
        with xr.open_dataset(OUTPUT_FILE) as ds:
            logging.info(f"   Variables : {list(ds.data_vars)}")
            logging.info(f"   Dimensions: {dict(ds.dims)}")
            logging.info(f"   Period    : {ds.attrs.get('climatological_period', '?')}")
        return

    # ── Download ─────────────────────────────────────────────────────────
    if not args.clim_only:
        force_months = list(CLIM_MONTHS) if args.force else (args.force_months or [])
        raw_files = download_all_months(force_months=force_months)
    else:
        raw_files = [_raw_file(m) for m in CLIM_MONTHS]
        missing   = [m for m, f in zip(CLIM_MONTHS, raw_files) if not _validate_raw(f)]
        if missing:
            logging.error(f"   ❌ Missing/invalid raw files for months: {missing}")
            logging.error("   Run without --clim-only to download them.")
            sys.exit(1)
        logging.info("   --clim-only: using existing raw files.")

    # ── Compute climatology ───────────────────────────────────────────────
    ds_clim = compute_climatology(raw_files)

    # ── Save ─────────────────────────────────────────────────────────────
    ds_clim.to_netcdf(OUTPUT_FILE)
    logging.info(f"\n   ✓ Saved: {OUTPUT_FILE.name} "
                 f"({OUTPUT_FILE.stat().st_size / 1024**2:.1f} MB)")

    logging.info("\n   Summary:")
    for var in ds_clim.data_vars:
        d = ds_clim[var].values
        logging.info(f"     {var}: shape={d.shape}, "
                     f"range=[{np.nanmin(d):.2f}, {np.nanmax(d):.2f}]")

    logging.info(f"\n   Per-month raw files kept in: {RAW_DIR}")
    logging.info("   (Delete the directory manually if disk space is a concern.)")

    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 2.1 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"   Log: {log_file}")
    logging.info("\n   Next: python scripts/ep_structure_analysis/"
                 "step3_precompute_composites.py")


if __name__ == "__main__":
    main()
