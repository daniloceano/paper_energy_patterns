# EP1 Vertical Structure and Instability Analysis

## ⚠️ Important: Data Corrections

**Two corrections are applied to vertically-resolved LEC data from Zenodo (DOI: 10.5281/zenodo.18243447):**

1. **Ca (Baroclinic Conversion)**: Sign inversion
   - `Ca_corrected = -Ca_raw`
   - Reason: Old LorenzCycleToolkit version saved `Ca_level.csv` with opposite sign

2. **Ck (Barotropic Conversion)**: Division by gravity
   - `Ck_corrected = Ck_raw / 9.8` (g = 9.8 m/s²)
   - Reason: Old LorenzCycleToolkit version saved `Ck_level.csv` without gravity normalization

**Validation**: These corrections were validated by comparing manual vertical integration with pre-computed values. See `validate_step2.py` for detailed validation analysis showing perfect agreement after corrections (Mean Absolute Error reduced to ~0.0 W/m²).

**Note**: Current version of LorenzCycleToolkit has fixed these issues. These corrections are specific to the Zenodo dataset used in this paper.

---

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
Select EP1 cyclones that satisfy spatial criteria for instability analysis:
- Belongs to EP1 (cluster 0 - strongest energetic conversions)
- Complete lifecycle: incipient → intensification → mature → decay
- Intensification center (temporal midpoint) within specified domain

**Domain Selection Rationale**:
- Current domain: 60°W-45°W, 45°S-30°S (southwestern Atlantic)
- Ensures environmental homogeneity across all selected cyclones
- Avoids mixing different synoptic regimes (e.g., La Plata vs. far offshore)
- Critical for meaningful comparison of instability diagnostics (RK, EGR)
- All cyclones experience similar SST gradients, baroclinicity, and large-scale flow

**Selection Method**:
- NOT intensity-based (no "top N" selection)
- Domain-based: ALL cyclones meeting criteria are included
- Provides representative sample of EP1 dynamics in target region
- Sample size: ~50 cyclones (varies with domain definition)

**Output**: CSV with all selected track IDs, genesis info, and vorticity statistics

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

**Data Corrections Applied**:

⚠️ **CRITICAL**: Two corrections are applied to vertically-resolved LEC data:

1. **Ca (Baroclinic Conversion)**: Sign inversion
   - `Ca_corrected = -Ca_raw`
   - Reason: Old LorenzCycleToolkit version saved `Ca_level.csv` with opposite sign

2. **Ck (Barotropic Conversion)**: Division by gravity
   - `Ck_corrected = Ck_raw / g` (g = 9.8 m/s²)
   - Reason: Old LorenzCycleToolkit version saved `Ck_level.csv` without gravity normalization

**Validation**: These corrections were validated by comparing manual vertical integration of level data with pre-computed integrated values from the toolkit. See `validate_step2.py` for detailed validation analysis and comparison plots.

**Note**: Current version of LorenzCycleToolkit has fixed these issues. These corrections are only needed for the Zenodo dataset (DOI: 10.5281/zenodo.18243447) used in this paper, which was generated with an older version of the toolkit.

**Physical Interpretation**:
- **Ca maximum**: Level of maximum baroclinic energy conversion, typically associated with the level of maximum temperature gradient
- **Ck maximum**: Level of maximum barotropic energy conversion, typically associated with horizontal wind shear and momentum flux convergence

**Output**: 
- Critical pressure levels (median across cases)
- Boxplots showing distribution
- List of levels to download (including ±1 level for vertical derivatives)

**Scripts**: 
- `step2_vertical_levels_analysis.py` - Main analysis (with corrections applied)
- `validate_step2.py` - Validation script that identified necessary corrections

---

### 3. ERA5 Data Acquisition

Download ERA5 reanalysis data ONLY for the identified critical pressure levels, covering **only the intensification phase**:

**Required Variables**:
- **u_component_of_wind**: Zonal wind (for vorticity in RK, wind shear in EGR)
- **v_component_of_wind**: Meridional wind (for vorticity in RK, wind shear in EGR)
- **temperature**: Temperature (for Brunt-Väisälä frequency in EGR)
- **geopotential**: Geopotential height (for vertical derivatives in EGR)
- **specific_humidity**: Specific humidity (for virtual temperature correction in EGR)

**Pressure Levels**:
- Level of Ca maximum ± 1 level (for centered finite differences in EGR)
- Level of Ck minimum ± 1 level (for RK criterion analysis)
- **250 hPa**: Upper-level jet stream (for composite analysis and synoptic context)

