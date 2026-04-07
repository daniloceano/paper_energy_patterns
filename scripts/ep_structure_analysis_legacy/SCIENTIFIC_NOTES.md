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
- **Domain:** 30° × 30° (or larger) downloaded per cyclone as a bounding box covering the entire intensification phase; this is a single NetCDF per cyclone stored in `data/era5_ep_structure`.
- **Composite domain:** 30° × 30° centered on the cyclone for each timestep. Figures include an inner 15° × 15° box indicating the LEC computation domain.

**Storm-Centered Methodology (CRITICAL - Fixed 2026-04-03):**

> ⚠️ **METHODOLOGICAL FIX:** Prior to 2026-04-03, the composite pipeline used a **FIXED domain center** per cyclone (the mean position during intensification), which was scientifically incorrect for storm-centered composites. An audit revealed that only ~15% of timesteps were adequately centered (within 222 km of the cyclone), with a mean offset of 1,079 km and maximum offset of 8,788 km.

The corrected methodology now implements **per-timestep storm centering**:

1. **For each timestep** during intensification, the cyclone center position is read from the track data (`data/tracks_SAt_filtered_with_energetics_processed.csv`).

2. **The 30°×30° subdomain** is extracted from the pre-downloaded ERA5 data, centered on the actual cyclone position at that specific timestep (not a fixed mean position).

3. **Diagnostic fields** are computed on this correctly-centered grid where the cyclone is always at the origin (x=0, y=0).

4. **Composite aggregation** accumulates all storm-centered fields:
   - **Full intensification mode:** ALL storm-centered timesteps from ALL cyclones
   - **Central time mode:** Only the central timestep (storm-centered) from each cyclone

**Statistics from reprocessing (2026-04-03):**
| Mode | EP1 Cases | EP1 Timesteps | EP2 Cases | EP2 Timesteps | Skipped (no pos) | Skipped (oob) |
|------|-----------|---------------|-----------|---------------|------------------|---------------|
| Full | 444 | 3,172 | 979 | 6,828 | 1,481 | 3,495 |
| Central | 442 | 442 | 978 | 978 | 0 | 0 |

**Skipped timesteps:** Some timesteps are skipped when the cyclone position is not available in the track file (rare) or when the required 30°×30° subdomain extends outside the downloaded data envelope. This is expected for cyclones near the edge of the download region.

**Old invalid products:** Moved to `_INVALID_METHODOLOGY_OLD/` directories (data and figures) with explanatory README files.

**Temporal Resolution:** 6-hourly

---

## 3. Methodology

### 3.1 Composite Modes

Two methodologies are available for aggregating cyclone fields during intensification:

#### Full Intensification Mode (default)

**Method:** Mean over all 6-hourly timesteps in the intensification phase

**Rationale:**  
- Captures the *average structure* during the entire deepening period
- Reduces noise from individual timesteps
- Represents the typical dynamical environment sustained throughout intensification
- Consistent with traditional composite methodology (e.g., Sinclair 1997; Lim & Simmonds 2007)

**Formula:** For each cyclone $i$, compute the phase-mean field:
$$\bar{\phi}_i(\mathbf{x}) = \frac{1}{N_i} \sum_{t=1}^{N_i} \phi_i(\mathbf{x}, t)$$
where $N_i$ is the number of timesteps in the intensification phase.

The composite mean is then:
$$\langle\phi\rangle(\mathbf{x}) = \frac{1}{M} \sum_{i=1}^{M} \bar{\phi}_i(\mathbf{x})$$
where $M$ is the number of cyclones in the sample.

#### Central Time Mode (new)

**Method:** Single timestep at the temporal center of the intensification phase

**Rationale:**  
- Captures a *snapshot* at the peak/center of intensification
- Avoids temporal smoothing that may obscure transient features
- Useful for comparing instantaneous vs. phase-averaged structures
- Isolates the most intense/active moment of deepening

**Formula:** For each cyclone $i$, select the central timestep:
$$t_{\text{center}} = \left\lfloor \frac{N_i}{2} \right\rfloor$$
where $N_i$ is the number of timesteps. For odd $N_i$, this is the exact middle; for even $N_i$, this is the timestep just after the midpoint (round-up convention).

The composite mean uses only this single timestep per cyclone:
$$\langle\phi\rangle(\mathbf{x}) = \frac{1}{M} \sum_{i=1}^{M} \phi_i(\mathbf{x}, t_{\text{center}, i})$$

**Example:**  
- Intensification from 2020-06-10 00Z to 2020-06-12 18Z (12 timesteps, 54 hours)
- Central timestep: index 6 → 2020-06-11 06Z (midpoint at 27 hours)

