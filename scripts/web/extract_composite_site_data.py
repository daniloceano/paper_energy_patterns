#!/usr/bin/env python3
"""
Extract composite analysis data for the web site.

Reads pre-computed ERA5 composites from data/era5_ep_structure/ and generates
domain statistics and boundary flux tables for each diagnostic.

This script requires xarray and netCDF4. It reads the pre-computed NetCDF
composite files and extracts:
  1. Inside/outside 15x15 domain mean values
  2. Boundary flux values (N/S/E/W) for flux/advection diagnostics
  3. Summary statistics for each diagnostic

Usage:
    python scripts/web/extract_composite_site_data.py

Outputs:
    web/src/content/composite_domain_stats.json
    web/src/content/composite_boundary_fluxes.json
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "era5_ep_structure"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

# Diagnostic variable names as they appear in the NetCDF files.
# These must match the variable names in precomputed_composites_ep*.nc.
# Update this mapping if the NetCDF variable names differ.
DIAGNOSTIC_VARS = {
    "egr": "egr",
    "pv_200": "pv_200",
    "pv_850": "pv_850",
    "temperature_advection": "adv_T_850",
    "moisture_flux_divergence": "div_q_975",
    "slp": "msl",
    "rk_criterion": "rk_criterion_250",
    "ke_advection": "ke_adv_250",
    "afc": "afc_250",
}

# Anomaly variable names (where available)
DIAGNOSTIC_ANOM_VARS = {
    "pv_200": "pv_200_anom",
    "pv_850": "pv_850_anom",
    "temperature_advection": "adv_T_850_anom",
    "moisture_flux_divergence": "div_q_975_anom",
    "slp": "msl_anom",
    "ke_advection": "ke_adv_250_anom",
}

# Diagnostics that involve flux/advection and need boundary tables
FLUX_DIAGNOSTICS = [
    "temperature_advection",
    "moisture_flux_divergence",
    "ke_advection",
    "afc",
]

# Inner domain definition: 15x15 degrees centred on the cyclone
# For a 30x30 domain at 0.25° resolution (120x120 grid points):
#   Full domain: indices 0..119
#   Inner 15x15: indices 30..89 (central 60 grid points)
INNER_START = 30
INNER_END = 90  # exclusive


def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def extract_stats():
    """Extract domain statistics and boundary fluxes from NetCDF composites."""
    domain_stats = []
    boundary_fluxes = []

    try:
        import xarray as xr
    except ImportError:
        print("  ⚠ xarray not available. Generating placeholder outputs.")
        _write_placeholders()
        return

    for ep_label, ep_file in [
        ("EP1", DATA_DIR / "precomputed_composites_ep1.nc"),
        ("EP2", DATA_DIR / "precomputed_composites_ep2.nc"),
    ]:
        if not ep_file.exists():
            print(f"  ⚠ {ep_file.name} not found, skipping {ep_label}")
            continue

        ds = xr.open_dataset(ep_file)

        for diag_key, var_name in DIAGNOSTIC_VARS.items():
            if var_name not in ds:
                print(f"  ⚠ Variable '{var_name}' not in {ep_file.name}")
                continue

            field = ds[var_name]

            # Compute domain means
            # Assuming the field has dimensions (lat, lon) or similar 2D
            dims = field.dims
            if len(dims) < 2:
                continue

            values = field.values
            if values.ndim == 2:
                ny, nx = values.shape
            else:
                # Take first slice if there are extra dimensions
                values = values.squeeze()
                if values.ndim != 2:
                    continue
                ny, nx = values.shape

            # Recompute inner boundaries based on actual grid size
            inner_y_start = ny // 4
            inner_y_end = 3 * ny // 4
            inner_x_start = nx // 4
            inner_x_end = 3 * nx // 4

            # Inside 15x15 mean
            inside = values[inner_y_start:inner_y_end, inner_x_start:inner_x_end]
            inside_mean = float(inside.mean()) if inside.size > 0 else None

            # Outside 15x15 mean (full domain minus inner)
            import numpy as np
            mask = np.ones_like(values, dtype=bool)
            mask[inner_y_start:inner_y_end, inner_x_start:inner_x_end] = False
            outside = values[mask]
            outside_mean = float(outside.mean()) if outside.size > 0 else None

            domain_stats.append({
                "diagnostic": diag_key,
                "energy_pattern": ep_label,
                "inside_mean": inside_mean,
                "outside_mean": outside_mean,
                "inside_std": float(inside.std()) if inside.size > 0 else None,
                "outside_std": float(outside.std()) if outside.size > 0 else None,
                "unit": str(ds[var_name].attrs.get("units", "")),
            })

            # Boundary fluxes for flux/advection diagnostics
            if diag_key in FLUX_DIAGNOSTICS:
                north = float(values[inner_y_start, inner_x_start:inner_x_end].mean())
                south = float(values[inner_y_end - 1, inner_x_start:inner_x_end].mean())
                east = float(values[inner_y_start:inner_y_end, inner_x_end - 1].mean())
                west = float(values[inner_y_start:inner_y_end, inner_x_start].mean())

                boundary_fluxes.append({
                    "diagnostic": diag_key,
                    "energy_pattern": ep_label,
                    "north": north,
                    "south": south,
                    "east": east,
                    "west": west,
                    "unit": str(ds[var_name].attrs.get("units", "")),
                })

        ds.close()

    # Write outputs
    stats_path = WEB_CONTENT / "composite_domain_stats.json"
    with open(stats_path, "w") as f:
        json.dump(domain_stats, f, indent=2)
    print(f"  ✓ {stats_path.relative_to(REPO_ROOT)} ({len(domain_stats)} entries)")

    fluxes_path = WEB_CONTENT / "composite_boundary_fluxes.json"
    with open(fluxes_path, "w") as f:
        json.dump(boundary_fluxes, f, indent=2)
    print(f"  ✓ {fluxes_path.relative_to(REPO_ROOT)} ({len(boundary_fluxes)} entries)")


def _write_placeholders():
    """Write empty placeholder files when xarray is not available."""
    for filename in ["composite_domain_stats.json", "composite_boundary_fluxes.json"]:
        path = WEB_CONTENT / filename
        with open(path, "w") as f:
            json.dump([], f, indent=2)
        print(f"  ✓ {path.relative_to(REPO_ROOT)} (placeholder)")


def main():
    print("Extracting composite analysis data for site...")
    ensure_output_dir()
    extract_stats()
    print("Done.")


if __name__ == "__main__":
    main()
