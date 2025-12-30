# Energy Pattern Characteristics Analysis

This directory contains exploratory analyses of Energy Pattern (EP) characteristics following Scientific Reports standards.

## Analyses Performed

### 1. Seasonality Analysis
**File:** `seasonality.png`

Examines the temporal distribution of Energy Patterns throughout the year:
- **Monthly distribution** (top panel): Stacked bar chart showing cyclone counts per month for each EP
- **Seasonal distribution** (bottom panels): Pie charts for each EP showing the percentage in each season (Summer/DJF, Autumn/MAM, Winter/JJA, Spring/SON)
- **Overall statistics**: Summary of seasonal distribution across all cyclones

**Key Findings:**
- **EP1**: Dominant in Winter (35.6%)
- **EP2**: Dominant in Spring (27.5%)
- **EP3**: Dominant in Summer (30.9%)

### 2. Genesis Regions Analysis
**File:** `genesis_regions.png`

Maps showing where cyclones of each Energy Pattern form, using **Kernel Density Estimation (KDE)** following **Hoskins and Hodges (2005)** methodology to identify regions of preferential cyclogenesis.

#### Methodology - Hoskins and Hodges (2005) KDE

This analysis uses the established methodology from Hoskins and Hodges (2005) for computing track density:

**Technical Implementation:**
1. **Global grid**: 2.5° resolution (128×64 lon×lat), spanning -180° to 180° longitude and -87.863° to 87.863° latitude
2. **Kernel**: Gaussian kernel with haversine metric (accounts for spherical Earth geometry)
3. **Bandwidth**: 0.05 radians (~555 km at mid-latitudes)
4. **Algorithm**: Ball tree for efficient nearest-neighbor searches
5. **Normalization**: 
   - Scaled by total number of cyclones
   - Divided by Earth's surface area (R² where R = 6369 km at 40°S)
   - Divided by time period (42 years: 1979-2020)
   - Final units: **cyclones per 10⁶ km² per year**

**Scientific Rationale:**
- **Haversine metric**: Uses great-circle distance on sphere, appropriate for global atmospheric phenomena
- **Gaussian smoothing**: Bandwidth of ~555 km balances between:
  * Too small → noise from individual genesis events
  * Too large → loss of regional patterns
- **Spherical geometry**: Correctly handles latitude-dependent area distortion
- **Temporal normalization**: Allows comparison across different time periods

**Advantages over simple point plots:**
1. Reveals underlying probability density function of genesis locations
2. Smooths random spatial variability to show systematic patterns
3. Identifies regions of preferential cyclogenesis quantitatively
4. Provides density values for statistical comparison
5. Established methodology used in major climatological studies

#### Panel Description:
- **Top-left map**: Composite KDE for all EPs showing overlapping genesis regions
  - Contour lines show density levels (50th, 75th, 90th, 95th percentiles)
  - Colored filled contours with transparency show spatial extent of each EP
  - Density units: **cyclones per 10⁶ km² per year**
  
- **Middle row**: Individual EP density maps with colorbar
  - Filled contours show full density distribution (YlOrRd colormap)
  - Black contour lines mark density levels for reference
  - Colorbar shows absolute density values
  - Maximum density annotated in title

- **Top-right panel**: Regional composition by Energy Pattern
  - Shows which regions (SE-BR, LA-PLAT, ARG) contribute to each EP
  - Green = SE-BR (Southeast Brazil)
  - Yellow = LA-PLAT (La Plata region)
  - Blue = ARG (Argentina)

- **Bottom row**: Energy Pattern proportion within each region (pie charts)
  - Three pies showing EP distribution for SE-BR, LA-PLAT, and ARG regions
  - Reveals regional preferences for specific energy patterns

**Key Findings:**
- **EP1**: Median genesis at (-60.4°, -42.1°) - Further south, concentrated near Argentina coast
  - Maximum density: ~3.9 cyclones/10⁶ km²/year
  - Most concentrated spatial distribution
- **EP2**: Median genesis at (-60.6°, -37.9°) - Middle latitudes, broader spatial distribution
  - Maximum density: ~23.7 cyclones/10⁶ km²/year (highest)
  - Extends further offshore and equatorward
- **EP3**: Median genesis at (-61.3°, -44.0°) - Southernmost, most concentrated density
  - Maximum density: ~6.9 cyclones/10⁶ km²/year
  - Intermediate spatial extent

