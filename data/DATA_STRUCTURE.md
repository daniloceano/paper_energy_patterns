# Data Structure Documentation

This document describes the data structure and sources for cyclone tracking and energetics analysis in the South Atlantic region.

---

## Overview: Data Sources Hierarchy

For the corrected climatology rerun, the authoritative population is the
3,820 complete-lifecycle set reproducibly selected from tracked
`energy_cache.parquet`; `ep1_cases.csv` and `epall_cases.csv` are downstream
subsets. See `scripts/lec_climatology_rerun/README.md`.

```
PRIMARY SOURCES (Remote):
├── GitHub: Tracks + Energy averages (Used by most scripts)
│   ├── tracks_SAt_filtered_with_periods.csv
│   └── csv_database_energy_by_periods/{track_id}_averages.csv
│
├── Zenodo Archive 1: Complete tracks with energetics (Preprocessing/Exploratory)
│   └── DOI: 10.5281/zenodo.18133432
│
└── Zenodo Archive 2: LEC results with vertical resolution (Vertical analysis)
    └── DOI: 10.5281/zenodo.18243447

LOCAL CACHE (Generated):
├── energy_cache.parquet          → Fast clustering pipeline access
├── tracks_*_processed.csv        → Exploratory analysis cache
├── era5_ep_structure/            → ERA5 composites
└── temp_lec_zenodo/              → Extracted LEC vertical data
```

**Key Point**: Main analysis scripts (figures 01, 05, 06, S2) use **GitHub tracks**, not Zenodo. Zenodo is for preprocessing and specialized analyses.

---

## 1. GitHub Source - Cyclone Tracks (Primary)

**URL**: `https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/refs/heads/master/tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv`

**Access Method**: `load_tracks()` from `scripts/utils/load_data.py`

### Dataset Characteristics:
- **Period**: 1979-2020 (42 years)
- **Cyclones**: 6,789 unique systems
- **Records**: 631,009 hourly track points
- **Tracking Method**: TRACK algorithm using 850 hPa relative vorticity
- **Temporal Resolution**: 1-hourly
- **Load Time**: ~10 seconds
- **Genesis Regions**: ARG (Argentina), LA-PLATA (La Plata basin), SE-BR (Southeast Brazil)

---

## Column Descriptions

### Identification and Location
- `track_id`: Unique cyclone identifier (format: YYYYNNNN, e.g., 19790097)
- `date`: UTC timestamp (ISO format)
- `lon vor`: Longitude of cyclone center (degrees)
- `lat vor`: Latitude of cyclone center (degrees)
- `vor42`: Filtered 850 hPa vorticity (×10⁵ s⁻¹, stored as positive values)
- `region`: Genesis region classification
- `period`: Life cycle phase (see below)

### Life Cycle Phases:
- `incipient`: Initial development phase
- `intensification`: Growth phase
- `mature`: Maximum intensity phase
- `decay`: Weakening phase

Phases are determined objectively using CycloPhaser based on vorticity evolution.

---

## Energy Budget Terms

### Availability
- Available at 3-hourly intervals
- May contain NaN values at intermediate time steps
- Computed in semi-Lagrangian (storm-following) framework

### Energy Budget Terms:

#### Available Energy:
- `Az`: Available zonal potential energy
- `Ae`: Available eddy potential energy
- `Kz`: Zonal kinetic energy
- `Ke`: Eddy kinetic energy

#### Conversion Terms:
- `Cz`: Az → Kz (zonal conversion)
- `Ca`: Az → Ae (baroclinic conversion)
- `Ck`: Ke → Kz (eddy-to-mean kinetic energy conversion)
- `Ce`: Ae → Ke (eddy kinetic generation)

#### Boundary Terms:
- `BAz`, `BAe`, `BKz`, `BKe`: Boundary fluxes of A and K
- `BΦZ`, `BΦE`: Boundary geopotential fluxes

#### Generation/Dissipation:
- `Gz`: Generation of Az
- `Ge`: Generation of Ae
- `RGz`, `RGe`: Residual generation terms
- `RKz`, `RKe`: Residual kinetic terms

