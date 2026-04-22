# SCIENTIFIC NOTES — LEC–Field Dependence Analysis

*Internal laboratory report. Last updated: 2026-04-22.*
*Authors: Danilo Couto de Souza. Contact: danilocs@usp.br*

---

## 1. Scientific Context and Research Questions

### Background

The Energy Pattern (EP) classification groups South Atlantic extratropical cyclones by
their dominant energetic regime during the intensification phase.  EP1, EP2, and EP3
were derived from PCA-based K-Means clustering on Lorenz Energy Cycle (LEC) diagnostics
computed from ERA5 reanalysis.  The subsequent composite analysis (pipeline:
`ep_structure_analysis`) revealed distinct atmospheric structures for each EP at the
group-mean level.

However, composite analysis captures *mean differences*: it tells us what the *average*
EP1, EP2, or EP3 cyclone looks like synoptically — but not how strongly the atmospheric
structure of an individual cyclone relates to its LEC signature.  This analysis bridges
that gap.

### Research Questions

1. **Inter-EP differences in LEC terms**: Do EP1, EP2, and EP3 cyclones diverge
   significantly in their LEC term magnitudes?  Which terms show the largest differences,
   and which EP pairs are most distinct?

2. **Inter-EP differences in synoptic structure**: Do the spatial features of the ERA5
   dynamic fields (PV, temperature advection, AFC, KE advection) differ systematically
   between EPs?  Which field–feature combinations are the strongest EP discriminators?

3. **LEC–field predictive associations**: Within each EP, do spatial structural features
   of the dynamic fields quantitatively predict LEC term magnitudes?
   - Primary measure: Spearman rank correlation ρ (monotonic association, directional).
   - Complementary measure: PREDEP α (non-parametric predictive dependence).

4. **Absolute vs. anomaly fields**: Does using EPALL-relative anomaly fields (isolating
   EP-specific structure) produce stronger or weaker LEC–field associations compared to
   absolute fields?

5. **Feature informativeness**: Which spatial features (e.g., zonal contrast, domain
   mean, NW quadrant mean) of which fields carry the most information about which LEC
   terms — and is this consistent across EPs or EP-specific?

---

## 2. Data and Sample

### 2.1 LEC Terms

**Source**: LEC results deposited on Zenodo (DOI: 10.5281/zenodo.18243447), 3-hourly
time series with 32 vertical levels, covering South Atlantic extratropical cyclones
identified in the Petrobras/CENPES cyclone database.

**Temporal averaging**: For this analysis, each LEC term is represented by its mean over
the **central 2–3 timesteps** of the intensification phase (the same temporal window
used in the `ep_structure_analysis` composites):

| Intensification length (N) | Timesteps selected |
|---|---|
| Odd N | 3 central: `[N//2−1, N//2, N//2+1]` |
| Even N | 2 central: `[N//2−1, N//2]` |
| N ≤ 3 | All timesteps |

Only cyclones with intensification duration > 24 h (N > 8 at 3-hourly resolution) are
included.  This ensures that the LEC snapshot and the ERA5 spatial snapshot are
temporally co-located.

**Terms analysed** — all 24 LEC terms are tested for inter-EP differences; the
**canonical 7** (`Ca`, `Ck`, `BAe`, `BKe`, `Ae`, `Ke`, `Ge`) are the primary analysis
terms for the association figures (they match the terms used to define EPs via
clustering):

| Term | Description | Units |
|------|-------------|-------|
| $A_z$ | Zonal available potential energy | W m⁻² |
| $A_e$ | Eddy available potential energy | W m⁻² |
| $K_z$ | Zonal kinetic energy | W m⁻² |
| $K_e$ | Eddy kinetic energy | W m⁻² |
| $C_z$ | Zonal APE → Zonal KE | W m⁻² |
| $C_a$ | Zonal APE → Eddy APE (baroclinic) | W m⁻² |
| $C_k$ | Eddy KE → Zonal KE (barotropic indicator) | W m⁻² |
| $C_e$ | Eddy APE → Eddy KE | W m⁻² |
| $BA_z, BA_e$ | Boundary APE fluxes | W m⁻² |
| $BK_z, BK_e$ | Boundary KE fluxes | W m⁻² |
| $B\Phi_Z, B\Phi_E$ | Boundary pressure work | W m⁻² |
| $G_z, G_e$ | APE generation (zonal, eddy) | W m⁻² |
| $RG_z, RK_z, RG_e, RK_e$ | Residuals | W m⁻² |
| $\partial X/\partial t$ | Energy tendencies (Az, Ae, Kz, Ke) | W m⁻² |

> **Note on canonical set**: `Ce`, `Cz`, and `Gz` were erroneously included in
> `LEC_TERMS_CORE` in earlier pipeline versions.  They are not part of the PCA-based
> clustering.  The canonical set was corrected (2025-04-19) to the 7 terms above.

