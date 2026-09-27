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
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"}

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
    # Filenames describe content only; publication order belongs in the paper.
    "main/tracks_genesis_frequency.png":              "main/tracks_genesis_frequency.png",
    "main/cyclone_20070643_lps_track.png":             "main/cyclone_20070643_lps_track.png",
    "main/phase_density.png":                          "main/phase_density.png",
    "main/lps_combined.png":                           "main/lps_combined.png",
    "main/vertical_levels.png":                        "main/vertical_levels.png",
    "main/ep_intensity_seasonality_trends.png":        "main/ep_intensity_seasonality_trends.png",
    "main/ep_genesis_density_kde.png":                 "main/ep_genesis_density_kde.png",
    "main/dynamical_composites_epall_relative.png":    "main/dynamical_composites_epall_relative.png",
    "main/pearson_epall_by_field_type.png":            "main/pearson_epall_by_field_type.png",
    "main/pca_clustering_validation.png":              "main/pca_clustering_validation.png",
    "main/pairwise_effectsize_lec_terms.png":          "main/pairwise_effectsize_lec_terms.png",
    "main/ck_subterms_vertical_profiles.png":          "main/ck_subterms_vertical_profiles.png",
    "main/pairwise_effectsize_composite_scalars.png":  "main/pairwise_effectsize_composite_scalars.png",

    # --- CPS analysis (cyclone phase space) ---
    # The 745-figure case gallery under figures/cps_analysis/cases/ is NOT copied:
    # it is a validation aid for the authors, not site content.
    "cps/fig0_cps_reference.png":                       "cps_analysis/fig0_cps_reference.png",
    "cps/fig1_phase_composition.png":                   "cps_analysis/fig1_phase_composition.png",
    "cps/fig2_phase_space.png":                         "cps_analysis/fig2_phase_space.png",
    "cps/fig3_transitions.png":                         "cps_analysis/fig3_transitions.png",
    "cps/fig4_tropical_runs.png":                       "cps_analysis/fig4_tropical_runs.png",
    "cps/fig5_phase_space_by_ep.png":                   "cps_analysis/fig5_phase_space_by_ep.png",
    "cps/fig6_phase_space_by_ep_single_state_sc.png":   "cps_analysis/fig6_phase_space_by_ep_single_state_sc.png",
    "cps/fig7_transition_trajectories.png":             "cps_analysis/fig7_transition_trajectories.png",
    "cps/fig8_ep_relative_subtropical.png":             "cps_analysis/fig8_ep_relative_subtropical.png",

    # NOTE: EP Structure composite figures are copied via copy_ep_structure_tree()
    # (canonical figures now have clean naming without mode suffixes)
}


def copy_figures(
    dry_run: bool = False, only: set[str] | None = None
) -> tuple[int, int, int]:
    """Copy figures to web/public/figures/.

    Returns (copied, skipped_missing, already_up_to_date).
    """
    copied = missing = up_to_date = 0

    for dst_rel, src_rel in FIGURES_MANIFEST.items():
        if only is not None and dst_rel not in only:
            continue
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