#### Tendencies:
- `∂Az/∂t (finite diff.)`: Time tendency of Az
- `∂Ae/∂t (finite diff.)`: Time tendency of Ae
- `∂Kz/∂t (finite diff.)`: Time tendency of Kz
- `∂Ke/∂t (finite diff.)`: Time tendency of Ke

### Units:
All energy terms in **W m⁻²** (Watts per square meter)

### Example Usage:
```python
from scripts.utils.load_data import load_tracks

# Load tracks from GitHub (primary source)
tracks = load_tracks()
print(f"Loaded {tracks['track_id'].nunique()} cyclones")

# Get genesis positions (first point of each track)
genesis = tracks.groupby('track_id').first().reset_index()
print(genesis[['track_id', 'lat vor', 'lon vor', 'region']])
```

---

## 2. GitHub Source - Energy Data by Cyclone

**URL Base**: `https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/master/csv_database_energy_by_periods`

**Access Methods**: 
- Single cyclone: `load_energy_by_cyclone(track_id)` 
- Batch: `load_all_energy_data(track_ids, n_workers=50)`

### Dataset Characteristics:
- **Structure**: One CSV file per cyclone (`{track_id}_averages.csv`)
- **Total Files**: up to 6,789 individual cyclone files
- **Variables**: 18+ energy terms (see Section 1 for variable list)
- **Format**: Phase-averaged values (one row per lifecycle phase)
- **Load Time**: ~4-5 minutes for all cyclones (50 parallel workers)
- **Used By**: Preprocessing pipeline → generates `energy_cache.parquet`

### Example Usage:
```python
from scripts.utils.load_data import load_energy_by_cyclone

# Load energy for specific cyclone
energy = load_energy_by_cyclone('19790097')
if energy is not None:
    print(energy[['period', 'Az', 'Ae', 'Kz', 'Ke', 'Ca', 'Ck']])
```

---

## 3. Zenodo Archive 1 - Complete Tracks with Energetics

**DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)  
**URL**: `https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv`

### Dataset Characteristics:
- **Size**: 180.8 MB compressed, ~63 MB uncompressed
- **Format**: Long format CSV (each row = one timestep)
- **Temporal Resolution**: 
  - Track data (position, vorticity): 1-hourly
  - Energy data (LEC terms): 3-hourly (NaN at intermediate hours)
- **Download Script**: `scripts/preprocess_data/extract_tracks_from_zenodo.py`
- **Local Cache**: `data/tracks_SAt_filtered_with_energetics_processed.csv` (66 MB)
- **Used By**: Exploratory scripts for individual cyclone deep-dives

**Note**: This is a **supplementary source** for detailed time-series analysis. Most scripts use GitHub tracks (Section 1) instead.

---

## 4. Local Cache - Preprocessed Phase-Averaged Energy Data

**Source**: Generated locally using `scripts/preprocess_data/preprocess_data.py`  
**File**: `data/energy_cache.parquet`  
**Input**: GitHub energy data (Section 2)  
**Format**: Each row = one cyclone-phase combination with averaged energy values

### Dataset Characteristics:
- **Processing**: Averages all energy terms within each life cycle phase
- **Input**: Individual cyclone energy data from Zenodo
- **Output**: Compressed Parquet file for fast loading
- **Size**: ~50-100 MB (compressed)

### Structure:
Each row contains averaged energy values for one phase of one cyclone:

```python
df.head()
            period             Az             Ae            Kz             Ke  ...
0        incipient  186096.878548  153604.209626  1.183953e+06  324852.711420  ...
1  intensification  371983.979049  276327.994286  2.420030e+06  650805.052089  ...
2           mature  384654.587402  106160.691261  3.226003e+06  405928.668884  ...
3            decay  443555.680415   50897.761686  3.457435e+06  183344.784495  ...
4         residual  645750.361195  167365.078105  3.287393e+06  381503.752583  ...
```

