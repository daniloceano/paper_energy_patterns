#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 5: Vertical Distribution of Energy Conversions for EP1, EP2, and EP3 Cyclones

This script creates a two-panel boxplot showing the vertical distribution of:
  • (a) Baroclinic conversion (Ca) across 32 pressure levels (1000–100 hPa)
  • (b) Barotropic conversion (Ck) across 32 pressure levels (1000–100 hPa)

Each panel shows three side-by-side boxes per pressure level, one for each
Energy Pattern (EP1, EP2, EP3). Analysis is restricted to the intensification
phase of each cyclone. A star marks, for each EP, the pressure level where its
median Ca is largest (panel a) / its median Ck is smallest (panel b).

Key findings:
  • Maximum Ca typically occurs in the mid-troposphere (~350–400 hPa) for all EPs
  • Minimum (most negative) Ck typically occurs in the mid-troposphere (~350 hPa) for EP1
  • EP comparison reveals pressure-level differences in baroclinic/barotropic energy pathways

Data source: corrected LorenzCycleToolKit 2.0.0 climatology
  • Validated phase-mean vertical profiles for all 3,820 cyclones
  • 32 pressure levels from 1000 to 10 hPa (1000–100 hPa displayed)
  • 3-hourly temporal resolution during intensification phase

IMPORTANT: This script requires corrected cluster and vertical products:
  • Cluster results: results/cluster/kmeans_clustered_data.csv
  • LEC data: data/corrected/vertical_phase_means_corrected.parquet

Outputs:
  • Figure: figures/main/vertical_levels.png (300 DPI)

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings('ignore')
from scripts.utils import corrected_lec as clec
from scripts.utils.ep_mapping import CLUSTER_TO_EP, assert_corrected_clustering

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results'
CLUSTER_RESULTS_DIR = RESULTS_DIR / 'cluster'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Figure settings
FIG_WIDTH = 14
FIG_HEIGHT = 16
DPI = 300

# Energy Pattern styles. Cluster identities come from cluster_to_ep.json.
EP_CONFIG = {
    'EP1': {
        'box_color': 'lightcoral',
        'edge_color': 'darkred',
        'median_color': 'darkred',
        'offset': -0.30,
    },
    'EP2': {
        'box_color': 'lightblue',
        'edge_color': 'darkblue',
        'median_color': 'darkblue',
        'offset': 0.00,
    },
    'EP3': {
        'box_color': 'lightgreen',
        'edge_color': 'darkgreen',
        'median_color': 'darkgreen',
        'offset': 0.30,
    },
}

BOX_WIDTH = 0.25

plt.rcParams.update({
    'font.size': 14,
    'axes.labelsize': 16,
    'axes.titlesize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 15,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans']
})

# ============================================================================
# Data Loading Functions
# ============================================================================

def get_cyclones_by_ep():
    """
    Load clustered data and return track IDs grouped by Energy Pattern.

    Returns
    -------
    dict
        Keys are EP names ('EP1', 'EP2', 'EP3'); values are lists of track_id strings.
    """
    cluster_file = CLUSTER_RESULTS_DIR / "kmeans_clustered_data.csv"

    if not cluster_file.exists():
        raise FileNotFoundError(
            f"Cluster file not found: {cluster_file}\n"
            "Please run clustering analysis first"
        )

    assert_corrected_clustering()
    clustered = pd.read_csv(cluster_file)
    clustered['track_id'] = clustered['track_id'].astype(str)
    clustered['ep'] = clustered['cluster'].map(CLUSTER_TO_EP)

    ep_tracks = {}
    for ep_num, ep_name in enumerate(EP_CONFIG, start=1):
        ep_tracks[ep_name] = clustered[clustered['ep'] == ep_num]['track_id'].tolist()

    return ep_tracks


