#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S3: Vertical Distribution of Energy Conversions for EP1, EP2, and EP3 Cyclones

This script creates a two-panel boxplot showing the vertical distribution of:
  • (a) Baroclinic conversion (Ca) across 32 pressure levels (1000–100 hPa)
  • (b) Barotropic conversion (Ck) across 32 pressure levels (1000–100 hPa)

Each panel shows three side-by-side boxes per pressure level, one for each
Energy Pattern (EP1, EP2, EP3). Analysis is restricted to the intensification
phase of each cyclone.

Key findings:
  • Maximum Ca typically occurs in the mid-troposphere (~350–400 hPa) for all EPs
  • Minimum (most negative) Ck typically occurs in the mid-troposphere (~350 hPa) for EP1
  • EP comparison reveals pressure-level differences in baroclinic/barotropic energy pathways

Data source: Zenodo (DOI: 10.5281/zenodo.18243447)
  • Complete Lorenz Energy Cycle results with vertical resolution
  • 32 pressure levels from 1000 hPa to 100 hPa
  • 3-hourly temporal resolution during intensification phase

IMPORTANT: This script requires the cluster results and Zenodo LEC archive:
  • Cluster results: results/cluster/kmeans_clustered_data.csv
  • LEC data: data/temp_lec_zenodo/LEC_Results_energetic-patterns/

Outputs:
  • Figure: figures/main/S2_vertical_levels.png (300 DPI)

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
import warnings
warnings.filterwarnings('ignore')
from tqdm import tqdm

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
LEC_DATA_DIR = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

# Physical constants
GRAVITY = 9.8  # m/s² — used for Ck correction

# Figure settings
FIG_WIDTH = 18
FIG_HEIGHT = 10
DPI = 300

# Zenodo data source
ZENODO_DOI = "10.5281/zenodo.18243447"

# Energy Pattern configuration
# cluster index follows kmeans_clustered_data.csv convention: EP1=0, EP2=1, EP3=2
EP_CONFIG = {
    'EP1': {
        'cluster': 0,
        'box_color': 'lightcoral',
        'edge_color': 'darkred',
        'median_color': 'darkred',
        'offset': -0.30,
    },
    'EP2': {
        'cluster': 1,
        'box_color': 'lightblue',
        'edge_color': 'darkblue',
        'median_color': 'darkblue',
        'offset': 0.00,
    },
    'EP3': {
        'cluster': 2,
        'box_color': 'lightgreen',
        'edge_color': 'darkgreen',
        'median_color': 'darkgreen',
        'offset': 0.30,
    },
}

BOX_WIDTH = 0.25

plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
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

    clustered = pd.read_csv(cluster_file)

    ep_tracks = {}
    for ep_name, cfg in EP_CONFIG.items():
        cluster_idx = cfg['cluster']
        ep_tracks[ep_name] = clustered[clustered['cluster'] == cluster_idx]['track_id'].tolist()

    return ep_tracks


def load_lec_level_data(track_id, variable='Ca'):
    """
    Load LEC level data (Ca or Ck) for a specific cyclone.

    Data corrections applied:
    1. Ca: Sign inversion (-Ca_raw)
    2. Ck: Division by gravity (Ck_raw / 9.8)

    See SCIENTIFIC_NOTES.md §Figure S2 for validation details.
    """
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    file_path = lec_dir / f"{variable}_level.csv"

    # Handle case where file_path is actually a directory
    if file_path.is_dir():
        file_path = file_path / f"{variable}_level.csv"

    if not file_path.exists():
        return None

    df = pd.read_csv(file_path, index_col=0, parse_dates=True)

    # Apply data corrections
    if variable == 'Ca':
        df = -df
    elif variable == 'Ck':
        df = df / GRAVITY

    return df


def get_intensification_phase_times(track_id):
    """Get start and end times of the intensification phase from periods.csv."""
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = lec_dir / "periods.csv" / "periods.csv"

    if not periods_file.exists():
        return None

    periods = pd.read_csv(periods_file, index_col=0)

    if 'intensification' not in periods.index:
        return None

    intensification_row = periods.loc['intensification']
    start_time = pd.to_datetime(intensification_row['start'])
    end_time = pd.to_datetime(intensification_row['end'])

    return start_time, end_time


