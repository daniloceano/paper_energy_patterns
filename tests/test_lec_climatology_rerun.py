from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from scripts.lec_climatology_rerun.common import (
    PRESSURE_LEVELS,
    REQUIRED_RESULT_COLUMNS,
    REQUIRED_VERTICAL_TERMS,
    RunConfig,
    StateDB,
    isolated_cds_home,
    load_keys,
    validate_lec_output,
    validate_netcdf,
)
from scripts.lec_climatology_rerun.prepare import population_from_cache
from scripts.lec_climatology_rerun.pipeline import recover
from scripts.lec_climatology_rerun.pipeline import choose_key
from scripts.lec_climatology_rerun.build_corrected_cache import parse_periods


def test_population_reproduces_complete_order_and_finite_terms(tmp_path: Path):
    terms = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]
    rows = []
    for track_id, phases in {
        "good": ["incipient", "intensification", "mature", "decay"],
        "wrong": ["incipient", "mature", "intensification", "decay"],
        "missing": ["incipient", "intensification", "decay"],
    }.items():
        for phase in phases:
            rows.append({"track_id": track_id, "phase": phase, "period": phase, **{term: 1.0 for term in terms}})
    rows[1]["Ca"] = np.nan
    # A second finite intensification record means the cyclone remains eligible,
    # matching the real aggregation-before-wide behavior.
    rows.append({"track_id": "good", "phase": "intensification", "period": "intensification 2", **{term: 2.0 for term in terms}})
    cache = tmp_path / "cache.parquet"
    pd.DataFrame(rows).to_parquet(cache)
    _, ids = population_from_cache(cache)
    assert ids == {"good"}


def test_sqlite_state_machine_and_active_runtime(tmp_path: Path):
    db = StateDB(tmp_path / "state.sqlite3")
    db.add_cyclones([{"track_id": "1", "n_timesteps": 8, "lifecycle_hours": 21}], {"1"})
    db.transition("1", "DOWNLOADING", download_attempts=1)
    db.advance_active_runtime(12.5)
    row = db.rows("track_id='1'")[0]
    assert row["state"] == "DOWNLOADING"
    assert float(db.get_meta("cumulative_active_runtime")) == pytest.approx(12.5)
    db.close()


def test_credentials_are_isolated_and_removed(tmp_path: Path):
    config = RunConfig(
        run_root=str(tmp_path), paper_repo=str(tmp_path), toolkit_source=str(tmp_path / "source"),
        toolkit_worktree=str(tmp_path / "worktree"), keys_file=str(tmp_path / "keys"),
    )
    config.create_directories()
    with isolated_cds_home(config, "secret-value-that-must-not-be-logged", "key-001") as home:
        rc = home / ".cdsapirc"
        assert rc.exists()
        assert oct(rc.stat().st_mode & 0o777) == "0o600"
        assert oct(home.stat().st_mode & 0o777) == "0o700"
    assert not home.exists()


def test_key_inventory_uses_token_field_not_human_label(tmp_path: Path):
    inventory = tmp_path / "keys"
    token_a = "a" * 36
    token_b = "b" * 36
    inventory.write_text(f"{token_a} - account one\n{token_b} - account two\n")
    assert load_keys(inventory) == [token_a, token_b]


def make_era5(path: Path, times: pd.DatetimeIndex):
    levels = np.array([int(value) for value in PRESSURE_LEVELS])
    shape = (len(times), len(levels), 2, 2)
    dataset = xr.Dataset(
        {name: (("valid_time", "pressure_level", "latitude", "longitude"), np.ones(shape))
         for name in ("u", "v", "t", "w", "z")},
        coords={"valid_time": times, "pressure_level": levels, "latitude": [-1, 0], "longitude": [0, 1]},
    )
    dataset.to_netcdf(path)


def test_netcdf_validation_rejects_missing_timestamp(tmp_path: Path):
    path = tmp_path / "era5.nc"
    times = pd.date_range("2000-01-01", periods=3, freq="3h")
    make_era5(path, times)
    info = validate_netcdf(path, [str(value) for value in times])
    assert info["n_levels"] == len(PRESSURE_LEVELS)
    with pytest.raises(ValueError, match="missing 1 expected timestamps"):
        validate_netcdf(path, [str(times[0] - pd.Timedelta(hours=3))])


