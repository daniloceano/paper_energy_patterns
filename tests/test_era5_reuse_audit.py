from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from scripts.ep_structure_analysis.audit_era5_reuse import (
    PRESSURE_LEVELS,
    audit_case,
)
from scripts.ep_structure_analysis.step2_download_era5_parallel import (
    drop_cds_auxiliary_coordinates,
    load_cds_credentials,
    validate_netcdf_file,
)


TRACK_ID = "20000001"
TIMES = pd.to_datetime(["2000-01-01 00:00", "2000-01-01 03:00"])


def _write_case(data_dir: Path, *, drop_variable: str | None = None, times=TIMES) -> None:
    levels = sorted(PRESSURE_LEVELS)
    latitudes = np.arange(5.0, -25.25, -0.25)
    longitudes = np.arange(-65.0, -34.75, 0.25)
    shape = (len(times), len(levels), len(latitudes), len(longitudes))

    data_vars = {
        name: (("time", "level", "latitude", "longitude"), np.zeros(shape, dtype="float32"))
        for name in ("u", "v", "t", "z", "q")
        if name != drop_variable
    }
    if drop_variable != "msl":
        data_vars["msl"] = (
            ("time", "latitude", "longitude"),
            np.zeros((len(times), len(latitudes), len(longitudes)), dtype="float32"),
        )

    dataset = xr.Dataset(
        data_vars,
        coords={
            "time": times,
            "level": levels,
            "latitude": latitudes,
            "longitude": longitudes,
        },
    )
    dataset.to_netcdf(data_dir / f"{TRACK_ID}_era5.nc")
    pd.DataFrame([{"track_id": TRACK_ID}]).to_csv(
        data_dir / f"{TRACK_ID}_metadata.csv", index=False
    )


def _row() -> pd.Series:
    return pd.Series(
        {
            "track_id": TRACK_ID,
            "ep": 1,
            "selected_times": ",".join(item.strftime("%Y-%m-%d %H:%M:%S") for item in TIMES),
        }
    )


def _positions(longitude: float = -50.0):
    return {(TRACK_ID, time): (-10.0, longitude) for time in TIMES}


def test_complete_case_is_reusable(tmp_path):
    _write_case(tmp_path)

    result = audit_case(_row(), tmp_path, _positions())

    assert result["status"] == "reusable"


def test_missing_required_time_is_rejected(tmp_path):
    _write_case(tmp_path, times=TIMES[:1])

    result = audit_case(_row(), tmp_path, _positions())

    assert "missing_times" in result["status"]
    assert TIMES[1].isoformat() in result["missing_times"]


def test_missing_variable_is_rejected(tmp_path):
    _write_case(tmp_path, drop_variable="q")

    result = audit_case(_row(), tmp_path, _positions())

    assert "missing_variables" in result["status"]
    assert result["missing_variables"] == "q"


def test_insufficient_spatial_coverage_is_rejected(tmp_path):
    _write_case(tmp_path)

    result = audit_case(_row(), tmp_path, _positions(longitude=-30.0))

    assert "insufficient_spatial_coverage" in result["status"]


def test_downloader_rejects_duplicate_nearest_time(tmp_path):
    _write_case(tmp_path, times=pd.to_datetime(["2000-01-01 00:00", "2000-01-01 00:00"]))

    valid, issues, _, _ = validate_netcdf_file(
        tmp_path / f"{TRACK_ID}_era5.nc",
        ["u", "v", "t", "z", "q"],
        ["msl"],
        sorted(PRESSURE_LEVELS),
        expected_times=TIMES,
    )

    assert not valid
    assert any("Missing required times" in issue for issue in issues)


def test_key_inventory_uses_only_healthy_synthetic_ids(tmp_path):
    import sqlite3

    keys = tmp_path / "cds-keys"
    tokens = ["a" * 40, "b" * 40, "c" * 40]
    keys.write_text("\n".join(f"{token} - account" for token in tokens) + "\n")
    health = tmp_path / "state.sqlite3"
    with sqlite3.connect(health) as connection:
        connection.execute("CREATE TABLE key_health (key_id TEXT, last_status TEXT)")
        connection.executemany(
            "INSERT INTO key_health VALUES (?, ?)",
            [("key-001", "healthy"), ("key-002", "licence_required"), ("key-003", "healthy")],
        )

    credentials = load_cds_credentials(keys, health)

    assert [key_id for key_id, _ in credentials] == ["key-001", "key-003"]
    assert [token for _, token in credentials] == [tokens[0], tokens[2]]


def test_cds_bookkeeping_fields_are_removed_before_merge():
    pressure = xr.Dataset(
        {"u": ("time", [1.0]), "expver": ("time", [1])},
        coords={"time": TIMES[:1], "number": 0},
    )
    surface = xr.Dataset(
        {"msl": ("time", [101325.0]), "number": ("time", [0])},
        coords={"time": TIMES[:1], "expver": "0001"},
    )

    merged = xr.merge(
        [
            drop_cds_auxiliary_coordinates(pressure),
            drop_cds_auxiliary_coordinates(surface),
        ],
        compat="override",
        join="exact",
    )

    assert set(merged.data_vars) == {"u", "msl"}
    assert "expver" not in merged.variables
    assert "number" not in merged.variables
