#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure: EP1 Instability Analysis - Multi-Scale Composite

This script creates a publication-ready 4×3 composite figure showing
baroclinic and barotropic instability metrics for EP1 cyclones across
three spatial scales: local (5°), mesoscale (15°), and synoptic (30°).

The four diagnostic metrics shown are:
  1. Rayleigh-Kuo (RK) Criterion 2D map (∂η/∂y at Ck=350 hPa)
  2. RK Criterion zonal mean profile  
  3. Baroclinic Potential Vorticity (PV at Ca=975 hPa)
  4. Eady Growth Rate (EGR at Ca=975 hPa)

Layout:
  • 4 rows (one per diagnostic)
  • 3 columns (one per spatial scale)
  • 12 panels total (labeled a-l)

Data source:
  • ERA5 reanalysis fields for selected EP1 cyclones
  • Cyclone-centered composites with fixed grid resolution (0.25°)
  
Critical levels:
  • Ck (conversion rate minimum): 350 hPa
  • Ca (conversion rate maximum): 975 hPa

Methodology:
  • Cyclone-centered extraction with symmetric coordinates
  • Ensemble mean across all EP1 cases
  • RK criterion: symmetric color scale around zero
  • PV: negative values only (Southern Hemisphere cyclones)
  • EGR: data-adaptive color scale with domain mean annotated

Outputs:
  • Figure: figures/main/ep1_instability_composite_4x3.png (300 DPI)

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / 'scripts'))

import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.lines import Line2D
import warnings

warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "main"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DPI = 300
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}

# --------------------------------------------------------------------------
# Font size configuration (centralized)
# --------------------------------------------------------------------------
BASE_FONTSIZE = 11
AXIS_LABELSIZE = 12
PANEL_TITLESIZE = 13
TICK_LABELSIZE = 12
LEGEND_FONTSIZE = 12
CBAR_LABELSIZE = 12
ANNOTATION_FONTSIZE = 12
FIGURE_TITLESIZE = 14

# Apply font sizes to rcParams for consistency
plt.rcParams.update({
    'font.size': BASE_FONTSIZE,
    'axes.labelsize': AXIS_LABELSIZE,
    'axes.titlesize': PANEL_TITLESIZE,
    'xtick.labelsize': TICK_LABELSIZE,
    'ytick.labelsize': TICK_LABELSIZE,
    'legend.fontsize': LEGEND_FONTSIZE,
    'figure.titlesize': FIGURE_TITLESIZE,
    'font.family': 'sans-serif',
    'figure.dpi': 100,
    'savefig.dpi': DPI,
    'savefig.bbox': 'tight',
    'axes.grid': False,
})


# ============================================================================
# Import computation functions from ep1_ibc_ibt_analysis
# ============================================================================

# Add ep1_ibc_ibt_analysis to path
sys.path.insert(0, str(BASE_DIR / 'scripts' / 'ep1_ibc_ibt_analysis'))

from ep1_ibc_ibt_analysis.step4_compute_instabilities import (
    rayleigh_kuo_criterion, 
    eady_growth_rate,
    geopotential_height
)


# ============================================================================
# Computation functions
# ============================================================================

