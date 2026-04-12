#!/usr/bin/env python3
"""
Extract composite analysis data for the web site.

This script is a SERIALIZER/INDEXER only — it does NOT recompute any science.
It reads the structured stats JSON produced by step5_update_scientific_notes.py
and catalogs composite figures produced by step4_create_figures.py, then writes
manifest files consumed by the Next.js web layer.

CANONICAL METHOD (April 2026):
  - Central timesteps only (2-3 per case)
  - EP1, EP2, EP3, EPALL composites
  - EPALL-relative anomalies: EP1−EPALL | EP2−EPALL | EP3−EPALL (1×3 panel)
  - AFC and BtCR use climatology decomposition by design (no EPALL-relative anomaly figure)

Scientific computation source of truth: scripts/ep_structure_analysis/
  - step4_create_figures.py  → figures/ep_structure/composite_*.png
  - step5_update_scientific_notes.py → results/ep_structure/composite_stats.json

Data flow:
  1. Run step4  → generates figures/ep_structure/composite_*.png
  2. Run step5  → generates results/ep_structure/composite_stats.json
  3. Run THIS   → generates web/src/content/composite_*.json  (web manifests)
  4. Run copy_figures_to_web.py → copies figures/ → web/public/figures/ for serving

  Note: step 3 checks figures/ep_structure/ (pipeline output) for existence flags.
  Step 4 (copy) can be run before or after step 3 — both are independent.

Usage:
    python scripts/web/extract_composite_site_data.py

Outputs:
    web/src/content/composite_domain_stats.json
    web/src/content/composite_boundary_fluxes.json
    web/src/content/composite_figures_manifest.json

Manifest schema (composite_figures_manifest.json):
  {
    "<diag_id>": {
      "real":       { "exists": bool, "api_path": str },  # 2×2 panel: EP1/EP2/EP3/EPALL
      "anom_clim":  { "exists": bool, "api_path": str },  # climatology-relative anomaly (X' = X − X̄_clim)
                                                           # omitted if no climatology anomaly figure exists
      "anom_epall": { "exists": bool, "api_path": str },  # 1×3 panel: EP1−EPALL | EP2−EPALL | EP3−EPALL
                                                           # omitted if no EPALL-relative figure exists
      "diff":       { "exists": bool, "api_path": str }   # legacy EP1−EP2 single-panel diff
    }
  }
"""

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results" / "ep_structure"
# Check figures in the pipeline output directory (source of truth).
# copy_figures_to_web.py copies from here → web/public/figures/ for deployment.
# Checking the source dir means exists=True whenever step4 has generated the figure,
# regardless of whether copy_figures_to_web.py has been run yet.
FIGURES_DIR = REPO_ROOT / "figures" / "ep_structure"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

