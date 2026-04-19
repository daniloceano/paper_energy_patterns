# SCIENTIFIC NOTES — LEC–Field Dependence Analysis

---

## Research Questions

1. **How much do the spatial features of the atmospheric dynamical fields predict the energetic behaviour of individual South Atlantic extratropical cyclones?**

2. **Does the predictive relationship between dynamical structure and energetics differ across Energy Patterns (EP1, EP2, EP3)?**

3. **Are there specific spatial features (e.g., zonal contrast, southern border mean) of specific fields (e.g., PV at 200 hPa, AFC at 250 hPa) that are particularly informative about specific LEC terms (e.g., baroclinic conversion Ca, barotropic conversion Ck)?**

4. **Does the use of EPALL-relative anomaly fields (isolating EP-specific structure) lead to stronger or weaker predictive associations compared to absolute fields?**

5. **For each scalar variable (LEC term or dynamic feature), do EP1, EP2, and EP3 differ significantly?  Which pairs differ, and how large is the effect?**

---

## Physical / Statistical Framework

### Motivation

The Energy Pattern classification (EP1, EP2, EP3) was derived from PCA-based K-Means clustering on Lorenz Energy Cycle diagnostics during the intensification phase of South Atlantic extratropical cyclones. The subsequent composite analysis (ep_structure_analysis) revealed distinct atmospheric structures for each EP using ERA5 fields.

However, the composite analysis operates on **group means** — it shows what the "average" EP1, EP2, or EP3 cyclone looks like, but does not capture the **individual-level relationship** between a cyclone's energetics and its atmospheric structure. This analysis bridges that gap.

### PREDEP as the Primary Measure

We adopt the PREDEP measure (Assunção et al. 2025, arXiv:2501.10815) as the primary association metric. PREDEP is a fully non-parametric measure of predictive dependence between continuous random variables.

**Formal definition:**

$$\alpha_{Y|X} = \frac{S_{Y|X} - S_Y}{S_{Y|X}}$$

where:
- $S_Y = \mathbb{E}[f_Y(Y)] = \int f_Y^2(y)\,dy$ is the marginal prediction rate (linked to the quadratic Rényi entropy)
- $S_{Y|X} = \mathbb{E}_X[\mathbb{E}_{Y|X} f_{Y|X}(Y|X)]$ is the conditional prediction rate
- $\alpha \in [0, 1]$
- $\alpha = 0 \iff X \perp Y$ (independence)
- $\alpha = 1$ means Y is perfectly predictable from X

**Direction convention in this analysis:**

The primary direction is:

$$\alpha_{\text{LEC term} | \text{feature}} \quad \text{where} \quad X = \text{feature},\; Y = \text{LEC term}$$

This answers: *"by what fraction does knowing the dynamic feature reduce the prediction loss of the LEC term?"*

For example, $\alpha_{Ca | \text{domain\_mean(PV\_200)}} = 0.35$ means that knowing the domain-mean PV at 200 hPa reduces the prediction error of baroclinic conversion ($C_a$) by 35%.

**PREDEP is asymmetric:** $\alpha_{Y|X} \neq \alpha_{X|Y}$ in general. This is a feature, not a bug — it correctly reflects that predicting Y from X is not the same as predicting X from Y.

### Why Not Pearson or Spearman Alone?

Pearson measures linear association; Spearman measures monotonic association. Neither captures:
- Non-functional dependencies (e.g., cyclones where both very high and very low PV are associated with similar energetics)
- Complex non-linear relationships common in atmospheric dynamics
- The prediction-loss interpretation that PREDEP provides

Pearson and Spearman are computed as **baseline comparisons only**.

---

## Datasets and Variables

### LEC Terms

Source: LEC results from Zenodo (DOI: 10.5281/zenodo.18243447), 3-hourly time series with 32 vertical levels.

For this analysis, we use the **intensification-phase mean** of each term:

| Term | Description | Units |
|------|-------------|-------|
| $A_z$ | Zonal available potential energy | W m⁻² |
| $A_e$ | Eddy available potential energy | W m⁻² |
| $K_z$ | Zonal kinetic energy | W m⁻² |
| $K_e$ | Eddy kinetic energy | W m⁻² |
| $C_z$ | Zonal APE → Zonal KE conversion | W m⁻² |
| $C_a$ | Zonal APE → Eddy APE conversion (baroclinic) | W m⁻² |
| $C_k$ | Eddy KE → Zonal KE conversion (barotropic) | W m⁻² |
| $C_e$ | Eddy APE → Eddy KE conversion | W m⁻² |
| $BA_z, BA_e$ | Boundary APE fluxes (zonal, eddy) | W m⁻² |
| $BK_z, BK_e$ | Boundary KE fluxes (zonal, eddy) | W m⁻² |
| $B\Phi_Z, B\Phi_E$ | Boundary pressure work fluxes | W m⁻² |
| $G_z, G_e$ | Generation of APE (zonal, eddy) | W m⁻² |
| Residuals | $RG_z, RK_z, RG_e, RK_e$ | W m⁻² |
| Tendencies | $\partial A_z/\partial t$, $\partial A_e/\partial t$, $\partial K_z/\partial t$, $\partial K_e/\partial t$ | W m⁻² |

All 24 terms are loaded.  Two term sets are used in the analysis:

- **Canonical 7 terms** (`LEC_TERMS_CORE`): `Ca`, `Ck`, `BAe`, `BKe`, `Ae`, `Ke`, `Ge` — the exact set used in the PCA-based K-Means EP classification.  These are the primary analysis terms (figures in `figures/lec_field_dependence/canonical/`).
- **All 24 terms** (exploratory): used for completeness and internal validation (`figures/lec_field_dependence/all/`).

**Note on term alignment**: `Ce`, `Cz`, `Gz` were present in `LEC_TERMS_CORE` in an earlier version of the pipeline but were never part of the clustering step.  They have been removed from `LEC_TERMS_CORE` (corrected 2025-04-19) to ensure canonical analysis is consistent with the EP classification.

### Dynamic Fields

Source: ERA5 reanalysis, 0.25° resolution, storm-centred 30°×30° domain.

| Field | Variable | Level | Physical Meaning |
|-------|----------|-------|-----------------|
| PV (low-level) | `pv_850` | 850 hPa | Diabatic PV anomaly, low-level forcing |
| PV (upper-level) | `pv_200` | 200 hPa | Tropopause dynamics, upper-level forcing |
| Temperature advection | `adv_T_850` | 850 hPa | Warm/cold advection structure |
| AFC | `afc_250` | 250 hPa | Ageostrophic flux convergence (eddy KE redistribution) |
| KE advection | `ke_adv_250` | 250 hPa | Jet-level kinetic energy tendency |

**Derivation (step 3b):** The raw per-cyclone ERA5 files contain instantaneous pressure-level fields (`u`, `v`, `t`, `z`, `q`) downloaded from the CDS API. The dynamic diagnostics listed above are NOT present in the raw files. They are computed in pipeline **step 3b** (`step3b_derive_era5_fields.py`) using the validated diagnostic functions from `scripts/ep_structure_analysis/step3_precompute_composites.py`, ensuring methodological consistency between this analysis and the ep_structure composites. Derived fields are saved to `{derived_dir}/{track_id}_era5_derived.nc` (raw files are never modified). Steps 4 and 5 read exclusively from the derived files.

Diagnostic formulas (consistent with ep_structure_analysis):

- **PV at 850/200 hPa**: Ertel potential vorticity $q = -g\left(\frac{\partial\theta}{\partial p}\right)\zeta_a$ computed via MetPy using 3-level centred finite differences on `h-1`, `h`, `h+1` pressure levels.
- **Temperature advection at 850 hPa**: $-\mathbf{V} \cdot \nabla T$ via MetPy advection with spherical-geometry gradients.
- **KE advection at 250 hPa**: $-\mathbf{V} \cdot \nabla\left(\frac{1}{2}|\mathbf{V}|^2\right)$ via MetPy advection.
- **AFC at 250 hPa**: Ageostrophic flux convergence following Orlanski & Katzfey (1991): $-\nabla \cdot (\mathbf{V}_a K)$ where $\mathbf{V}_a$ is the ageostrophic wind and $K$ is kinetic energy anomaly relative to the ERA5 climatological mean at 250 hPa.

Two versions of each field:
1. **Absolute**: the field as derived for the cyclone
2. **EPALL-relative anomaly**: cyclone field − EPALL composite mean (isolates what is distinctive about each cyclone relative to the average cyclone)

### Temporal Representation

Two LEC temporal windows are available (produced by `step2_build_lec_table.py --temporal-window`):

