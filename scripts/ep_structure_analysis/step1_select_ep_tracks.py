"""
Step 1: Select EP1, EP2, EP3, and EPALL Cyclone Tracks for Structure Analysis

Selects ALL cyclones from Energy Patterns 1, 2, and 3 for composite analysis
during their entire intensification phase.

IMPORTANT: The clustering was performed on cyclones already filtered for complete
lifecycle (incipient → intensification → mature → decay). Therefore, ALL cyclones
in the cluster file already satisfy this criterion and should NOT be filtered again.

Selection Criteria:
- EP1: Cluster 0 (444 cyclones, 11.6%) - High energy conversions
- EP2: Cluster 2 (979 cyclones, 25.6%) - Moderate conversions
- EP3: Cluster 1 (2,397 cyclones, 62.7%) - Weak/background energetics
- EPALL: Union of all three EPs (3,820 cyclones, 100%)

Intensity Subset:
- Additionally selects the 10 most intense cyclones per EP group
- Intensity metric: maximum |vor42| (central relative vorticity at 850 hPa)
- Used for the 'intense_10' composite mode in step3

Output:
- results/ep_structure/ep1_cases.csv           (all EP1 cyclones)
- results/ep_structure/ep2_cases.csv           (all EP2 cyclones)
- results/ep_structure/ep3_cases.csv           (all EP3 cyclones)
- results/ep_structure/epall_cases.csv         (all cyclones)
- results/ep_structure/ep1_top10_intense.csv   (10 most intense EP1)
- results/ep_structure/ep2_top10_intense.csv   (10 most intense EP2)
- results/ep_structure/ep3_top10_intense.csv   (10 most intense EP3)
- figures/ep_structure/tracks/ep1_tracks_overview.png
- figures/ep_structure/tracks/ep2_tracks_overview.png
- figures/ep_structure/tracks/ep3_tracks_overview.png

Author: Danilo Couto de Souza
Date: April 2026
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
from scripts.utils.ep_mapping import (
    CLUSTER_TO_EP, EP_TO_CLUSTER, ALL_EPS, EP_LABELS, EP_COLORS,
    get_ep_label, get_ep_abbrev, get_ep_color
)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLUSTER_FILE = PROJECT_ROOT / "results" / "cluster" / "kmeans_clustered_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "ep_structure"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR = PROJECT_ROOT / "figures" / "ep_structure" / "tracks"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LEC_DATA_DIR = PROJECT_ROOT / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
DPI = 300


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


def select_top10_intense(ep_df, tracks_df, ep_label):
    """
    Select the 10 most intense cyclones from an EP group based on max vorticity.
    
    Intensity metric: maximum |vor42| (central vorticity at 850 hPa) during the
    cyclone's full lifecycle.
    """
    print(f"\n   Selecting top 10 most intense {ep_label} cyclones...")
    
    # Get max vorticity for each cyclone from tracks data
    max_vor = tracks_df.groupby('track_id')['vor42'].max().reset_index()
    max_vor.columns = ['track_id', 'max_vorticity']
    
    # Merge with EP cases
    ep_df = ep_df.copy()
    ep_df = ep_df.merge(max_vor, on='track_id', how='left')
    
    # Filter out cases without vorticity data
    valid = ep_df[ep_df["max_vorticity"].notna()]
    n_valid = len(valid)
    print(f"      Cases with vorticity data: {n_valid}/{len(ep_df)}")
    
    if n_valid < 10:
        print(f"      Warning: Only {n_valid} cases available, using all")
        top10 = valid.nlargest(n_valid, "max_vorticity")
    else:
        top10 = valid.nlargest(10, "max_vorticity")
    
    # Report intensity range
    print(f"      Max |vor42| range: {top10['max_vorticity'].min():.2f} – {top10['max_vorticity'].max():.2f} ×10⁻⁵ s⁻¹")
    
    return top10.drop(columns=["max_vorticity"])


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


def select_ep_cases(ep_num, tracks_df, clustered_df):
    """
    Select all cases from an EP cluster.
    
    IMPORTANT: NO FILTERING by lifecycle - all cyclones in the cluster are used.
    """
    cluster_id = EP_TO_CLUSTER[ep_num]
    ep_label = get_ep_label(ep_num)
    
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
                    "ep": ep_num,
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
    print("STEP 1: SELECT EP1 + EP2 + EP3 CYCLONE TRACKS FOR STRUCTURE ANALYSIS")
    print("=" * 70)
    print()
    print("IMPORTANT: All cyclones from the clusters were already filtered for")
    print("complete lifecycle during the clustering analysis. NO additional")
    print("filtering is applied here to ensure consistency.")
    
    # 1. Load cluster assignments
    print("\n1. Loading cluster assignments...")
    if not CLUSTER_FILE.exists():
        raise FileNotFoundError(f"Cluster file not found: {CLUSTER_FILE}")

    clustered_df = pd.read_csv(CLUSTER_FILE)
    print(f"   Total clustered cyclones: {len(clustered_df)}")
    for cluster_id, ep_num in sorted(CLUSTER_TO_EP.items()):
        n = (clustered_df["cluster"] == cluster_id).sum()
        print(f"   {get_ep_label(ep_num)} (cluster {cluster_id}): {n} cyclones")

    # 2. Load tracks
    print("\n2. Loading track data...")
    tracks_df = load_tracks()
    print(f"   Total tracks in database: {tracks_df['track_id'].nunique()}")

    # 3. Select cases for each EP
    print("\n3. Selecting cases per EP...")

    ep_dfs = {}
    for ep_num in ALL_EPS:
        ep_dfs[ep_num] = select_ep_cases(ep_num, tracks_df, clustered_df)

    # 4. Create EPALL (union of all EPs)
    print("\n── EPALL (all EPs combined) ──")
    epall_df = pd.concat([ep_dfs[ep] for ep in ALL_EPS], ignore_index=True)
    print(f"   Total EPALL cyclones: {len(epall_df)}")
    print(f"   Total timesteps: {epall_df['n_timesteps'].sum()}")

    # 5. Save all cases
    print("\n4. Saving results...")
    for ep_num in ALL_EPS:
        ep_abbrev = get_ep_abbrev(ep_num)
        csv_path = OUTPUT_DIR / f"{ep_abbrev}_cases.csv"
        ep_dfs[ep_num].to_csv(csv_path, index=False)
        print(f"   Saved: {csv_path}")
    
    epall_csv = OUTPUT_DIR / "epall_cases.csv"
    epall_df.to_csv(epall_csv, index=False)
    print(f"   Saved: {epall_csv}")

    # 6. Select and save top-10 most intense cyclones per EP
    print("\n5. Selecting top-10 most intense cyclones per EP...")
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        ep_abbrev = get_ep_abbrev(ep_num)
        top10 = select_top10_intense(ep_dfs[ep_num], tracks_df, ep_label)
        top10_csv = OUTPUT_DIR / f"{ep_abbrev}_top10_intense.csv"
        top10.to_csv(top10_csv, index=False)
        print(f"   Saved: {top10_csv}")

    # 7. Visualisations
    print("\n6. Creating track visualisations...")
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        color = get_ep_color(ep_num)
        plot_tracks(ep_dfs[ep_num], tracks_df, ep_label, color)

    # 8. Summary
    print("\n" + "=" * 70)
    print("STEP 1 COMPLETE")
    print("=" * 70)
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        n_cases = len(ep_dfs[ep_num])
        print(f"   {ep_label} cases: {n_cases}")
    print(f"   EPALL total: {len(epall_df)}")
    print(
        f"\nNext step: python scripts/ep_structure_analysis/step2_download_era5_parallel.py"
    )


if __name__ == "__main__":
    main()
