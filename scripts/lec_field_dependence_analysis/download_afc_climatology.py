"""Download the expanded ERA5 climatology required by AFC.

Why this script exists
----------------------
The general EP-structure climatology covers 80 W--40 E. Two eligible cyclones
have 30-degree storm domains that extend beyond those limits, producing missing
AFC values inside the 15-degree feature box. This dedicated, restartable step
downloads only the required 250-hPa monthly means on 90 W--60 E, leaving the
existing climatology untouched. It uses one isolated CDS credential per worker.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import cdsapi
import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ep_structure_analysis.step2_download_era5_parallel import (
    cds_worker_pool,
    load_cds_credentials,
    safe_error,
)


YEARS = [str(year) for year in range(1991, 2021)]
MONTHS = list(range(1, 13))
VARIABLES = [
    "u_component_of_wind",
    "v_component_of_wind",
    "geopotential",
]
EXPECTED_VARS = ["u", "v", "z"]
DOMAIN = {"north": -5.0, "west": -90.0, "south": -80.0, "east": 60.0}
DATASET = "reanalysis-era5-pressure-levels-monthly-means"


def _raw_path(output_dir, month):
    return output_dir / "raw" / f"afc_250_month{month:02d}.nc"


def _valid_raw(path):
    if not path.is_file() or path.stat().st_size < 1024:
        return False
    try:
        with xr.open_dataset(path) as ds:
            if any(name not in ds for name in EXPECTED_VARS):
                return False
            lon_min = float(ds.longitude.min())
            lon_max = float(ds.longitude.max())
            lat_min = float(ds.latitude.min())
            lat_max = float(ds.latitude.max())
            return (
                lon_min <= DOMAIN["west"]
                and lon_max >= DOMAIN["east"]
                and lat_min <= DOMAIN["south"]
                and lat_max >= DOMAIN["north"]
            )
    except Exception:
        return False


def _download_month(task):
    month, output_dir = task
    output_dir = Path(output_dir)
    destination = _raw_path(output_dir, month)
    if _valid_raw(destination):
        return month, "reused", str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".nc.partial")
    partial.unlink(missing_ok=True)
    request = {
        "product_type": "monthly_averaged_reanalysis",
        "format": "netcdf",
        "variable": VARIABLES,
        "year": YEARS,
        "month": [f"{month:02d}"],
        "time": "00:00",
        "pressure_level": ["250"],
        "area": [
            DOMAIN["north"], DOMAIN["west"],
            DOMAIN["south"], DOMAIN["east"],
        ],
    }
    try:
        cdsapi.Client().retrieve(DATASET, request, str(partial))
        if not _valid_raw(partial):
            raise RuntimeError("downloaded NetCDF failed content/domain validation")
        partial.replace(destination)
        return month, "downloaded", str(destination)
    except Exception as exc:
        partial.unlink(missing_ok=True)
        return month, f"failed: {safe_error(exc)}", ""


def _build_climatology(output_dir):
    monthly = []
    for month in MONTHS:
        path = _raw_path(output_dir, month)
        if not _valid_raw(path):
            raise RuntimeError(f"month {month:02d} is missing or invalid: {path}")
        with xr.open_dataset(path) as source:
            time_coord = "valid_time" if "valid_time" in source.dims else "time"
            mean = source.mean(dim=time_coord).load()
        pressure_coord = (
            "pressure_level" if "pressure_level" in mean.dims else "level"
        )
        if pressure_coord in mean.dims:
            mean = mean.squeeze(pressure_coord, drop=True)
        mean = mean.rename({"u": "u_clim", "v": "v_clim", "z": "z_clim"})
        monthly.append(mean.expand_dims(month=[month]))
    climatology = xr.concat(monthly, dim="month")
    climatology.attrs.update({
        "description": "Expanded ERA5 monthly climatology for AFC at 250 hPa",
        "climatological_period": "1991-2020",
        "domain": "80S-5S, 90W-60E",
        "purpose": "Complete AFC coverage for all eligible LEC-field cases",
        "created_by": "download_afc_climatology.py",
        "created": datetime.now().isoformat(),
    })
    output = output_dir / "era5_climatology_250hPa_expanded.nc"
    partial = output.with_suffix(".nc.partial")
    try:
        climatology.to_netcdf(partial)
        with xr.open_dataset(partial) as check:
            if set(check.data_vars) != {"u_clim", "v_clim", "z_clim"}:
                raise RuntimeError("final climatology has unexpected variables")
            if dict(check.sizes).get("month") != 12:
                raise RuntimeError("final climatology does not contain 12 months")
            if not np.isfinite(check["u_clim"].values).all():
                raise RuntimeError("final climatology contains non-finite values")
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Download the expanded 250-hPa AFC climatology."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--keys-file", type=Path, required=True)
    parser.add_argument("--key-health-db", type=Path, default=None)
    parser.add_argument("--jobs", type=int, default=12)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be >= 1")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    credentials = load_cds_credentials(
        args.keys_file.resolve(),
        args.key_health_db.resolve() if args.key_health_db else None,
    )
    jobs = min(args.jobs, len(credentials), len(MONTHS), 22)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(output_dir / "download_afc_climatology.log"),
            logging.StreamHandler(),
        ],
    )
    logging.info("Expanded AFC domain: %s", DOMAIN)
    logging.info("Using %s workers with isolated credentials", jobs)

    tasks = [(month, str(output_dir)) for month in MONTHS]
    with cds_worker_pool(
        jobs, credentials, output_dir / ".cds_credentials"
    ) as pool:
        results = list(pool.imap_unordered(_download_month, tasks))
    results.sort()
    failures = []
    for month, status, path in results:
        logging.info("Month %02d: %s %s", month, status, path)
        if status.startswith("failed"):
            failures.append((month, status))
    if failures:
        logging.error("Download failures: %s", failures)
        sys.exit(1)

    output = _build_climatology(output_dir)
    logging.info("Expanded AFC climatology ready: %s", output)


if __name__ == "__main__":
    main()