| Window | Flag | Output file | Description |
|--------|------|-------------|-------------|
| **Full phase** | `full` (default) | `step2_lec_intensification_means.csv` | Mean over all 3-hourly timesteps in the intensification phase (~14 timesteps, ~42h) |
| **Central window** | `central` | `step2_lec_central_means.csv` | Mean over ±1 timestep around phase midpoint (3 timesteps = 9h window) |

**ERA5 fields**: single central timestep of the intensification phase (canonical ep_structure methodology; snapshot at cyclone mature stage).

**Temporal mismatch**: The full-phase LEC window includes early and late intensification, while the ERA5 snapshot captures only the mature stage.  The central-window option reduces this mismatch to 9h vs a single snapshot.  See Assumptions section for a quantified example.

---

## Methodology

### Feature Extraction

Each 2D storm-centred field is summarised into 13 scalar features computed on the inner 15°×15° box centred on the cyclone:

| Feature | Definition |
|---------|-----------|
| domain_mean | $\bar{f} = \frac{1}{N}\sum_i f_i$ (mean over inner box) |
| centre_value | $f(x_c, y_c)$ (value at cyclone centre) |
| border_north | Mean of northern 5-cell strip |
| border_south | Mean of southern 5-cell strip |
| border_east | Mean of eastern 5-cell strip |
| border_west | Mean of western 5-cell strip |
| contrast_ew | $\bar{f}_E - \bar{f}_W$ (zonal asymmetry) |
| contrast_sn | $\bar{f}_S - \bar{f}_N$ (meridional asymmetry) |
| quadrant_ne | Mean of NE quadrant |
| quadrant_nw | Mean of NW quadrant |
| quadrant_se | Mean of SE quadrant |
| quadrant_sw | Mean of SW quadrant |
| domain_abs_mean | $\frac{1}{N}\sum_i |f_i|$ (mean absolute value) |

**Rationale for feature choices:**

- `domain_mean`: overall field intensity in the cyclone vicinity
- `centre_value`: field intensity at the cyclone core
- Border means: spatial structure on each side of the cyclone
- Contrasts: capture baroclinic tilt (E-W) and frontal structure (S-N)
- Quadrant means: resolve the four-quadrant structure relevant to cyclone dynamics
- `domain_abs_mean`: important for signed fields where cancellation masks the intensity

**Notes on potential redundancy:**
- `domain_mean` and the mean of the four quadrants are mathematically related
- If quadrant means are all very similar, contrasts will be near zero — this is informative, not redundant
- `domain_abs_mean` adds value mainly for temperature advection and AFC where sign patterns are physically meaningful

### PREDEP Estimation

Following the bootstrap estimator in Assunção et al. (2025):

1. $S_Y$ is estimated via the convolution-density-at-zero trick: $S_Y = \hat{f}_W(0)$ where $W = Y_1 - Y_2$
2. $S_{Y|X}$ uses hierarchical clustering (Ward linkage) on X to define bins, then applies the same bootstrap within each bin
3. Number of bins: $k = \lfloor\sqrt{N}\rfloor$
4. Number of bootstrap pairs: $n_b = \lceil N \log N \rceil$
5. KDE bandwidth: Scott's rule

### Analysis Structure

For each **EP × LEC term × field × feature** combination:
1. Select the EP subsample
2. Extract x = feature values, y = LEC term values
3. Remove paired NaN
4. Check minimum sample size (N ≥ 30)
5. Compute PREDEP α_{Y|X}
6. Compute Pearson r and Spearman ρ as baselines

Total combinations: 3 EPs × ~24 LEC terms × 5 fields × 13 features × 2 field types = **~9,360 PREDEP estimates**

### Inter-EP Statistical Significance Testing (Step 7b)

Independently from the PREDEP analysis, every scalar variable in the pipeline is tested for statistically significant differences between EP1, EP2, and EP3.  This concerns both the LEC terms themselves and each derived dynamic feature.

#### Rationale

The PREDEP analysis answers *"how much does a dynamic feature predict an LEC term within an EP?"*.  The significance analysis answers a complementary question: *"do EP1, EP2, and EP3 actually differ on this variable?"*.  A variable for which EPs do not differ is unlikely to be useful for discriminating energetic patterns, regardless of its PREDEP value.

#### Decision Tree