def copy_cyclone_explorer_tree(dry_run: bool = False) -> tuple[int, int]:
    """Copy all cyclone explorer assets recursively, preserving folder structure."""
    src_root = FIGURES_SRC / "cyclone_explorer"
    dst_root = FIGURES_DST / "cyclone_explorer"

    if not src_root.exists():
        print("  ⚠  MISSING   cyclone_explorer/ directory in figures/")
        return 0, 0

    copied = 0
    up_to_date = 0
    for src in sorted(src_root.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        rel = src.relative_to(src_root)
        dst = dst_root / rel
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            up_to_date += 1
            continue

        if dry_run:
            print(f"  [dry-run]   cyclone_explorer/{rel}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✓  cyclone_explorer/{rel}")
        copied += 1

    return copied, up_to_date


def copy_ep_structure_tree(dry_run: bool = False) -> tuple[int, int]:
    """Copy all EP structure composite figures (canonical clean naming).

    Since composite figures now use clean naming without mode suffixes,
    we copy them dynamically rather than listing each one explicitly.
    Recurses into subdirectories (e.g. dynamical_composites/) so figures
    generated by step4b_create_dynamical_composites.py are included too.
    """
    src_root = FIGURES_SRC / "ep_structure"
    dst_root = FIGURES_DST / "ep_structure"

    if not src_root.exists():
        return 0, 0

    matches = set(src_root.rglob("composite_*.png")) | set(src_root.rglob("dynamical_composites_*.png"))

    copied = 0
    up_to_date = 0
    for src in sorted(matches):
        if not src.is_file():
            continue

        rel = src.relative_to(src_root)
        dst = dst_root / rel
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            up_to_date += 1
            continue

        if dry_run:
            print(f"  [dry-run]   ep_structure/{rel}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✓  ep_structure/{rel}")
        copied += 1

    return copied, up_to_date


def copy_analysis_tree(name: str, dry_run: bool = False) -> tuple[int, int]:
    """Copy one complete analysis figure tree into the site's static assets."""
    src_root = FIGURES_SRC / name
    dst_root = FIGURES_DST / name

    if not src_root.exists():
        print(f"  ⚠  MISSING   {name}/ directory in figures/")
        return 0, 0

    copied = 0
    up_to_date = 0
    for src in sorted(src_root.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        dst = dst_root / src.relative_to(src_root)
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            up_to_date += 1
            continue
        if dry_run:
            print(f"  [dry-run]   {name}/{src.relative_to(src_root)}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✓  {name}/{src.relative_to(src_root)}")
        copied += 1
    return copied, up_to_date


def main():
    parser = argparse.ArgumentParser(
        description="Copy figures to web/public/figures/ for Vercel deployment."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without copying")
    parser.add_argument(
        "--only",
        action="append",
        metavar="PATH",
        help="Copy only this manifest target (repeat for multiple figures)",
    )
    args = parser.parse_args()
    only = set(args.only) if args.only else None

    if only is not None:
        unknown = only.difference(FIGURES_MANIFEST)
        if unknown:
            parser.error(f"unknown manifest target(s): {', '.join(sorted(unknown))}")

    print("=" * 60)
    print("COPY FIGURES TO WEB PUBLIC ASSETS")
    print("=" * 60)
    print(f"  Source : {FIGURES_SRC.relative_to(REPO_ROOT)}")
    print(f"  Target : {FIGURES_DST.relative_to(REPO_ROOT)}")
    print(f"  Mode   : {'dry-run' if args.dry_run else 'copy'}")
    print()

    if not args.dry_run:
        FIGURES_DST.mkdir(parents=True, exist_ok=True)

    copied, missing, up_to_date = copy_figures(dry_run=args.dry_run, only=only)

    if only is None:
        # Copy complete analysis trees only during a full site synchronization.
        cx_copied, cx_uptodate = copy_cyclone_explorer_tree(dry_run=args.dry_run)
        ep_copied, ep_uptodate = copy_ep_structure_tree(dry_run=args.dry_run)
        ck_copied, ck_uptodate = copy_analysis_tree(
            "ck_subterms_corrected", dry_run=args.dry_run
        )
        lfd_copied, lfd_uptodate = copy_analysis_tree(
            "lec_field_dependence", dry_run=args.dry_run
        )
    else:
        cx_copied = cx_uptodate = 0
        ep_copied = ep_uptodate = 0
        ck_copied = ck_uptodate = 0
        lfd_copied = lfd_uptodate = 0

    total_copied = copied + cx_copied + ep_copied + ck_copied + lfd_copied
    total_uptodate = (
        up_to_date + cx_uptodate + ep_uptodate + ck_uptodate + lfd_uptodate
    )

    print()
    print(f"  ✓ Copied        : {total_copied}")
    print(f"  – Up-to-date    : {total_uptodate}")
    print(f"  ⚠ Source missing: {missing}")

    if missing > 0:
        print()
        print("  Missing figures will show as placeholders in the site.")
        print("  Run the scientific pipeline to generate them:")
        print("    python scripts/cluster_analysis_energy_patterns/run_pipeline.py")

    if not args.dry_run and total_copied > 0:
        print()
        print("  Next steps:")
        print("    git add web/public/figures/")
        print("    git commit -m 'Update web figures'")
        print("    git push   # Vercel auto-deploys")

    print("=" * 60)


if __name__ == "__main__":
    main()
