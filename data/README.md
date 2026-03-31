# Data Directory

This directory contains cached/processed data files. Input data is accessed remotely from **GitHub** and **Zenodo**.

---

## 📡 Remote Data Sources (Primary)

### 1. GitHub - Cyclone Tracks (Used by Main Scripts)

**URL**: `https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/refs/heads/master/tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv`

- **Access Function**: `load_tracks()` from `scripts/utils/load_data.py`
- **Records**: ~30,000 track points
- **Unique Cyclones**: ~1,500 (1979-2020)
- **Load Time**: ~10 seconds
- **Used By**: All main figure scripts (01, 05, 06, S2)

**Columns**:
- `track_id`: Cyclone identifier (YYYYNNNN format)
- `date`: UTC timestamp
- `lon vor`, `lat vor`: Cyclone center coordinates
- `vor42`: 850 hPa vorticity (×10⁵ s⁻¹)
- `region`: Genesis region (ARG, LA-PLATA, SE-BR)
- `period`: Life cycle phase (incipient, intensification, mature, decay)

### 2. GitHub - Energy Data by Cyclone

**URL Base**: `https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/master/csv_database_energy_by_periods`

- **Access Function**: `load_energy_by_cyclone(track_id)` or `load_all_energy_data(track_ids)`
- **Structure**: Individual CSV files per cyclone (`{track_id}_averages.csv`)
- **Load Time**: ~4-5 minutes (batch, 50 parallel workers)
- **Used By**: Preprocessing pipeline → generates `energy_cache.parquet`

**Energy Variables** (18+ terms, W m⁻²):
- **Reservoirs**: Az, Ae, Kz, Ke
- **Conversions**: Ca, Ck, Ce, Cz
- **Boundaries**: BAz, BAe, BKz, BKe
- **Generation**: Ge, Gz
- **Residuals**: RKe, RKz
- **Tendencies**: dAedt, dAzdt, dKedt, dKzdt

### 3. Zenodo - Complete Tracks with Energetics

**DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)  
**URL**: `https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv`

- **Size**: ~63 MB (~180 MB uncompressed)
- **Download Script**: `scripts/preprocess_data/extract_tracks_from_zenodo.py`
- **Local Cache**: `tracks_SAt_filtered_with_energetics_processed.csv` (66 MB)
- **Used By**: Exploratory scripts for individual cyclone deep-dives
- **Format**: Long-form CSV (1-hourly tracks, 3-hourly energy)

**Citation**: de Souza, D., & Gramcianinov, C. (2026). Southwestern Atlantic Cyclone Tracks and Semi-Lagrangian Lorenz Energy Cycle (LEC) diagnostics (1979–2020) [Data set]. Zenodo.

### 4. Zenodo - LEC Results with Vertical Resolution

**DOI**: [10.5281/zenodo.18243447](https://zenodo.org/records/18243447)  
**URL**: `https://zenodo.org/records/18243447/files/LEC_Results_energetic-patterns_csv_only.tar.gz`

- **Size**: ~634 MB (compressed), ~1.2 GB (extracted)
- **Download Script**: `scripts/preprocess_data/download_lec_from_zenodo.py`
- **Extract Location**: `temp_lec_zenodo/LEC_Results_energetic-patterns/`
- **Used By**: Vertical structure analysis (S3 figure), Ck subterms analysis

**Per-Cyclone Directory Structure**:
```
{track_id}_ERA5_track/
├── periods.csv                   (lifecycle phase times)
├── Ca_level.csv, Ck_level.csv   (32 pressure levels)
├── Ca_1_pressure_level.csv...   (baroclinic subterms)
├── Ck_1_pressure_level.csv...   (barotropic subterms)
└── Ba_level.csv, Bk_level.csv   (boundary effects)
```
- **Vertical Resolution**: 32 levels (1000-100 hPa)
- **Temporal Resolution**: 3-hourly

---

## 💾 Local Cached/Processed Files (This Directory)

### `energy_cache.parquet` (6 MB)

**Created By**: `scripts/preprocess_data/preprocess_data.py`  
**Load Function**: `load_cache()` from same script  
**Load Time**: <1 second  
**Used By**: All clustering pipeline scripts

**Content**: Phase-averaged energy data for all cyclones
- **Records**: ~30,000+ (one per cyclone-phase combination)
- **Columns**: track_id, period, phase, + all 18 energy terms
- **Format**: Parquet with Snappy compression (10:1 ratio)
- **Filtering**: Complete lifecycle cyclones only (4-phase sequence)

### `tracks_SAt_filtered_with_energetics_processed.csv` (66 MB)

**Created By**: `scripts/preprocess_data/extract_tracks_from_zenodo.py`  
**Source**: Zenodo DOI 10.5281/zenodo.18133432  
**Purpose**: Local cache for faster repeated access  
**Used By**: Exploratory individual cyclone scripts

**Columns**: track_id, date, lon/lat vor, vor42, Kz, Ke, Ck, Ca, BAe, BKe, Ge

### `era5_ep_structure/` Directory

**Created By**: EP structure analysis pipeline (`scripts/ep_structure_analysis/`)

**Files**:
- `precomputed_composites_ep1.nc` (~200 MB) - 444 EP1 cyclone composites
- `precomputed_composites_ep2.nc` (~200 MB) - 979 EP2 cyclone composites
- `era5_climatology_*.nc` (5 files) - 30-year monthly means (1991-2020) for anomaly calculation

**Composite Variables**:
- **Total-field**: egr, pv_200/850, adv_T_850, div_q_975, msl, ke_adv_250, u/v winds
- **Anomalies**: pv_anom, adv_T_anom, div_q_anom, ke_adv_anom, msl_anom

**Used By**: `scripts/main/07_figure_ep1_ep2_dynamical_composites.py`

### `ck_analysis/` Directory

**Created By**: `scripts/ck_subterms_analysis/`  
**Content**: Ck subterm decomposition and vertical breakdowns

### `temp_lec_zenodo/` Directory

**Source**: Zenodo LEC archive (DOI 10.5281/zenodo.18243447)  
**Size**: ~1.2 GB extracted  
**Purpose**: Temporary storage for LEC results with vertical resolution

---

## 📊 Data Usage Summary

| Script Category | Primary Data Source | Load Method |
|----------------|---------------------|-------------|
| **Main figures** (01, 05, 06) | GitHub tracks | `load_tracks()` |
| **Clustering pipeline** | energy_cache.parquet | `load_cache()` |
| **EP structure analysis** (07) | era5_ep_structure/ composites | `xr.open_dataset()` |
| **Vertical analysis** (S3) | temp_lec_zenodo/ | Direct CSV reads |
| **Exploratory scripts** | Zenodo cached tracks | Local CSV |

---

## 🔄 Data Pipeline Flow

```
1. Remote Sources (GitHub/Zenodo)
   ↓
2. Preprocessing Scripts (scripts/preprocess_data/)
   ↓
3. Local Cache (this directory)
   ↓
4. Analysis Scripts
   ↓
5. Results (results/) + Figures (figures/)
```

**Key Point**: Main analysis scripts use **GitHub** (not Zenodo) for tracks via `load_tracks()`. Zenodo is used for preprocessing and specialized analyses requiring full vertical resolution.

---

## 🗑️ `.gitignore` Guidelines

Large files not versioned:
- `*.parquet` (generated caches)
- `temp_lec_zenodo/` (Zenodo LEC archive)
- `era5_ep_structure/*.nc` (ERA5 composites)
- `*_processed.csv` files >50 MB

Small metadata/results are versioned for reproducibility.
