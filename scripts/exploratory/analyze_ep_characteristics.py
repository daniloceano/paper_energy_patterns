"""Exploratory analysis of Energy Pattern characteristics.

This script analyzes the characteristics of Energy Patterns (EP1, EP2, EP3):
- Seasonality: Monthly and seasonal distribution
- Genesis regions: Spatial distribution of cyclone formation
- Interannual variability: Temporal trends and variations
- Maximum intensity: Relationship with peak vorticity

Follows Scientific Reports figure standards.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.load_data import load_tracks

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files - use absolute paths
RESULTS_DIR = PROJECT_ROOT / "results" / "cluster"
CLUSTERED_DATA_FILE = "kmeans_clustered_data.csv"

# Output settings - use absolute paths
FIGURES_DIR = PROJECT_ROOT / "figures" / "exploratory" / "ep_analysis"
DPI = 300

# Energy Pattern mapping (cluster_id → EP_id)
CLUSTER_TO_EP = {
    0: 1,  # Cluster 0 → EP1 (lowest Ck)
    2: 2,  # Cluster 2 → EP2 (middle Ck)
    1: 3   # Cluster 1 → EP3 (highest Ck)
}

# EP names and colors (Scientific Reports style)
EP_NAMES = {
    1: 'EP1',
    2: 'EP2',
    3: 'EP3'
}

EP_COLORS = {
    1: '#1f77b4',  # Blue
    2: '#ff7f0e',  # Orange
    3: '#2ca02c'   # Green
}

# Region colors
REGION_COLORS = {
    'SE-BR': '#2ca02c',    # Green
    'LA-PLAT': '#ffff00',  # Yellow
    'ARG': '#1f77b4'       # Blue
}

# Seasons
SEASONS = {
    'DJF': [12, 1, 2],   # Summer
    'MAM': [3, 4, 5],    # Autumn
    'JJA': [6, 7, 8],    # Winter
    'SON': [9, 10, 11]   # Spring
}

SEASON_NAMES = {
    'DJF': 'Summer',
    'MAM': 'Autumn', 
    'JJA': 'Winter',
    'SON': 'Spring'
}

# ============================================================================


def load_data() -> pd.DataFrame:
    """Load tracks and merge with cluster assignments.
    
    Returns:
        DataFrame with track info and energy pattern assignments
    """
    print("Loading data...")
    
    # Load cluster assignments
    results_dir = Path(RESULTS_DIR)
    clustered_file = results_dir / CLUSTERED_DATA_FILE
    df_clustered = pd.read_csv(clustered_file, index_col=0)
    
    # Assign Energy Patterns
    # Assign Energy Patterns
    df_clustered['energy_pattern'] = df_clustered['cluster'].map(CLUSTER_TO_EP)
    print(f"  ✓ Cluster assignments: {len(df_clustered)} cyclones")
    
    # Load tracks using utility function
    print(f"  ⏳ Loading tracks...")
    df_tracks = load_tracks()
    df_tracks['date'] = pd.to_datetime(df_tracks['date'])
    print(f"  ✓ Tracks: {len(df_tracks)} observations")
    # Get first observation per cyclone (genesis)
    df_genesis = df_tracks.groupby('track_id').first().reset_index()
    print(f"  ✓ Genesis data: {len(df_genesis)} cyclones")
    
    # Get maximum vorticity per cyclone
    df_max_vor = df_tracks.groupby('track_id')['vor42'].max().reset_index()
    df_max_vor.columns = ['track_id', 'max_vor42']
    
    # Merge all data
    df_merged = df_genesis.merge(
        df_clustered[['energy_pattern', 'cluster']],
        left_on='track_id',
        right_index=True,
        how='inner'
    )
    
    df_merged = df_merged.merge(df_max_vor, on='track_id', how='left')
    
    # Extract temporal features
    df_merged['year'] = df_merged['date'].dt.year
    df_merged['month'] = df_merged['date'].dt.month
    df_merged['season'] = df_merged['month'].apply(get_season)
    
    print(f"  ✓ Merged data: {len(df_merged)} cyclones with EP assignments")
    print()
    
    return df_merged


def get_season(month: int) -> str:
    """Get season from month number.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Season code (DJF, MAM, JJA, SON)
    """
    for season, months in SEASONS.items():
        if month in months:
            return season
    return 'Unknown'


def plot_seasonality(df: pd.DataFrame, output_dir: Path):
    """Plot seasonal and monthly distribution of Energy Patterns.
    
    Creates a figure with:
    - Monthly distribution (bar plot)
    - Seasonal distribution (pie charts per EP)
    """
    print("\nAnalyzing seasonality...")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 6))
    gs = fig.add_gridspec(2, 4, hspace=0.35, wspace=0.3)
    
    # Monthly distribution (top, spanning all columns)
    ax_monthly = fig.add_subplot(gs[0, :])
    
    # Count by month and EP
    monthly_counts = df.groupby(['month', 'energy_pattern']).size().unstack(fill_value=0)
    
    # Reorder columns
    monthly_counts = monthly_counts[[1, 2, 3]]
    
    # Plot stacked bar chart
    x_pos = np.arange(1, 13)
    bottom = np.zeros(12)
    
    for ep_id in [1, 2, 3]:
        if ep_id in monthly_counts.columns:
            counts = monthly_counts[ep_id].reindex(range(1, 13), fill_value=0).values
            ax_monthly.bar(x_pos, counts, bottom=bottom, 
                          color=EP_COLORS[ep_id], label=EP_NAMES[ep_id],
                          edgecolor='white', linewidth=0.5)
            bottom += counts
    
    ax_monthly.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax_monthly.set_ylabel('Number of Cyclones', fontsize=12, fontweight='bold')
    ax_monthly.set_title('Monthly Distribution of Energy Patterns', 
                         fontsize=13, fontweight='bold', pad=10)
    ax_monthly.set_xticks(x_pos)
    ax_monthly.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    ax_monthly.legend(loc='upper right', framealpha=0.9)
    ax_monthly.grid(True, axis='y', alpha=0.3)
    ax_monthly.set_axisbelow(True)
    
    # Seasonal distribution (bottom row - one pie per EP)
    for idx, ep_id in enumerate([1, 2, 3]):
        ax_pie = fig.add_subplot(gs[1, idx])
        
        df_ep = df[df['energy_pattern'] == ep_id]
        season_counts = df_ep['season'].value_counts()
        
        # Reorder seasons
        season_order = ['DJF', 'MAM', 'JJA', 'SON']
        season_counts = season_counts.reindex(season_order, fill_value=0)
        
        # Colors for seasons
        season_colors = ['#d62728', '#ff7f0e', '#1f77b4', '#2ca02c']  # Red, Orange, Blue, Green
        
        # Plot pie chart
        wedges, texts, autotexts = ax_pie.pie(
            season_counts.values,
            labels=[SEASON_NAMES[s] for s in season_order],
            colors=season_colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )
        
        # Make percentage text white for better contrast
        for autotext in autotexts:
            autotext.set_color('white')
        
        ax_pie.set_title(f'{EP_NAMES[ep_id]}\n(n = {len(df_ep)})',
                        fontsize=11, fontweight='bold', pad=10)
    
    # Add empty subplot for overall stats
    ax_stats = fig.add_subplot(gs[1, 3])
    ax_stats.axis('off')
    
    # Calculate overall seasonal distribution
    season_counts_all = df['season'].value_counts()
    season_counts_all = season_counts_all.reindex(['DJF', 'MAM', 'JJA', 'SON'], fill_value=0)
    
    stats_text = "Overall Distribution:\n\n"
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        count = season_counts_all[season]
        pct = 100 * count / len(df)
        stats_text += f"{SEASON_NAMES[season]:10s}: {count:4d} ({pct:4.1f}%)\n"
    
    stats_text += f"\nTotal: {len(df)} cyclones"
    
    ax_stats.text(0.1, 0.5, stats_text, fontsize=10, family='monospace',
                 verticalalignment='center',
                 bbox=dict(boxstyle='round,pad=0.8', facecolor='lightgray', alpha=0.3))
    
    # Save figure
    output_file = output_dir / 'seasonality.png'
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")


def compute_kde_hodges(tracks_df: pd.DataFrame, num_time: float) -> tuple:
    """Compute KDE following Hoskins and Hodges (2005) methodology.
    
    Parameters
    ----------
    tracks_df : pd.DataFrame
        DataFrame with 'lat vor' and 'lon vor' columns
    num_time : float
        Number of time units (years) for normalization
        
    Returns
    -------
    density : np.ndarray
        2D array with density values (cyclones per 10^6 km^2 per year)
    longrd : np.ndarray
        Longitude grid
    latgrd : np.ndarray
        Latitude grid
    """
    from sklearn.neighbors import KernelDensity
    
    # (1) Create global grid: 128 x 64 (lon, lat): 2.5 degree
    k = 64
    longrd = np.linspace(-180, 180, 2 * k)
    latgrd = np.linspace(-87.863, 87.863, k)
    tx, ty = np.meshgrid(longrd, latgrd)
    mesh = np.vstack((ty.ravel(), tx.ravel())).T
    mesh *= np.pi / 180.  # Convert to radians

    # (2) Extract positions
    pos = tracks_df[['lat vor', 'lon vor']].copy()
    x = pos['lon vor'].values
    y = pos['lat vor'].values

    # (3) Build KDE for positions
    h = np.vstack([y, x]).T
    h *= np.pi / 180.  # Convert lat/long to radians
    bdw = 0.05  # Bandwidth in radians (~555 km)
    kde = KernelDensity(bandwidth=bdw, metric='haversine',
        kernel='gaussian', algorithm='ball_tree').fit(h)

    # (4) Evaluate kde on grid
    v = np.exp(kde.score_samples(mesh)).reshape((k, 2 * k))

    # (5) Convert to scaled density
    # Units: cyclones per 10^6 km^2 per year
    R = 6369345.0 * 1e-3  # Earth radius in km at 40ºS
    factor = (1 / (R * R)) * 1.e6
    density = v * pos.shape[0] * factor / num_time

    return density, longrd, latgrd


def plot_genesis_regions(df: pd.DataFrame, output_dir: Path):
    """Plot genesis locations for each Energy Pattern using KDE.
    
    Creates maps showing cyclone genesis density and regional distribution.
    Uses Hoskins and Hodges (2005) KDE methodology.
    """
    print("\nAnalyzing genesis regions...")
    
    # Create figure with map projection and pie charts
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Main map (all EPs) - top row, spanning 2 columns
    ax_main = fig.add_subplot(gs[0, :2], projection=ccrs.PlateCarree())
    
    # Individual EP maps - middle row
    axes_ep = []
    for i in range(3):
        ax = fig.add_subplot(gs[1, i], projection=ccrs.PlateCarree())
        axes_ep.append(ax)
    
    # Set map extent (South Atlantic region)
    extent = [-80, -20, -60, -20]
    
    for ax in [ax_main] + axes_ep:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        ax.coastlines(resolution='50m', linewidth=0.8)
        ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.2)
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False,
                    linewidth=0.5, alpha=0.5)
    
    # Calculate time span for density normalization
    num_years = df['year'].max() - df['year'].min() + 1
    
    # Compute KDE using Hodges method for all EPs
    density_all, longrd, latgrd = compute_kde_hodges(df, num_years)
    
    # Mask to South Atlantic region
    lon_mask = (longrd >= -80) & (longrd <= -20)
    lat_mask = (latgrd >= -60) & (latgrd <= -20)
    lon_idx = np.where(lon_mask)[0]
    lat_idx = np.where(lat_mask)[0]
    
    # Plot contours for each EP on main map
    for ep_id in [1, 2, 3]:
        ep_data = df[df['energy_pattern'] == ep_id]
        
        if len(ep_data) < 3:
            continue
        
        # Compute KDE for this EP
        density_ep, _, _ = compute_kde_hodges(ep_data, num_years)
        
        # Extract region
        density_region = density_ep[np.ix_(lat_idx, lon_idx)]
        lon_region = longrd[lon_idx]
        lat_region = latgrd[lat_idx]
        
        # Plot contours
        levels = np.percentile(density_region[density_region > 0], [50, 75, 90, 95])
        ax_main.contour(lon_region, lat_region, density_region, levels=levels,
                       colors=[EP_COLORS[ep_id]], linewidths=2,
                       transform=ccrs.PlateCarree(), alpha=0.8)
        ax_main.contourf(lon_region, lat_region, density_region, levels=[levels[0], levels[-1]],
                        colors=[EP_COLORS[ep_id]], alpha=0.15,
                        transform=ccrs.PlateCarree())
    
    # Add legend manually
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], color=EP_COLORS[ep_id], lw=2, 
                             label=EP_NAMES[ep_id]) for ep_id in [1, 2, 3]]
    ax_main.legend(handles=legend_elements, loc='lower left', 
                  framealpha=0.9, fontsize=10)
    
    ax_main.set_title('Genesis Density - All Energy Patterns',
                     fontsize=13, fontweight='bold', pad=10)
    
    # Plot individual EPs with Hodges KDE
    for idx, ep_id in enumerate([1, 2, 3]):
        ep_data = df[df['energy_pattern'] == ep_id]
        ax = axes_ep[idx]
        
        if len(ep_data) < 3:
            ax.text(0.5, 0.5, 'Insufficient data', 
                   transform=ax.transAxes, ha='center', va='center')
            continue
        
        # Compute KDE using Hodges method
        density_ep, _, _ = compute_kde_hodges(ep_data, num_years)
        
        # Extract region
        density_region = density_ep[np.ix_(lat_idx, lon_idx)]
        lon_region = longrd[lon_idx]
        lat_region = latgrd[lat_idx]
        
        # Plot filled contours
        cf = ax.contourf(lon_region, lat_region, density_region, levels=12,
                   cmap='YlOrRd', transform=ccrs.PlateCarree(), alpha=0.8)
        plt.colorbar(cf, ax=ax, label='Density (cyc/10⁶km²/yr)', 
                    shrink=0.8)
        
        # Plot contour lines
        cs = ax.contour(lon_region, lat_region, density_region, levels=6,
                       colors='black', linewidths=0.5,
                       transform=ccrs.PlateCarree(), alpha=0.6)
        
        ax.set_title(f'{EP_NAMES[ep_id]} (n={len(ep_data)}, max={density_region.max():.1f})',
                    fontsize=11, fontweight='bold', pad=5)
    
    # Add pie charts - top right: EP by region
    ax_pie1 = fig.add_subplot(gs[0, 2])
    ax_pie1.axis('off')
    
    # Count EP by region
    ep_by_region = df.groupby(['region', 'energy_pattern']).size().unstack(fill_value=0)
    
    # Plot stacked data showing regions composition for each EP
    ax_pie1.text(0.5, 0.95, 'Region Distribution by Energy Pattern',
                ha='center', va='top', fontsize=11, fontweight='bold',
                transform=ax_pie1.transAxes)
    
    y_pos = 0.75
    for ep_id in [1, 2, 3]:
        if ep_id in ep_by_region.columns:
            region_counts = ep_by_region[ep_id]
            total = region_counts.sum()
            
            ax_pie1.text(0.1, y_pos, f'{EP_NAMES[ep_id]}:',
                        ha='left', va='center', fontsize=10, fontweight='bold',
                        transform=ax_pie1.transAxes)
            
            for region in region_counts.index:
                count = region_counts[region]
                pct = 100 * count / total if total > 0 else 0
                color = REGION_COLORS.get(region, 'gray')
                
                ax_pie1.text(0.3, y_pos, f'{region}: {count} ({pct:.1f}%)',
                            ha='left', va='center', fontsize=9,
                            color=color, fontweight='bold',
                            transform=ax_pie1.transAxes)
                y_pos -= 0.06
            y_pos -= 0.04
    
    # Pie charts - bottom row: EP proportion per region (3 pies)
    region_list = ['SE-BR', 'LA-PLAT', 'ARG'] if 'SE-BR' in df['region'].unique() else df['region'].unique()[:3]
    
    for idx, region in enumerate(region_list):
        if region in df['region'].values:
            ax_pie = fig.add_subplot(gs[2, idx])
            
            df_region = df[df['region'] == region]
            ep_counts = df_region['energy_pattern'].value_counts()
            ep_counts = ep_counts.reindex([1, 2, 3], fill_value=0)
            
            if ep_counts.sum() > 0:
                colors = [EP_COLORS[ep_id] for ep_id in [1, 2, 3]]
                
                wedges, texts, autotexts = ax_pie.pie(
                    ep_counts.values,
                    labels=[EP_NAMES[ep_id] for ep_id in [1, 2, 3]],
                    colors=colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    textprops={'fontsize': 9, 'fontweight': 'bold'}
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                
                region_color = REGION_COLORS.get(region, 'gray')
                ax_pie.set_title(f'{region}\n(n = {len(df_region)})',
                               fontsize=11, fontweight='bold', pad=10,
                               color=region_color)
    
    # Save figure
    output_file = output_dir / 'genesis_regions.png'
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")


def plot_interannual_variability(df: pd.DataFrame, output_dir: Path):
    """Plot interannual variability of Energy Patterns with trend analysis.
    
    Creates time series showing:
    - Annual counts per EP
    - Relative frequency per EP with Mann-Kendall trend analysis
    """
    print("\nAnalyzing interannual variability...")
    
    # Import for Mann-Kendall test
    try:
        import pymannkendall as mk
    except ImportError:
        print("  ⚠️  pymannkendall not available, trends will not be computed")
        mk = None
    
    # Create figure
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # Annual counts
    ax_counts = axes[0]
    
    # Count by year and EP
    yearly_counts = df.groupby(['year', 'energy_pattern']).size().unstack(fill_value=0)
    yearly_counts = yearly_counts[[1, 2, 3]]  # Reorder
    
    # Plot stacked area chart
    years = yearly_counts.index
    ax_counts.fill_between(years, 0, yearly_counts[1], 
                          color=EP_COLORS[1], alpha=0.7, label=EP_NAMES[1])
    ax_counts.fill_between(years, yearly_counts[1], 
                          yearly_counts[1] + yearly_counts[2],
                          color=EP_COLORS[2], alpha=0.7, label=EP_NAMES[2])
    ax_counts.fill_between(years, yearly_counts[1] + yearly_counts[2],
                          yearly_counts[1] + yearly_counts[2] + yearly_counts[3],
                          color=EP_COLORS[3], alpha=0.7, label=EP_NAMES[3])
    
    ax_counts.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax_counts.set_ylabel('Number of Cyclones', fontsize=12, fontweight='bold')
    ax_counts.set_title('Interannual Variability - Absolute Counts',
                       fontsize=13, fontweight='bold', pad=10)
    ax_counts.legend(loc='upper left', framealpha=0.9)
    ax_counts.grid(True, axis='y', alpha=0.3)
    ax_counts.set_axisbelow(True)
    
    # Relative frequency with trend analysis
    ax_freq = axes[1]
    
    # Calculate percentages
    yearly_total = yearly_counts.sum(axis=1)
    yearly_pct = yearly_counts.div(yearly_total, axis=0) * 100
    
    # Plot lines and trends
    for ep_id in [1, 2, 3]:
        # Plot original data
        ax_freq.plot(years, yearly_pct[ep_id], 
                    color=EP_COLORS[ep_id], linewidth=2.5,
                    marker='o', markersize=4, label=EP_NAMES[ep_id],
                    alpha=0.8)
        
        # Compute and plot trend using Mann-Kendall
        if mk is not None and len(yearly_pct[ep_id]) > 3:
            try:
                # Mann-Kendall test
                mk_result = mk.original_test(yearly_pct[ep_id].values)
                
                # Compute Sen's slope for trend line
                from scipy import stats
                x_numeric = np.arange(len(years))
                slope, intercept = stats.theilslopes(yearly_pct[ep_id].values, x_numeric)[:2]
                trend_line = slope * x_numeric + intercept
                
                # Plot trend line
                linestyle = '-' if mk_result.p < 0.05 else '--'
                ax_freq.plot(years, trend_line,
                           color=EP_COLORS[ep_id], linewidth=2,
                           linestyle=linestyle, alpha=0.5)
                
                # Add trend annotation
                trend_direction = '↑' if mk_result.trend == 'increasing' else '↓' if mk_result.trend == 'decreasing' else '→'
                sig_marker = '*' if mk_result.p < 0.05 else ''
                trend_text = f'{EP_NAMES[ep_id]}: {trend_direction}{sig_marker}'
                
                # Position annotations
                y_pos = 0.95 - (ep_id - 1) * 0.05
                ax_freq.text(0.02, y_pos, trend_text,
                           transform=ax_freq.transAxes,
                           fontsize=9, color=EP_COLORS[ep_id],
                           fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor='white', alpha=0.7))
                
            except Exception as e:
                print(f"  ⚠️  Could not compute trend for {EP_NAMES[ep_id]}: {e}")
    
    ax_freq.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax_freq.set_ylabel('Relative Frequency (%)', fontsize=12, fontweight='bold')
    
    # Add note about trend lines
    title_text = 'Interannual Variability - Relative Frequency'
    if mk is not None:
        title_text += '\n(Solid lines: significant trend p<0.05; Dashed: non-significant)'
    ax_freq.set_title(title_text, fontsize=13, fontweight='bold', pad=10)
    
    ax_freq.legend(loc='best', framealpha=0.9)
    ax_freq.grid(True, alpha=0.3)
    ax_freq.set_axisbelow(True)
    ax_freq.set_ylim(0, 100)
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / 'interannual_variability.png'
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")
    
    # Print trend statistics
    if mk is not None:
        print("\n  Trend analysis (Mann-Kendall test):")
        for ep_id in [1, 2, 3]:
            if len(yearly_pct[ep_id]) > 3:
                try:
                    mk_result = mk.original_test(yearly_pct[ep_id].values)
                    print(f"    {EP_NAMES[ep_id]}:")
                    print(f"      Trend: {mk_result.trend}")
                    print(f"      p-value: {mk_result.p:.4f}")
                    print(f"      Tau: {mk_result.Tau:.4f}")
                except:
                    pass


def plot_intensity_relationship(df: pd.DataFrame, output_dir: Path):
    """Plot relationship between EP and maximum vorticity.
    
    Creates:
    - Box plots showing vorticity distribution per EP
    - Violin plots for detailed distribution
    - Statistical comparison
    """
    print("\nAnalyzing intensity relationship...")
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Prepare data
    data_list = []
    for ep_id in [1, 2, 3]:
        df_ep = df[df['energy_pattern'] == ep_id]
        data_list.append(df_ep['max_vor42'].dropna())
    
    # Box plot
    ax_box = axes[0]
    
    bp = ax_box.boxplot(data_list, labels=[EP_NAMES[ep_id] for ep_id in [1, 2, 3]],
                        patch_artist=True, widths=0.6,
                        boxprops=dict(linewidth=1.5),
                        whiskerprops=dict(linewidth=1.5),
                        capprops=dict(linewidth=1.5),
                        medianprops=dict(linewidth=2, color='darkred'))
    
    # Color boxes
    for patch, ep_id in zip(bp['boxes'], [1, 2, 3]):
        patch.set_facecolor(EP_COLORS[ep_id])
        patch.set_alpha(0.7)
    
    ax_box.set_ylabel('Maximum Vorticity (10⁻⁵ s⁻¹)', fontsize=12, fontweight='bold')
    ax_box.set_title('Maximum Intensity by Energy Pattern',
                    fontsize=13, fontweight='bold', pad=10)
    ax_box.grid(True, axis='y', alpha=0.3)
    ax_box.set_axisbelow(True)
    ax_box.tick_params(axis='x', rotation=15)
    
    # Add sample sizes
    for i, ep_id in enumerate([1, 2, 3]):
        n = len(data_list[i])
        mean_val = data_list[i].mean()
        ax_box.text(i + 1, ax_box.get_ylim()[1] * 0.95, f'n = {n}\nμ = {mean_val:.2f}',
                   ha='center', va='top', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Violin plot
    ax_violin = axes[1]
    
    # Prepare data for seaborn
    df_plot = df[['energy_pattern', 'max_vor42']].dropna()
    df_plot['EP'] = df_plot['energy_pattern'].map(EP_NAMES)
    
    parts = ax_violin.violinplot(data_list, positions=[1, 2, 3],
                                 widths=0.7, showmeans=True, showmedians=True)
    
    # Color violin plots
    for i, (pc, ep_id) in enumerate(zip(parts['bodies'], [1, 2, 3])):
        pc.set_facecolor(EP_COLORS[ep_id])
        pc.set_alpha(0.7)
    
    ax_violin.set_xticks([1, 2, 3])
    ax_violin.set_xticklabels([EP_NAMES[ep_id] for ep_id in [1, 2, 3]])
    ax_violin.set_ylabel('Maximum Vorticity (10⁻⁵ s⁻¹)', fontsize=12, fontweight='bold')
    ax_violin.set_title('Intensity Distribution by Energy Pattern',
                       fontsize=13, fontweight='bold', pad=10)
    ax_violin.grid(True, axis='y', alpha=0.3)
    ax_violin.set_axisbelow(True)
    ax_violin.tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / 'intensity_relationship.png'
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")
    
    # Print statistics
    print("\n  Intensity statistics:")
    for ep_id in [1, 2, 3]:
        df_ep = df[df['energy_pattern'] == ep_id]
        vor_stats = df_ep['max_vor42'].describe()
        print(f"    {EP_NAMES[ep_id]}:")
        print(f"      Mean: {vor_stats['mean']:.2f} ± {vor_stats['std']:.2f}")
        print(f"      Median: {vor_stats['50%']:.2f}")
        print(f"      Range: [{vor_stats['min']:.2f}, {vor_stats['max']:.2f}]")


def create_summary_statistics(df: pd.DataFrame, output_dir: Path):
    """Create summary statistics table.
    
    Creates a comprehensive summary of EP characteristics.
    """
    print("\nGenerating summary statistics...")
    
    summary_data = []
    
    for ep_id in [1, 2, 3]:
        df_ep = df[df['energy_pattern'] == ep_id]
        
        # Calculate statistics
        n_cyclones = len(df_ep)
        pct_total = 100 * n_cyclones / len(df)
        
        # Seasonal distribution
        season_mode = df_ep['season'].mode()[0] if len(df_ep) > 0 else 'N/A'
        season_pct = 100 * (df_ep['season'] == season_mode).sum() / n_cyclones if n_cyclones > 0 else 0
        
        # Intensity
        mean_vor = df_ep['max_vor42'].mean()
        std_vor = df_ep['max_vor42'].std()
        
        # Genesis location (median)
        median_lon = df_ep['lon vor'].median()
        median_lat = df_ep['lat vor'].median()
        
        # Interannual variability (std of annual counts)
        yearly_counts = df_ep.groupby('year').size()
        interannual_std = yearly_counts.std()
        
        summary_data.append({
            'Energy Pattern': EP_NAMES[ep_id],
            'N Cyclones': n_cyclones,
            '% of Total': f'{pct_total:.1f}%',
            'Dominant Season': f'{SEASON_NAMES[season_mode]} ({season_pct:.1f}%)',
            'Mean Max Vorticity': f'{mean_vor:.2f} ± {std_vor:.2f}',
            'Median Genesis (lon, lat)': f'({median_lon:.1f}°, {median_lat:.1f}°)',
            'Interannual Std': f'{interannual_std:.1f}'
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # Save to CSV
    output_file = output_dir / 'summary_statistics.csv'
    df_summary.to_csv(output_file, index=False)
    print(f"  ✓ Saved: {output_file.name}")
    
    # Print table
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(df_summary.to_string(index=False))
    print("=" * 80)


def main():
    """Main execution function."""
    
    output_dir = Path(FIGURES_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Exploratory Analysis: Energy Pattern Characteristics")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print()
    
    # Load data
    df = load_data()
    
    # Display distribution
    print("Energy Pattern distribution:")
    for ep_id in sorted(df['energy_pattern'].unique()):
        count = (df['energy_pattern'] == ep_id).sum()
        pct = 100 * count / len(df)
        print(f"  {EP_NAMES[ep_id]:30s}: {count:4d} cyclones ({pct:5.1f}%)")
    print()
    
    # Generate analyses
    plot_seasonality(df, output_dir)
    plot_genesis_regions(df, output_dir)
    plot_interannual_variability(df, output_dir)
    plot_intensity_relationship(df, output_dir)
    create_summary_statistics(df, output_dir)
    
    print()
    print("=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  • {output_dir}/seasonality.png")
    print(f"  • {output_dir}/genesis_regions.png")
    print(f"  • {output_dir}/interannual_variability.png")
    print(f"  • {output_dir}/intensity_relationship.png")
    print(f"  • {output_dir}/summary_statistics.csv")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
