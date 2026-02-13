"""
Step 5: Create Publication-Quality Figures for EP1 Full Analysis

Creates composite figures from precomputed data or recomputes if needed.

Modifications from ep1_ibc_ibt_analysis/step5:
- Uses precomputed composites when available
- PV composites: includes PV(250 hPa) contours + wind vectors (gray) at 250 hPa
- EGR composites: includes SLP contours + wind vectors at 975 hPa
- Generates time series plots (new)

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1_full"
RESULTS_DIR = BASE_DIR / "results" / "ep1_full"
FIGURES_DIR = BASE_DIR / "figures" / "ep1_full"

# Create subdirectories
(FIGURES_DIR / "composite").mkdir(parents=True, exist_ok=True)
(FIGURES_DIR / "timeseries").mkdir(parents=True, exist_ok=True)

DPI = 300
DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}

# Plotting style
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


def load_precomputed_composites():
    """Load precomputed composites if available."""
    comp_file = DATA_DIR / "precomputed_composites.nc"
    if comp_file.exists():
        print(f"Loading precomputed composites from {comp_file}")
        return xr.open_dataset(comp_file)
    else:
        print("⚠️  Precomputed composites not found. Run step3 first.")
        return None


def plot_pv_composite_with_jet(domain_name, ds_comp, output_dir):
    """
    Create PV composite figure with 250 hPa jet overlay.
    
    Modifications:
    - Shaded: PV at 975 hPa (baroclinic instability)
    - Contours (green): PV at 250 hPa (upper-level dynamics)
    - Vectors (gray): Wind at 250 hPa (jet structure)
    """
    print(f"  Creating PV composite for {domain_name}...")
    
    try:
        # Load data for this domain
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'
        level_dim = f'level_{domain_name}'
        
        # Get coordinates
        x = ds_comp[x_dim].values
        y = ds_comp[y_dim].values
        levels = ds_comp[level_dim].values
        
        # Get PV at different levels from pv_all
        pv_all = ds_comp[f'{domain_name}_pv_all'].values  # (level, y, x)
        
        # Find indices for 975 and 250 hPa
        idx_975 = np.argmin(np.abs(levels - 975))
        idx_250 = np.argmin(np.abs(levels - 250))
        
        pv_975 = pv_all[idx_975] * 1e6  # Convert to PVU-like units
        pv_250 = pv_all[idx_250] * 1e6
        
        # Get winds at 250 hPa from u_all/v_all
        u_all = ds_comp[f'{domain_name}_u_all'].values
        v_all = ds_comp[f'{domain_name}_v_all'].values
        
        u_250 = u_all[idx_250]
        v_250 = v_all[idx_250]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Shaded: PV at 975 hPa
        pv_min = np.nanmin(pv_975)
        pv_levels = np.linspace(pv_min, 0, 21)
        im = ax.contourf(x, y, pv_975, levels=pv_levels, cmap='RdYlBu_r', extend='both')
        
        # Contours (green): PV at 250 hPa
        pv250_levels = np.linspace(np.nanpercentile(pv_250, 5), np.nanpercentile(pv_250, 95), 8)
        cs_pv250 = ax.contour(x, y, pv_250, levels=pv250_levels, colors='green', linewidths=1.3, alpha=0.8)
        ax.clabel(cs_pv250, inline=1, fontsize=8, fmt='%1.0f')
        
        # Vectors (gray): Wind at 250 hPa (subsample for clarity)
        skip = max(1, len(x) // 15)
        ax.quiver(x[::skip], y[::skip], u_250[::skip, ::skip], v_250[::skip, ::skip],
                 color='gray', alpha=0.6, scale=400, width=0.003)
        
        # Formatting
        ax.set_xlabel('Relative Longitude (°)')
        ax.set_ylabel('Relative Latitude (°)')
        ax.set_title(f'EP1 Composite: PV at 975 hPa (shaded), PV at 250 hPa (green), Jet (vectors)\nDomain: {domain_name}')
        ax.set_aspect('equal')
        
        # Colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='4%', pad=0.1)
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label('PV at 975 hPa (10$^{-6}$ K m$^2$ kg$^{-1}$ s$^{-1}$)')
        
        # Save
        out_file = output_dir / f'pv_composite_{domain_name}.png'
        fig.savefig(out_file, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        print(f"    ✓ Saved: {out_file}")
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()


def plot_egr_composite_with_slp(domain_name, ds_comp, output_dir):
    """
    Create EGR composite figure with SLP and low-level winds.
    
    Modifications:
    - Shaded: Eady Growth Rate
    - Contours (black): SLP (mean sea level pressure)
    - Vectors (black): Wind at 975 hPa (low-level circulation)
    """
    print(f"  Creating EGR composite for {domain_name}...")
    
    try:
        # Load data for this domain
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'
        level_dim = f'level_{domain_name}'
        
        x = ds_comp[x_dim].values
        y = ds_comp[y_dim].values
        levels = ds_comp[level_dim].values
        
        # EGR (computed in step3 or needs recomputation)
        egr = ds_comp[f'{domain_name}_egr'].values if f'{domain_name}_egr' in ds_comp else None
        
        # SLP
        msl = ds_comp[f'{domain_name}_msl'].values if f'{domain_name}_msl' in ds_comp else None
        
        # Winds at 975 hPa
        u_all = ds_comp[f'{domain_name}_u_all'].values
        v_all = ds_comp[f'{domain_name}_v_all'].values
        
        idx_975 = np.argmin(np.abs(levels - 975))
        u_975 = u_all[idx_975]
        v_975 = v_all[idx_975]
        
        if egr is None:
            print(f"    ⚠️  EGR not found in precomputed data")
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Shaded: EGR
        egr_levels = np.linspace(np.nanpercentile(egr, 1), np.nanpercentile(egr, 99), 21)
        im = ax.contourf(x, y, egr, levels=egr_levels, cmap='YlOrRd', extend='both')
        
        # Contours (black): SLP
        if msl is not None:
            msl_hpa = msl / 100.0  # Convert Pa to hPa
            slp_levels = np.arange(
                np.floor(np.nanmin(msl_hpa) / 2) * 2,
                np.ceil(np.nanmax(msl_hpa) / 2) * 2 + 2,
                2
            )
            cs_slp = ax.contour(x, y, msl_hpa, levels=slp_levels, colors='black', linewidths=1.0, alpha=0.7)
            ax.clabel(cs_slp, inline=1, fontsize=8, fmt='%1.0f')
        
        # Vectors (black): Wind at 975 hPa
        skip = max(1, len(x) // 15)
        ax.quiver(x[::skip], y[::skip], u_975[::skip, ::skip], v_975[::skip, ::skip],
                 color='black', alpha=0.7, scale=300, width=0.003)
        
        # Formatting
        ax.set_xlabel('Relative Longitude (°)')
        ax.set_ylabel('Relative Latitude (°)')
        ax.set_title(f'EP1 Composite: EGR (shaded), SLP (contours), 975 hPa wind (vectors)\nDomain: {domain_name}')
        ax.set_aspect('equal')
        
        # Colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='4%', pad=0.1)
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label('Eady Growth Rate (day$^{-1}$)')
        
        # Save
        out_file = output_dir / f'egr_composite_{domain_name}.png'
        fig.savefig(out_file, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        print(f"    ✓ Saved: {out_file}")
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()


def plot_timeseries_statistics(output_dir):
    """
    Create time series statistics plot (mean ± std across all cases).
    """
    print("\nCreating time series statistics...")
    
    instab_dir = RESULTS_DIR / "instabilities"
    if not instab_dir.exists():
        print("  ⚠️  Instability results not found. Run step4 first.")
        return
    
    # Load all timeseries files
    timeseries_files = list(instab_dir.glob("*_timeseries.nc"))
    if len(timeseries_files) == 0:
        print("  ⚠️  No timeseries files found.")
        return
    
    print(f"  Found {len(timeseries_files)} cases")
    
    # For each domain, collect all time series (normalized to relative time)
    for domain_name in DOMAIN_SIZES.keys():
        egr_series_list = []
        rk_series_list = []
        
        for ts_file in timeseries_files:
            try:
                ds = xr.open_dataset(ts_file)
                time_dim = f'time_{domain_name}'
                
                if time_dim in ds.coords:
                    egr = ds[f'{domain_name}_egr'].values
                    rk = ds[f'{domain_name}_rk_satisfied'].values
                    
                    egr_series_list.append(egr)
                    rk_series_list.append(rk)
                
                ds.close()
            except Exception:
                continue
        
        if len(egr_series_list) == 0:
            continue
        
        # Find common length (minimum across all cases)
        min_len = min(len(s) for s in egr_series_list)
        
        # Truncate all to common length
        egr_array = np.array([s[:min_len] for s in egr_series_list])
        rk_array = np.array([s[:min_len] for s in rk_series_list])
        
        # Compute mean and std
        egr_mean = np.nanmean(egr_array, axis=0)
        egr_std = np.nanstd(egr_array, axis=0)
        rk_fraction = np.nanmean(rk_array, axis=0)  # Fraction of cases satisfying RK
        
        # Relative time (normalized)
        rel_time = np.linspace(0, 1, min_len)
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # EGR
        ax1.plot(rel_time, egr_mean, 'b-', linewidth=2, label='Mean')
        ax1.fill_between(rel_time, egr_mean - egr_std, egr_mean + egr_std, alpha=0.3, color='b', label='±1σ')
        ax1.set_ylabel('EGR (day$^{-1}$)')
        ax1.set_title(f'EP1 Intensification Phase Evolution - {domain_name} domain')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RK
        ax2.plot(rel_time, rk_fraction * 100, 'r-', linewidth=2)
        ax2.set_xlabel('Normalized Time (0 = start, 1 = end of intensification)')
        ax2.set_ylabel('RK Satisfied (%)')
        ax2.set_ylim([0, 100])
        ax2.grid(True, alpha=0.3)
        
        # Save
        out_file = output_dir / f'timeseries_{domain_name}.png'
        fig.savefig(out_file, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        print(f"  ✓ Saved: {out_file}")


def main():
    print("=" * 80)
    print("STEP 5: CREATE FIGURES")
    print("=" * 80)
    
    # Load precomputed composites
    ds_comp = load_precomputed_composites()
    if ds_comp is None:
        return
    
    # Create composite figures for each domain
    print("\nCreating composite figures...")
    composite_dir = FIGURES_DIR / "composite"
    
    for domain_name in DOMAIN_SIZES.keys():
        print(f"\nDomain: {domain_name}")
        plot_pv_composite_with_jet(domain_name, ds_comp, composite_dir)
        plot_egr_composite_with_slp(domain_name, ds_comp, composite_dir)
    
    ds_comp.close()
    
    # Create time series plots
    timeseries_dir = FIGURES_DIR / "timeseries"
    plot_timeseries_statistics(timeseries_dir)
    
    print("\n" + "=" * 80)
    print("✓ FIGURES COMPLETE")
    print("=" * 80)
    print(f"\nFigures saved in:")
    print(f"  - {composite_dir}")
    print(f"  - {timeseries_dir}")


if __name__ == '__main__':
    main()
