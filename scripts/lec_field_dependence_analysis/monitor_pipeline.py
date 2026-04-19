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
    StepDef("3b", "Derive dynamic ERA5 fields",
            ["step3b_derived_field_manifest.csv"], ["lec_field_step3b", "step3b_chunk"],
            chunk_output_pattern="step3b_derived_field_manifest_chunk*.csv"),
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
    STALE   = "STALE"    # log from a previous run, output was cleaned

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

def _pipeline_has_no_status() -> bool:
    """True when no pipeline_status.txt exists (no active or recently active run)."""
    return not STATUS_FILE.exists()


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

    # --- Step 8b: figure-count based detection ---
    if step.key == "8b":
        fig_count = len(list(FIGURES_DIR.glob("significance_*.png"))) + \
                    len(list(FIGURES_DIR.glob("effect_*.png"))) + \
                    len(list(FIGURES_DIR.glob("volcano_*.png")))
        # Use log success marker as primary signal, figure count as detail
        if recent_log and _log_has_success(recent_log, step.key):
            return Status.DONE, f"{fig_count} figures", last_log_ts
        if fig_count > 0 and recent_log and not _log_has_error(recent_log) \
                and not _log_is_recent(recent_log):
            # Stale log without error + figures present → treat as done
            return Status.DONE, f"{fig_count} figures", last_log_ts
        if recent_log and _log_has_error(recent_log):
            return Status.FAILED, _extract_error_line(recent_log), last_log_ts
        if recent_log and _log_is_recent(recent_log):
            return Status.RUNNING, f"{fig_count} figures so far", last_log_ts
        if fig_count > 0:
            return Status.DONE, f"{fig_count} figures", last_log_ts
        return Status.PENDING, "—", last_log_ts

    # All primary outputs present → DONE
    if outputs_total > 0 and len(outputs_present) == outputs_total:
        return Status.DONE, f"{len(outputs_present)}/{outputs_total} files", last_log_ts

    # For chunked steps: chunk files alone are valid output when log
    # confirms success (downstream steps read chunks directly).
    if step.chunk_output_pattern and chunk_count > 0:
        # Check if ANY of the step's logs contain the success marker
        all_logs = _find_recent_logs(step.log_prefix)
        any_success = any(_log_has_success(l, step.key) for l in all_logs[:5])
        any_error   = any(_log_has_error(l) for l in all_logs[:5])
        if any_success and not any_error:
            return Status.DONE, f"{chunk_count} chunks", last_log_ts
        # Chunks exist but no success marker: could still be running
        if recent_log and _log_is_recent(recent_log):
            return Status.RUNNING, f"{chunk_count} chunks so far", last_log_ts
        # Stale log with chunks but no success → check for errors
        if any_error:
            detail = _extract_error_line(all_logs[0]) if all_logs else "see log"
            return Status.FAILED, detail, last_log_ts
        # Chunks exist, no recent activity, no success/error in logs
        # Accept as done if chunk count is reasonable (≥ n_chunks)
        if chunk_count >= 10:
            return Status.DONE, f"{chunk_count} chunks (no merge needed)", last_log_ts
        return Status.PARTIAL, f"{chunk_count} chunks", last_log_ts

    # Log-based checks
    if recent_log:
        if _log_has_success(recent_log, step.key):
            # success marker present but output file missing:
            # if no pipeline is running/registered, this is a stale log from
            # a previous run whose outputs were cleaned — show as STALE, not FAILED
            if outputs_total > 0 and not outputs_present:
                if _pipeline_has_no_status():
                    return Status.STALE, "prev run log (output cleaned)", last_log_ts
                return Status.FAILED, "log OK but output missing", last_log_ts
            detail = "done (log)"
            return Status.DONE, detail, last_log_ts

        if _log_has_error(recent_log):
            detail = _extract_error_line(recent_log)
            return Status.FAILED, detail, last_log_ts

        if _log_is_recent(recent_log):
            last_line = _log_tail(recent_log, 1)[:60]
            return Status.RUNNING, last_line or "active", last_log_ts

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
    Status.STALE:   C.DIM,
}

