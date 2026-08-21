#!/usr/bin/env python3
"""Freeze the article population and create 3-hourly toolkit track files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

from .common import (
    PROJECT_ROOT,
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


def load_tracks(path: Path) -> pd.DataFrame:
    columns = ["track_id", "date", "lat vor", "lon vor"]
    frame = pd.read_csv(path, usecols=columns, dtype={"track_id": str})
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    return frame.sort_values(["track_id", "date"])


def choose_pilots(manifest: pd.DataFrame, ep1_file: Path) -> list[str]:
    ordered = manifest.set_index("track_id")
    durations = ordered["lifecycle_hours"]
    selected = [
        str(durations.idxmin()),
        str((durations - durations.median()).abs().idxmin()),
        str(durations.idxmax()),
    ]
    if ep1_file.exists():
        ep1 = pd.read_csv(ep1_file, dtype={"track_id": str})
        candidates = ordered.loc[ordered.index.intersection(ep1["track_id"])]
        if not candidates.empty:
            selected.append(
                str((candidates["lifecycle_hours"] - durations.median()).abs().idxmin())
            )
    return list(dict.fromkeys(selected))


def prepare(config: RunConfig, track_source: Path | None = None) -> dict:
    config.create_directories()
    config.save()
    cache = PROJECT_ROOT / "data" / "energy_cache.parquet"
    raw_cache, population = population_from_cache(cache)
    tracks_path = select_track_source(track_source)
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
        start, end = cyclone["date"].iloc[[0, -1]]
        rows.append({
            "track_id": track_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "n_timesteps": len(cyclone),
            "lifecycle_hours": (end - start).total_seconds() / 3600,
            "track_sha256": sha256_file(track_path),
        })

    manifest = pd.DataFrame(rows)
    pilots = choose_pilots(
        manifest, PROJECT_ROOT / "results" / "ep_structure" / "ep1_cases.csv"
    )
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
    db.set_meta("pilot_ids", ",".join(pilots))
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
    parser.add_argument("--keys-file", type=Path, default=Path("/p1-swell/danilocs/cds-keys"))
    parser.add_argument("--download-workers", type=int, default=3)
    parser.add_argument("--max-download-workers", type=int, default=8)
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
    result = prepare(config, args.track_source)
    print(json.dumps({"population": result["population"], "pilots": result["pilots"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