For each variable separately:

1. **Data preparation**
   - Split values by EP (EP1, EP2, EP3) — three independent groups.
   - Remove NaN / non-finite values.
   - Record per-group $n$.
   - Check degeneracy: skip if any group has $n < 8$ or zero variance.

2. **Normality assessment** — Shapiro-Wilk test per group ($\alpha = 0.05$).
   - For $n > 5000$, a random subsample of 5000 is used.  The result is flagged: at large $n$, Shapiro-Wilk over-rejects and minor non-normality is detected even when practically irrelevant.  This is a known limitation (Razali & Wah 2011).
   - **Caveat**: with EP3 having $N \approx 1600$ and EP2 $\approx 770$, the test is appropriately sensitive but still powerful enough to reject for modest departures. Results are logged in an auditable table (Shapiro statistic and $p$-value per group).

3. **Homogeneity of variances** — Levene's test with `center='median'` (Brown-Forsythe variant), which is more robust to non-normality than the mean-based version.

4. **Global test selection**:

   | Condition | Test | Justification |
   |-----------|------|---------------|
   | All groups normal + equal variances | **One-way ANOVA** | Classical F-test; assumptions met |
   | All groups normal + unequal variances | **Welch ANOVA** (Welch 1951) | Does not assume equal variances; uses weight $w_i = n_i / s_i^2$ |
   | At least one group non-normal | **Kruskal-Wallis** | Rank-based; no distributional assumption |

   The Welch ANOVA is implemented from scratch (see `utils_statistical_tests.py`) as `pingouin` is not available in the environment.

5. **Post-hoc pairwise tests** (only if global test is significant):

   | After | Post-hoc | Correction | Notes |
   |-------|----------|------------|-------|
   | One-way ANOVA | **Tukey HSD** | Inherent FWER control | `scipy.stats.tukey_hsd` |
   | Welch ANOVA | **Pairwise Welch t-tests** | Holm step-down | Used because Games-Howell requires `pingouin`.  Holm correction guarantees FWER ≤ $\alpha$. |
   | Kruskal-Wallis | **Dunn test** | Holm step-down | Implemented from Dunn (1964) with tie adjustment; `scikit_posthocs` not available. |

   **On Games-Howell**: The Games-Howell test is the canonical choice after Welch ANOVA in unbalanced designs.  It uses the Studentized Range distribution with Welch-Satterthwaite degrees of freedom.  In the absence of the `pingouin` library, pairwise Welch t-tests with Holm correction provide equivalent protection against Type I error and are widely accepted (e.g., Ruxton & Beauchamp 2008).

   **On Dunn's test**: Dunn (1964) is the standard non-parametric post-hoc for Kruskal-Wallis.  It compares mean ranks between pairs with a $z$-statistic:

   $$z_{ij} = \frac{\bar{R}_i - \bar{R}_j}{\sigma_{ij}} \quad \text{where} \quad \sigma_{ij} = \sqrt{\left[\frac{N(N+1)}{12} - \frac{\sum_t (t^3 - t)}{12(N-1)}\right] \left(\frac{1}{n_i} + \frac{1}{n_j}\right)}$$

   and the tie-correction term accounts for rank ties.

6. **Multiple comparison correction** — applied at two levels:

   a. **Within-variable pairwise**: Holm step-down (applied inside Welch t-test and Dunn procedures).  Tukey HSD controls FWER internally.

   b. **Across all variables**: Benjamini-Hochberg FDR correction applied to the global test $p$-values across all variables tested.  This is the recommended approach when testing dozens to hundreds of variables in an exploratory setting (Benjamini & Hochberg 1995).  Holm correction is available as a more conservative alternative.

7. **Effect size** — reported alongside every $p$-value to prevent over-reliance on statistical significance:

   | Context | Measure | Interpretation |
   |---------|---------|----------------|
   | ANOVA / Welch ANOVA (global) | $\omega^2$ | Less biased than $\eta^2$; proportion of variance explained.  Small: 0.01, Medium: 0.06, Large: 0.14 |
   | Kruskal-Wallis (global) | $\varepsilon^2 = (H - k + 1)/(N - k)$ | Non-parametric analogue; same interpretation thresholds as $\omega^2$ |
   | Parametric pairwise | Cohen's $d$ | Standardised mean difference.  Small: 0.20, Medium: 0.50, Large: 0.80 |
   | Non-parametric pairwise | Rank-biserial $r$ | $r = 1 - 2U/(n_1 n_2)$ from Mann-Whitney $U$.  Small: 0.10, Medium: 0.30, Large: 0.50 |

