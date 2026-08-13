"""
Export the CPS dataset for the cyclone_monitor_south_atlantic repository.

Consolidates the Cyclone Phase Space results of this project into two flat CSVs
in the format of that repository's Dataset 1 (`tracks_SAt_source.csv`): a
per-timestep table keyed on (`track_id`, `date`), and a per-cyclone
classification reference.

Join contract
-------------
Every (`track_id`, `date`) pair written here exists in the monitor's track file
(verified at export: 212,996 / 212,996). The CPS series are 3-HOURLY while the
track file is 1-hourly, so the CPS table joins onto a SUBSET of its rows:

    tracks.merge(cps, on=["track_id", "date"], how="left")

leaves NaN on the two hours between CPS timesteps. The values are deliberately
NOT interpolated to 1-hourly, unlike the LEC terms in Dataset 1. The CPS
parameters are the input to a threshold classification, and interpolated points
would be labelled from values nobody computed; the literature this protocol
follows controls short-term noise through a persistence requirement rather than
through interpolation or smoothing.

Population
----------
All tracks, not only those carrying an Energy Pattern. 6,776 of the catalogue's
6,789 cyclones have CPS series; the 13 without (one 2002, twelve 2009) appear in
the classification file with `has_cps = False` so the gap is explicit rather
than silent.

Inputs:
    results/cps_analysis/phase_timesteps.csv
    results/cps_analysis/phase_classification.csv
    data/tracks_SAt_filtered_with_energetics_processed.csv   (join verification)

Outputs (in the monitor repo, data/raw/ — gitignored there):
    cps_parameters_SAt.csv
    cps_classification_SAt.csv
    cps_consolidation_report.txt

Run:
    python scripts/cps_analysis/export_cps_for_monitor.py
    python scripts/cps_analysis/export_cps_for_monitor.py --dest /other/path

Author: Danilo Couto de Souza
Date: August 2026
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    CANONICAL_SOURCE,
    CANONICAL_PRECEDENCE,
    SINGLE_STATE_CLASSES,
    TRANSITIONS,
    CHARACTERISTIC_CLASSES,
    UNDETERMINED,
    MIN_PERSISTENCE_HOURS,
    GENESIS_LAT_BAND,
    SC_MIN_OCEAN_FRACTION,
    SC_MAX_HOURS_PAST_PEAK,
    TT_MAX_POLEWARD_LAT,
    describe_interval,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT_ROOT / "results" / "cps_analysis"
TRACKS = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"
DEFAULT_DEST = Path("/p1-swell/danilocs/cyclone_monitor_south_atlantic/data/raw")

NO_CPS = "no_cps_data"

# Whether a class is an IDENTIFICATION or merely a description. This distinction
# is the whole point of the `*_like` naming and it must survive the export: a
# consumer that groups `SC_like` under "Subtropical" is asserting something the
# classification explicitly refuses to assert. The columns `class_kind` and
# `is_identified` exist so that grouping cannot be got wrong by accident.
#
#   identified     passed the 36 h persistence gate AND the identification
#                  guards (genesis band, ocean, warm-seclusion test)
#   characteristic showed a dominant structure that never lasted 36 h; NOT
#                  guarded, and NOT a claim that the cyclone is of that type
#   undetermined   no dominant structure
#   no_data        no CPS series
CLASS_KIND = {
    **{c: "identified" for c in list(SINGLE_STATE_CLASSES) + list(TRANSITIONS)},
    **{c: "characteristic" for c in CHARACTERISTIC_CLASSES},
    UNDETERMINED: "undetermined",
}
CLASS_LABELS = {**SINGLE_STATE_CLASSES, **TRANSITIONS, **CHARACTERISTIC_CLASSES,
                UNDETERMINED: "no structure held for the persistence gate, none dominant",
                NO_CPS: "no CPS series computed for this cyclone"}

TS_COLUMNS = ["track_id", "date", "B", "VTL", "VTU", "SIZE", "dir",
              "lat", "lon", "over_ocean", "cps_class", "cps_state"]
CY_COLUMNS = ["track_id", "year", "region", "genesis_lat", "genesis_lon", "ep",
              "has_cps", "phase_class", "phase_class_label",
              "class_kind", "is_identified",
              "genesis_state", "genesis_onset_h", "pure_genesis",
              "state_sequence", "transitions", "n_persistent_states",
              "dominant_class", "dominance", "frac_EC", "frac_SC", "frac_TC",
              "hours_EC", "hours_SC", "hours_TC",
              "n_warm_seclusions", "n_out_of_band", "n_indeterminate_warm",
              "antecedent_characteristics", "antecedent_hours"]


def build_timesteps() -> pd.DataFrame:
    """Per-timestep CPS parameters, with BOTH views of the classification.

    `cps_class` is the raw threshold label of that single timestep: no
    persistence, no guards. It is the right thing to colour a phase diagram by,
    and the wrong thing to count cyclone types with.

    `cps_state` is the guarded view: the accepted persistent state covering that
    timestep, or empty. A timestep inside a run that the guards REJECTED (warm
    seclusion, genesis out of band) is empty here even though `cps_class` may
    read "subtropical" — which is exactly the distinction that gets lost when
    only the raw label is shipped.
    """
    ts = pd.read_csv(RESULTS / "phase_timesteps.csv", parse_dates=["datetime"])
    ts = ts.rename(columns={"datetime": "date"})
    ts["cps_class"] = ts["cps_class"].fillna("unclassified")

    states = pd.read_csv(RESULTS / "phase_states.csv", parse_dates=["start", "end"])
    accepted = states[states["state"].isin(["EC", "SC", "TC"])]
    ts["cps_state"] = ""
    idx = {t: g for t, g in accepted.groupby("track_id")}
    col = ts.columns.get_loc("cps_state")
    for tid, g in ts.groupby("track_id"):
        runs = idx.get(tid)
        if runs is None:
            continue
        for r in runs.itertuples():
            m = (g["date"] >= r.start) & (g["date"] <= r.end)
            ts.iloc[g.index[m.to_numpy()], col] = r.state
    return ts[TS_COLUMNS].sort_values(["track_id", "date"]).reset_index(drop=True)


def build_classification() -> pd.DataFrame:
    cy = pd.read_csv(RESULTS / "phase_classification.csv")
    cy["has_cps"] = True

    # The 13 cyclones without CPS series are carried explicitly, so a consumer
    # joining on track_id never silently loses them.
    if TRACKS.exists():
        allt = pd.read_csv(TRACKS, usecols=["track_id", "date"],
                           parse_dates=["date"])
        missing = sorted(set(allt.track_id) - set(cy.track_id))
        if missing:
            first = allt.groupby("track_id")["date"].min()
            extra = pd.DataFrame({
                "track_id": missing,
                "year": [int(first[t].year) for t in missing],
                "has_cps": False,
                "phase_class": NO_CPS,
            })
            cy = pd.concat([cy, extra], ignore_index=True)

    cy["class_kind"] = cy["phase_class"].map(CLASS_KIND).fillna("no_data")
    cy["is_identified"] = cy["class_kind"] == "identified"
    cy["phase_class_label"] = cy["phase_class"].map(CLASS_LABELS)
    for c in CY_COLUMNS:
        if c not in cy:
            cy[c] = pd.NA
    return cy[CY_COLUMNS].sort_values("track_id").reset_index(drop=True)


def verify_join(ts: pd.DataFrame) -> dict:
    if not TRACKS.exists():
        return {"checked": False}
    trk = pd.read_csv(TRACKS, usecols=["track_id", "date"], parse_dates=["date"])
    keys_t = set(zip(trk.track_id, trk.date))
    keys_c = set(zip(ts.track_id, ts.date))
    return {"checked": True, "track_rows": len(trk),
            "track_cyclones": int(trk.track_id.nunique()),
            "cps_keys": len(keys_c), "matched": len(keys_c & keys_t)}


def write_report(path: Path, ts: pd.DataFrame, cy: pd.DataFrame, join: dict,
                 outputs: dict) -> None:
    L = []
    bar = "=" * 70
    sub = "─" * 70
    L += [bar, "CPS Consolidation Report", bar, "",
          f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
          f"Source project: {PROJECT_ROOT}",
          f"Produced by: scripts/cps_analysis/export_cps_for_monitor.py", ""]
    L += [sub, "Output files", sub]
    for name, p in outputs.items():
        size = p.stat().st_size / 1e6 if p.exists() else 0
        L.append(f"  {name:<30s} {size:8.1f} MB")
    L += ["", sub, "Dataset 1 — per-timestep CPS parameters", sub,
          f"  Rows:            {len(ts):,}",
          f"  Unique tracks:   {ts.track_id.nunique():,}",
          f"  Date range:      {ts.date.min():%Y-%m-%d} to {ts.date.max():%Y-%m-%d}",
          f"  Temporal step:   3-hourly (NOT interpolated to 1-hourly)",
          f"  Duplicate keys:  {int(ts.duplicated(['track_id', 'date']).sum())}", ""]
    L += [sub, "Join verification against the monitor track file", sub]
    if join["checked"]:
        pct = 100 * join["matched"] / join["cps_keys"]
        L += [f"  Track file rows:        {join['track_rows']:,}",
              f"  Track file cyclones:    {join['track_cyclones']:,}",
              f"  CPS (track_id, date) keys: {join['cps_keys']:,}",
              f"  Found in track file:    {join['matched']:,}  ({pct:.2f}%)",
              f"  STATUS: {'PASS' if pct == 100 else 'INCOMPLETE — investigate'}"]
    else:
        L.append("  SKIPPED — reference track file not available locally")
    L += ["", sub, "Per-timestep labels — raw vs guarded", sub,
          "  cps_class = raw threshold label of that timestep (no persistence, no guards)"]
    for k, v in ts.cps_class.value_counts().items():
        L.append(f"    {k:<16s} {v:9,d}  ({100 * v / len(ts):5.1f}%)")
    L.append("  cps_state = accepted persistent state covering that timestep")
    sv = ts.cps_state.replace("", "(none)").value_counts()
    for k, v in sv.items():
        L.append(f"    {k:<16s} {v:9,d}  ({100 * v / len(ts):5.1f}%)")
    L += ["", sub, "Identification vs description", sub,
          "  Grouping a `*_like` class under Subtropical or Tropical asserts what the",
          "  classification refuses to assert. Use `is_identified` / `class_kind`."]
    for k, v in cy.class_kind.value_counts().items():
        L.append(f"    {k:<16s} {v:6,d}  ({100 * v / len(cy):5.2f}%)")
    L += ["", sub, "Dataset 2 — per-cyclone classification", sub,
          f"  Rows:            {len(cy):,}",
          f"  With CPS series: {int(cy.has_cps.sum()):,}",
          f"  Without:         {int((~cy.has_cps.astype(bool)).sum()):,}", ""]
    vc = cy.phase_class.value_counts()
    for k in list(SINGLE_STATE_CLASSES) + list(TRANSITIONS) + \
            list(CHARACTERISTIC_CLASSES) + [UNDETERMINED, NO_CPS]:
        n = int(vc.get(k, 0))
        L.append(f"  {k:<16s} {n:6,d}  ({100 * n / len(cy):5.2f}%)   {CLASS_LABELS[k]}")
    L += ["", sub, "Classification protocol", sub,
          f"  Thresholds: {CANONICAL_SOURCE}"]
    for cls in CANONICAL_PRECEDENCE:
        terms = ", ".join(describe_interval(iv, p) for p, iv in CANONICAL[cls].items())
        L.append(f"    {cls:<14s} {terms}")
    L += [f"  Timestep precedence: {' > '.join(CANONICAL_PRECEDENCE)}",
          f"  Persistence gate:    >= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours",
          f"  Subtropical guards:  genesis in "
          f"{abs(GENESIS_LAT_BAND[1]):.0f}-{abs(GENESIS_LAT_BAND[0]):.0f} S, "
          f">= {SC_MIN_OCEAN_FRACTION:.0%} over ocean, run starting no more than "
          f"{SC_MAX_HOURS_PAST_PEAK:.0f} h past the intensity peak",
          f"  Tropical guard:      run equatorward of "
          f"{abs(TT_MAX_POLEWARD_LAT):.0f} S and over ocean", "",
          "  Full method: scripts/cps_analysis/SCIENTIFIC_NOTES.md in the source project.",
          "  CPS parameters computed by Andres Rodriguez (IAG-USP).", "", bar]
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST,
                    help=f"destination directory (default {DEFAULT_DEST})")
    args = ap.parse_args()
    dest = args.dest
    if not dest.exists():
        print(f"Destination does not exist: {dest}")
        return 1

    print("=" * 70)
    print("EXPORT CPS DATASET FOR cyclone_monitor_south_atlantic")
    print("=" * 70)

    ts = build_timesteps()
    cy = build_classification()
    join = verify_join(ts)

    outputs = {"cps_parameters_SAt.csv": dest / "cps_parameters_SAt.csv",
               "cps_classification_SAt.csv": dest / "cps_classification_SAt.csv",
               "cps_consolidation_report.txt": dest / "cps_consolidation_report.txt"}

    ts.to_csv(outputs["cps_parameters_SAt.csv"], index=False)
    cy.to_csv(outputs["cps_classification_SAt.csv"], index=False)
    write_report(outputs["cps_consolidation_report.txt"], ts, cy, join, outputs)

    print(f"\n  timesteps : {len(ts):,} rows, {ts.track_id.nunique():,} cyclones")
    print(f"  cyclones  : {len(cy):,} rows "
          f"({int(cy.has_cps.sum()):,} with CPS, "
          f"{int((~cy.has_cps.astype(bool)).sum())} without)")
    if join["checked"]:
        pct = 100 * join["matched"] / join["cps_keys"]
        print(f"  join check: {join['matched']:,}/{join['cps_keys']:,} "
              f"({pct:.2f}%) keys found in the monitor track file")
    for name, p in outputs.items():
        print(f"  wrote {p}  ({p.stat().st_size / 1e6:.1f} MB)")
    print("\nExport complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
