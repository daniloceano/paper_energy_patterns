"""Derive per-cyclone ERA5 diagnostics for LEC--field dependence.

For each cyclone, the five diagnostics are computed at the exact 2--3 central
intensification timestamps selected by the EP-structure pipeline and averaged
on the storm-relative grid. Raw ERA5 files are never modified. AFC is required
and uses the canonical 250-hPa monthly climatology.

Remote example::

    python -m scripts.lec_field_dependence_analysis.step3b_derive_era5_fields \
        --era5-dir /path/to/era5_ep_structure \
        --derived-dir /path/to/derived_corrected_2to3 \
        --tracks-file /path/to/tracks_with_energetics_corrected.csv \
        --workers 16
"""

import argparse
import hashlib
import logging
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from metpy.units import units

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ep_structure_analysis import step3_precompute_composites as composite_step
from scripts.ep_structure_analysis.timestep_selection import selected_timestep_indices
from scripts.lec_field_dependence_analysis.utils_io import LOG_DIR, RESULTS_DIR


INPUT_MANIFEST = RESULTS_DIR / "step3_era5_field_manifest.csv"
ERA5_FILE_PATTERN = "{track_id}_era5.nc"
DERIVED_FILE_PATTERN = "{track_id}_era5_derived.nc"
REQUIRED_RAW_VARS = ["u", "v", "t", "z"]
REQUIRED_DERIVED_VARS = [
    "pv_850", "pv_200", "adv_T_850", "ke_adv_250", "afc_250",
]
REQUIRED_LEVELS = [175, 200, 225, 250, 825, 850, 875]
TEMPORAL_METHOD = "central_2_or_3_mean"
N_WORKERS_DEFAULT = 4


def setup_logging(chunk_id=None):
    """Log to the repository and stderr."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_chunk{chunk_id}" if chunk_id is not None else ""
    log_file = LOG_DIR / f"lec_field_step3b{suffix}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    logging.info("Log file: %s", log_file)


def _to_array(value):
    """Return a plain ndarray from xarray/MetPy/pint output."""
    if hasattr(value, "metpy") and hasattr(value.metpy, "unit_array"):
        try:
            return np.asarray(value.metpy.unit_array.magnitude)
        except Exception:
            pass
    if hasattr(value, "values"):
        raw = value.values
        return np.asarray(raw.magnitude if hasattr(raw, "magnitude") else raw)
    if hasattr(value, "magnitude"):
        return np.asarray(value.magnitude)
    return np.asarray(value)


def _validate_derived_nc(
    path, expected_selected_times=None, expected_climatology_sha256=None
):
    """Reject incomplete files and all legacy one-timestep products."""
    if not path.exists():
        return False, "file_missing"
    try:
        ds = xr.open_dataset(path)
    except Exception as exc:
        return False, f"open_error: {exc}"
    try:
        missing = [name for name in REQUIRED_DERIVED_VARS if name not in ds]
        if missing:
            return False, f"missing_required_vars: {missing}"
        if ds.attrs.get("temporal_method") != TEMPORAL_METHOD:
            return False, "obsolete_or_missing_temporal_method"
        stored_hash = str(ds.attrs.get("afc_climatology_sha256", ""))
        if len(stored_hash) != 64:
            return False, "missing_afc_climatology_provenance"
        if (
            expected_climatology_sha256 is not None
            and stored_hash != expected_climatology_sha256
        ):
            return False, "afc_climatology_hash_mismatch"
        try:
            n_used = int(ds.attrs.get("n_timesteps_used", 0))
        except (TypeError, ValueError):
            return False, "invalid_n_timesteps_used"
        if n_used not in (2, 3):
            return False, f"invalid_n_timesteps_used: {n_used}"
        selected = [
            item.strip()
            for item in str(ds.attrs.get("selected_times", "")).split(",")
            if item.strip()
        ]
        if len(selected) != n_used:
            return False, f"selected_times_count_mismatch: {len(selected)} != {n_used}"
        if expected_selected_times is not None:
            expected = [
                item.strip() for item in str(expected_selected_times).split(",")
                if item.strip()
            ]
            if [pd.Timestamp(item) for item in selected] != [
                pd.Timestamp(item) for item in expected
            ]:
                return False, "selected_times_do_not_match_manifest"
        shapes = {tuple(ds[name].shape) for name in REQUIRED_DERIVED_VARS}
        if len(shapes) != 1 or len(next(iter(shapes))) != 2:
            return False, f"inconsistent_or_non_2d_shapes: {sorted(shapes)}"
        all_nan = [
            name for name in REQUIRED_DERIVED_VARS
            if np.all(np.isnan(ds[name].values))
        ]
        if all_nan:
            return False, f"all_nan: {all_nan}"
        return True, "ok"
    finally:
        ds.close()


def _worker_init(
    era5_dir, cases_dir, tracks_file, output_dir, afc_climatology
):
    """Configure canonical shared inputs inside every worker process."""
    composite_step.configure_runtime_paths(
        era5_dir, cases_dir, tracks_file, output_dir
    )
    composite_step.CLIMATOLOGY_FILE = Path(afc_climatology).resolve()


def _sha256(path):
    """Compute a stable provenance digest without loading the file in memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _failure(track_id, status):
    return {
        "track_id": str(track_id),
        "status": status,
        "output_path": "",
        "n_timesteps_used": 0,
    }


