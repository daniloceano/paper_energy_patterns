"""
Step 2 (CANONICAL): classify each cyclone into a pure phase class or a phase
transition, using persistence-gated states.

This is the analysis of record. The exploratory runs that established the
methodology - six threshold sets crossed with four identification rules, the
warm-seclusion diagnosis, the documented-case check - live in `sensitivity/`
and are kept for reference only.

Thresholds (`cps_criteria.CANONICAL`), following de Souza et al. (2026):
    extratropical  B > 10,          VTL < 0,    VTU < 0
    subtropical    -25 < B < 25,    VTL > -50,  VTU < -10
    tropical       B < 10,          VTL > 0,    VTU > 0

Method
------
1. Label every classifiable timestep with a class (precedence tropical >
   subtropical > extratropical; the specs overlap by construction). Timesteps in
   none of the three are `unclassified`.

2. Reduce to PERSISTENT STATES: a class counts as a state of the cyclone only
   when held for >= 36 consecutive hours (Guishard et al. 2009, "persist in its
   hybrid form for at least 36 h, i.e., more than one diurnal cycle"; Gozzo
   et al. 2014, "for more than 36 consecutive hours").

   This gating is what makes the scheme workable. On raw timestep labels, 75.5%
   of the population visits two or more classes and the commonest non-pure
   sequence is EC -> SC -> EC - a transient excursion, not a transition. There
   is no defined answer for such a cyclone under a "genesis as X, later Y" rule.

3. Apply the TROPICAL-TRANSITION TEST to every persistent tropical run
   (see `cps_criteria`, and Results below). A run that fails becomes a
   `warm_seclusion` (if preceded by an extratropical state) or an
   `indeterminate_warm_core` (if preceded by nothing), and is REMOVED from the
   state sequence, so it cannot masquerade as a tropical phase downstream.

4. Classify from the surviving state sequence:
     no persistent state          -> indeterminate
     one persistent state X       -> pure X            (EC / SC / TC)
     two or more distinct states  -> transition, named by the ordered pairs
                                     present, with precedence TT > ET > ST > SD

Transition names (ET restricted to its established meaning, Evans and Hart 2003:
"46% of Atlantic tropical storms undergo a process of extratropical transition
in which the storm evolves FROM A TROPICAL CYCLONE to a baroclinic system"):
    TT  tropical transition       EC or SC -> TC      Davis and Bosart (2003, 2004)
    ET  extratropical transition  TC -> EC            Evans and Hart (2003)
    ST  subtropical transition    EC -> SC            Reboita et al. (2022)
    SD  subtropical decay         SC -> EC            (named here; see README)

Inputs:
    results/cps_analysis/cps_timesteps.csv          (step 1)

Outputs:
    results/cps_analysis/phase_timesteps.csv
    results/cps_analysis/phase_states.csv           one row per persistent state
    results/cps_analysis/phase_classification.csv   one row per cyclone
    results/cps_analysis/phase_definitions.txt
    results/cps_analysis/cyclone_lists_by_class.csv inspection list, one row per cyclone
    results/cps_analysis/cyclone_lists_by_class.txt the same, grouped, IDs only

Run:
    python scripts/cps_analysis/step2_classify_phases.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import argparse
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from scripts.utils.ep_mapping import ALL_EPS, get_ep_label
from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    CANONICAL_SOURCE,
    CANONICAL_PRECEDENCE,
    SINGLE_STATE_CLASSES,
    TRANSITIONS,
    TRANSITION_PRECEDENCE,
    SECLUSION,
    INDETERMINATE_WARM,
    INDETERMINATE,
    CHARACTERISTIC_CLASSES,
    MIN_DOMINANCE,
    UNDETERMINED,
    MIN_PERSISTENCE_HOURS,
    PURE_GENESIS_MAX_ONSET_HOURS,
    GENESIS_LAT_BAND,
    OUT_OF_BAND,
    SC_REQUIRE_GENESIS_BAND,
    SC_MIN_OCEAN_FRACTION,
    SC_MAX_HOURS_PAST_PEAK,
    TT_MAX_POLEWARD_LAT,
    TT_MIN_OCEAN_FRACTION,
    UNCLASSIFIED,
    _in_interval,
    describe_interval,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
IN_FILE = RESULTS_DIR / "cps_timesteps.csv"

OUT_TIMESTEPS = RESULTS_DIR / "phase_timesteps.csv"
OUT_STATES = RESULTS_DIR / "phase_states.csv"
OUT_CLASS = RESULTS_DIR / "phase_classification.csv"
OUT_DEFS = RESULTS_DIR / "phase_definitions.txt"
OUT_LISTS = RESULTS_DIR / "cyclone_lists_by_class.csv"
OUT_LISTS_TXT = RESULTS_DIR / "cyclone_lists_by_class.txt"

MAX_GAP_HOURS = 3.5
CODE = {"tropical": "TC", "subtropical": "SC", "extratropical": "EC"}


# ---------------------------------------------------------------------------
# Ocean mask (same implementation as the sensitivity runs)
# ---------------------------------------------------------------------------

def build_ocean_flag(lon: pd.Series, lat: pd.Series) -> pd.Series:
    """True over ocean, NaN if Natural Earth land polygons are unavailable."""
    try:
        import cartopy.io.shapereader as shpreader
        from shapely.geometry import Point
        from shapely.ops import unary_union
        from shapely.prepared import prep
        shp = shpreader.natural_earth(resolution="110m", category="physical", name="land")
        land = prep(unary_union(list(shpreader.Reader(shp).geometries())))
    except Exception:
        return pd.Series(np.nan, index=lon.index, dtype="object")

    key = pd.Series(list(zip(lon.round(2), lat.round(2))), index=lon.index)
    lookup = {p: (not land.contains(Point(p[0], p[1]))) for p in pd.unique(key.dropna())}
    return key.map(lookup)


# ---------------------------------------------------------------------------
# Persistent states
# ---------------------------------------------------------------------------

def persistent_runs(times: np.ndarray, flag: np.ndarray,
                    min_hours: float) -> list:
    """Contiguous True runs spanning at least `min_hours`, as (start, end, hours)."""
    runs, start, prev = [], None, None
    for t, ok in zip(times, flag):
        if ok:
            gap_ok = prev is None or (t - prev) / np.timedelta64(1, "h") <= MAX_GAP_HOURS
            if start is None or not gap_ok:
                if start is not None:
                    runs.append((start, prev, (prev - start) / np.timedelta64(1, "h")))
                start = t
            prev = t
        else:
            if start is not None:
                runs.append((start, prev, (prev - start) / np.timedelta64(1, "h")))
            start = prev = None
    if start is not None:
        runs.append((start, prev, (prev - start) / np.timedelta64(1, "h")))
    return [(s, e, float(h)) for s, e, h in runs if h >= min_hours]


def tropical_transition_test(window: pd.DataFrame, previous_state: str) -> tuple:
    """Decide whether a persistent tropical run is a genuine tropical transition.

    Returns (verdict, reason); verdict is "TC" (accepted as a tropical state),
    SECLUSION, or INDETERMINATE_WARM.

    The run must lie equatorward of TT_MAX_POLEWARD_LAT and be mostly over
    ocean. Two points, both forced by the sensitivity work:

    * The test is on the position DURING the run, not at genesis. Six of the
      sixteen persistent tropical runs in this population belong to cyclones
      that formed inside 20-40 S, moved ~30 deg poleward, and only then acquired
      a warm core at 55-62 S.

    * Only the poleward bound is applied. The equatorward bound of the
      Guishard/Gozzo band exists to keep tropical systems out of a SUBTROPICAL
      climatology; here it would do the opposite of what is wanted, excluding
      the most plausibly tropical cases. Iba (Reboita et al. 2021) formed at
      about 20 S, on the edge of that band.

    `previous_state` is recorded as a descriptor of the pathway (EC -> TC or
    SC -> TC) but does NOT bypass the test: the occlusion sequence of a warm
    seclusion passes through hybrid structure too, so being preceded by a
    subtropical state is not evidence of a tropical transition.
    """
    lat_med = float(window["lat"].median())
    equatorward = lat_med > TT_MAX_POLEWARD_LAT
    ocean = pd.to_numeric(window["over_ocean"], errors="coerce")
    ocean_frac = float(ocean.mean()) if ocean.notna().any() else 1.0
    over_ocean = ocean_frac >= TT_MIN_OCEAN_FRACTION

    where = (f"run at median {lat_med:.1f} deg, {ocean_frac:.0%} over ocean")
    if equatorward and over_ocean:
        return "TC", where
    if previous_state == "EC":
        return SECLUSION, where
    return INDETERMINATE_WARM, where


def transitions_in(sequence: list) -> list:
    """Ordered transition codes implied by a sequence of persistent states."""
    names = {("EC", "SC"): "ST", ("SC", "EC"): "SD",
             ("EC", "TC"): "TT", ("SC", "TC"): "TT",
             ("TC", "EC"): "ET", ("TC", "SC"): "ET"}
    return [names[(a, b)] for a, b in zip(sequence, sequence[1:])
            if (a, b) in names]


def subtropical_identification_test(window: pd.DataFrame, genesis_lat: float,
                                    peak_time, run_start) -> tuple:
    """Gozzo criteria 1 and 3, plus the warm-seclusion guard, on a hybrid run.

    Returns (verdict, reason) where verdict is "SC", OUT_OF_BAND or SECLUSION.
    See the SUBTROPICAL IDENTIFICATION GUARDS block in cps_criteria for why each
    clause is here and why the 24 h onset criterion deliberately is not.
    """
    lo, hi = GENESIS_LAT_BAND
    in_band = pd.notna(genesis_lat) and lo < float(genesis_lat) < hi

    ocean = pd.to_numeric(window["over_ocean"], errors="coerce")
    ocean_frac = float(ocean.mean()) if ocean.notna().any() else 1.0

    past_peak = (float((run_start - peak_time) / np.timedelta64(1, "h"))
                 if peak_time is not None else 0.0)

    where = (f"genesis {float(genesis_lat):.1f} deg, {ocean_frac:.0%} over ocean, "
             f"run starts {past_peak:+.0f} h from intensity peak")

    if SC_REQUIRE_GENESIS_BAND and not in_band:
        return OUT_OF_BAND, where
    if ocean_frac < SC_MIN_OCEAN_FRACTION:
        return OUT_OF_BAND, where
    if past_peak > SC_MAX_HOURS_PAST_PEAK:
        return SECLUSION, where
    return "SC", where


def _classify_one(item):
    """Worker wrapper: takes (track_id, group), returns the classify_cyclone triple.

    Top-level so it is picklable by ProcessPoolExecutor.
    """
    _, g = item
    return classify_cyclone(g)


def classify_cyclone(g: pd.DataFrame) -> dict:
    """Full canonical classification of one cyclone."""
    g = g.sort_values("datetime")
    times = g["datetime"].values

    # Time of peak intensity, for the warm-seclusion guard. vor42 is a magnitude,
    # so the peak is its MAXIMUM.
    vor = pd.to_numeric(g["vor42"], errors="coerce")
    peak_time = g["datetime"].values[int(vor.values.argmax())] if vor.notna().any() else None
    genesis_lat = g["genesis_lat"].iloc[0]

    # --- persistent runs of every class ---
    runs = []
    for cls in CANONICAL_PRECEDENCE:
        flag = (g["cps_class"] == cls).to_numpy(dtype=bool)
        for start, end, hours in persistent_runs(times, flag, MIN_PERSISTENCE_HOURS):
            runs.append(dict(start=start, end=end, hours=hours, code=CODE[cls]))
    runs.sort(key=lambda r: r["start"])

    # Life-cycle phase in which each state begins. Recorded for every state, so
    # the timing of a transition can be expressed in life-cycle terms rather
    # than in hours from genesis.
    for r in runs:
        at = g.loc[g["datetime"] == r["start"], "period"]
        r["phase_at_onset"] = str(at.iloc[0]) if len(at) else ""

    # --- identification tests, in chronological order ---
    # Both the tropical and the subtropical classes are guarded. Extratropical
    # runs need no guard: nothing masquerades as a cold-core frontal cyclone.
    kept, rejected = [], []
    for r in runs:
        if r["code"] == "EC":
            kept.append(r)
            continue
        prev = kept[-1]["code"] if kept else "none"
        window = g[(g["datetime"] >= r["start"]) & (g["datetime"] <= r["end"])]
        if r["code"] == "TC":
            verdict, reason = tropical_transition_test(window, prev)
            accepted = verdict == "TC"
        else:
            verdict, reason = subtropical_identification_test(
                window, genesis_lat, peak_time, r["start"])
            accepted = verdict == "SC"
        r = {**r, "previous_state": prev, "tt_verdict": verdict, "tt_reason": reason,
             "lat_median": round(float(window["lat"].median()), 2),
             "vtu_median": round(float(window["VTU"].median()), 1),
             "hours_past_peak": (round(float((r["start"] - peak_time)
                                             / np.timedelta64(1, "h")), 1)
                                 if peak_time is not None else np.nan),
             "phase_at_onset": str(window["period"].iloc[0])}
        if accepted:
            kept.append(r)
        else:
            rejected.append(r)

    sequence = [r["code"] for r in kept]
    # Collapse immediate repeats (EC, EC -> EC) so the sequence reads as states.
    collapsed = [c for i, c in enumerate(sequence) if i == 0 or c != sequence[i - 1]]
    trans = transitions_in(collapsed)

    classifiable = g["cps_class"].notna()
    n_class = int(classifiable.sum())
    frac = {c: (float((g.loc[classifiable, "cps_class"] == c).mean())
                if n_class else np.nan)
            for c in CANONICAL_PRECEDENCE}

    # --- characteristics, for cyclones with no persistent state ---
    # The 36 h requirement is left untouched for the named classes; a cyclone
    # that never meets it is described by what it showed, not pooled into one
    # undifferentiated bucket.
    dominant_code, dominance = "", np.nan
    if n_class:
        counts = g.loc[classifiable, "cps_class"].value_counts(normalize=True)
        top = counts.idxmax()
        dominance = float(counts.max())
        dominant_code = CODE.get(top, "")

    # --- headline label ---
    if not collapsed:
        if dominant_code and dominance >= MIN_DOMINANCE:
            label = f"{dominant_code}_like"
        else:
            label = UNDETERMINED
    elif len(set(collapsed)) == 1:
        label = collapsed[0]
    else:
        label = next(t for t in TRANSITION_PRECEDENCE if t in trans)

    # --- genesis framing -----------------------------------------------------
    # The literature's "pure" qualifies the GENESIS: Silva et al. (2022) call
    # Guara a "genese subtropical pura" while also reporting that it later
    # became extratropical. So the first persistent state, and whether it is in
    # place from the start, are reported as their own quantities.
    genesis_state = kept[0]["code"] if kept else ""
    genesis_onset = (float((kept[0]["start"] - times[0]) / np.timedelta64(1, "h"))
                     if kept else np.nan)

    # Share of the cyclone's own classifiable timesteps spent in each class -
    # the "spent most of its life as X" reading, which the class label does NOT
    # assert on its own.

    # What the cyclone showed BEFORE its first persistent state, even if that
    # structure never lasted 36 h. This is what makes a case like 19980144 -
    # 30 h subtropical followed by 39 h tropical - legible: the subtropical
    # phase is 6 h short of the gate, so it is not a state, but recording it
    # flags the cyclone as a tropical-transition candidate without claiming it.
    antecedent, antecedent_h = "", 0.0
    if kept:
        pre = g[g["datetime"] < kept[0]["start"]]
        # `unclassified` is a real label, not missing data, but it says nothing
        # about what the cyclone was, so it is excluded here.
        pre_c = pre.loc[pre["cps_class"].isin(CANONICAL_PRECEDENCE), "cps_class"]
        if len(pre_c):
            top = pre_c.value_counts().idxmax()
            longest = max((h for _, _, h in persistent_runs(
                pre["datetime"].values, (pre["cps_class"] == top).to_numpy(dtype=bool), 0.0)),
                default=0.0)
            if longest > 0:
                antecedent, antecedent_h = CODE.get(top, ""), longest

    out = dict(
        phase_class=label,
        antecedent_characteristics=antecedent,
        antecedent_hours=round(antecedent_h, 1),
        genesis_state=genesis_state,
        genesis_onset_h=round(genesis_onset, 1) if np.isfinite(genesis_onset) else np.nan,
        pure_genesis=bool(genesis_state
                          and np.isfinite(genesis_onset)
                          and genesis_onset <= PURE_GENESIS_MAX_ONSET_HOURS),
        frac_EC=round(frac["extratropical"], 3),
        frac_SC=round(frac["subtropical"], 3),
        frac_TC=round(frac["tropical"], 3),
        dominant_class=dominant_code,
        dominance=round(dominance, 3) if np.isfinite(dominance) else np.nan,
        state_sequence="->".join(collapsed) if collapsed else "",
        n_persistent_states=len(collapsed),
        transitions=",".join(trans),
        n_transitions=len(trans),
        has_TT="TT" in trans, has_ET="ET" in trans,
        has_ST="ST" in trans, has_SD="SD" in trans,
        n_warm_seclusions=sum(r["tt_verdict"] == SECLUSION for r in rejected),
        n_indeterminate_warm=sum(r["tt_verdict"] == INDETERMINATE_WARM for r in rejected),
        n_out_of_band=sum(r["tt_verdict"] == OUT_OF_BAND for r in rejected),
        n_rejected_SC=sum(r["code"] == "SC" for r in rejected),
        hours_EC=sum(r["hours"] for r in kept if r["code"] == "EC"),
        hours_SC=sum(r["hours"] for r in kept if r["code"] == "SC"),
        hours_TC=sum(r["hours"] for r in kept if r["code"] == "TC"),
    )
    return out, kept, rejected


def main(jobs: int = 1):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 2 (CANONICAL): phase classification")
    print("=" * 70)

    if not IN_FILE.exists():
        print(f"Missing {IN_FILE}. Run step 1 first.")
        return 1

    df = pd.read_csv(IN_FILE, parse_dates=["datetime"])
    print(f"\nLoaded {len(df):,} timesteps for {df['track_id'].nunique():,} cyclones")
    print(f"Thresholds: {CANONICAL_SOURCE}")
    for cls in CANONICAL_PRECEDENCE:
        terms = ", ".join(describe_interval(iv, p) for p, iv in CANONICAL[cls].items())
        print(f"  {cls:<14s} {terms}")
    print(f"Persistence: >= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours")

    # --- ocean mask ---
    print("\nBuilding ocean mask ...")
    df["over_ocean"] = build_ocean_flag(df["lon"], df["lat"])
    if df["over_ocean"].notna().any():
        print(f"  {pd.to_numeric(df['over_ocean'], errors='coerce').mean():.1%} over ocean")
    else:
        print("  Land polygons unavailable — the ocean clause of the TT test is skipped.")

    # --- timestep labels ---
    classifiable = df[["B", "VTL", "VTU"]].notna().all(axis=1)
    label = pd.Series(UNCLASSIFIED, index=df.index, dtype=object)
    for cls in reversed(CANONICAL_PRECEDENCE):
        mask = classifiable.copy()
        for param, interval in CANONICAL[cls].items():
            mask &= _in_interval(df[param], interval)
        label = label.mask(mask, cls)
    df["cps_class"] = label.mask(~classifiable, np.nan)

    counts = df["cps_class"].value_counts()
    total = counts.sum()
    print("\nTimestep labels:")
    for cls in CANONICAL_PRECEDENCE + [UNCLASSIFIED]:
        n = int(counts.get(cls, 0))
        print(f"  {cls:<14s} {n:8,d}  ({n / total:5.1%})")

    df.to_csv(OUT_TIMESTEPS, index=False)
    print(f"\nWrote {OUT_TIMESTEPS.relative_to(PROJECT_ROOT)}")

    # --- per-cyclone classification ---
    # Parallel over cyclones: each is independent, and the ordering is restored
    # by sorting on track_id afterwards, so the output is identical to a serial
    # run regardless of --jobs.
    print(f"\nClassifying cyclones (jobs = {jobs}) ...")
    groups = [(tid, g) for tid, g in df.groupby("track_id", sort=True)]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            results = list(ex.map(_classify_one, groups, chunksize=32))
    else:
        results = [_classify_one(item) for item in groups]

    rows, state_rows = [], []
    for (tid, g), (out, kept, rejected) in zip(groups, results):
        rows.append({"track_id": tid, "ep": g["ep"].iloc[0],
                     "region": g["region"].iloc[0],
                     "genesis_lat": g["genesis_lat"].iloc[0],
                     "genesis_lon": g["genesis_lon"].iloc[0],
                     "year": g["datetime"].iloc[0].year, **out})
        for r in kept + rejected:
            state_rows.append({
                "track_id": tid, "ep": g["ep"].iloc[0],
                "state": r["code"] if r in kept else r["tt_verdict"],
                # Which class the run WAS before any verdict. Without this a
                # rejected run labelled `warm_seclusion` is ambiguous: both the
                # tropical and the subtropical guard can emit that verdict.
                "run_code": r["code"],
                "start": pd.Timestamp(r["start"]), "end": pd.Timestamp(r["end"]),
                "duration_h": r["hours"],
                "onset_h_from_genesis": round(
                    float((r["start"] - g["datetime"].values[0]) / np.timedelta64(1, "h")), 1),
                "previous_state": r.get("previous_state", ""),
                "tt_verdict": r.get("tt_verdict", ""),
                "tt_reason": r.get("tt_reason", ""),
                "lat_median": r.get("lat_median", ""),
                "vtu_median": r.get("vtu_median", ""),
                "hours_past_peak": r.get("hours_past_peak", ""),
                "phase_at_onset": r.get("phase_at_onset", ""),
            })

    cyclones = pd.DataFrame(rows)
    states = pd.DataFrame(state_rows).sort_values(["track_id", "start"])
    cyclones.to_csv(OUT_CLASS, index=False)
    states.to_csv(OUT_STATES, index=False)
    print(f"Wrote {OUT_CLASS.relative_to(PROJECT_ROOT)}  ({len(cyclones):,} cyclones)")
    print(f"Wrote {OUT_STATES.relative_to(PROJECT_ROOT)}  ({len(states):,} persistent states)")

    # --- summary ---
    print("\n" + "-" * 70)
    print("PHASE CLASSIFICATION — whole population")
    print("-" * 70)
    order = (list(SINGLE_STATE_CLASSES) + TRANSITION_PRECEDENCE
             + list(CHARACTERISTIC_CLASSES) + [UNDETERMINED])
    vc = cyclones["phase_class"].value_counts()
    for k in order:
        n = int(vc.get(k, 0))
        desc = (SINGLE_STATE_CLASSES.get(k) or TRANSITIONS.get(k)
                or CHARACTERISTIC_CLASSES.get(k) or "no dominant structure")
        print(f"  {k:<16s} {n:6,d}  ({n / len(cyclones):5.1%})   {desc}")

    print("\n  Cyclones showing each transition (not mutually exclusive):")
    for t in TRANSITION_PRECEDENCE:
        n = int(cyclones[f"has_{t}"].sum())
        print(f"    {t}: {n:5,d}")

    print(f"\n  Persistent tropical runs rejected by the TT test:")
    print(f"    warm seclusions        : {int(cyclones['n_warm_seclusions'].sum()):,}")
    print(f"    indeterminate warm core: {int(cyclones['n_indeterminate_warm'].sum()):,}")
    n_tt_runs = int((states["state"] == "TC").sum())
    print(f"    accepted tropical runs : {n_tt_runs:,}")

    if n_tt_runs:
        print("\n  Accepted tropical runs:")
        cols = ["track_id", "start", "end", "duration_h", "previous_state",
                "lat_median", "vtu_median", "phase_at_onset", "tt_reason"]
        print(states[states["state"] == "TC"][cols].to_string(index=False))

    print("\n" + "-" * 70)
    print("GENESIS FRAMING  (the sense in which the literature says \"pure\")")
    print("-" * 70)
    print("  Silva et al. (2022) call Guara a 'genese subtropical pura' and also report")
    print("  that it later became extratropical, so 'pure' qualifies the genesis, not")
    print("  the whole life. First persistent state, and whether it is in place within")
    print(f"  {PURE_GENESIS_MAX_ONSET_HOURS:.0f} h of genesis:")
    for code, name in SINGLE_STATE_CLASSES.items():
        sub = cyclones[cyclones["genesis_state"] == code]
        if sub.empty:
            continue
        n_pure = int(sub["pure_genesis"].sum())
        print(f"    {code} genesis: {len(sub):5,d} cyclones, of which "
              f"{n_pure:5,d} ({n_pure / len(sub):5.1%}) with the state in place "
              f"within {PURE_GENESIS_MAX_ONSET_HOURS:.0f} h")

    print("\n  How much of its own life each class actually spends in its own class:")
    for code in SINGLE_STATE_CLASSES:
        sub = cyclones[cyclones["phase_class"] == code]
        if sub.empty:
            continue
        f = sub[f"frac_{code}"]
        share = " ".join(f">={t:.0%}: {(f >= t).sum():4d}" for t in (0.5, 0.7, 0.9))
        print(f"    {code}: median {f.median():.2f}  (p10 {f.quantile(.1):.2f}, "
              f"p90 {f.quantile(.9):.2f})   {share}")
        n_dom = int((sub["dominant_class"] == code).sum())
        print(f"        {code} is the dominant class in {n_dom:,} of {len(sub):,} "
              f"({n_dom / len(sub):.0%})")

    print("\n  Most common state sequences:")
    print(cyclones["state_sequence"].value_counts().head(10).to_string())

    # --- definitions file ---
    with open(OUT_DEFS, "w") as fh:
        fh.write("CANONICAL CPS phase classification\n")
        fh.write("=" * 60 + "\n\n")
        fh.write(f"Thresholds: {CANONICAL_SOURCE}\n")
        for cls in CANONICAL_PRECEDENCE:
            terms = ", ".join(describe_interval(iv, p) for p, iv in CANONICAL[cls].items())
            fh.write(f"  {cls:<14s} {terms}\n")
        fh.write(f"\nPersistence gate : >= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours\n")
        fh.write("Timestep precedence: " + " > ".join(CANONICAL_PRECEDENCE) + "\n")
        fh.write("\nTropical-transition test on each persistent tropical run:\n")
        fh.write(f"  run median latitude equatorward of {TT_MAX_POLEWARD_LAT:.0f} deg "
                 f"AND >= {TT_MIN_OCEAN_FRACTION:.0%} over ocean -> accept\n")
        fh.write("  else: warm_seclusion (if preceded by EC) or "
                 "indeterminate_warm_core\n")
        fh.write("  the preceding state (EC -> TC or SC -> TC) is recorded as a\n")
        fh.write("  pathway descriptor and does NOT bypass the test\n")
        fh.write("\nCharacteristic classes for cyclones with no persistent state:\n")
        fh.write(f"  dominant structure >= {MIN_DOMINANCE:.0%} of classifiable steps "
                 f"-> EC_like / SC_like / TC_like\n")
        fh.write("  otherwise -> undetermined\n")
        fh.write("\nTransition codes:\n")
        for k, v in TRANSITIONS.items():
            fh.write(f"  {k}: {v}\n")
        fh.write("Headline precedence: " + " > ".join(TRANSITION_PRECEDENCE) + "\n")
    print(f"\nWrote {OUT_DEFS.relative_to(PROJECT_ROOT)}")

    # --- inspection lists --------------------------------------------------
    # One row per cyclone, sorted by class then date, carrying enough context to
    # go and look a case up: when and where it formed, what its state sequence
    # was, and how long it held each state.
    genesis = df.groupby("track_id")["datetime"].min()
    lists = cyclones.copy()
    lists["genesis_time"] = lists["track_id"].map(genesis)
    lists["ep"] = lists["ep"].map(
        lambda e: get_ep_label(int(e)) if pd.notna(e) else "")
    cols = ["phase_class", "track_id", "ep", "region", "genesis_time",
            "antecedent_characteristics", "antecedent_hours",
            "genesis_lat", "genesis_lon", "genesis_state", "genesis_onset_h",
            "pure_genesis", "dominant_class", "frac_EC", "frac_SC", "frac_TC",
            "state_sequence", "transitions", "hours_EC", "hours_SC", "hours_TC",
            "n_warm_seclusions", "n_indeterminate_warm"]
    lists = lists[cols].sort_values(["phase_class", "genesis_time"])
    lists.to_csv(OUT_LISTS, index=False)
    print(f"Wrote {OUT_LISTS.relative_to(PROJECT_ROOT)}")

    with open(OUT_LISTS_TXT, "w") as fh:
        fh.write("Cyclone track_id lists by canonical phase class\n")
        fh.write("=" * 60 + "\n")
        fh.write(f"population: {len(cyclones):,} cyclones\n\n")
        for k in order:
            ids = lists.loc[lists["phase_class"] == k, "track_id"].tolist()
            desc = (SINGLE_STATE_CLASSES.get(k) or TRANSITIONS.get(k)
                or CHARACTERISTIC_CLASSES.get(k) or "no dominant structure")
            fh.write(f"\n{k}  —  {desc}  —  {len(ids):,} cyclones\n")
            fh.write("-" * 60 + "\n")
            for i in range(0, len(ids), 10):
                fh.write("  " + "  ".join(f"{t}" for t in ids[i:i + 10]) + "\n")
        # Warm seclusions are not a phase class but are worth listing.
        sec = cyclones.loc[cyclones["n_warm_seclusions"] > 0, "track_id"].tolist()
        fh.write(f"\n\nwarm seclusions (rejected tropical runs) — {len(sec)} cyclones\n")
        fh.write("-" * 60 + "\n")
        for i in range(0, len(sec), 10):
            fh.write("  " + "  ".join(f"{t}" for t in sec[i:i + 10]) + "\n")
    print(f"Wrote {OUT_LISTS_TXT.relative_to(PROJECT_ROOT)}")

    print("\nStep 2 complete.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", "-j", type=int, default=1,
                    help="parallel workers over cyclones (default 1). Output is "
                         "independent of this value.")
    sys.exit(main(jobs=ap.parse_args().jobs))
