#!/usr/bin/env bash
# =============================================================================
#  run_pipeline.sh  —  LEC Field Dependence Analysis — Remote Pipeline Runner
# =============================================================================
#
#  Orchestrates steps 3b–9 on a remote server.
#  Steps 1–3 MUST already have been run locally before using this script.
#
#  Usage:
#    bash run_pipeline.sh --era5-dir /data/era5/
#    bash run_pipeline.sh --era5-dir /data/era5/ --background          # nohup mode
#    bash run_pipeline.sh --era5-dir /data/era5/ --n-chunks 20 --workers 4
#    bash run_pipeline.sh --era5-dir /data/era5/ --skip-done
#    bash run_pipeline.sh --era5-dir /data/era5/ --only 3b,4,5,6
#    bash run_pipeline.sh --era5-dir /data/era5/ --clean                # wipe results+logs first
#    bash run_pipeline.sh --era5-dir /data/era5/ --clean --dry-run      # preview what would be deleted
#
#  Pipeline execution model:
#    Steps run SEQUENTIALLY.  The next step only starts after the previous one
#    finishes.  Within each heavy step (3b, 4, 5, 7) up to N_CHUNKS parallel
#    background jobs are used — that parallelism is internal to the step.
#
#  Options:
#    --era5-dir PATH       Path to per-cyclone raw ERA5 NetCDF files [REQUIRED]
#    --derived-dir PATH    Path for derived per-cyclone field files (*_era5_derived.nc)
#                          (default: {era5-dir}/derived/)
#                          Produced by step 3b; consumed by steps 4 and 5.
#    --background          Re-exec under nohup (survives SSH disconnect).
#                          Prints PID + log path and exits immediately.
#    --clean               Delete all previous results and pipeline logs before
#                          running, so the pipeline starts from a clean slate.
#                          Clears: results/lec_field_dependence/  figures/lec_field_dependence/
#                                  logs/step*  logs/orchestrator*  logs/nohup_pipeline*
#                                  logs/pipeline.pid  logs/pipeline_status.txt
#                          Combine with --dry-run to preview what would be deleted.
#    --dry-run             When used with --clean: list what would be deleted and exit.
#                          Has no effect without --clean.
#    --n-chunks N          Parallel chunks per heavy step (default: 16)
#    --workers N           CPU workers per chunk (default: 4)
#    --conda-env NAME      Conda environment to use (default: paper_energy_patterns)
#    --skip-done           Skip steps whose output files already exist
#    --stop-on-error       Halt the pipeline on the first failed step.
#                          Default: continue — all errors are logged and
#                          reported in the final summary.
#    --only STEPS          Run only these steps, e.g. "4,5,6" or "3b,4,5"
#
#  Error handling:
#    By default every step is attempted.  If a step fails, its exit code and
#    log file are recorded.  The pipeline continues.  At the end a summary
#    lists every failed step with the path to its log so you can inspect it
#    and decide whether to remove or rerun that step.
#    Use --stop-on-error to restore the old "halt at first failure" behaviour.
#
#  Notes:
#    - Steps 3b, 4, 5, 7 use parallel background jobs (n-chunks processes at once).
#    - Step 3b MUST complete before steps 4 and 5 (stored in --derived-dir).
#    - Step 6 handles chunk merging for steps 4 and 5 automatically.
#    - Step 8 handles chunk merging for step 7 automatically.
#    - All output goes to logs/ in the project root.
#
# =============================================================================

