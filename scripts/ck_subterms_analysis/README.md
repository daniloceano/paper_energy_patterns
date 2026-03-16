# Ck Subterms Analysis: Barotropic Energy Conversion Decomposition

## Scientific Motivation

The barotropic conversion term C_K (also written Ck) represents the transfer of kinetic energy
between cyclone-scale eddies and the large-scale mean flow. In the limited-area, semi-Lagrangian
Lorenz Energy Cycle framework used here, C_K enters the eddy kinetic energy (K_E) equation as a
positive source: when C_K > 0 the mean flow feeds the eddies (barotropic instability, K_Z → K_E);
when C_K < 0 the eddies feed the mean flow (K_E → K_Z).

The full expression for C_K (vertically integrated from pressure level p_t to p_b; paper.tex Eq.
for C_K) is:

$$C_K = \int_{p_t}^{p_b} \frac{1}{g} \left[
  \underbrace{\frac{\cos\phi}{a}(u)'(v)'\frac{\partial}{\partial\phi}\!\left(\frac{[u]}{\cos\phi}\right)}_{\text{(A)}}
+ \underbrace{\frac{(v)'^2}{a}\frac{\partial [v]}{\partial\phi}}_{\text{(B)}}
+ \underbrace{\frac{\tan\phi}{a}(u)'^2[v]}_{\text{(C)}}
+ \underbrace{(\omega)'(u)'\frac{\partial [u]}{\partial p}}_{\text{(D)}}
+ \underbrace{(\omega)'(v)'\frac{\partial [v]}{\partial p}}_{\text{(E)}}
\right] dp$$

where square brackets and primes denote area means and deviations, respectively, and
g = 9.8 m s⁻².

### Physical Interpretation of Subterms (from paper.tex)

| Subterm | Physical mechanism |
|---------|-------------------|
| Term (A) | Eddy momentum flux linked to the meridional (N–S) gradient of zonal wind — most directly associated with barotropic instability |
| Term (B) | Meridional flux of eddy KE associated with meridional wind and its meridional gradient |
| Term (C) | Meridional flux of zonal eddy KE (tan-φ curvature term) |
| Term (D) | Zonal and vertical flux associated with the vertical shear of zonal wind |
| Term (E) | Meridional and vertical flux associated with the vertical shear of meridional wind |

### Sign Convention (authoritative source: paper.tex)

$$\frac{\partial K_E}{\partial t} = BK_E + C_E + C_K + B\Phi_E - D_E$$

- **C_K < 0**: K_E → K_Z (eddies export energy to mean flow). EP1 cyclones have mean C_K ≈ −16.5 W m⁻² — they are the strongest energy exporters among all Energy Patterns.
- **C_K > 0**: K_Z → K_E (mean flow accelerates eddies; barotropic instability).

Note: EP1 cyclones are NOT driven by barotropic instability (that would require C_K > 0). Instead, they have large negative C_K, reflecting intense eddy-to-mean energy export. The term "barotropic conversion" refers to the magnitude of C_K, regardless of sign.

### Energy Pattern 1 (EP1) Characteristics

EP1 cyclones exhibit the strongest energetic conversions in the Southwestern Atlantic:
- **Mean C_K**: −16.48 W m⁻² (largest-magnitude barotropic conversion among all patterns)
- **Frequency**: 444 cyclones (11.6% of total)
- **Analysis scope**: ALL EP1 cyclones (no spatial restriction)
- **Dominant level**: C_K is most negative at ~350 hPa (from paper.tex Fig. S3)

## Research Questions

1. **Which C_K subterm dominates the eddy-to-mean energy export during EP1 intensification?**
   - Dominance = subterm with minimum (most negative) intensification-phase mean
   - Results: Ck⁽ᴱ⁾ (Term E, 43%), Ck⁽ᴮ⁾ (Term B, 38%), Ck⁽ᴬ⁾ (Term A, 19%)

2. **Is genesis location linked to the dominant C_K subterm?**
   - Genesis density maps + normalized anomaly maps

3. **How does the updated LorenzCycleToolkit decomposition compare with the Zenodo dataset?**
   - Validation of new LEC results against Zenodo aggregated C_K
   - Internal consistency: subterm sum ≈ total C_K

## Methodology

### Prerequisites

**IMPORTANT**: This analysis requires the cluster analysis results:
- `results/cluster/kmeans_clustered_data.csv` (produced by `scripts/cluster_analysis_energy_patterns/`)
- This file contains the EP assignments for all cyclones, including all 444 EP1 cyclones
- **No spatial restriction** — all EP1 cyclones regardless of genesis location are included

### Workflow Overview

```
Step 1: Prepare Track Files
    ↓
Step 2: Run LorenzCycleToolkit (automated ERA5 download & LEC computation)
    ↓
Step 3: Extract and Analyze Ck Subterms
    ↓
Step 4: Compare Lifecycle Evolution
    ↓
Step 5: Statistical Analysis and Visualization
```

---

### Step 1: Prepare Track Files for LorenzCycleToolkit

**Objective**: Convert ALL EP1 cyclone tracks to LorenzCycleToolkit input format.

**Input**:
- `results/cluster/kmeans_clustered_data.csv` — EP assignments from cluster analysis (444 EP1 cyclones)
- Main track database (via `load_tracks()`)

**Output Format** (one file per cyclone):
```
time;Lat;Lon
2005-08-08-0000;-22.5;-45.0
2005-08-08-0600;-23.0;-44.5
2005-08-08-1200;-23.5;-44.0
...
```

**File Naming**: `track_{track_id}.txt`
- Example: `track_20070643.txt`

**Output Directory**: `data/ck_analysis/tracks/`

**Key Considerations**:
- Time format: `YYYY-MM-DD-HHMM` (no spaces, dash before time)
- Header: `time;Lat;Lon` (capitalized)
- Coordinates: Latitude and Longitude in decimal degrees
- Delimiter: Semicolon (`;`) with NO spaces
- Data source: Full cyclone lifecycle (all phases, all timesteps)
- Temporal resolution: 3-hourly (matches project configuration)

**Script**: `step1_prepare_tracks.py`

---

### Step 2: Run LorenzCycleToolkit with ERA5 Download

**Objective**: Compute Lorenz Energy Cycle with full term decomposition using the updated toolkit version.

**LorenzCycleToolkit Configuration**:
```python
# Example configuration (to be adjusted)
from LorenzCycleToolkit import LorenzCycleAnalysis

# Initialize analysis
lec = LorenzCycleAnalysis(
    track_file='data/ck_analysis/tracks/track_20070643.txt',
    dataset='ERA5',
    auto_download=True,  # Automatically download ERA5 data
    pressure_levels='standard',  # All standard pressure levels
    spatial_filter='moving_box',  # Follow cyclone center
    box_size=15,  # 15° × 15° domain (consistent with EP1 analysis)
    decompose_terms=True  # Enable full term decomposition
)

# Run analysis
lec.compute()
lec.save_results('results/ck_analysis/lec_results/')
```

**Key Features of Updated Toolkit**:
- **Automatic ERA5 download**: No manual CDS API interaction needed
- **Term decomposition**: Separates Ck into individual subterms
- **Vertical resolution**: Maintains level-by-level information
- **Phase identification**: Uses CycloPhaser for lifecycle detection

**Output Structure** (per cyclone):
```
results/ck_analysis/lec_results/{track_id}_ERA5_track/
├── periods.csv              # Lifecycle phases
├── results.csv              # Integrated terms (all phases)
├── Ck_level.csv            # Total Ck by pressure level
├── Ck_uv_level.csv         # Horizontal momentum flux term
├── Ck_uw_level.csv         # Vertical momentum flux (zonal) term
├── Ck_vw_level.csv         # Vertical momentum flux (meridional) term
├── Ca_level.csv            # Baroclinic conversion (for reference)
└── ...                     # Other energy terms
```

**Computational Requirements**:
- **Storage**: ~500 MB per cyclone (ERA5 data + results)
- **Time**: ~30-60 min per cyclone (depending on lifecycle length)
- **Total for ALL EP1**: ~444 cyclones × 500 MB = ~222 GB
- **Processing**: Can be parallelized across cyclones

**Script**: `step2_run_lec_toolkit.py` (wrapper script)
- Iterates through prepared tracks
- Submits LorenzCycleToolkit jobs
- Monitors progress and handles errors

---

### Step 3: Extract and Analyze Ck Subterms

**Objective**: Load LEC results and extract Ck subterm contributions for all EP1 cyclones.

**Analysis Tasks**:

1. **Load Ck Subterms by Level**:
   - `Ck_uv(p)`: Horizontal momentum flux contribution
   - `Ck_uw(p)`: Vertical momentum flux (zonal) contribution
   - `Ck_vw(p)`: Vertical momentum flux (meridional) contribution
   - Validate: `Ck_total ≈ Ck_uv + Ck_uw + Ck_vw`

2. **Phase-Specific Analysis**:
   - Extract values during intensification phase only
   - Compare with mature and decay phases
   - Compute phase-averaged profiles

3. **Vertical Structure**:
   - Identify pressure level of maximum contribution for each subterm
   - Analyze vertical distribution (surface → upper troposphere)
   - Compare with Ck minimum level from Step 2 of EP1 analysis

4. **Relative Importance Metrics**:
   - Percentage contribution: $\frac{Ck_{subterm}}{Ck_{total}} \times 100\%$
   - Dominant term identification (largest absolute contribution)
   - Term consistency across cyclones (standard deviation)

**Output**:
- `results/ck_analysis/subterms_by_cyclone.csv` - Individual cyclone subterm values
- `results/ck_analysis/subterms_statistics.csv` - Ensemble statistics
- `results/ck_analysis/vertical_profiles.csv` - Mean profiles by phase

**Script**: `step3_extract_subterms.py`

---

### Step 4: Lifecycle Evolution Analysis

**Objective**: Quantify how Ck subterm contributions change throughout the cyclone lifecycle.

**Methodology**:

1. **Temporal Evolution**:
   - Time series of each subterm throughout lifecycle
   - Smoothed profiles (24h running mean)
   - Identification of transition points between phases

2. **Phase Composites**:
   - Mean subterm values by phase (incipient, intensification, mature, decay)
   - Vertical structure evolution (2D: pressure × phase)
   - Statistical significance testing (phase-to-phase changes)

3. **Energetic Pathway Analysis**:
   - Dominant mechanism identification by phase
   - Transitions: Which subterm leads intensification onset?
   - Which subterm sustains mature phase?

**Visualization**:
- Time-height cross-sections (pressure × time)
- Phase-composite boxplots (subterm × phase)
- Stacked area charts (relative contribution evolution)

**Output**:
- `figures/ck_analysis/lifecycle_evolution.png`
- `figures/ck_analysis/phase_composites.png`
- `results/ck_analysis/lifecycle_statistics.csv`

**Script**: `step4_lifecycle_analysis.py`

---

### Step 5: Statistical Analysis and Validation

**Objective**: Validate results against previous analysis and identify patterns.

**Validation**:

1. **Comparison with Zenodo Dataset**:
   - Compare aggregated Ck from new analysis with old results
   - Expected: Close agreement in total Ck values
   - Difference: New analysis provides subterm breakdown

2. **Consistency Checks**:
   - Mass budget conservation (total energy should be conserved)
   - Term magnitude reasonableness (compare with literature values)
   - Spatial averaging consistency

**Statistical Tests**:

1. **Inter-cyclone Variability**:
   - Standard deviation of subterm contributions
   - Coefficient of variation (CV = σ/μ)
   - Identification of outlier cyclones

2. **Regional/Seasonal Patterns**:
   - Subterm contributions vs. genesis latitude
   - Summer vs. winter differences (if data sufficient)
   - Track orientation effects (NE vs. SE propagation)

3. **Correlation Analysis**:
   - Subterm vs. cyclone intensity (maximum vorticity)
   - Subterm vs. lifecycle duration
   - Cross-correlations between subterms

**Output**:
- `figures/ck_analysis/validation_plots.png`
- `figures/ck_analysis/statistical_summary.png`
- `results/ck_analysis/final_report.txt`

**Script**: `step5_statistical_analysis.py`

---

## Expected Results

### Hypothesis 1: Horizontal Momentum Flux Dominance

**Expectation**: The horizontal momentum flux term ($-\overline{u'v'}\frac{\partial \overline{u}}{\partial y}$) will dominate Ck during intensification.

**Rationale**:
- EP1 cyclones occur in regions of strong baroclinicity
- Associated with strong meridional temperature gradients
- Thermal wind balance implies strong vertical wind shear
- Eddy momentum fluxes (u'v') transport momentum meridionally
- This is the "classic" barotropic conversion mechanism

**Expected Magnitude**: ~70-80% of total Ck

---

### Hypothesis 2: Vertical Level Structure

**Expectation**: Maximum Ck contributions occur at mid-tropospheric levels (500-700 hPa).

**Rationale**:
- Previous analysis shows Ck minimum at ~500-600 hPa
- This level corresponds to:
  - Maximum meridional wind shear ($\partial u/\partial y$)
  - Jet stream level in South Atlantic
  - Level of maximum eddy kinetic energy

**Implication**: Barotropic conversion is primarily a mid-tropospheric process in EP1 cyclones

---

### Hypothesis 3: Phase-Dependent Mechanisms

**Expectation**: Different subterms dominate in different lifecycle phases.

**Phase-Specific Predictions**:

1. **Incipient Phase**:
   - Weak Ck (small absolute values)
   - All subterms comparable in magnitude
   - Horizontal flux begins to dominate

2. **Intensification Phase**:
   - Horizontal momentum flux (u'v') dominates
   - Strong negative Ck (energy from eddies to mean flow)
   - Peak subterm magnitudes

3. **Mature Phase**:
   - Horizontal flux remains dominant but weakens
   - Vertical flux terms become relatively more important
   - Beginning of transition to decay

4. **Decay Phase**:
   - Weakening of all subterms
   - Possible reversal of some terms (positive contributions)
   - Dominance structure may shift

---

## Technical Notes

### Data Sources

1. **Cyclone Selection**:
   - From `results/cluster/kmeans_clustered_data.csv` (cluster analysis results)
   - 444 EP1 cyclones with complete lifecycle
   - No spatial domain restriction (all EP1 cyclones regardless of genesis location)

3. **ERA5 Reanalysis**:
   - Automatically downloaded by LorenzCycleToolkit
   - Standard pressure levels (1000-100 hPa)
   - 3-hourly temporal resolution
   - 0.25° spatial resolution

3. **Track Data**:
   - From main database via `load_tracks()`
   - Full lifecycle coverage
   - Vorticity center tracking

### LorenzCycleToolkit Updates

**New Version Features** (compared to Zenodo dataset):

1. **Term Decomposition**:
   - Previous: Only total Ck computed
   - New: Ck separated into three subterms

2. **Pressure Level Output**:
   - Previous: Single `Ck_level.csv` file
   - New: Separate files for each subterm (`Ck_uv_level.csv`, etc.)

3. **Corrections Applied**:
   - Previous version had sign/normalization issues (documented in EP1 analysis)
   - New version: Corrections already implemented
   - No post-processing corrections needed

4. **Automatic Workflow**:
   - Previous: Manual ERA5 download via CDS API
   - New: Integrated download within toolkit
   - Simplified workflow, fewer error points

### Spatial Domain Considerations

**Analysis Domain**: 15° × 15° box centered on cyclone

**Rationale**:
- Consistent with EP1 instability analysis (step3_download_era5.py)
- Large enough to capture synoptic-scale features
- Small enough to focus on cyclone-related processes
- Captures eddy momentum fluxes and mean state gradients

**Alternative Domains** (for sensitivity analysis):
- 10° × 10°: More local, emphasizes cyclone core
- 20° × 20°: More regional, includes larger-scale environment

---

## Directory Structure

```
data/ck_analysis/
├── tracks/                        # Prepared track files
│   ├── track_19790001.txt
│   ├── track_19790006.txt
│   └── ...
└── era5/                          # ERA5 data (downloaded by toolkit)
    └── {track_id}/
        └── ...

results/ck_analysis/
├── lec_results/                   # LorenzCycleToolkit output
│   └── {track_id}_ERA5_track/
│       ├── periods.csv
│       ├── results.csv
│       ├── Ck_level.csv
│       ├── Ck_uv_level.csv
│       ├── Ck_uw_level.csv
│       └── Ck_vw_level.csv
├── subterms_by_cyclone.csv       # Individual cyclone data
├── subterms_statistics.csv       # Ensemble statistics
├── vertical_profiles.csv         # Mean vertical profiles
├── lifecycle_statistics.csv      # Phase-composite statistics
└── final_report.txt              # Summary of findings

figures/ck_analysis/
├── vertical_profiles.png         # Mean profiles by subterm
├── lifecycle_evolution.png       # Time evolution composites
├── phase_composites.png          # Boxplots by phase
├── validation_plots.png          # Comparison with Zenodo data
└── statistical_summary.png       # Scatter plots and correlations
```

---

## References

### Lorenz Energy Cycle

- **Lorenz, E. N.** (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.

- **Brennan, F. E., & Vincent, D. G.** (1980). Zonal and eddy components of the synoptic-scale energy budget during intensification of Hurricane Carmen (1974). *Monthly Weather Review*, 108(7), 954-965.

### Barotropic Conversion

- **Orlanski, I., & Sheldon, J. P.** (1995). Stages in the energetics of baroclinic systems. *Tellus A*, 47(5), 605-628.

- **Dias Pinto, J. R., & da Rocha, R. P.** (2011). The energy cycle and structural evolution of cyclones over southeastern South America in three case studies. *Journal of Geophysical Research*, 116, D14104.

### South Atlantic Cyclones

- **Gan, M. A., & Rao, V. B.** (1991). Surface cyclogenesis over South America. *Monthly Weather Review*, 119(5), 1293-1302.

- **Reboita, M. S., et al.** (2010). Climatology of cyclones over the South Atlantic. *International Journal of Climatology*, 30(11), 1781-1798.

---

## Future Work

### Sensitivity Analyses

1. **Domain Size Sensitivity**:
   - Repeat analysis with 10°×10° and 20°×20° domains
   - Assess impact on subterm contributions

2. **Vertical Resolution**:
   - Use all available pressure levels vs. subset
   - Impact on vertical derivative calculations

3. **Temporal Resolution**:
   - Effect of 3-hourly vs. 6-hourly data
   - Sub-daily variability in subterm contributions

### Extended Analyses

1. **Comparison with Other Energy Patterns**:
   - EP2, EP3, EP4 cyclones
   - Identify unique features of EP1 barotropic conversion

2. **Seasonal Variability**:
   - Winter (JJA) vs. summer (DJF) differences
   - Connection to ENSO phases

3. **Trajectory Analysis**:
   - Subterm evolution along cyclone track
   - Spatial patterns of energy conversion

4. **Ageostrophic Effects**:
   - Role of ageostrophic circulation in Ck subterms
   - Connection to frontal dynamics
