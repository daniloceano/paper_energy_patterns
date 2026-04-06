#!/usr/bin/env python3
"""
Targeted Upload: pv200_wind200 Dynamic Panels to Supabase Storage

This script uploads ONLY the pv200_wind200 dynamic field panels to Supabase Storage.
It is designed for high parallelism and resumability.

Usage:
    source web/.env.local
    python scripts/web/upload_pv200_wind200.py --dry-run    # preview
    python scripts/web/upload_pv200_wind200.py --workers 50  # upload with 50 parallel workers
    python scripts/web/upload_pv200_wind200.py --workers 100 --overwrite  # re-upload all

Author: Danilo Couto de Souza
Date: April 2026
"""

import argparse
import json
import mimetypes
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
CYCLONE_EXPLORER_DIR = FIGURES_DIR / "cyclone_explorer"
BUCKET_NAME = "figures"
PRODUCT_ID = "pv200_wind200"

# Thread-safe counters
stats_lock = Lock()
stats = {"uploaded": 0, "skipped": 0, "errors": 0, "error_list": []}


def get_supabase_client():
    """Initialize Supabase client from environment variables."""
    try:
        from supabase import create_client
    except ImportError:
        print("❌ supabase-py not installed. Run: pip install supabase")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL — your Supabase project URL")
        print("   SUPABASE_SERVICE_ROLE_KEY — service role key")
        print()
        print("   Source them from web/.env.local:")
        print("   source web/.env.local")
        sys.exit(1)

    return create_client(url, key)


def collect_pv200_wind200_files() -> list[tuple[Path, str]]:
    """Collect all pv200_wind200 panel files for upload.
    
    Returns list of (local_path, bucket_object_key) pairs.
    """
    pairs = []
    
    for ep_dir in ["ep1", "ep2"]:
        ep_path = CYCLONE_EXPLORER_DIR / ep_dir
        if not ep_path.exists():
            continue
            
        for track_dir in sorted(ep_path.iterdir()):
            if not track_dir.is_dir():
                continue
            
            pv_dir = track_dir / "dynamic_fields" / PRODUCT_ID
            if not pv_dir.exists():
                continue
            
            for panel_file in sorted(pv_dir.glob("panel_t*.png")):
                # Object key = path relative to figures/
                object_key = str(panel_file.relative_to(FIGURES_DIR))
                pairs.append((panel_file, object_key))
    
    return pairs


def upload_one_file(client, local_path: Path, object_key: str, overwrite: bool) -> tuple[str, str, str]:
    """Upload a single file to Supabase Storage.
    
    Returns: (object_key, status, message)
        status: "uploaded", "skipped", or "error"
    """
    mime_type = "image/png"
    
    try:
        with open(local_path, "rb") as f:
            data = f.read()
        
        if overwrite:
            client.storage.from_(BUCKET_NAME).upload(
                object_key,
                data,
                {"content-type": mime_type, "upsert": "true"},
            )
        else:
            client.storage.from_(BUCKET_NAME).upload(
                object_key,
                data,
                {"content-type": mime_type},
            )
        
        return object_key, "uploaded", ""
    
    except Exception as e:
        err_str = str(e)
        if "already exists" in err_str or "Duplicate" in err_str:
            return object_key, "skipped", "already exists"
        else:
            return object_key, "error", err_str


def worker_upload(args):
    """Worker function for parallel upload."""
    client, local_path, object_key, overwrite = args
    return upload_one_file(client, local_path, object_key, overwrite)


