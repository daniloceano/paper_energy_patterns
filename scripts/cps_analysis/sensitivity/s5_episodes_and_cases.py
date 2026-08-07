"""
Step 6: Export every classified episode with its start/end dates, and check the
classification against documented, named South Atlantic cyclones.

Part A - EPISODE EXPORT
    For every cyclone and every threshold set, list each maximal continuous
    spell of tropical / subtropical / extratropical structure: when it starts,
    when it ends, how long it lasts, how long after genesis it begins, and
    which of the four identification rules it satisfies. This is the table to
    read when you want to eyeball whether a given classification is sensible.

    The distinction between the rules, restated at episode level:

      persistent  the episode lasts >= 36 h. Nothing about WHERE or WHEN.
                  A warm seclusion passes this easily - it is a real, sustained
                  structure, just not a tropical one.

      strict      the episode lasts >= 36 h AND lies over ocean AND the cyclone
                  formed between 20 S and 40 S AND the episode STARTS within
                  24 h of genesis. The last clause is what a seclusion fails:
                  it develops after the baroclinic life cycle has run, typically
                  75-100 h in.

Part B - DOCUMENTED CASE CHECK
    The Brazilian Navy has named subtropical and tropical cyclones over the
    South Atlantic since 2011, and several are documented in peer-reviewed
    case studies with explicit genesis times and positions. This step searches
    the catalogue for a track matching each documented case in space and time,
    and reports what our classification says about it.

    Cases outside the catalogue period (genesis years 1979-2020) are listed and
    reported as such rather than silently skipped - Raoni (2021), Yakecan
    (2022) and Biguá (2024) all postdate the track set.

Inputs:
    results/cps_analysis/cps_timesteps_classified.csv   (step 2)
    results/cps_analysis/cyclone_types.csv              (step 2)

Outputs:
    results/cps_analysis/episodes_all.csv
    results/cps_analysis/episodes_subtropical_strict.csv
    results/cps_analysis/documented_case_check.csv
    results/cps_analysis/documented_case_report.txt

Run:
    python scripts/cps_analysis/sensitivity/s5_episodes_and_cases.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

import numpy as np
import pandas as pd

from scripts.utils.ep_mapping import get_ep_label
from scripts.cps_analysis.cps_criteria import (
    CRITERIA,
    CLASS_PRECEDENCE,
    MIN_PERSISTENCE_HOURS,
    MAX_ONSET_HOURS,
    GENESIS_LAT_BAND,
    PRIMARY_CRITERIA,
    CROSS_BASIN_CRITERIA,
    DEFAULT_CRITERION,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis" / "sensitivity"
TS_FILE = RESULTS_DIR / "cps_timesteps_classified.csv"
CY_FILE = RESULTS_DIR / "cyclone_types.csv"

MAX_GAP_HOURS = 3.5

# =============================================================================
# DOCUMENTED CASES
# =============================================================================
# Every entry is sourced from a peer-reviewed publication. Dates and positions
# are as published; where a study gives both a precursor genesis and a naming
# time, the precursor genesis is used, because that is what a vorticity tracker
# would pick up.
#
# `search_days` widens the time window around the published genesis, and
# `search_deg` the position window, when looking for a matching track. Both are
# generous on purpose: our tracking uses 850-hPa vorticity while the published
# studies use MSLP or 925-hPa vorticity, so centres differ.

DOCUMENTED_CASES = [
    # ---- within the catalogue period (genesis 1979-2020) --------------------
    dict(name="Catarina", genesis="2004-03-20", lysis="2004-03-28",
         lat=-29.0, lon=-45.0, expected="tropical",
         source="McTaggart-Cowan et al. (2006), MWR 134, 3029-3053",
         note="peak intensity 0000 UTC 28 Mar 2004, cat-1 hurricane at landfall",
         search_days=5, search_deg=8),
    dict(name="Anita", genesis="2010-03-04 06:00", lysis="2010-03-13 00:00",
         lat=-19.75, lon=-34.75, expected="subtropical",
         source="Reboita et al. (2019), Atmosphere 10, 6 - their Table 2",
         note="9-day lifetime; potential for tropical transition (Dias Pinto et al. 2013)",
         search_days=3, search_deg=6),
    dict(name="Arani", genesis="2011-03-08 12:00", lysis="2011-03-17 18:00",
         lat=-24.00, lon=-41.25, expected="subtropical",
         source="Reboita et al. (2019), Atmosphere 10, 6 - their Table 2",
         note="first Navy-named system (Nov 2011 list); 9-day lifetime",
         search_days=3, search_deg=6),
    dict(name="Bapo", genesis="2015-02-04 18:00", lysis="2015-02-10 06:00",
         lat=-26.00, lon=-43.50, expected="subtropical",
         source="Reboita et al. (2019), Atmosphere 10, 6 - their Table 2",
         note="6-day lifetime", search_days=3, search_deg=6),
    dict(name="Cari", genesis="2015-03-08 00:00", lysis="2015-03-17 18:00",
         lat=-26.25, lon=-45.00, expected="subtropical",
         source="Reboita et al. (2019), Atmosphere 10, 6 - their Table 2",
         note="longest lifetime of the named set (10 days)",
         search_days=3, search_deg=6),
    dict(name="Deni", genesis="2016-11-15 00:00", lysis="2016-11-18 00:00",
         lat=-23.00, lon=-42.50, expected="subtropical",
         source="Reboita et al. (2019), Atmosphere 10, 6 - their Table 2",
         note="short-lived (3 days)", search_days=3, search_deg=6),
    dict(name="Ecai", genesis="2016-12-04 00:00", lysis="2016-12-06 18:00",
         lat=-26.50, lon=-47.50, expected="subtropical",
         source="Reboita et al. (2019), Atmosphere 10, 6 - their Table 2",
         note="Ecai; short-lived (3 days)", search_days=3, search_deg=6),
    dict(name="Guara", genesis="2017-12-09 00:00", lysis=None,
         lat=-18.0, lon=-38.0, expected="subtropical",
         source="Silva et al. (2022), Rev. Bras. Geogr. Fis. 15, 333-342",
         note="pure subtropical genesis off Bahia / Espirito Santo",
         search_days=3, search_deg=7),
    dict(name="Iba", genesis="2019-03-23", lysis="2019-03-28",
         lat=-20.0, lon=-36.0, expected="tropical",
         source="Reboita et al. (2021), JGR-Atmos 126, e2020JD033431",
         note="first pure tropical cyclogenesis in the western South Atlantic",
         search_days=4, search_deg=7),

    # ---- outside the catalogue period --------------------------------------
    dict(name="Raoni", genesis="2021-06-26 18:00", lysis="2021-07-01",
         lat=-33.0, lon=-53.0, expected="subtropical",
         source="Reboita et al. (2022), QJRMS 148, 2991-3009",
         note="precursor genesis 1800 UTC 26 Jun 2021; named 1200 UTC 29 Jun; "
              "subtropical transition from a Shapiro-Keyser extratropical cyclone",
         search_days=3, search_deg=6),
    dict(name="Yakecan", genesis="2022-05-16", lysis="2022-05-19",
         lat=-33.0, lon=-52.0, expected="subtropical",
         source="Brazilian Navy / METAREA V records",
         note="16-19 May 2022; NOT peer-reviewed-sourced here - dates from "
              "Navy records, listed for completeness only",
         search_days=3, search_deg=6),
    dict(name="Akara", genesis="2024-02-15 12:00", lysis="2024-02-23 00:00",
         lat=-25.0, lon=-42.0, expected="tropical",
         source="Reboita et al. (2024), JMSE 12, 1934",
         note="tropical transition; CPS-tropical 17-21 Feb under the classic "
              "definition, 16-22 Feb under the relaxed -VTU > -60",
         search_days=3, search_deg=7),
    dict(name="Bigua", genesis="2024-12-14 18:00", lysis=None,
         lat=-30.0, lon=-55.0, expected="subtropical",
         source="Brazilian Navy / METAREA V records",
         note="formed 1800 UTC 14 Dec 2024 over Paraguay / NE Argentina / "
              "western Rio Grande do Sul; NOT peer-reviewed-sourced here",
         search_days=3, search_deg=7),
]


# =============================================================================
# PART A - EPISODES
# =============================================================================

def episodes_for(times: np.ndarray, flag: np.ndarray) -> list:
    """Maximal contiguous True runs as (start, end, span_hours) triples."""
    out, start, prev = [], None, None
    for t, ok in zip(times, flag):
        if ok:
            gap_ok = prev is None or (t - prev) / np.timedelta64(1, "h") <= MAX_GAP_HOURS
            if start is None or not gap_ok:
                if start is not None:
                    out.append((start, prev, (prev - start) / np.timedelta64(1, "h")))
                start = t
            prev = t
        else:
            if start is not None:
                out.append((start, prev, (prev - start) / np.timedelta64(1, "h")))
            start, prev = None, None
    if start is not None:
        out.append((start, prev, (prev - start) / np.timedelta64(1, "h")))
    return [(s, e, float(h)) for s, e, h in out]


def build_episodes(ts: pd.DataFrame, criteria: list) -> pd.DataFrame:
    """One row per (cyclone, criterion, class, episode)."""
    rows = []
    for tid, g in ts.groupby("track_id", sort=True):
        g = g.sort_values("datetime")
        times = g["datetime"].values
        genesis = times[0]
        ocean = g["over_ocean"].fillna(False).to_numpy(dtype=bool)
        glat = g["genesis_lat"].iloc[0]
        lat_ok = (pd.notna(glat)
                  and GENESIS_LAT_BAND[0] <= glat <= GENESIS_LAT_BAND[1])
        ep = g["ep"].iloc[0]

        for criterion in criteria:
            for cls in CLASS_PRECEDENCE:
                flag = g[f"{criterion}_{cls}"].to_numpy(dtype=bool)
                for start, end, hours in episodes_for(times, flag):
                    onset = float((start - genesis) / np.timedelta64(1, "h"))
                    sel = g["datetime"].values == start
                    # Fraction of the episode spent over ocean.
                    span = (times >= start) & (times <= end)
                    ocean_frac = ocean[span].mean() if span.any() else np.nan
                    # An episode qualifies under the ocean-restricted rules only
                    # if the >=36 h requirement is met by the ocean-only part.
                    ocean_hours = max(
                        (h for _, _, h in episodes_for(times[span], ocean[span])),
                        default=0.0)

                    rows.append({
                        "track_id": tid,
                        "criterion": criterion,
                        "class": cls,
                        "episode_start": pd.Timestamp(start),
                        "episode_end": pd.Timestamp(end),
                        "duration_h": hours,
                        "onset_h_from_genesis": round(onset, 1),
                        "genesis_time": pd.Timestamp(genesis),
                        "lat_at_start": round(float(g.loc[sel, "lat"].iloc[0]), 2),
                        "lon_at_start": round(float(g.loc[sel, "lon"].iloc[0]), 2),
                        "genesis_lat": round(float(glat), 2) if pd.notna(glat) else np.nan,
                        "region": g["region"].iloc[0],
                        "ep": get_ep_label(int(ep)) if pd.notna(ep) else "",
                        "frac_over_ocean": round(float(ocean_frac), 2),
                        "meets_persistent": hours >= MIN_PERSISTENCE_HOURS,
                        "meets_protocol": bool(lat_ok and ocean_hours >= MIN_PERSISTENCE_HOURS),
                        "meets_strict": bool(lat_ok
                                             and ocean_hours >= MIN_PERSISTENCE_HOURS
                                             and onset <= MAX_ONSET_HOURS),
                    })
    return pd.DataFrame(rows)


# =============================================================================
# PART B - DOCUMENTED CASES
# =============================================================================

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Scalars or arrays."""
    r = 6371.0
    p1, p2 = np.deg2rad(lat1), np.deg2rad(lat2)
    dp = p2 - p1
    dl = np.deg2rad(np.asarray(lon2) - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return r * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# A candidate track is accepted as the documented system only if its own
# genesis is within this distance and time of the published genesis. The
# box search alone is far too permissive: at 25 S, 7 deg of longitude is
# ~700 km, so a box match can still be a completely different cyclone.
MATCH_MAX_KM = 600.0
MATCH_MAX_HOURS = 48.0


def check_cases(ts: pd.DataFrame, cyclones: pd.DataFrame) -> tuple:
    """Search the catalogue for each documented case; report the verdict."""
    lines, rows = [], []
    tmin, tmax = ts["datetime"].min(), ts["datetime"].max()
    lines.append(f"Catalogue covers {tmin:%Y-%m-%d} to {tmax:%Y-%m-%d} "
                 f"({cyclones['track_id'].nunique():,} cyclones)\n")

    for case in DOCUMENTED_CASES:
        gen = pd.Timestamp(case["genesis"])
        w = pd.Timedelta(days=case["search_days"])
        d = case["search_deg"]

        lines.append("=" * 70)
        lines.append(f"{case['name']}  —  documented genesis {gen:%Y-%m-%d %H:%M} "
                     f"at {case['lat']:.2f}, {case['lon']:.2f}")
        lines.append(f"  expected: {case['expected']}")
        lines.append(f"  source  : {case['source']}")
        lines.append(f"  note    : {case['note']}")

        if not (tmin <= gen <= tmax):
            lines.append(f"  VERDICT : OUT OF CATALOGUE PERIOD "
                         f"(genesis {gen:%Y-%m-%d} is outside "
                         f"{tmin:%Y-%m-%d}..{tmax:%Y-%m-%d})")
            rows.append({**{k: case[k] for k in ("name", "expected", "source")},
                         "genesis": gen, "status": "out_of_period",
                         "matched_track": "", "our_label_any": "",
                         "our_label_persistent": "", "our_label_strict": ""})
            lines.append("")
            continue

        near = ts[(ts["datetime"] >= gen - w) & (ts["datetime"] <= gen + w)
                  & (ts["lat"] - case["lat"]).abs().le(d)
                  & (ts["lon"] - case["lon"]).abs().le(d)]

        if near.empty:
            lines.append("  VERDICT : NO MATCHING TRACK in the catalogue "
                         "(genesis outside the ARG / LA-PLATA / SE-BR boxes)")
            rows.append({**{k: case[k] for k in ("name", "expected", "source")},
                         "genesis": gen, "status": "not_in_catalogue",
                         "matched_track": "", "our_label_any": "",
                         "our_label_persistent": "", "our_label_strict": ""})
            lines.append("")
            continue

        # Rank candidates by genesis-to-genesis separation in BOTH time and
        # space. A box match alone is not enough - at 25 S, 7 deg of longitude
        # is ~700 km, wide enough to catch an unrelated cyclone.
        cands = []
        for tid, g in near.groupby("track_id"):
            full = ts[ts["track_id"] == tid].sort_values("datetime")
            tgen = full["datetime"].min()
            glat = full["lat"].iloc[0]
            glon = full["lon"].iloc[0]
            dt_h = abs((tgen - gen).total_seconds()) / 3600
            dist_km = float(haversine_km(case["lat"], case["lon"], glat, glon))
            # Closest approach of the whole track to the documented genesis
            # point, which catches systems the tracker picked up elsewhere.
            approach = float(haversine_km(case["lat"], case["lon"],
                                          full["lat"].values,
                                          full["lon"].values).min())
            cands.append(dict(dt_h=dt_h, dist_km=dist_km, approach_km=approach,
                              tid=tid, tgen=tgen, glat=glat, glon=glon))

        cands.sort(key=lambda c: (c["dist_km"] / MATCH_MAX_KM
                                  + c["dt_h"] / MATCH_MAX_HOURS))

        lines.append(f"  {len(cands)} candidate track(s) in the space-time window:")
        for c in cands[:4]:
            row = cyclones[cyclones["track_id"] == c["tid"]]
            if row.empty:
                continue
            row = row.iloc[0]
            labels = {r: row[f"{DEFAULT_CRITERION}_type_{r}"]
                      for r in ("any", "persistent", "protocol", "strict")}
            lines.append(
                f"    track {c['tid']}  genesis {c['tgen']:%Y-%m-%d %H:%M} "
                f"at {c['glat']:.1f},{c['glon']:.1f}")
            lines.append(
                f"        separation from documented genesis: "
                f"{c['dt_h']:.0f} h, {c['dist_km']:.0f} km "
                f"(track's closest approach {c['approach_km']:.0f} km)  "
                f"region {row['region']}  "
                f"EP{int(row['ep']) if pd.notna(row['ep']) else '-'}")
            lines.append(
                f"        {DEFAULT_CRITERION}: any={labels['any']}  "
                f"persistent={labels['persistent']}  "
                f"protocol={labels['protocol']}  strict={labels['strict']}")

        best = cands[0]
        brow = cyclones[cyclones["track_id"] == best["tid"]]
        if brow.empty:
            lines.append("")
            continue
        brow = brow.iloc[0]
        lab_any = brow[f"{DEFAULT_CRITERION}_type_any"]
        lab_per = brow[f"{DEFAULT_CRITERION}_type_persistent"]
        lab_str = brow[f"{DEFAULT_CRITERION}_type_strict"]

        accepted = (best["dist_km"] <= MATCH_MAX_KM
                    and best["dt_h"] <= MATCH_MAX_HOURS)

        if not accepted:
            verdict = (f"NO CONFIDENT MATCH - nearest candidate is "
                       f"{best['dist_km']:.0f} km and {best['dt_h']:.0f} h from the "
                       f"documented genesis (limits {MATCH_MAX_KM:.0f} km / "
                       f"{MATCH_MAX_HOURS:.0f} h); treated as a different system")
            status = "no_confident_match"
        elif lab_per == case["expected"] or lab_str == case["expected"]:
            verdict = (f"MATCH - classified {case['expected']} "
                       f"(separation {best['dist_km']:.0f} km, {best['dt_h']:.0f} h)")
            status = "match"
        elif lab_any == case["expected"]:
            verdict = (f"PARTIAL - reaches {case['expected']} at some timestep "
                       f"but not for a sustained spell")
            status = "partial"
        else:
            verdict = (f"MISMATCH - expected {case['expected']}, "
                       f"got persistent={lab_per}, strict={lab_str}")
            status = "mismatch"

        lines.append(f"  VERDICT : {verdict}")
        lines.append("")
        rows.append({**{k: case[k] for k in ("name", "expected", "source")},
                     "genesis": gen, "status": status,
                     "matched_track": best["tid"] if accepted else "",
                     "genesis_offset_h": round(best["dt_h"], 1),
                     "genesis_offset_km": round(best["dist_km"], 0),
                     "closest_approach_km": round(best["approach_km"], 0),
                     "our_label_any": lab_any if accepted else "",
                     "our_label_persistent": lab_per if accepted else "",
                     "our_label_strict": lab_str if accepted else ""})

    return lines, pd.DataFrame(rows)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 5: Episode export and documented-case check")
    print("=" * 70)

    for f in (TS_FILE, CY_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    ts = pd.read_csv(TS_FILE, parse_dates=["datetime"])
    cyclones = pd.read_csv(CY_FILE)

    # ---------------- Part A ----------------
    criteria = PRIMARY_CRITERIA + CROSS_BASIN_CRITERIA
    print(f"\nPart A: building episodes for {len(criteria)} threshold sets ...")
    eps = build_episodes(ts, criteria)
    eps = eps.sort_values(["criterion", "class", "episode_start"])
    eps.to_csv(RESULTS_DIR / "episodes_all.csv", index=False)
    print(f"  {len(eps):,} episodes -> episodes_all.csv")

    for crit in criteria:
        sub = eps[eps["criterion"] == crit]
        line = f"  {crit:<12s}"
        for cls in CLASS_PRECEDENCE:
            c = sub[sub["class"] == cls]
            line += (f" | {cls[:5]}: {len(c):5,d} eps, "
                     f"{int(c['meets_persistent'].sum()):4,d} >=36h, "
                     f"{int(c['meets_strict'].sum()):3,d} strict")
        print(line)

    # The inspectable shortlist: sustained subtropical episodes, default set.
    short = eps[(eps["criterion"] == DEFAULT_CRITERION)
                & (eps["class"] == "subtropical")
                & eps["meets_persistent"]].copy()
    short = short.sort_values("episode_start")
    short.to_csv(RESULTS_DIR / "episodes_subtropical_strict.csv", index=False)
    print(f"\n  {len(short):,} sustained subtropical episodes ({DEFAULT_CRITERION}) "
          f"-> episodes_subtropical_strict.csv")
    print(f"    of which {int(short['meets_strict'].sum()):,} also satisfy the "
          f"strict rule")

    print("\n  First 12 strict subtropical episodes (for visual inspection):")
    cols = ["track_id", "episode_start", "episode_end", "duration_h",
            "onset_h_from_genesis", "genesis_lat", "region", "ep"]
    strict = short[short["meets_strict"]].head(12)
    print(strict[cols].to_string(index=False))

    # ---------------- Part B ----------------
    print("\n\nPart B: documented-case check ...")
    lines, table = check_cases(ts, cyclones)
    print("\n".join(lines))

    table.to_csv(RESULTS_DIR / "documented_case_check.csv", index=False)
    with open(RESULTS_DIR / "documented_case_report.txt", "w") as fh:
        fh.write("Documented-case check for the CPS classification\n")
        fh.write("=" * 70 + "\n\n")
        fh.write("\n".join(lines) + "\n")

    print("\nSummary of verdicts:")
    for status, n in table["status"].value_counts().items():
        names = ", ".join(table.loc[table["status"] == status, "name"])
        print(f"  {status:<18s} {n:2d}   ({names})")

    print(f"\nWrote {(RESULTS_DIR / 'documented_case_check.csv').relative_to(PROJECT_ROOT)}")
    print(f"Wrote {(RESULTS_DIR / 'documented_case_report.txt').relative_to(PROJECT_ROOT)}")
    print("\nStep 5 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
