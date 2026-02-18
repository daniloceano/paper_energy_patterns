# Main Figures for Publication

This directory contains publication-ready figures for the Energy Patterns manuscript, following Scientific Reports standards.

## Main Figures

### Figure 1: Study Area and Workflow Overview
**File:** `1_study_area_and_workflow.png`

Two-panel figure providing context for the study and the processing pipeline used in the manuscript.

#### Panel Layout:
- **(a) Study Area Map (Top)**
  - Shows the Southwestern Atlantic focus, typical genesis regions and the domain boxes used for case selection (e.g., 60°W–45°W, 45°S–30°S).
- **(b) Analysis Workflow (Bottom)**
  - Diagram summarizing data sources (ERA5, LEC outputs), clustering (k-means), case selection, diagnostic computations (RK, PV, EGR) and figure-generation steps.

**Purpose:** Introduces the geographic focus and reproducible processing pipeline used for clustering, case selection and instability composite generation.

---

### Figure 2: Case Study - Cyclone 20070643
**File:** `2_20070643_lps_track_publication.png`

Three-panel figure showing detailed energetics and trajectory of cyclone 20070643 (maximum vorticity: 15.48 × 10⁻⁵ s⁻¹).

#### Cyclone Details:
- **Track ID**: 20070643
- **Genesis**: 2007-07-24 14:00 UTC
- **Lysis**: 2007-07-29 03:00 UTC
- **Peak vorticity**: 2007-07-27 02:00 UTC (15.48 × 10⁻⁵ s⁻¹)
- **Duration**: 109 hours

#### Panel Layout:

**(a) Conversion LPS (Top-Left)**
- Baroclinic (Ca) and barotropic (Ck) energy conversions
- X-axis: Ck - Conversion from zonal to eddy KE (W m⁻²)
- Y-axis: Ca - Conversion from zonal to eddy APE (W m⁻²)
- Marker color: Ge - Generation of eddy APE (W m⁻²)
- Marker size: Ke - Eddy Kinetic Energy (J m⁻²)

**(b) Imports LPS (Top-Right)**
- Energy transport across cyclone boundaries
- X-axis: BAe - Eddy APE boundary flux (W m⁻²)
- Y-axis: BKe - Eddy KE boundary flux (W m⁻²)
- Marker color: Ge (W m⁻²)
- Marker size: Ke (J m⁻²)

**(c) Track Map (Bottom)**
- Geographic trajectory with energy and vorticity information
- Marker color: vor42 - Relative vorticity (10⁻⁵ s⁻¹)
- Marker size: Ke - Eddy Kinetic Energy (J m⁻²)
- Temporal resolution: 3-hourly (matching Ke availability)
- Green circle: Genesis location
- Red X: Lysis location

---

### Figure 3: Phase Space Density (2×2 Layout)
**File:** `3_phase_density_2x2.png`

Four-panel figure showing density distributions in Lorenz Phase Space for all cyclones in the Dataset, for each development phase.

#### Panel Layout:
- **(a) Conversion Phase Space for Incipient Phase**
- **(b) Import Phase Space for Incipient Phase**
- **(c) Conversion Phase Space for Intensification Phase**
- **(d) Import Phase Space for Intensification Phase**
- **(e) Conversion Phase Space for Mature Phase**
- **(f) Import Phase Space for Mature Phase**
- **(g) Conversion Phase Space for Decay Phase**
- **(h) Import Phase Space for Decay Phase**

**Purpose**: Reveals dominant energy pathways and their variability across cyclones lifecycle.

---

### Figure 4: Lorenz Phase Space for Energy Patterns (EP1–EP3)
**Files:** `lps_ep1_conversion.png`, `lps_ep1_imports.png`, `lps_ep2_conversion.png`, `lps_ep2_imports.png`, `lps_ep3_conversion.png`, `lps_ep3_imports.png`

Two-panel LPS diagrams are provided for each Energy Pattern (EP1, EP2, EP3), showing both:
- **Conversion LPS (left):** Ca × Ck phase space across sequential phases
- **Imports LPS (right):** BAe × BKe phase space across sequential phases

Each panel shows the phase trajectory through: Incipient → Intensification → Mature → Decay, with:
- **Marker color:** Ge — Generation of eddy APE (W m⁻²)
- **Marker size:** Ke — Eddy Kinetic Energy (J m⁻²)
- **Legends:** EP linewidths and Ke marker-size legend included; Ke legend placed inside the plot in zoomed variants for clarity
- **Zoomed variants:** Available to inspect behavior near zero and compare EPs more clearly

