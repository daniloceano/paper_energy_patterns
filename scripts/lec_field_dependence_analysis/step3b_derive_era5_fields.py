"""
Step 3b: Derive ERA5 Dynamic Fields from Raw Per-Cyclone Data

⟵ Prerequisite: step 3 (ERA5 field mapping) must be complete.
⟶ Outputs required by: step 4 (absolute features) and step 5 (anomaly features).

Motivation
----------
The raw per-cyclone ERA5 files (*_era5.nc) contain instantaneous multi-level
fields (u, v, t, z, q, msl) downloaded by the ep_structure_analysis pipeline.
Steps 4 and 5 of this pipeline need higher-level dynamic diagnostics —
pv_850, pv_200, adv_T_850, ke_adv_250, afc_250 — that are NOT stored in the
raw files and must be derived.

This step fills that gap: it reads the raw ERA5 file for each cyclone, extracts
the storm-centred subdomain at the canonical central timestep, computes the
derived fields, and saves them to a separate derived NetCDF, leaving the raw
data completely untouched.

Scientific methodology
----------------------
The diagnostic computations are **not reimplemented here**.  They are imported
directly from scripts/ep_structure_analysis/step3_precompute_composites.py,
which carries the validated, project-canonical implementations:

    compute_pv_at_level              — baroclinic PV via MetPy (3-level centred FD)
    temperature_advection_850        — -V·∇T via MetPy (spherical geometry)
    kinetic_energy_advection_250     — -V·∇(½|V|²) via MetPy
    ageostrophic_flux_convergence_250 — -∇·(v_ag'φ'), requires era5_climatology_250hPa.nc

Same pressure-level triples are used:
    PV@200 hPa  → 175 / 200 / 225 hPa
    PV@850 hPa  → 825 / 850 / 875 hPa
    T_adv@850   → single level: 850 hPa
    KE_adv@250  → single level: 250 hPa
    AFC@250     → 250 hPa + 30-year monthly climatology (optional)

Temporal representation
-----------------------
Like the composite step in ep_structure_analysis, this step uses only the
CENTRAL timestep of each cyclone's intensification phase.  If the central
timestep position is not found in the track data, it falls back to the first
available timestep with a position match.

Storage strategy
----------------
    Raw ERA5 files    : {era5_dir}/{track_id}_era5.nc          (NEVER modified)
    Derived files     : {derived_dir}/{track_id}_era5_derived.nc (created here)

The derived directory is independent of the raw ERA5 directory.  It defaults to
{era5_dir}/derived/ but can be overridden with --derived-dir.

--- REMOTE EXECUTION REQUIRED ---

Usage
-----
    # All cyclones, parallel chunks (recommended on HPC)
    python step3b_derive_era5_fields.py --era5-dir /path/to/era5/

    # Custom derived output directory
    python step3b_derive_era5_fields.py \
        --era5-dir /path/to/era5/ --derived-dir /path/to/derived/

    # Parallel chunks (HPC mode — same pattern as steps 4/5)
    python step3b_derive_era5_fields.py \
        --era5-dir /path/to/era5/ --chunk 0 --n-chunks 16

Output
------
    {derived_dir}/{track_id}_era5_derived.nc   — one file per cyclone
    results/lec_field_dependence/step3b_derived_field_manifest.csv  — summary

Fields in each derived NetCDF
------------------------------
    pv_850      Potential Vorticity @ 850 hPa   [K m² kg⁻¹ s⁻¹]
    pv_200      Potential Vorticity @ 200 hPa   [K m² kg⁻¹ s⁻¹]
    adv_T_850   Temperature Advection @ 850 hPa [K s⁻¹]
    ke_adv_250  KE Advection @ 250 hPa          [W kg⁻¹]
    afc_250     Ageostrophic Flux Convergence @ 250 hPa [W kg⁻¹]
                (only when era5_climatology_250hPa.nc is available)

Coordinates: latitude and longitude in the storm-centred domain (-15° to +15°).

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr
from concurrent.futures import ProcessPoolExecutor, as_completed

from metpy.units import units

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR,
    LOG_DIR,
)

# ---------------------------------------------------------------------------
# Reuse validated physics functions from ep_structure_analysis — no
# reimplementation of any diagnostic formula.
# ---------------------------------------------------------------------------
from scripts.ep_structure_analysis.step3_precompute_composites import (
    compute_pv_at_level,
    temperature_advection_850,
    kinetic_energy_advection_250,
    ageostrophic_flux_convergence_250,
    get_cyclone_positions_for_case,
    extract_subdomain,
    _get_case_start_time,
    _load_clim,
    CLIMATOLOGY_FILE,
    DOMAIN_SIZE,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_MANIFEST = RESULTS_DIR / "step3_era5_field_manifest.csv"
OUTPUT_MANIFEST = RESULTS_DIR / "step3b_derived_field_manifest.csv"

ERA5_FILE_PATTERN = "{track_id}_era5.nc"
DERIVED_FILE_PATTERN = "{track_id}_era5_derived.nc"

# Variables that MUST be present in a raw ERA5 file to proceed
REQUIRED_RAW_VARS = ["u", "v", "t", "z"]

# Every derived file must have ALL of these to be considered valid
REQUIRED_DERIVED_VARS = ["pv_850", "pv_200", "adv_T_850", "ke_adv_250"]

# afc_250 is computed only when the climatology file is available
OPTIONAL_DERIVED_VARS = ["afc_250"]

# Required pressure levels in raw ERA5 files
REQUIRED_LEVELS_FOR_PV200 = [175, 200, 225]
REQUIRED_LEVELS_FOR_PV850 = [825, 850, 875]
REQUIRED_LEVELS_FOR_ADV = [850]
REQUIRED_LEVELS_FOR_KE = [250]
REQUIRED_LEVELS_ALL = sorted(set(
    REQUIRED_LEVELS_FOR_PV200 +
    REQUIRED_LEVELS_FOR_PV850 +
    REQUIRED_LEVELS_FOR_ADV +
    REQUIRED_LEVELS_FOR_KE
))

N_WORKERS_DEFAULT = 4


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(chunk_id=None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_chunk{chunk_id}" if chunk_id is not None else ""
    log_file = LOG_DIR / f"lec_field_step3b{suffix}_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"Log file: {log_file}")


# ---------------------------------------------------------------------------
# Helper: extract plain numpy array from any MetPy / xarray result
# ---------------------------------------------------------------------------

def _to_array(da) -> np.ndarray:
    """
    Extract a plain numpy ndarray from a MetPy pint-backed DataArray,
    a regular xarray DataArray, a pint Quantity, or any array-like.
    """
    # MetPy pint-backed DataArray (most common case after our diagnostics)
    if hasattr(da, "metpy") and hasattr(da.metpy, "unit_array"):
        try:
            return np.asarray(da.metpy.unit_array.magnitude)
        except Exception:
            pass
    # Regular xarray DataArray
    if hasattr(da, "values"):
        val = da.values
        if hasattr(val, "magnitude"):
            return np.asarray(val.magnitude)
        return np.asarray(val)
    # pint Quantity
    if hasattr(da, "magnitude"):
        return np.asarray(da.magnitude)
    return np.asarray(da)


# ---------------------------------------------------------------------------
# Validation of a derived NetCDF file
# ---------------------------------------------------------------------------

def _validate_derived_nc(fpath: Path) -> tuple:
    """
    Validate a derived NetCDF file.

    Returns
    -------
    (bool, str)
        (is_valid, status_message)
    """
    if not fpath.exists():
        return False, "file_missing"
    try:
        ds = xr.open_dataset(fpath)
    except Exception as e:
        return False, f"open_error: {e}"

    missing = [v for v in REQUIRED_DERIVED_VARS if v not in ds.data_vars]
    if missing:
        ds.close()
        return False, f"missing_required_vars: {missing}"

    all_nan = [
        v for v in REQUIRED_DERIVED_VARS
        if np.all(np.isnan(ds[v].values))
    ]
    if all_nan:
        ds.close()
        return False, f"all_nan: {all_nan}"

    ds.close()
    return True, "ok"


# ---------------------------------------------------------------------------
# Single-cyclone derivation
# ---------------------------------------------------------------------------

def _derive_fields_for_cyclone(track_id: str, era5_dir: Path, derived_dir: Path) -> dict:
    """
    Derive all dynamic fields for one cyclone and save the result.

    Returns
    -------
    dict
        {
            'track_id': str,
            'status': 'ok' | <failure_reason>,
            'output_path': str,
            'has_afc': bool,
        }
    """
    fname = ERA5_FILE_PATTERN.format(track_id=track_id)
    fpath = era5_dir / fname
    out_fname = DERIVED_FILE_PATTERN.format(track_id=track_id)
    out_path = derived_dir / out_fname

    if not fpath.exists():
        return {
            "track_id": track_id,
            "status": "file_not_found",
            "output_path": "",
            "has_afc": False,
        }

    try:
        ds = xr.open_dataset(fpath)
    except Exception as e:
        return {
            "track_id": track_id,
            "status": f"open_error: {e}",
            "output_path": "",
            "has_afc": False,
        }

    # ── Validate required raw variables ──────────────────────────────────
    missing_raw = [v for v in REQUIRED_RAW_VARS if v not in ds.data_vars]
    if missing_raw:
        ds.close()
        return {
            "track_id": track_id,
            "status": f"missing_raw_vars: {missing_raw}",
            "output_path": "",
            "has_afc": False,
        }

    try:
        # ── Pressure level coordinate ─────────────────────────────────────
        pc = "pressure_level" if "pressure_level" in ds.coords else "level"
        levels = ds[pc].values

        # Validate critical pressure levels are present
        for req_lev in REQUIRED_LEVELS_ALL:
            if np.min(np.abs(levels - req_lev)) > 10.0:
                ds.close()
                return {
                    "track_id": track_id,
                    "status": f"missing_pressure_level: {req_lev} hPa not found (nearest: {levels[np.argmin(np.abs(levels - req_lev))]})",
                    "output_path": "",
                    "has_afc": False,
                }

        # ── Time coordinate ───────────────────────────────────────────────
        tc = "valid_time" if "valid_time" in ds.dims else "time"
        era5_times = ds[tc].values
        n_times = len(era5_times)

        if n_times == 0:
            ds.close()
            return {
                "track_id": track_id,
                "status": "no_timesteps",
                "output_path": "",
                "has_afc": False,
            }

        # ── Get cyclone position for the central timestep ─────────────────
        positions = get_cyclone_positions_for_case(int(track_id), era5_times)
        central_idx = positions.get("central_idx", n_times // 2)
        pos = positions.get(central_idx)

        if pos is None:
            # Fall back to the first timestep that has a position match
            for ti in range(n_times):
                if positions.get(ti) is not None:
                    central_idx = ti
                    pos = positions.get(ti)
                    break
            if pos is None:
                ds.close()
                return {
                    "track_id": track_id,
                    "status": "no_valid_position",
                    "output_path": "",
                    "has_afc": False,
                }

        center_lat, center_lon = pos

        # ── Extract storm-centred subdomain ───────────────────────────────
        ds_t = ds.isel({tc: central_idx})
        try:
            ds_c = extract_subdomain(ds_t, center_lat, center_lon, DOMAIN_SIZE)
        except Exception as e:
            ds.close()
            return {
                "track_id": track_id,
                "status": f"subdomain_error: {e}",
                "output_path": "",
                "has_afc": False,
            }

        # ── Determine case month for AFC climatology ──────────────────────
        try:
            meta_path = era5_dir / f"{track_id}_metadata.csv"
            if meta_path.exists():
                meta = pd.read_csv(meta_path).iloc[0]
                case_month = _get_case_start_time(meta).month
            else:
                case_month = pd.Timestamp(era5_times[central_idx]).month
        except Exception:
            case_month = pd.Timestamp(era5_times[central_idx]).month

        ds.close()

        # ── Level helpers on the centred subdomain ────────────────────────
        def _idx(target_hPa):
            return int(np.argmin(np.abs(levels - target_hPa)))

        def _sel(da, target_hPa):
            return da.isel({pc: _idx(target_hPa)})

        u_da = ds_c["u"]
        v_da = ds_c["v"]
        T_da = ds_c["t"]
        z_da = ds_c["z"]

        # Log subdomain info for the first cyclone to aid diagnostics
        if not hasattr(_derive_fields_for_cyclone, "_logged_once"):
            _derive_fields_for_cyclone._logged_once = True
            logging.info(
                f"   Subdomain info for {track_id}: dims={dict(ds_c.sizes)} "
                f"lat=[{float(ds_c.latitude.min()):.2f},{float(ds_c.latitude.max()):.2f}] "
                f"lon=[{float(ds_c.longitude.min()):.2f},{float(ds_c.longitude.max()):.2f}] "
                f"levels={levels.tolist()} "
                f"T_850_range=[{float((_sel(T_da,850)).min()):.1f},{float((_sel(T_da,850)).max()):.1f}]K "
                f"u_850_range=[{float((_sel(u_da,850)).min()):.1f},{float((_sel(u_da,850)).max()):.1f}]m/s "
                f"has_nan_u850={bool(np.any(np.isnan(_sel(u_da,850).values)))} "
                f"has_nan_T850={bool(np.any(np.isnan(_sel(T_da,850).values)))}"
            )

        # ── PV @ 850 hPa ──────────────────────────────────────────────────
        pv_850_arr = compute_pv_at_level(
            _sel(u_da, 825) * units("m/s"),
            _sel(u_da, 850) * units("m/s"),
            _sel(u_da, 875) * units("m/s"),
            _sel(v_da, 825) * units("m/s"),
            _sel(v_da, 850) * units("m/s"),
            _sel(v_da, 875) * units("m/s"),
            _sel(T_da, 825) * units.kelvin,
            _sel(T_da, 850) * units.kelvin,
            _sel(T_da, 875) * units.kelvin,
            np.array([
                levels[_idx(825)],
                levels[_idx(850)],
                levels[_idx(875)],
            ]) * 100.0,
        )

        # ── PV @ 200 hPa ──────────────────────────────────────────────────
        pv_200_arr = compute_pv_at_level(
            _sel(u_da, 175) * units("m/s"),
            _sel(u_da, 200) * units("m/s"),
            _sel(u_da, 225) * units("m/s"),
            _sel(v_da, 175) * units("m/s"),
            _sel(v_da, 200) * units("m/s"),
            _sel(v_da, 225) * units("m/s"),
            _sel(T_da, 175) * units.kelvin,
            _sel(T_da, 200) * units.kelvin,
            _sel(T_da, 225) * units.kelvin,
            np.array([
                levels[_idx(175)],
                levels[_idx(200)],
                levels[_idx(225)],
            ]) * 100.0,
        )

        # ── Temperature advection @ 850 hPa ──────────────────────────────
        u_850 = _sel(u_da, 850) * units("m/s")
        v_850 = _sel(v_da, 850) * units("m/s")
        T_850 = _sel(T_da, 850) * units.kelvin
        adv_T_850_da = temperature_advection_850(u_850, v_850, T_850)
        adv_T_850_2d = _to_array(adv_T_850_da).squeeze()

        # ── KE advection @ 250 hPa ────────────────────────────────────────
        u_250 = _sel(u_da, 250) * units("m/s")
        v_250 = _sel(v_da, 250) * units("m/s")
        ke_adv_250_da = kinetic_energy_advection_250(u_250, v_250)
        ke_adv_250_2d = _to_array(ke_adv_250_da).squeeze()

        # ── AFC @ 250 hPa (requires climatology) ──────────────────────────
        afc_2d = None
        has_afc = False
        z_250 = _sel(z_da, 250) * units("m**2/s**2")

        ds_clim = _load_clim(
            CLIMATOLOGY_FILE,
            "250 hPa (AFC)",
            "AFC derivation skipped — climatology file absent.",
        )
        if ds_clim is not None:
            try:
                case_lats = u_250.latitude.values
                case_lons = u_250.longitude.values
                clim_sub = ds_clim.sel(month=case_month).interp(
                    latitude=case_lats,
                    longitude=case_lons,
                    method="linear",
                )
                afc_da = ageostrophic_flux_convergence_250(
                    u_250, v_250, z_250,
                    clim_sub["u_clim"],
                    clim_sub["v_clim"],
                    clim_sub["z_clim"],
                )
                afc_2d = _to_array(afc_da).squeeze()
                has_afc = True
            except Exception as e_afc:
                logging.warning(
                    f"   {track_id}: AFC computation failed ({type(e_afc).__name__}: {e_afc})"
                )

        # ── Build output dataset ──────────────────────────────────────────
        lat_out = ds_c["latitude"].values
        lon_out = ds_c["longitude"].values
        coords = {"latitude": lat_out, "longitude": lon_out}
        dims = ["latitude", "longitude"]

        pv_850_2d = np.asarray(pv_850_arr).squeeze()
        pv_200_2d = np.asarray(pv_200_arr).squeeze()

        data_vars = {
            "pv_850": xr.DataArray(
                pv_850_2d, coords=coords, dims=dims,
                attrs={
                    "long_name": "Potential Vorticity at 850 hPa",
                    "units": "K m2 kg-1 s-1",
                    "method": "MetPy baroclinic PV, centred FD over 825/850/875 hPa",
                },
            ),
            "pv_200": xr.DataArray(
                pv_200_2d, coords=coords, dims=dims,
                attrs={
                    "long_name": "Potential Vorticity at 200 hPa",
                    "units": "K m2 kg-1 s-1",
                    "method": "MetPy baroclinic PV, centred FD over 175/200/225 hPa",
                },
            ),
            "adv_T_850": xr.DataArray(
                adv_T_850_2d, coords=coords, dims=dims,
                attrs={
                    "long_name": "Temperature Advection at 850 hPa (-V.gradT)",
                    "units": "K s-1",
                    "sign_convention": "positive = warm advection",
                },
            ),
            "ke_adv_250": xr.DataArray(
                ke_adv_250_2d, coords=coords, dims=dims,
                attrs={
                    "long_name": "Kinetic Energy Advection at 250 hPa (-V.grad(KE))",
                    "units": "W kg-1",
                },
            ),
        }

        if afc_2d is not None:
            data_vars["afc_250"] = xr.DataArray(
                afc_2d, coords=coords, dims=dims,
                attrs={
                    "long_name": "Ageostrophic Flux Convergence at 250 hPa",
                    "units": "W kg-1",
                    "method": "Orlanski & Katzfey (1991); reference: 30-yr monthly climatology",
                },
            )

        ds_out = xr.Dataset(
            data_vars,
            attrs={
                "track_id": str(track_id),
                "center_lat": float(center_lat),
                "center_lon": float(center_lon),
                "central_timestep_idx": int(central_idx),
                "case_month": int(case_month),
                "has_afc": str(has_afc),
                "description": (
                    "Derived dynamic fields for LEC-field dependence analysis. "
                    "Computed from raw ERA5 per-cyclone data using the diagnostic "
                    "functions from scripts/ep_structure_analysis/step3_precompute_composites.py."
                ),
                "created_by": "step3b_derive_era5_fields.py",
                "created_at": datetime.now().isoformat(),
            },
        )

        ds_out.to_netcdf(out_path)

        # ── Post-save validation ──────────────────────────────────────────
        valid, valid_msg = _validate_derived_nc(out_path)
        if not valid:
            # Delete the invalid file so it doesn't mislead subsequent runs.
            # Without this, a NaN-filled file left on disk would look valid
            # to step 4 (file exists, variables present) and silently produce
            # all-NaN features downstream.
            try:
                out_path.unlink()
                logging.warning(
                    f"   {track_id}: Deleted invalid derived file "
                    f"({valid_msg}) — will recompute on next run."
                )
            except Exception as del_err:
                logging.warning(
                    f"   {track_id}: Could not delete invalid file "
                    f"({del_err}); it will be retried on next run."
                )
            return {
                "track_id": track_id,
                "status": f"validation_failed: {valid_msg}",
                "output_path": "",
                "has_afc": False,
            }

        return {
            "track_id": track_id,
            "status": "ok",
            "output_path": str(out_path),
            "has_afc": has_afc,
        }

    except Exception as e:
        return {
            "track_id": track_id,
            "status": f"error: {type(e).__name__}: {e}",
            "output_path": "",
            "has_afc": False,
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Derive ERA5 dynamic fields from raw per-cyclone data "
            "(step 3b — required before steps 4 and 5)."
        )
    )
    parser.add_argument(
        "--era5-dir", type=Path, required=True,
        help="Directory containing raw per-cyclone ERA5 NetCDFs (*_era5.nc).",
    )
    parser.add_argument(
        "--derived-dir", type=Path, default=None,
        help=(
            "Output directory for derived files (*_era5_derived.nc). "
            "Default: {era5-dir}/derived/"
        ),
    )
    parser.add_argument("--chunk", type=int, default=None, help="Chunk index (0-based).")
    parser.add_argument("--n-chunks", type=int, default=None, help="Total number of chunks.")
    parser.add_argument(
        "--workers", type=int, default=N_WORKERS_DEFAULT,
        help=f"Parallel workers (default: {N_WORKERS_DEFAULT}).",
    )
    args = parser.parse_args()

    era5_dir = args.era5_dir.resolve()
    derived_dir = (args.derived_dir or era5_dir / "derived").resolve()
    derived_dir.mkdir(parents=True, exist_ok=True)

    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    setup_logging(args.chunk)

    logging.info("=" * 70)
    logging.info("STEP 3b: DERIVE ERA5 DYNAMIC FIELDS — LEC–FIELD DEPENDENCE")
    logging.info("=" * 70)
    logging.info(f"ERA5 raw dir  : {era5_dir}")
    logging.info(f"Derived dir   : {derived_dir}")
    logging.info(f"Fields        : {REQUIRED_DERIVED_VARS + OPTIONAL_DERIVED_VARS}")
    logging.info(f"Source funcs  : scripts/ep_structure_analysis/step3_precompute_composites.py")

    # ── AFC climatology check ─────────────────────────────────────────────
    if not CLIMATOLOGY_FILE.exists():
        logging.warning(
            f"\n⚠  CLIMATOLOGY NOT FOUND: {CLIMATOLOGY_FILE}\n"
            f"   afc_250 will NOT be computed for any cyclone.\n"
            f"   Downstream steps 4/5 will have NaN for all afc_250 features.\n"
            f"   To compute afc_250, download the climatology:\n"
            f"   python scripts/ep_structure_analysis/step2d_download_era5_monthly_means.py "
            f"--groups 250hPa"
        )
    else:
        logging.info(f"Climatology   : {CLIMATOLOGY_FILE} ✓ (afc_250 will be computed)")

    # ── Load manifest ─────────────────────────────────────────────────────
    if not INPUT_MANIFEST.exists():
        logging.error(
            f"Manifest not found: {INPUT_MANIFEST}\n"
            f"Run step 3 (step3_map_era5_fields.py) before step 3b."
        )
        sys.exit(1)

    manifest = pd.read_csv(INPUT_MANIFEST)
    if "era5_available" in manifest.columns:
        n_avail = manifest["era5_available"].sum()
        if n_avail == 0:
            logging.warning(
                f"Manifest has {len(manifest)} cases but ALL are marked era5_available=False "
                f"(step 3 ran in dry-run mode). Proceeding — files will be checked individually."
            )
        else:
            manifest = manifest[manifest["era5_available"]]

    track_ids = manifest["track_id"].astype(str).tolist()
    logging.info(f"\nTotal cases in manifest: {len(track_ids)}")

    # ── Chunking ──────────────────────────────────────────────────────────
    if args.chunk is not None and args.n_chunks is not None:
        chunks = np.array_split(track_ids, args.n_chunks)
        track_ids = list(chunks[args.chunk])
        logging.info(f"Chunk {args.chunk}/{args.n_chunks}: {len(track_ids)} cases")

    # ── Resume: skip already-derived and validated files ──────────────────
    pending = []
    skipped_done = 0
    for tid in track_ids:
        out_path = derived_dir / DERIVED_FILE_PATTERN.format(track_id=tid)
        valid, _msg = _validate_derived_nc(out_path)
        if valid:
            skipped_done += 1
        else:
            pending.append(tid)

    if skipped_done:
        logging.info(f"Already derived and valid: {skipped_done} (skipped)")
    logging.info(f"To process: {len(pending)}")

    if not pending:
        logging.info("Nothing to process — all files are already derived and valid.")
        # Still write the manifest so the monitor can confirm this chunk is done.
        all_done_rows = [
            {
                "track_id": tid,
                "status": "already_done",
                "output_path": str(derived_dir / DERIVED_FILE_PATTERN.format(track_id=tid)),
                "has_afc": "unknown",
            }
            for tid in track_ids
        ]
        pd.DataFrame(all_done_rows).to_csv(
            RESULTS_DIR / f"step3b_derived_field_manifest{chunk_suffix}.csv",
            index=False,
        )
        logging.info(f"  Manifest: {RESULTS_DIR}/step3b_derived_field_manifest{chunk_suffix}.csv")
        logging.info("\n✓ Step 3b complete.")
        return

    # ── Derive fields ─────────────────────────────────────────────────────
    logging.info(f"\nDeriving fields (workers={args.workers})...")
    results = []
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    _derive_fields_for_cyclone, tid, era5_dir, derived_dir
                ): tid
                for tid in pending
            }
            for i, future in enumerate(as_completed(futures), 1):
                r = future.result()
                results.append(r)
                if i % 50 == 0:
                    n_ok_so_far = sum(1 for x in results if x["status"] == "ok")
                    logging.info(
                        f"   Progress: {i}/{len(pending)} — {n_ok_so_far} ok so far"
                    )
    else:
        for i, tid in enumerate(pending, 1):
            r = _derive_fields_for_cyclone(tid, era5_dir, derived_dir)
            results.append(r)
            if i % 50 == 0:
                n_ok_so_far = sum(1 for x in results if x["status"] == "ok")
                logging.info(
                    f"   Progress: {i}/{len(pending)} — {n_ok_so_far} ok so far"
                )

    # ── Summary ───────────────────────────────────────────────────────────
    result_df = pd.DataFrame(results)
    n_ok = (result_df["status"] == "ok").sum()
    n_fail = len(result_df) - n_ok
    n_with_afc = result_df["has_afc"].sum() if "has_afc" in result_df.columns else 0

    logging.info(f"\n{'=' * 60}")
    logging.info("STEP 3b SUMMARY")
    logging.info(f"  Already done (skipped) : {skipped_done}")
    logging.info(f"  Newly derived OK       : {n_ok}")
    logging.info(f"  With AFC               : {n_with_afc}")
    logging.info(f"  Failed                 : {n_fail}")

    if n_fail > 0:
        logging.info("\n  Failure breakdown:")
        for status, count in result_df["status"].value_counts().items():
            if status != "ok":
                logging.warning(f"     {status}: {count}")

    # CRITICAL: if every cyclone failed, something is fundamentally wrong
    if n_ok == 0 and skipped_done == 0:
        logging.error(
            "\nCRITICAL: 0 cyclones produced valid derived files.\n"
            "Likely causes:\n"
            "  1. --era5-dir does not contain *_era5.nc files\n"
            "  2. Raw files are missing required variables (u, v, t, z)\n"
            "  3. Pressure levels are missing "
            "(need 175/200/225/825/850/875/250 hPa in raw files)\n"
            f"  Check: ls {era5_dir}/*.nc | head -5"
        )
        sys.exit(1)

    # ── Save manifest ─────────────────────────────────────────────────────
    # Include already-done cases in the manifest
    already_done_rows = [
        {
            "track_id": tid,
            "status": "already_done",
            "output_path": str(derived_dir / DERIVED_FILE_PATTERN.format(track_id=tid)),
            "has_afc": "unknown",
        }
        for tid in track_ids
        if tid not in result_df["track_id"].values
    ]

    final_df = pd.concat(
        [pd.DataFrame(already_done_rows), result_df], ignore_index=True
    )
    final_df.to_csv(
        RESULTS_DIR / f"step3b_derived_field_manifest{chunk_suffix}.csv",
        index=False,
    )
    logging.info(f"\n  Manifest: {RESULTS_DIR}/step3b_derived_field_manifest{chunk_suffix}.csv")
    logging.info(f"  Derived dir: {derived_dir}")
    logging.info("\n✓ Step 3b complete.")
    logging.info(
        "  → Next: run step 4 with "
        f"--era5-dir {era5_dir} --derived-dir {derived_dir}"
    )


if __name__ == "__main__":
    main()
