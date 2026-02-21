# Scientific Notes: EP Structure Analysis – EP1 vs EP2

## Overview

This document presents the spatial structure comparison between Energy Pattern 1
(EP1) and Energy Pattern 2 (EP2) cyclones during their intensification phase,
using standard dynamical diagnostics from ERA5 reanalysis.

**Key Diagnostics:**
- Eady Growth Rate (EGR, 250–850 hPa layer)  
- Potential Vorticity at 200 hPa (upper-level)  
- Potential Vorticity at 850 hPa (low-level)  
- Temperature advection at 850 hPa  
- Sea Level Pressure (SLP)

**Generated:** 2026-02-21 18:29

---

## 1. Dataset

### 1.1 Sample Composition

| | EP1 | EP2 |
|---|-----|-----|
| Cluster | 0 | 2 |
| Cases analysed | 444 | 979 |

### 1.2 ERA5 Variables

- **Pressure levels (hPa):** 175, 200, 225, 250, 500, 825, 850, 875
- **Pressure-level variables:** u, v, t, z, q
- **Single-level variables:** msl (mean sea level pressure)
- **Temporal resolution:** 6-hourly
- **Spatial resolution:** 0.25° × 0.25°
- **Domain:** 30° × 30° centred on cyclone track centre

---

## 2. Methodology

### 2.1 Spherical Grid Spacing

All horizontal derivatives account for spherical geometry:

**Meridional spacing (dy):**
$$dy = R_{\oplus} \Delta\phi$$

**Zonal spacing (dx):**
$$dx = R_{\oplus} \cos(\phi) \Delta\lambda$$

