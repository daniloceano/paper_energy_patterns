#!/usr/bin/env python3
"""
Delete every object under a prefix in a Supabase Storage bucket.

Direct `DELETE FROM storage.objects` is blocked by Supabase (a protect_delete
trigger guards against orphaning the underlying files), so removal has to go
through the Storage API. This script walks the prefix recursively, because the
list endpoint only returns one directory level at a time, and then deletes the
objects it found in batches.

Credentials are read from web/.env.local (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).

Usage:
    python scripts/web/delete_supabase_prefix.py --bucket figures \
        --prefix cyclone_explorer/ --dry-run
    python scripts/web/delete_supabase_prefix.py --bucket figures \
        --prefix cyclone_explorer/ --yes

Author: Danilo Couto de Souza
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / "web" / ".env.local"

LIST_PAGE = 1000       # objects per list call
DELETE_BATCH = 500     # object paths per delete call


def load_env() -> tuple[str, str]:
    """Read SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from web/.env.local."""
    if not ENV_FILE.exists():
        sys.exit(f"Missing {ENV_FILE}")
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Z_]+)\s*=\s*(.*)\s*$", line)
        if m:
            env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    url = env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        sys.exit("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not found in web/.env.local")
    return url.rstrip("/"), key


def api(url: str, key: str, method: str, path: str, payload: dict) -> list | dict:
    req = urllib.request.Request(
        f"{url}{path}",
        data=json.dumps(payload).encode(),
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or "[]")


def walk(url: str, key: str, bucket: str, prefix: str) -> list[str]:
    """Collect every object path under *prefix* (depth-first)."""
    found: list[str] = []
    stack = [prefix]
    while stack:
        cur = stack.pop()
        offset = 0
        while True:
            page = api(url, key, "POST", f"/storage/v1/object/list/{bucket}",
                       {"prefix": cur, "limit": LIST_PAGE, "offset": offset,
                        "sortBy": {"column": "name", "order": "asc"}})
            if not page:
                break
            for it in page:
                name = it.get("name")
                if not name:
                    continue
                full = f"{cur}{name}"
                # Supabase marks real objects with an id; folders come back null.
                if it.get("id"):
                    found.append(full)
                else:
                    stack.append(f"{full}/")
            if len(page) < LIST_PAGE:
                break
            offset += LIST_PAGE
        print(f"  walked {cur}  (total objects so far: {len(found):,})", flush=True)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--prefix", required=True, help="e.g. cyclone_explorer/")
    ap.add_argument("--yes", action="store_true", help="actually delete")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    url, key = load_env()
    print(f"Bucket {a.bucket!r}, prefix {a.prefix!r}\nListing…", flush=True)
    objects = walk(url, key, a.bucket, a.prefix)
    print(f"\nFound {len(objects):,} objects under {a.prefix!r}")

    if not objects:
        print("Nothing to do.")
        return 0
    if a.dry_run or not a.yes:
        for o in objects[:10]:
            print("   ", o)
        if len(objects) > 10:
            print(f"    … and {len(objects) - 10:,} more")
        print("\nDry run — pass --yes to delete.")
        return 0

    deleted = 0
    for i in range(0, len(objects), DELETE_BATCH):
        batch = objects[i:i + DELETE_BATCH]
        api(url, key, "DELETE", f"/storage/v1/object/{a.bucket}", {"prefixes": batch})
        deleted += len(batch)
        print(f"  deleted {deleted:,}/{len(objects):,}", flush=True)

    print(f"\nDone — removed {deleted:,} objects under {a.prefix!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
