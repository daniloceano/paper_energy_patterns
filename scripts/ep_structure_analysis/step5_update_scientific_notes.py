"""
Step 5: Update Scientific Notes for EP Structure Analysis

Populates SCIENTIFIC_NOTES.md with statistics computed from the
precomputed composite files. Optionally generates a PDF via pandoc.

Usage:
    python step5_update_scientific_notes.py [--pdf]

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import argparse
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
SCRIPT_DIR = Path(__file__).resolve().parent
NOTES_FILE = SCRIPT_DIR / "SCIENTIFIC_NOTES.md"


def load_stats():
    """Compute summary statistics from precomputed composites."""
    stats = {}

    for ep in ["ep1", "ep2"]:
        f = DATA_DIR / f"precomputed_composites_{ep}.nc"
        if not f.exists():
            print(f"⚠️  Missing {f.name} — skipping {ep.upper()}")
            continue

        ds = xr.open_dataset(f)
        label = ep.upper()

        n = int(ds.attrs.get("n_cases", 0))
        stats[f"{label}_N_CASES"] = str(n)

        # EGR
        egr = ds["egr"].values
        stats[f"{label}_EGR_MEAN"] = f"{np.nanmean(egr):.2f}"
        stats[f"{label}_EGR_STD"] = f"{np.nanstd(egr):.2f}"
        stats[f"{label}_EGR_MEDIAN"] = f"{np.nanmedian(egr):.2f}"
        stats[f"{label}_EGR_MIN"] = f"{np.nanmin(egr):.2f}"
        stats[f"{label}_EGR_MAX"] = f"{np.nanmax(egr):.2f}"

        # PV 200 (PVU)
        pv200 = ds["pv_200"].values * 1e6
        stats[f"{label}_PV200_MEAN"] = f"{np.nanmean(pv200):.2f}"
        stats[f"{label}_PV200_MIN"] = f"{np.nanmin(pv200):.2f}"
        stats[f"{label}_PV200_MAX"] = f"{np.nanmax(pv200):.2f}"

        # PV 850 (PVU)
        pv850 = ds["pv_850"].values * 1e6
        stats[f"{label}_PV850_MEAN"] = f"{np.nanmean(pv850):.2f}"
        stats[f"{label}_PV850_MIN"] = f"{np.nanmin(pv850):.2f}"
        stats[f"{label}_PV850_MAX"] = f"{np.nanmax(pv850):.2f}"

        # Temperature advection (K/h)
        advT = ds["adv_T_850"].values * 3600
        stats[f"{label}_ADVT_MEAN"] = f"{np.nanmean(advT):.3f}"
        stats[f"{label}_ADVT_MAX_WARM"] = f"{np.nanmax(advT):.3f}"
        stats[f"{label}_ADVT_MAX_COLD"] = f"{np.nanmin(advT):.3f}"

        # SLP
        if "msl" in ds:
            msl = ds["msl"].values / 100
            stats[f"{label}_SLP_MIN"] = f"{np.nanmin(msl):.1f}"
            stats[f"{label}_SLP_MAX"] = f"{np.nanmax(msl):.1f}"

        ds.close()

    stats["GENERATION_DATE"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return stats


def populate_notes(stats):
    """Replace placeholders in SCIENTIFIC_NOTES.md."""
    if not NOTES_FILE.exists():
        print(f"⚠️  {NOTES_FILE} not found — skipping population")
        return

    text = NOTES_FILE.read_text()
    n_replaced = 0
    for key, val in stats.items():
        placeholder = "{" + key + "}"
        if placeholder in text:
            text = text.replace(placeholder, val)
            n_replaced += 1

    NOTES_FILE.write_text(text)
    print(f"   ✓ Populated {n_replaced} placeholders in SCIENTIFIC_NOTES.md")


def generate_pdf():
    """Generate PDF from SCIENTIFIC_NOTES.md using pandoc."""
    pdf_out = RESULTS_DIR / "SCIENTIFIC_NOTES.pdf"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pandoc", str(NOTES_FILE),
        "-o", str(pdf_out),
        "--pdf-engine=xelatex",
        "-V", "geometry:margin=2.5cm",
        "-V", "fontsize=11pt",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✓ PDF generated: {pdf_out}")
    except FileNotFoundError:
        print("   ⚠️  pandoc not found — PDF generation skipped")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  pandoc failed: {e.stderr.decode()[:200]}")


def main():
    parser = argparse.ArgumentParser(description="Update scientific notes for EP structure analysis")
    parser.add_argument("--pdf", action="store_true", help="Generate PDF via pandoc")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 5: UPDATE SCIENTIFIC NOTES")
    print("=" * 60)

    print("\n1. Computing statistics from composites...")
    stats = load_stats()
    if not stats:
        print("   ❌ No composite data found. Run step3 first.")
        return

    print(f"   Computed {len(stats)} statistics")

    print("\n2. Populating SCIENTIFIC_NOTES.md...")
    populate_notes(stats)

    if args.pdf:
        print("\n3. Generating PDF...")
        generate_pdf()

    print("\n" + "=" * 60)
    print("✓ STEP 5 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
