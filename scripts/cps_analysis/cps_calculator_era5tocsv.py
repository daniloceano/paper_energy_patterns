"""
Cyclone Phase Space (CPS) Calculator for ERA5-style NetCDFs (CSV version).
Uses only z, u, v from the NetCDF and only the first three columns
from the trackfile: date, latitude, longitude.

Usage:
    python cps_calculator_era5rr.py --nc ciclone_ERA5_CPS.nc --track trackfile --dt 3 --output CPS_era5.csv
"""

import argparse
import sys
import numpy as np
import xarray as xr
import pandas as pd
from tqdm import tqdm

GRAVITY = 9.80665          # m/s^2
UNDEF = -999000000.0       # GrADS undefined sentinel


# --------------------------- helpers -----------------------------------------

def parse_trackfile_basic(path, dt_hours=6):
    """
    Parse trackfile: AAAAMMDDHH[MM]  lat  lon  ...

    All records are parsed regardless of hour; the dt_hours parameter
    is kept for API compatibility but the hour-filter is removed so
    that the NetCDF time-matching step selects the appropriate subset.
    This avoids mismatches when the NetCDF time axis is offset from
    round hours (e.g. 01Z, 04Z, 07Z instead of 00Z, 03Z, 06Z).
    Also handles 12-digit DTG with minutes (e.g. 197902261000).
    Returns list of dicts {time (pd.Timestamp), lat, lon}.
    """
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue

            dtg = parts[0][:10]
            lat = float(parts[1])
            lon = float(parts[2])

            hour = int(dtg[8:10])

            # Support optional minutes in 12-digit DTG (YYYYMMDDHHММ)
            minute = 0
            if len(parts[0]) >= 12:
                try:
                    minute = int(parts[0][10:12])
                except ValueError:
                    minute = 0

            ts = pd.Timestamp(
                year=int(dtg[0:4]),
                month=int(dtg[4:6]),
                day=int(dtg[6:8]),
                hour=hour,
                minute=minute,
            )

            records.append({
                "time": ts,
                "lat": lat,
                "lon": lon
            })

    return records


def haversine_km(lat0, lon0, lat2d, lon2d):
    """Great-circle distance [km] from scalar (lat0,lon0) to 2-D arrays."""
    R = 6371.0

    f1 = np.deg2rad(lat0)
    f2 = np.deg2rad(lat2d)

    df = f2 - f1
    dl = np.deg2rad(lon2d - lon0)

    a = (
        np.sin(df / 2) ** 2
        + np.cos(f1) * np.cos(f2) * np.sin(dl / 2) ** 2
    )

    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def interp_to_pressure_vec(z_3d, lev_hpa, target_hpa):
    """
    Vectorised log-pressure linear interpolation
    (lev, lat, lon) -> (lat, lon).
    """
    lev = np.asarray(lev_hpa, dtype=float)

    si = np.argsort(lev)
    lev = lev[si]
    z3 = z_3d[si]

    log_lev = np.log(lev)
    log_tgt = np.log(float(target_hpa))

    if log_tgt < log_lev[0] or log_tgt > log_lev[-1]:
        return np.full(z3.shape[1:], np.nan)

    ih = int(np.searchsorted(log_lev, log_tgt, side="right"))
    il = ih - 1

    il = max(il, 0)
    ih = min(ih, len(lev) - 1)

    lp_lo = log_lev[il]
    lp_hi = log_lev[ih]

    denom = lp_hi - lp_lo

    if denom == 0:
        return z3[il].copy()

    w = (log_tgt - lp_lo) / denom

    return z3[il] + w * (z3[ih] - z3[il])


def storm_bearing(lat1, lon1, lat2, lon2):
    """Meteorological bearing [degrees, CW from N]."""

    dx = (lon2 - lon1) * 111.0 * np.cos(np.deg2rad(lat1))
    dy = (lat2 - lat1) * 111.0

    return (270.0 - np.degrees(np.arctan2(dy, dx))) % 360.0


