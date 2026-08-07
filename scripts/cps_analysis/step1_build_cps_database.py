"""
Step 1: Consolidate the per-cyclone CPS CSVs into one tidy timestep database.

The CPS calculator (`cps_calculator_era5tocsv.py`, A. Rodriguez) writes one CSV
per cyclone into `csv_output/`. This step reads all of them, applies the
Southern Hemisphere sign convention to B, joins the canonical track metadata
(position, genesis region, life cycle period) and the Energy Pattern membership
from the K-Means clustering, and writes a single analysis-ready table.

What happens to B
-----------------
The calculator stores the two semicircle thickness means separately (`B_left`,
`B_right`). Hart's (2003) parameter is

    B = h [ (Z600 - Z900)_R - (Z600 - Z900)_L ],   h = -1 in the Southern Hemisphere

so for our basin  B = B_left - B_right, which is what is computed here. The
resulting population is dominated by B > 0 (asymmetric/frontal), as expected for
an extratropical cyclone track set — this is the sanity check printed at the end.

Missing values
--------------
The calculator emits the GrADS sentinel -999000000 for the FIRST timestep of
every cyclone (storm motion, hence B, is undefined without a previous position;
VTL/VTU are also suppressed there). Those become NaN. As a consequence the
genesis timestep is never classifiable — cyclogenesis-time statistics of the
kind reported by Conrado et al. (2024) cannot be reproduced from this database.

Inputs:
    scripts/cps_analysis/csv_output/CPS_<track_id>.csv   (A. Rodriguez, 2026)
    tracks_SAt_filtered_with_periods.csv                 (via scripts/utils/load_data)
    results/cluster/kmeans_clustered_data.csv            (cluster analysis, step 4)

Output:
    results/cps_analysis/cps_timesteps.csv

Run:
    python scripts/cps_analysis/step1_build_cps_database.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from tqdm import tqdm

from scripts.utils.load_data import load_tracks
from scripts.utils.ep_mapping import CLUSTER_TO_EP, ALL_EPS, get_ep_label

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = Path(__file__).resolve().parent / "csv_output"
CLUSTER_FILE = PROJECT_ROOT / "results" / "cluster" / "kmeans_clustered_data.csv"
OUT_DIR = PROJECT_ROOT / "results" / "cps_analysis"
OUT_FILE = OUT_DIR / "cps_timesteps.csv"

# GrADS undefined sentinel written by the calculator. Anything at or below
# -999 is treated as missing (the raw value is -999000000).
UNDEF_THRESHOLD = -999.0

CPS_NUMERIC_COLS = ["B_left", "B_right", "dir", "SIZE", "VTL", "VTU"]


def read_one(path: Path) -> pd.DataFrame:
    """Read a single CPS CSV, mask sentinels, return a tidy frame."""
    df = pd.read_csv(path)
    for col in CPS_NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].mask(df[col] <= UNDEF_THRESHOLD)

    # Southern Hemisphere Hart (2003) B, Eq. (2) with h = -1.
    df["B"] = df["B_left"] - df["B_right"]

    # "00Z01JAN1979" -> Timestamp
    df["datetime"] = pd.to_datetime(df["time"], format="%HZ%d%b%Y")
    df["track_id"] = int(path.stem.replace("CPS_", ""))
    return df[["track_id", "datetime", "B", "VTL", "VTU", "SIZE", "dir"]]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 1: Build the consolidated CPS timestep database")
    print("=" * 70)

    if not CSV_DIR.exists():
        print(f"Missing {CSV_DIR}. Run the CPS calculator first (see README).")
        return 1

    files = sorted(CSV_DIR.glob("CPS_*.csv"))
    print(f"\nReading {len(files)} per-cyclone CPS files from {CSV_DIR.name}/ ...")

    frames, failed = [], []
    for path in tqdm(files, unit="file"):
        try:
            frames.append(read_one(path))
        except Exception as exc:  # keep going; report at the end
            failed.append((path.name, str(exc)[:80]))

    if failed:
        print(f"\n  {len(failed)} file(s) could not be read:")
        for name, msg in failed[:10]:
            print(f"    {name}: {msg}")

    cps = pd.concat(frames, ignore_index=True)
    print(f"  {len(cps):,} timesteps for {cps['track_id'].nunique():,} cyclones")

    # --- Join canonical track metadata ---------------------------------------
    print("\nJoining track metadata ...")
    tracks = load_tracks()
    tracks["track_id"] = tracks["track_id"].astype(int)
    tracks["date"] = pd.to_datetime(tracks["date"])
    track_cols = ["track_id", "date", "lat vor", "lon vor", "vor42", "region", "period"]
    tracks = tracks[[c for c in track_cols if c in tracks.columns]]

    merged = cps.merge(
        tracks,
        left_on=["track_id", "datetime"],
        right_on=["track_id", "date"],
        how="left",
    ).drop(columns=["date"])
    merged = merged.rename(columns={"lat vor": "lat", "lon vor": "lon"})

    matched = merged["lat"].notna().mean()
    print(f"  position matched for {matched:.2%} of CPS timesteps")
    if matched < 0.99:
        print("  Track/CPS time axes disagree for >1% of steps — inspect before using.")

    # --- Genesis position and Energy Pattern membership -----------------------
    genesis = (
        tracks.sort_values(["track_id", "date"])
        .groupby("track_id")
        .first()[["lat vor", "lon vor"]]
        .rename(columns={"lat vor": "genesis_lat", "lon vor": "genesis_lon"})
    )
    merged = merged.merge(genesis, left_on="track_id", right_index=True, how="left")

    print("\nJoining Energy Pattern membership ...")
    if not CLUSTER_FILE.exists():
        print(f"  Missing {CLUSTER_FILE}. Run the cluster analysis pipeline first.")
        return 1

    clustered = pd.read_csv(CLUSTER_FILE)
    clustered["track_id"] = clustered["track_id"].astype(int)
    clustered["ep"] = clustered["cluster"].map(CLUSTER_TO_EP)
    merged = merged.merge(clustered[["track_id", "ep"]], on="track_id", how="left")

    n_ep = merged.loc[merged["ep"].notna(), "track_id"].nunique()
    n_total = merged["track_id"].nunique()
    print(f"  {n_ep:,} of {n_total:,} cyclones carry an EP label "
          f"({n_total - n_ep:,} outside the clustered subset)")

    merged = merged.sort_values(["track_id", "datetime"]).reset_index(drop=True)
    merged.to_csv(OUT_FILE, index=False)
    print(f"\nWrote {OUT_FILE.relative_to(PROJECT_ROOT)}  ({len(merged):,} rows)")

    # --- Sanity checks --------------------------------------------------------
    valid = merged[["B", "VTL", "VTU"]].notna().all(axis=1)
    print("\n" + "-" * 70)
    print("SANITY CHECKS")
    print("-" * 70)
    print(f"  classifiable timesteps : {valid.sum():,} / {len(merged):,} "
          f"({valid.mean():.1%})")
    print(f"  first-step sentinels    : {merged.groupby('track_id').head(1)['B'].isna().sum():,} "
          f"(expected {merged['track_id'].nunique():,})")

    print("\n  Sign convention (Southern Hemisphere, expect a cold-core, frontal population):")
    print(f"    median B   = {merged['B'].median():8.1f} m     "
          f"(fraction B > 10 m: {(merged['B'] > 10).mean():.1%})")
    print(f"    median VTL = {merged['VTL'].median():8.1f}       "
          f"(fraction VTL > 0: {(merged['VTL'] > 0).mean():.1%})")
    print(f"    median VTU = {merged['VTU'].median():8.1f}       "
          f"(fraction VTU > 0: {(merged['VTU'] > 0).mean():.1%})")
    if merged["B"].median() < 0:
        print("    Median B is negative — the left/right semicircles may be swapped.")

    print("\n  Cyclones per Energy Pattern:")
    for ep in ALL_EPS:
        n = merged.loc[merged["ep"] == ep, "track_id"].nunique()
        print(f"    {get_ep_label(ep)}: {n:5,d}")

    print("\nStep 1 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
