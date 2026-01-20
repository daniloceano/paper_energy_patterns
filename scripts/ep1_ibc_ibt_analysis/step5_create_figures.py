"""
Step 5: Create Publication-Quality Figures

This script generates composite figures for EP1 instability analysis.

For each domain (5°, 15°, 30°):
1. 2D map of ∂η/∂y (RK criterion) at Ck level  
2. Zonal mean profile of ∂η/∂y
3. Potential vorticity (baroclinic PV from MetPy) at Ca level
4. Eady Growth Rate map with domain-mean annotated

Author: Danilo Couto de Souza
Date: January 2026
"""

# ============================================================================
# CONFIGURATION OPTIONS
# ============================================================================
PLOT_INDIVIDUAL = False  # Set to False for faster debugging of composites only
# ============================================================================

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings

warnings.filterwarnings('ignore')

# Import step4 functions for recomputation
from step4_compute_instabilities import (
    rayleigh_kuo_criterion, eady_growth_rate,
    geopotential_height
)


def compute_baroclinic_pv(u, v, T, q, p, z, lat_2d, lon_2d):
    """
    Compute baroclinic potential vorticity using MetPy.
    
    Following MetPy's approach with xarray DataArrays for proper coordinate handling.
    """
    from metpy.calc import potential_temperature, potential_vorticity_baroclinic
    from metpy.units import units
    import xarray as xr
    
    # Create xarray DataArrays with proper coordinates
    nlev, nlat, nlon = T.shape
    
    # Create coordinate arrays
    lat_1d = lat_2d[:, 0]
    lon_1d = lon_2d[0, :]
    
    # Convert pressure from Pa to hPa for consistency
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
    
    # Pressure as DataArray (1D)
    pressure_da = xr.DataArray(
        pressure_hpa,
        coords={'level': pressure_hpa},
        dims=['level']
    ) * units.hPa
    
    # Calculate potential temperature
    theta = potential_temperature(pressure_da, temperature_da)
    
    # Calculate baroclinic PV
    pv_baroclinic = potential_vorticity_baroclinic(theta, pressure_da, u_da, v_da)
    
    # Return middle level as plain numpy array (MetPy returns all 3 levels)
    return pv_baroclinic.isel(level=1).metpy.unit_array.magnitude

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "ep1_vertical"

# Create subdirectories  
(FIGURES_DIR / "composite").mkdir(parents=True, exist_ok=True)

DPI = 300
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}

# Scientific Reports style
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 12,
    'figure.dpi': 100,
    'savefig.dpi': DPI,
    'savefig.bbox': 'tight',
    'axes.grid': False,
})


def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """
    Extract subdomain centered on cyclone.
    Interpolates to fixed grid to ensure all domains have same dimensions.
    
    Grid resolution: 0.25° (ERA5 native resolution)
    Ensures consistent grid size across all cyclones.
    """
    half = domain_size / 2.0
    
    # Define target grid with fixed resolution
    resolution = 0.25  # ERA5 resolution
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