set -uo pipefail
ORIG_ARGS=("$@")   # Saved before parsing — used by --background re-exec

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PIPELINE_DIR="$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
ERA5_DIR=""
DERIVED_DIR=""
N_CHUNKS=16
N_WORKERS=4
CONDA_ENV="paper_energy_patterns"
SKIP_DONE=false
ONLY_STEPS=""
BACKGROUND=false
STOP_ON_ERROR=false
CLEAN=false
DRY_RUN=false

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --era5-dir)         ERA5_DIR="$2";     shift 2 ;;
        --derived-dir)      DERIVED_DIR="$2"; shift 2 ;;
        --n-chunks)         N_CHUNKS="$2";     shift 2 ;;
        --workers)          N_WORKERS="$2";    shift 2 ;;
        --conda-env)        CONDA_ENV="$2";    shift 2 ;;
        --skip-done)        SKIP_DONE=true;       shift   ;;
        --stop-on-error)    STOP_ON_ERROR=true;   shift   ;;
        --background)       BACKGROUND=true;      shift   ;;
        --only)             ONLY_STEPS="$2";      shift 2 ;;
        --clean)            CLEAN=true;             shift   ;;
        --dry-run)          DRY_RUN=true;           shift   ;;
        -h|--help)
            sed -n '/^#  Usage/,/^# ====/p' "$0" | head -n -1
            exit 0
            ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$ERA5_DIR" ]]; then
    echo "ERROR: --era5-dir is required." >&2
    echo "Run: bash run_pipeline.sh --help" >&2
    exit 1
fi

if [[ ! -d "$ERA5_DIR" ]]; then
    echo "ERROR: ERA5 directory not found: $ERA5_DIR" >&2
    exit 1
fi

# Derived directory defaults to {era5-dir}/derived/ (same default as step 3b)
if [[ -z "$DERIVED_DIR" ]]; then
    DERIVED_DIR="${ERA5_DIR%/}/derived"
fi