def test_lec_output_validation(tmp_path: Path):
    track_id = "20000001"
    directory = tmp_path / f"{track_id}_ERA5_track"
    vertical = directory / "results_vertical_levels"
    vertical.mkdir(parents=True)
    times = pd.date_range("2000-01-01", periods=3, freq="3h")
    frame = pd.DataFrame({"time": times, **{term: np.ones(3) for term in REQUIRED_RESULT_COLUMNS}})
    frame.to_csv(directory / f"{track_id}_ERA5_track_results.csv", index=False)
    pd.DataFrame({
        "phase": ["incipient", "intensification", "mature", "decay"],
        "start": [times[0], times[0], times[1], times[2]],
        "end": [times[0], times[1], times[1], times[2]],
    }).to_csv(directory / "periods.csv", index=False)
    pd.DataFrame({"time": times}).to_csv(directory / f"{track_id}_ERA5_track_trackfile", sep=";", index=False)
    for term in REQUIRED_VERTICAL_TERMS:
        pd.DataFrame(np.ones((3, 2)), index=times, columns=[10000, 100000]).to_csv(vertical / f"{term}_pressure_level.csv")
    (directory / f"log.{track_id}_ERA5").write_text("Analysis complete\n")
    info = validate_lec_output(directory, track_id, [str(value) for value in times])
    assert info["rows"] == 3


def test_period_parser_preserves_secondary_cycles(tmp_path: Path):
    path = tmp_path / "periods.csv"
    phases = ["incipient", "intensification", "mature", "decay", "intensification 2"]
    pd.DataFrame({
        "phase": phases,
        "start": pd.date_range("2000-01-01", periods=len(phases), freq="3h"),
        "end": pd.date_range("2000-01-01", periods=len(phases), freq="3h"),
    }).to_csv(path, index=False)
    parsed = parse_periods(path)
    assert [period for period, _, _, _ in parsed] == phases
    assert parsed[-1][1] == "intensification"


def test_restart_recovery_uses_validated_netcdf(tmp_path: Path):
    config = RunConfig(
        run_root=str(tmp_path), paper_repo=str(tmp_path), toolkit_source=str(tmp_path / "source"),
        toolkit_worktree=str(tmp_path / "worktree"), keys_file=str(tmp_path / "keys"),
    )
    config.create_directories()
    times = pd.date_range("2000-01-01", periods=3, freq="3h")
    track = config.tracks_dir / "track_1.txt"
    track.write_text("time;Lat;Lon\n" + "\n".join(f"{value:%Y-%m-%d-%H%M};-40;-50" for value in times) + "\n")
    make_era5(config.downloads_dir / "1_ERA5.nc", times)
    db = StateDB(config.db)
    db.add_cyclones([{"track_id": "1", "n_timesteps": 3, "lifecycle_hours": 6}], set())
    db.transition("1", "DOWNLOADING")
    recover(config, db)
    assert db.rows("track_id='1'")[0]["state"] == "DOWNLOADED"
    db.close()


def test_key_selection_never_reuses_an_active_key(tmp_path: Path):
    db = StateDB(tmp_path / "state.sqlite3")
    db.init_keys(2)
    keys = ["a" * 36, "b" * 36]
    selected = choose_key(db, keys, 0, {"key-001"})
    assert selected is not None and selected[1] == "key-002"
    assert choose_key(db, keys, selected[0], {"key-001", "key-002"}) is None
    db.close()


def test_key_selection_excludes_preflight_disabled_accounts(tmp_path: Path):
    db = StateDB(tmp_path / "state.sqlite3")
    db.init_keys(2)
    db.conn.execute(
        "UPDATE key_health SET last_status='licence_required',cooldown_until=0 WHERE key_id='key-001'"
    )
    db.conn.commit()
    keys = ["a" * 36, "b" * 36]
    selected = choose_key(db, keys, 0)
    assert selected is not None and selected[1] == "key-002"
    db.close()
