"""
Step 1: Select EP1 and EP2 Cyclone Tracks for Structure Analysis

Selects ALL cyclones from Energy Pattern 1 (EP1, cluster 0) and Energy Pattern 2
(EP2, cluster 2) for composite analysis during their entire intensification phase.

IMPORTANT: The clustering was performed on cyclones already filtered for complete
lifecycle (incipient → intensification → mature → decay). Therefore, ALL cyclones
in the cluster file already satisfy this criterion and should NOT be filtered again.

Selection Criteria:
- Belongs to EP1 (cluster 0) OR EP2 (cluster 2) from kmeans_clustered_data.csv
- ALL cyclones from these clusters are used (no additional lifecycle filtering)
- Consistency: Same cyclones used in clustering are used here

Output:
- results/ep_structure/ep1_cases.csv
- results/ep_structure/ep2_cases.csv
- figures/ep_structure/tracks/ep1_tracks_overview.png
- figures/ep_structure/tracks/ep2_tracks_overview.png

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.lines import Line2D
from scripts.utils.load_data import load_tracks

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLUSTER_FILE = PROJECT_ROOT / "results" / "cluster" / "kmeans_clustered_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "ep_structure"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = PROJECT_ROOT / "figures" / "ep_structure" / "tracks"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = PROJECT_ROOT / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
DPI = 300

# Cluster → EP mapping
CLUSTER_TO_EP = {0: 1, 2: 2}  # cluster 0 → EP1, cluster 2 → EP2


def _resolve_csv(path: Path):
    """Handle Zenodo quirk where *.csv can be a directory containing a CSV."""
    if path.is_dir():
        csvs = list(path.glob("*.csv"))
        return csvs[0] if csvs else None
    return path if path.exists() else None


def get_intensification_info(track_id, tracks_df):
    """
    Get intensification phase information for a track.
    Returns (start_time, end_time, n_timesteps, center_lat, center_lon) or None.
    """
    lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
    periods_file = _resolve_csv(lec_dir / "periods.csv")

    if periods_file is None:
        return None

    periods = pd.read_csv(periods_file, index_col=0)
    if "intensification" not in periods.index:
        return None

    intensification = periods.loc["intensification"]
    start_time = pd.to_datetime(intensification["start"])
    end_time = pd.to_datetime(intensification["end"])

    # Get track data during intensification
    track_data = tracks_df[tracks_df["track_id"] == track_id].copy()
    track_data["time"] = pd.to_datetime(track_data["date"])
    track_intens = track_data[
        (track_data["time"] >= start_time) & (track_data["time"] <= end_time)
    ]

    if len(track_intens) == 0:
        return None

    n_timesteps = len(track_intens)

    # Temporal centre point
    t_center = start_time + (end_time - start_time) / 2
    time_diffs = np.abs((track_intens["time"] - t_center).dt.total_seconds())
    closest_idx = time_diffs.idxmin()

    center_lat = track_intens.loc[closest_idx, "lat vor"]
    center_lon = track_intens.loc[closest_idx, "lon vor"]

    return start_time, end_time, n_timesteps, center_lat, center_lon


def plot_tracks(selected_df, tracks_df, ep_label, color):
    """Create overview map for a given EP group."""
    print(f"   Creating {ep_label} track visualisation...")

    fig = plt.figure(figsize=(14, 10))
    proj = ccrs.Stereographic(central_latitude=-90, central_longitude=0)
    ax = fig.add_subplot(111, projection=proj)
    ax.set_extent([-80, 40, -70, -20], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.3)
    ax.add_feature(cfeature.OCEAN, facecolor="white")
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="black")

    gl = ax.gridlines(
        draw_labels=True,
        linewidth=0.5,
        linestyle="--",
        alpha=0.7,
        color="gray",
        x_inline=False,
        y_inline=False,
    )
    gl.top_labels = False
    gl.right_labels = False

    for _, case in selected_df.iterrows():
        track_id = case["track_id"]
        track = tracks_df[tracks_df["track_id"] == track_id].copy()
        if len(track) == 0:
            continue
        track = track.sort_values("date")

        lec_dir = LEC_DATA_DIR / f"{track_id}_ERA5_track"
        periods_file = _resolve_csv(lec_dir / "periods.csv")

        if periods_file is not None:
            periods = pd.read_csv(periods_file, index_col=0)
            intensification = periods.loc["intensification"]
            t_start = pd.to_datetime(intensification["start"])
            t_end = pd.to_datetime(intensification["end"])

            track["date"] = pd.to_datetime(track["date"])
            track_intens = track[(track["date"] >= t_start) & (track["date"] <= t_end)]

            ax.plot(
                track["lon vor"].values,
                track["lat vor"].values,
                color="gray",
                linewidth=0.6,
                alpha=0.3,
                transform=ccrs.PlateCarree(),
                zorder=2,
            )

            if len(track_intens) > 0:
                ax.plot(
                    track_intens["lon vor"].values,
                    track_intens["lat vor"].values,
                    color=color,
                    linewidth=1.5,
                    alpha=0.9,
                    transform=ccrs.PlateCarree(),
                    zorder=3,
                )

            ax.plot(
                track["lon vor"].iloc[0],
                track["lat vor"].iloc[0],
                "o",
                color="green",
                markersize=3,
                markeredgecolor="k",
                markeredgewidth=0.3,
                transform=ccrs.PlateCarree(),
                zorder=4,
            )

    legend_elements = [
        Line2D([0], [0], color="gray", linewidth=1.5, alpha=0.5, label="Complete track"),
        Line2D([0], [0], color=color, linewidth=2, alpha=0.9, label="Intensification"),
        Line2D(
            [0], [0], marker="o", color="w", markerfacecolor="green",
            markersize=6, markeredgecolor="k", label="Genesis",
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper left", framealpha=0.95, fontsize=9)
    ax.set_title(
        f"All {ep_label} Cyclone Tracks (n={len(selected_df)})",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()
    out_path = FIGURES_DIR / f"{ep_label.lower()}_tracks_overview.png"
    plt.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"   Saved: {out_path}")


def select_ep_cases(ep_label, cluster_id, tracks_df, clustered_df):
    """
    Select all cases from an EP cluster.
    
    IMPORTANT: NO FILTERING by lifecycle - all cyclones in the cluster are used.
    The clustering was already performed on complete-lifecycle cyclones only.
    Re-filtering here would create inconsistency with the cluster analysis.
    """
    print(f"\n── {ep_label} (cluster {cluster_id}) ──")

    ep_cyclones = clustered_df[clustered_df["cluster"] == cluster_id]
    ep_track_ids = ep_cyclones["track_id"].unique()
    print(f"   Total {ep_label} cyclones from cluster: {len(ep_track_ids)}")

    # Get intensification info for each track (no lifecycle filtering)
    cases = []
    for track_id in ep_track_ids:
        info = get_intensification_info(track_id, tracks_df)
        if info is not None:
            start_time, end_time, n_timesteps, center_lat, center_lon = info
            cases.append(
                {
                    "track_id": track_id,
                    "intensification_start": start_time,
                    "intensification_end": end_time,
                    "n_timesteps": n_timesteps,
                    "center_lat": center_lat,
                    "center_lon": center_lon,
                    "duration_hours": (end_time - start_time).total_seconds() / 3600,
                }
            )

    df = pd.DataFrame(cases)
    print(f"   Valid cases with intensification data: {len(df)}")

    if len(df) > 0:
        print(f"   Mean timesteps/case: {df['n_timesteps'].mean():.1f}")
        print(f"   Total timesteps: {df['n_timesteps'].sum()}")
        print(f"   Mean duration: {df['duration_hours'].mean():.1f} h")
        print(
            f"   Lat range: [{df['center_lat'].min():.1f}, {df['center_lat'].max():.1f}]"
        )
        print(
            f"   Lon range: [{df['center_lon'].min():.1f}, {df['center_lon'].max():.1f}]"
        )

    return df


def main():
    print("=" * 70)
    print("STEP 1: SELECT EP1 + EP2 CYCLONE TRACKS FOR STRUCTURE ANALYSIS")
    print("=" * 70)
    print()
    print("IMPORTANT: All cyclones from the cluster were already filtered for")
    print("complete lifecycle during the clustering analysis. NO additional")
    print("filtering is applied here to ensure consistency.")
    
    # 1. Load cluster assignments
    print("\n1. Loading cluster assignments...")
    if not CLUSTER_FILE.exists():
        raise FileNotFoundError(f"Cluster file not found: {CLUSTER_FILE}")

    clustered_df = pd.read_csv(CLUSTER_FILE)
    print(f"   Total clustered cyclones: {len(clustered_df)}")
    for cid, ep in CLUSTER_TO_EP.items():
        n = (clustered_df["cluster"] == cid).sum()
        print(f"   EP{ep} (cluster {cid}): {n} cyclones")

    # 2. Load tracks
    print("\n2. Loading track data...")
    tracks_df = load_tracks()
    print(f"   Total tracks in database: {tracks_df['track_id'].nunique()}")

    # 3. Select cases for each EP
    print("\n3. Selecting cases per EP...")

    ep1_df = select_ep_cases("EP1", 0, tracks_df, clustered_df)
    ep2_df = select_ep_cases("EP2", 2, tracks_df, clustered_df)

    # 4. Save
    print("\n4. Saving results...")
    ep1_csv = OUTPUT_DIR / "ep1_cases.csv"
    ep2_csv = OUTPUT_DIR / "ep2_cases.csv"
    ep1_df.to_csv(ep1_csv, index=False)
    ep2_df.to_csv(ep2_csv, index=False)
    print(f"   Saved: {ep1_csv}")
    print(f"   Saved: {ep2_csv}")

    # 5. Visualisations
    print("\n5. Creating track visualisations...")
    plot_tracks(ep1_df, tracks_df, "EP1", color="gold")
    plot_tracks(ep2_df, tracks_df, "EP2", color="dodgerblue")

    # 6. Summary
    print("\n" + "=" * 70)
    print("STEP 1 COMPLETE")
    print("=" * 70)
    print(f"   EP1 cases: {len(ep1_df)}")
    print(f"   EP2 cases: {len(ep2_df)}")
    print(f"   Total:     {len(ep1_df) + len(ep2_df)}")
    print(
        f"\nNext step: python scripts/ep_structure_analysis/step2_download_era5_parallel.py"
    )


if __name__ == "__main__":
    main()
