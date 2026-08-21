#!/usr/bin/env python3
"""Independent progress monitor with active-runtime ETA."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from .common import RunConfig


def duration(seconds: float | None) -> str:
    if seconds is None or not math.isfinite(seconds):
        return "n/a"
    if seconds >= 86400:
        return f"{seconds / 86400:.1f} active server-days"
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
    total = len(rows)
    complete = counts.get("COMPLETE", 0)
    downloaded = sum(counts.get(state, 0) for state in ("DOWNLOADED", "COMPUTE_QUEUED", "COMPUTING", "VALIDATING", "COMPLETE"))
    failed_retry = counts.get("FAILED_RETRYABLE", 0)
    failed_final = counts.get("FAILED_FINAL", 0)
    bytes_downloaded = sum(int(row["bytes_downloaded"] or 0) for row in rows)
    active_seconds = float(meta.get("cumulative_active_runtime", 0))
    active_downloads = progress_records(config, "download")
    active_downloads = [item for item in active_downloads if item.get("status") == "requesting"]

    completed_rows = [row for row in rows if row["state"] == "COMPLETE"]
    per_step = [
        (float(row["download_seconds"] or 0) + float(row["compute_seconds"] or 0)) / int(row["n_timesteps"])
        for row in completed_rows if int(row["n_timesteps"]) > 0
    ]
    per_step.sort()
    remaining_steps = sum(int(row["n_timesteps"]) for row in rows if row["state"] not in ("COMPLETE", "FAILED_FINAL"))
    compute_workers = max(1, config.max_compute_workers)
    if per_step:
        median = per_step[len(per_step) // 2]
        low = per_step[max(0, int(len(per_step) * 0.25) - 1)]
        high = per_step[min(len(per_step) - 1, int(len(per_step) * 0.75))]
        eta = remaining_steps * median / compute_workers
        eta_low = remaining_steps * low / compute_workers
        eta_high = remaining_steps * high / compute_workers
    elif complete and active_seconds:
        rate = complete / active_seconds
        eta = (total - complete) / rate
        eta_low, eta_high = eta * 0.7, eta * 1.5
    else:
        eta = eta_low = eta_high = None

    recent = []
    for row in completed_rows:
        if row["completed_at"]:
            try:
                when = datetime.fromisoformat(row["completed_at"])
                if (now - when).total_seconds() <= 3600:
                    recent.append(row)
            except ValueError:
                pass
    recent_rate = len(recent)
    all_rate = complete / (active_seconds / 3600) if active_seconds > 0 else 0

    output = [
        f"Corrected LEC climatology | {now.isoformat(timespec='seconds')}",
        "=" * 78,
        f"TOTAL {total} | COMPLETE {complete} | COMPUTING {counts.get('COMPUTING', 0)} | "
        f"DOWNLOADING {counts.get('DOWNLOADING', 0)} | QUEUED {counts.get('DOWNLOAD_QUEUED', 0) + counts.get('COMPUTE_QUEUED', 0)} | "
        f"PENDING {counts.get('PENDING', 0)} | FAILED/RETRYING {failed_final}/{failed_retry}",
        "",
        "DOWNLOAD PROGRESS",
        f"  {downloaded}/{total} downloaded or beyond | {bytes_downloaded / 1024**3:.2f} GiB observed",
        f"  active workers: {counts.get('DOWNLOADING', 0)} | CDS requests visibly running: {len(active_downloads)}",
        "",
        "COMPUTE PROGRESS",
        f"  {complete}/{total} validated complete | active workers: {counts.get('COMPUTING', 0)}",
        f"  completion rate: {all_rate:.2f} cyclones/active h overall; {recent_rate}/last wall-clock h",
        "",
        "ACTIVE TIME AND ETA",
        f"  cumulative active runtime: {duration(active_seconds)}",
        f"  estimated remaining ACTIVE runtime: {duration(eta)}",
        f"  robust uncertainty interval: {duration(eta_low)} to {duration(eta_high)}",
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
    now_epoch = time.time()
    for row in keys:
        cooldown = max(0, float(row["cooldown_until"]) - now_epoch)
        output.append(
            f"  {row['key_id']:9s} {(row['last_status'] or 'unused'):10s} "
            f"{row['successes']:9d} {row['retries']:7d} {row['failures']:8d} {duration(cooldown):>8s}"
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

