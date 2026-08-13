# Scientific Notes — Explosive Cyclones by Energy Pattern

### 2026-06-16 — Analysis design (validated with PI before implementation)

---

## Research Questions

1. What fraction of the cyclones in each Energy Pattern (EP1, EP2, EP3) undergo
   **explosive cyclogenesis** ("bombs"), and how does this fraction differ across EPs?
2. How do the explosive systems distribute among intensity classes (weak / moderate /
   intense) by EP?
3. Does explosive deepening preferentially occur **during the intensification phase**, and
   does the surface-pressure picture corroborate the energetic-pathway interpretation of the
   EPs (EP1 strong conversions, EP2 moderate, EP3 weak)?
4. Is each EP **enriched or depleted** in explosive cyclones relative to the pooled
   population, and does that enrichment strengthen along the severity ladder — i.e. is an EP
   over-represented specifically in the *severe tail* rather than merely in the count of
   bombs?
5. **Where** do the explosive cyclones of each EP form, live, and undergo their maximum
   deepening — and are those three locations distinct?

## Physical / Statistical Framework

A cyclone is "explosive" when its central-pressure deepening reaches **at least 1 Bergeron**
(Sanders & Gyakum 1980). The deepening rate is geostrophically normalized with the **sine** of
latitude (the threshold scales with the Coriolis parameter, f ≈ 2Ω sin φ), referenced to 60°:

$$
\mathrm{NDR} = \frac{\Delta p_{24\mathrm{h}}}{24\ \mathrm{hPa}} \cdot
\frac{\sin 60^\circ}{\lvert \sin \varphi \rvert} \quad [\text{Bergeron}],
\qquad \Delta p_{24\mathrm{h}} = p(t) - p(t+24\,\mathrm{h}),
$$

with φ the mean latitude over the 24-h window (Δp > 0 for deepening). NDR ≥ 1 ⇒ bomb. The
local threshold is ≈ 13.9 hPa/24 h at 30° and ≈ 27.7 hPa/24 h at the pole. **Note:** the
adjustment uses **sin φ, not cos φ** — all standard formulations (Sanders & Gyakum; Lim &
Simmonds; Allen et al.; the South Atlantic AABC study) use the sine. The "updates" in the
literature concern the reference latitude (60° vs 45°), the time window, and the combined
criterion of Allen et al. (2010) — not a switch to cosine.

Intensity classes (AABC 2024): weak [1.0, 1.3), moderate [1.3, 1.8], intense (> 1.8).

## Datasets and Variables

- **Cyclone tracks**: *Atlantic Extratropical Cyclone Tracks Database* (Gramcianinov et al.
  2020), TRACK algorithm on 850-hPa relative vorticity ζ₈₅₀; 1979–2020; **1-hourly**.
  Columns used: `date`, `lat vor`, `lon vor`, `period` (CycloPhaser phases), `region`.
  Tracks provide **no central pressure** — hence the MSLP step below.
- **EP membership**: K-Means clustering on phase-mean LEC diagnostics
  (`results/cluster/kmeans_clustered_data.csv`); full populations **EP1 = 444, EP2 = 979,
  EP3 = 2397** (total 3820). This is the authoritative population and is used here in full
  (**not** the reduced composite subset of 332/776/1625, which excludes intensification < 24 h).
- **MSLP**: ERA5 `mean_sea_level_pressure`, 0.25°, hourly, downloaded storm-following over each
  full track (genesis→lysis, padded ±12 h), in a box = track envelope + 6°.

## Methodology

1. **Population (step1).** Map clusters → EPs; extract the full hourly tracks for all 3820
   cyclones.
2. **MSLP download (step2).** Storm-following `msl` over each full track. Light CDS parallelism.
3. **Central-pressure assignment — "A+B" (step3).** At each track timestep, start at the ζ₈₅₀
   centre and **descend the MSLP gradient** to the bottom of the pressure basin the centre
   drains into; accept it only if that bottom is a **local interior minimum** within a search
   radius R0 = 3° ("A"). If none is found within R0, expand once to R1 = 5°. If the descent
   leaves the radius (open wave / displaced surface low / boundary-touching minimum), the
   timestep is **flagged and set to NaN** rather than forced to a boundary value. A
   continuity check flags centres that jump > 4° between consecutive steps. Because descent
   follows the basin topology, a deeper minimum belonging to a neighbouring system (across a
   col) never hijacks the centre. A best-effort `over_land` flag marks continental positions.
