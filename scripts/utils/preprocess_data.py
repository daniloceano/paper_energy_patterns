"""
Script to preprocess and cache all energy data in an efficient format.

This script loads all cyclone energy data from GitHub once, processes it,
and saves to a local Parquet file for fast loading by analysis scripts.

Run this script once (or whenever data is updated) to create the cache.
"""

import sys
import time
from pathlib import Path
from typing import Optional
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.load_data import load_tracks, load_energy_by_cyclone

# ============================================================================
# CONFIGURATION
# ============================================================================

# Output file path
CACHE_FILE = PROJECT_ROOT / "data" / "energy_cache.parquet"

# Processing options
USE_PARALLEL = True  # Use parallel processing (faster)
N_WORKERS = 50  # Number of parallel workers (adjust for server: 50 cores available)

# ============================================================================


def _process_single_cyclone(track_id: str) -> Optional[pd.DataFrame]:
    """Process a single cyclone and return its energy data with track_id.
    
    Returns None if loading fails.
    """
    df = load_energy_by_cyclone(str(track_id))
    if df is None or df.empty:
        return None
    
    # Add track_id column
    df['track_id'] = track_id
    
    # Ensure period is string and lowercase
    df['period'] = df['period'].astype(str).str.strip().str.lower()
    
    # Add phase column (main categories)
    def classify_phase(period):
        if period.startswith('incipient'):
            return 'incipient'
        elif period.startswith('intensification'):
            return 'intensification'
        elif period.startswith('mature'):
            return 'mature'
        elif period.startswith('decay'):
            return 'decay'
        elif period.startswith('residual'):
            return 'residual'
        else:
            return 'other'
    
    df['phase'] = df['period'].apply(classify_phase)
    
    return df


def preprocess_all_data(use_parallel: bool = True, n_workers: int = 4) -> pd.DataFrame:
    """Load and process all cyclone energy data.
    
    Args:
        use_parallel: Whether to use parallel processing
        n_workers: Number of parallel workers
        
    Returns:
        Combined DataFrame with all energy data
    """
    t_start = time.time()
    
    print("📊 STEP 1/4: Loading cyclone tracks...")
    t0 = time.time()
    tracks = load_tracks()
    track_ids = tracks['track_id'].unique().tolist()
    t1 = time.time()
    print(f"   ✓ Loaded {len(track_ids)} track IDs in {t1-t0:.2f}s")
    print()
    
    print(f"📊 STEP 2/4: Processing {len(track_ids)} cyclones...")
    print(f"   Mode: {'PARALLEL' if use_parallel else 'SEQUENTIAL'}")
    print(f"   Workers: {n_workers if use_parallel else 1}")
    print(f"   Estimated time: {len(track_ids) * 0.15 / (n_workers if use_parallel else 1) / 60:.1f} minutes")
    print()
    
    t2 = time.time()
    all_dfs = []
    failed_count = 0
    
    if use_parallel:
        # Parallel processing
        print(f"   🚀 Starting {n_workers} parallel workers...")
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(_process_single_cyclone, tid): tid 
                      for tid in track_ids}
            
            for future in tqdm(as_completed(futures), total=len(futures), 
                             desc="   Processing", ncols=80, 
                             bar_format='   {l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'):
                try:
                    result = future.result()
                    if result is not None:
                        all_dfs.append(result)
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    continue
    else:
        # Sequential processing
        for tid in tqdm(track_ids, desc="   Processing", ncols=80,
                       bar_format='   {l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'):
            result = _process_single_cyclone(tid)
            if result is not None:
                all_dfs.append(result)
            else:
                failed_count += 1
    
    t3 = time.time()
    processing_time = t3 - t2
    rate = len(track_ids) / processing_time
    
    print()
    print(f"   ✓ Processed {len(all_dfs)} cyclones successfully in {processing_time:.2f}s")
    print(f"   ✓ Processing rate: {rate:.1f} cyclones/second")
    if failed_count > 0:
        print(f"   ⚠️  Failed to load: {failed_count} cyclones")
    print()
    
    # Combine all dataframes
    print("📊 STEP 3/4: Combining data...")
    t4 = time.time()
    combined = pd.concat(all_dfs, ignore_index=True)
    t5 = time.time()
    print(f"   ✓ Combined in {t5-t4:.2f}s")
    print()
    
    # Convert numeric columns
    print("📊 STEP 4/4: Converting numeric columns...")
    t6 = time.time()
    numeric_cols = ['Az', 'Ae', 'Kz', 'Ke', 'Cz', 'Ca', 'Ck', 'Ce',
                   'BAz', 'BAe', 'BKz', 'BKe', 'Ge', 'Gz', 'RKe', 'RKz',
                   'dAedt', 'dAzdt', 'dKedt', 'dKzdt']
    
    for col in numeric_cols:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors='coerce')
    t7 = time.time()
    print(f"   ✓ Converted {len([c for c in numeric_cols if c in combined.columns])} columns in {t7-t6:.2f}s")
    print()
    
    # Summary
    t_end = time.time()
    total_time = t_end - t_start
    
    print("=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    print(f"Total processing time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    print(f"Combined shape: {combined.shape}")
    print(f"Unique cyclones: {combined['track_id'].nunique()}")
    print(f"Memory usage: {combined.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    print()
    print("Phase distribution:")
    for phase, count in combined['phase'].value_counts().items():
        print(f"  {phase:20s}: {count:6d} records ({count/len(combined)*100:.1f}%)")
    print("=" * 70)
    
    return combined


def save_cache(df: pd.DataFrame, output_path: Path):
    """Save processed data to Parquet format.
    
    Args:
        df: DataFrame to save
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print()
    print(f"💾 Saving to {output_path}...")
    t0 = time.time()
    df.to_parquet(output_path, index=False, compression='snappy')
    t1 = time.time()
    
    # Print file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"   ✓ Saved in {t1-t0:.2f}s")
    print(f"   ✓ File size: {size_mb:.2f} MB")
    print(f"   ✓ Compression ratio: {df.memory_usage(deep=True).sum() / output_path.stat().st_size:.2f}x")


def load_cache(cache_path: Path = None) -> pd.DataFrame:
    """Load preprocessed data from cache.
    
    Args:
        cache_path: Path to cache file (default: CACHE_FILE)
        
    Returns:
        DataFrame with all energy data
    """
    if cache_path is None:
        cache_path = CACHE_FILE
    
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Cache file not found: {cache_path}\n"
            f"Run this script first to create the cache."
        )
    
    print(f"Loading cache from {cache_path}...")
    df = pd.read_parquet(cache_path)
    print(f"✓ Loaded {len(df)} records from {df['track_id'].nunique()} cyclones")
    return df


def main():
    """Main execution function."""
    print("=" * 70)
    print("Energy Data Preprocessing")
    print("=" * 70)
    print()
    
    # Check if cache already exists
    if CACHE_FILE.exists():
        size_mb = CACHE_FILE.stat().st_size / (1024 * 1024)
        print(f"⚠️  Cache file already exists: {CACHE_FILE}")
        print(f"   Size: {size_mb:.2f} MB")
        
        response = input("\nOverwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return 0
        print()
    
    # Process all data
    df = preprocess_all_data(use_parallel=USE_PARALLEL, n_workers=N_WORKERS)
    
    # Save to cache
    save_cache(df, CACHE_FILE)
    
    print()
    print("=" * 70)
    print("✅ Preprocessing complete!")
    print("=" * 70)
    print()
    print("To use the cache in your analysis scripts:")
    print("  from scripts.utils.preprocess_data import load_cache")
    print("  df = load_cache()")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
