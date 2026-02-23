# Scientific Notes: Spatial Structure Analysis of Energy Patterns

**Objective:** Investigate the spatial structure and dynamical characteristics of Energy Pattern 1 (EP1) and Energy Pattern 2 (EP2) cyclones during intensification phase.

**Author:** Danilo Couto de Souza  
**Date:** February 2026

---

## 1. Introduction

### 1.1 Motivation

Following the identification of three distinct energy patterns in South Atlantic cyclones through PCA-based K-Means clustering (see `cluster_analysis_energy_patterns/SCIENTIFIC_NOTES.md`), this analysis investigates the **spatial structure** of the most energetically active patterns.

**Energy Pattern Characteristics** (from cluster analysis):
- **EP1 (11.6%):** Large barotropic and baroclinic conversions; **exports energy** to surroundings
- **EP2 (25.6%):** Moderate balanced conversions; **imports energy** from large-scale environment  
- **EP3 (62.7%):** Weak energetics representing typical "day-to-day" cyclones

**Rationale for EP1 and EP2 focus:**  
EP3 cyclones exhibit weak energy budget activity and represent the climatological background. EP1 and EP2 cyclones, being energetically distinct and more intense, are the primary focus for understanding what structural characteristics differentiate high-impact systems from typical cyclones.

### 1.2 Research Questions

1. What are the spatial structures of baroclinic instability (EGR) in EP1 vs EP2?
2. How do upper-level (200 hPa) and low-level (850 hPa) PV anomalies differ between patterns?
3. What thermal advection patterns characterize each energy pattern?
4. How does near-surface moisture distribution and convergence differ?

**Approach:** Composite analysis of ERA5 reanalysis fields during the intensification phase of all EP1 (N=444) and EP2 (N=979) cyclones.

---

## 2. Dataset

### 2.1 Sample Composition

| Energy Pattern | Cluster ID | Cases Analyzed | Percentage |
|----------------|------------|----------------|------------|
| **EP1** | 0 | 444 | 11.6% |
| **EP2** | 2 | 979 | 25.6% |

**Source:** All EP1 and EP2 cyclones from cluster analysis with complete lifecycle phases.

**Temporal Coverage:** Intensification phase only (6-hourly timesteps during deepening period)

### 2.2 ERA5 Reanalysis Data

**Variables Downloaded:**
- **Pressure levels (hPa):** 175, 200, 225, 250, 500, 825, 850, 875, 975
- **Pressure-level variables:** u, v, t, z, q (winds, temperature, geopotential, specific humidity)
- **Single-level variables:** msl (mean sea level pressure)

**Spatial Configuration:**
- **Resolution:** 0.25° × 0.25°
- **Domain:** 30° × 30° centered on cyclone track center
- **Composite domain:** 15° × 15° (marked in figures)

**Temporal Resolution:** 6-hourly

---

## 3. Methodology

### 3.1 Diagnostic Fields Computed

| Diagnostic | Level(s) | Purpose | Key Reference |
|------------|----------|---------|---------------|
| **Eady Growth Rate** | 250–850 hPa | Baroclinic instability measure | Lindzen & Farrell (1980) |
| **Potential Vorticity** | 200 hPa | Upper-level dynamics, tropopause folding | Hoskins et al. (1985) |
| **Potential Vorticity** | 850 hPa | Low-level PV anomaly, diabatic effects | Čampa & Wernli (2012) |
| **Temperature Advection** | 850 hPa | Warm/cold advection patterns | Sanders & Gyakum (1980) |
| **Specific Humidity** | 975 hPa | Near-surface moisture distribution | - |
| **Moisture Flux Divergence** | 975 hPa | Moisture convergence (convective potential) | Banacos & Schultz (2005) |
| **Sea Level Pressure** | Surface | Cyclone intensity and position | - |
| **RK criterion** (Rayleigh-Kuo) | 250 hPa | Barotropic/baroclinic instability condition | Rayleigh (1880); Kuo (1949) |
| **KE Advection** | 250 hPa | Kinetic energy tendency from advection | - |

### 3.2 Spherical Grid Spacing

