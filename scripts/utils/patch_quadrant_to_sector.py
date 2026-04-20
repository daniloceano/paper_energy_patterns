"""
One-off patch: replace quadrant_ne/nw/se/sw columns in step4/step5 CSVs
with sector_north/south/east/west columns.

Derivation (no raw ERA5 data needed):
  sector_north = (quadrant_ne + quadrant_nw) / 2   -- full northern half
  sector_south = (quadrant_se + quadrant_sw) / 2   -- full southern half
  sector_east  = (quadrant_ne + quadrant_se) / 2   -- full eastern half
  sector_west  = (quadrant_nw + quadrant_sw) / 2   -- full western half

This is exact because each sector is the union of two equal-area quadrants.

Run:
    python scripts/utils/patch_quadrant_to_sector.py
"""
import pandas as pd
from pathlib import Path

RESULTS = Path("results/lec_field_dependence")


def patch_csv(path: Path) -> bool:
    df = pd.read_csv(path)

    quad_cols = [c for c in df.columns if any(
        c.endswith(f"__{q}") for q in ("quadrant_ne", "quadrant_nw", "quadrant_se", "quadrant_sw")
    )]
    if not quad_cols:
        return False  # Nothing to patch

    # Identify field prefixes (e.g. "pv_850", "pv_850_anom_epall")
    prefixes = set()
    for col in quad_cols:
        prefix = col.rsplit("__quadrant_", 1)[0]
        prefixes.add(prefix)

    for prefix in sorted(prefixes):
        ne = df.get(f"{prefix}__quadrant_ne")
        nw = df.get(f"{prefix}__quadrant_nw")
        se = df.get(f"{prefix}__quadrant_se")
        sw = df.get(f"{prefix}__quadrant_sw")
        if ne is None:
            continue

        df[f"{prefix}__sector_north"] = (ne + nw) / 2.0
        df[f"{prefix}__sector_south"] = (se + sw) / 2.0
        df[f"{prefix}__sector_east"]  = (ne + se) / 2.0
        df[f"{prefix}__sector_west"]  = (nw + sw) / 2.0

    # Drop quadrant columns
    df = df.drop(columns=quad_cols)
    df.to_csv(path, index=False)
    return True


def main():
    files = sorted(
        list(RESULTS.glob("step4_features_absolute*.csv")) +
        list(RESULTS.glob("step5_features_anomaly*.csv"))
    )

    print(f"Patching {len(files)} CSV files...")
    patched = 0
    for f in files:
        if patch_csv(f):
            print(f"  ✓ {f.name}")
            patched += 1
        else:
            print(f"  - {f.name} (nothing to patch)")

    print(f"\nPatched {patched}/{len(files)} files.")

    # Verify
    df4 = pd.read_csv(RESULTS / "step4_features_absolute.csv")
    sec = [c for c in df4.columns if "sector" in c]
    quad = [c for c in df4.columns if "quadrant" in c]
    print(f"step4: {len(sec)} sector cols, {len(quad)} quadrant cols remaining")
    print("Sector sample:", sec[:4])
    assert len(quad) == 0, "Quadrant columns still present!"
    print("✓ All quadrant columns removed.")


if __name__ == "__main__":
    main()