def _compute_fields(ds_centered, levels, pressure_coord, case_month, climatology):
    """Compute the five canonical diagnostics for one storm-centred time."""
    def level_index(target):
        return int(np.argmin(np.abs(levels - target)))

    def select(field, target):
        return field.isel({pressure_coord: level_index(target)})

    u = ds_centered["u"]
    v = ds_centered["v"]
    temperature = ds_centered["t"]
    geopotential = ds_centered["z"]
    u250 = select(u, 250) * units("m/s")
    v250 = select(v, 250) * units("m/s")
    z250 = select(geopotential, 250) * units("m**2/s**2")
    u850 = select(u, 850) * units("m/s")
    v850 = select(v, 850) * units("m/s")
    t850 = select(temperature, 850) * units.kelvin

    fields = {
        "pv_850": composite_step.compute_pv_at_level(
            select(u, 825) * units("m/s"), u850,
            select(u, 875) * units("m/s"),
            select(v, 825) * units("m/s"), v850,
            select(v, 875) * units("m/s"),
            select(temperature, 825) * units.kelvin, t850,
            select(temperature, 875) * units.kelvin,
            np.array([
                levels[level_index(825)], levels[level_index(850)],
                levels[level_index(875)],
            ]) * 100.0,
        ),
        "pv_200": composite_step.compute_pv_at_level(
            select(u, 175) * units("m/s"),
            select(u, 200) * units("m/s"),
            select(u, 225) * units("m/s"),
            select(v, 175) * units("m/s"),
            select(v, 200) * units("m/s"),
            select(v, 225) * units("m/s"),
            select(temperature, 175) * units.kelvin,
            select(temperature, 200) * units.kelvin,
            select(temperature, 225) * units.kelvin,
            np.array([
                levels[level_index(175)], levels[level_index(200)],
                levels[level_index(225)],
            ]) * 100.0,
        ),
        "adv_T_850": composite_step.temperature_advection_850(u850, v850, t850),
        "ke_adv_250": composite_step.kinetic_energy_advection_250(u250, v250),
    }
    clim_subdomain = climatology.sel(month=case_month).interp(
        latitude=u250.latitude.values,
        longitude=u250.longitude.values,
        method="linear",
    )
    fields["afc_250"] = composite_step.ageostrophic_flux_convergence_250(
        u250,
        v250,
        z250,
        clim_subdomain["u_clim"],
        clim_subdomain["v_clim"],
        clim_subdomain["z_clim"],
    )
    return {name: _to_array(value).squeeze() for name, value in fields.items()}


