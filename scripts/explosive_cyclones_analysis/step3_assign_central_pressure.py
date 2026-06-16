"""
Step 3: Assign a central MSLP to each track timestep (the "A+B" method).

For each cyclone and each (hourly) track position given by the 850-hPa vorticity
centre, we locate the surface low by GRADIENT DESCENT on the MSLP field, starting
from the vorticity centre and walking downhill to the bottom of the pressure basin
the centre belongs to (the "B" part). The result is accepted only if that bottom is
a genuine LOCAL INTERIOR MINIMUM within a search radius R0 (the "A" part):

    - found within R0 (deg)                       -> flag "ok"
    - not found within R0, found within R1         -> flag "expanded"
    - the descent leaves the radius (no closed low) -> flag "no_interior_min", MSLP = NaN
    - jumps > MAX_JUMP from the previous valid centre -> additionally flagged "jump"

Because descent follows the basin the vorticity centre drains into, a deeper minimum
belonging to a NEIGHBOURING system (across a col) never hijacks the centre, even if
its value is lower. A boundary-touching minimum is rejected rather than used.

A best-effort `over_land` flag marks continental positions, where MSLP reduction
(e.g. over the Andes) is less reliable. It is left as NaN if land polygons are
unavailable (offline compute node).

HEAVY / REMOTE STEP — pure CPU, embarrassingly parallel over cyclones. Use many
workers (e.g. --workers 100).

Inputs:
    results/explosive_cyclones/tracks_by_ep.csv      (step1)
    data/era5_explosive_cyclones/{track_id}_mslp.nc  (step2)

Output:
    results/explosive_cyclones/central_pressure_timeseries.csv

Run:
    python scripts/explosive_cyclones_analysis/step3_assign_central_pressure.py --workers 100

Author: Danilo Couto de Souza
Date: June 2026
"""

import sys
import argparse
import multiprocessing as mp
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACKS_FILE = PROJECT_ROOT / "results" / "explosive_cyclones" / "tracks_by_ep.csv"
DATA_DIR = PROJECT_ROOT / "data" / "era5_explosive_cyclones"
OUT_FILE = PROJECT_ROOT / "results" / "explosive_cyclones" / "central_pressure_timeseries.csv"

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
R0_DEG = 3.0       # primary search radius around the vorticity centre
R1_DEG = 5.0       # expanded radius, tried once if nothing is found within R0
MAX_JUMP_DEG = 4.0  # continuity: flag centres that jump more than this between steps
MAX_DESCENT_STEPS = 600

# Best-effort land mask (built once per worker process)
_LAND_PREP = None


def _init_worker():
    """Build a prepared land geometry once per process (best effort)."""
    global _LAND_PREP
    try:
        import cartopy.io.shapereader as shpreader
        from shapely.ops import unary_union
        from shapely.prepared import prep
        geoms = list(shpreader.Reader(shpreader.natural_earth(
            resolution="110m", category="physical", name="land")).geometries())
        _LAND_PREP = prep(unary_union(geoms))
    except Exception:
        _LAND_PREP = None


def _over_land(lat, lon):
    if _LAND_PREP is None or not np.isfinite(lat) or not np.isfinite(lon):
        return np.nan
    try:
        from shapely.geometry import Point
        return bool(_LAND_PREP.contains(Point(float(lon), float(lat))))
    except Exception:
        return np.nan


def _haversine_deg(lat1, lon1, lat2, lon2):
    """Great-circle angular distance in degrees."""
    r1, r2 = np.radians(lat1), np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(r1) * np.cos(r2) * np.sin(dlon / 2) ** 2
    return np.degrees(2 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0))))


def find_center(P, lat_arr, lon_arr, lat0, lon0, r_cap):
    """Gradient-descent to the local interior minimum within r_cap of (lat0, lon0).

    Returns dict(lat, lon, mslp, offset) or None if the basin bottom lies outside
    r_cap (open wave / displaced surface low / boundary-touching minimum).
    """
    nlat, nlon = P.shape
    i = int(np.argmin(np.abs(lat_arr - lat0)))
    j = int(np.argmin(np.abs(lon_arr - lon0)))

    for _ in range(MAX_DESCENT_STEPS):
        cur = P[i, j]
        bi, bj, best = i, j, cur
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < nlat and 0 <= nj < nlon and P[ni, nj] < best:
                    best, bi, bj = P[ni, nj], ni, nj
        if (bi, bj) == (i, j):
            break  # reached a strict local minimum
        i, j = bi, bj
        if _haversine_deg(lat0, lon0, lat_arr[i], lon_arr[j]) > r_cap:
            return None  # basin bottom is outside the search disk

    # Safety: must be a true interior cell of the field (box has >= 6 deg buffer)
    if i in (0, nlat - 1) or j in (0, nlon - 1):
        return None
    off = _haversine_deg(lat0, lon0, lat_arr[i], lon_arr[j])
    if off > r_cap:
        return None
    return {"lat": float(lat_arr[i]), "lon": float(lon_arr[j]),
            "mslp": float(P[i, j]), "offset": float(off)}


def _coord_name(ds, candidates):
    for c in candidates:
        if c in ds.coords or c in ds.dims:
            return c
    return None