**Rationale**: 
- Instead of downloading all 21 pressure levels, download only ~3-7 levels needed
- Saves significant download time and storage space
- EGR requires vertical derivatives, hence ±1 level for centered differences
- 250 hPa provides upper-tropospheric jet structure for composite figures

**Spatial Coverage Strategy**:
- **Single domain per cyclone**: Track extent during intensification phase + 15° buffer on all sides
- **Rationale**: This buffer allows for 30°×30° analysis (largest domain) while reusing the same data for smaller domains (5°×5° and 15°×15°)
- **Efficiency**: Avoids redundant downloads of nested domains

**Temporal Coverage**:
- **Only intensification phase** of each cyclone (all time steps)
- 6-hourly data
- **Central time step** identified for instability analysis

**Note**: This step should be run on a remote server with good internet connection and storage capacity. Requires CDS API credentials.

**Script**: `step3_download_era5.py`

---

### 4. Instability Diagnostics

This step computes atmospheric instability diagnostics using ERA5 data to quantify barotropic and baroclinic instability processes during cyclone intensification.

**Script**: `step4_compute_instabilities.py`

**Key Features**:
- Multi-scale analysis (5°×5°, 15°×15°, 30°×30° domains)
- Physics-based quality controls
- Virtual temperature correction for accurate static stability
- Centered finite differences for vertical derivatives
- Individual and consolidated results

#### 4.1 Eady Growth Rate (EGR) - Baroclinic Instability

**Formula**:
$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

where:
- $f = 2\Omega \sin(\phi)$ is the Coriolis parameter
- $N = \sqrt{\frac{g}{\theta_v}\frac{\partial \theta_v}{\partial z}}$ is the Brunt-Väisälä frequency (static stability)
- $\theta_v = T_v \left(\frac{p_0}{p}\right)^\kappa$ is the virtual potential temperature
- $T_v = T(1 + 0.61q)$ is the virtual temperature (moisture-corrected)
- $\left|\frac{\partial \vec{V}}{\partial z}\right| = \sqrt{\left(\frac{\partial u}{\partial z}\right)^2 + \left(\frac{\partial v}{\partial z}\right)^2}$ is the vertical wind shear magnitude

**Computational Details**:
- Requires 3 vertical levels (upper, middle, lower) for centered finite differences
- Computed at critical level where Ca is maximum (baroclinic conversion peak)
- Virtual temperature includes moisture effect: reduces density, affects static stability
- Quality controls:
  - Mask regions with $|lat| < 5°$ (near-equator, f→0)
  - Require $N^2 > 10^{-6}$ s⁻² (stable stratification)
  - Cap EGR at 5 day⁻¹ (remove unphysical values)

**Physical Interpretation**:
- EGR quantifies the e-folding growth rate of baroclinic waves
- Higher EGR → stronger baroclinic instability
- Typical midlatitude values: 0.5-2.0 day⁻¹
- During cyclogenesis: can reach 3-5 day⁻¹
- Depends on three factors:
  1. **Rotation** (f): Stronger at higher latitudes
  2. **Static stability** (N): Weaker stability → larger EGR
  3. **Vertical shear**: Stronger shear → larger EGR

**Output Variables** (per domain):
- `egr_<domain>_mean`: Domain-averaged EGR (day⁻¹)
- `egr_<domain>_max`: Maximum EGR in domain (day⁻¹)
- `N_<domain>`: Mean static stability (s⁻¹)
- `shear_<domain>`: Mean vertical wind shear magnitude (s⁻¹)

---

#### 4.2 Rayleigh-Kuo (RK) Criterion - Barotropic Instability

**Criterion**:
Barotropic instability occurs when the meridional gradient of absolute vorticity **changes sign** within the domain:

$$\frac{\partial \eta}{\partial y} = \frac{\partial (\zeta + f)}{\partial y}$$

must have both positive and negative values in the domain.

where:
- $\eta = \zeta + f$ is the absolute vorticity
- $\zeta = \frac{\partial v}{\partial x} - \frac{\partial u}{\partial y}$ is the relative vorticity
- $f = 2\Omega \sin(\phi)$ is the Coriolis parameter (planetary vorticity)

**Two Analysis Methods**:

1. **2D Field Analysis**: Checks criterion in the full spatial (latitude-longitude) field
   - Captures local variations and mesoscale structures
   - Most sensitive to small-scale features

