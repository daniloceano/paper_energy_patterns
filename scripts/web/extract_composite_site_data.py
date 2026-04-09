#!/usr/bin/env python3
"""
Extract composite analysis data for the web site.

This script is a SERIALIZER/INDEXER only — it does NOT recompute any science.
It reads the structured stats JSON produced by step5_update_scientific_notes.py
and catalogs composite figures produced by step4_create_figures.py, then writes
manifest files consumed by the Next.js web layer.

CANONICAL METHOD (April 2026):
  - Central timesteps only (2-3 per case)
  - All composites use the canonical method

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

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results" / "ep_structure"
# Figures are served from web/public/figures/ (committed static assets).
# copy_figures_to_web.py copies from figures/ → web/public/figures/.
FIGURES_DIR = REPO_ROOT / "web" / "public" / "figures" / "ep_structure"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

# Composite mode (set via --mode argument in main())
COMPOSITE_MODE = "central_time"  # canonical Apr 2026

# Mapping from web diagnostic id to step4 figure filenames.
# Must match DIAGNOSTIC_FIGURE_SLUGS in web/src/lib/constants.ts.
# Note: filenames will have _{mode} suffix appended for real composites
#
# NEW April 2026: Added EPALL-relative anomaly figures (anom_epall)
# These show EPx - EPALL instead of climatology-based anomalies.
DIAGNOSTIC_FIGURE_MAP = {
    "egr":                      {"real": "composite_egr.png",                "anom_epall": "composite_egr_anom_epall.png",        "diff": "composite_egr_diff.png"},
    "pv-200":                   {"real": "composite_pv200.png",          "anom": "composite_pv200_anom.png",          "anom_epall": "composite_pv200_anom_epall.png",     "diff": "composite_pv200_diff.png"},
    "pv-850":                   {"real": "composite_pv850.png",          "anom": "composite_pv850_anom.png",          "anom_epall": "composite_pv850_anom_epall.png",     "diff": "composite_pv850_diff.png"},
    "temperature-advection":    {"real": "composite_advT850.png",        "anom": "composite_advT850_anom.png",        "anom_epall": "composite_advT850_anom_epall.png",   "diff": "composite_advT850_diff.png"},
    "moisture-flux-divergence": {"real": "composite_moisture_flux.png",  "anom": "composite_moisture_flux_anom.png",  "diff": "composite_moisture_flux_diff.png"},
    "slp":                      {"real": "composite_slp.png",            "anom": "composite_slp_anom.png",            "anom_epall": "composite_slp_anom_epall.png",       "diff": "composite_slp_diff.png"},
    "rk-criterion":             {"real": "composite_rk_criterion.png",   "anom_epall": "composite_rk_criterion_anom_epall.png",                                              "diff": "composite_rk_criterion_diff.png"},
    "ke-advection":             {"real": "composite_ke_advection.png",   "anom_epall": "composite_ke_advection_anom_epall.png",                                              "diff": "composite_ke_advection_diff.png"},
    "afc":                      {"real": "composite_afc_250.png",                                                     "diff": "composite_afc_diff.png"},  # AFC uses climatology by design
    "btcr":                     {"real": "composite_btcr.png",                                                        "diff": "composite_btcr_diff.png"},  # BtCR uses climatology by design
}


def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def build_figures_manifest():
    """Catalog which step4 composite figures actually exist on disk.

    Returns a dict keyed by diagnostic_id with availability flags.
    Uses the API path format: 'figures/ep_structure/<filename>'
    
    NOTE: All composite figures (real, anomaly, diff) have mode suffix.
    The mode affects both the composite method and which climatology reference is used.
    
    NEW April 2026: Includes anom_epall (EPALL-relative anomalies) where available.
    """
    manifest = {}
    
    for diag_id, filenames in DIAGNOSTIC_FIGURE_MAP.items():
        manifest[diag_id] = {}
        
        # Add mode suffix to REAL composites
        real_base = filenames["real"].replace(".png", ".png")
        real_path = FIGURES_DIR / real_base
        manifest[diag_id]["real"] = {
            "exists": real_path.exists(),
            "api_path": f"figures/ep_structure/{real_base}",
        }
        
        # Climatology-based anomalies (legacy)
        anom_name = filenames.get("anom")
        if anom_name:
            anom_base = anom_name.replace(".png", ".png")
            anom_path = FIGURES_DIR / anom_base
            manifest[diag_id]["anom"] = {
                "exists": anom_path.exists(),
                "api_path": f"figures/ep_structure/{anom_base}",
                "anomaly_type": "climatology",
            }
        
        # EPALL-relative anomalies (new April 2026)
        anom_epall_name = filenames.get("anom_epall")
        if anom_epall_name:
            anom_epall_base = anom_epall_name.replace(".png", ".png")
            anom_epall_path = FIGURES_DIR / anom_epall_base
            manifest[diag_id]["anom_epall"] = {
                "exists": anom_epall_path.exists(),
                "api_path": f"figures/ep_structure/{anom_epall_base}",
                "anomaly_type": "EPALL-relative",
            }

        # Difference figures also get mode suffix
        diff_name = filenames.get("diff")
        if diff_name:
            diff_base = diff_name.replace(".png", ".png")
            diff_path = FIGURES_DIR / diff_base
            manifest[diag_id]["diff"] = {
                "exists": diff_path.exists(),
                "api_path": f"figures/ep_structure/{diff_base}",
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
        print(f"    Run scripts/ep_structure_analysis/step5_update_scientific_notes.py --mode {COMPOSITE_MODE} first.")
        return [], []

    data = json.loads(stats_file.read_text())
    return data.get("domain_stats", []), data.get("boundary_fluxes", [])


def main():
    parser = argparse.ArgumentParser(description="Extract composite data for web (canonical method)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("EXTRACT COMPOSITE DATA FOR WEB (serializer only)")
    print("=" * 60)
    print(f"Method: Central timesteps (canonical Apr 2026)")
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
    print(f"\n2. Reading domain stats from results/ep_structure/composite_stats.json...")
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