def process_cyclone(args):
    """Worker: assign central pressure for every timestep of one cyclone."""
    track_id, df = args
    nc = DATA_DIR / f"{track_id}_mslp.nc"
    if not nc.exists():
        return pd.DataFrame()

    try:
        ds = xr.open_dataset(nc)
        tc = _coord_name(ds, ["valid_time", "time"])
        latn = _coord_name(ds, ["latitude", "lat"])
        lonn = _coord_name(ds, ["longitude", "lon"])
        ds = ds.sortby(tc)
        P = ds["msl"].values.astype("float64") / 100.0  # Pa -> hPa, [ntime,nlat,nlon]
        times = pd.DatetimeIndex(ds[tc].values)
        lat_arr = ds[latn].values.astype("float64")
        lon_arr = ds[lonn].values.astype("float64")
        ds.close()
    except Exception:
        return pd.DataFrame()

    df = df.copy()
    df["t"] = pd.to_datetime(df["date"])

    rows = []
    prev_lat = prev_lon = None
    for _, r in df.iterrows():
        t = r["t"]
        lat0, lon0 = float(r["lat vor"]), float(r["lon vor"])
        idx = times.get_indexer([t], method="nearest", tolerance=pd.Timedelta("1h"))[0]

        rec = {"track_id": track_id, "ep": int(r["ep"]), "time": t,
               "vor_lat": lat0, "vor_lon": lon0,
               "central_lat": np.nan, "central_lon": np.nan, "central_mslp": np.nan,
               "offset_deg": np.nan, "radius_used": np.nan,
               "flag": "no_field", "over_land": np.nan, "jump_deg": np.nan}

        if idx != -1:
            field = P[idx]
            res = find_center(field, lat_arr, lon_arr, lat0, lon0, R0_DEG)
            flag, radius = "ok", R0_DEG
            if res is None:
                res = find_center(field, lat_arr, lon_arr, lat0, lon0, R1_DEG)
                flag, radius = "expanded", R1_DEG
            if res is None:
                flag, radius = "no_interior_min", np.nan
            else:
                if prev_lat is not None:
                    jump = _haversine_deg(prev_lat, prev_lon, res["lat"], res["lon"])
                    rec["jump_deg"] = jump
                    if jump > MAX_JUMP_DEG:
                        flag = "jump"
                rec.update(central_lat=res["lat"], central_lon=res["lon"],
                           central_mslp=res["mslp"], offset_deg=res["offset"],
                           radius_used=radius, over_land=_over_land(res["lat"], res["lon"]))
                prev_lat, prev_lon = res["lat"], res["lon"]
            rec["flag"] = flag
        rows.append(rec)

    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description="Assign central MSLP to vorticity tracks (A+B)")
    ap.add_argument("--workers", type=int, default=min(8, mp.cpu_count()),
                    help="CPU workers — heavy parallelism OK (e.g. 100 on a server)")
    ap.add_argument("--sample", type=int, default=0, help="Only the first N cyclones")
    ap.add_argument("--ep", type=int, choices=[1, 2, 3], default=None, help="Restrict to one EP")
    args = ap.parse_args()

    if not TRACKS_FILE.exists():
        print(f"❌ Missing {TRACKS_FILE}. Run step1 first.")
        return 1

    tracks = pd.read_csv(TRACKS_FILE)
    if args.ep is not None:
        tracks = tracks[tracks["ep"] == args.ep]
    groups = [(int(tid), df) for tid, df in tracks.groupby("track_id")]
    if args.sample:
        groups = groups[: args.sample]

    # Only process cyclones whose MSLP file is present (lets step3 run while step2
    # is still downloading the rest)
    present = [(tid, df) for tid, df in groups if (DATA_DIR / f"{tid}_mslp.nc").exists()]
    n_missing = len(groups) - len(present)

    print("=" * 70)
    print("STEP 3: Assign central pressure (A+B gradient descent)")
    print(f"  Cyclones with MSLP: {len(present)}  |  missing downloads: {n_missing}")
    print(f"  Workers: {args.workers}  |  R0={R0_DEG}° R1={R1_DEG}° max_jump={MAX_JUMP_DEG}°")
    print("=" * 70)
    if not present:
        print("❌ No MSLP files found. Run step2 first.")
        return 1

    parts = []
    with mp.Pool(processes=args.workers, initializer=_init_worker) as pool:
        for part in tqdm(pool.imap_unordered(process_cyclone, present),
                         total=len(present), desc="central pressure"):
            if len(part):
                parts.append(part)

    out = pd.concat(parts, ignore_index=True).sort_values(["track_id", "time"])
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)

    # Quick diagnostics
    valid = out["central_mslp"].notna()
    print(f"\nWrote {OUT_FILE}  ({len(out)} rows, {out['track_id'].nunique()} cyclones)")
    print(f"  valid central pressures: {valid.sum()}/{len(out)} ({100*valid.mean():.1f}%)")
    print("  flag breakdown:")
    for flag, n in out["flag"].value_counts().items():
        print(f"    {flag:16s}: {n}")
    if valid.any():
        q = out.loc[valid, "offset_deg"].quantile([0.5, 0.9, 0.99])
        print(f"  offset_deg (vor->MSLP min): median={q[0.5]:.2f}, "
              f"p90={q[0.9]:.2f}, p99={q[0.99]:.2f}")
    print("  Next: python scripts/explosive_cyclones_analysis/step4_compute_ndr_classify.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
