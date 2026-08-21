# Preprocess Data

> For the corrected 2026 Lorenz Energy Cycle climatology, use
> `scripts/lec_climatology_rerun/`. It preserves the legacy cache, pins
> toolkit/data provenance, and refuses to build a corrected cache until all
> 3,820 selected cyclones validate as complete.

Scripts for downloading and preprocessing cyclone data from remote sources (GitHub, Zenodo) into optimized local caches.

---

## Overview: Data Pipeline

```
REMOTE SOURCES                PREPROCESSING              LOCAL CACHE
┌──────────────┐             ┌──────────────┐          ┌──────────────┐
│ GitHub       │────────────>│ preprocess   │─────────>│ energy_cache │
│ Energy CSVs  │  Load 1500  │ _data.py     │  Filter  │ .parquet     │
│ (per-cycle)  │  cyclones   │              │  & Save  │ (6 MB)       │
└──────────────┘             └──────────────┘          └──────────────┘

┌──────────────┐             ┌──────────────┐          ┌──────────────┐
│ Zenodo       │────────────>│ extract_     │─────────>│ tracks_*_    │
│ 18133432     │  Download   │ tracks.py    │  Subset  │ processed.csv│
│ Full tracks  │  ~180 MB    │              │  columns │ (66 MB)      │
└──────────────┘             └──────────────┘          └──────────────┘

┌──────────────┐             ┌──────────────┐          ┌──────────────┐
│ Zenodo       │────────────>│ download_    │─────────>│ temp_lec_    │
│ 18243447     │  Download   │ lec.py       │  Extract │ zenodo/      │
│ LEC vertical │  ~634 MB    │              │  tar.gz  │ (1.2 GB)     │
└──────────────┘             └──────────────┘          └──────────────┘
```

**Key Points:**
- **Main analysis scripts** use GitHub tracks via `load_tracks()` - no preprocessing needed
- **Clustering pipeline** requires `energy_cache.parquet` - run `preprocess_data.py` once
- **Vertical analysis** (S3 figure) requires LEC data - run `download_lec_from_zenodo.py` once
- **Exploratory scripts** may use Zenodo tracks cache - run `extract_tracks_from_zenodo.py` if needed

---

## Scripts

### 1. `preprocess_data.py` ⭐ (Most Important)

**Purpose**: Creates fast-loading energy cache for clustering pipeline

**Input**: GitHub energy data (via `scripts/utils/load_data.load_all_energy_data()`)  
**Output**: `data/energy_cache.parquet` (~6 MB compressed, <1 sec load time)  
**Process**:
1. Downloads up to 6,789 individual cyclone energy CSVs from GitHub (parallel, 50 workers)
2. Filters for complete lifecycle cyclones (4-phase sequence: incipient→intensification→mature→decay)
3. Standardizes column names and data types
4. Saves as compressed Parquet (Snappy compression, ~10:1 ratio)

**Run Time**: ~4-5 minutes (parallel loading)  
**Used By**:
- `scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py`
- All clustering pipeline scripts
- Exploratory KDE/boxplot scripts

**Run Once**: Only re-run if upstream GitHub energy data changes

```bash
python scripts/preprocess_data/preprocess_data.py
```

**Configuration** (in script header):
```python
N_WORKERS = 50  # Parallel download workers (adjust based on network/CPU)
```

---

### 2. `download_lec_from_zenodo.py` (For Vertical Analysis)

**Purpose**: Downloads complete LEC results with 32 vertical levels

