#!/bin/bash
#
# File Transfer Guide for LEC Field Dependence Analysis
# ======================================================
#
# Transfers pipeline outputs from remote server (master.iag.usp.br / swell)
# to local machine using SCP with SSH key authentication.
#
# All 11 pipeline steps run on the remote server.
# Local machine receives: results CSVs, figures, logs, and verification report.
#
# Author: Danilo Couto de Souza
# Date: April 2026

set -e

# ==============================================================================
# CONFIGURATION
# ==============================================================================

REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"

LOCAL_BASE="$HOME/Documents/Programs_and_scripts/paper_energy_patterns"

SCP_OPTS="-i $SSH_KEY -C"   # -C enables compression

# ==============================================================================
# TRANSFER SECTIONS
# ==============================================================================

echo "=============================================================================="
echo "LEC FIELD DEPENDENCE ANALYSIS – FILE TRANSFER GUIDE"
echo "=============================================================================="
echo ""
echo "⚠️  IMPORTANT: You will be prompted for password for each SCP command."
echo "    Consider using ssh-agent or ControlMaster to avoid repeated prompts."
echo ""
echo "Authentication: SSH key at $SSH_KEY"
echo "Remote server:  ${REMOTE_USER}@${REMOTE_HOST}"
echo "Remote path:    ${REMOTE_BASE}"
echo ""

# ------------------------------------------------------------------------------
# SECTION 0: PRE-FLIGHT — run verification on remote
# ------------------------------------------------------------------------------

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SECTION 0: PRE-FLIGHT VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Running --verify on remote to check pipeline outputs..."
echo ""
ssh -i "$SSH_KEY" "${REMOTE_USER}@${REMOTE_HOST}" \
    "cd ${REMOTE_BASE} && conda run -n paper_energy_patterns python scripts/lec_field_dependence_analysis/monitor_pipeline.py --verify" \
    2>/dev/null || echo "⚠️  Could not run remote verification (non-fatal)"
echo ""
read -p "Continue with transfer? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Transfer cancelled."
    exit 0
fi

# ------------------------------------------------------------------------------
# SECTION 1: RESULTS (CSV tables — essential)
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 1: RESULTS — CSV tables (~5-50 MB)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Transfers merged CSVs, integrated tables, diagnostic/pairwise tables,"
echo "and summary tables.  Chunk files are NOT transferred (only merged outputs)."
echo ""
read -p "Transfer result CSVs? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    mkdir -p "${LOCAL_BASE}/results/lec_field_dependence"

    # Transfer only the essential files (not chunk files)
    ESSENTIAL_FILES=(
        "step1_eligible_cases.csv"
        "step1_metadata_report.txt"
        "step2_lec_intensification_means.csv"
        "step2_lec_qa_report.txt"
        "step3_era5_field_manifest.csv"
        "step3_field_mapping_report.txt"
        "step4_features_absolute.csv"
        "step5_features_anomaly.csv"
        "step6_integrated_all.csv"
        "step6_integrated_absolute.csv"
        "step6_integrated_anomaly.csv"
        "step6_integration_qa_report.txt"
        "step7b_diagnostic_table.csv"
        "step7b_pairwise_table.csv"
        "step7b_significance_report.txt"
        "step8_summary_table.csv"
        "step8_top_associations.csv"
        "step8_abs_vs_anom_comparison.csv"
        "step9_pipeline_status.txt"
    )

    FAIL_COUNT=0
    for f in "${ESSENTIAL_FILES[@]}"; do
        echo "  → ${f}..."
        scp $SCP_OPTS \
            "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/lec_field_dependence/${f}" \
            "${LOCAL_BASE}/results/lec_field_dependence/" 2>/dev/null \
            && echo "    ✓" \
            || { echo "    ⚠️  not found or transfer failed"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
    done

    echo ""
    if [[ $FAIL_COUNT -gt 0 ]]; then
        echo "⚠️  ${FAIL_COUNT} file(s) could not be transferred"
    else
        echo "✓ All result CSVs transferred!"
    fi
fi

# ------------------------------------------------------------------------------
# SECTION 2: FIGURES
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 2: FIGURES (~5-30 MB)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Transfers all PNG figures: PREDEP heatmaps, significance plots, volcanos."
echo ""
read -p "Transfer figures? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    mkdir -p "${LOCAL_BASE}/figures/lec_field_dependence"
    echo "  → figures/lec_field_dependence/*.png..."
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/figures/lec_field_dependence/*.png" \
        "${LOCAL_BASE}/figures/lec_field_dependence/" \
        && echo "✓ Figures transferred!" \
        || echo "⚠️  No figures found or transfer failed"
fi

# ------------------------------------------------------------------------------
# SECTION 3: LOGS (optional)
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 3: LOGS (optional, ~1-10 MB)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Transfer pipeline logs? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "${LOCAL_BASE}/logs"
    echo "  → Orchestrator and step logs..."
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/orchestrator_*.log" \
        "${LOCAL_BASE}/logs/" 2>/dev/null || true
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/lec_field_*.log" \
        "${LOCAL_BASE}/logs/" 2>/dev/null || true
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/step*_chunk*.log" \
        "${LOCAL_BASE}/logs/" 2>/dev/null || true
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/nohup_pipeline.log" \
        "${LOCAL_BASE}/logs/" 2>/dev/null || true
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/pipeline.pid" \
        "${LOCAL_BASE}/logs/" 2>/dev/null || true
    scp $SCP_OPTS \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/pipeline_status.txt" \
        "${LOCAL_BASE}/logs/" 2>/dev/null || true
    echo "✓ Logs transferred!"
fi

# ------------------------------------------------------------------------------
# SECTION 4: DO NOT TRANSFER
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⛔ SECTION 4: SKIP THESE FILES (keep on server)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "❌ DO NOT transfer: step*_chunk*.csv (~100s of chunk files, redundant)"
echo "   → Merged CSVs already contain all chunk data"
echo ""
echo "❌ DO NOT transfer: data/era5_ep_structure/*_era5.nc (~13 GB)"
echo "   → Raw ERA5 files stay on server"
echo ""

# ==============================================================================
# POST-TRANSFER VERIFICATION
# ==============================================================================

echo ""
echo "=============================================================================="
echo "✓ FILE TRANSFER COMPLETE"
echo "=============================================================================="
echo ""
echo "Run local verification:"
echo "  python scripts/lec_field_dependence_analysis/monitor_pipeline.py --verify"
echo ""
echo "Quick status check:"
echo "  python scripts/lec_field_dependence_analysis/monitor_pipeline.py --no-color"
echo ""
echo "Transferred data size: ~10-80 MB (vs ~13 GB ERA5 + chunks on server)"
echo ""
