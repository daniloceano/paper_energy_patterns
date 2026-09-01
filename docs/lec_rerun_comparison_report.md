# Legacy vs corrected LEC climatology — technical report

**Author**: Danilo Couto de Souza · **Generated**: 2026-09-01 ·
**Reference article**: de Souza et al. (2025), *Clim. Dyn.*,
[10.1007/s00382-025-07918-y](https://doi.org/10.1007/s00382-025-07918-y)

**Preliminary — the rerun is still running.** 3,298 of 3,820 cyclones (86%) are validated COMPLETE; the remaining 522 are pending or failed. The numbers below are stable in structure but will shift slightly as the population completes.

## 1. What is compared

The rerun (`scripts/lec_climatology_rerun`) recomputes the semi-Lagrangian Lorenz
Energy Cycle with LorenzCycleToolKit 2.0.0, which corrected `Ca`, the fifth `Ck`
subterm, `BΦZ`, `BΦE`, vertical-level alignment, time tendencies and NaN handling.
Everything else is held fixed: the same cyclones, the same frozen lifecycle
windows, the same 3-hourly time steps, the same 15° × 15° moving box and the same
32-level (10–1000 hPa) control volume. Both sides are phase means over identical
windows, so every difference reported here is attributable to the equation and
numerical correction alone.

The legacy side is `data/energy_cache.parquet`, the article input. Re-aggregating
the archived Zenodo per-cyclone results for 10 random
cyclones reproduces that cache to a maximum relative difference of
1e-13, confirming the two sides are built
the same way.

Paired sample: **3,298 cyclones**,
13,345 cyclone-phase rows,
24 terms.

## 2. What changed and what did not

16 of the 24 terms are numerically unchanged
(relative change below 1%, Spearman ≈ 1, essentially no sign
changes): Az, Ae, Kz, Ke, Cz, Ce, Gz, Ge, BAz, BAe, BKz, BKe, ∂Az/∂t, ∂Ae/∂t, ∂Kz/∂t and ∂Ke/∂t. This includes all four energy reservoirs, both
generation terms, the four lateral boundary transports and all four budget
tendencies — the corrections did not touch them.

The 8 terms that did change are exactly those the toolkit correction
targets, plus the residuals that inherit them (see
`figures/lec_rerun_comparison/violin_conversion.png` and `violin_boundary.png`;
the energy, generation and budget figures show the two halves of each violin
overlying each other exactly):

| Term | Group | Median legacy | Median corrected | Median Δ | Relative change | Spearman | Sign changes |
|---|---|---:|---:|---:|---:|---:|---:|
| Ca | conversion | 0.49 | 1.49 | 0.99 | 2.10× | 0.97 | 5.3% |
| BΦE | boundary | 35.57 | -1.07 | -37.53 | 1.03× | -0.41 | 67.6% |
| BΦZ | boundary | 55.19 | 6.54 | -45.33 | 0.88× | 0.47 | 28.9% |
| RGe | residual | 1.27 | 0.19 | -0.99 | 0.56× | 0.76 | 20.7% |
| Ck | conversion | -1.78 | 0.04 | 1.78 | 0.55× | 0.89 | 21.1% |
| RGz | residual | -1.03 | 0.14 | 0.99 | 0.41× | 0.86 | 16.8% |
| RKe | residual | -5.14 | -3.21 | 1.78 | 0.31× | 0.98 | 7.7% |
| RKz | residual | 7.98 | 5.78 | -1.78 | 0.08× | 1.00 | 2.9% |


![Figure 1. Conversion terms, legacy (left half) versus corrected (right half) of each violin, by life-cycle phase. C_A shifts upward in every phase and C_K crosses zero.](../figures/lec_rerun_comparison/violin_conversion.png)

*Figure 1. Conversion terms, legacy (left half) versus corrected (right half) of each violin, by life-cycle phase. C_A shifts upward in every phase and C_K crosses zero.*


![Figure 2. Boundary transport terms. The four lateral fluxes are unchanged; the two pressure-work terms BΦZ and BΦE collapse.](../figures/lec_rerun_comparison/violin_boundary.png)

*Figure 2. Boundary transport terms. The four lateral fluxes are unchanged; the two pressure-work terms BΦZ and BΦE collapse.*


![Figure 3. Residual terms, which inherit the C_A and C_K corrections through the budget closure.](../figures/lec_rerun_comparison/violin_residual.png)

*Figure 3. Residual terms, which inherit the C_A and C_K corrections through the budget closure.*

The energy, generation and budget-tendency violins are not reproduced here: the
two halves of every violin coincide exactly. They are in
`figures/lec_rerun_comparison/` if a reader wants to confirm it.

*Relative change* is the median |Δ| divided by the median |legacy| value: 1.00×
means the typical change is as large as the term itself. *Spearman* is the
rank correlation between the two versions across cyclone-phases — the quantity
that matters for the downstream PCA and k-means, which depend on ordering.

Three features stand out:

- **`Ca` roughly triples** (median 0.49 →
  1.49 W m⁻²) but keeps its ranking
  (Spearman 0.97) and its sign in
  95% of cases. Baroclinic conversion
  is systematically stronger, not reordered.
- **`Ck` shifts by about 1.78 W m⁻²**, an almost
  uniform positive offset that carries the median from
  -1.78 to
  0.04 W m⁻². The shift is largest in the
  intensification phase (2.75 W m⁻²).
- **The pressure-work boundary terms collapse.** `BΦZ` and `BΦE` lose most of
  their amplitude, and `BΦE` is now *anti*-correlated with its legacy counterpart
  (Spearman -0.41), so the legacy term cannot be
  rescaled into agreement — its structure was wrong, not just its amplitude.

The residuals `RGz`, `RKz`, `RGe` and `RKe` change by the same amounts as `Ca` and
`Ck` with opposite signs, as expected from the budget closure — they are a
consistency check rather than an independent finding. The corrected toolkit also
outputs two terms with no legacy counterpart (`C_overturning`, `M`); they are not
comparable and are excluded.

## 3. Sign changes

Sign is what carries physical meaning in the LEC, so a change of sign matters more
than a change of magnitude. Per-sample sign-change rates are in
`figures/lec_rerun_comparison/signflip_heatmap.png`; the terms at risk are
Ca, Ck, BΦZ, BΦE, RGz, RGe and RKe.
The worst case is BΦE, which changes sign in
68% of cyclone-phases.


![Figure 4. Percentage of cyclone-phases whose term changed sign between the two versions.](../figures/lec_rerun_comparison/signflip_heatmap.png)

*Figure 4. Percentage of cyclone-phases whose term changed sign between the two versions.*

Three terms change the sign of their *climatological median*, which is the level at
which the article's statements are made: **Ck, BΦE and RGz**. Of these, `Ck` is
the consequential one: it enters the clustering and the conversion LPS. `BΦE` and
`RGz` enter neither, appearing only in the all-terms effect-size figure (Fig. S2),
which would need regenerating but carries no headline claim.

## 4. Consequences for the interpretation

**The clustering input is only partly affected.** The energy patterns are built from
seven terms (Ca, Ck, BAe, BKe, Ae, Ke and Ge) across four phases. 5
of the seven (BAe, BKe, Ae, Ke and Ge) are
unchanged; only Ca and Ck move. The EP separation should therefore
survive in outline, but the two conversion terms are precisely the ones that define
the conversion Lorenz Phase Space and the EP1 signature, so the clustering must be
rerun before any EP statement is reasserted.

**The barotropic result is the one that moves.**
`figures/lec_rerun_comparison/lec_diagram_before_after.png` shows this on the
four-box diagram: the `Ck` arrow reverses between the two versions during the
incipient and intensification phases, and shortens during maturity and decay.
With the convention of de Souza et al. (2025) — `Ca` > 0 feeds eddy APE,
`Ck` < 0 feeds eddy KE:

| Phase | Ck < 0 (legacy → corrected) | Ca > 0 & Ck < 0 | \|Ck\| > \|Ca\| with Ck < 0 | Median Ck |
|---|---|---|---|---|
| incipient | 67% → 39% | 54% → 30% | 57% → 19% | -0.94 → 0.53 |
| intensification | 76% → 47% | 68% → 41% | 68% → 18% | -2.31 → 0.18 |
| mature | 70% → 53% | 61% → 48% | 66% → 35% | -2.65 → -0.34 |
| decay | 68% → 57% | 57% → 49% | 64% → 40% | -1.88 → -0.61 |
| all phases | 70% → 49% | 60% → 42% | 64% → 28% | -1.78 → 0.04 |

Pooled over the life cycle, the share of cyclone-phases with barotropic conversion
feeding the eddy falls from 70% to
49%, occupancy of the doubly eddy-feeding
quadrant falls from 60% to
42%, and the share of cases where
barotropic conversion exceeds baroclinic conversion falls from
64% to
28%. During intensification the
last figure drops from 68% to
18%.


![Figure 5. Four-box Lorenz Energy Cycle by life-cycle phase: (A) incipient, (B) intensification, (C) mature, (D) decay. Dark is legacy, red is corrected.](../figures/lec_rerun_comparison/lec_diagram_before_after.png)

*Figure 5. Four-box Lorenz Energy Cycle by life-cycle phase: (A) incipient, (B) intensification, (C) mature, (D) decay. Dark is legacy, red is corrected.*


This weakens the article's headline claim that barotropic conversions are ubiquitous
during cyclone evolution and can exceed baroclinic conversions. In the corrected
climatology, barotropic conversion is close to neutral in the median, it is a
minority contributor during intensification, and it feeds the eddy in roughly half
of the cases rather than seven in ten. Two qualitative statements survive and one
does not:

- *Survives*: baroclinic conversion feeds the eddy in the large majority of cases,
  and is now unambiguously the dominant eddy source (`Ca` roughly tripled while
  `Ck` moved toward zero).
- *Survives, restated*: barotropic conversion remains present and eddy-feeding in a
  substantial minority of cyclone-phases, so it is still a real pathway — it is no
  longer the typical one.
- *Does not survive as stated*: the ordering of the phases. The legacy `Ck` was most
  strongly eddy-feeding during intensification and maturity; the corrected `Ck` is
  weakest during the incipient phase and becomes progressively more eddy-feeding
  toward decay. Any statement tying the barotropic peak to maturity needs to be
  rechecked against the corrected LPS.


**The leading EOF survives in shape but is reweighted.**
`figures/lec_rerun_comparison/eof1_diagram_before_after.png` redraws the thesis
EOF figure with both versions on the same axes. EOF 1 still explains a comparable
share of the variance (21-31% before, 21-29% after) and the two
patterns correlate at 0.78-0.87 across phases, so the mode is recognisably the
same. 6 of the 24 loadings move by less than 0.05, including
∂Ae/∂t, BAz, Az, Ca and BAe. The largest shifts are BΦE (1.41), RGe (0.63), RGz (0.59), i.e. the terms the
correction hit directly; among the terms the classical diagram actually shows, the
largest are Ck (0.32), ∂Az/∂t (0.13), BKz (0.11). The pattern is therefore stable where the
underlying terms did not change and moves where they did — which is what the
downstream PCA and k-means will inherit, and another reason to rerun them rather
than assume the EPs carry over. Beyond the leading mode the rank itself is not preserved — legacy EOF 2 in the incipient phase matches corrected mode 3; legacy EOF 3 in the incipient phase matches corrected mode 2; legacy EOF 2 in the intensification phase matches corrected mode 4; legacy EOF 3 in the intensification phase matches corrected mode 2; legacy EOF 4 in the intensification phase matches corrected mode 3 — because EOF 2 and EOF 3 explain similar variance and the correction is enough to reorder them. The figures pair modes by pattern correlation rather than by rank; comparing them by rank would be misleading.


![Figure 6. EOF 1 loadings on the LEC diagram, by phase: (A) incipient, (B) intensification, (C) mature, (D) decay. Dark is legacy, red is corrected.](../figures/lec_rerun_comparison/eof1_diagram_before_after.png)

*Figure 6. EOF 1 loadings on the LEC diagram, by phase: (A) incipient, (B) intensification, (C) mature, (D) decay. Dark is legacy, red is corrected.*

The same diagram for EOF 2 to EOF 4 (Figures 6 to 8 of the article) is in
`eof2_diagram_before_after.png`, `eof3_...` and `eof4_...`.

The `BΦ` collapse does not affect the published figures (the article uses `BAe` and
`BKe` for the import LPS, both unchanged), but it does affect the budget closure and
any future use of the pressure-work terms.

## 5. Caveats

- Partial population: the above uses 3,298 of 3,820 cyclones. Re-run `scripts/lec_rerun_comparison/run_all.py` when the rerun finishes to regenerate every number, figure and this document; the qualitative conclusions are unlikely to move, the exact percentages will.
- Statistics are medians and rank correlations throughout, because LEC phase means
  are heavy tailed. The violin figures are trimmed for display only; every number
  here uses the full sample.
- Secondary lifecycle periods (`decay 2`, etc.) are matched to their own legacy
  counterpart and folded into the parent phase, as in the corrected cache builder.
  Rows named `residual` are excluded.
- This report compares diagnostics, not conclusions. Nothing here substitutes for
  rerunning the PCA, the k-means and the EP figures on the corrected cache.

## 6. Files

| Artifact | Path |
|---|---|
| This report (PDF, figures embedded) | `docs/lec_rerun_comparison_report.pdf` |
| Paired table | `results/lec_rerun_comparison/paired_terms.parquet` |
| Term summary | `results/lec_rerun_comparison/term_change_summary.csv` |
| Per-phase summary | `results/lec_rerun_comparison/term_change_by_phase.csv` |
| Conversion regime | `results/lec_rerun_comparison/conversion_regime.csv` |
| Coverage / provenance | `results/lec_rerun_comparison/coverage.json` |
| Split-violin figures | `figures/lec_rerun_comparison/violin_{energy,conversion,generation,boundary,budget,residual}.png` |
| Sign-change heatmap | `figures/lec_rerun_comparison/signflip_heatmap.png` |
| Before/after LEC diagram | `figures/lec_rerun_comparison/lec_diagram_before_after.png` |
| Before/after EOF diagrams | `figures/lec_rerun_comparison/eof{1,2,3,4}_diagram_before_after.png` |
| EOF loadings and variance | `results/lec_rerun_comparison/eof_loadings.csv`, `eof_variance.csv` |
