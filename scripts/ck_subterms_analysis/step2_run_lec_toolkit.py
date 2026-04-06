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
   - 3-hourly temporal resolution (matches track resolution)

Output:
- results/ck_analysis/lec_results/{track_id}_ERA5_track/
  ├── periods.csv              # Lifecycle phases
  ├── results.csv              # Integrated terms (all phases)
  ├── Ck_level.csv            # Total Ck by pressure level
  ├── Ck_uv_level.csv         # Horizontal momentum flux term
  ├── Ck_uw_level.csv         # Vertical momentum flux (zonal) term
  ├── Ck_vw_level.csv         # Vertical momentum flux (meridional) term
  └── ...                     # Other energy terms and figures

Processing:
- Parallel execution with configurable number of workers (default: 5)
- Multiple cyclones processed concurrently
- Progress updates as cyclones complete
- ThreadPoolExecutor manages concurrent jobs

Error Handling:
- Checks if LEC already computed (avoids reprocessing)
- Detailed logging of each step (download, execution, moving)
- Logs all successes and failures

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import subprocess
import time
import shutil
import logging
from datetime import datetime
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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
LOG_FILE = LOG_DIR / "step2_lec_current.log"  # Fixed name, will be overwritten
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

# LorenzCycleToolkit settings
# Use 3-hour temporal resolution
TIME_RESOLUTION = 3  # hours (was 6)
# Flags: -t (track), -r (residuals), -v (verbose), --cdsapi (auto download)
LEC_FLAGS = ['-t', '-r', '-v', '--cdsapi']

# Timeout per cyclone (in seconds)
# Set to None to disable timeout, or a value like 14400 (4 hours) if needed
TIMEOUT_SECONDS = None  # No timeout - let it run to completion

# Parallel execution settings
N_PARALLEL_JOBS = 5  # Number of cyclones to process concurrently


