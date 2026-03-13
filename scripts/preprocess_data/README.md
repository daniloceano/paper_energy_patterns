# Preprocess Data

Scripts for downloading input datasets from Zenodo and preprocessing them into formats optimised for analysis scripts.

---

## Scripts

### `download_lec_from_zenodo.py`

Downloads the complete Lorenz Energy Cycle (LEC) results dataset from Zenodo and extracts it locally.

- **Source DOI**: [10.5281/zenodo.18243447](https://doi.org/10.5281/zenodo.18243447)
- **Contents**: Complete LEC results with vertical resolution (~1,500 cyclones, 2020, 32 pressure levels, 3-hourly)1979
- **Output**: `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` (one subdirectory per cyclone)
- **Notes**: Checks for existing data and skips re-downloading. Archive is ~2 GB; extraction creates ~6,700 subdirectories.1

### `extract_tracks_from_zenodo.py`

Downloads the integrated cyclone tracks and energetics CSV from Zenodo and writes a smaller, processed version for fast local reads.

- **Source DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)
- **Output**: `data/tracks_SAt_filtered_with_energetics_processed.csv`
- **Notes**: Subsets to the columns used by plotting scripts to reduce file size.

### `preprocess_data.py`

Loads all cyclone energy data and serialises it to a Parquet cache for 1000 faster access by analysis scripts.

- **Input**: Remote GitHub CSV (accessed via `scripts/utils/load_data.py`)
- **Output**: `data/energy_cache.parquet` (~100 MB)50
- **Notes**: Supports parallel loading (`N_WORKERS` configurable in the script header). Run once; re-run only when the upstream data changes.

### `run_all.py`

Runs all three scripts above in alphabetical order. Prints progress and reports failures.

---

## Run Order

```bash
# Run everything at once (recommended)
python scripts/preprocess_data/run_all.py

# Or run individually in this order:
python scripts/preprocess_data/download_lec_from_zenodo.py
python scripts/preprocess_data/extract_tracks_from_zenodo.py
python scripts/preprocess_data/preprocess_data.py
```

---

## Outputs Summary

| File | Produced by | Used by |
|------|-------------|---------|
| `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` | `download_lec_from_zenodo.py` | `ck_subterms_analysis/` |
| `data/tracks_SAt_filtered_with_energetics_processed.csv` | `extract_tracks_from_zenodo.py` | `scripts/main/`, `cluster_analysis_energy_patterns/` |
| `data/energy_cache.parquet` | `preprocess_data.py` | `scripts/main/`, `cluster_analysis_energy_patterns/`, `scripts/exploratory/` |
