#!/usr/bin/env python3
"""
Sync web/src/content/dynamical_composites_manifest.json against the figures
actually produced by step4b_create_dynamical_composites.py.

This script is a SERIALIZER/INDEXER only — it does NOT recompute any science.
It updates figure availability and reads sample sizes directly from the current
step-3 NetCDF outputs so the site cannot retain counts from an older run.

Scientific computation source of truth:
  scripts/ep_structure_analysis/step4b_create_dynamical_composites.py
    → figures/ep_structure/dynamical_composites/dynamical_composites_{total,anom,epall_anom}.png

Usage:
    python scripts/web/sync_dynamical_composites_manifest.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import xarray as xr

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "figures" / "ep_structure" / "dynamical_composites"
DATA_DIR = REPO_ROOT / "data" / "era5_ep_structure"
MANIFEST_PATH = REPO_ROOT / "web" / "src" / "content" / "dynamical_composites_manifest.json"

# Maps manifest key -> filename in FIGURES_DIR
FIGURE_FILES = {
    "total": "dynamical_composites_total.png",
    "anom": "dynamical_composites_anom.png",
    "epall_anom": "dynamical_composites_epall_anom.png",
}


def main():
    manifest = json.loads(MANIFEST_PATH.read_text())

    for key, filename in FIGURE_FILES.items():
        path = FIGURES_DIR / filename
        entry = manifest["figures"][key]
        entry["exists"] = path.exists()
        entry["api_path"] = f"figures/ep_structure/dynamical_composites/{filename}"
        status = "found" if path.exists() else "MISSING"
        print(f"  {key:12s} -> {entry['api_path']}  [{status}]")

    composite_paths = {
        ep: DATA_DIR / f"precomputed_composites_{ep}.nc"
        for ep in ("ep1", "ep2", "ep3", "epall")
    }
    missing = [path for path in composite_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "cannot refresh dynamical-composite metadata; missing: "
            + ", ".join(str(path.relative_to(REPO_ROOT)) for path in missing)
        )

    metadata = manifest.setdefault("metadata", {})
    for ep, path in composite_paths.items():
        with xr.open_dataset(path) as dataset:
            metadata[f"n_{ep}"] = int(dataset.attrs["n_cases"])
            metadata["composite_method"] = dataset.attrs.get(
                "composite_mode", "central_time"
            )
    newest_mtime = max(path.stat().st_mtime for path in composite_paths.values())
    metadata["generated_at"] = datetime.fromtimestamp(
        newest_mtime, tz=timezone.utc
    ).date().isoformat()

    manifest["figures"]["epall_anom"]["rows"][2] = (
        "Row 3: AFC − EPALL (shading) + 250 hPa anomaly wind + total RK "
        "sign-reversal hatching + KE-adv − EPALL contours"
    )

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\n✓ {MANIFEST_PATH.relative_to(REPO_ROOT)} updated")


if __name__ == "__main__":
    main()