2. **Zonal Mean Analysis**: Checks criterion after averaging in longitude
   - Formula: $\overline{\frac{\partial \eta}{\partial y}}$ where overbar denotes zonal mean
   - Reveals large-scale meridional structure
   - Filters out zonal asymmetries
   - Tests if barotropic instability is fundamentally a meridional phenomenon

**Computational Details**:
- Computed at critical level where Ck is minimum (barotropic conversion peak)
- Uses spherical coordinate metric factors for accurate derivatives:
  - $\frac{\partial}{\partial x} = \frac{1}{R_E \cos\phi} \frac{\partial}{\partial \lambda}$
  - $\frac{\partial}{\partial y} = \frac{1}{R_E} \frac{\partial}{\partial \phi}$
- Criterion satisfied if $\min(\frac{\partial \eta}{\partial y}) < 0$ AND $\max(\frac{\partial \eta}{\partial y}) > 0$

**Physical Interpretation**:
- RK criterion is a **necessary condition** for barotropic instability
- Sign change of $\frac{\partial \eta}{\partial y}$ allows wave energy to extract kinetic energy from mean flow
- **2D analysis**: Tests if criterion is met anywhere in domain (most inclusive)
- **Zonal mean**: Tests if large-scale meridional flow structure supports barotropic instability
- Both satisfied → instability supported at all scales

**Output Variables** (per domain):
- `rk_<domain>_satisfied`: Boolean, True if 2D criterion met
- `rk_<domain>_satisfied_zonal`: Boolean, True if zonal mean criterion met
- `rk_<domain>_min`: Minimum value of ∂η/∂y in 2D field (s⁻¹ m⁻¹)
- `rk_<domain>_max`: Maximum value of ∂η/∂y in 2D field (s⁻¹ m⁻¹)
- `rk_<domain>_min_zonal`: Minimum value of ∂η/∂y in zonal mean (s⁻¹ m⁻¹)
- `rk_<domain>_max_zonal`: Maximum value of ∂η/∂y in zonal mean (s⁻¹ m⁻¹)

---

#### 4.3 Multi-Scale Analysis Strategy

**Domain Definitions**:
- **Local** (5°×5°): Cyclone core, ~550 km × 550 km at 45°S
- **Mesoscale** (15°×15°): Regional environment, ~1650 km × 1650 km
- **Synoptic** (30°×30°): Large-scale flow, ~3300 km × 3300 km

**Hypothesis Testing**:
- **Baroclinic instability (EGR)**: Expected to be consistent across scales (large-scale phenomenon)
- **Barotropic instability (RK)**: Expected to be strongest at local scale, weakening at larger scales

**Implementation**:
- All three domains extracted from single ERA5 download (30°+buffer)
- Analysis performed at central time step of intensification phase
- Ensures direct comparison across scales using identical atmospheric state

---

#### 4.4 Results Summary

**From ~50 EP1 cyclones analyzed** (all within domain 60°W-45°W, 45°S-30°S):

**Eady Growth Rate** (mean ± std day⁻¹):
- Local (5°): 1.237 ± 0.441 day⁻¹
- Mesoscale (15°): 1.353 ± 0.295 day⁻¹
- Synoptic (30°): 1.169 ± 0.178 day⁻¹

**Interpretation**:
- All values indicate **moderate to strong baroclinic instability**
- EGR ~ 1.2-1.4 day⁻¹ typical of intensifying midlatitude cyclones
- Maximum EGR reaches 3-5 day⁻¹ in most intense regions
- Relatively consistent across scales (supports large-scale nature)

**Rayleigh-Kuo Criterion**:
- Local (5°): 10/10 cases (100%)
- Mesoscale (15°): 10/10 cases (100%)
- Synoptic (30°): 10/10 cases (100%)

**Rayleigh-Kuo Criterion (Zonal Mean)**:
- Local (5°): 10/10 cases (100%)
- Mesoscale (15°): 10/10 cases (100%)
- Synoptic (30°): 10/10 cases (100%)

**Interpretation**:
- **All EP1 cyclones satisfy RK criterion** during intensification
- Criterion met at **all spatial scales** in both 2D field and zonal mean
- Indicates widespread favorable conditions for barotropic instability
- Zonal mean analysis confirms large-scale meridional structure supports instability
- Both analyses satisfied → instability not limited to local eddies
- Contrary to initial hypothesis: not confined to local scale
- Suggests large-scale flow configuration supports barotropic processes

**Output Files**:
- `results/ep1_vertical/instabilities/<track_id>_instabilities.csv` (individual cases)
- `results/ep1_vertical/instabilities_all.csv` (consolidated)
- `results/ep1_vertical/instabilities_summary.csv` (summary statistics)

