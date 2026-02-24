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

# Key files that indicate successful completion
REQUIRED_FILES = ["results.csv", "periods.csv"]

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

def is_cyclone_complete(track_id: str) -> bool:
    """
    Check if LEC analysis is complete for a cyclone.
    
    A cyclone is considered complete if its result directory exists and
    contains the required output files.
    """
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if not result_dir.exists():
        return False
    
    # Check for any required file
    for fname in REQUIRED_FILES:
        if (result_dir / fname).exists():
            return True
    
    # Also check for any *_level.csv files (alternative indicator)
    level_files = list(result_dir.glob("*_level.csv"))
    if len(level_files) > 0:
        return True
    
    return False


def get_processing_time(track_id: str) -> float | None:
    """
    Estimate processing time for a cyclone by checking log timestamps.
    
    Returns processing time in seconds, or None if cannot determine.
    """
    # Try to get time from result directory modification time
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if not result_dir.exists():
        return None
    
    # Get the modification time of results.csv (last file written)
    results_file = result_dir / "results.csv"
    if not results_file.exists():
        # Try any level file
        level_files = list(result_dir.glob("*_level.csv"))
        if len(level_files) == 0:
            return None
        results_file = level_files[0]
    
    # Get creation time from stdout log (start time)
    stdout_log = CYCLONE_LOG_DIR / f"{track_id}_stdout.log"
    
    if not stdout_log.exists():
        # Fallback: estimate from directory creation time
        return None
    
    try:
        # Start time = log file creation time
        start_time = stdout_log.stat().st_ctime
        # End time = result file modification time
        end_time = results_file.stat().st_mtime
        
        processing_time = end_time - start_time
        
        # Sanity check: ignore if > 24 hours (likely interrupted)
        if processing_time > MAX_PROCESSING_HOURS * 3600:
            return None
        
        # Sanity check: ignore if negative (clock issues)
        if processing_time < 0:
            return None
        
        return processing_time
        
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
            "pending": [],
            "processing_times": {},
            "total_size_bytes": 0,
        }
    
    completed = []
    pending = []
    processing_times = {}
    total_size_bytes = 0
    
    for track_file in track_files:
        # Extract track ID: track_19790205.txt -> 19790205
        track_id = track_file.stem.replace('track_', '')
        
        if is_cyclone_complete(track_id):
            completed.append(track_id)
            
            # Get processing time
            proc_time = get_processing_time(track_id)
            if proc_time is not None:
                processing_times[track_id] = proc_time
            
            # Get disk usage
            size_info = get_cyclone_size_info(track_id)
            total_size_bytes += size_info["total_bytes"]
        else:
            pending.append(track_id)
    
    return {
        "total": len(track_files),
        "completed": completed,
        "pending": pending,
        "processing_times": processing_times,
        "total_size_bytes": total_size_bytes,
    }


# ============================================================================
# STATISTICS
# ============================================================================

def compute_statistics(scan_data: dict):
    """
    Compute statistics from scan data.
    
    Returns dict with:
        - mean_time: mean processing time (seconds)
        - median_time: median processing time (seconds)
        - min_time: minimum processing time (seconds)
        - max_time: maximum processing time (seconds)
        - n_with_time: number of cyclones with valid processing time
        - eta_seconds: estimated time remaining (seconds)
    """
    times = list(scan_data["processing_times"].values())
    
    if len(times) == 0:
        return {
            "mean_time": None,
            "median_time": None,
            "min_time": None,
            "max_time": None,
            "n_with_time": 0,
            "eta_seconds": None,
        }
    
    mean_time = sum(times) / len(times)
    median_time = sorted(times)[len(times) // 2]
    min_time = min(times)
    max_time = max(times)
    
    # ETA calculation
    n_pending = len(scan_data["pending"])
    eta_seconds = mean_time * n_pending if n_pending > 0 else 0
    
    return {
        "mean_time": mean_time,
        "median_time": median_time,
        "min_time": min_time,
        "max_time": max_time,
        "n_with_time": len(times),
        "eta_seconds": eta_seconds,
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
    n_total = scan_data["total"]
    
    print()
    print(f"  Progress  {_bar(n_completed, n_total)}")
    print()
    print(f"  ✓ Completed: {n_completed}")
    print(f"  ⏳ Pending:  {len(scan_data['pending'])}")
    print(f"  📁 Total:    {n_total} cyclones")
    print()
    print(f"  💾 Disk:     {_fmt_bytes(scan_data['total_size_bytes'])}")
    
    # Processing time statistics
    print()
    print("  " + "─" * (W - 2))
    print("  PROCESSING TIME STATISTICS")
    print("  " + "─" * (W - 2))
    
    if stats["mean_time"] is not None:
        print(f"  Mean:        {format_runtime(stats['mean_time'])}")
        print(f"  Median:      {format_runtime(stats['median_time'])}")
        print(f"  Min:         {format_runtime(stats['min_time'])}")
        print(f"  Max:         {format_runtime(stats['max_time'])}")
        print(f"  Sample size: {stats['n_with_time']}/{n_completed} completed cyclones")
        print()
        
        # ETA
        if stats["eta_seconds"] is not None and stats["eta_seconds"] > 0:
            eta_str = format_eta(stats["eta_seconds"])
            eta_time = datetime.now() + timedelta(seconds=stats["eta_seconds"])
            eta_time_str = eta_time.strftime("%Y-%m-%d %H:%M")
            
            print(f"  ⏱  Estimated time remaining: {eta_str}")
            print(f"  🎯 Expected completion:     {eta_time_str}")
            print()
            print(f"     (Based on mean processing time of {format_runtime(stats['mean_time'])})")
            print(f"     (Cyclones taking >{MAX_PROCESSING_HOURS}h are excluded as likely interrupted)")
        elif len(scan_data["pending"]) == 0:
            print(f"  ✅ All cyclones completed!")
        else:
            print(f"  ⏱  ETA: Not yet available (need more completed cyclones)")
    else:
        print(f"  No timing data available yet.")
        print(f"  (Processing times will appear after first cyclone completes)")
    
    # Recent completions
    if n_completed > 0:
        print()
        print("  " + "─" * (W - 2))
        print("  RECENT COMPLETIONS (last 5)")
        print("  " + "─" * (W - 2))
        
        # Get last 5 completed (by result directory mtime)
        completed_with_time = []
        for track_id in scan_data["completed"]:
            result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
            if result_dir.exists():
                mtime = result_dir.stat().st_mtime
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
        print("  PENDING (next 5 to process)")
        print("  " + "─" * (W - 2))
        
        for track_id in scan_data["pending"][:5]:
            print(f"  {track_id}")
        
        if len(scan_data["pending"]) > 5:
            print(f"  ... and {len(scan_data['pending']) - 5} more")
    
    print()
    
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