**Purpose:** Illustrates how the three canonical energy patterns differ in their Lorenz Phase Space signatures and how their conversion/import pathways evolve through development phases.

---

### Figure 5: Energy Pattern Characteristics
**File:** `5_ep_intensity_seasonality_trends.png` (706 KB)

Three-panel figure combining key characteristics of Energy Patterns:

#### (a) Intensity Distribution (Top-Left)
- **Type**: Violin plot
- **Shows**: Maximum vorticity distribution (10⁻⁵ s⁻¹) for each Energy Pattern
- **Key Statistics**:
  - **EP1**: 8.81 ± 2.47 × 10⁻⁵ s⁻¹
  - **EP2**: 9.34 ± 2.40 × 10⁻⁵ s⁻¹ (highest)
  - **EP3**: 6.37 ± 2.41 × 10⁻⁵ s⁻¹ (lowest)

**Interpretation**: EP2 produces the most intense cyclones on average, while EP3 (most frequent, 62.7%) produces the weakest cyclones. This suggests that moderate energy conversion patterns (EP2) with balanced pathways may be optimal for cyclone intensification.

#### (b) Seasonal Distribution (Top-Right)
- **Type**: Grouped bar chart
- **Shows**: Percentage of cyclones per season for each Energy Pattern
- **Seasons**: DJF (Summer), MAM (Autumn), JJA (Winter), SON (Spring)
- **Key Findings**:
  - **EP1**: Dominant in Winter (35.6%)
  - **EP2**: Dominant in Summer (30.9%)
  - **EP3**: Dominant in Spring (27.5%)

**Interpretation**: Clear seasonal preferences reflect different environmental conditions favorable to each energy pattern. EP1's winter preference aligns with stronger meridional temperature gradients, while EP2's summer prevalence suggests more barotropic conditions.

#### (c) Interannual Variability and Trends (Bottom - Full Width)
- **Type**: Time series with Mann-Kendall trend analysis
- **Period**: 1979-2020 (42 years)
- **Shows**: Absolute number of cyclones per year for each EP with trend lines
- **Statistical Method**: 
  - Mann-Kendall test for monotonic trends on absolute counts (α = 0.05)
  - Sen's slope estimator for trend magnitude (cyclones/year)
  - Solid lines = significant trends (p < 0.05)
  - Dashed lines = non-significant trends

**Trend Results**:
- **EP1**: No significant trend (p = 1.000, τ = 0.000, slope = 0.000) → Stable occurrence
- **EP2**: Significant increasing trend (p = 0.006, τ = 0.296, slope = 0.172)* → Increasing by ~0.17 cyclones/year
- **EP3**: No significant trend (p = 0.728, τ = 0.038, slope = 0.000) → Stable occurrence


**Methodology — Mann–Kendall with Hamed–Rao correction and Theil–Sen slope**

We test for monotonic trends in the **annual time series** of cyclone counts (one value per year, 1979–2020) using the Mann–Kendall (MK) family of tests and estimate trend magnitude with the Theil–Sen slope estimator. Autocorrelation is explicitly assessed on **detrended residuals** (after removing the Theil–Sen linear trend) using a single **Ljung–Box portmanteau test**; when significant serial correlation is detected (p < 0.05), we apply the Hamed & Rao (1998) variance correction.

**Key formulas** (implemented in `scripts/main/figure_intensity_seasonality_trends.py`):

1. **Mann–Kendall S-statistic**:

   $$
   S = \sum_{i=1}^{n-1} \sum_{j=i+1}^{n} \operatorname{sgn}(x_j - x_i),
   $$

   where $\operatorname{sgn}(y)=1$ if $y>0$, $=0$ if $y=0$, and $=-1$ if $y<0$. Under the null hypothesis of no trend, $S$ is approximately normally distributed for large $n$ with mean 0 and variance $\mathrm{Var}(S)$.

2. **Theil–Sen slope estimator**:

   $$
   \beta = \mathrm{median}\left\{ \frac{x_j - x_i}{t_j - t_i} : 1 \le i < j \le n \right\}.
   $$

   This is a robust, nonparametric estimate of the linear trend (cyclones per year). Confidence intervals (95% CI) are computed via `scipy.stats.theilslopes`.

