# Scientific Notes: EP1 Full Cyclones Analysis

## Overview

This document presents the scientific methodology and results for the complete analysis
of ALL Energy Pattern 1 (EP1) cyclones during their entire intensification phase.

**Key Differences from Subset Analysis (`ep1_ibc_ibt_analysis`):**
- Sample size: ALL EP1 cyclones vs. 94 selected cases
- Temporal coverage: ALL intensification timesteps vs. temporal center only
- Spatial coverage: All EP1 regions vs. specific spatial domain (60°W-45°W, 45°S-30°S)

**Generated:** AUTO-FILLED BY `update_scientific_notes.py`

---

## 1. Dataset Characteristics

### 1.1 Sample Composition

**Total cases analyzed:** {N_CASES}

**Temporal statistics:**
- Mean intensification duration: {MEAN_DURATION:.1f} hours
- Total timesteps analyzed: {TOTAL_TIMESTEPS}
- Mean timesteps per case: {MEAN_TIMESTEPS:.1f}

**Spatial distribution:**
- Latitude range: [{LAT_MIN:.1f}°, {LAT_MAX:.1f}°]
- Longitude range: [{LON_MIN:.1f}°, {LON_MAX:.1f}°]
- Primary genesis region: {GENESIS_REGION}

### 1.2 Data Sources

**ERA5 Reanalysis Variables:**
- Pressure levels: u, v, t, z, q
- Single level: msl (Mean Sea Level Pressure)
- Temporal resolution: 6-hourly
- Spatial resolution: 0.25° × 0.25°
- **Pressure levels (targeted)**: 1000, 975, 950, 400, 350, 300, 250 hPa

**Vertical Level Selection:**

Preliminary analysis (see `ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py`) identified critical levels for EP1 cyclones:

- **Maximum Ca (baroclinic conversion)**: 975 hPa
  - Download levels: 1000, 975, 950 hPa (center + adjacent for vertical derivatives)
  
- **Minimum Ck (barotropic conversion)**: 350 hPa  
  - Download levels: 400, 350, 300 hPa (center + adjacent for vertical derivatives)
  
- **Upper-level jet**: 250 hPa
  - For PV structure and wind vector overlays in visualization

This targeted approach reduces data volume from 14 levels to **7 levels** while preserving all necessary information for instability diagnostics.

> 📖 **Detailed vertical level documentation**: See `VERTICAL_LEVELS.md` in this directory for comprehensive rationale, efficiency comparison, and diagnostic requirements.

---

## 2. Methodology

### 2.1 Baroclinic Instability: Eady Growth Rate

**Formula:**
$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

**Components:**
- Coriolis parameter: $f = 2\Omega \sin(\phi)$
- Brunt-Väisälä frequency: $N^2 = \frac{g}{\theta_v} \frac{\partial \theta_v}{\partial z}$
- Vertical wind shear: $|\partial \vec{V}/\partial z| = \sqrt{(\partial u/\partial z)^2 + (\partial v/\partial z)^2}$

**Computational level:** 975 hPa (identified as maximum Ca level for EP1 cyclones)

**Vertical derivative calculation:** Uses 950, 975, 1000 hPa levels

**Physical interpretation:**
- > 1.0 day⁻¹: Strong baroclinic instability (favorable for cyclogenesis)
- 0.5-1.0 day⁻¹: Moderate instability
- < 0.5 day⁻¹: Weak instability

### 2.2 Barotropic Instability: Rayleigh-Kuo Criterion

**Criterion:** Necessary condition for barotropic instability

$$\frac{\partial}{\partial y}(\zeta + f) \text{ changes sign in domain}$$

where:
- $\zeta$ = relative vorticity
- $f$ = Coriolis parameter
- $\eta = \zeta + f$ = absolute vorticity

**Computational level:** 350 hPa (identified as minimum Ck level for EP1 cyclones)

**Note:** 250 hPa data also downloaded for upper-level jet visualization

**Physical interpretation:**
- Sign change of $\partial \eta/\partial y$ is **necessary** but not sufficient for barotropic instability
- Indicates potential for lateral shear instability in upper-level jet
- Frequent satisfaction suggests favorable conditions for cyclone intensification via upper-level dynamics

### 2.3 Multi-Scale Analysis

**Domains:**
- **Local (5° × 5°)**: Core cyclone structure
- **Mesoscale (15° × 15°)**: Regional environment
- **Synoptic (30° × 30°)**: Large-scale circulation

**Purpose:** Assess scale-dependence of instability processes

---

## 3. Results

### 3.1 Eady Growth Rate Statistics

#### Local Domain (5° × 5°)
- **Mean EGR:** {EGR_LOCAL_MEAN:.2f} ± {EGR_LOCAL_STD:.2f} day⁻¹
- **Median EGR:** {EGR_LOCAL_MEDIAN:.2f} day⁻¹
- **Range:** [{EGR_LOCAL_MIN:.2f}, {EGR_LOCAL_MAX:.2f}] day⁻¹
- **Interpretation:** {EGR_LOCAL_INTERP}

#### Mesoscale Domain (15° × 15°)
- **Mean EGR:** {EGR_MESO_MEAN:.2f} ± {EGR_MESO_STD:.2f} day⁻¹
- **Median EGR:** {EGR_MESO_MEDIAN:.2f} day⁻¹
- **Range:** [{EGR_MESO_MIN:.2f}, {EGR_MESO_MAX:.2f}] day⁻¹
- **Interpretation:** {EGR_MESO_INTERP}