### 3.3 Diagnostic Fields Computed

| Diagnostic | Level(s) | Purpose | Key Reference |
|------------|----------|---------|---------------|
| **Eady Growth Rate** | 500–850 hPa | Baroclinic instability measure | Lindzen & Farrell (1980); Besson et al. (2021) |
| **Potential Vorticity** | 200 hPa | Upper-level dynamics, tropopause folding | Hoskins et al. (1985) |
| **Potential Vorticity** | 850 hPa | Low-level PV anomaly, diabatic effects | Čampa & Wernli (2012) |
| **Temperature Advection** | 850 hPa | Warm/cold advection patterns | Sanders & Gyakum (1980) |
| **Specific Humidity** | 975 hPa | Near-surface moisture distribution | - |
| **Moisture Flux Divergence** | 975 hPa | Moisture convergence (convective potential) | Banacos & Schultz (2005) |
| **Sea Level Pressure** | Surface | Cyclone intensity and position | - |
| **RK criterion** (Rayleigh-Kuo) | 250 hPa | Barotropic/baroclinic instability condition | Rayleigh (1880); Kuo (1949) |
| **KE Advection** | 250 hPa | Kinetic energy tendency from advection | - |
| **AFC** (Ageostrophic Flux Convergence) | 250 hPa | Eddy KE redistribution via ageostrophic pressure work | Orlanski & Katzfey (1991); Orlanski & Sheldon (1993) |
| **BtCR** (Barotropic Critical Region) | 250 hPa | Effective deformation $\Delta_m = \sigma_m^2 - \zeta_m^2$ and dilatation axis $\phi_{dil}$; identifies jet-exit zones where deformation dominates rotation | Rivière (2006) |

**Anomaly diagnostics** (departure from 1991–2020 climatology — same temporal decomposition as AFC):

| Anomaly Diagnostic | Level | Base Field Primed | Output Variable |
|--------------------|-------|-------------------|-----------------|
| **PV anomaly** | 200 hPa | PV(u,v,T) − PV(ū_m,v̄_m,T̄_m) at 175/200/225 hPa | `pv_200_anom` |
| **PV anomaly** | 850 hPa | PV(u,v,T) − PV(ū_m,v̄_m,T̄_m) at 825/850/875 hPa | `pv_850_anom` |
| **Temp advection anomaly** | 850 hPa | u′, v′, T′ at 850 hPa | `adv_T_850_anom` |
| **Moisture flux div anomaly** | 975 hPa | u′, v′, q′ at 975 hPa | `div_q_975_anom` |
| **KE advection anomaly** | 250 hPa | u′, v′ at 250 hPa | `ke_adv_250_anom` |
| **SLP anomaly** | Surface | msl (Pa) | `msl_anom` |

> **Note:** EGR is not decomposed into anomaly form. The EGR formula involves N² and vertical shear over a deep layer (500–850 hPa), making a clean temporal decomposition ill-defined. EGR is interpreted as a total-field baroclinic instability measure.

### 3.3 Spherical Grid Spacing

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

### 3.4 Eady Growth Rate (EGR)

**Formula:**
$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

where:
- $f = 2\Omega \sin(\phi)$ = Coriolis parameter
- $N^2 = \frac{g}{\bar{\theta}} \frac{\partial \theta}{\partial z}$ = dry Brunt-Väisälä frequency (using dry potential temperature $\theta$; the code does not apply a virtual temperature correction, consistent with Besson et al. 2021 and the standard EGR formulation as in Hoskins & Valdes 1990)
- $\left|\frac{\partial \vec{V}}{\partial z}\right|$ = vertical wind shear magnitude

**Layer:** 500–850 hPa (following Besson et al. 2021, Eq. 5: this layer encompasses the main lower-to-mid tropospheric baroclinic zone while avoiding contamination from the jet-level wind maximum at 250 hPa)

**Quality Control:**
- $N^2 > 10^{-6}$ s⁻² (exclude statically unstable regions)
- $|\phi| > 5°$ (avoid equatorial singularity)
- $\sigma_{EGR} < 5$ day⁻¹ (cap unrealistic values)

### 3.5 Potential Vorticity

**Formula:**
$$PV = -g \left(\zeta_\theta + f\right) \frac{\partial \theta}{\partial p}$$

where $\zeta_\theta$ = relative vorticity on isentropic surface, $\theta$ = potential temperature.

**Levels:**
- **200 hPa:** Uses 175, 200, 225 hPa (upper-level tropopause dynamics)
- **850 hPa:** Uses 825, 850, 875 hPa (low-level diabatic PV anomaly)