where:
- $R_{\oplus} = 6.371 \times 10^6$ m (Earth's radius)
- $\phi$ = latitude (radians)
- $\lambda$ = longitude (radians)
- $\Delta\phi$, $\Delta\lambda$ computed via `np.gradient()` for non-uniform grids

**Coordinate verification:**
- Latitude and longitude must be monotonic (checked at runtime)
- Sign of gradients automatically correct regardless of increasing/decreasing coordinates

### 2.2 Eady Growth Rate (EGR)

$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

**Layer-mean implementation (250–850 hPa):**

1. **Virtual potential temperature:**
   $$\theta_v = T_v \left(\frac{p_0}{p}\right)^{\kappa}$$
   where $T_v = T(1 + 0.61q)$, $\kappa = R_d / c_p = 0.286$

2. **Static stability (Brunt-Väisälä frequency):**
   $$N^2 = \frac{g}{\theta_{v,mid}} \frac{\Delta\theta_v}{\Delta z}$$
   where $\theta_{v,mid} = (\theta_{v,250} + \theta_{v,850})/2$

3. **Vertical wind shear:**
   $$\left|\frac{\partial \vec{V}}{\partial z}\right| = \sqrt{\left(\frac{\Delta u}{\Delta z}\right)^2 + \left(\frac{\Delta v}{\Delta z}\right)^2}$$

4. **Geopotential height:**
   $$z = \frac{\Phi}{g}$$

**Quality control:**
- $N^2 > 10^{-6}$ s$^{-2}$ (exclude statically unstable regions)
- $|\phi| > 5°$ (exclude near-equatorial regions where $f \approx 0$)
- $\sigma_{EGR} < 5$ day$^{-1}$ (cap unrealistic values)

**References:** Lindzen & Farrell (1980); Hoskins & Valdes (1990)

### 2.3 Potential Vorticity

Baroclinic PV computed with MetPy using centred finite differences:

$$PV = -g \left(\zeta_\theta + f\right) \frac{\partial \theta}{\partial p}$$

where:
- $\zeta_\theta$ = relative vorticity on isentropic surface
- $f = 2\Omega \sin(\phi)$ = Coriolis parameter
- $\Omega = 7.292 \times 10^{-5}$ rad s$^{-1}$

**Vertical levels:**
- **200 hPa:** uses 175, 200, 225 hPa → upper-level tropopause dynamics
- **850 hPa:** uses 825, 850, 875 hPa → low-level PV anomaly

**Implementation:**
- Potential temperature: $\theta = T(p_0/p)^{\kappa}$ via `metpy.calc.potential_temperature`
- PV via `metpy.calc.potential_vorticity_baroclinic`
- Returns PV at middle level (200 or 850 hPa)
- Units: K m² kg⁻¹ s⁻¹ (SI), converted to PVU (1 PVU = 10⁻⁶ K m² kg⁻¹ s⁻¹) in figures

**References:** Hoskins et al. (1985); Čampa & Wernli (2012)

### 2.4 Temperature Advection

Horizontal temperature advection at 850 hPa:

$$\text{advT} = -\vec{V} \cdot \nabla T = -\left(u\frac{\partial T}{\partial x} + v\frac{\partial T}{\partial y}\right)$$

**Implementation:**
1. Temperature gradients computed via `np.gradient()` with spherical $dx$, $dy$
2. Sign convention: **positive** = warm air advection, **negative** = cold air advection
3. Units: K s⁻¹ (converted to K h⁻¹ in tables/figures)

**Physical interpretation:**
- Warm advection (>0): promotes ascent ahead of surface low
- Cold advection (<0): promotes descent behind surface low

### 2.5 Moisture Flux Divergence

Moisture flux divergence at 975 hPa (near-surface):

$$\nabla \cdot (q\vec{V}) = \frac{\partial (qu)}{\partial x} + \frac{\partial (qv)}{\partial y}$$

**Implementation:**
1. Moisture fluxes: $qu$ and $qv$ (kg kg⁻¹ m s⁻¹)
2. Derivatives via `np.gradient()` with spherical grid spacing
3. Units tracked via MetPy: input $q$ in kg/kg → output in g kg⁻¹ s⁻¹

**Physical interpretation:**
- **Positive (divergence):** moisture export / drying
- **Negative (convergence):** moisture import / moistening  
  (supports convection and latent heat release)

### 2.6 Sea Level Pressure

Mean sea level pressure from ERA5 single-level data, composited over the
30° × 30° domain for all intensification timesteps.

**Units:** hPa (hectopascals)

---

## 3. Results

### 3.1 Eady Growth Rate

| | EP1 | EP2 |
|---|-----|-----|
| Mean (day⁻¹) | 0.56 ± 0.09 | 0.56 ± 0.10 |
| Median (day⁻¹) | 0.57 | 0.58 |
| Range (day⁻¹) | [0.37, 0.73] | [0.36, 0.72] |

### 3.2 Potential Vorticity at 200 hPa

| | EP1 | EP2 |
|---|-----|-----|
| Mean (PVU) | -4.54 | -4.42 |
| Range (PVU) | [-7.08, -1.26] | [-6.86, -1.18] |

### 3.3 Potential Vorticity at 850 hPa

| | EP1 | EP2 |
|---|-----|-----|
| Mean (PVU) | -0.50 | -0.52 |
| Range (PVU) | [-0.74, -0.30] | [-0.75, -0.31] |

### 3.4 Temperature Advection at 850 hPa

| | EP1 | EP2 |
|---|-----|-----|
| Domain mean (K h⁻¹) | -0.031 | -0.003 |
| Max warm advection (K h⁻¹) | 0.071 | 0.111 |
| Max cold advection (K h⁻¹) | -0.132 | -0.119 |

### 3.5 Sea Level Pressure

| | EP1 | EP2 |
|---|-----|-----|
| Min (hPa) | 996.5 | 994.8 |
| Max (hPa) | 1018.3 | 1019.2 |

---

## 4. Composite Figures

### 4.1 EGR (250–850 hPa)

![EGR Composite](../../figures/ep_structure/composite_egr.png)

### 4.2 PV at 200 hPa

![PV@200 Composite](../../figures/ep_structure/composite_pv200.png)

### 4.3 PV at 850 hPa

![PV@850 Composite](../../figures/ep_structure/composite_pv850.png)

### 4.4 Temperature Advection at 850 hPa

![Temp Advection Composite](../../figures/ep_structure/composite_advT850.png)

### 4.5 Sea Level Pressure

![SLP Composite](../../figures/ep_structure/composite_slp.png)

---

## 5. Physical Interpretation

### 5.1 EP1 Structure

{EP1_INTERPRETATION}

### 5.2 EP2 Structure

{EP2_INTERPRETATION}

### 5.3 Key Differences

{KEY_DIFFERENCES}

---

## 7. Computational Implementation

### 7.1 Grid Spacing on Spherical Earth

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

### 7.2 Divergence on Spherical Coordinates

For small domains (~30°), the simplified Cartesian approximation is valid:

$$\nabla \cdot \vec{F} \approx \frac{\partial F_x}{\partial x} + \frac{\partial F_y}{\partial y}$$

where $dx$ and $dy$ account for spherical geometry (Section 7.1).

**Full spherical formula** (not required for 30° domain):
$$\nabla \cdot \vec{F} = \frac{1}{R\cos\phi}\frac{\partial F_\lambda}{\partial \lambda} + \frac{1}{R\cos\phi}\frac{\partial(F_\phi \cos\phi)}{\partial \phi}$$

Our implementation uses the simplified form with accurate $dx$, $dy$ — appropriate for mesoscale domains.

### 7.3 Unit Tracking

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

### 7.4 Numerical Methods

- **Spatial derivatives:** `numpy.gradient()` with 2nd-order centred finite differences
- **Vertical derivatives:** Centred FD over 3 levels (e.g., 175–200–225 hPa for PV@200)
- **Interpolation:** Linear interpolation to regular 0.25° grid via `xarray.interp()`

### 7.5 Quality Control Filters

| Diagnostic | Filter | Rationale |
|------------|--------|-----------|
| EGR | $N^2 > 10^{-6}$ s⁻² | Exclude statically unstable regions |
| EGR | $\|\phi\| > 5°$ | Avoid near-equatorial ($f \approx 0$) |
| EGR | $\sigma_{EGR} < 5$ day⁻¹ | Cap unrealistic growth rates |
| PV | Valid only where $\theta$ monotonic | Ensure isentropic sorting |

### 7.6 Code Verification

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

## 8. References

- Čampa, J., & Wernli, H. (2012). A PV perspective on the vertical structure of mature midlatitude cyclones. *J. Atmos. Sci.*, 69(2), 725–740.
- Davis, C. A., & Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. *Mon. Wea. Rev.*, 119(8), 1929–1953.
- Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Q. J. R. Meteorol. Soc.*, 111(470), 877–946.
- Hoskins, B. J., & Valdes, P. J. (1990). On the existence of storm-tracks. *J. Atmos. Sci.*, 47(15), 1854–1864.
- Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *J. Atmos. Sci.*, 37(7), 1648–1654.
- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb." *Mon. Wea. Rev.*, 108(10), 1589–1606.
- Simmonds, I., & Lim, E.-P. (2009). Biases in the calculation of Southern Hemisphere mean baroclinic eddy growth rate. *Geophys. Res. Lett.*, 36(1), L01707.

---

**Document auto-generated:** 2026-02-21 18:29  
**Author:** Danilo Couto de Souza