#### Interpretation Guidance

- **Do not interpret based solely on $p < 0.05$.**  At these sample sizes ($N \approx 330$ to 1600), even trivially small differences can be statistically significant.
- **Effect size is the primary interpretive quantity.**  A variable with $\omega^2 < 0.01$ is negligible regardless of $p$.
- **Use the decision tree as an audit trail**, not as a binary verdict.  The full diagnostic table logs normality results, test choices, and effect sizes for every variable.
- **Physical consistency matters.**  A statistically significant difference in $C_a$ between EP1 and EP3 is scientifically meaningful because $C_a$ is the dominant baroclinic conversion.  A significant difference in a boundary flux residual may be a statistical artefact.

#### Known Limitations of the Significance Analysis

1. **Large-sample over-rejection**: Shapiro-Wilk rejects normality for practically normal distributions when $N > 500$.  The non-parametric path (Kruskal-Wallis → Dunn) is conservative but may miss subtleties that ANOVA captures better via CLT robustness.

2. **Balanced-design assumption**: Tukey HSD assumes balanced groups.  With EP1 ($\approx$330), EP2 ($\approx$770), EP3 ($\approx$1600), designs are unbalanced by a factor of ~5.  Welch-based corrections and rank tests partly address this but interpretation should note the imbalance.

3. **Global FDR correction**: With ~150+ variables tested, the FDR correction reduces the number of discoveries.  Variables that are significant at raw $p < 0.05$ but not after FDR correction should be flagged as *suggestive but unconfirmed*.

4. **Independence assumption**: Variables (especially derived features from the same field) are correlated.  FDR correction treats them as independent tests, which is conservative in the presence of positive dependence (Benjamini & Yekutieli 2001 show FDR still controls at $q$ level under positive regression dependency).

---

## Assumptions

1. **Phase-mean LEC representativeness**: The intensification-phase mean captures the dominant energetic behaviour. Sub-phase variability is averaged out.

2. **Central-timestep representativeness**: The 2–3 central timesteps of intensification represent the mature structure of the intensifying cyclone. This is the same assumption used in the ep_structure_analysis composite.

3. **Temporal mismatch (quantified)**: In the default configuration, the LEC term covers the **full** intensification phase (~42h), while the ERA5 field is from the **central** single timestep only.  This mismatch is large in practice.  Example — cyclone ID 19790001:
   - Full-phase mean $C_a$ = +0.28 W m⁻²
   - Central-window (±1 ts, 9h) mean $C_a$ = −0.35 W m⁻²
   The sign reversal indicates that early/late intensification dominates the full-phase mean for this cyclone.  **Mitigation**: the `--temporal-window central` option produces `step2_lec_central_means.csv` which averages LEC over the same 9h window around the midpoint, reducing the temporal mismatch.  The central-window PREDEP run (on the server) is needed to quantify whether this reduces or increases PREDEP values.  All current results use the **full-phase** mean (default).

4. **Storm-centred domain validity**: The 30°×30° domain adequately captures the synoptic-scale structure relevant to the energy budget. Some influence from neighbouring systems is possible.

5. **PREDEP estimation validity**: The bootstrap estimator requires sufficient sample size. EP1 (N ≈ 330) is marginal; EP2 (N ≈ 770) and EP3 (N ≈ 1600) are adequate.

6. **Feature independence from EP classification**: The LEC terms used to define EPs (via PCA-clustering) are also part of the PREDEP analysis. This creates a circularity where EP classification is not independent of the LEC values being analysed. However, the question is not "can we predict EP membership?" but "given that a cyclone is in EP1, how does its structure predict its specific energetics?" — the EP grouping serves only as a stratification.

---

## Caveats and Limitations

1. **Sample size for EP1**: ~330 cyclones is borderline for the bootstrap PREDEP estimator. Results for EP1 should be interpreted with wider uncertainty.

2. **Multiple testing**: With ~9,360 combinations, some high PREDEP values will arise by chance. No formal multiple-testing correction is applied in this exploratory phase. Top associations should be validated by physical reasoning.

