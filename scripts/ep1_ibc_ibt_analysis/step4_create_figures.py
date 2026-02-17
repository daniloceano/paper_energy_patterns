"""
Step 4: Create Publication-Quality Figures for EP1 Analysis

Creates 4-panel composite figures from precomputed data.

For each domain (5°, 15°, 30°):
Panel (a): 2D map of ∂η/∂y (Rayleigh-Kuo criterion) at Ck level (350 hPa)
Panel (b): Zonal mean profile of ∂η/∂y
Panel (c): PV at Ca level (975 hPa, shaded) + PV at Ck level (350 hPa, contours) + 200 hPa wind vectors
Panel (d): EGR at Ca level (975 hPa, shaded) + SLP contours + wind vectors at Ca level (975 hPa)

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
import logging
from datetime import datetime

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "ep1_vertical"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

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

# Vector plotting parameters: increase size and reduce density
# `VECTOR_SKIP` is now a mapping per domain name (step for slicing arrays)
# Smaller step -> denser vectors; larger step -> lower density
VECTOR_SKIP = {
    'local': 3,
    'mesoscale': 8,
    'synoptic': 16,
}
# Scales for arrow length (smaller -> longer arrows on plot)
VECTOR_SCALE_250 = 250
VECTOR_SCALE_975 = 100
# Arrow shaft width
VECTOR_WIDTH = 0.005
# Alpha for vectors
VECTOR_ALPHA = 1

def setup_logging():
    """Setup logging to file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"step4_figures_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file


def load_precomputed_composites():
    """Load precomputed composite data from separate domain files."""
    
    logging.info("Loading precomputed composites...")
    
    domain_datasets = {}
    total_size_mb = 0
    
    for domain in DOMAIN_SIZES.keys():
        comp_file = DATA_DIR / f'precomputed_composites_{domain}.nc'
        
        if not comp_file.exists():
            logging.error(f"❌ ERROR: File not found: {comp_file}")
            logging.error("Please run step3_precompute_composites.py first.")
            return None
        
        file_size_mb = comp_file.stat().st_size / 1024**2
        total_size_mb += file_size_mb
        logging.info(f"   {domain}: {comp_file.name} ({file_size_mb:.1f} MB)")
        
        domain_datasets[domain] = xr.open_dataset(comp_file)
    
    logging.info(f"   ✓ Loaded {len(domain_datasets)} domains, total {total_size_mb:.1f} MB")
    
    return domain_datasets