### 2.2 ERA5 Dynamic Fields

**Source**: ERA5 reanalysis, 0.25° resolution, storm-centred 30°×30° domain extracted
from per-cyclone netCDF files in `data/era5_ep_structure/`.

**Derivation (step 3b)**: Raw files contain pressure-level `u`, `v`, `t`, `z`, `q`.
The five dynamic diagnostics are computed by `step3b_derive_era5_fields.py` using the
same diagnostic functions as `ep_structure_analysis`:

| Field | Level | Formula |
|-------|-------|---------|
| `pv_850` | 850 hPa | Ertel PV: $q = -g\,(\partial\theta/\partial p)\,\zeta_a$ (MetPy 3-level FD) |
| `pv_200` | 200 hPa | Same formula |
| `adv_T_850` | 850 hPa | $-\mathbf{V} \cdot \nabla T$ (MetPy spherical gradients) |
| `ke_adv_250` | 250 hPa | $-\mathbf{V} \cdot \nabla(\tfrac{1}{2}|\mathbf{V}|^2)$ |
| `afc_250` | 250 hPa | $-\nabla \cdot (\mathbf{V}_a K)$ (Orlanski & Katzfey 1991) |

ERA5 fields use the **single central timestep** of the intensification phase.

Two versions: **absolute** (raw derived field) and **EPALL-relative anomaly** (cyclone
field − EPALL composite mean).

### 2.3 Sample Sizes

| EP | N | % of total |
|----|---|--|
| EP1 | 332 | 12% |
| EP2 | 776 | 28% |
| EP3 | 1,625 | 60% |
| **Total** | **2,733** | 100% |

Group imbalance (factor ~5 across EPs) is intrinsic to the clustering solution and is
handled by the rank-based statistical tests used throughout.

---

## 3. Derived Fields and Feature Extraction

### 3.1 Feature Set (Current Pipeline Outputs)

Each 2D storm-centred field is summarised into 13 scalar features computed on the inner
15°×15° box centred on the cyclone (`step4_extract_features_absolute.py`,
`step5_extract_features_anomaly.py`).

| Feature | Definition |
|---|---|
| `domain_mean` | Spatial mean over the inner box |
| `centre_value` | Value at cyclone centre pixel |
| `border_north/south/east/west` | Mean over 5-cell-thick strip (1.25°) along each edge of inner box (strip spans full 15° edge length) |
| `contrast_ew` | $\bar{f}_E - \bar{f}_W$ (zonal asymmetry) |
| `contrast_sn` | $\bar{f}_S - \bar{f}_N$ (meridional asymmetry) |
| `sector_north/south/east/west` | Mean over cardinal sector (N/S/E/W half) of inner box |
| `domain_abs_mean` | $\overline{|f|}$ (mean absolute value) |

> **Feature set updated 2026-04-22:** `utils_features.py` was updated to replace
> diagonal quadrant means with cardinal sector means (`sector_north`, `sector_south`,
> `sector_east`, `sector_west`).  Step 4 was rerun on 2026-04-22 and all downstream
> steps (5–9) were regenerated accordingly.  All current results use sector features.

### 3.2 Feature Design Rationale

- `domain_mean`: overall field intensity; tends toward zero for signed fields
- `domain_abs_mean`: overall intensity for signed fields where sign cancellation matters
  (most useful for temperature advection and AFC)
- Border means: sharp spatial gradients on each side
- Contrasts: E–W = baroclinic tilt proxy; S–N = frontal structure proxy
- Sector means: capture structural asymmetry in each cardinal direction (N/S/E/W half-box means)

Total: 5 fields × 13 features × 2 types (absolute + anomaly) = **130 variables**
tested for inter-EP differences, plus 24 LEC terms = **154 variables** total.

---

## 4. Statistical Framework

### 4.1 Overview

Every scalar variable in the pipeline is tested for statistically significant
differences between EP1, EP2, and EP3 using a pre-specified decision tree
(implemented in `utils_statistical_tests.py`, orchestrated by
`step7b_ep_significance_tests.py`).  This is independent of the correlation / PREDEP
analysis and answers: *do EPs actually differ on this variable?*

### 4.2 Decision Tree

**Step 1 — Normality (Shapiro–Wilk, α = 0.05 per group):**
For n > 5,000, a subsample of 5,000 is used (seed = 42; over-rejection warning noted).

**Step 2 — Variance homogeneity (Brown–Forsythe–Levene, center='median'):**
Applied only when all groups pass normality.

**Step 3 — Global test selection:**

| Condition | Test | Effect size |
|-----------|------|-------------|
| All normal + equal variances | One-way ANOVA | $\omega^2$ |
| All normal + unequal variances | Welch ANOVA (custom impl.) | $\omega^2$ |
| ≥ 1 group non-normal | **Kruskal–Wallis** | $\varepsilon^2 = (H - k + 1)/(N - k)$ |

