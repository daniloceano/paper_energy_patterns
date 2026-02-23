#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract tracks and energetics from the remote Zenodo CSV and write a smaller,
processed CSV for fast local reads used by plotting scripts.

Saves to: <repo_root>/data/tracks_SAt_filtered_with_energetics_processed.csv

Run: python scripts/analysis/extract_tracks_from_zenodo.py
"""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_URL = "https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv"
OUT_FILE = BASE_DIR / 'data' / 'tracks_SAt_filtered_with_energetics_processed.csv'

# Columns that plotting scripts use (subset to speed up reads)
COLUMNS = [
    'track_id', 'date', 'lon vor', 'lat vor',
    'vor42', 'Kz', 'Ke',
    'Ck', 'Ca', 'BAe', 'BKe', 'Ge'
]


def main():
    print("Downloading and processing remote CSV (this may take a while)...")
    print(f"Source: {DATA_URL}")
    df = pd.read_csv(DATA_URL)

    # Ensure date is parsed
    df['date'] = pd.to_datetime(df['date'])

    # Keep only needed columns (if present)
    existing_cols = [c for c in COLUMNS if c in df.columns]
    df_small = df[existing_cols].copy()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_small.to_csv(OUT_FILE, index=False)

    print(f"✓ Saved processed file: {OUT_FILE}")
    print(f"Records: {len(df_small)} | Unique tracks: {df_small['track_id'].nunique()}")


if __name__ == '__main__':
    raise SystemExit(main())