def main():
    parser = argparse.ArgumentParser(
        description="Upload pv200_wind200 panels to Supabase Storage"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=50,
        help="Number of parallel upload workers (default: 50)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files (default: skip)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without uploading"
    )
    parser.add_argument(
        "--output-summary",
        type=str,
        default=None,
        help="Write summary JSON to this file"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("UPLOAD pv200_wind200 DYNAMIC PANELS TO SUPABASE")
    print("=" * 70)
    print(f"  Bucket    : {BUCKET_NAME}")
    print(f"  Product   : {PRODUCT_ID}")
    print(f"  Workers   : {args.workers}")
    print(f"  Mode      : {'dry-run' if args.dry_run else ('overwrite' if args.overwrite else 'skip existing')}")
    print()

    # Collect files
    print("Collecting files...")
    pairs = collect_pv200_wind200_files()
    print(f"  Found {len(pairs)} pv200_wind200 panel files")
    
    # Breakdown by EP
    ep1_count = sum(1 for _, k in pairs if "/ep1/" in k)
    ep2_count = sum(1 for _, k in pairs if "/ep2/" in k)
    print(f"    EP1: {ep1_count}")
    print(f"    EP2: {ep2_count}")
    print()

    if not pairs:
        print("  Nothing to upload.")
        return

    if args.dry_run:
        print(f"[dry-run] Would upload {len(pairs)} files")
        # Show a few samples
        for local_path, object_key in pairs[:5]:
            print(f"  {object_key}")
        if len(pairs) > 5:
            print(f"  ... and {len(pairs) - 5} more")
        return

    # Connect to Supabase
    print("Connecting to Supabase...")
    client = get_supabase_client()
    supabase_url = os.environ.get("SUPABASE_URL", "")
    print(f"  Connected to: {supabase_url}")
    print()

    # Upload in parallel
    print(f"Uploading with {args.workers} parallel workers...")
    
    uploaded = 0
    skipped = 0
    errors = 0
    error_details = []
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(worker_upload, (client, lp, ok, args.overwrite)): ok
            for lp, ok in pairs
        }
        
        # Process results with progress bar
        with tqdm(total=len(pairs), desc="Uploading", unit="file") as pbar:
            for future in as_completed(futures):
                object_key, status, message = future.result()
                
                if status == "uploaded":
                    uploaded += 1
                elif status == "skipped":
                    skipped += 1
                else:
                    errors += 1
                    error_details.append((object_key, message))
                
                pbar.update(1)
                
                # Log periodic progress
                total_done = uploaded + skipped + errors
                if total_done % 500 == 0:
                    pbar.set_postfix({
                        "up": uploaded,
                        "skip": skipped,
                        "err": errors
                    })

    elapsed = time.time() - start_time
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  ✓ Uploaded : {uploaded}")
    print(f"  – Skipped  : {skipped}")
    print(f"  ✗ Errors   : {errors}")
    print(f"  Time       : {elapsed:.1f}s ({len(pairs)/elapsed:.1f} files/sec)")
    print()

    if errors > 0 and errors <= 20:
        print("  Error details:")
        for obj_key, msg in error_details[:20]:
            print(f"    {obj_key}: {msg}")
        print()

    # Validate completeness
    expected = len(pairs)
    success = uploaded + skipped
    print(f"  Expected files : {expected}")
    print(f"  Processed      : {success} ({100*success/expected:.1f}%)")
    
    if success == expected:
        print("  ✓ All pv200_wind200 panels uploaded/present in Supabase!")
    else:
        print(f"  ⚠ {expected - success} files failed")
    
    # Print sample URLs
    base_url = f"{supabase_url.rstrip('/')}/storage/v1/object/public/{BUCKET_NAME}"
    print()
    print("Sample public URLs:")
    for _, object_key in pairs[:3]:
        print(f"  {base_url}/{object_key}")

    # Write summary if requested
    if args.output_summary:
        summary = {
            "product": PRODUCT_ID,
            "total_files": len(pairs),
            "ep1_count": ep1_count,
            "ep2_count": ep2_count,
            "uploaded": uploaded,
            "skipped": skipped,
            "errors": errors,
            "elapsed_seconds": elapsed,
            "error_details": error_details[:100],
        }
        with open(args.output_summary, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n  Summary written to: {args.output_summary}")

    print()
    print("=" * 70)
    print("✓ DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
