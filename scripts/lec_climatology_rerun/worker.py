#!/usr/bin/env python3
"""One-shot download and compute workers used by the scheduler.

This module never reads the multi-key file. A download subprocess sees exactly
one temporary HOME containing one credential, and removes it on exit.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

from .common import (
    ERA5_VARIABLES,
    PRESSURE_LEVELS,
    RunConfig,
    read_track_times,
    safe_error,
    utc_now,
    validate_lec_output,
    validate_netcdf,
)


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_text(json.dumps(payload, sort_keys=True) + "\n")
    temp.replace(path)


def classify_error(exc: Exception) -> tuple[str, bool]:
    text = str(exc).lower()
    if "429" in text or "too many" in text:
        return "HTTP_429", True
    if any(code in text for code in ("500", "502", "503", "504")):
        return "HTTP_5XX", True
    if "timeout" in text or "timed out" in text:
        return "TIMEOUT", True
    if any(word in text for word in ("unauthorized", "forbidden", "401", "403", "authentication")):
        return "AUTH", True
    if any(word in text for word in ("connection", "network", "temporar")):
        return "NETWORK", True
    return type(exc).__name__.upper(), False


def download_one(config: RunConfig, track_id: str) -> int:
    import cdsapi
    import pandas as pd
    import xarray as xr

    track_path = config.tracks_dir / f"track_{track_id}.txt"
    output = config.downloads_dir / f"{track_id}_ERA5.nc"
    progress = config.progress_dir / f"download_{track_id}.json"
    track = pd.read_csv(track_path, sep=";", parse_dates=["time"])
    expected_times = [str(value) for value in track["time"]]
    if output.exists():
        validate_netcdf(output, expected_times)
        atomic_json(progress, {"status": "complete", "bytes": output.stat().st_size, "updated_at": utc_now()})
        return 0

    north = min(90, math.ceil(float(track["Lat"].max()) + 15))
    south = max(-90, math.floor(float(track["Lat"].min()) - 15))
    west = max(-180, math.floor(float(track["Lon"].min()) - 15))
    east = min(180, math.ceil(float(track["Lon"].max()) + 15))
    if west >= east:
        raise ValueError("wrapped ERA5 download domains are unsupported")
    dates = pd.date_range(track["time"].min().date(), track["time"].max().date(), freq="D")
    daily_dir = config.downloads_dir / "daily" / track_id
    daily_dir.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client(timeout=600, retry_max=0, quiet=True)
    daily_files: list[Path] = []
    try:
        for index, date in enumerate(dates, 1):
            day_times = track.loc[track["time"].dt.date == date.date(), "time"]
            if day_times.empty:
                continue
            target = daily_dir / f"era5_{date:%Y%m%d}.nc"
            daily_files.append(target)
            if target.exists():
                try:
                    validate_netcdf(target, [str(value) for value in day_times])
                    continue
                except Exception:
                    target.unlink()
            part = target.with_suffix(".nc.part")
            part.unlink(missing_ok=True)
            request = {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": ERA5_VARIABLES,
                "pressure_level": PRESSURE_LEVELS,
                "year": f"{date.year:04d}",
                "month": f"{date.month:02d}",
                "day": f"{date.day:02d}",
                "time": [value.strftime("%H:00") for value in day_times],
                "area": [north, west, south, east],
            }
            atomic_json(progress, {
                "status": "requesting", "day": index, "days": len(dates),
                "bytes": sum(path.stat().st_size for path in daily_files if path.exists()),
                "updated_at": utc_now(),
            })
            client.retrieve("reanalysis-era5-pressure-levels", request, str(part))
            validate_netcdf(part, [str(value) for value in day_times])
            part.replace(target)

        if not daily_files:
            raise ValueError("no ERA5 daily requests were generated")
        combined_part = output.with_suffix(".nc.part")
        combined_part.unlink(missing_ok=True)
        datasets = [xr.open_dataset(path) for path in daily_files]
        try:
            time_name = "valid_time" if "valid_time" in datasets[0].coords else "time"
            combined = xr.concat(datasets, dim=time_name).sortby(time_name)
            combined.to_netcdf(combined_part)
            combined.close()
        finally:
            for dataset in datasets:
                dataset.close()
        info = validate_netcdf(combined_part, expected_times)
        combined_part.replace(output)
        atomic_json(progress, {"status": "complete", **info, "updated_at": utc_now()})
        return 0
    except Exception as exc:
        category, retryable = classify_error(exc)
        atomic_json(progress, {
            "status": "failed", "category": category, "retryable": retryable,
            "error": safe_error(exc), "updated_at": utc_now(),
        })
        return 75 if retryable else 65


def compute_one(config: RunConfig, track_id: str) -> int:
    source = config.downloads_dir / f"{track_id}_ERA5.nc"
    track = config.tracks_dir / f"track_{track_id}.txt"
    result = config.results_dir / f"{track_id}_ERA5_track"
    progress = config.progress_dir / f"compute_{track_id}.json"
    expected_times = read_track_times(track)
    if result.exists():
        try:
            info = validate_lec_output(
                result,
                track_id,
                expected_times,
                config.phase_windows_dir / f"{track_id}.csv",
            )
            atomic_json(progress, {"status": "complete", **info, "updated_at": utc_now()})
            return 0
        except Exception:
            # Preserve invalid output for audit instead of overwriting it.
            quarantine = config.root / "invalid_outputs" / f"{track_id}_{int(time.time())}"
            quarantine.parent.mkdir(parents=True, exist_ok=True)
            result.replace(quarantine)

    validate_netcdf(source, expected_times)
    toolkit = Path(config.toolkit_worktree)
    inbox = config.root / "compute_inbox" / track_id
    inbox.mkdir(parents=True, exist_ok=True)
    infile = inbox / f"{track_id}_ERA5.nc"
    infile.unlink(missing_ok=True)
    os.link(source, infile)  # toolkit removes this link; the canonical file remains
    toolkit_result = toolkit / "LEC_Results" / f"{track_id}_ERA5_track"
    if toolkit_result.exists():
        quarantine = config.root / "invalid_outputs" / f"toolkit_{track_id}_{int(time.time())}"
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        toolkit_result.replace(quarantine)
    stdout = config.logs_dir / f"{track_id}_compute.stdout.log"
    stderr = config.logs_dir / f"{track_id}_compute.stderr.log"
    command = [
        "conda", "run", "-n", config.conda_env, "python",
        str(toolkit / "lorenzcycletoolkit.py"), str(infile),
        "-t", "-r", "-v", "--cdsapi",
        "--time-resolution", str(config.time_resolution_hours),
        "--trackfile", str(track),
    ]
    atomic_json(progress, {"status": "running", "started_at": utc_now()})
    with stdout.open("w") as out, stderr.open("w") as err:
        completed = subprocess.run(command, cwd=toolkit, stdout=out, stderr=err)
    if completed.returncode != 0:
        atomic_json(progress, {
            "status": "failed", "category": "TOOLKIT_EXIT",
            "retryable": True, "returncode": completed.returncode,
            "error": f"toolkit exited {completed.returncode}; see per-cyclone logs",
            "updated_at": utc_now(),
        })
        return 75
    if not toolkit_result.exists():
        atomic_json(progress, {
            "status": "failed", "category": "MISSING_OUTPUT", "retryable": True,
            "error": "toolkit exited successfully but output directory is missing",
            "updated_at": utc_now(),
        })
        return 75
    # The scientific target is the same population and phase aggregation used
    # by the article. Freeze those independently archived phase windows rather
    # than silently reclassifying lifecycles with a newer CycloPhaser release.
    frozen_periods = config.phase_windows_dir / f"{track_id}.csv"
    if not frozen_periods.is_file():
        atomic_json(progress, {
            "status": "failed", "category": "PHASE_WINDOWS", "retryable": False,
            "error": "frozen article lifecycle windows are missing",
            "updated_at": utc_now(),
        })
        return 65
    shutil.copyfile(frozen_periods, toolkit_result / "periods.csv")
    temp_result = config.results_dir / f".{track_id}_ERA5_track.part"
    if temp_result.exists():
        shutil.rmtree(temp_result)
    toolkit_result.replace(temp_result)
    try:
        info = validate_lec_output(temp_result, track_id, expected_times, frozen_periods)
    except Exception as exc:
        quarantine = config.root / "invalid_outputs" / f"{track_id}_{int(time.time())}"
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        temp_result.replace(quarantine)
        atomic_json(progress, {
            "status": "failed", "category": "OUTPUT_VALIDATION", "retryable": True,
            "error": safe_error(exc), "updated_at": utc_now(),
        })
        return 75
    temp_result.replace(result)
    atomic_json(progress, {"status": "complete", **info, "updated_at": utc_now()})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["download", "compute"])
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--track-id", required=True)
    args = parser.parse_args()
    config = RunConfig.load(args.run_root)
    try:
        if args.stage == "download":
            return download_one(config, args.track_id)
        return compute_one(config, args.track_id)
    except Exception as exc:
        progress = config.progress_dir / f"{args.stage}_{args.track_id}.json"
        category, retryable = classify_error(exc)
        atomic_json(progress, {
            "status": "failed", "category": category, "retryable": retryable,
            "error": safe_error(exc), "updated_at": utc_now(),
        })
        return 75 if retryable else 65


if __name__ == "__main__":
    raise SystemExit(main())
