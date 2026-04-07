#!/bin/bash
#
# File Transfer Guide for EP Structure Analysis
# ===============================================
#
# Transfers pipeline outputs from remote server (master.iag.usp.br) to local
# machine using SCP with SSH key authentication.
#
# Steps run on remote:
#   step1 (select tracks) → step2 (download ERA5) → step3 (precompute composites)
#
# Steps run locally:
#   step4 (create figures) → step5 (update scientific notes)
#
# Author: Danilo Couto de Souza
# Date: February 2026

set -e

# ==============================================================================
# CONFIGURATION
# ==============================================================================

REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"

LOCAL_BASE="$HOME/Documents/Programs_and_scripts/paper_energy_patterns"

# ==============================================================================
# TRANSFER SECTIONS
# ==============================================================================

echo "=============================================================================="
echo "EP STRUCTURE ANALYSIS – FILE TRANSFER GUIDE"
echo "=============================================================================="
echo ""
echo "⚠️  IMPORTANT: You will be prompted for password in TWO separate windows!"
echo "    Keep both authentication windows ready during transfer."
echo ""
echo "Authentication: SSH key at $SSH_KEY"
echo "Remote server: ${REMOTE_USER}@${REMOTE_HOST}"
echo ""

# ------------------------------------------------------------------------------
# SECTION 1: ESSENTIAL FILES (precomputed composites)
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 1: ESSENTIAL FILES (Required)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Transfer precomputed composites (EP1 + EP2, ~100-300 MB total)"
echo ""
read -p "Transfer precomputed composites? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "→ Transferring data/era5_ep_structure/precomputed_composites_*.nc..."
    mkdir -p "${LOCAL_BASE}/data/era5_ep_structure"
    scp -i "$SSH_KEY" -C \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/data/era5_ep_structure/precomputed_composites_*.nc" \
        "${LOCAL_BASE}/data/era5_ep_structure/"
    echo "✓ Done!"
fi

# ------------------------------------------------------------------------------
# SECTION 2: OPTIONAL FILES
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 2: OPTIONAL FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Log files
echo "→ Transfer logs? (~1-5 MB)"
read -p "Transfer log files? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Transferring logs..."
    mkdir -p "${LOCAL_BASE}/logs"
    scp -i "$SSH_KEY" -C \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/ep_structure_\*.log" \
        "${LOCAL_BASE}/logs/" || echo "⚠️  No log files found or transfer failed"
    echo "✓ Done!"
fi

# Results metadata
echo ""
echo "→ Transfer results? (~1-10 MB metadata)"
read -p "Transfer results/ep_structure/ directory? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Transferring results..."
    mkdir -p "${LOCAL_BASE}/results/ep_structure"
    scp -i "$SSH_KEY" -C -r \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep_structure/" \
        "${LOCAL_BASE}/results/"
    echo "✓ Done!"
fi

# Figures (if generated on remote)
echo ""
echo "→ Transfer figures? (~5-15 MB)"
read -p "Transfer figures/ep_structure/? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Transferring figures..."
    mkdir -p "${LOCAL_BASE}/figures/ep_structure"
    scp -i "$SSH_KEY" -C -r \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/figures/ep_structure/" \
        "${LOCAL_BASE}/figures/"
    echo "✓ Done!"
fi

# ------------------------------------------------------------------------------
# SECTION 3: DO NOT TRANSFER
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⛔ SECTION 3: SKIP THESE FILES (keep on server)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "❌ DO NOT transfer: data/era5_ep_structure/*_era5.nc (~30-60 GB)"
echo "   → Raw ERA5 files stay on server"
echo ""

# ==============================================================================
# SUMMARY
# ==============================================================================

echo ""
echo "=============================================================================="
echo "✓ FILE TRANSFER COMPLETE"
echo "=============================================================================="
echo ""
echo "Next steps on LOCAL machine:"
echo "  1. cd ${LOCAL_BASE}"
echo "  2. conda activate paper_energy_patterns"
echo "  3. python scripts/ep_structure_analysis/step4_create_figures.py"
echo ""
echo "Transferred data size: ~100-300 MB (vs ~30-60 GB raw ERA5)"
echo ""
