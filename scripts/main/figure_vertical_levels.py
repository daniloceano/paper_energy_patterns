#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vertical Distribution of Energy Conversions for EP1, EP2, and EP3 Cyclones

This script creates a two-panel boxplot showing the vertical distribution of:
  • (a) Baroclinic conversion (Ca) from 1000 to 100 hPa
  • (b) Barotropic conversion (Ck) from 1000 to 100 hPa

Each panel shows three side-by-side boxes per pressure level, one for each
Energy Pattern (EP1, EP2, EP3). Analysis is restricted to the intensification
phase of each cyclone. A star marks, for each EP, the pressure level where the
absolute median conversion is largest. This keeps the diagnostic meaningful for
both negative-Ck (mean-flow-to-eddy) and positive-Ck (eddy-to-mean-flow) regimes.

The corrected profiles are pressure integrands in W m^-2 Pa^-1. Their pressure
integral reproduces the corresponding phase-mean Ca or Ck in W m^-2.

Data source: corrected LorenzCycleToolKit 2.0.0 climatology
  • Validated phase-mean vertical profiles for all 3,820 cyclones
  • 32 pressure levels from 1000 to 10 hPa (1000–100 hPa displayed)
  • 3-hourly temporal resolution during intensification phase

IMPORTANT: This script requires corrected cluster and vertical products:
  • Cluster results: results/cluster/kmeans_clustered_data.csv
  • LEC data: data/corrected/vertical_phase_means_corrected.parquet

Outputs:
  • Figure: figures/main/vertical_levels.png (300 DPI)
  • Level statistics: results/vertical_structure/level_statistics.csv
  • Machine-readable summary: results/vertical_structure/summary.json

