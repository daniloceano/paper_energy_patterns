# Data Structure Documentation

## Cyclone Tracks (`tracks_SAt_filtered_with_periods.csv`)

Hourly observations of cyclone positions and characteristics.

### Columns:
- `track_id`: Unique cyclone identifier (format: YYYYNNNN, e.g., 19790097)
- `date`: Observation timestamp (ISO format)
- `lon vor`: Longitude of vortex center
- `lat vor`: Latitude of vortex center
- `vor42`: Relative vorticity at 850 hPa (units: 10⁻⁵ s⁻¹)
- `region`: Geographic region (mostly 'ARG' - Argentina/SW Atlantic)
- `geometry`: Point geometry (WKT format)
- `period`: Life cycle phase (see below)

### Life Cycle Phases:
- `incipient`: Initial development phase
- `intensification`: Growth phase
- `mature`: Maximum intensity phase
- `decay`: Weakening phase
- `residual`: Final dissipation phase

Some cyclones may have secondary phases (e.g., `mature 2`, `decay 2`) indicating cyclone regeneration.

---

## Energy Data (`{track_id}_averages.csv`)

Average energy budget terms for each life cycle phase of a cyclone.

### File Format:
- One file per cyclone
- Filename: `{track_id}_averages.csv` (e.g., `19790097_averages.csv`)
- Each row represents one life cycle phase

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
