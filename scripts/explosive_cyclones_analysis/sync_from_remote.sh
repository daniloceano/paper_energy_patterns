#!/usr/bin/env bash
# =============================================================================
#  sync_from_remote.sh — Pull explosive-cyclone analysis outputs from remote
# =============================================================================
#
#  The heavy steps run on the remote server:
#    step2 (download MSLP)  +  step3 (assign central pressure)  +  step4 (NDR)
#  This script pulls back ONLY the lightweight tables and figures so you can run
#  step5 (figures) and inspect results locally.
#
#  Uses SSH ControlMaster so you are prompted for your password at most ONCE.
#
#  What is transferred:
#    results/explosive_cyclones/   *.csv, *.txt, *.json, *.md, *.parquet
#    figures/explosive_cyclones/   all figures (if generated on the remote)
#
#  What is NOT transferred:
#    data/era5_explosive_cyclones/*.nc  — raw MSLP (~tens of GB, stays remote)
#    *.nc, *.grib, *.grb, *.zarr, __pycache__/, *.pyc
#
#  Safety:
#    --update    : never overwrite local files that are the same age or newer
#    no --delete : never remove files that exist only locally
#
#  Usage:
#    bash scripts/explosive_cyclones_analysis/sync_from_remote.sh [--dry-run] [--logs]
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
SYNC_LOGS=false
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --logs)    SYNC_LOGS=true ;;
        --dry-run) DRY_RUN=true   ;;
        -h|--help) sed -n '/^#  Usage/,/^# ====/p' "$0" | grep -v '^# ===='; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# --- SSH ControlMaster: single shared connection -----------------------------
SOCKET="/tmp/ssh_exp_sync_$$"
SSH_E="ssh -S $SOCKET -i $SSH_KEY -o BatchMode=no"
_close_master() { ssh -S "$SOCKET" -O exit "$REMOTE_USER@$REMOTE_HOST" 2>/dev/null || true; }
trap _close_master EXIT

echo "Connecting to ${REMOTE_USER}@${REMOTE_HOST}..."
echo "(You will be prompted for your password or key passphrase at most once.)"
ssh -M -S "$SOCKET" -i "$SSH_KEY" -fN "$REMOTE_USER@$REMOTE_HOST"

# --- rsync helper: lightweight files only ------------------------------------
_rsync_light() {
    local label="$1" remote_path="$2" local_path="$3"
    mkdir -p "$local_path"
    local flags="-avz --update --progress"
    $DRY_RUN && flags="-avzn --update"
    echo ""
    echo "  ─── $label ─────────────────────────────────────"
    $DRY_RUN && echo "  [DRY RUN — no files will be copied]"
    # shellcheck disable=SC2086
    rsync $flags \
        --exclude="*.nc" --exclude="*.grib" --exclude="*.grb" --exclude="*.grb2" \
        --exclude="*.zarr" --exclude="*.idx" --exclude="__pycache__/" --exclude="*.pyc" \
        --filter="+ */" \
        --filter="+ *.csv" --filter="+ *.txt" --filter="+ *.json" --filter="+ *.md" \
        --filter="+ *.parquet" --filter="+ *.feather" \
        --filter="+ *.png" --filter="+ *.pdf" \
        --filter="- *" \
        -e "$SSH_E" \
        "${REMOTE_USER}@${REMOTE_HOST}:${remote_path}/" "${local_path}/"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Explosive Cyclones Analysis — Sync from Remote"
echo " Remote : ${REMOTE_USER}@${REMOTE_HOST}"
echo " Local  : ${LOCAL_BASE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

_rsync_light "results/explosive_cyclones" \
    "${REMOTE_BASE}/results/explosive_cyclones" \
    "${LOCAL_BASE}/results/explosive_cyclones"

_rsync_light "figures/explosive_cyclones" \
    "${REMOTE_BASE}/figures/explosive_cyclones" \
    "${LOCAL_BASE}/figures/explosive_cyclones"

if $SYNC_LOGS; then
    _rsync_light "logs (explosive_*)" "${REMOTE_BASE}/logs" "${LOCAL_BASE}/logs"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for d in "${LOCAL_BASE}/results/explosive_cyclones" "${LOCAL_BASE}/figures/explosive_cyclones"; do
    if [ -d "$d" ]; then
        n=$(find "$d" -maxdepth 2 -type f | wc -l | tr -d ' ')
        echo "   ${d#$LOCAL_BASE/}  →  ${n} file(s)"
    fi
done
if $DRY_RUN; then
    echo " Dry run complete. Run without --dry-run to copy files."
else
    echo " Sync complete. Next: python scripts/explosive_cyclones_analysis/run_all.py"
    echo "                       (steps 4-7: NDR, validation figures, relative frequency, density maps)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
