#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: Intensity, Seasonality, and Interannual Trends by Energy Pattern

This script creates a three-panel publication-ready figure combining:
  (a) Violin plot of maximum cyclone intensity (vorticity) per Energy Pattern
  (b) Seasonal distribution (% of cyclones per season) for each EP
  (c) Interannual time series (1979–2020) with Mann–Kendall trend analysis

Trend analysis methodology:
  • Annual cyclone counts per EP (42 years: 1979–2020)
  • Autocorrelation detection via Ljung–Box test (lags 1..10)
  • Mann–Kendall family tests: original, Hamed–Rao, Yue–Wang, pre-whitening variants
  • Theil–Sen slope estimator with 95% confidence intervals
  • When autocorrelation is detected (any lag p<0.05), Hamed–Rao modification is used for annotation
  • All test results saved to results/exploratory/mk_trend_results.csv

Outputs:
  • Figure: figures/main/ep_intensity_seasonality_trends.png (300 DPI)
  • CSV: results/exploratory/mk_trend_results.csv (all MK test results with slope, CI, autocorr info)

Author: Danilo Couto de Souza
Date: December 2024 / Updated January 2025
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import os
from datetime import datetime

try:
    from statsmodels.stats.diagnostic import acorr_ljungbox
except TypeError as e:
    raise EnvironmentError(
        f"Failed to import statsmodels: {e}\n"
        "This usually means you are running with the wrong Python environment.\n"
        "Please activate the project environment first:\n"
        "    conda activate paper_energy_patterns\n"
        "then run the script again."
    ) from e

# Require pymannkendall for trend analysis
try:
    import pymannkendall as mk
except ImportError:
    raise ImportError("pymannkendall is required for the trend analysis. Please install it (see requirements.txt)")

from scipy.stats import theilslopes

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results' / 'cluster'
FIGURES_DIR = BASE_DIR / 'figures' / 'main'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Energy Pattern configuration
EP_NAMES = ['EP1', 'EP2', 'EP3']
EP_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green

# Cluster to EP mapping (based on Ck energy levels)
CLUSTER_TO_EP = {
    0: 1,
    2: 2,
    1: 3
}

# Season configuration
SEASONS = {
    'DJF': [12, 1, 2],
    'MAM': [3, 4, 5],
    'JJA': [6, 7, 8],
    'SON': [9, 10, 11]
}
SEASON_COLORS = {
    'DJF': '#e74c3c',
    'MAM': '#f39c12',
    'JJA': '#3498db',
    'SON': '#2ecc71'
}

# Figure settings
# Font size configuration (customizable)
BASE_FONTSIZE = 10
AXIS_LABELSIZE = 11
PANEL_TITLESIZE = 12
TICK_LABELSIZE = 10
LEGEND_FONTSIZE = 9
FIGURE_TITLESIZE = 13
ANNOTATION_FONTSIZE = 9

plt.rcParams.update({
    'font.size': BASE_FONTSIZE,
    'axes.labelsize': AXIS_LABELSIZE,
    'axes.titlesize': PANEL_TITLESIZE,
    'xtick.labelsize': TICK_LABELSIZE,
    'ytick.labelsize': TICK_LABELSIZE,
    'legend.fontsize': LEGEND_FONTSIZE,
    'figure.titlesize': FIGURE_TITLESIZE,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
})

# ============================================================================
# Load Data
# ============================================================================

def load_data():
    """Load cyclone data with EP assignments."""
    import sys
    scripts_dir = BASE_DIR / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.load_data import load_tracks

    cluster_file = RESULTS_DIR / 'kmeans_clustered_data.csv'
    df_clustered = pd.read_csv(cluster_file, index_col=0)
    df_clustered['EP'] = df_clustered['cluster'].map(CLUSTER_TO_EP)

    print("Loading track data...")
    df_tracks = load_tracks()
    df_tracks['date'] = pd.to_datetime(df_tracks['date'])

    df_genesis = df_tracks.groupby('track_id').first().reset_index()

    df_max_vor = df_tracks.groupby('track_id')['vor42'].max().reset_index()
    df_max_vor.columns = ['track_id', 'max_vorticity_module']

    df = df_genesis.merge(
        df_clustered[['EP']],
        left_on='track_id',
        right_index=True,
        how='inner'
    )
    df = df.merge(df_max_vor, on='track_id', how='left')
    df['time'] = df['date']

    print(f"Loaded {len(df)} cyclones with EP assignments")
    print(f"EP distribution: {df['EP'].value_counts().sort_index().to_dict()}")
    return df

