#!/bin/bash
#
# File Transfer Guide for EP1 Full Analysis
# ==========================================
#
# This script provides optimized file transfer commands for remote→local workflow
# using SCP with SSH key authentication (master.iag.usp.br).
#
# Authentication: Uses SSH key at ~/Documents/Master/id_rsa.danilocs
# Note: You will be prompted for password in TWO separate windows during transfer
#
# Author: Danilo Couto de Souza
# Date: February 2026

set -e  # Exit on error

# ==============================================================================
# CONFIGURATION (adjust paths as needed)
# ==============================================================================

# Remote server details
REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"

# Local base directory
LOCAL_BASE="$HOME/Documents/Programs_and_scripts/paper_energy_patterns"

# ==============================================================================
# TRANSFER SECTIONS
# ==============================================================================

echo "=============================================================================="
echo "EP1 FULL ANALYSIS - FILE TRANSFER GUIDE"
echo "=============================================================================="
echo ""
echo "⚠️  IMPORTANT: You will be prompted for password in TWO separate windows!"
echo "    Keep both authentication windows ready during transfer."
echo ""
echo "Authentication: SSH key at $SSH_KEY"
echo "Remote server: ${REMOTE_USER}@${REMOTE_HOST}"
echo ""

# ------------------------------------------------------------------------------
# ESSENTIAL FILES (~100-300 MB) - Required for local figure generation
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 1: ESSENTIAL FILES (Required)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Transfer precomputed composites (3 domain files, ~100-300 MB total)"
echo ""
read -p "Transfer precomputed composites? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "→ Transferring data/era5_ep1_full/precomputed_composites_*.nc..."
    scp -i "$SSH_KEY" -C \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/data/era5_ep1_full/precomputed_composites_*.nc" \
        "${LOCAL_BASE}/data/era5_ep1_full/"
    echo "✓ Done!"
fi

# ------------------------------------------------------------------------------
# OPTIONAL FILES
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SECTION 2: OPTIONAL FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Log files
echo "→ Transfer logs? (~1-5 MB)"
read -p "Transfer logs/step*.log files? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Transferring logs..."
    mkdir -p "${LOCAL_BASE}/logs"
    scp -i "$SSH_KEY" -C \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/logs/step*.log" \
        "${LOCAL_BASE}/logs/" || echo "⚠️  No log files found or transfer failed"
    echo "✓ Done!"
fi

# Results metadata
echo ""
echo "→ Transfer results? (~1-10 MB metadata)"
read -p "Transfer results/ep1_full/ directory? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Transferring results..."
    scp -i "$SSH_KEY" -C -r \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/results/ep1_full/" \
        "${LOCAL_BASE}/results/"
    echo "✓ Done!"
fi

# Figures (if generated on remote)
echo ""
echo "→ Transfer figures? (~5-15 MB)"
read -p "Transfer figures/ep1_full/composite/? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Transferring figures..."
    scp -i "$SSH_KEY" -C -r \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/figures/ep1_full/" \
        "${LOCAL_BASE}/figures/"
    echo "✓ Done!"
fi

# ------------------------------------------------------------------------------
# FILES TO SKIP (stay on remote server)
# ------------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⛔ SECTION 3: SKIP THESE FILES (keep on server)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "❌ DO NOT transfer: data/era5_ep1_full/*_era5.nc (~50-80 GB)"
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
echo "  2. conda activate paper_energy"
echo "  3. python scripts/ep1_full_analysis/step4_create_figures.py"
echo ""
echo "Transferred data size: ~100-300 MB (vs ~50-80 GB raw ERA5)"
echo "Storage optimization: Transferred only 0.2-0.6% of total data volume"
echo ""
