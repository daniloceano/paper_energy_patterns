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
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Climatological period (WMO standard 30-year normal)
CLIM_YEARS = list(range(1991, 2021))    # 1991–2020 inclusive
CLIM_MONTHS = list(range(1, 13))        # All 12 months

# Pressure level for AFC
PRESSURE_LEVEL = 250   # hPa

# Variables (CDS API names → NetCDF short names)
CDS_VARIABLES = [
    "u_component_of_wind",
    "v_component_of_wind",
    "geopotential",
]
NC_SHORT_NAMES = {"u_component_of_wind": "u",
                  "v_component_of_wind": "v",
                  "geopotential": "z"}

# Domain: generous envelope covering all cyclone 30°×30° subdomains
# Based on cyclone centers: lat ∈ [-63, -21], lon ∈ [-64, +24]
# Plus 15° buffer on each side, rounded outward
DOMAIN = {
    "north": -5,
    "south": -80,
    "west": -80,
    "east": 40,
}

# Output file
OUTPUT_FILE = DATA_DIR / "era5_climatology_250hPa.nc"


# ============================================================================
# DOWNLOAD
# ============================================================================

def download_era5_monthly_means():
    """
    Download ERA5 monthly-mean u, v, z at 250 hPa for all years in CLIM_YEARS.

    Uses the pre-computed ERA5 monthly-mean dataset from CDS
    (``reanalysis-era5-pressure-levels-monthly-means``), which is much
    faster than averaging hourly data ourselves.

    Returns
    -------
    raw_file : Path
        Path to the downloaded raw NetCDF file.
    """
    raw_file = DATA_DIR / "era5_monthly_means_250hPa_raw.nc"

    if raw_file.exists():
        logging.info(f"   Raw file already exists: {raw_file.name}")
        logging.info("   Skipping download. Delete the file to re-download.")
        return raw_file

    logging.info("   Downloading ERA5 monthly means from CDS...")
    logging.info(f"   Years: {CLIM_YEARS[0]}–{CLIM_YEARS[-1]}")
    logging.info(f"   Level: {PRESSURE_LEVEL} hPa")
    logging.info(f"   Variables: {CDS_VARIABLES}")
    logging.info(f"   Domain: N={DOMAIN['north']}, S={DOMAIN['south']}, "
                 f"W={DOMAIN['west']}, E={DOMAIN['east']}")

    c = cdsapi.Client()

    c.retrieve(
        "reanalysis-era5-pressure-levels-monthly-means",
        {
            "product_type": "monthly_averaged_reanalysis",
            "format": "netcdf",
            "variable": CDS_VARIABLES,
            "pressure_level": [str(PRESSURE_LEVEL)],
            "year": [str(y) for y in CLIM_YEARS],
            "month": [f"{m:02d}" for m in CLIM_MONTHS],
            "time": "00:00",
            "area": [DOMAIN["north"], DOMAIN["west"],
                     DOMAIN["south"], DOMAIN["east"]],
        },
        str(raw_file),
    )

    logging.info(f"   ✓ Downloaded: {raw_file.name} "
                 f"({raw_file.stat().st_size / 1024**2:.1f} MB)")
    return raw_file


# ============================================================================
# COMPUTE CLIMATOLOGY
# ============================================================================

