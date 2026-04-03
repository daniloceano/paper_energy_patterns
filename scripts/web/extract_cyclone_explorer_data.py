"""
Extract Cyclone Explorer Data for Web

Generates manifest JSON files for the cyclone temporal explorer feature.
For each EP1/EP2 cyclone with available ERA5 data, creates a structured
manifest linking:
  - Full track coordinates and lifecycle phases
  - Intensification timesteps
  - Generated panel figures
  - Track point indices corresponding to each timestep

This is a SERIALIZER/INDEXER only — does NOT recompute science or generate figures.

Data sources:
  - results/ep_structure/ep{1,2}_cases.csv → case list + intensification metadata
  - GitHub tracks CSV → full track coordinates
  - figures/cyclone_explorer/{ep_label}/{track_id}/ → pre-generated panels
  - data/era5_ep_structure/{track_id}_era5.nc → timestep timestamps

Usage:
  python scripts/web/extract_cyclone_explorer_data.py
  python scripts/web/extract_cyclone_explorer_data.py --subset 10

Outputs:
  web/src/content/cyclone_explorer_manifest.json

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import argparse
import json
import os
import pandas as pd
import xarray as xr
import numpy as np
from datetime import datetime
from tqdm import tqdm

from scripts.utils.load_data import load_tracks

# ============================================================================
# CONFIGURATION
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = REPO_ROOT / "results" / "ep_structure"
FIGURES_DIR = REPO_ROOT / "figures" / "cyclone_explorer"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

DYNAMIC_PRODUCTS = [
    {
        "id": "slp_pv850_wind850",
        "label": "SLP + PV850 + wind850",
        "description": "Sea level pressure with potential vorticity and wind vectors at 850 hPa.",
    },
    {
        "id": "tadv_pv850_wind850",
        "label": "Temperature advection + PV850 + wind850",
        "description": "850 hPa temperature advection with PV and wind vectors.",
    },
    {
        "id": "afc_keadvanom_wind250",
        "label": "AFC250 + KE advection anomaly250 + wind250",
        "description": "Ageostrophic flux convergence and KE advection anomaly at 250 hPa with jet-level wind vectors.",
    },
    {
        "id": "rk_criterion_250",
        "label": "RK criterion at 250 hPa",
        "description": "Rayleigh-Kuo criterion map with 250 hPa flow context.",
    },
    {
        "id": "btcr_critical_region",
        "label": "Barotropic critical region",
        "description": "BtCR effective deformation and dilatation-axis structure at 250 hPa.",
    },
]

# Global tracks DataFrame (loaded once)
TRACKS_DF = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tracks_df():
    """Load tracks DataFrame (cached)."""
    global TRACKS_DF
    if TRACKS_DF is None:
        TRACKS_DF = load_tracks()
    return TRACKS_DF


def load_full_track(track_id):
    """
    Load full track from global tracks DataFrame.
    
    Returns
    -------
    dict with keys:
        - lats: list of floats
        - lons: list of floats
        - times: list of ISO strings
        - phase: list of phase labels (or None if not available)
        - slp: list of floats (or None if not available)
    or None if track not found
    """
    tracks_df = get_tracks_df()
    track_id_int = int(track_id)
    
    track_data = tracks_df[tracks_df["track_id"] == track_id_int].copy()
    
    if len(track_data) == 0:
        return None
    
    try:
        result = {
            "lats": track_data["lat vor"].tolist(),
            "lons": track_data["lon vor"].tolist(),
            "times": pd.to_datetime(track_data["date"]).dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
        }
        
        # Optional: phase information
        if "phase" in track_data.columns:
            result["phase"] = track_data["phase"].tolist()
        else:
            result["phase"] = None
        
        # Optional: SLP
        if "msl (Pa)" in track_data.columns:
            result["slp"] = (track_data["msl (Pa)"] / 100).tolist()  # Pa to hPa
        elif "slp" in track_data.columns:
            result["slp"] = track_data["slp"].tolist()
        else:
            result["slp"] = None
        
        return result
        
    except Exception as e:
        print(f"Warning: Failed to load track for {track_id}: {e}")
        return None


def find_track_indices_for_timesteps(track_times, intensification_times):
    """
    Match intensification timesteps to full track indices.
    
    Parameters
    ----------
    track_times : list of datetime-like
    intensification_times : list of datetime-like
    
    Returns
    -------
    list of int
        Track indices corresponding to each intensification timestep
    """
    # Convert to tz-naive datetime for comparison
    track_times = pd.to_datetime(track_times).tz_localize(None)
    intensification_times = pd.to_datetime(intensification_times)
    if intensification_times.tz is not None:
        intensification_times = intensification_times.tz_localize(None)
    
    indices = []
    for t in intensification_times:
        # Find closest match in track
        if hasattr(t, 'tz_localize'):
            t = t.tz_localize(None) if t.tzinfo is not None else t
        diffs = np.abs((track_times - t).total_seconds())
        idx = int(np.argmin(diffs))
        indices.append(idx)
    
    return indices


def supabase_base_from_env():
    """Return figures base URL when provided via env vars."""
    base = os.environ.get("SUPABASE_FIGURES_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_FIGURES_URL")
    if base:
        return base.rstrip("/")
    return None


def as_public_url(path_or_none, supabase_base):
    """Convert figures/<...> path into public URL when Supabase base is set."""
    if path_or_none is None:
        return None
    if not supabase_base:
        return path_or_none
    if path_or_none.startswith("http://") or path_or_none.startswith("https://"):
        return path_or_none
    bucket_rel = path_or_none.replace("figures/", "", 1)
    return f"{supabase_base}/{bucket_rel}"


def extract_cyclone_data(track_id, ep_label, supabase_base=None):
    """
    Extract all data for one cyclone.
    
    Returns
    -------
    dict or None
    """
    # Convert track_id to string if needed
    track_id = str(track_id)
    
    # Check if ERA5 data exists
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    if not nc_file.exists():
        return None
    
    # Load full track
    track = load_full_track(track_id)
    if track is None:
        return None
    
    # Load intensification metadata from cases CSV
    cases_file = RESULTS_DIR / f"{ep_label.lower()}_cases.csv"
    cases_df = pd.read_csv(cases_file)
    case_row = cases_df[cases_df['track_id'] == int(track_id)]
    
    if len(case_row) == 0:
        return None
    
    case_row = case_row.iloc[0]
    
    # Get timesteps from NetCDF
    try:
        ds = xr.open_dataset(nc_file)
        tc = "valid_time" if "valid_time" in ds.dims else "time"
        timestep_times = pd.to_datetime(ds[tc].values)
        n_timesteps = len(timestep_times)
        
        # Available fields
        available_fields = list(ds.data_vars)
        ds.close()
    except Exception as e:
        print(f"Warning: Failed to read {nc_file}: {e}")
        return None
    
    # Find track indices for each timestep
    track_indices = find_track_indices_for_timesteps(track["times"], timestep_times)
    
    # Check which panels exist
    panel_dir = FIGURES_DIR / ep_label.lower() / track_id
    panels_exist = panel_dir.exists()
    
    # Build timesteps list
    timesteps = []
    for t_idx, (time, track_idx) in enumerate(zip(timestep_times, track_indices)):
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        panel_path = None
        synoptic_basic = None
        dynamic_images = {}

        if panels_exist:
            # Legacy synoptic path (kept for backward compatibility)
            panel_file = panel_dir / f"panel_t{t_idx:03d}.png"
            if panel_file.exists():
                panel_path = f"figures/cyclone_explorer/{ep_label.lower()}/{track_id}/panel_t{t_idx:03d}.png"

            # Explicit synoptic category path
            syn_file = panel_dir / "synoptic_fields" / f"panel_t{t_idx:03d}.png"
            if syn_file.exists():
                synoptic_basic = f"figures/cyclone_explorer/{ep_label.lower()}/{track_id}/synoptic_fields/panel_t{t_idx:03d}.png"
            else:
                synoptic_basic = panel_path

            # Dynamic category paths
            for product in DYNAMIC_PRODUCTS:
                pid = product["id"]
                dyn_file = panel_dir / "dynamic_fields" / pid / f"panel_t{t_idx:03d}.png"
                dynamic_images[pid] = (
                    f"figures/cyclone_explorer/{ep_label.lower()}/{track_id}/dynamic_fields/{pid}/panel_t{t_idx:03d}.png"
                    if dyn_file.exists()
                    else None
                )
        
        timesteps.append({
            "index": t_idx,
            "time": time_str,
            "track_point_index": track_idx,
            "panel_image": as_public_url(panel_path, supabase_base),
            "has_panel": panel_path is not None,
            "images": {
                "synoptic": {
                    "basic": as_public_url(synoptic_basic, supabase_base),
                },
                "dynamic": {
                    pid: as_public_url(dynamic_images.get(pid), supabase_base)
                    for pid in [p["id"] for p in DYNAMIC_PRODUCTS]
                },
            },
        })
    
    # Build cyclone entry
    cyclone_data = {
        "track_id": track_id,
        "ep_label": ep_label,
        "metadata": {
            "intensification_start": case_row["intensification_start"],
            "intensification_end": case_row["intensification_end"],
            "duration_hours": float(case_row["duration_hours"]),
            "n_timesteps": n_timesteps,
            "center_lat": float(case_row["center_lat"]),
            "center_lon": float(case_row["center_lon"]),
        },
        "track": track,
        "timesteps": timesteps,
        "available_fields": available_fields,
    }
    
    return cyclone_data


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Extract cyclone explorer data for web")
    parser.add_argument("--subset", "-s", type=int, default=None,
                       help="Process only first N cyclones per EP (for testing)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("EXTRACT CYCLONE EXPLORER DATA FOR WEB")
    print("=" * 60)
    
    if args.subset:
        print(f"Subset mode: {args.subset} cyclones per EP")

    supabase_base = supabase_base_from_env()
    if supabase_base:
        print(f"Supabase figures base detected: {supabase_base}")
    
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
    
    if args.subset:
        ep1_cases = ep1_cases.head(args.subset) if not ep1_cases.empty else ep1_cases
        ep2_cases = ep2_cases.head(args.subset) if not ep2_cases.empty else ep2_cases
    
    print(f"\nProcessing:")
    print(f"  EP1: {len(ep1_cases)} cases")
    print(f"  EP2: {len(ep2_cases)} cases")
    
    # Extract data for each cyclone
    cyclones = {}
    ep1_count = 0
    ep2_count = 0
    
    print("\nExtracting EP1 cyclones...")
    for _, row in tqdm(ep1_cases.iterrows(), total=len(ep1_cases), desc="EP1"):
        track_id = row['track_id']
        data = extract_cyclone_data(track_id, "EP1", supabase_base=supabase_base)
        if data:
            cyclones[track_id] = data
            ep1_count += 1
    
    print("\nExtracting EP2 cyclones...")
    for _, row in tqdm(ep2_cases.iterrows(), total=len(ep2_cases), desc="EP2"):
        track_id = row['track_id']
        data = extract_cyclone_data(track_id, "EP2", supabase_base=supabase_base)
        if data:
            cyclones[track_id] = data
            ep2_count += 1
    
    # Build manifest
    manifest = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_cyclones": len(cyclones),
            "ep1_count": ep1_count,
            "ep2_count": ep2_count,
            "field_groups": ["synoptic", "dynamic"],
            "synoptic_products": [
                {
                    "id": "basic",
                    "label": "Synoptic fields",
                    "description": "SLP, temperature, specific humidity and geopotential diagnostics in the cyclone-centered panel.",
                }
            ],
            "dynamic_products": DYNAMIC_PRODUCTS,
            "figures_base_url": supabase_base,
        },
        "cyclones": cyclones
    }
    
    # Write manifest
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)
    manifest_path = WEB_CONTENT / "cyclone_explorer_manifest.json"
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total cyclones: {len(cyclones)}")
    print(f"  EP1: {ep1_count}")
    print(f"  EP2: {ep2_count}")
    print(f"\n  ✓ Manifest: {manifest_path.relative_to(REPO_ROOT)}")
    
    # Calculate statistics
    total_timesteps = sum(len(c["timesteps"]) for c in cyclones.values())
    timesteps_with_panels = sum(
        sum(1 for ts in c["timesteps"] if ts["has_panel"])
        for c in cyclones.values()
    )
    
    print(f"\n  Total timesteps: {total_timesteps}")
    print(f"  Timesteps with panels: {timesteps_with_panels}")
    if total_timesteps > 0:
        print(f"  Coverage: {timesteps_with_panels/total_timesteps*100:.1f}%")
    else:
        print(f"  Coverage: N/A (no timesteps)")
    
    print("\n" + "=" * 60)
    print("✓ DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