def compute_baroclinic_pv(u, v, T, q, p, z, lat_2d, lon_2d):
    """
    Compute baroclinic potential vorticity using MetPy.
    
    Parameters
    ----------
    u, v : ndarray (3, nlat, nlon)
        Wind components at 3 levels
    T : ndarray (3, nlat, nlon)
        Temperature at 3 levels
    q : ndarray (3, nlat, nlon)
        Specific humidity at 3 levels
    p : ndarray (3,)
        Pressure levels in Pa
    z : ndarray (3, nlat, nlon)
        Geopotential height at 3 levels
    lat_2d, lon_2d : ndarray (nlat, nlon)
        2D latitude/longitude grids
        
    Returns
    -------
    pv : ndarray (nlat, nlon)
        Baroclinic PV at middle level (K m^2 kg^-1 s^-1)
    """
    from metpy.calc import potential_temperature, potential_vorticity_baroclinic
    from metpy.units import units
    import xarray as xr
    
    nlev, nlat, nlon = T.shape
    
    # Create coordinate arrays
    lat_1d = lat_2d[:, 0]
    lon_1d = lon_2d[0, :]
    pressure_hpa = p / 100.0
    
    # Create DataArrays with coordinates
    temperature_da = xr.DataArray(
        T,
        coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units.kelvin
    
    u_da = xr.DataArray(
        u,
        coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units('m/s')
    
    v_da = xr.DataArray(
        v,
        coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units('m/s')
    
    pressure_da = xr.DataArray(
        pressure_hpa,
        coords={'level': pressure_hpa},
        dims=['level']
    ) * units.hPa
    
    # Calculate potential temperature and PV
    theta = potential_temperature(pressure_da, temperature_da)
    pv_baroclinic = potential_vorticity_baroclinic(theta, pressure_da, u_da, v_da)
    
    # Return middle level as plain numpy array
    return pv_baroclinic.isel(level=1).metpy.unit_array.magnitude


def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """
    Extract subdomain centered on cyclone.
    Interpolates to fixed grid to ensure all domains have same dimensions.
    
    Parameters
    ----------
    ds : xarray.Dataset
        ERA5 dataset with variables u, v, t, z, q
    center_lat, center_lon : float
        Cyclone center coordinates
    domain_size : float
        Domain size in degrees
        
    Returns
    -------
    ds_interp : xarray.Dataset
        Interpolated subdomain on regular grid
    """
    half = domain_size / 2.0
    
    # Define target grid with fixed resolution (ERA5 native: 0.25°)
    resolution = 0.25
    n_points = int(domain_size / resolution) + 1
    
    # Create regular grid centered on cyclone
    lat_target = np.linspace(center_lat + half, center_lat - half, n_points)
    lon_target = np.linspace(center_lon - half, center_lon + half, n_points)
    
    # Extract larger region from original data
    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1)
    )
    
    # Interpolate each variable to target grid
    ds_interp = xr.Dataset()
    ds_interp.coords['latitude'] = lat_target
    ds_interp.coords['longitude'] = lon_target
    
    for var in ['u', 'v', 't', 'z', 'q']:
        if var in ds_sub:
            data_interp = ds_sub[var].interp(
                latitude=lat_target,
                longitude=lon_target,
                method='linear'
            )
            ds_interp[var] = data_interp
    
    return ds_interp


def compute_composites_for_domain(cases, domain_size):
    """
    Compute composite fields for a given domain size.
    
    Parameters
    ----------
    cases : pandas.DataFrame
        Selected EP1 cases with track_id, center coordinates
    domain_size : float
        Domain size in degrees
        
    Returns
    -------
    dict
        Dictionary with averaged fields and coordinates
    """
    composite_data = []
    
    print(f"  Processing {len(cases)} cases for domain {domain_size}°...")
    
    for idx, row in cases.iterrows():
        track_id = row['track_id']
        
        # Load data
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        meta_file = DATA_DIR / f"{track_id}_metadata.csv"
        
        if not nc_file.exists() or not meta_file.exists():
            continue
        
        ds = xr.open_dataset(nc_file)
        meta = pd.read_csv(meta_file).iloc[0]
        
        center_lat = meta['track_center_lat']
        center_lon = meta['track_center_lon']
        
        # Central time
        t_idx = len(ds.valid_time) // 2
        ds_t = ds.isel(valid_time=t_idx)
        
        # Extract domain
        ds_sub = extract_subdomain(ds_t, center_lat, center_lon, domain_size)
        
        # Compute diagnostics
        lat_2d, lon_2d = np.meshgrid(
            ds_sub.latitude.values, ds_sub.longitude.values, indexing='ij'
        )
        
        # Critical levels
        lev_rk = 350  # Ck minimum
        u_rk = ds_sub['u'].sel(pressure_level=lev_rk).values
        v_rk = ds_sub['v'].sel(pressure_level=lev_rk).values
        
        lev3_ca = [950, 975, 1000]  # Ca maximum ± 1 level
        u3 = ds_sub['u'].sel(pressure_level=lev3_ca).values
        v3 = ds_sub['v'].sel(pressure_level=lev3_ca).values
        T3 = ds_sub['t'].sel(pressure_level=lev3_ca).values
        q3 = ds_sub['q'].sel(pressure_level=lev3_ca).values
        z3 = geopotential_height(ds_sub['z'].sel(pressure_level=lev3_ca).values)
        p3 = np.array(lev3_ca) * 100.0
        
        # Compute diagnostics
        _, _, deta_dy, deta_dy_zonal, _ = rayleigh_kuo_criterion(u_rk, v_rk, lat_2d, lon_2d)
        _, egr_day, _ = eady_growth_rate(u3, v3, T3, q3, p3, z3, lat_2d)
        
        try:
            pv = compute_baroclinic_pv(u3, v3, T3, q3, p3, z3, lat_2d, lon_2d)
        except Exception:
            pv = np.full_like(lat_2d, np.nan)
        
        composite_data.append({
            'deta_dy': deta_dy,
            'deta_dy_zonal': deta_dy_zonal,
            'egr_day': egr_day,
            'pv': pv,
        })
    
    # Average all fields (use nanmean to handle missing values)
    deta_dy_mean = np.nanmean(np.stack([d['deta_dy'] for d in composite_data]), axis=0)
    egr_day_mean = np.nanmean(np.stack([d['egr_day'] for d in composite_data]), axis=0)
    pv_mean = np.nanmean(np.stack([d['pv'] for d in composite_data]), axis=0)
    deta_dy_zonal_mean = np.nanmean(np.stack([d['deta_dy_zonal'] for d in composite_data]), axis=0)
    
    # Keep individual members for RK zonal mean plot
    deta_dy_zonal_individual = [d['deta_dy_zonal'] for d in composite_data]
    
    # Get grid dimensions
    nlat, nlon = deta_dy_mean.shape
    
    # Create symmetric relative coordinates centered at (0, 0)
    x = np.linspace(-nlon / 2, (nlon / 2) - 1, nlon) * 0.25  # degrees
    y = np.linspace(-nlat / 2, (nlat / 2) - 1, nlat) * 0.25  # degrees
    x_2d, y_2d = np.meshgrid(x, y)
    
    return {
        'deta_dy_mean': deta_dy_mean,
        'deta_dy_zonal_mean': deta_dy_zonal_mean,
        'deta_dy_zonal_individual': deta_dy_zonal_individual,
        'pv_mean': pv_mean,
        'egr_day_mean': egr_day_mean,
        'x': x,
        'y': y,
        'x_2d': x_2d,
        'y_2d': y_2d,
        'n_cases': len(composite_data)
    }


# ============================================================================
# Figure creation
# ============================================================================

def create_main_figure(data_dict, output_file):
    """
    Create main 4×3 composite figure.
    
    Rows: RK 2D, RK Zonal, PV, EGR
    Cols: Local, Mesoscale, Synoptic
    
    Parameters
    ----------
    data_dict : dict
        Dictionary with composite data for each domain
    output_file : Path
        Output file path
    """
    # Compact layout: reserve extra column for colorbars so they don't
    # shrink the main plotting panels when added. Increase figure width.
    fig = plt.figure(figsize=(8, 10))
    gs = gridspec.GridSpec(4, 4, hspace=0.12, wspace=0.06,
                          left=0.05, right=0.98, top=0.98, bottom=0.03,
                          width_ratios=[1, 1, 1, 0.12])
    
    domains = ['local', 'mesoscale', 'synoptic']
    domain_labels = ['5°', '15°', '30°']
    
    # Panel labels
    panel_labels = [
        ['(a)', '(b)', '(c)'],
        ['(d)', '(e)', '(f)'],
        ['(g)', '(h)', '(i)'],
        ['(j)', '(k)', '(l)']
    ]
    
    # ========================================================================
    # Row 1: RK 2D criterion - compute shared colorbar levels
    # ========================================================================
    print("  Creating Row 1: RK 2D...")
    # Find global max for symmetric colorbar
    rk_max_abs = max([np.nanmax(np.abs(data_dict[d]['deta_dy_mean'])) for d in domains])
    levels_rk = np.linspace(-rk_max_abs, rk_max_abs, 21)
    
    for col, (domain, label) in enumerate(zip(domains, domain_labels)):
        ax = fig.add_subplot(gs[0, col])
        data = data_dict[domain]
        
        im = ax.contourf(data['x_2d'], data['y_2d'], data['deta_dy_mean'],
                        levels=levels_rk, cmap='RdBu_r', extend='both')
        ax.contour(data['x_2d'], data['y_2d'], data['deta_dy_mean'],
                  levels=[0], colors='k', linewidths=1.5)
        
        # Mark center
        ax.plot(0, 0, 'k*', markersize=15, markeredgecolor='white', markeredgewidth=1.5)
        
        ax.set_xlim(data['x'].min(), data['x'].max())
        ax.set_ylim(data['y'].min(), data['y'].max())
        # Force the axes box to be square so map panels have consistent display size
        try:
            ax.set_box_aspect(1)
        except Exception:
            ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Remove tick labels (composite data)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Panel label (compact) — remove full title to save space
        ax.text(0.01, 0.98, panel_labels[0][col], transform=ax.transAxes,
            fontsize=ANNOTATION_FONTSIZE+1, fontweight='bold', ha='left', va='top')
        
        # # Add sample size
        # ax.text(0.98, 0.02, f'n={data["n_cases"]}',
        #     transform=ax.transAxes, fontsize=ANNOTATION_FONTSIZE, ha='right', va='bottom',
        #     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Colorbar placed in dedicated cbar column (col index 3)
        if col == 2:
            cax = fig.add_subplot(gs[0, 3])
            cb = plt.colorbar(im, cax=cax)
            cb.set_label(r'∂η/∂y (s$^{-1}$ m$^{-1}$)', fontsize=CBAR_LABELSIZE)
            cb.ax.tick_params(labelsize=CBAR_LABELSIZE)
            cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2e}'))
            cax.yaxis.set_ticks_position('right')
            cax.xaxis.set_visible(False)
    
    # ========================================================================
    # Row 2: RK Zonal Mean
    # ========================================================================
    print("  Creating Row 2: RK Zonal Mean...")
    for col, (domain, label) in enumerate(zip(domains, domain_labels)):
        ax = fig.add_subplot(gs[1, col])
        data = data_dict[domain]
        
        ax.axvline(0, color='k', linestyle='--', linewidth=1, alpha=0.5)
        ax.axhline(0, color='k', linestyle='-', linewidth=1, alpha=0.3)
        
        # Plot all individual cases in gray (like step5)
        for member in data['deta_dy_zonal_individual']:
            ax.plot(member, data['y'], color='gray', linewidth=0.5, alpha=0.3)

        # Plot composite mean in bold (no in-axes legend; placed to the right)
        ax.plot(data['deta_dy_zonal_mean'], data['y'], color='b', linewidth=2.5)
        
        ax.set_ylim(data['y'].min(), data['y'].max())
        ax.grid(True, alpha=0.3)

        # Make zonal-mean panels use the same display box aspect as map panels
        try:
            ax.set_box_aspect(1)
        except Exception:
            pass
        
        # Remove tick labels
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Panel label (compact)
        ax.text(0.01, 0.98, panel_labels[1][col], transform=ax.transAxes,
            fontsize=ANNOTATION_FONTSIZE+1, fontweight='bold', ha='left', va='top')
        
        # Place legend in dedicated right column (gs[1,3]) for the first column
        if col == 0:
            legend_ax = fig.add_subplot(gs[1, 3])
            legend_ax.axis('off')
            handles = [
                Line2D([0], [0], color='gray', linewidth=0.8, alpha=0.9),
                Line2D([0], [0], color='b', linewidth=2.5)
            ]
            labels = ['Individual\ncase', 'Composite\nmean']
            legend = legend_ax.legend(handles, labels, loc='center', frameon=True,
                                      fontsize=LEGEND_FONTSIZE, handlelength=2)
            # Nudge legend further right into the margin/space reserved for colorbars
            try:
                pos = legend_ax.get_position()
                shift = 0.06
                legend_ax.set_position([pos.x0 + shift, pos.y0, pos.width, pos.height])
            except Exception:
                pass
    
    # ========================================================================
    # Row 3: Baroclinic PV - compute shared colorbar levels
    # ========================================================================
    print("  Creating Row 3: Baroclinic PV...")
    # Find global min for shared colorbar (negative values only)
    pv_min = min([np.nanmin(data_dict[d]['pv_mean'] * 1e6) for d in domains])
    pv_levels = np.linspace(pv_min, 0, 21)
    
    for col, (domain, label) in enumerate(zip(domains, domain_labels)):
        ax = fig.add_subplot(gs[2, col])
        data = data_dict[domain]
        
        im = ax.contourf(data['x_2d'], data['y_2d'], data['pv_mean'] * 1e6,
                        levels=pv_levels, cmap='RdYlBu_r', extend='both')
        
        # Mark center
        ax.plot(0, 0, 'k*', markersize=15, markeredgecolor='white', markeredgewidth=1.5)
        
        ax.set_xlim(data['x'].min(), data['x'].max())
        ax.set_ylim(data['y'].min(), data['y'].max())
        try:
            ax.set_box_aspect(1)
        except Exception:
            ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Remove tick labels
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Panel label (compact)
        ax.text(0.01, 0.98, panel_labels[2][col], transform=ax.transAxes,
            fontsize=ANNOTATION_FONTSIZE+1, fontweight='bold', ha='left', va='top')
        
        # Colorbar placed in dedicated cbar column (col index 3)
        if col == 2:
            cax = fig.add_subplot(gs[2, 3])
            cb = plt.colorbar(im, cax=cax)
            cb.set_label(r'PV (10$^{-6}$ K m$^2$ kg$^{-1}$ s$^{-1}$)', fontsize=CBAR_LABELSIZE)
            cb.ax.tick_params(labelsize=CBAR_LABELSIZE)
            cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            cax.yaxis.set_ticks_position('right')
            cax.xaxis.set_visible(False)
    
    # ========================================================================
    # Row 4: Eady Growth Rate - compute shared colorbar levels
    # ========================================================================
    print("  Creating Row 4: Eady Growth Rate...")
    # Find global range for shared colorbar
    egr_min_global = max(0, min([np.nanpercentile(data_dict[d]['egr_day_mean'], 1) for d in domains]))
    egr_max_global = max([np.nanpercentile(data_dict[d]['egr_day_mean'], 99) for d in domains])
    
    if egr_max_global > egr_min_global:
        egr_levels = np.linspace(egr_min_global, egr_max_global, 21)
    else:
        egr_levels = np.linspace(0, 4, 21)
    
    for col, (domain, label) in enumerate(zip(domains, domain_labels)):
        ax = fig.add_subplot(gs[3, col])
        data = data_dict[domain]
        
        im = ax.contourf(data['x_2d'], data['y_2d'], data['egr_day_mean'],
                        levels=egr_levels, cmap='YlOrRd', extend='both')
        
        # Mark center
        ax.plot(0, 0, 'k*', markersize=15, markeredgecolor='white', markeredgewidth=1.5)
        
        ax.set_xlim(data['x'].min(), data['x'].max())
        ax.set_ylim(data['y'].min(), data['y'].max())
        try:
            ax.set_box_aspect(1)
        except Exception:
            ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Remove tick labels
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Panel label (compact)
        ax.text(0.01, 0.98, panel_labels[3][col], transform=ax.transAxes,
            fontsize=ANNOTATION_FONTSIZE+1, fontweight='bold', ha='left', va='top')
        
        # Mean EGR annotation
        mean_egr = np.nanmean(data['egr_day_mean'])
        ax.text(0.98, 0.02, f'Mean: {mean_egr:.2f} day$^{{-1}}$',
            transform=ax.transAxes, fontsize=ANNOTATION_FONTSIZE, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Colorbar placed in dedicated cbar column (col index 3)
        if col == 2:
            cax = fig.add_subplot(gs[3, 3])
            cb = plt.colorbar(im, cax=cax)
            cb.set_label(r'EGR (day$^{-1}$)', fontsize=CBAR_LABELSIZE)
            cb.ax.tick_params(labelsize=CBAR_LABELSIZE)
            cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            cax.yaxis.set_ticks_position('right')
            cax.xaxis.set_visible(False)
    
    # Save figure
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")


# ============================================================================
# Main execution
# ============================================================================

def main():
    """Generate main composite figure for EP1 instability analysis."""
    
    print("=" * 80)
    print("EP1 INSTABILITY COMPOSITE FIGURE (4×3)")
    print("=" * 80)
    
    # Load cases
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print(f"\n❌ Error: {cases_file} not found.")
        print(f"   Run step1-4 in scripts/ep1_ibc_ibt_analysis/ first.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"\nProcessing {len(cases)} EP1 cases")
    print(f"Domains: {list(DOMAIN_SIZES.keys())}\n")
    
    # Compute composites for each domain
    data_dict = {}
    for domain_name, domain_size in DOMAIN_SIZES.items():
        print(f"\n{'='*80}")
        print(f"Computing composites for {domain_name.upper()} domain ({domain_size}°)")
        print(f"{'='*80}")
        
        data_dict[domain_name] = compute_composites_for_domain(cases, domain_size)
    
    # Create main figure
    print(f"\n{'='*80}")
    print("Creating main figure...")
    print(f"{'='*80}")
    
    output_file = FIGURES_DIR / "7_ep1_instability_composite_4x3.png"
    create_main_figure(data_dict, output_file)
    
    print(f"\n{'='*80}")
    print("✅ Main figure created successfully!")
    print(f"{'='*80}")
    print(f"\nOutput: {output_file}")
    print()


if __name__ == "__main__":
    main()
