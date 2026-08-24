#!/usr/bin/env python3
"""Independent progress monitor with active-runtime ETA."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow running this file directly, not only as `python -m`.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_climatology_rerun.common import RunConfig


def duration(seconds: float | None, *, active: bool = True) -> str:
    if seconds is None or not math.isfinite(seconds):
        return "n/a"
    if seconds >= 86400:
        qualifier = " active server-days" if active else " days"
        return f"{seconds / 86400:.1f}{qualifier}"
    if seconds >= 3600:
        return f"{seconds / 3600:.1f} h"
    if seconds >= 60:
        return f"{seconds / 60:.1f} min"
    return f"{seconds:.0f} s"


def progress_records(config: RunConfig, stage: str) -> list[dict]:
    records = []
    for path in config.progress_dir.glob(f"{stage}_*.json"):
        try:
            value = json.loads(path.read_text())
            value["track_id"] = path.stem.replace(f"{stage}_", "")
            records.append(value)
        except Exception:
            pass
    return records


def snapshot(config: RunConfig) -> str:
    conn = sqlite3.connect(f"file:{config.db}?mode=ro", uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute("SELECT * FROM cyclones"))
    counts = {row["state"]: row["n"] for row in conn.execute("SELECT state,COUNT(*) n FROM cyclones GROUP BY state")}
    meta = {row["key"]: row["value"] for row in conn.execute("SELECT key,value FROM meta")}
    keys = list(conn.execute("SELECT * FROM key_health ORDER BY key_id"))
    now = datetime.now(timezone.utc)
    now_epoch = time.time()
    total = len(rows)
    complete = counts.get("COMPLETE", 0)
    downloaded = sum(counts.get(state, 0) for state in ("DOWNLOADED", "COMPUTE_QUEUED", "COMPUTING", "VALIDATING", "COMPLETE"))
    failed_retry = counts.get("FAILED_RETRYABLE", 0)
    failed_final = counts.get("FAILED_FINAL", 0)
    bytes_downloaded = sum(int(row["bytes_downloaded"] or 0) for row in rows)
    staged_bytes = sum(
        path.stat().st_size for path in config.downloads_dir.rglob("*") if path.is_file()
    )
    active_seconds = float(meta.get("cumulative_active_runtime", 0))
    active_download_ids = {row["track_id"] for row in rows if row["state"] == "DOWNLOADING"}
    active_downloads = progress_records(config, "download")
    active_downloads = [
        item for item in active_downloads
        if item.get("status") == "requesting" and item["track_id"] in active_download_ids
    ]
    transferring = sum(
        any(path.is_file() and path.stat().st_size > 0 for path in [
            *(config.downloads_dir / "daily" / item["track_id"]).glob("*.part"),
            config.downloads_dir / f"{item['track_id']}_ERA5.nc.part",
        ])
        for item in active_downloads
    )
    waiting = max(0, len(active_downloads) - transferring)

    completed_rows = [row for row in rows if row["state"] == "COMPLETE"]
    download_per_step = sorted(
        float(row["download_seconds"]) / int(row["n_timesteps"])
        for row in completed_rows
        if int(row["n_timesteps"]) > 0 and row["download_seconds"] is not None
    )
    compute_per_step = sorted(
        float(row["compute_seconds"]) / int(row["n_timesteps"])
        for row in completed_rows
        if int(row["n_timesteps"]) > 0 and row["compute_seconds"] is not None
    )
    remaining_steps = sum(int(row["n_timesteps"]) for row in rows if row["state"] not in ("COMPLETE", "FAILED_FINAL"))
    usable_keys = sum(
        row["last_status"] not in ("licence_required", "authentication_failed")
        and float(row["cooldown_until"]) <= now_epoch
        for row in keys
    )
    download_workers = max(1, min(config.max_download_workers, usable_keys))
    compute_workers = max(1, config.max_compute_workers)

    def stage_estimates(samples: list[float], workers: int) -> tuple[float, float, float]:
        median = samples[len(samples) // 2]
        low = samples[max(0, int(len(samples) * 0.25) - 1)]
        high = samples[min(len(samples) - 1, int(len(samples) * 0.75))]
        return tuple(remaining_steps * value / workers for value in (median, low, high))

    if download_per_step and compute_per_step:
        download_eta = stage_estimates(download_per_step, download_workers)
        compute_eta = stage_estimates(compute_per_step, compute_workers)
        # Both stages overlap; the slower one bounds steady-state completion.
        eta, eta_low, eta_high = (
            max(download_eta[index], compute_eta[index]) for index in range(3)
        )
    elif complete and active_seconds:
        rate = complete / active_seconds
        eta = (total - complete) / rate
        eta_low, eta_high = eta * 0.7, eta * 1.5
    else:
        eta = eta_low = eta_high = None

    recent = []
    recent_downloads = []
    for row in rows:
        if row["downloaded_at"]:
            try:
                when = datetime.fromisoformat(row["downloaded_at"])
                if (now - when).total_seconds() <= 3600:
                    recent_downloads.append(row)
            except ValueError:
                pass
    for row in completed_rows:
        if row["completed_at"]:
            try:
                when = datetime.fromisoformat(row["completed_at"])
                if (now - when).total_seconds() <= 3600:
                    recent.append(row)
            except ValueError:
                pass
    recent_rate = len(recent)
    download_rate = downloaded / (active_seconds / 3600) if active_seconds > 0 else 0
    all_rate = complete / (active_seconds / 3600) if active_seconds > 0 else 0

    output = [
        f"Corrected LEC climatology | {now.isoformat(timespec='seconds')}",
        "=" * 78,
        f"TOTAL {total} | COMPLETE {complete} | COMPUTING {counts.get('COMPUTING', 0)} | "
        f"DOWNLOADING {counts.get('DOWNLOADING', 0)} | QUEUED {counts.get('DOWNLOAD_QUEUED', 0) + counts.get('COMPUTE_QUEUED', 0)} | "
        f"PENDING {counts.get('PENDING', 0)} | FAILED/RETRYING {failed_final}/{failed_retry}",
        "",
        "DOWNLOAD PROGRESS",
        f"  {downloaded}/{total} downloaded or beyond | {bytes_downloaded / 1024**3:.2f} GiB validated",
        f"  ERA5 currently staged (daily/final/.part): {staged_bytes / 1024**3:.2f} GiB",
        f"  active workers: {counts.get('DOWNLOADING', 0)} | CDS submitted/waiting: {waiting} | transferring: {transferring}",
        f"  throughput: {download_rate:.2f} downloads/active h overall; {len(recent_downloads)}/last wall-clock h",
        "",
        "COMPUTE PROGRESS",
        f"  {complete}/{total} validated complete | active workers: {counts.get('COMPUTING', 0)}",
        f"  completion rate: {all_rate:.2f} cyclones/active h overall; {recent_rate}/last wall-clock h",
        "",
        "ACTIVE TIME AND ETA",
        f"  cumulative active runtime: {duration(active_seconds)}",
        f"  estimated remaining ACTIVE runtime: {duration(eta)}",
        f"  robust uncertainty interval: {duration(eta_low)} to {duration(eta_high)}",
        f"  ETA stage capacity: {download_workers} usable download workers; {compute_workers} compute workers",
        "  (calendar completion requires continuous server operation and is intentionally not asserted)",
        "",
        "FAILURES",
        f"  retryable: {failed_retry} | final: {failed_final}",
    ]
    failures = list(conn.execute(
        "SELECT track_id,state,last_error FROM cyclones WHERE state LIKE 'FAILED%' ORDER BY updated_at DESC LIMIT 5"
    ))
    for row in failures:
        output.append(f"  {row['track_id']} {row['state']}: {row['last_error'] or 'unspecified'}")
    output.extend(["", "KEY HEALTH (values are never displayed)", "  worker   status     successes retries failures cooldown"])
    for row in keys:
        cooldown = max(0, float(row["cooldown_until"]) - now_epoch)
        output.append(
            f"  {row['key_id']:9s} {(row['last_status'] or 'unused'):10s} "
            f"{row['successes']:9d} {row['retries']:7d} {row['failures']:8d} {duration(cooldown, active=False):>8s}"
        )
    conn.close()
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()
    config = RunConfig.load(args.run_root)
    while True:
        if args.watch:
            print("\033[2J\033[H", end="")
        print(snapshot(config), flush=True)
        if not args.watch:
            return 0
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
