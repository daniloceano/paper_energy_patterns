#!/usr/bin/env python3
"""
Validate that composite_boundary_fluxes.json contains the expected
value_total and value_anomaly (north_anom / south_anom / east_anom / west_anom)
fields for flux diagnostics that have anomaly composites.

Usage:
    python scripts/web/test_composite_json_fields.py

Exits with code 0 on success, 1 on failure.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FLUXES_FILE = REPO_ROOT / "web" / "src" / "content" / "composite_boundary_fluxes.json"
DOMAIN_FILE = REPO_ROOT / "web" / "src" / "content" / "composite_domain_stats.json"

# Diagnostics that MUST have anomaly boundary fields
ANOM_FLUX_DIAGS = {"temperature-advection", "moisture-flux-divergence", "ke-advection"}
# Diagnostics that MUST have anomaly domain fields
ANOM_DOMAIN_DIAGS = ANOM_FLUX_DIAGS


def check_boundary_fluxes():
    if not FLUXES_FILE.exists():
        print(f"❌  {FLUXES_FILE.relative_to(REPO_ROOT)} not found.")
        return False

    data = json.loads(FLUXES_FILE.read_text())
    errors = []

    for entry in data:
        diag = entry.get("diagnostic_id", "")
        ep   = entry.get("ep", "")
        if diag not in ANOM_FLUX_DIAGS:
            continue
        for field in ("north_anom", "south_anom", "east_anom", "west_anom"):
            if field not in entry:
                errors.append(f"  Missing '{field}' in {diag}/{ep}")

    if errors:
        print("❌  boundary_fluxes anomaly field check FAILED:")
        for e in errors:
            print(e)
        return False

    print(f"✓  composite_boundary_fluxes.json — anomaly fields present for {ANOM_FLUX_DIAGS}")
    return True


def check_domain_stats():
    if not DOMAIN_FILE.exists():
        print(f"❌  {DOMAIN_FILE.relative_to(REPO_ROOT)} not found.")
        return False

    data = json.loads(DOMAIN_FILE.read_text())
    errors = []

    for entry in data:
        diag = entry.get("diagnostic_id", "")
        ep   = entry.get("ep", "")
        if diag not in ANOM_DOMAIN_DIAGS:
            continue
        for field in ("inside_15x15_anom", "outside_15x15_anom"):
            if field not in entry:
                errors.append(f"  Missing '{field}' in {diag}/{ep}")

    if errors:
        print("❌  domain_stats anomaly field check FAILED:")
        for e in errors:
            print(e)
        return False

    print(f"✓  composite_domain_stats.json — anomaly fields present for {ANOM_DOMAIN_DIAGS}")
    return True


if __name__ == "__main__":
    ok_flux   = check_boundary_fluxes()
    ok_domain = check_domain_stats()
    sys.exit(0 if (ok_flux and ok_domain) else 1)