**Step 4 — Post-hoc pairwise tests (only if global p < α):**

| After | Post-hoc | Multiple-comp. correction | Pairwise effect size |
|-------|----------|--------------------------|---------------------|
| ANOVA | Tukey HSD | FWER (internal) | Cohen's *d* |
| Welch ANOVA | Pairwise Welch *t* | Holm step-down | Cohen's *d* |
| **Kruskal–Wallis** | **Dunn (1964)** | **Holm step-down** | rank-biserial *r* |

**Step 5 — Cross-variable correction:**
Benjamini–Hochberg FDR applied to all global test raw p-values within each block
(LEC terms, absolute features, anomaly features independently).

### 4.3 Effect Size Reference

| Measure | Context | Thresholds |
|---------|---------|------------|
| $\varepsilon^2$ | Kruskal–Wallis global | < 0.01 negligible; 0.01–0.06 small; 0.06–0.14 medium; > 0.14 large |
| $\omega^2$ | ANOVA/Welch global | Same thresholds |
| rank-biserial *r* | Non-parametric pairwise | < 0.10 negligible; 0.10–0.30 small; 0.30–0.50 medium; > 0.50 large |
| Cohen's *d* | Parametric pairwise | 0.20 small; 0.50 medium; 0.80 large |

### 4.4 Association Metrics (Spearman ρ and PREDEP)

For each EP × LEC term × field × feature combination, within the EP subsample:

- **Spearman ρ**: Primary metric.  Monotonic rank correlation.  Robust to
  non-Gaussianity.  Directly interpretable.
- **Pearson r**: Complementary linear metric.  Divergence from Spearman indicates
  non-linear (but monotonic) structure.
- **PREDEP α**: Non-parametric predictive dependence (Assunção et al. 2025).
  Direction: X = feature, Y = LEC term.  α = 0 → independence; α = 1 → perfect
  predictability.

PREDEP estimation: bootstrap estimator with $k = \lfloor\sqrt{N}\rfloor$ Ward-linkage
bins, $n_b = \lceil N \log N \rceil$ bootstrap pairs, Scott KDE bandwidth.

---

## 5. Inter-EP Significance: Empirical Results (April 2026 Run)

*Source data: `results/lec_field_dependence/step7b_diagnostic_table.csv`,
`step7b_pairwise_table.csv`, `step7b_significance_report.txt` (generated 2026-04-19).*

### 5.1 Statistical Path Actually Observed

**This is a key section: it describes what the decision tree did in practice, not just
what it was designed to do.**

| Criterion | Result |
|---|---|
| Total variables tested | 154 |
| all_normal = True (all 3 EP groups pass Shapiro–Wilk) | **0 / 154 (0%)** |
| Took ANOVA or Welch ANOVA path | **0 / 154 (0%)** |
| Took Kruskal–Wallis path | **154 / 154 (100%)** |
| Post-hoc test used | **Dunn (1964) with Holm step-down** |
| Pairwise effect size reported | **rank-biserial r** |
| Global effect size reported | **ε² (epsilon-squared)** |
| Cross-variable correction | **Benjamini–Hochberg FDR** |

**Explanation**: With EP1 n = 332, EP2 n = 776, EP3 n = 1,625, Shapiro–Wilk is highly
powered and detected non-normality in every tested group.  LEC terms (especially
conversion and residual terms) and ERA5-derived features (PV, advection) are
intrinsically skewed or heavy-tailed.  The ANOVA and Welch ANOVA branches are correctly
implemented in the code but were never activated in this dataset.

**Practical implication for methods writing**: All significance claims are backed by
Kruskal–Wallis (global, H-statistic, ε²) + Dunn post-hoc (pairwise, z-statistic, rank-
biserial r), with Holm correction for pairwise tests and BH-FDR across variables.

### 5.2 Significance Summary by Block

| Block | Variables | Sig (BH-adj p < 0.05) | Not significant |
|---|---|---|---|
| LEC terms | 24 | **24 / 24** | 0 |
| Absolute features | 65 | **60 / 65** | 5 |
| Anomaly features | 65 | **61 / 65** | 4 |

### 5.3 Pairwise Contrast Summary

| EP pair | Significant (out of 145 variables) | % |
|---|---|---|
| EP1 vs EP2 | 103 | 71% |
| EP1 vs EP3 | 112 | 77% |
| **EP2 vs EP3** | **130** | **90%** |

EP2 vs EP3 shows the most pervasive differences.  These groups, which together account
for 88% of the sample, are the most energetically and structurally distinct pair.

### 5.4 LEC Terms: Which Differ Between EPs

All 24 LEC terms are significant (BH-adj p < 0.05).  Table sorted by global ε².
Bold marks contrasts with large pairwise effect |r| > 0.50.

