"""
Step 5: Update Scientific Notes for EP Structure Analysis

Populates SCIENTIFIC_NOTES.md with statistics computed from the
precomputed composite files. Generates PDF by default.

Usage:
    python step5_update_scientific_notes.py          # Update notes + generate PDF
    python step5_update_scientific_notes.py --no-pdf # Update notes only

Output:
    - SCIENTIFIC_NOTES.md (updated with statistics)
    - docs/scientific_notes_ep_structure.pdf (default)

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import argparse
import json
import subprocess
import numpy as np
import xarray as xr
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPT_DIR = Path(__file__).resolve().parent
NOTES_FILE = SCRIPT_DIR / "SCIENTIFIC_NOTES.md"

# Domain definitions for regional statistics
DOMAIN_FULL = 30.0  # degrees
DOMAIN_LEC = 15.0   # degrees
HALF_LEC = DOMAIN_LEC / 2.0


def get_domain_mask(x, y, x_min, x_max, y_min, y_max):
    """Create boolean mask for a rectangular domain."""
    return (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)


def compute_regional_stats(data, x, y):
    """Compute statistics for different regions.
    
    Returns dict with keys:
      - full30: Full 30×30° domain
      - lec15: Central 15×15° LEC domain  
      - lec15_NW, lec15_NE, lec15_SW, lec15_SE: Quadrants
    """
    stats = {}
    
    # Full 30×30° domain
    stats['full30'] = np.nanmean(data)
    
    # Central 15×15° LEC domain
    mask_lec = get_domain_mask(x, y, -HALF_LEC, HALF_LEC, -HALF_LEC, HALF_LEC)
    stats['lec15'] = np.nanmean(data[mask_lec])
    
    # Quadrants of 15×15° domain
    # NW: x<0, y>0
    mask_nw = get_domain_mask(x, y, -HALF_LEC, 0, 0, HALF_LEC)
    stats['lec15_NW'] = np.nanmean(data[mask_nw])
    
    # NE: x>0, y>0
    mask_ne = get_domain_mask(x, y, 0, HALF_LEC, 0, HALF_LEC)
    stats['lec15_NE'] = np.nanmean(data[mask_ne])
    
    # SW: x<0, y<0
    mask_sw = get_domain_mask(x, y, -HALF_LEC, 0, -HALF_LEC, 0)
    stats['lec15_SW'] = np.nanmean(data[mask_sw])
    
    # SE: x>0, y<0
    mask_se = get_domain_mask(x, y, 0, HALF_LEC, -HALF_LEC, 0)
    stats['lec15_SE'] = np.nanmean(data[mask_se])
    
    return stats


def compute_boundary_stats(data, x, y):
    """Compute statistics along boundaries of LEC 15×15° domain.
    
    Useful for flux/advection fields to assess lateral transport.
    
    Returns dict with keys:
      - north: Mean along northern boundary (y = +7.5°, -7.5° ≤ x ≤ +7.5°)
      - south: Mean along southern boundary (y = -7.5°, -7.5° ≤ x ≤ +7.5°)
      - east: Mean along eastern boundary (x = +7.5°, -7.5° ≤ y ≤ +7.5°)
      - west: Mean along western boundary (x = -7.5°, -7.5° ≤ y ≤ +7.5°)
    """
    stats = {}
    
    # Tolerance for boundary selection (half grid spacing)
    tol = 0.25  # degrees (ERA5 resolution)
    
    # Northern boundary: y ≈ +HALF_LEC
    mask_north = (np.abs(y - HALF_LEC) < tol) & (x >= -HALF_LEC) & (x <= HALF_LEC)
    stats['north'] = np.nanmean(data[mask_north]) if np.any(mask_north) else np.nan
    
    # Southern boundary: y ≈ -HALF_LEC
    mask_south = (np.abs(y + HALF_LEC) < tol) & (x >= -HALF_LEC) & (x <= HALF_LEC)
    stats['south'] = np.nanmean(data[mask_south]) if np.any(mask_south) else np.nan
    
    # Eastern boundary: x ≈ +HALF_LEC
    mask_east = (np.abs(x - HALF_LEC) < tol) & (y >= -HALF_LEC) & (y <= HALF_LEC)
    stats['east'] = np.nanmean(data[mask_east]) if np.any(mask_east) else np.nan
    
    # Western boundary: x ≈ -HALF_LEC
    mask_west = (np.abs(x + HALF_LEC) < tol) & (y >= -HALF_LEC) & (y <= HALF_LEC)
    stats['west'] = np.nanmean(data[mask_west]) if np.any(mask_west) else np.nan
    
    return stats


def load_stats():
    """Compute summary statistics from precomputed composites.
    
    Includes both global and regional statistics:
    - Full 30×30° domain
    - Central 15×15° LEC domain
    - Four quadrants (NW, NE, SW, SE) of LEC domain
    """
    stats = {}

    for ep in ["ep1", "ep2"]:
        f = DATA_DIR / f"precomputed_composites_{ep}.nc"
        if not f.exists():
            print(f"⚠️  Missing {f.name} — skipping {ep.upper()}")
            continue

        ds = xr.open_dataset(f)
        label = ep.upper()

        # Get coordinates for regional masks
        x = ds.coords['x'].values
        y = ds.coords['y'].values
        x_2d, y_2d = np.meshgrid(x, y)

        n = int(ds.attrs.get("n_cases", 0))
        stats[f"{label}_N_CASES"] = str(n)

        # === EGR ===
        egr = ds["egr"].values
        stats[f"{label}_EGR_MEAN"] = f"{np.nanmean(egr):.2f}"
        stats[f"{label}_EGR_STD"] = f"{np.nanstd(egr):.2f}"
        stats[f"{label}_EGR_MEDIAN"] = f"{np.nanmedian(egr):.2f}"
        stats[f"{label}_EGR_MIN"] = f"{np.nanmin(egr):.2f}"
        stats[f"{label}_EGR_MAX"] = f"{np.nanmax(egr):.2f}"
        
        # Regional stats for EGR
        egr_regional = compute_regional_stats(egr, x_2d, y_2d)
        stats[f"{label}_EGR_FULL30"] = f"{egr_regional['full30']:.2f}"
        stats[f"{label}_EGR_LEC15"] = f"{egr_regional['lec15']:.2f}"
        stats[f"{label}_EGR_LEC15_NW"] = f"{egr_regional['lec15_NW']:.2f}"
        stats[f"{label}_EGR_LEC15_NE"] = f"{egr_regional['lec15_NE']:.2f}"
        stats[f"{label}_EGR_LEC15_SW"] = f"{egr_regional['lec15_SW']:.2f}"
        stats[f"{label}_EGR_LEC15_SE"] = f"{egr_regional['lec15_SE']:.2f}"

        # === PV 200 (PVU) ===
        pv200 = ds["pv_200"].values * 1e6
        stats[f"{label}_PV200_MEAN"] = f"{np.nanmean(pv200):.2f}"
        stats[f"{label}_PV200_MIN"] = f"{np.nanmin(pv200):.2f}"
        stats[f"{label}_PV200_MAX"] = f"{np.nanmax(pv200):.2f}"
        
        pv200_regional = compute_regional_stats(pv200, x_2d, y_2d)
        stats[f"{label}_PV200_FULL30"] = f"{pv200_regional['full30']:.2f}"
        stats[f"{label}_PV200_LEC15"] = f"{pv200_regional['lec15']:.2f}"

        # === PV 850 (PVU) ===
        pv850 = ds["pv_850"].values * 1e6
        stats[f"{label}_PV850_MEAN"] = f"{np.nanmean(pv850):.2f}"
        stats[f"{label}_PV850_MIN"] = f"{np.nanmin(pv850):.2f}"
        stats[f"{label}_PV850_MAX"] = f"{np.nanmax(pv850):.2f}"
        
        pv850_regional = compute_regional_stats(pv850, x_2d, y_2d)
        stats[f"{label}_PV850_FULL30"] = f"{pv850_regional['full30']:.2f}"
        stats[f"{label}_PV850_LEC15"] = f"{pv850_regional['lec15']:.2f}"

        # === Temperature advection (K/h) ===
        advT = ds["adv_T_850"].values * 3600
        stats[f"{label}_ADVT_MEAN"] = f"{np.nanmean(advT):.3f}"
        stats[f"{label}_ADVT_MAX_WARM"] = f"{np.nanmax(advT):.3f}"
        stats[f"{label}_ADVT_MAX_COLD"] = f"{np.nanmin(advT):.3f}"
        
        advT_regional = compute_regional_stats(advT, x_2d, y_2d)
        stats[f"{label}_ADVT_FULL30"] = f"{advT_regional['full30']:.3f}"
        stats[f"{label}_ADVT_LEC15"] = f"{advT_regional['lec15']:.3f}"
        
        # Boundary values for temperature advection (flux field)
        advT_boundary = compute_boundary_stats(advT, x_2d, y_2d)
        stats[f"{label}_ADVT_NORTH"] = f"{advT_boundary['north']:.3f}"
        stats[f"{label}_ADVT_SOUTH"] = f"{advT_boundary['south']:.3f}"
        stats[f"{label}_ADVT_EAST"] = f"{advT_boundary['east']:.3f}"
        stats[f"{label}_ADVT_WEST"] = f"{advT_boundary['west']:.3f}"

        # === Temperature advection anomaly @ 850 hPa ===
        if "adv_T_850_anom" in ds:
            advT_a = ds["adv_T_850_anom"].values * 3600
            advT_a_regional = compute_regional_stats(advT_a, x_2d, y_2d)
            stats[f"{label}_ADVT_ANOM_FULL30"] = f"{advT_a_regional['full30']:.3f}"
            stats[f"{label}_ADVT_ANOM_LEC15"]  = f"{advT_a_regional['lec15']:.3f}"
            advT_a_boundary = compute_boundary_stats(advT_a, x_2d, y_2d)
            stats[f"{label}_ADVT_ANOM_NORTH"] = f"{advT_a_boundary['north']:.3f}"
            stats[f"{label}_ADVT_ANOM_SOUTH"] = f"{advT_a_boundary['south']:.3f}"
            stats[f"{label}_ADVT_ANOM_EAST"]  = f"{advT_a_boundary['east']:.3f}"
            stats[f"{label}_ADVT_ANOM_WEST"]  = f"{advT_a_boundary['west']:.3f}"

        # === Specific humidity @ 975 hPa ===
        if "q_975" in ds:
            q975 = ds["q_975"].values * 1000  # kg/kg to g/kg
            stats[f"{label}_Q975_MEAN"] = f"{np.nanmean(q975):.2f}"
            stats[f"{label}_Q975_MIN"] = f"{np.nanmin(q975):.2f}"
            stats[f"{label}_Q975_MAX"] = f"{np.nanmax(q975):.2f}"
            
            q975_regional = compute_regional_stats(q975, x_2d, y_2d)
            stats[f"{label}_Q975_FULL30"] = f"{q975_regional['full30']:.2f}"
            stats[f"{label}_Q975_LEC15"] = f"{q975_regional['lec15']:.2f}"

        # === Moisture flux divergence @ 975 hPa ===
        # Variable is "div_q_975" in NetCDF (step3 output); "div_qflux_975" was an alias — use correct name
        divq_var = "div_q_975" if "div_q_975" in ds else ("div_qflux_975" if "div_qflux_975" in ds else None)
        if divq_var is not None:
            div_q = ds[divq_var].values * 1000 * 3600  # kg/kg/s to g/kg/h
            stats[f"{label}_DIVQ_MEAN"] = f"{np.nanmean(div_q):.3e}"
            stats[f"{label}_DIVQ_MIN"] = f"{np.nanmin(div_q):.3e}"
            stats[f"{label}_DIVQ_MAX"] = f"{np.nanmax(div_q):.3e}"
            
            div_q_regional = compute_regional_stats(div_q, x_2d, y_2d)
            stats[f"{label}_DIVQ_FULL30"] = f"{div_q_regional['full30']:.3e}"
            stats[f"{label}_DIVQ_LEC15"] = f"{div_q_regional['lec15']:.3e}"
            
            # Boundary values for moisture flux divergence (flux field)
            div_q_boundary = compute_boundary_stats(div_q, x_2d, y_2d)
            stats[f"{label}_DIVQ_NORTH"] = f"{div_q_boundary['north']:.3e}"
            stats[f"{label}_DIVQ_SOUTH"] = f"{div_q_boundary['south']:.3e}"
            stats[f"{label}_DIVQ_EAST"] = f"{div_q_boundary['east']:.3e}"
            stats[f"{label}_DIVQ_WEST"] = f"{div_q_boundary['west']:.3e}"

        # === Moisture flux divergence anomaly @ 975 hPa ===
        divq_anom_var = "div_q_975_anom" if "div_q_975_anom" in ds else None
        if divq_anom_var is not None:
            div_q_a = ds[divq_anom_var].values * 1000 * 3600
            div_q_a_regional = compute_regional_stats(div_q_a, x_2d, y_2d)
            stats[f"{label}_DIVQ_ANOM_FULL30"] = f"{div_q_a_regional['full30']:.3e}"
            stats[f"{label}_DIVQ_ANOM_LEC15"]  = f"{div_q_a_regional['lec15']:.3e}"
            div_q_a_boundary = compute_boundary_stats(div_q_a, x_2d, y_2d)
            stats[f"{label}_DIVQ_ANOM_NORTH"] = f"{div_q_a_boundary['north']:.3e}"
            stats[f"{label}_DIVQ_ANOM_SOUTH"] = f"{div_q_a_boundary['south']:.3e}"
            stats[f"{label}_DIVQ_ANOM_EAST"]  = f"{div_q_a_boundary['east']:.3e}"
            stats[f"{label}_DIVQ_ANOM_WEST"]  = f"{div_q_a_boundary['west']:.3e}"

        # === SLP ===
        if "msl" in ds:
            msl = ds["msl"].values / 100
            stats[f"{label}_SLP_MIN"] = f"{np.nanmin(msl):.1f}"
            stats[f"{label}_SLP_MAX"] = f"{np.nanmax(msl):.1f}"
            
            msl_regional = compute_regional_stats(msl, x_2d, y_2d)
            stats[f"{label}_SLP_FULL30"] = f"{msl_regional['full30']:.1f}"
            stats[f"{label}_SLP_LEC15"] = f"{msl_regional['lec15']:.1f}"

        # === KE advection @ 250 hPa (if available) ===
        if "ke_adv_250" in ds:
            ke_adv = ds["ke_adv_250"].values
            stats[f"{label}_KEADV_MEAN"] = f"{np.nanmean(ke_adv):.3e}"
            stats[f"{label}_KEADV_MIN"] = f"{np.nanmin(ke_adv):.3e}"
            stats[f"{label}_KEADV_MAX"] = f"{np.nanmax(ke_adv):.3e}"
            
            ke_adv_regional = compute_regional_stats(ke_adv, x_2d, y_2d)
            stats[f"{label}_KEADV_FULL30"] = f"{ke_adv_regional['full30']:.3e}"
            stats[f"{label}_KEADV_LEC15"] = f"{ke_adv_regional['lec15']:.3e}"
            
            # Boundary values for KE advection (flux field)
            ke_adv_boundary = compute_boundary_stats(ke_adv, x_2d, y_2d)
            stats[f"{label}_KEADV_NORTH"] = f"{ke_adv_boundary['north']:.3e}"
            stats[f"{label}_KEADV_SOUTH"] = f"{ke_adv_boundary['south']:.3e}"
            stats[f"{label}_KEADV_EAST"] = f"{ke_adv_boundary['east']:.3e}"
            stats[f"{label}_KEADV_WEST"] = f"{ke_adv_boundary['west']:.3e}"

        # === KE advection anomaly @ 250 hPa ===
        if "ke_adv_250_anom" in ds:
            ke_adv_a = ds["ke_adv_250_anom"].values
            ke_adv_a_regional = compute_regional_stats(ke_adv_a, x_2d, y_2d)
            stats[f"{label}_KEADV_ANOM_FULL30"] = f"{ke_adv_a_regional['full30']:.3e}"
            stats[f"{label}_KEADV_ANOM_LEC15"]  = f"{ke_adv_a_regional['lec15']:.3e}"
            ke_adv_a_boundary = compute_boundary_stats(ke_adv_a, x_2d, y_2d)
            stats[f"{label}_KEADV_ANOM_NORTH"] = f"{ke_adv_a_boundary['north']:.3e}"
            stats[f"{label}_KEADV_ANOM_SOUTH"] = f"{ke_adv_a_boundary['south']:.3e}"
            stats[f"{label}_KEADV_ANOM_EAST"]  = f"{ke_adv_a_boundary['east']:.3e}"
            stats[f"{label}_KEADV_ANOM_WEST"]  = f"{ke_adv_a_boundary['west']:.3e}"

        # === RK criterion @ 250 hPa (if available) ===
        if "rk_criterion_250" in ds:
            rk = ds["rk_criterion_250"].values
            stats[f"{label}_RK_MEAN"] = f"{np.nanmean(rk):.3e}"
            stats[f"{label}_RK_MIN"] = f"{np.nanmin(rk):.3e}"
            stats[f"{label}_RK_MAX"] = f"{np.nanmax(rk):.3e}"
            
            rk_regional = compute_regional_stats(rk, x_2d, y_2d)
            stats[f"{label}_RK_FULL30"] = f"{rk_regional['full30']:.3e}"
            stats[f"{label}_RK_LEC15"] = f"{rk_regional['lec15']:.3e}"

        # === AFC @ 250 hPa (if available; requires step2_1 climatology) ===
        if "afc_250" in ds:
            afc = ds["afc_250"].values
            stats[f"{label}_AFC_MEAN"] = f"{np.nanmean(afc):.3e}"
            stats[f"{label}_AFC_MIN"] = f"{np.nanmin(afc):.3e}"
            stats[f"{label}_AFC_MAX"] = f"{np.nanmax(afc):.3e}"

            afc_regional = compute_regional_stats(afc, x_2d, y_2d)
            stats[f"{label}_AFC_FULL30"] = f"{afc_regional['full30']:.3e}"
            stats[f"{label}_AFC_LEC15"] = f"{afc_regional['lec15']:.3e}"

            # Boundary values for AFC (flux divergence field)
            afc_boundary = compute_boundary_stats(afc, x_2d, y_2d)
            stats[f"{label}_AFC_NORTH"] = f"{afc_boundary['north']:.3e}"
            stats[f"{label}_AFC_SOUTH"] = f"{afc_boundary['south']:.3e}"
            stats[f"{label}_AFC_EAST"] = f"{afc_boundary['east']:.3e}"
            stats[f"{label}_AFC_WEST"] = f"{afc_boundary['west']:.3e}"

        ds.close()

    stats["GENERATION_DATE"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return stats


def export_stats_json(stats):
    """Export computed statistics to results/ep_structure/composite_stats.json.
    
    This structured JSON is the source of truth for the web layer.
    The web scripts/web/extract_composite_site_data.py reads from this file.
    
    Domain definitions:
      - "inside_15x15" (lec15): Mean within the central ±7.5° LEC subdomain
      - "outside_15x15" (full30): Mean over the full 30×30° domain
        NOTE: "outside" here means "full domain" — use as context ring
        The web displays lec15 as "inside" and full30 as "outside" (full domain)
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Mapping from internal stat keys to structured JSON entries
    # Format: prefix → (diag_id, unit, is_flux, anom_prefix_or_None)
    DIAG_MAP = {
        # (stat_prefix, diag_id, unit, is_flux, anom_prefix)
        "EGR":   ("egr",                      "day⁻¹",        False, None),
        "PV200": ("pv-200",                   "PVU",          False, None),
        "PV850": ("pv-850",                   "PVU",          False, None),
        "ADVT":  ("temperature-advection",    "K h⁻¹",        True,  "ADVT_ANOM"),
        "DIVQ":  ("moisture-flux-divergence", "g kg⁻¹ s⁻¹",  True,  "DIVQ_ANOM"),
        "SLP":   ("slp",                      "hPa",          False, None),
        "KEADV": ("ke-advection",             "m² s⁻³",       True,  "KEADV_ANOM"),
        "AFC":   ("afc",                      "m² s⁻³",       True,  None),
        "RK":    ("rk-criterion",             "s⁻¹",          False, None),
    }

    domain_stats = []
    boundary_fluxes = []

    for prefix, (diag_id, unit, is_flux, anom_prefix) in DIAG_MAP.items():
        for ep in ["EP1", "EP2"]:
            lec_key  = f"{ep}_{prefix}_LEC15"
            full_key = f"{ep}_{prefix}_FULL30"
            if lec_key in stats:
                entry = {
                    "diagnostic_id": diag_id,
                    "ep": ep,
                    "unit": unit,
                    "inside_15x15": stats[lec_key],
                    "outside_15x15": stats[full_key] if full_key in stats else None,
                }
                # Add anomaly domain fields if available
                if anom_prefix:
                    a_lec  = f"{ep}_{anom_prefix}_LEC15"
                    a_full = f"{ep}_{anom_prefix}_FULL30"
                    entry["inside_15x15_anom"]  = stats.get(a_lec)
                    entry["outside_15x15_anom"] = stats.get(a_full)
                domain_stats.append(entry)
            if is_flux:
                n_key  = f"{ep}_{prefix}_NORTH"
                s_key  = f"{ep}_{prefix}_SOUTH"
                e_key  = f"{ep}_{prefix}_EAST"
                w_key  = f"{ep}_{prefix}_WEST"
                if n_key in stats:
                    entry = {
                        "diagnostic_id": diag_id,
                        "ep": ep,
                        "unit": unit,
                        "north": stats[n_key],
                        "south": stats.get(s_key),
                        "east":  stats.get(e_key),
                        "west":  stats.get(w_key),
                    }
                    # Add anomaly boundary fields if available
                    if anom_prefix:
                        entry["north_anom"] = stats.get(f"{ep}_{anom_prefix}_NORTH")
                        entry["south_anom"] = stats.get(f"{ep}_{anom_prefix}_SOUTH")
                        entry["east_anom"]  = stats.get(f"{ep}_{anom_prefix}_EAST")
                        entry["west_anom"]  = stats.get(f"{ep}_{anom_prefix}_WEST")
                    boundary_fluxes.append(entry)

    out = {
        "generated_at": stats.get("GENERATION_DATE", ""),
        "domain_stats": domain_stats,
        "boundary_fluxes": boundary_fluxes,
    }

    out_path = RESULTS_DIR / "composite_stats.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"   ✓ Exported structured stats to {out_path.relative_to(PROJECT_ROOT)}")
    return out_path


