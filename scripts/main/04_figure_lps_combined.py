#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: Combined LPS Diagrams for Publication

This script combines two Lorenz Phase Space (LPS) diagrams into a single figure:
- Left panel: Conversion LPS (zoom)
- Right panel: Imports LPS (zoom)

Source figures:
- figures/cluster/lps_conversion_zoom.png
- figures/cluster/lps_imports_zoom.png

Author: Danilo Couto de Souza
Date: January 2026
"""

import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
CLUSTER_FIGURES_DIR = BASE_DIR / 'figures' / 'cluster'
MAIN_FIGURES_DIR = BASE_DIR / 'figures' / 'main'
MAIN_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Source files (LPS zoom versions)
SOURCE_FILES = [
    'lps_conversion_zoom.png',
    'lps_imports_zoom.png',
]

# Output file
OUTPUT_FILE = MAIN_FIGURES_DIR / 'lps_combined.png'

# Figure settings
DPI = 300
FIGSIZE = (16, 7)  # Wide figure to accommodate two LPS diagrams side by side

# Panel labels
PANEL_LABELS = ['(a)', '(b)']

# ============================================================================
# Main Function
# ============================================================================

def create_combined_figure():
    """Create combined LPS figure from individual LPS diagrams."""
    
    print("=" * 70)
    print("CREATING COMBINED LPS FIGURE")
    print("=" * 70)
    print(f"Source directory: {CLUSTER_FIGURES_DIR}")
    print(f"Output directory: {MAIN_FIGURES_DIR}")
    print()
    
    # Check if source files exist
    source_paths = [CLUSTER_FIGURES_DIR / f for f in SOURCE_FILES]
    missing_files = [f for f in source_paths if not f.exists()]
    
    if missing_files:
        print("❌ ERROR: Missing source files:")
        for f in missing_files:
            print(f"  - {f}")
        print()
        print("Please run the following command to generate them:")
        print("  python scripts/cluster/step5_plot_energy_patterns.py")
        return 1
    
    # Load images
    print("Loading images...")
    images = []
    for path in source_paths:
        img = mpimg.imread(path)
        images.append(img)
        print(f"  ✓ {path.name}")
    print()
    
    # Create figure with 1 row, 2 columns
    print("Creating combined figure...")
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI)
    
    # Plot each image
    for ax, img, label in zip(axes, images, PANEL_LABELS):
        ax.imshow(img)
        ax.axis('off')
        
        # Add panel label in upper left corner
        ax.text(0.02, 0.98, label, transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='none', alpha=0.8))
    
    # Adjust layout to minimize white space
    plt.subplots_adjust(wspace=0.05, hspace=0.0)
    
    # Save figure
    fig.savefig(OUTPUT_FILE, dpi=DPI, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    
    print(f"✓ Figure saved: {OUTPUT_FILE}")
    print(f"  Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print()
    
    print("=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print()
    print("Figure details:")
    print("  - Layout: 1 row × 2 columns")
    print("  - Left panel (a): Conversion LPS")
    print("  - Right panel (b): Imports LPS")
    print(f"  - Resolution: {DPI} DPI")
    print(f"  - Dimensions: {FIGSIZE[0]} × {FIGSIZE[1]} inches")
    print()
    
    return 0


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == '__main__':
    import sys
    sys.exit(create_combined_figure())
