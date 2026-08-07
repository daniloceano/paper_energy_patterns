"""
Step 2: Classify every CPS timestep and every cyclone as extratropical,
subtropical or tropical, under six literature threshold sets.

Threshold sets live in `cps_criteria.py` and are transcribed verbatim from the
peer-reviewed sources - nothing here is tuned to our data. Three are South
Atlantic sets (C01, GOZZO14, C03); three are cross-basin controls (YANASE14
global, CAVICCHIA19 Australian east coast lows, GUISHARD09 North Atlantic).

Timestep level
    Each classifiable timestep is tested against the three class definitions.
    The classes OVERLAP by construction (Conrado et al. 2024, their Fig. 2b),
    so a precedence order is applied: tropical > subtropical > extratropical.
    Timesteps in none of the three are labelled `unclassified` - the direct
    analogue of Yanase et al.'s (2014) explicit "ill-defined" class.

Cyclone level - four rules of increasing strictness
    `type_any`        most tropical class attained at ANY single timestep.
                      Mirrors "systems that in any time of their lifecycle
                      obtained tropical features" (Conrado et al. 2024), but is
                      very sensitive to single-timestep noise.

    `type_persistent` class held for >= 36 CONSECUTIVE hours. The persistence
                      requirement of Guishard et al. (2009) ("persist in its
                      hybrid form for at least 36 h, i.e., more than one
                      diurnal cycle") and Gozzo et al. (2014).

    `type_protocol`   + over ocean, + genesis between 20 S and 40 S.

    `type_strict`     + the qualifying 36-h run must BEGIN within 24 h of
                      genesis. This is Guishard et al.'s (2009) requirement to
                      "become subtropical within 24 h if identified first as a
                      purely cold- or warm-cored system", and it is the
                      criterion that separates a genuine hybrid genesis from a
                      warm core acquired late in a baroclinic life cycle
                      (a Shapiro-Keyser warm seclusion). Persistence alone
                      cannot do this - a seclusion persists. See step 4.

IMPORTANT on interpreting the columns: applying the geographic and timing
criteria to ALL THREE classes keeps them like-for-like, but means the
"extratropical" counts under `type_protocol`/`type_strict` are not a basin
climatology - most of the ARG genesis box lies outside 20-40 S and is excluded
by construction. Only within-EP ratios under a fixed rule are comparable.

NOT implemented: the gale-force wind requirement (Gozzo et al. deliberately
dropped it for the South Atlantic) and Gozzo et al.'s manual rejection step by
visual inspection of geopotential-height-anomaly and 925-hPa temperature fields.

Inputs:
    results/cps_analysis/cps_timesteps.csv          (step 1)

Outputs:
    results/cps_analysis/cps_timesteps_classified.csv
    results/cps_analysis/cyclone_types.csv
    results/cps_analysis/criteria_definitions.txt

Run:
    python scripts/cps_analysis/sensitivity/s1_classify_cyclone_types.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

import numpy as np
import pandas as pd

from scripts.cps_analysis.cps_criteria import (
    CRITERIA,
    MAX_ONSET_HOURS,
    CRITERIA_SOURCES,
    CRITERIA_DESCRIPTIONS,
    CLASS_PRECEDENCE,
    UNCLASSIFIED,
    MIN_PERSISTENCE_HOURS,
    GENESIS_LAT_BAND,
    class_mask,
    describe_criterion,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis" / "sensitivity"
IN_FILE = PROJECT_ROOT / "results" / "cps_analysis" / "cps_timesteps.csv"
OUT_TIMESTEPS = RESULTS_DIR / "cps_timesteps_classified.csv"
OUT_CYCLONES = RESULTS_DIR / "cyclone_types.csv"
OUT_CRITERIA = RESULTS_DIR / "criteria_definitions.txt"

# Two CPS samples belong to the same run only if they are this close in time.
# The database is sampled 3-hourly; the tolerance absorbs rounding only.
MAX_GAP_HOURS = 3.5


# ---------------------------------------------------------------------------
# Ocean mask
# ---------------------------------------------------------------------------

def build_ocean_flag(lon: pd.Series, lat: pd.Series) -> pd.Series:
    """True where the position is over ocean, NaN if land polygons unavailable.

    Uses Natural Earth 110 m land polygons through cartopy. On a node without
    the cached shapefile and without network access this returns all-NaN, and
    the Gozzo ocean criterion is skipped (reported by the caller).
    """
    try:
        import cartopy.io.shapereader as shpreader
        from shapely.geometry import Point
        from shapely.ops import unary_union
        from shapely.prepared import prep
    except Exception:
        return pd.Series(np.nan, index=lon.index, dtype="object")

    try:
        shp = shpreader.natural_earth(resolution="110m", category="physical", name="land")
        land = prep(unary_union(list(shpreader.Reader(shp).geometries())))
    except Exception:
        return pd.Series(np.nan, index=lon.index, dtype="object")

    # Evaluate once per unique rounded position, then map back: ~200k point-in
    # -polygon tests collapse to a few thousand.
    key = pd.Series(list(zip(lon.round(2), lat.round(2))), index=lon.index)
    uniq = pd.unique(key.dropna())
    lookup = {p: (not land.contains(Point(p[0], p[1]))) for p in uniq}
    return key.map(lookup)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def qualifying_runs(times: np.ndarray, flag: np.ndarray) -> list:
    """All maximal contiguous True runs, as (start_time, span_hours) pairs.

    A run of k contiguous samples spanning t0..t1 is credited with (t1 - t0)
    hours, so a single isolated timestep counts as 0 h. Runs break across time
    gaps larger than MAX_GAP_HOURS.
    """
    runs = []
    start = None
    prev_t = None

    for t, ok in zip(times, flag):
        if ok:
            gap_ok = (prev_t is None
                      or (t - prev_t) / np.timedelta64(1, "h") <= MAX_GAP_HOURS)
            if start is None or not gap_ok:
                if start is not None:
                    runs.append((start, (prev_t - start) / np.timedelta64(1, "h")))
                start = t
            prev_t = t
        else:
            if start is not None:
                runs.append((start, (prev_t - start) / np.timedelta64(1, "h")))
            start = None
            prev_t = None

    if start is not None:
        runs.append((start, (prev_t - start) / np.timedelta64(1, "h")))

    return [(s, float(h)) for s, h in runs]


def max_consecutive_hours(times: np.ndarray, flag: np.ndarray) -> float:
    """Longest time span (hours) over which `flag` stays True without a time gap."""
    runs = qualifying_runs(times, flag)
    return max((h for _, h in runs), default=0.0)


def onset_of_first_qualifying_run(times: np.ndarray, flag: np.ndarray,
                                  genesis: np.datetime64,
                                  min_hours: float) -> float:
    """Hours from genesis to the start of the first run lasting >= min_hours.

    Returns np.inf when no run is long enough. This is the quantity Guishard
    et al. (2009) and Gozzo et al. (2014) bound at 24 h.
    """
    for start, hours in qualifying_runs(times, flag):
        if hours >= min_hours:
            return float((start - genesis) / np.timedelta64(1, "h"))
    return float("inf")


def aggregate_cyclone(group: pd.DataFrame, criterion: str) -> dict:
    """Per-cyclone summary of one criterion set."""
    times = group["datetime"].values
    out = {}

    for cls in CLASS_PRECEDENCE:
        flag = group[f"{criterion}_{cls}"].to_numpy(dtype=bool)
        out[f"n_{cls}"] = int(flag.sum())
        out[f"hours_{cls}"] = max_consecutive_hours(times, flag)

    # Precedence: the most tropical class attained wins.
    out["type_any"] = UNCLASSIFIED
    out["type_persistent"] = UNCLASSIFIED
    for cls in CLASS_PRECEDENCE:
        if out["type_any"] == UNCLASSIFIED and out[f"n_{cls}"] > 0:
            out["type_any"] = cls
        if (out["type_persistent"] == UNCLASSIFIED
                and out[f"hours_{cls}"] >= MIN_PERSISTENCE_HOURS):
            out["type_persistent"] = cls

    # --- Gozzo et al. (2014) geographic protocol ------------------------------
    # Their criteria 1 and 3: genesis between 20 S and 40 S, and the thresholds
    # attained over the ocean. Gozzo et al. impose this on subtropical cyclones,
    # to keep polar and mesoscale lows out of the climatology. It is applied
    # here to ALL THREE classes, because the same contamination affects the
    # tropical class: at high latitudes the symmetric warm-core corner of the
    # phase space is occupied by warm-seclusion extratropical cyclones, not by
    # tropical systems (Hart 2003).
    has_ocean = "over_ocean" in group and group["over_ocean"].notna().any()
    out["ocean_criterion_applied"] = bool(has_ocean)
    ocean = (group["over_ocean"].fillna(False).to_numpy(dtype=bool)
             if has_ocean else np.ones(len(group), dtype=bool))

    genesis_lat = group["genesis_lat"].iloc[0]
    lat_ok = (
        pd.notna(genesis_lat)
        and GENESIS_LAT_BAND[0] <= genesis_lat <= GENESIS_LAT_BAND[1]
    )
    out["genesis_lat_in_band"] = bool(lat_ok)

    genesis = times[0] if len(times) else None

    out["type_protocol"] = UNCLASSIFIED
    out["type_strict"] = UNCLASSIFIED
    for cls in CLASS_PRECEDENCE:
        flag = group[f"{criterion}_{cls}"].to_numpy(dtype=bool) & ocean
        hours = max_consecutive_hours(times, flag)
        out[f"hours_{cls}_ocean"] = hours
        out[f"protocol_{cls}"] = bool(lat_ok and hours >= MIN_PERSISTENCE_HOURS)
        if out["type_protocol"] == UNCLASSIFIED and out[f"protocol_{cls}"]:
            out["type_protocol"] = cls

        # Onset of the first run that itself satisfies the 36-h persistence
        # requirement, measured from genesis. This is Guishard et al.'s (2009)
        # "become subtropical within 24 h" criterion.
        onset = onset_of_first_qualifying_run(
            times, flag, genesis, MIN_PERSISTENCE_HOURS
        )
        out[f"onset_{cls}"] = onset
        out[f"strict_{cls}"] = bool(
            out[f"protocol_{cls}"] and onset <= MAX_ONSET_HOURS
        )
        if out["type_strict"] == UNCLASSIFIED and out[f"strict_{cls}"]:
            out["type_strict"] = cls

    # Backwards-compatible alias: Gozzo's protocol as they defined it.
    out["gozzo_subtropical"] = out["protocol_subtropical"]

    return out


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 1: Classify CPS timesteps and cyclones")
    print("=" * 70)

    if not IN_FILE.exists():
        print(f"Missing {IN_FILE}. Run step 1 first.")
        return 1

    df = pd.read_csv(IN_FILE, parse_dates=["datetime"])
    print(f"\nLoaded {len(df):,} timesteps for {df['track_id'].nunique():,} cyclones")

    classifiable = df[["B", "VTL", "VTU"]].notna().all(axis=1)
    print(f"  classifiable: {classifiable.sum():,} ({classifiable.mean():.1%})")

    # --- Ocean flag -----------------------------------------------------------
    print("\nBuilding ocean mask (Natural Earth 110 m land polygons) ...")
    df["over_ocean"] = build_ocean_flag(df["lon"], df["lat"])
    if df["over_ocean"].notna().any():
        frac = pd.to_numeric(df["over_ocean"], errors="coerce").mean()
        print(f"  {frac:.1%} of timesteps over ocean")
    else:
        print("  Land polygons unavailable — Gozzo ocean criterion will be SKIPPED.")

    # --- Timestep classification ---------------------------------------------
    print("\nClassifying timesteps ...")
    for criterion in CRITERIA:
        for cls in CLASS_PRECEDENCE:
            df[f"{criterion}_{cls}"] = class_mask(df, criterion, cls) & classifiable

        label = pd.Series(UNCLASSIFIED, index=df.index, dtype=object)
        for cls in reversed(CLASS_PRECEDENCE):  # reverse => precedence wins
            label = label.mask(df[f"{criterion}_{cls}"], cls)
        label = label.mask(~classifiable, np.nan)
        df[f"type_{criterion}"] = label

        counts = label.value_counts(dropna=True)
        total = counts.sum()
        summary = "  ".join(
            f"{c}={counts.get(c, 0):,} ({counts.get(c, 0) / total:.1%})"
            for c in CLASS_PRECEDENCE + [UNCLASSIFIED]
        )
        print(f"  {criterion:<8s} {summary}")

    df.to_csv(OUT_TIMESTEPS, index=False)
    print(f"\nWrote {OUT_TIMESTEPS.relative_to(PROJECT_ROOT)}")

    # --- Cyclone-level aggregation -------------------------------------------
    print("\nAggregating to cyclone level ...")
    static_cols = ["ep", "region", "genesis_lat", "genesis_lon"]
    static = df.groupby("track_id")[static_cols].first()
    static["year"] = df.groupby("track_id")["datetime"].first().dt.year
    static["n_timesteps"] = df.groupby("track_id").size()

    per_criterion = []
    for criterion in CRITERIA:
        recs = {
            tid: aggregate_cyclone(g, criterion)
            for tid, g in df.groupby("track_id", sort=True)
        }
        agg = pd.DataFrame.from_dict(recs, orient="index")
        agg.index.name = "track_id"
        agg.columns = [f"{criterion}_{c}" for c in agg.columns]
        per_criterion.append(agg)

    cyclones = static.join(per_criterion)
    cyclones.to_csv(OUT_CYCLONES)
    print(f"Wrote {OUT_CYCLONES.relative_to(PROJECT_ROOT)}  ({len(cyclones):,} cyclones)")

    # --- Console summary ------------------------------------------------------
    print("\n" + "-" * 70)
    print("CYCLONE COUNTS BY TYPE (whole population)")
    print("-" * 70)
    notes = {
        "type_any": "any single timestep",
        "type_persistent": f">= {MIN_PERSISTENCE_HOURS:.0f} h",
        "type_protocol": f">= {MIN_PERSISTENCE_HOURS:.0f} h, ocean, genesis 20-40S",
        "type_strict": (f">= {MIN_PERSISTENCE_HOURS:.0f} h, ocean, genesis 20-40S, "
                        f"onset <= {MAX_ONSET_HOURS:.0f} h"),
    }
    for criterion in CRITERIA:
        print(f"\n{criterion}  [{CRITERIA_SOURCES[criterion]}]")
        for rule, note in notes.items():
            counts = cyclones[f"{criterion}_{rule}"].value_counts()
            parts = "  ".join(
                f"{c}={counts.get(c, 0):,}" for c in CLASS_PRECEDENCE + [UNCLASSIFIED]
            )
            print(f"  {rule:<16s} ({note:<34s}) {parts}")

    # --- Persist the criteria actually used ----------------------------------
    with open(OUT_CRITERIA, "w") as fh:
        fh.write("CPS classification criteria applied in this analysis\n")
        fh.write("=" * 60 + "\n\n")
        fh.write(f"Persistence requirement : >= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours\n")
        fh.write(f"Genesis latitude band   : {GENESIS_LAT_BAND[0]} to {GENESIS_LAT_BAND[1]} deg\n")
        fh.write(f"Max onset from genesis  : <= {MAX_ONSET_HOURS:.0f} h (strict rule only)\n")
        fh.write("Precedence              : " + " > ".join(CLASS_PRECEDENCE) + "\n\n")
        for criterion in CRITERIA:
            fh.write(describe_criterion(criterion) + "\n")
            fh.write(f"    note: {CRITERIA_DESCRIPTIONS[criterion]}\n\n")
    print(f"\nWrote {OUT_CRITERIA.relative_to(PROJECT_ROOT)}")

    print("\nStep 1 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