def generate_boundary_flux_table(stats):
    """Generate a Markdown table comparing total and anomaly boundary fluxes.

    Returns a Markdown string with one section per flux diagnostic.
    EP' = anomaly relative to 1991–2020 climatology.
    """
    FLUX_DIAGS = [
        # (label, prefix, anom_prefix, unit)
        ("Temperature Advection (850 hPa)", "ADVT",  "ADVT_ANOM",  "K h⁻¹"),
        ("Moisture Flux Div. (975 hPa)",    "DIVQ",  "DIVQ_ANOM",  "g kg⁻¹ s⁻¹"),
        ("KE Advection (250 hPa)",          "KEADV", "KEADV_ANOM", "m² s⁻³"),
        ("AFC (250 hPa)",                   "AFC",   None,          "m² s⁻³"),
    ]

    lines = [
        "> **EP' = anomalia relativa à climatologia ERA5 1991–2020.** "
        "Campos totais usam o compósito bruto; anomalias usam u′, v′, T′/q′ "
        "(desvios da média mensal climatológica).\n",
        "| Diagnóstico | Fronteira | EP1 (total) | EP1′ (anomalia) | EP2 (total) | EP2′ (anomalia) |",
        "|-------------|-----------|------------:|----------------:|------------:|----------------:|",
    ]

    for diag_label, prefix, anom_prefix, unit in FLUX_DIAGS:
        for boundary in ["NORTH", "SOUTH", "EAST", "WEST"]:
            bname = boundary.capitalize()
            ep1_total = stats.get(f"EP1_{prefix}_{boundary}", "—")
            ep2_total = stats.get(f"EP2_{prefix}_{boundary}", "—")
            ep1_anom  = stats.get(f"EP1_{anom_prefix}_{boundary}", "—") if anom_prefix else "—"
            ep2_anom  = stats.get(f"EP2_{anom_prefix}_{boundary}", "—") if anom_prefix else "—"
            lines.append(
                f"| {diag_label} | {bname} (+{unit}) "
                f"| {ep1_total} | {ep1_anom} | {ep2_total} | {ep2_anom} |"
            )

    return "\n".join(lines) + "\n"


