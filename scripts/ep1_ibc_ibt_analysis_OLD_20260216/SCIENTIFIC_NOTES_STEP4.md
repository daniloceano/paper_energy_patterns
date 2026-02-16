# Step 4: Scientific Notes and Implementation Details

## Physical Constants and Quality Controls

### Constants (SI units)
```python
G = 9.80665              # Standard gravity (m s⁻²)
OMEGA = 7.292e-5         # Earth angular velocity (rad s⁻¹)
R_d = 287.0              # Gas constant dry air (J kg⁻¹ K⁻¹)
C_p = 1004.0             # Specific heat constant pressure (J kg⁻¹ K⁻¹)
KAPPA = R_d / C_p ≈ 0.286  # Poisson constant
P_0 = 100000.0           # Reference pressure 1000 hPa (Pa)
R_EARTH = 6.371e6        # Earth radius (m)
```

### Quality Control Thresholds
```python
MIN_LAT = 5.0            # Minimum |lat| for EGR (avoid f→0 at equator)
MAX_EGR_DAY = 5.0        # Maximum reasonable EGR (cap unphysical values)
MIN_N_SQUARED = 1e-6     # Minimum N² for stable stratification (s⁻²)
```

---

## Eady Growth Rate (EGR) - Detailed Derivation

### 1. Virtual Temperature Correction

Standard temperature T does not account for moisture effects on air density. Virtual temperature $T_v$ is the temperature dry air would need to have the same density as moist air at the same pressure:

$$T_v = T(1 + 0.61q)$$

where:
- $T$ = temperature (K)
- $q$ = specific humidity (kg/kg)
- 0.61 comes from the ratio of gas constants: $(R_v/R_d - 1) \approx 0.608$

**Physical meaning**: Moisture makes air less dense (water vapor lighter than dry air), so virtual temperature is higher than actual temperature in moist air.

**Typical magnitude**: For subtropical cyclones with q ~ 0.01 kg/kg, correction is ~6 K.

---

### 2. Virtual Potential Temperature

Potential temperature $\theta$ is the temperature an air parcel would have if brought adiabatically to reference pressure $p_0$ = 1000 hPa:

$$\theta = T \left(\frac{p_0}{p}\right)^\kappa$$

Virtual potential temperature combines both corrections:

$$\theta_v = T_v \left(\frac{p_0}{p}\right)^\kappa$$

**Physical meaning**: $\theta_v$ is conserved for adiabatic, reversible processes in moist air. It's the natural vertical coordinate for atmospheric stability.

---

### 3. Brunt-Väisälä Frequency (Static Stability)

The Brunt-Väisälä frequency N characterizes the frequency of vertical oscillations of a displaced air parcel in a stably stratified atmosphere:

$$N^2 = \frac{g}{\theta_v} \frac{\partial \theta_v}{\partial z}$$

**Derivation** (simplified):
1. Vertically displace air parcel by δz in environment with stratification $\partial\theta_v/\partial z$
2. Parcel conserves its $\theta_v$, environment has different $\theta_v$
3. Buoyancy force: $F = -g \frac{\delta\theta_v}{\theta_v}$
4. Equation of motion: $\frac{d^2(\delta z)}{dt^2} = -N^2 (\delta z)$
5. Solution: oscillation with frequency N (if N² > 0)

**Physical interpretation**:
- $N^2 > 0$: Stable stratification → parcel oscillates (gravity waves)
- $N^2 = 0$: Neutral stratification → parcel remains displaced
- $N^2 < 0$: Unstable stratification → parcel accelerates away (convection)

**Typical values**:
- Troposphere: N ~ 0.01 s⁻¹ (period ~ 10 min)
- Stratosphere: N ~ 0.02 s⁻¹ (period ~ 5 min)
- Our results: N ~ 0.0105 ± 0.0020 s⁻¹

**Computational implementation**:
```python
# 3-level centered finite difference
dtheta_v = theta_v[upper] - theta_v[lower]
dz = z[upper] - z[lower]
dtheta_v_dz = dtheta_v / dz

# N² = (g/θv)(∂θv/∂z)
N_squared = (G / theta_v[middle]) * dtheta_v_dz
N = sqrt(N_squared)  # only if N² > MIN_N_SQUARED
```

