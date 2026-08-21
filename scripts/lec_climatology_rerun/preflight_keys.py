#!/usr/bin/env python3
"""Safely discover which inventoried CDS accounts accepted the ERA5 licence."""

from __future__ import annotations

import argparse
import os
import tempfile
import time
from pathlib import Path

import cdsapi

from .common import RunConfig, StateDB, isolated_cds_home, load_keys, utc_now


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


def run(config: RunConfig) -> list[str]:
    keys = load_keys(Path(config.keys_file))
    db = StateDB(config.db)
    db.init_keys(len(keys))
    authorized: list[str] = []
    old_home = os.environ.get("HOME")
    try:
        for index, key in enumerate(keys, 1):
            key_id = f"key-{index:03d}"
            target = Path(tempfile.gettempdir()) / f"cds_licence_preflight_{index}.nc"
            target.unlink(missing_ok=True)
            try:
                with isolated_cds_home(config, key, key_id) as home:
                    os.environ["HOME"] = str(home)
                    cdsapi.Client(timeout=60, retry_max=0, quiet=True).retrieve(
                        "reanalysis-era5-pressure-levels", REQUEST, str(target)
                    )
                authorized.append(key_id)
                set_health(db, key_id, "healthy", 0)
                print(f"{key_id} authorized", flush=True)
            except Exception as exc:
                text = str(exc).lower()
                if "licence" in text or "license" in text:
                    status = "licence_required"
                    # Do not retry every scheduler restart. Re-run this preflight
                    # after account owners accept the official CDS licence.
                    cooldown = time.time() + 30 * 86400
                elif any(value in text for value in ("401", "403", "unauthorized", "forbidden")):
                    status = "authentication_failed"
                    cooldown = time.time() + 30 * 86400
                else:
                    status = "preflight_transient_failure"
                    cooldown = time.time() + 1800
                set_health(db, key_id, status, cooldown)
                print(f"{key_id} {status}", flush=True)
            finally:
                target.unlink(missing_ok=True)
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