**Consolidation Script**: `consolidate_instability_results.py`

---

### 5. Visualization

This step creates publication-quality figures for Scientific Reports standard.

**Script**: `step5_create_figures.py`

**Requirements**: MetPy (for baroclinic potential vorticity), Cartopy (for maps)

#### Figure Structure

For each domain (5°, 15°, 30°) and each cyclone (+ composite), a 4-panel figure is created:

**Panel (a): ∂η/∂y 2D Map (RK Criterion)**
- Filled contours of meridional gradient of absolute vorticity
- Computed at Ck minimum level (barotropic conversion peak)
- Colormap: RdBu_r (red=positive, blue=negative)
- Black contour at zero separating positive/negative regions
- Cyclone center marked with star
- Indicates regions satisfying RK criterion

**Panel (b): Zonal Mean ∂η/∂y Profile**
- Vertical profile showing $\overline{\partial\eta/\partial y}$ vs latitude
- Filters out zonal asymmetries
- Zero line marked
- Cyclone center latitude marked
- For composite: individual cases in gray, ensemble mean in blue
- Tests meridional structure of barotropic instability

**Panel (c): Baroclinic Potential Vorticity**
- PV computed using MetPy's `potential_vorticity_baroclinic` function
- Formula: $\text{PV} = -g(\zeta + f)\frac{\partial\theta}{\partial p}$
- Computed at Ca maximum level (baroclinic conversion peak)
- Uses xarray DataArrays for proper coordinate handling
- Colormap: RdYlBu_r
- Units: $10^{-6}$ K m² kg⁻¹ s⁻¹ (PVU × 10⁻⁶)
- Higher PV indicates stronger baroclinic instability potential
- Typical values: -10 to +2 PVU for midlatitude cyclones

**Panel (d): Eady Growth Rate**
- EGR computed at Ca maximum level
- Filled contours in YlOrRd colormap
- Domain-mean EGR annotated in text box
- Units: day⁻¹
- Quantifies baroclinic instability strength

#### Output Organization

```
figures/ep1_vertical/
├── individual/
│   ├── 19790644_local.png       # N tracks × 3 domains = 3N figures
│   ├── 19790644_mesoscale.png
│   ├── 19790644_synoptic.png
│   └── ...
├── composite/
│   ├── composite_local.png      # 3 composite figures
│   ├── composite_mesoscale.png
│   └── composite_synoptic.png
└── tracks/
    ├── selected_tracks_overview.png  # All selected tracks together
    ├── track_19790644_domains.png
    ├── track_19820917_domains.png
    └── ...                      # N individual track maps
```

**Total**: 3N + 3 + N + 1 figures (where N ≈ 50 is the number of selected cyclones)
- Individual 4-panel figures: 3N (3 domains × N cyclones)
- Composite figures: 3 (one per domain)
- Track overview: 1 (all tracks on single map)
- Individual track maps: N (one per cyclone)

#### 5.2 Cyclone Track Visualization

**Overview Map** (`tracks_overview.png`):
- All 10 cyclone tracks plotted on a single map
- Complete tracks shown as thin lines (different colors for each cyclone)
- **Intensification period highlighted** as thick lines (analysis time window)
- Genesis points marked with circles
- South Atlantic domain (-70°W to 20°E, -60°S to -10°S)
- Color-coded by track_id for easy identification

**Individual Track Maps** (`track_<id>_domains.png`):
- One map per cyclone showing:
  - Complete track from genesis to lysis (thin blue line)
  - **Intensification period highlighted** (thick red line, analysis time window)
  - Genesis point (green circle)
  - Central time step marked with red star (analysis center)
  - Analysis domains overlaid as colored boxes:
    - **Red**: 5°×5° (local domain)
    - **Orange**: 15°×15° (mesoscale domain)
    - **Blue**: 30°×30° (synoptic domain)
  - Map extent: 40°×40° centered on analysis position
  - Coastlines, borders, land/ocean features for geographic reference

**Purpose**:
- Provides spatial context for instability analysis
- Shows cyclone trajectories and genesis regions
- **Highlights intensification period** used for instability diagnostics
- Visualizes domain sizes relative to track length and environment
- Links track position to downloaded ERA5 data extent
- Helps interpret why certain scales show stronger instability signals

#### Figure Quality

- **DPI**: 300 (publication quality)
- **Format**: PNG (as requested, no PDF)
- **Style**: Scientific Reports standard
  - Sans-serif fonts
  - 10pt base font size
  - Clear axis labels with units
  - Colorbars with descriptive labels
  - Panel labels (a, b, c, d)
  - Informative titles

