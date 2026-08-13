#!/usr/bin/env bash
# =============================================================================
#  sync_from_remote.sh — Pull Cyclone Phase Space (CPS) outputs from remote
# =============================================================================
#
#  The CPS pipeline runs on the remote server (steps 1-9 over 6,776 cyclones).
#  This script pulls back the tables and figures so you can read and present
#  them locally, leaving the heavy per-timestep databases and the 628-figure
#  case gallery on the server unless you ask for them.
#
#  Uses SSH ControlMaster so you are prompted for your password at most ONCE,
#  however many rsync operations run.
#
#  What is transferred BY DEFAULT  (~20 MB):
#    results/cps_analysis/         *.csv, *.txt, *.md, *.json  — including
#                                  sensitivity/, minus the timestep databases
#    figures/cps_analysis/         fig0-fig10 and sensitivity/, minus cases/
#
#  What is NOT transferred by default (opt in with the flags below):
#    results/cps_analysis/*timesteps*.csv   ~65 MB  the per-timestep databases
#    results/cps_analysis/sensitivity/cps_timesteps_classified.csv   69 MB
#    results/cps_analysis/sensitivity/episodes_all.csv               19 MB
#    figures/cps_analysis/cases/           106 MB, 628 files  the case gallery
#    scripts/cps_analysis/csv_output/       30 MB, 6,776 files  the INPUTS
#    scripts/cps_analysis/cps_output/, cyclone_tracks/   never transferred
#    *.nc, *.grib, *.grb, *.zarr, __pycache__/, *.pyc
#
#  Safety:
#    --update    : never overwrite local files that are the same age or newer
#    no --delete : never remove files that exist only locally
#
#  Usage:
#    bash scripts/cps_analysis/sync_from_remote.sh [options]
#
#  Options:
#    --dry-run     Show what would be transferred; don't copy anything
#    --cases       Also pull the case-diagram gallery (figures/.../cases/, 106 MB)
#    --timesteps   Also pull the per-timestep databases (~155 MB total)
#    --inputs      Also pull scripts/cps_analysis/csv_output/ — the per-cyclone
#                  CPS CSVs written by A. Rodriguez. These are IRREPLACEABLE:
#                  the ERA5 NetCDFs they came from were not retained. Worth
#                  running once as an off-server backup.
#    --logs        Also pull logs/
#    --all         --cases --timesteps --inputs --logs
#
#  Prerequisites:
#    Run the pipeline on the remote first:
#      python scripts/cps_analysis/run_all.py
#
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BASE="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- Configuration (matches the other sync scripts in this repo) -------------
REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"

# --- Argument parsing --------------------------------------------------------
DRY_RUN=false
SYNC_CASES=false
SYNC_TIMESTEPS=false
SYNC_INPUTS=false
SYNC_LOGS=false

for arg in "$@"; do
    case "$arg" in
        --dry-run)   DRY_RUN=true ;;
        --cases)     SYNC_CASES=true ;;
        --timesteps) SYNC_TIMESTEPS=true ;;
        --inputs)    SYNC_INPUTS=true ;;
        --logs)      SYNC_LOGS=true ;;
        --all)       SYNC_CASES=true; SYNC_TIMESTEPS=true
                     SYNC_INPUTS=true; SYNC_LOGS=true ;;
        -h|--help)
            sed -n '/^#  Usage/,/^# ====/p' "$0" | grep -v '^# ===='
            exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# --- SSH ControlMaster: one connection, reused by every rsync call -----------
SOCKET="/tmp/ssh_cps_sync_$$"
SSH_E="ssh -S $SOCKET -i $SSH_KEY -o BatchMode=no"

_close_master() {
    ssh -S "$SOCKET" -O exit "$REMOTE_USER@$REMOTE_HOST" 2>/dev/null || true
}
trap _close_master EXIT

echo "Connecting to ${REMOTE_USER}@${REMOTE_HOST}..."
echo "(You will be prompted for your password or key passphrase at most once.)"
echo ""
ssh -M -S "$SOCKET" -i "$SSH_KEY" -fN "$REMOTE_USER@$REMOTE_HOST"

