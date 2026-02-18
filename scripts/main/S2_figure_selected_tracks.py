#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S2: All EP1 Cyclones – Track Overview

Shows all 385 EP1 cyclones used in the instability composite analysis,
highlighting the intensification phase and genesis locations.

Inputs:
  • results/ep1_vertical/all_ep1_cases.csv  (from step1_select_all_ep1.py)
  • Full track database (load_tracks utility)

The figure shows:
  • Complete cyclone tracks (gray, thin lines)
  • Intensification phase segments (gold, thick lines)
  • Genesis locations (green circles)

Outputs:
  • Figure: figures/main/S2_selected_tracks.png (300 DPI)

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

from scripts.utils.load_data import load_tracks

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results' / 'ep1_vertical'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

# Figure settings
FIG_WIDTH = 12
FIG_HEIGHT = 8
DPI = 300

plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 14,
    'figure.titlesize': 14,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
})

# ============================================================================
# Load Data
# ============================================================================

def load_selected_cases():
    """Load all EP1 cases from step1_select_all_ep1 results."""
    selected_file = RESULTS_DIR / "all_ep1_cases.csv"

    if not selected_file.exists():
        raise FileNotFoundError(
            f"Cases file not found: {selected_file}\n"
            "Please run scripts/ep1_ibc_ibt_analysis/step1_select_all_ep1.py first"
        )

    return pd.read_csv(selected_file)


# ============================================================================
# Main Figure Generation
# ============================================================================

def plot_selected_tracks(selected_df, tracks_df):
    """
    Create overview map with all EP1 cyclone tracks.
    Shows complete tracks and highlights intensification phase.
    """
    print("\nCreating Figure S2: All EP1 Cyclones...")

    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))

    proj = ccrs.Stereographic(central_latitude=-90, central_longitude=0)
    ax = fig.add_subplot(111, projection=proj)
    ax.set_extent([-80, 40, -70, -20], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax.add_feature(cfeature.OCEAN, facecolor='white')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='black')

    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', alpha=0.7,
                      color='gray', x_inline=False, y_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}

    for _, case in selected_df.iterrows():
        track_id = case['track_id']
        t_start  = pd.to_datetime(case['intensification_start'])
        t_end    = pd.to_datetime(case['intensification_end'])

        track = tracks_df[tracks_df['track_id'] == track_id].copy()
        if len(track) == 0:
            continue
        track = track.sort_values('date')
        track['date'] = pd.to_datetime(track['date'])

        # Complete track (gray, thin)
        ax.plot(track['lon vor'].values, track['lat vor'].values,
                color='gray', linewidth=0.8, alpha=0.4,
                transform=ccrs.PlateCarree(), zorder=2)

        # Intensification phase (gold, thick)
        track_intens = track[(track['date'] >= t_start) & (track['date'] <= t_end)]
        if len(track_intens) > 0:
            ax.plot(track_intens['lon vor'].values, track_intens['lat vor'].values,
                    color='gold', linewidth=2.0, alpha=0.85,
                    transform=ccrs.PlateCarree(), zorder=3)

        # Genesis marker (green circle)
        ax.plot(track['lon vor'].iloc[0], track['lat vor'].iloc[0],
                'o', color='green', markersize=4, markeredgecolor='k',
                markeredgewidth=0.4, transform=ccrs.PlateCarree(), zorder=4)

    legend_elements = [
        Line2D([0], [0], color='gray', linewidth=1.5, alpha=0.6, label='Complete track'),
        Line2D([0], [0], color='gold', linewidth=2.5, label='Intensification phase'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
               markersize=6, markeredgecolor='k', label='Genesis'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=12, framealpha=0.95)

    n_cyclones = len(selected_df)

    output_file = FIGURES_DIR / "S2_selected_tracks.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()

    print(f"\u2713 Figure saved: {output_file}")
    print(f"  \u2022 All EP1 cyclones: {n_cyclones}")

    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate Figure S2: All EP1 Cyclones track overview."""

    print("=" * 80)
    print("Figure S2: All EP1 Cyclones for Instability Analysis")
    print("=" * 80)

    print("\n1. Loading all EP1 cases...")
    selected_df = load_selected_cases()
    print(f"   Found {len(selected_df)} EP1 cyclones")

    print("\n2. Loading complete track data...")
    tracks = load_tracks()
    print(f"   Loaded {tracks['track_id'].nunique()} cyclone tracks")

    print("\n3. Generating figure...")
    output_file = plot_selected_tracks(selected_df, tracks)

    print("\n" + "=" * 80)
    print("✅ Figure S2 generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