---

### 4. Vertical Wind Shear

Magnitude of the vertical wind shear vector:

$$\left|\frac{\partial \vec{V}}{\partial z}\right| = \sqrt{\left(\frac{\partial u}{\partial z}\right)^2 + \left(\frac{\partial v}{\partial z}\right)^2}$$

**Physical meaning**: Rate of change of horizontal wind with height. Strong shear tilts developing baroclinic waves, allowing efficient extraction of potential energy.

**Thermal wind balance**: In geostrophic balance, vertical shear is proportional to horizontal temperature gradient:

$$\frac{\partial \vec{V}_g}{\partial z} = -\frac{g}{fT} \hat{k} \times \nabla_p T$$

This links baroclinicity (temperature gradient) to vertical shear → both appear in EGR formula.

**Typical values**:
- Weak shear: < 0.003 s⁻¹
- Moderate: 0.003-0.006 s⁻¹
- Strong: > 0.006 s⁻¹
- Our results: 0.0051 ± 0.0015 s⁻¹ (moderate to strong)

---

### 5. Eady Growth Rate Formula

$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

**Derivation**: From Eady (1949) model of baroclinic instability on an f-plane with constant N and linear shear. The factor 0.31 comes from solving the eigenvalue problem for the most unstable wave.

**Dimensional analysis**:
- $[f] = s^{-1}$ (frequency)
- $[N] = s^{-1}$ (frequency)
- $[\partial V/\partial z] = s^{-1}$ (shear)
- $[\sigma] = \frac{s^{-1}}{s^{-1}} \cdot s^{-1} = s^{-1}$ (growth rate) ✓

**Physical interpretation**:

1. **$|f|$ (rotation)**: Provides restoring force for geostrophic balance. Higher latitude → stronger rotation → faster growth.

2. **$1/N$ (weak stability)**: Weaker static stability allows easier vertical displacement → faster growth. Factor $1/N$ means growth rate inversely proportional to stability.

3. **$|\partial V/\partial z|$ (shear)**: Tilts the wave, allowing efficient conversion of available potential energy to kinetic energy.

**Why 0.31?** From Eady model:
- Most unstable wavelength: $\lambda = 3.9 \frac{NH}{f}$ (H = scale height)
- Maximum growth rate: $\sigma_{max} = 0.31 \frac{f}{N} |\partial V/\partial z|$

**Conversion to day⁻¹**:
$$\sigma_{day} = \sigma_{s^{-1}} \times 86400 \, s/day$$

**Interpretation of values**:
- 0.5-1.0 day⁻¹: Moderate baroclinic instability
- 1.0-2.0 day⁻¹: Strong instability (typical cyclogenesis)
- 2.0-5.0 day⁻¹: Very strong instability (explosive cyclogenesis)
- > 5.0 day⁻¹: Likely unphysical (numerical issues or extreme events)

**Our results**: 
- Mean: 1.17-1.35 day⁻¹ (strong baroclinic instability)
- Max: 2.44-4.11 day⁻¹ (very strong in most intense regions)

---

## Rayleigh-Kuo (RK) Criterion - Detailed Derivation

### 1. Relative Vorticity

Vertical component of vorticity (rotation rate about vertical axis):

$$\zeta = \frac{\partial v}{\partial x} - \frac{\partial u}{\partial y}$$

**Spherical coordinates** (Earth is not flat!):
$$\frac{\partial}{\partial x} = \frac{1}{R_E \cos\phi} \frac{\partial}{\partial \lambda}$$
$$\frac{\partial}{\partial y} = \frac{1}{R_E} \frac{\partial}{\partial \phi}$$

where $\phi$ = latitude, $\lambda$ = longitude.

**Physical meaning**: Measures local spinning of air. Positive for counterclockwise rotation (cyclonic in NH, anticyclonic in SH).

**Typical values**:
- Synoptic systems: $|\zeta| \sim 10^{-5}$ s⁻¹
- Strong cyclones: $|\zeta| \sim 10^{-4}$ s⁻¹