3. **Hamed & Rao (1998) effective sample size correction**:

   Let $r_k$ be the lag-$k$ sample autocorrelation and $n$ the sample size. The **effective sample size** is

   $$
   n_e = \frac{n}{1 + 2\sum_{k=1}^{n-1} \left(1 - \frac{k}{n}\right) r_k }.
   $$

   The MK test variance is then scaled by $n/n_e$ to account for positive serial correlation, yielding a corrected $Z$-statistic and p-value. This correction is implemented in `pymannkendall.hamed_rao_modification_test`.

**Implementation details**:

- **Data**: Annual cyclone counts per Energy Pattern (EP), 1979–2020 (42 years).
- **Detrending**: Before testing for autocorrelation, the linear trend (estimated via Theil–Sen slope) is removed from the series to obtain residuals.
- **Autocorrelation detection**: Single **Ljung–Box portmanteau test** at lag $h = \min(10, n-1)$ applied to the detrended residuals. The series is flagged as autocorrelated if $p < 0.05$. This avoids the multiple comparison problem inherent in testing individual lags separately.
- **Test selection**: When autocorrelation is present, the **Hamed–Rao modification** is used for figure annotation; otherwise the **original MK test** is used.
- **Tests executed** (all saved to CSV): `original_test`, `hamed_rao_modification_test`, `yue_wang_modification_test`, `pre_whitening_modification_test`, `trend_free_pre_whitening_modification_test`. Each test yields a trend direction (increasing/decreasing/no trend), p-value, and Kendall's tau.
- **Slope & CI**: Computed once per EP using `scipy.stats.theilslopes` on annual counts; reported in cyclones/year with 95% confidence interval.

**References**:

- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13, 245–259.
- Kendall, M. G. (1975). *Rank Correlation Methods* (4th ed.). Griffin, London.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63, 1379–1389.
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann–Kendall trend test for autocorrelated data. *Journal of Hydrology*, 204(1–4), 182–196. https://doi.org/10.1016/S0022-1694(97)00125-X
- Yue, S., & Wang, C. (2004). The influence of serial correlation on the Mann–Kendall test for detecting monotonic trends. *Water Resources Management*, 18, 201–218.

**Reproducibility**:

- Install `pymannkendall` (v1.4+), `scipy`, and `statsmodels` (see `requirements.txt`).
- Run: `python scripts/main/figure_intensity_seasonality_trends.py`
- Outputs: `figures/main/ep_intensity_seasonality_trends.png` and `results/exploratory/mk_trend_results.csv`.

**Output file structure** (`results/exploratory/mk_trend_results.csv`):
  - `EP`: Energy Pattern label (EP1, EP2, EP3)
  - `test`: Name of MK test run
  - `trend`: trend direction string (increasing/decreasing/no trend)
  - `p_value`: p-value for the test
  - `tau`: Kendall's tau (if provided by the test)
  - `slope_per_year`: Theil–Sen slope (counts per year)
  - `slope_ci_low`, `slope_ci_high`: lower/upper bounds of Theil–Sen slope (95% CI)
  - `lb_portmanteau_pvalue`: p-value from Ljung–Box portmanteau test on detrended residuals
  - `max_lag_tested`: maximum lag used in Ljung–Box test ($h = \min(10, n-1)$)
  - `chosen`: boolean indicating which test was selected for annotation (Hamed-Rao when autocorr present, otherwise original)
  - `years_range`: data years covered
  - `created`: timestamp of the record

Use this CSV for traceability and further inspection.

---

### Figure 6: Genesis Density (KDE - Hoskins & Hodges Method)
**File:** `6_ep_genesis_density_kde.png` (1.5 MB)

Four-panel map figure showing cyclone genesis density using Kernel Density Estimation with normalized relative anomaly visualization for Energy Patterns.

#### Methodology

**KDE Computation** — Following **Hoskins and Hodges (2005)**:
- **Kernel**: Gaussian with haversine metric (great circle distance)
- **Bandwidth**: 0.05 radians (~555 km)
- **Grid**: Global 2.5° grid (128×64 lon×lat)
- **Units**: Cyclones per 10⁶ km² per year
- **Normalization**: 
  - Total number of cyclones
  - Earth radius at 40°S (6369 km)
  - Time period (42 years)

