#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_corrected_tracks.py — Per-timestep tracks carrying corrected energetics.

Drop-in replacement for ``data/tracks_SAt_filtered_with_energetics_processed.csv``,
which is a legacy artefact: its ``Kz, Ke, Ck, Ca, BAe, BKe, Ge`` columns come
from the superseded LorenzCycleToolKit results and must not reach any figure of
this article again.

What is kept and what is rebuilt
--------------------------------
* Kept from the tracks database (Zenodo DOI 10.5281/zenodo.18133432): the
  1-hourly positions and ``vor42``. These are *tracking* quantities, unrelated
  to the LEC equations, and they are the very input the rerun fed to the
  toolkit. Reusing them is not reusing legacy energetics.
* Rebuilt from the corrected rerun: every LEC term, taken from each cyclone's
  integrated results file at the 3-hourly steps the toolkit actually computed.

The output reproduces the legacy schema exactly -- 1-hourly rows, LEC columns
populated only on the 3-hourly steps and NaN in between -- so the figure scripts
that consume it need no change beyond their input path.

Only the 3,820 cyclones of the rerun population appear; the legacy file also
carried cyclones outside it, which never had usable energetics.

Usage
-----
    RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
    python -m scripts.lec_climatology_rerun.build_corrected_tracks --run-root "$RUN"

    # exploratory build from the cyclones finished so far (never for the paper)
    python -m scripts.lec_climatology_rerun.build_corrected_tracks \\
        --run-root "$RUN" --allow-partial

Output
------
    data/corrected/tracks_with_energetics_corrected.csv

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.utils import corrected_lec as clec  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: Tracking columns carried over unchanged. Deliberately excludes every LEC
#: column of the legacy file.
TRACK_COLUMNS = ["track_id", "date", "lon vor", "lat vor", "vor42"]

#: LEC columns written by this builder, in the legacy column order so the
#: output is a positional drop-in.
LEC_COLUMNS = ["Kz", "Ke", "Ck", "Ca", "BAe", "BKe", "Ge"]

DEFAULT_TRACK_SOURCE = (
    PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"
)


def load_track_positions(source: Path, track_ids: set[str]) -> pd.DataFrame:
    """1-hourly positions of the rerun population, without legacy energetics."""
    frame = pd.read_csv(source, usecols=TRACK_COLUMNS, dtype={"track_id": str})
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame[frame["track_id"].isin(track_ids)]
    return frame.sort_values(["track_id", "date"], ignore_index=True)


def corrected_terms(track_id: str) -> pd.DataFrame:
    """Corrected LEC terms of one cyclone at its computed timesteps."""
    results = clec.read_integrated(track_id)
    missing = [term for term in LEC_COLUMNS if term not in results.columns]
    if missing:
        raise ValueError(f"{track_id}: corrected results lack {missing}")
    terms = results[LEC_COLUMNS].copy()
    terms.insert(0, "track_id", str(track_id))
    return terms.reset_index().rename(columns={"time": "date"})


def build(track_ids: list[str], source: Path, output: Path, workers: int) -> Path:
    positions = load_track_positions(source, set(track_ids))
    found = set(positions["track_id"].unique())
    absent = sorted(set(track_ids) - found)
    if absent:
        raise ValueError(
            f"{len(absent)} rerun cyclones have no track positions in {source} "
            f"(first: {absent[:5]}). The tracks source does not match the rerun."
        )

    frames: list[pd.DataFrame] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(corrected_terms, tid): tid for tid in track_ids}
        for done, future in enumerate(as_completed(futures), start=1):
            frames.append(future.result())
            if done % 250 == 0 or done == len(track_ids):
                print(f"  read {done}/{len(track_ids)} corrected result files", flush=True)

    energetics = pd.concat(frames, ignore_index=True)
    merged = positions.merge(energetics, on=["track_id", "date"], how="left")

    unmatched = energetics.merge(
        positions[["track_id", "date"]], on=["track_id", "date"], how="left", indicator=True
    )
    orphans = int((unmatched["_merge"] == "left_only").sum())
    if orphans:
        raise ValueError(
            f"{orphans} corrected timesteps have no matching track position. "
            "Positions and LEC timestamps must agree exactly."
        )

    covered = merged.loc[merged["Ck"].notna(), "track_id"].nunique()
    if covered != len(track_ids):
        raise ValueError(f"only {covered}/{len(track_ids)} cyclones carry LEC values")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    merged.to_csv(temporary, index=False)
    temporary.replace(output)

    print(f"\ncyclones           : {covered}")
    print(f"rows (1-hourly)    : {len(merged)}")
    print(f"rows with LEC (3-h): {int(merged['Ck'].notna().sum())}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--run-root", type=Path)
    parser.add_argument(
        "--track-source", type=Path, default=DEFAULT_TRACK_SOURCE,
        help="tracks database providing positions and vor42 (LEC columns ignored)",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument(
        "--allow-partial", action="store_true",
        help="build from the cyclones already COMPLETE; exploratory only",
    )
    parser.add_argument(
        "--limit", type=int, metavar="N",
        help="smoke test on the first N cyclones; implies --allow-partial",
    )
    args = parser.parse_args()

    if args.run_root:
        import os

        os.environ["PAPER_LEC_RUN_ROOT"] = str(args.run_root)

    if args.limit:
        args.allow_partial = True
    if args.allow_partial:
        track_ids = clec.complete_track_ids()[: args.limit]
        suffix = "_partial"
        print(
            f"WARNING: partial build from {len(track_ids)} COMPLETE cyclones of "
            f"{clec.EXPECTED_POPULATION}. Not publishable.",
        )
    else:
        track_ids = clec.require_complete("build_corrected_tracks")
        suffix = ""

    output = args.output or clec.corrected_path(
        clec.TRACKS_WITH_ENERGETICS.replace(".csv", f"{suffix}.csv")
    )
    print(build(track_ids, args.track_source, output, args.workers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
