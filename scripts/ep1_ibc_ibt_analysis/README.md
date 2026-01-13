# EP1 Vertical Structure and Instability Analysis

## Scientific Motivation

The Energy Pattern 1 (EP1) represents cyclones with the most intense energetic conversions in the Southwestern Atlantic, characterized by strong barotropic and baroclinic processes. These systems exhibit:

- **Mean Ck**: -16.48 W/m² (strongest barotropic conversion)
- **Frequency**: 444 cyclones (11.6% of total)
- **Characteristics**: Dominated by intense energy conversions from both available potential energy (APE) to kinetic energy (KE)

Understanding the vertical structure and mechanisms driving these intense energy conversions is crucial for:
1. Identifying the atmospheric levels where barotropic and baroclinic processes are most active
2. Diagnosing the physical mechanisms responsible for cyclone intensification
3. Distinguishing between local versus large-scale instability processes

## Research Questions

1. **At which atmospheric levels do the maximum/minimum values of Ca and Ck occur during EP1 cyclones?**
   - Ca (baroclinic conversion): Az → Ae, related to baroclinic instability
   - Ck (barotropic conversion): Ke → Kz, related to barotropic instability

2. **Are barotropic and baroclinic instabilities present during the intensification phase?**
   - Barotropic instability: Diagnosed through the Rayleigh-Kuo (RK) criterion
   - Baroclinic instability: Diagnosed through the Eady Growth Rate (EGR)

3. **Is barotropic instability a local or large-scale phenomenon in EP1 cyclones?**
   - Compare RK criterion across three spatial domains: 5°×5°, 15°×15°, and 30°×30°
   - Hypothesis: Barotropic instability is locally concentrated around the cyclone center

## Methodology

### 1. Case Selection
Select the 10 most intense cyclones from EP1 based on:
- Maximum vorticity during mature phase
- Strong energy conversion signatures (Ca and Ck)
- Data availability for the intensification phase

**Output**: List of selected track IDs with justification

**Script**: `step1_select_cases.py`

---

### 2. Vertical Distribution Analysis (LEC Data)

**IMPORTANT**: This step is now performed BEFORE downloading ERA5 data to optimize the download.

Analyze existing LEC (Lorenz Energy Cycle) results from `data/lec_results/` to identify critical pressure levels:

**Analysis**:
- Load `Ca_level.csv` and `Ck_level.csv` for each selected cyclone
- Extract data during intensification phase only
- Compute mean vertical profiles of Ca(p) and Ck(p)
- Identify pressure level with maximum Ca (baroclinic conversion)
- Identify pressure level with minimum Ck (barotropic conversion)
- Create boxplots showing distribution across all 10 cases
- Determine median levels for download

**Physical Interpretation**:
- **Ca maximum**: Level of maximum baroclinic energy conversion, typically associated with the level of maximum temperature gradient
- **Ck maximum**: Level of maximum barotropic energy conversion, typically associated with horizontal wind shear and momentum flux convergence

**Output**: 
- Critical pressure levels (median across cases)
- Boxplots showing distribution
- List of levels to download (including ±1 level for vertical derivatives)

**Script**: `step3_vertical_levels_analysis.py`

---

### 3. ERA5 Data Acquisition

Download ERA5 reanalysis data ONLY for the identified critical pressure levels, covering **only the intensification phase**:

**Required Variables**:
- **u_component_of_wind**: Zonal wind (for vorticity in RK, wind shear in EGR)
- **v_component_of_wind**: Meridional wind (for vorticity in RK, wind shear in EGR)
- **temperature**: Temperature (for Brunt-Väisälä frequency in EGR)
- **geopotential**: Geopotential height (for vertical derivatives in EGR)

**Pressure Levels**:
- Level of Ca maximum ± 1 level (for centered finite differences in EGR)
- Level of Ck minimum ± 1 level (for RK criterion analysis)

**Rationale**: 
- Instead of downloading all 21 pressure levels, download only ~3-6 levels needed
- Saves significant download time and storage space
- EGR requires vertical derivatives, hence ±1 level for centered differences

**Spatial Coverage Strategy**:
- **Single domain per cyclone**: Track extent during intensification phase + 15° buffer on all sides
- **Rationale**: This buffer allows for 30°×30° analysis (largest domain) while reusing the same data for smaller domains (5°×5° and 15°×15°)
- **Efficiency**: Avoids redundant downloads of nested domains

**Temporal Coverage**:
- **Only intensification phase** of each cyclone (all time steps)
- 6-hourly data
- **Central time step** identified for instability analysis

**Note**: This step should be run on a remote server with good internet connection and storage capacity. Requires CDS API credentials.

**Script**: `step2_download_era5.py`

---

### 4. Instability Diagnostics

#### 4.1 Rayleigh-Kuo (RK) Criterion for Barotropic Instability

The Rayleigh-Kuo criterion states that barotropic instability occurs when the meridional gradient of absolute vorticity changes sign within the domain:

$$\frac{\partial \eta}{\partial y} < 0$$

where $\eta = \zeta + f$ is the absolute vorticity ($\zeta$ = relative vorticity, $f$ = Coriolis parameter).

**Application**:
- Compute at the pressure level where Ck is maximum
- Apply to three domains: 5°×5°, 15°×15°, 30°×30° (extracted from single downloaded domain)
- **Analysis time**: Central time step of intensification phase for each cyclone
- Identify regions where the criterion is satisfied
- Create individual maps for each cyclone
- Generate composite (ensemble mean) across all cases

**Hypothesis**: Barotropic instability is a local phenomenon, strongest in the 5°×5° domain and weakening at larger scales.

---

#### 4.2 Eady Growth Rate (EGR) for Baroclinic Instability