def compute_climatology(raw_file):
    """
    Compute 12-month climatological means from the raw monthly-mean file.

    For each calendar month (1–12), average over all CLIM_YEARS.
    Result: a Dataset with dimension ``month`` (1–12) and the three variables.

    Parameters
    ----------
    raw_file : Path
        Raw ERA5 monthly-mean NetCDF file (360 time steps for 30 years × 12 months).

    Returns
    -------
    ds_clim : xr.Dataset
        Climatological mean with dimensions (month, latitude, longitude).
    """
    logging.info("   Computing 30-year climatological means...")

    ds = xr.open_dataset(raw_file)

    # Determine time coordinate name
    tc = "valid_time" if "valid_time" in ds.dims else "time"

    # Group by calendar month and compute the mean over years
    ds_clim = ds.groupby(f"{tc}.month").mean(dim=tc)

    # Rename variables with _clim suffix to avoid confusion with instantaneous data
    rename_map = {}
    for cds_name, nc_name in NC_SHORT_NAMES.items():
        if nc_name in ds_clim:
            rename_map[nc_name] = f"{nc_name}_clim"
    ds_clim = ds_clim.rename(rename_map)

    # Drop pressure level dimension if singleton
    pc = "pressure_level" if "pressure_level" in ds_clim.dims else "level"
    if pc in ds_clim.dims and ds_clim.sizes[pc] == 1:
        ds_clim = ds_clim.squeeze(pc, drop=True)

    # Add metadata
    ds_clim.attrs["description"] = (
        f"ERA5 monthly climatological means at {PRESSURE_LEVEL} hPa "
        f"({CLIM_YEARS[0]}–{CLIM_YEARS[-1]})"
    )
    ds_clim.attrs["climatological_period"] = f"{CLIM_YEARS[0]}-{CLIM_YEARS[-1]}"
    ds_clim.attrs["pressure_level_hPa"] = PRESSURE_LEVEL
    ds_clim.attrs["purpose"] = (
        "Base state for AFC (Ageostrophic Flux Convergence) "
        "temporal decomposition (Orlanski & Katzfey 1991)"
    )
    ds_clim.attrs["created"] = datetime.now().isoformat()

    for var in ds_clim.data_vars:
        base = var.replace("_clim", "")
        if base == "u":
            ds_clim[var].attrs.update(
                long_name="Climatological zonal wind at 250 hPa",
                units="m s-1",
            )
        elif base == "v":
            ds_clim[var].attrs.update(
                long_name="Climatological meridional wind at 250 hPa",
                units="m s-1",
            )
        elif base == "z":
            ds_clim[var].attrs.update(
                long_name="Climatological geopotential at 250 hPa",
                units="m2 s-2",
            )

    ds.close()
    return ds_clim


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download ERA5 monthly means and compute climatology for AFC"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-computation even if output file already exists",
    )
    args = parser.parse_args()

    # Logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"era5_monthly_means_{timestamp}.log"

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

    # Check if output already exists
    if OUTPUT_FILE.exists() and not args.force:
        logging.info(f"\n   ✓ Climatology file already exists: {OUTPUT_FILE.name}")
        logging.info("   Use --force to re-compute.")
        # Validate briefly
        with xr.open_dataset(OUTPUT_FILE) as ds:
            logging.info(f"   Variables: {list(ds.data_vars)}")
            logging.info(f"   Dimensions: {dict(ds.dims)}")
            logging.info(f"   Period: {ds.attrs.get('climatological_period', 'unknown')}")
        return

    # Step 1: Download raw monthly means
    raw_file = download_era5_monthly_means()

    # Step 2: Compute climatology
    ds_clim = compute_climatology(raw_file)

    # Step 3: Save
    ds_clim.to_netcdf(OUTPUT_FILE)
    logging.info(f"\n   ✓ Saved: {OUTPUT_FILE.name} "
                 f"({OUTPUT_FILE.stat().st_size / 1024**2:.1f} MB)")

    # Print summary
    logging.info("\n   Summary:")
    for var in ds_clim.data_vars:
        data = ds_clim[var].values
        logging.info(f"     {var}: shape={data.shape}, "
                     f"range=[{np.nanmin(data):.2f}, {np.nanmax(data):.2f}]")

    logging.info(f"\n   Raw monthly-mean file kept at:")
    logging.info(f"     {raw_file}")
    logging.info("   (Delete manually if disk space is a concern.)")

    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 2.1 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"   Log: {log_file}")
    logging.info("\n   Next: python scripts/ep_structure_analysis/"
                 "step3_precompute_composites.py")


if __name__ == "__main__":
    main()