**Regional Patterns:**
- All EPs show genesis concentrated in southwestern Atlantic
- ARG region (blue) dominates genesis for all patterns
- Subtle latitudinal shifts between EPs visible in KDE contours
- Density gradients suggest orographic and SST gradient influences

### 3. Interannual Variability Analysis
**File:** `interannual_variability.png`

Time series analysis from 1979 to present with statistical trend detection.

**Panels:**
- **Absolute counts** (top panel): Stacked area chart showing annual cyclone counts per EP
- **Relative frequency** (bottom panel): Line plot showing percentage of each EP over time with **Mann-Kendall trend analysis**

#### Trend Analysis Methodology
**Mann-Kendall test** is a non-parametric statistical test used to detect monotonic trends in time series data. Unlike linear regression, it:
- **Requires no assumption of normality**: Works with any distribution
- **Robust to outliers**: Not influenced by extreme values
- **Detects monotonic trends**: Identifies consistent increasing or decreasing patterns

**Sen's slope estimator** quantifies the magnitude of trends (used for trend lines in the figure).

**Interpretation:**
- **Solid trend lines**: Statistically significant (p < 0.05)
- **Dashed trend lines**: Non-significant trends
- **Arrows**: ↑ (increasing), ↓ (decreasing), → (no trend)
- **Asterisk (*)**: Marks significant trends

**Key Findings:**
- **EP1**: No significant trend (p = 0.626, τ = -0.053)
  - Relatively stable occurrence throughout the period
  - Interannual std = 3.1 cyclones/year (lowest variability)

- **EP2**: Significant increasing trend (p = 0.035, τ = 0.228)*
  - Moderate baroclinic patterns becoming more frequent
  - Interannual std = 5.2 cyclones/year

- **EP3**: Significant decreasing trend (p = 0.044, τ = -0.217)*
  - Weak baroclinic patterns becoming less frequent
  - Interannual std = 7.0 cyclones/year (highest variability)

**Climate Change Implications:**
The opposing trends in EP2 (increasing) and EP3 (decreasing) suggest a systematic shift in cyclone energetics over the 1979-present period, potentially related to:
- Changes in meridional temperature gradients
- Shifts in baroclinic zone position
- Variations in large-scale circulation patterns (SAM, ENSO)

### 4. Intensity Relationship Analysis
**File:** `intensity_relationship.png`

Examines relationship between Energy Pattern and maximum cyclone intensity (measured by vorticity):
- **Box plots** (left panel): Distribution statistics with median, quartiles, outliers
- **Violin plots** (right panel): Full probability density distribution

**Key Findings:**
- **EP2 has highest mean intensity**: 9.34 ± 2.40 × 10⁻⁵ s⁻¹
- **EP1 has moderate intensity**: 8.81 ± 2.47 × 10⁻⁵ s⁻¹
- **EP3 has lowest intensity**: 6.37 ± 2.41 × 10⁻⁵ s⁻¹

**Interpretation:** Strong baroclinic conversion (EP1) doesn't necessarily mean strongest cyclones. EP2 (moderate baroclinic) produces the most intense cyclones on average, suggesting optimal balance between energy sources.

## Summary Statistics

**File:** `summary_statistics.csv`

Comprehensive table with all key metrics:

| Energy Pattern | N Cyclones | % of Total | Dominant Season | Mean Max Vorticity | Median Genesis | Interannual Std |
|----------------|------------|------------|-----------------|-------------------|----------------|-----------------|
| EP1            | 444        | 11.6%      | Winter (35.6%)  | 8.81 ± 2.47       | (-60.4°, -42.1°) | 3.1 |
| EP2            | 979        | 25.6%      | Spring (27.5%)  | 9.34 ± 2.40       | (-60.6°, -37.9°) | 5.2 |
| EP3            | 2397       | 62.7%      | Summer (30.9%)  | 6.37 ± 2.41       | (-61.3°, -44.0°) | 7.0 |

## Scientific Insights

### Energy-Intensity Relationship
The analysis reveals an interesting pattern:
- **EP1** has strong baroclinic energy conversion (mean Ck = -16.48 W/m²)
- But **EP2** produces the most intense cyclones (mean max vorticity = 9.34)
- This suggests that moderate baroclinic forcing with balanced energy pathways may be optimal for cyclone intensification
- **EP3** (weak baroclinic) produces weakest cyclones despite being most frequent