# Mapping from web diagnostic id to step4 figure filenames.
# Must match DIAGNOSTIC_FIGURE_SLUGS in web/src/lib/constants.ts.
#
# Schema: each entry has:
#   "real"       → 2×2 panel figure (EP1/EP2/EP3/EPALL), always present
#   "anom_clim"  → climatology-relative anomaly figure (EP1/EP2/EP3/EPALL or EP1/EP2/EP3)
#                  X' = X − X̄_clim (departure from 1991–2020 ERA5 monthly climatology)
#   "anom_epall" → 1×3 panel figure (EP1−EPALL | EP2−EPALL | EP3−EPALL), only where available
#   "diff"       → legacy EP1−EP2 single-panel difference figure
#
# No climatology anomaly for:
#   - rk-criterion (background-flow diagnostic; shown as total field only)
#   - afc (already is a climatology anomaly by construction — Orlanski & Katzfey 1991)
#   - btcr (uses climatological decomposition by construction — Rivière 2006)
# Note: egr clim-anom (composite_egr_anom.png) requires era5_climatology_egr.nc (500/850 hPa u,v,T,z);
#   will show exists=False until that file is downloaded and step3/step4 re-run.
#
# No EPALL-relative anomaly for:
#   - moisture-flux-divergence (no anom_epall figure; div_q_975_minus_epall is in composites
#     but no separate EPALL-relative figure is generated for this diagnostic)
#   - btcr (uses climatological decomposition by construction — Rivière 2006)
#   - rk-criterion (β − ∂²ū/∂y² is a background-flow diagnostic; shown as total field only)
# Note: afc NOW has anom_epall = AFC_EPx − AFC_EPALL (added April 2026)
DIAGNOSTIC_FIGURE_MAP = {
    "egr":                      {"real": "composite_egr.png",         "anom_clim": "composite_egr_anom.png",                 "anom_epall": "composite_egr_anom_epall.png",          "diff": "composite_egr_diff.png"},
    "pv-200":                   {"real": "composite_pv200.png",        "anom_clim": "composite_pv200_anom.png",               "anom_epall": "composite_pv200_anom_epall.png",        "diff": "composite_pv200_diff.png"},
    "pv-850":                   {"real": "composite_pv850.png",        "anom_clim": "composite_pv850_anom.png",               "anom_epall": "composite_pv850_anom_epall.png",        "diff": "composite_pv850_diff.png"},
    "temperature-advection":    {"real": "composite_advT850.png",      "anom_clim": "composite_advT850_anom.png",             "anom_epall": "composite_advT850_anom_epall.png",      "diff": "composite_advT850_diff.png"},
    "moisture-flux-divergence": {"real": "composite_moisture_flux.png","anom_clim": "composite_moisture_flux_anom.png",                                                               "diff": "composite_moisture_flux_diff.png"},
    "slp":                      {"real": "composite_slp.png",          "anom_clim": "composite_slp_anom.png",                 "anom_epall": "composite_slp_anom_epall.png",          "diff": "composite_slp_diff.png"},
    "rk-criterion":             {"real": "composite_rk_criterion.png",                                                                                                                 "diff": "composite_rk_criterion_diff.png"},
    # NOTE: rk-criterion has no anom_clim or anom_epall — RK is shown as total composite only.
    "ke-advection":             {"real": "composite_ke_advection.png", "anom_clim": "composite_ke_advection_anom.png",        "anom_epall": "composite_ke_advection_anom_epall.png", "diff": "composite_ke_advection_diff.png"},
    "afc":                      {"real": "composite_afc_250.png",                                                      "anom_epall": "composite_afc_anom_epall.png",          "diff": "composite_afc_diff.png"},
    # NOTE: afc has no anom_clim (it is already a clim anomaly by construction — Orlanski & Katzfey 1991).
    # anom_epall = AFC_EPx − AFC_EPALL: isolates per-pattern divergence from the typical cyclone's AFC.
    "btcr":                     {"real": "composite_btcr.png",                                                                                                                         "diff": "composite_btcr_diff.png"},
    # NOTE: btcr has no anom_clim (same reason as afc) and no anom_epall.
}


def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def build_figures_manifest():
    """Catalog which step4 composite figures actually exist on disk.

    Returns a dict keyed by diagnostic_id with availability flags.
    Uses the API path format: 'figures/ep_structure/<filename>'

    Schema per diagnostic:
      "real"       → 2×2 panel (EP1/EP2/EP3/EPALL total field composite)
      "anom_clim"  → climatology-relative anomaly (X' = X − X̄_clim), only where it exists
      "anom_epall" → 1×3 panel (EP1−EPALL | EP2−EPALL | EP3−EPALL), only where it exists
      "diff"       → legacy EP1−EP2 single-panel difference (kept for backward compat)
    """
    manifest = {}

    for diag_id, filenames in DIAGNOSTIC_FIGURE_MAP.items():
        manifest[diag_id] = {}

        # Total field composite (2×2 panel: EP1/EP2/EP3/EPALL)
        real_base = filenames["real"]
        real_path = FIGURES_DIR / real_base
        manifest[diag_id]["real"] = {
            "exists": real_path.exists(),
            "api_path": f"figures/ep_structure/{real_base}",
        }

        # Climatology-relative anomaly figure (X' = X − X̄_clim, 1991–2020)
        anom_clim_name = filenames.get("anom_clim")
        if anom_clim_name:
            anom_clim_path = FIGURES_DIR / anom_clim_name
            manifest[diag_id]["anom_clim"] = {
                "exists": anom_clim_path.exists(),
                "api_path": f"figures/ep_structure/{anom_clim_name}",
            }

        # EPALL-relative anomaly figure (1×3 panel: EP1−EPALL | EP2−EPALL | EP3−EPALL)
        anom_epall_name = filenames.get("anom_epall")
        if anom_epall_name:
            anom_epall_path = FIGURES_DIR / anom_epall_name
            manifest[diag_id]["anom_epall"] = {
                "exists": anom_epall_path.exists(),
                "api_path": f"figures/ep_structure/{anom_epall_name}",
            }

        # Legacy EP1−EP2 difference figure (kept for backward compatibility)
        diff_name = filenames.get("diff")
        if diff_name:
            diff_path = FIGURES_DIR / diff_name
            manifest[diag_id]["diff"] = {
                "exists": diff_path.exists(),
                "api_path": f"figures/ep_structure/{diff_name}",
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
        print(f"    Run scripts/ep_structure_analysis/step5_update_scientific_notes.py first.")
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