| Term | ε² | Effect class | Significant pairwise contrasts (Dunn–Holm) |
|---|---|---|---|
| $K_e$ | **0.396** | Large | EP2>EP1 (r=0.20); **EP1>EP3 (r=0.60)**; **EP2>EP3 (r=0.79)** |
| $RK_e$ | 0.290 | Large | EP1>EP2 (r=0.15); **EP3>EP1 (r=0.50)**; **EP3>EP2 (r=0.68)** |
| $C_e$ | 0.286 | Large | EP2>EP1 (r=0.25); EP1>EP3 (r=0.42); **EP2>EP3 (r=0.69)** |
| $C_a$ | 0.278 | Large | **EP1>EP3 (r=0.58)**; **EP2>EP3 (r=0.64)** *(EP1 ≈ EP2)* |
| $A_e$ | 0.276 | Large | EP2>EP1 (r=0.23); EP1>EP3 (r=0.47); **EP2>EP3 (r=0.66)** |
| $RG_e$ | 0.178 | Large | EP1>EP3 (r=0.45); **EP2>EP3 (r=0.51)** *(EP1 ≈ EP2)* |
| $G_e$ | 0.143 | Large | EP2>EP1 (r=0.22); EP1>EP3 (r=0.23); **EP2>EP3 (r=0.50)** |
| $C_k$ | 0.108 | Medium | EP2>EP1 (r=0.20); **EP3>EP1 (r=0.54)**; EP3>EP2 (r=0.29) |
| $RK_z$ | 0.103 | Medium | EP1>EP3 (r=0.36); EP2>EP3 (r=0.39) |
| $BK_z$ | 0.081 | Medium | EP3>EP1 (r=0.27); EP3>EP2 (r=0.36); EP1>EP2 (r=0.08) |
| $\partial K_e/\partial t$ | 0.073 | Medium | EP1>EP3 (r=0.36); EP2>EP3 (r=0.30) |
| $B\Phi_Z$ | 0.072 | Medium | EP2>EP1 (r=0.32); EP2>EP3 (r=0.35) |
| $BA_z$ | 0.069 | Medium | EP1>EP2 (r=0.25); EP1>EP3 (r=0.44); EP2>EP3 (r=0.21) |
| $RG_z$ | 0.061 | Medium | EP3>EP1 (r=0.29); EP3>EP2 (r=0.29) |
| $B\Phi_E$ | 0.057 | Small | EP2>EP1 (r=0.36); EP3>EP1 (r=0.09); EP2>EP3 (r=0.29) |
| $BK_e$ | 0.046 | Small | EP2>EP1 (r=0.18); EP1>EP3 (r=0.09); EP2>EP3 (r=0.29) |
| $A_z$ | 0.038 | Small | EP1>EP2 (r=0.33); EP1>EP3 (r=0.35) *(EP2 ≈ EP3)* |
| $\partial A_e/\partial t$ | 0.034 | Small | EP1>EP2 (r=0.20); EP1>EP3 (r=0.34); EP2>EP3 (r=0.11) |
| $C_z$ | 0.027 | Small | EP1>EP2 (r=0.15); EP3>EP2 (r=0.22) |
| $K_z$ | 0.024 | Small | EP1>EP3 (r=0.16); EP2>EP3 (r=0.19) |
| $G_z$ | 0.024 | Small | EP2>EP1 (r=0.13); EP3>EP1 (r=0.26); EP3>EP2 (r=0.13) |
| $\partial A_z/\partial t$ | 0.015 | Small | EP1>EP2 (r=0.13); EP3>EP2 (r=0.17) |
| $BA_e$ | 0.009 | Negligible | EP2>EP1 (r=0.17); EP3>EP1 (r=0.16) |
| $\partial K_z/\partial t$ | 0.005 | Negligible | EP1>EP3 (r=0.09); EP2>EP3 (r=0.08) |

Note: pairwise r values shown as absolute magnitude; direction stated explicitly in
"direction" column of step7b_pairwise_table.csv.

**Physical summary of LEC inter-EP differences:**

- **Eddy energy terms dominate** ($A_e$, $K_e$, $C_e$, $C_a$, ε² = 0.28–0.40):
  these are the primary EP discriminators, consistent with the EP classification
  being grounded in the eddy PCA component.
- **EP3 has dramatically lower eddy kinetic energy and baroclinic conversion** than
  EP1 and EP2 (large r values for EP1>EP3 and EP2>EP3 for $K_e$, $C_a$, $C_e$).
- **EP3 has distinctly higher barotropic conversion** ($C_k$; EP3>EP1, r=0.54),
  identifying EP3 as the barotropically dominated class.
- **$C_a$ does not differ between EP1 and EP2** (only 2/3 pairs significant):
  baroclinic conversion levels are similar in EP1 and EP2; EP3 is the outlier.
- **Canonical 7 terms** (Ca, Ck, BAe, BKe, Ae, Ke, Ge) all show significant
  inter-EP differences, validating the EP clustering.