All horizontal derivatives account for Earth's spherical geometry:

**Meridional spacing:**
$$dy = R_{\oplus} \Delta\phi$$

**Zonal spacing:**
$$dx = R_{\oplus} \cos(\phi) \Delta\lambda$$

where $R_{\oplus} = 6.371 \times 10^6$ m, $\phi$ = latitude, $\lambda$ = longitude.

**Implementation:** `compute_spherical_grid_spacing(lat_1d, lon_1d)`
- ✅ Verifies coordinate monotonicity  
- ✅ Correct gradient signs regardless of coordinate direction
- ✅ Uses `numpy.gradient()` for non-uniform grids

### 3.3 Eady Growth Rate (EGR)

**Formula:**
$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

where:
- $f = 2\Omega \sin(\phi)$ = Coriolis parameter
- $N^2 = \frac{g}{\theta_v} \frac{\partial \theta_v}{\partial z}$ = static stability (Brunt-Väisälä frequency)
- $\left|\frac{\partial \vec{V}}{\partial z}\right|$ = vertical wind shear magnitude

**Layer:** 250–850 hPa (captures main tropospheric baroclinic zone)

**Quality Control:**
- $N^2 > 10^{-6}$ s⁻² (exclude statically unstable regions)
- $|\phi| > 5°$ (avoid equatorial singularity)
- $\sigma_{EGR} < 5$ day⁻¹ (cap unrealistic values)

### 3.4 Potential Vorticity

**Formula:**
$$PV = -g \left(\zeta_\theta + f\right) \frac{\partial \theta}{\partial p}$$

where $\zeta_\theta$ = relative vorticity on isentropic surface, $\theta$ = potential temperature.

**Levels:**
- **200 hPa:** Uses 175, 200, 225 hPa (upper-level tropopause dynamics)
- **850 hPa:** Uses 825, 850, 875 hPa (low-level diabatic PV anomaly)

**Units:** K m² kg⁻¹ s⁻¹ (SI), converted to PVU (1 PVU = 10⁻⁶ K m² kg⁻¹ s⁻¹) in figures

### 3.5 Temperature Advection

**Formula:**
$$\text{advT} = -\vec{V} \cdot \nabla T = -\left(u\frac{\partial T}{\partial x} + v\frac{\partial T}{\partial y}\right)$$

**Level:** 850 hPa  
**Sign Convention:** Positive = warm air advection; Negative = cold air advection  
**Units:** K h⁻¹ (converted from K s⁻¹)

### 3.6 Moisture Fields at 975 hPa

**Specific Humidity (q):**
- Direct measure of atmospheric moisture content
- Units: g kg⁻¹ (converted from kg kg⁻¹)
- Level: 975 hPa (near-surface, above boundary layer)

**Moisture Flux Divergence:**
$$\nabla \cdot (q\vec{V}) = \frac{\partial (qu)}{\partial x} + \frac{\partial (qv)}{\partial y}$$

- **Negative values** → Moisture convergence (convective potential, latent heat release)
- **Positive values** → Moisture divergence (evaporation/drying)
- Units: g kg⁻¹ h⁻¹ (converted from kg kg⁻¹ s⁻¹)
- Key diabatic process in cyclone intensification (Banacos & Schultz, 2005)

### 3.7 Rayleigh-Kuo Stability Criterion (250 hPa)

**Formula:**
$$RK = \beta - \frac{\partial^2 u}{\partial y^2}$$

where:
- $\beta = \frac{\partial f}{\partial y} = \frac{2\Omega \cos(\phi)}{R_{\oplus}}$ = Rossby parameter
- $\frac{\partial^2 u}{\partial y^2}$ = meridional curvature of zonal wind

**Physical Interpretation:**
- **Negative values** → Necessary condition for barotropic/baroclinic instability satisfied
- **Combined criterion:** Incorporates planetary vorticity gradient and wind shear curvature
- Level: 250 hPa (jet stream level, maximum barotropic effects)

**References:** Rayleigh (1880), Kuo (1949), Charney & Stern (1962)

### 3.8 Kinetic Energy Advection (250 hPa)

