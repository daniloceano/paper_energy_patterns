#!/usr/bin/env bash
# =============================================================================
#  fetch_test_data.sh — Download a minimal REAL sample for local pipeline tests
# =============================================================================
#
#  Downloads a small, representative subset of per-cyclone ERA5 files from the
#  remote server so that the full logic of step3b → step4 → step5 → step6 → 7
#  can be exercised locally without running on the full 2733-cyclone dataset.
#
#  WHY THIS EXISTS
#  ---------------
#  The remote server holds all real data (~2733 per-cyclone NetCDFs, ~hundreds
#  of GB).  Local debugging was blind — fixes were tested only in theory and
#  then had to be validated in a full server run.  This script breaks that
#  cycle: download a few real files → test locally → fix → scale on server.
#
#  WHAT IT DOWNLOADS  (6 cyclones, ~2 per EP, median-duration cases)
#  -------------------------------------------------------------------
#  Selected via `step3_era5_field_manifest.csv` + `step2_lec_means.csv`
#  picking the 40th and 60th percentile of intensification duration per EP so
#  that chosen cases are representative (not outliers) of each energy pattern:
#
#    EP1  track 19971118  (36 h, centre lat=-45.0, lon=-21.5)
#    EP1  track 19970555  (42 h, centre lat=-36.5, lon=-32.9)
#    EP2  track 20090049  (36 h, centre lat=-50.6, lon=-53.6)
#    EP2  track 19800401  (42 h, centre lat=-46.1, lon=-27.8)
#    EP3  track 20010500  (33 h, centre lat=-51.1, lon=-39.3)
#    EP3  track 20140194  (42 h, centre lat=-49.9, lon=-39.4)
#
#  Per cyclone (2 files each):
#    {track_id}_era5.nc          raw ERA5 per-cyclone (u,v,t,z,q,msl, 9 levels)
#    {track_id}_metadata.csv     intensification timing and track metadata
#
#  Plus shared auxiliary files:
#    data/era5_ep_structure/precomputed_composites_ep1.nc
#    data/era5_ep_structure/precomputed_composites_ep2.nc
#    data/era5_ep_structure/precomputed_composites_ep3.nc
#    data/era5_ep_structure/precomputed_composites_epall.nc
#    data/era5_ep_structure/era5_climatology_250hPa.nc
#
#  DESTINATION
#  -----------
#  Files land in data/test/lec_field_dependence/ mirroring the remote layout:
#    data/test/lec_field_dependence/era5/           ← per-cyclone ERA5 + metadata
#    data/test/lec_field_dependence/era5/derived/   ← step3b will write here
#    data/test/lec_field_dependence/composites/     ← precomputed composites
#
#  USAGE
#  -----
#    # Normal download
#    bash scripts/lec_field_dependence_analysis/fetch_test_data.sh
#
#    # Preview: show what would be downloaded without copying
#    bash scripts/lec_field_dependence_analysis/fetch_test_data.sh --dry-run
#
#    # Re-download (overwrite existing test data)
#    bash scripts/lec_field_dependence_analysis/fetch_test_data.sh --force
#
#  After the download, run the smoke test:
#    bash scripts/lec_field_dependence_analysis/run_smoke_test.sh
#
#  NOTE: This script uses the same SSH key + ControlMaster as sync_from_remote.sh.
#        Run `ssh-add ~/Documents/Master/id_rsa.danilocs` once before use if the
#        key has a passphrase.
#
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BASE="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"

# Destination for test data
TEST_DIR="$LOCAL_BASE/data/test/lec_field_dependence"
ERA5_TEST_DIR="$TEST_DIR/era5"
COMPOSITES_TEST_DIR="$TEST_DIR/composites"

# ──────────────────────────────────────────────────────────────────────────
# Representative test cyclones (2 per EP, median-duration cases)
# Selection methodology: 40th and 60th percentile of intensification duration
# within each EP, using step3_era5_field_manifest.csv + step2_lec_*.csv.
# These are real cases with confirmed ERA5 file availability.
# ──────────────────────────────────────────────────────────────────────────
# EP  track_id  duration  center_lat  center_lon
# EP1  19971118     36h    -45.0       -21.5
# EP1  19970555     42h    -36.5       -32.9
# EP2  20090049     36h    -50.6       -53.6
# EP2  19800401     42h    -46.1       -27.8
# EP3  20010500     33h    -51.1       -39.3
# EP3  20140194     42h    -49.9       -39.4
TEST_TRACK_IDS=(
    19971118
    19970555
    20090049
    19800401
    20010500
    20140194
)