# ============================================================================
# Plotting Functions
# ============================================================================

def plot_intensity_violin(ax, df):
    data_list = []
    for ep_num in [1, 2, 3]:
        ep_data = df[df['EP'] == ep_num]
        intensities = ep_data['max_vorticity_module'].values
        data_list.append(intensities)

    parts = ax.violinplot(data_list, positions=[1, 2, 3], showmeans=True, showmedians=True, widths=0.7)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(EP_COLORS[i])
        pc.set_alpha(0.6)
        pc.set_edgecolor(EP_COLORS[i])
        pc.set_linewidth(1.5)

    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians', 'cmeans'):
        if partname in parts:
            vp = parts[partname]
            vp.set_edgecolor('black')
            vp.set_linewidth(1.2)
            vp.set_alpha(0.5)

    for i, (ep_num, color) in enumerate(zip([1, 2, 3], EP_COLORS)):
        ep_data = df[df['EP'] == ep_num]
        mean_val = ep_data['max_vorticity_module'].mean()
        std_val = ep_data['max_vorticity_module'].std()
        # ax.text(i + 1, mean_val + 0.5, f'{mean_val:.2f}±{std_val:.2f}', ha='center',
        #         va='bottom', fontsize=ANNOTATION_FONTSIZE, fontweight='bold')

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(EP_NAMES, fontweight='bold')
    ax.set_ylabel('Maximum Vorticity (-1 $\\times$ 10$^{-5}$ s$^{-1}$)', fontsize=AXIS_LABELSIZE, fontweight='bold')
    ax.set_title('(a) Intensity Distribution', fontsize=PANEL_TITLESIZE, fontweight='bold', loc='left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(bottom=0)


def plot_seasonality_bars(ax, df):
    df['month'] = pd.to_datetime(df['time']).dt.month
    df['season'] = df['month'].map(lambda m: next(s for s, months in SEASONS.items() if m in months))

    season_order = ['DJF', 'MAM', 'JJA', 'SON']
    x = np.arange(len(season_order))
    width = 0.25

    for i, (ep_num, color) in enumerate(zip([1, 2, 3], EP_COLORS)):
        ep_data = df[df['EP'] == ep_num]
        counts = []
        for season in season_order:
            count = len(ep_data[ep_data['season'] == season])
            counts.append(count)
        total = sum(counts)
        percentages = [c / total * 100 for c in counts]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, percentages, width, label=EP_NAMES[i], color=color, alpha=0.8, edgecolor='black', linewidth=1)
        for j, (bar, pct) in enumerate(zip(bars, percentages)):
            height = bar.get_height()
            # ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            #         f'{pct:.1f}%', ha='center', va='bottom', fontsize=ANNOTATION_FONTSIZE,
            #         rotation=90, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(season_order, fontweight='bold')
    ax.set_ylabel('Frequency (%)', fontsize=AXIS_LABELSIZE, fontweight='bold')
    ax.set_title('(b) Seasonal Distribution', fontsize=PANEL_TITLESIZE, fontweight='bold', loc='left')
    # Legend above the plot, keep x-position at right edge (bbox x=1.0)
    ax.legend(loc='upper right', ncol=1, frameon=True, fancybox=True, shadow=True,
              bbox_to_anchor=(1.0, 0.98), bbox_transform=ax.transAxes)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max([ax.get_ylim()[1]]) * 1.15)


