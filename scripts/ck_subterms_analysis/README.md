# Ck Subterms Analysis — Barotropic Conversion Decomposition, all Energy Patterns

Decomposes the barotropic conversion term `C_K` into its five subterms for
**EP1, EP2, EP3 and EPALL**, from the corrected LEC climatology.

## What changed and why

The decomposition used to be an EP1-only study (444 cyclones). That was a
computational limit, not a scientific choice: the article's archived results
carried only the total `C_K`, so obtaining the subterms required a separate
LorenzCycleToolKit run, and running it over the whole population would have
meant ~222 GB of ERA5 and thousands of toolkit executions.

The corrected climatology rerun (`scripts/lec_climatology_rerun`) removes that
limit. It writes `Ck_1_pressure_level.csv` … `Ck_5_pressure_level.csv` for every
one of the 3,820 cyclones, so **the decomposition is now available for every
Energy Pattern at no extra computational cost**. This pipeline reads those
products; it launches nothing.

The previous EP1 side run is retired in `deprecated_ep1_side_run/`. Its outputs
in `results/ck_analysis/` predate the LorenzCycleToolKit 2.0.0 corrections and
must not reach the article.

## Scientific framing

`C_K` is the transfer of kinetic energy between the cyclone-scale eddy and the
large-scale mean flow. In the limited-area, semi-Lagrangian framework used here:

- `C_K < 0` → K_Z → K_E: the mean flow feeds the eddy (barotropic instability);
- `C_K > 0` → K_E → K_Z: the eddy exports energy to the mean flow.

The **dominant subterm** of a cyclone is therefore the *most negative* one — the
largest contributor to the mean-to-eddy transfer.

Vertically integrated from p_t to p_b (manuscript equation for C_K):

$$C_K = \int_{p_t}^{p_b} \frac{1}{g} \left[
  \underbrace{\frac{\cos\phi}{a}(u)'(v)'\frac{\partial}{\partial\phi}\!\left(\frac{[u]}{\cos\phi}\right)}_{\text{(A)}}
+ \underbrace{\frac{(v)'^2}{a}\frac{\partial [v]}{\partial\phi}}_{\text{(B)}}
+ \underbrace{\frac{\tan\phi}{a}(u)'^2[v]}_{\text{(C)}}
+ \underbrace{(\omega)'(u)'\frac{\partial [u]}{\partial p}}_{\text{(D)}}
+ \underbrace{(\omega)'(v)'\frac{\partial [v]}{\partial p}}_{\text{(E)}}
\right] dp$$

Square brackets are area means, primes the deviations from them.

| File stem | Label | Physical mechanism |
|---|---|---|
| `Ck_1` | Ck_A | Eddy momentum flux against the meridional shear of `[u]` — the classic barotropic-instability term |
| `Ck_2` | Ck_B | Meridional flux of eddy KE against the meridional gradient of `[v]` |
| `Ck_3` | Ck_C | Curvature (tan φ) flux of zonal eddy KE |
| `Ck_4` | Ck_D | Vertical flux of zonal eddy momentum against the shear of `[u]` |
| `Ck_5` | Ck_E | Vertical flux of meridional eddy momentum against the shear of `[v]` |

### Unit convention (important)

The toolkit writes the `Ck` family **without** the `1/g` factor, in both
versions. `scripts/utils/corrected_lec.py` applies `g = 9.80665` on read, so
every value in this pipeline already integrates to the integrated `C_K`. Never
re-apply a gravity division downstream. The legacy scripts used `9.8`, a 0.07 %
high bias.

The decomposition is verified to close, `C_K = Σ Ck_i`, to round-off; the
relative residual is carried in the output and step 1 refuses to write above
`1e-6`.

## Research questions

1. Which subterm dominates the barotropic transfer in each Energy Pattern and
   each lifecycle phase?
2. How large is each subterm, and what share of the total `C_K` does it carry?
3. Do the Energy Patterns differ in *mechanism*, or only in *amplitude* of the
   same mechanism?

## Pipeline

```bash
python scripts/ck_subterms_analysis/run_all.py
```

| Step | Script | Output |
|---|---|---|
| 1 | `step1_build_subterms_table.py` | Integrated subterms per cyclone, phase and EP; closure validation |
| 2 | `step2_subterm_statistics.py` | Descriptive statistics, dominance frequency, EP contrasts |
| 3 | `step3_subterm_figures.py` | Vertical profiles, boxplots, lifecycle evolution |

### Prerequisites

1. The corrected rerun is COMPLETE and
   `scripts/lec_climatology_rerun/build_corrected_vertical_levels.py` has written
   `data/corrected/vertical_phase_means_corrected.parquet`.
2. The clustering has been rebuilt on `data/corrected/energy_cache_corrected.parquet`,
   so `results/cluster/cluster_to_ep.json` records a corrected lineage. `run_all.py`
   refuses to proceed on a legacy clustering unless `--allow-partial` is given.

`--allow-partial` runs the pipeline on whatever the rerun has finished so far.
Use it to develop and sanity-check; never for an article result, because the
population then depends on the moment the script ran.

## Statistics

The subterm distributions are heavy-tailed and change sign, so the tests are
rank based:

- Kruskal-Wallis across EP1/EP2/EP3 per (subterm, phase);
- pairwise Mann-Whitney U with the rank-biserial correlation as effect size;
- Benjamini-Hochberg FDR at q = 0.05 over all pairwise tests of a phase, which
  controls the 5 subterms × 3 contrasts multiplicity.

EPALL is reported descriptively and never tested against its own members.

## Outputs

```
results/ck_subterms_corrected/
├── subterms_by_cyclone.csv    one row per (track_id, phase): the six integrated
│                              Ck quantities, shares, dominant subterm, closure
├── subterms_long.csv          tidy form for plotting
├── subterm_statistics.csv     mean/median/IQR/share per EP, phase, subterm
├── dominance_frequency.csv    how often each subterm dominates
├── ep_contrasts.csv           Kruskal-Wallis + FDR-corrected pairwise tests
├── build_report.md            coverage and closure validation
└── statistics_report.md       readable answer to the three questions

figures/ck_subterms_corrected/
├── ck_subterms_vertical_profiles.png   mean profile of C_K and subterms per EP
├── ck_subterms_boxplots.png            integrated subterm distributions per EP
└── ck_subterms_lifecycle.png           phase-by-phase ensemble means per EP
```

## Expectations to re-test, not to assume

The earlier EP1-only study, on legacy data, reported Ck_E dominant in 43 % of
cases, Ck_B in 38 % and Ck_A in 19 %, and hypothesised that the horizontal
momentum flux (Ck_A) would carry 70–80 % of the total. Both the toolkit
correction and the widened population make those numbers provisional: treat the
new `statistics_report.md` as the result, and revisit the manuscript text rather
than reconciling the new output to the old claims.

## References

- **Lorenz, E. N.** (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157–167.
- **Orlanski, I., & Sheldon, J. P.** (1995). Stages in the energetics of baroclinic systems. *Tellus A*, 47(5), 605–628.
- **Dias Pinto, J. R., & da Rocha, R. P.** (2011). The energy cycle and structural evolution of cyclones over southeastern South America in three case studies. *JGR*, 116, D14104.
- **Michaelides, S. C.** (1987). Limited area energetics of Genoa cyclogenesis. *Mon. Wea. Rev.*, 115, 13–26.
