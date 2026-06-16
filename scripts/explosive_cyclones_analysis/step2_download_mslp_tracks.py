"""
Step 2: Download storm-following ERA5 MSLP over the FULL track of each cyclone.

The bomb criterion needs a continuous central-pressure time series (>= 24 h), so
unlike the composite analysis (which only keeps the central timesteps), here we
download mean sea level pressure (`msl`) at every track timestep, over a moving
bounding box that follows the cyclone, with a small padding so that centred 24 h
deepening windows are available at the ends of the track.

HEAVY / REMOTE STEP. The CDS API throttles parallel requests, so keep parallelism
LIGHT here (a handful of jobs). The heavy compute is in step3.

Inputs:
    results/explosive_cyclones/tracks_by_ep.csv   (from step1)

Outputs (data/era5_explosive_cyclones/, git-ignored, kept on the remote server):
    {track_id}_mslp.nc        msl(time, latitude, longitude) over the track box
    {track_id}_metadata.csv   provenance (box, period, n_times)

Run (remote server):
    python scripts/explosive_cyclones_analysis/step2_download_mslp_tracks.py --jobs 6
    # smoke test on a few cyclones:
    python scripts/explosive_cyclones_analysis/step2_download_mslp_tracks.py --sample 5 --jobs 3

Author: Danilo Couto de Souza
Date: June 2026
"""

import sys
import time
import logging
import argparse
import multiprocessing as mp
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import xarray as xr
import cdsapi
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACKS_FILE = PROJECT_ROOT / "results" / "explosive_cyclones" / "tracks_by_ep.csv"
DATA_DIR = PROJECT_ROOT / "data" / "era5_explosive_cyclones"
LOG_DIR = PROJECT_ROOT / "logs"

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
BOX_BUFFER_DEG = 6.0      # padding around the track envelope (search radius < this)
TIME_PAD_HOURS = 12       # padding before genesis / after lysis for centred windows
DEFAULT_JOBS = 6          # KEEP LIGHT — CDS API throttles concurrent requests
DEFAULT_DROP_INVALID_DAYS = True

CDS_DATASET = "reanalysis-era5-single-levels"
CDS_VARIABLE = "mean_sea_level_pressure"


def _coord_name(ds, candidates):
    for c in candidates:
        if c in ds.coords or c in ds.dims:
            return c
    return None


def validate_mslp_file(nc_file, t_start, t_end):
    """Return True if the file exists, has `msl`, and covers [t_start, t_end]."""
    if not nc_file.exists():
        return False
    try:
        with xr.open_dataset(nc_file) as ds:
            if "msl" not in ds.data_vars:
                return False
            tc = _coord_name(ds, ["valid_time", "time"])
            if tc is None or ds[tc].size == 0:
                return False
            tmin = pd.to_datetime(ds[tc].values.min())
            tmax = pd.to_datetime(ds[tc].values.max())
            # allow a 1 h tolerance at the edges
            return (tmin <= t_start + pd.Timedelta("1h")) and (tmax >= t_end - pd.Timedelta("1h"))
    except Exception:
        return False


def compute_request(track_df):
    """Build (area, years, months, days, times, t_start, t_end) for one cyclone."""
    t = pd.to_datetime(track_df["date"])
    t_start = t.min() - pd.Timedelta(hours=TIME_PAD_HOURS)
    t_end = t.max() + pd.Timedelta(hours=TIME_PAD_HOURS)

    lats = track_df["lat vor"].astype(float).values
    lons = track_df["lon vor"].astype(float).values
    north = min(90.0, lats.max() + BOX_BUFFER_DEG)
    south = max(-90.0, lats.min() - BOX_BUFFER_DEG)
    west = lons.min() - BOX_BUFFER_DEG
    east = lons.max() + BOX_BUFFER_DEG
    area = [north, west, south, east]  # CDS order: N, W, S, E

    hours = pd.date_range(t_start.floor("h"), t_end.ceil("h"), freq="h")
    years = sorted({f"{d.year}" for d in hours})
    months = sorted({f"{d.month:02d}" for d in hours})
    days = sorted({f"{d.day:02d}" for d in hours})
    times = [f"{h:02d}:00" for h in range(24)]
    return area, years, months, days, times, t_start, t_end


