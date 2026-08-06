"""
step2_1_monitor.py — MSLP Download Progress Monitor (explosive cyclones)

Simple file-existence scan of data/era5_explosive_cyclones/ against the full
EP population (results/explosive_cyclones/ep_membership.csv): how many
{track_id}_mslp.nc files exist vs. how many are expected, per EP and overall,
with a live-refreshing progress bar. Meant to run alongside
step2_download_mslp_tracks.py (e.g. in a second terminal, or piped to a log
while that step runs under nohup).

Only checks file existence + mtime (no NetCDF opened), so scanning ~3800
files takes a fraction of a second.

Usage:
    # One-shot snapshot
    python scripts/explosive_cyclones_analysis/step2_1_monitor.py

    # Live refresh every 30 s (Ctrl+C to stop)
    python scripts/explosive_cyclones_analysis/step2_1_monitor.py --watch

    # Custom interval, no terminal clear (safe for nohup / log capture)
    python scripts/explosive_cyclones_analysis/step2_1_monitor.py --watch --interval 60 --no-clear

Author: Danilo Couto de Souza
Date: August 2026
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMBERSHIP_FILE = PROJECT_ROOT / "results" / "explosive_cyclones" / "ep_membership.csv"
DATA_DIR = PROJECT_ROOT / "data" / "era5_explosive_cyclones"

EP_LABELS = {1: "EP1", 2: "EP2", 3: "EP3"}
BAR_W = 30
DOWNLOAD_SCRIPT = "step2_download_mslp_tracks.py"


def _bar(n: int, total: int, width: int = BAR_W) -> str:
    frac = n / total if total else 0.0
    filled = int(width * frac)
    bar = "█" * filled + "░" * (width - filled)
    pad = len(str(total))
    return f"[{bar}]  {n:>{pad}}/{total}  ({frac * 100:5.1f}%)"


def detect_download_process():
    """Return dict with running/pid/runtime/cpu/mem for the step2 download process, if any."""
    if not HAS_PSUTIL:
        return {"running": False}
    for proc in psutil.process_iter(["pid", "cmdline", "create_time"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if any(DOWNLOAD_SCRIPT in arg for arg in cmdline):
                runtime = time.time() - proc.info["create_time"]
                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    mem_mb = proc.memory_info().rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu, mem_mb = None, None
                return {"running": True, "pid": proc.info["pid"],
                         "runtime": runtime, "cpu": cpu, "mem_mb": mem_mb}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return {"running": False}


def _fmt_runtime(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def scan(membership: pd.DataFrame) -> pd.DataFrame:
    """Return membership with an added 'done' bool and 'mtime' (or NaT) column."""
    done, mtimes = [], []
    for tid in membership["track_id"]:
        f = DATA_DIR / f"{tid}_mslp.nc"
        if f.exists():
            done.append(True)
            mtimes.append(f.stat().st_mtime)
        else:
            done.append(False)
            mtimes.append(None)
    out = membership.copy()
    out["done"] = done
    out["mtime"] = mtimes
    return out


def print_report(scanned: pd.DataFrame, proc_info: dict) -> None:
    W = 72
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print()
    print("═" * W)
    print("  EXPLOSIVE CYCLONES — MSLP DOWNLOAD MONITOR (step2)")
    print(f"  Scanned : {now}")
    print(f"  Dir     : {DATA_DIR}")

    if proc_info.get("running"):
        line = f"  ⬇ DOWNLOAD ACTIVE  PID={proc_info['pid']}  Runtime={_fmt_runtime(proc_info['runtime'])}"
        if proc_info.get("cpu") is not None:
            line += f"  CPU={proc_info['cpu']:.0f}%"
        if proc_info.get("mem_mb") is not None:
            line += f"  RAM={proc_info['mem_mb']:.0f}MB"
        print(line)
    elif HAS_PSUTIL:
        print("  ⏸  Download process: not running")
    else:
        print("  ⏸  Download process: unknown (pip install psutil for detection)")
    print("═" * W)

    for ep in (1, 2, 3):
        sub = scanned[scanned["ep"] == ep]
        if sub.empty:
            continue
        n_total = len(sub)
        n_done = int(sub["done"].sum())
        print()
        print(f"  {EP_LABELS[ep]}  {_bar(n_done, n_total)}")

    print()
    print("  " + "─" * (W - 2))
    n_total = len(scanned)
    n_done = int(scanned["done"].sum())
    n_missing = n_total - n_done
    print(f"  ALL   {_bar(n_done, n_total)}")
    print(f"        done: {n_done}   missing: {n_missing}")

    # Rough download rate / ETA from files created in the last 10 minutes
    recent_cutoff = time.time() - 600
    recent = scanned["mtime"].dropna()
    recent = recent[recent >= recent_cutoff]
    if len(recent) > 1 and n_missing > 0:
        rate_per_min = len(recent) / 10.0
        eta_min = n_missing / rate_per_min if rate_per_min > 0 else float("inf")
        eta_str = _fmt_runtime(eta_min * 60) if eta_min != float("inf") else "unknown"
        print(f"        recent rate: ~{rate_per_min:.1f} files/min (last 10 min)   "
              f"ETA: ~{eta_str}")
    elif n_missing > 0:
        print("        recent rate: no downloads in the last 10 min")

    if n_missing == 0:
        print()
        print("  ✓ All MSLP files downloaded. Next: step3_assign_central_pressure.py")
    print("═" * W)


def main():
    ap = argparse.ArgumentParser(description="Monitor MSLP download progress for explosive cyclones")
    ap.add_argument("--watch", "-w", action="store_true", help="Refresh continuously until Ctrl+C")
    ap.add_argument("--interval", "-i", type=int, default=30, help="Refresh interval in seconds (default 30)")
    ap.add_argument("--no-clear", action="store_true", help="Don't clear the terminal between refreshes")
    args = ap.parse_args()

    if not MEMBERSHIP_FILE.exists():
        print(f"❌ Missing {MEMBERSHIP_FILE}. Run step1 first.")
        return 1

    membership = pd.read_csv(MEMBERSHIP_FILE)

    def _run_once():
        scanned = scan(membership)
        proc_info = detect_download_process()
        if args.watch and not args.no_clear:
            os.system("clear")
        print_report(scanned, proc_info)

    if args.watch:
        print(f"  Monitoring every {args.interval}s (Ctrl+C to stop)…", flush=True)
        try:
            while True:
                _run_once()
                print(f"\n  Next refresh in {args.interval}s (Ctrl+C to stop)", flush=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n  Monitor stopped.")
    else:
        _run_once()
    return 0


if __name__ == "__main__":
    sys.exit(main())