**Min-Max Normalization for EP Panels** — To highlight spatial contributions:

Panels (b)–(d) display **normalized relative anomalies** rather than absolute densities. This approach emphasizes regions where each Energy Pattern has enhanced or reduced genesis contribution relative to the overall climatology, independent of the absolute frequency of each EP.

The normalization follows these steps:

1. **Min-Max scaling** (applied separately to each density field):
   
   $$
   \text{norm}(x) = \frac{x - \min(x)}{\max(x) - \min(x)}, \quad x > 0
   $$
   
   where $x$ represents the KDE density field. Grid cells with zero density remain zero. This scales all positive density values to the range [0, 1] while preserving spatial structure.

2. **Relative anomaly** (difference in normalized space):
   
   $$
   \Delta_{\text{EP}} = \text{norm}(\text{density}_{\text{EP}}) - \text{norm}(\text{density}_{\text{All}})
   $$
   
   Values range from approximately -1 to +1, where:
   - **Positive values** (red): regions with relatively stronger EP contribution
   - **Negative values** (blue): regions with relatively weaker EP contribution
   - **Near zero** (white): proportional to overall climatology

**Why this approach?**

Simply plotting absolute EP densities is dominated by EP3's high frequency (62.7% of cyclones), obscuring spatial patterns in EP1 and EP2. Dividing raw densities (density_EP / density_All) also fails because it amplifies noise in low-density regions and doesn't account for the expected fractional contribution of each EP.

Min-Max normalization removes scale differences before comparison, allowing us to identify **spatial patterns** in genesis distribution that are unique to each EP, independent of their overall frequency. This reveals where each energy pathway preferentially generates cyclones within the common genesis region.

#### Panel Description

**(a) All Cyclones** (Top-Left)
- **Type**: Absolute density (cyclones per 10⁶ km²/year)
- Composite genesis density for entire dataset (3820 cyclones, 1979–2020)
- **Maximum density**: 34.36 cyclones/10⁶ km²/year
- **Primary hotspot**: Southwestern Atlantic near Argentina coast (~60°W, 40-45°S)
- Shows overall cyclogenesis climatology baseline

**(b) EP1** (Top-Right)
- **Type**: Normalized relative anomaly (dimensionless, range ≈ -1 to +1)
- 444 cyclones (11.6% of total)
- **Colormap**: RdBu_r (diverging, red = enhanced contribution, blue = reduced)
- **Pattern**: Negative/neutral anomalies across most of domain
- **Interpretation**: EP1 genesis is less spatially concentrated than the overall climatology; despite being the least frequent EP, its genesis locations are broadly distributed rather than clustered in the main hotspot

**(c) EP2** (Bottom-Left)
- **Type**: Normalized relative anomaly
- 979 cyclones (25.6% of total)
- **Pattern**: Moderate positive anomaly in northern part of genesis region
- **Interpretation**: EP2 shows enhanced genesis contribution at slightly more equatorward latitudes (~37-42°S), suggesting environmental conditions favorable to EP2's balanced energy pathways are offset northward from the main climatological hotspot

**(d) EP3** (Bottom-Right)
- **Type**: Normalized relative anomaly
- 2397 cyclones (62.7% of total) - **Most frequent**
- **Pattern**: Strong positive anomaly concentrated near 40-45°S and coastal regions
- **Interpretation**: EP3 dominates the core genesis hotspot near the Argentina coast. Despite being the most frequent EP overall, its spatial concentration exceeds its fractional frequency, indicating a strong geographic preference for the primary baroclinic zone

#### Key Findings

**Spatial Differentiation**:
- **EP3** concentrates in the primary genesis hotspot (40-45°S, near coast), showing positive anomalies that indicate over-representation relative to its 62.7% frequency share
- **EP2** exhibits positive anomalies slightly equatorward (~37-42°S), suggesting environmental conditions favorable to balanced energy pathways peak northward of the climatological maximum
- **EP1** shows weak/negative anomalies, indicating a more dispersed genesis distribution that underutilizes the main hotspot despite being concentrated at southern latitudes in absolute terms

**Physical Interpretation**:
- The normalized anomaly approach reveals that **Energy Pattern determines preferred genesis latitude** within the broader South Atlantic genesis region
- EP3 (highest barotropic conversion) dominates where SST gradients and baroclinicity peak
- EP2 (balanced conversions) prefers transition zones with moderate gradients
- EP1 (lowest barotropic, highest baroclinic) occurs more uniformly across the domain, not preferentially tied to the strongest frontal zones

