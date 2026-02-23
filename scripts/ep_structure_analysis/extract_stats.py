"""Quick script to extract statistics and update SCIENTIFIC_NOTES.md"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "era5_ep_structure"
NOTES_FILE = Path(__file__).parent / "SCIENTIFIC_NOTES.md"

stats = {}

for ep in ["ep1", "ep2"]:
    f = DATA_DIR / f"precomputed_composites_{ep}.nc"
    if not f.exists():
        print(f"⚠️  Missing {f.name} - skipping {ep.upper()}")
        continue
    
    print(f"Reading {f.name}...")
    ds = xr.open_dataset(f)
    label = ep.upper()
    
    # EGR
    egr = ds["egr"].values
    stats[f"{label}_EGR_MEAN"] = f"{np.nanmean(egr):.2f}"
    stats[f"{label}_EGR_STD"] = f"{np.nanstd(egr):.2f}"
    stats[f"{label}_EGR_MEDIAN"] = f"{np.nanmedian(egr):.2f}"
    stats[f"{label}_EGR_MIN"] = f"{np.nanmin(egr):.2f}"
    stats[f"{label}_EGR_MAX"] = f"{np.nanmax(egr):.2f}"
    
    # PV 200 (convert to PVU)
    pv200 = ds["pv_200"].values * 1e6
    stats[f"{label}_PV200_MEAN"] = f"{np.nanmean(pv200):.2f}"
    stats[f"{label}_PV200_MIN"] = f"{np.nanmin(pv200):.2f}"
    stats[f"{label}_PV200_MAX"] = f"{np.nanmax(pv200):.2f}"
    
    # PV 850 (convert to PVU)
    pv850 = ds["pv_850"].values * 1e6
    stats[f"{label}_PV850_MEAN"] = f"{np.nanmean(pv850):.2f}"
    stats[f"{label}_PV850_MIN"] = f"{np.nanmin(pv850):.2f}"
    stats[f"{label}_PV850_MAX"] = f"{np.nanmax(pv850):.2f}"
    
    # Temperature advection (convert to K/h)
    advT = ds["adv_T_850"].values * 3600
    stats[f"{label}_ADVT_MEAN"] = f"{np.nanmean(advT):.3f}"
    stats[f"{label}_ADVT_MAX_WARM"] = f"{np.nanmax(advT):.3f}"
    stats[f"{label}_ADVT_MAX_COLD"] = f"{np.nanmin(advT):.3f}"
    
    # SLP
    if "msl" in ds:
        msl = ds["msl"].values / 100  # Pa to hPa
        stats[f"{label}_SLP_MIN"] = f"{np.nanmin(msl):.1f}"
        stats[f"{label}_SLP_MAX"] = f"{np.nanmax(msl):.1f}"
    
    ds.close()

# Update SCIENTIFIC_NOTES.md
if NOTES_FILE.exists():
    text = NOTES_FILE.read_text()
    n_replaced = 0
    for key, val in stats.items():
        placeholder = "{" + key + "}"
        if placeholder in text:
            text = text.replace(placeholder, val)
            n_replaced += 1
    
    NOTES_FILE.write_text(text)
    print(f"✓ Updated {n_replaced} placeholders in SCIENTIFIC_NOTES.md")
else:
    print(f"⚠️  {NOTES_FILE} not found")

# Print summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for key, val in sorted(stats.items()):
    print(f"{key:25s} = {val}")
print("="*60)
