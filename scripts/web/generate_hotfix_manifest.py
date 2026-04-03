"""
Hotfix: Generate subset manifest for Cyclone Explorer

Generates a lightweight manifest with only 10 cyclones per EP for deployment.
Selects cyclones with best storm-centering (lowest mean distance to domain center).

This is a TEMPORARY hotfix to reduce bundle size for Vercel deployment.

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import json
import pandas as pd
from datetime import datetime
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
WEB_CONTENT = PROJECT_ROOT / "web" / "src" / "content"
FIGURES_DIR = PROJECT_ROOT / "figures" / "cyclone_explorer"

# Subset selection
HOTFIX_SELECTION_FILE = RESULTS_DIR / "hotfix_subset_selection.csv"

# Track data
TRACKS_FILE = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"

from scripts.utils.load_data import load_tracks

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def load_full_tracks():
    """Load full track data."""
    return load_tracks()


def get_case_metadata(track_id: str, ep_label: str, cases_df: pd.DataFrame) -> dict:
    """Get intensification metadata for a cyclone."""
    row = cases_df[cases_df["track_id"] == int(track_id)]
    if row.empty:
        return None
    row = row.iloc[0]
    return {
        "intensification_start": str(row["intensification_start"]),
        "intensification_end": str(row["intensification_end"]),
        "duration_hours": float(row["duration_hours"]),
        "n_timesteps": int(row["n_timesteps"]),
        "center_lat": float(row["center_lat"]),
        "center_lon": float(row["center_lon"]),
    }


def get_track_coordinates(track_id: str, tracks_df: pd.DataFrame) -> dict:
    """Extract track coordinates for a cyclone."""
    t = tracks_df[tracks_df["track_id"] == int(track_id)]
    if t.empty:
        return {"lats": [], "lons": []}
    return {
        "lats": t["lat vor"].tolist() if "lat vor" in t.columns else t["lat"].tolist(),
        "lons": t["lon vor"].tolist() if "lon vor" in t.columns else t["lon"].tolist(),
    }


def get_timestep_info(track_id: str, ep_label: str, tracks_df: pd.DataFrame) -> list:
    """Get timestep information including panel availability."""
    import xarray as xr
    
    nc_file = DATA_DIR / f"{track_id}_era5.nc"
    if not nc_file.exists():
        return []
    
    ds = xr.open_dataset(nc_file)
    tc = "valid_time" if "valid_time" in ds.dims else "time"
    times = ds[tc].values
    ds.close()
    
    # Get track data for matching
    t = tracks_df[tracks_df["track_id"] == int(track_id)]
    if not t.empty and "date" in t.columns:
        t = t.copy()
        t["date"] = pd.to_datetime(t["date"])
    
    # Panel base directory
    panel_dir = FIGURES_DIR / ep_label.lower() / track_id
    
    timesteps = []
    for idx, tval in enumerate(times):
        time_ts = pd.to_datetime(tval)
        time_str = time_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Find track point index
        track_point_index = 0
        if not t.empty:
            diffs = (t["date"] - time_ts).abs()
            nearest_idx = diffs.idxmin()
            track_point_index = t.index.get_loc(nearest_idx) if isinstance(t.index, pd.RangeIndex) else list(t.index).index(nearest_idx)
        
        # Check panel availability
        panel_file = f"panel_t{idx:03d}.png"
        legacy_path = panel_dir / panel_file
        has_panel = legacy_path.exists()
        
        # Build image paths
        images = {
            "synoptic": {"basic": None},
            "dynamic": {}
        }
        
        # Synoptic
        syn_path = panel_dir / "synoptic_fields" / panel_file
        if syn_path.exists():
            images["synoptic"]["basic"] = f"figures/cyclone_explorer/{ep_label.lower()}/{track_id}/synoptic_fields/{panel_file}"
        
        # Dynamic products
        for product in DYNAMIC_PRODUCTS:
            dyn_path = panel_dir / "dynamic_fields" / product["id"] / panel_file
            if dyn_path.exists():
                images["dynamic"][product["id"]] = f"figures/cyclone_explorer/{ep_label.lower()}/{track_id}/dynamic_fields/{product['id']}/{panel_file}"
        
        timesteps.append({
            "index": idx,
            "time": time_str,
            "track_point_index": track_point_index,
            "panel_image": f"figures/cyclone_explorer/{ep_label.lower()}/{track_id}/{panel_file}" if has_panel else None,
            "has_panel": has_panel,
            "images": images,
        })
    
    return timesteps


def main():
    logging.info("=" * 70)
    logging.info("HOTFIX: GENERATE SUBSET MANIFEST")
    logging.info("=" * 70)
    
    # Load selection
    if not HOTFIX_SELECTION_FILE.exists():
        logging.error(f"Selection file not found: {HOTFIX_SELECTION_FILE}")
        logging.error("Run storm centering audit first to generate selection.")
        return
    
    selection = pd.read_csv(HOTFIX_SELECTION_FILE)
    selected_tracks = set(selection["track_id"].astype(str).tolist())
    
    logging.info(f"Selected {len(selected_tracks)} cyclones for hotfix subset")
    
    # Load case data
    ep1_cases = pd.read_csv(RESULTS_DIR / "ep1_cases.csv")
    ep2_cases = pd.read_csv(RESULTS_DIR / "ep2_cases.csv")
    
    # Load tracks
    tracks_df = load_full_tracks()
    
    # Build manifest
    manifest = {
        "metadata": {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_cyclones": len(selected_tracks),
            "ep1_count": len(selection[selection["ep_label"] == "EP1"]),
            "ep2_count": len(selection[selection["ep_label"] == "EP2"]),
            "field_groups": ["synoptic", "dynamic"],
            "synoptic_products": [
                {
                    "id": "basic",
                    "label": "Synoptic fields",
                    "description": "SLP, temperature, specific humidity and geopotential diagnostics in the cyclone-centered panel."
                }
            ],
            "dynamic_products": DYNAMIC_PRODUCTS,
            "figures_base_url": None,
            "is_hotfix_subset": True,
            "hotfix_note": "This manifest contains a curated subset of 10 cyclones per EP selected for best storm-centering. Full dataset will be available after infrastructure improvements.",
        },
        "cyclones": {}
    }
    
    # Process each selected cyclone
    for _, row in selection.iterrows():
        track_id = str(row["track_id"])
        ep_label = row["ep_label"]
        
        cases_df = ep1_cases if ep_label == "EP1" else ep2_cases
        
        metadata = get_case_metadata(track_id, ep_label, cases_df)
        if metadata is None:
            logging.warning(f"No metadata for {track_id}")
            continue
        
        track = get_track_coordinates(track_id, tracks_df)
        timesteps = get_timestep_info(track_id, ep_label, tracks_df)
        
        manifest["cyclones"][track_id] = {
            "track_id": track_id,
            "ep_label": ep_label,
            "metadata": metadata,
            "track": track,
            "timesteps": timesteps,
            "available_fields": ["synoptic", "dynamic"],
        }
        
        n_panels = sum(1 for ts in timesteps if ts["has_panel"])
        logging.info(f"  {ep_label} {track_id}: {n_panels} panels")
    
    # Save manifest
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)
    manifest_path = WEB_CONTENT / "cyclone_explorer_manifest.json"
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logging.info(f"\nSaved manifest: {manifest_path}")
    logging.info(f"Manifest size: {manifest_path.stat().st_size / 1024:.1f} KB")
    
    # Summary
    logging.info("\n" + "=" * 70)
    logging.info("HOTFIX MANIFEST COMPLETE")
    logging.info("=" * 70)
    logging.info(f"EP1 cyclones: {manifest['metadata']['ep1_count']}")
    logging.info(f"EP2 cyclones: {manifest['metadata']['ep2_count']}")
    logging.info(f"Total cyclones: {manifest['metadata']['total_cyclones']}")


if __name__ == "__main__":
    main()
