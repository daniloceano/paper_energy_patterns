#!/usr/bin/env python3
"""Safely discover which inventoried CDS accounts accepted the ERA5 licence."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import time
from pathlib import Path

import cdsapi

# Allow running this file directly, not only as `python -m`.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_climatology_rerun.common import (
    RunConfig,
    StateDB,
    isolated_cds_home,
    load_keys,
    utc_now,
)


REQUEST = {
    "product_type": "reanalysis",
    "format": "netcdf",
    "variable": ["temperature"],
    "pressure_level": ["1000"],
    "year": "1979",
    "month": "01",
    "day": "01",
    "time": ["00:00"],
    "area": [-39, -50, -40, -49],
}


def set_health(db: StateDB, key_id: str, status: str, cooldown_until: float) -> None:
    db.conn.execute(
        """UPDATE key_health SET last_status=?,cooldown_until=?,updated_at=?
           WHERE key_id=?""",
        (status, cooldown_until, utc_now(), key_id),
    )
    db.conn.commit()


def probe_key(
    config: RunConfig, key: str, key_id: str, attempts: int = 3
) -> tuple[str, float]:
    """Classify one account. Licence and authentication verdicts are decided on
    the first answer; anything else is retried, because a flaky CDS would
    otherwise demote a perfectly good account."""
    for attempt in range(1, attempts + 1):
        try:
            with isolated_cds_home(config, key, key_id) as home:
                os.environ["HOME"] = str(home)
                # Both verdicts arrive with the submission response, so neither
                # wait for the job nor pass a target: waiting for real data made
                # one sweep take hours and competed with production for CDS
                # capacity. Release the queued job rather than leaving it for
                # the CDS workers to run.
                client = cdsapi.Client(
                    timeout=60, retry_max=0, quiet=True, wait_until_complete=False
                )
                submitted = client.retrieve("reanalysis-era5-pressure-levels", REQUEST)
                with contextlib.suppress(Exception):
                    submitted.delete()
            return "healthy", 0
        except Exception as exc:
            text = str(exc).lower()
            if "licence" in text or "license" in text:
                # Do not retry every scheduler restart. Re-run this preflight
                # after account owners accept the official CDS licence.
                return "licence_required", time.time() + 30 * 86400
            if any(value in text for value in ("401", "403", "unauthorized", "forbidden")):
                return "authentication_failed", time.time() + 30 * 86400
            if attempt < attempts:
                time.sleep(2 * attempt)
    return "preflight_transient_failure", time.time() + 1800


def run(config: RunConfig) -> list[str]:
    keys = load_keys(Path(config.keys_file))
    db = StateDB(config.db)
    db.init_keys(len(keys))
    authorized: list[str] = []
    old_home = os.environ.get("HOME")
    try:
        for index, key in enumerate(keys, 1):
            key_id = f"key-{index:03d}"
            status, cooldown = probe_key(config, key, key_id)
            if status == "healthy":
                authorized.append(key_id)
            set_health(db, key_id, status, cooldown)
            print(f"{key_id} {'authorized' if status == 'healthy' else status}", flush=True)
    finally:
        if old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old_home
        db.set_meta("key_preflight_at", utc_now())
        db.set_meta("authorized_key_count", len(authorized))
        db.event("download", "KEY_PREFLIGHT", f"authorized={len(authorized)}/{len(keys)}")
        db.close()
    return authorized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    config = RunConfig.load(args.run_root)
    authorized = run(config)
    print(f"authorized keys: {len(authorized)}")
    return 0 if authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
