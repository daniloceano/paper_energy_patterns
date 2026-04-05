#!/usr/bin/env python3
"""
Debug version of upload script - shows detailed errors for first 5 files.
"""

import os
import sys
import mimetypes
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
BUCKET_NAME = "figures"

# Get credentials
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Missing environment variables")
    sys.exit(1)

print(f"Connecting to: {url}")

try:
    from supabase import create_client
    client = create_client(url, key)
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    sys.exit(1)

# Get first 5 cyclone_explorer files
cyclone_dir = FIGURES_DIR / "cyclone_explorer"
files = sorted(cyclone_dir.rglob("*.png"))[:5]

print(f"\nTesting upload of first 5 files from {len(list(cyclone_dir.rglob('*.png')))} total...")
print()

for file_path in files:
    # Build object key (path within bucket)
    object_key = str(file_path.relative_to(FIGURES_DIR))
    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"
    
    print(f"📁 {object_key}")
    print(f"   Local: {file_path}")
    print(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
    print(f"   MIME: {mime_type}")
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        
        result = client.storage.from_(BUCKET_NAME).upload(
            object_key,
            data,
            {"content-type": mime_type, "upsert": "true"}
        )
        
        print(f"   ✓ SUCCESS: {result}")
        
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Show full traceback for first error
        if files.index(file_path) == 0:
            import traceback
            print("\n" + "=" * 60)
            print("FULL TRACEBACK:")
            print("=" * 60)
            traceback.print_exc()
            print("=" * 60)
    
    print()

print("\nCheck the errors above to understand what's failing.")
