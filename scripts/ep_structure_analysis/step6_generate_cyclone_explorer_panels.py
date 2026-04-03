"""
Step 6: Generate Cyclone Explorer Multi-Panel Figures

Creates a 2×2 multi-panel figure for each timestep of each EP1/EP2 cyclone
during their intensification phase. These panels enable temporal exploration
of individual cyclones on the website.

Panel Layout (2×2 grid, 30°×30° panel centered on cyclone; inner 15°×15° box shown):
  Top-left:     SLP + 850 hPa wind vectors
  Top-right:    Temperature 850 hPa
  Bottom-left:  Specific Humidity 975 hPa
  Bottom-right: Geopotential 500 hPa

Output:
  figures/cyclone_explorer/{ep_label}/{track_id}/panel_t{index:03d}.png

Usage:
  python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py
  python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py --jobs 4
  python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py --subset 10

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import argparse
import logging
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
FIGURES_DIR = PROJECT_ROOT / "figures" / "cyclone_explorer"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DPI = 150  # Lower than paper figures (trade-off size vs quality)
# Panels are a 30°×30° view centered on the cyclone; a 15°×15° box is overlaid
DOMAIN_SIZE = 30.0  # degrees (panel domain)
INNER_BOX_SIZE = 15.0  # degrees (visual box shown inside panel)
INNER_BOX_HALF = INNER_BOX_SIZE / 2.0

# Plotting style
plt.rcParams.update({
    "font.size": 8,
    "font.family": "sans-serif",
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.dpi": 100,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "axes.grid": False,
})

# Vector plot parameters
VECTOR_SKIP = 8
VECTOR_SCALE = 150
VECTOR_WIDTH = 0.003


# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"step6_cyclone_explorer_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("=" * 70)
    logging.info("STEP 6: GENERATE CYCLONE EXPLORER PANELS")
    logging.info("=" * 70)
    
    return log_file


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """Extract subdomain centered on cyclone."""
    half = domain_size / 2.0
    lat_min, lat_max = center_lat - half, center_lat + half
    lon_min, lon_max = center_lon - half, center_lon + half
    
    return ds.sel(
        latitude=slice(lat_max, lat_min),  # descending
        longitude=slice(lon_min, lon_max)
    )


def _add_cyclone_center_mark(ax, marker_size=100):
    """Add cyclone center marker at origin."""
    ax.scatter([0], [0], marker='x', s=marker_size, c='red', 
               linewidths=2, zorder=10, label='Cyclone center')


# ============================================================================
# PANEL PLOTTING
# ============================================================================

def create_panel_figure(ds_timestep, center_lat, center_lon, time_str, track_id):
    """
    Create 2×2 multi-panel figure for one timestep.
    
    Parameters
    ----------
    ds_timestep : xr.Dataset
        ERA5 data for single timestep (no time dimension)
    center_lat, center_lon : float
        Cyclone center coordinates
    time_str : str
        ISO format timestamp
    track_id : str
        Cyclone track ID
        
    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    # Extract subdomain
    ds_sub = extract_subdomain(ds_timestep, center_lat, center_lon, DOMAIN_SIZE)
    
    # Get pressure coordinate name
    pc = "pressure_level" if "pressure_level" in ds_sub.coords else "level"
    levels = ds_sub[pc].values
    
    def _idx(target_hPa):
        return int(np.argmin(np.abs(levels - target_hPa)))
    
    def _sel(da, target_hPa):
        return da.isel({pc: _idx(target_hPa)})
    
    # Extract fields - select appropriate pressure levels
    u_850 = _sel(ds_sub["u"], 850).values
    v_850 = _sel(ds_sub["v"], 850).values
    t_850 = _sel(ds_sub["t"], 850).values - 273.15  # K to °C
    q_975 = _sel(ds_sub["q"], 975).values * 1000  # kg/kg to g/kg
    z_500 = _sel(ds_sub["z"], 500).values / 9.81  # m²/s² to m
    # MSL may have pressure_level dim (constant across levels) - take first
    msl_raw = ds_sub["msl"]
    if pc in msl_raw.dims:
        msl_raw = msl_raw.isel({pc: 0})
    msl = msl_raw.values / 100  # Pa to hPa
    
    # Coordinates relative to center
    lats = ds_sub.latitude.values
    lons = ds_sub.longitude.values
    y = lats - center_lat
    x = lons - center_lon
    X, Y = np.meshgrid(x, y)
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    fig.suptitle(f"Track {track_id} — {time_str}", fontsize=11, fontweight='bold')
    
    # ────────────────────────────────────────────────────────────────────────
    # Top-left: SLP + 850 hPa wind vectors
    # Panels are a 30°×30° view centered on the cyclone; an inner 15°×15° box is
    # drawn to indicate the smaller composite region used elsewhere in the repo.
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[0, 0]
    cs = ax.contourf(X, Y, msl, levels=15, cmap='RdYlBu_r', extend='both')
    ax.contour(X, Y, msl, levels=10, colors='black', linewidths=0.5, alpha=0.4)
    
    # Wind vectors (subsample)
    skip = VECTOR_SKIP
    ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
              u_850[::skip, ::skip], v_850[::skip, ::skip],
              scale=VECTOR_SCALE, width=VECTOR_WIDTH, color='black', alpha=0.6)
    
    _add_cyclone_center_mark(ax)
    # draw inner 15°×15° box centered at origin
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("SLP + 850 hPa Winds", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="SLP (hPa)", shrink=0.8)
    
    # ────────────────────────────────────────────────────────────────────────
    # Top-right: Temperature 850 hPa
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[0, 1]
    cs = ax.contourf(X, Y, t_850, levels=15, cmap='RdBu_r', extend='both')
    ax.contour(X, Y, t_850, levels=10, colors='black', linewidths=0.5, alpha=0.4)
    _add_cyclone_center_mark(ax)
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("Temperature 850 hPa", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="T (°C)", shrink=0.8)
    
    # ────────────────────────────────────────────────────────────────────────
    # Bottom-left: Specific Humidity 975 hPa
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[1, 0]
    cs = ax.contourf(X, Y, q_975, levels=15, cmap='YlGnBu', extend='max')
    _add_cyclone_center_mark(ax)
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("Specific Humidity 975 hPa", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="q (g/kg)", shrink=0.8)
    
    # ────────────────────────────────────────────────────────────────────────
    # Bottom-right: Geopotential 500 hPa
    # ────────────────────────────────────────────────────────────────────────
    ax = axes[1, 1]
    cs = ax.contourf(X, Y, z_500, levels=15, cmap='viridis', extend='both')
    ax.contour(X, Y, z_500, levels=10, colors='white', linewidths=0.5, alpha=0.6)
    _add_cyclone_center_mark(ax)
    try:
        rect = mpatches.Rectangle((-INNER_BOX_HALF, -INNER_BOX_HALF), INNER_BOX_SIZE, INNER_BOX_SIZE,
                                  linewidth=1, edgecolor='black', linestyle='--', facecolor='none', zorder=9)
        ax.add_patch(rect)
    except Exception:
        pass
    ax.set_title("Geopotential 500 hPa", fontweight='bold')
    ax.set_xlabel("Longitude offset (°)")
    ax.set_ylabel("Latitude offset (°)")
    plt.colorbar(cs, ax=ax, label="Z (m)", shrink=0.8)
    
    plt.tight_layout()
    return fig