def download_one(args):
    track_id, track_df = args
    out_nc = DATA_DIR / f"{track_id}_mslp.nc"
    area, years, months, days, times, t_start, t_end = compute_request(track_df)

    if validate_mslp_file(out_nc, t_start, t_end):
        return (track_id, "skip")

    tmp = DATA_DIR / f"{track_id}_mslp_raw.nc"
    try:
        c = cdsapi.Client(quiet=True)
        c.retrieve(
            CDS_DATASET,
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": CDS_VARIABLE,
                "year": years,
                "month": months,
                "day": days,
                "time": times,
                "area": area,
            },
            str(tmp),
        )
        # Trim to the exact padded window to drop extra days from month spillover
        ds = xr.open_dataset(tmp)
        tc = _coord_name(ds, ["valid_time", "time"])
        ds = ds.sortby(tc).sel({tc: slice(t_start, t_end)})
        ds.to_netcdf(out_nc)
        ds.close()
        tmp.unlink(missing_ok=True)

        meta = {
            "track_id": track_id,
            "ep": int(track_df["ep"].iloc[0]),
            "t_start": t_start.isoformat(),
            "t_end": t_end.isoformat(),
            "n_track_times": int(len(track_df)),
            "north": area[0], "west": area[1], "south": area[2], "east": area[3],
            "variable": CDS_VARIABLE,
            "downloaded": datetime.now().isoformat(timespec="seconds"),
        }
        pd.DataFrame([meta]).to_csv(DATA_DIR / f"{track_id}_metadata.csv", index=False)
        return (track_id, "ok")
    except Exception as e:
        logging.error(f"{track_id}: {e}")
        tmp.unlink(missing_ok=True)
        return (track_id, f"fail: {e}")


def main():
    ap = argparse.ArgumentParser(description="Download storm-following ERA5 MSLP per cyclone")
    ap.add_argument("--jobs", type=int, default=DEFAULT_JOBS,
                    help=f"Parallel CDS requests — keep light (default {DEFAULT_JOBS})")
    ap.add_argument("--sample", type=int, default=0, help="Only the first N cyclones (smoke test)")
    ap.add_argument("--ep", type=int, choices=[1, 2, 3], default=None, help="Restrict to one EP")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_DIR / f"explosive_mslp_download_{ts}.log"),
                  logging.StreamHandler(sys.stderr)],
    )

    if not TRACKS_FILE.exists():
        print(f"❌ Missing {TRACKS_FILE}. Run step1 first.")
        return 1

    tracks = pd.read_csv(TRACKS_FILE)
    if args.ep is not None:
        tracks = tracks[tracks["ep"] == args.ep]

    groups = [(int(tid), df) for tid, df in tracks.groupby("track_id")]
    if args.sample:
        groups = groups[: args.sample]

    if args.jobs > 8:
        print(f"⚠️  {args.jobs} jobs may exceed CDS limits (recommended 4-6).")

    print("=" * 70)
    print("STEP 2: Download storm-following ERA5 MSLP")
    print(f"  Cyclones: {len(groups)}  |  Jobs: {args.jobs}  |  Box buffer: {BOX_BUFFER_DEG}°")
    print(f"  Output: {DATA_DIR}")
    print("=" * 70)

    t0 = time.time()
    counts = {"ok": 0, "skip": 0, "fail": 0}
    with mp.Pool(processes=args.jobs) as pool:
        for tid, status in tqdm(pool.imap_unordered(download_one, groups),
                                total=len(groups), desc="MSLP download"):
            key = "fail" if status.startswith("fail") else status
            counts[key] += 1

    print(f"\nDone in {(time.time() - t0) / 60:.1f} min  |  "
          f"ok={counts['ok']}  skip={counts['skip']}  fail={counts['fail']}")
    if counts["fail"]:
        print("  ⚠️  Some downloads failed — re-run to retry (resumable).")
    print("  Next: python scripts/explosive_cyclones_analysis/step3_assign_central_pressure.py")
    return 0


if __name__ == "__main__":
    main()