def plot_interannual_trends(ax, df):
    df['year'] = pd.to_datetime(df['time']).dt.year
    years = sorted(df['year'].unique())

    results_dir = BASE_DIR / 'results' / 'exploratory'
    results_dir.mkdir(parents=True, exist_ok=True)
    out_csv = results_dir / 'mk_trend_results.csv'

    for ep_num, color, label in zip([1, 2, 3], EP_COLORS, EP_NAMES):
        ep_data = df[df['EP'] == ep_num]
        annual_counts = [len(ep_data[ep_data['year'] == year]) for year in years]

        ax.plot(years, annual_counts, marker='o', markersize=4, linewidth=1.5, color=color, label=label, alpha=0.8)

        # Compute Theil-Sen slope first (needed for detrending)
        try:
            tsl = theilslopes(annual_counts, years)
            slope = float(tsl[0])
            intercept = float(tsl[1])
            slope_ci_low = float(tsl[2])
            slope_ci_high = float(tsl[3])
        except Exception:
            slope = np.nan
            intercept = np.nan
            slope_ci_low = np.nan
            slope_ci_high = np.nan

        # Detrend series using Theil-Sen slope to remove trend before testing autocorrelation
        years_array = np.array(years)
        annual_counts_array = np.array(annual_counts)
        if not np.isnan(slope):
            trend_line = slope * years_array + intercept
            detrended = annual_counts_array - trend_line
        else:
            detrended = annual_counts_array

        # Test autocorrelation on detrended residuals using Ljung-Box portmanteau test
        # Use single test at max_lag (not multiple individual tests to avoid multiple comparisons)
        max_lag = min(10, max(1, len(years) - 1))
        lb_pvalue = np.nan
        try:
            lb_result = acorr_ljungbox(detrended, lags=[max_lag], return_df=True)
            lb_pvalue = float(lb_result['lb_pvalue'].values[0])
        except Exception:
            lb_pvalue = np.nan

        has_autocorr = (not np.isnan(lb_pvalue)) and (lb_pvalue < 0.05)

        tests = [
            ('original_test', getattr(mk, 'original_test', None)),
            ('hamed_rao_modification_test', getattr(mk, 'hamed_rao_modification_test', None)),
            ('yue_wang_modification_test', getattr(mk, 'yue_wang_modification_test', None)),
            ('pre_whitening_modification_test', getattr(mk, 'pre_whitening_modification_test', None)),
            ('trend_free_pre_whitening_modification_test', getattr(mk, 'trend_free_pre_whitening_modification_test', None)),
        ]

        results_rows = []
        for test_name, test_func in tests:
            if test_func is None:
                row = {'EP': label, 'test': test_name, 'trend': None, 'p_value': np.nan, 'tau': np.nan}
            else:
                try:
                    res = test_func(annual_counts)
                    trend = getattr(res, 'trend', None) or getattr(res, 'result', None)
                    pval = float(getattr(res, 'p', None) or getattr(res, 'p_value', np.nan))
                    tau = float(getattr(res, 'Tau', None) or getattr(res, 'tau', np.nan) or np.nan)
                    row = {'EP': label, 'test': test_name, 'trend': trend, 'p_value': pval, 'tau': tau}
                except Exception:
                    row = {'EP': label, 'test': test_name, 'trend': None, 'p_value': np.nan, 'tau': np.nan}

            row.update({
                'slope_per_year': slope,
                'slope_ci_low': slope_ci_low,
                'slope_ci_high': slope_ci_high,
                'lb_portmanteau_pvalue': lb_pvalue,
                'max_lag_tested': max_lag,
                'chosen': (test_name == 'hamed_rao_modification_test') if has_autocorr else (test_name == 'original_test'),
                'years_range': f"{min(years)}-{max(years)}",
                'created': datetime.utcnow().isoformat()
            })

            results_rows.append(row)

        df_rows = pd.DataFrame(results_rows)

        if not out_csv.exists():
            header_lines = [
                f"# mk_trend_results.csv",
                f"# Created: {datetime.utcnow().isoformat()} UTC",
                f"# Description: Mann-Kendall family of tests applied to annual cyclone counts per EP. Each row is a test result for one EP.",
                f"# Tests included: original_test, hamed_rao_modification_test, yue_wang_modification_test, pre_whitening_modification_test, trend_free_pre_whitening_modification_test",
                f"# Autocorrelation detection: Ljung-Box portmanteau test at lag h=min(10, n-1) on detrended residuals (Theil-Sen slope removed). Significant if p<0.05.",
                "# Columns: EP,test,trend,p_value,tau,slope_per_year,slope_ci_low,slope_ci_high,lb_portmanteau_pvalue,max_lag_tested,chosen,years_range,created",
                "# NOTE: lines starting with '#' are comments."
            ]
            with open(out_csv, 'w') as f:
                for L in header_lines:
                    f.write(L + '\n')
                df_rows.to_csv(f, index=False)
        else:
            df_rows.to_csv(out_csv, mode='a', header=False, index=False)

        chosen_test_name = 'hamed_rao_modification_test' if has_autocorr else 'original_test'
        chosen_row = df_rows[df_rows['test'] == chosen_test_name].iloc[0]
        chosen_p = float(chosen_row['p_value']) if not pd.isna(chosen_row['p_value']) else np.nan
        chosen_trend = chosen_row['trend']

        trend_line = slope * np.array(years) + intercept

        if not np.isnan(chosen_p) and chosen_p < 0.05:
            linestyle = '-'
            if chosen_trend == 'increasing':
                trend_symbol = '↑*'
            elif chosen_trend == 'decreasing':
                trend_symbol = '↓*'
            else:
                trend_symbol = '→*'
        else:
            linestyle = '--'
            if slope > 0:
                trend_symbol = '↑'
            elif slope < 0:
                trend_symbol = '↓'
            else:
                trend_symbol = '→'

        ax.plot(years, trend_line, linestyle=linestyle, linewidth=2.5, color=color, alpha=0.7)
        mid_year = years[len(years)//2]
        mid_idx = len(years)//2
        mid_value = annual_counts[mid_idx]
        ax.text(mid_year, mid_value, trend_symbol, fontsize=ANNOTATION_FONTSIZE+5, color=color, fontweight='bold', ha='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.8))

        # Print summary for this EP
        autocorr_status = f"YES (Ljung-Box at lag {max_lag}: p={lb_pvalue:.5f})" if has_autocorr else f"NO (Ljung-Box at lag {max_lag}: p={lb_pvalue:.5f})"
        print(f"  {label}:")
        print(f"    • Autocorrelation (detrended residuals): {autocorr_status}")
        print(f"    • Test used for annotation: {chosen_test_name}")
        print(f"    • Trend: {chosen_trend} (p={chosen_p:.5f}, tau={chosen_row['tau']:.4f})") 
        print(f"    • Theil–Sen slope: {slope:.4f} cyclones/year (95% CI: [{slope_ci_low:.4f}, {slope_ci_high:.4f}])")
        print(f"    • All {len(tests)} test results saved to CSV.")

    ax.set_xlabel('Year', fontsize=AXIS_LABELSIZE, fontweight='bold')
    ax.set_ylabel('Number of Cyclones', fontsize=AXIS_LABELSIZE, fontweight='bold')
    ax.set_title('(c) Interannual Variability and Trends (p < 0.05 | Solid: significant, Dashed: non-significant)', fontsize=PANEL_TITLESIZE, fontweight='bold', loc='left')
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True, ncol=3, fontsize=LEGEND_FONTSIZE)
    ax.grid(True, alpha=0.3, linestyle='--')

# ============================================================================
# Main Figure Creation
# ============================================================================

def create_figure():
    df = load_data()
    fig = plt.figure(figsize=(10, 6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.3, left=0.08, right=0.95, top=0.95, bottom=0.08)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    print("\n" + "="*60)
    print("Panel (a): Intensity violin plot")
    print("="*60)
    plot_intensity_violin(ax1, df)
    print("  ✓ Violin plot complete.")

    print("\n" + "="*60)
    print("Panel (b): Seasonal distribution bars")
    print("="*60)
    plot_seasonality_bars(ax2, df)
    print("  ✓ Seasonality bars complete.")

    print("\n" + "="*60)
    print("Panel (c): Interannual trends with Mann–Kendall analysis")
    print("="*60)
    print("Running autocorrelation checks and MK tests for each EP...\n")
    plot_interannual_trends(ax3, df)
    print("\n  ✓ Trend analysis complete.")

    output_file = FIGURES_DIR / '6_ep_intensity_seasonality_trends.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n{'='*60}")
    print(f"Figure saved: {output_file}")
    print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")
    plt.close()

if __name__ == '__main__':
    print("="*60)
    print("CREATING FIGURE: Intensity, Seasonality, and Trends")
    print("="*60)
    create_figure()
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
