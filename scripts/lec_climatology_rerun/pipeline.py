#!/usr/bin/env python3
"""Persistent two-stage scheduler for the corrected LEC climatology."""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .common import (
    ACTIVE_STATES,
    RunConfig,
    StateDB,
    git_output,
    isolated_cds_home,
    load_keys,
    read_track_times,
    safe_error,
    utc_now,
    validate_lec_output,
    validate_netcdf,
)


def provision_toolkit(config: RunConfig) -> None:
    source = Path(config.toolkit_source)
    worktree = Path(config.toolkit_worktree)
    git_output(source, "cat-file", "-e", f"{config.toolkit_commit}^{{commit}}")
    ancestor = subprocess.run(
        ["git", "-C", str(source), "merge-base", "--is-ancestor", config.correction_commit, config.toolkit_commit]
    )
    if ancestor.returncode != 0:
        raise RuntimeError("configured toolkit commit does not contain the correction commit")
    if not worktree.exists():
        worktree.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "-C", str(source), "worktree", "add", "--detach", str(worktree), config.toolkit_commit],
            check=True,
        )
    actual = git_output(worktree, "rev-parse", "HEAD")
    if actual != config.toolkit_commit:
        raise RuntimeError(f"toolkit worktree is {actual}, expected {config.toolkit_commit}")
    dirty = git_output(worktree, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise RuntimeError("pinned toolkit worktree has tracked modifications")
    (worktree / "LEC_Results").mkdir(exist_ok=True)


def _run_worker(config: RunConfig, stage: str, track_id: str, env: dict[str, str] | None = None) -> int:
    log = config.logs_dir / f"{track_id}_{stage}.launcher.log"
    command = [
        sys.executable, "-m", "scripts.lec_climatology_rerun.worker", stage,
        "--run-root", config.run_root, "--track-id", track_id,
    ]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    with log.open("a") as stream:
        stream.write(f"\n[{utc_now()}] start {stage} attempt\n")
        stream.flush()
        result = subprocess.run(
            command, cwd=config.paper_repo, env=merged_env,
            stdout=stream, stderr=subprocess.STDOUT,
        )
        stream.write(f"[{utc_now()}] exit={result.returncode}\n")
    return result.returncode


def _run_download(config: RunConfig, track_id: str, key_value: str, key_id: str) -> int:
    with isolated_cds_home(config, key_value, key_id) as home:
        return _run_worker(config, "download", track_id, {"HOME": str(home)})


def read_progress(config: RunConfig, stage: str, track_id: str) -> dict[str, Any]:
    path = config.progress_dir / f"{stage}_{track_id}.json"
    try:
        return json.loads(path.read_text())
    except Exception:
        return {"status": "failed", "retryable": True, "category": "NO_PROGRESS", "error": "worker progress record missing"}


def recover(config: RunConfig, db: StateDB) -> None:
    """Resolve interrupted states from validated artifacts, never directory existence."""
    for row in db.rows("state IN (%s)" % ",".join("?" for _ in ACTIVE_STATES), tuple(ACTIVE_STATES)):
        track_id = row["track_id"]
        times = read_track_times(config.tracks_dir / f"track_{track_id}.txt")
        result = config.results_dir / f"{track_id}_ERA5_track"
        data = config.downloads_dir / f"{track_id}_ERA5.nc"
        try:
            validate_lec_output(
                result, track_id, times, config.phase_windows_dir / f"{track_id}.csv"
            )
            db.transition(track_id, "COMPLETE", completed_at=utc_now())
            continue
        except Exception:
            pass
        try:
            info = validate_netcdf(data, times)
            db.transition(track_id, "DOWNLOADED", bytes_downloaded=info["bytes"])
        except Exception:
            data.with_suffix(".nc.part").unlink(missing_ok=True)
            db.transition(track_id, "PENDING")
    db.event("scheduler", "RECOVERY_COMPLETE", "interrupted states reconciled")


def choose_key(
    db: StateDB,
    keys: list[str],
    cursor: int,
    busy_key_ids: set[str] | None = None,
) -> tuple[int, str, str] | None:
    now = time.time()
    busy_key_ids = busy_key_ids or set()
    health = {row["key_id"]: row for row in db.conn.execute("SELECT * FROM key_health")}
    for offset in range(len(keys)):
        index = (cursor + offset) % len(keys)
        key_id = f"key-{index + 1:03d}"
        permanently_disabled = health[key_id]["last_status"] in {
            "licence_required", "authentication_failed"
        }
        if (
            key_id not in busy_key_ids
            and not permanently_disabled
            and float(health[key_id]["cooldown_until"]) <= now
        ):
            return (index + 1, key_id, keys[index])
    return None


def retry_delay(attempt: int) -> float:
    return min(3600.0, 30.0 * (2 ** max(0, attempt - 1))) + random.uniform(0, 20)


def eligible_clause(mode: str) -> tuple[str, tuple[Any, ...]]:
    return ("is_pilot=1", ()) if mode == "pilot" else ("1=1", ())


def run(config: RunConfig, mode: str) -> int:
    provision_toolkit(config)
    if mode == "production" and not config.production_gate.exists():
        raise RuntimeError("production is not approved; complete pilots then run approve-production")
    keys = load_keys(Path(config.keys_file))
    db = StateDB(config.db)
    db.init_keys(len(keys))
    recover(config, db)
    db.set_meta("last_scheduler_start", utc_now())
    db.set_meta("scheduler_mode", mode)
    config.stop_file.unlink(missing_ok=True)

    stop_requested = False

    def stop_handler(signum, frame):  # noqa: ARG001
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)
    download_pool = ThreadPoolExecutor(max_workers=config.max_download_workers, thread_name_prefix="download")
    compute_pool = ThreadPoolExecutor(max_workers=config.max_compute_workers, thread_name_prefix="compute")
    downloads: dict[Future[int], tuple[str, str, float]] = {}
    computes: dict[Future[int], tuple[str, float]] = {}
    current_download_limit = config.initial_download_workers
    download_window: list[str] = []
    key_cursor = 0
    last_tick = time.monotonic()
    clause, params = eligible_clause(mode)
    try:
        while True:
            now_mono = time.monotonic()
            db.advance_active_runtime(now_mono - last_tick)
            last_tick = now_mono
            if config.stop_file.exists():
                stop_requested = True

            # Collect downloads.
            for future in list(downloads):
                if not future.done():
                    continue
                track_id, key_id, started = downloads.pop(future)
                row = db.rows("track_id=?", (track_id,))[0]
                progress = read_progress(config, "download", track_id)
                try:
                    rc = future.result()
                except Exception as exc:
                    rc, progress = 75, {"retryable": True, "category": "LAUNCHER", "error": safe_error(exc)}
                category = progress.get("category", "OK")
                if rc == 0:
                    try:
                        data = config.downloads_dir / f"{track_id}_ERA5.nc"
                        info = validate_netcdf(data, read_track_times(config.tracks_dir / f"track_{track_id}.txt"))
                        db.transition(
                            track_id, "DOWNLOADED", downloaded_at=utc_now(),
                            bytes_downloaded=info["bytes"], download_seconds=time.monotonic() - started,
                        )
                        db.update_key(key_id, True, False)
                        download_window.append("OK")
                        continue
                    except Exception as exc:
                        rc = 75
                        category = "OUTPUT_VALIDATION"
                        progress = {"retryable": True, "error": safe_error(exc)}
                retryable = bool(progress.get("retryable", rc == 75))
                attempts = int(row["download_attempts"])
                final = not retryable or attempts >= config.max_download_retries
                cooldown = 0.0
                if category == "AUTH":
                    cooldown = time.time() + 6 * 3600
                elif category in {"HTTP_429", "HTTP_5XX", "TIMEOUT", "NETWORK"}:
                    cooldown = time.time() + min(1800, retry_delay(attempts))
                db.update_key(key_id, False, retryable, cooldown)
                db.transition(
                    track_id, "FAILED_FINAL" if final else "FAILED_RETRYABLE",
                    error=progress.get("error", category),
                    next_retry_at=0 if final else time.time() + retry_delay(attempts),
                )
                download_window.append(category)

            # Adaptive CDS capacity over a small completion window.
            if len(download_window) >= 5:
                degraded = sum(value != "OK" for value in download_window)
                throttled = any(value in {"HTTP_429", "HTTP_5XX", "TIMEOUT"} for value in download_window)
                old = current_download_limit
                if throttled or degraded >= 2:
                    current_download_limit = max(1, current_download_limit - 1)
                elif degraded == 0:
                    current_download_limit = min(config.max_download_workers, current_download_limit + 1)
                if old != current_download_limit:
                    db.event("download", "ADAPTIVE_CAPACITY", f"{old}->{current_download_limit}; window={download_window}")
                download_window.clear()

            # Collect compute jobs and validate before COMPLETE.
            for future in list(computes):
                if not future.done():
                    continue
                track_id, started = computes.pop(future)
                row = db.rows("track_id=?", (track_id,))[0]
                progress = read_progress(config, "compute", track_id)
                try:
                    rc = future.result()
                except Exception as exc:
                    rc, progress = 75, {"retryable": True, "error": safe_error(exc)}
                if rc == 0:
                    try:
                        db.transition(track_id, "VALIDATING")
                        times = read_track_times(config.tracks_dir / f"track_{track_id}.txt")
                        validate_lec_output(
                            config.results_dir / f"{track_id}_ERA5_track",
                            track_id,
                            times,
                            config.phase_windows_dir / f"{track_id}.csv",
                        )
                        db.transition(
                            track_id, "COMPLETE", completed_at=utc_now(),
                            compute_seconds=time.monotonic() - started, last_error=None,
                        )
                        if config.cleanup_era5_after_complete:
                            (config.downloads_dir / f"{track_id}_ERA5.nc").unlink(missing_ok=True)
                            shutil.rmtree(config.downloads_dir / "daily" / track_id, ignore_errors=True)
                        continue
                    except Exception as exc:
                        rc = 75
                        progress = {"retryable": True, "error": safe_error(exc)}
                if rc != 0:
                    attempts = int(row["compute_attempts"])
                    retryable = bool(progress.get("retryable", rc == 75))
                    final = not retryable or attempts >= config.max_compute_retries
                    db.transition(
                        track_id, "FAILED_FINAL" if final else "FAILED_RETRYABLE",
                        error=progress.get("error", "compute worker failed"),
                        next_retry_at=0 if final else time.time() + retry_delay(attempts),
                    )

            # Requeue elapsed retryable failures based on validated data presence.
            for row in db.rows(f"{clause} AND state='FAILED_RETRYABLE' AND next_retry_at<=?", (*params, time.time())):
                track_id = row["track_id"]
                data = config.downloads_dir / f"{track_id}_ERA5.nc"
                try:
                    validate_netcdf(data, read_track_times(config.tracks_dir / f"track_{track_id}.txt"))
                    db.transition(track_id, "DOWNLOADED")
                except Exception:
                    db.transition(track_id, "PENDING")

            if not stop_requested:
                # Feed compute independently from downloads.
                slots = config.max_compute_workers - len(computes)
                if slots > 0:
                    for row in db.rows(f"{clause} AND state='DOWNLOADED' ORDER BY lifecycle_hours LIMIT ?", (*params, slots)):
                        track_id = row["track_id"]
                        db.transition(
                            track_id, "COMPUTE_QUEUED",
                            compute_attempts=int(row["compute_attempts"]) + 1,
                        )
                        db.transition(track_id, "COMPUTING", started_compute_at=utc_now())
                        computes[compute_pool.submit(_run_worker, config, "compute", track_id)] = (track_id, time.monotonic())

                # Backpressure caps downloaded-but-not-yet-complete inventory.
                buffered = len(db.rows(f"{clause} AND state IN ('DOWNLOADED','COMPUTE_QUEUED','COMPUTING','VALIDATING')", params))
                slots = min(current_download_limit - len(downloads), config.backpressure_downloaded - buffered)
                if slots > 0:
                    candidates = db.rows(f"{clause} AND state='PENDING' ORDER BY lifecycle_hours LIMIT ?", (*params, slots))
                    for row in candidates:
                        busy_keys = {value[1] for value in downloads.values()}
                        chosen = choose_key(db, keys, key_cursor, busy_keys)
                        if chosen is None:
                            break
                        key_cursor, key_id, key_value = chosen
                        track_id = row["track_id"]
                        db.transition(
                            track_id, "DOWNLOAD_QUEUED", key_id=key_id,
                            download_attempts=int(row["download_attempts"]) + 1,
                        )
                        db.transition(track_id, "DOWNLOADING", started_download_at=utc_now())
                        downloads[download_pool.submit(_run_download, config, track_id, key_value, key_id)] = (
                            track_id, key_id, time.monotonic()
                        )

            active = len(downloads) + len(computes)
            remaining = db.rows(f"{clause} AND state NOT IN ('COMPLETE','FAILED_FINAL')", params)
            if stop_requested and active == 0:
                db.event("scheduler", "GRACEFUL_STOP", f"mode={mode}")
                return 0
            if not remaining and active == 0:
                db.event("scheduler", "MODE_COMPLETE", f"mode={mode}")
                return 0
            time.sleep(config.poll_seconds)
    finally:
        download_pool.shutdown(wait=True, cancel_futures=False)
        compute_pool.shutdown(wait=True, cancel_futures=False)
        db.set_meta("last_scheduler_stop", utc_now())
        db.close()


