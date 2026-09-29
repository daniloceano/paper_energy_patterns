"""Shared coverage rules for the canonical CPS analysis.

Coverage is measured in hours against the complete hourly trajectory used by
the CPS pipeline.  A usable CPS point closes the interval since the preceding
CPS timestamp; that interval contributes to the covered duration only when B,
VTL and VTU are all finite.  Time before the first CPS timestamp and after the
last CPS timestamp is therefore uncovered.  The structurally undefined first
CPS point contributes zero hours when it coincides with track genesis.

This duration-based definition is deliberately not a ratio of usable CSV rows:
the original CPS grids may start/end one or two hours inside the full track and
some have a final two-hour interval.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COVERAGE_THRESHOLD = 0.75
COVERAGE_TOLERANCE = 1e-9
NO_DATA = "no_data"
INSUFFICIENT_COVERAGE = "insufficient_coverage"
COMPLETE = "complete"
ELIGIBLE_INCOMPLETE = "eligible_incomplete"

COVERAGE_BINS = [-np.inf, 0.25, 0.50, 0.75, 0.90, 1.0 - COVERAGE_TOLERANCE, np.inf]
COVERAGE_BIN_LABELS = ["<25%", "25-<50%", "50-<75%", "75-<90%", "90-<100%", "100%"]


def coverage_status(coverage: float, n_usable: int) -> str:
    """Return the mutually exclusive audit status for one trajectory."""
    if n_usable == 0 or not np.isfinite(coverage):
        return NO_DATA
    if coverage + COVERAGE_TOLERANCE < COVERAGE_THRESHOLD:
        return INSUFFICIENT_COVERAGE
    if coverage >= 1.0 - COVERAGE_TOLERANCE:
        return COMPLETE
    return ELIGIBLE_INCOMPLETE


def coverage_bin(values: pd.Series) -> pd.Series:
    """Bin coverage fractions with 75% as an explicit boundary."""
    clipped = pd.to_numeric(values, errors="coerce").clip(lower=0.0, upper=1.0)
    return pd.cut(
        clipped,
        bins=COVERAGE_BINS,
        labels=COVERAGE_BIN_LABELS,
        right=False,
        include_lowest=True,
    )


def validate_and_measure_coverage(
    cps: pd.DataFrame,
    tracks: pd.DataFrame,
    cyclone_metadata: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate CPS/track alignment and return annotated timesteps + coverage.

    Parameters
    ----------
    cps
        One row per original CPS CSV row. Required columns are ``track_id``,
        ``datetime``, ``B``, ``VTL`` and ``VTU``.
    tracks
        Complete hourly trajectories with ``track_id`` and ``date``.
    cyclone_metadata
        One row per track with the metadata that must accompany the audit table
        (EP, region and genesis coordinates in the canonical pipeline).

    Raises
    ------
    ValueError
        If any CPS timestamp is absent from its track, if time axes are not
        strictly increasing/unique, or if an interval is inconsistent with the
        original 3-hour CPS cadence (the only accepted exception is a final
        2-hour endpoint).
    """
    needed_cps = {"track_id", "datetime", "B", "VTL", "VTU"}
    needed_tracks = {"track_id", "date"}
    if missing := needed_cps.difference(cps.columns):
        raise ValueError(f"CPS data lack required columns: {sorted(missing)}")
    if missing := needed_tracks.difference(tracks.columns):
        raise ValueError(f"track data lack required columns: {sorted(missing)}")

    cps = cps.sort_values(["track_id", "datetime"]).copy()
    tracks = tracks.sort_values(["track_id", "date"]).copy()
    cps["cps_usable"] = cps[["B", "VTL", "VTU"]].notna().all(axis=1)
    cps["cps_interval_hours"] = (
        cps.groupby("track_id", sort=False)["datetime"]
        .diff()
        .dt.total_seconds()
        .div(3600.0)
        .fillna(0.0)
    )

    track_axes = {
        int(track_id): pd.DatetimeIndex(group["date"])
        for track_id, group in tracks.groupby("track_id", sort=False)
    }
    problems: list[str] = []
    rows: list[dict] = []

    for track_id, group in cps.groupby("track_id", sort=False):
        track_id = int(track_id)
        axis = track_axes.get(track_id)
        if axis is None:
            problems.append(f"{track_id}: CPS file has no reference trajectory")
            continue

        cps_axis = pd.DatetimeIndex(group["datetime"])
        absent = cps_axis.difference(axis)
        if len(absent):
            problems.append(
                f"{track_id}: {len(absent)} CPS timestamp(s) absent from track"
            )
        if cps_axis.has_duplicates or not cps_axis.is_monotonic_increasing:
            problems.append(f"{track_id}: CPS timestamps are duplicated or unordered")

        gaps = group["cps_interval_hours"].iloc[1:]
        bad_gap = ~gaps.eq(3.0)
        if len(gaps) and gaps.iloc[-1] == 2.0:
            bad_gap.iloc[-1] = False
        if bad_gap.any():
            problems.append(
                f"{track_id}: unexpected CPS interval(s) "
                f"{sorted(gaps[bad_gap].unique().tolist())}"
            )

        track_start, track_end = axis[0], axis[-1]
        duration_h = float((track_end - track_start).total_seconds() / 3600.0)
        lead_h = float((cps_axis[0] - track_start).total_seconds() / 3600.0)
        tail_h = float((track_end - cps_axis[-1]).total_seconds() / 3600.0)
        if duration_h <= 0:
            problems.append(f"{track_id}: non-positive trajectory duration")
        if not (0.0 <= lead_h <= 2.0 and 0.0 <= tail_h <= 2.0):
            problems.append(
                f"{track_id}: CPS edge offsets outside 0-2 h "
                f"(lead={lead_h:g}, tail={tail_h:g})"
            )

        usable_h = float(
            group.loc[group["cps_usable"], "cps_interval_hours"].sum()
        )
        n_usable = int(group["cps_usable"].sum())
        coverage = usable_h / duration_h if duration_h > 0 else np.nan
        if np.isfinite(coverage) and not (-COVERAGE_TOLERANCE <= coverage <= 1.0 + COVERAGE_TOLERANCE):
            problems.append(f"{track_id}: coverage outside [0, 1]: {coverage:g}")

        rows.append(
            {
                "track_id": track_id,
                "has_cps_file": True,
                "track_start": track_start,
                "track_end": track_end,
                "track_duration_hours": duration_h,
                "cps_start": cps_axis[0],
                "cps_end": cps_axis[-1],
                "cps_lead_uncovered_hours": lead_h,
                "cps_tail_uncovered_hours": tail_h,
                "n_cps_timesteps": len(group),
                "n_usable_timesteps": n_usable,
                "usable_coverage_hours": usable_h,
                "coverage_fraction": min(max(coverage, 0.0), 1.0),
            }
        )

    if problems:
        preview = "\n  ".join(problems[:20])
        raise ValueError(
            f"CPS/track temporal alignment failed for {len(problems)} case(s):\n  {preview}"
        )

    coverage = pd.DataFrame(rows)

    # Add catalogue trajectories without a CPS file as explicit no-data cases.
    track_summary = (
        tracks.groupby("track_id", as_index=False)
        .agg(track_start=("date", "min"), track_end=("date", "max"))
    )
    track_summary["track_duration_hours"] = (
        track_summary["track_end"] - track_summary["track_start"]
    ).dt.total_seconds().div(3600.0)
    missing_ids = track_summary.loc[
        ~track_summary["track_id"].isin(coverage["track_id"])
    ].copy()
    if len(missing_ids):
        missing_ids = missing_ids.assign(
            has_cps_file=False,
            cps_start=pd.NaT,
            cps_end=pd.NaT,
            cps_lead_uncovered_hours=np.nan,
            cps_tail_uncovered_hours=np.nan,
            n_cps_timesteps=0,
            n_usable_timesteps=0,
            usable_coverage_hours=0.0,
            coverage_fraction=0.0,
        )
        coverage = pd.concat([coverage, missing_ids[coverage.columns]], ignore_index=True)

    coverage["coverage_status"] = [
        coverage_status(value, int(n_usable))
        for value, n_usable in zip(
            coverage["coverage_fraction"], coverage["n_usable_timesteps"]
        )
    ]
    coverage["analysis_included"] = coverage["coverage_fraction"].ge(
        COVERAGE_THRESHOLD - COVERAGE_TOLERANCE
    ) & coverage["n_usable_timesteps"].gt(0)
    coverage["coverage_bin"] = coverage_bin(coverage["coverage_fraction"])

    coverage = coverage.merge(cyclone_metadata, on="track_id", how="left", validate="one_to_one")
    coverage = coverage.sort_values("track_id").reset_index(drop=True)

    annotate = coverage[
        [
            "track_id",
            "track_duration_hours",
            "usable_coverage_hours",
            "coverage_fraction",
            "coverage_status",
            "coverage_bin",
            "analysis_included",
        ]
    ]
    cps = cps.merge(annotate, on="track_id", how="left", validate="many_to_one")
    return cps, coverage
