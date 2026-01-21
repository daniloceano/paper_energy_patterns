"""
Step 2: Run LorenzCycleToolkit for Selected EP1 Cyclones

This script automates the computation of the Lorenz Energy Cycle (LEC) with
full term decomposition using the updated LorenzCycleToolkit.

Prerequisites:
- Run step1_prepare_tracks.py first (creates track files)
- LorenzCycleToolkit installed at ~/Documents/Programs_and_scripts/lorenz-cycle/
- CDS API credentials configured in ~/.cdsapirc

How it works:
1. Iterates through all prepared track files (from step1)
2. For each cyclone, runs lorenzcycletoolkit.py with:
   - Automatic ERA5 data download (--cdsapi)
   - Moving framework (-t) to follow cyclone center
   - Residuals computation (-r) for dissipation/generation terms
   - Plots generation (-p) for visualization
   - 6-hourly temporal resolution (matches track resolution)

Output:
- results/ck_analysis/lec_results/{track_id}_ERA5_track/
  ├── periods.csv              # Lifecycle phases
  ├── results.csv              # Integrated terms (all phases)
  ├── Ck_level.csv            # Total Ck by pressure level
  ├── Ck_uv_level.csv         # Horizontal momentum flux term
  ├── Ck_uw_level.csv         # Vertical momentum flux (zonal) term
  ├── Ck_vw_level.csv         # Vertical momentum flux (meridional) term
  └── ...                     # Other energy terms and figures

Parallelization:
- Uses multiprocessing to process cyclones in parallel
- Default: N_WORKERS = 4 (adjust based on available cores)
- Each worker runs one LorenzCycleToolkit instance

Error Handling:
- Checks if LEC already computed (avoids reprocessing)
- Handles CDS API rate limits gracefully
- Logs all successes and failures

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import subprocess
import multiprocessing as mp
from functools import partial
import time
import shutil
import logging
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]
TRACKS_DIR = BASE_DIR / "data" / "ck_analysis" / "tracks"
RESULTS_DIR = BASE_DIR / "results" / "ck_analysis" / "lec_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_DIR = BASE_DIR / "results" / "ck_analysis" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"step2_lec_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
CYCLONE_LOG_DIR = LOG_DIR / "cyclones"  # Individual cyclone stdout/stderr
CYCLONE_LOG_DIR.mkdir(parents=True, exist_ok=True)

# LorenzCycleToolkit installation path
# LORENZ_TOOLKIT_DIR = Path.home() / "Documents" / "Programs_and_scripts" / "lorenz-cycle"
LORENZ_TOOLKIT_DIR = Path("/p1-swell/danilocs/LorenzCycleToolkit/")
LORENZ_SCRIPT = LORENZ_TOOLKIT_DIR / "lorenzcycletoolkit.py"
LORENZ_RESULTS_DIR = LORENZ_TOOLKIT_DIR / "LEC_Results"  # Where LorenzCycleToolkit saves results

# Conda environment for LorenzCycleToolkit
# Note: LorenzCycleToolkit requires its own conda environment
LORENZ_CONDA_ENV = "lorenz"

# Parallelization settings
N_WORKERS = 4  # Adjust based on available CPU cores and CDS API limits

# LorenzCycleToolkit settings
TIME_RESOLUTION = 6  # hours (matches track temporal resolution)
# Flags: -t (track), -r (residuals), -p (plots), -v (verbose), --cdsapi (auto download)
LEC_FLAGS = ['-t', '-r', '-p', '-v', '--cdsapi']


def check_prerequisites():
    """Check if all prerequisites are met."""
    
    print("\n1. Checking prerequisites...")
    
    # Check if tracks directory exists and has files
    if not TRACKS_DIR.exists():
        print(f"   ❌ Error: Tracks directory not found: {TRACKS_DIR}")
        print("      Please run step1_prepare_tracks.py first.")
        return False
    
    track_files = list(TRACKS_DIR.glob("track_*.txt"))
    if len(track_files) == 0:
        print(f"   ❌ Error: No track files found in {TRACKS_DIR}")
        print("      Please run step1_prepare_tracks.py first.")
        return False
    
    print(f"   ✓ Found {len(track_files)} track files")
    
    # Check if LorenzCycleToolkit exists
    if not LORENZ_SCRIPT.exists():
        print(f"   ❌ Error: LorenzCycleToolkit not found: {LORENZ_SCRIPT}")
        print(f"      Expected at: {LORENZ_TOOLKIT_DIR}")
        return False
    
    print(f"   ✓ LorenzCycleToolkit found: {LORENZ_SCRIPT}")
    
    # Check CDS API credentials
    cdsapirc = Path.home() / ".cdsapirc"
    if not cdsapirc.exists():
        print(f"   ⚠ Warning: CDS API credentials not found: {cdsapirc}")
        print("      ERA5 data download will fail without proper configuration.")
        print("      See: https://cds.climate.copernicus.eu/api-how-to")
    else:
        print(f"   ✓ CDS API credentials found")
    
    return True


def is_already_processed(track_id):
    """
    Check if LEC has already been computed for this cyclone.
    
    Checks for existence of results in project directory or LorenzCycleToolkit directory.
    """
    # Check in project results directory
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if result_dir.exists():
        # Check for key output files
        required_files = [
            result_dir / "results.csv",
            result_dir / "periods.csv",
            result_dir / "Ck_level.csv"
        ]
        
        if all(f.exists() for f in required_files):
            return True
    
    # Also check in LorenzCycleToolkit results directory
    lorenz_result_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if lorenz_result_dir.exists():
        # Check for key output files
        required_files = [
            lorenz_result_dir / "results.csv",
            lorenz_result_dir / "periods.csv",
            lorenz_result_dir / "Ck_level.csv"
        ]
        
        if all(f.exists() for f in required_files):
            return True
    
    return False


def move_results_to_project(track_id):
    """
    Move LEC results from LorenzCycleToolkit directory to project directory.
    
    Args:
        track_id: Cyclone track ID
        
    Returns:
        True if successful, False otherwise
    """
    source_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
    dest_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    try:
        if not source_dir.exists():
            return False
        
        # Remove destination if it exists (to avoid conflicts)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        
        # Move entire directory
        shutil.move(str(source_dir), str(dest_dir))
        
        return True
        
    except Exception as e:
        print(f"      ⚠ Warning: Failed to move results for {track_id}: {e}")
        return False


def process_cyclone(track_file):
    """
    Process a single cyclone using LorenzCycleToolkit.
    
    Args:
        track_file: Path to track file
        
    Returns:
        (track_id, success, message) tuple
    """
    # Extract track ID from filename: track_19790205.txt -> 19790205
    track_id = track_file.stem.replace('track_', '')
    
    # Setup logging for this worker
    logger = logging.getLogger(f'worker_{mp.current_process().name}')
    logger.info(f"[{track_id}] Starting processing...")
    
    try:
        # Check if already processed
        if is_already_processed(track_id):
            logger.info(f"[{track_id}] Already processed, skipping")
            return (track_id, True, "Already processed (skipped)")
        
        # Prepare command
        # Output file: 19790205_ERA5.nc (will be created by --cdsapi)
        output_file = f"{track_id}_ERA5.nc"
        
        # Use conda run to execute in the lorenz environment
        cmd = [
            'conda', 'run', '-n', LORENZ_CONDA_ENV,
            'python',
            str(LORENZ_SCRIPT),
            output_file,
            *LEC_FLAGS,
            '--time-resolution', str(TIME_RESOLUTION),
            '--trackfile', str(track_file)
        ]
        
        logger.info(f"[{track_id}] Running LorenzCycleToolkit...")
        logger.debug(f"[{track_id}] Command: {' '.join(cmd)}")
        
        # Prepare log files for stdout/stderr
        stdout_log = CYCLONE_LOG_DIR / f"{track_id}_stdout.log"
        stderr_log = CYCLONE_LOG_DIR / f"{track_id}_stderr.log"
        
        # Run LorenzCycleToolkit
        # Note: Must run from LORENZ_TOOLKIT_DIR to access inputs/ directory
        result = subprocess.run(
            cmd,
            cwd=str(LORENZ_TOOLKIT_DIR),
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout per cyclone
        )
        
        # Save full output to files
        with open(stdout_log, 'w') as f:
            f.write(result.stdout)
        with open(stderr_log, 'w') as f:
            f.write(result.stderr)
        
        if result.returncode == 0:
            logger.info(f"[{track_id}] LorenzCycleToolkit completed successfully")
            # Move results from LorenzCycleToolkit directory to project directory
            if move_results_to_project(track_id):
                # Verify results were moved successfully
                if is_already_processed(track_id):
                    logger.info(f"[{track_id}] ✓ Completed and validated")
                    return (track_id, True, "Completed successfully")
                else:
                    logger.error(f"[{track_id}] Results moved but validation failed")
                    return (track_id, False, "Results moved but validation failed")
            else:
                # Check if results are in LorenzCycleToolkit directory
                lorenz_result_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
                if lorenz_result_dir.exists():
                    logger.error(f"[{track_id}] Failed to move results")
                    return (track_id, False, "Completed but failed to move results")
                else:
                    logger.error(f"[{track_id}] Output files not found")
                    return (track_id, False, "Completed but output files not found")
        else:
            # Extract error message (last non-empty lines)
            stderr_lines = [line for line in result.stderr.split('\n') if line.strip()]
            error_msg = stderr_lines[-5:] if len(stderr_lines) >= 5 else stderr_lines
            
            logger.error(f"[{track_id}] LorenzCycleToolkit failed with exit code {result.returncode}")
            logger.error(f"[{track_id}] Last stderr lines: {error_msg}")
            logger.error(f"[{track_id}] Full logs: stdout={stdout_log}, stderr={stderr_log}")
            
            return (track_id, False, f"Exit code {result.returncode}. See {stderr_log}")
            
    except subprocess.TimeoutExpired:
        logger.error(f"[{track_id}] Timeout (>2 hours)")
        return (track_id, False, "Timeout (>2 hours)")
        
    except Exception as e:
        logger.exception(f"[{track_id}] Exception occurred: {str(e)}")
        return (track_id, False, f"Exception: {str(e)}")


def main():
    """Run LorenzCycleToolkit for all selected cyclones."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()  # Also print to console
        ]
    )
    logger = logging.getLogger('main')
    
    print("=" * 80)
    print("STEP 2: Running LorenzCycleToolkit for EP1 Cyclones")
    print("=" * 80)
    print(f"\nLog file: {LOG_FILE}")
    
    logger.info("Starting step2_run_lec_toolkit.py")
    logger.info(f"Log file: {LOG_FILE}")
    
    # Check prerequisites
    logger.info("Checking prerequisites...")
    if not check_prerequisites():
        logger.error("Prerequisites check failed")
        return 1
    logger.info("Prerequisites check passed")
    
    # Get list of track files
    track_files = sorted(TRACKS_DIR.glob("track_*.txt"))
    n_total = len(track_files)
    
    print(f"\n2. Processing configuration:")
    print(f"   Total cyclones: {n_total}")
    print(f"   Parallel workers: {N_WORKERS}")
    print(f"   Temporal resolution: {TIME_RESOLUTION} hours")
    print(f"   LorenzCycleToolkit: {LORENZ_SCRIPT}")
    print(f"   Results directory: {RESULTS_DIR}")
    
    # Check how many are already processed
    already_processed = [f for f in track_files if is_already_processed(f.stem.replace('track_', ''))]
    print(f"\n   Already processed: {len(already_processed)}/{n_total}")
    if len(already_processed) > 0:
        print(f"   These will be skipped")
    
    print(f"\n3. Starting parallel processing...")
    print(f"   Using conda environment: {LORENZ_CONDA_ENV}")
    print(f"   Note: This may take several hours depending on:")
    print(f"   - Number of cyclones to process")
    print(f"   - CDS API response time")
    print(f"   - Cyclone lifecycle duration")
    print(f"\n   Progress updates will appear as cyclones complete.")
    print(f"   You can monitor: {RESULTS_DIR}")
    print(f"   Real-time log: tail -f {LOG_FILE}")
    print()
    
    logger.info(f"Starting parallel processing of {n_total} cyclones with {N_WORKERS} workers")
    start_time = time.time()
    
    # Process cyclones in parallel
    logger.info("Launching worker pool...")
    with mp.Pool(processes=N_WORKERS) as pool:
        results = pool.map(process_cyclone, track_files)
    
    logger.info("All workers completed")
    
    # Analyze results
    successes = [(tid, msg) for tid, success, msg in results if success]
    failures = [(tid, msg) for tid, success, msg in results if not success]
    
    elapsed_time = time.time() - start_time
    elapsed_hours = elapsed_time / 3600
    
    # Summary
    logger.info(f"Processing completed. Successes: {len(successes)}, Failures: {len(failures)}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal time: {elapsed_hours:.2f} hours ({elapsed_time:.0f} seconds)")
    print(f"Average time per cyclone: {elapsed_time / n_total:.0f} seconds")
    
    print(f"\n✅ Successful: {len(successes)}/{n_total}")
    if len(successes) > 0:
        # Count actually processed vs skipped
        processed = [tid for tid, msg in successes if 'skipped' not in msg.lower()]
        skipped = [tid for tid, msg in successes if 'skipped' in msg.lower()]
        
        if len(processed) > 0:
            print(f"   Newly processed: {len(processed)}")
            print(f"   Examples:")
            for tid in processed[:5]:
                print(f"      - {tid}")
        
        if len(skipped) > 0:
            print(f"   Skipped (already done): {len(skipped)}")
    
    print(f"\n❌ Failed: {len(failures)}/{n_total}")
    if len(failures) > 0:
        print(f"\n   Failed cyclones:")
        for tid, msg in failures[:10]:  # Show first 10 failures
            print(f"      - {tid}: {msg}")
        
        if len(failures) > 10:
            print(f"      ... and {len(failures) - 10} more")
        
        # Save failures to file
        failures_file = RESULTS_DIR / "failed_cyclones.txt"
        with open(failures_file, 'w') as f:
            f.write("# Failed cyclones from step2_run_lec_toolkit.py\n")
            f.write(f"# Total failures: {len(failures)}\n\n")
            for tid, msg in failures:
                f.write(f"{tid}: {msg}\n")
        
        print(f"\n   Full failure log saved to: {failures_file}")
        print(f"\n   Common reasons for failure:")
        print(f"   - CDS API rate limits (too many concurrent requests)")
        print(f"   - Network connectivity issues")
        print(f"   - Invalid track data")
        print(f"   - Insufficient disk space")
        print(f"\n   To retry failed cyclones:")
        print(f"   1. Fix any issues (check CDS API status, disk space, etc.)")
        print(f"   2. Re-run this script (successfully processed ones will be skipped)")
    
    if len(successes) > 0 and len(failures) == 0:
        print(f"\n✓ All cyclones processed successfully!")
        print(f"  Results saved to: {RESULTS_DIR}")
        print(f"\nNext step:")
        print(f"   Run step3_extract_subterms.py to analyze Ck subterm contributions")
    elif len(successes) > 0:
        print(f"\n✓ Partial success: {len(successes)} cyclones processed")
        print(f"  You can proceed to step3 with available data,")
        print(f"  or re-run this script to retry failed cyclones")
    
    print("\n" + "=" * 80)
    
    return 1 if len(failures) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