4. **NDR and classification (step4).** Reindex central pressure to a regular hourly grid
   (interpolate gaps ≤ 2 h); slide a **centred 24-h window** and take the **maximum NDR** per
   cyclone, reported over the full life cycle **and** restricted to the intensification phase
   (`period` starting with "intensification"). A 6-hourly-subsampled NDR is also reported for
   comparison with synoptic-resolution climatologies. Flag bombs and assign intensity classes;
   aggregate by EP.
5. **Figures (step5).** Results (bomb frequency, NDR distribution, intensity composition by EP)
   plus validation (offset distribution, flag fraction by phase).
6. **Relative frequency (step6).** The explosive rate of each EP against the pooled EPALL
   population, on a **nested severity ladder** (NDR ≥ 1.0, ≥ 1.3, ≥ 1.8). Rates carry Wilson
   95% score intervals; the ratio to EPALL is a *descriptive effect size* only, because each
   EP is nested in the reference. The inferential claim is Fisher's exact test of each EP
   against the **other two pooled** — a genuinely independent contrast — with Holm correction
   over the nine tests. Denominator: only cyclones with an **assessable** NDR (a
   central-pressure series spanning a full 24-h window); see Assumptions.
7. **Density maps (step7).** Spherical KDE (Gaussian kernel, haversine metric, bandwidth
   0.05 rad ≈ 318 km, 2.5° Hoskins & Hodges grid — the same estimator as the manuscript's
   genesis-density figure, imported from `scripts/cps_analysis/cps_density.py`) for three
   kinds of position: **genesis** (one per cyclone), **track** (whole life cycle, hourly
   positions subsampled to 3 h and weighted by dt/24, giving cyclone days) and **deepening**
   (the position at the time of maximum NDR — where the explosive deepening is centred).
   Rows are explosive class, columns are EPALL / EP1 / EP2 / EP3, in both an absolute and a
   min-max-normalised anomaly convention.

## Assumptions

- The 850-hPa vorticity centre and the surface low lie within R0–R1 of each other for closed,
  deepening systems (validated a posteriori via the offset distribution).
- ERA5 0.25° hourly MSLP resolves the central-pressure evolution of these systems adequately.
- φ in the NDR may be taken at the central/vorticity position (the two differ by ≲ a few
  degrees; the sin factor is insensitive to this).
- Short-gap (≤ 2 h) linear interpolation of central pressure does not bias the 24-h deepening.
- **A cyclone without an assessable NDR is unclassifiable, not non-explosive.** Steps 6 and 7
  therefore exclude it from numerator *and* denominator. This matters because the
  unassessable fraction is not uniform across EPs (EP3 3.3%, EP1 2.1%, EP2 1.2%) and EP3 is
  the low-frequency pattern, so charging its missing NDRs to the non-bomb column — which is
  what step4's aggregate table does — would exaggerate the very contrast the analysis
  reports. The effect is small (EP3 19.6% vs 20.3%) and both conventions are printed, but it
  is the wrong direction to leave implicit.
- The whole-life density maps subsample the hourly tracks to 3 h. The residence-time weight
  (dt/24) makes the density invariant to this in expectation; hourly positions of a single
  cyclone are in any case far from independent samples.

## Results and Interpretation

### 2026-08-13 — First full-population results (3,759 of 3,820 cyclones)

Coverage: 3,759 of the 3,820 cyclones have ERA5 MSLP (98.4%; the remaining 61 failed on
transient CDS queue rejections and are still being retried). Of those, **3,660 have an
assessable NDR** — a central-pressure series spanning a full 24-h window. The earlier June
run used only 1,145 cyclones and, because CDS queue rejections concentrated in whichever
cyclones were dispatched last, that subsample was almost entirely 1979–1993; the frequencies
below supersede it. Reassuringly, they barely moved (EP1 41.4 → 42.1%, EP2 52.9 → 56.5%,
EP3 18.6 → 20.2%), so the ordering was not an artefact of the biased sample.

