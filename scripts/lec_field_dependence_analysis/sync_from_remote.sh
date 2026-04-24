#!/usr/bin/env bash
# =============================================================================
#  sync_from_remote.sh — Pull LEC Field Dependence outputs from remote server
# =============================================================================
#
#  Uses SSH ControlMaster so you are only prompted for your password ONCE,
#  regardless of how many rsync operations run.
#
#  What is transferred:
#    results/lec_field_dependence/   — all merged CSVs and reports
#    figures/lec_field_dependence/   — all generated figures
#
#  Safety:
#    --update     : local files that are the same age or NEWER than the remote
#                   version are NEVER overwritten (protects step 1-3 local outputs)
#    no --delete  : files that exist only locally are NEVER removed
#
#  Usage:
#    bash scripts/lec_field_dependence_analysis/sync_from_remote.sh
#
#  Options:
#    --logs       Also transfer pipeline logs (logs/) — off by default
#    --dry-run    Show what would be transferred; don't copy anything
#
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BASE="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ---------------------------------------------------------------------------
# Configuration — adjust if your remote setup changes
# ---------------------------------------------------------------------------
REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
SYNC_LOGS=false
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --logs)    SYNC_LOGS=true ;;
        --dry-run) DRY_RUN=true   ;;
        -h|--help)
            sed -n '/^#  Usage/,/^# ====/p' "$0" | grep -v '^# ===='
            exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# SSH ControlMaster setup — single connection, reused by all rsync calls
# ---------------------------------------------------------------------------
SOCKET="/tmp/ssh_lec_sync_$$"
SSH_E="ssh -S $SOCKET -i $SSH_KEY -o BatchMode=no"

_close_master() {
    ssh -S "$SOCKET" -O exit "$REMOTE_USER@$REMOTE_HOST" 2>/dev/null || true
}
trap _close_master EXIT

echo "Connecting to ${REMOTE_USER}@${REMOTE_HOST}..."
echo "(You will be prompted for your password or key passphrase at most once.)"
echo ""
ssh -M -S "$SOCKET" -i "$SSH_KEY" -fN "$REMOTE_USER@$REMOTE_HOST"

# ---------------------------------------------------------------------------
# rsync helper
# ---------------------------------------------------------------------------
_rsync() {
    local label="$1"
    local remote_path="$2"
    local local_path="$3"

    mkdir -p "$local_path"

    local rsync_flags="-avz --update --progress"
    $DRY_RUN && rsync_flags="-avzn --update"

    echo ""
    echo "  ─── $label ─────────────────────────────────────"
    $DRY_RUN && echo "  [DRY RUN — no files will be copied]"
    rsync $rsync_flags \
        -e "$SSH_E" \
        "${REMOTE_USER}@${REMOTE_HOST}:${remote_path}/" \
        "${local_path}/"
}

# ---------------------------------------------------------------------------
# Transfers
# ---------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " LEC Field Dependence — Sync from Remote"
echo " Remote: ${REMOTE_USER}@${REMOTE_HOST}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

_rsync "results" \
    "${REMOTE_BASE}/results/lec_field_dependence" \
    "${LOCAL_BASE}/results/lec_field_dependence"

_rsync "figures" \
    "${REMOTE_BASE}/figures/lec_field_dependence" \
    "${LOCAL_BASE}/figures/lec_field_dependence"

if $SYNC_LOGS; then
    _rsync "logs" \
        "${REMOTE_BASE}/logs" \
        "${LOCAL_BASE}/logs"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$DRY_RUN && echo " Dry run complete. Run without --dry-run to copy files." \
          || echo " Sync complete."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