**Formula:**
$$\text{KE\_adv} = -\vec{V} \cdot \nabla(KE) = -\vec{V} \cdot \nabla\left(\frac{1}{2}(u^2 + v^2)\right)$$

**Physical Interpretation:**
- **Positive values** → KE advection causes local acceleration (energy gain)
- **Negative values** → KE advection causes local deceleration (energy loss)
- Level: 250 hPa (jet stream level)
- Units: m² s⁻³

**Significance:**  
Quantifies energy transport within the jet stream. Positive advection indicates regions where the flow pattern favors kinetic energy accumulation, potentially intensifying upper-level divergence and cyclone development.

---

## 4. Results

**Note:** Statistical summaries presented below are computed from spatial composites centered on cyclone genesis locations. Each subsection presents the composite figure followed by quantitative statistics. Physical interpretation of spatial patterns and EP1 vs EP2 differences is currently under analysis.

### 4.1 Eady Growth Rate (Baroclinic Instability)

![EGR Composite](figures/ep_structure/composite_egr.png)

*Figure: Eady growth rate composite (250–850 hPa layer) for EP1 (left) and EP2 (right). Contours show growth rate in day⁻¹. The 15° × 15° box marks the LEC computation domain.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean ± SD (day⁻¹) | 0.56 ± 0.09 | 0.56 ± 0.10 |
| Median (day⁻¹) | 0.57 | 0.58 |
| Range (day⁻¹) | [0.37, 0.73] | [0.36, 0.72] |

### 4.2 Upper-Level Dynamics (200 hPa PV)

![PV@200 Composite](figures/ep_structure/composite_pv200.png)

*Figure: Potential vorticity at 200 hPa for EP1 (left) and EP2 (right). Units: PVU (10⁻⁶ K m² kg⁻¹ s⁻¹). Shows tropopause dynamics and stratospheric intrusions.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean (PVU) | -4.54 | -4.42 |
| Range (PVU) | [-7.08, -1.26] | [-6.86, -1.18] |

### 4.3 Low-Level PV Anomaly (850 hPa)

![PV@850 Composite](figures/ep_structure/composite_pv850.png)

*Figure: Potential vorticity at 850 hPa for EP1 (left) and EP2 (right). Units: PVU. Indicates diabatic PV generation and low-level cyclonic circulation.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean (PVU) | -0.50 | -0.52 |
| Range (PVU) | [-0.74, -0.30] | [-0.75, -0.31] |

### 4.4 Temperature Advection (850 hPa)

![Temp Advection Composite](figures/ep_structure/composite_advT850.png)

*Figure: Temperature advection at 850 hPa for EP1 (left) and EP2 (right). Units: K h⁻¹. Positive (red) = warm advection; Negative (blue) = cold advection.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Domain mean (K h⁻¹) | -0.031 | -0.003 |
| Max warm advection (K h⁻¹) | 0.071 | 0.111 |
| Max cold advection (K h⁻¹) | -0.132 | -0.119 |
| LEC 15×15° mean (K h⁻¹) | -0.070 | -0.021 |
| Full 30×30° mean (K h⁻¹) | -0.031 | -0.003 |

**Lateral boundaries (flux assessment):**

| Boundary | EP1 | EP2 |
|----------|-----|-----|
| North (+7.5°) | -0.025 | 0.020 |
| South (-7.5°) | -0.081 | -0.037 |
| East (+7.5°) | -0.008 | 0.068 |
| West (-7.5°) | -0.095 | -0.074 |

### 4.5 Sea Level Pressure

![SLP Composite](figures/ep_structure/composite_slp.png)

*Figure: Mean sea level pressure for EP1 (left) and EP2 (right). Units: hPa. Shows cyclone intensity and horizontal structure.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Minimum (hPa) | 996.5 | 994.8 |
| Maximum (hPa) | 1018.3 | 1019.2 |
| LEC 15×15° mean (hPa) | 1008.1 | 1005.2 |
| Full 30×30° mean (hPa) | 1009.3 | 1006.4 |

### 4.6 Specific Humidity (975 hPa)

