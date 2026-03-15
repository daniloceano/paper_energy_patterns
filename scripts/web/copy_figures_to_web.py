#!/usr/bin/env python3
"""
Copy figures needed by the web site into web/public/figures/.

This script is part of the web layer — it does NOT generate figures.
It takes outputs already produced by the scientific pipeline and makes
them available as Next.js static assets so the site works on Vercel
without any external storage service.

Serving strategy:
  figures/ (repo root)      → scientific pipeline output (gitignored)
  web/public/figures/       → web app static assets (committed, served at /figures/...)

The Next.js app serves web/public/ at the root URL, so:
  web/public/figures/cluster/pca_variance_wide.png → https://site.vercel.app/figures/cluster/pca_variance_wide.png

Usage:
  python scripts/web/copy_figures_to_web.py           # copy all needed figures
  python scripts/web/copy_figures_to_web.py --dry-run  # preview without copying

Run this whenever figures are regenerated, then commit web/public/figures/:
  python scripts/web/copy_figures_to_web.py
  git add web/public/figures/
  git commit -m "Update web figures"
  git push   # Vercel auto-deploys

Author: Danilo Couto de Souza
"""

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_SRC = REPO_ROOT / "figures"
FIGURES_DST = REPO_ROOT / "web" / "public" / "figures"

# Figures the web site actually uses.
# Keys are target paths relative to web/public/figures/.
# Values are source paths relative to figures/ (repo root).
# If source == target, just list the path once.
FIGURES_MANIFEST = {
    # --- Cluster analysis ---
    "cluster/pca_variance_wide.png":      "cluster/pca_variance_wide.png",
    "cluster/pca_loadings_wide.png":      "cluster/pca_loadings_wide.png",
    "cluster/pca_correlation_wide.png":   "cluster/pca_correlation_wide.png",
    "cluster/pca_scatter_wide.png":       "cluster/pca_scatter_wide.png",
    "cluster/optimal_k_analysis.png":     "cluster/optimal_k_analysis.png",
    "cluster/lps_conversion_default.png": "cluster/lps_conversion_default.png",
    "cluster/lps_conversion_zoom.png":    "cluster/lps_conversion_zoom.png",
    "cluster/lps_imports_default.png":    "cluster/lps_imports_default.png",
    "cluster/lps_imports_zoom.png":       "cluster/lps_imports_zoom.png",

    # --- Main / publication figures ---
    "main/4_lps_combined.png":                    "main/4_lps_combined.png",
    "main/5_ep_intensity_seasonality_trends.png":  "main/5_ep_intensity_seasonality_trends.png",
    "main/6_ep_genesis_density_kde.png":           "main/6_ep_genesis_density_kde.png",
    "main/7_ep1_instability_composite_4x3.png":    "main/7_ep1_instability_composite_4x3.png",
    "main/S1_pca_clustering_validation.png":       "main/S1_pca_clustering_validation.png",
    "main/S2_selected_tracks.png":                 "main/S2_selected_tracks.png",
    "main/S3_vertical_levels.png":                 "main/S3_vertical_levels.png",
    "main/1_tracks_genesis_frequency.png":         "main/1_tracks_genesis_frequency.png",
    "main/2_20070643_lps_track_publication.png":   "main/2_20070643_lps_track_publication.png",
    "main/3_phase_density_2x2.png":                "main/3_phase_density_2x2.png",

    # --- EP Structure composite figures (step4_create_figures.py output) ---
    "ep_structure/composite_egr.png":                    "ep_structure/composite_egr.png",
    "ep_structure/composite_pv200.png":                  "ep_structure/composite_pv200.png",
    "ep_structure/composite_pv200_anom.png":             "ep_structure/composite_pv200_anom.png",
    "ep_structure/composite_pv850.png":                  "ep_structure/composite_pv850.png",
    "ep_structure/composite_pv850_anom.png":             "ep_structure/composite_pv850_anom.png",
    "ep_structure/composite_advT850.png":                "ep_structure/composite_advT850.png",
    "ep_structure/composite_advT850_anom.png":           "ep_structure/composite_advT850_anom.png",
    "ep_structure/composite_moisture_flux.png":          "ep_structure/composite_moisture_flux.png",
    "ep_structure/composite_moisture_flux_anom.png":     "ep_structure/composite_moisture_flux_anom.png",
    "ep_structure/composite_slp.png":                    "ep_structure/composite_slp.png",
    "ep_structure/composite_slp_anom.png":               "ep_structure/composite_slp_anom.png",
    "ep_structure/composite_rk_criterion.png":           "ep_structure/composite_rk_criterion.png",
    "ep_structure/composite_ke_advection.png":           "ep_structure/composite_ke_advection.png",
    "ep_structure/composite_ke_advection_anom.png":      "ep_structure/composite_ke_advection_anom.png",
    "ep_structure/composite_afc_250.png":                "ep_structure/composite_afc_250.png",
    "ep_structure/composite_wind250.png":                "ep_structure/composite_wind250.png",
    "ep_structure/composite_wind250_anom.png":           "ep_structure/composite_wind250_anom.png",
}


def copy_figures(dry_run: bool = False) -> tuple[int, int, int]:
    """Copy figures to web/public/figures/.

    Returns (copied, skipped_missing, already_up_to_date).
    """
    copied = missing = up_to_date = 0

    for dst_rel, src_rel in FIGURES_MANIFEST.items():
        src = FIGURES_SRC / src_rel
        dst = FIGURES_DST / dst_rel

        if not src.exists():
            print(f"  ⚠  MISSING   {src_rel}")
            missing += 1
            continue

        # Check if already up-to-date (same size + mtime)
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            up_to_date += 1
            continue

        if dry_run:
            print(f"  [dry-run]   {dst_rel}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✓  {dst_rel}")
        copied += 1

    return copied, missing, up_to_date


def main():
    parser = argparse.ArgumentParser(
        description="Copy figures to web/public/figures/ for Vercel deployment."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without copying")
    args = parser.parse_args()

    print("=" * 60)
    print("COPY FIGURES TO WEB PUBLIC ASSETS")
    print("=" * 60)
    print(f"  Source : {FIGURES_SRC.relative_to(REPO_ROOT)}")
    print(f"  Target : {FIGURES_DST.relative_to(REPO_ROOT)}")
    print(f"  Mode   : {'dry-run' if args.dry_run else 'copy'}")
    print()

    if not args.dry_run:
        FIGURES_DST.mkdir(parents=True, exist_ok=True)

    copied, missing, up_to_date = copy_figures(dry_run=args.dry_run)

    print()
    print(f"  ✓ Copied        : {copied}")
    print(f"  – Up-to-date    : {up_to_date}")
    print(f"  ⚠ Source missing: {missing}")

    if missing > 0:
        print()
        print("  Missing figures will show as placeholders in the site.")
        print("  Run the scientific pipeline to generate them:")
        print("    python scripts/ep_structure_analysis/step4_create_figures.py")
        print("    python scripts/cluster_analysis_energy_patterns/run_pipeline.py")

    if not args.dry_run and copied > 0:
        print()
        print("  Next steps:")
        print("    git add web/public/figures/")
        print("    git commit -m 'Update web figures'")
        print("    git push   # Vercel auto-deploys")

    print("=" * 60)


if __name__ == "__main__":
    main()
