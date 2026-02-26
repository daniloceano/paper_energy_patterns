"""
step2_monitor_ck.py — Progress Monitor for LorenzCycleToolkit Ck Analysis

Monitors the progress of step2_run_lec_toolkit.py which processes EP1 cyclones
through the LorenzCycleToolkit for Ck subterm decomposition.

Features:
- Detects if step2_run_lec_toolkit.py is currently running
- Shows progress (completed/total cyclones)
- Displays per-cyclone processing times
- Estimates time remaining based on average processing time
- Filters out stalled processes (>24h = likely interrupted)
- Watch mode for continuous monitoring

Usage:
    # One-shot report
    python scripts/ck_subterms_analysis/step2_monitor_ck.py

    # Live refresh every 60 s (run alongside step 2)
    python scripts/ck_subterms_analysis/step2_monitor_ck.py --watch

    # Custom refresh interval (30 s)
    python scripts/ck_subterms_analysis/step2_monitor_ck.py --watch --interval 30

    # No terminal clear — safe for nohup / log capture
    python scripts/ck_subterms_analysis/step2_monitor_ck.py --watch --no-clear

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
import os
import time
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACKS_DIR   = PROJECT_ROOT / "data" / "ck_analysis" / "tracks"
RESULTS_DIR  = PROJECT_ROOT / "results" / "ck_analysis" / "lec_results"
LOG_DIR      = PROJECT_ROOT / "results" / "ck_analysis" / "logs"
CYCLONE_LOG_DIR = LOG_DIR / "cyclones"

# Maximum processing time threshold (24 hours)
# Cyclones taking longer are considered stalled/interrupted
MAX_PROCESSING_HOURS = 24

# Key patterns that indicate successful completion
# LorenzCycleToolkit creates files like: {track_id}_ERA5_track_results.csv
RESULT_FILE_PATTERNS = ["*_results.csv", "*_trackfile"]

# ============================================================================
# PROCESS DETECTION
# ============================================================================

def detect_lec_process():
    """
    Detect if step2_run_lec_toolkit.py is currently running.
    
    Returns:
        dict with keys:
            - running: bool
            - pid: int or None
            - cpu_percent: float or None
            - memory_mb: float or None
            - runtime_seconds: float or None
    """
    if not HAS_PSUTIL:
        return {"running": False, "pid": None, "cpu_percent": None, 
                "memory_mb": None, "runtime_seconds": None}
    
    script_name = "step2_run_lec_toolkit.py"
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info.get('cmdline') or []
            # Check if this is a Python process running our script
            if any(script_name in arg for arg in cmdline):
                # Get process details
                pid = proc.info['pid']
                runtime = time.time() - proc.info['create_time']
                
                # Get CPU and memory (may take a moment)
                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    mem_mb = proc.memory_info().rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu = None
                    mem_mb = None
                
                return {
                    "running": True,
                    "pid": pid,
                    "cpu_percent": cpu,
                    "memory_mb": mem_mb,
                    "runtime_seconds": runtime,
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return {"running": False, "pid": None, "cpu_percent": None,
            "memory_mb": None, "runtime_seconds": None}


def format_runtime(seconds):
    """Format runtime in human-readable format."""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_eta(seconds):
    """Format ETA in human-readable format."""
    if seconds is None or seconds <= 0:
        return "N/A"
    
    td = timedelta(seconds=int(seconds))
    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or len(parts) == 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts)


# ============================================================================
# FILE SCANNING
# ============================================================================

def get_cyclone_status(track_id: str) -> str:
    """
    Check the processing status of a cyclone.
    
    Returns:
        'completed' - directory exists with final output files
        'in_progress' - directory exists but no final files yet
        'pending' - directory doesn't exist yet
    """
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if not result_dir.exists():
        return 'pending'
    
    # Check for result file patterns (LorenzCycleToolkit naming)
    for pattern in RESULT_FILE_PATTERNS:
        matching_files = list(result_dir.glob(pattern))
        if len(matching_files) > 0:
            return 'completed'
    
    # Also check for log completion message
    log_file = result_dir / f"log.{track_id}_ERA5"
    if log_file.exists():
        try:
            # Check last 5 lines for completion message
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    if 'Analysis complete' in line or 'ran in' in line:
                        return 'completed'
        except Exception:
            pass
    
    # Directory exists but no final files yet
    return 'in_progress'


def get_processing_time(track_id: str) -> float | None:
    """
    Extract processing time from LorenzCycleToolkit log file.
    
    Returns processing time in seconds, or None if cannot determine.
    Looks for line like: "Analysis complete! Moving framework ran in 953.41 seconds"
    """
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if not result_dir.exists():
        return None
    
    # Check the toolkit log file
    log_file = result_dir / f"log.{track_id}_ERA5"
    
    if not log_file.exists():
        return None
    
    try:
        # Read last 20 lines to find completion message
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        for line in reversed(lines[-20:]):
            if 'ran in' in line and 'seconds' in line:
                # Extract time from pattern: "ran in 953.41 seconds"

                match = re.search(r'ran in ([0-9.]+) seconds', line)
                if match:
                    processing_time = float(match.group(1))
                    
                    # Sanity check: ignore if > 24 hours (likely error in log)
                    if processing_time > MAX_PROCESSING_HOURS * 3600:
                        return None
                    
                    return processing_time
        
        return None
        
    except Exception:
        return None


def get_cyclone_size_info(track_id: str) -> dict:
    """
    Get information about cyclone result directory size.
    
    Returns dict with total_bytes and file_count.
    """
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if not result_dir.exists():
        return {"total_bytes": 0, "file_count": 0}
    
    total_bytes = 0
    file_count = 0
    
    try:
        for f in result_dir.rglob("*"):
            if f.is_file():
                total_bytes += f.stat().st_size
                file_count += 1
    except Exception:
        pass
    
    return {"total_bytes": total_bytes, "file_count": file_count}


def scan_all_cyclones():
    """
    Scan all track files and determine processing status.
    
    Returns dict with:
        - total: total number of cyclones
        - completed: list of completed track_ids
        - in_progress: list of in-progress track_ids
        - pending: list of pending track_ids
        - processing_times: dict of track_id -> processing time (seconds)
        - total_size_bytes: total disk usage
    """
    # Get all track files
    track_files = sorted(TRACKS_DIR.glob("track_*.txt"))
    
    if len(track_files) == 0:
        return {
            "total": 0,
            "completed": [],
            "in_progress": [],
            "pending": [],
            "processing_times": {},
            "total_size_bytes": 0,
        }
    
    completed = []
    in_progress = []
    pending = []
    processing_times = {}
    total_size_bytes = 0
    
    for track_file in track_files:
        # Extract track ID: track_19790205.txt -> 19790205
        track_id = track_file.stem.replace('track_', '')
        
        status = get_cyclone_status(track_id)
        
        if status == 'completed':
            completed.append(track_id)
            
            # Get processing time
            proc_time = get_processing_time(track_id)
            if proc_time is not None:
                processing_times[track_id] = proc_time
            
            # Get disk usage
            size_info = get_cyclone_size_info(track_id)
            total_size_bytes += size_info["total_bytes"]
            
        elif status == 'in_progress':
            in_progress.append(track_id)
            
            # Get disk usage (partial)
            size_info = get_cyclone_size_info(track_id)
            total_size_bytes += size_info["total_bytes"]
            
        else:  # pending
            pending.append(track_id)
    
    return {
        "total": len(track_files),
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
        "processing_times": processing_times,
        "total_size_bytes": total_size_bytes,
    }


# ============================================================================
# STATISTICS
# ============================================================================

def compute_statistics(scan_data: dict):
    """
    Compute statistics from scan data, excluding outliers.
    
    Uses IQR (Interquartile Range) method to identify outliers:
    - Outliers are values < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
    - Statistics are computed from filtered data (without outliers)
    - Outliers provide confidence margin (best/worst case scenarios)
    
    Returns dict with:
        - mean_time: mean processing time (seconds, without outliers)
        - median_time: median processing time (seconds)
        - min_time: minimum processing time (seconds, without outliers)
        - max_time: maximum processing time (seconds, without outliers)
        - n_with_time: number of cyclones with valid processing time
        - n_outliers: number of outliers excluded
        - outliers_low: list of low outliers (fast completions)
        - outliers_high: list of high outliers (slow completions)
        - margin_low: best case time (min of low outliers or min_time)
        - margin_high: worst case time (max of high outliers or max_time)
        - eta_seconds: estimated time remaining (seconds)
        - eta_best: best case ETA (seconds)
        - eta_worst: worst case ETA (seconds)
    """
    times = list(scan_data["processing_times"].values())
    
    if len(times) == 0:
        return {
            "mean_time": None,
            "median_time": None,
            "min_time": None,
            "max_time": None,
            "n_with_time": 0,
            "n_outliers": 0,
            "outliers_low": [],
            "outliers_high": [],
            "margin_low": None,
            "margin_high": None,
            "eta_seconds": None,
            "eta_best": None,
            "eta_worst": None,
        }
    
    # Need at least 4 samples for IQR to be meaningful
    if len(times) < 4:
        # Not enough data for outlier detection, use all values
        mean_time = sum(times) / len(times)
        sorted_times = sorted(times)
        median_time = sorted_times[len(times) // 2]
        min_time = min(times)
        max_time = max(times)
        
        n_pending = len(scan_data["pending"]) + len(scan_data["in_progress"])
        eta_seconds = mean_time * n_pending if n_pending > 0 else 0
        
        return {
            "mean_time": mean_time,
            "median_time": median_time,
            "min_time": min_time,
            "max_time": max_time,
            "n_with_time": len(times),
            "n_outliers": 0,
            "outliers_low": [],
            "outliers_high": [],
            "margin_low": min_time,
            "margin_high": max_time,
            "eta_seconds": eta_seconds,
            "eta_best": min_time * n_pending if n_pending > 0 else 0,
            "eta_worst": max_time * n_pending if n_pending > 0 else 0,
        }
    
    # Sort times for quartile calculation
    sorted_times = sorted(times)
    n = len(sorted_times)
    
    # Calculate quartiles
    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    q1 = sorted_times[q1_idx]
    q3 = sorted_times[q3_idx]
    iqr = q3 - q1
    
    # Define outlier thresholds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Separate inliers and outliers
    inliers = []
    outliers_low = []
    outliers_high = []
    
    for t in times:
        if t < lower_bound:
            outliers_low.append(t)
        elif t > upper_bound:
            outliers_high.append(t)
        else:
            inliers.append(t)
    
    # If outlier detection removed too many points, disable it
    if len(inliers) < max(3, len(times) * 0.5):
        # More than 50% marked as outliers - probably not real outliers
        inliers = times
        outliers_low = []
        outliers_high = []
    
    # Compute statistics from inliers
    mean_time = sum(inliers) / len(inliers)
    sorted_inliers = sorted(inliers)
    median_time = sorted_inliers[len(sorted_inliers) // 2]
    min_time = min(inliers)
    max_time = max(inliers)
    
    # Confidence margins from outliers
    margin_low = min(outliers_low) if outliers_low else min_time
    margin_high = max(outliers_high) if outliers_high else max_time
    
    # ETA calculations
    n_pending = len(scan_data["pending"]) + len(scan_data["in_progress"])
    eta_seconds = mean_time * n_pending if n_pending > 0 else 0
    eta_best = margin_low * n_pending if n_pending > 0 else 0
    eta_worst = margin_high * n_pending if n_pending > 0 else 0
    
    return {
        "mean_time": mean_time,
        "median_time": median_time,
        "min_time": min_time,
        "max_time": max_time,
        "n_with_time": len(times),
        "n_outliers": len(outliers_low) + len(outliers_high),
        "outliers_low": sorted(outliers_low),
        "outliers_high": sorted(outliers_high),
        "margin_low": margin_low,
        "margin_high": margin_high,
        "eta_seconds": eta_seconds,
        "eta_best": eta_best,
        "eta_worst": eta_worst,
    }


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

BAR_W = 40   # number of block characters in a progress bar


def _bar(n: int, total: int, width: int = BAR_W) -> str:
    """Return a Unicode block progress bar: [████░░░░]  n/total (xx.x%)."""
    frac  = n / total if total else 0.0
    filled = int(width * frac)
    bar   = "█" * filled + "░" * (width - filled)
    pad   = len(str(total))
    return f"[{bar}]  {n:>{pad}}/{total}  ({frac * 100:5.1f}%)"


def _fmt_bytes(n: float) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:6.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


# ============================================================================
# REPORT RENDERING
# ============================================================================

def print_report(
    scan_data: dict,
    stats: dict,
    proc_info: dict,
    scan_elapsed: float,
) -> None:
    """Render the full monitor report to stdout."""
    
    W   = 80
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print()
    print("═" * W)
    print("  LORENZ CYCLE TOOLKIT — Ck ANALYSIS PROGRESS MONITOR")
    print(f"  Scanned : {now}  ({scan_elapsed:.1f} s)")
    print(f"  Tracks  : {TRACKS_DIR}")
    print(f"  Results : {RESULTS_DIR}")
    
    # Process status
    if proc_info["running"]:
        runtime_str = format_runtime(proc_info["runtime_seconds"])
        status = f"  ⚙ PROCESSING ACTIVE  PID={proc_info['pid']}  Runtime={runtime_str}"
        if proc_info["cpu_percent"] is not None:
            status += f"  CPU={proc_info['cpu_percent']:.1f}%"
        if proc_info["memory_mb"] is not None:
            status += f"  RAM={proc_info['memory_mb']:.0f}MB"
        print(status)
    elif HAS_PSUTIL:
        print("  ⏸  Processing: not running")
    else:
        print("  ⏸  Processing: unknown (install psutil for detection)")
    
    print("═" * W)
    
    # Progress bar
    n_completed = len(scan_data["completed"])
    n_in_progress = len(scan_data["in_progress"])
    n_pending = len(scan_data["pending"])
    n_total = scan_data["total"]
    
    print()
    print(f"  Progress  {_bar(n_completed, n_total)}")
    print()
    print(f"  ✅ Completed:   {n_completed:>4}")
    print(f"  ⚙️  Processing:  {n_in_progress:>4}  (directory created, awaiting final files)")
    print(f"  ⏳ Pending:     {n_pending:>4}  (not started yet)")
    print(f"  {'─' * 20}")
    print(f"  📁 Total:       {n_total:>4} cyclones")
    print()
    print(f"  💾 Disk:        {_fmt_bytes(scan_data['total_size_bytes'])}")
    print()
    
    # If there are in-progress cyclones, show current activity
    if n_in_progress > 0:
        print(f"  ⚙️  Processing (not yet complete): {n_in_progress} cyclone(s)")
        print(f"     (Directory exists but missing final result files)")
        print()
        
        # Show just first 5 in-progress cyclones
        for track_id in scan_data["in_progress"][:5]:
            result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
            if result_dir.exists():
                # Count files in directory
                n_files = len(list(result_dir.glob("*.*")))
                dir_size = get_cyclone_size_info(track_id)["total_bytes"]
                
                print(f"     {track_id}  ({n_files} files, {_fmt_bytes(dir_size)})")
        
        if n_in_progress > 5:
            print(f"     ... and {n_in_progress - 5} more")
        print()
    
    # Processing time statistics
    print()
    print("  " + "─" * (W - 2))
    print("  PROCESSING TIME STATISTICS (from log files)")
    print("  " + "─" * (W - 2))
    
    if stats["mean_time"] is not None:
        # Show if outliers were excluded
        n_used = stats['n_with_time'] - stats['n_outliers']
        
        print(f"  Mean:        {format_runtime(stats['mean_time'])}")
        print(f"  Median:      {format_runtime(stats['median_time'])}")
        print(f"  Min:         {format_runtime(stats['min_time'])}")
        print(f"  Max:         {format_runtime(stats['max_time'])}")
        print(f"  Sample size: {n_used}/{n_completed} completed cyclones")
        
        # Show outlier information
        if stats['n_outliers'] > 0:
            print(f"  Outliers:    {stats['n_outliers']} excluded from statistics")
            
            if stats['outliers_low']:
                low_str = ", ".join([format_runtime(t) for t in stats['outliers_low'][:3]])
                if len(stats['outliers_low']) > 3:
                    low_str += f", ... ({len(stats['outliers_low'])} total)"
                print(f"    • Fast:    {low_str}")
            
            if stats['outliers_high']:
                high_str = ", ".join([format_runtime(t) for t in stats['outliers_high'][:3]])
                if len(stats['outliers_high']) > 3:
                    high_str += f", ... ({len(stats['outliers_high'])} total)"
                print(f"    • Slow:    {high_str}")
        
        # Show confidence margins
        if stats['margin_low'] != stats['min_time'] or stats['margin_high'] != stats['max_time']:
            print()
            print(f"  Confidence margin (from outliers):")
            print(f"    • Best case:  {format_runtime(stats['margin_low'])}")
            print(f"    • Worst case: {format_runtime(stats['margin_high'])}")
        
        # Show percentage of completed cyclones with valid timing data
        if n_completed > 0:
            pct_with_time = 100.0 * stats['n_with_time'] / n_completed
            if pct_with_time < 90:
                print(f"  ({pct_with_time:.1f}% of completed have timing data)")
        
        print()
        
        # ETA
        if stats["eta_seconds"] is not None and stats["eta_seconds"] > 0:
            eta_str = format_eta(stats["eta_seconds"])
            eta_time = datetime.now() + timedelta(seconds=stats["eta_seconds"])
            eta_time_str = eta_time.strftime("%Y-%m-%d %H:%M")
            
            n_remaining = n_in_progress + n_pending
            
            print(f"  ⏱  Estimated time remaining: {eta_str}")
            print(f"  🎯 Expected completion:     {eta_time_str}")
            
            # Show confidence interval for ETA
            if stats["eta_best"] is not None and stats["eta_worst"] is not None:
                eta_best_str = format_eta(stats["eta_best"])
                eta_worst_str = format_eta(stats["eta_worst"])
                
                if stats['n_outliers'] > 0:
                    print(f"     Confidence interval:    {eta_best_str} to {eta_worst_str}")
            
            print()
            print(f"     (Based on {n_remaining} remaining × mean {format_runtime(stats['mean_time'])})")
            
            if stats['n_outliers'] > 0:
                print(f"     ({stats['n_outliers']} outliers excluded; used for confidence margin)")
            else:
                print(f"     (No outliers detected in timing data)")
                
            print(f"     (Cyclones taking >{MAX_PROCESSING_HOURS}h excluded as likely interrupted)")
        elif n_in_progress + n_pending == 0:
            print(f"  ✅ All cyclones completed!")
        else:
            print(f"  ⏱  ETA: Not yet available (need more completed cyclones)")
    else:
        print(f"  No timing data available yet.")
        print(f"  (Processing times extracted from log files after completion)")
    
    # Recent completions
    if n_completed > 0:
        print()
        print("  " + "─" * (W - 2))
        print("  RECENT COMPLETIONS (last 5)")
        print("  " + "─" * (W - 2))
        
        # Get last 5 completed (by log file mtime or result directory mtime)
        completed_with_time = []
        for track_id in scan_data["completed"]:
            result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
            
            # Try to get completion time from log file
            log_file = result_dir / f"log.{track_id}_ERA5"
            if log_file.exists():
                mtime = log_file.stat().st_mtime
            elif result_dir.exists():
                mtime = result_dir.stat().st_mtime
            else:
                continue
            
            completed_with_time.append((track_id, mtime))
        
        completed_with_time.sort(key=lambda x: x[1], reverse=True)
        
        for track_id, mtime in completed_with_time[:5]:
            completed_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            proc_time = scan_data["processing_times"].get(track_id)
            
            if proc_time is not None:
                proc_str = format_runtime(proc_time)
                print(f"  {track_id}  completed {completed_time}  ({proc_str})")
            else:
                print(f"  {track_id}  completed {completed_time}")
    
    # Pending (next 5)
    if len(scan_data["pending"]) > 0:
        print()
        print("  " + "─" * (W - 2))
        print("  PENDING (next 5 not yet started)")
        print("  " + "─" * (W - 2))
        
        for track_id in scan_data["pending"][:5]:
            print(f"  {track_id}")
        
        if len(scan_data["pending"]) > 5:
            print(f"  ... and {len(scan_data['pending']) - 5} more")
    
    print()
    
    # Check for failed cyclones file
    failed_file = RESULTS_DIR / "failed_cyclones.txt"
    if failed_file.exists():
        try:
            # Check if file is old (more than 7 days)
            file_age_days = (time.time() - failed_file.stat().st_mtime) / 86400
            
            with open(failed_file, 'r') as f:
                lines = f.readlines()
            
            # Extract track IDs from failed file (format: "19790205: Failed...")
            failed_ids = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract track_id from start of line
                    parts = line.split(':')
                    if len(parts) > 0:
                        track_id = parts[0].strip()
                        # Only count as failed if NOT completed
                        if track_id in scan_data["pending"] or track_id in scan_data["in_progress"]:
                            failed_ids.append(track_id)
            
            if len(failed_ids) > 0:
                print("  " + "─" * (W - 2))
                print(f"  ⚠️  FAILED CYCLONES ({len(failed_ids)} still unresolved)")
                print("  " + "─" * (W - 2))
                print(f"  (Cyclones that failed and have NOT been successfully reprocessed)")
                print()
                for track_id in failed_ids[:5]:
                    print(f"  {track_id}")
                if len(failed_ids) > 5:
                    print(f"  ... and {len(failed_ids) - 5} more")
                print(f"\n  See: {failed_file}")
                print()
            elif file_age_days > 7:
                print("  " + "─" * (W - 2))
                print(f"  ℹ️  Note: Old failed_cyclones.txt found (age: {file_age_days:.1f} days)")
                print(f"     All listed failures have been successfully reprocessed.")
                print("  " + "─" * (W - 2))
                print()
        except Exception as e:
            pass
    
    # Footer notes
    if not HAS_PSUTIL:
        print("  " + "─" * (W - 2))
        print("  Note: Install psutil for process detection:")
        print("        pip install psutil")
        print()
    
    print("═" * W)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor LorenzCycleToolkit processing progress for Ck analysis.\n"
            "Tracks completed cyclones, estimates time remaining, and shows statistics."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--watch", "-w", action="store_true",
        help="Refresh continuously until Ctrl+C.",
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=60, metavar="SECS",
        help="Refresh interval in seconds for --watch mode (default: 60).",
    )
    parser.add_argument(
        "--no-clear", action="store_true",
        help="Do not clear the terminal between refreshes (safe for nohup/log capture).",
    )
    args = parser.parse_args()
    
    # Check if tracks directory exists
    if not TRACKS_DIR.exists():
        print(f"\n❌  Tracks directory not found: {TRACKS_DIR}")
        print("    Run step1_prepare_tracks.py first.\n")
        sys.exit(1)
    
    track_files = list(TRACKS_DIR.glob("track_*.txt"))
    if len(track_files) == 0:
        print(f"\n❌  No track files found in: {TRACKS_DIR}")
        print("    Run step1_prepare_tracks.py first.\n")
        sys.exit(1)
    
    def _run_once() -> None:
        t0 = time.monotonic()
        proc_info = detect_lec_process()
        scan_data = scan_all_cyclones()
        stats = compute_statistics(scan_data)
        elapsed = time.monotonic() - t0
        
        if args.watch and not args.no_clear:
            os.system("clear")
        print_report(scan_data, stats, proc_info, elapsed)
    
    if args.watch:
        print(f"  Monitoring every {args.interval} s  (Ctrl+C to stop)…", flush=True)
        try:
            while True:
                _run_once()
                print(
                    f"\n  Next refresh in {args.interval} s  (Ctrl+C to stop)",
                    flush=True,
                )
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n  Monitor stopped.")
    else:
        _run_once()


if __name__ == "__main__":
    main()