STATUS_ICONS = {
    Status.DONE:    "✓",
    Status.RUNNING: "▶",
    Status.FAILED:  "✗",
    Status.PENDING: "·",
    Status.PARTIAL: "◑",
    Status.STALE:   "~",
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
              Status.PENDING: 0, Status.PARTIAL: 0, Status.STALE: 0}

    for step in STEPS:
        status, detail, last_ts = check_step(step)
        counts[status] = counts.get(status, 0) + 1

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

    # Active log tails — show last message from recently active or completed steps
    shown_tails = False
    for step in STEPS:
        logs = _find_recent_logs(step.log_prefix)
        if not logs:
            continue
        latest = logs[0]
        status_for_step, _, _ = check_step(step)
        # Show tail for: running, failed, or recently completed steps
        # STALE logs are from previous cleaned runs — do not show their tails
        show = (status_for_step != Status.STALE
                and (show_log_tail
                     or status_for_step in (Status.RUNNING, Status.FAILED)
                     or (status_for_step == Status.DONE and _log_is_recent(latest))))
        if not show:
            continue
        tail = _log_tail(latest, 3)
        if not tail:
            continue
        label = f"  [{step.key}] {step.label}"
        if use_color:
            col = C.RED if status_for_step == Status.FAILED else C.DIM
            lines.append(f"{col}{label}:{C.RESET}")
            lines.append(f"{col}    {tail[:90]}{C.RESET}")
        else:
            lines.append(f"{label}:")
            lines.append(f"    {tail[:90]}")
        lines.append("")
        shown_tails = True

    # Show orchestrator log tail if pipeline recently active
    orch_logs = sorted(LOG_DIR.glob("orchestrator_*.log"),
                       key=lambda f: f.stat().st_mtime, reverse=True) \
                if LOG_DIR.exists() else []
    if orch_logs:
        orch_tail = _log_tail(orch_logs[0], 4)
        if orch_tail and (show_log_tail or _log_is_recent(orch_logs[0])):
            if use_color:
                lines.append(f"{C.DIM}  [orchestrator]:{C.RESET}")
                lines.append(f"{C.DIM}    {orch_tail[:90]}{C.RESET}")
            else:
                lines.append("  [orchestrator]:")
                lines.append(f"    {orch_tail[:90]}")
            lines.append("")
            shown_tails = True

    if not shown_tails:
        lines.append("")

    # Paths
    lines.append(f"{C.DIM if use_color else ''}  Results: {RESULTS_DIR}{C.RESET if use_color else ''}")
    lines.append(f"{C.DIM if use_color else ''}  Logs:    {LOG_DIR}{C.RESET if use_color else ''}")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Deep verification (--verify)