### Columns:
- `track_id`: Cyclone identifier
- `period`: Life cycle phase (incipient, intensification, mature, decay, residual)
- `phase`: Simplified phase classification
- All energy terms: Az, Ae, Kz, Ke, Ca, Ce, Ck, Cz, etc. (phase-averaged)
- Boundary terms: BAz, BAe, BKz, BKe (phase-averaged)
- Generation terms: Gz, Ge, RGz, RGe, RKz, RKe (phase-averaged)
- Tendencies: dAzdt, dAedt, dKzdt, dKedt (phase-averaged)

### Usage:
```python
from scripts.preprocess_data.preprocess_data import load_cache

# Load cached preprocessed data (fast!)
df = load_cache()
print(f"Loaded {len(df)} records in <1 second")

# Filter by phase
intensification = df[df['period'] == 'intensification']

# Analyze specific conversion
mean_ca = df.groupby('period')['Ca'].mean()
```

### Generation Command:
```bash
python scripts/preprocess_data/preprocess_data.py
```
Downloads all energy data from GitHub → filters complete lifecycles → saves Parquet cache.

### Advantages:
- **Fast loading**: ~1-2 seconds vs several minutes for raw data
- **Memory efficient**: Compressed Parquet format
- **Analysis-ready**: Pre-aggregated by phase
- **Consistent**: All cyclones processed uniformly

---

## 5. Zenodo Archive 2 - LEC Results with Vertical Resolution