# --- rsync helper ------------------------------------------------------------
_rsync() {
    local label="$1"
    local remote_path="$2"
    local local_path="$3"
    shift 3
    # remaining args are extra rsync options (--exclude, --filter, ...)

    mkdir -p "$local_path"

    local rsync_flags="-avz --update --progress"
    $DRY_RUN && rsync_flags="-avzn --update"

    echo ""
    echo "  ─── $label ─────────────────────────────────────"
    $DRY_RUN && echo "  [DRY RUN — no files will be copied]"
    # shellcheck disable=SC2086
    rsync $rsync_flags \
        --exclude="*.nc" \
        --exclude="*.grib" \
        --exclude="*.grb" \
        --exclude="*.grb2" \
        --exclude="*.zarr" \
        --exclude="*.idx" \
        --exclude="__pycache__/" \
        --exclude="*.pyc" \
        "$@" \
        -e "$SSH_E" \
        "${REMOTE_USER}@${REMOTE_HOST}:${remote_path}/" \
        "${local_path}/"
}

# --- What to leave behind ----------------------------------------------------
# The per-timestep databases are the pipeline's intermediate state: 6,776
# cyclones x ~31 three-hourly steps. Everything a reader needs is already
# aggregated in the per-cyclone and per-state tables, so they stay remote
# unless asked for.
RESULTS_EXCLUDES=()
if ! $SYNC_TIMESTEPS; then
    RESULTS_EXCLUDES+=(--exclude="*timesteps*.csv" --exclude="episodes_all.csv")
fi

# The case gallery is one figure per class x year x genesis region.
FIGURES_EXCLUDES=()
if ! $SYNC_CASES; then
    FIGURES_EXCLUDES+=(--exclude="cases/")
fi

# Expanding an empty array under `set -u` is an error in bash 3.2 (what macOS
# ships), so both arrays are expanded through the ${arr[@]+...} guard below.

# --- Transfers ---------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Cyclone Phase Space Analysis — Sync from Remote"
echo " Remote : ${REMOTE_USER}@${REMOTE_HOST}"
echo " Local  : ${LOCAL_BASE}"
echo " Extras : cases=$SYNC_CASES  timesteps=$SYNC_TIMESTEPS  inputs=$SYNC_INPUTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Tables and reports, canonical + sensitivity (light files only)
_rsync "results/cps_analysis  (tables and reports, incl. sensitivity/)" \
    "${REMOTE_BASE}/results/cps_analysis" \
    "${LOCAL_BASE}/results/cps_analysis" \
    ${RESULTS_EXCLUDES[@]+"${RESULTS_EXCLUDES[@]}"} \
    --filter="+ */" \
    --filter="+ *.csv" \
    --filter="+ *.txt" \
    --filter="+ *.md" \
    --filter="+ *.json" \
    --filter="+ *.parquet" \
    --filter="+ *.feather" \
    --filter="- *"

# Figures: fig0-fig10 and the sensitivity set; cases/ only on request
_rsync "figures/cps_analysis  (fig0–fig10, sensitivity/)" \
    "${REMOTE_BASE}/figures/cps_analysis" \
    "${LOCAL_BASE}/figures/cps_analysis" \
    ${FIGURES_EXCLUDES[@]+"${FIGURES_EXCLUDES[@]}"}

if $SYNC_INPUTS; then
    # IRREPLACEABLE: the ERA5 subsets these were computed from are gone.
    _rsync "scripts/cps_analysis/csv_output  (6,776 per-cyclone CPS CSVs — backup)" \
        "${REMOTE_BASE}/scripts/cps_analysis/csv_output" \
        "${LOCAL_BASE}/scripts/cps_analysis/csv_output"
fi

if $SYNC_LOGS; then
    _rsync "logs" \
        "${REMOTE_BASE}/logs" \
        "${LOCAL_BASE}/logs"
fi

# --- Summary -----------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Summary of local directories after sync:"
for d in \
    "${LOCAL_BASE}/results/cps_analysis" \
    "${LOCAL_BASE}/results/cps_analysis/sensitivity" \
    "${LOCAL_BASE}/figures/cps_analysis" \
    "${LOCAL_BASE}/figures/cps_analysis/cases" \
    "${LOCAL_BASE}/scripts/cps_analysis/csv_output"; do
    if [ -d "$d" ]; then
        n=$(find "$d" -maxdepth 3 -type f | wc -l | tr -d ' ')
        s=$(du -sh "$d" 2>/dev/null | cut -f1)
        echo "   ${d#$LOCAL_BASE/}  →  ${n} file(s), ${s}"
    else
        echo "   ${d#$LOCAL_BASE/}  →  (not present)"
    fi
done
echo ""
if $DRY_RUN; then
    echo " Dry run complete. Run without --dry-run to copy files."
else
    echo " Sync complete."
    $SYNC_CASES     || echo " (case gallery left on the remote — add --cases)"
    $SYNC_TIMESTEPS || echo " (timestep databases left on the remote — add --timesteps)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