def create_composite_figure(domain_name, ds_domain, output_dir):
    """
    Create 4-panel composite figure for a domain.
    
    Panel layout:
    (a) ∂η/∂y 2D map at Ck level       (b) ∂η/∂y zonal mean profile
    (c) PV composite (Ca + Ck + jet)   (d) EGR + SLP + winds
    """
    logging.info(f"  Creating 4-panel composite for {domain_name}...")
    
    try:
        # Load data for this domain
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'
        level_dim = f'level_{domain_name}'
        
        # Get coordinates
        x = ds_domain[x_dim].values
        y = ds_domain[y_dim].values
        
        # List available variables for debugging
        available_vars = list(ds_domain.data_vars.keys())
        logging.info(f"    Available variables in {domain_name}: {len(available_vars)} vars")
        logging.info(f"    Variables: {', '.join(sorted(available_vars)[:10])}{'...' if len(available_vars) > 10 else ''}")
        
        # Get diagnostic fields (precomputed in step3) with existence checks
        deta_dy = ds_domain[f'{domain_name}_deta_dy'].values if f'{domain_name}_deta_dy' in ds_domain else None
        deta_dy_zonal = ds_domain[f'{domain_name}_deta_dy_zonal'].values if f'{domain_name}_deta_dy_zonal' in ds_domain else None
        pv_ca = ds_domain[f'{domain_name}_pv_ca'].values if f'{domain_name}_pv_ca' in ds_domain else None
        pv_200 = ds_domain[f'{domain_name}_pv_200'].values if f'{domain_name}_pv_200' in ds_domain else None
        egr = ds_domain[f'{domain_name}_egr'].values if f'{domain_name}_egr' in ds_domain else None
        
        # Get SLP if available
        msl = ds_domain[f'{domain_name}_msl'].values if f'{domain_name}_msl' in ds_domain else None
        
        # Log what we found
        logging.info(f"    Data availability: EGR={'✓' if egr is not None else '✗'}, "
                    f"PV_Ca={'✓' if pv_ca is not None else '✗'}, "
                    f"PV_200={'✓' if pv_200 is not None else '✗'}, "
                    f"SLP={'✓' if msl is not None else '✗'}, "
                    f"deta_dy={'✓' if deta_dy is not None else '✗'}")
        
        if deta_dy is None or pv_ca is None or egr is None:
            logging.error(f"    ❌ Missing essential diagnostic variables for {domain_name}")
            return
        
        # Get winds at specific levels from 3D arrays
        if level_dim in ds_domain.coords:
            levels = ds_domain[level_dim].values
            u_all = ds_domain[f'{domain_name}_u'].values
            v_all = ds_domain[f'{domain_name}_v'].values
            
            # Find indices
            idx_975 = np.argmin(np.abs(levels - 975))
            idx_200 = np.argmin(np.abs(levels - 200))
            
            u_975 = u_all[idx_975]
            v_975 = v_all[idx_975]
            u_200 = u_all[idx_200]
            v_200 = v_all[idx_200]
        else:
            u_975 = v_975 = u_200 = v_200 = None
        
        # Create figure with 4 panels
        fig = plt.figure(figsize=(14, 10))
        gs = gridspec.GridSpec(2, 2, hspace=0.25, wspace=0.3)
        
        # ========================================================================
        # Panel (a): ∂η/∂y 2D map at Ck level
        # ========================================================================
        ax1 = fig.add_subplot(gs[0, 0])
        
        # Color levels
        deta_max = np.nanmax(np.abs(deta_dy))
        deta_levels = np.linspace(-deta_max, deta_max, 21)
        
        im1 = ax1.contourf(x, y, deta_dy, levels=deta_levels, cmap='RdBu_r', extend='both')
        ax1.contour(x, y, deta_dy, levels=[0], colors='black', linewidths=1.5)
        
        ax1.set_xlabel('Relative Longitude (°)')
        ax1.set_ylabel('Relative Latitude (°)')
        ax1.set_title('(a) ∂η/∂y at Ck level (350 hPa)')
        ax1.set_aspect('equal')
        
        # Colorbar
        divider = make_axes_locatable(ax1)
        cax1 = divider.append_axes('right', size='4%', pad=0.1)
        cbar1 = fig.colorbar(im1, cax=cax1)
        cbar1.set_label('∂η/∂y (s$^{-1}$ m$^{-1}$)')
        
        # ========================================================================
        # Panel (b): Zonal mean profile of ∂η/∂y
        # ========================================================================
        ax2 = fig.add_subplot(gs[0, 1])
        
        ax2.plot(deta_dy_zonal, y, 'b-', linewidth=2)
        ax2.axvline(0, color='black', linestyle='--', linewidth=1)
        ax2.grid(True, alpha=0.3)
        
        ax2.set_xlabel('∂η/∂y (s$^{-1}$ m$^{-1}$)')
        ax2.set_ylabel('Relative Latitude (°)')
        ax2.set_title('(b) Zonal mean ∂η/∂y')
        
        # ========================================================================
        # Panel (c): PV at Ca (shaded) + PV at 200 hPa (contours) + 200 hPa winds
        # ========================================================================
        ax3 = fig.add_subplot(gs[1, 0])
        
        # Shaded: PV at Ca level (975 hPa)
        # Note: MetPy returns PV in SI units (K m^2 kg^-1 s^-1)
        # 1 PVU = 1e-6 K m^2 kg^-1 s^-1, so multiply by 1e6 to get PVU
        pv_ca_pvu = pv_ca * 1e6  # Convert to PVU
        logging.info(f"   PV at Ca range: [{np.nanmin(pv_ca_pvu):.2f}, {np.nanmax(pv_ca_pvu):.2f}] PVU")
        pv_min = np.nanmin(pv_ca_pvu)
        pv_levels = np.linspace(pv_min, 0, 21)
        
        im3 = ax3.contourf(x, y, pv_ca_pvu, levels=pv_levels, cmap='RdYlBu_r', extend='both')
        
        # Contours: PV at 200 hPa (tropopause level) - green
        # 2 PVU is the dynamical tropopause definition
        pv_200_pvu = pv_200 * 1e6
        logging.info(f"   PV at 200 hPa range: [{np.nanmin(pv_200_pvu):.2f}, {np.nanmax(pv_200_pvu):.2f}] PVU")
        pv_200_levels = np.linspace(np.nanpercentile(pv_200_pvu, 10), np.nanpercentile(pv_200_pvu, 90), 8)
        cs_pv = ax3.contour(x, y, pv_200_pvu, levels=pv_200_levels, colors='green', linewidths=1.3, alpha=0.8)
        ax3.clabel(cs_pv, inline=1, fontsize=8, fmt='%1.0f')
        
        # Add 2 PVU contour (tropopause) in black
        cs_trop = ax3.contour(x, y, pv_200_pvu, levels=[2.0], colors='black', linewidths=2.0, linestyles='--')
        ax3.clabel(cs_trop, inline=1, fontsize=9, fmt='%1.0f PVU')
        
        # Vectors: 200 hPa winds (gray)
        if u_200 is not None and v_200 is not None:
            skip = max(1, VECTOR_SKIP.get(domain_name, 12))
            ax3.quiver(x[::skip], y[::skip], u_200[::skip, ::skip], v_200[::skip, ::skip],
                      color='grey', alpha=VECTOR_ALPHA, scale=VECTOR_SCALE_250, width=VECTOR_WIDTH)
        
        ax3.set_xlabel('Relative Longitude (°)')
        ax3.set_ylabel('Relative Latitude (°)')
        ax3.set_title('(c) PV at Ca (shaded), PV at 200 hPa (green), 2 PVU (dashed)')
        ax3.set_aspect('equal')
        
        # Colorbar
        divider = make_axes_locatable(ax3)
        cax3 = divider.append_axes('right', size='4%', pad=0.1)
        cbar3 = fig.colorbar(im3, cax=cax3)
        cbar3.set_label('PV at Ca (975 hPa) [PVU]')
        
        # ========================================================================
        # Panel (d): EGR (shaded) + SLP (contours) + 975 hPa winds
        # ========================================================================
        ax4 = fig.add_subplot(gs[1, 1])
        
        # Shaded: EGR
        egr_levels = np.linspace(np.nanpercentile(egr, 1), np.nanpercentile(egr, 99), 21)
        im4 = ax4.contourf(x, y, egr, levels=egr_levels, cmap='YlOrRd', extend='both')
        
        # Annotate domain-mean EGR
        egr_mean = np.nanmean(egr)
        ax4.text(0.05, 0.95, f'Mean: {egr_mean:.2f} day$^{{-1}}$',
                transform=ax4.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Contours: SLP (black)
        if msl is not None:
            logging.info(f"    Plotting SLP: range [{np.nanmin(msl)/100:.1f}, {np.nanmax(msl)/100:.1f}] hPa")
            msl_hpa = msl / 100.0  # Convert Pa to hPa
            slp_levels = np.arange(
                np.floor(np.nanmin(msl_hpa) / 2) * 2,
                np.ceil(np.nanmax(msl_hpa) / 2) * 2 + 2,
                2
            )
            cs_slp = ax4.contour(x, y, msl_hpa, levels=slp_levels, colors='black', linewidths=1.0, alpha=0.7)
            ax4.clabel(cs_slp, inline=1, fontsize=8, fmt='%1.0f')
        else:
            logging.warning(f"    ⚠️  SLP not available for {domain_name}")
        
        # Contours: PV at 200 hPa (green) - shows upper-level forcing
        if pv_200 is not None:
            pv_200_pvu = pv_200 * 1e6
            logging.info(f"    Plotting PV@200: range [{np.nanmin(pv_200_pvu):.2f}, {np.nanmax(pv_200_pvu):.2f}] PVU")
            pv_200_levels = np.linspace(np.nanpercentile(pv_200_pvu, 10), 
                                         np.nanpercentile(pv_200_pvu, 90), 6)
            cs_pv200 = ax4.contour(x, y, pv_200_pvu, levels=pv_200_levels, 
                                   colors='green', linewidths=1.0, alpha=0.6)
            ax4.clabel(cs_pv200, inline=1, fontsize=7, fmt='%1.0f')
            
            # 2 PVU contour (tropopause)
            cs_trop = ax4.contour(x, y, pv_200_pvu, levels=[2.0], 
                                 colors='darkgreen', linewidths=1.8, linestyles='--')
        else:
            logging.warning(f"    ⚠️  PV@200hPa not available for {domain_name}")
        
        # Vectors: 975 hPa winds (black)
        if u_975 is not None and v_975 is not None:
            skip = max(1, VECTOR_SKIP.get(domain_name, 12))
            ax4.quiver(x[::skip], y[::skip], u_975[::skip, ::skip], v_975[::skip, ::skip],
                      color='black', alpha=VECTOR_ALPHA, scale=VECTOR_SCALE_975, width=VECTOR_WIDTH)
        
        ax4.set_xlabel('Relative Longitude (°)')
        ax4.set_ylabel('Relative Latitude (°)')
        ax4.set_title('(d) EGR (shaded), SLP (black), PV@200hPa (green), 975 hPa wind')
        ax4.set_aspect('equal')
        
        # Colorbar
        divider = make_axes_locatable(ax4)
        cax4 = divider.append_axes('right', size='4%', pad=0.1)
        cbar4 = fig.colorbar(im4, cax=cax4)
        cbar4.set_label('EGR (day$^{-1}$)')
        
        # ========================================================================
        # Overall title and save
        # ========================================================================
        fig.suptitle(f'EP1 Composite Analysis - {domain_name.capitalize()} Domain ({DOMAIN_SIZES[domain_name]}°)',
                    fontsize=13, fontweight='bold', y=0.98)
        
        out_file = output_dir / f'composite_{domain_name}.png'
        fig.savefig(out_file, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        logging.info(f"    ✓ Saved: {out_file.name}")
        
    except Exception as e:
        logging.error(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()


def create_tropopause_figure(ds_domain, domain_name, output_dir):
    """
    Create composite figure showing upper-level dynamics:
    - Omega (vertical velocity) at 200 hPa (shaded)
    - PV at 200 hPa (contours, with 2 PVU tropopause)
    - Wind vectors at 250 hPa (jet level)
    
    This figure highlights the coupling between upper-level forcing (PV),
    vertical motion (omega), and the jet stream structure.
    """
    domain_size = DOMAIN_SIZES[domain_name]
    logging.info(f"  Creating tropopause figure for {domain_name}...")
    
    try:
        # Load data
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'
        level_dim = f'level_{domain_name}'
        
        x = ds_domain[x_dim].values
        y = ds_domain[y_dim].values
        
        # Get PV at 200 hPa
        pv_200 = ds_domain[f'{domain_name}_pv_200'].values
        pv_200_pvu = pv_200 * 1e6  # Convert to PVU
        
        # Get omega and winds at specific levels
        if level_dim in ds_domain.coords:
            levels = ds_domain[level_dim].values
            
            # Check if omega (w) exists
            if f'{domain_name}_w' not in ds_domain:
                logging.warning(f"    ⚠️  Omega (w) not found for {domain_name}, skipping tropopause figure")
                return
            
            w_all = ds_domain[f'{domain_name}_w'].values
            u_all = ds_domain[f'{domain_name}_u'].values
            v_all = ds_domain[f'{domain_name}_v'].values
            
            # Find levels
            idx_200 = np.argmin(np.abs(levels - 200))
            idx_250 = np.argmin(np.abs(levels - 250))
            
            omega_200 = w_all[idx_200]  # Pa/s
            u_250 = u_all[idx_250]
            v_250 = v_all[idx_250]
        else:
            logging.warning(f"    ⚠️  No pressure levels found for {domain_name}, skipping tropopause figure")
            return
        
        # Create single-panel figure
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111)
        
        # Shaded: Omega at 200 hPa (Pa/s)
        # Convert to hPa/h for easier interpretation: 1 Pa/s = 36 hPa/h
        omega_hpa_h = omega_200 * 36.0
        
        # Symmetric scale around zero
        vmax = np.nanpercentile(np.abs(omega_hpa_h), 95)
        omega_levels = np.linspace(-vmax, vmax, 21)
        
        im = ax.contourf(x, y, omega_hpa_h, levels=omega_levels, 
                        cmap='RdBu_r', extend='both')
        
        # Contours: PV at 200 hPa
        pv_levels = np.linspace(np.nanpercentile(pv_200_pvu, 10), 
                               np.nanpercentile(pv_200_pvu, 90), 10)
        cs_pv = ax.contour(x, y, pv_200_pvu, levels=pv_levels, 
                          colors='green', linewidths=1.2, alpha=0.7)
        ax.clabel(cs_pv, inline=1, fontsize=8, fmt='%1.1f')
        
        # 2 PVU contour (dynamical tropopause) - thick black dashed
        cs_trop = ax.contour(x, y, pv_200_pvu, levels=[2.0], 
                            colors='black', linewidths=2.5, linestyles='--')
        ax.clabel(cs_trop, inline=1, fontsize=10, fmt='%1.0f PVU', fontweight='bold')
        
        # Wind vectors at 250 hPa (jet level)
        skip = max(1, VECTOR_SKIP.get(domain_name, 12))
        ax.quiver(x[::skip], y[::skip], u_250[::skip, ::skip], v_250[::skip, ::skip],
                 color='black', alpha=VECTOR_ALPHA, scale=VECTOR_SCALE_250, width=VECTOR_WIDTH)
        
        ax.set_xlabel('Relative Longitude (°)', fontsize=11)
        ax.set_ylabel('Relative Latitude (°)', fontsize=11)
        ax.set_title(f'Upper-Level Dynamics - {domain_name.capitalize()} Domain ({domain_size}°)\\n' +
                    'Omega at 200 hPa (shaded), PV at 200 hPa (green), 2 PVU (dashed), 250 hPa wind (vectors)',
                    fontsize=12, fontweight='bold')
        ax.set_aspect('equal')
        
        # Colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='4%', pad=0.1)
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label('Omega at 200 hPa (hPa h$^{-1}$)', fontsize=10)
        
        # Add annotation
        ax.text(0.02, 0.98, 
               'Negative omega = upward motion',
               transform=ax.transAxes, fontsize=9,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save
        out_file = output_dir / f'tropopause_{domain_name}.png'
        fig.savefig(out_file, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        logging.info(f"    ✓ Saved: {out_file.name}")
        
    except Exception as e:
        logging.error(f"    ❌ Error creating tropopause figure: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main execution function."""
    
    # Setup logging
    log_file = setup_logging()
    
    logging.info("=" * 80)
    logging.info("STEP 4: CREATE FIGURES")
    logging.info("=" * 80)
    logging.info(f"Log file: {log_file}")
    
    # Load precomputed composites
    domain_datasets = load_precomputed_composites()
    if domain_datasets is None:
        return
    
    # Verify required variables
    logging.info("\nVerifying data integrity...")
    for domain in DOMAIN_SIZES.keys():
        ds = domain_datasets[domain]
        required_vars = [f'{domain}_egr', f'{domain}_deta_dy', f'{domain}_pv_ca', f'{domain}_pv_200']
        missing = [v for v in required_vars if v not in ds]
        
        if missing:
            logging.error(f"❌ Missing required variables in {domain}: {missing}")
            logging.error("   Please re-run step3_precompute_composites.py")
            return
    
    logging.info("   ✓ All required variables present in all domains")
    
    # Create composite figures for each domain
    logging.info("\nCreating 4-panel composite figures...")
    composite_dir = FIGURES_DIR / "composite"
    
    for domain_name in DOMAIN_SIZES.keys():
        logging.info(f"\nDomain: {domain_name}")
        create_composite_figure(domain_name, domain_datasets[domain_name], composite_dir)
    
    # Create tropopause figures (omega + PV@200 + wind@250)
    logging.info("\nCreating tropopause-level figures...")
    
    for domain_name in DOMAIN_SIZES.keys():
        logging.info(f"\nDomain: {domain_name}")
        create_tropopause_figure(domain_datasets[domain_name], domain_name, composite_dir)
    
    # Close datasets
    for domain_name in DOMAIN_SIZES.keys():
        domain_datasets[domain_name].close()
    
    logging.info("\n" + "=" * 80)
    logging.info("✓ FIGURES COMPLETE")
    logging.info("=" * 80)
    logging.info(f"\nFigures saved in: {composite_dir}")
    logging.info("\nGenerated figures:")
    for domain in DOMAIN_SIZES.keys():
        comp_file = composite_dir / f"composite_{domain}.png"
        trop_file = composite_dir / f"tropopause_{domain}.png"
        if comp_file.exists():
            size_mb = comp_file.stat().st_size / 1024**2
            logging.info(f"  ✓ composite_{domain}.png ({size_mb:.2f} MB)")
        if trop_file.exists():
            size_mb = trop_file.stat().st_size / 1024**2
            logging.info(f"  ✓ tropopause_{domain}.png ({size_mb:.2f} MB)")
    
    logging.info(f"\nLog file: {log_file}")


if __name__ == '__main__':
    main()