**DOI**: [10.5281/zenodo.18243447](https://zenodo.org/records/18243447)  
**URL**: `https://zenodo.org/records/18243447/files/LEC_Results_energetic-patterns_csv_only.tar.gz`  
**Local Extract**: `data/temp_lec_zenodo/LEC_Results_energetic-patterns/`  
**Format**: One directory per cyclone with multiple CSV files

### Dataset Characteristics:
- **Size**: 634 MB compressed, ~1.2 GB extracted
- **Period**: 1979-2020 (42 years)
- **Cyclones**: 6,789 systems before complete-lifecycle filtering
- **Analysis**: Full Lorenz Energy Cycle with vertical resolution
- **Pressure Levels**: 32 levels from 1000 hPa to 100 hPa
- **Temporal Resolution**: 3-hourly during each life cycle phase
- **Download Script**: `scripts/preprocess_data/download_lec_from_zenodo.py`
- **Used By**: S3 figure (vertical structure), Ck subterms analysis

### Directory Structure:
```
{track_id}_ERA5_track/
├── {track_id}_ERA5_track_results.csv    # Integrated LEC results over life cycle
├── {track_id}_ERA5_track_trackfile      # Track metadata
├── periods.csv                           # Phase time periods
├── log.{track_id}_ERA5                  # Processing log
├── Az_level.csv                          # Available zonal PE by level
├── Ae_level.csv                          # Available eddy PE by level
├── Kz_level.csv                          # Zonal KE by level
├── Ke_level.csv                          # Eddy KE by level
├── Ca_level.csv                          # Baroclinic conversion by level
├── Ce_level.csv                          # Eddy generation by level
├── Ck_level.csv                          # Barotropic conversion by level
├── Cz_level.csv                          # Zonal conversion by level
├── Ge_level.csv                          # Eddy PE generation by level
└── Gz_level.csv                          # Zonal PE generation by level
```

### File Descriptions:

#### 1. `{track_id}_ERA5_track_results.csv`
Life cycle-integrated energy budget for the entire cyclone:
- Columns: All LEC terms (Az, Ae, Kz, Ke, Ca, Ce, Ck, Cz, etc.)
- Single row per cyclone
- Time-averaged over entire life cycle

#### 2. `periods.csv`
Time periods for each life cycle phase:
```csv
,start,end
intensification,1979-01-01 12:00:00,1979-01-05 09:00:00
mature,1979-01-05 09:00:00,1979-01-08 18:00:00
decay,1979-01-08 18:00:00,1979-01-12 00:00:00
```
- Index column: Phase name
- `start`: Phase start time (UTC)
- `end`: Phase end time (UTC)

#### 3. `{energy_term}_level.csv`
Energy term computed at each pressure level over time:
- Index: Timestamps (3-hourly)
- Columns: Pressure levels in Pa (1000.0, 2000.0, ..., 100000.0)
- Values: Energy term in W m⁻² at each level and time
- Covers all life cycle phases

Example structure:
```csv
time,1000.0,2000.0,3000.0,...,100000.0
1979-02-20 00:00:00,-1.858e-07,1.180e-07,9.514e-09,...,-1.779e-05
1979-02-20 03:00:00,2.144e-07,6.407e-08,-1.437e-07,...,-1.811e-05
```

#### 4. `{track_id}_ERA5_track_trackfile`
Cyclone track positions and metadata throughout life cycle

### Pressure Levels:
32 levels in Pascals (Pa):
```
1000, 2000, 3000, 5000, 7000, 10000, 12500, 15000, 17500, 20000,
22500, 25000, 30000, 35000, 40000, 45000, 50000, 55000, 60000,
65000, 70000, 75000, 77500, 80000, 82500, 85000, 87500, 90000,
92500, 95000, 97500, 100000
```
(Equivalent to 10-1000 hPa)

### Download and Extract:
```bash
# Download from Zenodo (one-time)
python scripts/preprocess_data/download_lec_from_zenodo.py

# Data extracted to: data/temp_lec_zenodo/LEC_Results_energetic-patterns/
```

### Usage Examples:

#### Load phase periods:
```python
import pandas as pd

track_id = '19790006'
base_dir = 'data/temp_lec_zenodo/LEC_Results_energetic-patterns'
periods = pd.read_csv(f'{base_dir}/{track_id}_ERA5_track/periods.csv', index_col=0)

# Get intensification times
start = pd.to_datetime(periods.loc['intensification', 'start'])
end = pd.to_datetime(periods.loc['intensification', 'end'])
```

#### Load vertical profile:
```python
# Load Ca (baroclinic conversion) by pressure level
ca_levels = pd.read_csv(
    f'{base_dir}/{track_id}_ERA5_track/Ca_level.csv',
    index_col=0, parse_dates=True
)

# Filter for intensification phase
ca_intensification = ca_levels[(ca_levels.index >= start) & (ca_levels.index <= end)]

# Compute mean profile during intensification
ca_mean_profile = ca_intensification.mean(axis=0)

# Convert pressure from Pa to hPa
pressure_hpa = ca_mean_profile.index.astype(float) / 100.0
```

#### Analyze all cyclones:
```python
from pathlib import Path

lec_dir = Path('data/temp_lec_zenodo/LEC_Results_energetic-patterns')
all_cyclones = [d.name.replace('_ERA5_track', '') 
                for d in lec_dir.iterdir() 
                if d.is_dir() and d.name.endswith('_ERA5_track')]

print(f"Found {len(all_cyclones)} cyclones with LEC results")
```

**Note**: This dataset is large (~1.2 GB). Only download if you need vertical resolution analysis.

### Applications:
- **Vertical structure analysis**: Energy conversions by pressure level
- **Phase-specific energetics**: Filter by intensification, mature, etc.
- **Time evolution**: 3-hourly resolution throughout life cycle
- **Diagnostic studies**: Baroclinic vs barotropic processes at different levels
- **Statistical analysis**: Ensemble statistics across many cyclones

---

## 6. Local Generated - ERA5 Composite Data

**Directory**: `data/era5_ep_structure/`  
**Created By**: `scripts/ep_structure_analysis/` pipeline  
**Used By**: `scripts/main/07_figure_ep1_ep2_dynamical_composites.py`

### Files:
- `precomputed_composites_ep1.nc` (~200 MB) - Composite of 444 EP1 cyclones
- `precomputed_composites_ep2.nc` (~200 MB) - Composite of 979 EP2 cyclones
- `era5_climatology_*.nc` (5 files) - 30-year monthly means (1991-2020)

### Composite Variables:
**Total-field diagnostics:**
- `egr`: Eady Growth Rate (500-850 hPa) [day⁻¹]
- `pv_200`, `pv_850`: Potential Vorticity [PVU]
- `adv_T_850`: Temperature advection [K h⁻¹]
- `div_q_975`: Moisture flux divergence [kg m⁻² h⁻¹]
- `msl`: Mean sea level pressure [hPa]
- `ke_adv_250`: KE advection [W m⁻²]
- `u_250`, `v_250`, `u_850`, `v_850`: Wind components

**Anomaly diagnostics:**
- `pv_200_anom`, `pv_850_anom`, `adv_T_850_anom`, etc.

### Generation:
```bash
# Run EP structure analysis pipeline
cd scripts/ep_structure_analysis
python step1_select_ep_tracks.py      # Select EP1/EP2 cases
python step2_download_era5_parallel.py # Download ERA5 per case
python step2_1_download_era5_monthly_means.py # Download climatology
python step3_precompute_composites.py  # Create composites
```

---

## Data Access Summary

### Quick Reference:

| Dataset | Source | Access Method | Primary Use |
|---------|--------|---------------|-------------|
| **Tracks (1-hourly)** | GitHub | `load_tracks()` | Main figures (01, 05, 06, S2) |
| **Energy (phase-avg)** | GitHub | `load_energy_by_cyclone()` | Preprocessing pipeline |
| **Energy Cache** | Local (generated) | `load_cache()` | Clustering analysis |
| **Zenodo Tracks** | Zenodo 18133432 | Local CSV cache | Exploratory deep-dives |
| **LEC Vertical** | Zenodo 18243447 | Direct CSV reads | S3 figure, Ck analysis |
| **ERA5 Composites** | Local (generated) | `xarray.open_dataset()` | 07 figure (EP dynamics) |

### Primary Loading Functions:

```python
# === MOST COMMON: GitHub tracks (used by most scripts) ===
from scripts.utils.load_data import load_tracks
tracks = load_tracks()  # ~10 sec load time

# === Clustering pipeline: local cache ===
from scripts.preprocess_data.preprocess_data import load_cache
df = load_cache()  # <1 sec load time

# === Individual cyclone energy: GitHub ===
from scripts.utils.load_data import load_energy_by_cyclone
energy = load_energy_by_cyclone('19790097')  # Returns None if not found

# === Vertical structure: Zenodo LEC ===
import pandas as pd
track_id = '19790006'
base_dir = 'data/temp_lec_zenodo/LEC_Results_energetic-patterns'
ca_levels = pd.read_csv(f'{base_dir}/{track_id}_ERA5_track/Ca_level.csv',
                        index_col=0, parse_dates=True)

# === ERA5 composites: local NetCDF ===
import xarray as xr
ep1_composite = xr.open_dataset('data/era5_ep_structure/precomputed_composites_ep1.nc')
```

---

## Data Pipeline Flowchart

```
┌─────────────────────────────────────────────────────┐
│         REMOTE SOURCES (GitHub + Zenodo)            │
├─────────────────────────────────────────────────────┤
│ GitHub:                                             │
│  • tracks_SAt_filtered_with_periods.csv             │
│  • csv_database_energy_by_periods/*.csv             │
│                                                     │
│ Zenodo 18133432:                                    │
│  • tracks_SAt_filtered_with_energetics.csv          │
│                                                     │
│ Zenodo 18243447:                                    │
│  • LEC_Results_energetic-patterns.tar.gz            │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────┐
│      PREPROCESSING (scripts/preprocess_data/)       │
├─────────────────────────────────────────────────────┤
│ • preprocess_data.py → energy_cache.parquet         │
│ • extract_tracks_from_zenodo.py → local CSV        │
│ • download_lec_from_zenodo.py → temp_lec_zenodo/   │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────┐
│       LOCAL CACHE (data/ directory)                 │
├─────────────────────────────────────────────────────┤
│ • energy_cache.parquet (6 MB, fast access)         │
│ • tracks_*_processed.csv (66 MB, exploratory)      │
│ • temp_lec_zenodo/ (1.2 GB, vertical analysis)     │
│ • era5_ep_structure/ (400+ MB, composites)         │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────┐
│          ANALYSIS & FIGURES                         │
├─────────────────────────────────────────────────────┤
│ Main Scripts → figures/main/                        │
│ Clustering → results/cluster/                       │
│ EP Structure → results/ep_structure/                │
└─────────────────────────────────────────────────────┘
```
