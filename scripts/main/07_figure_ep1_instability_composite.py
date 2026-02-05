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
import warnings

warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "main"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DPI = 300
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}

# Scientific Reports style - optimized for 12-panel figure
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
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
    fig = plt.figure(figsize=(16, 18))
    gs = gridspec.GridSpec(4, 3, hspace=0.35, wspace=0.3,
                          left=0.08, right=0.95, top=0.96, bottom=0.04)
    
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
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Remove tick labels (composite data)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Title with domain size (using derivative notation)
        title = f'{panel_labels[0][col]} ∂η/∂y ({label})'
        ax.set_title(title, fontsize=13, loc='left', fontweight='bold')
        
        # Add sample size
        ax.text(0.98, 0.02, f'n={data["n_cases"]}',
               transform=ax.transAxes, fontsize=10, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Colorbar only in last column
        if col == 2:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="4%", pad=0.08)
            cb = plt.colorbar(im, cax=cax)
            cb.set_label(r'∂η/∂y (s$^{-1}$ m$^{-1}$)', fontsize=11)
            cb.ax.tick_params(labelsize=11)
            cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2e}'))
    
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
            ax.plot(member, data['y'], 'gray', linewidth=0.5, alpha=0.3)
        
        # Plot ensemble mean in bold
        ax.plot(data['deta_dy_zonal_mean'], data['y'], 'b-', linewidth=2.5, label='Ensemble mean')
        
        ax.set_ylim(data['y'].min(), data['y'].max())
        ax.grid(True, alpha=0.3)
        
        # Remove tick labels
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Title with overbar notation
        title = f'{panel_labels[1][col]} $\\overline{{∂η/∂y}}$ ({label})'
        ax.set_title(title, fontsize=13, loc='left', fontweight='bold')
        
        # Add legend only to first panel
        if col == 0:
            ax.legend(fontsize=9, frameon=True, loc='best')
    
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
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Remove tick labels
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Title
        title = f'{panel_labels[2][col]} Potential Vorticity ({label})'
        ax.set_title(title, fontsize=13, loc='left', fontweight='bold')
        
        # Colorbar only in last column
        if col == 2:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="4%", pad=0.08)
            cb = plt.colorbar(im, cax=cax)
            cb.set_label(r'PV (10$^{-6}$ K m$^2$ kg$^{-1}$ s$^{-1}$)', fontsize=11)
            cb.ax.tick_params(labelsize=11)
            cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    
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
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Remove tick labels
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Title
        title = f'{panel_labels[3][col]} Eady Growth Rate ({label})'
        ax.set_title(title, fontsize=13, loc='left', fontweight='bold')
        
        # Mean EGR annotation
        mean_egr = np.nanmean(data['egr_day_mean'])
        ax.text(0.98, 0.02, f'Mean: {mean_egr:.2f} day$^{{-1}}$',
               transform=ax.transAxes, fontsize=10, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Colorbar only in last column
        if col == 2:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="4%", pad=0.08)
            cb = plt.colorbar(im, cax=cax)
            cb.set_label(r'EGR (day$^{-1}$)', fontsize=11)
            cb.ax.tick_params(labelsize=11)
            cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    
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
    
    output_file = FIGURES_DIR / "ep1_instability_composite_4x3.png"
    create_main_figure(data_dict, output_file)
    
    print(f"\n{'='*80}")
    print("✅ Main figure created successfully!")
    print(f"{'='*80}")
    print(f"\nOutput: {output_file}")
    print()


if __name__ == "__main__":
    main()
