#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download LEC (Lorenz Energy Cycle) Results from Zenodo

Downloads the complete LEC results dataset from Zenodo and extracts it to
data/temp_lec_zenodo/LEC_Results_energetic-patterns/

Data Source: Zenodo (DOI: 10.5281/zenodo.18243447)
- Complete Lorenz Energy Cycle results with vertical resolution
- ~1,500 cyclones from 1979-2020
- 32 pressure levels from 1000 hPa to 100 hPa
- 3-hourly temporal resolution

Directory Structure After Download:
    data/temp_lec_zenodo/LEC_Results_energetic-patterns/
        ├── 19790006_ERA5_track/
        │   ├── periods.csv/
        │   ├── Ca_level.csv
        │   ├── Ck_level.csv
        │   └── ...
        ├── 19790012_ERA5_track/
        └── ...

Author: Danilo Couto de Souza
Date: January 2026
"""

from pathlib import Path
import requests
import zipfile
import tarfile
import io
import warnings
import subprocess
import shutil
from tqdm import tqdm

# Suppress SSL warnings if we need to use verify=False
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]
TEMP_DIR = BASE_DIR / "data" / "temp_lec_zenodo"
EXPECTED_SUBDIR = "LEC_Results_energetic-patterns"

# Data source information
ZENODO_DOI = "10.5281/zenodo.18243447"
ZENODO_RECORD_ID = "18243447"
ZENODO_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}"

# Minimum expected number of cyclone directories
MIN_EXPECTED_DIRS = 1000


def check_if_already_downloaded():
    """
    Check if LEC data has already been downloaded.
    
    Returns:
        Path to extracted data directory if found, None otherwise
    """
    # Check for the expected directory structure
    expected_dir = TEMP_DIR / EXPECTED_SUBDIR
    if expected_dir.exists():
        cyclone_dirs = [d for d in expected_dir.iterdir() 
                       if d.is_dir() and d.name.endswith('_ERA5_track')]
        if len(cyclone_dirs) >= MIN_EXPECTED_DIRS:
            return expected_dir
    
    # Check if data is directly in TEMP_DIR
    if TEMP_DIR.exists():
        cyclone_dirs = [d for d in TEMP_DIR.iterdir() 
                       if d.is_dir() and d.name.endswith('_ERA5_track')]
        if len(cyclone_dirs) >= MIN_EXPECTED_DIRS:
            return TEMP_DIR
    
    # Check for any subdirectory with many _ERA5_track folders
    if TEMP_DIR.exists():
        for item in TEMP_DIR.iterdir():
            if item.is_dir():
                subdirs = [d for d in item.iterdir() 
                          if d.is_dir() and d.name.endswith('_ERA5_track')]
                if len(subdirs) >= MIN_EXPECTED_DIRS:
                    return item
    
    return None


def download_and_extract_lec_data():
    """
    Download and extract LEC results from Zenodo.
    
    Returns:
        Path to extracted data directory
    """
    print("=" * 80)
    print("DOWNLOADING LEC RESULTS FROM ZENODO")
    print("=" * 80)
    print(f"\nData source: {ZENODO_DOI}")
    print(f"URL: {ZENODO_URL}")
    
    # Check if already downloaded
    existing_dir = check_if_already_downloaded()
    if existing_dir:
        cyclone_dirs = [d for d in existing_dir.iterdir() 
                       if d.is_dir() and d.name.endswith('_ERA5_track')]
        print(f"\n✓ Data already downloaded: {existing_dir}")
        print(f"  Found {len(cyclone_dirs)} cyclone directories")
        return existing_dir
    
    # Create temp directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Known file information from Zenodo record
    file_name = "LEC_Results_energetic-patterns_csv_only.tar.gz"
    file_size = 633900000  # ~633.9 MB
    is_tarfile = True
    
    # Direct download URL (bypasses API issues)
    download_url = f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files/{file_name}"
    
    print(f"\nDownload URL: {download_url}")
    
    # Add headers to avoid 403 errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f"\nDownloading: {file_name}")
    print(f"Size: {file_size / 1024 / 1024:.1f} MB")
    print("This may take several minutes...")
    
    # Download archive file with progress bar
    print(f"\nAttempting to download from Zenodo...")
    
    archive_path = TEMP_DIR / file_name
    download_success = False
    
    # Try using wget or curl first (these work better with Zenodo)
    if shutil.which('wget'):
        print("   Using wget for download...")
        try:
            result = subprocess.run(
                ['wget', '-c', '--progress=bar:force', download_url, '-O', str(archive_path)],
                check=True,
                capture_output=False
            )
            download_success = True
        except subprocess.CalledProcessError as e:
            print(f"   wget failed: {e}")
    
    if not download_success and shutil.which('curl'):
        print("   Using curl for download...")
        try:
            result = subprocess.run(
                ['curl', '-L', '--progress-bar', download_url, '-o', str(archive_path)],
                check=True,
                capture_output=False
            )
            download_success = True
        except subprocess.CalledProcessError as e:
            print(f"   curl failed: {e}")
    
    # Fallback to Python requests
    if not download_success:
        print("   Using Python requests for download...")
        try:
            # Try with verify=True first
            response = requests.get(download_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            # Write to file with progress bar
            archive_data = io.BytesIO()
            with tqdm(total=file_size, unit='B', unit_scale=True, desc='Downloading') as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    archive_data.write(chunk)
                    pbar.update(len(chunk))
            
            # Save to file
            archive_data.seek(0)
            with open(archive_path, 'wb') as f:
                f.write(archive_data.read())
            
            download_success = True
            
        except requests.exceptions.SSLError:
            print("   SSL error encountered, retrying with verify=False...")
            try:
                response = requests.get(download_url, headers=headers, stream=True, timeout=60, verify=False)
                response.raise_for_status()
                
                # Write to file with progress bar
                archive_data = io.BytesIO()
                with tqdm(total=file_size, unit='B', unit_scale=True, desc='Downloading') as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        archive_data.write(chunk)
                        pbar.update(len(chunk))
                
                # Save to file
                archive_data.seek(0)
                with open(archive_path, 'wb') as f:
                    f.write(archive_data.read())
                
                download_success = True
                
            except requests.exceptions.RequestException as e:
                print(f"   Python requests also failed: {e}")
        except requests.exceptions.RequestException as e:
            print(f"   Python requests failed: {e}")
    
    if not download_success:
        print(f"\n❌ All download methods failed")
        print("\n" + "=" * 80)
        print("MANUAL DOWNLOAD REQUIRED")
        print("=" * 80)
        print(f"\nPlease download the file manually:")
        print(f"1. Visit: {ZENODO_URL}")
        print(f"2. Download: {file_name}")
        print(f"3. Save to: {archive_path}")
        print(f"4. Extract with: tar -xzf {archive_path} -C {TEMP_DIR}")
        print()
        raise RuntimeError(f"Automatic download failed. Please download manually (see instructions above).")
    
    print(f"\n✓ Download complete: {archive_path}")
    
    # Extract archive file
    print("\nExtracting archive...")
    
    try:
        if is_tarfile:
            with tarfile.open(archive_path, mode='r:gz') as tar_ref:
                tar_ref.extractall(TEMP_DIR, filter='data')
        else:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(TEMP_DIR)
    except Exception as e:
        raise RuntimeError(f"Failed to extract archive: {e}")
    
    # Find the extracted directory
    extracted_dir = None
    
    # First, check for expected directory structure
    expected_dir = TEMP_DIR / EXPECTED_SUBDIR
    if expected_dir.exists():
        cyclone_dirs = [d for d in expected_dir.iterdir() 
                       if d.is_dir() and d.name.endswith('_ERA5_track')]
        if len(cyclone_dirs) > 10:
            extracted_dir = expected_dir
    
    # If not found, look for any directory with _ERA5_track subdirectories
    if extracted_dir is None:
        for item in TEMP_DIR.iterdir():
            if item.is_dir():
                subdirs = [d for d in item.iterdir() 
                          if d.is_dir() and d.name.endswith('_ERA5_track')]
                if len(subdirs) > 10:
                    extracted_dir = item
                    break
    
    # Check if _ERA5_track directories are directly in TEMP_DIR
    if extracted_dir is None:
        subdirs = [d for d in TEMP_DIR.iterdir() 
                  if d.is_dir() and d.name.endswith('_ERA5_track')]
        if len(subdirs) > 10:
            extracted_dir = TEMP_DIR
    
    if extracted_dir is None:
        raise FileNotFoundError(f"Could not find extracted LEC data in {TEMP_DIR}")
    
    # Count cyclone directories
    cyclone_dirs = [d for d in extracted_dir.iterdir() 
                   if d.is_dir() and d.name.endswith('_ERA5_track')]
    
    print(f"\n✓ Successfully extracted to: {extracted_dir}")
    print(f"  Found {len(cyclone_dirs)} cyclone directories")
    
    if len(cyclone_dirs) < MIN_EXPECTED_DIRS:
        print(f"\n⚠ Warning: Expected at least {MIN_EXPECTED_DIRS} directories, "
              f"but found only {len(cyclone_dirs)}")
    
    return extracted_dir


def main():
    """Main function to download LEC data from Zenodo."""
    try:
        extracted_dir = download_and_extract_lec_data()
        
        print("\n" + "=" * 80)
        print("DOWNLOAD COMPLETE")
        print("=" * 80)
        print(f"\nData location: {extracted_dir}")
        print("\nYou can now run scripts that depend on LEC data:")
        print("  - scripts/ep1_ibc_ibt_analysis/step1_select_cases.py")
        print("  - scripts/ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py")
        print("  - scripts/ep1_ibc_ibt_analysis/step3_download_era5.py")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