![Moisture Composite](figures/ep_structure/composite_moisture_flux.png)

*Figure: Specific humidity (shading, g kg⁻¹) and moisture flux vectors at 975 hPa for EP1 (left) and EP2 (right).*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean (g kg⁻¹) | 6.37 | 6.52 |
| Range (g kg⁻¹) | [2.79, 11.14] | [3.13, 11.16] |
| LEC 15×15° mean (g kg⁻¹) | 6.31 | 6.58 |
| Full 30×30° mean (g kg⁻¹) | 6.37 | 6.52 |

### 4.7 Rayleigh-Kuo Stability Criterion (250 hPa)

![RK Criterion Composite](figures/ep_structure/composite_rk_criterion.png)

*Figure: Rayleigh-Kuo criterion at 250 hPa for EP1 (left) and EP2 (right). Units: s⁻¹. Negative values (blue) indicate regions satisfying the necessary condition for barotropic/baroclinic instability. Wind vectors show 250 hPa flow.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean (s⁻¹) | 2.242e-11 | 2.271e-11 |
| Range (s⁻¹) | [-2.427e-11, 6.908e-11] | [-7.869e-12, 6.445e-11] |
| LEC 15×15° mean | 2.814e-11 | 2.818e-11 |
| Full 30×30° mean | 2.242e-11 | 2.271e-11 |

*Negative values indicate regions satisfying the necessary condition for barotropic/baroclinic instability.*

### 4.8 Kinetic Energy Advection (250 hPa)

![KE Advection Composite](figures/ep_structure/composite_ke_advection.png)

*Figure: Kinetic energy advection at 250 hPa for EP1 (left) and EP2 (right). Units: m² s⁻³. Positive values (purple) indicate KE gain through advection; negative values (orange) indicate KE loss. Wind vectors show 250 hPa flow.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean (m² s⁻³) | -1.760e-03 | -4.142e-04 |
| Range (m² s⁻³) | [-1.241e-02, 4.948e-03] | [-7.759e-03, 7.122e-03] |
| LEC 15×15° mean | -2.622e-03 | -1.380e-03 |
| Full 30×30° mean | -1.760e-03 | -4.142e-04 |

**Lateral boundaries (flux assessment):**

| Boundary | EP1 | EP2 |
|----------|-----|-----|
| North (+7.5°) | 1.207e-03 | 3.303e-03 |
| South (-7.5°) | -7.365e-03 | -5.867e-03 |
| East (+7.5°) | -1.957e-03 | 1.570e-03 |
| West (-7.5°) | -1.308e-03 | -1.924e-03 |

---

## 5. Physical Interpretation

**Status:** Analysis of spatial patterns and physical mechanisms is ongoing. Preliminary observations include:

### 5.1 EP1 Characteristics

- {EP1_INTERPRETATION}

### 5.2 EP2 Characteristics

- {EP2_INTERPRETATION}

### 5.3 Key Structural Differences

- {KEY_DIFFERENCES}

**Future Work:** Detailed analysis of spatial patterns, vertical coupling mechanisms, and relationship between energetics (from cluster analysis) and structural characteristics.

---

## 6. Computational Implementation

### 6.1 Grid Spacing on Spherical Earth

**Function:** `compute_spherical_grid_spacing(lat_1d, lon_1d)`

Computes accurate grid spacing accounting for Earth's spherical geometry:

```python
# Meridional spacing (constant per latitude band)
dy = R_EARTH * Δφ  # meters

# Zonal spacing (varies with latitude)
dx = R_EARTH * cos(φ) * Δλ  # meters
```

**Quality checks:**
- ✅ Verifies latitude is monotonic (increasing or decreasing)
- ✅ Verifies longitude is monotonic
- ✅ Raises `ValueError` if non-monotonic
- ✅ Gradient sign automatically correct regardless of coordinate direction

### 6.2 Divergence on Spherical Coordinates

For small domains (~30°), the simplified Cartesian approximation is valid:

$$\nabla \cdot \vec{F} \approx \frac{\partial F_x}{\partial x} + \frac{\partial F_y}{\partial y}$$