def _derive_fields_for_cyclone(
    track_id, selected_times, era5_dir, derived_dir, climatology_sha256
):
    """Compute and atomically save the 2--3-time mean for one cyclone."""
    track_id = str(track_id)
    input_path = era5_dir / ERA5_FILE_PATTERN.format(track_id=track_id)
    output_path = derived_dir / DERIVED_FILE_PATTERN.format(track_id=track_id)
    metadata_path = era5_dir / f"{track_id}_metadata.csv"
    if not input_path.exists():
        return _failure(track_id, "file_not_found")
    if not metadata_path.exists():
        return _failure(track_id, "metadata_file_not_found")
    try:
        ds = xr.open_dataset(input_path)
    except Exception as exc:
        return _failure(track_id, f"open_error: {exc}")

    try:
        missing_raw = [name for name in REQUIRED_RAW_VARS if name not in ds]
        if missing_raw:
            return _failure(track_id, f"missing_raw_vars: {missing_raw}")
        pressure_coord = "pressure_level" if "pressure_level" in ds.coords else "level"
        levels = ds[pressure_coord].values
        for required_level in REQUIRED_LEVELS:
            nearest = levels[np.argmin(np.abs(levels - required_level))]
            if abs(float(nearest) - required_level) > 10.0:
                return _failure(
                    track_id,
                    f"missing_pressure_level: {required_level} (nearest={nearest})",
                )

        time_coord = "valid_time" if "valid_time" in ds.dims else "time"
        era5_times = ds[time_coord].values
        requested_times = [
            value.strip() for value in str(selected_times).split(",") if value.strip()
        ]
        if len(requested_times) not in (2, 3):
            return _failure(
                track_id, f"invalid_selected_times_count: {len(requested_times)}"
            )
        try:
            selected_indices = selected_timestep_indices(era5_times, requested_times)
        except ValueError as exc:
            return _failure(track_id, f"selected_time_mapping_error: {exc}")

        metadata = pd.read_csv(metadata_path).iloc[0]
        case_month = composite_step._get_case_start_time(metadata).month
        positions = composite_step.get_cyclone_positions_for_case(
            int(track_id), era5_times
        )
        climatology = composite_step._load_clim(
            composite_step.CLIMATOLOGY_FILE,
            "250 hPa (AFC)",
            "AFC is required for LEC--field dependence.",
        )
        if climatology is None:
            return _failure(track_id, "required_afc_climatology_missing")

        values_by_field = {name: [] for name in REQUIRED_DERIVED_VARS}
        centers = []
        expected_shape = None
        for time_index in selected_indices:
            position = positions.get(time_index)
            if position is None:
                return _failure(
                    track_id, f"no_position_for_selected_timestep: {time_index}"
                )
            center_lat, center_lon = position
            available, message = composite_step.check_subdomain_available(
                ds, center_lat, center_lon, composite_step.DOMAIN_SIZE
            )
            if not available:
                return _failure(
                    track_id, f"subdomain_unavailable_at_{time_index}: {message}"
                )
            centered = composite_step.extract_subdomain(
                ds.isel({time_coord: time_index}),
                center_lat,
                center_lon,
                composite_step.DOMAIN_SIZE,
            )
            diagnostics = _compute_fields(
                centered, levels, pressure_coord, case_month, climatology
            )
            for field_name, array in diagnostics.items():
                if array.ndim != 2:
                    raise ValueError(
                        f"{field_name} at time index {time_index} is not 2-D: {array.shape}"
                    )
                if expected_shape is None:
                    expected_shape = array.shape
                elif array.shape != expected_shape:
                    raise ValueError(
                        f"inconsistent field shapes: {array.shape} != {expected_shape}"
                    )
                values_by_field[field_name].append(array)
            centers.append((center_lat, center_lon))

        # A few outer grid cells can be NaN at every selected time after
        # spherical derivatives.  They are expected and retained as NaN.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Mean of empty slice")
            mean_fields = {
                name: np.nanmean(np.stack(values, axis=0), axis=0)
                for name, values in values_by_field.items()
            }
        ny, nx = expected_shape
        coords = {
            "y": ("y", np.arange(ny, dtype=np.int16), {
                "long_name": "storm-relative south-to-north grid index"
            }),
            "x": ("x", np.arange(nx, dtype=np.int16), {
                "long_name": "storm-relative west-to-east grid index"
            }),
        }
        attributes = {
            "pv_850": {"long_name": "Potential Vorticity at 850 hPa", "units": "K m2 kg-1 s-1"},
            "pv_200": {"long_name": "Potential Vorticity at 200 hPa", "units": "K m2 kg-1 s-1"},
            "adv_T_850": {"long_name": "Temperature Advection at 850 hPa (-V.gradT)", "units": "K s-1"},
            "ke_adv_250": {"long_name": "Kinetic Energy Advection at 250 hPa (-V.grad(KE))", "units": "W kg-1"},
            "afc_250": {"long_name": "Ageostrophic Flux Convergence at 250 hPa", "units": "W kg-1"},
        }
        output = xr.Dataset(
            {
                name: xr.DataArray(
                    mean_fields[name], coords=coords, dims=("y", "x"),
                    attrs=attributes[name],
                )
                for name in REQUIRED_DERIVED_VARS
            },
            attrs={
                "track_id": track_id,
                "temporal_method": TEMPORAL_METHOD,
                "n_timesteps_used": len(selected_indices),
                "selected_times": ",".join(requested_times),
                "selected_timestep_indices": ",".join(map(str, selected_indices)),
                "center_lats": ",".join(f"{lat:.6f}" for lat, _ in centers),
                "center_lons": ",".join(f"{lon:.6f}" for _, lon in centers),
                "case_month": int(case_month),
                "afc_climatology_path": str(composite_step.CLIMATOLOGY_FILE),
                "afc_climatology_sha256": climatology_sha256,
                "domain_size_degrees": float(composite_step.DOMAIN_SIZE),
                "description": (
                    "Storm-relative diagnostic mean over the exact 2-3 central "
                    "intensification times selected by step 1."
                ),
                "created_by": "step3b_derive_era5_fields.py",
                "created_at": datetime.now().isoformat(),
            },
        )
        composite_step.write_netcdf_atomic(output, output_path)
    except Exception as exc:
        return _failure(track_id, f"error: {type(exc).__name__}: {exc}")
    finally:
        ds.close()

    valid, validation_message = _validate_derived_nc(
        output_path, selected_times, climatology_sha256
    )
    if not valid:
        output_path.unlink(missing_ok=True)
        return _failure(track_id, f"validation_failed: {validation_message}")
    return {
        "track_id": track_id,
        "status": "ok",
        "output_path": str(output_path),
        "n_timesteps_used": len(selected_indices),
    }