# ============================================================================
# PROCESSING
# ============================================================================

def process_one_cyclone(task):
    """
    Generate panel figures for all timesteps of one cyclone.

    This function now centers each timestep on the cyclone position at that
    timestep (nearest track point), instead of using a single fixed center for
    the whole intensification phase. This ensures the explorer panels follow
    the cyclone as it evolves.

    Parameters
    ----------
    task : tuple (track_id, ep_label, center_lat, center_lon)

    Returns
    -------
    track_id : str
    n_panels : int
        Number of panels generated
    error : str or None
    """
    track_id, ep_label, center_lat, center_lon = task
    track_id = str(track_id)

    nc_file = DATA_DIR / f"{track_id}_era5.nc"

    if not nc_file.exists():
        return track_id, 0, "missing_nc"

    try:
        # Open NetCDF
        ds = xr.open_dataset(nc_file)
        tc = "valid_time" if "valid_time" in ds.dims else "time"
        n_times = len(ds[tc])

        # Load local tracks file (per-timestep cyclone positions)
        tracks_file = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"
        if not tracks_file.exists():
            # fallback: use fixed center for all timesteps (maintain previous behavior)
            tracks_df = None
            logging.warning(f"Tracks file not found: {tracks_file} — using fixed center")
        else:
            tracks_df = pd.read_csv(tracks_file, parse_dates=["date"])
            tracks_df = tracks_df[tracks_df["track_id"] == int(track_id)] if tracks_df["track_id"].dtype != object else tracks_df[tracks_df["track_id"] == track_id]

        # Create output directory
        out_dir = FIGURES_DIR / ep_label.lower() / track_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Generate panel for each timestep
        for t_idx in range(n_times):
            ds_t = ds.isel({tc: t_idx})
            # time value in NetCDF may be seconds since epoch
            tval = ds[tc].values[t_idx]
            time_ts = pd.to_datetime(tval)
            time_str = time_ts.strftime("%Y-%m-%d %H:%M UTC")

            # Determine cyclone center for this timestep (nearest track point)
            if tracks_df is not None and not tracks_df.empty:
                # Find nearest time in tracks_df
                diffs = (tracks_df["date"] - time_ts).abs()
                nearest = tracks_df.loc[diffs.idxmin()]
                cur_lat = float(nearest["lat vor"]) if "lat vor" in nearest.index else float(nearest.get("lat", center_lat))
                cur_lon = float(nearest["lon vor"]) if "lon vor" in nearest.index else float(nearest.get("lon", center_lon))
            else:
                # Use fixed center (previous behavior)
                cur_lat, cur_lon = center_lat, center_lon

            fig = create_panel_figure(ds_t, cur_lat, cur_lon, time_str, track_id)

            out_path = out_dir / f"panel_t{t_idx:03d}.png"
            fig.savefig(out_path, dpi=DPI, bbox_inches='tight')
            plt.close(fig)

        ds.close()
        return track_id, n_times, None

    except Exception as e:
        return track_id, 0, str(e)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate cyclone explorer panels")
    parser.add_argument("--jobs", "-j", type=int, default=1,
                       help="Number of parallel workers (default: 1)")
    parser.add_argument("--subset", "-s", type=int, default=None,
                       help="Process only first N cyclones per EP (for testing)")
    args = parser.parse_args()
    
    log_file = setup_logging()
    logging.info(f"   Parallel workers: {args.jobs}")
    if args.subset:
        logging.info(f"   Subset mode: {args.subset} cyclones per EP")
    
    # Load cases
    ep1_cases = pd.read_csv(RESULTS_DIR / "ep1_cases.csv")
    ep2_cases = pd.read_csv(RESULTS_DIR / "ep2_cases.csv")
    
    # Filter to only cases with ERA5 data available
    ep1_with_data = []
    for _, row in ep1_cases.iterrows():
        track_id = str(row['track_id'])
        if (DATA_DIR / f"{track_id}_era5.nc").exists():
            ep1_with_data.append(row)
    ep1_cases = pd.DataFrame(ep1_with_data) if ep1_with_data else pd.DataFrame()
    
    ep2_with_data = []
    for _, row in ep2_cases.iterrows():
        track_id = str(row['track_id'])
        if (DATA_DIR / f"{track_id}_era5.nc").exists():
            ep2_with_data.append(row)
    ep2_cases = pd.DataFrame(ep2_with_data) if ep2_with_data else pd.DataFrame()
    
    logging.info(f"   EP1 with ERA5 data: {len(ep1_cases)} cases")
    logging.info(f"   EP2 with ERA5 data: {len(ep2_cases)} cases")
    
    if args.subset:
        ep1_cases = ep1_cases.head(args.subset) if not ep1_cases.empty else ep1_cases
        ep2_cases = ep2_cases.head(args.subset) if not ep2_cases.empty else ep2_cases
    
    logging.info(f"   EP1: {len(ep1_cases)} cases")
    logging.info(f"   EP2: {len(ep2_cases)} cases")
    
    # Combine and prepare task list (track_id, ep_label, center_lat, center_lon)
    tasks = []
    for _, row in ep1_cases.iterrows():
        tasks.append((row['track_id'], 'EP1', row['center_lat'], row['center_lon']))
    for _, row in ep2_cases.iterrows():
        tasks.append((row['track_id'], 'EP2', row['center_lat'], row['center_lon']))
    
    logging.info(f"\n   Total tasks: {len(tasks)}")
    logging.info(f"   Output: {FIGURES_DIR}")
    
    # Process
    success = 0
    total_panels = 0
    failed = []
    
    if args.jobs == 1:
        # Sequential
        for task in tqdm(tasks, desc="Generating panels"):
            tid, n_panels, error = process_one_cyclone(task)
            if error:
                failed.append((tid, error))
            else:
                success += 1
                total_panels += n_panels
    else:
        # Parallel
        with ProcessPoolExecutor(max_workers=args.jobs) as executor:
            futures = {executor.submit(process_one_cyclone, task): task[0] 
                      for task in tasks}
            
            for future in tqdm(as_completed(futures), total=len(tasks), 
                             desc="Generating panels"):
                tid, n_panels, error = future.result()
                if error:
                    failed.append((tid, error))
                else:
                    success += 1
                    total_panels += n_panels
    
    # Summary
    logging.info("\n" + "=" * 70)
    logging.info("SUMMARY")
    logging.info("=" * 70)
    logging.info(f"   Success: {success}/{len(tasks)} cyclones")
    logging.info(f"   Total panels generated: {total_panels}")
    logging.info(f"   Failed: {len(failed)}")
    
    if failed and len(failed) <= 20:
        logging.info("\n   Failed cases:")
        for tid, error in failed:
            logging.info(f"     {tid}: {error}")
    
    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 6 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"Log: {log_file}")
    logging.info(f"\nNext: python scripts/web/extract_cyclone_explorer_data.py")


if __name__ == "__main__":
    main()