def to_gpm(z_array):
    """
    Convert geopotential to geopotential metres
    if stored as J/kg (m^2/s^2).
    """
    if np.nanmedian(z_array) > 5000:
        return z_array / GRAVITY

    return z_array


def normalize_dims(ds):
    """
    Normalize ERA5-style coordinate names to lat/lon/lev/time.

    Handles the ERA5 GRIB-derived NetCDF structure where the file has:
      - 'time'       dim  -> integer forecast reference indices (e.g. [0, 1])
      - 'valid_time' coord -> actual datetime64 values (the real time axis)

    In that case we drop the bogus 'time' dim and promote 'valid_time'
    as the new 'time' dimension so the rest of the script works correctly.
    """
    import numpy as np

    # Special case: 'time' exists but contains integers (not datetimes),
    # while 'valid_time' holds the real datetime axis.
    # ERA5 GRIB->NetCDF often produces:
    #   time dim  (size N) = integer reference indices
    #   valid_time coord (time, valid_time) = 2-D datetime array
    # We flatten valid_time into a single 1-D time axis.
    if (
        "time" in ds.dims
        and "valid_time" in ds.coords
        and not np.issubdtype(ds["time"].dtype, np.datetime64)
    ):
        import xarray as xr
        vt = ds["valid_time"]
        times_flat = vt.values.ravel()
        _, unique_idx = np.unique(times_flat, return_index=True)
        times_unique = times_flat[unique_idx]

        # Stack all time-like dims into one flat index, then relabel.
        stack_dims = tuple(d for d in vt.dims)   # e.g. ("time", "valid_time")
        if len(stack_dims) == 1:
            # 1-D case: just rename the coord.
            ds = ds.rename({"time": "_ref_time"})
            ds = ds.rename({"valid_time": "time"})
        else:
            # N-D case: stack all dims that make up valid_time.
            ds = ds.stack(_tidx=stack_dims)
            flat_vt = ds["valid_time"].values
            ds = ds.assign_coords(_tidx=flat_vt)
            ds = ds.rename({"_tidx": "time"})
            # Drop duplicate timestamps arising from stacking.
            _, unique_idx2 = np.unique(flat_vt, return_index=True)
            ds = ds.isel(time=unique_idx2)
        # Drop leftover helper coords if still present.
        for drop in ["valid_time", "_ref_time"]:
            if drop in ds.coords and drop not in ds.dims:
                ds = ds.drop_vars(drop)

    # Standard coordinate renames.
    rename = {}
    for old, new in [
        ("latitude", "lat"),
        ("longitude", "lon"),
        ("pressure", "lev"),
        ("level", "lev"),
        ("plev", "lev"),
        ("pressure_level", "lev"),
        ("valid_time", "time"),
    ]:
        if old in ds.dims and new not in ds.dims:
            rename[old] = new
        elif old in ds.coords and new not in ds.coords and old not in ds.dims:
            rename[old] = new

    if rename:
        ds = ds.rename(rename)

    if "lev" not in ds.coords and "lev" in ds.dims:
        ds = ds.set_coords("lev")

    return ds


# --------------------------- CPS parameters ----------------------------------

def calc_B(
    z_gpm,
    lev_hpa,
    lats,
    lons,
    lat0,
    lon0,
    bearing,
    ptop=600,
    pbot=900,
    critrad=500
):
    """
    B (Hart 2003):
    area-averaged thickness difference
    (right - left hemisphere).
    """

    z_top = interp_to_pressure_vec(z_gpm, lev_hpa, ptop)
    z_bot = interp_to_pressure_vec(z_gpm, lev_hpa, pbot)

    thick = z_top - z_bot

    LON2D, LAT2D = np.meshgrid(lons, lats)

    dx = (
        (LON2D - lon0)
        * 111.0
        * np.cos(np.deg2rad(LAT2D))
    )

    dy = (LAT2D - lat0) * 111.0

    dist = np.sqrt(dx ** 2 + dy ** 2)

    cdir = (
        270.0
        - np.degrees(np.arctan2(dy, dx))
    ) % 360.0

    mind = bearing % 360.0
    maxd = (mind + 180.0) % 360.0

    if maxd > mind:
        right_mask = (cdir >= mind) & (cdir < maxd)
    else:
        right_mask = (cdir >= mind) | (cdir < maxd)

    in_r = right_mask & (dist <= critrad)
    in_l = ~right_mask & (dist <= critrad)

    r_avg = float(np.nanmean(thick[in_r])) if in_r.any() else UNDEF
    l_avg = float(np.nanmean(thick[in_l])) if in_l.any() else UNDEF

    if not np.isfinite(r_avg):
        r_avg = UNDEF

    if not np.isfinite(l_avg):
        l_avg = UNDEF

    return l_avg, r_avg