**Units:** K m² kg⁻¹ s⁻¹ (SI), converted to PVU (1 PVU = 10⁻⁶ K m² kg⁻¹ s⁻¹) in figures

### 3.6 Temperature Advection

**Formula:**
$$\text{advT} = -\vec{V} \cdot \nabla T = -\left(u\frac{\partial T}{\partial x} + v\frac{\partial T}{\partial y}\right)$$

**Level:** 850 hPa  
**Sign Convention:** Positive = warm air advection; Negative = cold air advection  
**Units:** K h⁻¹ (converted from K s⁻¹)

### 3.7 Moisture Fields at 975 hPa

**Specific Humidity (q):**
- Direct measure of atmospheric moisture content
- Units: g kg⁻¹ (converted from kg kg⁻¹)
- Level: 975 hPa (near-surface, above boundary layer)

**Moisture Flux Divergence:**
$$\nabla \cdot (q\vec{V}) = \frac{\partial (qu)}{\partial x} + \frac{\partial (qv)}{\partial y}$$

- **Negative values** → Moisture convergence (convective potential, latent heat release)
- **Positive values** → Moisture divergence (evaporation/drying)
- Units: g kg⁻¹ s⁻¹ (composite files store values as kg kg⁻¹ s⁻¹ × 10³; figures plot as-is without further rescaling)
- Key diabatic process in cyclone intensification (Banacos & Schultz, 2005)

### 3.8 Rayleigh-Kuo Stability Criterion (250 hPa)

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

### 3.9 Kinetic Energy Advection (250 hPa)

**Formula:**
$$\text{KE\_adv} = -\vec{V} \cdot \nabla(KE) = -\vec{V} \cdot \nabla\left(\frac{1}{2}(u^2 + v^2)\right)$$

**Physical Interpretation:**
- **Positive values** → KE advection causes local acceleration (energy gain)
- **Negative values** → KE advection causes local deceleration (energy loss)
- Level: 250 hPa (jet stream level)
- Units: m² s⁻³

**Significance:**  
Quantifies energy transport within the jet stream. Positive advection indicates regions where the flow pattern favors kinetic energy accumulation, potentially intensifying upper-level divergence and cyclone development.

### 3.10 Ageostrophic Flux Convergence — AFC (250 hPa)

The AFC diagnostic quantifies the redistribution of **eddy kinetic energy** through pressure work by the ageostrophic component of the eddy wind, following Orlanski & Katzfey (1991) and Orlanski & Sheldon (1993).

**Temporal decomposition (Solman & Menéndez 1998; Decker & Martin 2005):**
$$\vec{V} = \vec{V}_m + \vec{v}' \qquad \Phi = \Phi_m + \phi'$$

where $\vec{V}_m$, $\Phi_m$ are the **30-year monthly climatological means** (1991–2020, WMO standard period) and $\vec{v}'$, $\phi'$ are the instantaneous eddy perturbations.  This base state is independent of the area-mean decomposition used in the Lorenz Energy Cycle, providing an independent validation of the energy pathways.

**Geostrophic eddy wind:**
$$u_g' = -\frac{1}{f}\frac{\partial \phi'}{\partial y}, \qquad v_g' = \frac{1}{f}\frac{\partial \phi'}{\partial x}$$

**Ageostrophic eddy wind:**
$$\vec{v}_{ag}' = \vec{v}' - \vec{v}_g'$$

**AFC (Ageostrophic Geopotential Flux Convergence):**
$$AFC = -\nabla \cdot (\vec{v}_{ag}' \, \phi')$$

**Sign convention:**
- **Positive (AFC > 0):** Convergence of ageostrophic geopotential flux → **source** of eddy KE
- **Negative (AFC < 0):** Divergence of flux → **sink** of eddy KE

**Units:** m² s⁻³ (≡ W kg⁻¹)

**References:** Orlanski & Katzfey (1991), Orlanski & Sheldon (1993), Solman & Menéndez (1998)

> **Note on climatology data source:** The 30-year monthly climatology used as base state is described in Section 3.10.

### 3.11 Anomaly Fields — Temporal Decomposition

To isolate the **synoptic-scale eddy signature** of EP1 and EP2 cyclones from the background climatological state, five additional diagnostics are computed as anomaly (eddy perturbation) fields using the same temporal decomposition already applied to AFC.

**Sign convention — anomaly definition:**
$$X' = X - \bar{X}_m$$

that is, **instantaneous minus climatology** (positive anomaly = instantaneous value exceeds the climatological background).  This is the standard convention in the extratropical dynamics literature (Trenberth 1984; Orlanski & Katzfey 1991; Decker & Martin 2005) and is used throughout all anomaly diagnostics in this study.  The reverse sign ($\bar{X}_m - X$) is *not* used.

