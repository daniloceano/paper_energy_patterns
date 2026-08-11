# Scientific Notes — Main and Supplementary Figures

**Project:** Energetic patterns of South Atlantic extratropical cyclones (1979–2020)  
**Document scope:** Scientific rationale, variable definitions, equations, sign conventions,
interpretation guidance, methodological caveats, and literature support for each
publication figure.

This document is the **scientific companion** to [`README.md`](README.md). It does not
describe how to run the scripts (see `README.md` for that). It documents *why* each
diagnostic is used, *what* the variables mean, and *how the results should and should not
be interpreted*.

---

## Contents

- [Scientific Notes — Main and Supplementary Figures](#scientific-notes--main-and-supplementary-figures)
  - [Contents](#contents)
  - [1. Lorenz Energy Cycle framework — general](#1-lorenz-energy-cycle-framework--general)
    - [1.1 Background and framework](#11-background-and-framework)
    - [1.2 Variable definitions and sign conventions](#12-variable-definitions-and-sign-conventions)
    - [1.3 Energy Patterns (EP) classification](#13-energy-patterns-ep-classification)
  - [2. Figure 1 — Tracks and genesis frequency](#2-figure-1--tracks-and-genesis-frequency)
  - [3. Figure 2 — Case study: cyclone 20070643](#3-figure-2--case-study-cyclone-20070643)
    - [3.1 Lorenz Phase Space diagrams](#31-lorenz-phase-space-diagrams)
    - [3.2 Track panel (panel c)](#32-track-panel-panel-c)
  - [4. Figure 3 — Phase-space density by lifecycle phase](#4-figure-3--phase-space-density-by-lifecycle-phase)
  - [5. Figure 4 — Lorenz Phase Space for EP1–EP3](#5-figure-4--lorenz-phase-space-for-ep1ep3)
  - [7. Figure 6 — Intensity, seasonality, and interannual trends](#7-figure-6--intensity-seasonality-and-interannual-trends)
    - [7.1 Intensity distribution (panel a — violin plot)](#71-intensity-distribution-panel-a--violin-plot)
    - [7.2 Seasonal distribution (panel b — bar chart)](#72-seasonal-distribution-panel-b--bar-chart)
    - [7.3 Trend analysis (panel c — Mann–Kendall)](#73-trend-analysis-panel-c--mannkendall)
      - [Motivation](#motivation)
      - [Mann–Kendall S-statistic](#mannkendall-s-statistic)
      - [Theil–Sen slope estimator](#theilsen-slope-estimator)
      - [Autocorrelation detection and correction](#autocorrelation-detection-and-correction)
      - [Interpretation constraints](#interpretation-constraints)
  - [8. Figure 7 — Genesis density (KDE)](#8-figure-7--genesis-density-kde)
    - [8.1 KDE methodology](#81-kde-methodology)
    - [8.2 Min-max normalized relative anomaly (panels b–d)](#82-min-max-normalized-relative-anomaly-panels-bd)
    - [8.3 Interpretation guidance](#83-interpretation-guidance)
  - [9. Figure 8 — EP − EPALL dynamical composites (EPALL-relative anomaly)](#9-figure-8--ep--epall-dynamical-composites-epall-relative-anomaly)
    - [9.1 Rationale for the EPALL-relative approach](#91-rationale-for-the-epall-relative-approach)
    - [9.2 Composite methodology](#92-composite-methodology)
    - [9.3 Row 1: Upper-level / baroclinic structure departure](#93-row-1-upper-level--baroclinic-structure-departure)
    - [9.4 Row 2: Low-level frontal / thermal structure departure](#94-row-2-low-level-frontal--thermal-structure-departure)
    - [9.5 Row 3: Jet-level energetics departure](#95-row-3-jet-level-energetics-departure)
    - [9.6 Global colormap design](#96-global-colormap-design)
  - [9. Figure S1 — PCA and clustering validation](#9-figure-s1--pca-and-clustering-validation)
  - [10. Figure 5 — Vertical Ca/Ck profiles (EP1, EP2, EP3)](#10-figure-5--vertical-cack-profiles-ep1-ep2-ep3)
    - [10.1 Vertical profiles](#101-vertical-profiles)
    - [10.2 Data corrections](#102-data-corrections)
    - [10.3 Interpretation](#103-interpretation)
  - [Figure S3 — C_K vertical profile and integrated subterms (EP1)](#figure-s3--c_k-vertical-profile-and-integrated-subterms-ep1)
  - [12. Global caveats and interpretation boundaries](#12-global-caveats-and-interpretation-boundaries)
  - [13. References](#13-references)
    - [TODO / unresolved uncertainties](#todo--unresolved-uncertainties)

---

## 1. Lorenz Energy Cycle framework — general

### 1.1 Background and framework

The Lorenz Energy Cycle (LEC; Lorenz 1955) partitions the atmospheric energy budget
into zonal-mean and eddy components of available potential energy (APE) and kinetic
energy (KE). For this study, the LEC is computed in a **limited-area, storm-relative**
framework: the integration domain is a 15°×15° box centred at the tracked cyclone
position at each time step. This choice avoids the classical global-domain assumption
and allows the energy budget to be attributed specifically to the cyclone's local
environment at each phase of its lifecycle.

The computations were performed with the **LorenzCycleToolkit** (results archived at
Zenodo DOI: `10.5281/zenodo.18243447`). Variables were computed from ERA5 reanalysis
at 3-hourly temporal resolution. The lifecycle of each cyclone is divided into four
sequential phases — Incipient, Intensification, Mature, and Decay — based on the
temporal evolution of the energy terms.

### 1.2 Variable definitions and sign conventions

The six key LEC variables depicted in the figures are:

| Symbol | Full name | Physical meaning |
|--------|-----------|-----------------|
| $C_a$ | Conversion of zonal APE to eddy APE | Baroclinic energy extraction from the mean state |
| $C_k$ | Conversion of zonal KE to eddy KE | Barotropic energy exchange with mean flow |
| $BA_e$ | Boundary flux of eddy APE | Net import/export of eddy APE across the domain boundary |
| $BK_e$ | Boundary flux of eddy KE | Net import/export of eddy KE across the domain boundary |
| $G_e$ | Generation of eddy APE | Production of eddy APE by diabatic heating and heat fluxes |
| $K_e$ | Eddy kinetic energy | Total kinetic energy associated with eddy flow in the domain |

All terms are expressed as **area-integrated quantities** (units: W m⁻²) except $K_e$
(units: J m⁻²). The sign convention follow the standard Lorenz (1955) formulation:

- $C_a > 0$: zonal APE → eddy APE (baroclinic development; the mean temperature
  gradient is being exploited by the growing disturbance)
- $C_a < 0$: eddy APE → zonal APE (baroclinic stabilization)
- $C_k < 0$: zonal KE → eddy KE ($KZ \to KE$; barotropic growth — the mean zonal flow
  exports kinetic energy into the growing eddy)
- $C_k > 0$: eddy KE → zonal KE ($KE \to KZ$; barotropic export — eddies return kinetic
  energy to the mean zonal flow)
- $BA_e > 0$: eddy APE imported into the domain
- $BK_e > 0$: eddy KE imported into the domain (consistent with downstream development)
- $G_e > 0$: diabatic generation of eddy APE (e.g., latent heat release)

> **Sign convention note (Southern Hemisphere):** The sign conventions above are
> defined in the standard mathematical framework and apply independently of hemisphere.
> However, the *physical interpretation* must account for the reversed meridional
> temperature gradient sign in the Southern Hemisphere: in the SH, the mean
> equator-to-pole temperature gradient is negative (cold poleward), which is the reverse
> of the NH. For correctly implemented LEC code, $C_a > 0$ still indicates baroclinic
> growth regardless of hemisphere. Reviewers and coauthors are encouraged to verify
> sign convention documentation in the LorenzCycleToolkit if there is any doubt.

### 1.3 Energy Patterns (EP) classification

K-means clustering (k = 3) on the principal components of the LEC energy terms
defines three Energy Patterns:

- **EP1:** Large positive $C_a$ (strong baroclinic extraction from the mean temperature
  gradient) combined with strongly negative $C_k$ ($KZ \to KE$ — the mean zonal flow
  actively exports kinetic energy into the developing cyclone). EP1 systems therefore
  simultaneously exploit both the mean APE reservoir (via $C_a > 0$) and the mean
  kinetic energy reservoir (via $C_k \ll 0$). This co-occurrence of baroclinic and
  barotropic growth is a defining feature of EP1.
- **EP2:** Moderate conversion magnitudes; neither baroclinic nor barotropic conversion
  overwhelmingly dominates. EP2 occupies an intermediate position in $C_a$–$C_k$ space
  relative to EP1 and EP3.
- **EP3:** Distinct $C_a$ and $C_k$ signatures compared with EP1. The full EP3
  characterisation should be read from the LPS trajectories in Figure 4 (cluster
  centroid positions in the $C_k$–$C_a$ plane) in conjunction with Figure 8
  (EPALL-relative composites), which together capture the distinguishing dynamics.

**Caution:** The EP labels are assigned by k-means, which maximizes within-cluster
variance in PCA space. The physical descriptions above are post-hoc interpretations
consistent with the cluster centroid positions in energy-space; they should be treated
as descriptive summaries, not deterministic or exclusive physical mechanisms.

---

## 2. Figure 1 — Tracks and genesis frequency

**What this figure shows:** All cyclone tracks in the dataset (n ≈ 3820, 1979–2020)
colored by genesis region (ARG, SE-BR, LA-PLATA), plus a sunburst chart of genesis
frequency decomposed by region and season.

**Scientific purpose:** To establish the geographic scope and seasonal distribution of
the cyclone population, providing context for the EP-based analysis.

**Genesis region definitions:**
The three regions (ARG, SE-BR, LA-PLATA) are rectangular geographic boxes defined
in the preprocessing pipeline. The exact bounding coordinates are encoded in
`scripts/preprocess_data/` and should be documented there. Readers comparing
regional statistics across studies should verify region boundaries, as definitions
vary across the South Atlantic cyclone climatology literature
(e.g., Hoskins & Hodges 2005; Reboita et al. 2010; Gramcianinov et al. 2019).

**Seasonal convention:** Southern Hemisphere seasons are used throughout:
- DJF = austral summer (Dec–Feb)
- MAM = austral autumn (Mar–May)
- JJA = austral winter (Jun–Aug)
- SON = austral spring (Sep–Nov)

**Methodological note:** The frequency sunburst shows the percentage of cyclones
within each genesis-region × season cell relative to the total dataset. It does not
account for differences in region area, so it is a frequency diagram, not a density
diagram.

---

## 3. Figure 2 — Case study: cyclone 20070643

**What this figure shows:** Three-panel energetics + track portrait for a single
representative cyclone (ID 20070643).

**Scientific purpose:** To illustrate how the Lorenz Phase Space (LPS) diagram
encodes the lifecycle energetics of an individual cyclone, motivating the
population-level analysis in Figures 3–4.

### 3.1 Lorenz Phase Space diagrams

Two complementary LPS diagrams are shown:

**Conversion LPS** (panel a):
- X-axis: $C_k$ — barotropic conversion [W m⁻²]
- Y-axis: $C_a$ — baroclinic conversion [W m⁻²]
- Marker color: $G_e$ — generation of eddy APE [W m⁻²]
- Marker size: $K_e$ — eddy kinetic energy [J m⁻²]

The trajectory through this plane reveals the dominant energy pathway. With the
sign convention $C_k < 0$ = $KZ \to KE$:
- **Upper-left quadrant** ($C_a > 0$, $C_k < 0$): both baroclinic growth (exploiting
  the mean temperature gradient) and barotropic growth (importing $KE$ from the mean
  zonal flow) are simultaneously active. EP1 cyclones characteristically occupy this
  region.
- **Upper-right quadrant** ($C_a > 0$, $C_k > 0$): baroclinic growth with concurrent
  barotropic export of eddy $KE$ back to the mean flow.
- **Lower-left quadrant** ($C_a < 0$, $C_k < 0$): barotropic $KZ \to KE$ growth
  despite baroclinic stabilization.
- **Lower-right quadrant** ($C_a < 0$, $C_k > 0$): both baroclinic and barotropic
  stabilization; characteristic of decaying systems.

**Imports LPS** (panel b):
- X-axis: $BA_e$ — eddy APE boundary flux [W m⁻²]
- Y-axis: $BK_e$ — eddy KE boundary flux [W m⁻²]
- Marker color: $G_e$; marker size: $K_e$ (same as conversion panel)

The imports plane documents whether the cyclone is gaining or losing energy laterally
across its domain boundary. $BK_e > 0$ with $BA_e > 0$ indicates both eddy KE and APE
are imported, consistent with downstream development (e.g., from an upstream trough).

**Interpretation caution:** These phase-space trajectories are sequence diagrams —
they show *where* the cyclone visits in energy space at each time step. They do not
prove causality between energy states. A cyclone spending time in the baroclinic
quadrant is *consistent with* baroclinic development but does not rule out other
physical processes operating simultaneously.

### 3.2 Track panel (panel c)

The geographic track is plotted at 3-hourly resolution (matching LEC data availability),
colored by relative vorticity (`vor42`, ×10⁻⁵ s⁻¹) and sized by $K_e$. Genesis is
marked with a green circle; lysis with a red × marker.

**Cyclone 20070643 metadata (verified from data file):**
- Genesis: 2007-07-24 14:00 UTC
- Lysis: 2007-07-29 03:00 UTC
- Duration: 109 hours
- Peak vorticity: 2007-07-27 02:00 UTC, 15.48 × 10⁻⁵ s⁻¹

---

## 4. Figure 3 — Phase-space density by lifecycle phase

**What this figure shows:**
Kernel density distributions in the Lorenz Phase Space for the **full cyclone population**,
stratified by lifecycle phase (Incipient, Intensification, Mature, Decay). The 2×2
arrangement of pre-rendered images produces an effective 8-panel figure:
(a)–(b) Incipient, (c)–(d) Intensification, (e)–(f) Mature, (g)–(h) Decay.
Within each arrangement, left = Conversion plane, right = Imports plane.

**Scientific purpose:** To reveal the dominant energy pathways across the cyclone
population as a whole, and to show how these pathways evolve through the lifecycle.
This figure motivates the EP classification: if all cyclones followed the same
trajectory, a single cluster would suffice; the diversity of trajectories shown here
supports the need for multiple clusters.

**Methodological note:** The density in each panel is computed by a KDE over the
phase-space positions of all cyclones at the corresponding lifecycle phase, not per
individual track. The bandwidth and kernel used are inherited from
`scripts/exploratory/density_diagrams_with_ge.py` (see that script for details).

**Interpretation guidance:**
- A concentrated high-density region indicates a preferred (common) energy state at
  that lifecycle phase.
- A bimodal or diffuse distribution indicates diversity in energy pathways.
- Phase-to-phase shifts in the density peak reveal systematic lifestyle progression.

---

## 5. Figure 4 — Lorenz Phase Space for EP1–EP3

**What this figure shows:**
Two-panel LPS figure for all three Energy Patterns (EP1, EP2, EP3) displayed together,
showing phase trajectories from Incipient through Decay:
- **(a) Conversion LPS:** $C_a$ (y) vs $C_k$ (x); marker color = $G_e$; size = $K_e$
- **(b) Imports LPS:** $BK_e$ (y) vs $BA_e$ (x); marker color = $G_e$; size = $K_e$

**Scientific purpose:** To show how the three EP clusters differ qualitatively in their
LPS signatures: EP1 predominantly occupies positive $C_a$ / negative $C_k$ territory
(baroclinic AND barotropic growth simultaneously, the defining EP1 signature); EP2
occupies intermediate territory; EP3 has a distinct $C_k$ position — see Figure 4
centroid coordinates for the exact placement.

**Interpretation caution:**
- The phase trajectories connect phase-median values (or phase-mean centroids), not
  individual cyclone paths. They summarize typical behaviour, not the full
  within-cluster variance (see Figure 3 for that).
- Overlap between EP trajectories in the imports plane is expected; differences are
  more pronounced in the conversion plane.
- "Zoomed" variants of this figure focus on the region near zero on both axes, where
  the EP differences are most visible; this zoom does not distort or omit data.

---

## 7. Figure 6 — Intensity, seasonality, and interannual trends

### 7.1 Intensity distribution (panel a — violin plot)

**Variable:** Maximum relative vorticity per cyclone (`vor42`), units: ×10⁻⁵ s⁻¹.
The vorticity is taken at the 850 hPa level (standard for relative vorticity tracking)
and represents the peak instantaneous vorticity recorded anywhere along the track.

**Interpretation:** Higher vorticity indicates a more intense cyclone. The violin
shows the full distribution; the mean and median within each EP are also displayed.
Differences in intensity distributions between EPs should be interpreted as
*statistical tendencies*, not deterministic predictions — there is substantial
overlap between EPs at the individual-cyclone level.

### 7.2 Seasonal distribution (panel b — bar chart)

**Method:** Genesis month is assigned to a season (SH convention); the percentage
of cyclones per season within each EP is computed as $n_\text{EP,season} / n_\text{EP,total} \times 100$.

**Physical interpretation — caution:**
Seasonal preferences in genesis frequency reflect aggregate climatological conditions
(meridional temperature gradient strength, jet-stream position, baroclinic instability
availability). However, the relationship between season and EP is correlational.
Causal attribution (e.g., "EP1 occurs in winter because stronger baroclinicity favours
$C_a$") is physically reasonable but not directly demonstrated by the frequency
statistics alone.

### 7.3 Trend analysis (panel c — Mann–Kendall)

#### Motivation

Annual cyclone counts are a discrete, low-sample-size (n = 42 years, 1979–2020)
time series that may contain serial correlation. Classical trend tests assume
independence, which can inflate false positive rates when positive autocorrelation
is present (Hamed & Rao 1998). A non-parametric framework is used throughout.

#### Mann–Kendall S-statistic

$$
S = \sum_{i=1}^{n-1} \sum_{j=i+1}^{n} \operatorname{sgn}(x_j - x_i),
$$

where $\operatorname{sgn}(y) = 1$ if $y > 0$, $= 0$ if $y = 0$, $= -1$ if $y < 0$.
Under $H_0$ (no trend, independent data), $S$ is approximately normally distributed
for large $n$ with mean 0 and variance $\mathrm{Var}(S)$ (Mann 1945; Kendall 1975).

#### Theil–Sen slope estimator

$$
\hat{\beta} = \mathrm{median}\!\left\{ \frac{x_j - x_i}{t_j - t_i} : 1 \le i < j \le n \right\}.
$$

This robust, nonparametric estimator of the linear trend rate (cyclones per year)
is resistant to outliers. Implemented via `scipy.stats.theilslopes` with 95%
confidence intervals (Sen 1968).

#### Autocorrelation detection and correction

**Detrending:** Before testing for autocorrelation, the Theil–Sen trend line is
subtracted from the series to avoid conflating trend with autocorrelation signal.

**Ljung–Box test:** Applied to the detrended residuals at a single lag
$h = \min(10, n-1)$. If the test rejects $H_0$ at $p < 0.05$ (serial independence),
the series is flagged as autocorrelated.

> **Why a single Ljung–Box test (not multiple lag tests)?**
> Testing individual lags separately inflates the family-wise Type I error. The
> portmanteau test at lag $h$ evaluates the joint null across all lags $1, \ldots, h$
> simultaneously.

**Hamed–Rao effective sample size correction** (when autocorrelation is detected):

The effective sample size is:

$$
n_e = \frac{n}{1 + \dfrac{2}{n} \sum_{k=1}^{n-1} (n - k)\, r_k},
$$

where $r_k$ is the sample lag-$k$ autocorrelation of the detrended residuals.
The MK test variance is multiplied by $n / n_e$, yielding a corrected $Z$-statistic
and p-value. This correction reduces the inflated false positive rate caused by
positive serial correlation (Hamed & Rao 1998). Implemented via
`pymannkendall.hamed_rao_modification_test`.

When no autocorrelation is detected, the original Mann–Kendall test is used.

**All five MK variants** are computed and saved to `results/exploratory/mk_trend_results.csv`
for transparency (original, Hamed–Rao, Yue–Wang, pre-whitening, trend-free pre-whitening;
see Yue & Wang 2004 for the Yue–Wang modification). The figure annotation uses only
the designated variant (Hamed–Rao when autocorrelated; original otherwise). The CSV
allows reviewers to inspect all variants.

#### Interpretation constraints

1. **Significance at $\alpha = 0.05$ is not proof of a physical trend.** With 42 data
   points and multiple testing across three EPs, some false discoveries are expected.
2. **The test is for monotonic trends**, not step changes or other trend shapes.
3. **The Hamed–Rao correction is conservative.** Estimated autocorrelations from
   short residual series are noisy; the effective sample size may be under- or
   overestimated.
4. **Annual counts conflate frequency with duration changes.** If cyclone generation
   rates and track lengths both change, counts alone do not disambiguate the two.

---

## 8. Figure 7 — Genesis density (KDE)

### 8.1 KDE methodology

Genesis density is computed following **Hoskins & Hodges (2005)** using a Gaussian
kernel with the haversine (great-circle) distance metric:

$$
\hat{f}(\mathbf{x}) = \frac{1}{n \, A(\mathbf{x})} \sum_{i=1}^{n}
   K\!\left(\frac{d(\mathbf{x}, \mathbf{x}_i)}{\sigma}\right),
$$

where:
- $d(\mathbf{x}, \mathbf{x}_i)$ = great-circle distance between evaluation point $\mathbf{x}$ and genesis location $\mathbf{x}_i$
- $\sigma \approx 0.05$ radians $\approx$ 555 km at the equatorial radius — the kernel bandwidth
- $K(\cdot)$ = Gaussian kernel: $K(u) = \exp(-u^2 / 2)$
- $A(\mathbf{x})$ = area element at $\mathbf{x}$ (accounts for the convergence of meridians)
- $n$ = number of cyclone genesis events in the group

**Grid:** Global 2.5° resolution (128 longitude × 64 latitude points, consistent with
standard spectral truncation practice in the Hoskins & Hodges framework).

**Normalization to density units (panel a, all cyclones):**
$$
\rho_\infty = \frac{\hat{f} \cdot n}{T \cdot A_s}
$$
where $T$ is the study period in years (42 years, 1979–2020) and $A_s$ is a reference
area scale. The result is expressed in **cyclones per 10⁶ km² per year**, which is the
standard unit for Southern Hemisphere cyclone density maps
(e.g., Hoskins & Hodges 2005; Reboita et al. 2010).

**Implementation note:** The script uses `sklearn.neighbors.KernelDensity` with a
haversine metric on radian-converted coordinates, which correctly handles great-circle
distances. A reference Earth radius of 6369 km (at ~40°S) is used in area
normalization. The exact normalization constants are in the script configuration block
of `06_figure_genesis_density_kde.py`.

### 8.2 Min-max normalized relative anomaly (panels b–d)

To compare genesis distributions across EPs of very different size
(EP1: ~12% of total; EP3: ~63% of total), a normalized relative anomaly is
computed for each EP panel:

**Step 1 — Min-max scaling** (applied separately to each density field):
$$
\widetilde{\rho}(x) =
\begin{cases}
\dfrac{\rho(x) - \min(\rho > 0)}{\max(\rho) - \min(\rho > 0)} & \text{if } \rho(x) > 0 \\
0 & \text{otherwise}
\end{cases}
$$

This maps positive density values to [0, 1] while preserving the spatial structure.
Zero-density grid cells remain at zero.

**Step 2 — Relative anomaly:**
$$
\Delta_\text{EP}(x) = \widetilde{\rho}_\text{EP}(x) - \widetilde{\rho}_\text{All}(x)
$$

Values range approximately $-1$ to $+1$:
- $\Delta_\text{EP} > 0$ (red): the EP contributes *relatively more* genesis at
  this location than the overall climatology, after normalizing for scale differences
- $\Delta_\text{EP} < 0$ (blue): *relatively less* genesis contribution
- $\Delta_\text{EP} \approx 0$ (white): proportional contribution matching the climatology

### 8.3 Interpretation guidance

**What the normalization achieves:** It isolates *spatial preference* (where within
the genesis region does each EP preferentially occur?) from *frequency effects*
(how many cyclones does each EP contain?). Without normalization, Panel (d) would be
dominated by EP3's absolute majority.

**What the normalization does not show:**
- It does not indicate *absolute intensities* — a strong red anomaly in a region of
  low absolute density still corresponds to relatively few cyclones.
- It does not establish whether the spatial preference is statistically significant.
  Significance testing for spatially correlated density fields requires bootstrap or
  Monte Carlo approaches not yet applied here.
- The normalization is purely spatial and descriptive; it does not account for
  genesis-region overlap between EPs.

**Caution about interpretation:** Statements such as "EP2 preferentially generates
cyclones equatorward" are descriptive spatial observations consistent with the
normalized anomaly patterns. They should be treated as hypotheses warranted by the
data pattern, not confirmed physical causal relationships without further analysis.

---

## 9. Figure 8 — EP − EPALL dynamical composites (EPALL-relative anomaly)

### 9.1 Rationale for the EPALL-relative approach

Figure 8 shows **EP − EPALL composites**: the mean field of each Energy Pattern
minus the mean field of all cyclones combined (EPALL). Subtracting EPALL eliminates
the dynamical signature that is common to all intensifying South Atlantic extratropical
cyclones. The residual therefore isolates what is *dynamically distinctive* about
each pattern — why EP1, EP2, and EP3 are energetically different, rather than how
they resemble a generic cyclone.

> **Contrast with climatological anomaly approach:**
> The climatological anomaly (field − ERA5 monthly mean) removes the background
> climate state but retains features shared by all cyclones. The EPALL-relative
> approach removes those shared-cyclone features, revealing the EP-specific structure
> at a finer level of detail.

### 9.2 Composite methodology

Storm-relative composites for EP1 (n as reported by script), EP2, EP3, and EPALL
are precomputed by `step3_precompute_composites.py` over each cyclone's
**intensification phase**, with each case centred at the tracked position
(0°, 0° in relative coordinates). Domain: ±15° in both relative longitude and
latitude (121 × 121 grid points at 0.25° ERA5). Figure 7 then computes
`EP_composite − EPALL_composite` at plot time.

> **General caveats for storm-relative composites:**
> 1. Compositing smooths case-to-case variability; individual cyclones may differ
>    substantially from the mean composite.
> 2. Storm-relative centering does not rotate fields to align with propagation
>    direction. Asymmetries may partly reflect preferred propagation directions.
> 3. Cases with tracking failures or data gaps are excluded.

### 9.3 Row 1: Upper-level / baroclinic structure departure

**Shading — $(\text{PV}_{200}) - \text{EPALL}$ [PVU]:**

Ertel PV at 200 hPa minus the EPALL composite. Positive values (red) indicate the
EP has a stronger ridge (or weaker trough) at 200 hPa relative to the generic
cyclone; negative values (blue) indicate a deeper upper-level trough anomaly.

In the Southern Hemisphere, cyclonic PV is negative; an upper trough deepening
corresponds to more negative PV, so an *anomalously deep trough relative to EPALL*
appears as a blue (negative) departure.

**Contours — $(\text{EGR}) - \text{EPALL}$ [day⁻¹]:**

Eady Growth Rate departure from the EPALL composite. Solid firebrick contours
(positive: 0.03, 0.06, 0.09, 0.12 day⁻¹) indicate the EP's baroclinic instability
potential *exceeds* that of a generic intensifying cyclone. Dashed steelblue contours
(negative levels) indicate a deficit. All EGR contour linewidths: 2.0 pt.

> Note: EGR is a potential growth rate (see Eq. in section 7 notes), not an
> observed growth rate. A positive EGR departure means the environment is
> *more favourable* for baroclinic development relative to the EPALL average — not
> that intensification is faster.

**SLP total thin contours:** Total EP composite sea-level pressure [hPa] at 2 hPa
intervals — provides the absolute cyclone position and depth as a spatial reference
layer. No wind vectors are drawn in Row 1.

### 9.4 Row 2: Low-level frontal / thermal structure departure

**Shading — $(\text{PV}_{850}) - \text{EPALL}$ [PVU]:**

Low-level PV departure from EPALL. Anomalously cyclonic PV at 850 hPa appears as a
negative departure (more negative than EPALL, blue). Positive values indicate
anticyclonic PV features exceeding the EPALL reference (Rossa et al. 2000;
Lackmann 2011).

**Contours — $(\text{T-adv}_{850}) - \text{EPALL}$ [K h⁻¹]:**

Horizontal temperature advection at 850 hPa:
$$
\text{T-adv} = -\mathbf{v}_{850} \cdot \nabla T_{850} \quad [\text{K s}^{-1}]
$$
Residue relative to EPALL, converted to K h⁻¹ (×3600). Contour interval:
0.05 K h⁻¹ (up to ±0.20 K h⁻¹). Dashed blue = relative cold-advection excess;
solid red = relative warm-advection excess. Reveals which EPs have stronger or
weaker frontal thermal gradients than the average intensifying cyclone.

**Wind vectors — $(u, v)_{850} - \text{EPALL}$ [m s⁻¹]:** Reference vector: 5 m s⁻¹.

### 9.5 Row 3: Jet-level energetics departure

**Shading — $\text{AFC}_{250} - \text{EPALL}$ [W m⁻²]:**

Ageostrophic geopotential flux convergence at 250 hPa:
$$
\text{AFC} = -\nabla \cdot (\mathbf{v}_{ag} \,\phi)
$$
minus the EPALL composite (Orlanski & Katzfey 1991; Orlanski & Sheldon 1993).

Sign convention of the departure:
- $\text{AFC} - \text{EPALL} > 0$ (red): EP has a stronger local eddy KE source
  at the jet level than the average cyclone — indicates more active jet-level
  energy import than typical.
- $\text{AFC} - \text{EPALL} < 0$ (blue): EP receives less jet-level KE import
  than the average intensifying cyclone.

> **Connection to LEC:** AFC is the jet-level counterpart of $BK_e$ in the LEC
> framework. A positive AFC departure in an EP's composite suggests that EP is
> distinctively associated with enhanced downstream energy propagation from the jet
> (i.e., $BK_e > 0$ above average). In the context of the sign correction where
> $C_k < 0$ = $KZ \to KE$, positive AFC − EPALL is physically consistent with
> the kinetic energy source identified by strongly negative $C_k$ in EP1.

**Wind vectors — $(u, v)_{250} - \text{EPALL}$ [m s⁻¹]:** Reference vector: 5 m s⁻¹.

**Contours — $(\text{KE-adv}_{250}) - \text{EPALL}$ [m² s⁻³]:**

Kinetic energy advection at 250 hPa minus the EPALL composite, contoured at ±0.005 and
±0.010 m² s⁻³. Solid firebrick contours = EP has *greater* jet-level KE transport than
the generic cyclone; dashed steelblue = EP has *less*. This field directly represents
the local KE flux divergence signature at the jet level — complementary to AFC
(which captures the ageostrophic flux convergence contribution). Linewidths: 2.0 pt.

**Rayleigh–Kuo sign-reversal hatching:**

The hatching marks the meridional zero-crossing band of $\partial \eta / \partial y$
at 250 hPa using the **total EP composite** (not EPALL-relative). Subtracting
EPALL from $\partial \eta / \partial y$ would produce a physically meaningless field
because the Rayleigh–Kuo criterion is an intrinsic property of the background flow,
not a departure from a reference.

For each grid point $(i, j)$, the mask is True when:
$$
\min_{|i'-i| \le 1} [\partial \eta / \partial y]_{(i', j)} < 0
\quad \text{AND} \quad
\max_{|i'-i| \le 1} [\partial \eta / \partial y]_{(i', j)} > 0.
$$

> **Critical caveat:** The hatching marks where the *necessary* condition for
> barotropic instability (sign reversal of $\partial \eta / \partial y$) is locally
> approached. This is **not sufficient** for barotropic instability. The classical
> Rayleigh–Kuo theorem requires the sign reversal to extend over a finite meridional
> distance, and actual barotropic growth requires additional conditions.

**LEC box (dashed rectangle, all panels):** The 15°×15° domain used for LEC
integration, centred at (0°, 0°). Shows how the dynamical EP-distinctive fields
relate spatially to the LEC computation window.

### 9.6 Global colormap design

Shading fields use the custom diverging colormap `CMAP_PV_ANOM` (rows 1–2: PV
anomalies) and `CMAP_AFC` (row 3: AFC anomaly), both defined in
`scripts/utils/colormaps.py`. Both resolve to the same 7-stop blue→neutral→red
palette (`#011462 → #106294 → #A7C9DA → #E8E1DD → #CDB7B6 → #935B5E → #5B020A`),
chosen for perceptual symmetry around zero and print-safe contrast. Colormap limits
for each row are computed as the 98th percentile of absolute values across **all
three EP columns**, so the colour scale is identical between EP1, EP2, and EP3.
Amplitude differences between patterns are directly readable from colour intensity
without any scale rescaling.

---

## 9. Figure S1 — PCA and clustering validation

**Scientific purpose:** To establish that:
1. PCA retains sufficient information with a reduced number of components (90%
   variance threshold applied).
2. The choice of $k = 3$ clusters is objectively justified by multiple independent
   Cluster Validity Indices (CVIs).

**PCA variance panel (a):**  
The cumulative explained variance curve shows how many components are needed to
represent 90% of the total variance in LEC energy-term space. The "kink" in the
curve (elbow) additionally guides component selection.

**Cluster validity indices panel (b):**  
Five independently defined CVIs are normalised to [0, 1] and displayed together.
Their agreement at $k = 3$ constitutes convergent evidence for three clusters.

> **Caution:** CVIs measure internal cluster quality (compactness, separation), not
> whether the clusters correspond to physically distinct atmospheric regimes. The
> physical interpretation of EP1–EP3 is validated by the dynamical composites
> (Figure 7) and the characteristic LPS trajectories (Figure 4), not by the CVIs
> alone.

---

## 10. Figure 5 — Vertical Ca/Ck profiles (EP1, EP2, EP3)

**Scientific purpose:** To determine which pressure level(s) carry the strongest
baroclinic ($C_a$) and barotropic ($C_k$) energy conversion signals across all three
Energy Patterns, and to identify systematic differences in the vertical structure of
the conversion terms between EP1, EP2, and EP3.

### 10.1 Vertical profiles

For each cyclone in EP1, EP2, and EP3 with available Zenodo LEC data, the
time-mean (over the intensification phase) profiles of $C_a(p)$ and $C_k(p)$ at
32 pressure levels (1000–100 hPa) are computed. These profiles are aggregated into
per-EP level distributions and displayed as three side-by-side box-and-whisker plots
at each pressure level — one box per EP (EP1: red, EP2: blue, EP3: green).

The figure reveals:
- **Peak $C_a$** level: typically in the mid-troposphere (~350–400 hPa), near the
  level of maximum baroclinic interaction between the lower-tropospheric temperature
  gradient and the upper-level jet. Differences between EPs in the pressure level
  and magnitude of peak $C_a$ reflect differences in the effective baroclinic depth.
- **Minimum $C_k$** level (most negative $C_k$, indicative of the strongest
  $KZ \to KE$ transfer): again in the mid-troposphere, but the depth and magnitude
  vary markedly between EPs — EP1 typically shows the most pronounced barotropic
  signal, consistent with its dominant $C_k < 0$ signature in the integrated LEC.

### 10.2 Data corrections

Two corrections are applied to raw LEC level data from the Zenodo archive:

**Ca sign inversion:**
$$
C_{a,\text{corrected}} = -C_{a,\text{raw}}
$$
*Reason:* The LorenzCycleToolkit version used to produce the Zenodo archive stored
`Ca_level.csv` with the opposite sign convention relative to the integrated `Ca`
values reported in the main LEC output files.

**Ck gravity normalization:**
$$
C_{k,\text{corrected}} = C_{k,\text{raw}} / g, \quad g = 9.8 \, \text{m s}^{-2}
$$
*Reason:* The same LorenzCycleToolkit version stored `Ck_level.csv` without dividing
by $g$, unlike the integrated `Ck` terms. This mismatch was identified by comparing
the vertical integral of `Ck_level.csv` with integrated `Ck` in the same ensemble
(see `scripts/ep_structure_analysis/validate_step2.py` or equivalent validation).

> **These corrections are version-specific.** If the Zenodo archive is ever replaced
> or regenerated with an updated version of LorenzCycleToolkit, it is essential to
> re-validate whether these corrections still apply before using this figure.

### 10.3 Interpretation

The identification of ~350–400 hPa as the level of peak $C_a$ is broadly consistent
with the classical picture of baroclinic instability, in which the temperature
perturbation and geopotential tilt are maximized near the steering level of the wave
(Charney 1947; Eady 1949). The co-location of the $C_a$ maximum and $C_k$ minimum
(most negative $C_k$, i.e., maximum $KZ \to KE$ transfer) in the mid-troposphere
for EP1 suggests that in the same layer the cyclone is simultaneously extracting
energy baroclinically ($C_a > 0 \Rightarrow$ APE from mean temperature gradient) and
barotropically ($C_k < 0 \Rightarrow$ KE imported from the mean zonal flow). This
co-occurrence of both growth mechanisms in one vertical layer is consistent with
active development in an environment that offers both baroclinic and barotropic
energy sources (Simmons & Hoskins 1978).

Comparing all three EPs in the same panels makes it possible to assess whether the
vertical level of dominant conversion — and not just the time-integrated magnitude —
differs between patterns. If the peak levels are similar across EPs while the
magnitudes differ, the EP classification is primarily an amplitude distinction. If
the peak levels differ, the EPs reflect structurally different vertical modes of
interaction with the background state.

**Caveats:**
- Sample sizes differ between EPs; the width of the distributions (IQR and whiskers)
  should be interpreted relative to the per-EP sample counts printed in the figure
  legend and at runtime.
- Cyclones with missing or incomplete LEC data from the Zenodo archive are excluded
  from each EP independently.

---

## Figure S3 — C_K vertical profile and integrated subterms (EP1)

**Scientific purpose:** To identify the pressure level at which barotropic
kinetic-energy conversion is strongest for EP1 cyclones, and to decompose the
vertically integrated $C_K$ into its five physical subterms.

$C_K$ decomposes barotropic kinetic-energy conversion into five subterms (A–E):

$$
C_K = \int \frac{1}{g} \left[ C_K^{(A)} + C_K^{(B)} + C_K^{(C)} + C_K^{(D)} + C_K^{(E)} \right] dp
$$

Sign convention (authoritative: `paper.tex`):
- $C_K < 0 \Rightarrow K_Z \to K_E$ (barotropic instability feeds the eddies)
- $C_K > 0 \Rightarrow K_E \to K_Z$ (eddies export energy to the mean flow)

EP1 cyclones show mean $C_K \approx -16.5$ W m⁻² — the strongest barotropic-instability
pattern among the three EPs — with the dominant level at ~350 hPa.

**Subterm mapping** (LorenzCycleToolkit `Ck_1`…`Ck_5` → paper labels A–E):

| Toolkit term | Paper label | Physical meaning |
|---|---|---|
| `Ck_1` | $C_K^{(A)}$ | Meridional gradient of zonal wind |
| `Ck_2` | $C_K^{(B)}$ | Meridional flux of eddy KE |
| `Ck_3` | $C_K^{(C)}$ | Curvature (tan φ) term |
| `Ck_4` | $C_K^{(D)}$ | Vertical shear of zonal wind |
| `Ck_5` | $C_K^{(E)}$ | Vertical shear of meridional wind |

**Data availability note:** Per-pressure-level files for the individual $C_K$
subterms are not part of the local Zenodo archive. Panel (a) therefore shows the
vertical profile of the *total* $C_K$ (from `Ck_level.csv`, EP1 cyclones,
intensification phase, gravity-corrected). Panel (b) shows the vertically
integrated subterms from `results/ck_analysis/ck_subterms_boxplot_input.csv`
(EP1 cyclones, phase-mean).

**Caveats:**
- Panel (a) and panel (b) come from different processing pipelines (Zenodo
  per-level archive vs. locally computed integrated subterms) — they are
  complementary, not directly reconcilable term-by-term.
- Results are restricted to EP1; the same subterm decomposition has not been
  run for EP2/EP3.

---

## 11. Global caveats and interpretation boundaries

1. **ERA5 reanalysis limitations:** All composites and statistics are derived from
   ERA5. Systematic biases in ERA5's representation of South Atlantic cyclones
   (e.g., intensity underestimation for rapidly deepening events in the pre-satellite
   era) may affect the results, particularly for the pre-1979 period (not applicable
   here, as the dataset starts in 1979) and for small, intense cyclones that may be
   under-resolved at 0.25°.

2. **Tracking algorithm sensitivity:** The cyclone database is produced by a specific
   tracking algorithm applied to ERA5 relative vorticity. Different algorithms,
   thresholds, or tracking variables produce different cyclone populations. Comparisons
   with other South Atlantic cyclone climatologies should account for methodological
   differences.

3. **Limited-area LEC framework sensitivity:** Results depend on the choice of
   integration domain (15°×15° box). Sensitivity to domain size is not explored in
   the current analysis. The domain choice is motivated by previous literature on
   regional LEC applications but has inherent subjectivity.

4. **k-means sensitivity:** k-means clustering is sensitive to initialisation and
   assumes spherical clusters. The robustness of k = 3 is supported by the CVI
   convergence (Figure S1), but the specific EP boundaries are not unique; a different
   clustering algorithm or feature set may produce different partitions.

5. **Trend significance and serial correlation:** Even with the Hamed–Rao correction,
   the trend results should be interpreted cautiously. The 42-year period (1979–2020)
   overlaps with the ERA5 period and does not extend into a longer climatological baseline.
   ERA5 homogeneity changes across its assimilation period (particularly the introduction
   of different satellite observing systems over time) may introduce artificial low-
   frequency variability that mimics trends.

6. **Composite field causality:** All composite fields in Figure 8 are simultaneous
   means during the intensification phase — they document co-location and co-occurrence,
   not causal relationships. The association between, e.g., positive AFC and cyclone
   intensification is consistent with downstream development theory but is not proved
   by composite analysis alone.

---

## 12. References

**Charney, J. G.** (1947). The dynamics of long waves in a baroclinic westerly current.
*Journal of Meteorology*, 4(5), 135–162. https://doi.org/10.1175/1520-0469(1947)004<0135:TDOLWI>2.0.CO;2

**Charney, J. G., & Stern, M. E.** (1962). On the stability of internal baroclinic jets
in a rotating atmosphere. *Journal of Atmospheric Sciences*, 19(2), 159–172.
https://doi.org/10.1175/1520-0469(1962)019<0159:OTSOIB>2.0.CO;2

**Eady, E. T.** (1949). Long waves and cyclone waves. *Tellus*, 1(3), 33–52.
https://doi.org/10.3402/tellusa.v1i3.8507

**Hamed, K. H., & Rao, A. R.** (1998). A modified Mann–Kendall trend test for
autocorrelated data. *Journal of Hydrology*, 204(1–4), 182–196.
https://doi.org/10.1016/S0022-1694(97)00125-X

**Hoskins, B. J., McIntyre, M. E., & Robertson, A. W.** (1985). On the use and
significance of isentropic potential vorticity maps. *Quarterly Journal of the Royal
Meteorological Society*, 111(470), 877–946.
https://doi.org/10.1002/qj.49711147002

**Hoskins, B. J., & Hodges, K. I.** (2002). New perspectives on the Northern Hemisphere
winter storm tracks. *Journal of the Atmospheric Sciences*, 59(6), 1041–1061.
https://doi.org/10.1175/1520-0469(2002)059<1041:NPOTNH>2.0.CO;2

**Hoskins, B. J., & Hodges, K. I.** (2005). A new perspective on Southern Hemisphere
storm tracks. *Journal of Climate*, 18(20), 4108–4129.
https://doi.org/10.1175/JCLI3570.1

**Kendall, M. G.** (1975). *Rank Correlation Methods* (4th ed.). Griffin, London.

**Kuo, H. L.** (1949). Dynamic instability of two-dimensional nondivergent flow in a
barotropic atmosphere. *Journal of Meteorology*, 6(2), 105–122.
https://doi.org/10.1175/1520-0469(1949)006<0105:DIOTDN>2.0.CO;2

**Lackmann, G.** (2011). *Midlatitude Synoptic Meteorology: Dynamics, Analysis, and
Forecasting*. American Meteorological Society, Boston. [Textbook; chapter on PV and
frontal dynamics]

**Lindzen, R. S., & Farrell, B.** (1980). A simple approximate result for the maximum
growth rate of baroclinic instabilities. *Journal of the Atmospheric Sciences*, 37(7),
1648–1654. https://doi.org/10.1175/1520-0469(1980)037<1648:ASARFT>2.0.CO;2

**Lorenz, E. N.** (1955). Available potential energy and the maintenance of the general
circulation. *Tellus*, 7(2), 157–167. https://doi.org/10.3402/tellusa.v7i2.8796

**Mann, H. B.** (1945). Nonparametric tests against trend. *Econometrica*, 13(3),
245–259. https://doi.org/10.2307/1907187

**Orlanski, I., & Katzfey, J.** (1991). The life cycle of a cyclone wave in the
Southern Hemisphere. Part I: Eddy energy budget. *Journal of the Atmospheric Sciences*,
48(17), 1972–1998. https://doi.org/10.1175/1520-0469(1991)048<1972:TLCOAC>2.0.CO;2

**Orlanski, I., & Sheldon, J. P.** (1993). A case of downstream baroclinic development
over western North America. *Monthly Weather Review*, 121(11), 2929–2950.
https://doi.org/10.1175/1520-0493(1993)121<2929:ACODBD>2.0.CO;2

**Rayleigh, Lord** (1880). On the stability, or instability, of certain fluid motions.
*Proceedings of the London Mathematical Society*, 11, 57–72.
https://doi.org/10.1112/plms/s1-11.1.57

**Reboita, M. S., Gan, M. A., Rocha, R. P., & Ambrizzi, T.** (2010). Regimes of
variability in the Brazilian precipitation: a review. *Revista Brasileira de
Meteorologia*, 25(2), 233–248. [*Note: cited as a South Atlantic cyclone climatology
context reference; verify specific findings match the usage context in the paper.*]

**Rossa, A. M., Wernli, H., & Davies, H. C.** (2000). Growth and decay of an
extra-tropical cyclone's PV-tower. *Meteorology and Atmospheric Physics*, 73(3–4),
139–156. https://doi.org/10.1007/s007030050070

**Sanders, F., & Gyakum, J. R.** (1980). Synoptic-dynamic climatology of the "bomb".
*Monthly Weather Review*, 108(10), 1589–1606.
https://doi.org/10.1175/1520-0493(1980)108<1589:SDCOT>2.0.CO;2

**Sen, P. K.** (1968). Estimates of the regression coefficient based on Kendall's tau.
*Journal of the American Statistical Association*, 63(324), 1379–1389.
https://doi.org/10.1080/01621459.1968.10480934

**Simmons, A. J., & Hoskins, B. J.** (1978). The life cycles of some nonlinear baroclinic
waves. *Journal of the Atmospheric Sciences*, 35(3), 414–432.
https://doi.org/10.1175/1520-0469(1978)035<0414:TLCONS>2.0.CO;2

**Sinclair, M. R.** (1994). An objective cyclone climatology for the Southern Hemisphere.
*Monthly Weather Review*, 122(10), 2239–2256.
https://doi.org/10.1175/1520-0493(1994)122<2239:AOCCFT>2.0.CO;2

**Yue, S., & Wang, C.** (2004). The Mann-Kendall test modified by effective sample size
to detect trend in serially correlated hydrological series. *Water Resources Management*,
18(3), 201–218. https://doi.org/10.1023/B:WARM.0000043140.61082.60

---

### TODO / unresolved uncertainties

- **Figure 5 corrections re-validation:** The Ca sign inversion and Ck / $g$
  normalization applied in `05_figure_vertical_levels.py` were validated against the
  current Zenodo archive. If the archive is regenerated, re-run the validation script
  before interpreting the figure.

- **Besson et al. (2021, WCD):** Cited in the old `figures/main/README.md` as a
  reference for EGR in the composite analysis. Full bibliographic details were not
  verified during this documentation revision. The citation should be confirmed and
  added to the reference list above before submission.

- **LorenzCycleToolkit paper:** If the LorenzCycleToolkit used to compute the Zenodo
  archive has an associated methods paper, it should be cited in the manuscript and
  in the methods documentation. Check the tool's repository or Zenodo metadata for
  a preferred citation.

- **Davis & Emanuel (1991):** Cited in the old README in the context of PV diagnostics
  for cyclogenesis. Reference is: Davis, C. A., & Emanuel, K. A. (1991). Potential
  vorticity diagnostics of cyclogenesis. *Monthly Weather Review*, 119(8), 1929–1953.
  https://doi.org/10.1175/1520-0493(1991)119<1929:PVDOC>2.0.CO;2 — Add to reference
  list if used in the paper.

- **Sign convention verification:** The sign convention for Ca and Ck in the
  LorenzCycleToolkit should be explicitly verified against the derivation in Lorenz (1955)
  and against a known test case before final submission.
