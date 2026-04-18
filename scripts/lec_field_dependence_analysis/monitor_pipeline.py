"""
monitor_pipeline.py  —  LEC Field Dependence Analysis — Execution Monitor

Displays real-time status of all pipeline steps: which are done, running,
pending, or failed.  For chunked steps (4, 5, 7), shows chunk-level progress.

Usage:
    python monitor_pipeline.py
    python monitor_pipeline.py --watch              # refresh every 15s
    python monitor_pipeline.py --watch --interval 5  # refresh every 5s
    python monitor_pipeline.py --log-dir /custom/log/dir
    python monitor_pipeline.py --no-color

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import NamedTuple, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[1]
RESULTS_DIR = PROJECT_DIR / "results" / "lec_field_dependence"
LOG_DIR     = PROJECT_DIR / "logs"
FIGURES_DIR = PROJECT_DIR / "figures" / "lec_field_dependence"

PID_FILE    = LOG_DIR / "pipeline.pid"
STATUS_FILE = LOG_DIR / "pipeline_status.txt"

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"
    BLUE   = "\033[94m"

def no_color(s: str) -> str:
    import re
    return re.sub(r'\033\[[0-9;]*m', '', s)

# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------
class StepDef(NamedTuple):
    key: str              # e.g. "4", "7b"
    label: str            # Human-readable description
    outputs: list         # Primary output files (relative to RESULTS_DIR)
    log_prefix: list      # List of log file prefix patterns to search in LOG_DIR
    n_chunks: Optional[int] = None  # (unused — chunk count detected from files)
    chunk_output_pattern: Optional[str] = None  # glob pattern for chunk CSVs in RESULTS_DIR


STEPS: list[StepDef] = [
    StepDef("1",  "Consolidate metadata",
            ["step1_eligible_cases.csv"], ["lec_field_step1", "step1_"]),
    StepDef("2",  "Build LEC table",
            ["step2_lec_intensification_means.csv"], ["lec_field_step2", "step2_"]),
    StepDef("3",  "Map ERA5 fields",
            ["step3_era5_field_manifest.csv"], ["lec_field_step3", "step3_"]),
    StepDef("4",  "Extract absolute features",
            ["step4_features_absolute.csv"], ["lec_field_step4", "step4_chunk"],
            chunk_output_pattern="step4_features_absolute_chunk*.csv"),
    StepDef("5",  "Extract anomaly features",
            ["step5_features_anomaly.csv"], ["lec_field_step5", "step5_chunk"],
            chunk_output_pattern="step5_features_anomaly_chunk*.csv"),
    StepDef("6",  "Integrate tables",
            ["step6_integrated_all.csv"], ["lec_field_step6", "step6_"]),
    StepDef("7",  "Compute PREDEP",
            ["step7_predep_absolute.csv", "step7_predep_anomaly.csv"],
            ["lec_field_step7", "step7_absolute", "step7_anomaly"],
            chunk_output_pattern="step7_predep_*chunk*.csv"),
    StepDef("7b", "EP significance tests",
            ["step7b_diagnostic_table.csv", "step7b_pairwise_table.csv"],
            ["lec_field_step7b", "step7b_"]),
    StepDef("8",  "Synthesis figures (PREDEP)",
            ["step8_summary_table.csv"], ["lec_field_step8", "step8_"]),
    StepDef("8b", "Significance figures",
            [], ["lec_field_step8b", "step8b_"]),
    StepDef("9",  "Update docs",
            ["step9_pipeline_status.txt"], ["lec_field_step9", "step9_"]),
]

# ---------------------------------------------------------------------------
# Status detection
# ---------------------------------------------------------------------------
STALE_THRESHOLD_SECONDS = 300   # log file modified within this = "running"

# ---------------------------------------------------------------------------
# Pipeline-level (orchestrator) status
# ---------------------------------------------------------------------------

def _pid_is_alive(pid: int) -> bool:
    """Return True if the process with this PID is still running."""
    import os
    try:
        os.kill(pid, 0)   # signal 0: existence check only
        return True
    except (ProcessLookupError, PermissionError):
        return False   # ProcessLookupError = gone; PermissionError = exists but not ours (treat as alive)

def check_orchestrator() -> tuple[str, str, str]:
    """
    Returns (orch_status, detail_str, timestamp_str).
    orch_status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'UNKNOWN'
    """
    status_str = "UNKNOWN"
    detail     = "no status file"
    ts_str     = "—"

    # Try reading status file written by run_pipeline.sh
    if STATUS_FILE.exists():
        try:
            line = STATUS_FILE.read_text().strip().split("|")  # STATUS|epoch|pid
            status_str = line[0] if line else "UNKNOWN"
            epoch      = int(line[1]) if len(line) > 1 else None
            pid        = int(line[2]) if len(line) > 2 else None
            if epoch:
                ts_str = datetime.fromtimestamp(epoch).strftime("%H:%M:%S")
            if pid:
                detail = f"PID {pid}"
                if status_str == "RUNNING":
                    if _pid_is_alive(pid):
                        elapsed = int(time.time()) - epoch if epoch else 0
                        h, rem = divmod(elapsed, 3600)
                        m, s   = divmod(rem, 60)
                        detail = f"PID {pid}  running {h:02d}:{m:02d}:{s:02d}"
                    else:
                        # Process dead but status still says RUNNING → crashed
                        status_str = "CRASHED"
                        detail = f"PID {pid} no longer alive — may have crashed"
        except Exception as e:
            detail = f"parse error: {e}"

    elif PID_FILE.exists():
        # Fallback: only PID file, no status file
        try:
            pid = int(PID_FILE.read_text().strip())
            alive = _pid_is_alive(pid)
            status_str = "RUNNING" if alive else "STOPPED"
            detail     = f"PID {pid}" + (" (alive)" if alive else " (no longer alive)")
        except Exception:
            pass

    return status_str, detail, ts_str

class Status:
    DONE    = "DONE"
    RUNNING = "RUNNING"
    FAILED  = "FAILED"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"   # some chunks done, not all

def _find_recent_logs(prefix: str | list) -> list[Path]:
    """Return log files matching one or more prefix patterns, sorted newest first."""
    prefixes = [prefix] if isinstance(prefix, str) else prefix
    all_logs: list[Path] = []
    for p in prefixes:
        all_logs.extend(LOG_DIR.glob(f"{p}*.log"))
    return sorted(set(all_logs), key=lambda f: f.stat().st_mtime, reverse=True)

def _log_has_success(log_path: Path, step_key: str) -> bool:
    """Check if the log contains the canonical success marker."""
    try:
        text = log_path.read_text(errors="replace")
        marker = f"✓ Step {step_key} complete"
        return marker in text
    except Exception:
        return False

def _log_has_error(log_path: Path) -> bool:
    try:
        text = log_path.read_text(errors="replace")
        return "ERROR" in text or "Traceback" in text
    except Exception:
        return False

def _log_is_recent(log_path: Path) -> bool:
    """Return True if log file was modified recently (within stale threshold)."""
    try:
        age = time.time() - log_path.stat().st_mtime
        return age < STALE_THRESHOLD_SECONDS
    except Exception:
        return False

def _count_chunks(pattern: str) -> int:
    return len(list(RESULTS_DIR.glob(pattern)))

def _log_last_modified(log_path: Path) -> str:
    try:
        ts = log_path.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except Exception:
        return "—"

def _log_tail(log_path: Path, n_lines: int = 1) -> str:
    """Return the last n_lines of a log file as a single string."""
    try:
        lines = log_path.read_text(errors="replace").splitlines()
        return " | ".join(l.strip() for l in lines[-n_lines:] if l.strip())
    except Exception:
        return ""

def _extract_error_line(log_path: Path) -> str:
    """Find the first ERROR or Traceback line in a log file."""
    try:
        lines = log_path.read_text(errors="replace").splitlines()
        for line in reversed(lines):
            if "ERROR" in line or "Error" in line or "Traceback" in line:
                # Strip the timestamp prefix if present
                stripped = line.strip()
                parts = stripped.split("  ", 2)
                msg = parts[-1] if len(parts) >= 2 else stripped
                return msg[:58]
        return "error (see log)"
    except Exception:
        return "error (see log)"

def check_step(step: StepDef) -> tuple[str, str, str]:
    """
    Returns (status, detail_str, last_log_time_str).
    """

    # --- Check primary outputs ---
    outputs_present = [f for f in step.outputs if (RESULTS_DIR / f).exists()]
    outputs_total   = len(step.outputs)

    # --- Chunk accounting ---
    chunk_count = 0
    if step.chunk_output_pattern:
        chunk_count = _count_chunks(step.chunk_output_pattern)

    # --- Find most recent log file ---
    logs = _find_recent_logs(step.log_prefix)
    recent_log = logs[0] if logs else None
    last_log_ts = _log_last_modified(recent_log) if recent_log else "—"

    # --- Step 8b: check figures dir ---
    if step.key == "8b":
        fig_count = len(list(FIGURES_DIR.glob("significance_*.png"))) + \
                    len(list(FIGURES_DIR.glob("effect_*.png"))) + \
                    len(list(FIGURES_DIR.glob("volcano_*.png")))
        if fig_count >= 9:
            return Status.DONE, f"{fig_count} figures", last_log_ts
        if recent_log and _log_has_error(recent_log):
            return Status.FAILED, "see log", last_log_ts
        if recent_log and _log_is_recent(recent_log):
            return Status.RUNNING, f"{fig_count}/12 figures", last_log_ts
        return Status.PENDING, "—", last_log_ts

    # All primary outputs present → DONE
    if outputs_total > 0 and len(outputs_present) == outputs_total:
        return Status.DONE, f"{len(outputs_present)}/{outputs_total} files", last_log_ts

    # Log-based checks
    if recent_log:
        if _log_has_success(recent_log, step.key):
            # success marker present but output file missing (unusual)
            if outputs_total > 0 and not outputs_present:
                return Status.FAILED, "log OK but output missing", last_log_ts
            detail = f"{chunk_count} chunks" if chunk_count else "done (log)"
            return Status.DONE, detail, last_log_ts

        if _log_has_error(recent_log):
            detail = _extract_error_line(recent_log)
            return Status.FAILED, detail, last_log_ts

        if _log_is_recent(recent_log):
            # Chunk progress
            if step.chunk_output_pattern and chunk_count > 0:
                return Status.RUNNING, f"{chunk_count} chunks done so far", last_log_ts
            last_line = _log_tail(recent_log, 1)[:60]
            return Status.RUNNING, last_line or "active", last_log_ts

        # Stale log — may be a previous run that failed silently
        if chunk_count > 0 and outputs_total > 0 and not outputs_present:
            return Status.PARTIAL, f"{chunk_count} chunk files, main CSV missing", last_log_ts

    if chunk_count > 0:
        return Status.PARTIAL, f"{chunk_count} chunk files (no merged output)", last_log_ts

    return Status.PENDING, "—", "—"

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
STATUS_COLORS = {
    Status.DONE:    C.GREEN,
    Status.RUNNING: C.YELLOW,
    Status.FAILED:  C.RED,
    Status.PENDING: C.DIM,
    Status.PARTIAL: C.CYAN,
}

STATUS_ICONS = {
    Status.DONE:    "✓",
    Status.RUNNING: "▶",
    Status.FAILED:  "✗",
    Status.PENDING: "·",
    Status.PARTIAL: "◑",
}

def _color_status(status: str, use_color: bool) -> str:
    icon = STATUS_ICONS.get(status, "?")
    label = f"{icon} {status:<8}"
    if use_color:
        col = STATUS_COLORS.get(status, "")
        return f"{col}{label}{C.RESET}"
    return label

def render(use_color: bool = True, show_log_tail: bool = False) -> str:
    width = 100
    lines: list[str] = []

    border = "═" * width
    title  = " LEC Field Dependence Pipeline — Status Monitor "
    pad    = (width - len(no_color(title))) // 2

    lines.append(f"╔{border}╗")
    lines.append(f"║{' ' * pad}{C.BOLD}{title}{C.RESET}{' ' * (width - pad - len(no_color(title)))}║")
    ts_str = f"  Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  "
    ts_pad = width - len(ts_str)
    lines.append(f"║{ts_str}{' ' * ts_pad}║")
    lines.append(f"╚{border}╝")
    lines.append("")

    # --- Orchestrator status ---
    orch_status, orch_detail, orch_ts = check_orchestrator()
    ORCH_COLORS = {
        "RUNNING":   C.YELLOW,
        "COMPLETED": C.GREEN,
        "FAILED":    C.RED,
        "CRASHED":   C.RED,
        "STOPPED":   C.RED,
        "UNKNOWN":   C.DIM,
    }
    ORCH_ICONS = {
        "RUNNING":   "▶",
        "COMPLETED": "✓",
        "FAILED":    "✗",
        "CRASHED":   "✗",
        "STOPPED":   "✗",
        "UNKNOWN":   "?",
    }
    orch_icon = ORCH_ICONS.get(orch_status, "?")
    if use_color:
        col = ORCH_COLORS.get(orch_status, "")
        orch_line = f"  {col}{C.BOLD}Pipeline: {orch_icon} {orch_status}{C.RESET}   {orch_detail}   [{orch_ts}]"
    else:
        orch_line = f"  Pipeline: {orch_icon} {orch_status}   {orch_detail}   [{orch_ts}]"
    lines.append(orch_line)
    lines.append("")

    # Table header
    h_step   = "STEP"
    h_desc   = "DESCRIPTION"
    h_status = "STATUS    "
    h_detail = "PROGRESS / DETAIL"
    h_time   = "LAST LOG"
    if use_color:
        header = (f"{C.BOLD}{h_step:<5}  {h_desc:<32}  {h_status}  "
                  f"{h_detail:<40}  {h_time}{C.RESET}")
    else:
        header = f"{h_step:<5}  {h_desc:<32}  {h_status}  {h_detail:<40}  {h_time}"
    lines.append(header)
    lines.append("─" * width)

    counts = {Status.DONE: 0, Status.RUNNING: 0, Status.FAILED: 0,
              Status.PENDING: 0, Status.PARTIAL: 0}

    for step in STEPS:
        status, detail, last_ts = check_step(step)
        counts[status] += 1

        # Trim detail
        if len(detail) > 38:
            detail = detail[:35] + "..."

        status_str = _color_status(status, use_color)
        raw_status = f"{STATUS_ICONS.get(status, '?')} {status:<8}"
        # align: status column is 10 chars when plain
        if use_color:
            line = f"{step.key:<5}  {step.label:<32}  {status_str}  {detail:<40}  {last_ts}"
        else:
            line = f"{step.key:<5}  {step.label:<32}  {raw_status}  {detail:<40}  {last_ts}"
        lines.append(line)

    lines.append("─" * width)

    # Summary bar
    summary_parts = []
    for stat, icon in STATUS_ICONS.items():
        n = counts[stat]
        if n == 0:
            continue
        if use_color:
            col = STATUS_COLORS.get(stat, "")
            summary_parts.append(f"{col}{icon} {stat}: {n}{C.RESET}")
        else:
            summary_parts.append(f"{icon} {stat}: {n}")
    lines.append("  " + "   ".join(summary_parts))
    lines.append("")

    # Active log tails
    if show_log_tail:
        for step in STEPS:
            logs = _find_recent_logs(step.log_prefix)
            if logs and _log_is_recent(logs[0]):
                tail = _log_tail(logs[0], 3)
                if tail:
                    label = f"  [{step.key}] {step.label}"
                    if use_color:
                        lines.append(f"{C.DIM}{label}:{C.RESET}")
                        lines.append(f"{C.DIM}    {tail[:90]}{C.RESET}")
                    else:
                        lines.append(f"{label}:")
                        lines.append(f"    {tail[:90]}")
                    lines.append("")

    # Paths
    lines.append(f"{C.DIM if use_color else ''}  Results: {RESULTS_DIR}{C.RESET if use_color else ''}")
    lines.append(f"{C.DIM if use_color else ''}  Logs:    {LOG_DIR}{C.RESET if use_color else ''}")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Monitor LEC field dependence pipeline execution status"
    )
    parser.add_argument("--watch", action="store_true",
                        help="Continuously refresh the display")
    parser.add_argument("--interval", type=int, default=15,
                        help="Refresh interval in seconds when --watch is used (default: 15)")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI color output")
    parser.add_argument("--log-dir", type=Path, default=None,
                        help="Override log directory (default: <project>/logs/)")
    parser.add_argument("--log-tail", action="store_true",
                        help="Show last log lines for running steps")
    args = parser.parse_args()

    global LOG_DIR
    if args.log_dir:
        LOG_DIR = args.log_dir

    use_color = not args.no_color and sys.stdout.isatty()

    if args.watch:
        try:
            while True:
                output = render(use_color=use_color, show_log_tail=args.log_tail)
                if use_color:
                    # Clear screen
                    print("\033[2J\033[H", end="")
                else:
                    print("\n" + "=" * 40 + "\n")
                print(output)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
    else:
        print(render(use_color=use_color, show_log_tail=args.log_tail))


if __name__ == "__main__":
    main()
