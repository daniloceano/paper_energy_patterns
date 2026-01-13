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

---

### 2. ERA5 Data Acquisition
Download ERA5 reanalysis data for the selected cases covering **only the intensification phase**:

**Required Variables**:
- **3D Fields** (multiple pressure levels):
  - Zonal wind (u)
  - Meridional wind (v)
  - Temperature (T)
  - Geopotential height (Z)
  
- **Pressure Levels**:
  - Standard levels: 1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100 hPa

**Spatial Coverage Strategy**:
- **Single domain per cyclone**: Download one domain large enough to accommodate all analysis scales
- **Domain size**: Track extent during intensification phase + 15° buffer on all sides
- **Rationale**: This buffer allows for 30°×30° analysis (largest domain) while reusing the same data for smaller domains (5°×5° and 15°×15°)
- **Efficiency**: Avoids redundant downloads of nested domains

**Temporal Coverage**:
- **Only intensification phase** of each cyclone (all time steps)
- 6-hourly data
- **Central time step** identified for instability analysis

**Note**: This step should be run on a remote server with good internet connection and storage capacity.

---

### 3. Vertical Distribution of Energy Conversions

Compute Ca and Ck at each pressure level for the intensification phase of selected cyclones using the Lorenz Energy Cycle framework adapted for pressure levels.

**Analysis**:
- Identify levels of maximum positive Ca (strongest baroclinic conversion)
- Identify levels of maximum negative Ck (strongest barotropic conversion)
- Create vertical profiles showing Ca(p) and Ck(p) for each cyclone
- Compute ensemble mean and spread across the 10 cases

**Physical Interpretation**:
- **Ca maximum**: Level of maximum baroclinic energy conversion, typically associated with the level of maximum temperature gradient
- **Ck maximum**: Level of maximum barotropic energy conversion, typically associated with horizontal wind shear and momentum flux convergence

**Output**: Vertical profiles and identification of critical levels

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
scripts/ep1_vertical_analysis/
├── README.md                           # This file
├── step1_select_cases.py              # Case selection (10 most intense EP1 cyclones)
├── step2_download_era5.py             # ERA5 data download (run on server)
├── step3_vertical_levels_analysis.py  # Compute Ca/Ck vertical profiles
├── step4_compute_instabilities.py     # Calculate RK and EGR
├── step5_create_figures.py            # Generate all figures
└── run_all.py                         # Sequential execution of all steps
```

## Data Requirements

### Input
- `results/cluster/kmeans_clustered_data.csv`: EP1 cyclone classifications
- `data/tracks_SAt_filtered_with_energetics_processed.csv`: Track and energy data
- ERA5 reanalysis data (downloaded by step2)

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