def approve_production(config: RunConfig) -> None:
    db = StateDB(config.db)
    pilots = db.rows("is_pilot=1")
    if not pilots or any(row["state"] != "COMPLETE" for row in pilots):
        raise RuntimeError("all pilot cases must be COMPLETE before production approval")
    payload = {
        "approved_at": utc_now(),
        "pilot_ids": [row["track_id"] for row in pilots],
        "toolkit_commit": config.toolkit_commit,
    }
    config.production_gate.write_text(json.dumps(payload, indent=2) + "\n")
    db.event("validation", "PRODUCTION_APPROVED", json.dumps(payload))
    db.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["pilot", "production", "approve-production", "stop", "retry-failures", "provision"])
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    config = RunConfig.load(args.run_root)
    if args.command == "stop":
        config.stop_file.write_text(utc_now() + "\n")
        print(f"graceful stop requested: {config.stop_file}")
        return 0
    if args.command == "approve-production":
        approve_production(config)
        print("production approved")
        return 0
    if args.command == "retry-failures":
        db = StateDB(config.db)
        for row in db.rows("state IN ('FAILED_RETRYABLE','FAILED_FINAL')"):
            db.transition(row["track_id"], "PENDING", error="manually requeued", next_retry_at=0)
        db.close()
        print("failures requeued")
        return 0
    if args.command == "provision":
        provision_toolkit(config)
        print(f"pinned toolkit ready: {config.toolkit_worktree} @ {config.toolkit_commit}")
        return 0
    return run(config, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