---

### 2. Absolute Vorticity

Sum of relative vorticity and planetary vorticity:

$$\eta = \zeta + f$$

where $f = 2\Omega \sin\phi$ is the Coriolis parameter.

**Physical meaning**: Total rotation rate as seen from inertial (non-rotating) frame. Combines Earth's rotation (f) with atmospheric rotation (ζ).

**Why "absolute"?** It's the vorticity in an absolute (inertial) reference frame, not rotating with Earth.

**At 45°S**: $f \approx -10^{-4}$ s⁻¹ (negative in SH)

---

### 3. Rayleigh-Kuo Criterion

**Statement**: A necessary condition for barotropic instability is that the meridional gradient of absolute vorticity **changes sign** somewhere in the domain:

$$\frac{\partial \eta}{\partial y} = 0 \text{ somewhere, with } \frac{\partial \eta}{\partial y} < 0 \text{ on one side and } > 0 \text{ on other}$$

Or more simply: $\min(\partial\eta/\partial y) < 0$ AND $\max(\partial\eta/\partial y) > 0$

**Historical context**:
- **Rayleigh (1880)**: For inviscid parallel shear flow, instability requires $\frac{d^2U}{dy^2}$ to change sign
- **Kuo (1949)**: Extended to rotating fluids: criterion becomes sign change of $\frac{\partial \eta}{\partial y}$

**Physical mechanism**:

1. **Basic state**: Flow with absolute vorticity gradient $\partial\eta/\partial y$
2. **Perturbation**: Small wave-like disturbance
3. **Vorticity equation**: Perturbation vorticity evolves as $\frac{\partial \zeta'}{\partial t} + V \frac{\partial \zeta'}{\partial y} = -v' \frac{\partial \eta}{\partial y}$
4. **Growth**: If $\partial\eta/\partial y$ changes sign, perturbations can extract energy from basic flow

**Why sign change?** Counter-propagating Rossby waves on the two sides of the $\partial\eta/\partial y = 0$ point can phase-lock and amplify each other → instability.

**Interpretation**:
- Criterion is **necessary** but **not sufficient**
- Satisfaction means instability is *possible* (if other conditions met)
- Non-satisfaction means instability is *impossible*

---

### 4. Connection to Barotropic Energy Conversion

Barotropic conversion Ck represents kinetic energy transfer from eddies to mean flow (or vice versa):

$$C_k = -\overline{u'v'} \frac{\partial \bar{u}}{\partial y} - \overline{v'v'} \frac{\partial \bar{v}}{\partial y}$$

**Physical link to RK**:
- RK criterion indicates regions where wave growth can occur via horizontal shear
- Growing waves generate Reynolds stresses $\overline{u'v'}$
- These stresses cause momentum transport and energy conversion
- Negative Ck (common in cyclones) means energy flows from mean to eddies

**Our finding**: All 10 EP1 cyclones satisfy RK criterion at all scales (5°, 15°, 30°).
**Implication**: Favorable conditions for barotropic processes are widespread, not just locally confined.

---

## Results Interpretation

### Eady Growth Rate Statistics

| Domain | Size | Mean EGR (day⁻¹) | Std Dev | Max EGR (day⁻¹) |
|--------|------|------------------|---------|-----------------|
| Local | 5° | 1.237 | 0.441 | 2.442 ± 0.668 |
| Mesoscale | 15° | 1.353 | 0.295 | 3.518 ± 0.673 |
| Synoptic | 30° | 1.169 | 0.178 | 4.111 ± 0.643 |

**Key findings**:
1. **Strong baroclinic instability**: EGR ~ 1.2-1.4 day⁻¹ indicates rapid growth potential
2. **Scale consistency**: EGR values similar across scales → baroclinic processes are large-scale
3. **Spatial structure**: Maximum EGR increases with domain size (local max < mesoscale max < synoptic max)
   - Suggests strongest instability not concentrated at cyclone center
   - Rather, extends across broader synoptic environment
4. **Variability**: Higher variance at local scale (σ=0.44) than synoptic (σ=0.18)
   - Local conditions more variable case-to-case
   - Large-scale baroclinicity more consistent