#### Physical Interpretation from Figures

**∂η/∂y Maps (RK)**: 
- Sign changes visible as red-blue transitions
- Crossing of zero contour indicates criterion satisfied
- Spatial structure shows where barotropic conversion most active

**Zonal Mean Profiles**:
- Reveals large-scale meridional structure
- All cases show sign changes → criterion met at all scales
- Ensemble mean confirms systematic meridional gradient reversal

**Baroclinic PV**:
- Higher PV associated with stronger temperature gradients
- PV maxima coincide with regions of active baroclinic conversion
- Spatial distribution shows baroclinic instability structure

**EGR Maps**:
- Spatial distribution of baroclinic instability strength
- Maximum values (3-5 day⁻¹) indicate very strong instability
- Domain means (1.2-1.4 day⁻¹) consistent with intensifying cyclones
- Relatively uniform across domains → large-scale phenomenon

---

## Expected Results

1. **Sample Size**: 
   - Domain-based selection yields ~50 EP1 cyclones
   - All within specified domain (60°W-45°W, 45°S-30°S)
   - Environmentally homogeneous sample for robust statistics

2. **Vertical Structure**: 
   - Ca maximum expected in mid-troposphere (500-700 hPa)
   - Ck maximum expected in upper-troposphere (300-500 hPa) or near surface

3. **Barotropic Instability**:
   - RK criterion expected to be satisfied during intensification
   - Multi-scale analysis reveals whether instability is local or large-scale
   - Initial hypothesis: local phenomenon, but results show large-scale presence

4. **Baroclinic Instability**:
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
├── step1_select_cases.py              # Domain-based case selection (~50 EP1 cyclones)
├── step2_vertical_levels_analysis.py  # Analyze LEC data to identify critical levels (with corrections)
├── validate_step2.py                  # Validation script for vertical integration corrections
├── step3_download_era5.py             # ERA5 data download at identified levels (run on server)
├── step4_compute_instabilities.py     # Calculate RK and EGR
├── step5_create_figures.py            # Generate all figures
└── run_all.py                         # Sequential execution of all steps
```

**Execution Order**:
1. `step1_select_cases.py` - Select EP1 cyclones within specified domain (~50 cases)
2. `step2_vertical_levels_analysis.py` - Analyze existing LEC data to identify critical levels (applies validated corrections)
3. `step3_download_era5.py` - Download ERA5 data at identified levels (requires CDS API)
4. `step4_compute_instabilities.py` - Compute RK and EGR diagnostics
5. `step5_create_figures.py` - Generate all publication figures

**Optional**:
- `validate_step2.py` - Validates vertical integration corrections (already run, corrections applied in step2)

### Validation Script (`validate_step2.py`)

This script validates that vertically-resolved LEC data correctly integrates to match pre-computed values. It performs the following:

**Purpose**:
- Load `Ca_level.csv` and `Ck_level.csv` for EP1 cyclones
- Manually integrate over pressure levels using trapezoidal rule
- Compare with pre-computed integrated values from LorenzCycleToolkit
- Identify necessary corrections to match pre-computed values

**Findings**:
The validation identified two necessary corrections:
1. **Ca**: Sign inversion required (`Ca_corrected = -Ca_raw`)
2. **Ck**: Division by gravity required (`Ck_corrected = Ck_raw / 9.8`)

**Output**:
- Comparison boxplots showing raw vs. corrected vs. original values
- Detailed statistics (mean absolute error before/after corrections)
- Saved to `figures/exploratory/validation_vertical_integration.png`

**Why These Corrections?**
An older version of LorenzCycleToolkit saved vertically-resolved data (`Ca_level.csv`, `Ck_level.csv`) with different conventions than the integrated values. These corrections ensure consistency. The current version of the toolkit has fixed these issues, but the Zenodo dataset used in this paper was generated with the old version.

## Data Requirements

### Input
- `results/cluster/kmeans_clustered_data.csv`: EP1 cyclone classifications
- `data/tracks_SAt_filtered_with_energetics_processed.csv`: Track and energy data
- `data/temp_lec_zenodo/LEC_Results_energetic-patterns/`: LEC data from Zenodo (DOI: 10.5281/zenodo.18243447)
- ERA5 reanalysis data (downloaded by step3)

### Output
- `results/ep1_vertical/`: Numerical results (vertical profiles, statistics)
- `figures/ep1_vertical/`: Publication-quality figures
- `figures/exploratory/validation_vertical_integration.png`: Validation plots

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