**Full decomposition identity:**
$$X = \bar{X}_m + X'$$

where $\bar{X}_m$ is the **30-year WMO monthly climatological mean** (1991–2020, ERA5 monthly-averaged reanalysis) and $X'$ is the **eddy perturbation** at the time of the cyclone track.

**Climatology data source:**  
ERA5 monthly-averaged reanalysis on pressure levels (`reanalysis-era5-pressure-levels-monthly-means`), downloaded via CDS API in `step2_1_download_era5_monthly_means.py`. The download is organized in four groups:

| Group | Levels (hPa) | Variables | Climatology file |
|-------|-------------|-----------|------------------|
| `250hPa` | 250 | u, v, z | `era5_climatology_250hPa.nc` |
| `pv200` | 175, 200, 225 | u, v, t | `era5_climatology_pv200.nc` |
| `pv850` | 825, 850, 875 | u, v, t | `era5_climatology_pv850.nc` |
| `mfd975` | 975 | u, v, q | `era5_climatology_mfd975.nc` |
| `slp` | surface | msl | `era5_climatology_slp.nc` |

**Application to diagnostics:**  
For each diagnostic $D = D(u, v, T, \ldots)$ the anomaly (eddy) field is computed by substituting all input fields with their climatological perturbations:

$$D' = D(u', v', T', \ldots) \quad \text{where } u' = u - \bar{u}_m, \; T' = T - \bar{T}_m, \ldots$$

For **linear** diagnostics (temperature advection, KE self-advection), this substitution recovers the exact anomaly since cross-terms vanish.  For **non-linear** diagnostics (PV, moisture flux divergence), the full anomaly decomposes into:

