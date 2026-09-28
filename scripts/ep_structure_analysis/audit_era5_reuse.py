#!/usr/bin/env python3
"""Audit whether existing canonical ERA5 files are safe to reuse.

Why this script is necessary
----------------------------
``step2c_monitor.py`` checks file readability, variables and pressure levels,
while ``step2b_reuse_legacy_era5.py`` checks temporal and spatial coverage only
when importing a legacy file.  Neither one verifies an *already canonical*
archive against a newly generated set of case CSVs.  That distinction matters
after a corrected clustering: a file can exist and contain every variable but
still represent the wrong central timesteps or an insufficient storm-centred
domain.

This auditor is deliberately read-only.  It never downloads, patches, moves or
rewrites ERA5 data.  For every case it verifies:

* NetCDF and companion metadata existence;
* required variables and pressure levels;
* exact availability of the selected central timesteps;
* a track position for every selected timestep; and
* 30 degree by 30 degree spatial coverage around every selected position.

The detailed CSV and JSON summary provide a reproducible gate before step 3.
Exit status is zero only when every requested case is safe to reuse.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import xarray as xr

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.utils import corrected_lec as clec


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
DEFAULT_CASES_DIR = PROJECT_ROOT / "results" / "ep_structure"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "results" / "ep_structure"

PRESSURE_VARIABLES = {"u", "v", "t", "z", "q"}
SINGLE_LEVEL_VARIABLES = {"msl"}
PRESSURE_LEVELS = {175, 200, 225, 250, 500, 825, 850, 875, 975}
HALF_DOMAIN_DEGREES = 15.0
DOMAIN_TOLERANCE_DEGREES = 0.5
TIME_TOLERANCE = pd.Timedelta(minutes=1)


def parse_selected_times(value: str) -> list[pd.Timestamp]:
    """Parse the comma-separated ``selected_times`` case-list field."""
    if pd.isna(value) or not str(value).strip():
        return []
    return [pd.Timestamp(item.strip()) for item in str(value).split(",")]


def _coord_name(ds: xr.Dataset, candidates: Iterable[str]) -> str | None:
    return next((name for name in candidates if name in ds.coords), None)


def _normalise_longitudes(values: np.ndarray) -> np.ndarray:
    """Return longitude values in the -180..180 convention."""
    values = np.asarray(values, dtype=float)
    return (values + 180.0) % 360.0 - 180.0


def _covers_position(
    latitude: float,
    longitude: float,
    dataset_latitudes: np.ndarray,
    dataset_longitudes: np.ndarray,
) -> bool:
    """Whether the dataset covers a 30° box centred on one track position."""
    lats = np.asarray(dataset_latitudes, dtype=float)
    lons = _normalise_longitudes(dataset_longitudes)
    lon = float(_normalise_longitudes(np.asarray([longitude]))[0])

    return (
        float(lats.max()) >= latitude + HALF_DOMAIN_DEGREES - DOMAIN_TOLERANCE_DEGREES
        and float(lats.min()) <= latitude - HALF_DOMAIN_DEGREES + DOMAIN_TOLERANCE_DEGREES
        and float(lons.max()) >= lon + HALF_DOMAIN_DEGREES - DOMAIN_TOLERANCE_DEGREES
        and float(lons.min()) <= lon - HALF_DOMAIN_DEGREES + DOMAIN_TOLERANCE_DEGREES
    )


def load_cases(cases_dir: Path) -> pd.DataFrame:
    """Load EP1--EP3 case lists and reject duplicate or malformed membership."""
    frames = []
    for ep in (1, 2, 3):
        path = cases_dir / f"ep{ep}_cases.csv"
        if not path.is_file():
            raise FileNotFoundError(f"case list not found: {path}")
        frame = pd.read_csv(path, dtype={"track_id": str})
        required = {"track_id", "selected_times"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{path} lacks columns: {sorted(missing)}")
        frame = frame.copy()
        frame["ep"] = ep
        frames.append(frame)

    cases = pd.concat(frames, ignore_index=True)
    duplicates = cases.loc[cases["track_id"].duplicated(), "track_id"].unique()
    if len(duplicates):
        raise ValueError(
            "case lists contain duplicate track IDs across EPs: "
            + ", ".join(duplicates[:10])
        )
    return cases


def build_track_lookup(tracks: pd.DataFrame) -> dict[tuple[str, pd.Timestamp], tuple[float, float]]:
    """Index corrected track positions by exact track ID and timestamp."""
    columns = ["track_id", "date", "lat vor", "lon vor"]
    missing = set(columns) - set(tracks.columns)
    if missing:
        raise ValueError(f"corrected tracks lack columns: {sorted(missing)}")

    lookup: dict[tuple[str, pd.Timestamp], tuple[float, float]] = {}
    for row in tracks[columns].itertuples(index=False, name=None):
        track_id, date, latitude, longitude = row
        lookup[(str(track_id), pd.Timestamp(date))] = (float(latitude), float(longitude))
    return lookup


def audit_case(
    row: pd.Series,
    data_dir: Path,
    track_lookup: dict[tuple[str, pd.Timestamp], tuple[float, float]],
) -> dict:
    """Audit one case without loading the gridded fields into memory."""
    track_id = str(row["track_id"])
    ep = int(row["ep"])
    required_times = parse_selected_times(row["selected_times"])
    nc_path = data_dir / f"{track_id}_era5.nc"
    metadata_path = data_dir / f"{track_id}_metadata.csv"

    record = {
        "track_id": track_id,
        "ep": ep,
        "status": "reusable",
        "netcdf_exists": nc_path.is_file(),
        "metadata_exists": metadata_path.is_file(),
        "missing_variables": "",
        "missing_levels": "",
        "missing_times": "",
        "missing_track_positions": "",
        "out_of_bounds_times": "",
        "error": "",
    }

    problems: list[str] = []
    if not nc_path.is_file():
        problems.append("missing_netcdf")
    if not metadata_path.is_file():
        problems.append("missing_metadata")
    if problems:
        record["status"] = "+".join(problems)
        return record

    try:
        with xr.open_dataset(nc_path) as ds:
            expected_variables = PRESSURE_VARIABLES | SINGLE_LEVEL_VARIABLES
            missing_variables = sorted(expected_variables - set(ds.data_vars))
            if missing_variables:
                problems.append("missing_variables")
                record["missing_variables"] = ",".join(missing_variables)

            level_coord = _coord_name(ds, ("pressure_level", "level"))
            if level_coord is None:
                missing_levels = sorted(PRESSURE_LEVELS)
            else:
                actual_levels = {int(round(float(value))) for value in ds[level_coord].values}
                missing_levels = sorted(PRESSURE_LEVELS - actual_levels)
            if missing_levels:
                problems.append("missing_levels")
                record["missing_levels"] = ",".join(map(str, missing_levels))

            time_coord = _coord_name(ds, ("valid_time", "time"))
            if time_coord is None:
                available_times = pd.DatetimeIndex([])
            else:
                available_times = pd.DatetimeIndex(pd.to_datetime(ds[time_coord].values))

            missing_times = []
            for required_time in required_times:
                if len(available_times) == 0:
                    missing_times.append(required_time)
                    continue
                offsets = np.abs(available_times - required_time)
                if offsets.min() > TIME_TOLERANCE:
                    missing_times.append(required_time)
            if missing_times:
                problems.append("missing_times")
                record["missing_times"] = ",".join(item.isoformat() for item in missing_times)

            lat_coord = _coord_name(ds, ("latitude", "lat"))
            lon_coord = _coord_name(ds, ("longitude", "lon"))
            missing_positions = []
            out_of_bounds = []
            if lat_coord is None or lon_coord is None:
                problems.append("missing_spatial_coordinates")
            else:
                for required_time in required_times:
                    position = track_lookup.get((track_id, required_time))
                    if position is None:
                        missing_positions.append(required_time)
                        continue
                    latitude, longitude = position
                    if not _covers_position(
                        latitude,
                        longitude,
                        ds[lat_coord].values,
                        ds[lon_coord].values,
                    ):
                        out_of_bounds.append(required_time)

            if missing_positions:
                problems.append("missing_track_positions")
                record["missing_track_positions"] = ",".join(
                    item.isoformat() for item in missing_positions
                )
            if out_of_bounds:
                problems.append("insufficient_spatial_coverage")
                record["out_of_bounds_times"] = ",".join(
                    item.isoformat() for item in out_of_bounds
                )

    except Exception as exc:  # preserve a per-case diagnostic instead of aborting the audit
        problems.append("read_error")
        record["error"] = f"{type(exc).__name__}: {exc}"

    if problems:
        record["status"] = "+".join(dict.fromkeys(problems))
    return record


def build_summary(records: pd.DataFrame, data_dir: Path, cases_dir: Path) -> dict:
    status_counts = {str(key): int(value) for key, value in records["status"].value_counts().items()}
    ep_counts = {
        f"EP{int(ep)}": {
            "cases": int(len(group)),
            "reusable": int((group["status"] == "reusable").sum()),
        }
        for ep, group in records.groupby("ep")
    }
    return {
        "data_dir": str(data_dir.resolve()),
        "cases_dir": str(cases_dir.resolve()),
        "total_cases": int(len(records)),
        "reusable_cases": int((records["status"] == "reusable").sum()),
        "all_reusable": bool((records["status"] == "reusable").all()),
        "status_counts": status_counts,
        "by_ep": ep_counts,
        "requirements": {
            "pressure_variables": sorted(PRESSURE_VARIABLES),
            "single_level_variables": sorted(SINGLE_LEVEL_VARIABLES),
            "pressure_levels_hpa": sorted(PRESSURE_LEVELS),
            "half_domain_degrees": HALF_DOMAIN_DEGREES,
            "domain_tolerance_degrees": DOMAIN_TOLERANCE_DEGREES,
            "time_tolerance_minutes": TIME_TOLERANCE.total_seconds() / 60,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument(
        "--corrected-data-dir",
        type=Path,
        default=None,
        help="Directory containing tracks_with_energetics_corrected.csv",
    )
    args = parser.parse_args()

    if args.corrected_data_dir is not None:
        import os

        os.environ["PAPER_CORRECTED_DATA"] = str(args.corrected_data_dir)

    cases = load_cases(args.cases_dir)
    tracks = clec.read_corrected_tracks()
    track_lookup = build_track_lookup(tracks)

    records = pd.DataFrame(
        [audit_case(row, args.data_dir, track_lookup) for _, row in cases.iterrows()]
    )
    summary = build_summary(records, args.data_dir, args.cases_dir)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.report_dir / "era5_reuse_audit.csv"
    json_path = args.report_dir / "era5_reuse_audit_summary.json"
    records.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Detailed audit: {csv_path}")
    print(f"Summary: {json_path}")
    return 0 if summary["all_reusable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