# ---------------------------------------------------------------------------
# Clean mode: remove previous results and pipeline logs
# ---------------------------------------------------------------------------
if $CLEAN; then
    _RESULTS_CLEAN="$PROJECT_DIR/results/lec_field_dependence"
    _FIGURES_CLEAN="$PROJECT_DIR/figures/lec_field_dependence"
    _LOGS_DIR="$PROJECT_DIR/logs"

    # Collect targets — bash 3.2-compatible (no mapfile)
    _RESULT_FILES=()
    while IFS= read -r f; do _RESULT_FILES+=("$f"); done < \
        <(find "$_RESULTS_CLEAN" -mindepth 1 -maxdepth 1 -type f 2>/dev/null | sort)

    _FIGURE_FILES=()
    while IFS= read -r f; do _FIGURE_FILES+=("$f"); done < \
        <(find "$_FIGURES_CLEAN" -mindepth 1 -maxdepth 1 -type f 2>/dev/null | sort)

    _LOG_FILES=()
    while IFS= read -r f; do _LOG_FILES+=("$f"); done < \
        <(find "$_LOGS_DIR" -maxdepth 1 -type f \( \
            -name "step*_*.log"           \
            -o -name "orchestrator_*.log" \
            -o -name "nohup_pipeline_*.log" \
            -o -name "pipeline.pid"       \
            -o -name "pipeline_status.txt" \
        \) 2>/dev/null | sort)

    _ALL_TARGETS=("${_RESULT_FILES[@]+"${_RESULT_FILES[@]}"}" "${_FIGURE_FILES[@]+"${_FIGURE_FILES[@]}"}" "${_LOG_FILES[@]+"${_LOG_FILES[@]}"}")

    echo "=== CLEAN MODE ==="
    if [[ ${#_ALL_TARGETS[@]} -eq 0 ]]; then
        echo "  Nothing to clean — output directories are already empty."
        $DRY_RUN && exit 0
    else
        echo "  Results  : ${#_RESULT_FILES[@]} file(s) in $_RESULTS_CLEAN"
        echo "  Figures  : ${#_FIGURE_FILES[@]} file(s) in $_FIGURES_CLEAN"
        echo "  Logs     : ${#_LOG_FILES[@]} file(s) in $_LOGS_DIR"
        echo ""
        if $DRY_RUN; then
            echo "  [DRY RUN] The following files would be deleted:"
            for f in "${_ALL_TARGETS[@]}"; do echo "    $f"; done
            exit 0
        fi
        echo "  Deleting..."
        for f in "${_ALL_TARGETS[@]}"; do
            rm -f "$f" && echo "    removed: $f"
        done
        echo "  Done. Clean slate ready."
    fi
    echo "=================="
    echo ""
fi

# ---------------------------------------------------------------------------
# Background mode: re-exec this script under nohup and exit the parent
# ---------------------------------------------------------------------------
if $BACKGROUND; then
    LOG_DIR_EARLY="$PROJECT_DIR/logs"
    mkdir -p "$LOG_DIR_EARLY"
    NOHUP_LOG="$LOG_DIR_EARLY/nohup_pipeline_$(date +%Y%m%d_%H%M%S).log"
    # Rebuild args without --background so the child does not fork again
    NEW_ARGS=()
    for arg in "${ORIG_ARGS[@]}"; do
        [[ "$arg" == "--background" ]] && continue
        NEW_ARGS+=("$arg")
    done
    echo "Starting pipeline in background (nohup)..."
    echo "  nohup log : $NOHUP_LOG"
    echo "  Monitor   : python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch"
    nohup bash "$SCRIPT_DIR/run_pipeline.sh" "${NEW_ARGS[@]}" > "$NOHUP_LOG" 2>&1 &
    BGPID=$!
    echo "  PID       : $BGPID"
    echo "$BGPID" > "$LOG_DIR_EARLY/pipeline.pid"
    printf 'RUNNING|%s|%s\n' "$(date +%s)" "$BGPID" > "$LOG_DIR_EARLY/pipeline_status.txt"
    exit 0
fi

# ---------------------------------------------------------------------------
# Paths and setup
# ---------------------------------------------------------------------------
RESULTS_DIR="$PROJECT_DIR/results/lec_field_dependence"
LOG_DIR="$PROJECT_DIR/logs"
TS=$(date +%Y%m%d_%H%M%S)
ORCH_LOG="$LOG_DIR/orchestrator_${TS}.log"

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

PYTHON="conda run -n $CONDA_ENV python"

PID_FILE="$LOG_DIR/pipeline.pid"
STATUS_FILE="$LOG_DIR/pipeline_status.txt"

# Write PID so the monitor can track this process
echo "$$" > "$PID_FILE"
printf 'RUNNING|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"

PIPELINE_START=$(date +%s)
STEP_ERRORS=0
FAILED_STEPS=()

# Cleanup on unexpected exit (SIGINT, SIGTERM, unhandled error)
_on_unexpected_exit() {
    local code=$?
    if [[ $code -ne 0 ]]; then
        printf 'FAILED|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"
        type _log &>/dev/null && _log "Pipeline terminated unexpectedly (exit $code)"
        if [[ ${#FAILED_STEPS[@]} -gt 0 ]]; then
            type _log &>/dev/null && _log "Steps that failed before termination:"
            for _entry in "${FAILED_STEPS[@]}"; do
                type _log &>/dev/null && _log "   ✗  $_entry"
            done
        fi
    fi
}
trap '_on_unexpected_exit' EXIT

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
_log() {
    local msg="$1"
    printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$ORCH_LOG"
}

_elapsed() {
    local start=$1
    local diff=$(( $(date +%s) - start ))
    printf "%02d:%02d:%02d" $((diff/3600)) $(( (diff%3600)/60 )) $((diff%60))
}

should_run() {
    local step="$1"
    if [[ -z "$ONLY_STEPS" ]]; then
        return 0  # run all
    fi
    [[ ",$ONLY_STEPS," == *",$step,"* ]] && return 0
    return 1
}

output_ready() {
    # Returns true if the primary output exists OR any chunk file of that output exists
    local base="$1"
    [[ -f "$base" ]] && return 0
    # Check for chunk files: base_chunk0.csv
    local stem="${base%.csv}"
    compgen -G "${stem}_chunk*.csv" > /dev/null 2>&1 && return 0
    return 1
}

# Run a single (non-chunked) step.
# On failure: records in FAILED_STEPS and continues unless --stop-on-error.
run_single() {
    local step="$1"
    local cmd="$2"
    local step_start=$(date +%s)
    local step_log="$LOG_DIR/${step}_${TS}.log"

    _log "START  [$step]"
    if eval "$cmd" >> "$step_log" 2>&1; then
        _log "DONE   [$step]  elapsed=$(_elapsed $step_start)  log=$(basename $step_log)"
        return 0
    else
        local exit_code=$?
        _log "FAILED [$step] (exit $exit_code)  elapsed=$(_elapsed $step_start)"
        _log "       Log: $step_log"
        STEP_ERRORS=$(( STEP_ERRORS + 1 ))
        FAILED_STEPS+=("[$step]  exit=$exit_code  log=$step_log")
        if $STOP_ON_ERROR; then
            _log "Halting (--stop-on-error is set)."
            printf 'FAILED|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"
            trap - EXIT
            exit 1
        fi
        return 1
    fi
}

# Run N_CHUNKS parallel background jobs, wait, and collect per-chunk exit codes.
# On failure: logs which chunks failed with their log paths, records in
# FAILED_STEPS, and continues unless --stop-on-error.
run_chunks() {
    local step="$1"
    local n="$2"
    local cmd_tmpl="$3"     # use {CHUNK} as placeholder for chunk index
    local step_start=$(date +%s)

    _log "START  [$step]  launching $n parallel chunks..."

    local pids=()
    local chunk_logs=()
    for i in $(seq 0 $(( n - 1 ))); do
        local chunk_log="$LOG_DIR/${step}_chunk${i}_${TS}.log"
        chunk_logs+=("$chunk_log")
        local cmd="${cmd_tmpl//\{CHUNK\}/$i}"
        eval "$cmd" >> "$chunk_log" 2>&1 &
        pids+=($!)
    done

    local failed_chunks=()
    for i in "${!pids[@]}"; do
        if ! wait "${pids[$i]}"; then
            failed_chunks+=("chunk${i}")
        fi
    done

    local n_failed=${#failed_chunks[@]}
    if [[ $n_failed -gt 0 ]]; then
        _log "FAILED [$step]  $n_failed/$n chunks failed  elapsed=$(_elapsed $step_start)"
        _log "       Failed chunks and their logs:"
        for fc in "${failed_chunks[@]}"; do
            local idx="${fc#chunk}"
            _log "         $LOG_DIR/${step}_${fc}_${TS}.log"
        done
        STEP_ERRORS=$(( STEP_ERRORS + 1 ))
        FAILED_STEPS+=("[$step]  $n_failed/$n chunks failed: ${failed_chunks[*]}  logs: $LOG_DIR/${step}_chunk*_${TS}.log")
        if $STOP_ON_ERROR; then
            _log "Halting (--stop-on-error is set)."
            printf 'FAILED|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"
            trap - EXIT
            exit 1
        fi
        return 1
    fi

    _log "DONE   [$step]  all $n chunks OK  elapsed=$(_elapsed $step_start)"
    return 0
}

# ---------------------------------------------------------------------------
# Print header
# ---------------------------------------------------------------------------
_log "=================================================================="
_log " LEC Field Dependence Pipeline"
_log " Project dir:     $PROJECT_DIR"
_log " ERA5 dir:        $ERA5_DIR"
_log " Derived dir:     $DERIVED_DIR"
_log " Chunks:          $N_CHUNKS"
_log " Workers/chunk:   $N_WORKERS"
_log " Conda env:       $CONDA_ENV"
_log " Skip done:       $SKIP_DONE"
_log " Only steps:      ${ONLY_STEPS:-all}"
_log " Orch log:        $ORCH_LOG"
_log "=================================================================="

cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Step 1 — Consolidate metadata
# ---------------------------------------------------------------------------
if should_run 1; then
    if $SKIP_DONE && [[ -f "$RESULTS_DIR/step1_eligible_cases.csv" ]]; then
        _log "SKIP   [step1]  output already exists"
    else
        run_single "step1" \
            "$PYTHON $PIPELINE_DIR/step1_consolidate_metadata.py"
    fi
fi

# ---------------------------------------------------------------------------
# Step 2 — Build LEC table
# ---------------------------------------------------------------------------
if should_run 2; then
    if $SKIP_DONE && [[ -f "$RESULTS_DIR/step2_lec_means.csv" ]]; then
        _log "SKIP   [step2]  output already exists"
    else
        run_single "step2" \
            "$PYTHON $PIPELINE_DIR/step2_build_lec_table.py"
    fi
fi

# ---------------------------------------------------------------------------
# Step 3 — Map ERA5 field availability
# ---------------------------------------------------------------------------
if should_run 3; then
    if $SKIP_DONE && [[ -f "$RESULTS_DIR/step3_era5_field_manifest.csv" ]]; then
        _log "SKIP   [step3]  output already exists"
    else
        run_single "step3" \
            "$PYTHON $PIPELINE_DIR/step3_map_era5_fields.py --era5-dir $ERA5_DIR"
    fi
fi

# ---------------------------------------------------------------------------
# Step 3b — Derive dynamic ERA5 fields per cyclone
#   MUST run before steps 4 and 5.  Reads raw ERA5 NetCDFs from --era5-dir
#   and writes derived files (*_era5_derived.nc) to --derived-dir.
# ---------------------------------------------------------------------------
if should_run 3b; then
    if $SKIP_DONE && [[ -f "$RESULTS_DIR/step3b_derived_field_manifest.csv" ]]; then
        _log "SKIP   [step3b]  manifest already exists"
    else
        CMD="$PYTHON $PIPELINE_DIR/step3b_derive_era5_fields.py \
            --era5-dir $ERA5_DIR --derived-dir $DERIVED_DIR \
            --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
        run_chunks "step3b" $N_CHUNKS "$CMD"
    fi
fi

# ---------------------------------------------------------------------------
# Step 4 — Extract absolute features
# ---------------------------------------------------------------------------
if should_run 4; then
    if $SKIP_DONE && output_ready "$RESULTS_DIR/step4_features_absolute.csv"; then
        _log "SKIP   [step4]  output already exists"
    else
        CMD="$PYTHON $PIPELINE_DIR/step4_extract_features_absolute.py \
            --era5-dir $ERA5_DIR --derived-dir $DERIVED_DIR \
            --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
        run_chunks "step4" $N_CHUNKS "$CMD"
    fi
fi

# ---------------------------------------------------------------------------
# Step 5 — Extract anomaly features
# ---------------------------------------------------------------------------
if should_run 5; then
    if $SKIP_DONE && output_ready "$RESULTS_DIR/step5_features_anomaly.csv"; then
        _log "SKIP   [step5]  output already exists"
    else
        CMD="$PYTHON $PIPELINE_DIR/step5_extract_features_anomaly.py \
            --era5-dir $ERA5_DIR --derived-dir $DERIVED_DIR \
            --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
        run_chunks "step5" $N_CHUNKS "$CMD"
    fi
fi

# ---------------------------------------------------------------------------
# Step 6 — Integrate tables  (merges chunk files from steps 4 and 5)
# ---------------------------------------------------------------------------
if should_run 6; then
    if $SKIP_DONE && [[ -f "$RESULTS_DIR/step6_integrated_all.csv" ]]; then
        _log "SKIP   [step6]  output already exists"
    else
        run_single "step6" \
            "$PYTHON $PIPELINE_DIR/step6_integrate_tables.py"
    fi
fi

# --- Coverage guard after step6 ---
# If the integrated table exists but has too few rows, the ERA5 dir was wrong.
if should_run 6 || should_run 4 || should_run 5; then
    INT_FILE="$RESULTS_DIR/step6_integrated_all.csv"
    if [[ -f "$INT_FILE" ]]; then
        N_ROWS=$(tail -n +2 "$INT_FILE" | wc -l | tr -d ' ')
        MIN_ROWS=30
        if [[ $N_ROWS -lt $MIN_ROWS ]]; then
            _log "ERROR  [coverage-guard]  step6_integrated_all.csv has only $N_ROWS rows (expected >=$MIN_ROWS)."
            _log "       Possible causes:"
            _log "         1. Step 3b was not run or failed — derived fields are missing."
            _log "         2. ERA5 directory ('$ERA5_DIR') has no per-cyclone NetCDF files."
            _log "         3. Derived dir ('$DERIVED_DIR') is empty or mismatched."
            _log "       Check the paths and rerun: --only 3b,4,5,6,7,7b,8,8b,9 --skip-done"
            STEP_ERRORS=$(( STEP_ERRORS + 1 ))
            FAILED_STEPS+=("[coverage-guard]  step6 has $N_ROWS rows (<$MIN_ROWS) — check --era5-dir")
            if $STOP_ON_ERROR; then
                printf 'FAILED|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"
                trap - EXIT
                exit 1
            fi
        fi
        _log "INFO   coverage check OK: $N_ROWS rows in integrated table"
    fi
fi

# ---------------------------------------------------------------------------
# Step 7 — Compute PREDEP (absolute first, then anomaly — sequential)
# ---------------------------------------------------------------------------
if should_run 7; then
    _skip_abs="$RESULTS_DIR/step7_predep_absolute.csv"
    _skip_anom="$RESULTS_DIR/step7_predep_anomaly.csv"

    CMD_ABS="$PYTHON $PIPELINE_DIR/step7_compute_predep.py \
        --field-type absolute \
        --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
    CMD_ANOM="$PYTHON $PIPELINE_DIR/step7_compute_predep.py \
        --field-type anomaly \
        --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"

    if $SKIP_DONE && output_ready "$_skip_abs"; then
        _log "SKIP   [step7-absolute]  output already exists"
    else
        run_chunks "step7_absolute" $N_CHUNKS "$CMD_ABS"
    fi

    if $SKIP_DONE && output_ready "$_skip_anom"; then
        _log "SKIP   [step7-anomaly]  output already exists"
    else
        run_chunks "step7_anomaly" $N_CHUNKS "$CMD_ANOM"
    fi
fi

# ---------------------------------------------------------------------------
# Step 7b — Significance tests between EPs
# ---------------------------------------------------------------------------
if should_run 7b; then
    if $SKIP_DONE && [[ -f "$RESULTS_DIR/step7b_diagnostic_table.csv" ]]; then
        _log "SKIP   [step7b]  output already exists"
    else
        run_single "step7b" \
            "$PYTHON $PIPELINE_DIR/step7b_ep_significance_tests.py"
    fi
fi

# ---------------------------------------------------------------------------
# Step 8 — Synthesis figures (PREDEP heatmaps; reads chunks from step 7 directly)
# ---------------------------------------------------------------------------
if should_run 8; then
    run_single "step8" \
        "$PYTHON $PIPELINE_DIR/step8_synthesis_figures.py"
fi

# ---------------------------------------------------------------------------
# Step 8b — Significance figures
# ---------------------------------------------------------------------------
if should_run 8b; then
    run_single "step8b" \
        "$PYTHON $PIPELINE_DIR/step8b_significance_figures.py"
fi

# ---------------------------------------------------------------------------
# Step 9 — Update docs
# ---------------------------------------------------------------------------
if should_run 9; then
    run_single "step9" \
        "$PYTHON $PIPELINE_DIR/step9_update_docs.py"
fi

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
_log "=================================================================="
if [[ $STEP_ERRORS -eq 0 ]]; then
    _log " ✓  ALL STEPS COMPLETED  —  total time: $(_elapsed $PIPELINE_START)"
    printf 'COMPLETED|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"
else
    _log " ✗  PIPELINE FINISHED WITH $STEP_ERRORS FAILED STEP(S)  —  $(_elapsed $PIPELINE_START)"
    _log ""
    _log " Failed steps:"
    for entry in "${FAILED_STEPS[@]}"; do
        _log "   ✗  $entry"
    done
    _log ""
    _log " To re-run only failed steps, use --only <steps> --skip-done"
    _log " To halt at first failure: --stop-on-error"
    printf 'FAILED|%s|%s\n' "$(date +%s)" "$$" > "$STATUS_FILE"
fi
_log "=================================================================="

# Disable the trap so it doesn't overwrite COMPLETED/FAILED status
trap - EXIT

exit $STEP_ERRORS