**Comparison with literature**:
- Gyakum et al. (1989): EGR ~ 1-2 day⁻¹ for explosive cyclogenesis
- Our values (1.2-1.4 day⁻¹) consistent with intensifying extratropical cyclones

---

### Rayleigh-Kuo Criterion Results

| Domain | Size | Cases Satisfied | Percentage |
|--------|------|-----------------|------------|
| Local | 5° | 10/10 | 100% |
| Mesoscale | 15° | 10/10 | 100% |
| Synoptic | 30° | 10/10 | 100% |

**Key findings**:
1. **Universal satisfaction**: All EP1 cyclones meet necessary condition for barotropic instability
2. **Scale independence**: Criterion satisfied at all scales examined
3. **Contrary to hypothesis**: Initial expectation was local-scale phenomenon
   - Results show large-scale flow configuration supports barotropic processes
   - Suggests interaction between synoptic forcing and local cyclone dynamics

**Physical interpretation**:
- Large-scale flow pattern (jets, fronts) creates $\partial\eta/\partial y$ structure
- This structure persists across scales from cyclone core to synoptic environment
- Both local (cyclone-induced) and remote (synoptic) contributions to vorticity gradient

**Connection to Ck**:
- Mean Ck for EP1: -16.48 W/m² (strongest barotropic conversion of all EPs)
- RK satisfaction indicates this conversion occurs through barotropic instability mechanism
- Negative Ck means energy flows from mean flow → eddies → consistent with RK-based wave growth

---

## Computational Considerations

### Vertical Derivatives

Centered finite differences used for accuracy:

$$\frac{\partial f}{\partial z} \approx \frac{f_{i+1} - f_{i-1}}{z_{i+1} - z_{i-1}}$$

Requires 3 vertical levels (upper, middle, lower).

**Advantages**:
- Second-order accurate: $O(\Delta z^2)$
- Symmetric: no bias toward upper or lower level

**Pressure to height conversion**:
$$z = \frac{\Phi}{g}$$

where $\Phi$ = geopotential (m² s⁻²), downloaded from ERA5.

---

### Horizontal Derivatives

Spherical geometry accounted for using metric factors:

```python
dx = R_EARTH * cos(lat) * dlon_radians
dy = R_EARTH * dlat_radians

du_dy = gradient(u, axis=0) / dy
dv_dx = gradient(v, axis=1) / dx
```

**Why necessary?** 
- On sphere, 1° longitude ≠ 1° latitude in metric distance
- At equator: 1° lon ≈ 111 km, 1° lat ≈ 111 km
- At 45°: 1° lon ≈ 78 km, 1° lat ≈ 111 km

Failure to account for this introduces systematic errors in vorticity calculation.

---

### Quality Control Flags

1. **Near-equator masking**: $|lat| < 5°$ excluded
   - $f \to 0$ near equator makes $f/N$ term unstable
   
2. **Static stability check**: Require $N^2 > 10^{-6}$ s⁻²
   - Filters unstable stratification (convection, not baroclinic instability)
   - Also filters numerical noise in $\partial\theta_v/\partial z$

3. **EGR cap**: Values > 5.0 day⁻¹ set to NaN
   - Removes unphysical extremes from averaging
   - Can occur near topography, data gaps, or numerical issues

---

## References

**Eady Model**:
- Eady, E. T. (1949). Long waves and cyclone waves. Tellus, 1(3), 33-52.

**Rayleigh-Kuo Criterion**:
- Rayleigh, Lord (1880). On the stability of certain fluid motions. Proceedings of the London Mathematical Society, 11, 57-70.
- Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. Journal of Meteorology, 6(2), 105-122.

**Barotropic Instability in Cyclones**:
- Gyakum, J. R., et al. (1989). A case study of explosive cyclogenesis. Monthly Weather Review, 117(9), 2054-2077.

**Virtual Temperature**:
- Wallace, J. M., & Hobbs, P. V. (2006). Atmospheric Science: An Introductory Survey (2nd ed.). Academic Press.

**Lorenz Energy Cycle**:
- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. Tellus, 7(2), 157-167.