def update_lorenz_toolkit():
    """Update LorenzCycleToolkit from git repository."""
    
    print("\n1. Updating LorenzCycleToolkit...")
    
    if not LORENZ_TOOLKIT_DIR.exists():
        print(f"   ❌ Error: LorenzCycleToolkit directory not found: {LORENZ_TOOLKIT_DIR}")
        return False
    
    try:
        # Run git pull
        result = subprocess.run(
            ['git', 'pull'],
            cwd=str(LORENZ_TOOLKIT_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if 'Already up to date' in output or 'Already up-to-date' in output:
                print(f"   ✓ LorenzCycleToolkit is up to date")
            else:
                print(f"   ✓ LorenzCycleToolkit updated successfully")
                print(f"      {output.split(chr(10))[0]}")
            return True
        else:
            print(f"   ⚠ Warning: git pull failed: {result.stderr.strip()}")
            print(f"   Continuing with current version...")
            return True  # Continue anyway
            
    except Exception as e:
        print(f"   ⚠ Warning: Failed to update LorenzCycleToolkit: {e}")
        print(f"   Continuing with current version...")
        return True  # Continue anyway


def check_conda_environment():
    """Check if lorenz conda environment is properly configured."""
    
    print("\n2. Checking conda environment...")
    
    try:
        # Check if environment exists
        result = subprocess.run(
            ['conda', 'env', 'list'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if LORENZ_CONDA_ENV not in result.stdout:
            print(f"   ❌ Error: Conda environment '{LORENZ_CONDA_ENV}' not found")
            print(f"   Creating environment...")
            return recreate_conda_environment()
        
        # Check if required packages are installed
        result = subprocess.run(
            ['conda', 'run', '-n', LORENZ_CONDA_ENV, 'python', '-c',
             'import xarray, numpy, scipy, matplotlib, cdsapi, metpy; print("OK")'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and 'OK' in result.stdout:
            print(f"   ✓ Environment '{LORENZ_CONDA_ENV}' is properly configured")
            return True
        else:
            print(f"   ⚠ Environment '{LORENZ_CONDA_ENV}' is missing required packages")
            print(f"   Recreating environment...")
            return recreate_conda_environment()
            
    except Exception as e:
        print(f"   ⚠ Warning: Failed to check conda environment: {e}")
        print(f"   Attempting to recreate...")
        return recreate_conda_environment()


def recreate_conda_environment():
    """Remove and recreate the lorenz conda environment."""
    
    print(f"   Removing old environment '{LORENZ_CONDA_ENV}'...")
    
    try:
        # Remove existing environment
        subprocess.run(
            ['conda', 'env', 'remove', '-n', LORENZ_CONDA_ENV, '-y'],
            capture_output=True,
            timeout=120
        )
        
        # Check if there's an environment.yml in LorenzCycleToolkit
        env_file = LORENZ_TOOLKIT_DIR / "environment.yml"
        
        if env_file.exists():
            print(f"   Creating environment from {env_file}...")
            result = subprocess.run(
                ['conda', 'env', 'create', '-f', str(env_file)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
        else:
            # Create basic environment
            print(f"   Creating environment with basic packages...")
            result = subprocess.run(
                ['conda', 'create', '-n', LORENZ_CONDA_ENV, '-y',
                 'python=3.11', 'xarray', 'numpy', 'scipy', 'matplotlib',
                 'cdsapi', 'metpy', 'netcdf4', 'dask', '-c', 'conda-forge'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
        
        if result.returncode == 0:
            print(f"   ✓ Environment '{LORENZ_CONDA_ENV}' created successfully")
            return True
        else:
            print(f"   ❌ Failed to create environment: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to recreate environment: {e}")
        return False


def check_prerequisites():
    """Check if all prerequisites are met."""
    
    print("\n3. Checking prerequisites...")
    
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
    
    # Setup correct namelist for ERA5-cdsapi
    namelist_source = LORENZ_TOOLKIT_DIR / "inputs" / "namelist_ERA5-cdsapi"
    namelist_dest = LORENZ_TOOLKIT_DIR / "inputs" / "namelist"
    
    if not namelist_source.exists():
        print(f"   ❌ Error: ERA5-cdsapi namelist not found: {namelist_source}")
        return False
    
    # Copy namelist_ERA5-cdsapi to namelist
    try:
        shutil.copy2(namelist_source, namelist_dest)
        print(f"   ✓ Namelist configured for ERA5-cdsapi")
    except Exception as e:
        print(f"   ❌ Error copying namelist: {e}")
        return False
    
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
    Returns tuple: (is_processed, location) where location is 'project', 'lorenz', or None
    
    The function looks for evidence of completed LEC computation by checking for:
    1. Main results file: {track_id}_ERA5_track_results.csv
    2. Vertical levels directory: results_vertical_levels/
    3. Log file with completion marker: log.{track_id}_ERA5
    
    A case is considered "already processed" if it has the results CSV file
    (which is the primary output of LorenzCycleToolkit).
    """
    # Check in project results directory
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if result_dir.exists():
        # Primary indicator: main results CSV file
        # LorenzCycleToolkit generates: {track_id}_ERA5_track_results.csv
        results_csv = result_dir / f"{track_id}_ERA5_track_results.csv"
        
        if results_csv.exists():
            return True, 'project'
        
        # Fallback checks for older formats or partial results
        # (kept for backwards compatibility)
        possible_files = [
            result_dir / "results.csv",
            result_dir / "periods.csv",
        ]
        # Check for any level files (Ck, Ca, Ce, etc.)
        level_files = list(result_dir.glob("*_level.csv"))
        
        if any(f.exists() for f in possible_files) or len(level_files) > 0:
            return True, 'project'
    
    # Also check in LorenzCycleToolkit results directory
    lorenz_result_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if lorenz_result_dir.exists():
        # Check for main results CSV
        results_csv = lorenz_result_dir / f"{track_id}_ERA5_track_results.csv"
        
        if results_csv.exists():
            return True, 'lorenz'
        
        # Fallback checks
        possible_files = [
            lorenz_result_dir / "results.csv",
            lorenz_result_dir / "periods.csv",
        ]
        level_files = list(lorenz_result_dir.glob("*_level.csv"))
        
        if any(f.exists() for f in possible_files) or len(level_files) > 0:
            return True, 'lorenz'
    
    return False, None


def list_result_files(result_dir):
    """List all result files in a directory for logging purposes."""
    if not result_dir.exists():
        return []
    
    files = []
    for f in sorted(result_dir.iterdir()):
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            files.append(f"{f.name} ({size_kb:.1f} KB)")
    return files


def move_results_to_project(track_id, logger):
    """
    Move LEC results from LorenzCycleToolkit directory to project directory.
    
    Args:
        track_id: Cyclone track ID
        logger: Logger instance for detailed logging
        
    Returns:
        (success, message) tuple
    """
    source_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
    dest_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    try:
        if not source_dir.exists():
            return False, f"Source directory not found: {source_dir}"
        
        # List source files for logging
        source_files = list_result_files(source_dir)
        logger.info(f"[{track_id}] Source directory contains {len(source_files)} files:")
        for f in source_files[:10]:  # Show first 10
            logger.info(f"[{track_id}]   - {f}")
        if len(source_files) > 10:
            logger.info(f"[{track_id}]   ... and {len(source_files) - 10} more files")
        
        # Remove destination if it exists (to avoid conflicts)
        if dest_dir.exists():
            logger.info(f"[{track_id}] Removing existing destination: {dest_dir}")
            shutil.rmtree(dest_dir)
        
        # Move entire directory
        logger.info(f"[{track_id}] Moving results to: {dest_dir}")
        shutil.move(str(source_dir), str(dest_dir))
        
        # Verify move was successful
        if dest_dir.exists():
            dest_files = list_result_files(dest_dir)
            logger.info(f"[{track_id}] Successfully moved {len(dest_files)} files to project directory")
            return True, f"Moved {len(dest_files)} files successfully"
        else:
            return False, "Destination directory not found after move"
        
    except Exception as e:
        logger.exception(f"[{track_id}] Exception during move: {e}")
        return False, f"Exception during move: {str(e)}"


def parse_toolkit_output(stdout, stderr, logger, track_id):
    """
    Parse LorenzCycleToolkit output to extract detailed status information.
    
    Returns dict with status information about each step.
    """
    status = {
        'data_download': None,
        'data_processing': None,
        'lec_computation': None,
        'output_saved': None,
        'errors': [],
        'warnings': []
    }
    
    # Check stdout for progress indicators
    if stdout:
        if 'Downloading' in stdout or 'download' in stdout.lower():
            if 'successfully' in stdout.lower() or 'complete' in stdout.lower():
                status['data_download'] = 'success'
            elif 'error' in stdout.lower() or 'failed' in stdout.lower():
                status['data_download'] = 'failed'
            else:
                status['data_download'] = 'attempted'
        
        if 'Processing' in stdout or 'Computing' in stdout:
            status['data_processing'] = 'in_progress'
        
        if 'saved' in stdout.lower() or 'written' in stdout.lower():
            status['output_saved'] = 'success'
    
    # Check stderr for errors and warnings
    if stderr:
        lines = stderr.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'error' in line_lower:
                status['errors'].append(line.strip())
            elif 'warning' in line_lower:
                status['warnings'].append(line.strip())
    
    # Log parsed status
    logger.info(f"[{track_id}] Parsed status:")
    logger.info(f"[{track_id}]   Data download: {status['data_download']}")
    logger.info(f"[{track_id}]   Data processing: {status['data_processing']}")
    logger.info(f"[{track_id}]   Output saved: {status['output_saved']}")
    if status['errors']:
        logger.warning(f"[{track_id}]   Errors found: {len(status['errors'])}")
        for err in status['errors'][-5:]:  # Last 5 errors
            logger.warning(f"[{track_id}]     {err[:200]}")
    if status['warnings']:
        logger.info(f"[{track_id}]   Warnings found: {len(status['warnings'])}")
    
    return status


def process_cyclone(track_file, current_idx, total_count, logger):
    """
    Process a single cyclone using LorenzCycleToolkit (parallel version).
    
    Args:
        track_file: Path to track file
        current_idx: Current index (1-based) for progress display
        total_count: Total number of cyclones
        logger: Logger instance
        
    Returns:
        (track_id, success, message) tuple
    """
    # Extract track ID from filename: track_19790205.txt -> 19790205
    track_id = track_file.stem.replace('track_', '')
    
    progress_prefix = f"[{current_idx}/{total_count}]"
    
    # Check if already processed before starting
    is_processed, location = is_already_processed(track_id)
    if is_processed:
        msg = f"Already processed (found in {location})"
        print(f"   {progress_prefix} {track_id} - ✓ {msg} (skipping)")
        logger.info(f"[{track_id}] {msg}, skipping")
        return (track_id, True, msg)
    
    print(f"   {progress_prefix} {track_id} - Starting processing...")
    logger.info(f"[{track_id}] {'='*60}")
    logger.info(f"[{track_id}] Starting processing...")
    logger.info(f"[{track_id}] Track file: {track_file}")
    
    start_time = time.time()
    
    # Prepare log files for stdout/stderr (overwrite existing)
    stdout_log = CYCLONE_LOG_DIR / f"{track_id}_stdout.log"
    stderr_log = CYCLONE_LOG_DIR / f"{track_id}_stderr.log"
    
    try:
        # Prepare command
        output_file = f"{track_id}_ERA5.nc"
        
        cmd = [
            'conda', 'run', '-n', LORENZ_CONDA_ENV,
            'python',
            str(LORENZ_SCRIPT),
            output_file,
            *LEC_FLAGS,
            '--time-resolution', str(TIME_RESOLUTION),
            '--trackfile', str(track_file)
        ]
        
        logger.info(f"[{track_id}] Command: {' '.join(cmd)}")
        logger.info(f"[{track_id}] Working directory: {LORENZ_TOOLKIT_DIR}")
        logger.info(f"[{track_id}] Running LorenzCycleToolkit (this may take a while)...")
        
        # Run LorenzCycleToolkit - no timeout for serial execution
        result = subprocess.run(
            cmd,
            cwd=str(LORENZ_TOOLKIT_DIR),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS  # None = no timeout
        )
        
        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60
        
        # Save full output to files (overwrite existing)
        with open(stdout_log, 'w') as f:
            f.write(f"# LorenzCycleToolkit stdout for {track_id}\n")
            f.write(f"# Command: {' '.join(cmd)}\n")
            f.write(f"# Started: {datetime.now().isoformat()}\n")
            f.write(f"# Exit code: {result.returncode}\n")
            f.write(f"# Elapsed time: {elapsed_min:.1f} minutes\n")
            f.write("="*80 + "\n\n")
            f.write(result.stdout)
        
        with open(stderr_log, 'w') as f:
            f.write(f"# LorenzCycleToolkit stderr for {track_id}\n")
            f.write(f"# Command: {' '.join(cmd)}\n")
            f.write(f"# Started: {datetime.now().isoformat()}\n")
            f.write(f"# Exit code: {result.returncode}\n")
            f.write(f"# Elapsed time: {elapsed_min:.1f} minutes\n")
            f.write("="*80 + "\n\n")
            f.write(result.stderr)
        
        logger.info(f"[{track_id}] Execution completed in {elapsed_min:.1f} minutes")
        logger.info(f"[{track_id}] Exit code: {result.returncode}")
        logger.info(f"[{track_id}] Stdout saved to: {stdout_log}")
        logger.info(f"[{track_id}] Stderr saved to: {stderr_log}")
        
        # Parse output for detailed status
        status = parse_toolkit_output(result.stdout, result.stderr, logger, track_id)
        
        if result.returncode == 0:
            logger.info(f"[{track_id}] LorenzCycleToolkit completed successfully")
            
            # Check if results exist in LorenzCycleToolkit directory
            lorenz_result_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
            
            if lorenz_result_dir.exists():
                logger.info(f"[{track_id}] Results found in: {lorenz_result_dir}")
                
                # Move results to project directory
                move_success, move_msg = move_results_to_project(track_id, logger)
                
                if move_success:
                    # Verify results in project directory
                    is_valid, loc = is_already_processed(track_id)
                    if is_valid:
                        msg = f"Completed successfully ({elapsed_min:.1f} min)"
                        print(f"   {progress_prefix} {track_id} - ✓ {msg}")
                        logger.info(f"[{track_id}] ✓ {msg}")
                        return (track_id, True, msg)
                    else:
                        msg = f"Results moved but validation failed"
                        print(f"   {progress_prefix} {track_id} - ⚠ {msg}")
                        logger.warning(f"[{track_id}] {msg}")
                        # Still consider it a partial success - results exist
                        return (track_id, True, msg)
                else:
                    msg = f"Failed to move results: {move_msg}"
                    print(f"   {progress_prefix} {track_id} - ❌ {msg}")
                    logger.error(f"[{track_id}] {msg}")
                    return (track_id, False, msg)
            else:
                # Check if results went directly to project directory
                project_result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
                if project_result_dir.exists():
                    msg = f"Completed (results in project dir) ({elapsed_min:.1f} min)"
                    print(f"   {progress_prefix} {track_id} - ✓ {msg}")
                    logger.info(f"[{track_id}] ✓ {msg}")
                    return (track_id, True, msg)
                else:
                    msg = "Completed but no output directory found"
                    print(f"   {progress_prefix} {track_id} - ❌ {msg}")
                    logger.error(f"[{track_id}] {msg}")
                    logger.error(f"[{track_id}] Checked: {lorenz_result_dir}")
                    logger.error(f"[{track_id}] Checked: {project_result_dir}")
                    return (track_id, False, msg)
        else:
            # Extract error message (last non-empty lines)
            stderr_lines = [line for line in result.stderr.split('\n') if line.strip()]
            error_summary = stderr_lines[-5:] if len(stderr_lines) >= 5 else stderr_lines
            
            msg = f"Failed (exit code {result.returncode})"
            print(f"   {progress_prefix} {track_id} - ❌ {msg}")
            logger.error(f"[{track_id}] LorenzCycleToolkit failed with exit code {result.returncode}")
            logger.error(f"[{track_id}] Last stderr lines:")
            for line in error_summary:
                logger.error(f"[{track_id}]   {line}")
            logger.error(f"[{track_id}] Full logs: stdout={stdout_log}, stderr={stderr_log}")
            
            return (track_id, False, f"{msg}. Check {stderr_log}")
            
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60
        msg = f"Timeout after {elapsed_min:.1f} minutes"
        print(f"   {progress_prefix} {track_id} - ❌ {msg}")
        logger.error(f"[{track_id}] {msg}")
        return (track_id, False, msg)
        
    except Exception as e:
        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60
        msg = f"Exception after {elapsed_min:.1f} min: {str(e)}"
        print(f"   {progress_prefix} {track_id} - ❌ Exception: {str(e)}")
        logger.exception(f"[{track_id}] {msg}")
        return (track_id, False, msg)


def main():
    """Run LorenzCycleToolkit for all selected cyclones (parallel execution)."""
    
    # Remove old log file to overwrite
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    # Setup logging - overwrite mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),  # Overwrite mode
            logging.StreamHandler()  # Also print to console
        ]
    )
    logger = logging.getLogger('main')
    
    print("=" * 80)
    print("STEP 2: Running LorenzCycleToolkit for EP1 Cyclones (Parallel Execution)")
    print("=" * 80)
    print(f"\nLog file: {LOG_FILE}")
    
    logger.info("="*80)
    logger.info("Starting step2_run_lec_toolkit.py (Parallel Execution)")
    logger.info("="*80)
    logger.info(f"Log file: {LOG_FILE}")
    
    # Update LorenzCycleToolkit
    logger.info("Updating LorenzCycleToolkit...")
    if not update_lorenz_toolkit():
        logger.error("Failed to update LorenzCycleToolkit")
        return 1
    
    # Check conda environment
    logger.info("Checking conda environment...")
    if not check_conda_environment():
        logger.error("Failed to setup conda environment")
        return 1
    
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
    print(f"   Execution mode: PARALLEL ({N_PARALLEL_JOBS} concurrent jobs)")
    print(f"   Temporal resolution: {TIME_RESOLUTION} hours")
    print(f"   Timeout per cyclone: {'None (no limit)' if TIMEOUT_SECONDS is None else f'{TIMEOUT_SECONDS/3600:.1f} hours'}")
    print(f"   LorenzCycleToolkit: {LORENZ_SCRIPT}")
    print(f"   Results directory: {RESULTS_DIR}")
    
    logger.info(f"Total cyclones: {n_total}")
    logger.info(f"Execution mode: PARALLEL ({N_PARALLEL_JOBS} workers)")
    logger.info(f"Temporal resolution: {TIME_RESOLUTION} hours")
    logger.info(f"LorenzCycleToolkit: {LORENZ_SCRIPT}")
    logger.info(f"Results directory: {RESULTS_DIR}")
    
    # Check how many are already processed
    already_processed = []
    to_process = []
    for f in track_files:
        track_id = f.stem.replace('track_', '')
        is_done, loc = is_already_processed(track_id)
        if is_done:
            already_processed.append((track_id, loc))
        else:
            to_process.append(f)
    
    print(f"\n   Already processed: {len(already_processed)}/{n_total}")
    print(f"   To process: {len(to_process)}/{n_total}")
    if len(already_processed) > 0:
        print(f"   Already processed cases will be skipped")
        logger.info(f"Already processed: {len(already_processed)}/{n_total}")
        for tid, loc in already_processed[:5]:
            logger.info(f"  - {tid} (in {loc})")
        if len(already_processed) > 5:
            logger.info(f"  ... and {len(already_processed) - 5} more")
    
    logger.info(f"To process: {len(to_process)}/{n_total}")
    
    print(f"\n4. Starting parallel processing...")
    print(f"   Using conda environment: {LORENZ_CONDA_ENV}")
    print(f"   Concurrent jobs: {N_PARALLEL_JOBS}")
    print(f"   Note: This may take several hours depending on:")
    print(f"   - Number of cyclones to process")
    print(f"   - CDS API response time")
    print(f"   - Cyclone lifecycle duration")
    print(f"\n   Progress updates will appear as cyclones complete.")
    print(f"   You can monitor: {RESULTS_DIR}")
    print(f"   Real-time log: tail -f {LOG_FILE}")
    print()
    
    logger.info(f"Starting parallel processing with {N_PARALLEL_JOBS} workers...")
    start_time = time.time()
    
    # Process cyclones in parallel using ThreadPoolExecutor
    results = []
    completed_count = 0
    print(f"\n   Progress (completed/total):")
    
    with ThreadPoolExecutor(max_workers=N_PARALLEL_JOBS) as executor:
        # Submit all jobs
        future_to_track = {}
        for idx, track_file in enumerate(track_files, 1):
            future = executor.submit(process_cyclone, track_file, idx, n_total, logger)
            future_to_track[future] = (track_file, idx)
        
        # Process results as they complete
        for future in as_completed(future_to_track):
            track_file, idx = future_to_track[future]
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                # Log progress periodically
                if completed_count % 10 == 0:
                    elapsed = time.time() - start_time
                    elapsed_hours = elapsed / 3600
                    successes_so_far = sum(1 for _, s, _ in results if s)
                    logger.info(f"Progress: {completed_count}/{n_total} completed, {successes_so_far} successful, {elapsed_hours:.1f} hours elapsed")
            except Exception as e:
                track_id = track_file.stem.replace('track_', '')
                logger.exception(f"[{track_id}] Exception in future: {e}")
                results.append((track_id, False, f"Exception: {str(e)}"))
                completed_count += 1
    
    print(f"\n   All {n_total} cases completed!\n")
    logger.info("All cyclones processed")
    
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
    if n_total > 0:
        print(f"Average time per cyclone: {elapsed_time / n_total:.0f} seconds")
    
    print(f"\n✅ Successful: {len(successes)}/{n_total}")
    if len(successes) > 0:
        # Count actually processed vs skipped
        processed = [tid for tid, msg in successes if 'skipped' not in msg.lower() and 'already' not in msg.lower()]
        skipped = [tid for tid, msg in successes if 'skipped' in msg.lower() or 'already' in msg.lower()]
        
        if len(processed) > 0:
            print(f"   Newly processed: {len(processed)}")
            print(f"   Examples:")
            for tid in processed[:5]:
                print(f"      - {tid}")
            if len(processed) > 5:
                print(f"      ... and {len(processed) - 5} more")
        
        if len(skipped) > 0:
            print(f"   Skipped (already done): {len(skipped)}")
    
    print(f"\n❌ Failed: {len(failures)}/{n_total}")
    if len(failures) > 0:
        print(f"\n   Failed cyclones:")
        for tid, msg in failures[:10]:  # Show first 10 failures
            print(f"      - {tid}: {msg[:80]}")
        
        if len(failures) > 10:
            print(f"      ... and {len(failures) - 10} more")
        
        # Save failures to file
        failures_file = RESULTS_DIR / "failed_cyclones.txt"
        with open(failures_file, 'w') as f:
            f.write("# Failed cyclones from step2_run_lec_toolkit.py\n")
            f.write(f"# Run date: {datetime.now().isoformat()}\n")
            f.write(f"# Total failures: {len(failures)}\n\n")
            for tid, msg in failures:
                f.write(f"{tid}: {msg}\n")
        
        print(f"\n   Full failure log saved to: {failures_file}")
        print(f"\n   Common reasons for failure:")
        print(f"   - CDS API rate limits (reduce N_PARALLEL_JOBS if needed)")
        print(f"   - Network connectivity issues")
        print(f"   - Invalid track data (KeyError on valid_time)")
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
    
    logger.info("="*80)
    logger.info(f"Final summary: {len(successes)} successes, {len(failures)} failures")
    logger.info(f"Total time: {elapsed_hours:.2f} hours")
    logger.info("="*80)
    
    return 1 if len(failures) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