def create_composite_figure(domain_name, domain_size, all_data, output_dir):
    """
    Create composite 4-panel figure (ensemble mean across all cyclones).
    
    Following the methodology from the provided example:
    1. All domains have standardized grid sizes
    2. Simply average all fields directly
    3. Use symmetric relative coordinates centered at (0, 0)
    """
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 2, hspace=0.25, wspace=0.3)
    
    print(f"    Averaging {len(all_data)} cases...")
    
    # Stack and average all fields (all have same shape!)
    # Use nanmean to ignore NaN values from individual cases
    deta_dy_mean = np.nanmean(np.stack([d['deta_dy'] for d in all_data]), axis=0)
    egr_day_mean = np.nanmean(np.stack([d['egr_day'] for d in all_data]), axis=0)
    pv_mean = np.nanmean(np.stack([d['pv'] for d in all_data]), axis=0)
    deta_dy_zonal_mean = np.nanmean(np.stack([d['deta_dy_zonal'] for d in all_data]), axis=0)
    
    # Get grid dimensions from first case (all identical)
    nlat, nlon = deta_dy_mean.shape
    
    # Create symmetric relative coordinates centered at (0, 0)
    # Following example: x = linspace(-x_size/2, (x_size/2)-1, x_size)
    x = np.linspace(-nlon / 2, (nlon / 2) - 1, nlon) * 0.25  # degrees (resolution = 0.25°)
    y = np.linspace(-nlat / 2, (nlat / 2) - 1, nlat) * 0.25  # degrees
    
    # Create 2D meshgrid for contour plots
    x_2d, y_2d = np.meshgrid(x, y)
    
    lev_rk = all_data[0]['lev_rk']
    lev_ca = all_data[0]['lev_ca']
    
    # =========================================================================
    # Panel 1: Composite ∂η/∂y
    # =========================================================================
    ax1 = fig.add_subplot(gs[0, 0])
    
    levels_rk = np.linspace(-2e-8, 2e-8, 21)
    im1 = ax1.contourf(x_2d, y_2d, deta_dy_mean, levels=levels_rk,
                       cmap='RdBu_r', extend='both')
    ax1.contour(x_2d, y_2d, deta_dy_mean, levels=[0], colors='k', linewidths=1.5)
    
    # Mark center
    ax1.plot(0, 0, 'k*', markersize=15, markeredgecolor='white', markeredgewidth=1)
    
    ax1.set_xlabel('Relative Longitude (°)', fontsize=10)
    ax1.set_ylabel('Relative Latitude (°)', fontsize=10)
    ax1.set_xlim(x.min(), x.max())
    ax1.set_ylim(y.min(), y.max())
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    divider1 = make_axes_locatable(ax1)
    cax1 = divider1.append_axes("right", size="5%", pad=0.1)
    cb1 = plt.colorbar(im1, cax=cax1)
    cb1.set_label(r'$\partial\eta/\partial y$ (s$^{-1}$ m$^{-1}$)', fontsize=9)
    
    ax1.set_title(f'(a) RK Criterion 2D - Composite (Ck: {lev_rk} hPa)', 
                  fontsize=10, loc='left')
    
    # =========================================================================
    # Panel 2: Composite zonal mean ∂η/∂y
    # =========================================================================
    ax2 = fig.add_subplot(gs[0, 1])
    
    ax2.axvline(0, color='k', linestyle='--', linewidth=1, alpha=0.5)
    ax2.axhline(0, color='k', linestyle='-', linewidth=1, alpha=0.3, label='Center')
    
    # Plot all individual cases in gray
    for d in all_data:
        y_case = np.linspace(-nlat / 2, (nlat / 2) - 1, nlat) * 0.25
        ax2.plot(d['deta_dy_zonal'], y_case, 'gray', linewidth=0.5, alpha=0.3)
    
    # Plot ensemble mean
    ax2.plot(deta_dy_zonal_mean, y, 'b-', linewidth=2.5, label='Ensemble mean')
    
    ax2.set_xlabel(r'$\overline{\partial\eta/\partial y}$ (s$^{-1}$ m$^{-1}$)', fontsize=10)
    ax2.set_ylabel('Relative Latitude (° from center)', fontsize=10)
    ax2.set_ylim(y.min(), y.max())
    ax2.set_title(f'(b) RK Zonal Mean - Composite', fontsize=10, loc='left')
    ax2.legend(fontsize=8, frameon=True, loc='best')
    ax2.grid(True, alpha=0.3)
    
    # =========================================================================
    # Panel 3: Composite PV
    # =========================================================================
    ax3 = fig.add_subplot(gs[1, 0])
    
    pv_levels = np.linspace(-2, 2, 21)
    im3 = ax3.contourf(x_2d, y_2d, pv_mean * 1e6, levels=pv_levels,
                       cmap='RdYlBu_r', extend='both')
    
    # Mark center
    ax3.plot(0, 0, 'k*', markersize=15, markeredgecolor='white', markeredgewidth=1)
    
    ax3.set_xlabel('Relative Longitude (°)', fontsize=10)
    ax3.set_ylabel('Relative Latitude (°)', fontsize=10)
    ax3.set_xlim(x.min(), x.max())
    ax3.set_ylim(y.min(), y.max())
    ax3.set_aspect('equal')
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    divider3 = make_axes_locatable(ax3)
    cax3 = divider3.append_axes("right", size="5%", pad=0.1)
    cb3 = plt.colorbar(im3, cax=cax3)
    cb3.set_label(r'PV (10$^{-6}$ K m$^2$ kg$^{-1}$ s$^{-1}$)', fontsize=9)
    
    ax3.set_title(f'(c) Baroclinic PV - Composite (Ca: {lev_ca} hPa)', 
                  fontsize=10, loc='left')
    
    # =========================================================================
    # Panel 4: Composite EGR
    # =========================================================================
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Determine levels based on actual data range
    egr_min_plot = max(0, np.nanpercentile(egr_day_mean, 1))  # 1st percentile, but >= 0
    egr_max_plot = np.nanpercentile(egr_day_mean, 99)  # 99th percentile
    
    if egr_max_plot > egr_min_plot:
        egr_levels = np.linspace(egr_min_plot, egr_max_plot, 21)
    else:
        # Fallback if data is problematic
        egr_levels = np.linspace(0, 4, 21)
    
    im4 = ax4.contourf(x_2d, y_2d, egr_day_mean, levels=egr_levels,
                       cmap='YlOrRd', extend='both')
    
    # Mark center
    ax4.plot(0, 0, 'k*', markersize=15, markeredgecolor='white', markeredgewidth=1)
    
    ax4.set_xlabel('Relative Longitude (°)', fontsize=10)
    ax4.set_ylabel('Relative Latitude (°)', fontsize=10)
    ax4.set_xlim(x.min(), x.max())
    ax4.set_ylim(y.min(), y.max())
    ax4.set_aspect('equal')
    ax4.grid(True, alpha=0.3, linestyle='--')
    
    divider4 = make_axes_locatable(ax4)
    cax4 = divider4.append_axes("right", size="5%", pad=0.1)
    cb4 = plt.colorbar(im4, cax=cax4)
    cb4.set_label(r'EGR (day$^{-1}$)', fontsize=9)
    
    mean_egr = np.mean(egr_day_mean)
    ax4.text(0.05, 0.95, f'Mean: {mean_egr:.2f} day$^{{-1}}$',
             transform=ax4.transAxes, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax4.set_title(f'(d) EGR - Composite (Ca: {lev_ca} hPa)', fontsize=10, loc='left')
    
    fig.suptitle(f'Composite (n={len(all_data)}) - {domain_name.upper()} domain ({domain_size}°×{domain_size}°)',
                 fontsize=12, fontweight='bold', y=0.995)
    
    output_file = output_dir / f"composite_{domain_name}.png"
    plt.savefig(output_file, dpi=DPI, bbox_inches='tight')
    plt.close()
    
    print(f"    ✓ Saved: {output_file.name}")
    
    return output_file


def main():
    """Generate all figures."""
    
    print("=" * 80)
    print("STEP 5: Creating Composite Figures")
    print("=" * 80)
    
    # Load cases
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        print(f"\n❌ Error: {cases_file} not found.")
        return
    
    cases = pd.read_csv(cases_file)
    print(f"\nProcessing {len(cases)} cases")
    print(f"Domains: {list(DOMAIN_SIZES.keys())}")
    print(f"PLOT_INDIVIDUAL = {PLOT_INDIVIDUAL}\n")
    
    # Process each domain
    for domain_name, domain_size in DOMAIN_SIZES.items():
        print(f"\n{'='*80}")
        print(f"DOMAIN: {domain_name.upper()} ({domain_size}°×{domain_size}°)")
        print(f"{'='*80}")
        
        composite_data = []
        
        # Process each case
        for idx, row in cases.iterrows():
            track_id = row['track_id']
            
            # Load data
            nc_file = DATA_DIR / f"{track_id}_era5.nc"
            meta_file = DATA_DIR / f"{track_id}_metadata.csv"
            
            if not nc_file.exists() or not meta_file.exists():
                print(f"  ⚠️  Data not found for track {track_id}, skipping")
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
            
            # Compute diagnostics for composite
            lat_2d, lon_2d = np.meshgrid(
                ds_sub.latitude.values, ds_sub.longitude.values, indexing='ij'
            )
            
            # Use critical levels
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
            
            _, _, deta_dy, deta_dy_zonal, _ = rayleigh_kuo_criterion(u_rk, v_rk, lat_2d, lon_2d)
            _, egr_day, _ = eady_growth_rate(u3, v3, T3, q3, p3, z3, lat_2d)
            
            try:
                pv = compute_baroclinic_pv(u3, v3, T3, q3, p3, z3, lat_2d, lon_2d)
            except Exception as e:
                print(f"  ⚠️  PV computation failed for {track_id}: {e}")
                pv = np.full_like(lat_2d, np.nan)
            
            # Store data for composite
            composite_data.append({
                'deta_dy': deta_dy,
                'deta_dy_zonal': deta_dy_zonal,
                'egr_day': egr_day,
                'pv': pv,
                'lev_rk': lev_rk,
                'lev_ca': lev3_ca[1]
            })
            
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(cases)} cases...")
        
        # Create composite figure
        if len(composite_data) > 0:
            print(f"\n  Creating composite figure...")
            create_composite_figure(
                domain_name, domain_size, composite_data,
                FIGURES_DIR / "composite"
            )
        else:
            print(f"\n  ⚠️  No data for {domain_name} domain")
    
    print(f"\n{'='*80}")
    print("✅ All composite figures created successfully!")
    print(f"{'='*80}")
    print(f"\nOutput directory: {FIGURES_DIR / 'composite'}")
    print()


if __name__ == "__main__":
    main()
