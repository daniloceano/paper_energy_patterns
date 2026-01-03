# Three Most Intense Cyclones - Individual Figures

This directory contains individual figures for the three most intense cyclones in the dataset, using the `lorenz-phase-space` package for LPS diagrams.

## Cyclones Featured

1. **19920472**: Maximum vorticity 15.95 × 10⁻⁵ s⁻¹
  - Genesis: 1992-06-05 09:00 UTC — Lysis: 1992-06-15 01:00 UTC
  - Peak vorticity: 1992-06-07 21:00 UTC (15.95 × 10⁻⁵ s⁻¹)
2. **19950629**: Maximum vorticity 15.53 × 10⁻⁵ s⁻¹
  - Genesis: 1995-07-14 22:00 UTC — Lysis: 1995-07-22 09:00 UTC
  - Peak vorticity: 1995-07-17 14:00 UTC (15.53 × 10⁻⁵ s⁻¹)
3. **20070643**: Maximum vorticity 15.48 × 10⁻⁵ s⁻¹
  - Genesis: 2007-07-24 14:00 UTC — Lysis: 2007-07-29 03:00 UTC
  - Peak vorticity: 2007-07-27 02:00 UTC (15.48 × 10⁻⁵ s⁻¹)

## Figures Generated

For each cyclone, three separate figures are created:

### 1. Conversion Phase Space (`{track_id}_lps_conversion.png`)

Lorenz Phase Space showing baroclinic and barotropic energy conversions.

**Axes:**
- X-axis: Ck - Conversion from zonal to eddy Kinetic Energy (W m⁻²)
- Y-axis: Ca - Conversion from zonal to eddy Potential Energy (W m⁻²)

**Markers:**
- Color: Ge - Generation of eddy Available Potential Energy (W m⁻²)
- Size: Ke - Eddy Kinetic Energy (J m⁻²)

**Features:**
- Generated using `lorenz-phase-space` package
- Standard mode (zoom=False) for consistent scaling
- Includes trajectory connections and phase space annotations
- Special markers: 'A' (start), 'Z' (end)

### 2. Imports Phase Space (`{track_id}_lps_imports.png`)

Lorenz Phase Space showing energy transport across cyclone boundaries.

**Axes:**
- X-axis: BAe - Eddy APE transport across boundaries (W m⁻²)
- Y-axis: BKe - Eddy KE transport across boundaries (W m⁻²)

**Markers:**
- Color: Ge - Generation of eddy Available Potential Energy (W m⁻²)
- Size: Ke - Eddy Kinetic Energy (J m⁻²)

**Features:**
- Generated using `lorenz-phase-space` package
- Standard mode (zoom=False) for consistent scaling
- Shows role of boundary fluxes in cyclone energetics

### 3. Track Map (`{track_id}_track.png`)

Geographic track with energy reservoir information.

**Map Features:**
- Track line showing complete cyclone path
- Green circle: Genesis location
- Red X: Lysis location
- Coastlines, borders, and geographic features

**Markers:**
- Color: `vor42` - Relative vorticity (10$^{-5}$ s$^{-1}$)
- Size: `Ke` - Eddy Kinetic Energy (J m$^{-2}$)

**Temporal sampling:** The track map is plotted at the temporal resolution of `Ke` (3-hourly). Points are plotted only at timestamps where `Ke` is present; if no 3-hour samples exist for a cyclone, the script falls back to every 3rd hourly record.

**Legends:** A single combined legend shows representative `Ke` size proxies and the Genesis/Lysis markers (avoids overlapping separate legend boxes).

## Technical Details

### Data Source
- **URL**: https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv
- **DOI**: 10.5281/zenodo.18133432
- **Temporal Resolution**: 
  - Track data: 1-hourly
  - Energy data: 3-hourly (LPS uses energy records only)

### Software
- **lorenz-phase-space**: 1.4.0
- **Python**: 3.11
- **Key packages**: matplotlib, cartopy, pandas, numpy

### Figure Specifications
- **Resolution**: 300 DPI
- **Format**: PNG with white background
- **Font**: Arial/Helvetica sans-serif
- **Color schemes**:
  - LPS: cmocean.cm.curl (default from lorenz-phase-space)
  - Track Ae: RdBu_r (diverging, centered on zero)

## Usage

To regenerate these figures:

```bash
source activate.sh
python scripts/exploratory/figure_three_intense_cyclones_individual.py
```

## Interpretation

### Conversion Phase Space Quadrants

| Quadrant | Ck | Ca | Physical Interpretation |
|----------|----|----|------------------------|
| Upper-Left | - | + | Barotropic and baroclinic instabilities |
| Upper-Right | + | + | Baroclinic instability |
| Lower-Left | - | - | Barotropic instability |
| Lower-Right | + | - | Eddy feeding local circulation |

### Energy Flow Analysis

1. **Conversion diagrams** reveal the dominant energy pathways during cyclone evolution
2. **Imports diagrams** show the relative importance of boundary fluxes vs local generation
3. **Track maps** demonstrate spatial variability in energy reservoirs along the cyclone path

### Comparing the Three Cyclones

These extreme cases allow investigation of:
- **Different intensification mechanisms**: Baroclinic vs barotropic pathways
- **Energy import strategies**: Systems relying on boundary fluxes vs diabatic generation
- **Spatial patterns**: Genesis regions and preferred development zones
- **Temporal evolution**: How energy budgets change through the life cycle

## Scientific Context

These figures support analysis of:
- Extreme cyclone energetics in the Southwestern Atlantic
- Variability in intensification mechanisms for very intense systems
- Role of different energy pathways in producing extreme vorticity
- Relationship between energy reservoirs and cyclone intensity

## Files

```
three_most_intense_cyclones/
├── README.md (this file)
├── 19920472_lps_conversion.png
├── 19920472_lps_imports.png
├── 19920472_track.png
├── 19950629_lps_conversion.png
├── 19950629_lps_imports.png
├── 19950629_track.png
├── 20070643_lps_conversion.png
├── 20070643_lps_imports.png
└── 20070643_track.png
```

## References

### Lorenz Phase Space Package
- GitHub: https://github.com/daniloceano/lorenz_phase_space
- PyPI: https://pypi.org/project/lorenz-phase-space/

### Dataset
- de Souza, D., & Gramcianinov, C. (2026). Southwestern Atlantic Cyclone Tracks and Semi-Lagrangian Lorenz Energy Cycle (LEC) diagnostics (1979–2020) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.18133432

---

**Generated**: January 2, 2026  
**Script**: `scripts/exploratory/figure_three_intense_cyclones_individual.py`