**Methodological Note**:
The Min-Max normalization successfully isolates **spatial preferences** from **frequency differences**, revealing subtle but systematic geographic patterns that would be masked by plotting absolute densities (which EP3 dominates) or simple ratios (which amplify noise).

## References

**Hoskins, B. J., & Hodges, K. I. (2005).** A new perspective on Southern Hemisphere storm tracks. *Journal of Climate*, 18(20), 4108-4129. https://doi.org/10.1175/JCLI3570.1

---

### Figure 7: EP1 Instability Composite (4×3)
**File:** `7_ep1_instability_composite_4x3.png`

Four-by-three composite figure showing instability diagnostics for EP1 cyclones across three spatial scales (local 5°, mesoscale 15°, synoptic 30°). The rows show, from top to bottom:
- Rayleigh–Kuo (RK) 2D maps (∂η/∂y at Ck = 350 hPa)
- RK zonal-mean profiles (ensemble members in gray; ensemble mean in bold)
- Baroclinic Potential Vorticity (PV at Ca ≈ 975 hPa)
- Baroclinic Potential Vorticity (PV at Ca ≈ 975 hPa, **shaded**) + **PV at 200 hPa (green contours; 2-PVU tropopause in dark-green dashed)**
- Eady Growth Rate (EGR at Ca ≈ 975 hPa, **shaded**) + **SLP (black contours, hPa)**

Notes on presentation and compact layout:
- The figure is optimized for compact display (titles removed; panels labeled with (a)–(l) in the top-left corner) to maximize data density while preserving readability.
- Shared colorbar scales are used per row to facilitate cross-scale comparison; colorbars are placed in the rightmost column.
- PV@200 hPa contours (green) are overlaid on the 975-hPa PV shading to show the tropopause structure; the 2-PVU isoline (dark-green dashed) marks the dynamical tropopause.
- SLP black contours (2-hPa intervals, labelled) are overlaid on the EGR shading to connect baroclinic instability with surface pressure structure.

Data source:
- Precomputed composites: `data/era5_ep1/precomputed_composites_{local,mesoscale,synoptic}.nc`
- Generated by `scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py` from all 385 EP1 ERA5 files.

Case selection:
- **Script:** `scripts/ep1_ibc_ibt_analysis/step1_select_all_ep1.py` — selects **all** EP1 cyclones (cluster 0) with complete lifecycles.
- **No spatial domain filter** — the full EP1 population is used.
- **Required inputs:**
  - Clustered results: `results/cluster/kmeans_clustered_data.csv`.
  - LEC outputs per track under `data/temp_lec_zenodo/LEC_Results_energetic-patterns/`.
- **Primary output:** `results/ep1_vertical/all_ep1_cases.csv` (385 cases: `track_id`, `intensification_start`, `intensification_end`, `center_lat`, `center_lon`, `duration_hours`).

Outputs:
- `figures/main/7_ep1_instability_composite_4x3.png` (300 DPI, publication-ready)

Recreate:
```bash
# 1. Ensure composites are available
python scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py
# 2. Generate figure (reads precomputed composites, no per-case recomputation)
python scripts/main/07_figure_ep1_instability_composite.py
```

---

## Supplementary Figures

### Figure S1: PCA and Clustering Validation
**File:** `S1_pca_clustering_validation.png` (590 KB)

Two-panel figure showing the dimensionality reduction and clustering validation:

#### (a) PCA Explained Variance (Left)
- **Type**: Bar plot with cumulative line
- **Shows**: Individual and cumulative variance explained by principal components
- **Key Features**:
  - Individual variance shown as bars (steelblue)
  - Cumulative variance as line (dark green)
  - 90% threshold marked with red dashed line
  - Optimal number of components highlighted (red bar)
- **Result**: 90% of variance explained by n components
- **Interpretation**: Validates PCA's effectiveness in capturing energy patterns with reduced dimensionality

#### (b) Optimal k Selection (Right)
- **Type**: Line plot with normalized cluster validity indices
- **Shows**: Multiple cluster validity indices (CVIs) normalized to [0,1] range
- **Indices Shown**:
  - Silhouette Score
  - Davies-Bouldin Index (inverted)
  - Calinski-Harabasz Index
  - Score Function
  - Gap Statistic
  - Mean Index (black line, weighted average)
