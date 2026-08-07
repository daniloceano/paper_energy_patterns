# Scientific Notes — CPS Sensitivity Tests

**This is not the analysis of record.** It is the exploratory record that established the
methodology now implemented in the canonical pipeline. The canonical science notes are in
`../SCIENTIFIC_NOTES.md`; the framework, datasets, equations and sign conventions are
documented there and are not repeated here.

Purpose of this document: to keep the evidence behind each canonical design choice, and to
serve the paper's sensitivity discussion.

CPS computation: **Andres Rodriguez (IAG-USP)**.
Sensitivity tests and these notes: **Danilo Couto de Souza**.

---

## Table of Contents

- [Threshold sets tested](#threshold-sets-tested)
- [Sensitivity pipeline](#sensitivity-pipeline)
- [Results](#results)
- [What each finding decided](#what-each-finding-decided)
- [References](#references)

---

## Threshold sets tested

There is no single accepted partition. Six sets are applied, all transcribed verbatim from
peer-reviewed sources into `cps_criteria.py`. Three are South Atlantic sets:

| Set | Class | $B$ [m] | $-V_T^L$ | $-V_T^U$ | Source |
|---|---|---|---|---|---|
| **C01** | extratropical | $> 10$ | $< 0$ | $< 0$ | Cavicchia et al. (2019), via Conrado et al. (2024) Fig. 2a |
| | subtropical | $< 10$ | $> 0$ | $< 0$ | |
| | tropical | $< 10$ | $> 0$ | $> 0$ | |
| **GOZZO14** | extratropical | $> 10$ | $< 0$ | $< 0$ | C01 |
| | **subtropical** | $< 25$ | $> -50$ | $< -10$ | **Gozzo et al. (2014)** |
| | tropical | $< 10$ | $> 0$ | $> 0$ | C01 |
| **C03** | extratropical | $> 10$ | $< 0$ | $< 0$ | C01 |
| | subtropical | $< 25$ | $> -50$ | $< -10$ | Gozzo et al. (2014) |
| | **tropical** | $-10 < B < 10$ | $> 0$ | $> -50$ | **Marrafon et al. (2022)**, via Conrado et al. (2024) Fig. 2a |

Three further sets are applied as **cross-basin controls**, to check that the South
Atlantic conclusions are not an artefact of one basin's threshold choices:

| Set | Basin | Class | $B$ | $-V_T^L$ | $-V_T^U$ |
|---|---|---|---|---|---|
| **YANASE14** | global | tropical | — | $> 0$ | $> -10$ |
| | | subtropical ("HC") | — | $> 0$ | $< -10$ |
| | | extratropical ("EC") | — | $< -50$ | — |
| **CAVICCHIA19** | Australian ECLs | tropical ("warm-cored") | — | $> 0$ | $> 0$ |
| | | subtropical ("hybrid") | — | $> 0$ | $< 0$ |
| | | extratropical ("cold-cored") | — | $< 0$ | $< 0$ |
| **GUISHARD09** | North Atlantic | subtropical | — | $> -10$ | $< -10$ |

Both YANASE14 and CAVICCHIA19 use the **thermal wind only**, with no $B$ condition.
Yanase et al. (2014), verbatim: *"cyclones are classified as TCs for $-V_T^L > 0$ and
$-V_T^U > -10$, HCs for $-V_T^L > 0$ and $-V_T^U < -10$, ECs for $-V_T^L < -50$, and
ill-defined cyclones for the others, where the threshold of $-V_T^U$ is based on Guishard
et al. (2009)."* Their explicit *ill-defined* class is the direct analogue of our
`unclassified`.

Cavicchia et al. (2019), verbatim: *"three classes of cyclones are defined based on the
thermal wind parameters $V_T^U$ and $V_T^L$ only: the cold-cored cyclone is associated with
$-V_T^L < 0$ and $-V_T^U < 0$, the warm-cored cyclone with $-V_T^L > 0$ and $-V_T^U > 0$,
and the hybrid cyclone with $-V_T^L > 0$ and $-V_T^U < 0$."* **They deliberately name their
classes cold-cored / hybrid / warm-cored rather than extratropical / subtropical /
tropical**, because they study a mid-latitude population comparable to ours — a naming
choice this analysis should adopt (see Results §2).


---

## Sensitivity pipeline

### Sensitivity pipeline (`sensitivity/`)

The exploratory suite that established the design above. Six threshold sets (three South
Atlantic, three cross-basin) crossed with four identification rules of increasing
strictness, plus three dedicated diagnostics:

- **Life-cycle timing** — phase composition of each class, onset relative to genesis, and
  the attrition of each class as the rules tighten. This is the warm-seclusion diagnosis.
- **Distributions** — seasonal, interannual, geographic and life-cycle properties.
  Non-parametric throughout (Kruskal–Wallis, Mann–Whitney with rank-biserial correlation),
  because none of lifetime, vorticity or persistence is normally distributed and the group
  sizes are very unequal.
- **Episodes and documented cases** — every episode with start/end dates, and a check
  against thirteen named South Atlantic cyclones.

Contingency analysis in both pipelines uses chi-square with Cramér's V and Pearson
standardised residuals, Fisher's exact test where counts are single-digit, and
genesis-region stratification as a confounding control.


---

## Results

*These are the exploratory results that established the canonical design. The
headline numbers of the analysis are in **Canonical Results** above.*

### S1. Population composition and validation against the literature

Two independent external anchors, at opposite ends of the strictness scale.

**Relaxed protocol.** Applying the geographic protocol without the onset criterion
(`type_protocol`: subtropical thresholds, ≥ 36 consecutive hours, over ocean, genesis
20°–40°S) to the whole 6,776-cyclone population gives **389 subtropical cyclones over
1979–2020 = 9.3 per year = 5.7% of the population**.

Gozzo et al. (2014), for 1979–2011 with ERA-Interim, report *"a total of 238 (233)
subtropical cyclogeneses [...] corresponding to 3.7% (4.2%) of the total cyclogeneses"*,
a mean of $7.2 \pm 2.8$ per year. Their climatology is deliberately **broad** — they
dropped the gale-force wind threshold and the upper-closed-low requirement to capture
shallow coastal systems.

**Strict protocol.** Adding the onset criterion (`type_strict`) gives **104 subtropical
cyclones = 2.5 per year = 1.5% of the population** with the GOZZO14 thresholds. Applying
the strict protocol with the **GUISHARD09 thresholds** — the set of the same lineage as the
strict-end climatologies, before Gozzo et al. relaxed the $-V_T^L$ bound — gives
**74 cyclones = 1.8 per year**.

Evans and Braun (2012), the first South Atlantic subtropical climatology and the strict
end of the literature, report **1.2 SCs per year** (as quoted by Gozzo et al. 2014).
Guishard et al.'s (2009) North Atlantic climatology, using the same five-criterion
protocol, gives **4 per year** — for a different basin, and with a gale-force wind
requirement we do not apply.

The comparisons bracket the literature at both ends and in the right order:

| Our result | Literature |
|---|---|
| 9.3/yr — GOZZO14 thresholds, relaxed protocol | Gozzo et al. (2014), broad criteria: **7.2/yr** |
| 1.8/yr — GUISHARD09 thresholds, strict protocol | Evans and Braun (2012), South Atlantic, strict: **1.2/yr** |

**Both ends validate the whole chain** — Andres's calculator, the sign conventions, the
classification code and the protocol implementation. The agreement is of the right order
rather than exact, as it must be: the reanalyses differ (ERA5 vs ERA-Interim), the tracking
level differs (850-hPa vorticity here vs 925-hPa in Gozzo et al.), and we omit both the
gale requirement and Gozzo et al.'s manual visual rejection — all of which push our counts
upward relative to theirs, which is the direction observed.

The seasonality validates independently too: over the whole population the subtropical
class peaks in **austral summer (DJF 34.5%, MAM 24.1%, SON 21.7%, JJA 19.6%)**, matching
Gozzo et al. (2014): *"most of the SCs develop during austral summer (December–February)"*.

Whole-population counts under each rule (GOZZO14 thresholds):

| Rule | Tropical | Subtropical | Extratropical | Unclassified |
|---|---|---|---|---|
| `type_any` | 767 | 2,948 | 3,040 | 21 |
| `type_persistent` | 16 | 796 | 2,787 | 3,177 |
| `type_protocol` | 8 | 389 | 1,056 | 5,323 |
| **`type_strict`** | **0** | **104** | **862** | **5,810** |

### S2. The tropical class is warm seclusions — resolved, not merely flagged — **[IMPORTANT]**

Three independent lines of evidence, all pointing the same way.

**(a) Latitude.** Tropical-classified timesteps have a median latitude of **−57.7°**, with
98% poleward of 35°S.

**(b) Life-cycle phase.** The class is overwhelmingly a late-life-cycle phenomenon
(% of the class's timesteps, GOZZO14):

| Class | incipient | intensification | mature | decay | residual |
|---|---|---|---|---|---|
| tropical | 0.2% | 5.8% | **27.0%** | **65.8%** | 1.2% |
| subtropical | 3.3% | 21.2% | 13.5% | 59.7% | 2.3% |
| extratropical | 8.2% | 44.9% | 8.0% | 36.4% | 2.5% |
| *(all timesteps)* | *7.1%* | *37.4%* | *9.7%* | *43.4%* | *2.4%* |

**93% of tropical timesteps fall in mature + decay**, against a 53% baseline, and the
mature share is 2.8× enriched. The class is essentially absent from the incipient phase
(0.2% vs 7.1%).

**(c) Onset relative to genesis.** The tropical class first appears a median of **75 h
after genesis, at 58% through the life cycle**, and only 5.1% of cases reach it within
24 h. For the extratropical class the corresponding figures are 3 h and 97.5%. Restricting
to runs that themselves satisfy the 36-h persistence requirement, the tropical onset median
is **98 h** and **0.0%** occur within 24 h.

This is the Shapiro–Keyser warm seclusion, exactly as Hart (2003) describes it — his
20-year climatology found that region of the phase space populated by *"warm-core cyclones
(primarily warm-seclusion extratropical cyclones)"*.

**Applying the onset criterion resolves it.** Tropical counts, persistent → strict:

| Threshold set | Basin | persistent | strict |
|---|---|---|---|
| C01 | South Atlantic (via Conrado et al.) | 16 | **0** |
| GOZZO14 | South Atlantic | 16 | **0** |
| C03 | South Atlantic, relaxed tropical | 40 | **0** |
| YANASE14 | global | 38 | **1** |
| CAVICCHIA19 | Australian ECLs | 33 | **1** |
| GUISHARD09 | North Atlantic | 16 | **0** |

**The tropical class collapses to 0–1 cyclones under every threshold set, including the
three imported from other basins.** Persistence alone does not remove the contamination
(it is the difference between the `any` and `persistent` columns that persistence buys);
the genesis-relative onset criterion does.

Independently, **Catarina (2004; McTaggart-Cowan et al. 2006), Anita (2010) and Iba (2019;
Reboita et al. 2021) are not in this catalogue at all** — their genesis positions lie
outside the ARG / LA-PLATA / SE-BR boxes. The
catalogue was built for an extratropical-cyclone energetics study and by construction
cannot contain the known South Atlantic tropical systems. A tropical count of zero is
therefore the *correct* answer for this population, not a failure of the method.

**Which tropical threshold set to use.** The choice matters far less than the protocol.
C03's relaxed bound ($-V_T^U > -50$) is the better-justified one physically — Reboita
et al. (2024) show South Atlantic tropical systems with moderately warm upper cores, and
it more than doubles the tropical count under the permissive rules (1,334 vs 767 under
`type_any`). But under the strict rule C03 and C01 both give zero. **The relaxed tropical
threshold changes how much seclusion contamination is admitted, not how many tropical
cyclones are found.**

### S3. EP × thermal type — the association reverses with strictness — **[IMPORTANT]**

**Under the permissive rules, EP2 leads.** GOZZO14 `type_any` (n = 3,812;
$\chi^2 = 79.7$, dof = 6, $p = 4.2\times10^{-15}$, Cramér's V = 0.102):

| | Tropical | Subtropical | Extratropical |
|---|---|---|---|
| **EP1** (n=441) | 39 (**8.8%**) | 245 (55.6%) | 156 (35.4%) |
| **EP2** (n=978) | 241 (**24.6%**) | 490 (50.1%) | 244 (24.9%) |
| **EP3** (n=2,393) | 359 (**15.0%**) | 1,210 (50.6%) | 818 (34.2%) |

`EP2 × tropical` $z = +6.0$, `EP1 × tropical` $z = -4.1$. The ordering EP2 > EP3 > EP1
survives stratification by genesis region (see §4).

**Under the strict rule, the ordering inverts.** GOZZO14 `type_strict`:

| | Subtropical | Extratropical | Unclassified |
|---|---|---|---|
| **EP1** | 1 (**0.2%**) | 94 (21.3%) | 346 (78.5%) |
| **EP2** | 4 (**0.4%**) | 224 (22.9%) | 750 (76.7%) |
| **EP3** | 59 (**2.5%**) | 320 (13.4%) | 2,014 (84.2%) |

`EP3 × subtropical` $z = +3.0$, `EP2 × subtropical` $z = -3.1$.

The strict rule gates on genesis latitude, and the EPs draw unequally from the 20°–40°S
band (EP1 44%, EP2 53%, EP3 38% of their populations), so the raw comparison mixes the
structural signal with the geographic gate. **Conditioning on cyclones that pass the gate**
removes it:

| | strict subtropical / in band | rate |
|---|---|---|
| **EP1** | 1 / 193 | 0.52% |
| **EP2** | 4 / 518 | 0.77% |
| **EP3** | 59 / 908 | **6.50%** |

EP3 vs EP1+EP2 pooled: **odds ratio 9.81, Fisher exact $p = 1.8\times10^{-10}$.**

**The mechanism is the onset timing.** Among cyclones in the band that reach a persistent
hybrid spell at all:

| | n | median onset | within 24 h |
|---|---|---|---|
| **EP1** | 19 | 96 h | 5.3% |
| **EP2** | 100 | 81 h | 4.0% |
| **EP3** | 188 | **45 h** | **31.4%** |

**EP1 and EP2 acquire hybrid structure late (~80–96 h after genesis); EP3 acquires it
early.** So the two results are not in conflict — they describe different things:

- **EP2 more often *acquires* a warm core**, but does so mid-to-late in the life cycle,
  after a baroclinic development. That is transitional / seclusion-like structure.
- **EP3 more often *is born* hybrid.** These are the subtropical cyclones *sensu stricto*.

This is physically coherent. EP3 is characterised in the clustering as *weak energetics
representing typical "day-to-day" cyclones* — and weak baroclinic conversion is precisely
what a subtropical cyclone has, being diabatically rather than baroclinically driven. EP1
and EP2, with their large $C_a$/$C_k$ signatures, are vigorously baroclinic systems, which
is the regime that maintains an asymmetric cold core and then occludes into a seclusion.

**[PRELIMINARY]** — this interpretation is a structural correlation, not a demonstrated
mechanism, and the strict-rule cells for EP1 and EP2 hold single-digit counts.

### S4. Robustness

**Genesis region.** The permissive-rule EP2 enrichment survives in every genesis region,
and is strongest in SE-BR (`type_any`, GOZZO14, % tropical):

| Region | n | EP1 | EP2 | EP3 | $\chi^2$ | $p$ | V |
|---|---|---|---|---|---|---|---|
| ARG | 2,254 | 9.3% | **23.4%** | 16.7% | 64.6 | $5\times10^{-12}$ | 0.120 |
| LA-PLATA | 811 | 11.1% | **27.9%** | 13.9% | 29.8 | $4\times10^{-5}$ | 0.135 |
| SE-BR | 747 | 4.7% | **23.2%** | 10.4% | 53.5 | $9\times10^{-10}$ | 0.189 |

It is therefore not explained by EP2's more equatorward genesis distribution (median
genesis latitude −37.9°S, vs −42.1° for EP1 and −44.0° for EP3).

**Threshold set.** The strict-rule reversal reproduces under the cross-basin sets — e.g.
YANASE14 `type_strict` subtropical: EP1 = 2, EP2 = 4, EP3 = 31.

### S5. Distributions

**Subtropical cyclones are longer-lived, more intense and larger** than extratropical ones
(`type_persistent`, EP-labelled population; Kruskal–Wallis across types, all
$p < 10^{-37}$):

| | n | lifetime | max \|vorticity\| [10⁻⁵ s⁻¹] | max gale radius | longest hybrid spell |
|---|---|---|---|---|---|
| extratropical | 2,008 | 105 h | 7.4 | 874 km | 3 h |
| subtropical | 628 | **148 h** | **8.5** | **918 km** | **48 h** |
| unclassified | 1,163 | 72 h | 6.4 | 762 km | 6 h |

extratropical vs subtropical: lifetime $p = 3\times10^{-49}$ (rank-biserial $r = +0.39$),
vorticity $p = 1.6\times10^{-13}$ ($r = +0.20$).

**Seasonality differs sharply between EPs** (subtropical class, % of each EP's subtropical
cyclones by season of genesis):

| | DJF | MAM | JJA | SON | n |
|---|---|---|---|---|---|
| **EP1** | 11.7% | 30.0% | **41.7%** | 16.7% | 60 |
| **EP2** | 23.9% | 26.6% | 19.1% | **30.3%** | 188 |
| **EP3** | **40.5%** | 22.9% | 17.6% | 18.9% | 380 |

EP3's subtropical cyclones peak in austral summer — the season Gozzo et al. (2014)
identify for South Atlantic subtropical cyclogenesis — while EP1's peak in winter. This is
consistent with §3: EP3 holds the genuinely subtropical population, EP1 the
baroclinic-then-seclusion one, which follows the winter storm track. **[PRELIMINARY]** —
EP1's n = 60 makes its seasonal percentages noisy.

**Interannual.** Subtropical 19.0 ± 4.6 per year (range 11–33), extratropical 66.4 ± 10.1,
under `type_persistent`. No visually obvious trend in the 5-year running means.

**Persistence.** EP2's advantage in hybrid persistence is concentrated below ~40 h and
vanishes beyond ~45 h: EP2 more often *reaches* hybrid structure but does not *sustain* it
longer than EP3 once it gets there (median longest hybrid spell among subtropical
cyclones: EP1 48 h, EP2 45 h, EP3 49.5 h).

### S6. Validation against documented named cyclones

The Brazilian Navy Hydrographic Centre has named South Atlantic subtropical and tropical
cyclones since 2011, and several are documented in peer-reviewed case studies with explicit
genesis times and positions. Step 6 searches the catalogue for each and reports what our
classification says. A candidate track is accepted as the documented system only if its own
genesis lies within **600 km and 48 h** of the published one — a box search alone is far too
permissive (at 25°S, 7° of longitude is ~700 km).

| Case | Documented genesis | Status | Our label |
|---|---|---|---|
| **Bapo** | 18Z 4 Feb 2015, 26.0°S 43.5°W | **match** (332 km, 9 h) | **subtropical** ✓ |
| **Cari** | 00Z 8 Mar 2015, 26.25°S 45.0°W | **match** (254 km, 22 h) | **subtropical** ✓ |
| Eçaí | 00Z 4 Dec 2016, 26.5°S 47.5°W | no confident match | nearest candidate 1,300 km away |
| Guará | 00Z 9 Dec 2017, ~18°S 38°W | not in catalogue | genesis north of the SE-BR box |
| Anita | 06Z 4 Mar 2010, 19.75°S 34.75°W | not in catalogue | genesis north of the boxes |
| Arani | 12Z 8 Mar 2011, 24.0°S 41.25°W | not in catalogue | genesis east of the boxes |
| Deni | 00Z 15 Nov 2016, 23.0°S 42.5°W | not in catalogue | genesis east of the boxes |
| Iba | 23 Mar 2019, ~20°S 36°W | not in catalogue | genesis north of the boxes |
| Catarina | ~20 Mar 2004, ~29°S 45°W | not in catalogue | see below |
| Raoni | 18Z 26 Jun 2021 | out of period | catalogue ends with 2020 genesis |
| Yakecan | 16 May 2022 | out of period | |
| Akará | 12Z 15 Feb 2024 | out of period | |
| Biguá | 18Z 14 Dec 2024 | out of period | |

**Both testable named subtropical cyclones are classified subtropical**, and both under the
sustained rules (Bapo also under the full strict rule). The sample is small — only two of
the thirteen documented cases are actually testable — but it is a genuine external check
that the classification is not systematically wrong.

**Catarina is definitively absent.** During its hurricane phase (22–29 March 2004) the
nearest catalogue track is **1,634 km away**. It is not a matching failure; the system is
simply not in the track set.

**Why so many named systems are missing.** The catalogue's three genesis boxes
(ARG 55–39°S/70–50°W, LA-PLATA 38–23°S/69–52°W, SE-BR 38–23°S/52–37°W) were drawn for an
extratropical-cyclone energetics study. Named subtropical and tropical systems in the South
Atlantic form preferentially **north and east of them** — Anita at 19.75°S, Iba at ~20°S,
Guará at ~18°S all lie north of the 23°S boundary. This is a structural property of the
population, not a defect in the classification, and it reinforces the point in §2: **the
counts here describe thermal structure within an extratropical catalogue, not a subtropical
or tropical climatology of the basin.**

The four cases postdating the catalogue (Raoni, Yakecan, Akará, Biguá) are listed for
completeness and would be the natural targets if the track set is ever extended past 2020.
Note that the Yakecan and Biguá dates come from Brazilian Navy / METAREA V records rather
than from a peer-reviewed study, and are flagged as such in the code.


---

## What each finding decided

Each result above is the reason for a specific choice in the canonical analysis. The mapping
is listed in `README.md` of this folder, findings 1–9.

---

## References

Beven, J. L. (1997). A study of three "hybrid" storms. *Preprints, 22nd Conf. on Hurricanes
and Tropical Meteorology*, Amer. Meteor. Soc., 645-646. [cited via Gozzo et al. 2014]

Braun, S. A. (2010). Reevaluating the role of the Saharan air layer in Atlantic tropical
cyclogenesis and evolution. *Mon. Wea. Rev.*, **138**(6), 2007-2037.
doi:[10.1175/2009MWR3135.1](https://doi.org/10.1175/2009MWR3135.1)
[Gozzo et al. 2014 cite this work as "Braun 2009"; the published year is 2010.]

Cavicchia, L., Pepler, A., Dowdy, A., & Walsh, K. (2019). A physically based climatology of
the occurrence and intensification of Australian east coast lows. *J. Climate*, **32**(10),
2823-2841. doi:[10.1175/JCLI-D-18-0549.1](https://doi.org/10.1175/JCLI-D-18-0549.1)

Conrado, E. T. de C., da Rocha, R. P., Reboita, M. S., & Cardoso, A. A. (2024). Cyclone
classification over the South Atlantic Ocean in centenary reanalysis. *Atmosphere*,
**15**(12), 1533. doi:[10.3390/atmos15121533](https://doi.org/10.3390/atmos15121533)

Davis, C. A., & Bosart, L. F. (2004). The TT problem: Forecasting the tropical transition of
cyclones. *Bull. Amer. Meteor. Soc.*, **85**(11), 1657-1662.
[bibliographic details as given in the reference list of Reboita et al. 2024]

Evans, J. L., & Braun, A. (2012). A climatology of subtropical cyclones in the South
Atlantic. *J. Climate*, **25**(21), 7328-7340.
doi:[10.1175/JCLI-D-11-00212.1](https://doi.org/10.1175/JCLI-D-11-00212.1)

Evans, J. L., & Guishard, M. P. (2009). Atlantic subtropical storms. Part I: Diagnostic
criteria and composite analysis. *Mon. Wea. Rev.*, **137**(7), 2065-2080.
doi:[10.1175/2009MWR2468.1](https://doi.org/10.1175/2009MWR2468.1)

Gozzo, L. F., da Rocha, R. P., Reboita, M. S., & Sugahara, S. (2014). Subtropical cyclones
over the southwestern South Atlantic: Climatological aspects and case study. *J. Climate*,
**27**(22), 8543-8562.
doi:[10.1175/JCLI-D-14-00149.1](https://doi.org/10.1175/JCLI-D-14-00149.1)

Guishard, M. P., Evans, J. L., & Hart, R. E. (2009). Atlantic subtropical storms. Part II:
Climatology. *J. Climate*, **22**(13), 3574-3594.
doi:[10.1175/2008JCLI2346.1](https://doi.org/10.1175/2008JCLI2346.1)

Hart, R. E. (2003). A cyclone phase space derived from thermal wind and thermal asymmetry.
*Mon. Wea. Rev.*, **131**(4), 585-616.
doi:[10.1175/1520-0493(2003)131<0585:ACPSDF>2.0.CO;2](https://doi.org/10.1175/1520-0493(2003)131%3C0585:ACPSDF%3E2.0.CO;2)

Hart, R. E., & Evans, J. L. (2001). A climatology of the extratropical transition of
Atlantic tropical cyclones. *J. Climate*, **14**(4), 546-564.
[cited via Guishard et al. 2009]

Marrafon, V. H., Reboita, M. S., da Rocha, R. P., & de Jesus, E. M. (2022). Classificacao
dos tipos de ciclones sobre o Oceano Atlantico Sul em projecoes com o RegCM4 e MCGs.
*Rev. Bras. Climatol.*, **30**, 1-25.
doi:[10.55761/abclima.v30i18.14603](https://doi.org/10.55761/abclima.v30i18.14603)

McTaggart-Cowan, R., Bosart, L. F., Davis, C. A., Atallah, E. H., Gyakum, J. R., &
Emanuel, K. A. (2006). Analysis of Hurricane Catarina (2004). *Mon. Wea. Rev.*, **134**(11),
3029-3053. doi:[10.1175/MWR3330.1](https://doi.org/10.1175/MWR3330.1)

Reboita, M. S., Crespo, N. M., Dutra, L. M. M., Silva, B. A., Capucin, B. C., &
da Rocha, R. P. (2021). Iba: The first pure tropical cyclogenesis over the western South
Atlantic Ocean. *J. Geophys. Res. Atmos.*, **126**(1), e2020JD033431.
doi:[10.1029/2020JD033431](https://doi.org/10.1029/2020JD033431)

Reboita, M. S., Nogueira, N. C. de O., Gomes, I. B. dos S., Palma, L. L. da C., &
da Rocha, R. P. (2024). Assessment of a tropical transition over the southwestern South
Atlantic Ocean: The case of cyclone Akara. *J. Mar. Sci. Eng.*, **12**(11), 1934.
doi:[10.3390/jmse12111934](https://doi.org/10.3390/jmse12111934)

Shapiro, M. A., & Keyser, D. (1990). Fronts, jet streams and the tropopause. In
*Extratropical Cyclones: The Erik Palmen Memorial Volume*, Amer. Meteor. Soc., 167-191.
[cited via Hart 2003]

Wood, K., Yanase, W., Beven, J., Camargo, S. J., Courtney, J. B., Fogarty, C., Fukuda, J.,
Kitabatake, N., Kucas, M., McTaggart-Cowan, R., et al. (2023). Phase transitions between
tropical, subtropical, and extratropical cyclones: A review from IWTC-10.
*Trop. Cyclone Res. Rev.*, **12**(4), 294-308.
doi:[10.1016/j.tcrr.2023.11.002](https://doi.org/10.1016/j.tcrr.2023.11.002)

Yanase, W., Niino, H., Hodges, K., & Kitabatake, N. (2014). Parameter spaces of
environmental fields responsible for cyclone development from tropics to extratropics.
*J. Climate*, **27**(2), 652-671.
doi:[10.1175/JCLI-D-13-00153.1](https://doi.org/10.1175/JCLI-D-13-00153.1)

---
