#!/usr/bin/env python3
"""
Orchestrator: prepare the web site for deployment.

Runs all steps needed to go from scientific pipeline outputs to a
commit-ready web site, in the correct order.

Usage:
    # From the repository root:
    python scripts/web/prepare_site.py                # full run
    python scripts/web/prepare_site.py --skip-science # skip step4/step5 (use existing figures)
    python scripts/web/prepare_site.py --no-commit    # prepare but do not git commit/push
    python scripts/web/prepare_site.py --dry-run      # preview without making changes

Steps (can be skipped individually with --skip-<step>):
    1. [opt] Run scientific pipeline  (step4_create_figures + step5_update_scientific_notes)
    2. Copy figures to web/public/figures/
    3. Regenerate web/src/content/*.json manifests
    4. [opt] Upload to Supabase Storage (only if SUPABASE_URL is set)
    5. [opt] git add + commit + push

The script does NOT recompute any science.  Steps 1/4/5 are optional.

Author: Danilo Couto de Souza
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON = sys.executable


def run(cmd: list[str], desc: str, dry_run: bool = False) -> bool:
    """Run a command, return True on success."""
    print(f"  → {desc}")
    if dry_run:
        print(f"    [dry-run] {' '.join(cmd)}")
        return True
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print(f"  ✗ FAILED (exit {result.returncode}): {' '.join(cmd)}")
        return False
    return True


def check_figures_exist() -> tuple[int, int]:
    """Check figure inventory in web/public/figures/."""
    public_figures = REPO_ROOT / "web" / "public" / "figures"
    all_pngs = list(public_figures.rglob("*.png")) if public_figures.exists() else []
    return len(all_pngs), len(all_pngs)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare the Energy Patterns web site for deployment."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--skip-science", action="store_true",
                        help="Skip step4/step5 (use existing figures)")
    parser.add_argument("--no-commit", action="store_true",
                        help="Prepare everything but skip git commit/push")
    parser.add_argument("--no-upload", action="store_true",
                        help="Skip Supabase Storage upload even if credentials are set")
    parser.add_argument("--commit-msg", default="",
                        help="Custom git commit message (default: auto-generated)")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("PREPARE SITE FOR DEPLOYMENT")
    print("=" * 60)
    if args.dry_run:
        print("  Mode: DRY RUN — no changes will be made")
    print()

    errors: list[str] = []

    # ── Step 1: Scientific pipeline (optional) ────────────────────────────
    if not args.skip_science:
        print("[ Step 1 ] Run scientific pipeline")
        print("  Note: This step regenerates figures from the scientific pipeline.")
        print("  Skip with --skip-science if figures are already up-to-date.")
        print()
        ok1a = run(
            [PYTHON, "scripts/ep_structure_analysis/step4_create_figures.py"],
            "step4_create_figures.py",
            dry_run=args.dry_run,
        )
        ok1b = run(
            [PYTHON, "scripts/ep_structure_analysis/step5_update_scientific_notes.py"],
            "step5_update_scientific_notes.py",
            dry_run=args.dry_run,
        )
        if not (ok1a and ok1b):
            errors.append("Step 1: scientific pipeline failed")
        print()
    else:
        print("[ Step 1 ] Scientific pipeline — SKIPPED (--skip-science)")
        print()

    # ── Step 2: Copy figures to web/public/figures/ ───────────────────────
    # Note: extract_composite_site_data.py (step 3) checks figures/ (source),
    # so steps 2 and 3 are independent and can run in either order.
    print("[ Step 2 ] Copy figures → web/public/figures/")
    ok2 = run(
        [PYTHON, "scripts/web/copy_figures_to_web.py"],
        "copy_figures_to_web.py",
        dry_run=args.dry_run,
    )
    if not ok2:
        errors.append("Step 2: copy_figures_to_web.py failed")
    print()

    # ── Step 3: Regenerate manifests ──────────────────────────────────────
    print("[ Step 3 ] Regenerate web/src/content/*.json manifests")
    manifest_scripts = [
        ("scripts/web/build_site_manifest.py",         "build_site_manifest.py"),
        ("scripts/web/extract_cluster_site_data.py",   "extract_cluster_site_data.py"),
        ("scripts/web/extract_composite_site_data.py", "extract_composite_site_data.py"),
        ("scripts/web/extract_ck_subterms_site_data.py", "extract_ck_subterms_site_data.py"),
        ("scripts/web/extract_cyclone_explorer_data.py", "extract_cyclone_explorer_data.py"),
    ]
    step3_ok = True
    for script, desc in manifest_scripts:
        ok = run([PYTHON, script], desc, dry_run=args.dry_run)
        if not ok:
            errors.append(f"Step 3: {desc} failed")
            step3_ok = False
    print()

    # ── Step 4: Upload to Supabase Storage (optional) ────────────────────
    import os
    has_supabase = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
    if has_supabase and not args.no_upload:
        print("[ Step 4 ] Upload figures to Supabase Storage")
        ok4 = run(
            [PYTHON, "scripts/web/upload_figures_to_supabase.py", "--overwrite"],
            "upload_figures_to_supabase.py --overwrite",
            dry_run=args.dry_run,
        )
        if not ok4:
            errors.append("Step 4: Supabase upload failed (non-fatal)")
        print()
    else:
        reason = "--no-upload" if args.no_upload else "SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY not set"
        print(f"[ Step 4 ] Supabase upload — SKIPPED ({reason})")
        print("  Figures will be served from web/public/figures/ (static assets).")
        print()

    # ── Step 5: git add + commit + push (optional) ───────────────────────
    if not args.no_commit and not args.dry_run:
        print("[ Step 5 ] git add + commit + push")
        commit_msg = args.commit_msg or "chore: update web figures and manifests"

        n_found, n_expected = check_figures_exist()
        print(f"  Found {n_found}/{n_expected} expected figures in web/public/figures/")

        subprocess.run(["git", "add", "web/public/figures/", "web/src/content/"], cwd=REPO_ROOT)
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        staged = result.stdout.strip().splitlines()

        if staged:
            print(f"  Staged {len(staged)} file(s)")
            ok5 = run(
                ["git", "commit", "-m", commit_msg,
                 "--trailer", "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"],
                f'git commit -m "{commit_msg}"',
            )
            if ok5:
                run(["git", "push"], "git push → Vercel auto-deploys")
        else:
            print("  Nothing to commit — web/public/figures/ and web/src/content/ are up-to-date")
        print()
    elif args.no_commit:
        print("[ Step 5 ] git commit/push — SKIPPED (--no-commit)")
        print("  Manual steps:")
        print("    git add web/public/figures/ web/src/content/")
        print('    git commit -m "chore: update web figures and manifests"')
        print("    git push")
        print()
    else:
        print("[ Step 5 ] git commit/push — SKIPPED (dry-run)")
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    print("=" * 60)
    if errors:
        print("COMPLETED WITH ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("✓ ALL STEPS COMPLETED SUCCESSFULLY")
        print()
        print("  The Vercel site will auto-deploy on the next git push.")
        print("  No manual build step needed.")
    print("=" * 60)
    print()

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