### Seasonal Patterns
- **EP1 (Winter-dominant)**: Associated with stronger meridional temperature gradients
- **EP2 (Spring-dominant)**: Transition season with balanced conditions
- **EP3 (Summer-dominant)**: Weaker baroclinic forcing, more barotropic dynamics

### Spatial Distribution (KDE Analysis)
Genesis density analysis reveals:
- **Primary cyclogenesis zone**: Southwestern Atlantic near Argentina coast (~60°W, 40-45°S)
- **Latitudinal preferences**: 
  - EP1 and EP3: More concentrated at higher latitudes (~42-44°S)
  - EP2: Slightly more northern (~38°S), broader spatial extent
- **Density gradients**: Suggest influence of:
  - Orographic forcing from Andes Mountains
  - SST gradients (Brazil-Malvinas Confluence)
  - Upper-level jet stream position

### Temporal Trends (Mann-Kendall Analysis)
**Significant findings over 1979-present:**
- **EP1**: No significant trend (stable throughout period)
- **EP2**: Significant increasing trend (p = 0.035, τ = 0.228)*
  - Moderate baroclinic patterns becoming more prevalent
  - May indicate shift in optimal conditions for cyclogenesis
- **EP3**: Significant decreasing trend (p = 0.044, τ = -0.217)*
  - Weak baroclinic patterns becoming less frequent
  - Compensates for EP2 increase

**Climate Change Context:**
### Color Scheme (Scientific Reports compliant)
- **Energy Patterns**: EP1 (Blue #1f77b4), EP2 (Orange #ff7f0e), EP3 (Green #2ca02c)
- **Seasons**: Summer (Red), Autumn (Orange), Winter (Blue), Spring (Green)
- **Regions**: SE-BR (Green), LA-PLAT (Yellow), ARG (Blue)

### Statistical Methods
1. **Kernel Density Estimation (Hoskins & Hodges 2005)**:
   - Gaussian kernel with haversine metric
   - Bandwidth: 0.05 radians (~555 km)
   - Global grid: 2.5° resolution (128×64)
   - Units: cyclones per 10⁶ km² per year
   - Accounts for spherical Earth geometry
   - Established methodology used in major climatological studies

2. **Mann-Kendall Trend Test**:
   - Non-parametric test for monotonic trends
   - Null hypothesis: No trend exists
   - Significance level: α = 0.05
   - Sen's slope estimator for trend magnitude
   - Tau statistic quantifies trend strength (-1 to +1)

3. **Statistical Significance**:
   - Solid trend lines: p < 0.05 (significant)
   - Dashed lines: p ≥ 0.05 (non-significant)
   - Confidence: 95% for all tests
   - Modulation by large-scale climate modes (SAM, ENSO)
3. **Implications**: Cyclones may be transitioning toward more moderate energy conversion patterns with higher intensification potential

## Methodology

### Data Sources
- **Energy Pattern assignments**: From K-Means clustering of PCA-reduced energy budget terms
- **Track data**: From `tracks_SAt_filtered_with_periods.csv` (6789 cyclones, 1979-present)
- **Genesis**: First observation time for each cyclone
- **Maximum intensity**: Peak vorticity (vor42) during cyclone lifetime

### Analysis Period
- 1979 to present (based on available track data)
- All seasons included
- South Atlantic region focus

### Color Scheme (Scientific Reports compliant)
- **EP1**: Blue (#1f77b4)
- **EP2**: Orange (#ff7f0e)
- **EP3**: Green (#2ca02c)
- **Seasons**: Red (Summer), Orange (Autumn), Blue (Winter), Green (Spring)

### Map Projection
- PlateCarree (equirectangular)
- Extent: 80°W-20°W, 60°S-20°S
- Resolution: 50m coastlines
- Features: Land (lightgray), Ocean (lightblue)

## Script

Generated by: `scripts/exploratory/analyze_ep_characteristics.py`

## Future Analyses

Potential extensions:
1. **ENSO/SAM influence**: Correlation with climate indices
2. **Track characteristics**: Duration, propagation speed, trajectory patterns
3. **Environmental conditions**: SST, wind shear, moisture availability
4. **Socioeconomic impacts**: Correlation with damage reports, precipitation
5. **Future projections**: Application to climate model outputs

## References

- Energy Pattern definitions: See `ENERGY_PATTERNS.md`
- Clustering methodology: See `scripts/cluster/README.md`
- Track data description: See `data/DATA_STRUCTURE.md`
