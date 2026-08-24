#!/usr/bin/env python3
"""Freeze the article population and create 3-hourly toolkit track files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import pandas as pd

# Allow running this file directly, not only as `python -m`.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_climatology_rerun.common import (
    PROJECT_ROOT,
    PHASE_SOURCE_DOI,
    TRACK_SOURCE_DOI,
    TRACK_SOURCE_URL,
    RunConfig,
    StateDB,
    git_output,
    sha256_file,
    utc_now,
)

PHASES = ["incipient", "intensification", "mature", "decay"]
ENERGY_VARS = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]


def population_from_cache(cache: Path) -> tuple[pd.DataFrame, set[str]]:
    """Reproduce the exact scientific inclusion rule used before PCA."""
    frame = pd.read_parquet(cache)
    frame["track_id"] = frame["track_id"].astype(str)
    eligible: list[str] = []
    for track_id, group in frame.groupby("track_id", sort=False):
        sequence = group["phase"].drop_duplicates().tolist()
        if not all(phase in sequence for phase in PHASES):
            continue
        positions = [sequence.index(phase) for phase in PHASES]
        if positions != sorted(positions):
            continue
        selected = group[group["phase"].isin(PHASES)]
        clean = selected.dropna(subset=ENERGY_VARS)
        if set(clean["phase"]) == set(PHASES):
            eligible.append(track_id)
    return frame, set(eligible)


def select_track_source(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    preferred = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"
    if preferred.exists():
        return preferred
    raise FileNotFoundError(
        f"track source not found: {preferred}. Recreate it from {TRACK_SOURCE_URL} "
        "with scripts/preprocess_data/extract_tracks_from_zenodo.py"
    )


def select_periods_source(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    preferred = PROJECT_ROOT / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
    if preferred.exists():
        return preferred
    raise FileNotFoundError(
        f"legacy lifecycle-window source not found: {preferred}. Recreate it from "
        f"Zenodo DOI {PHASE_SOURCE_DOI} with scripts/preprocess_data/download_lec_from_zenodo.py"
    )


def period_file(source: Path, track_id: str) -> Path:
    base = source / f"{track_id}_ERA5_track" / "periods.csv"
    candidates = [base / "periods.csv", base]
    return next((path for path in candidates if path.is_file()), candidates[0])


def load_tracks(path: Path) -> pd.DataFrame:
    columns = ["track_id", "date", "lat vor", "lon vor"]
    frame = pd.read_csv(path, usecols=columns, dtype={"track_id": str})
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    return frame.sort_values(["track_id", "date"])


def choose_pilots(manifest: pd.DataFrame, ep1_file: Path) -> list[str]:
    ordered = manifest.set_index("track_id")
    durations = ordered["lifecycle_hours"]
    long_candidates = ordered.loc[durations.ge(durations.quantile(0.95))]
    if "download_envelope_degrees2" in long_candidates:
        long_id = str(long_candidates["download_envelope_degrees2"].idxmin())
    else:
        long_id = str(long_candidates.index[0])
    selected = [
        str(durations.idxmin()),
        str((durations - durations.median()).abs().idxmin()),
        # Exercise a genuinely long lifecycle while isolating duration from
        # spatial-footprint cost: within the longest 5%, use the smallest CDS
        # envelope rather than a globe-spanning outlier.
        long_id,
    ]
    if ep1_file.exists():
        ep1 = pd.read_csv(ep1_file, dtype={"track_id": str})
        candidates = ordered.loc[ordered.index.intersection(ep1["track_id"])]
        if not candidates.empty:
            selected.append(
                str((candidates["lifecycle_hours"] - durations.median()).abs().idxmin())
            )
    return list(dict.fromkeys(selected))


def prepare(
    config: RunConfig,
    track_source: Path | None = None,
    ep1_cases: Path | None = None,
    periods_source: Path | None = None,
) -> dict:
    config.create_directories()
    config.save()
    cache = PROJECT_ROOT / "data" / "energy_cache.parquet"
    raw_cache, population = population_from_cache(cache)
    tracks_path = select_track_source(track_source)
    periods_root = select_periods_source(periods_source)
    tracks = load_tracks(tracks_path)
    available = set(tracks["track_id"])
    missing = sorted(population - available)
    if missing:
        raise RuntimeError(
            f"track source is incomplete: {len(missing)} of {len(population)} selected IDs missing; "
            f"examples: {missing[:10]}"
        )

    rows: list[dict] = []
    for track_id in sorted(population):
        cyclone = tracks[tracks["track_id"] == track_id].copy()
        # The archived energetics are at synoptic 3-hourly timestamps. Selecting
        # exact timestamps avoids shifting the storm centre backwards with floor().
        cyclone = cyclone[cyclone["date"].dt.hour.mod(3).eq(0)]
        cyclone = cyclone.drop_duplicates("date").sort_values("date")
        if len(cyclone) < 2:
            raise RuntimeError(f"insufficient 3-hourly track points for {track_id}")
        track_path = config.tracks_dir / f"track_{track_id}.txt"
        temp = track_path.with_suffix(".txt.part")
        with temp.open("w", newline="") as stream:
            writer = csv.writer(stream, delimiter=";", lineterminator="\n")
            writer.writerow(["time", "Lat", "Lon"])
            for _, record in cyclone.iterrows():
                writer.writerow([
                    record["date"].strftime("%Y-%m-%d-%H%M"),
                    f"{record['lat vor']:.6f}",
                    f"{record['lon vor']:.6f}",
                ])
        temp.replace(track_path)
        source_periods = period_file(periods_root, track_id)
        if not source_periods.is_file():
            raise FileNotFoundError(f"missing lifecycle windows for {track_id}: {source_periods}")
        period_frame = pd.read_csv(source_periods, index_col=0)
        if not {"start", "end"}.issubset(period_frame.columns):
            raise ValueError(f"invalid lifecycle windows for {track_id}")
        canonical = {
            phase for label in period_frame.index.astype(str).str.lower()
            for phase in PHASES if label.startswith(phase)
        }
        if canonical != set(PHASES):
            raise ValueError(f"incomplete lifecycle windows for {track_id}: {sorted(canonical)}")
        expected = pd.DatetimeIndex(cyclone["date"])
        for _, period in period_frame.iterrows():
            start, end = pd.to_datetime(period["start"]), pd.to_datetime(period["end"])
            if start > end or not ((expected >= start) & (expected <= end)).any():
                raise ValueError(f"non-overlapping lifecycle window for {track_id}: {start}--{end}")
        frozen_periods = config.phase_windows_dir / f"{track_id}.csv"
        temp_periods = frozen_periods.with_suffix(".csv.part")
        period_frame.to_csv(temp_periods)
        temp_periods.replace(frozen_periods)
        start, end = cyclone["date"].iloc[[0, -1]]
        north = min(90, math.ceil(float(cyclone["lat vor"].max()) + 15))
        south = max(-90, math.floor(float(cyclone["lat vor"].min()) - 15))
        west = max(-180, math.floor(float(cyclone["lon vor"].min()) - 15))
        east = min(180, math.ceil(float(cyclone["lon vor"].max()) + 15))
        rows.append({
            "track_id": track_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "n_timesteps": len(cyclone),
            "lifecycle_hours": (end - start).total_seconds() / 3600,
            "track_sha256": sha256_file(track_path),
            "phase_windows_sha256": sha256_file(frozen_periods),
            "download_envelope_degrees2": (north - south) * (east - west),
        })

    manifest = pd.DataFrame(rows)
    ep1_source = ep1_cases or PROJECT_ROOT / "results" / "ep_structure" / "ep1_cases.csv"
    pilots = choose_pilots(manifest, ep1_source)
    manifest["is_pilot"] = manifest["track_id"].isin(pilots)
    temp_manifest = config.manifest.with_suffix(".csv.part")
    manifest.to_csv(temp_manifest, index=False)
    temp_manifest.replace(config.manifest)

    db = StateDB(config.db)
    db.add_cyclones(rows, set(pilots))
    db.set_meta("initialized_at", utc_now())
    db.set_meta("paper_commit", git_output(PROJECT_ROOT, "rev-parse", "HEAD"))
    db.set_meta("toolkit_commit", config.toolkit_commit)
    db.set_meta("correction_commit", config.correction_commit)
    db.set_meta("population_count", len(population))
    db.set_meta("population_source", str(cache))
    db.set_meta("population_source_sha256", sha256_file(cache))
    db.set_meta("population_raw_cyclones", raw_cache["track_id"].nunique())
    db.set_meta("population_criteria", "four phases in order + finite seven clustering terms")
    db.set_meta("track_source", str(tracks_path))
    db.set_meta("track_source_sha256", sha256_file(tracks_path))
    db.set_meta("track_source_doi", TRACK_SOURCE_DOI)
    db.set_meta("phase_windows_source", str(periods_root))
    db.set_meta("phase_windows_source_doi", PHASE_SOURCE_DOI)
    db.set_meta("phase_windows_manifest_sha256", sha256_file(config.manifest))
    db.set_meta("pilot_ids", ",".join(pilots))
    db.set_meta("ep1_pilot_source", str(ep1_source) if ep1_source.exists() else "unavailable")
    # Preparation is intentionally restartable.  Preserve elapsed active time
    # when it is rerun to refresh manifests/provenance on an existing run.
    if db.get_meta("cumulative_active_runtime") is None:
        db.set_meta("cumulative_active_runtime", 0)
    db.event("prepare", "POPULATION_FROZEN", f"{len(population)} cyclones; pilots={pilots}")
    db.close()

    provenance = {
        "created_at": utc_now(),
        "paper_commit": git_output(PROJECT_ROOT, "rev-parse", "HEAD"),
        "toolkit_commit": config.toolkit_commit,
        "correction_commit": config.correction_commit,
        "population": {
            "source": str(cache),
            "sha256": sha256_file(cache),
            "raw_cyclones": int(raw_cache["track_id"].nunique()),
            "selected_cyclones": len(population),
            "criteria": "incipient -> intensification -> mature -> decay; all seven PCA terms finite",
        },
        "tracks": {
            "source": str(tracks_path),
            "doi": TRACK_SOURCE_DOI,
            "sha256": sha256_file(tracks_path),
            "time_resolution_hours": config.time_resolution_hours,
            "selection": "exact UTC hours divisible by 3 (no coordinate time shifting)",
        },
        "phase_windows": {
            "source": str(periods_root),
            "doi": PHASE_SOURCE_DOI,
            "policy": "freeze legacy period windows to preserve the article population and phase aggregation",
            "manifest_sha256": sha256_file(config.manifest),
        },
        "era5": {
            "moving_domain_degrees": [15, 15],
            "download_buffer_degrees": 15,
            "requested_pressure_hpa": [1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000],
            "analysis_pressure_hpa": [10, 20, 30, 50, 70, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000],
            "variables": ["u", "v", "t", "w", "z"],
        },
        "workers": {
            "download_initial": config.initial_download_workers,
            "download_max": config.max_download_workers,
            "compute": config.max_compute_workers,
        },
        "pilots": pilots,
        "pilot_selection": "minimum, median, smallest CDS envelope among the longest 5%, and median-duration EP1",
    }
    provenance_path = config.root / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--paper-repo", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--toolkit-source", type=Path, default=Path("/p1-swell/danilocs/LorenzCycleToolkit"))
    parser.add_argument("--toolkit-worktree", type=Path)
    parser.add_argument("--track-source", type=Path)
    parser.add_argument("--ep1-cases", type=Path)
    parser.add_argument("--periods-source", type=Path)
    parser.add_argument("--keys-file", type=Path, default=Path("/p1-swell/danilocs/cds-keys"))
    parser.add_argument("--download-workers", type=int, default=8)
    parser.add_argument("--max-download-workers", type=int, default=16)
    parser.add_argument("--compute-workers", type=int, default=8)
    args = parser.parse_args()
    worktree = args.toolkit_worktree or args.run_root / "LorenzCycleToolkit-pinned"
    config = RunConfig(
        run_root=str(args.run_root.resolve()),
        paper_repo=str(args.paper_repo.resolve()),
        toolkit_source=str(args.toolkit_source.resolve()),
        toolkit_worktree=str(worktree.resolve()),
        keys_file=str(args.keys_file.resolve()),
        initial_download_workers=args.download_workers,
        max_download_workers=args.max_download_workers,
        max_compute_workers=args.compute_workers,
    )
    result = prepare(config, args.track_source, args.ep1_cases, args.periods_source)
    print(json.dumps({"population": result["population"], "pilots": result["pilots"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