def _manifest_rows(manifest):
    """Yield stable strings for IDs and authoritative selected times."""
    for row in manifest.itertuples(index=False):
        yield str(row.track_id), str(row.selected_times)


def main():
    parser = argparse.ArgumentParser(
        description="Derive exact 2--3-time ERA5 means for LEC--field dependence."
    )
    parser.add_argument("--era5-dir", type=Path, required=True)
    parser.add_argument("--derived-dir", type=Path, default=None)
    parser.add_argument(
        "--tracks-file", type=Path, required=True,
        help="Corrected hourly cyclone track table used for storm positions.",
    )
    parser.add_argument(
        "--afc-climatology", type=Path, required=True,
        help="Expanded 250-hPa monthly climatology used to compute AFC.",
    )
    parser.add_argument("--chunk", type=int, default=None)
    parser.add_argument("--n-chunks", type=int, default=None)
    parser.add_argument("--workers", type=int, default=N_WORKERS_DEFAULT)
    args = parser.parse_args()

    if (args.chunk is None) != (args.n_chunks is None):
        parser.error("--chunk and --n-chunks must be provided together")
    if args.n_chunks is not None and not 0 <= args.chunk < args.n_chunks:
        parser.error("--chunk must satisfy 0 <= chunk < n-chunks")
    if args.workers < 1:
        parser.error("--workers must be >= 1")

    era5_dir = args.era5_dir.resolve()
    tracks_file = args.tracks_file.resolve()
    afc_climatology = args.afc_climatology.resolve()
    derived_dir = (args.derived_dir or era5_dir / "derived").resolve()
    derived_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(args.chunk)
    composite_step.configure_runtime_paths(
        era5_dir, RESULTS_DIR, tracks_file, derived_dir
    )
    composite_step.CLIMATOLOGY_FILE = afc_climatology

    logging.info("=" * 70)
    logging.info("STEP 3b: DERIVE ERA5 DYNAMIC FIELDS -- LEC--FIELD DEPENDENCE")
    logging.info("=" * 70)
    logging.info("ERA5 raw dir : %s", era5_dir)
    logging.info("Derived dir  : %s", derived_dir)
    logging.info("Tracks file  : %s", tracks_file)
    logging.info("AFC climate  : %s", afc_climatology)
    logging.info("Temporal rule: %s", TEMPORAL_METHOD)
    logging.info("Required fields: %s", REQUIRED_DERIVED_VARS)

    if not era5_dir.is_dir():
        logging.error("ERA5 directory not found: %s", era5_dir)
        sys.exit(1)
    if not tracks_file.is_file():
        logging.error("Corrected tracks file not found: %s", tracks_file)
        sys.exit(1)
    if not afc_climatology.is_file():
        logging.error(
            "Required AFC climatology not found: %s", afc_climatology
        )
        sys.exit(1)
    if not INPUT_MANIFEST.is_file():
        logging.error("Step 3 manifest not found: %s", INPUT_MANIFEST)
        sys.exit(1)

    climatology_sha256 = _sha256(afc_climatology)
    logging.info("AFC SHA256   : %s", climatology_sha256)

    manifest = pd.read_csv(INPUT_MANIFEST, dtype={"track_id": str})
    required_columns = {"track_id", "selected_times"}
    missing_columns = required_columns - set(manifest.columns)
    if missing_columns:
        logging.error("Manifest missing required columns: %s", sorted(missing_columns))
        sys.exit(1)
    if "era5_available" in manifest:
        available = manifest["era5_available"].astype(str).str.lower().isin({"true", "1"})
        if available.any():
            manifest = manifest[available].copy()
    if args.n_chunks is not None:
        manifest = np.array_split(manifest, args.n_chunks)[args.chunk]
        logging.info("Chunk %s/%s: %s cases", args.chunk, args.n_chunks, len(manifest))

    cases = list(_manifest_rows(manifest))
    pending = []
    completed = []
    for track_id, selected_times in cases:
        path = derived_dir / DERIVED_FILE_PATTERN.format(track_id=track_id)
        valid, _ = _validate_derived_nc(
            path, selected_times, climatology_sha256
        )
        (completed if valid else pending).append((track_id, selected_times))
    logging.info("Valid existing outputs: %s", len(completed))
    logging.info("Cases to process: %s", len(pending))

    results = []
    if args.workers > 1 and pending:
        with ProcessPoolExecutor(
            max_workers=args.workers,
            initializer=_worker_init,
            initargs=(
                era5_dir, RESULTS_DIR, tracks_file, derived_dir, afc_climatology,
            ),
        ) as executor:
            futures = {
                executor.submit(
                    _derive_fields_for_cyclone, track_id, selected_times,
                    era5_dir, derived_dir, climatology_sha256,
                ): track_id
                for track_id, selected_times in pending
            }
            for index, future in enumerate(as_completed(futures), 1):
                results.append(future.result())
                if index % 50 == 0:
                    ok_count = sum(row["status"] == "ok" for row in results)
                    logging.info("Progress %s/%s (%s ok)", index, len(pending), ok_count)
    else:
        for index, (track_id, selected_times) in enumerate(pending, 1):
            results.append(
                _derive_fields_for_cyclone(
                    track_id, selected_times, era5_dir, derived_dir,
                    climatology_sha256,
                )
            )
            if index % 50 == 0:
                ok_count = sum(row["status"] == "ok" for row in results)
                logging.info("Progress %s/%s (%s ok)", index, len(pending), ok_count)

    already_done = [
        {
            "track_id": track_id,
            "status": "already_done",
            "output_path": str(derived_dir / DERIVED_FILE_PATTERN.format(track_id=track_id)),
            "n_timesteps_used": len([
                part for part in selected_times.split(",") if part.strip()
            ]),
        }
        for track_id, selected_times in completed
    ]
    final = pd.DataFrame(already_done + results)
    chunk_suffix = f"_chunk{args.chunk}" if args.chunk is not None else ""
    output_manifest = RESULTS_DIR / f"step3b_derived_field_manifest{chunk_suffix}.csv"
    final.to_csv(output_manifest, index=False)

    new_ok = sum(row["status"] == "ok" for row in results)
    failures = [row for row in results if row["status"] != "ok"]
    logging.info("Already valid: %s", len(completed))
    logging.info("Newly derived: %s", new_ok)
    logging.info("Failed: %s", len(failures))
    logging.info("Manifest: %s", output_manifest)
    if failures:
        for status, count in pd.Series(
            [row["status"] for row in failures]
        ).value_counts().items():
            logging.error("%s: %s", status, count)
        sys.exit(1)
    logging.info("Step 3b complete: all %s cases valid.", len(cases))


if __name__ == "__main__":
    main()
