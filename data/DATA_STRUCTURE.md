# Data Structure Documentation

## Integrated Tracks and Energetics Dataset

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

## Data Access

All data is accessed directly from GitHub without downloading:

```python
from load_data import load_tracks, load_energy_by_cyclone, load_all_energy_data

# Load all tracks
tracks = load_tracks()

# Load energy for specific cyclone
energy = load_energy_by_cyclone('19790097')

# Load energy for multiple cyclones
track_ids = tracks['track_id'].unique()[:10]  # First 10
energy_dict = load_all_energy_data(track_ids)
```