def analyze_vertical_profiles(track_ids, ep_label):
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

    successful = 0
    missing = 0

    for track_id in tqdm(track_ids, desc=f"  {ep_label}", leave=False):

        ca_data = load_lec_level_data(track_id, 'Ca')
        ck_data = load_lec_level_data(track_id, 'Ck')

        if ca_data is None or ck_data is None:
            missing += 1
            continue

        phase_times = get_intensification_phase_times(track_id)
        if phase_times is None:
            missing += 1
            continue

        start_time, end_time = phase_times

        ca_intens = ca_data[(ca_data.index >= start_time) & (ca_data.index <= end_time)]
        ck_intens = ck_data[(ck_data.index >= start_time) & (ck_data.index <= end_time)]

        if len(ca_intens) == 0:
            missing += 1
            continue

        ca_mean = ca_intens.mean(axis=0)
        ck_mean = ck_intens.mean(axis=0)

        # Convert pressure levels Pa → hPa; keep only >= 100 hPa
        pressure_hpa = ca_mean.index.astype(float) / 100.0
        valid = pressure_hpa >= 100.0
        pressure_hpa = pressure_hpa[valid]
        ca_mean = ca_mean[valid]
        ck_mean = ck_mean[valid]

        for p_hpa, ca_val, ck_val in zip(pressure_hpa, ca_mean.values, ck_mean.values):
            p_key = int(p_hpa)
            results['ca_by_level'].setdefault(p_key, []).append(ca_val)
            results['ck_by_level'].setdefault(p_key, []).append(ck_val)

        results['ca_profiles'][track_id] = ca_mean
        results['ck_profiles'][track_id] = ck_mean

        successful += 1

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
    print("\n3. Creating Figure S2: Vertical Distribution of Energy Conversions...")

    # Collect all pressure levels present across all EPs
    all_levels = set()
    for ep_results in results_by_ep.values():
        all_levels.update(ep_results['ca_by_level'].keys())
    pressure_levels = sorted(all_levels, reverse=True)  # 1000 → 100 hPa

    group_positions = np.arange(len(pressure_levels))

    fig, axes = plt.subplots(2, 1, figsize=(FIG_WIDTH, FIG_HEIGHT))

    # ---- Panel (a): Ca ----
    ax1 = axes[0]
    legend_patches_a = []

    for ep_name, cfg in EP_CONFIG.items():
        ep_results = results_by_ep[ep_name]
        offsets = group_positions + cfg['offset']
        ca_data = [ep_results['ca_by_level'].get(p, [np.nan]) for p in pressure_levels]

        bp = ax1.boxplot(
            ca_data,
            positions=offsets,
            widths=BOX_WIDTH,
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
            offsets[max_idx], ca_medians[max_idx],
            '*', color=cfg['edge_color'], markersize=12,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5,
        )

        n_sys = len(ep_results['ca_profiles'])
        from matplotlib.patches import Patch
        legend_patches_a.append(
            Patch(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'],
                  label=f"{ep_name} (n={n_sys})")
        )

    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Ca (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Baroclinic Conversion (Ca) by Pressure Level',
                  fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax1.set_xticks(group_positions)
    ax1.set_xticklabels([str(int(p)) for p in pressure_levels], rotation=45, ha='right')
    ax1.set_xlim([group_positions[0] - 0.6, group_positions[-1] + 0.6])
    ax1.legend(handles=legend_patches_a, loc='best', frameon=True,
               fancybox=True, shadow=True)

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
            offsets[min_idx], ck_medians[min_idx],
            '*', color=cfg['edge_color'], markersize=12,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5,
        )

        n_sys = len(ep_results['ck_profiles'])
        from matplotlib.patches import Patch
        legend_patches_b.append(
            Patch(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'],
                  label=f"{ep_name} (n={n_sys})")
        )

    ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Pressure Level (hPa)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Ck (W m$^{-2}$)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Barotropic Conversion (Ck) by Pressure Level',
                  fontweight='bold', loc='left')
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax2.set_xticks(group_positions)
    ax2.set_xticklabels([str(int(p)) for p in pressure_levels], rotation=45, ha='right')
    ax2.set_xlim([group_positions[0] - 0.6, group_positions[-1] + 0.6])
    ax2.legend(handles=legend_patches_b, loc='best', frameon=True,
               fancybox=True, shadow=True)

    plt.tight_layout()

    output_file = FIGURES_DIR / "S3_vertical_levels.png"
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
    """Generate Figure S2: Vertical Distribution of Energy Conversions for EP1–EP3."""

    print("=" * 80)
    print("Figure S2: Vertical Distribution of Energy Conversions (EP1, EP2, EP3)")
    print("=" * 80)

    if not LEC_DATA_DIR.exists():
        raise FileNotFoundError(
            f"LEC data directory not found: {LEC_DATA_DIR}\n"
            "Please download the Zenodo archive (DOI: 10.5281/zenodo.18243447) and "
            "unpack it into data/temp_lec_zenodo/"
        )

    print("\n1. Loading cyclones by Energy Pattern...")
    ep_tracks = get_cyclones_by_ep()
    for ep_name, track_ids in ep_tracks.items():
        print(f"   {ep_name}: {len(track_ids)} cyclones")

    print(f"\n2. Analyzing vertical profiles (intensification phase)...")
    print(f"   Data source: Zenodo (DOI: {ZENODO_DOI})")
    results_by_ep = {}
    for ep_name, track_ids in ep_tracks.items():
        results_by_ep[ep_name] = analyze_vertical_profiles(track_ids, ep_name)

    output_file = create_boxplots(results_by_ep)

    print("\n" + "=" * 80)
    print("✅ Figure S2 generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
