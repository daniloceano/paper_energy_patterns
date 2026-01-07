# Main Figures for Publication

This directory contains publication-ready figures for the Energy Patterns manuscript, following Scientific Reports standards.

## Figures

### Figure 1: Energy Pattern Characteristics
**File:** `ep_intensity_seasonality_trends.png` (706 KB)

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


**Methodology — Seasonal Mann–Kendall, Hamed–Rao correction, and Theil–Sen slope**

We test for monotonic trends in the monthly time series of cyclone counts using Mann–Kendall (MK) family tests and estimate trend magnitude with a (seasonal) Theil–Sen estimator. Seasonality and autocorrelation are explicitly considered: the script computes the Seasonal MK where appropriate and applies the Hamed & Rao (1998) variance correction when serial correlation is present.

Key formulas used in the README and implemented in `scripts/main/figure_intensity_seasonality_trends.py`:

- Mann–Kendall S-statistic (non-seasonal):

  $$
  S = \sum_{i=1}^{n-1} \sum_{j=i+1}^{n} \operatorname{sgn}(x_j - x_i),
  $$

  where $\operatorname{sgn}(y)=1$ if $y>0$, $0$ if $y=0$, and $-1$ if $y<0$.

- Theil–Sen (Sen's) slope (non-seasonal):

  $$
  \beta = \mathrm{median}\left\{ \frac{x_j - x_i}{t_j - t_i} : 1 \le i < j \le n \right\},
  $$

  For seasonal data the script computes slopes within each season (e.g., all Januaries) and combines them (median of seasonal slopes) to obtain a seasonal Theil–Sen estimate. The script reports slopes in counts per year (monthly slope × 12 for monthly data).

- Hamed & Rao (1998) effective sample size correction for autocorrelation:

  Let $r_k$ be the lag-$k$ autocorrelation of the series and $n$ the sample size. Define the effective sample size $n_e$ as

  $$
  n_e = \frac{n}{1 + 2\sum_{k=1}^{n-1} \left(1 - \frac{k}{n}\right) r_k }.
  $$

  The MK variance is adjusted by the factor $n/n_e$ (equivalently the variance is inflated to account for positive serial correlation). The adjusted variance is used to compute the $Z$-score for the MK statistic and the associated p-value. The script implements this correction via the `hamed_rao_modification_test` routine in `pymannkendall` when autocorrelation is detected by the Ljung–Box test.

Implementation notes:

- Autocorrelation detection: the script runs the Ljung–Box test across lags 1..10 (or up to available years) and records p-values. If one or more lags have $p<0.05$, the script flags the series as autocorrelated and prefers the Hamed–Rao modification when annotating figures.
- Tests executed (saved to CSV): `original_test`, `hamed_rao_modification_test`, `yue_wang_modification_test`, `pre_whitening_modification_test`, `trend_free_pre_whitening_modification_test`. The CSV contains the Theil–Sen slope and its 95% CI when available.

References and implementation notes:

- Mann, H. B. (1945). Nonparametric tests against trend. Econometrica.
- Kendall, M. G. (1975). Rank Correlation Methods. Griffin.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. Journal of the American Statistical Association.
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann–Kendall trend test for autocorrelated data. Journal of Hydrology, 204(1-4), 182–196. https://doi.org/10.1016/S0022-1694(97)00125-X
- Yue, S., Pilon, P., & Cavadias, G. (2002). Power of the Mann–Kendall and Spearman's rho tests for detecting monotonic trends in hydrological series. Journal of Hydrology.
- Yue, S., & Wang, C. Y. (2004). The influence of serial correlation on the Mann–Kendall test. Water Resources Management.

Reproducibility:

- The code uses the `pymannkendall` package (`seasonal_test` and `seasonal_sens_slope`) to run the SMK and seasonal Theil–Sen estimators. Ensure `pymannkendall` is installed (see `requirements.txt`) before running `scripts/main/figure_intensity_seasonality_trends.py`.
- The README and script include exact commands and parameters used (monthly aggregation, `period=12`, significance level `alpha=0.05`).

MK Tests and saved results

- This analysis now runs a suite of Mann–Kendall style tests on the annual counts per Energy Pattern (EP):
  - `original_test` (Original Mann–Kendall)
  - `hamed_rao_modification_test` (Hamed & Rao, 1998)
  - `yue_wang_modification_test` (Yue & Wang, 2004)
  - `pre_whitening_modification_test` (Pre-whitening approach)
  - `trend_free_pre_whitening_modification_test` (Trend-free pre-whitening)

- Autocorrelation is evaluated with the Ljung–Box test across lags 1..10 (or up to available years). If significant autocorrelation is detected (one or more lags with p<0.05), the script will prefer the Hamed & Rao modification for annotation; otherwise it uses the original MK result. All test results are saved for each EP.

- Output file: `results/exploratory/mk_trend_results.csv`. The file includes a small header describing the contents, and the following columns:
  - `EP`: Energy Pattern label (EP1, EP2, EP3)
  - `test`: Name of MK test run
  - `trend`: trend direction string (increasing/decreasing/no trend)
  - `p_value`: p-value for the test
  - `tau`: Kendall's tau (if provided by the test)
  - `slope_per_year`: Theil–Sen slope (counts per year)
  - `slope_ci_low`, `slope_ci_high`: lower/upper bounds of Theil–Sen slope (95% CI)
  - `autocorr_pvalues`: dict-string of Ljung–Box p-values per lag
  - `significant_lags`: list-string of lags where autocorrelation p<0.05
  - `chosen`: boolean indicating which test was selected for annotation (Hamed-Rao when autocorr present, otherwise original)
  - `years_range`: data years covered
  - `created`: timestamp of the record

Use this CSV for traceability and further inspection.

**Climate Change Implications**: The significant increase in EP2 cyclones (~7 additional cyclones over 42 years) while EP1 and EP3 remain stable suggests a systematic shift in cyclone energetics. The increase in EP2 (moderate baroclinic, high intensity) may indicate:
- Enhanced conditions for moderate energy conversion pathways
- Changes in baroclinic zone strength or position favoring EP2 formation
- Shifts in available potential energy gradients
- Adaptation to changing large-scale circulation patterns (SAM, ENSO)
- Note: Using absolute counts is more appropriate than relative frequencies for trend analysis, as it avoids artifacts from inter-annual variability in total cyclone numbers

---

### Figure 3: Phase Space Density (2×2 Layout)
**File:** `phase_density_2x2.png`

Four-panel figure showing density distributions in Lorenz Phase Space for all Energy Patterns.

#### Panel Layout:
- **(a) All Cyclones - Conversion Phase Space**: Composite density for entire dataset
- **(b) All Cyclones - Imports Phase Space**: Composite boundary flux density
- **(c) Individual EPs - Conversion Phase Space**: Separated by Energy Pattern
- **(d) Individual EPs - Imports Phase Space**: Separated by Energy Pattern

**Purpose**: Reveals dominant energy pathways and their variability across Energy Patterns.

---

### Figure 4: Case Study - Cyclone 20070643
**File:** `20070643_lps_track_publication.png`

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

**Scientific Insights**: This extreme case demonstrates the energy pathway evolution during rapid intensification, showing the relative importance of baroclinic/barotropic conversions and boundary energy fluxes.

---

### Figure 2: Genesis Density (KDE - Hoskins & Hodges Method)
**File:** `ep_genesis_density_kde.png` (1.5 MB)

Four-panel map figure showing cyclone genesis density using Kernel Density Estimation.

#### Methodology
Following **Hoskins and Hodges (2005)**, cyclone genesis density is computed using:
- **Kernel**: Gaussian with haversine metric (great circle distance)
- **Bandwidth**: 0.05 radians (~555 km)
- **Grid**: Global 2.5° grid (128×64 lon×lat)
- **Units**: Cyclones per 10⁶ km² per year
- **Normalization**: 
  - Total number of cyclones
  - Earth radius at 40°S (6369 km)
  - Time period (42 years)

**Advantages of KDE over point plots**:
1. Reveals underlying probability density of genesis locations
2. Smooths random spatial variability to show systematic patterns
3. Identifies regions of preferential cyclogenesis
4. Quantifies genesis density for comparison

#### Panel Description

**(a) All Cyclones** (Top-Left)
- Composite genesis density for entire dataset
- **Maximum density**: 34.36 cyclones/10⁶ km²/year
- **Primary hotspot**: Southwestern Atlantic near Argentina coast (~60°W, 40-45°S)
- Shows overall cyclogenesis climatology

**(b) EP1** (Top-Right)
- 444 cyclones (11.6% of total)
- **Maximum density**: 3.85 cyclones/10⁶ km²/year
- **Pattern**: Most concentrated genesis, southern distribution
- **Geographic preference**: Closer to Argentina coast, strongest baroclinic forcing

**(c) EP2** (Bottom-Left)
- 979 cyclones (25.6% of total)
- **Maximum density**: 6.86 cyclones/10⁶ km²/year
- **Pattern**: Intermediate concentration and spatial extent
- **Geographic preference**: Middle latitudes, balanced distribution

**(d) EP3** (Bottom-Right)
- 2397 cyclones (62.7% of total) - **Most frequent**
- **Maximum density**: 23.65 cyclones/10⁶ km²/year - **Highest density**
- **Pattern**: Broadest spatial distribution, dominates overall density
- **Geographic preference**: Extends further offshore and equatorward
- **Pattern**: Intermediate concentration and spatial extent
- **Geographic preference**: Middle latitudes, balanced distribution

#### Key Findings

**Spatial Patterns**:
- All EPs share a common genesis region in the southwestern Atlantic
- Latitudinal differences are subtle but systematic:
  - EP1: Most concentrated near 40-45°S
  - EP2: Broadest extent, peak slightly north (~37-42°S)
  - EP3: Intermediate position (~38-44°S)

**Density Comparison**:
- EP3 dominates absolute density (23.65 cyclones/10⁶ km²/year) - most frequent
- EP2 has intermediate density (6.86)
- EP1 has lowest density (3.85) but highest per-cyclone concentration
---

## Scripts

### `figure_intensity_seasonality_trends.py`
Creates Figure 1 with intensity, seasonality, and trend analysis.

**Key Features**:
- Loads track data and merges with clustering results
- Computes maximum vorticity per cyclone
- Seasonal aggregation and percentage calculations
- Mann-Kendall trend analysis with Sen's slope
- Publication-quality formatting (300 DPI)

**Dependencies**:
- pandas, numpy, matplotlib, seaborn
- pymannkendall (trend analysis)
- scipy.stats.theilslopes (Sen's slope)

### `figure_genesis_density_kde.py`
Creates Figure 2 with KDE-based genesis density maps.

**Key Features**:
- Implements Hoskins & Hodges (2005) KDE methodology
- Uses scikit-learn KernelDensity with haversine metric
- Cartopy for map projections and geographic features
- Normalized density (cyclones/area/time)
- Consistent colormap across panels for comparison

**Dependencies**:
- pandas, numpy, matplotlib
- cartopy (map projections)
- sklearn.neighbors.KernelDensity

---

## Color Scheme

Following Scientific Reports standards for colorblind-friendly palettes:

### Energy Patterns
- **EP1**: Blue (#1f77b4)
- **EP2**: Orange (#ff7f0e)
- **EP3**: Green (#2ca02c)

### Seasons
- **Summer (DJF)**: Red (#e74c3c)
- **Autumn (MAM)**: Orange (#f39c12)
- **Winter (JJA)**: Blue (#3498db)
- **Spring (SON)**: Green (#2ecc71)

### Density Maps
- **Colormap**: YlOrRd (Yellow-Orange-Red)
- **Purpose**: Intuitive hot-spot identification
- **Range**: 0 to 95th percentile (extended beyond)

---

## Figure Specifications

Both figures meet **Scientific Reports** requirements:

- **Resolution**: 300 DPI
- **Format**: PNG with white background
- **Font**: Arial/Helvetica sans-serif
- **Font sizes**: 
  - Axis labels: 10-11 pt (bold)
  - Titles: 11-12 pt (bold)
  - Tick labels: 9-10 pt
  - Legend: 9 pt
- **Panel labels**: (a), (b), (c), (d) in bold, top-left position
- **Line weights**: 1.0-2.5 pt (depending on element)
- **Grid**: Subtle gray dashed lines (alpha=0.3)

---

## References

**Hoskins, B. J., & Hodges, K. I. (2005).** A new perspective on Southern Hemisphere storm tracks. *Journal of Climate*, 18(20), 4108-4129. https://doi.org/10.1175/JCLI3570.1

---

## Usage

To regenerate figures:

```bash
# Activate environment
source activate.sh

# Generate Figure 1
python scripts/main/figure_intensity_seasonality_trends.py

# Generate Figure 2
python scripts/main/figure_genesis_density_kde.py
```

Both scripts will save outputs to `figures/main/` directory.
