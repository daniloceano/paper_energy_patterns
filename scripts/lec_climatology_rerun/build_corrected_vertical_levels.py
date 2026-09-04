#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_corrected_vertical_levels.py — Phase-mean vertical profiles for the whole
corrected climatology.

The corrected rerun writes, for every one of the 3,820 cyclones, a full set of
pressure-level files including the five ``Ck`` subterms. That is what makes the
barotropic decomposition available for **every** Energy Pattern instead of the
EP1-only side run that ``scripts/ck_subterms_analysis`` used to launch: the
subterms already exist for the whole population, so no extra ERA5 download or
toolkit execution is needed.

Reading 3,820 x N pressure-level CSVs in every figure script is slow and invites
each script to re-implement the unit conventions. This builder collapses them
once into a single tidy table of phase means:

    track_id | phase | term | level_hpa | value

Values pass through :mod:`scripts.utils.corrected_lec`, so the ``g`` / ``2g``
rescalings are already applied and the profiles integrate to the corresponding
integrated term. Vertically integrating a profile from this table therefore
reproduces the phase mean in ``energy_cache_corrected.parquet``.

Secondary periods (``decay 2``) are folded into their main phase, matching the
aggregation of ``build_corrected_cache.py``.

Usage
-----
    RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
    python -m scripts.lec_climatology_rerun.build_corrected_vertical_levels \\
        --run-root "$RUN"

    # every available term rather than the figure set
    python -m scripts.lec_climatology_rerun.build_corrected_vertical_levels \\
        --run-root "$RUN" --terms all

    # exploratory build from the cyclones finished so far (never for the paper)
    python -m scripts.lec_climatology_rerun.build_corrected_vertical_levels \\
        --run-root "$RUN" --allow-partial

Output
------
    data/corrected/vertical_phase_means_corrected.parquet

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.utils import corrected_lec as clec  # noqa: E402

#: Terms the article's vertical figures need: the two conversions the paper
#: discusses plus the full Ck decomposition, now available for every EP.
FIGURE_TERMS = ["Ca", "Ck", *clec.CK_SUBTERMS]


def profiles_for(track_id: str, terms: list[str]) -> pd.DataFrame:
    """Phase-mean vertical profiles of one cyclone, or an empty frame."""
    return clec.phase_mean_profiles(track_id, terms)


def build(track_ids: list[str], terms: list[str], output: Path, workers: int) -> Path:
    frames: list[pd.DataFrame] = []
    failures: list[tuple[str, str]] = []

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(profiles_for, tid, terms): tid for tid in track_ids}
        for done, future in enumerate(as_completed(futures), start=1):
            track_id = futures[future]
            try:
                frame = future.result()
            except Exception as error:  # noqa: BLE001 - reported, not swallowed
                failures.append((track_id, str(error)))
            else:
                if not frame.empty:
                    frames.append(frame)
            if done % 250 == 0 or done == len(track_ids):
                print(f"  processed {done}/{len(track_ids)} cyclones", flush=True)

    if failures:
        preview = "; ".join(f"{tid}: {msg}" for tid, msg in failures[:5])
        raise RuntimeError(
            f"{len(failures)} cyclones failed to yield vertical profiles ({preview}). "
            "A validated COMPLETE cyclone must always have readable vertical files."
        )

    table = pd.concat(frames, ignore_index=True)
    table["phase"] = table["phase"].astype("category")
    table["term"] = table["term"].astype("category")

    covered = table["track_id"].nunique()
    if covered != len(track_ids):
        raise RuntimeError(f"only {covered}/{len(track_ids)} cyclones produced profiles")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    table.to_parquet(temporary, index=False, compression="snappy")
    temporary.replace(output)

    print(f"\ncyclones : {covered}")
    print(f"terms    : {sorted(table['term'].unique())}")
    print(f"phases   : {sorted(table['phase'].unique())}")
    print(f"levels   : {table['level_hpa'].nunique()}")
    print(f"rows     : {len(table)}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build corrected vertical phase means.")
    parser.add_argument("--run-root", type=Path)
    parser.add_argument(
        "--terms", nargs="+", default=FIGURE_TERMS,
        help="term stems, or 'all' for every stem in corrected_lec.VERTICAL_TERMS",
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
        os.environ["PAPER_LEC_RUN_ROOT"] = str(args.run_root)

    terms = clec.VERTICAL_TERMS if args.terms == ["all"] else list(args.terms)
    unknown = [term for term in terms if term not in clec.VERTICAL_TERMS]
    if unknown:
        parser.error(f"unknown vertical terms: {unknown}")

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
        track_ids = clec.require_complete("build_corrected_vertical_levels")
        suffix = ""

    # One cyclone is enough to catch a change in the toolkit's file conventions.
    print(f"convention check on {track_ids[0]}: ok "
          f"(max relative error {max(clec.verify_conventions(track_ids[0]).values()):.2e})")

    output = args.output or clec.corrected_path(
        clec.VERTICAL_PHASE_MEANS.replace(".parquet", f"{suffix}.parquet")
    )
    print(build(track_ids, terms, output, args.workers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