# ---------------------------------------------------------------------------
def verify() -> str:
    """
    Deep-check all pipeline outputs: expected files, row counts, figure counts,
    log errors.  Returns a detailed report string.
    """
    import csv as _csv

    lines: list[str] = []
    ok_count = 0
    warn_count = 0
    fail_count = 0

    def _ok(msg: str):
        nonlocal ok_count
        ok_count += 1
        lines.append(f"  ✓  {msg}")

    def _warn(msg: str):
        nonlocal warn_count
        warn_count += 1
        lines.append(f"  ⚠  {msg}")

    def _fail(msg: str):
        nonlocal fail_count
        fail_count += 1
        lines.append(f"  ✗  {msg}")

    def _csv_rows(path: Path) -> int:
        try:
            with open(path) as f:
                reader = _csv.reader(f)
                next(reader)  # header
                return sum(1 for _ in reader)
        except Exception:
            return -1

    lines.append("=" * 80)
    lines.append("  LEC Field Dependence Pipeline — Deep Verification Report")
    lines.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    # --- Step 1 ---
    lines.append("[Step 1] Consolidate metadata")
    f1 = RESULTS_DIR / "step1_eligible_cases.csv"
    if f1.exists():
        n = _csv_rows(f1)
        if n > 100:
            _ok(f"step1_eligible_cases.csv — {n} cyclones")
        else:
            _warn(f"step1_eligible_cases.csv — only {n} cyclones (expected >100)")
    else:
        _fail("step1_eligible_cases.csv MISSING")
    lines.append("")

    # --- Step 2 ---
    lines.append("[Step 2] Build LEC table")
    f2 = RESULTS_DIR / "step2_lec_intensification_means.csv"
    if f2.exists():
        n = _csv_rows(f2)
        _ok(f"step2_lec_intensification_means.csv — {n} rows")
    else:
        _fail("step2_lec_intensification_means.csv MISSING")
    lines.append("")

    # --- Step 3 ---
    lines.append("[Step 3] Map ERA5 fields")
    f3 = RESULTS_DIR / "step3_era5_field_manifest.csv"
    if f3.exists():
        n = _csv_rows(f3)
        _ok(f"step3_era5_field_manifest.csv — {n} rows")
    else:
        _fail("step3_era5_field_manifest.csv MISSING")
    lines.append("")

    # --- Step 3b ---
    lines.append("[Step 3b] Derive dynamic ERA5 fields")
    f3b = RESULTS_DIR / "step3b_derived_field_manifest.csv"
    chunks_3b = sorted(RESULTS_DIR.glob("step3b_derived_field_manifest_chunk*.csv"))
    if f3b.exists():
        n = _csv_rows(f3b)
        try:
            import pandas as _pd3b
            df3b = _pd3b.read_csv(f3b)
            n_ok_derived = (df3b.get("status", df3b.get("_status", _pd3b.Series(["ok"] * len(df3b)))) == "ok").sum()
            _ok(f"step3b_derived_field_manifest.csv — {n} rows ({n_ok_derived} derived OK)")
        except Exception:
            _ok(f"step3b_derived_field_manifest.csv — {n} rows")
    elif chunks_3b:
        _ok(f"{len(chunks_3b)} chunk manifest files found (merged manifest not yet written — OK)")
    else:
        _fail(
            "step3b_derived_field_manifest.csv MISSING — step 3b was not run.\n"
            "       → Steps 4 and 5 require derived files from step 3b.\n"
            "       → If step 4/5 results show all-NaN features, this is the root cause.\n"
            "       → Fix: run step 3b before steps 4 and 5."
        )
    lines.append("")

    def _check_feature_csv(label: str, path: Path, chunks: list) -> None:
        """Check feature CSV for existence + non-null rate across feature columns."""
        import pandas as pd
        if path.exists():
            n = _csv_rows(path)
            try:
                df_feat = pd.read_csv(path)
                feat_cols = [c for c in df_feat.columns if "__" in c]
                if not feat_cols:
                    _warn(f"{path.name} — {n} rows but NO feature columns found")
                    lines.append("       → Re-run step 4/5 without --skip-done to rebuild features.")
                else:
                    pct = df_feat[feat_cols].notna().mean().mean() * 100
                    if pct < 50:
                        _fail(f"{path.name} — {n} rows, {len(feat_cols)} feature cols, "
                              f"only {pct:.0f}% non-null (sparse extraction!)")
                        lines.append("       → Root cause: step 3b was likely not run before steps 4/5.")
                        lines.append(f"       → Fix: run step 3b, then delete {path.name} and re-run.")
                    elif pct < 90:
                        _warn(f"{path.name} — {n} rows, {len(feat_cols)} feature cols, "
                              f"{pct:.0f}% non-null (expected ≥90%)")
                    else:
                        _ok(f"{path.name} — {n} rows, {len(feat_cols)} feature cols, {pct:.0f}% non-null")
            except Exception as e:
                _warn(f"{path.name} — could not inspect feature columns: {e}")
        elif chunks:
            _ok(f"{len(chunks)} chunk files (no merged CSV — OK, step6 reads chunks directly)")
        else:
            _fail(f"{label}: MISSING — no merged CSV and no chunk files found")

    # --- Step 4 ---
    lines.append("[Step 4] Extract absolute features")
    chunks4 = sorted(RESULTS_DIR.glob("step4_features_absolute_chunk*.csv"))
    _check_feature_csv("step4_features_absolute",
                       RESULTS_DIR / "step4_features_absolute.csv", chunks4)
    lines.append("")

    # --- Step 5 ---
    lines.append("[Step 5] Extract anomaly features")
    chunks5 = sorted(RESULTS_DIR.glob("step5_features_anomaly_chunk*.csv"))
    _check_feature_csv("step5_features_anomaly",
                       RESULTS_DIR / "step5_features_anomaly.csv", chunks5)
    lines.append("")

    # --- Step 6 ---
    lines.append("[Step 6] Integrate tables")
    import pandas as _pd
    for fname in ["step6_integrated_all.csv", "step6_integrated_absolute.csv",
                   "step6_integrated_anomaly.csv"]:
        fp = RESULTS_DIR / fname
        if fp.exists():
            n = _csv_rows(fp)
            if n < 30:
                _warn(f"{fname} — only {n} rows (expected ≥30)")
                continue
            try:
                df6 = _pd.read_csv(fp)
                feat_cols6 = [c for c in df6.columns if "__" in c]
                if feat_cols6:
                    pct6 = df6[feat_cols6].notna().mean().mean() * 100
                    if pct6 < 50:
                        _fail(f"{fname} — {n} rows, {pct6:.0f}% feature non-null "
                              f"(sparse — bad ERA5 run propagated)")
                        lines.append(f"       → Fix: delete {fname} + step4/5 CSVs and re-run from step 4.")
                    else:
                        _ok(f"{fname} — {n} rows, {len(feat_cols6)} feature cols, {pct6:.0f}% non-null")
                else:
                    _ok(f"{fname} — {n} rows (LEC+metadata only, no ERA5 feature columns)")
            except Exception:
                _ok(f"{fname} — {n} rows")
        else:
            tag = fname.replace("step6_integrated_", "").replace(".csv", "")
            if tag == "all":
                _fail(f"{fname} MISSING")
            else:
                _warn(f"{fname} MISSING (optional if {tag} features not extracted)")
    lines.append("")

    # --- Step 7 ---
    lines.append("[Step 7] Compute PREDEP")
    for ftype in ["absolute", "anomaly"]:
        merged = RESULTS_DIR / f"step7_predep_{ftype}.csv"
        chunks = sorted(RESULTS_DIR.glob(f"step7_predep_{ftype}_chunk*.csv"))
        all_files = ([merged] if merged.exists() else []) + chunks
        total_rows = sum(_csv_rows(f) for f in all_files)
        if not all_files:
            _fail(f"step7_predep_{ftype}: no merged file and no chunks")
            continue
        label = f"step7_predep_{ftype}.csv" if merged.exists() else f"{len(chunks)} chunk files"
        try:
            sample_dfs = [_pd.read_csv(f) for f in all_files[:3]]
            sample = _pd.concat(sample_dfs, ignore_index=True)
            if "predep" not in sample.columns:
                _warn(f"step7_predep_{ftype}: {label}, {total_rows} rows — 'predep' column missing!")
            else:
                pct_valid = sample["predep"].notna().mean() * 100
                if pct_valid < 1:
                    _fail(f"step7_predep_{ftype}: {label}, {total_rows} rows — "
                          f"predep {pct_valid:.0f}% non-null (all NaN!)")
                    lines.append("       → All PREDEP computations excluded (n_valid < 30).")
                    lines.append("       → Root cause: feature columns are NaN in step4/5/6.")
                    lines.append("       → Fix: delete step4/5/6 outputs and re-run from step 4.")
                elif pct_valid < 30:
                    _warn(f"step7_predep_{ftype}: {label}, {total_rows} rows — "
                          f"predep {pct_valid:.0f}% non-null (many exclusions)")
                else:
                    _ok(f"step7_predep_{ftype}: {label}, {total_rows} rows, "
                        f"{pct_valid:.0f}% valid predep")
        except Exception as e:
            _warn(f"step7_predep_{ftype}: {label}, {total_rows} rows — could not sample: {e}")
    lines.append("")

    # --- Step 7b ---
    lines.append("[Step 7b] EP significance tests")
    f7b_diag = RESULTS_DIR / "step7b_diagnostic_table.csv"
    f7b_pair = RESULTS_DIR / "step7b_pairwise_table.csv"
    expected_8b_figs = 0
    n_data_blocks = 0
    if f7b_diag.exists():
        n_diag = _csv_rows(f7b_diag)
        _ok(f"step7b_diagnostic_table.csv — {n_diag} variables tested")
        # Check which blocks are present and their skip rate
        try:
            diag = _pd.read_csv(f7b_diag)
            _blk_defs = [
                ("LEC terms",  "var_type",   "LEC term"),
                ("absolute",   "field_type", "absolute"),
                ("anomaly",    "field_type", "anomaly"),
            ]
            blocks_found = []
            for blk_label, col, val in _blk_defs:
                if col not in diag.columns:
                    continue
                blk = diag[diag[col] == val]
                if len(blk) == 0:
                    continue
                blocks_found.append(blk_label)
                n_skip = (blk["global_test"] == "SKIPPED").sum() \
                         if "global_test" in blk.columns else 0
                pct_skip = n_skip / len(blk) * 100
                if pct_skip == 100:
                    _warn(f"  Block '{blk_label}': {len(blk)} variables — ALL SKIPPED "
                          f"(NaN features from bad ERA5 run)")
                    lines.append("       → Fix: delete step4/5/6 outputs and re-run from step 4.")
                elif pct_skip > 50:
                    _warn(f"  Block '{blk_label}': {len(blk)} variables, {pct_skip:.0f}% SKIPPED")
                    n_data_blocks += 1
                else:
                    n_sig_blk = (blk["global_p_adjusted"] < 0.05).sum() \
                                if "global_p_adjusted" in blk.columns else "?"
                    _ok(f"  Block '{blk_label}': {len(blk)} vars, "
                        f"{n_sig_blk} significant, {pct_skip:.0f}% skipped")
                    n_data_blocks += 1
            if blocks_found:
                pass  # already printed per-block
            else:
                _warn("  No recognizable blocks (var_type/field_type) in diagnostic table")
            n_sig = (diag["global_p_adjusted"] < 0.05).sum() \
                    if "global_p_adjusted" in diag.columns else "?"
            _ok(f"  Significant variables (p_adj < 0.05): {n_sig} / {n_diag}")
            has_pair = f7b_pair.exists() and _csv_rows(f7b_pair) > 0
            expected_8b_figs = n_data_blocks * (4 if has_pair else 2)
            lines.append(f"       Expected step8b figures: {expected_8b_figs} "
                         f"({n_data_blocks} data-bearing blocks × {'4' if has_pair else '2'} types)")
        except Exception as e:
            _warn(f"  Could not parse diagnostic table: {e}")
    else:
        _fail("step7b_diagnostic_table.csv MISSING")
    if f7b_pair.exists():
        n_pair = _csv_rows(f7b_pair)
        _ok(f"step7b_pairwise_table.csv — {n_pair} pairwise comparisons")
    else:
        _warn("step7b_pairwise_table.csv MISSING (no pairwise tests?)")
    lines.append("")

    # --- Step 8 ---
    lines.append("[Step 8] Synthesis figures (PREDEP)")
    f8_summary = RESULTS_DIR / "step8_summary_table.csv"
    if f8_summary.exists():
        n8 = _csv_rows(f8_summary)
        if n8 == 0:
            _fail("step8_summary_table.csv — 0 rows (all PREDEP values are NaN)")
            lines.append("       → Root cause: NaN feature columns in step4/5/6 → step7 excluded all rows.")
            lines.append("       → Fix: delete step4/5/6/7 outputs and re-run from step 4.")
        elif n8 < 10:
            _warn(f"step8_summary_table.csv — only {n8} rows (expected ≥10)")
        else:
            _ok(f"step8_summary_table.csv — {n8} rows")
    else:
        _fail("step8_summary_table.csv MISSING")
    # Count step8 figures
    s8_figs = (list(FIGURES_DIR.glob("heatmap_predep_*.png")) +
               list(FIGURES_DIR.glob("top_predep_*.png")) +
               list(FIGURES_DIR.glob("ep_comparison_*.png")))
    if s8_figs:
        _ok(f"Step 8 figures: {len(s8_figs)} files")
        for fg in sorted(s8_figs):
            lines.append(f"       {fg.name}")
    else:
        _warn("No step 8 figures found (heatmap_predep_*, top_predep_*, ep_comparison_*)")
    lines.append("")

    # --- Step 8b ---
    lines.append("[Step 8b] Significance figures")
    s8b_figs = (list(FIGURES_DIR.glob("significance_heatmap_*.png")) +
                list(FIGURES_DIR.glob("effect_size_heatmap_*.png")) +
                list(FIGURES_DIR.glob("volcano_*.png")) +
                list(FIGURES_DIR.glob("effect_ranking_*.png")))
    actual_8b = len(s8b_figs)
    if actual_8b == 0:
        _warn("No step 8b figures found")
    elif expected_8b_figs > 0 and actual_8b < expected_8b_figs:
        _warn(f"Step 8b figures: {actual_8b}/{expected_8b_figs} expected "
              f"({expected_8b_figs - actual_8b} missing — blocks with all-SKIPPED tests produce no figures)")
        for fg in sorted(s8b_figs):
            lines.append(f"       {fg.name}")
    else:
        _ok(f"Step 8b figures: {actual_8b} files")
        for fg in sorted(s8b_figs):
            lines.append(f"       {fg.name}")
    lines.append("")

    # --- Step 9 ---
    lines.append("[Step 9] Update docs")
    f9 = RESULTS_DIR / "step9_pipeline_status.txt"
    if f9.exists():
        _ok("step9_pipeline_status.txt present")
    else:
        _warn("step9_pipeline_status.txt MISSING")
    lines.append("")

    # --- Log errors scan ---
    lines.append("[Logs] Scanning for errors in pipeline logs...")
    import re as _re
    # Match only logs from this pipeline (lec_field_dependence) to avoid false positives
    # from other pipelines (e.g. ep_structure_analysis) that share the logs/ directory.
    _lec_log_re = _re.compile(
        r'^(lec_field_|orchestrator_|step[45]_chunk\d+_|step7_(absolute|anomaly)_chunk\d+_)',
        _re.IGNORECASE,
    )
    all_pipe_logs = [
        lp for lp in LOG_DIR.glob("*.log")
        if _lec_log_re.match(lp.name)
    ] if LOG_DIR.exists() else []
    all_pipe_logs.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    error_logs = [lp for lp in all_pipe_logs if _log_has_error(lp)]
    if error_logs:
        _warn(f"{len(error_logs)} log(s) contain ERROR/Traceback:")
        for lp in error_logs[:8]:
            err_line = _extract_error_line(lp)
            lines.append(f"       {lp.name}: {err_line}")
    else:
        _ok(f"No errors in {len(all_pipe_logs)} pipeline logs")
    lines.append("")

    # --- Summary ---
    lines.append("=" * 80)
    label = "ALL CHECKS PASSED" if fail_count == 0 and warn_count == 0 \
        else "PASSED WITH WARNINGS" if fail_count == 0 \
        else "ISSUES FOUND"
    lines.append(f"  {label}:  ✓ {ok_count} ok   ⚠ {warn_count} warnings   ✗ {fail_count} failures")
    lines.append("=" * 80)

    return "\n".join(lines)
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
    parser.add_argument("--verify", action="store_true",
                        help="Deep-check all outputs: row counts, figures, log errors")
    args = parser.parse_args()

    global LOG_DIR
    if args.log_dir:
        LOG_DIR = args.log_dir

    use_color = not args.no_color and sys.stdout.isatty()

    if args.verify:
        print(verify())
        return

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
