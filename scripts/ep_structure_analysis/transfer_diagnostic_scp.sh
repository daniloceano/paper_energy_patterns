#!/bin/bash
#
# Minimal Transfer Script for Step 3 Diagnostics
# ================================================
#
# Transfers the minimum files needed to reproduce step3 failures locally:
#   1. Diagnostic outputs from diagnose_step3_failures.py (run on remote first)
#   2. A small sample of ERA5 NetCDF files (problematic EP1/EP2 + a few EP3)
#   3. Metadata CSVs for the sampled cases
#
# Workflow:
#   REMOTE: python scripts/ep_structure_analysis/diagnose_step3_failures.py
#   LOCAL:  bash scripts/ep_structure_analysis/transfer_diagnostic_scp.sh
#   LOCAL:  inspect diagnose_step3_failures.csv, pick cases to debug
#
# Author: Danilo Couto de Souza
# Date: April 2026

set -e

REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"
LOCAL_BASE="$HOME/Documents/Programs_and_scripts/paper_energy_patterns"

SCP="scp -i $SSH_KEY -C"

echo "=============================================================================="
echo "STEP 3 DIAGNOSTIC — FILE TRANSFER"
echo "=============================================================================="
echo ""
echo "Remote: ${REMOTE_USER}@${REMOTE_HOST}"
echo ""

# =============================================================================
# STEP 1 — Diagnostic outputs (always transfer these first)
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SECTION 1: Diagnostic outputs (run diagnose_step3_failures.py on remote first)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "→ Transferring results/ep_structure/diagnose_step3_*.* ..."
mkdir -p "${LOCAL_BASE}/results/ep_structure"
$SCP \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep_structure/diagnose_step3_failures.csv" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep_structure/diagnose_step3_summary.txt" \
    "${LOCAL_BASE}/results/ep_structure/" \
    || echo "⚠  Diagnostic outputs not found — run diagnose_step3_failures.py on remote first"

echo ""

# =============================================================================
# SECTION 2 — Cases CSV files
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SECTION 2: Cases CSV files (ep1_cases, ep2_cases, ep3_cases)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Transfer cases CSVs? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    $SCP \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep_structure/ep1_cases.csv" \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep_structure/ep2_cases.csv" \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep_structure/ep3_cases.csv" \
        "${LOCAL_BASE}/results/ep_structure/"
    echo "✓ Done!"
fi

echo ""

# =============================================================================
# SECTION 3 — Sample ERA5 files for local debugging
# =============================================================================
#
# Strategy: transfer a small representative sample of cases
#   - 3 EP1 failures (likely no_meta_file — from step2b)
#   - 3 EP2 failures (same issue)
#   - 3 EP3 OK cases (baseline from step2 fresh download)
#   - 3 EP1/EP2 OOB cases (if any survive after fix)
#
# After running Section 1, open diagnose_step3_failures.csv and fill in
# the track IDs below before running this section.
#
# Example (fill in based on your diagnostic output):

EP1_FAIL_TRACK_IDS=()   # e.g., (19790135 19790166 19790201)
EP2_FAIL_TRACK_IDS=()   # e.g., (19790050 19790099 19800010)
EP3_OK_TRACK_IDS=()     # e.g., (19790001 19790026 19790055)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SECTION 3: Sample ERA5 NetCDF files (for local debugging)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Edit this script to fill in track IDs from diagnose_step3_failures.csv."
echo ""

if [ ${#EP1_FAIL_TRACK_IDS[@]} -eq 0 ] && [ ${#EP2_FAIL_TRACK_IDS[@]} -eq 0 ] && [ ${#EP3_OK_TRACK_IDS[@]} -eq 0 ]; then
    echo "⚠  No track IDs specified. Edit EP1_FAIL_TRACK_IDS / EP2_FAIL_TRACK_IDS /"
    echo "   EP3_OK_TRACK_IDS near the top of this script, then re-run."
else
    read -p "Transfer sample ERA5 files? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        mkdir -p "${LOCAL_BASE}/data/era5_ep_structure"

        for TID in "${EP1_FAIL_TRACK_IDS[@]}" "${EP2_FAIL_TRACK_IDS[@]}" "${EP3_OK_TRACK_IDS[@]}"; do
            echo "  → ${TID}_era5.nc ..."
            $SCP \
                "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/data/era5_ep_structure/${TID}_era5.nc" \
                "${LOCAL_BASE}/data/era5_ep_structure/" \
                || echo "    ⚠ Not found: ${TID}_era5.nc"

            echo "  → ${TID}_metadata.csv ..."
            $SCP \
                "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/data/era5_ep_structure/${TID}_metadata.csv" \
                "${LOCAL_BASE}/data/era5_ep_structure/" \
                || echo "    ⚠ Not found: ${TID}_metadata.csv (confirms missing metadata bug)"
        done
        echo "✓ Done!"
    fi
fi

echo ""

# =============================================================================
# SECTION 4 — Logs
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SECTION 4: Step 3 log files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Transfer step3 log files? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "${LOCAL_BASE}/logs"
    $SCP \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/ep_structure_composites_*.log" \
        "${LOCAL_BASE}/logs/" \
        || echo "⚠  No log files found"
    echo "✓ Done!"
fi

echo ""
echo "=============================================================================="
echo "✓ TRANSFER COMPLETE"
echo "=============================================================================="
echo ""
echo "Next steps:"
echo "  1. Open results/ep_structure/diagnose_step3_summary.txt"
echo "  2. Open results/ep_structure/diagnose_step3_failures.csv"
echo "  3. Fill in track IDs in Section 3 of this script for deeper local debugging"
echo ""
echo "After pushing fixes, re-run on remote:"
echo "  python scripts/ep_structure_analysis/step2b_reuse_legacy_era5.py --dry-run"
echo "    → check that 'compatible' count increases"
echo "  python scripts/ep_structure_analysis/diagnose_step3_failures.py"
echo "    → confirm no_meta_file count drops to 0"
echo "  python scripts/ep_structure_analysis/step3_precompute_composites.py --mode central_time --jobs 4"
echo ""