The Eady Growth Rate quantifies the growth rate of baroclinic waves:

$$\sigma_{EGR} = 0.31 \frac{f}{N} \left|\frac{\partial U}{\partial z}\right|$$

where:
- $f$ = Coriolis parameter
- $N$ = Brunt-Väisälä frequency (static stability)
- $\frac{\partial U}{\partial z}$ = vertical wind shear

**Application**:
- Compute at the pressure level where Ca is maximum
- Apply to three domains: 5°×5°, 15°×15°, 30°×30° (extracted from single downloaded domain)
- **Analysis time**: Central time step of intensification phase for each cyclone
- Calculate domain-averaged EGR for each case
- Create spatial maps showing EGR distribution
- Generate individual maps for each cyclone
- Generate composite (ensemble mean) across all cases

**Physical Interpretation**: Higher EGR values indicate stronger baroclinic instability and potential for rapid cyclone intensification.

---

### 5. Visualization and Comparison

#### 5.1 Vertical Structure Figures
- Vertical profiles of Ca and Ck for each cyclone
- Ensemble mean with uncertainty bands
- Highlight critical levels

#### 5.2 Cyclone Tracks
- **Overview map**: All 10 tracks plotted together
  - Complete track shown (all phases)
  - Intensification phase highlighted (thicker line, different color)
  - Genesis points marked
- **Individual maps**: One map per cyclone showing:
  - Complete track with intensification highlighted
  - Analysis domains overlaid (5°×5°, 15°×15°, 30°×30°)
  - Central time step of intensification marked
  - Downloaded domain extent shown

#### 5.3 Multi-Domain RK Comparison
- **Composite figure**: Ensemble mean across all cyclones
  - Three-panel layout (5°×5°, 15°×15°, 30°×30°)
  - Color-coded regions satisfying RK criterion
  - Statistical summary for each domain
- **Individual figures**: One per cyclone (10 figures)
  - Three-panel layout showing scale dependency
  - Cyclone center marked
  - Analysis at central time step of intensification

#### 5.4 Multi-Domain EGR Maps
- **Composite figure**: Ensemble mean across all cyclones
  - Three-panel layout (5°×5°, 15°×15°, 30°×30°)
  - Spatial distribution of EGR
  - Domain-averaged values annotated
- **Individual figures**: One per cyclone (10 figures)
  - Three-panel layout showing scale dependency
  - Cyclone center marked
  - Analysis at central time step of intensification

---

## Expected Results

1. **Vertical Structure**: 
   - Ca maximum expected in mid-troposphere (500-700 hPa)
   - Ck maximum expected in upper-troposphere (300-500 hPa) or near surface

2. **Barotropic Instability**:
   - RK criterion satisfied locally (5°×5°) around cyclone center
   - Signal weakens at larger scales (15°×15°, 30°×30°)
   - Confirms local nature of barotropic processes

3. **Baroclinic Instability**:
   - High EGR values during intensification phase
   - Maximum in regions of strong temperature gradients
   - Consistent across different domain sizes (large-scale phenomenon)

---

## Physical Interpretation

This analysis aims to demonstrate that EP1 cyclones are characterized by:

1. **Multi-level energetic structure**: Different conversion processes dominate at different atmospheric levels
2. **Local barotropic instability**: Concentrated around the cyclone center, contributing to rapid intensification through horizontal momentum convergence
3. **Large-scale baroclinic instability**: Driven by synoptic-scale temperature gradients, providing the initial energy source for development

The combination of these processes explains why EP1 cyclones have the strongest energetic conversions and why they represent the most dynamically active systems in the Southwestern Atlantic.

---

## Directory Structure

```
scripts/ep1_ibc_ibt_analysis/
├── README.md                           # This file
├── step1_select_cases.py              # Case selection (10 most intense EP1 cyclones)
├── step2_vertical_levels_analysis.py  # Analyze LEC data to identify critical levels
├── step3_download_era5.py             # ERA5 data download at identified levels (run on server)
├── step4_compute_instabilities.py     # Calculate RK and EGR
├── step5_create_figures.py            # Generate all figures
└── run_all.py                         # Sequential execution of all steps
```

**Execution Order**:
1. `step1_select_cases.py` - Select 10 most intense EP1 cyclones
2. `step2_vertical_levels_analysis.py` - Analyze existing LEC data to identify critical levels
3. `step3_download_era5.py` - Download ERA5 data at identified levels (requires CDS API)
4. `step4_compute_instabilities.py` - Compute RK and EGR diagnostics
5. `step5_create_figures.py` - Generate all publication figures

## Data Requirements

### Input
- `results/cluster/kmeans_clustered_data.csv`: EP1 cyclone classifications
- `data/tracks_SAt_filtered_with_energetics_processed.csv`: Track and energy data
- ERA5 reanalysis data (downloaded by step3)

### Output
- `results/ep1_vertical/`: Numerical results (vertical profiles, statistics)
- `figures/ep1_vertical/`: Publication-quality figures

---

## References

### Instability Theory
- **Rayleigh-Kuo Criterion**: Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *Journal of Meteorology*, 6(2), 105-122.
- **Eady Growth Rate**: Eady, E. T. (1949). Long waves and cyclone waves. *Tellus*, 1(3), 33-52.

### Energy Cycle
- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.

---

## Notes

- This analysis focuses exclusively on EP1 cyclones (most energetically active)
- All diagnostics are computed during the **intensification phase** when energy conversions are most active
- Multi-domain comparison (5°×5°, 15°×15°, 30°×30°) allows scale-dependent analysis
- Results will be compared with EP2 and EP3 in future work to understand what makes EP1 unique
