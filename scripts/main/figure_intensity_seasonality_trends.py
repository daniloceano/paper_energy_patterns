#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: Intensity, Seasonality, and Interannual Trends by Energy Pattern

This script creates a publication-ready figure combining:
- Top-left: Violin plot of maximum intensity by EP
- Top-right: Seasonal bar chart for each EP
- Bottom: Interannual variability with Mann-Kendall trends (full width)

Author: Danilo Couto de Souza
Date: December 2024
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Try importing Mann-Kendall for trend analysis
try:
    import pymannkendall as mk
    from scipy.stats import theilslopes
    HAS_MANNKENDALL = True
except ImportError:
    HAS_MANNKENDALL = False
    print("Warning: pymannkendall not installed. Trends will not be computed.")

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
    0: 1,  # Cluster 0 → EP1 (lowest Ck)
    2: 2,  # Cluster 2 → EP2 (middle Ck)
    1: 3   # Cluster 1 → EP3 (highest Ck)
}

# Season configuration
SEASONS = {
    'DJF': [12, 1, 2],  # Summer
    'MAM': [3, 4, 5],   # Autumn
    'JJA': [6, 7, 8],   # Winter
    'SON': [9, 10, 11]  # Spring
}
SEASON_COLORS = {
    'DJF': '#e74c3c',  # Red
    'MAM': '#f39c12',  # Orange
    'JJA': '#3498db',  # Blue
    'SON': '#2ecc71'   # Green
}

# Figure settings
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
})

# ============================================================================
# Load Data
# ============================================================================

def load_data():
    """Load cyclone data with EP assignments."""
    # Add parent directory to path for imports
    import sys
    scripts_dir = BASE_DIR / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.load_data import load_tracks
    
    # Load clustering results
    cluster_file = RESULTS_DIR / 'kmeans_clustered_data.csv'
    df_clustered = pd.read_csv(cluster_file, index_col=0)
    df_clustered['EP'] = df_clustered['cluster'].map(CLUSTER_TO_EP)
    
    # Load tracks
    print("Loading track data...")
    df_tracks = load_tracks()
    df_tracks['date'] = pd.to_datetime(df_tracks['date'])
    
    # Get genesis (first observation per cyclone)
    df_genesis = df_tracks.groupby('track_id').first().reset_index()
    
    # Get maximum vorticity per cyclone
    df_max_vor = df_tracks.groupby('track_id')['vor42'].max().reset_index()
    df_max_vor.columns = ['track_id', 'max_vorticity_module']
    
    # Merge all data
    df = df_genesis.merge(
        df_clustered[['EP']],
        left_on='track_id',
        right_index=True,
        how='inner'
    )
    df = df.merge(df_max_vor, on='track_id', how='left')
    
    # Rename date column for consistency
    df['time'] = df['date']
    
    print(f"Loaded {len(df)} cyclones with EP assignments")
    print(f"EP distribution: {df['EP'].value_counts().sort_index().to_dict()}")
    
    return df

# ============================================================================
# Plotting Functions
# ============================================================================

