"""Shared configuration, state, validation, and provenance helpers.

The production scheduler is the only writer to the SQLite database. Worker
processes communicate through exit codes and small, non-sensitive JSON status
files. This deliberately avoids SQLite writes from concurrent workers.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TOOLKIT_COMMIT = "d38cda7e37d8e8a3a937a5919640a94bef19e34a"
CORRECTION_COMMIT = "d07707767c2962fed0475ff4573e7d15a97f8c69"
TRACK_SOURCE_DOI = "10.5281/zenodo.18133432"
TRACK_SOURCE_URL = (
    "https://zenodo.org/records/18133432/files/"
    "tracks_SAt_filtered_with_energetics.csv"
)
CDS_URL = "https://cds.climate.copernicus.eu/api"

PRESSURE_LEVELS = [
    "1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100",
    "125", "150", "175", "200", "225", "250", "300", "350", "400",
    "450", "500", "550", "600", "650", "700", "750", "775", "800",
    "825", "850", "875", "900", "925", "950", "975", "1000",
]
ANALYSIS_LEVELS = PRESSURE_LEVELS[5:]  # toolkit drops levels above 10 hPa
ERA5_VARIABLES = [
    "u_component_of_wind",
    "v_component_of_wind",
    "temperature",
    "vertical_velocity",
    "geopotential",
]
REQUIRED_DATA_VARS = {"u", "v", "t", "w", "z"}
REQUIRED_RESULT_COLUMNS = {
    "Az", "Ae", "Kz", "Ke", "Cz", "Ca", "Ck", "Ce",
    "BAz", "BAe", "BKz", "BKe", "Gz", "Ge",
}
REQUIRED_VERTICAL_TERMS = {
    "Az", "Ae", "Kz", "Ke", "Cz", "Ca", "Ck", "Ce", "Gz", "Ge",
}

STATES = (
    "PENDING", "DOWNLOAD_QUEUED", "DOWNLOADING", "DOWNLOADED",
    "COMPUTE_QUEUED", "COMPUTING", "VALIDATING", "COMPLETE",
    "FAILED_RETRYABLE", "FAILED_FINAL",
)
ACTIVE_STATES = {"DOWNLOAD_QUEUED", "DOWNLOADING", "COMPUTE_QUEUED", "COMPUTING", "VALIDATING"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def safe_error(value: object, limit: int = 500) -> str:
    """Return a concise error that cannot contain a CDS credential value."""
    text = str(value).replace("\n", " ")
    text = re.sub(r"(?i)(key|token|authorization)(\s*[:=]\s*)\S+", r"\1\2[REDACTED]", text)
    text = re.sub(r"\b[A-Za-z0-9_-]{35,}\b", "[REDACTED]", text)
    return text[:limit]


@dataclass(frozen=True)
class RunConfig:
    run_root: str
    paper_repo: str
    toolkit_source: str
    toolkit_worktree: str
    toolkit_commit: str = EXPECTED_TOOLKIT_COMMIT
    correction_commit: str = CORRECTION_COMMIT
    conda_env: str = "lorenz"
    keys_file: str = "/p1-swell/danilocs/cds-keys"
    max_download_workers: int = 8
    initial_download_workers: int = 3
    max_compute_workers: int = 8
    max_download_retries: int = 7
    max_compute_retries: int = 3
    backpressure_downloaded: int = 16
    time_resolution_hours: int = 3
    cleanup_era5_after_complete: bool = True
    poll_seconds: int = 5

    @property
    def root(self) -> Path:
        return Path(self.run_root)

    @property
    def db(self) -> Path:
        return self.root / "state.sqlite3"

    @property
    def manifest(self) -> Path:
        return self.root / "population_manifest.csv"

    @property
    def tracks_dir(self) -> Path:
        return self.root / "tracks"

    @property
    def downloads_dir(self) -> Path:
        return self.root / "era5"

    @property
    def results_dir(self) -> Path:
        return self.root / "lec_results"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def credentials_dir(self) -> Path:
        return self.root / ".worker_credentials"

    @property
    def progress_dir(self) -> Path:
        return self.root / "worker_progress"

    @property
    def stop_file(self) -> Path:
        return self.root / "STOP"

    @property
    def production_gate(self) -> Path:
        return self.root / "PRODUCTION_APPROVED"

    def create_directories(self) -> None:
        for path in (
            self.root, self.tracks_dir, self.downloads_dir, self.results_dir,
            self.logs_dir, self.credentials_dir, self.progress_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        os.chmod(self.credentials_dir, 0o700)

    def save(self) -> Path:
        self.create_directories()
        path = self.root / "config.json"
        temp = path.with_suffix(".json.part")
        temp.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")
        temp.replace(path)
        return path

    @classmethod
    def load(cls, run_root: Path | str) -> "RunConfig":
        data = json.loads((Path(run_root) / "config.json").read_text())
        return cls(**data)


class StateDB:
    def __init__(self, path: Path):
        self.path = path
        self.conn = sqlite3.connect(path, timeout=60)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=FULL")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self._create_schema()

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cyclones (
                track_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                is_pilot INTEGER NOT NULL DEFAULT 0,
                n_timesteps INTEGER NOT NULL,
                lifecycle_hours REAL NOT NULL,
                download_attempts INTEGER NOT NULL DEFAULT 0,
                compute_attempts INTEGER NOT NULL DEFAULT 0,
                bytes_downloaded INTEGER NOT NULL DEFAULT 0,
                key_id TEXT,
                next_retry_at REAL NOT NULL DEFAULT 0,
                last_error TEXT,
                started_download_at TEXT,
                downloaded_at TEXT,
                started_compute_at TEXT,
                completed_at TEXT,
                download_seconds REAL,
                compute_seconds REAL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cyclones_state ON cyclones(state);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                track_id TEXT,
                stage TEXT NOT NULL,
                event TEXT NOT NULL,
                detail TEXT
            );
            CREATE TABLE IF NOT EXISTS key_health (
                key_id TEXT PRIMARY KEY,
                successes INTEGER NOT NULL DEFAULT 0,
                retries INTEGER NOT NULL DEFAULT 0,
                failures INTEGER NOT NULL DEFAULT 0,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                cooldown_until REAL NOT NULL DEFAULT 0,
                last_status TEXT,
                updated_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def set_meta(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value))
        )
        self.conn.commit()

    def get_meta(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def add_cyclones(self, rows: Iterable[dict[str, Any]], pilot_ids: set[str]) -> None:
        now = utc_now()
        self.conn.executemany(
            """INSERT INTO cyclones(track_id,state,is_pilot,n_timesteps,lifecycle_hours,updated_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(track_id) DO UPDATE SET
                 is_pilot=excluded.is_pilot,
                 n_timesteps=excluded.n_timesteps,
                 lifecycle_hours=excluded.lifecycle_hours""",
            [
                (str(r["track_id"]), "PENDING", int(str(r["track_id"]) in pilot_ids),
                 int(r["n_timesteps"]), float(r["lifecycle_hours"]), now)
                for r in rows
            ],
        )
        self.conn.commit()

    def transition(self, track_id: str, state: str, *, error: str | None = None, **fields: Any) -> None:
        if state not in STATES:
            raise ValueError(f"invalid state: {state}")
        updates = {"state": state, "updated_at": utc_now(), **fields}
        if error is not None:
            updates["last_error"] = safe_error(error)
        sql = ",".join(f"{key}=?" for key in updates)
        self.conn.execute(
            f"UPDATE cyclones SET {sql} WHERE track_id=?",
            [*updates.values(), track_id],
        )
        self.conn.execute(
            "INSERT INTO events(ts,track_id,stage,event,detail) VALUES(?,?,?,?,?)",
            (utc_now(), track_id, state.split("_")[0], state, updates.get("last_error")),
        )
        self.conn.commit()

    def rows(self, where: str = "1=1", params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.conn.execute(f"SELECT * FROM cyclones WHERE {where}", params))

    def counts(self) -> dict[str, int]:
        values = {state: 0 for state in STATES}
        for row in self.conn.execute("SELECT state,COUNT(*) n FROM cyclones GROUP BY state"):
            values[row["state"]] = row["n"]
        return values

    def event(self, stage: str, event: str, detail: str = "", track_id: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO events(ts,track_id,stage,event,detail) VALUES(?,?,?,?,?)",
            (utc_now(), track_id, stage, event, safe_error(detail, 1000)),
        )
        self.conn.commit()

    def init_keys(self, count: int) -> None:
        now = utc_now()
        self.conn.executemany(
            "INSERT OR IGNORE INTO key_health(key_id,updated_at) VALUES(?,?)",
            [(f"key-{i + 1:03d}", now) for i in range(count)],
        )
        self.conn.commit()

    def update_key(self, key_id: str, success: bool, retryable: bool, cooldown_until: float = 0) -> None:
        if success:
            sql = """UPDATE key_health SET successes=successes+1,consecutive_failures=0,
                     cooldown_until=0,last_status='healthy',updated_at=? WHERE key_id=?"""
            args = (utc_now(), key_id)
        else:
            sql = """UPDATE key_health SET retries=retries+?,failures=failures+1,
                     consecutive_failures=consecutive_failures+1,cooldown_until=?,
                     last_status=?,updated_at=? WHERE key_id=?"""
            args = (int(retryable), cooldown_until, "cooldown" if cooldown_until else "failed", utc_now(), key_id)
        self.conn.execute(sql, args)
        self.conn.commit()

    def advance_active_runtime(self, seconds: float) -> None:
        current = float(self.get_meta("cumulative_active_runtime", 0.0))
        self.set_meta("cumulative_active_runtime", current + max(0.0, seconds))
        self.set_meta("last_heartbeat", utc_now())


def load_keys(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text().splitlines()]
    # Server inventory format is "<token> - <human label>". Only the first
    # whitespace-delimited field is a CDS token; labels must never enter the
    # generated .cdsapirc or logs.
    keys = [line.split(maxsplit=1)[0] for line in lines if line and not line.startswith("#")]
    if not keys:
        raise RuntimeError(f"no credentials found in {path}")
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate CDS credential tokens in inventory")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{32,}", key) for key in keys):
        raise RuntimeError("unexpected CDS credential inventory format")
    return keys


@contextlib.contextmanager
def isolated_cds_home(config: RunConfig, key_value: str, key_id: str):
    """Create a mode-0700 HOME with a mode-0600 .cdsapirc for one process."""
    import tempfile

    home = Path(tempfile.mkdtemp(prefix=f"{key_id}-", dir=config.credentials_dir))
    os.chmod(home, 0o700)
    rc = home / ".cdsapirc"
    fd = os.open(rc, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(f"url: {CDS_URL}\nkey: {key_value}\n")
        yield home
    finally:
        with contextlib.suppress(FileNotFoundError):
            rc.unlink()
        with contextlib.suppress(OSError):
            home.rmdir()


def validate_netcdf(path: Path, expected_times: list[str] | None = None) -> dict[str, Any]:
    import pandas as pd
    import xarray as xr

    if not path.exists() or path.stat().st_size < 1024:
        raise ValueError("NetCDF missing or too small")
    with xr.open_dataset(path) as ds:
        missing = REQUIRED_DATA_VARS - set(ds.data_vars)
        if missing:
            raise ValueError(f"missing ERA5 variables: {sorted(missing)}")
        time_name = "valid_time" if "valid_time" in ds.coords else "time"
        level_name = "pressure_level" if "pressure_level" in ds.coords else "level"
        if time_name not in ds.coords or level_name not in ds.coords:
            raise ValueError("missing time or pressure coordinate")
        times = pd.DatetimeIndex(ds[time_name].values)
        levels = {str(int(float(v))) for v in ds[level_name].values}
        if not set(PRESSURE_LEVELS).issubset(levels):
            raise ValueError("pressure-level set is incomplete")
        if expected_times:
            wanted = pd.DatetimeIndex(pd.to_datetime(expected_times))
            missing_times = wanted.difference(times)
            if len(missing_times):
                raise ValueError(f"missing {len(missing_times)} expected timestamps")
        for dim in (time_name, level_name):
            if ds.sizes.get(dim, 0) == 0:
                raise ValueError(f"empty dimension: {dim}")
        return {
            "bytes": path.stat().st_size,
            "n_times": len(times),
            "n_levels": len(levels),
            "start": str(times.min()),
            "end": str(times.max()),
        }


def _find_vertical_file(vertical: Path, stem: str) -> Path | None:
    candidates = [
        vertical / f"{stem}_pressure_level.csv",
        vertical / f"{stem}_level.csv",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    matches = sorted(vertical.glob(f"{stem}_*.csv"))
    return matches[0] if matches else None


def validate_lec_output(result_dir: Path, track_id: str, expected_times: list[str]) -> dict[str, Any]:
    import numpy as np
    import pandas as pd

    main = result_dir / f"{track_id}_ERA5_track_results.csv"
    periods = result_dir / "periods.csv"
    vertical = result_dir / "results_vertical_levels"
    trackfile = result_dir / f"{track_id}_ERA5_track_trackfile"
    for path in (main, periods, trackfile):
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"required output missing: {path.name}")
    if not vertical.is_dir():
        raise ValueError("results_vertical_levels is missing")
    frame = pd.read_csv(main)
    missing_cols = REQUIRED_RESULT_COLUMNS - set(frame.columns)
    if missing_cols:
        raise ValueError(f"main results missing columns: {sorted(missing_cols)}")
    numeric = frame[list(REQUIRED_RESULT_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    if numeric.empty or not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("main results contain NaN or infinite required values")
    expected = pd.DatetimeIndex(pd.to_datetime(expected_times))
    vertical_shapes: dict[str, tuple[int, int]] = {}
    for stem in sorted(REQUIRED_VERTICAL_TERMS):
        path = _find_vertical_file(vertical, stem)
        if path is None or path.stat().st_size == 0:
            raise ValueError(f"vertical output missing for {stem}")
        data = pd.read_csv(path, index_col=0)
        if data.empty:
            raise ValueError(f"empty vertical output for {stem}")
        data.index = pd.to_datetime(data.index, errors="coerce")
        if data.index.isna().any() or len(expected.difference(data.index)):
            raise ValueError(f"timestamp mismatch in vertical output for {stem}")
        values = data.apply(pd.to_numeric, errors="coerce").to_numpy()
        if not np.isfinite(values).all():
            raise ValueError(f"NaN or infinite values in vertical output for {stem}")
        vertical_shapes[stem] = data.shape
    log_files = list(result_dir.glob("log.*"))
    if not log_files:
        raise ValueError("toolkit completion log is missing")
    log_tail = log_files[0].read_text(errors="replace")[-10000:]
    if "Analysis complete" not in log_tail:
        raise ValueError("toolkit completion marker is missing")
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "vertical_shapes": vertical_shapes,
        "bytes": sum(p.stat().st_size for p in result_dir.rglob("*") if p.is_file()),
    }


def read_track_times(track_path: Path) -> list[str]:
    import pandas as pd

    frame = pd.read_csv(track_path, sep=";")
    return [str(v) for v in pd.to_datetime(frame["time"], format="%Y-%m-%d-%H%M")]
