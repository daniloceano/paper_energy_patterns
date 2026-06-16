"""
Step 1: Select the full EP1/EP2/EP3 cyclone populations and their tracks.

This analysis assesses the occurrence of *explosive cyclones* ("bombs") in each
Energy Pattern. The bomb classification is a surface-pressure diagnostic layered
on top of the vorticity-based life cycle, so it must run over the FULL EP
populations defined by the K-Means clustering — NOT the reduced subset used for
the composite analysis (which keeps only intensification phases >= 24 h).

Authoritative population (from clustering on LEC diagnostics):
    EP1 = 444, EP2 = 979, EP3 = 2397   (total 3820)

Outputs (results/explosive_cyclones/):
    ep_membership.csv          track_id, cluster, ep
    tracks_by_ep.csv           full hourly tracks with an `ep` column (master input
                               for step2 download and step3 central-pressure search)
    ep_population_summary.csv  ep, n_cyclones

Run:
    python scripts/explosive_cyclones_analysis/step1_select_ep_populations.py

Author: Danilo Couto de Souza
Date: June 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

from scripts.utils.load_data import load_tracks
from scripts.utils.ep_mapping import CLUSTER_TO_EP, ALL_EPS, EP_COUNTS, get_ep_label

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLUSTER_FILE = PROJECT_ROOT / "results" / "cluster" / "kmeans_clustered_data.csv"
OUT_DIR = PROJECT_ROOT / "results" / "explosive_cyclones"

# Track columns we keep for the downstream pressure analysis
TRACK_COLS = ["track_id", "date", "lat vor", "lon vor", "vor42", "period", "region"]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 1: Select full EP1/EP2/EP3 populations and tracks")
    print("=" * 70)

    # --- EP membership from clustering ---------------------------------------
    if not CLUSTER_FILE.exists():
        print(f"❌ Missing {CLUSTER_FILE}. Run the cluster analysis pipeline first.")
        return 1

    clustered = pd.read_csv(CLUSTER_FILE)
    clustered["track_id"] = clustered["track_id"].astype(int)
    clustered["ep"] = clustered["cluster"].map(CLUSTER_TO_EP)

    membership = clustered[["track_id", "cluster", "ep"]].sort_values("track_id")
    membership.to_csv(OUT_DIR / "ep_membership.csv", index=False)

    # --- Validate counts against the single source of truth ------------------
    print("\nEP populations (clustering):")
    ok = True
    for ep in ALL_EPS:
        n = int((membership["ep"] == ep).sum())
        expected = EP_COUNTS[ep]
        flag = "✓" if n == expected else "⚠"
        if n != expected:
            ok = False
        print(f"  {get_ep_label(ep)}: {n:4d}  (expected {expected})  {flag}")
    print(f"  Total: {len(membership)}")
    if not ok:
        print("  ⚠️  Count mismatch vs ep_mapping.EP_COUNTS — check the cluster file.")

    # --- Full tracks for these cyclones --------------------------------------
    tracks = load_tracks()
    tracks["track_id"] = tracks["track_id"].astype(int)

    keep = [c for c in TRACK_COLS if c in tracks.columns]
    missing = set(TRACK_COLS) - set(keep)
    if missing:
        print(f"  ⚠️  Track columns not found and skipped: {missing}")

    ep_map = dict(zip(membership["track_id"], membership["ep"]))
    tracks_ep = tracks[tracks["track_id"].isin(ep_map)].copy()
    tracks_ep["ep"] = tracks_ep["track_id"].map(ep_map)
    tracks_ep = tracks_ep[keep + ["ep"]].sort_values(["track_id", "date"])

    n_with_tracks = tracks_ep["track_id"].nunique()
    print(f"\nCyclones with track data: {n_with_tracks}/{len(membership)}")
    if n_with_tracks < len(membership):
        missing_ids = set(membership["track_id"]) - set(tracks_ep["track_id"])
        print(f"  ⚠️  {len(missing_ids)} clustered cyclones have no track rows "
              f"(e.g., {sorted(missing_ids)[:5]} ...)")

    tracks_ep.to_csv(OUT_DIR / "tracks_by_ep.csv", index=False)

    summary = (
        tracks_ep.groupby("ep")["track_id"].nunique()
        .rename("n_cyclones").reset_index()
    )
    summary["ep_label"] = summary["ep"].map(get_ep_label)
    summary.to_csv(OUT_DIR / "ep_population_summary.csv", index=False)

    print("\nWrote:")
    print(f"  {OUT_DIR / 'ep_membership.csv'}")
    print(f"  {OUT_DIR / 'tracks_by_ep.csv'}  ({len(tracks_ep)} track points)")
    print(f"  {OUT_DIR / 'ep_population_summary.csv'}")
    print("\n✓ Step 1 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