def calc_VT(
    z_gpm,
    lev_hpa,
    lats,
    lons,
    lat0,
    lon0,
    levs_target,
    drad=500
):
    """
    VT = slope of OLS regression:
    DZ(p) ~ ln(p).
    """

    LON2D, LAT2D = np.meshgrid(lons, lats)

    dist = haversine_km(
        lat0,
        lon0,
        LAT2D,
        LON2D
    )

    inside = dist <= drad

    Sumx = Sumy = Sumx2 = Sumxy = 0.0
    n = 0

    for plev in levs_target:

        z_p = interp_to_pressure_vec(
            z_gpm,
            lev_hpa,
            plev
        )

        z_in = np.where(inside, z_p, np.nan)

        fin = np.isfinite(z_in)

        if not fin.any():
            continue

        mn = float(np.nanmin(z_in[fin]))
        mx = float(np.nanmax(z_in[fin]))

        dz = mx - mn

        lp = np.log(plev)

        Sumx += lp
        Sumy += dz
        Sumx2 += lp * lp
        Sumxy += lp * dz

        n += 1

    denom = Sumx * Sumx - n * Sumx2

    if n < 2 or denom == 0:
        return np.nan

    slope = (Sumx * Sumy - n * Sumxy) / denom

    return float(slope) if abs(slope) <= 2000 else np.nan


def calc_SIZE(u_2d, v_2d, lats, wrad=17):
    """
    Cyclone SIZE = equivalent radius of the area
    where |V| >= wrad m/s.
    """

    inc = abs(float(lats[1] - lats[0]))

    wind = np.sqrt(u_2d ** 2 + v_2d ** 2)

    LAT2D = np.tile(
        lats[:, np.newaxis],
        (1, u_2d.shape[1])
    )

    xsize = (
        np.cos(np.deg2rad(LAT2D))
        * 111.0
        * inc
    )

    ysize = 111.0 * inc

    tot = float(
        np.nansum(
            np.where(
                wind >= wrad,
                xsize * ysize,
                0.0
            )
        )
    )

    return np.sqrt(tot / np.pi)


# --------------------------- main --------------------------------------------