> All figures in this section are quoted from the run over **3,759 processed / 3,660
> assessable** cyclones. The pipeline re-runs itself when the outstanding downloads land
> (`finalize_after_download.sh`), which will shift the third significant figure; the
> population line at the top of every step6/step7 figure is authoritative.

**1. Explosive frequency is strongly EP-dependent, and EP2 — not EP1 — leads.**

| | EP1 | EP2 | EP3 | EPALL |
|---|---|---|---|---|
| bomb, NDR ≥ 1.0 | **42.1%** (178/423) | **56.5%** (539/954) | **20.2%** (462/2283) | 32.2% |
| ratio to EPALL | 1.31 [1.16, 1.45] | 1.75 [1.65, 1.85] | 0.63 [0.58, 0.68] | 1 |
| Fisher vs other two | p = 7×10⁻⁶ | p = 2×10⁻⁷⁴ | p = 1×10⁻⁸⁷ | — |

All three contrasts survive Holm correction. EP2 is enriched ~1.8×, EP1 ~1.3×, EP3 depleted
to ~0.6× of the pooled rate.

**2. The enrichment strengthens along the severity ladder for EP2 and weakens for EP3.**
Ratios to EPALL at NDR ≥ 1.0 / ≥ 1.3 / ≥ 1.8:

- **EP2**: 1.75 → 1.97 → **2.26** — over-represented specifically in the *severe tail*.
  In absolute terms 56.5% → 33.2% → 9.4% of EP2 cyclones.
- **EP3**: 0.63 → 0.51 → **0.40** — depleted throughout, and progressively more so
  (20.2% → 8.6% → 1.7%).
- **EP1**: 1.31 → 1.46 → 1.41 — enriched, but the intense cell (25 cyclones, 5.9%) is the
  only one of the nine contrasts that fails Holm (p = 0.07); EP1's excess is in the *moderate*
  band rather than the extreme tail. **[UNCERTAIN — small cell.]**

**3. Explosive deepening is overwhelmingly an intensification-phase phenomenon.** 1,120 of
the 1,179 life-cycle bombs (**95.1%**) reach NDR ≥ 1 with the 24-h window centred inside a
CycloPhaser intensification phase. Repeating the whole of step6 on the intensification scope
changes no conclusion (EP1 40.6%, EP2 55.7%, EP3 19.7%; identical ratio ordering and
significance pattern). This is a consistency check on the life-cycle framework as much as a
result: the surface-pressure diagnostic and the vorticity-based phase segmentation agree
about when a cyclone is deepening.

**4. Interpretation — the ordering is EP2 > EP1 > EP3, not EP1 > EP2 > EP3.** The energetic
ordering of the clusters (EP1 high conversions, EP2 moderate, EP3 weak) does *not* map
monotonically onto explosive frequency, which was the a-priori expectation recorded above.
The result is robust to the denominator, the scope and the sample, so it is a property of the
clusters rather than of the method. A plausible reading, consistent with the EP definitions:
EP1 is defined by *large conversion magnitudes* including strong **export** of energy to the
surroundings, whereas EP2 **imports** energy from the large-scale environment. Sustaining a
24-h central-pressure collapse plausibly favours the importing pathway over the exporting
one, i.e. the sign of the boundary flux may matter more for surface deepening than the raw
magnitude of the interior conversions. **[PRELIMINARY — this is an interpretation of an
association, not a demonstrated mechanism; testing it requires relating NDR to the individual
LEC terms, not to the cluster label.]**

**5. Genesis, residence and deepening are three different places** (step7). For the bombs,
the median position of maximum deepening is **~8° south and ~26° east** of the median
genesis point (EPALL: genesis 37.8°S 60.7°W → deepening 45.5°S 35.1°W), so a map of where
bombs are *born* is not a map of where they *explode*. The displacement is EP-dependent:
EP3 bombs travel furthest before deepening (+31° lon), EP1 the least (+23° lon, and only
4.6° of latitude). In the genesis maps, the bomb population carries a secondary maximum
near 30–35°S off SE Brazil that the full population does not, while EP3's bomb genesis is
strongly depleted there; in the deepening maps, EP3's bombs are displaced along a
50–55°S band well east of the continent.

