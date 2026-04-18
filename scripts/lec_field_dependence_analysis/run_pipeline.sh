#!/usr/bin/env bash
# =============================================================================
#  run_pipeline.sh  —  LEC Field Dependence Analysis — Remote Pipeline Runner
# =============================================================================
#
#  Orchestrates steps 4–9 on a remote server.
#  Steps 1–3 MUST already have been run locally before using this script.
#
#  Usage:
#    bash run_pipeline.sh --era5-dir /data/era5/
#    bash run_pipeline.sh --era5-dir /data/era5/ --n-chunks 20 --workers 4
#    bash run_pipeline.sh --era5-dir /data/era5/ --skip-done
#    bash run_pipeline.sh --era5-dir /data/era5/ --only 4,5,6
#    bash run_pipeline.sh --era5-dir /data/era5/ --parallel-streams  # run abs+anom in parallel
#
#  Options:
#    --era5-dir PATH       Path to per-cyclone ERA5 NetCDF files [REQUIRED]
#    --n-chunks N          Parallel chunks per heavy step (default: 16)
#    --workers N           CPU workers per chunk (default: 4)
#    --conda-env NAME      Conda environment to use (default: paper_energy_patterns)
#    --skip-done           Skip steps whose output files already exist
#    --only STEPS          Run only these steps, e.g. "4,5,6" or "7,7b"
#    --parallel-streams    Run absolute+anomaly in parallel for steps 4,5,7
#                          (double the CPU load — use on servers with many cores)
#
#  Notes:
#    - Steps 4, 5, 7 use parallel background jobs (n-chunks processes at once).
#    - Step 6 handles chunk merging for steps 4 and 5 automatically.
#    - Step 8 handles chunk merging for step 7 automatically.
#    - All output goes to logs/ in the project root.
#
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PIPELINE_DIR="$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
ERA5_DIR=""
N_CHUNKS=16
N_WORKERS=4
CONDA_ENV="paper_energy_patterns"
SKIP_DONE=false
ONLY_STEPS=""
PARALLEL_STREAMS=false

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --era5-dir)         ERA5_DIR="$2";     shift 2 ;;
        --n-chunks)         N_CHUNKS="$2";     shift 2 ;;
        --workers)          N_WORKERS="$2";    shift 2 ;;
        --conda-env)        CONDA_ENV="$2";    shift 2 ;;
        --skip-done)        SKIP_DONE=true;    shift   ;;
        --only)             ONLY_STEPS="$2";   shift 2 ;;
        --parallel-streams) PARALLEL_STREAMS=true; shift ;;
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

# ---------------------------------------------------------------------------
# Paths and setup
# ---------------------------------------------------------------------------
RESULTS_DIR="$PROJECT_DIR/results/lec_field_dependence"
LOG_DIR="$PROJECT_DIR/logs"
TS=$(date +%Y%m%d_%H%M%S)
ORCH_LOG="$LOG_DIR/orchestrator_${TS}.log"

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

PYTHON="conda run -n $CONDA_ENV python"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
PIPELINE_START=$(date +%s)
STEP_ERRORS=0

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

# Run a single (non-chunked) step
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
        _log "FAILED [$step]  elapsed=$(_elapsed $step_start)  log=$(basename $step_log)"
        STEP_ERRORS=$(( STEP_ERRORS + 1 ))
        return 1
    fi
}