def analyze_vertical_profiles(track_ids, ep_label, vertical_data):
    """
    Analyze vertical profiles of Ca and Ck for a given set of cyclones.

    Parameters
    ----------
    track_ids : list of str
        Cyclone track IDs to process.
    ep_label : str
        Label for this energy pattern (e.g., 'EP1'), used in progress output.

    Returns
    -------
    dict
        'ca_by_level': {pressure_hPa: [values per cyclone]}
        'ck_by_level': {pressure_hPa: [values per cyclone]}
        'ca_profiles': {track_id: pd.Series}
        'ck_profiles': {track_id: pd.Series}
    """
    results = {
        'ca_by_level': {},
        'ck_by_level': {},
        'ca_profiles': {},
        'ck_profiles': {},
    }

    wanted = {str(track_id) for track_id in track_ids}
    subset = vertical_data[
        vertical_data['track_id'].astype(str).isin(wanted)
        & (vertical_data['level_hpa'] >= 100.0)
    ].copy()
    for term, prefix in [('Ca', 'ca'), ('Ck', 'ck')]:
        term_data = subset[subset['term'] == term]
        for level, values in term_data.groupby('level_hpa')['value']:
            results[f'{prefix}_by_level'][int(level)] = values.dropna().tolist()
        for track_id, profile in term_data.groupby('track_id'):
            results[f'{prefix}_profiles'][str(track_id)] = (
                profile.set_index('level_hpa')['value']
            )

    successful = subset['track_id'].nunique()
    missing = len(wanted) - successful
    print(f"   {ep_label}: {successful} analyzed, {missing} skipped")
    return results


# ============================================================================
# Figure Generation
# ============================================================================

