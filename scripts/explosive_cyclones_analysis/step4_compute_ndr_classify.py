"""
Step 4: Compute the Normalized Deepening Rate (NDR) and classify bombs by EP.

Sanders & Gyakum (1980): a cyclone is "explosive" (a bomb) when the central-pressure
deepening reaches >= 1 Bergeron, geostrophically adjusted with the SINE of latitude
(reference 60 deg, because the threshold scales with the Coriolis parameter f ~ sin phi):

    NDR = (dP_24h / 24 hPa) * (sin 60 deg / |sin phi|)        [Bergeron]

where dP_24h = p(t) - p(t+24h) (positive = deepening) and phi is the mean latitude
over the window. We slide a centred 24 h window over the whole track and take the
MAXIMUM NDR per cyclone, reported both over the full life cycle and restricted to the
intensification phase. We also report a 6-hourly-subsampled value for comparability
with the synoptic-resolution literature.

Intensity classes (AABC 2024): weak [1.0, 1.3), moderate [1.3, 1.8], intense (> 1.8).

Inputs:
    results/explosive_cyclones/central_pressure_timeseries.csv  (step3)
    results/explosive_cyclones/tracks_by_ep.csv                 (step1; intensification window)

Outputs:
    results/explosive_cyclones/ndr_by_cyclone.csv
    results/explosive_cyclones/bomb_frequency_by_ep.csv

Run:
    python scripts/explosive_cyclones_analysis/step4_compute_ndr_classify.py

Author: Danilo Couto de Souza
Date: June 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from scripts.utils.ep_mapping import ALL_EPS, get_ep_label, EP_COUNTS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "results" / "explosive_cyclones"
CP_FILE = OUT_DIR / "central_pressure_timeseries.csv"
TRACKS_FILE = OUT_DIR / "tracks_by_ep.csv"

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
WINDOW_H = 24          # deepening window (hours)
GAP_FILL_H = 2         # interpolate central-pressure gaps up to this many hours
SIN60 = np.sin(np.radians(60.0))
BOMB_THRESHOLD = 1.0   # Bergeron
CLASS_EDGES = [(1.0, 1.3, "weak"), (1.3, 1.8, "moderate"), (1.8, np.inf, "intense")]


def classify(ndr):
    if not np.isfinite(ndr) or ndr < BOMB_THRESHOLD:
        return "non-explosive"
    for lo, hi, name in CLASS_EDGES:
        if lo <= ndr < hi or (hi == np.inf and ndr >= lo):
            return name
    return "non-explosive"


def max_ndr(p, lat, cadence_h, center_mask=None):
    """Max NDR over centred WINDOW_H windows on an evenly-spaced (cadence_h) series.

    p, lat: pandas Series indexed by a regular DatetimeIndex (cadence_h spacing).
    center_mask: optional boolean Series (same index) — True where the window CENTER
                 must lie to be counted (used for the intensification scope).
    Returns (ndr_max, time_of_max).
    """
    steps = WINDOW_H // cadence_h
    if len(p) <= steps:
        return np.nan, pd.NaT
    vals = p.values
    lats = lat.values
    idx = p.index
    best, best_t = np.nan, pd.NaT
    for k in range(len(p) - steps):
        p0, p1 = vals[k], vals[k + steps]
        if not (np.isfinite(p0) and np.isfinite(p1)):
            continue
        center_t = idx[k] + pd.Timedelta(hours=WINDOW_H // 2)
        if center_mask is not None:
            ci = center_mask.index.get_indexer([center_t], method="nearest",
                                               tolerance=pd.Timedelta(hours=cadence_h))[0]
            if ci == -1 or not bool(center_mask.iloc[ci]):
                continue
        phi = np.nanmean(lats[k:k + steps + 1])
        if not np.isfinite(phi) or abs(np.sin(np.radians(phi))) < 1e-6:
            continue
        dP = p0 - p1  # positive = deepening
        ndr = (dP / WINDOW_H) * (SIN60 / abs(np.sin(np.radians(phi))))
        if not np.isfinite(best) or ndr > best:
            best, best_t = ndr, center_t
    return best, best_t


def intensification_ranges(tracks):
    """Map track_id -> boolean of whether a timestamp is in any intensification phase."""
    t = tracks.copy()
    t["t"] = pd.to_datetime(t["date"])
    t["is_int"] = t["period"].astype(str).str.startswith("intensification")
    return t


def main():
    if not CP_FILE.exists():
        print(f"❌ Missing {CP_FILE}. Run step3 first.")
        return 1

    cp = pd.read_csv(CP_FILE, parse_dates=["time"])
    tracks = pd.read_csv(TRACKS_FILE) if TRACKS_FILE.exists() else None
    intdf = intensification_ranges(tracks) if tracks is not None else None

    print("=" * 70)
    print("STEP 4: Compute NDR and classify bombs")
    print(f"  Window: {WINDOW_H} h centred  |  threshold: {BOMB_THRESHOLD} Bergeron (sin, ref 60 deg)")
    print("=" * 70)

    rows = []
    for tid, g in cp.groupby("track_id"):
        g = g.sort_values("time")
        # latitude for phi: central where valid, else vorticity centre
        lat_raw = g["central_lat"].where(g["central_lat"].notna(), g["vor_lat"])
        s_p = pd.Series(g["central_mslp"].values, index=pd.DatetimeIndex(g["time"]))
        s_lat = pd.Series(lat_raw.values, index=pd.DatetimeIndex(g["time"]))

        # regular hourly grid + short-gap interpolation
        full = pd.date_range(s_p.index.min(), s_p.index.max(), freq="h")
        p_h = s_p.reindex(full).interpolate(limit=GAP_FILL_H, limit_area="inside")
        lat_h = s_lat.reindex(full).interpolate(limit=GAP_FILL_H, limit_area="inside")

        # intensification center-mask on the hourly grid
        cmask = None
        if intdf is not None:
            gi = intdf[intdf["track_id"] == tid]
            if len(gi):
                int_times = pd.DatetimeIndex(gi.loc[gi["is_int"], "t"].values)
                cmask = pd.Series(full.isin(int_times), index=full)

        ndr_life, t_life = max_ndr(p_h, lat_h, cadence_h=1)
        ndr_int, t_int = max_ndr(p_h, lat_h, cadence_h=1, center_mask=cmask) if cmask is not None else (np.nan, pd.NaT)

        # 6-hourly subsample (00/06/12/18) for literature comparison
        six = full[(full.hour % 6) == 0]
        ndr_6h, _ = max_ndr(p_h.reindex(six), lat_h.reindex(six), cadence_h=6)

        n_valid = int(g["central_mslp"].notna().sum())
        rows.append({
            "track_id": tid, "ep": int(g["ep"].iloc[0]),
            "ndr_max_lifecycle": ndr_life, "time_ndr_max": t_life,
            "ndr_max_intensification": ndr_int,
            "ndr_max_lifecycle_6h": ndr_6h,
            "bomb_lifecycle": bool(np.isfinite(ndr_life) and ndr_life >= BOMB_THRESHOLD),
            "bomb_intensification": bool(np.isfinite(ndr_int) and ndr_int >= BOMB_THRESHOLD),
            "intensity_class": classify(ndr_life),
            "min_mslp": float(np.nanmin(g["central_mslp"])) if n_valid else np.nan,
            "n_valid_central": n_valid, "n_steps": len(g),
            "frac_flagged": float((g["flag"] != "ok").mean()),
            "max_offset_deg": float(np.nanmax(g["offset_deg"])) if n_valid else np.nan,
            "frac_over_land": float(pd.to_numeric(g["over_land"], errors="coerce").mean()),
        })

    out = pd.DataFrame(rows).sort_values(["ep", "track_id"])
    out.to_csv(OUT_DIR / "ndr_by_cyclone.csv", index=False)

    # ---- aggregate by EP ----------------------------------------------------
    agg_rows = []
    for ep in ALL_EPS:
        e = out[out["ep"] == ep]
        n = len(e)
        agg_rows.append({
            "ep": ep, "ep_label": get_ep_label(ep), "n_cyclones": n,
            "n_processed_expected": EP_COUNTS[ep],
            "n_bomb_lifecycle": int(e["bomb_lifecycle"].sum()),
            "pct_bomb_lifecycle": round(100 * e["bomb_lifecycle"].mean(), 2) if n else np.nan,
            "n_bomb_intensification": int(e["bomb_intensification"].sum()),
            "pct_bomb_intensification": round(100 * e["bomb_intensification"].mean(), 2) if n else np.nan,
            "n_weak": int((e["intensity_class"] == "weak").sum()),
            "n_moderate": int((e["intensity_class"] == "moderate").sum()),
            "n_intense": int((e["intensity_class"] == "intense").sum()),
            "median_ndr_max": round(float(e["ndr_max_lifecycle"].median()), 3) if n else np.nan,
        })
    agg = pd.DataFrame(agg_rows)
    agg.to_csv(OUT_DIR / "bomb_frequency_by_ep.csv", index=False)

    print(f"\nWrote {OUT_DIR / 'ndr_by_cyclone.csv'}  ({len(out)} cyclones)")
    print(f"Wrote {OUT_DIR / 'bomb_frequency_by_ep.csv'}")
    print("\nBomb frequency by EP (life cycle):")
    for _, r in agg.iterrows():
        print(f"  {r['ep_label']}: {r['n_bomb_lifecycle']:4d}/{r['n_cyclones']:<4d} "
              f"({r['pct_bomb_lifecycle']}%)  | weak {r['n_weak']} mod {r['n_moderate']} int {r['n_intense']}")
    print("  Next: python scripts/explosive_cyclones_analysis/step5_figures_tables.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