def main():

    ap = argparse.ArgumentParser(
        description="CPS Calculator - Hart (2003) for ERA5"
    )

    ap.add_argument(
        "--nc",
        default="ciclone_ERA5_CPS.nc",
        help="NetCDF file"
    )

    ap.add_argument(
        "--track",
        default="trackfile",
        help="Track file"
    )

    ap.add_argument(
        "--output",
        default="CPS_output.csv",
        help="Output CSV"
    )

    ap.add_argument(
        "--drad",
        type=float,
        default=500,
        help="VT radius [km]"
    )

    ap.add_argument(
        "--wrad",
        type=float,
        default=17,
        help="Wind threshold SIZE [m/s]"
    )

    ap.add_argument(
        "--ptop",
        type=float,
        default=600,
        help="B upper level [hPa]"
    )

    ap.add_argument(
        "--pbot",
        type=float,
        default=900,
        help="B lower level [hPa]"
    )

    ap.add_argument(
        "--dt",
        type=int,
        default=6,
        help="Synoptic cadence [h]"
    )

    args = ap.parse_args()

    LEVS_VTU = [600, 550, 500, 450, 400, 350, 300]
    LEVS_VTL = [900, 850, 800, 750, 700, 650, 600]

    print("=" * 62)
    print("  Cyclone Phase Space (CPS) Calculator  -  Hart (2003)")
    print("=" * 62)

    print(f"\n[1/5] Loading NetCDF: {args.nc}")

    ds = xr.open_dataset(args.nc)

    ds = normalize_dims(ds)

    if "lev" not in ds.coords and "lev" not in ds.dims:
        raise KeyError(
            "Missing pressure coordinate: expected 'lev'"
        )

    if "time" not in ds.coords and "time" not in ds.dims:
        raise KeyError(
            "Missing time coordinate: expected 'time'"
        )

    if ds["lev"].values.max() > 2000:
        ds["lev"] = ds["lev"] / 100.0
        ds["lev"].attrs["units"] = "hPa"

    if ds["lat"].values[0] > ds["lat"].values[-1]:
        ds = ds.reindex(lat=ds["lat"][::-1])

    if ds["lon"].values[0] > ds["lon"].values[-1]:
        ds = ds.reindex(lon=ds["lon"][::-1])

    nc_times = pd.DatetimeIndex(ds["time"].values)

    tolerance = pd.Timedelta(hours=3)

    print(
        f"      NetCDF steps: {len(nc_times)}"
        f"  |  match tolerance: 3 h"
    )

    print(f"[2/5] Parsing track file: {args.track}")

    track = parse_trackfile_basic(
        args.track,
        dt_hours=args.dt
    )

    print(f"      {len(track)} records in track file")

    print("[3/5] Matching track times to NetCDF time axis ...")

    # For every track record find the nearest NetCDF step within tolerance.
    candidates = []
    for rec in track:
        diff = abs(nc_times - rec["time"])
        idx = int(diff.argmin())
        if diff[idx] <= tolerance:
            candidates.append({**rec, "nc_tidx": idx, "_diff": diff[idx]})

    # Deduplicate: keep only the closest track record per NetCDF step.
    best = {}
    for c in candidates:
        tidx = c["nc_tidx"]
        if tidx not in best or c["_diff"] < best[tidx]["_diff"]:
            best[tidx] = c

    matched = [best[k] for k in sorted(best)]
    for m in matched:
        m.pop("_diff", None)

    print(f"      {len(matched)} matched time steps")

    if not matched:
        sys.exit(
            "ERROR: No track records matched NetCDF times."
        )

    print("[4/5] Computing CPS parameters ...")

    pbar = tqdm(
        total=len(matched) * 4,
        unit="task",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} "
                   "[{elapsed}<{remaining}]  {desc}"
    )

    results = []

    N = len(matched)

    for i, rec in enumerate(matched):

        ts = rec["time"]
        lat0 = rec["lat"]
        lon0 = rec["lon"]
        tidx = rec["nc_tidx"]

        label = ts.strftime("%HZ%d%b%Y").upper()

        first = (i == 0)

        ds_t = ds.isel(time=tidx)

        lev_hpa = ds_t["lev"].values.astype(float)

        if first:
            bearing = 0.0
        else:
            p = matched[i - 1]

            bearing = storm_bearing(
                p["lat"],
                p["lon"],
                lat0,
                lon0
            )

        pbar.set_description(f"[{i + 1}/{N}] {label} B")

        if first:
            left = right = UNDEF

        else:
            try:

                z_raw = ds_t["z"].sel(
                    lat=slice(lat0 - 7, lat0 + 7),
                    lon=slice(lon0 - 15, lon0 + 15)
                ).values

                if z_raw.ndim == 4:
                    z_raw = z_raw[0]

                z_gpm = to_gpm(z_raw)

                lats_b = ds_t["lat"].sel(
                    lat=slice(lat0 - 7, lat0 + 7)
                ).values

                lons_b = ds_t["lon"].sel(
                    lon=slice(lon0 - 15, lon0 + 15)
                ).values

                left, right = calc_B(
                    z_gpm,
                    lev_hpa,
                    lats_b,
                    lons_b,
                    lat0,
                    lon0,
                    bearing,
                    ptop=args.ptop,
                    pbot=args.pbot
                )

            except Exception as e:
                print(f"\nWARNING B [{label}]: {e}")

                left = right = UNDEF

        pbar.update(1)

        try:

            z_vt_raw = ds_t["z"].sel(
                lat=slice(lat0 - 30, lat0 + 30),
                lon=slice(lon0 - 30, lon0 + 30)
            ).values

            if z_vt_raw.ndim == 4:
                z_vt_raw = z_vt_raw[0]

            z_vt_gpm = to_gpm(z_vt_raw)

            lats_vt = ds_t["lat"].sel(
                lat=slice(lat0 - 30, lat0 + 30)
            ).values

            lons_vt = ds_t["lon"].sel(
                lon=slice(lon0 - 30, lon0 + 30)
            ).values

        except Exception as e:

            z_vt_gpm = None

            print(f"\nWARNING VT extract [{label}]: {e}")

        pbar.set_description(f"[{i + 1}/{N}] {label} VTL")

        if first:
            vtl = UNDEF

        elif z_vt_gpm is None:
            vtl = np.nan

        else:
            try:

                vtl = calc_VT(
                    z_vt_gpm,
                    lev_hpa,
                    lats_vt,
                    lons_vt,
                    lat0,
                    lon0,
                    LEVS_VTL,
                    drad=args.drad
                )

            except Exception as e:
                print(f"\nWARNING VTL [{label}]: {e}")

                vtl = np.nan

        pbar.update(1)

        pbar.set_description(f"[{i + 1}/{N}] {label} VTU")

        if first:
            vtu = UNDEF

        elif z_vt_gpm is None:
            vtu = np.nan

        else:
            try:

                vtu = calc_VT(
                    z_vt_gpm,
                    lev_hpa,
                    lats_vt,
                    lons_vt,
                    lat0,
                    lon0,
                    LEVS_VTU,
                    drad=args.drad
                )

            except Exception as e:
                print(f"\nWARNING VTU [{label}]: {e}")

                vtu = np.nan

        pbar.update(1)

        pbar.set_description(f"[{i + 1}/{N}] {label} SIZE")

        try:

            u_raw = ds_t["u"].sel(
                lev=925,
                method="nearest"
            ).sel(
                lat=slice(lat0 - 10, lat0 + 10),
                lon=slice(lon0 - 16, lon0 + 16)
            ).values

            v_raw = ds_t["v"].sel(
                lev=925,
                method="nearest"
            ).sel(
                lat=slice(lat0 - 10, lat0 + 10),
                lon=slice(lon0 - 16, lon0 + 16)
            ).values

            lats_sz = ds_t["lat"].sel(
                lat=slice(lat0 - 10, lat0 + 10)
            ).values

            if u_raw.ndim == 3:
                u_raw = u_raw[0]

            if v_raw.ndim == 3:
                v_raw = v_raw[0]

            size = calc_SIZE(
                u_raw,
                v_raw,
                lats_sz,
                wrad=args.wrad
            )

        except Exception as e:

            print(f"\nWARNING SIZE [{label}]: {e}")

            size = np.nan

        pbar.update(1)

        def fmt(v):

            if v == UNDEF:
                return UNDEF

            if isinstance(v, (float, np.floating)) and np.isfinite(v):
                return round(float(v), 3)

            return v

        results.append({
            "time": label,
            "B_left": fmt(left),
            "B_right": fmt(right),
            "dir": round(bearing, 7),
            "SIZE": fmt(size),
            "VTL": fmt(vtl),
            "VTU": fmt(vtu),
        })

    pbar.close()

    ds.close()

    print(f"\n[5/5] Writing output: {args.output}")

    df = pd.DataFrame(results)

    df.to_csv(args.output, index=False)

    print(f"\n✓ Saved -> {args.output} ({len(results)} rows)")

    print()
    print("Reminder:")
    print("B_left, B_right, VTL, VTU = -999000000 at t=0")
    print("(no prior position to compute storm motion direction).")


if __name__ == "__main__":
    main()
