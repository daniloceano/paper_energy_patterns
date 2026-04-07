"""
Audit storm-centering for ERA5 EP structure NetCDF files.

Creates a CSV audit with one row per track/timestep containing:
 - track_id, t_idx, timestamp
 - cyclone_lat, cyclone_lon (from local tracks CSV)
 - center_used_lat, center_used_lon (intensification center / metadata)
 - dataset_lat_min/max, lon_min/max
 - relative offsets (deg)
 - distance_km between cyclone center and center_used
 - storm_centered_ok (distance_deg <= 2.0)

Also writes a short text report summarizing issues.

Author: Copilot (surgical audit script)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import xarray as xr
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRACKS_FILE = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"

# Threshold (degrees) to consider cyclone centered
CENTERING_DEG_THRESHOLD = 2.0  # degrees (~220 km)


def haversine_km(lat1, lon1, lat2, lon2):
    # Returns distance in km between two (lat, lon) pairs (handles antimeridian)
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    # normalize longitude difference to [-180, 180]
    dlon = lon2 - lon1
    dlon = (dlon + 180) % 360 - 180
    dlambda = math.radians(dlon)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def main():
    # Load tracks (local)
    if not TRACKS_FILE.exists():
        raise FileNotFoundError(f"Tracks file not found: {TRACKS_FILE}")

    tracks = pd.read_csv(TRACKS_FILE, parse_dates=["date"])  # columns: track_id, date, lon vor, lat vor

    records = []
    nc_files = sorted(DATA_DIR.glob("*_era5.nc"))
    for nc in nc_files:
        track_id = nc.name.split("_")[0]
        meta_file = DATA_DIR / f"{track_id}_metadata.csv"
        if meta_file.exists():
            meta = pd.read_csv(meta_file).iloc[0].to_dict()
            center_used_lat = float(meta.get("track_center_lat", np.nan))
            center_used_lon = float(meta.get("track_center_lon", np.nan))
            domain = {k: float(meta[k]) for k in ["north", "south", "east", "west"]}
        else:
            center_used_lat, center_used_lon = np.nan, np.nan
            domain = {"north": np.nan, "south": np.nan, "east": np.nan, "west": np.nan}

        try:
            ds = xr.open_dataset(nc)
            tc = "valid_time" if "valid_time" in ds.dims else "time"
            times = ds[tc].values

            lats = ds["latitude"].values
            lons = ds["longitude"].values
            lat_min, lat_max = float(lats.min()), float(lats.max())
            lon_min, lon_max = float(lons.min()), float(lons.max())

            # subset tracks for this cyclone
            tdf = tracks[tracks["track_id"].astype(str) == str(track_id)].copy()
            if tdf.empty:
                # no track info available locally
                for t_idx, tval in enumerate(times):
                    records.append({
                        "track_id": track_id,
                        "t_idx": int(t_idx),
                        "timestamp": pd.to_datetime(tval).isoformat(),
                        "cyclone_lat": np.nan,
                        "cyclone_lon": np.nan,
                        "center_used_lat": center_used_lat,
                        "center_used_lon": center_used_lon,
                        "ds_lat_min": lat_min,
                        "ds_lat_max": lat_max,
                        "ds_lon_min": lon_min,
                        "ds_lon_max": lon_max,
                        "delta_lat_deg": np.nan,
                        "delta_lon_deg": np.nan,
                        "distance_km": np.nan,
                        "storm_centered_ok": False,
                    })
                ds.close()
                continue

            # ensure datetime
            if "date" in tdf.columns:
                tdf["date"] = pd.to_datetime(tdf["date"])

            for t_idx, tval in enumerate(times):
                t_ts = pd.to_datetime(tval)
                # find nearest track time
                diffs = (tdf["date"] - t_ts).abs()
                nearest = tdf.loc[diffs.idxmin()]
                cyclone_lat = float(nearest["lat vor"]) if "lat vor" in nearest.index else float(nearest.get("lat", np.nan))
                cyclone_lon = float(nearest["lon vor"]) if "lon vor" in nearest.index else float(nearest.get("lon", np.nan))

                delta_lat = cyclone_lat - center_used_lat if not np.isnan(center_used_lat) else np.nan
                delta_lon = cyclone_lon - center_used_lon if not np.isnan(center_used_lon) else np.nan
                distance = haversine_km(cyclone_lat, cyclone_lon, center_used_lat, center_used_lon) if (not np.isnan(center_used_lat) and not np.isnan(cyclone_lat)) else np.nan

                centered_ok = False
                if not np.isnan(distance):
                    # convert deg threshold to km roughly
                    centered_ok = distance <= (CENTERING_DEG_THRESHOLD * 111.0)

                records.append({
                    "track_id": track_id,
                    "t_idx": int(t_idx),
                    "timestamp": t_ts.isoformat(),
                    "cyclone_lat": cyclone_lat,
                    "cyclone_lon": cyclone_lon,
                    "center_used_lat": center_used_lat,
                    "center_used_lon": center_used_lon,
                    "ds_lat_min": lat_min,
                    "ds_lat_max": lat_max,
                    "ds_lon_min": lon_min,
                    "ds_lon_max": lon_max,
                    "delta_lat_deg": delta_lat,
                    "delta_lon_deg": delta_lon,
                    "distance_km": distance,
                    "storm_centered_ok": bool(centered_ok),
                })

            ds.close()
        except Exception as e:
            # record failure
            records.append({
                "track_id": track_id,
                "t_idx": -1,
                "timestamp": None,
                "cyclone_lat": None,
                "cyclone_lon": None,
                "center_used_lat": center_used_lat,
                "center_used_lon": center_used_lon,
                "ds_lat_min": None,
                "ds_lat_max": None,
                "ds_lon_min": None,
                "ds_lon_max": None,
                "delta_lat_deg": None,
                "delta_lon_deg": None,
                "distance_km": None,
                "storm_centered_ok": False,
                "error": str(e),
            })

    df = pd.DataFrame.from_records(records)
    out_csv = RESULTS_DIR / "storm_centering_audit.csv"
    df.to_csv(out_csv, index=False)

    # Summary report
    total = len(df)
    ok = df["storm_centered_ok"].sum()
    missing = df["cyclone_lat"].isna().sum()
    failures = df["distance_km"].isna().sum()

    report_lines = [
        f"Storm-centering audit\n",
        f"Total timesteps checked: {total}\n",
        f"Centered (<= {CENTERING_DEG_THRESHOLD} deg): {int(ok)}\n",
        f"Missing cyclone positions (no local track): {int(missing)}\n",
        f"Timesteps with read errors: {int(failures)}\n",
        "Top 20 largest distances (km):\n",
    ]

    top = df[~df["distance_km"].isna()].sort_values("distance_km", ascending=False).head(20)
    for _, row in top.iterrows():
        report_lines.append(f"{row['track_id']} t{int(row['t_idx'])} {row['timestamp']} dist_km={row['distance_km']:.1f} km (delta_deg=({row['delta_lat_deg']:.2f},{row['delta_lon_deg']:.2f}))\n")

    report_lines.append(f"\nAudit CSV: {out_csv}\n")
    report_txt = RESULTS_DIR / "storm_centering_audit_report.txt"
    with open(report_txt, "w") as fh:
        fh.writelines(report_lines)

    print("Audit complete")
    print(f"CSV: {out_csv}")
    print(f"Report: {report_txt}")


if __name__ == '__main__':
    main()
