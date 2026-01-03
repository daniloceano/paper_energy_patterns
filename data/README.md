# Data Directory

## Input Data (Accessed from Zenodo)

Input data **does not need to be downloaded** - accessed directly via URL:

### Cyclone Tracks and Energetics (Integrated Dataset)
- **DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)
- **Direct URL**: https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv
- **Citation**: de Souza, D., & Gramcianinov, C. (2026). Southwestern Atlantic Cyclone Tracks and Semi-Lagrangian Lorenz Energy Cycle (LEC) diagnostics (1979–2020) [Data set]. Zenodo.
- **Description**: Complete dataset combining cyclone tracks with semi-Lagrangian Lorenz Energy Cycle diagnostics
- **Period**: 1979-2020 (42 years)
- **Format**: Long format CSV (each row = one time step of one cyclone)
- **Size**: 180.8 MB
- **Temporal Resolution**:
  - Track variables (position, vorticity): 1-hourly
  - Energy variables (LEC terms): 3-hourly

#### Main Columns:

**Identification and Location:**
  - `track_id`: Unique cyclone identifier (format: YYYYNNNN)
  - `date`: UTC timestamp
  - `lon vor`, `lat vor`: Cyclone center coordinates (degrees)
  - `vor42`: Filtered 850 hPa vorticity (×10⁵ s⁻¹, positive values)
  - `region`: Genesis region (ARG, LA-PLATA, SE-BR)
  - `period`: Life cycle phase (incipient, intensification, mature, decay)

**Energy Reservoirs (J m⁻²):**
  - `Az`, `Ae`, `Kz`, `Ke`

**Conversion Terms (W m⁻²):**
  - `Cz`, `Ca`, `Ce`, `Ck`

**Boundary Terms (W m⁻²):**
  - `BAz`, `BAe`, `BKz`, `BKe` (flux terms)
  - `BΦZ`, `BΦE` (pressure-work terms)

**Generation Terms (W m⁻²):**
  - `Gz`, `Ge` (diabatic generation)

**Tendencies (W m⁻²):**
  - `∂Az/∂t`, `∂Ae/∂t`, `∂Kz/∂t`, `∂Ke/∂t`

**Residuals (W m⁻²):**
  - `RGz`, `RGe`, `RKz`, `RKe`

#### Key Features:
- **Semi-Lagrangian**: 15°×15° storm-following control volume
- **Quality Controlled**: Minimum lifetime/displacement thresholds applied
- **Phase Attribution**: Objective life-cycle segmentation using CycloPhaser
- **Missing Values**: Some timestamps may contain NaN for energy terms

## Processed Data (This directory)

Use this folder to save:
- Intermediate processed data
- Aggregations and statistics
- Data subsets for specific analyses
- Classification/clustering results

**Note**: Don't version very large files. Use `.gitignore` as needed.