- **Features**:
  - Optimal k=3 marked with red dashed line
  - Optimal point highlighted with red star
  - Legend positioned outside plot for clarity
- **Result**: k=3 clusters identified as optimal
- **Interpretation**: Multiple independent validation criteria converge on 3 distinct energy patterns, providing robust statistical support for the classification

**Purpose**: This supplementary figure provides transparency and reproducibility by showing:
1. How dimensionality reduction preserves information (PCA validation)
2. How the optimal number of clusters was objectively determined (clustering validation)
3. That the 3 Energy Patterns are statistically justified, not arbitrary

**Generated by**: `scripts/main/S1_figure_pca_clustering_validation.py`

---

### Figure S2: All EP1 Cyclones for Instability Analysis
**File:** `S2_selected_tracks.png`

Map showing **all 385 EP1 cyclones** used in the composite instability analysis.

#### What is shown

- **Gray thin lines** – complete tracks.
- **Gold thick lines** – intensification phase only (LEC-derived start/end).
- **Green circles** – genesis location.

No spatial domain filter is applied; all EP1 cases with a complete lifecycle (incipient → intensification → mature → decay) are included.

#### Inputs

- `results/ep1_vertical/all_ep1_cases.csv` – generated by `step1_select_all_ep1.py`.
- Full track table from `scripts.utils.load_data.load_tracks()`.

**Generated by:** `python scripts/main/S2_figure_selected_tracks.py`

#### Map Elements

**Track visualization**:
- **Gray lines**: Complete cyclone tracks (full lifecycle)
- **Gold thick lines**: Intensification phase segments
- **Red stars**: Analysis centers (temporal center of intensification phase)
- **Green circles**: Genesis locations
- **Blue box**: Selection domain (60°W–45°W, 45°S–30°S)

**Projection**: South Polar Stereographic (centered at 90°S)
**Spatial extent**: 80°W–40°E, 70°S–20°S (shows South Atlantic context)

#### Results

**Number of selected cyclones**: Varies based on data availability (typically 30–50 systems)
- All meet complete lifecycle requirement
- All have intensification center within selection domain
- Number depends on LEC data availability from Zenodo archive

**Geographic distribution**:
- Genesis predominantly near Argentina coast (40–50°S)
- Intensification centers concentrated in selection domain
- Tracks generally move east-southeastward following typical storm track

#### Processing Requirements

This figure requires upstream processing from the EP1 instability analysis pipeline:

**Prerequisites**:
1. Clustering results: `results/cluster/kmeans_clustered_data.csv`
2. LEC data from Zenodo (DOI: 10.5281/zenodo.18243447): `data/temp_lec_zenodo/LEC_Results_energetic-patterns/`
3. Selected cases: `results/ep1_vertical/selected_cases.csv`

**Run sequence**:
```bash
# First, run case selection (in ep1_ibc_ibt_analysis pipeline)
python scripts/ep1_ibc_ibt_analysis/step1_select_cases.py

# Then, generate figure S2
python scripts/main/S2_figure_selected_tracks.py
```

**Key inputs**:
- `results/ep1_vertical/selected_cases.csv` — Selected track metadata
- `data/tracks_SAt_filtered_with_energetics_processed.csv` — Complete track data
- `data/temp_lec_zenodo/LEC_Results_energetic-patterns/<track_id>_ERA5_track/periods.csv` — Phase timing

**Purpose**: Documents the case selection methodology and shows spatial distribution of selected EP1 cyclones used for instability diagnostics in Figure 7.

**Generated by**: `scripts/main/S2_figure_selected_tracks.py`

---

### Figure S3: Vertical Distribution of Energy Conversions
**File:** `S3_vertical_levels.png`

Two-panel boxplot showing the vertical distribution of baroclinic (Ca) and barotropic (Ck) energy conversions across 32 pressure levels (1000–100 hPa) for selected EP1 cyclones during their intensification phase.

#### Panel Description

**(a) Baroclinic Conversion (Ca) by Pressure Level** (Top)
- **Type**: Boxplot showing distribution across all selected EP1 cyclones
- **Y-axis**: Ca (W m⁻²) — Baroclinic energy conversion
- **X-axis**: Pressure level (hPa) — 1000 to 100 hPa (32 levels)
- **Key finding**: Maximum Ca typically occurs in mid-troposphere (~350–400 hPa)
- **Marker**: Red star indicates pressure level with maximum median Ca
- **Box elements**:
  - Red boxes with dark red edges
  - Median shown as dark red line
  - Interquartile range (IQR) shown as box
  - Whiskers extend to 1.5×IQR
  - Outliers excluded for clarity