3. **Feature simplicity**: The 13 scalar features are deliberately simple. More sophisticated features (gradients, wavelet decompositions, EOF coefficients) are deferred to a potential follow-up analysis.

4. **PREDEP is a global measure**: It captures the overall predictive dependence, not the functional form. Two combinations with identical PREDEP values may have very different underlying relationships.

5. **KDE sensitivity**: The bootstrap PREDEP estimator relies on kernel density estimation, which can be sensitive to outliers and bounded distributions. LEC terms with heavy-tailed distributions (e.g., boundary fluxes) may produce noisier estimates.

6. **No spatial autocorrelation correction**: Adjacent grid cells in the domain are correlated. The feature extraction (means, contrasts) partially mitigates this by aggregating, but does not fully account for spatial dependence.

7. **Composites vs individuals**: The EPALL composite used for anomaly computation is a group mean. Individual cyclone deviations from EPALL may include both EP-specific signal and inter-cyclone variability within EPALL.

8. **Statistical significance ≠ physical significance**: With N > 300 per group, many differences will be statistically significant even when the effect size is negligible.  All significance results should be interpreted jointly with effect size and physical reasoning.

9. **Correlated test variables**: Features derived from the same field (e.g., quadrant means and domain mean) are correlated.  The FDR correction assumes independence or positive dependence, which is satisfied here but reduces discovery power.

---

## Known Methodological Risks

- **Temporal mismatch (quantified risk)**: Full-phase LEC mean vs ERA5 central-snapshot can produce sign-reversal in individual LEC terms.  This inflates within-EP variance of LEC values, which biases PREDEP downward (attenuates the signal).  Estimated magnitude: ≥0.10 reduction in PREDEP for some Ca/Ck terms.  Mitigation: `--temporal-window central` rerun on server.
- The Ward linkage clustering used to define X-bins in PREDEP may be sub-optimal for some LEC term distributions that are multi-modal
- The fixed number of bins ($k = \sqrt{N}$) may under-resolve conditional densities for EP3 (large N) or over-resolve for EP1 (small N)
- If per-cyclone ERA5 fields have variable grid sizes (non-standard domain), the feature extraction functions assume 121×121 and will produce incorrect results
- **LEC terms `Ce`, `Cz`, `Gz`** were formerly included in the canonical set but are **not part of the EP clustering**.  Updated (2025-04-19): `LEC_TERMS_CORE` now matches the clustering set exactly (7 terms).  Results files with all 24 terms remain available in `all/` subdirectory.

---

## Results and Interpretation

### 2025-04-19 — First full pipeline run (full-phase LEC, absolute + anomaly fields)

**Run summary**: 2733 cyclones (EP1=330, EP2=768, EP3=1635), 65 ERA5 features, 24 LEC terms, absolute + anomaly field types.  Total PREDEP estimates: ~9,360.  Server runtime: ~2h 8m.

**General pattern**: Most PREDEP values fall in the 0.40–0.70 range.  A genuine floor exists around 0.40 for the full-phase LEC — consistent with the temporal mismatch (LEC full-phase mean vs ERA5 snapshot reduces correlation for all features).  Values below 0.10 are sparse.

**Top canonical associations (PREDEP > 0.70, canonical 7 terms):**

| EP | LEC term | Field | Feature | PREDEP | Field type |
|----|----------|-------|---------|--------|------------|
| EP3 | $G_e$ | `afc_250_anom_epall` | `contrast_sn` | **0.721** | anomaly |
| EP3 | $A_e$ | `afc_250_anom_epall` | `contrast_sn` | 0.718 | anomaly |
| EP3 | $BA_e$ | `afc_250_anom_epall` | `contrast_sn` | 0.716 | anomaly |
| EP3 | $BK_e$ | `afc_250_anom_epall` | `contrast_sn` | 0.715 | anomaly |
| EP3 | $C_k$ | `afc_250_anom_epall` | `contrast_sn` | 0.714 | anomaly |
| EP3 | $A_e$ | `afc_250` | `quadrant_sw` | 0.713 | absolute |
| EP3 | $K_e$ | `afc_250_anom_epall` | `contrast_sn` | 0.711 | anomaly |
| EP3 | $C_a$ | `afc_250_anom_epall` | `contrast_sn` | 0.704 | anomaly |
| EP1 | $G_e$ | `pv_200` | `quadrant_ne` | 0.699 | absolute |