def populate_notes(stats):
    """Replace placeholders in SCIENTIFIC_NOTES.md."""
    if not NOTES_FILE.exists():
        print(f"⚠️  {NOTES_FILE} not found — skipping population")
        return

    text = NOTES_FILE.read_text()
    n_replaced = 0

    # Replace simple key placeholders
    for key, val in stats.items():
        placeholder = "{" + key + "}"
        if placeholder in text:
            text = text.replace(placeholder, val)
            n_replaced += 1

    # Replace special table placeholder
    table_placeholder = "{BOUNDARY_FLUX_TOTAL_ANOM_TABLE}"
    if table_placeholder in text:
        table_md = generate_boundary_flux_table(stats)
        text = text.replace(table_placeholder, table_md)
        n_replaced += 1

    NOTES_FILE.write_text(text)
    print(f"   ✓ Populated {n_replaced} placeholders in SCIENTIFIC_NOTES.md")


def generate_pdf():
    """Generate PDF from SCIENTIFIC_NOTES.md using pandoc."""
    pdf_out = DOCS_DIR / "scientific_notes_ep_structure.pdf"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Simplified command for reliability - run from project root for correct image paths
    cmd = [
        "pandoc", 
        str(NOTES_FILE.relative_to(PROJECT_ROOT)),
        "-o", str(pdf_out.relative_to(PROJECT_ROOT)),
        "--pdf-engine=xelatex",
        "--resource-path=.:scripts/ep_structure_analysis",  # Allows pandoc to find figures/
        "-V", "geometry:margin=2.5cm",
        "-V", "fontsize=11pt",
    ]

    print(f"   Running: pandoc {NOTES_FILE.relative_to(PROJECT_ROOT)} → {pdf_out.relative_to(PROJECT_ROOT)}")
    
    try:
        # Run without capturing output so we can see what's happening
        result = subprocess.run(
            cmd, 
            check=True, 
            cwd=str(PROJECT_ROOT),  # Run from project root so relative paths work
            timeout=60  # 1 minute timeout
        )
        
        if pdf_out.exists():
            print(f"   ✓ PDF generated: {pdf_out.relative_to(PROJECT_ROOT)}")
            print(f"   ✓ Size: {pdf_out.stat().st_size / 1024:.1f} KB")
            return pdf_out
        else:
            print(f"   ⚠️  PDF command succeeded but file not found")
            return None
            
    except FileNotFoundError:
        print("   ❌ pandoc not found — install with: brew install pandoc")
        return None
    except subprocess.TimeoutExpired:
        print("   ❌ pandoc timed out after 60 seconds")
        return None
    except subprocess.CalledProcessError as e:
        print(f"   ❌ pandoc failed with exit code {e.returncode}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Update scientific notes for EP structure analysis")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 5: UPDATE SCIENTIFIC NOTES")
    print("=" * 60)

    print("\n1. Computing statistics from composites...")
    stats = load_stats()
    if not stats:
        print("   ❌ No composite data found. Run step3 first.")
        return

    print(f"   ✓ Computed {len(stats)} statistics")

    print("\n2. Exporting structured stats to JSON (for web layer)...")
    export_stats_json(stats)

    print("\n3. Populating SCIENTIFIC_NOTES.md...")
    populate_notes(stats)
    
    # Print summary of key statistics
    print("\n   Key statistics computed:")
    for key in sorted(stats.keys()):
        if key.endswith('_N_CASES') or key.endswith('_MEAN'):
            print(f"   {key:40s} = {stats[key]}")

    if not args.no_pdf:
        print("\n4. Generating PDF...")
        pdf_path = generate_pdf()
        if pdf_path and pdf_path.exists():
            print(f"   ✓ PDF ready at: {pdf_path.relative_to(PROJECT_ROOT)}")
    else:
        print("\n4. PDF generation skipped (use without --no-pdf to generate)")

    print("\n" + "=" * 60)
    print("✓ STEP 5 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
