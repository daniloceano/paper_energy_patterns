#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S2: All EP1 and EP2 Cyclones – Track Overview

Shows all EP1 and EP2 cyclones used in the dynamical structure composite 
analysis, highlighting the intensification phase and genesis locations.

Inputs:
  • results/ep_structure/ep1_cases.csv  (from step1_select_ep_tracks.py)
  • results/ep_structure/ep2_cases.csv  (from step1_select_ep_tracks.py)
  • Full track database (load_tracks utility)

The figure shows:
  • Complete cyclone tracks (gray, thin lines)
  • EP1 intensification phase (purple, thick lines)
  • EP2 intensification phase (dodgerblue, thick lines)
  • Genesis locations (EP1: purple circles, EP2: dodgerblue squares)

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
RESULTS_DIR = BASE_DIR / 'results' / 'ep_structure'
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
    """Load EP1 and EP2 cases from step1_select_ep_tracks results."""
    ep1_file = RESULTS_DIR / "ep1_cases.csv"
    ep2_file = RESULTS_DIR / "ep2_cases.csv"

    if not ep1_file.exists() or not ep2_file.exists():
        raise FileNotFoundError(
            f"Cases files not found: {ep1_file} or {ep2_file}\n"
            "Please run scripts/ep_structure_analysis/step1_select_ep_tracks.py first"
        )

    ep1_df = pd.read_csv(ep1_file)
    ep2_df = pd.read_csv(ep2_file)
    
    return ep1_df, ep2_df


# ============================================================================
# Main Figure Generation
# ============================================================================

def plot_selected_tracks(ep1_df, ep2_df, tracks_df):
    """
    Create overview map with all EP1 and EP2 cyclone tracks.
    Shows complete tracks and highlights intensification phase for each EP.
    """
    print("\nCreating Figure S2: All EP1 and EP2 Cyclones...")

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

    # Plot EP1 tracks
    for _, case in ep1_df.iterrows():
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
                color='gray', linewidth=0.6, alpha=0.3,
                transform=ccrs.PlateCarree(), zorder=2)

        # EP1 intensification phase (purple, thick)
        track_intens = track[(track['date'] >= t_start) & (track['date'] <= t_end)]
        if len(track_intens) > 0:
            ax.plot(track_intens['lon vor'].values, track_intens['lat vor'].values,
                    color='purple', linewidth=1.5, alpha=0.85,
                    transform=ccrs.PlateCarree(), zorder=3)

        # Genesis marker (purple circle)
        ax.plot(track['lon vor'].iloc[0], track['lat vor'].iloc[0],
                'o', color='purple', markersize=3, markeredgecolor='k',
                markeredgewidth=0.3, transform=ccrs.PlateCarree(), zorder=5)

    # Plot EP2 tracks
    for _, case in ep2_df.iterrows():
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
                color='gray', linewidth=0.6, alpha=0.3,
                transform=ccrs.PlateCarree(), zorder=2)

        # EP2 intensification phase (dodgerblue, thick)
        track_intens = track[(track['date'] >= t_start) & (track['date'] <= t_end)]
        if len(track_intens) > 0:
            ax.plot(track_intens['lon vor'].values, track_intens['lat vor'].values,
                    color='dodgerblue', linewidth=1.5, alpha=0.85,
                    transform=ccrs.PlateCarree(), zorder=3)

        # Genesis marker (dodgerblue square)
        ax.plot(track['lon vor'].iloc[0], track['lat vor'].iloc[0],
                's', color='dodgerblue', markersize=3, markeredgecolor='k',
                markeredgewidth=0.3, transform=ccrs.PlateCarree(), zorder=5)

    legend_elements = [
        Line2D([0], [0], color='gray', linewidth=1.5, alpha=0.5, label='Complete track'),
        Line2D([0], [0], color='purple', linewidth=2.5, label=f'EP1 intensification (n={len(ep1_df)})'),
        Line2D([0], [0], color='dodgerblue', linewidth=2.5, label=f'EP2 intensification (n={len(ep2_df)})'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='purple',
               markersize=6, markeredgecolor='k', label='EP1 genesis'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='dodgerblue',
               markersize=6, markeredgecolor='k', label='EP2 genesis'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11, framealpha=0.95)

    output_file = FIGURES_DIR / "S2_selected_tracks.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()

    print(f"\u2713 Figure saved: {output_file}")
    print(f"  \u2022 EP1 cyclones: {len(ep1_df)}")
    print(f"  \u2022 EP2 cyclones: {len(ep2_df)}")
    print(f"  \u2022 Total: {len(ep1_df) + len(ep2_df)}")

    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate Figure S2: All EP1 and EP2 Cyclones track overview."""

    print("=" * 80)
    print("Figure S2: All EP1 and EP2 Cyclones for Dynamical Structure Analysis")
    print("=" * 80)

    print("\n1. Loading EP1 and EP2 cases...")
    ep1_df, ep2_df = load_selected_cases()
    print(f"   Found {len(ep1_df)} EP1 cyclones")
    print(f"   Found {len(ep2_df)} EP2 cyclones")
    print(f"   Total: {len(ep1_df) + len(ep2_df)} cyclones")

    print("\n2. Loading complete track data...")
    tracks = load_tracks()
    print(f"   Loaded {tracks['track_id'].nunique()} cyclone tracks")

    print("\n3. Generating figure...")
    output_file = plot_selected_tracks(ep1_df, ep2_df, tracks)

    print("\n" + "=" * 80)
    print("✅ Figure S2 generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