def create_boxplots(results_by_ep):
    """
    Create publication-quality boxplots showing Ca and Ck distributions by
    pressure level for EP1, EP2, and EP3 side by side.

    Parameters
    ----------
    results_by_ep : dict
        Keys are EP names ('EP1', 'EP2', 'EP3'); values are results dicts from
        analyze_vertical_profiles().
    """
    print("\n3. Creating Figure 5: Vertical Distribution of Energy Conversions...")

    # Collect all pressure levels present across all EPs
    all_levels = set()
    for ep_results in results_by_ep.values():
        all_levels.update(ep_results['ca_by_level'].keys())
    pressure_levels = sorted(all_levels, reverse=True)  # 1000 → 100 hPa

    group_positions = np.arange(len(pressure_levels))

    fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH, FIG_HEIGHT), sharey=True)

    from matplotlib.patches import Patch

    # ---- Panel (a): Ca ----
    ax1 = axes[0]
    legend_patches_a = []

    for ep_name, cfg in EP_CONFIG.items():
        ep_results = results_by_ep[ep_name]
        offsets = group_positions + cfg['offset']
        ca_data = [ep_results['ca_by_level'].get(p, [np.nan]) for p in pressure_levels]

        ax1.boxplot(
            ca_data,
            positions=offsets,
            widths=BOX_WIDTH,
            vert=False,
            manage_ticks=False,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color=cfg['median_color'], linewidth=2),
            boxprops=dict(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'], alpha=0.8),
            whiskerprops=dict(color=cfg['edge_color'], linewidth=1.2),
            capprops=dict(color=cfg['edge_color'], linewidth=1.2),
        )

        # Mark maximum Ca level for this EP
        ca_medians = [np.nanmedian(ep_results['ca_by_level'].get(p, [np.nan]))
                      for p in pressure_levels]
        max_idx = int(np.nanargmax(ca_medians))
        ax1.plot(
            ca_medians[max_idx], offsets[max_idx],
            '*', color=cfg['edge_color'], markersize=12,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5,
        )

        n_sys = len(ep_results['ca_profiles'])
        legend_patches_a.append(
            Patch(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'],
                  label=ep_name)
        )

    ax1.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_title('(a) Baroclinic Conversion (Ca)',
                  fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax1.legend(handles=legend_patches_a, loc='best', frameon=True,
               fancybox=True, shadow=True)
    ax1_fmt = mticker.ScalarFormatter(useMathText=True)
    ax1_fmt.set_scientific(True)
    ax1_fmt.set_powerlimits((0, 0))
    ax1.xaxis.set_major_formatter(ax1_fmt)

    # ---- Panel (b): Ck ----
    ax2 = axes[1]
    legend_patches_b = []

    for ep_name, cfg in EP_CONFIG.items():
        ep_results = results_by_ep[ep_name]
        offsets = group_positions + cfg['offset']
        ck_data = [ep_results['ck_by_level'].get(p, [np.nan]) for p in pressure_levels]

        ax2.boxplot(
            ck_data,
            positions=offsets,
            widths=BOX_WIDTH,
            vert=False,
            manage_ticks=False,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color=cfg['median_color'], linewidth=2),
            boxprops=dict(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'], alpha=0.8),
            whiskerprops=dict(color=cfg['edge_color'], linewidth=1.2),
            capprops=dict(color=cfg['edge_color'], linewidth=1.2),
        )

        # Mark minimum Ck level for this EP
        ck_medians = [np.nanmedian(ep_results['ck_by_level'].get(p, [np.nan]))
                      for p in pressure_levels]
        min_idx = int(np.nanargmin(ck_medians))
        ax2.plot(
            ck_medians[min_idx], offsets[min_idx],
            '*', color=cfg['edge_color'], markersize=12,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5,
        )

        n_sys = len(ep_results['ck_profiles'])
        legend_patches_b.append(
            Patch(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'],
                  label=ep_name)
        )

    ax2.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_title('(b) Barotropic Conversion (Ck)',
                  fontweight='bold', loc='left')
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax2.legend(handles=legend_patches_b, loc='best', frameon=True,
               fancybox=True, shadow=True)
    ax2_fmt = mticker.ScalarFormatter(useMathText=True)
    ax2_fmt.set_scientific(True)
    ax2_fmt.set_powerlimits((0, 0))
    ax2.xaxis.set_major_formatter(ax2_fmt)

    # Set pressure-level y-axis ticks after all boxplots are drawn
    pressure_labels = [str(int(p)) for p in pressure_levels]
    ax1.set_yticks(group_positions)
    ax1.set_yticklabels(pressure_labels)
    ax1.set_ylim([group_positions[0] - 0.6, group_positions[-1] + 0.6])

    plt.tight_layout()

    output_file = FIGURES_DIR / "vertical_levels.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()

    print(f"   ✓ Figure saved: {output_file}")

    # Summary statistics per EP
    print("\n   Key findings by Energy Pattern:")
    for ep_name, ep_results in results_by_ep.items():
        ca_medians = [np.nanmedian(ep_results['ca_by_level'].get(p, [np.nan]))
                      for p in pressure_levels]
        ck_medians = [np.nanmedian(ep_results['ck_by_level'].get(p, [np.nan]))
                      for p in pressure_levels]
        max_ca_idx = int(np.nanargmax(ca_medians))
        min_ck_idx = int(np.nanargmin(ck_medians))
        print(f"   • {ep_name}: max Ca = {ca_medians[max_ca_idx]:.4f} W m⁻² at "
              f"{pressure_levels[max_ca_idx]} hPa | "
              f"min Ck = {ck_medians[min_ck_idx]:.4f} W m⁻² at "
              f"{pressure_levels[min_ck_idx]} hPa")

    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate Figure 5: Vertical Distribution of Energy Conversions for EP1–EP3."""

    print("=" * 80)
    print("Figure 5: Vertical Distribution of Energy Conversions (EP1, EP2, EP3)")
    print("=" * 80)

    print("\n1. Loading cyclones by Energy Pattern...")
    ep_tracks = get_cyclones_by_ep()
    for ep_name, track_ids in ep_tracks.items():
        print(f"   {ep_name}: {len(track_ids)} cyclones")

    print(f"\n2. Loading corrected vertical profiles (intensification phase)...")
    vertical_data = clec.read_vertical_phase_means(
        terms=['Ca', 'Ck'], phases=['intensification']
    )
    print(f"   Data source: {clec.corrected_path(clec.VERTICAL_PHASE_MEANS)}")
    results_by_ep = {}
    for ep_name, track_ids in ep_tracks.items():
        results_by_ep[ep_name] = analyze_vertical_profiles(
            track_ids, ep_name, vertical_data
        )

    output_file = create_boxplots(results_by_ep)

    print("\n" + "=" * 80)
    print("✅ Figure 5 generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
