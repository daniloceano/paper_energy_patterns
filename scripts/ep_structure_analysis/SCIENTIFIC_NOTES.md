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

**Generated:** {GENERATION_DATE}

---

## 1. Dataset

### 1.1 Sample Composition

| | EP1 | EP2 |
|---|-----|-----|
| Cluster | 0 | 2 |
| Cases analysed | {EP1_N_CASES} | {EP2_N_CASES} |

### 1.2 ERA5 Variables

- **Pressure levels (hPa):** 175, 200, 225, 250, 500, 825, 850, 875
- **Pressure-level variables:** u, v, t, z, q
- **Single-level variables:** msl (mean sea level pressure)
- **Temporal resolution:** 6-hourly
- **Spatial resolution:** 0.25° × 0.25°
- **Domain:** 30° × 30° centred on cyclone track centre

---

## 2. Methodology

### 2.1 Eady Growth Rate (EGR)

$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

Computed using the 250–850 hPa layer:
- Vertical wind shear from 250 and 850 hPa winds
- Static stability (N) from virtual potential temperature at both levels
- References: Lindzen & Farrell (1980); Hoskins & Valdes (1990)

### 2.2 Potential Vorticity

Baroclinic PV computed with MetPy using centred finite differences:
- **200 hPa:** levels 175, 200, 225 hPa → tropopause dynamics (Hoskins et al., 1985)
- **850 hPa:** levels 825, 850, 875 hPa → low-level PV anomaly (Čampa & Wernli, 2012)

### 2.3 Temperature Advection

$$\text{advT} = -\vec{V} \cdot \nabla T$$

Computed at 850 hPa using centred finite differences for ∂T/∂x and ∂T/∂y.
Positive values: warm air advection; negative: cold air advection.

### 2.4 Sea Level Pressure

Mean sea level pressure from ERA5 single-level data, composited over the
30° × 30° domain for all intensification timesteps.

---

## 3. Results

### 3.1 Eady Growth Rate

| | EP1 | EP2 |
|---|-----|-----|
| Mean (day⁻¹) | {EP1_EGR_MEAN} ± {EP1_EGR_STD} | {EP2_EGR_MEAN} ± {EP2_EGR_STD} |
| Median (day⁻¹) | {EP1_EGR_MEDIAN} | {EP2_EGR_MEDIAN} |
| Range (day⁻¹) | [{EP1_EGR_MIN}, {EP1_EGR_MAX}] | [{EP2_EGR_MIN}, {EP2_EGR_MAX}] |

### 3.2 Potential Vorticity at 200 hPa

| | EP1 | EP2 |
|---|-----|-----|
| Mean (PVU) | {EP1_PV200_MEAN} | {EP2_PV200_MEAN} |
| Range (PVU) | [{EP1_PV200_MIN}, {EP1_PV200_MAX}] | [{EP2_PV200_MIN}, {EP2_PV200_MAX}] |

### 3.3 Potential Vorticity at 850 hPa

| | EP1 | EP2 |
|---|-----|-----|
| Mean (PVU) | {EP1_PV850_MEAN} | {EP2_PV850_MEAN} |
| Range (PVU) | [{EP1_PV850_MIN}, {EP1_PV850_MAX}] | [{EP2_PV850_MIN}, {EP2_PV850_MAX}] |

### 3.4 Temperature Advection at 850 hPa

| | EP1 | EP2 |
|---|-----|-----|
| Domain mean (K h⁻¹) | {EP1_ADVT_MEAN} | {EP2_ADVT_MEAN} |
| Max warm advection (K h⁻¹) | {EP1_ADVT_MAX_WARM} | {EP2_ADVT_MAX_WARM} |
| Max cold advection (K h⁻¹) | {EP1_ADVT_MAX_COLD} | {EP2_ADVT_MAX_COLD} |

### 3.5 Sea Level Pressure

| | EP1 | EP2 |
|---|-----|-----|
| Min (hPa) | {EP1_SLP_MIN} | {EP2_SLP_MIN} |
| Max (hPa) | {EP1_SLP_MAX} | {EP2_SLP_MAX} |

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

## 6. References

- Čampa, J., & Wernli, H. (2012). A PV perspective on the vertical structure of mature midlatitude cyclones. *J. Atmos. Sci.*, 69(2), 725–740.
- Davis, C. A., & Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. *Mon. Wea. Rev.*, 119(8), 1929–1953.
- Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Q. J. R. Meteorol. Soc.*, 111(470), 877–946.
- Hoskins, B. J., & Valdes, P. J. (1990). On the existence of storm-tracks. *J. Atmos. Sci.*, 47(15), 1854–1864.
- Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *J. Atmos. Sci.*, 37(7), 1648–1654.
- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb." *Mon. Wea. Rev.*, 108(10), 1589–1606.
- Simmonds, I., & Lim, E.-P. (2009). Biases in the calculation of Southern Hemisphere mean baroclinic eddy growth rate. *Geophys. Res. Lett.*, 36(1), L01707.

---

**Document auto-generated:** {GENERATION_DATE}  
**Author:** Danilo Couto de Souza