# Run N_CHUNKS parallel background jobs, wait, collect exit codes
run_chunks() {
    local step="$1"
    local n="$2"
    local cmd_tmpl="$3"     # use {CHUNK} as placeholder for chunk index
    local step_start=$(date +%s)

    _log "START  [$step]  launching $n parallel chunks..."

    local pids=()
    for i in $(seq 0 $(( n - 1 ))); do
        local chunk_log="$LOG_DIR/${step}_chunk${i}_${TS}.log"
        local cmd="${cmd_tmpl//\{CHUNK\}/$i}"
        eval "$cmd" >> "$chunk_log" 2>&1 &
        pids+=($!)
    done

    local failed=0
    for pid in "${pids[@]}"; do
        wait "$pid" || failed=$(( failed + 1 ))
    done

    if [[ $failed -gt 0 ]]; then
        _log "FAILED [$step]  $failed/$n chunks failed  elapsed=$(_elapsed $step_start)"
        STEP_ERRORS=$(( STEP_ERRORS + 1 ))
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
_log " Chunks:          $N_CHUNKS"
_log " Workers/chunk:   $N_WORKERS"
_log " Conda env:       $CONDA_ENV"
_log " Skip done:       $SKIP_DONE"
_log " Only steps:      ${ONLY_STEPS:-all}"
_log " Parallel streams:$PARALLEL_STREAMS"
_log " Orch log:        $ORCH_LOG"
_log "=================================================================="

cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Step 4 — Extract absolute features
# ---------------------------------------------------------------------------
if should_run 4; then
    if $SKIP_DONE && output_ready "$RESULTS_DIR/step4_features_absolute.csv"; then
        _log "SKIP   [step4]  output already exists"
    else
        CMD="$PYTHON $PIPELINE_DIR/step4_extract_features_absolute.py \
            --era5-dir $ERA5_DIR --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"

        if $PARALLEL_STREAMS; then
            # Launch step 5 at the same time in a subshell, then handle step 4 here
            CMD5="$PYTHON $PIPELINE_DIR/step5_extract_features_anomaly.py \
                --era5-dir $ERA5_DIR --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
            if ! $SKIP_DONE || ! output_ready "$RESULTS_DIR/step5_features_anomaly.csv"; then
                _log "PARALLEL-STREAMS: launching step4 + step5 together"
                ( run_chunks "step4" $N_CHUNKS "$CMD" ) &
                PID4=$!
                ( run_chunks "step5" $N_CHUNKS "$CMD5" ) &
                PID5=$!
                PSTREAMS_FAIL=0
                wait $PID4 || PSTREAMS_FAIL=$(( PSTREAMS_FAIL + 1 ))
                wait $PID5 || PSTREAMS_FAIL=$(( PSTREAMS_FAIL + 1 ))
                if [[ $PSTREAMS_FAIL -gt 0 ]]; then
                    _log "FAILED [step4+step5 parallel streams]  stopping."
                    exit 1
                fi
            else
                _log "SKIP   [step5]  output already exists (parallel-streams)"
                run_chunks "step4" $N_CHUNKS "$CMD" || { _log "Stopping."; exit 1; }
            fi
        else
            run_chunks "step4" $N_CHUNKS "$CMD" || { _log "Stopping."; exit 1; }
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Step 5 — Extract anomaly features (skipped if already done in parallel above)
# ---------------------------------------------------------------------------
if should_run 5 && ! $PARALLEL_STREAMS; then
    if $SKIP_DONE && output_ready "$RESULTS_DIR/step5_features_anomaly.csv"; then
        _log "SKIP   [step5]  output already exists"
    else
        CMD="$PYTHON $PIPELINE_DIR/step5_extract_features_anomaly.py \
            --era5-dir $ERA5_DIR --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
        run_chunks "step5" $N_CHUNKS "$CMD" || { _log "Stopping."; exit 1; }
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
            "$PYTHON $PIPELINE_DIR/step6_integrate_tables.py" \
            || { _log "Stopping."; exit 1; }
    fi
fi

# ---------------------------------------------------------------------------
# Step 7 — Compute PREDEP (absolute + anomaly field types)
# ---------------------------------------------------------------------------
if should_run 7; then
    SKIP_ABS=false
    SKIP_ANOM=false
    $SKIP_DONE && output_ready "$RESULTS_DIR/step7_predep_absolute.csv" && SKIP_ABS=true
    $SKIP_DONE && output_ready "$RESULTS_DIR/step7_predep_anomaly.csv"  && SKIP_ANOM=true

    CMD_ABS="$PYTHON $PIPELINE_DIR/step7_compute_predep.py \
        --field-type absolute --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"
    CMD_ANOM="$PYTHON $PIPELINE_DIR/step7_compute_predep.py \
        --field-type anomaly --chunk {CHUNK} --n-chunks $N_CHUNKS --workers $N_WORKERS"

    if $PARALLEL_STREAMS && ! $SKIP_ABS && ! $SKIP_ANOM; then
        _log "PARALLEL-STREAMS: launching step7-absolute + step7-anomaly together"
        STEP7_START=$(date +%s)
        ( run_chunks "step7_absolute" $N_CHUNKS "$CMD_ABS" ) &
        P7A=$!
        ( run_chunks "step7_anomaly"  $N_CHUNKS "$CMD_ANOM" ) &
        P7N=$!
        P7_FAIL=0
        wait $P7A || P7_FAIL=$(( P7_FAIL + 1 ))
        wait $P7N || P7_FAIL=$(( P7_FAIL + 1 ))
        if [[ $P7_FAIL -gt 0 ]]; then
            _log "FAILED [step7 parallel streams]  stopping."
            exit 1
        fi
        _log "DONE   [step7 parallel streams]  elapsed=$(_elapsed $STEP7_START)"

    else
        # Sequential: absolute then anomaly
        if $SKIP_ABS; then
            _log "SKIP   [step7-absolute]  output already exists"
        else
            run_chunks "step7_absolute" $N_CHUNKS "$CMD_ABS" || { _log "Stopping."; exit 1; }
        fi

        if $SKIP_ANOM; then
            _log "SKIP   [step7-anomaly]  output already exists"
        else
            run_chunks "step7_anomaly" $N_CHUNKS "$CMD_ANOM" || { _log "Stopping."; exit 1; }
        fi
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
            "$PYTHON $PIPELINE_DIR/step7b_ep_significance_tests.py" \
            || { _log "Stopping."; exit 1; }
    fi
fi

# ---------------------------------------------------------------------------
# Step 8 — Synthesis figures (PREDEP heatmaps; reads chunks from step 7 directly)
# ---------------------------------------------------------------------------
if should_run 8; then
    run_single "step8" \
        "$PYTHON $PIPELINE_DIR/step8_synthesis_figures.py" \
        || { _log "Stopping."; exit 1; }
fi

# ---------------------------------------------------------------------------
# Step 8b — Significance figures
# ---------------------------------------------------------------------------
if should_run 8b; then
    run_single "step8b" \
        "$PYTHON $PIPELINE_DIR/step8b_significance_figures.py" \
        || { _log "Stopping."; exit 1; }
fi

# ---------------------------------------------------------------------------
# Step 9 — Update docs
# ---------------------------------------------------------------------------
if should_run 9; then
    run_single "step9" \
        "$PYTHON $PIPELINE_DIR/step9_update_docs.py" \
        || { _log "Stopping."; exit 1; }
fi

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
_log "=================================================================="
if [[ $STEP_ERRORS -eq 0 ]]; then
    _log " ✓  ALL STEPS COMPLETED  —  total time: $(_elapsed $PIPELINE_START)"
else
    _log " ✗  PIPELINE FINISHED WITH $STEP_ERRORS ERRORS  —  $(_elapsed $PIPELINE_START)"
fi
_log "=================================================================="

exit $STEP_ERRORS