**(b) Barotropic Conversion (Ck) by Pressure Level** (Bottom)
- **Type**: Boxplot showing distribution across all selected EP1 cyclones
- **Y-axis**: Ck (W m⁻²) — Barotropic energy conversion
- **X-axis**: Pressure level (hPa) — 1000 to 100 hPa (32 levels)
- **Key finding**: Minimum (most negative) Ck typically occurs in mid-troposphere (~350 hPa)
- **Marker**: Blue star indicates pressure level with minimum median Ck
- **Box elements**:
  - Blue boxes with dark blue edges
  - Median shown as dark blue line
  - Same statistical representation as panel (a)

#### Methodology

**Data source**: Zenodo archive (DOI: 10.5281/zenodo.18243447)
- Complete Lorenz Energy Cycle results with vertical resolution
- 32 pressure levels from 1000 hPa to 100 hPa
- 3-hourly temporal resolution

**Analysis period**: Intensification phase only
- Temporal range: From intensification start to end time (defined in LEC `periods.csv`)
- Time-averaged profiles: Mean Ca and Ck computed across all 3-hourly time steps within intensification phase

**Data corrections applied** (validated in `scripts/ep1_ibc_ibt_analysis/validate_step2.py`):
1. **Ca**: Sign inversion (Ca_corrected = -Ca_raw)
   - Reason: Old LorenzCycleToolkit version saved Ca_level with opposite sign
2. **Ck**: Division by gravity (Ck_corrected = Ck_raw / 9.8 m/s²)
   - Reason: Old LorenzCycleToolkit version saved Ck_level without gravity normalization

These corrections ensure vertical integration matches pre-computed integrated values.

**Sample size**: Varies based on data availability (typically 30–50 EP1 cyclones with complete intensification phase data)

#### Key Findings

**Critical vertical levels for EP1 cyclones**:
- **Maximum baroclinic conversion (Ca)**: ~350–400 hPa (mid-troposphere)
  - Indicates level of strongest meridional temperature gradient conversion
  - Corresponds to jet stream level where baroclinic instability peaks
- **Minimum barotropic conversion (Ck)**: ~350 hPa (mid-troposphere)
  - Most negative Ck indicates energy transfer from eddy to mean flow
  - Co-location with maximum Ca suggests coupled baroclinic-barotropic dynamics

**Implications for instability diagnostics**:
- Identifies Ca ≈ 350 hPa as optimal level for Rayleigh–Kuo criterion analysis
- Identifies Ck ≈ 350 hPa as optimal level for barotropic instability diagnostics
- Justifies pressure level selection for Figure 7 instability composites

**Vertical structure insights**:
- Ca shows broad mid-tropospheric maximum (500–300 hPa)
- Ck shows more concentrated mid-tropospheric minimum
- Near-surface levels (>850 hPa) show weaker conversions
- Upper troposphere (200–100 hPa) shows reduced baroclinic activity

#### Processing Requirements

This figure requires upstream processing from the EP1 instability analysis pipeline:

**Prerequisites**:
1. Clustering results: `results/cluster/kmeans_clustered_data.csv`
2. LEC vertical data from Zenodo: `data/temp_lec_zenodo/LEC_Results_energetic-patterns/<track_id>_ERA5_track/Ca_level.csv` and `Ck_level.csv`
3. Phase timing data: `data/temp_lec_zenodo/LEC_Results_energetic-patterns/<track_id>_ERA5_track/periods.csv`

**Run sequence**:
```bash
# First, download and analyze vertical levels (in ep1_ibc_ibt_analysis pipeline)
python scripts/ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py

# Then, generate figure S3
python scripts/main/S3_figure_vertical_levels.py
```

**Note**: The step2 script downloads LEC data from Zenodo (~1.5 GB) and performs vertical integration validation. The S3 figure script uses the same data but focuses on figure generation.

**Purpose**: Identifies critical pressure levels for instability diagnostics and justifies the vertical level selection used in composite analysis (Figure 7).

**Generated by**: `scripts/main/S3_figure_vertical_levels.py`