**Physical interpretation (EP3)**:
- The S–N contrast of the AFC anomaly at 250 hPa ($\alpha_{Y|AFC_{\delta,SN}} \approx 0.71$ for all energy terms) identifies **meridional asymmetry of the upper-level ageostrophic flux** as the dominant predictor for EP3 energetics.  This is the energy-pattern class associated with the most barotropic structure and the strongest boundary KE fluxes.
- The consistent signal across all 7 canonical terms (Ae, BAe, BKe, Ca, Ck, Ge, Ke) for the same feature (AFC anomaly S–N contrast) suggests that upper-level AFC structure is a **synoptic organiser** for EP3 — a single structural feature predicts the entire energetic signature.
- The SW quadrant of absolute AFC also appears prominently, consistent with the EP3 composite showing a jet-streak downstream of the cyclone centre.

**Physical interpretation (EP1)**:
- PV at 200 hPa NE quadrant ($\alpha \approx 0.699$ for $G_e$) identifies upper-level tropopause structure northeast of the cyclone as informative for diabatic APE generation.  This is consistent with the EP1 composite showing a cut-off low or upper-level trough.

**Anomaly vs Absolute**: For EP3 top associations, EPALL-relative anomaly fields (`afc_250_anom_epall`) generally outperform absolute fields, suggesting that **deviation from the climatological extratropical cyclone structure** is more informative than the absolute field intensity.  For EP1, the absolute field performs comparably.

**[PRELIMINARY]** These results use the full-phase LEC mean (temporal mismatch present).  A rerun with `--temporal-window central` on the server will isolate the central-window effect.

---

## Next Steps

### Completed (as of 2025-04-19)
- [x] Steps 1–8 executed (full pipeline, full-phase LEC)
- [x] LEC_TERMS_CORE corrected to 7 matching terms
- [x] Figures regenerated with discrete PREDEP scale (grey <0.10, 5 red bins)
- [x] Two figure families: `canonical/` (7 terms) and `all/` (all terms)
- [x] `step2_lec_central_means.csv` generated locally (central-window LEC)
- [x] `step6_integrated_*_central.csv` generated locally

### Pending
1. **Run step7 on server with central-window LEC** — transfer `step6_integrated_*_central.csv` and run full step7; compare PREDEP distributions between full-phase and central-window outputs
2. **Assess PREDEP floor**: PREDEP~0.40 floor for full-phase LEC may reflect temporal mismatch.  Central-window rerun will test this hypothesis.
3. **Identify physically meaningful top associations** — current top results point to AFC anomaly S–N contrast for EP3.  Validate with ep_structure composites.
4. **Steps 9/10 (significance analysis and CK analysis)** — if applicable
5. **Consider extending to:**
   - PREDEP confidence intervals (bootstrap CI)
   - The reverse direction: $\alpha_{\text{feature}|\text{LEC}}$
   - Additional fields (EGR, moisture flux divergence, SLP)
   - Conditional PREDEP controlling for cyclone latitude/longitude

---

## References

- Assunção, R., Figueiredo, F., Tinoco Junior, F. N., de Sá-Freire, L. M., & Silva, F. (2025). An Interpretable Measure for Quantifying Predictive Dependence between Continuous Random Variables. arXiv:2501.10815v1.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. JRSS-B, 57(1), 289–300.
- Benjamini, Y., & Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under dependency. Annals of Statistics, 29(4), 1165–1188.
- Dunn, O. J. (1964). Multiple comparisons using rank sums. Technometrics, 6(3), 241–252.
- Goodman, L. A., & Kruskal, W. H. (1954). Measures of association for cross classifications. JASA, 49, 732–764.
- Razali, N. M., & Wah, Y. B. (2011). Power comparisons of Shapiro-Wilk, Kolmogorov-Smirnov, Lilliefors and Anderson-Darling tests. JOSMA, 2(1), 21–33.
- Rényi, A. (1961). On measures of information and entropy. Proc. 4th Berkeley Symp.
- Ruxton, G. D., & Beauchamp, G. (2008). Time for some a priori thinking about post hoc testing. Behavioral Ecology, 19(3), 690–693.
- Welch, B. L. (1951). On the comparison of several mean values: an alternative approach. Biometrika, 38(3/4), 330–336.
- Couto de Souza, D. (2024). PhD Thesis — Cyclone Energetics in the South Atlantic (Chapter 6).
