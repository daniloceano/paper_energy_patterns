# Main Figures for Publication

This directory contains publication-ready figures for the Energy Patterns manuscript, following Scientific Reports standards.

## Figures

### Figure 1: Energy Pattern Characteristics
**File:** `ep_intensity_seasonality_trends.png` (729 KB)

Three-panel figure combining key characteristics of Energy Patterns:

#### (a) Intensity Distribution (Top-Left)
- **Type**: Violin plot
- **Shows**: Maximum vorticity distribution (10⁻⁵ s⁻¹) for each Energy Pattern
- **Key Statistics**:
  - **EP1**: 8.81 ± 2.47 × 10⁻⁵ s⁻¹
  - **EP2**: 9.34 ± 2.40 × 10⁻⁵ s⁻¹ (highest)
  - **EP3**: 6.37 ± 2.41 × 10⁻⁵ s⁻¹ (lowest)

**Interpretation**: EP2 produces the most intense cyclones on average, while EP3 (most frequent, 62.7%) produces the weakest cyclones. This suggests that moderate energy conversion patterns (EP2) with balanced pathways may be optimal for cyclone intensification.

#### (b) Seasonal Distribution (Top-Right)
- **Type**: Grouped bar chart
- **Shows**: Percentage of cyclones per season for each Energy Pattern
- **Seasons**: DJF (Summer), MAM (Autumn), JJA (Winter), SON (Spring)
- **Key Findings**:
  - **EP1**: Dominant in Winter (35.6%)
  - **EP2**: Dominant in Summer (30.9%)
  - **EP3**: Dominant in Spring (27.5%)

**Interpretation**: Clear seasonal preferences reflect different environmental conditions favorable to each energy pattern. EP1's winter preference aligns with stronger meridional temperature gradients, while EP2's summer prevalence suggests more barotropic conditions.

#### (c) Interannual Variability and Trends (Bottom - Full Width)
- **Type**: Time series with Mann-Kendall trend analysis
- **Period**: 1979-2020 (42 years)
- **Shows**: Relative frequency (%) of each EP over time with trend lines
- **Statistical Method**: 
  - Mann-Kendall test for monotonic trends (α = 0.05)
  - Sen's slope estimator for trend magnitude
  - Solid lines = significant trends (p < 0.05)
  - Dashed lines = non-significant trends

**Trend Results**:
- **EP1**: No significant trend (p = 0.626, τ = -0.053) → Stable occurrence
- **EP2**: Significant increasing trend (p = 0.035, τ = 0.228)* → Becoming more frequent
- **EP3**: Significant decreasing trend (p = 0.044, τ = -0.217)* → Becoming less frequent

**Climate Change Implications**: The opposing trends (EP2 increasing, EP3 decreasing) while EP1 remains stable suggest a systematic shift in cyclone energetics over the past 40+ years. The increase in EP2 (moderate baroclinic, high intensity) may indicate:
- Changes in baroclinic zone strength or position
- Shifts in available potential energy gradients
- Potential intensification of individual cyclones despite weaker baroclinic forcing
- Adaptation to changing large-scale circulation patterns (SAM, ENSO)

---

### Figure 2: Genesis Density (KDE - Hoskins & Hodges Method)
**File:** `ep_genesis_density_kde.png` (1.5 MB)

Four-panel map figure showing cyclone genesis density using Kernel Density Estimation.

#### Methodology
Following **Hoskins and Hodges (2005)**, cyclone genesis density is computed using:
- **Kernel**: Gaussian with haversine metric (great circle distance)
- **Bandwidth**: 0.05 radians (~555 km)
- **Grid**: Global 2.5° grid (128×64 lon×lat)
- **Units**: Cyclones per 10⁶ km² per year
- **Normalization**: 
  - Total number of cyclones
  - Earth radius at 40°S (6369 km)
  - Time period (42 years)

**Advantages of KDE over point plots**:
1. Reveals underlying probability density of genesis locations
2. Smooths random spatial variability to show systematic patterns
3. Identifies regions of preferential cyclogenesis
4. Quantifies genesis density for comparison

#### Panel Description

**(a) All Cyclones** (Top-Left)
- Composite genesis density for entire dataset
- **Maximum density**: 34.36 cyclones/10⁶ km²/year
- **Primary hotspot**: Southwestern Atlantic near Argentina coast (~60°W, 40-45°S)
- Shows overall cyclogenesis climatology

**(b) EP1** (Top-Right)
- 444 cyclones (11.6% of total)
- **Maximum density**: 3.85 cyclones/10⁶ km²/year
- **Pattern**: Most concentrated genesis, southern distribution
- **Geographic preference**: Closer to Argentina coast, strongest baroclinic forcing