where $dx$ and $dy$ account for spherical geometry (Section 6.1).

**Full spherical formula** (not required for 30° domain):
$$\nabla \cdot \vec{F} = \frac{1}{R\cos\phi}\frac{\partial F_\lambda}{\partial \lambda} + \frac{1}{R\cos\phi}\frac{\partial(F_\phi \cos\phi)}{\partial \phi}$$

Our implementation uses the simplified form with accurate $dx$, $dy$ — appropriate for mesoscale domains.

### 6.3 Unit Tracking

All calculations use **MetPy units** for automatic dimensional analysis:

```python
# Example: moisture flux
qu = (q * units('kg/kg')) * (u * units('m/s'))
# → qu.units = 'kg / kg * m / s' (automatically tracked)

# Convert divergence to g/kg/s
div_q_si = (dqu_dx + dqv_dy) * units('kg/kg/s')
div_q_gkg = (div_q_si * 1000 * units('g/kg')).magnitude
```

**Benefits:**
- Prevents unit errors (e.g., mixing K and °C)
- Documents unit transformations  
- Explicit conversions (no hardcoded magic numbers)

### 6.4 Numerical Methods

- **Spatial derivatives:** `numpy.gradient()` with 2nd-order centred finite differences
- **Vertical derivatives:** Centred FD over 3 levels (e.g., 175–200–225 hPa for PV@200)
- **Interpolation:** Linear interpolation to regular 0.25° grid via `xarray.interp()`

### 6.5 Quality Control Filters

| Diagnostic | Filter | Rationale |
|------------|--------|-----------|
| EGR | $N^2 > 10^{-6}$ s⁻² | Exclude statically unstable regions |
| EGR | $\|\phi\| > 5°$ | Avoid near-equatorial ($f \approx 0$) |
| EGR | $\sigma_{EGR} < 5$ day⁻¹ | Cap unrealistic growth rates |
| PV | Valid only where $\theta$ monotonic | Ensure isentropic sorting |

### 6.6 Code Verification

**Test cases:**
1. ✅ Zonal wind → zero meridional derivative
2. ✅ Meridional wind → zero zonal derivative  
3. ✅ Uniform field → zero divergence
4. ✅ Reversed latitude (90→-90) → correct gradient sign

**Validation:**
- Cross-check EGR values with literature (typical: 0.3–1.0 day⁻¹)
- PV@200 should align with tropopause (~2–3 PVU contour)
- Compare temperature advection with operational analyses

---

## 7. References

- Banacos, P. C., & Schultz, D. M. (2005). The use of moisture flux convergence in forecasting convective initiation: Historical and operational perspectives. *Weather and Forecasting*, 20(3), 351–366.
- Čampa, J., & Wernli, H. (2012). A PV perspective on the vertical structure of mature midlatitude cyclones. *J. Atmos. Sci.*, 69(2), 725–740.
- Charney, J. G., & Stern, M. E. (1962). On the stability of internal baroclinic jets in a rotating atmosphere. *Journal of the Atmospheric Sciences*, 19(2), 159–172.
- Davis, C. A., & Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. *Mon. Wea. Rev.*, 119(8), 1929–1953.
- Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Q. J. R. Meteorol. Soc.*, 111(470), 877–946.
- Hoskins, B. J., & Valdes, P. J. (1990). On the existence of storm-tracks. *J. Atmos. Sci.*, 47(15), 1854–1864.
- Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *Journal of Meteorology*, 6(2), 105–122.
- Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *J. Atmos. Sci.*, 37(7), 1648–1654.
- Rayleigh, Lord (1880). On the stability, or instability, of certain fluid motions. *Proceedings of the London Mathematical Society*, s1-11(1), 57–72.
- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb." *Mon. Wea. Rev.*, 108(10), 1589–1606.
- Simmonds, I., & Lim, E.-P. (2009). Biases in the calculation of Southern Hemisphere mean baroclinic eddy growth rate. *Geophys. Res. Lett.*, 36(1), L01707.

---

**Document auto-generated:** 2026-02-21 18:29  
**Author:** Danilo Couto de Souza