Conditioning on the genesis region (which the clustering never saw) shows the same
structure: bombs are **45.7%** of LA-PLATA genesis, **32.3%** of SE-BR and only **27.2%** of
ARG.

**6. The intensity classes track a genesis-latitude gradient, and it is not a normalisation
artefact.** Median genesis latitude falls monotonically with class — non-explosive 43.8°S,
weak 42.2°S, moderate 36.2°S, **intense 33.8°S** — and the share born in LA-PLATA or SE-BR
rises 37% → 41% → 57% → **69%**. Because NDR carries a 1/|sin φ| factor, a subtropical
cyclone clears a given NDR with less absolute deepening, so the gradient could in principle
be manufactured by the normalisation. Inverting the normalisation at the latitude of maximum
deepening shows it is not: the **raw** 24-h deepening also rises monotonically across the
classes (weak 22.8, moderate 29.1, **intense 39.6 hPa/24 h**). Intense bombs deepen more in
absolute terms, not merely more per unit sin φ.

Note also that the gradient is in *genesis* latitude, not deepening latitude: median
deepening latitude varies by only ~3° across the classes (46.7°S → 43.7°S). Intense bombs
are born much further north but explode at much the same latitude as the rest, i.e. they
travel further poleward before deepening.

**7. Robustness of the EP result to the latitude normalisation.** The same 1/|sin φ| factor
is a real concern for the headline EP contrast, because the EPs do not deepen at the same
latitude (median for bombs: EP1 42.4°S, EP2 44.6°S, EP3 48.1°S). The effective leniency
ratio between EP2 and EP3 is sin(48.1°)/sin(44.6°) ≈ **1.06** — a 6% easier threshold for
EP2 — against an observed rate ratio of 56.5/20.3 ≈ **2.8**. The normalisation therefore
accounts for a negligible part of the EP contrast. It is a much larger share of the
*regional* contrast: LA-PLATA bombs deepen at 40.2°S against ARG's 49.0°S, worth ~17% in
effective threshold, so the LA-PLATA-vs-ARG bomb-rate gap (45.7% vs 27.2%) should not be
read at face value. Consistently, the median raw dP₂₄ of bombs is essentially identical
across the three genesis regions (~26 hPa/24 h) while their median NDR is not (ARG 1.26,
LA-PLATA 1.39, SE-BR 1.43). **[This is a property of the Sanders & Gyakum definition used
throughout the literature, not an error — but regional comparisons of bomb frequency inherit
it and should be stated with the caveat.]**

### Method validation

The offset between the ζ₈₅₀ centre and the assigned surface low has median **1.35°**
(p90 = 2.96°, p99 = 4.58°), comfortably inside R0 = 3°/R1 = 5°, so the search radii are not
truncating the vortex-tilt distribution. **88.1%** of the 431,821 timesteps received a valid
central pressure; of the rest, the dominant flag is `no_interior_min` (51,203 steps — open
waves with no closed low, concentrated as expected in the incipient phase), with 34,689
resolved only by the expanded radius and 3,816 continuity `jump` flags.

## Caveats and Limitations

- **Vortex tilt / displacement.** A radius too small biases the central pressure high
  (deepening underestimated); R0 = 3° with the A+B interior-minimum rule mitigates this, and
  the offset histogram is the diagnostic.
- **Multiple/secondary centres & merging.** Mitigated by basin-respecting descent and the
  continuity flag, but complex multi-centre systems remain a source of noise.
- **Open waves.** Early life-cycle timesteps often lack a closed low; these are flagged/NaN by
  design and rarely affect the bomb signal (explosive deepening is a closed-low phenomenon).
- **Topography / MSLP reduction.** Many systems have genesis over land (ARG, SE-BR); MSLP
  reduction over high terrain (Andes) is unreliable. The `over_land` flag is best-effort and a
  finer orography mask is a possible refinement.
