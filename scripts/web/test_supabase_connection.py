#!/usr/bin/env python3
"""
Test Supabase connection and upload a single file.
This helps diagnose upload failures.
"""

import os
import sys
from pathlib import Path

# Check environment variables
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print("=" * 60)
print("SUPABASE CONNECTION TEST")
print("=" * 60)

if not supabase_url or not supabase_key:
    print("❌ Missing environment variables!")
    print(f"   SUPABASE_URL: {'✓' if supabase_url else '✗ NOT SET'}")
    print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✓' if supabase_key else '✗ NOT SET'}")
    sys.exit(1)

print(f"✓ SUPABASE_URL: {supabase_url}")
print(f"✓ SUPABASE_SERVICE_ROLE_KEY: {supabase_key[:20]}..." if supabase_key else "✗")
print()

# Try to import supabase
try:
    from supabase import create_client
    print("✓ supabase-py installed")
except ImportError:
    print("❌ supabase-py NOT installed")
    print("   Install with: pip install supabase")
    sys.exit(1)

# Try to connect
print("\nConnecting to Supabase...")
try:
    client = create_client(supabase_url, supabase_key)
    print("✓ Client created successfully")
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    sys.exit(1)

# Try to access storage
print("\nChecking storage access...")
try:
    buckets = client.storage.list_buckets()
    print(f"✓ Storage accessible")
    print(f"  Found {len(buckets)} buckets:")
    for bucket in buckets:
        print(f"    - {bucket.name} (public: {bucket.public})")
except Exception as e:
    print(f"❌ Failed to access storage: {e}")
    sys.exit(1)

# Check if 'figures' bucket exists
BUCKET_NAME = "figures"
bucket_exists = any(b.name == BUCKET_NAME for b in buckets)
if not bucket_exists:
    print(f"\n❌ Bucket '{BUCKET_NAME}' does NOT exist!")
    print("   Create it in Supabase Dashboard:")
    print("   Storage → New bucket → Name: figures → Public: YES")
    sys.exit(1)
else:
    print(f"\n✓ Bucket '{BUCKET_NAME}' exists")

# Find a small test file
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
test_files = list((REPO_ROOT / "web/public/figures/cluster").glob("*.png"))
if not test_files:
    print("\n⚠️  No test files found in web/public/figures/cluster/")
    sys.exit(0)

test_file = test_files[0]
print(f"\nTesting upload with: {test_file.name}")

# Try to upload
try:
    with open(test_file, "rb") as f:
        data = f.read()
    
    object_key = f"test/{test_file.name}"
    print(f"  Uploading to: {BUCKET_NAME}/{object_key}")
    
    result = client.storage.from_(BUCKET_NAME).upload(
        object_key,
        data,
        {"content-type": "image/png", "upsert": "true"}
    )
    
    print(f"✓ Upload successful!")
    print(f"  Result: {result}")
    
    # Try to get public URL
    public_url = client.storage.from_(BUCKET_NAME).get_public_url(object_key)
    print(f"  Public URL: {public_url}")
    
    # Clean up test file
    print(f"\nCleaning up test file...")
    client.storage.from_(BUCKET_NAME).remove([object_key])
    print(f"✓ Test file removed")
    
except Exception as e:
    print(f"❌ Upload failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED!")
print("=" * 60)
print("\nYour Supabase configuration is working correctly.")
print("The upload script should work now.")