- **$BA_e$ and $\partial K_z/\partial t$** have negligible ε² (< 0.01) despite
  statistical significance — these are large-sample artefacts; treat as
  indistinguishable across EPs for practical purposes.

### 5.5 Dynamic Field Features: Which Differ Between EPs

#### Top features by ε² (absolute; top 10)

| Feature | ε² | Effect class |
|---|---|---|
| `afc_250__domain_abs_mean` | **0.179** | Large |
| `pv_200__contrast_ew` | 0.132 | Medium |
| `ke_adv_250__domain_abs_mean` | 0.123 | Medium |
| `adv_T_850__sector_north` | 0.111 | Medium |
| `adv_T_850__sector_west` | 0.095 | Medium |
| `adv_T_850__border_north` | 0.094 | Medium |
| `adv_T_850__domain_mean` | 0.075 | Medium |
| `ke_adv_250__border_south` | 0.060 | Medium |
| `ke_adv_250__sector_west` | 0.048 | Small |
| `adv_T_850__domain_abs_mean` | 0.042 | Small |

#### Top features by ε² (anomaly; top 10)

| Feature | ε² | Effect class |
|---|---|---|
| `afc_250_anom_epall__domain_abs_mean` | **0.166** | Large |
| `pv_200_anom_epall__contrast_ew` | 0.132 | Medium |
| `ke_adv_250_anom_epall__domain_abs_mean` | 0.114 | Medium |
| `adv_T_850_anom_epall__sector_north` | 0.111 | Medium |
| `adv_T_850_anom_epall__sector_west` | 0.095 | Medium |
| `adv_T_850_anom_epall__border_north` | 0.094 | Medium |
| `adv_T_850_anom_epall__domain_mean` | 0.075 | Medium |
| `ke_adv_250_anom_epall__border_south` | 0.060 | Medium |
| `ke_adv_250_anom_epall__sector_west` | 0.048 | Small |
| `adv_T_850_anom_epall__contrast_sn` | 0.040 | Small |

#### Features NOT significantly different between EPs (after BH-FDR)

| Feature | ε² | Interpretation |
|---|---|---|
| `pv_200__domain_mean` | 0.001 | Overall PV 200 level does not differ between EPs |
| `pv_200__centre_value` | 0.000 | Centre-point PV 200: no EP signal |
| `pv_200__sector_north` | 0.001 | PV 200 northern sector: no EP signal |
| `pv_200__domain_abs_mean` | 0.001 | PV 200 absolute mean: no EP signal |
| `ke_adv_250__border_north` | 0.001 | Northern border KE advection: no EP signal |
| `ke_adv_250__sector_north` | 0.000 | KE adv northern sector: no EP signal |

Key finding: the **PV 200 hPa domain mean**, **centre value**, and **sector_north** do
not differ between EPs.  What matters for PV 200 is the *zonal gradient* (east–west
contrast, ε² = 0.132), not the domain-wide intensity level or the northern sector.

**Physical summary:**

- **AFC 250 hPa amplitude** (`domain_abs_mean`) is the single strongest EP discriminator
  among field features (ε² = 0.179), consistent with composite analysis showing
  markedly different AFC patterns per EP.
- **PV 200 hPa E–W contrast** (ε² = 0.132) reflects the east–west phase tilt of the
  upper-level trough relative to the surface cyclone.
- **KE advection amplitude at 250 hPa** captures jet-stream energy transport structure.
- **Temperature advection in the northern sector** (ε² = 0.111) and **western sector**
  (ε² = 0.095) capture warm advection ahead of the cold front and the warm conveyor
  belt structure — classical baroclinic signatures.  The cardinal sector formulation
  replaced the diagonal quadrant formulation (2026-04-22 rerun).
- Anomaly features produce slightly lower effect sizes than absolute features on average,
  except for `pv_200__contrast_ew` which is identical — the zonal PV contrast is
  entirely captured by the deviation from the EPALL mean.

---

## 6. LEC–Field Association Analysis

### 6.1 Status

Steps 7 and 8 (PREDEP + Spearman association analysis) were rerun on **2026-04-22**
with the canonical central-timestep LEC method and updated sector features.  Results
below supersede the preliminary full-phase run.

### 6.2 Preliminary Top Associations (Full-Phase Run — SUPERSEDED)

> These results used the now-removed full-phase LEC averaging.  They are retained to
> guide expectations for the rerun.

| EP | LEC term | Field | Feature | PREDEP α | Type |
|----|----------|-------|---------|----------|------|
| EP3 | $G_e$ | AFC 250 anom | `contrast_sn` | **0.721** | anomaly |
| EP3 | $A_e$ | AFC 250 anom | `contrast_sn` | 0.718 | anomaly |
| EP3 | $BA_e$ | AFC 250 anom | `contrast_sn` | 0.716 | anomaly |
| EP3 | $BK_e$ | AFC 250 anom | `contrast_sn` | 0.715 | anomaly |
| EP3 | $C_k$ | AFC 250 anom | `contrast_sn` | 0.714 | anomaly |
| EP3 | $K_e$ | AFC 250 anom | `contrast_sn` | 0.711 | anomaly |
| EP3 | $C_a$ | AFC 250 anom | `contrast_sn` | 0.704 | anomaly |
| EP1 | $G_e$ | PV 200 | `quadrant_ne` | 0.699 | absolute |

