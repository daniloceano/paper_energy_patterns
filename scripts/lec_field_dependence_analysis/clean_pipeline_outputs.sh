#!/usr/bin/env bash
# =============================================================================
#  clean_pipeline_outputs.sh — Safely remove LEC Field Dependence outputs
# =============================================================================
#
#  Removes only files produced by the lec_field_dependence_analysis pipeline.
#  Files outside results/lec_field_dependence/, figures/lec_field_dependence/,
#  and the pipeline's own logs are NEVER touched.
#
#  Usage:
#    bash clean_pipeline_outputs.sh [SCOPE...] [--dry-run] [--yes]
#
#  Scopes (one or more, or --all):
#    --all       Remove results + chunks + figures + logs  (full clean slate)
#    --results   Remove merged result CSVs (step1–step9 outputs, non-chunk)
#    --chunks    Remove intermediate chunk CSVs (step*_chunk*.csv)
#    --figures   Remove generated figures in figures/lec_field_dependence/
#    --logs      Remove pipeline logs (step*, orchestrator*, nohup_pipeline*,
#                pipeline.pid, pipeline_status.txt)
#
#  Safety flags:
#    --dry-run   List what would be deleted without deleting anything (DEFAULT)
#    --yes       Actually delete.  Without this flag, always dry-run.
#
#  Examples:
#    # Preview everything that would be cleaned
#    bash clean_pipeline_outputs.sh --all
#
#    # Actually wipe everything (fresh start)
#    bash clean_pipeline_outputs.sh --all --yes
#
#    # Wipe only intermediate chunk files, keep final results
#    bash clean_pipeline_outputs.sh --chunks --yes
#
#    # Wipe logs only
#    bash clean_pipeline_outputs.sh --logs --yes
#
#    # Wipe results + figures, dry-run first
#    bash clean_pipeline_outputs.sh --results --figures
#
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

RESULTS_DIR="$PROJECT_DIR/results/lec_field_dependence"
FIGURES_DIR="$PROJECT_DIR/figures/lec_field_dependence"
LOGS_DIR="$PROJECT_DIR/logs"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
DO_RESULTS=false
DO_CHUNKS=false
DO_FIGURES=false
DO_LOGS=false
DRY_RUN=true       # safe default: always dry-run unless --yes is passed
CONFIRMED=false

if [[ $# -eq 0 ]]; then
    echo "Usage: bash clean_pipeline_outputs.sh [--all|--results|--chunks|--figures|--logs] [--dry-run] [--yes]"
    echo "       Default mode is --dry-run. Pass --yes to actually delete."
    exit 0
fi

for arg in "$@"; do
    case "$arg" in
        --all)      DO_RESULTS=true; DO_CHUNKS=true; DO_FIGURES=true; DO_LOGS=true ;;
        --results)  DO_RESULTS=true ;;
        --chunks)   DO_CHUNKS=true  ;;
        --figures)  DO_FIGURES=true ;;
        --logs)     DO_LOGS=true    ;;
        --dry-run)  DRY_RUN=true    ;;
        --yes)      DRY_RUN=false; CONFIRMED=true ;;
        -h|--help)
            sed -n '/^#  Usage/,/^# ====/p' "$0" | grep -v '^# ====' 
            exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

if ! $DO_RESULTS && ! $DO_CHUNKS && ! $DO_FIGURES && ! $DO_LOGS; then
    echo "ERROR: specify at least one scope: --all, --results, --chunks, --figures, --logs" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Collect file targets
# ---------------------------------------------------------------------------

_collect_files() {
    # bash 3.2-compatible file collection
    local out_var="$1"; shift
    local targets=()
    local f
    for pattern in "$@"; do
        # Expand glob safely; skip if no matches
        for f in $pattern; do
            [[ -f "$f" ]] && targets+=("$f")
        done
    done
    # Return via name-ref workaround: print to stdout, caller reads with while-read
    for f in "${targets[@]+"${targets[@]}"}"; do echo "$f"; done
}

RESULT_FILES=()
CHUNK_FILES=()
FIGURE_FILES=()
LOG_FILES=()

if $DO_RESULTS; then
    # Merged result CSVs and text reports (non-chunk)
    while IFS= read -r f; do RESULT_FILES+=("$f"); done < <(
        find "$RESULTS_DIR" -mindepth 1 -maxdepth 1 -type f \
            ! -name "*_chunk*.csv" 2>/dev/null | sort
    )
fi

if $DO_CHUNKS; then
    # Intermediate chunk CSVs
    while IFS= read -r f; do CHUNK_FILES+=("$f"); done < <(
        find "$RESULTS_DIR" -mindepth 1 -maxdepth 1 -type f \
            -name "*_chunk*.csv" 2>/dev/null | sort
    )
fi

if $DO_FIGURES; then
    while IFS= read -r f; do FIGURE_FILES+=("$f"); done < <(
        find "$FIGURES_DIR" -mindepth 1 -type f 2>/dev/null | sort
    )
fi

if $DO_LOGS; then
    while IFS= read -r f; do LOG_FILES+=("$f"); done < <(
        find "$LOGS_DIR" -maxdepth 1 -type f \(   \
            -name "step*_*.log"                    \
            -o -name "orchestrator_*.log"          \
            -o -name "nohup_pipeline_*.log"        \
            -o -name "pipeline.pid"                \
            -o -name "pipeline_status.txt"         \
        \) 2>/dev/null | sort
    )
fi

ALL_FILES=()
for f in \
    "${RESULT_FILES[@]+"${RESULT_FILES[@]}"}" \
    "${CHUNK_FILES[@]+"${CHUNK_FILES[@]}"}"  \
    "${FIGURE_FILES[@]+"${FIGURE_FILES[@]}"}" \
    "${LOG_FILES[@]+"${LOG_FILES[@]}"}"; do
    ALL_FILES+=("$f")
done

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "  Scope selected:"
$DO_RESULTS && echo "    results  : ${#RESULT_FILES[@]} file(s)  ($RESULTS_DIR)"
$DO_CHUNKS  && echo "    chunks   : ${#CHUNK_FILES[@]} file(s)   ($RESULTS_DIR)"
$DO_FIGURES && echo "    figures  : ${#FIGURE_FILES[@]} file(s)  ($FIGURES_DIR)"
$DO_LOGS    && echo "    logs     : ${#LOG_FILES[@]} file(s)     ($LOGS_DIR)"
echo "    ─────────────────────────────────"
echo "    TOTAL    : ${#ALL_FILES[@]} file(s)"
echo ""

if [[ ${#ALL_FILES[@]} -eq 0 ]]; then
    echo "  Nothing to clean — all selected scopes are already empty."
    exit 0
fi

if $DRY_RUN; then
    echo "  [DRY RUN — pass --yes to actually delete]"
    echo ""
    echo "  Files that would be deleted:"
    for f in "${ALL_FILES[@]}"; do
        echo "    $f"
    done
    echo ""
    echo "  To delete: re-run with --yes"
    exit 0
fi

# ---------------------------------------------------------------------------
# Actual deletion (only reached when --yes was passed)
# ---------------------------------------------------------------------------
echo "  Deleting ${#ALL_FILES[@]} file(s)..."
for f in "${ALL_FILES[@]}"; do
    rm -f "$f" && echo "    removed: $(basename "$f")"
done
echo ""
echo "  Done."
exit 0
