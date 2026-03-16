#!/usr/bin/env python3
"""
Extract composite analysis data for the web site.

This script is a SERIALIZER/INDEXER only — it does NOT recompute any science.
It reads the structured stats JSON produced by step5_update_scientific_notes.py
and catalogs composite figures produced by step4_create_figures.py, then writes
manifest files consumed by the Next.js web layer.

Scientific computation source of truth: scripts/ep_structure_analysis/
  - step4_create_figures.py  → figures/ep_structure/composite_*.png
  - step5_update_scientific_notes.py → results/ep_structure/composite_stats.json

Data flow:
  1. Run step4  → generates figures/ep_structure/composite_*.png
  2. Run step5  → generates results/ep_structure/composite_stats.json
  3. Run THIS   → generates web/src/content/composite_*.json  (web manifests)

Usage:
    python scripts/web/extract_composite_site_data.py

Outputs:
    web/src/content/composite_domain_stats.json
    web/src/content/composite_boundary_fluxes.json
    web/src/content/composite_figures_manifest.json
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results" / "ep_structure"
# Figures are served from web/public/figures/ (committed static assets).
# copy_figures_to_web.py copies from figures/ → web/public/figures/.
FIGURES_DIR = REPO_ROOT / "web" / "public" / "figures" / "ep_structure"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

# Mapping from web diagnostic id to step4 figure filenames.
# Must match DIAGNOSTIC_FIGURE_SLUGS in web/src/lib/constants.ts.
DIAGNOSTIC_FIGURE_MAP = {
    "egr":                      {"real": "composite_egr.png"},
    "pv-200":                   {"real": "composite_pv200.png",          "anom": "composite_pv200_anom.png"},
    "pv-850":                   {"real": "composite_pv850.png",          "anom": "composite_pv850_anom.png"},
    "temperature-advection":    {"real": "composite_advT850.png",        "anom": "composite_advT850_anom.png"},
    "moisture-flux-divergence": {"real": "composite_moisture_flux.png",  "anom": "composite_moisture_flux_anom.png"},
    "slp":                      {"real": "composite_slp.png",            "anom": "composite_slp_anom.png"},
    "rk-criterion":             {"real": "composite_rk_criterion.png"},
    "ke-advection":             {"real": "composite_ke_advection.png",   "anom": "composite_ke_advection_anom.png"},
    "afc":                      {"real": "composite_afc_250.png"},
    "btcr":                     {"real": "composite_btcr.png"},
}


def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def build_figures_manifest():
    """Catalog which step4 composite figures actually exist on disk.

    Returns a dict keyed by diagnostic_id with availability flags.
    Uses the API path format: 'figures/ep_structure/<filename>'
    """
    manifest = {}
    for diag_id, filenames in DIAGNOSTIC_FIGURE_MAP.items():
        real_path = FIGURES_DIR / filenames["real"]
        anom_name = filenames.get("anom")
        anom_path = FIGURES_DIR / anom_name if anom_name else None

        manifest[diag_id] = {
            "real": {
                "exists": real_path.exists(),
                "api_path": f"figures/ep_structure/{filenames['real']}",
            },
        }
        if anom_name:
            manifest[diag_id]["anom"] = {
                "exists": anom_path.exists() if anom_path else False,
                "api_path": f"figures/ep_structure/{anom_name}",
            }

    return manifest


def load_domain_stats():
    """Read domain stats from step5 JSON output.

    Domain definitions (from step5_update_scientific_notes.py):
      - inside_15x15  (lec15):  mean within central ±7.5° LEC subdomain
      - outside_15x15 (full30): mean over the full 30×30° domain
        NOTE: 'outside' = full domain context (not a ring); the LEC subdomain
        is a subset of full30. This distinction is documented in step5.
      - inside_15x15_anom / outside_15x15_anom: same regions for anomaly composites
    """
    stats_file = RESULTS_DIR / "composite_stats.json"
    if not stats_file.exists():
        print(f"  ⚠ {stats_file.relative_to(REPO_ROOT)} not found.")
        print("    Run scripts/ep_structure_analysis/step5_update_scientific_notes.py first.")
        return [], []

    data = json.loads(stats_file.read_text())
    return data.get("domain_stats", []), data.get("boundary_fluxes", [])


def main():
    print("=" * 60)
    print("EXTRACT COMPOSITE DATA FOR WEB (serializer only)")
    print("=" * 60)
    ensure_output_dir()

    # 1. Catalog figures
    print("\n1. Cataloging composite figures from figures/ep_structure/...")
    figures = build_figures_manifest()
    total = sum(1 for d in figures.values() for f in d.values() if f.get("exists"))
    print(f"   Found {total} composite figures on disk")

    fig_path = WEB_CONTENT / "composite_figures_manifest.json"
    fig_path.write_text(json.dumps(figures, indent=2))
    print(f"   ✓ {fig_path.relative_to(REPO_ROOT)}")

    # 2. Load stats from step5 JSON
    print("\n2. Reading domain stats from results/ep_structure/composite_stats.json...")
    domain_stats, boundary_fluxes = load_domain_stats()

    if not domain_stats:
        print("   ⚠ No stats available — writing empty manifests")
        domain_stats, boundary_fluxes = [], []
    else:
        print(f"   Found {len(domain_stats)} domain stats entries")
        print(f"   Found {len(boundary_fluxes)} boundary flux entries")

    # 3. Write web manifests
    stats_path = WEB_CONTENT / "composite_domain_stats.json"
    stats_path.write_text(json.dumps(domain_stats, indent=2))
    print(f"   ✓ {stats_path.relative_to(REPO_ROOT)}")

    fluxes_path = WEB_CONTENT / "composite_boundary_fluxes.json"
    fluxes_path.write_text(json.dumps(boundary_fluxes, indent=2))
    print(f"   ✓ {fluxes_path.relative_to(REPO_ROOT)}")

    print("\n" + "=" * 60)
    print("✓ DONE — web manifests updated")
    print("=" * 60)


if __name__ == "__main__":
    main()

