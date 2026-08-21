#!/usr/bin/env python3
"""Build the clustering input only after every corrected cyclone is COMPLETE."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from .common import RunConfig

PHASES = ["incipient", "intensification", "mature", "decay"]


def parse_periods(path: Path) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    frame = pd.read_csv(path)
    if not {"start", "end"}.issubset(frame.columns):
        frame = pd.read_csv(path, index_col=0).reset_index()
    phase_col = next((column for column in frame.columns if column not in {"start", "end"}), frame.columns[0])
    result = {}
    for _, values in frame.iterrows():
        raw = str(values[phase_col]).strip().lower()
        phase = next((item for item in PHASES if raw.startswith(item)), None)
        if phase and phase not in result:
            result[phase] = (pd.to_datetime(values["start"]), pd.to_datetime(values["end"]))
    if set(result) != set(PHASES):
        raise ValueError(f"incomplete lifecycle periods in {path}: {sorted(result)}")
    return result


def load_results(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    time_column = next(
        (column for column in frame.columns if column.lower() in {"time", "date", "datetime", "unnamed: 0"}),
        frame.columns[0],
    )
    frame["_time"] = pd.to_datetime(frame[time_column], errors="coerce")
    if frame["_time"].isna().any():
        raise ValueError(f"unparseable result timestamps in {path}")
    return frame.set_index("_time")


def build(config: RunConfig, output: Path, force: bool = False) -> Path:
    conn = sqlite3.connect(config.db)
    incomplete = conn.execute("SELECT COUNT(*) FROM cyclones WHERE state!='COMPLETE'").fetchone()[0]
    ids = [row[0] for row in conn.execute("SELECT track_id FROM cyclones ORDER BY track_id")]
    conn.close()
    if incomplete:
        raise RuntimeError(f"refusing partial cache: {incomplete} cyclones are not COMPLETE")
    if output.exists() and not force:
        raise FileExistsError(f"output exists: {output}; use --force explicitly")
    records = []
    for track_id in ids:
        directory = config.results_dir / f"{track_id}_ERA5_track"
        results = load_results(directory / f"{track_id}_ERA5_track_results.csv")
        periods = parse_periods(directory / "periods.csv")
        numeric = results.select_dtypes(include="number")
        for phase in PHASES:
            start, end = periods[phase]
            selected = numeric.loc[(numeric.index >= start) & (numeric.index <= end)]
            if selected.empty:
                raise ValueError(f"no {phase} rows for {track_id}")
            record = selected.mean().to_dict()
            record.update({"track_id": track_id, "period": phase, "phase": phase})
            records.append(record)
    frame = pd.DataFrame(records)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    frame.to_parquet(temporary, index=False, compression="snappy")
    check = pd.read_parquet(temporary)
    if check["track_id"].nunique() != len(ids) or len(check) != 4 * len(ids):
        raise RuntimeError("corrected cache failed population/row-count validation")
    temporary.replace(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = RunConfig.load(args.run_root)
    output = args.output or config.root / "processed" / "energy_cache_corrected.parquet"
    print(build(config, output, args.force))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
