# Data Structure Documentation

This document describes the data structure for cyclone tracking and energetics analysis in the South Atlantic region.

---

## 1. Integrated Tracks and Energetics Dataset

**Source**: Zenodo ([DOI: 10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432))  
**File**: `tracks_SAt_filtered_with_energetics.csv`  
**Format**: Long format - each row is a single UTC time step of a cyclone

### Dataset Characteristics:
- **Period**: 1979-2020 (42 years)
- **Tracking Method**: TRACK algorithm using 850 hPa relative vorticity
- **Energy Method**: Semi-Lagrangian Lorenz Energy Cycle in 15°×15° storm-following domain
- **Temporal Resolution**: 
  - Track data (position, vorticity): 1-hourly
  - Energy data (LEC terms): 3-hourly (may contain NaN at 1h and 2h marks)
- **Regions**: ARG (Argentina), LA-PLATA (La Plata basin), SE-BR (Southeast Brazil)

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
from load_data import load_energy_by_cyclone

# Load energy data for a specific cyclone
energy = load_energy_by_cyclone('19790097')

# Each row is a life cycle phase
print(energy[['Az', 'Ae', 'Kz', 'Ke', 'Ca', 'Ce']])
```

---

## 2. Preprocessed Phase-Averaged Energy Data

**Source**: Generated locally using `scripts/analysis/preprocess_data.py`  
**File**: `data/energy_cache.parquet`  
**Format**: Each row represents phase-averaged energy values for a cyclone

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
from scripts.analysis.preprocess_data import load_cache

# Load preprocessed data
df = load_cache()

# Filter by phase
intensification_data = df[df['phase'] == 'intensification']

# Analyze specific conversion
mean_ca = df.groupby('phase')['Ca'].mean()
```

### Advantages:
- **Fast loading**: ~1-2 seconds vs several minutes for raw data
- **Memory efficient**: Compressed Parquet format
- **Analysis-ready**: Pre-aggregated by phase
- **Consistent**: All cyclones processed uniformly

---

## 3. Complete LEC Results Dataset

**Source**: Zenodo ([DOI: 10.5281/zenodo.18243447](https://zenodo.org/records/18243447))  
**Location**: Remote (Zenodo) or local `data/lec_results/` (if downloaded)  
**Format**: One directory per cyclone with multiple CSV files

### Dataset Characteristics:
- **Period**: 1979-2020 (42 years)
- **Cyclones**: ~1,500+ systems
- **Analysis**: Full Lorenz Energy Cycle with vertical resolution
- **Pressure Levels**: 32 levels from 1000 hPa to 100 hPa
- **Temporal Resolution**: 3-hourly during each life cycle phase

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

### Usage Examples:

#### Load phase periods:
```python
import pandas as pd

track_id = '19790006'
periods = pd.read_csv(f'data/lec_results/{track_id}_ERA5_track/periods.csv', index_col=0)

# Get intensification times
start = pd.to_datetime(periods.loc['intensification', 'start'])
end = pd.to_datetime(periods.loc['intensification', 'end'])
```

#### Load vertical profile:
```python
# Load Ca (baroclinic conversion) by pressure level
ca_levels = pd.read_csv(
    f'data/lec_results/{track_id}_ERA5_track/Ca_level.csv',
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

lec_dir = Path('data/lec_results')
all_cyclones = [d.name.replace('_ERA5_track', '') 
                for d in lec_dir.iterdir() 
                if d.is_dir() and d.name.endswith('_ERA5_track')]

print(f"Found {len(all_cyclones)} cyclones with LEC results")
```

### Applications:
- **Vertical structure analysis**: Energy conversions by pressure level
- **Phase-specific energetics**: Filter by intensification, mature, etc.
- **Time evolution**: 3-hourly resolution throughout life cycle
- **Diagnostic studies**: Baroclinic vs barotropic processes at different levels
- **Statistical analysis**: Ensemble statistics across many cyclones

---

## Data Access Summary

### Quick Reference:

| Dataset | Source | File | Use Case |
|---------|--------|------|----------|
| **Tracks + Energetics** | [Zenodo 18133432](https://doi.org/10.5281/zenodo.18133432) | `tracks_SAt_filtered_with_energetics.csv` | Time series analysis, tracking |
| **Phase-Averaged Energy** | Local preprocessing | `energy_cache.parquet` | Statistical analysis by phase |
| **Complete LEC Results** | [Zenodo 18243447](https://zenodo.org/records/18243447) | `lec_results/{track_id}_ERA5_track/` | Vertical structure, detailed energetics |

### Loading Functions:

```python
from scripts.utils.load_data import load_tracks, load_energy_by_cyclone
from scripts.analysis.preprocess_data import load_cache

# 1. Load tracks (time series, 1-hourly)
tracks = load_tracks()

# 2. Load phase-averaged energy (fast, preprocessed)
df = load_cache()

# 3. Load complete LEC results for specific cyclone (vertical levels)
import pandas as pd
track_id = '19790006'
ca_levels = pd.read_csv(f'data/lec_results/{track_id}_ERA5_track/Ca_level.csv',
                        index_col=0, parse_dates=True)
periods = pd.read_csv(f'data/lec_results/{track_id}_ERA5_track/periods.csv',
                      index_col=0)
```