$$D_{\text{anom}} = \underbrace{D(u', v', T', \ldots)}_{\text{pure-eddy term (computed)}} + \underbrace{\text{cross terms}}_{\text{omitted}}$$

The cross-terms (e.g. $-V_m \cdot \nabla T' - V' \cdot \nabla T_m$ for temperature advection) represent interactions between the mean and eddy flows and are **not** computed here.  The reported $D'$ therefore captures the **pure synoptic-scale eddy contribution**, which is the dominant term during active cyclone intensification.

**Exception — SLP anomaly:** computed directly as $\mathrm{SLP}' = \mathrm{SLP} - \overline{\mathrm{SLP}}_m$, since sea-level pressure is a single-field diagnostic that requires no input priming. This formulation is exact (no cross-terms).

**Physical rationale:**  
- **PV′:** Highlights stratospheric intrusions and diabatic generation that are anomalous relative to the climatological background tropopause structure.
- **Temp advection′:** Isolates warm/cold advection driven by the cyclone's eddy circulation, removing the climatological advective background.
- **Moisture flux div′:** Captures synoptic-scale convergence anomalies, filtering out the seasonal moisture cycle.
- **KE advection′:** Highlights energy transport by the eddy jet/streak relative to the mean flow.

**Note on EGR:** EGR is a layer-averaged diagnostic derived from the total wind shear and static stability. A temporal decomposition of EGR would require priming N² and the shear simultaneously, leading to non-trivial cross terms. For this reason EGR is retained as a total-field diagnostic only.

**Note on AFC:** AFC is by construction an anomaly field (it is already computed from eddy $\vec{v}'$ and $\phi'$ relative to the monthly climatology). No additional anomaly version is needed.

**Note on wind vectors in anomaly figures:** All anomaly composite figures overlay **eddy wind vectors** $\vec{V}' = \vec{V} - \bar{\vec{V}}_m$ (not total winds), consistent with the sign convention above.  This ensures that the overlaid circulation patterns reflect the cyclone-induced perturbation rather than the climatological background.

---

### 3.12 Barotropic Critical Region (BtCR) at 250 hPa

The BtCR concept, introduced by Rivière (2006), identifies jet-exit zones where the **low-frequency horizontal deformation field** dominates over rotation.  A synoptic-scale disturbance traversing such a region is forced into a preferred orientation that enables efficient extraction of baroclinic energy and can trigger explosive cyclogenesis.

#### 3.11.1 Low-Frequency Base State

Rivière (2006) defined the low-frequency background flow as the **8-day running mean** of the instantaneous wind field, which filters out synoptic-scale variability (periods of 2–6 days) while retaining the slowly-varying jet structure.  Computing a per-case 8-day running mean for hundreds of ERA5 cyclone tracks is impractical in this study.  Instead, the **30-year WMO monthly climatological mean** (1991–2020) is used as a surrogate.  This captures the same large-scale, slowly varying deformation structure as the 8-day mean, since the monthly climatology is dominated by the persistent jet-stream regime.

**Consequence:** the composite BtCR maps presented here reflect the mean deformation environment in which EP1 and EP2 cyclones develop, not a case-by-case instantaneous background.  This is consistent with the composite analysis framework adopted throughout this study.

#### 3.11.2 Formulation (Spherical Geometry)

All derivatives use the full spherical-geometry grid spacings (see §3.2) and include curvature correction terms (Rivière 2006; BtCR Technical Guide, Souza 2026).

**Background relative vorticity:**
$$\zeta_m = \frac{\partial v_m}{\partial x} - \frac{\partial u_m}{\partial y} + \frac{u_m \tan\phi}{a}$$

**Deformation components (with spherical curvature corrections):**
$$St = \frac{\partial u_m}{\partial x} - \frac{\partial v_m}{\partial y} - \frac{v_m \tan\phi}{a} \quad\text{(stretching deformation)}$$
$$Sh = \frac{\partial v_m}{\partial x} + \frac{\partial u_m}{\partial y} - \frac{u_m \tan\phi}{a} \quad\text{(shearing deformation)}$$

**Total deformation magnitude:**
$$\sigma_m = \sqrt{St^2 + Sh^2}$$

**Effective deformation (master BtCR indicator):**
$$\Delta_m = \sigma_m^2 - \zeta_m^2$$

| $\Delta_m$ sign | Physical regime | Implication |
|-----------------|-----------------|-------------|
| $< 0$ | Rotation dominates | Disturbance stays circular; no preferred orientation; barotropic exchanges negligible |
| $> 0$ | Deformation dominates | Fixed orientation points appear (stable + unstable); jet can tilt the system into an energy-producing or energy-draining configuration |

**Dilatation axis angle** (defined only where $\Delta_m > 0$):
$$\phi_{dil} = \frac{1}{2} \arctan\!\left(\frac{Sh}{St}\right)$$

The dilatation axis is the direction toward which the background flow stretches fluid parcels.  The **key BtCR structural signature** is a sudden reorientation of $\phi_{dil}$ across the composited jet exit: from SW–NE orientation upstream/on the anticyclonic side to NW–SE orientation downstream/on the cyclonic side (Rivière 2006, Fig. 9).

#### 3.11.3 Physical Interpretation

When a cyclone traverses a BtCR, two amplification mechanisms are activated:

1. **Interruption of barotropic drain:** Before reaching the BtCR, the eddy may be aligned in a configuration that drains energy to the jet (stable orientation point).  At the BtCR the alignment is rapidly reconfigured, replacing the energy-draining tilt with an energy-gaining one.

2. **Configuration term (conf):** Even in regions of modest baroclinicity, the BtCR forces the disturbance into the optimal baroclinic configuration (the $\text{conf}$ term in Rivière 2006, Eq. 12).  This term can exceed the direct baroclinic contribution $|B_c|$ in magnitude during explosive growth phases.

**Output variables:**
- `btcr_delta_m`  — $\Delta_m$ composite (s⁻²); plotted at scale $\times 10^{9}$ s⁻²
- `btcr_dil_angle` — $\phi_{dil}$ composite (radians); NaN where $\Delta_m \le 0$

**Figure output:** `figures/ep_structure/composite_btcr.png`

**References:**
- Rivière, G., 2006: Role of the Low-Frequency Deformation Field on the Explosive Growth of Extratropical Cyclones at the Jet Exit. Part I: Barotropic Critical Region. *J. Atmos. Sci.*, **63**, 1764–1775. doi:10.1175/JAS3728.1

---

## 4. Results

**Note:** Statistical summaries presented below are computed from spatial composites centered on cyclone genesis locations. Each subsection presents the composite figure followed by quantitative statistics. Physical interpretation of spatial patterns and EP1 vs EP2 differences is currently under analysis.

### 4.1 Eady Growth Rate (Baroclinic Instability)

![EGR Composite](figures/ep_structure/composite_egr.png)

*Figure: Eady growth rate composite (500–850 hPa layer, Besson et al. 2021) for EP1 (left) and EP2 (right). Contours show growth rate in day⁻¹. The 15° × 15° box marks the LEC computation domain.*

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

### 4.9 Ageostrophic Flux Convergence (250 hPa)

![AFC Composite](figures/ep_structure/composite_afc_250.png)

*Figure: Ageostrophic Flux Convergence at 250 hPa for EP1 (left) and EP2 (right). Units: m² s⁻³. Positive values (red) indicate eddy KE sources; negative values (blue) indicate eddy KE sinks. Base state: ERA5 30-year monthly climatology (1991–2020). Wind vectors show total composite-mean 250 hPa wind.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean (m² s⁻³) | 1.752e-04 | -2.870e-04 |
| Range (m² s⁻³) | [-6.170e-03, 6.491e-03] | [-6.673e-03, 6.259e-03] |
| LEC 15×15° mean | 1.575e-03 | 7.611e-04 |
| Full 30×30° mean | 1.752e-04 | -2.870e-04 |

**Lateral boundaries (flux assessment):**

| Boundary | EP1 | EP2 |
|----------|-----|-----|
| North (+7.5°) | 2.092e-03 | 5.479e-04 |
| South (-7.5°) | -5.042e-04 | -1.389e-03 |
| East (+7.5°) | 6.667e-04 | -3.241e-03 |
| West (-7.5°) | -1.856e-03 | 1.532e-03 |

---

### 4.10 PV Anomaly at 200 hPa

![PV′@200 Composite](figures/ep_structure/composite_pv200_anom.png)

*Figure: PV anomaly at 200 hPa (departure from 1991–2020 climatology) for EP1 (left) and EP2 (right). Units: PVU.*

**Computation method (exact subtraction):**
$$PV'_{200} = PV(u, v, T) - PV(\bar{u}_m, \bar{v}_m, \bar{T}_m)$$
where all PV values are computed using MetPy `potential_vorticity_baroclinic` on three levels (175/200/225 hPa) and the central level is extracted. The climatological PV uses monthly-mean (1991–2020) winds and temperature interpolated to case coordinates via `_clim_da`.

> **Why exact subtraction?** PV is inherently nonlinear: $PV(u', v', T') \neq PV(u,v,T) - PV(\bar{u}_m, \bar{v}_m, \bar{T}_m)$ because cross-terms of the form $(\zeta_m \frac{\partial\theta'}{\partial p} + \zeta' \frac{\partial\theta_m}{\partial p})$ are omitted in the pure-eddy approximation. In the Southern Hemisphere, these cross-terms can dominate and produce wrong-sign anomalies for cyclones. Computing $PV(u', v', T')$ was the former approach; exact subtraction was adopted in February 2026.

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean ± SD (PVU) | TBD | TBD |
| Range (PVU) | TBD | TBD |
| LEC 15×15° mean | TBD | TBD |

### 4.11 PV Anomaly at 850 hPa

![PV′@850 Composite](figures/ep_structure/composite_pv850_anom.png)

*Figure: PV anomaly at 850 hPa (departure from 1991–2020 climatology) for EP1 (left) and EP2 (right). Units: PVU.*

**Computation method:** Identical to §4.10 but using levels 825/850/875 hPa. Expected sign in Southern Hemisphere cyclones: **negative** at low levels (cyclonic circulation in SH corresponds to negative PV anomaly since $f < 0$).

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Mean ± SD (PVU) | TBD | TBD |
| Range (PVU) | TBD | TBD |
| LEC 15×15° mean | TBD | TBD |

### 4.12 Temperature Advection Anomaly (850 hPa)

![AdvT′@850 Composite](figures/ep_structure/composite_advT850_anom.png)

*Figure: Temperature advection eddy perturbation at 850 hPa (−V′·∇T′) for EP1 (left) and EP2 (right). Units: K h⁻¹. Positive = anomalous warm advection; Negative = anomalous cold advection.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Domain mean (K h⁻¹) | TBD | TBD |
| Max warm advection (K h⁻¹) | TBD | TBD |
| Max cold advection (K h⁻¹) | TBD | TBD |
| LEC 15×15° mean (K h⁻¹) | TBD | TBD |

**Lateral boundaries — anomaly (flux assessment):**

| Boundary | EP1′ (K h⁻¹) | EP2′ (K h⁻¹) |
|----------|-------------:|-------------:|
| North (+7.5°) | -0.057 | -0.048 |
| South (-7.5°) | 0.021 | 0.022 |
| East (+7.5°) | -0.023 | -0.029 |
| West (-7.5°) | -0.007 | -0.016 |

### 4.13 Moisture Flux Divergence Anomaly (975 hPa)

![MFD′@975 Composite](figures/ep_structure/composite_moisture_flux_anom.png)

*Figure: Moisture flux divergence eddy perturbation at 975 hPa ($\nabla\cdot(q'\vec{V}')$) for EP1 (left) and EP2 (right). Units: g kg⁻¹ s⁻¹. Negative = anomalous convergence.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Domain mean (g kg⁻¹ s⁻¹) | TBD | TBD |
| Max convergence anomaly (g kg⁻¹ s⁻¹) | TBD | TBD |
| LEC 15×15° mean (g kg⁻¹ s⁻¹) | TBD | TBD |

**Lateral boundaries — anomaly (flux assessment):**

| Boundary | EP1′ (g kg⁻¹ s⁻¹) | EP2′ (g kg⁻¹ s⁻¹) |
|----------|-------------------:|-------------------:|
| North (+7.5°) | 1.073e+01 | 8.352e+00 |
| South (-7.5°) | -5.168e+00 | -8.519e+00 |
| East (+7.5°) | -3.601e-01 | -1.422e+00 |
| West (-7.5°) | -2.091e+00 | 4.778e+00 |

### 4.14 KE Advection Anomaly (250 hPa)

![KE′ Adv@250 Composite](figures/ep_structure/composite_ke_advection_anom.png)

*Figure: Eddy KE self-advection at 250 hPa ($-\vec{V}'\cdot\nabla(\tfrac{1}{2}|\vec{V}'|^2)$) for EP1 (left) and EP2 (right). Units: m² s⁻³. Captures advection of eddy kinetic energy by the eddy wind itself; cross-term advection by the mean wind ($-\vec{V}_m\cdot\nabla(\tfrac{1}{2}|\vec{V}'|^2)$) is not included.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Domain mean (m² s⁻³) | TBD | TBD |
| Range (m² s⁻³) | TBD | TBD |
| LEC 15×15° mean | TBD | TBD |

**Lateral boundaries — anomaly (flux assessment):**

| Boundary | EP1′ (m² s⁻³) | EP2′ (m² s⁻³) |
|----------|---------------:|---------------:|
| North (+7.5°) | -4.546e-04 | -3.210e-04 |
| South (-7.5°) | -1.117e-03 | 6.557e-05 |
| East (+7.5°) | -6.259e-04 | -1.415e-04 |
| West (-7.5°) | -1.098e-04 | 2.944e-04 |

### 4.15 Sea Level Pressure Anomaly

![SLP′ Composite](figures/ep_structure/composite_slp_anom.png)

*Figure: Sea level pressure anomaly (SLP′ = SLP − climatological monthly mean) for EP1 (left) and EP2 (right). Units: hPa. Positive (red) = anomalous high pressure; Negative (blue) = anomalous low pressure. The low-pressure anomaly centred at the cyclone position directly indicates the deepening relative to the climatological background. **Eddy 850 hPa wind vectors** (V′ = V − V̅_m) overlaid.*

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Domain mean (hPa) | TBD | TBD |
| Minimum anomaly (hPa) | TBD | TBD |
| LEC 15×15° mean (hPa) | TBD | TBD |

### 4.16 Wind Speed Anomaly at 250 hPa

![Wind250 Anom Composite](figures/ep_structure/composite_wind250_anom.png)

*Figure: 250 hPa wind speed anomaly (|V| − |V̅_m|) for EP1 (left) and EP2 (right). Units: m s⁻¹. Diverging colormap (RdBu_r): red = stronger-than-climatology jet; blue = weaker-than-climatology jet.*

**Computation:**
$$\Delta|V|_{250} = \sqrt{u_{250}^2 + v_{250}^2} - \sqrt{(u_{250} - u'_{250})^2 + (v_{250} - v'_{250})^2}$$

The climatological wind speed is recovered as $V_{\text{clim}} = V_{\text{total}} - V'$ since both total and eddy prime winds are already stored in the composite dataset. No additional step3 computation is required.

**Summary Statistics:**

| Statistic | EP1 | EP2 |
|-----------|-----|-----|
| Domain mean (m s⁻¹) | TBD | TBD |
| Range (m s⁻¹) | TBD | TBD |
| LEC 15×15° mean (m s⁻¹) | TBD | TBD |

---

## 4.15 Boundary Flux Summary — Total vs Anomaly

The table below compares the mean diagnostic field along each edge of the 15°×15° LEC
subdomain for the **total** composite (EP1, EP2) and the **anomaly** composite
(EP1′, EP2′ — departure from the ERA5 1991–2020 monthly climatology).

> **EP' = anomalia relativa à climatologia ERA5 1991–2020.** Campos totais usam o compósito bruto; anomalias usam u′, v′, T′/q′ (desvios da média mensal climatológica).

| Diagnóstico | Fronteira | EP1 (total) | EP1′ (anomalia) | EP2 (total) | EP2′ (anomalia) |
|-------------|-----------|------------:|----------------:|------------:|----------------:|
| Temperature Advection (850 hPa) | North (+K h⁻¹) | -0.030 | -0.057 | 0.011 | -0.048 |
| Temperature Advection (850 hPa) | South (+K h⁻¹) | -0.079 | 0.021 | -0.055 | 0.022 |
| Temperature Advection (850 hPa) | East (+K h⁻¹) | -0.022 | -0.023 | 0.058 | -0.029 |
| Temperature Advection (850 hPa) | West (+K h⁻¹) | -0.094 | -0.007 | -0.088 | -0.016 |
| Moisture Flux Div. (975 hPa) | North (+g kg⁻¹ s⁻¹) | 1.456e+01 | 1.073e+01 | -2.866e+01 | 8.352e+00 |
| Moisture Flux Div. (975 hPa) | South (+g kg⁻¹ s⁻¹) | 3.522e+01 | -5.168e+00 | -1.359e+01 | -8.519e+00 |
| Moisture Flux Div. (975 hPa) | East (+g kg⁻¹ s⁻¹) | -7.553e+01 | -3.601e-01 | -1.143e+02 | -1.422e+00 |
| Moisture Flux Div. (975 hPa) | West (+g kg⁻¹ s⁻¹) | 5.112e+01 | -2.091e+00 | 3.617e+01 | 4.778e+00 |
| KE Advection (250 hPa) | North (+m² s⁻³) | 1.165e-03 | -4.546e-04 | 4.173e-03 | -3.210e-04 |
| KE Advection (250 hPa) | South (+m² s⁻³) | -1.058e-02 | -1.117e-03 | -9.517e-03 | 6.557e-05 |
| KE Advection (250 hPa) | East (+m² s⁻³) | -3.349e-03 | -6.259e-04 | 1.866e-03 | -1.415e-04 |
| KE Advection (250 hPa) | West (+m² s⁻³) | -1.805e-03 | -1.098e-04 | -3.653e-03 | 2.944e-04 |
| AFC (250 hPa) | North (+m² s⁻³) | 2.122e-03 | — | 5.687e-04 | — |
| AFC (250 hPa) | South (+m² s⁻³) | -5.140e-04 | — | -1.398e-03 | — |
| AFC (250 hPa) | East (+m² s⁻³) | 6.742e-04 | — | -3.255e-03 | — |
| AFC (250 hPa) | West (+m² s⁻³) | -1.881e-03 | — | 1.544e-03 | — |


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

- Besson, P., Fischer, L. J., Schemm, S., & Sprenger, M. (2021). A global analysis of the dry-dynamic forcing during cyclone growth and propagation. *Weather and Climate Dynamics*, 2(4), 991–1009. https://doi.org/10.5194/wcd-2-991-2021
- Banacos, P. C., & Schultz, D. M. (2005). The use of moisture flux convergence in forecasting convective initiation: Historical and operational perspectives. *Weather and Forecasting*, 20(3), 351–366.
- Čampa, J., & Wernli, H. (2012). A PV perspective on the vertical structure of mature midlatitude cyclones. *J. Atmos. Sci.*, 69(2), 725–740.
- Charney, J. G., & Stern, M. E. (1962). On the stability of internal baroclinic jets in a rotating atmosphere. *Journal of the Atmospheric Sciences*, 19(2), 159–172.
- Davis, C. A., & Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. *Mon. Wea. Rev.*, 119(8), 1929–1953.
- Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Q. J. R. Meteorol. Soc.*, 111(470), 877–946.
- Hoskins, B. J., & Valdes, P. J. (1990). On the existence of storm-tracks. *J. Atmos. Sci.*, 47(15), 1854–1864.
- Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *Journal of Meteorology*, 6(2), 105–122.
- Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *J. Atmos. Sci.*, 37(7), 1648–1654.
- Orlanski, I., & Katzfey, J. (1991). The life cycle of a cyclone wave in the Southern Hemisphere. Part I: Eddy energy budget. *J. Atmos. Sci.*, 48(17), 1972–1998.
- Orlanski, I., & Sheldon, J. P. (1993). A case of downstream baroclinic development over western North America. *Mon. Wea. Rev.*, 121(11), 2929–2950.
- Rayleigh, Lord (1880). On the stability, or instability, of certain fluid motions. *Proceedings of the London Mathematical Society*, s1-11(1), 57–72.
- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb." *Mon. Wea. Rev.*, 108(10), 1589–1606.
- Simmonds, I., & Lim, E.-P. (2009). Biases in the calculation of Southern Hemisphere mean baroclinic eddy growth rate. *Geophys. Res. Lett.*, 36(1), L01707.
- Solman, S. A., & Menéndez, C. G. (1998). Eddy kinetic energy budget in a limited area model. *Atmósfera*, 11(3), 163–181.

---

**Document auto-generated:** 2026-02-21 18:29  
**Author:** Danilo Couto de Souza