# Remote ERA5 directory (where the per-cyclone files live on the server)
REMOTE_ERA5_DIR="$REMOTE_BASE/data/era5_ep_structure"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
DRY_RUN=false
FORCE=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --force)   FORCE=true   ;;
        -h|--help)
            sed -n '/^#  USAGE/,/^#  NOTE/p' "$0" | grep -v "^#  NOTE"
            exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

RSYNC_FLAGS="-avz --progress"
if $DRY_RUN; then
    RSYNC_FLAGS="$RSYNC_FLAGS --dry-run"
    echo "=== DRY-RUN MODE: no files will be copied ==="
fi

# ---------------------------------------------------------------------------
# SSH ControlMaster — single connection, reused for all transfers
# ---------------------------------------------------------------------------
SOCKET="/tmp/ssh_lec_testfetch_$$"

cleanup() {
    ssh -S "$SOCKET" -O exit "$REMOTE_USER@$REMOTE_HOST" 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║      LEC Field Dependence — Fetch Minimal Test Data              ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo " Remote : ${REMOTE_USER}@${REMOTE_HOST}"
echo " To     : ${TEST_DIR}"
echo " Tracks : ${TEST_TRACK_IDS[*]}"
echo ""

echo "Connecting to ${REMOTE_USER}@${REMOTE_HOST}..."
ssh -M -S "$SOCKET" -i "$SSH_KEY" -fN "$REMOTE_USER@$REMOTE_HOST"
echo "Connected (ControlMaster socket: $SOCKET)"
echo ""

# ---------------------------------------------------------------------------
# Helper: rsync a single remote path to a local destination
# ---------------------------------------------------------------------------
fetch_file() {
    local remote_path="$1"
    local local_dest_dir="$2"
    local label="${3:-$remote_path}"

    mkdir -p "$local_dest_dir"

    if ! $FORCE && [[ -f "$local_dest_dir/$(basename "$remote_path")" ]]; then
        echo "  [SKIP]  $label (already exists; use --force to overwrite)"
        return 0
    fi

    echo "  [FETCH] $label"
    rsync $RSYNC_FLAGS \
        -e "ssh -S $SOCKET" \
        "${REMOTE_USER}@${REMOTE_HOST}:${remote_path}" \
        "${local_dest_dir}/" \
        2>&1 | grep -v "^$" | sed 's/^/          /'
}

# ---------------------------------------------------------------------------
# 1. Per-cyclone ERA5 files and metadata
# ---------------------------------------------------------------------------
echo "────────────────────────────────────────────────────────"
echo "1/3  Per-cyclone ERA5 + metadata  (${#TEST_TRACK_IDS[@]} cyclones × 2 files)"
echo "────────────────────────────────────────────────────────"

mkdir -p "$ERA5_TEST_DIR"
mkdir -p "$ERA5_TEST_DIR/derived"   # step3b will write here

n_era5=0
n_meta=0
missing_era5=()
missing_meta=()

for tid in "${TEST_TRACK_IDS[@]}"; do
    era5_remote="$REMOTE_ERA5_DIR/${tid}_era5.nc"
    meta_remote="$REMOTE_ERA5_DIR/${tid}_metadata.csv"

    # ERA5 file
    if ! $FORCE && [[ -f "$ERA5_TEST_DIR/${tid}_era5.nc" ]]; then
        echo "  [SKIP]  ${tid}_era5.nc (already exists)"
    else
        echo "  [FETCH] ${tid}_era5.nc"
        rsync $RSYNC_FLAGS \
            -e "ssh -S $SOCKET" \
            "${REMOTE_USER}@${REMOTE_HOST}:${era5_remote}" \
            "${ERA5_TEST_DIR}/" 2>&1 | grep -E "^sending|bytes|_era5|error" || true
        [[ -f "$ERA5_TEST_DIR/${tid}_era5.nc" ]] && n_era5=$((n_era5 + 1)) || missing_era5+=("$tid")
    fi

    # Metadata CSV
    if ! $FORCE && [[ -f "$ERA5_TEST_DIR/${tid}_metadata.csv" ]]; then
        echo "  [SKIP]  ${tid}_metadata.csv (already exists)"
    else
        echo "  [FETCH] ${tid}_metadata.csv"
        rsync $RSYNC_FLAGS \
            -e "ssh -S $SOCKET" \
            "${REMOTE_USER}@${REMOTE_HOST}:${meta_remote}" \
            "${ERA5_TEST_DIR}/" 2>&1 | grep -E "^sending|bytes|_metadata|error" || true
        [[ -f "$ERA5_TEST_DIR/${tid}_metadata.csv" ]] && n_meta=$((n_meta + 1)) || missing_meta+=("$tid")
    fi
done

# ---------------------------------------------------------------------------
# 2. Precomputed composites (EP1, EP2, EP3, EPALL)
# ---------------------------------------------------------------------------
echo ""
echo "────────────────────────────────────────────────────────"
echo "2/3  Precomputed composites  (4 files)"
echo "────────────────────────────────────────────────────────"

mkdir -p "$COMPOSITES_TEST_DIR"

for ep_label in ep1 ep2 ep3 epall; do
    remote_composite="$REMOTE_ERA5_DIR/precomputed_composites_${ep_label}.nc"
    fetch_file "$remote_composite" "$COMPOSITES_TEST_DIR" "precomputed_composites_${ep_label}.nc"
done

# ---------------------------------------------------------------------------
# 3. ERA5 monthly climatology (needed by step3b for AFC computation)
# ---------------------------------------------------------------------------
echo ""
echo "────────────────────────────────────────────────────────"
echo "3/3  ERA5 250 hPa climatology  (for AFC in step3b)"
echo "────────────────────────────────────────────────────────"

fetch_file "$REMOTE_ERA5_DIR/era5_climatology_250hPa.nc" "$COMPOSITES_TEST_DIR" "era5_climatology_250hPa.nc"

# ---------------------------------------------------------------------------
# Write a README inside the test directory
# ---------------------------------------------------------------------------
if ! $DRY_RUN; then
cat > "$TEST_DIR/README.md" << 'TESTREADME'
# Local Test Data — LEC Field Dependence

This directory contains a minimal representative subset of the real per-cyclone
ERA5 data, downloaded from the remote server for **local smoke testing** of the
`scripts/lec_field_dependence_analysis/` pipeline.

## What is here

| Path | Contents |
|------|----------|
| `era5/` | 6 per-cyclone raw ERA5 files (`*_era5.nc`) + metadata CSVs |
| `era5/derived/` | Step 3b output (derived fields) — empty until smoke test runs |
| `composites/` | 4 precomputed composites (EP1/2/3/EPALL) + 250hPa climatology |

## Which cyclones and why

| EP | Track ID | Duration | Centre lat/lon | Selection rationale |
|----|----------|----------|----------------|---------------------|
| EP1 | 19971118 | 36h | -45.0 / -21.5 | 40th percentile duration EP1 |
| EP1 | 19970555 | 42h | -36.5 / -32.9 | 60th percentile duration EP1 |
| EP2 | 20090049 | 36h | -50.6 / -53.6 | 40th percentile duration EP2 |
| EP2 | 19800401 | 42h | -46.1 / -27.8 | 60th percentile duration EP2 |
| EP3 | 20010500 | 33h | -51.1 / -39.3 | 40th percentile duration EP3 |
| EP3 | 20140194 | 42h | -49.9 / -39.4 | 60th percentile duration EP3 |

Cases were chosen at the 40th and 60th percentile of intensification duration
within each EP — representative of typical behaviour, not edge cases.

## How to use

```bash
# First, download the test data (one-time, or to refresh):
bash scripts/lec_field_dependence_analysis/fetch_test_data.sh

# Then run the smoke test (tests step3b → step4 → step5 → step6 → step7):
bash scripts/lec_field_dependence_analysis/run_smoke_test.sh
```

## This is NOT production data

- The remote server holds all 2733 cyclones.
- This directory holds only 6 for local logic validation.
- Raw files here are read-only inputs; derived files in `era5/derived/` are generated.
- Never commit these NetCDF files to git (they are .gitignored).
TESTREADME
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "══════════════════════════════════════════════════════════"
echo " Fetch complete"
echo "══════════════════════════════════════════════════════════"
echo ""
echo " ERA5 files downloaded  : $(ls "$ERA5_TEST_DIR/"*_era5.nc 2>/dev/null | wc -l | tr -d ' ') / ${#TEST_TRACK_IDS[@]}"
echo " Metadata files         : $(ls "$ERA5_TEST_DIR/"*_metadata.csv 2>/dev/null | wc -l | tr -d ' ') / ${#TEST_TRACK_IDS[@]}"
echo " Composites             : $(ls "$COMPOSITES_TEST_DIR/"*.nc 2>/dev/null | wc -l | tr -d ' ') / 5  (4 composites + 1 climatology)"
echo ""

if [[ ${#missing_era5[@]} -gt 0 ]]; then
    echo " ⚠ ERA5 files NOT found on server: ${missing_era5[*]}"
    echo "   Check that the ERA5 download (step2_download_era5_parallel.py) ran for these cases."
    echo ""
fi

if ! $DRY_RUN; then
    echo " All data is in: $TEST_DIR"
    echo ""
    echo " Next step:"
    echo "   bash scripts/lec_field_dependence_analysis/run_smoke_test.sh"
fi