**Key preliminary finding (EP3)**: The S–N contrast of the AFC anomaly at 250 hPa
dominates the PREDEP ranking for all 7 canonical LEC terms in EP3, suggesting that
meridional asymmetry of upper-level ageostrophic flux is a *synoptic organiser* for
EP3 energetics — a single feature encodes the full energetic signature.

**Key preliminary finding (EP1)**: Upper-level tropopause structure (PV 200 NE quadrant)
is the leading predictor for diabatic APE generation, consistent with the EP1 composite
showing a cut-off low or upper-level trough.

**Note on a persistent PREDEP floor (~0.40)**: Observed in the preliminary run for
nearly all variable pairs.  Likely reflects (a) the temporal mismatch (now resolved)
and (b) genuine climatological co-variation of structure and energetics.  The
central-timestep rerun should reduce this floor.

---

## 7. Interpretation Guide for Pipeline Figures

### 7.1 Label Convention

All figure labels for dynamic features follow: **Field Label — Feature Label**

| Field Label | Meaning |
|---|---|
| PV 850 | Potential vorticity at 850 hPa (absolute) |
| PV 200 | Potential vorticity at 200 hPa (absolute) |
| AdvT 850 | Temperature advection at 850 hPa (absolute) |
| AFC 250 | Ageostrophic flux convergence at 250 hPa (absolute) |
| KE adv 250 | Kinetic energy advection at 250 hPa (absolute) |
| …anom | EPALL-relative anomaly version of above |

| Feature Label | Meaning |
|---|---|
| domain mean | Spatial mean over the inner domain |
| centre value | Value at the cyclone centre pixel |
| border N/S/E/W | Mean along the border strip |
| E–W contrast | border_east − border_west |
| S–N contrast | border_south − border_north |
| sector N/S/E/W | Cardinal sector mean (half-box in each direction) |
| domain \|mean\| | Mean absolute value |

### 7.2 Figure Family Reference

#### Significance heatmap (`significance_heatmap_*.png`)

Binary (red/grey) matrix — rows = variables, columns = EP pair contrasts.
Red = statistically significant at p_adj < 0.05; grey = not significant.
- Full-red row: variable distinguishes all EP pairs.
- Full-red column: that EP pair differs in many variables.
- **Always cross-reference with the effect size heatmap.**

#### Effect size heatmap (`effect_size_heatmap_*.png`)

Discrete colour heatmap of |rank-biserial r| (pairwise), sorted by variable name.
Non-significant cells annotated "ns"; significant cells framed with black border.

**Discrete colour convention** (applies to both standard and `_discrete.png` variants):

| Colour | |r| range | Practical interpretation |
|---|---|---|
| Grey | < 0.10 | Negligible — can be ignored |
| Light yellow | 0.10–0.20 | Small |
| Yellow | 0.20–0.30 | Small–moderate |
| Yellow-orange | 0.30–0.40 | Moderate |
| Amber | 0.40–0.50 | Moderate |
| Orange | 0.50–0.60 | Large |
| Deep orange | 0.60–0.70 | Large |
| Orange-red | 0.70–0.80 | Very large |
| Red-orange | 0.80–0.90 | Very large |
| Red | ≥ 0.90 | Extreme |

New discrete variant files (generated `step8b_effect_heatmap_discrete.py`, 2026-04-22):
- `effect_size_heatmap_*_discrete.png` — pairwise |r| with legend
- `effect_size_global_*_discrete.png` — global ε² per variable

#### Effect ranking (`effect_ranking_*.png`)

Top 20 variables sorted by global ε² (Kruskal–Wallis).  Red = significant.
This is the **single most informative figure** for identifying which features matter.

#### Volcano plot (`volcano_*.png`)

Effect size (x) vs −log₁₀(p_adj) (y).  Top-right = high-confidence findings.
Points above the dashed line are significant (p_adj < 0.05).

#### PREDEP heatmap (step 8)

α values for each EP × LEC × field–feature combination.
- Discrete scale: grey < 0.10, light red → dark red (bins at 0.10, 0.30, 0.50, 0.70, 0.90).
- Primary reading: dark rows (predictable LEC terms) and dark columns (informative features).

#### Spearman / Pearson heatmaps (`diagnostics/correlation_heatmaps/`)

Same matrix structure as PREDEP heatmaps.  Primary starting point for association
analysis: scan for dark cells, compare Spearman vs Pearson agreement, compare across EPs.

### 7.3 Recommended Reading Order

