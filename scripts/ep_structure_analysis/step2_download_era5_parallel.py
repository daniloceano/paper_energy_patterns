"""
Step 2: Download ERA5 Data in Parallel for EP1, EP2, EP3 Cyclones

Downloads ERA5 reanalysis data for all EP cyclones using only CENTRAL TIMESTEPS
from their intensification phase (canonical methodology April 2026).

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

Total: 9 levels

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
import atexit
import contextlib
import os
import re
import shutil
import sqlite3
import tempfile

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
from scripts.utils.ep_mapping import ALL_EPS, get_ep_abbrev, get_ep_label
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
CDS_URL = "https://cds.climate.copernicus.eu/api"
DEFAULT_KEYS_FILE = Path("/p1-swell/danilocs/cds-keys")
DEFAULT_KEY_HEALTH_DB = Path(
    "/p1-swell/danilocs/lec_climatology_corrected_v2/state.sqlite3"
)

_WORKER_KEY_ID = "default"
_WORKER_KEY_VALUE = ""
_WORKER_CREDENTIAL_HOME: Path | None = None

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


def load_cds_credentials(keys_file: Path, health_db: Path | None = None) -> list[tuple[str, str]]:
    """Load CDS tokens without exposing them and optionally keep only healthy keys.

    The server inventory format is ``<token> - <human label>``.  Only the first
    whitespace-delimited field is a credential.  Returned identifiers are
    synthetic (``key-001`` etc.) and are safe to write to logs.
    """
    lines = [line.strip() for line in keys_file.read_text().splitlines()]
    tokens = [
        line.split(maxsplit=1)[0]
        for line in lines
        if line and not line.startswith("#")
    ]
    if not tokens:
        raise RuntimeError(f"no CDS credentials found in {keys_file}")
    if len(tokens) != len(set(tokens)):
        raise RuntimeError("duplicate CDS credentials in inventory")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{32,}", token) for token in tokens):
        raise RuntimeError("unexpected CDS credential inventory format")

    credentials = [(f"key-{index:03d}", token) for index, token in enumerate(tokens, 1)]
    if health_db is None:
        return credentials
    if not health_db.is_file():
        raise FileNotFoundError(f"CDS key-health database not found: {health_db}")

    with sqlite3.connect(health_db) as connection:
        healthy = {
            str(row[0])
            for row in connection.execute(
                "SELECT key_id FROM key_health WHERE last_status = 'healthy'"
            )
        }
    selected = [item for item in credentials if item[0] in healthy]
    if not selected:
        raise RuntimeError("key-health database contains no healthy CDS credentials")
    return selected


def _cleanup_worker_credentials() -> None:
    global _WORKER_CREDENTIAL_HOME
    if _WORKER_CREDENTIAL_HOME is not None:
        shutil.rmtree(_WORKER_CREDENTIAL_HOME, ignore_errors=True)
        _WORKER_CREDENTIAL_HOME = None


def _init_cds_worker(credentials_queue, credentials_root: str) -> None:
    """Give one long-lived download worker exactly one isolated CDS token."""
    global _WORKER_KEY_ID, _WORKER_KEY_VALUE, _WORKER_CREDENTIAL_HOME
    key_id, key_value = credentials_queue.get()
    root = Path(credentials_root)
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    home = Path(tempfile.mkdtemp(prefix=f"{key_id}-", dir=root))
    os.chmod(home, 0o700)
    rc_path = home / ".cdsapirc"
    descriptor = os.open(rc_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(f"url: {CDS_URL}\nkey: {key_value}\n")
    os.environ["HOME"] = str(home)
    _WORKER_KEY_ID = key_id
    _WORKER_KEY_VALUE = key_value
    _WORKER_CREDENTIAL_HOME = home
    atexit.register(_cleanup_worker_credentials)


@contextlib.contextmanager
def cds_worker_pool(
    n_jobs: int,
    credentials: list[tuple[str, str]] | None,
    credentials_root: Path,
):
    """Create a pool whose workers use distinct CDS credentials."""
    if not credentials:
        with mp.Pool(processes=n_jobs) as pool:
            yield pool
        return

    queue = mp.Queue()
    for credential in credentials[:n_jobs]:
        queue.put(credential)
    pool = mp.Pool(
        processes=n_jobs,
        initializer=_init_cds_worker,
        initargs=(queue, str(credentials_root)),
    )
    try:
        yield pool
    finally:
        pool.close()
        pool.join()
        queue.close()
        # multiprocessing workers do not reliably execute Python atexit hooks
        # when the pool shuts down.  Remove the dedicated credential root from
        # the parent after every pool so no temporary .cdsapirc survives.
        shutil.rmtree(credentials_root, ignore_errors=True)


def safe_error(exc: Exception) -> str:
    """Return an error message with the active credential removed."""
    message = f"{type(exc).__name__}: {exc}"
    if _WORKER_KEY_VALUE:
        message = message.replace(_WORKER_KEY_VALUE, "<redacted>")
    return message

def validate_netcdf_file(
    nc_file,
    expected_pvars,
    expected_svars,
    expected_levels,
    expected_times=None,
):
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
            elif expected_times is not None and len(expected_times) > 0:
                available = pd.DatetimeIndex(pd.to_datetime(ds[tc].values))
                missing_times = []
                for expected in pd.DatetimeIndex(pd.to_datetime(expected_times)):
                    if len(available) == 0 or np.abs(available - expected).min() > pd.Timedelta(minutes=1):
                        missing_times.append(expected)
                if missing_times:
                    issues.append(
                        "Missing required times: "
                        + ", ".join(item.isoformat() for item in missing_times)
                    )

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
            nc_file,
            expected_pvars,
            expected_svars,
            PRESSURE_LEVELS,
            expected_times=parse_selected_times(row["selected_times"]),
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

def parse_selected_times(times_str: str) -> list:
    """Parse selected_times CSV column into list of datetime objects."""
    return [pd.to_datetime(t.strip()) for t in times_str.split(',')]


def compute_domain_bounds(track_id, selected_times_str):
    """
    Compute domain covering 30°×30° boxes centered on CENTRAL TIMESTEPS only.
    
    CANONICAL METHODOLOGY (April 2026):
    - Uses only the central timesteps (2 or 3) from intensification
    - Computes bounding box that covers 30°×30° area around each central position
    - This ensures sufficient spatial coverage for composite analysis
    
    Parameters
    ----------
    track_id : str
        Cyclone track identifier
    selected_times_str : str
        Comma-separated string of selected central timesteps
    
    Returns
    -------
    dict or None
        Dictionary with 'north', 'south', 'east', 'west', 'track_center_lat', 'track_center_lon'
    """
    selected_times = parse_selected_times(selected_times_str)
    
    tracks = load_tracks()
    track_data = tracks[tracks["track_id"] == track_id].copy()
    track_data["time"] = pd.to_datetime(track_data["date"])
    
    # Filter to only the selected central timesteps
    track_selected = track_data[track_data["time"].isin(selected_times)]

    if len(track_selected) == 0:
        logging.warning(f"   No track data found for selected times: {track_id}")
        return None

    # Compute bounding box covering all selected positions + buffer
    # Each position needs 15° buffer in each direction (30°×30° total)
    lats = track_selected["lat vor"].values
    lons = track_selected["lon vor"].values
    
    lat_min_required = lats.min() - DOMAIN_BUFFER
    lat_max_required = lats.max() + DOMAIN_BUFFER
    lon_min_required = lons.min() - DOMAIN_BUFFER
    lon_max_required = lons.max() + DOMAIN_BUFFER
    
    # Clamp latitude to valid range
    lat_min_required = max(-90, lat_min_required)
    lat_max_required = min(90, lat_max_required)
    
    # Track center (for metadata): use middle of selected timesteps
    center_idx = len(track_selected) // 2
    clat = track_selected["lat vor"].iloc[center_idx]
    clon = track_selected["lon vor"].iloc[center_idx]

    return {
        "north": lat_max_required,
        "south": lat_min_required,
        "east": lon_max_required,
        "west": lon_min_required,
        "track_center_lat": clat,
        "track_center_lon": clon,
    }


def drop_cds_auxiliary_coordinates(ds: xr.Dataset) -> xr.Dataset:
    """Remove scalar CDS bookkeeping coordinates before product merging.

    Recent pressure- and single-level responses can expose ``expver`` and
    ``number`` with different coordinate/data-variable roles.  They do not
    describe the meteorological grid, but their inconsistent roles make
    ``xarray.merge`` fail.  Removing only these known bookkeeping fields keeps
    the scientific coordinates and variables unchanged.
    """
    removable = [name for name in ("expver", "number") if name in ds.variables]
    return ds.drop_vars(removable) if removable else ds


# ============================================================================
# DOWNLOAD / PATCH
# ============================================================================

def download_era5_for_case(track_id, selected_times_str, domain):
    """
    Download ERA5 pressure-level + single-level data for CENTRAL TIMESTEPS only.
    
    CANONICAL METHODOLOGY (April 2026):
    - Downloads only the 2-3 selected central timesteps
    - Significantly reduces data volume compared to full intensification
    """
    selected_times = parse_selected_times(selected_times_str)
    
    logging.info(f"      Downloading {track_id}")
    logging.info(f"         Selected timesteps: {len(selected_times)}")
    logging.info(f"         Times: {', '.join([t.strftime('%Y-%m-%d %H:%M') for t in selected_times])}")

    # Convert selected times to CDS API format
    years = sorted(set(str(t.year) for t in selected_times))
    months = sorted(set(f"{t.month:02d}" for t in selected_times))
    days = sorted(set(f"{t.day:02d}" for t in selected_times))
    times = sorted(set(t.strftime("%H:%M") for t in selected_times))

    c = cdsapi.Client(timeout=600, retry_max=3, quiet=True)

    partial_dir = DATA_DIR / ".partial" / f"{track_id}-{os.getpid()}"
    partial_dir.mkdir(parents=True, exist_ok=True)
    pf = partial_dir / f"{track_id}_era5_pressure.nc"
    sf = partial_dir / f"{track_id}_era5_single.nc"
    candidate = partial_dir / f"{track_id}_era5.nc"
    metadata_candidate = partial_dir / f"{track_id}_metadata.csv"
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
        with xr.open_dataset(pf) as ds_p, xr.open_dataset(sf) as ds_s:
            ds_m = xr.merge(
                [
                    drop_cds_auxiliary_coordinates(ds_p),
                    drop_cds_auxiliary_coordinates(ds_s),
                ],
                compat="override",
                join="exact",
            ).load()

        time_coord = "valid_time" if "valid_time" in ds_m.coords else "time"
        wanted_times = pd.DatetimeIndex(selected_times)
        available_times = pd.DatetimeIndex(pd.to_datetime(ds_m[time_coord].values))
        selected_indices = []
        for wanted in wanted_times:
            offsets = np.abs(available_times - wanted)
            if len(offsets) == 0 or offsets.min() > pd.Timedelta(minutes=1):
                raise ValueError(f"CDS response lacks required time {wanted.isoformat()}")
            selected_indices.append(int(offsets.argmin()))
        if len(set(selected_indices)) != len(selected_indices):
            raise ValueError("CDS response maps multiple required times to one timestep")
        ds_m = ds_m.isel({time_coord: selected_indices})
        ds_m.to_netcdf(candidate)
        ds_m.close()

        valid, issues, _, _ = validate_netcdf_file(
            candidate,
            list(NCVAR_PRESSURE.values()),
            list(NCVAR_SINGLE.values()),
            PRESSURE_LEVELS,
            expected_times=selected_times,
        )
        if not valid:
            raise ValueError("downloaded candidate failed validation: " + "; ".join(issues))

        logging.info(f"      ✓ {of}")

        # metadata
        selected_times = parse_selected_times(selected_times_str)
        meta = {
            "track_id": track_id,
            "n_timesteps_selected": len(selected_times),
            "selected_times": selected_times_str,
            "first_time": selected_times[0].isoformat(),
            "last_time": selected_times[-1].isoformat(),
            "north": domain["north"],
            "south": domain["south"],
            "east": domain["east"],
            "west": domain["west"],
            "track_center_lat": domain["track_center_lat"],
            "track_center_lon": domain["track_center_lon"],
            "pressure_levels_hPa": PRESSURE_LEVELS,
            "methodology": "Canonical April 2026 - central timesteps only",
        }
        pd.DataFrame([meta]).to_csv(metadata_candidate, index=False)

        # Replace the old file only after the complete candidate validates.
        candidate.replace(of)
        metadata_candidate.replace(DATA_DIR / f"{track_id}_metadata.csv")
        shutil.rmtree(partial_dir, ignore_errors=True)
        return True

    except Exception as e:
        logging.error(f"      ❌ {track_id} [{_WORKER_KEY_ID}]: {safe_error(e)}")
        shutil.rmtree(partial_dir, ignore_errors=True)
        return False


def patch_era5_file(track_id, selected_times_str, domain, missing_vars, missing_levels):
    """Download only missing variables/levels and merge with existing file."""
    logging.info(f"      Patching {track_id} (vars={missing_vars}, levels={missing_levels})")

    selected_times = parse_selected_times(selected_times_str)
    original = DATA_DIR / f"{track_id}_era5.nc"
    backup = DATA_DIR / f"{track_id}_era5_backup.nc"

    # Convert selected times to CDS API format
    years = sorted(set(str(t.year) for t in selected_times))
    months = sorted(set(f"{t.month:02d}" for t in selected_times))
    days = sorted(set(f"{t.day:02d}" for t in selected_times))
    times = sorted(set(t.strftime("%H:%M") for t in selected_times))

    c = cdsapi.Client(timeout=600, retry_max=3, quiet=True)

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
        logging.error(f"      ❌ Patch failed {track_id} [{_WORKER_KEY_ID}]: {safe_error(e)}")
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
        selected_times_str = row["selected_times"]
        domain = compute_domain_bounds(track_id, selected_times_str)
        if domain is None:
            return (track_id, False)
        return (track_id, download_era5_for_case(track_id, selected_times_str, domain))
    except Exception as e:
        logging.error(f"      ❌ {track_id}: {e}")
        return (track_id, False)


def _patch_wrapper(args):
    idx, row, mvars, mlevels, total = args
    track_id = row["track_id"]
    try:
        selected_times_str = row["selected_times"]
        mf = DATA_DIR / f"{track_id}_metadata.csv"
        if mf.exists():
            m = pd.read_csv(mf).iloc[0]
            domain = {k: m[k] for k in ["north", "south", "east", "west", "track_center_lat", "track_center_lon"]}
        else:
            domain = compute_domain_bounds(track_id, selected_times_str)
            if domain is None:
                return (track_id, False)
        return (track_id, patch_era5_file(track_id, selected_times_str, domain, mvars, mlevels))
    except Exception as e:
        logging.error(f"      ❌ {track_id}: {e}")
        return (track_id, False)


# ============================================================================
# PROCESS ONE EP GROUP
# ============================================================================

def process_ep_group(
    ep_label,
    cases,
    n_jobs,
    credentials=None,
    credentials_root=None,
    force_download_ids=None,
):
    """Validate, patch and download for one EP group. Returns (n_valid, n_failed)."""
    _print_only(f"\n{'─'*60}")
    _print_only(f"  {ep_label}: {len(cases)} cyclones")
    _print_only(f"{'─'*60}")

    logging.info(f"\n{'='*60}")
    logging.info(f"  Processing {ep_label} ({len(cases)} cases)")
    logging.info(f"{'='*60}")

    force_download_ids = set(force_download_ids or ())
    credentials_root = credentials_root or DATA_DIR / ".cds_credentials"
    forced = cases[cases["track_id"].astype(str).isin(force_download_ids)]
    ordinary = cases[~cases["track_id"].astype(str).isin(force_download_ids)]
    to_download, to_patch, valid, invalid = check_existing_files(ordinary, ep_label)
    to_download.extend((index, row) for index, row in forced.iterrows())

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
        with cds_worker_pool(n_jobs, credentials, credentials_root) as pool:
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
        with cds_worker_pool(n_jobs, credentials, credentials_root) as pool:
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
    global DATA_DIR
    parser = argparse.ArgumentParser(description="Download ERA5 data for EP structure analysis")
    parser.add_argument("--jobs", type=int, default=None,
                        help=f"Parallel CDS jobs (default: {MAX_PARALLEL_JOBS})")
    parser.add_argument("--log-file", type=str, default=None)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Canonical ERA5 archive to validate and update",
    )
    parser.add_argument(
        "--keys-file",
        type=Path,
        default=None,
        help=(
            "Multi-key CDS inventory. Each worker receives one isolated key; "
            f"server default: {DEFAULT_KEYS_FILE}"
        ),
    )
    parser.add_argument(
        "--key-health-db",
        type=Path,
        default=None,
        help=(
            "Optional key-health SQLite database; only keys marked healthy are used. "
            f"Server default: {DEFAULT_KEY_HEALTH_DB}"
        ),
    )
    parser.add_argument(
        "--audit-csv",
        type=Path,
        default=None,
        help=(
            "Output from audit_era5_reuse.py. Only rows whose status is not "
            "'reusable' are downloaded, and their old files remain until replacement validates."
        ),
    )
    args = parser.parse_args()
    DATA_DIR = args.data_dir.resolve()

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
    # Load all EP groups (EP1, EP2, EP3)
    ep_cases = {}
    missing_files = []
    
    for ep_num in ALL_EPS:
        ep_abbrev = get_ep_abbrev(ep_num)
        ep_file = RESULTS_DIR / f"{ep_abbrev}_cases.csv"
        
        if not ep_file.exists():
            missing_files.append(ep_file)
        else:
            ep_cases[ep_num] = pd.read_csv(ep_file)
    
    if missing_files:
        msg = f"❌ Case files not found: {', '.join([str(f) for f in missing_files])}. Run step1 first."
        _print_only(msg)
        logging.error(msg)
        return 1

    all_cases = pd.concat([ep_cases[ep] for ep in ALL_EPS], ignore_index=True)

    force_download_ids = set()
    if args.audit_csv is not None:
        audit = pd.read_csv(args.audit_csv, dtype={"track_id": str})
        required_columns = {"track_id", "status"}
        missing_columns = required_columns - set(audit.columns)
        if missing_columns:
            raise ValueError(
                f"audit CSV lacks columns: {sorted(missing_columns)}"
            )
        force_download_ids = set(
            audit.loc[audit["status"] != "reusable", "track_id"].astype(str)
        )
        if not force_download_ids:
            _print_only("\n  ✓ Audit reports every case reusable; nothing to download.")
            return 0
        _print_only(
            f"\n  Audit repair set: {len(force_download_ids)} cases require replacement"
        )
        ep_cases = {
            ep: frame[frame["track_id"].astype(str).isin(force_download_ids)].copy()
            for ep, frame in ep_cases.items()
        }
        all_cases = pd.concat([ep_cases[ep] for ep in ALL_EPS], ignore_index=True)

    _print_only(f"\n  EP1: {len(ep_cases[1])} cases  |  EP2: {len(ep_cases[2])} cases  |  EP3: {len(ep_cases[3])} cases  |  Total: {len(all_cases)}")
    _print_only(f"  Methodology: CANONICAL (Central timesteps only, April 2026)")
    _print_only(f"  Levels: {sorted(PRESSURE_LEVELS)} hPa")
    _print_only(f"  Variables: {list(NCVAR_PRESSURE.values()) + list(NCVAR_SINGLE.values())}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    credentials = None
    if args.keys_file is not None:
        credentials = load_cds_credentials(args.keys_file, args.key_health_db)
        _print_only(
            f"  CDS credentials: {len(credentials)} healthy keys loaded; values are never logged"
        )

    n_jobs = args.jobs if args.jobs is not None else MAX_PARALLEL_JOBS
    if credentials:
        n_jobs = min(n_jobs, len(credentials))
    if n_jobs > 22:
        _print_only("  ⚠️  Capping parallel CDS jobs at 22 (validated server limit)")
        n_jobs = 22
    elif n_jobs > 4 and not credentials:
        _print_only(f"  ⚠️  {n_jobs} jobs share the default CDS account")
    _print_only(f"  Parallel jobs: {n_jobs}")

    t0 = time.time()

    # ── Process each EP ───────────────────────────────────────────────────────
    ep_results = {}
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        n_ok, n_fail = process_ep_group(
            ep_label,
            ep_cases[ep_num],
            n_jobs,
            credentials=credentials,
            credentials_root=DATA_DIR / ".cds_credentials",
            force_download_ids=force_download_ids,
        )
        ep_results[ep_num] = (n_ok, n_fail)

    elapsed = time.time() - t0

    # ── Final report ──────────────────────────────────────────────────────────
    _print_only(f"\n{'='*60}")
    _print_only(f"  DOWNLOAD COMPLETE  ({elapsed/60:.1f} min)")
    _print_only(f"{'='*60}")
    
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        n_ok, n_fail = ep_results[ep_num]
        _print_only(f"  {ep_label}: {n_ok}/{len(ep_cases[ep_num])} valid  ({n_fail} failed)")
    
    total_ok = sum(r[0] for r in ep_results.values())
    total_fail = sum(r[1] for r in ep_results.values())
    _print_only(f"  Total: {total_ok}/{len(all_cases)} valid")

    logging.info(f"\nDOWNLOAD COMPLETE ({elapsed/60:.1f} min)")
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        n_ok, n_fail = ep_results[ep_num]
        logging.info(f"  {ep_label}: {n_ok}/{len(ep_cases[ep_num])}")

    print_completeness_report(all_cases)

    if total_fail == 0:
        _print_only("\n  ✓ All files ready!")
        _print_only("  Next: python scripts/ep_structure_analysis/step3_precompute_composites.py")
    elif total_fail > 0:
        _print_only(f"\n  ⚠️  {total_fail} failed — re-run to retry (or use --jobs 2)")

    _print_only(f"\n  Log: {log_file}")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
