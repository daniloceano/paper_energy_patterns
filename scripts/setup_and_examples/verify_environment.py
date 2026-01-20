"""
Environment verification script
Tests if all required packages are correctly installed
"""

import sys
from importlib.metadata import version, PackageNotFoundError


def check_package(package_name, display_name=None):
    """Check if a package is installed and return its version"""
    if display_name is None:
        display_name = package_name
    
    try:
        # Special handling for sklearn/scikit-learn
        if package_name == "sklearn":
            import sklearn
            ver = sklearn.__version__
            print(f"✓ {display_name:20s} {ver}")
            return True
        
        ver = version(package_name)
        print(f"✓ {display_name:20s} {ver}")
        return True
    except (PackageNotFoundError, ImportError):
        print(f"✗ {display_name:20s} NOT INSTALLED")
        return False


def main():
    print("=" * 60)
    print("Environment Verification")
    print("=" * 60)
    print()
    
    # Check Python version
    py_version = sys.version.split()[0]
    print(f"Python version: {py_version}")
    print()
    
    print("Checking required packages:")
    print("-" * 60)
    
    packages = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scipy", "scipy"),
        ("xarray", "xarray"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("cmocean", "cmocean"),
        ("cartopy", "cartopy"),
        ("geopandas", "geopandas"),
        ("shapely", "shapely"),
        ("sklearn", "sklearn"),
        ("statsmodels", "statsmodels"),
        ("netCDF4", "netCDF4"),
        ("h5py", "h5py"),
        ("requests", "requests"),
        ("tqdm", "tqdm"),
        ("metpy", "metpy"),
        ("cdsapi", "cdsapi"),
    ]
    
    all_installed = True
    for import_name, display_name in packages:
        if not check_package(import_name, display_name):
            all_installed = False
    
    print("-" * 60)
    print()
    
    # Test basic functionality
    if all_installed:
        print("Testing basic functionality...")
        print("-" * 60)
        
        try:
            import numpy as np
            import pandas as pd
            
            # Test numpy
            arr = np.array([1, 2, 3])
            print(f"✓ NumPy array creation: {arr}")
            
            # Test pandas
            df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
            print(f"✓ Pandas DataFrame creation: shape {df.shape}")
            
            # Test data loading function
            print()
            print("Testing data loading from GitHub...")
            
            # Add project root to path for imports
            import os
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from scripts.utils.load_data import load_tracks
            
            tracks = load_tracks()
            print(f"✓ Successfully loaded {len(tracks)} track records")
            print(f"✓ Found {tracks['track_id'].nunique()} unique cyclones")
            
            print()
            print("=" * 60)
            print("✅ All tests passed! Environment is ready to use.")
            print("=" * 60)
            
        except Exception as e:
            print()
            print("=" * 60)
            print(f"⚠️  Warning: Functionality test failed: {e}")
            print("=" * 60)
            return 1
    else:
        print("=" * 60)
        print("❌ Some packages are missing. Please install them.")
        print("=" * 60)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