1. **Effect ranking** (step 8b) — which features/terms have the largest inter-EP effect?
2. **Volcano plot** — confirm which are also statistically significant
3. **Spearman heatmaps** — identify strongest LEC–field associations and their direction
4. **PREDEP heatmap** — cross-check for non-monotonic structure
5. **Top associations bar chart** (step 8) — synthetic PREDEP ranking
6. **Physical plausibility** — are the leading results mechanistically grounded?

### 7.4 Statistical vs. Physical Significance

A p-value < 0.05 is a *necessary*, not *sufficient*, condition for scientific relevance.

1. **Effect size first.** Variables with ε² < 0.01 (BA_e, ∂Kz/∂t) are practically
   negligible regardless of p-value.
2. **Global test before pairwise.** Post-hoc contrasts are only interpretable if the
   global KW test is also significant.
3. **FDR-adjusted p for discovery claims.** Use `global_p_adjusted` from the diagnostic
   table when claiming EP differences.
4. **Physical mechanism must be plausible.** A significant Ca difference between EP1
   and EP3 is scientifically meaningful; a significant edge-feature difference in a
   weakly-forced field may be noise even at p < 0.05.
5. **Consistency across metrics.** Variables that are both significantly different between
   EPs (step 7b) AND show high Spearman ρ within an EP are the strongest candidates for
   physical interpretation.

---

## 8. Assumptions

1. **Central-timestep representativeness**: 2–3 central intensification timesteps
   represent the mature cyclone structure.  Shared with `ep_structure_analysis`.

2. **Temporal alignment**: LEC means and ERA5 fields are extracted from the same
   central timesteps.  The former mismatch (full-phase LEC vs single ERA5 snapshot) was
   removed.

3. **Storm-centred domain adequacy**: 30°×30° domain captures synoptic-scale structure
   relevant to the LEC.  Nearby system contamination is possible for some cases.

4. **EP label independence (within-EP analysis)**: The EP label is derived from the
   same LEC values being analysed, creating a group-level circularity.  Within-EP
   analyses (PREDEP, Spearman) are not affected: they use EP only as a stratification,
   not as a predictor.

5. **PREDEP estimator validity**: Bootstrap estimator requires adequate n.  EP1 (332)
   is marginal; EP2 (776) and EP3 (1,625) are adequate.

---

## 9. Caveats and Limitations

### 9.1 Statistical Caveats

1. **Large-sample Shapiro–Wilk over-rejection**: 100% of variables took the
   non-parametric path because Shapiro–Wilk rejected normality for every group.
   At n = 332–1,625 this is expected even for nearly Gaussian distributions.
   The KW + Dunn path is conservative but may miss distributional subtleties.

2. **Unbalanced groups** (EP1:EP2:EP3 ≈ 1:2:5): rank-based tests handle this
   gracefully; pairwise contrasts involving EP1 have wider confidence intervals.

3. **Multiple testing exposure**: 154 global tests + ~462 pairwise tests.  BH-FDR and
   Holm corrections are applied.  Variables with ε² < 0.01 that survive correction
   likely reflect genuine but practically negligible signal.

4. **Correlated test variables**: features from the same field are correlated.
   FDR correction under positive correlation is still valid (BH under PRDS is
   conservative), but number of "discoveries" is reduced.

5. **No post-hoc for non-significant global test**: if a variable's global KW p ≥ 0.05,
   no pairwise contrasts are computed (even if some pairs might differ).

### 9.2 Methodological Risks

- **PREDEP threshold floor**: persistent floor (~0.40) in preliminary run needs quantification
  with the new central-timestep rerun results now available.
- **Ward linkage bin choice for PREDEP**: may be sub-optimal for multimodal LEC
  distributions.
- **Fixed PREDEP bin count** $k = \lfloor\sqrt{N}\rfloor$: over-resolves for EP3; may
  under-resolve for EP1.

---

## 10. Next Steps

### Priority 1 — Pipeline consistency (near-term)

- [x] **Rerun step 4 with updated sector features** — completed 2026-04-22.  Steps 5–9
  also rerun.  All results now use cardinal sector features.

- [x] **Regenerate step 8b standard figures** with discrete colour scale — completed
  2026-04-22.

### Priority 2 — Full association rerun

- [x] **Rerun steps 7 + 8** (PREDEP + Spearman) with central-timestep LEC — completed
  2026-04-22.  Results supersede the full-phase preliminary run.

- [x] **Update Section 6 status** — updated 2026-04-22 to reflect completed rerun.

### Priority 3 — Analysis extensions

- [ ] **Validate physical coherence**: cross-check top associations with EP composites
  from `ep_structure_analysis`.
- [ ] **Quantify PREDEP floor change** between full-phase and central-timestep methods.
- [ ] PREDEP bootstrap confidence intervals.
- [ ] Reverse direction: $\alpha_{\text{feature}|\text{LEC}}$.
- [ ] Conditional PREDEP controlling for cyclone latitude/longitude.
- [ ] Additional fields: EGR, moisture flux divergence, SLP Laplacian.

