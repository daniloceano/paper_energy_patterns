#!/usr/bin/env python3
"""
Sync web/src/content/dynamical_composites_manifest.json against the figures
actually produced by step4b_create_dynamical_composites.py.

This script is a SERIALIZER/INDEXER only — it does NOT recompute any science
and does NOT touch the hand-curated copy (title/columns/rows/metadata) in the
manifest. It only updates "exists" and "api_path" for each figure entry so the
manifest can never silently drift from the figures/ directory layout again.

Scientific computation source of truth:
  scripts/ep_structure_analysis/step4b_create_dynamical_composites.py
    → figures/ep_structure/dynamical_composites/dynamical_composites_{total,anom,epall_anom}.png

Usage:
    python scripts/web/sync_dynamical_composites_manifest.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "figures" / "ep_structure" / "dynamical_composites"
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

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\n✓ {MANIFEST_PATH.relative_to(REPO_ROOT)} updated")


if __name__ == "__main__":
    main()