**Source**: Zenodo DOI [10.5281/zenodo.18243447](https://doi.org/10.5281/zenodo.18243447)  
**Output**: `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` (~1.2 GB extracted)  
**Contents**:
- Up to 6,789 cyclone directories (`{track_id}_ERA5_track/`)
- Each with 20+ CSV files (energy terms by pressure level)
- 32 pressure levels (1000-100 hPa)
- 3-hourly temporal resolution

**Run Time**: ~5-10 minutes (download 634 MB + extract)  
**Used By**:
- `scripts/main/S2_figure_vertical_levels.py` (supplementary figure)
- `scripts/ck_subterms_analysis/` (Ck decomposition)
- `scripts/ep_structure_analysis/step1_select_ep_tracks.py` (periods extraction)

**Notes**:
- Checks for existing data (skips if already downloaded)
- Large download (~634 MB compressed, 1.2 GB extracted)
- Only needed for vertical structure analysis

```bash
python scripts/preprocess_data/download_lec_from_zenodo.py
```

---

### 3. `extract_tracks_from_zenodo.py` (For Exploratory Analysis)

**Purpose**: Downloads and caches full track+energy time series from Zenodo

**Source**: Zenodo DOI [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)  
**Output**: `data/tracks_SAt_filtered_with_energetics_processed.csv` (~66 MB)  
**Contents**:
- 1-hourly track positions (lon, lat, vorticity)
- 3-hourly energy terms (Az, Ae, Kz, Ke, Ca, Ck, etc.)
- All lifecycle phases (incipient → decay)

**Run Time**: ~2-3 minutes (download ~180 MB + write subset)  
**Used By**:
- `scripts/exploratory/figure_three_intense_cyclones_individual*.py`
- Individual cyclone case studies
- Time-series plotting scripts

**Notes**:
- **Most main scripts use GitHub tracks instead** (via `load_tracks()`)
- This cache is for exploratory/detailed time-series analysis only
- Subsets columns to reduce file size vs. full Zenodo file

```bash
python scripts/preprocess_data/extract_tracks_from_zenodo.py
```

### 4. `run_all.py` (Convenience Script)

Runs all three preprocessing scripts in sequence. Prints progress and reports failures.

```bash
python scripts/preprocess_data/run_all.py
```

**Total Time**: ~10-15 minutes (downloads + processing)  
**Total Storage**: ~1.3 GB (temp_lec_zenodo: 1.2 GB, tracks CSV: 66 MB, cache: 6 MB)

---

## Quick Start Guide

### Minimum Setup (For Main Figures)

**Most scripts use GitHub data directly** - no preprocessing needed!

```bash
# Just run your analysis scripts - they'll auto-load from GitHub
python scripts/main/01_figure_tracks_genesis_frequency.py  # Works immediately
python scripts/main/06_figure_genesis_density_kde.py       # Works immediately
```

### For Clustering Analysis

**Required**: Energy cache

```bash
python scripts/preprocess_data/preprocess_data.py  # Run once (~5 min)
python scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py
```

### For Vertical Structure Analysis (S2 Figure)

**Required**: LEC vertical data

```bash
python scripts/preprocess_data/download_lec_from_zenodo.py  # Run once (~10 min)
python scripts/main/S2_figure_vertical_levels.py
```

### For Everything

```bash
python scripts/preprocess_data/run_all.py  # ~15 min, ~1.3 GB
```

---

## Data Sources Summary

| Source | Type | Access Method | Size | Usage |
|--------|------|---------------|------|-------|
| **GitHub tracks** | Remote CSV | `load_tracks()` | Stream | Main figures (01, 05, 06, S2) |
| **GitHub energy** | Remote CSVs | `load_all_energy_data()` | Stream | Preprocessing only |
| **Zenodo 18133432** | Archive | HTTP download | 180 MB | Exploratory time-series |
| **Zenodo 18243447** | Archive | HTTP download | 634 MB | Vertical analysis (S3) |
| **energy_cache.parquet** | Local cache | `load_cache()` | 6 MB | Clustering pipeline ⭐ |
| **tracks_*_processed.csv** | Local cache | `pd.read_csv()` | 66 MB | Exploratory scripts |
| **temp_lec_zenodo/** | Local extract | Direct file reads | 1.2 GB | Vertical/subterm analysis |

---

## Outputs Summary

| Output File/Directory | Produced By | Size | Used By | Required For |
|----------------------|-------------|------|---------|--------------|
| `data/energy_cache.parquet` | `preprocess_data.py` | 6 MB | Clustering pipeline | **Clustering analysis** ⭐ |
| `data/tracks_SAt_filtered_with_energetics_processed.csv` | `extract_tracks_from_zenodo.py` | 66 MB | Exploratory scripts | Individual case studies |
| `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` | `download_lec_from_zenodo.py` | 1.2 GB | S3 figure, Ck analysis | **Vertical structure** |

**Legend**:
- ⭐ = Essential for most analyses
- Others = Optional depending on analysis type

---

## Troubleshooting

### "energy_cache.parquet not found"
```bash
python scripts/preprocess_data/preprocess_data.py
```

### "temp_lec_zenodo directory not found"
```bash
python scripts/preprocess_data/download_lec_from_zenodo.py
```

### Slow GitHub downloads
Adjust parallel workers in `preprocess_data.py`:
```python
N_WORKERS = 30  # Reduce if network throttling occurs
```

### Disk space issues
- `temp_lec_zenodo/` is largest (1.2 GB) - only download if needed for S3/Ck analysis
- Can delete after analysis if space constrained
- `energy_cache.parquet` is essential (only 6 MB) - keep always