---

## 11. References

- Assunção, R., Figueiredo, F., et al. (2025). An Interpretable Measure for Quantifying
  Predictive Dependence between Continuous Random Variables. *arXiv:2501.10815v1.*
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate.
  *JRSS-B*, 57(1), 289–300.
- Benjamini, Y., & Yekutieli, D. (2001). The control of the FDR in multiple testing
  under dependency. *Annals of Statistics*, 29(4), 1165–1188.
- Dunn, O. J. (1964). Multiple comparisons using rank sums. *Technometrics*, 6(3),
  241–252.
- Orlanski, I., & Katzfey, J. (1991). The life cycle of a cyclone wave in the Southern
  Hemisphere. *J. Atmos. Sci.*, 48(17), 1972–1998.
- Razali, N. M., & Wah, Y. B. (2011). Power comparisons of Shapiro-Wilk,
  Kolmogorov-Smirnov, Lilliefors and Anderson-Darling tests. *JOSMA*, 2(1), 21–33.
- Ruxton, G. D., & Beauchamp, G. (2008). Time for some a priori thinking about post hoc
  testing. *Behavioral Ecology*, 19(3), 690–693.
- Welch, B. L. (1951). On the comparison of several mean values: an alternative
  approach. *Biometrika*, 38(3/4), 330–336.
- Couto de Souza, D. (2024). *PhD Thesis — Cyclone Energetics in the South Atlantic*
  (Chapter 6). IAG-USP.

---

## Appendix A: Decision Flowchart

```mermaid
flowchart TD
    A([Variable: split by EP1 / EP2 / EP3]) --> B{Any n_i < 8\nor zero variance?}
    B -- Yes --> SKIP([SKIPPED])

    B -- No --> C[Shapiro-Wilk per group\nα = 0.05  ·  subsample if n > 5000]
    C --> D{all_normal?}

    D -- Yes --> E[Brown-Forsythe Levene\ncenter='median']
    E --> F{equal_var?}

    F -- Yes --> G[One-way ANOVA\nF  ·  ω²]
    F -- No  --> H[Welch ANOVA\ncustom F*  ·  ω²]

    D -- No --> I[Kruskal-Wallis\nH  ·  ε²]

    G --> J{p < 0.05?}
    H --> J
    I --> J

    J -- No  --> K([Record effect; no post-hoc])
    J -- Yes --> L{Which path?}

    L -- ANOVA   --> M[Tukey HSD · Cohen d]
    L -- Welch   --> N[Welch t pairwise · Holm · Cohen d]
    L -- Kruskal --> O[Dunn 1964 · Holm · rank-biserial r]

    M & N & O --> P([Record results])
    P --> Q([BH-FDR across all variables in block])
```

> **Empirically**: all 154 variables in the April 2026 run took the
> **Kruskal–Wallis → Dunn (Holm)** path.  ANOVA branches never activated.

---

## Appendix B: Algorithmic Pseudocode

```
CONSTANTS:
  ALPHA = 0.05;  MIN_SAMPLE_SIZE = 8;  SHAPIRO_MAX_N = 5000

FOR each block IN [lec_terms, absolute_features, anomaly_features]:
  FOR each variable IN block:

    groups = split by EP; remove NaN/inf; record n_i
    IF any n_i < 8 OR zero variance: SKIP; continue

    FOR each group:
        IF n_i > 5000: subsample 5000 (seed=42)
        SW_stat, SW_p = shapiro(group)
        is_normal = (SW_p > 0.05)

    all_normal = all(is_normal)

    IF all_normal:
        levene_stat, levene_p = levene(*groups, center='median')
        equal_var = (levene_p > 0.05)

    IF all_normal AND equal_var:
        test = f_oneway(*groups)           # ANOVA
        effect = omega_squared(groups)     # ω²

    ELIF all_normal AND NOT equal_var:
        test = welch_anova(groups)         # custom
        effect = omega_squared(groups)     # ω²

    ELSE:  # ← empirically: always this branch
        test = kruskal(*groups)            # KW
        effect = (H - k + 1) / (N - k)    # ε²

    IF test.p < 0.05:
        IF ANOVA:   pairwise = tukey_hsd(*groups); pairwise_effect = cohen_d
        IF Welch:   pairwise = [ttest_ind(g_i,g_j,equal_var=False) …]; Holm; Cohen d
        IF KW:      # Dunn (1964):
                    rank all N jointly
                    z_ij = (R̄_i − R̄_j) / σ_ij  [tie-corrected]
                    p_raw = 2×norm.sf(|z_ij|)
                    r_rb = 1 − 2U/(n_i×n_j)      # rank-biserial r
                    p_adj = holm(p_raw)

    store diagnostic & pairwise rows

  global_p_adjusted = benjamini_hochberg(raw_p_global)  # across block
```