- **Latitude span.** Subtropical genesis (30° S) implies a low local threshold (≈13.9 hPa/24 h);
  φ is taken as the window-mean latitude for migrating systems. Any comparison between groups
  that deepen at *different* latitudes inherits the 1/|sin φ| factor: it is negligible for the
  EP contrast (~6% of an observed 2.8× ratio) but material for the genesis-region contrast
  (~17%). See Results §7.
- **Window length.** Short-lived cyclones may not span 24 h of valid central pressure → no NDR
  (99 of 3,759, recorded via `n_valid_central` / `n_steps`). step4 counts these as
  non-explosive; steps 6–7 exclude them — see Assumptions.
- **Sample completeness.** 66 of the 3,820 cyclones (1.7%) still lack MSLP after two download
  campaigns, all lost to transient CDS queue rejections rather than to any property of the
  cyclones. They are spread proportionally across EPs (12/14/40) and decades, so the residual
  bias is negligible, but the tables are not yet the full population.
- **The ratio in step6 is not an independent test.** Each EP is nested in EPALL, so the
  plotted ratio and its interval are a descriptive effect size; the significance claims come
  from the Fisher contrasts against the other two EPs pooled.
- **Nested outcomes.** The three severity outcomes are thresholds on the same NDR, so the
  nine Fisher contrasts are not independent of one another. Holm is valid without an
  independence assumption, but the ladder should be read as one coherent pattern rather than
  as three separate findings.
- **Density-map domain.** The whole-life maps are drawn on a frame holding ≥ 90.9% of each
  column's positions (deepening ≥ 97.3%, genesis 100%). The min-max normalisation used by
  the anomaly panels is therefore taken over the plotted region, not the globe.
- **Explosive class is a whole-cyclone label in the track maps.** A bomb's track density
  includes the non-explosive remainder of its life cycle; the structure-resolved question is
  answered by the deepening maps instead.

## Next Steps

- Land the remaining 66 MSLP downloads and re-run steps 3–7 for the complete 3,820 population.
- Test the EP2-over-EP1 interpretation directly: regress/compare NDR_max against the
  individual LEC terms (conversion magnitudes vs boundary fluxes) rather than the cluster
  label, which is the only way to distinguish "importing pathway favours deepening" from a
  cluster-composition effect.
- Check whether the EP2 excess survives conditioning on genesis region and season — LA-PLATA
  genesis alone carries a 45.7% bomb rate, and the EPs are not evenly distributed across the
  three regions.
- Inspect the offset distribution and flag fractions; tune R0/R1 if the tail is long.
- Optional: add an ERA5 orography mask for an explicit high-terrain flag; compare hourly vs
  6-hourly NDR; cross-check against the AABC (2024) South Atlantic explosive-cyclone counts.

## References

- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb". *Mon. Wea.
  Rev.*, 108, 1589–1606.
- Lim, E.-P., & Simmonds, I. (2002). Explosive cyclone development in the Southern Hemisphere…
  *Mon. Wea. Rev.*, 130, 2188–2209.
- Allen, J. T., Pezza, A. B., & Black, M. T. (2010). Explosive cyclogenesis: a global
  climatology comparing multiple reanalyses. *J. Climate*, 23, 6468–6484.
- Reale, M., et al. (2019). A global climatology of explosive cyclones using a multi-tracking
  approach. *Tellus A*, 71, 1611340.
- de Jesus, E. M., et al. (2024). Explosive cyclones between 2010 and 2020 in the South Atlantic
  under two detection schemes. *An. Acad. Bras. Ciênc.* (AABC).
- Gramcianinov, C. B., et al. (2020). Atlantic extratropical cyclone tracks database. (Tracks
  used in this study.)
- Hoskins, B. J., & Hodges, K. I. (2005). A new perspective on Southern Hemisphere storm
  tracks. *J. Climate*, 18, 4108–4129. doi:10.1175/JCLI3570.1 (KDE grid and normalisation
  used by the step7 density maps.)
- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference.
  *J. Amer. Statist. Assoc.*, 22, 209–212. (Score interval used for the proportions.)
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scand. J.
  Statist.*, 6, 65–70.