Author: Danilo Couto de Souza
Date: January 2026
"""

import hashlib
import json
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
ANALYSIS_RESULTS_DIR = RESULTS_DIR / 'vertical_structure'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Figure settings
FIG_WIDTH = 14
FIG_HEIGHT = 16
DPI = 300
DISPLAY_MIN_HPA = 100.0
DISPLAY_MAX_HPA = 1000.0
PROFILE_UNITS = 'W m^-2 Pa^-1'
INTEGRATED_UNITS = 'W m^-2'

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
        & vertical_data['level_hpa'].between(DISPLAY_MIN_HPA, DISPLAY_MAX_HPA)
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


def _sha256(path):
    """Return the SHA-256 checksum of a local source product."""
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _integrate_profiles(vertical_data, ep_by_track, lower_hpa, upper_hpa):
    """Integrate every cyclone profile over one pressure layer."""
    profiles = vertical_data.copy()
    profiles['track_id'] = profiles['track_id'].astype(str)
    profiles['ep'] = profiles['track_id'].map(ep_by_track)
    if profiles['ep'].isna().any():
        missing = profiles.loc[profiles['ep'].isna(), 'track_id'].nunique()
        raise RuntimeError(f'{missing} vertical-profile cyclones lack an EP assignment')

    wide = profiles.pivot(
        index=['track_id', 'ep', 'term'], columns='level_hpa', values='value'
    )
    levels = np.array(sorted(wide.columns.astype(float)))
    selected = (levels >= lower_hpa) & (levels <= upper_hpa)
    selected_levels = levels[selected]
    if len(selected_levels) < 2:
        raise ValueError(
            f'layer {lower_hpa:g}-{upper_hpa:g} hPa has fewer than two levels'
        )
    wide = wide.reindex(columns=levels)
    integrals = np.trapz(
        wide.loc[:, selected].to_numpy(dtype=float),
        selected_levels * 100.0,
        axis=1,
    )
    output = wide.index.to_frame(index=False)
    output['integral'] = integrals
    return output


def _validate_vertical_integrals(full_integrals):
    """Check pressure integrals against corrected integrated LEC results."""
    cache = clec.read_corrected_cache()
    phase_cache = cache[cache['phase'].eq('intensification')].copy()

    # A minority of cyclones has a secondary intensification interval. The
    # vertical builder combines its timesteps with the main interval, whereas
    # the cache retains one row per interval. Exact one-to-one validation is
    # therefore performed on cyclones with a single intensification interval.
    interval_counts = phase_cache.groupby('track_id', observed=True).size()
    single_interval_ids = set(interval_counts[interval_counts.eq(1)].index.astype(str))
    phase_cache['track_id'] = phase_cache['track_id'].astype(str)
    phase_cache = phase_cache[phase_cache['track_id'].isin(single_interval_ids)]
    cache_long = phase_cache.melt(
        id_vars=['track_id'],
        value_vars=['Ca', 'Ck'],
        var_name='term',
        value_name='integrated_reference',
    )
    check = full_integrals.merge(
        cache_long, on=['track_id', 'term'], how='inner', validate='one_to_one'
    )
    check['absolute_error'] = (
        check['integral'] - check['integrated_reference']
    ).abs()
    scale = check['integrated_reference'].abs().clip(lower=1e-12)
    check['relative_error'] = check['absolute_error'] / scale
    if not np.allclose(
        check['integral'], check['integrated_reference'], rtol=1e-10, atol=1e-10
    ):
        worst = check.nlargest(1, 'absolute_error').iloc[0]
        raise RuntimeError(
            'vertical integration does not reproduce the corrected cache: '
            f"track {worst['track_id']} {worst['term']} "
            f"absolute error {worst['absolute_error']:.3e}"
        )
    return {
        'single_interval_cyclones_checked': len(single_interval_ids),
        'comparison_rows': len(check),
        'maximum_absolute_error': float(check['absolute_error'].max()),
        'maximum_relative_error': float(check['relative_error'].max()),
        'rtol': 1e-10,
        'atol': 1e-10,
    }


def write_analysis_outputs(vertical_data, ep_tracks):
    """Write reproducible level statistics and a compact site-ready summary."""
    ep_by_track = {
        str(track_id): ep_name
        for ep_name, track_ids in ep_tracks.items()
        for track_id in track_ids
    }
    analysis = vertical_data.copy()
    analysis['track_id'] = analysis['track_id'].astype(str)
    analysis['ep'] = analysis['track_id'].map(ep_by_track)
    if analysis['ep'].isna().any():
        raise RuntimeError('vertical products and corrected clustering are inconsistent')
    if analysis.duplicated(['track_id', 'phase', 'term', 'level_hpa']).any():
        raise RuntimeError('duplicate cyclone/phase/term/level rows in vertical product')
    if not np.isfinite(analysis['value']).all():
        raise RuntimeError('non-finite values in corrected vertical product')

    expected_terms = {'Ca', 'Ck'}
    available_terms = set(analysis['term'].unique())
    if available_terms != expected_terms:
        raise RuntimeError(
            f'vertical product terms are {sorted(available_terms)}, '
            f'expected {sorted(expected_terms)}'
        )
    expected_levels = analysis['level_hpa'].nunique()
    coverage = analysis.groupby(
        ['track_id', 'term'], observed=True
    )['level_hpa'].nunique()
    expected_profiles = analysis['track_id'].nunique() * len(expected_terms)
    incomplete = coverage.ne(expected_levels)
    if len(coverage) != expected_profiles or incomplete.any():
        raise RuntimeError(
            'corrected vertical product has missing cyclone/term/level coverage: '
            f'{int(incomplete.sum())} incomplete profiles and '
            f'{expected_profiles - len(coverage)} missing profiles'
        )

    displayed = analysis[
        analysis['level_hpa'].between(DISPLAY_MIN_HPA, DISPLAY_MAX_HPA)
    ].copy()
    level_stats = (
        displayed.groupby(['ep', 'term', 'level_hpa'], observed=True)['value']
        .agg(
            n='count',
            mean='mean',
            median='median',
            q1=lambda values: values.quantile(0.25),
            q3=lambda values: values.quantile(0.75),
        )
        .reset_index()
        .sort_values(['ep', 'term', 'level_hpa'])
    )
    level_stats_path = ANALYSIS_RESULTS_DIR / 'level_statistics.csv'
    level_stats.to_csv(level_stats_path, index=False)

    layers = {
        'full_10_1000': (10.0, 1000.0),
        'displayed_100_1000': (100.0, 1000.0),
        'lower_700_1000': (700.0, 1000.0),
        'middle_400_700': (400.0, 700.0),
        'upper_100_400': (100.0, 400.0),
        'above_10_100': (10.0, 100.0),
    }
    layer_frames = {}
    for layer_name, (lower_hpa, upper_hpa) in layers.items():
        layer_frames[layer_name] = _integrate_profiles(
            analysis, ep_by_track, lower_hpa, upper_hpa
        )
    full_integrals = layer_frames['full_10_1000']
    validation = _validate_vertical_integrals(full_integrals)

    patterns = {}
    for ep_name in EP_CONFIG:
        patterns[ep_name] = {'n': len(ep_tracks[ep_name])}
        for term in ['Ca', 'Ck']:
            term_levels = level_stats[
                level_stats['ep'].eq(ep_name) & level_stats['term'].eq(term)
            ]
            dominant = term_levels.loc[term_levels['median'].abs().idxmax()]
            column = full_integrals[
                full_integrals['ep'].eq(ep_name) & full_integrals['term'].eq(term)
            ]['integral']
            layer_summary = {}
            for layer_name, frame in layer_frames.items():
                values = frame[
                    frame['ep'].eq(ep_name) & frame['term'].eq(term)
                ]['integral']
                layer_summary[layer_name] = {
                    'mean': float(values.mean()),
                    'median': float(values.median()),
                }
            patterns[ep_name][term] = {
                'dominant_level_hpa': int(dominant['level_hpa']),
                'dominant_median_profile': float(dominant['median']),
                'column_mean': float(column.mean()),
                'column_median': float(column.median()),
                'column_q1': float(column.quantile(0.25)),
                'column_q3': float(column.quantile(0.75)),
                'positive_percentage': float(100.0 * column.gt(0).mean()),
                'negative_percentage': float(100.0 * column.lt(0).mean()),
                'layers': layer_summary,
            }

    source_path = clec.corrected_path(clec.VERTICAL_PHASE_MEANS)
    summary = {
        'analysis': 'vertical_structure',
        'phase': 'intensification',
        'source': str(source_path.relative_to(BASE_DIR)),
        'source_sha256': _sha256(source_path),
        'cluster_source': 'results/cluster/kmeans_clustered_data.csv',
        'population': {
            'total': int(analysis['track_id'].nunique()),
            'energy_patterns': {
                ep_name: len(track_ids) for ep_name, track_ids in ep_tracks.items()
            },
            'levels_available': int(analysis['level_hpa'].nunique()),
            'levels_displayed': int(displayed['level_hpa'].nunique()),
            'display_range_hpa': [int(DISPLAY_MIN_HPA), int(DISPLAY_MAX_HPA)],
        },
        'units': {
            'profile': PROFILE_UNITS,
            'integrated': INTEGRATED_UNITS,
        },
        'sign_convention': {
            'Ca': 'Ca > 0: zonal available potential energy transfers to eddy available potential energy',
            'Ck': 'Ck < 0: zonal kinetic energy transfers to eddy kinetic energy; Ck > 0 is the reverse',
        },
        'validation': validation,
        'patterns': patterns,
        'figure': 'figures/main/vertical_levels.png',
        'level_statistics': 'results/vertical_structure/level_statistics.csv',
    }
    summary_path = ANALYSIS_RESULTS_DIR / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f"   ✓ Level statistics saved: {level_stats_path}")
    print(f"   ✓ Analysis summary saved: {summary_path}")
    print(
        "   ✓ Vertical integration validation: "
        f"{validation['comparison_rows']} comparisons, "
        f"max |error| = {validation['maximum_absolute_error']:.3e} W m⁻²"
    )
    return summary


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
    print("\nCreating the vertical distribution of energy conversions figure...")

    # Collect all pressure levels present across all EPs
    all_levels = set()
    for ep_results in results_by_ep.values():
        all_levels.update(ep_results['ca_by_level'].keys())
    pressure_levels = sorted(all_levels, reverse=True)  # 1000 → 100 hPa

    group_positions = np.arange(len(pressure_levels))

    fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH, FIG_HEIGHT), sharey=True)

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    dominant_marker = Line2D(
        [0], [0], marker='*', linestyle='none', color='slategray',
        markeredgecolor='white', markeredgewidth=0.8, markersize=12,
        label='Largest |median|',
    )

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

        # Mark the level with the strongest signed-median magnitude for this EP.
        ca_medians = [np.nanmedian(ep_results['ca_by_level'].get(p, [np.nan]))
                      for p in pressure_levels]
        max_idx = int(np.nanargmax(np.abs(ca_medians)))
        ax1.plot(
            ca_medians[max_idx], offsets[max_idx],
            '*', color=cfg['edge_color'], markersize=12,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5,
        )

        legend_patches_a.append(
            Patch(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'],
                  label=ep_name)
        )

    ax1.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_title(r'(a) Baroclinic Conversion ($C_A$)',
                  fontweight='bold', loc='left')
    ax1.set_xlabel(r'Pressure-level conversion profile (W m$^{-2}$ Pa$^{-1}$)')
    ax1.set_ylabel('Pressure (hPa)')
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax1.legend(handles=[*legend_patches_a, dominant_marker], loc='best', frameon=True,
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

        # Mark the dominant magnitude, preserving whether Ck is positive or negative.
        ck_medians = [np.nanmedian(ep_results['ck_by_level'].get(p, [np.nan]))
                      for p in pressure_levels]
        min_idx = int(np.nanargmax(np.abs(ck_medians)))
        ax2.plot(
            ck_medians[min_idx], offsets[min_idx],
            '*', color=cfg['edge_color'], markersize=12,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5,
        )

        legend_patches_b.append(
            Patch(facecolor=cfg['box_color'], edgecolor=cfg['edge_color'],
                  label=ep_name)
        )

    ax2.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_title(r'(b) Barotropic Conversion ($C_K$)',
                  fontweight='bold', loc='left')
    ax2.set_xlabel(r'Pressure-level conversion profile (W m$^{-2}$ Pa$^{-1}$)')
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax2.legend(handles=[*legend_patches_b, dominant_marker], loc='best', frameon=True,
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

    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate the vertical distribution of energy conversions for EP1–EP3."""

    print("=" * 80)
    print("Vertical Distribution of Energy Conversions (EP1, EP2, EP3)")
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

    print("\n3. Validating and summarizing the corrected vertical structure...")
    summary = write_analysis_outputs(vertical_data, ep_tracks)

    print("\n4. Creating the corrected vertical-structure figure...")
    create_boxplots(results_by_ep)

    print("\n   Key findings by Energy Pattern:")
    for ep_name, pattern in summary['patterns'].items():
        ca = pattern['Ca']
        ck = pattern['Ck']
        print(
            f"   • {ep_name}: mean column Ca = {ca['column_mean']:.2f} W m⁻²; "
            f"dominant median-profile level = {ca['dominant_level_hpa']} hPa | "
            f"mean column Ck = {ck['column_mean']:.2f} W m⁻²; "
            f"dominant median-profile level = {ck['dominant_level_hpa']} hPa"
        )

    print("\n" + "=" * 80)
    print("✅ Vertical-distribution figure generation complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