def plot_intensity_violin(ax, df):
    """Plot violin plot of maximum intensity by EP."""
    # Prepare data
    data_list = []
    for ep_num in [1, 2, 3]:
        ep_data = df[df['EP'] == ep_num]
        intensities = ep_data['max_vorticity_module'].values * 1e5  # Convert to 10^-5 s^-1
        data_list.append(intensities)
    
    # Create violin plot
    parts = ax.violinplot(data_list, positions=[1, 2, 3], 
                          showmeans=True, showmedians=True,
                          widths=0.7)
    
    # Color the violins
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(EP_COLORS[i])
        pc.set_alpha(0.6)
        pc.set_edgecolor(EP_COLORS[i])
        pc.set_linewidth(1.5)
    
    # Style the lines
    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians', 'cmeans'):
        if partname in parts:
            vp = parts[partname]
            vp.set_edgecolor('black')
            vp.set_linewidth(1.2)
    
    # Add mean values as text
    for i, (ep_num, color) in enumerate(zip([1, 2, 3], EP_COLORS)):
        ep_data = df[df['EP'] == ep_num]
        mean_val = ep_data['max_vorticity_module'].mean() * 1e5
        std_val = ep_data['max_vorticity_module'].std() * 1e5
        ax.text(i + 1, mean_val + 0.5, f'{mean_val:.2f}±{std_val:.2f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(EP_NAMES, fontweight='bold')
    ax.set_ylabel('Maximum Vorticity (10$^{-5}$ s$^{-1}$)', fontsize=11, fontweight='bold')
    ax.set_title('(a) Intensity Distribution', fontsize=12, fontweight='bold', loc='left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(bottom=0)

def plot_seasonality_bars(ax, df):
    """Plot seasonal distribution for each EP."""
    # Add month and season columns
    df['month'] = pd.to_datetime(df['time']).dt.month
    df['season'] = df['month'].map(lambda m: next(s for s, months in SEASONS.items() if m in months))
    
    # Prepare data for grouped bar chart
    season_order = ['DJF', 'MAM', 'JJA', 'SON']
    x = np.arange(len(season_order))
    width = 0.25
    
    # Plot bars for each EP
    for i, (ep_num, color) in enumerate(zip([1, 2, 3], EP_COLORS)):
        ep_data = df[df['EP'] == ep_num]
        counts = []
        for season in season_order:
            count = len(ep_data[ep_data['season'] == season])
            counts.append(count)
        
        # Calculate percentages
        total = sum(counts)
        percentages = [c / total * 100 for c in counts]
        
        offset = (i - 1) * width
        bars = ax.bar(x + offset, percentages, width, label=EP_NAMES[i], 
                      color=color, alpha=0.8, edgecolor='black', linewidth=1)
        
        # Add percentage labels on top of bars
        for j, (bar, pct) in enumerate(zip(bars, percentages)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{pct:.1f}%', ha='center', va='bottom', fontsize=8)
    
    ax.set_xticks(x)
    ax.set_xticklabels(season_order, fontweight='bold')
    ax.set_ylabel('Frequency (%)', fontsize=11, fontweight='bold')
    ax.set_title('(b) Seasonal Distribution', fontsize=12, fontweight='bold', loc='left')
    ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max([ax.get_ylim()[1]]) * 1.15)

def plot_interannual_trends(ax, df):
    """Plot interannual variability with Mann-Kendall trends."""
    # Add year column
    df['year'] = pd.to_datetime(df['time']).dt.year
    
    # Calculate annual counts and percentages
    years = sorted(df['year'].unique())
    
    for ep_num, color, label in zip([1, 2, 3], EP_COLORS, EP_NAMES):
        ep_data = df[df['EP'] == ep_num]
        
        # Annual percentage
        annual_pct = []
        for year in years:
            year_total = len(df[df['year'] == year])
            year_ep = len(ep_data[ep_data['year'] == year])
            pct = (year_ep / year_total * 100) if year_total > 0 else 0
            annual_pct.append(pct)
        
        # Plot line
        ax.plot(years, annual_pct, marker='o', markersize=4, linewidth=1.5,
               color=color, label=label, alpha=0.8)
        
        # Mann-Kendall trend analysis
        if HAS_MANNKENDALL and len(annual_pct) > 3:
            try:
                # Perform Mann-Kendall test
                result = mk.original_test(annual_pct)
                p_value = result.p
                tau = result.Tau
                
                # Compute Sen's slope for trend line
                res = theilslopes(annual_pct, years)
                slope = res[0]
                intercept = res[1]
                trend_line = slope * np.array(years) + intercept
                
                # Determine trend direction
                if p_value < 0.05:
                    linestyle = '-'
                    if result.trend == 'increasing':
                        trend_symbol = '↑*'
                    elif result.trend == 'decreasing':
                        trend_symbol = '↓*'
                    else:
                        trend_symbol = '→'
                else:
                    linestyle = '--'
                    if slope > 0:
                        trend_symbol = '↑'
                    elif slope < 0:
                        trend_symbol = '↓'
                    else:
                        trend_symbol = '→'
                
                # Plot trend line
                ax.plot(years, trend_line, linestyle=linestyle, linewidth=2.5,
                       color=color, alpha=0.7)
                
                # Add trend annotation
                mid_year = years[len(years)//2]
                mid_idx = len(years)//2
                mid_value = annual_pct[mid_idx]
                ax.text(mid_year, mid_value, trend_symbol, fontsize=14,
                       color=color, fontweight='bold', ha='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                edgecolor=color, alpha=0.8))
                
                print(f"{label}: trend={result.trend}, p={p_value:.4f}, Tau={tau:.4f}")
            
            except Exception as e:
                print(f"Error computing trend for {label}: {e}")
    
    ax.set_xlabel('Year', fontsize=11, fontweight='bold')
    ax.set_ylabel('Relative Frequency (%)', fontsize=11, fontweight='bold')
    ax.set_title('(c) Interannual Variability and Trends', fontsize=12, fontweight='bold', loc='left')
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True, ncol=3)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add note about trend significance
    ax.text(0.98, 0.02, '* p < 0.05 | Solid: significant, Dashed: non-significant',
           transform=ax.transAxes, ha='right', va='bottom', fontsize=8,
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='gray', alpha=0.8))

# ============================================================================
# Main Figure Creation
# ============================================================================

def create_figure():
    """Create the complete figure."""
    # Load data
    df = load_data()
    
    # Create figure with custom layout
    fig = plt.figure(figsize=(14, 10))
    
    # Create grid: 2 rows, top row has 2 columns, bottom row takes full width
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.3,
                         left=0.08, right=0.95, top=0.95, bottom=0.08)
    
    # Top row: violin plot and seasonality
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Bottom row: interannual trends (full width)
    ax3 = fig.add_subplot(gs[1, :])
    
    # Generate plots
    print("\n" + "="*60)
    print("Generating intensity violin plot...")
    plot_intensity_violin(ax1, df)
    
    print("\n" + "="*60)
    print("Generating seasonality bar chart...")
    plot_seasonality_bars(ax2, df)
    
    print("\n" + "="*60)
    print("Generating interannual trends...")
    plot_interannual_trends(ax3, df)
    
    # Save figure
    output_file = FIGURES_DIR / 'ep_intensity_seasonality_trends.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n{'='*60}")
    print(f"Figure saved: {output_file}")
    print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    plt.close()

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("CREATING FIGURE: Intensity, Seasonality, and Trends")
    print("="*60)
    
    create_figure()
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