**(c) EP2** (Bottom-Left)
- 979 cyclones (25.6% of total)
- **Maximum density**: 6.86 cyclones/10⁶ km²/year
- **Pattern**: Intermediate concentration and spatial extent
- **Geographic preference**: Middle latitudes, balanced distribution

**(d) EP3** (Bottom-Right)
- 2397 cyclones (62.7% of total) - **Most frequent**
- **Maximum density**: 23.65 cyclones/10⁶ km²/year - **Highest density**
- **Pattern**: Broadest spatial distribution, dominates overall density
- **Geographic preference**: Extends further offshore and equatorward
- **Pattern**: Intermediate concentration and spatial extent
- **Geographic preference**: Middle latitudes, balanced distribution

#### Key Findings

**Spatial Patterns**:
- All EPs share a common genesis region in the southwestern Atlantic
- Latitudinal differences are subtle but systematic:
  - EP1: Most concentrated near 40-45°S
  - EP2: Broadest extent, peak slightly north (~37-42°S)
  - EP3: Intermediate position (~38-44°S)

**Density Comparison**:
- EP3 dominates absolute density (23.65 cyclones/10⁶ km²/year) - most frequent
- EP2 has intermediate density (6.86)
- EP1 has lowest density (3.85) but highest per-cyclone concentration
- Geographic preferences suggest different formation mechanisms:
  - **EP1**: Strong baroclinic forcing near coastline/orography
  - **EP2**: Moderate conditions in transitional zone
  - **EP3**: Diverse conditions allowing genesis over broader area

**Oceanographic Context**:
The primary genesis region corresponds to:
- **Brazil-Malvinas Confluence**: Strong SST gradients
- **Lee of Andes**: Orographic effects, downstream development
- **Upper-level jet stream**: Baroclinic zone position
- **Low-level baroclinicity**: Continental-oceanic temperature contrasts

---

## Scripts

### `figure_intensity_seasonality_trends.py`
Creates Figure 1 with intensity, seasonality, and trend analysis.

**Key Features**:
- Loads track data and merges with clustering results
- Computes maximum vorticity per cyclone
- Seasonal aggregation and percentage calculations
- Mann-Kendall trend analysis with Sen's slope
- Publication-quality formatting (300 DPI)

**Dependencies**:
- pandas, numpy, matplotlib, seaborn
- pymannkendall (trend analysis)
- scipy.stats.theilslopes (Sen's slope)

### `figure_genesis_density_kde.py`
Creates Figure 2 with KDE-based genesis density maps.

**Key Features**:
- Implements Hoskins & Hodges (2005) KDE methodology
- Uses scikit-learn KernelDensity with haversine metric
- Cartopy for map projections and geographic features
- Normalized density (cyclones/area/time)
- Consistent colormap across panels for comparison

**Dependencies**:
- pandas, numpy, matplotlib
- cartopy (map projections)
- sklearn.neighbors.KernelDensity

---

## Color Scheme

Following Scientific Reports standards for colorblind-friendly palettes:

### Energy Patterns
- **EP1**: Blue (#1f77b4)
- **EP2**: Orange (#ff7f0e)
- **EP3**: Green (#2ca02c)

### Seasons
- **Summer (DJF)**: Red (#e74c3c)
- **Autumn (MAM)**: Orange (#f39c12)
- **Winter (JJA)**: Blue (#3498db)
- **Spring (SON)**: Green (#2ecc71)

### Density Maps
- **Colormap**: YlOrRd (Yellow-Orange-Red)
- **Purpose**: Intuitive hot-spot identification
- **Range**: 0 to 95th percentile (extended beyond)

---

## Figure Specifications

Both figures meet **Scientific Reports** requirements:

- **Resolution**: 300 DPI
- **Format**: PNG with white background
- **Font**: Arial/Helvetica sans-serif
- **Font sizes**: 
  - Axis labels: 10-11 pt (bold)
  - Titles: 11-12 pt (bold)
  - Tick labels: 9-10 pt
  - Legend: 9 pt
- **Panel labels**: (a), (b), (c), (d) in bold, top-left position
- **Line weights**: 1.0-2.5 pt (depending on element)
- **Grid**: Subtle gray dashed lines (alpha=0.3)

---

## References

**Hoskins, B. J., & Hodges, K. I. (2005).** A new perspective on Southern Hemisphere storm tracks. *Journal of Climate*, 18(20), 4108-4129. https://doi.org/10.1175/JCLI3570.1

---

## Usage

To regenerate figures:

```bash
# Activate environment
source activate.sh

# Generate Figure 1
python scripts/main/figure_intensity_seasonality_trends.py

# Generate Figure 2
python scripts/main/figure_genesis_density_kde.py
```

Both scripts will save outputs to `figures/main/` directory.