#### Synoptic Domain (30° × 30°)
- **Mean EGR:** {EGR_SYNOP_MEAN:.2f} ± {EGR_SYNOP_STD:.2f} day⁻¹
- **Median EGR:** {EGR_SYNOP_MEDIAN:.2f} day⁻¹
- **Range:** [{EGR_SYNOP_MIN:.2f}, {EGR_SYNOP_MAX:.2f}] day⁻¹
- **Interpretation:** {EGR_SYNOP_INTERP}

### 3.2 Rayleigh-Kuo Criterion Statistics

**Satisfaction frequency (% of all timesteps):**

| Domain | 2D Field | Zonal Mean | Interpretation |
|--------|----------|------------|----------------|
| Local | {RK_LOCAL_2D:.1f}% | {RK_LOCAL_ZM:.1f}% | {RK_LOCAL_INTERP} |
| Mesoscale | {RK_MESO_2D:.1f}% | {RK_MESO_ZM:.1f}% | {RK_MESO_INTERP} |
| Synoptic | {RK_SYNOP_2D:.1f}% | {RK_SYNOP_ZM:.1f}% | {RK_SYNOP_INTERP} |

### 3.3 Temporal Evolution

**Mean evolution during intensification phase:**

![EGR Evolution](../figures/ep1_full/timeseries/timeseries_mesoscale.png)

**Key findings:**
- {TEMPORAL_FINDING_1}
- {TEMPORAL_FINDING_2}
- {TEMPORAL_FINDING_3}

### 3.4 Composite Structure

**Spatial patterns (mesoscale domain):**

**Baroclinic PV:**
![PV Composite](../figures/ep1_full/composite/pv_composite_mesoscale.png)

- **975 hPa PV:** {PV_975_PATTERN}
- **250 hPa PV:** {PV_250_PATTERN}
- **Jet structure:** {JET_PATTERN}

**Eady Growth Rate + SLP:**
![EGR Composite](../figures/ep1_full/composite/egr_composite_mesoscale.png)

- **EGR spatial pattern:** {EGR_PATTERN}
- **SLP pattern:** {SLP_PATTERN}
- **Low-level circulation (975 hPa):** {WIND_975_PATTERN}

---

## 4. Physical Interpretation

### 4.1 Baroclinic Instability Characteristics

{BAROCLINIC_INTERPRETATION}

### 4.2 Barotropic Instability Role

{BAROTROPIC_INTERPRETATION}

### 4.3 Scale Dependence

{SCALE_DEPENDENCE}

### 4.4 Comparison with Subset Analysis

**EP1 subset (94 cases, spatial filter):**
- Mean EGR (mesoscale): {SUBSET_EGR_MESO:.2f} day⁻¹
- RK satisfaction (mesoscale): {SUBSET_RK_MESO:.1f}%

**EP1 full (all cases, all times):**
- Mean EGR (mesoscale): {EGR_MESO_MEAN:.2f} day⁻¹
- RK satisfaction (mesoscale): {RK_MESO_2D:.1f}%

**Differences:**
{COMPARISON_ANALYSIS}

---

## 5. Implications

### 5.1 Cyclone Intensification Mechanisms

{INTENSIFICATION_MECHANISMS}

### 5.2 Energy Pattern 1 Characteristics

{EP1_CHARACTERISTICS}

### 5.3 Predictability Considerations

{PREDICTABILITY}

---

## 6. Computational Notes

### 6.1 Quality Control

**Applied thresholds:**
- Minimum |latitude| = 5° (avoid equatorial singularity in f)
- Maximum EGR = 5.0 day⁻¹ (cap unphysical values)
- Minimum N² = 1.0×10⁻⁶ s⁻² (ensure stable stratification)

**Data completeness:**
- Cases with complete data: {COMPLETE_CASES_PCT:.1f}%
- Timesteps with valid EGR: {VALID_EGR_PCT:.1f}%
- Timesteps with valid RK: {VALID_RK_PCT:.1f}%

### 6.2 Parallelization Performance

**Download step (step2):**
- Workers used: {N_WORKERS}
- Total download time: {DOWNLOAD_TIME:.1f} hours
- Average per case: {DOWNLOAD_PER_CASE:.1f} minutes

**Computation step (step4):**
- Processing time: {COMPUTE_TIME:.1f} hours
- Average per case: {COMPUTE_PER_CASE:.1f} minutes

---

## 7. References

1. Eady, E. T. (1949). Long waves and cyclone waves. *Tellus*, 1(3), 33-52.

2. Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *Journal of Meteorology*, 6(2), 105-122.

3. Rayleigh, Lord. (1880). On the stability, or instability, of certain fluid motions. *Proceedings of the London Mathematical Society*, 1(1), 57-72.

4. Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Quarterly Journal of the Royal Meteorological Society*, 111(470), 877-946.

5. Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *Journal of the Atmospheric Sciences*, 37(7), 1648-1654.

---

**Document auto-generated:** {GENERATION_DATE}  
**Analysis period:** {ANALYSIS_PERIOD}  
**Contact:** Danilo Couto de Souza  
**Institution:** {INSTITUTION}
