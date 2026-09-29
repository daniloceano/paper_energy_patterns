# Scientific Notes — Cyclone Phase Space (CPS) Analysis

Thermal-structure classification of the South Atlantic cyclone population using the
Hart (2003) Cyclone Phase Space, and its cross-reference with the Energy Patterns
(EP1/EP2/EP3) derived from the Lorenz Energy Cycle clustering.

CPS computation: **Andres Rodriguez (IAG-USP)**.
Classification, cross-reference and these notes: **Danilo Couto de Souza**.

> **This document is the canonical record — the analysis of record.** The exploratory suite
> that established this design (six threshold sets × four identification rules, the
> warm-seclusion diagnosis, the documented-case check) has its own science notes at
> `sensitivity/SCIENTIFIC_NOTES.md`. Nothing in this file depends on reading that one;
> where a canonical choice was forced by a sensitivity result, the result is quoted here
> and the finding number given.

---

## Table of Contents

- [Research Questions](#research-questions)
- [Physical / Statistical Framework](#physical--statistical-framework)
- [Datasets and Variables](#datasets-and-variables)
- [Methodology](#methodology)
- [Assumptions](#assumptions)
- [Canonical Results](#canonical-results)
- [Caveats and Limitations](#caveats-and-limitations)
- [Next Steps](#next-steps)
- [References](#references)

---

## Research Questions

1. What is the thermal-structure composition (extratropical / subtropical / tropical) of
   the South Atlantic cyclone population studied here, when the Hart (2003) Cyclone Phase
   Space is applied to every timestep of every track?

2. **Does that composition differ between the three Energy Patterns?** Specifically: are
   cyclones with a given LEC signature (EP1 high conversions, EP2 moderate/importing, EP3
   weak) more or less likely to *be* — or to *become* — hybrid or warm-core systems?

3. How sensitive are the answers to (a) the choice of CPS thresholds, given that the
   literature offers several non-equivalent sets, and (b) the identification protocol
   layered on top of them (persistence, geography, timing relative to genesis)?

Question 2 is the motivating one. It asks whether the *energetics* classification and the
*thermal structure* classification of a cyclone are related — two independent descriptions
of the same population.

The distinction in question 2 between *being* and *becoming* is not cosmetic; it turned out
to be the analysis's main result. A cyclone that is hybrid from genesis and one that
acquires a warm core after 80 h of baroclinic development are different physical objects,
and the CPS assigns them the same label. Separating them requires the timing criterion of
Guishard et al. (2009), described under Methodology.

---

## Physical / Statistical Framework

### The Cyclone Phase Space

Hart (2003) describes cyclone structure with three parameters computed from the
three-dimensional geopotential field alone.

**(1) Storm-motion-relative thickness asymmetry**, Hart (2003) Eq. (2):

$$
B = h\left[ \overline{(Z_{600} - Z_{900})}\Big|_R - \overline{(Z_{600} - Z_{900})}\Big|_L \right]_{500\ \mathrm{km}}
$$

where $Z$ is isobaric geopotential height, $R$ and $L$ denote the semicircles to the right
and left of storm motion, the overbar is the areal mean over a 500-km-radius semicircle,
and the integer $h = +1$ in the Northern Hemisphere and $h = -1$ in the Southern
Hemisphere. Units: geopotential metres.

$B > 0$ means the cyclone is thermally asymmetric — a frontal structure, with warm
advection downstream of the motion vector. $B \simeq 0$ means a non-frontal, thermally
symmetric system.

**(2) and (3) Layer thermal winds**, Hart (2003) Eqs. (5) and (6). Defining
$\Delta Z = (Z_{\max} - Z_{\min})_p$ as the magnitude of the horizontal geopotential-height
gradient within 500 km of the centre on isobaric surface $p$:

$$
-|V_T^L| = \left.\frac{\partial(\Delta Z)}{\partial \ln p}\right|_{900\ \mathrm{hPa}}^{600\ \mathrm{hPa}},
\qquad
-|V_T^U| = \left.\frac{\partial(\Delta Z)}{\partial \ln p}\right|_{600\ \mathrm{hPa}}^{300\ \mathrm{hPa}}
$$

Each derivative is obtained by ordinary least squares on the vertical profile of
$\Delta Z$ against $\ln p$. Hart interpolates to a **50-hPa increment, giving seven
pressure levels** per regression.

> "Positive values of $-V_T$ indicate a warm-core cyclone within the layer, while negative
> values of $-V_T$ indicate a cold-core cyclone within the layer." — Hart (2003)

The three parameters place a cyclone in a continuum rather than in discrete boxes
(Beven 1997, as discussed by Gozzo et al. 2014); Wood et al. (2023) review the phase
transitions between the classes across basins. Stereotypically:

| Type | $B$ | $-V_T^L$ | $-V_T^U$ | Structure |
|---|---|---|---|---|
| Extratropical | $\gg 0$ | $< 0$ | $< 0$ | asymmetric, cold core through the troposphere |
| Subtropical | small | $> 0$ | $< 0$ | non-frontal, **low-level warm core, upper cold core** (hybrid) |
| Tropical | $\simeq 0$ | $> 0$ | $> 0$ | symmetric, warm core surface to tropopause |

Gozzo et al. (2014) state this directly:

> "CPS parameters are defined so that for an extratropical cyclone, $B \gg 0$,
> $-V_T^L < 0$, and $-V_T^U < 0$ [...] and for a tropical cyclone $B \simeq 0$,
> $-V_T^L > 0$, and $-V_T^U > 0$ [...] The SCs are nonfrontal, with small values of $B$
> [...] and present a low-level warm core and an upper-level cold core, implying
> $-V_T^L > 0$ and $-V_T^U < 0$."

**Reading the diagrams.** Every CPS figure shades the projection of each canonical class
onto the plane drawn — blue extratropical, green subtropical, red tropical, at high
transparency. Grey marks where more than one class can claim a point, which happens because
the specs overlap by construction; there the timestep precedence decides. Blank corners
belong to no cyclone type. `figures/cps_analysis/fig0_cps_reference.png` is the schematic
alone, without data.

**Sign convention used throughout this analysis.** The columns named `VTL` and `VTU` hold
Hart's *signed* $-V_T^L$ and $-V_T^U$, i.e. the slope itself, so that **positive means warm
core**. This is the quantity plotted on every CPS diagram in the cited literature.

### Threshold values

One threshold set is used, stated in the next subsection. Six further sets — three South
Atlantic and three cross-basin controls — were tested to establish that choice; they are
tabulated and discussed in `sensitivity/SCIENTIFIC_NOTES.md` and are not repeated here.

Provenance of the individual numbers:

- **$|B| = 10$ m** separates frontal from non-frontal. Hart (2003): *"A convenient and
  physically sound threshold for distinguishing a tropical thermal gradient from a
  nontropical thermal gradient is $B = 10$ m [...] no major hurricane (winds of greater
  than 115 kt) had associated with it a value of $B$ that exceeded 10 m."*

- **The Gozzo subtropical set.** Gozzo et al. (2014), section 2c, criterion 2, verbatim:
  *"It presents horizontal thermal symmetry and hybrid structure for more than 36
  consecutive hours. Both conditions are diagnosed by using the CPS parameters, with
  $B < 25$ m, $-V_T^U < -10$ and $-V_T^L > -50$."*
  The $-V_T^L$ bound is deliberately relaxed from the North Atlantic value of $-10$
  (Evans and Guishard 2009) because *"the CPS can sometimes give a very low or negative
  value of this parameter even for pure tropical cyclones (Braun 2009)"*. The identical
  set is quoted for the South Atlantic by Reboita et al. (2024).

- **The relaxed tropical bound $-V_T^U > -50$.** Justified physically by Reboita et al.
  (2024), discussing Akará: *"Some studies [...] have shown tropical cyclones with a
  moderately warm core, even with $-60 < -|V_T^U| < 10$, which means that the vertical
  wind shear between 300 and 600 hPa is not so weak compared to the classical
  definition."*

### The identification protocol beyond thresholds

A threshold set alone does not identify a cyclone type. Guishard et al. (2009) list five
**required characteristics** of an Atlantic subtropical storm, and Gozzo et al. (2014)
carry the same structure into the South Atlantic. Three are transcribed below.

> **Which of them the CANONICAL pipeline enforces.** (i) and (ii), plus the ocean clause
> and a warm-seclusion guard on the timing of each hybrid run. (iii) is deliberately NOT a
> gate — it selects systems *born* hybrid and so excludes transitions by construction, which
> would be a category error applied to the `ST` class; it is kept as the descriptive flag
> `pure_genesis`. See caveat C-xi for the history: (ii) was absent until it was added, and
> the counts in this document are post-guard.

**(i) Persistence — 36 consecutive hours.** *Enforced.* Guishard et al. (2009): the cyclone
must *"persist in its hybrid form for at least 36 h (i.e., more than one diurnal cycle)"*.
Gozzo et al. (2014): *"for more than 36 consecutive hours"*.

**(ii) Genesis latitude band — 20°–40°.** *Enforced (`SC_REQUIRE_GENESIS_BAND`).*
Guishard et al. (2009): *"attain gales in the
20°–40°N latitude band to reduce the possibility of tropical and extratropical systems
being introduced into the dataset"*. Gozzo et al. (2014), criterion 1: *"The SC forms
between 20° and 40°S."* Applied to the cyclone, since it is a statement about
cyclogenesis. In the coverage-eligible population it rejects 386 of 784 persistent hybrid
runs.

**(iii) Onset within 24 h of genesis — the anti-warm-seclusion criterion.**
*Recorded as `pure_genesis`, deliberately not a gate.* It is a filter on the TYPE OF
GENESIS: it selects cyclones that were **born** hybrid, and therefore excludes transitions
by design. A cyclone reaching a persistent subtropical state after a persistent
extratropical one cannot satisfy it under any circumstances, so using it to judge `ST`
would be a category error. The warm-seclusion problem it was meant to solve is handled
instead by the intensity-peak guard (iv).
Guishard et al. (2009): the cyclone must *"become subtropical (i.e., attain hybrid
structure) within 24 h if identified first as a purely cold- or warm-cored system"*, with
the rationale stated verbatim:

> "Systems that begin as robust tropical or extratropical cyclones have been rejected
> because they are deemed in this methodology to only be able to attain the hybrid
> structure via extratropical transition (ET; Hart and Evans 2001) or tropical transition
> (Davis and Bosart 2003), respectively."

Gozzo et al. (2014), criterion 3: the thresholds must be attained *"within 24 h after its
genesis if first tracked as an extratropical system"*.

**This is the criterion that does the work.** Persistence alone cannot separate a genuine
hybrid genesis from a warm core acquired late in a baroclinic life cycle, because a
Shapiro–Keyser warm seclusion routinely persists well beyond 36 h. What distinguishes them
is *when* the warm core appears: for a subtropical or tropical-transition system the hybrid
structure **is** the genesis mechanism (Davis and Bosart 2004), whereas a seclusion forms
at or after occlusion, having begun as a robust cold-core system.

Cavicchia et al. (2019), working on a mid-latitude population directly comparable to ours,
state the underlying limitation outright:

> "cyclone phase space alone does not distinguish tropical cyclones from warm-seclusion
> extratropical cyclones (Hart 2003)."

**Not implemented:** Guishard et al.'s gale-force wind requirement (Gozzo et al.
deliberately dropped it for the South Atlantic, *"the reasoning behind this is the abundant
occurrence of shallow cyclonic systems [...] that do not reach sustained winds of
17 m s⁻¹ but may cause notable weather events"*), and Gozzo et al.'s manual rejection step
by visual inspection of geopotential-height-anomaly and 925-hPa temperature fields.

### Statistical framework

EP × type contingency tables are tested with the **chi-square test of independence**,
with **Cramér's V** as effect size and **Pearson standardised residuals**
$z_{ij} = (O_{ij} - E_{ij}) / \sqrt{E_{ij}}$ identifying which cells drive any departure
from independence ($|z| > 2$ flagged). Cochran's condition (expected counts $\ge 5$) is
checked and violations are reported explicitly.

Because the official EP populations are very unequal (482 / 767 / 2,141), **counts are always
reported alongside within-EP percentages**; only the percentages are comparable across EPs.

Genesis-region stratification is used as a confounding control (see Results).

**Interval on a proportion — Wilson score.** A within-EP frequency $\hat p = k/n$ is
reported with the Wilson score interval, obtained by inverting the score test
$|\hat p - p| \big/ \sqrt{p(1-p)/n} \le z$ and solving the resulting quadratic in $p$:

$$p_\pm=\frac{\hat p+\dfrac{z^2}{2n}\;\pm\;z\sqrt{\dfrac{\hat p(1-\hat p)}{n}+\dfrac{z^2}{4n^2}}}{1+\dfrac{z^2}{n}},
\qquad z = 1.95996 \;\;(95\%)$$

The standard error uses the hypothesised $p$, not the observed $\hat p$, which is what
distinguishes it from the textbook Wald interval $\hat p \pm z\sqrt{\hat p(1-\hat p)/n}$.
The interval is asymmetric and its centre is pulled slightly toward $1/2$. Wald is not
used because it fails in exactly the regime this analysis lives in: for the sparse classes
(`TC` with 2 members, `SD` with 22) it can return lower limits below zero, which is not a
possible frequency.

**Contrast on a single class — Fisher exact.** Each EP is tested against the **other two
pooled**, a $2\times2$ table. Conditioning on all four margins, the count in the focal cell
follows the hypergeometric distribution

$$P(X=a)=\frac{\binom{K}{a}\binom{M-K}{N-a}}{\binom{M}{N}}$$

with $M$ the total, $K$ the class total and $N$ the EP size; the two-sided $p$ sums every
table whose probability does not exceed the observed one. The effect size reported is the
sample odds ratio $ad/bc$. Fisher is used consistently for every focal contrast, including
the sparse cells where Cochran's condition fails, so the test is not selected after seeing
the result.

**Ratios against EPALL are descriptive, not inferential.** Where a frequency is expressed
relative to the pooled population, EPALL is the coverage-eligible union
EP1 + EP2 + EP3 = 3,390 — not the 6,789-track catalogue. Each EP is
therefore **nested in its own denominator**, and the ratio cannot be read as an independent
comparison or given a $p$-value. The interval drawn on such a ratio is the Wilson interval
of the numerator divided by the EPALL point estimate, i.e. it carries the sampling
uncertainty of the EP alone. All inference comes from the EP-versus-other-two contrast.

**Multiple comparisons — Holm.** Where a family of contrasts is tested together, the
$p$-values are corrected by the Holm step-down procedure: sorted ascending, each
$p_{(i)}$ is compared against $\alpha/(m-i+1)$, stopping at the first failure. Equivalently
$p^{\text{adj}}_{(i)} = \max_{j\le i}\,(m-j+1)\,p_{(j)}$, capped at 1. Holm controls the
family-wise error rate and is uniformly more powerful than Bonferroni, which it never
rejects less than. The motivation is quantitative: with $m = 9$ contrasts and all nulls
true, $0.45$ nominally significant results are expected by chance alone, so an isolated
$p < 0.05$ among nine carries no evidential weight. Corrected and uncorrected $p$ are
**both** reported, and figures encode them separately — star level from the raw $p$, marker
fill from Holm survival — so that a corrected result never looks weaker than an
uncorrected one.

---

## Datasets and Variables

**ERA5 reanalysis** — geopotential ($z$) and horizontal wind ($u$, $v$) on pressure levels,
storm-following subsets extracted around each track. Used by the CPS calculator to produce
$B$, $-V_T^L$, $-V_T^U$ and `SIZE`. The per-cyclone NetCDF subsets were **not retained**
after processing; only the derived CSVs survive.

**Cyclone tracks** — `tracks_SAt_filtered_with_periods.csv`, the canonical track set of this
project: 6,789 cyclones, 1979–2020, tracked on 850-hPa relative vorticity, hourly, with a
life-cycle period label (incipient / intensification / mature / decay / residual) and a
genesis-region label. Genesis-region boxes:

| Region | Latitude | Longitude |
|---|---|---|
| ARG | 55°S – 39°S | 70°W – 50°W |
| LA-PLATA | 38°S – 23°S | 69°W – 52°W |
| SE-BR | 38°S – 23°S | 52°W – 37°W |

**Energy Patterns** — `results/cluster/kmeans_clustered_data.csv`, K-Means ($k=3$) on the
corrected PCA of LEC diagnostics; 3,820 cyclones. Mapping
(`scripts/utils/ep_mapping.py`): cluster 2 → EP1 (548), cluster 0 → EP2 (860),
cluster 1 → EP3 (2,412).

**Derived variables**

| Variable | Units | Description |
|---|---|---|
| `B` | gpm | $B_\text{left} - B_\text{right}$, i.e. Hart's $B$ with $h = -1$ |
| `VTL` | gpm/ln(p) | Hart's $-V_T^L$, 900–600 hPa; positive = low-level warm core |
| `VTU` | gpm/ln(p) | Hart's $-V_T^U$, 600–300 hPa; positive = upper warm core |
| `SIZE` | km | equivalent radius of the area with 925-hPa wind $\ge 17$ m s⁻¹ |
| `over_ocean` | bool | Natural Earth 110 m land polygons |

**Sampling.** CPS is 3-hourly; tracks are hourly. Every CPS timestamp in all 6,776 source
files matched its reference trajectory exactly, with unique, strictly increasing time axes;
the normal cadence is 3 h with an optional terminal 2 h interval.

---

## Methodology

### Step 1 — Consolidation

The 6,776 per-cyclone CSVs are concatenated; the GrADS sentinel `-999000000` is masked;
$B$ is formed as `B_left - B_right`, which applies the Southern Hemisphere factor $h=-1$;
track metadata and corrected EP labels are joined. Coverage is then computed against all
6,789 reference trajectories, including the 13 without a CPS file.

**Full-life coverage.** The denominator is the complete hourly-track duration from genesis
to track end. The numerator is the sum of CPS interval durations whose **ending** timestamp
has finite $B$, $-V_T^L$ and $-V_T^U$. The genesis sentinel contributes zero duration;
hours before the first CPS timestamp, after the last CPS timestamp, and intervals ending in
unusable values are uncovered. This duration-based definition, rather than a row-count
fraction, is the official gate: coverage $\ge 75\%$ is included; lower coverage is excluded;
zero usable duration is `no_data`, never `undetermined`.

**Sign-convention verification.** Over 178,651 classifiable timesteps in the official
population, median $B = +25.3$ m (72.5% with $B > 10$ m), median $-V_T^L = -111.3$,
and median $-V_T^U = -191.2$ (only 2.9% positive). A predominantly frontal, cold-core population is
exactly what an extratropical track catalogue should produce, confirming the sign handling.

**Implementation check against Hart (2003).** The calculator uses `LEVS_VTL = [900, 850,
800, 750, 700, 650, 600]` and `LEVS_VTU = [600, 550, 500, 450, 400, 350, 300]` — seven
levels at 50-hPa spacing, matching Hart's prescription exactly; a 500-km radius for both
$B$ and $\Delta Z$, matching Hart's Eqs. (2), (5), (6); and OLS regression of $\Delta Z$ on
$\ln p$. The implementation is faithful to the original formulation.

### Step 2 — Classification

Each classifiable timestep is tested against the three class definitions of each threshold
set. **The classes overlap by construction** (evident in Conrado et al. 2024, Fig. 2b), so
a precedence order is imposed: **tropical > subtropical > extratropical**. Timesteps
satisfying none of the three — the "warm tilted", "cold shallow" and "warm symmetrical"
corners that Conrado et al. name but do not assign to a cyclone type — are labelled
`unclassified`.

Four cyclone-level aggregation rules are produced, in increasing strictness:

| Rule | Definition | Reading |
|---|---|---|
| `type_any` | most tropical class attained at **any single timestep** | most permissive; mirrors *"systems that in any time of their lifecycle obtained tropical features"* (Conrado et al. 2024). Very sensitive to single-timestep noise. |
| `type_persistent` | class held for **≥ 36 consecutive hours** | the persistence requirement of Guishard et al. (2009) and Gozzo et al. (2014), applied to all three classes so the comparison is like-for-like. Used for distributional work, where sample size matters. |
| `type_protocol` | + **over ocean**, genesis in **20°–40°S** | adds the geographic criteria |
| `type_strict` | + qualifying run **begins ≤ 24 h after genesis** | the full protocol of Guishard et al. (2009) / Gozzo et al. (2014). **This is the identification rule; the others are diagnostics of it.** |

A run of $k$ contiguous samples spanning $t_0 \dots t_1$ is credited with $t_1 - t_0$ hours;
an isolated timestep counts as 0 h. Runs break across time gaps $> 3.5$ h. The onset used by
`type_strict` is the start of the **first run that itself satisfies the 36-h requirement** —
not the first isolated timestep of the class, which would be far noisier.

Since sampling is 3-hourly, the realisable spans are 0, 3, 6, … , 36, 39 h. Gozzo's
"*more than* 36 hours" is implemented as $\ge 36$ h; the next realisable value is 39 h, so
the distinction affects nothing.

**Two implementation notes on the onset criterion.**

*Conditionality.* Guishard et al. and Gozzo et al. phrase the 24-h bound conditionally —
it applies *"if identified first as a purely cold- or warm-cored system"* / *"if first
tracked as an extratropical system"*. Here it is applied unconditionally, which is
equivalent: a cyclone that is already hybrid at its first classifiable timestep has an
onset of 3 h and passes trivially. The conditional phrasing exists to make clear that the
criterion is not meant to penalise systems that were hybrid from the start.

*Application to all three classes.* Guishard et al. define the 24-h bound only for the
hybrid class. Extending it to the extratropical and tropical classes keeps the three
columns like-for-like, but it changes what those columns mean. **Under `type_protocol` and
`type_strict` the "extratropical" count is NOT a count of extratropical cyclones in the
basin** — it is the count of cyclones that are extratropical *and* form between 20°S and
40°S *and* over ocean. Since the ARG genesis box spans 39–55°S, most of the basin's
extratropical population is excluded by construction (2,607 → 991 → 810). Only the
within-EP *ratios* under a fixed rule are interpretable across EPs; the absolute
extratropical counts under the geographic rules are not a climatology.

### The canonical classification

One threshold set, one scheme. Thresholds follow **de Souza et al. (2026)**, verbatim:

> "systems are classified as extratropical when $B \gg 10$ m, $-|V_T^L| < 0$, and
> $-|V_T^U| < 0$; tropical when $B < 10$ m, $-|V_T^L| > 0$, and $-|V_T^U| > 0$
> (Wood et al., 2023). For subtropical cyclones over the South Atlantic Ocean, the
> thresholds are $-25 < B < 25$ m, $-|V_T^L| > -50$, and $-|V_T^U| < -10$
> (Gozzo et al., 2014, 2017; de Jesus et al., 2022; Cardoso et al., 2022)."

Note the **two-sided** $B$ bound for the subtropical class, consistent with the two-sided
symmetry definition of Evans and Hart (2003). It retains 97.2% of one-sided GOZZO14
subtropical timesteps here; the 2.8% removed sit at a median latitude of −46.2° and are
predominantly late-life-cycle (56.5% mature or decay).

**Persistence gate.** A class counts as a *state* of the cyclone only when held for
**≥ 36 consecutive hours** (Guishard et al. 2009, Gozzo et al. 2014). This is what makes
the scheme well-posed — see Sensitivity finding 7.

**Phase classes.**

| Code | Definition | Source for the name |
|---|---|---|
| `EC`/`SC`/`TC` | one persistent state for the whole life | — |
| `ST` | EC → SC | Reboita et al. (2022), Raoni: *"initially having extratropical features and later undergoing a subtropical transition"* |
| `SD` | SC → EC | named here; not an established term |
| `TT` | EC or SC → TC | Davis and Bosart (2003, 2004) |
| `ET` | TC → EC | Evans and Hart (2003) |
| `indeterminate` | no persistent state | cf. Yanase et al.'s (2014) explicit "ill-defined" class |

`ET` is deliberately **not** broadened to cover SC → EC. Evans and Hart (2003) define it
for tropical cyclones specifically — *"46% of Atlantic tropical storms undergo a process of
extratropical transition in which the storm evolves **from a tropical cyclone** to a
baroclinic system"* — with operational markers onset $B > 10$ m and completion
$-V_T^L < 0$, and a mean transition period of 33.4 h.

**The tropical-transition test.** Every persistent tropical run is a genuine `TT` only if
**either**:

the **tropical run itself** must lie **equatorward of 40°S** and be ≥ 50% over ocean.
Otherwise: **warm seclusion** (if preceded by an extratropical state) or **indeterminate
warm core**. Rejected runs are removed from the state sequence.

The preceding state (EC → TC or SC → TC) is **recorded as a pathway descriptor** but does
not bypass the test. An earlier version accepted any run preceded by a persistent
subtropical state, on the argument that the system had already demonstrated hybrid
structure — the Catarina route. Testing showed this does not discriminate: **the
Shapiro–Keyser occlusion sequence passes through hybrid structure on its way to the warm
seclusion** (cold core → hybrid → symmetric warm core), so "preceded by subtropical" is
what a seclusion does too. With a relaxed persistence gate that branch admitted seclusions
at 60.2°S and 56.9°S, while both plausible cases sat at 29°S and were caught by the
geographic test anyway.

**Only the poleward bound is applied.** Guishard et al. (2009) and Gozzo et al. (2014) use a
two-sided 20–40° band because they are building a *subtropical* climatology and the
equatorward bound keeps genuinely tropical systems out of it. For a tropical-transition test
that bound is not merely unnecessary but wrong — the further equatorward a warm core sits,
the more plausible it is as tropical. Iba, the first documented pure tropical cyclogenesis
in the western South Atlantic (Reboita et al. 2021), formed at about **20°S**, exactly on
the edge of that band. In this population the change is numerically inert (no tropical
timestep lies equatorward of 20°S) but it makes the rule correct for an extended catalogue.

Two implementation points, each forced by evidence rather than chosen:

1. **The geographic test is on the run, not on genesis.** Six of the sixteen persistent
   tropical runs belong to cyclones that formed *inside* the 20–40°S band, travelled ~30°
   poleward, and only then acquired a warm core at 55–62°S. A genesis-latitude gate passes
   every one of them (Sensitivity finding 4).

2. **The life-cycle phase of the run is recorded, never used as a gate.** It is close to
   tautological — a Shapiro–Keyser warm seclusion *is* the occluded stage — and a
   phase-only rule admits exactly one case, track **20160337 at −54.7°S**, independently
   confirmed from satellite imagery to be a classic extratropical cyclone (Sensitivity
   finding 5).

---

### Step 9 — Genesis and whole-life density

The classification answers *what* a cyclone is; step 9 asks *where*. Two position sets are
mapped for every phase class, separately for EPALL and each Energy Pattern:

| map | positions | quantity |
|---|---|---|
| genesis | the cyclogenesis point, one per cyclone | cyclogenesis events per $10^6$ km² per year |
| whole life | every 3-hourly position of the track | cyclone **days** per $10^6$ km² per year |

**Estimator.** Spherical kernel density estimation after Hoskins and Hodges (2005): Gaussian
kernel with a haversine metric, bandwidth $h = 0.05$ rad ($\approx 318$ km), evaluated on
their regular 2.5° grid. The KDE integrates to unity over the sphere, so

$$\rho(\lambda,\phi) \;=\; \hat{f}(\lambda,\phi)\; N \; \frac{10^6}{R^2} \; \frac{w}{n_{\text{years}}},
\qquad R = 6369.345\ \text{km},$$

with $N$ the number of positions and $w$ a weight that fixes the unit: $w = 1$ for genesis
events, and $w = \Delta t/24\ \text{h} = 1/8$ for the whole-life maps, which converts a count
of 3-hourly positions into **cyclone days** and so makes the number independent of the
sampling cadence. This is the same estimator, bandwidth and grid as the manuscript's genesis
figure, shared through `cps_density.py` so the two cannot drift apart.

**Two readings of the same field.** Absolute density carries the sample size — with EP1 at
482 cyclones and EP3 at 2,141, an EP1 panel is faint because EP1 is rare, not because its
cyclones form somewhere else. To separate the two, the EP panels are also drawn as the
min-max normalised anomaly $\tilde{\rho}_{\text{EP}} - \tilde{\rho}_{\text{EPALL}}$, where
$\tilde{\rho}$ scales the positive values of each field onto $[0,1]$. That comparison is of
**shape** only and says nothing about how many cyclones produced it; the absolute mode is
kept alongside precisely so the two questions are never conflated.

**Denominator.** EPALL is the coverage-eligible union EP1 ∪ EP2 ∪ EP3 = **3,390** cyclones,
not the 6,789-track catalogue — the same choice as step 8, and required here because the EP
panels are read against EPALL. The class counts in this section are therefore smaller than
those in C1 (e.g. `SC` 128 rather than 173).

**Whole life means whole life.** The track maps use every position of a cyclone of the given
class, not only the positions holding that structure. A single-state `SC` cyclone is
subtropical for a median 0.74 of its life (C2), so the remainder is in the map. For a
residence-time field that is the correct denominator — the question "where is the structure
held" is a different one, and it is what the phase-space figures answer.

**Minimum sample.** A panel with fewer than **10 cyclones** is drawn as raw positions with no
density field. The gate is on cyclones rather than positions because the 3-hourly positions of
one cyclone are not independent samples: `SC`/EP1 has 6 cyclones but 288 whole-track
positions, and a KDE over those positions would draw a smooth field out of only six
trajectories.

---

## Assumptions

1. **Raw, not smoothed, CPS values are classified.** The temporal smoothing in
   `cps_plots_csv_gris.py` (5-point centred rolling mean) is a plotting aid. The 36-h
   persistence requirement provides the equivalent noise control in a way that is
   explicit and reversible.

2. **Precedence tropical > subtropical > extratropical** resolves the class overlap. This
   is the convention of tropical-transition studies and maximises the tropical count; a
   different precedence would lower it.

3. **The 500-km CPS radius is appropriate for these systems.** Conrado et al. (2024) flag
   this themselves: *"the 500 km radius used to define the cyclone area in the CPS may not
   accurately represent meso-synoptic scale cyclones."* Many SE-BR systems are shallow and
   small.

4. **Track positions are cyclone centres for CPS purposes.** The tracking uses 850-hPa
   relative vorticity maxima, whereas Hart used MSLP minima and Gozzo et al. used 925-hPa
   vorticity. For tilted baroclinic systems the vorticity centre and the surface centre can
   differ by 1–2° early in the life cycle.

5. **EP membership is a fixed, exogenous label.** The clustering was performed on LEC
   diagnostics with no knowledge of thermal structure, so the two classifications are
   genuinely independent — which is what makes the cross-reference meaningful.

6. **A land/ocean mask at 110 m resolution is adequate** for the coarse "over ocean"
   criterion. Coastal systems within ~50 km of the coastline may be misassigned.

7. **Genesis in the track record is genesis of the system.** The onset criterion measures
   time from the first tracked position. If the tracking picks up a system late — after it
   has already developed — the measured onset is biased low and a seclusion could pass the
   24-h test. Conversely, if a pre-existing disturbance is tracked early, the onset is
   biased high. Both would blur the early/late separation rather than create it, so the
   very clean separation actually observed (median 51 h for EP3 vs 81–86 h for EP1/EP2)
   is unlikely to be a tracking artefact.

8. **The `period` labels (incipient / intensification / mature / decay) are taken as
   given** from the project's life-cycle segmentation, which is vorticity-based and
   independent of the CPS. This independence is what makes the phase-composition
   diagnostic in step 4 informative rather than circular.

---

## Canonical Results

Population: **6,789 reference tracks**, genesis years 1979–2020 (42 years). There are
**6,776 CPS files**; **6,157 cyclones** pass the official $\ge75\%$ coverage gate, of which
**3,390** carry a corrected Energy Pattern label (EP1 482 / EP2 767 / EP3 2,141).

### C1. Phase-class composition

| Class | n | % | |
|---|---|---|---|
| `EC` | 2,754 | 44.7% | extratropical throughout |
| `SC` | 173 | 2.8% | subtropical throughout |
| `TC` | 2 | 0.0% | tropical throughout |
| `ST` | 58 | 0.9% | subtropical transition (EC → SC) |
| `SD` | 22 | 0.4% | subtropical decay (SC → EC) |
| `TT` / `ET` | 0 | 0.0% | — |
| `EC_like` | 2,095 | 34.0% | extratropical characteristics, not sustained 36 h |
| `SC_like` | 493 | 8.0% | **hybrid characteristics, not sustained 36 h** |
| `TC_like` | 2 | 0.0% | warm-core characteristics, not sustained 36 h |
| `undetermined` | 558 | 9.1% | sufficient CPS coverage, no dominant structure |

Separately, the tropical-transition test rejected **12 warm seclusions** and 2
indeterminate warm cores.

**Characteristic classes.** A cyclone that never holds a class for 36 h is not thereby
structureless. The 36-h requirement of Guishard et al. (2009) and Gozzo et al. (2014) is
left untouched for the named classes, but instead of pooling everything else into one
bucket, a cyclone whose classifiable timesteps are dominated (≥ 50%) by one structure is
described by it. **`SC_like` is explicitly not a claim that the cyclone was subtropical** —
only that it showed hybrid characteristics without sustaining them. Yanase et al. (2014)
carry a comparable catch-all ("ill-defined cyclones for the others"); this resolves it
rather than pooling it.

**On the two `TC` cyclones.** Sixteen persistent tropical runs exist; fourteen are rejected
(twelve warm seclusions at a median −59.9°, two indeterminate warm cores). The two accepted:

| track | start | end | h | median lat | median $-V_T^U$ | antecedent |
|---|---|---|---|---|---|---|
| 19911137 | 1991-12-28 22Z | 1991-12-30 10Z | 36 | −29.85° | 27.7 | EC, 3 h |
| 19980144 | 1998-02-17 22Z | 1998-02-19 13Z | 39 | −29.35° | 15.8 | **SC, 30 h** |

Neither is labelled `TT`, and the reasons differ:

- **19911137** never held any structure before its tropical run: extratropical for 3 h + 3 h,
  subtropical for 3 h + 1 h, with 12 h unclassified between. There is no antecedent state to
  transition *from*.
- **19980144** was **subtropical for 30 h immediately before** its 39-h tropical run — the
  Catarina/Akará pathway — but 30 h is 6 h short of the 36-h gate, so the subtropical phase
  is not a state and the cyclone is not labelled `TT`. **This is a limitation of the
  threshold, not of the physics.** The `antecedent_characteristics` column records it, so
  the cyclone is legible as a tropical-transition candidate without being claimed as one.

**[UNCERTAIN]** Both have shallow warm cores ($-V_T^U$ 16–28 against 100+ for a genuine
tropical cyclone), neither has been inspected against imagery, and neither spends most of
its life tropical (median own-class share 0.34). Treat them as candidates.

### C2. "Pure" in the literature qualifies the genesis, not the whole life

The classes here are deliberately **not** called "pure". In the South Atlantic literature
"pure" qualifies the **cyclogenesis**:

- Silva et al. (2022) contrast Guará, *"com **gênese subtropical pura**"*, against Lexi,
  *"com **transição subtropical**"*, and confirm it from the phase diagram: *"o diagrama de
  fase confirmou a gênese subtropical pura do ciclone Guará e a gênese extratropical do
  Lexi com a posterior transição para a categoria subtropical"*.
- Reboita et al. (2021) title their paper *"Iba: The first **pure tropical
  cyclogenesis**"*.

Decisively, Silva et al. say of Guará — the exemplar of a pure subtropical genesis — that
*"ao longo do ciclo de vida o sistema sofreu **transição para extratropical** e
posteriormente decaiu"*. **The canonical "pure subtropical cyclone" of the literature did
not spend its life as a subtropical cyclone.** In this scheme Guará would be `SD`
(subtropical genesis followed by an extratropical state), and Lexi would be `ST` — which is
exactly how Silva et al. describe them.

So two quantities are reported separately rather than being conflated in one label:

**(i) Genesis type** — the first persistent state, and whether it is in place within 24 h
of genesis (the Guishard/Gozzo window):

| first persistent state | cyclones | of which in place within 24 h |
|---|---|---|
| EC | 2,810 | 2,290 (81.5%) |
| SC | 197 | 114 (57.9%) |
| TC | 2 | 0 (0.0%) |

**(ii) Dominance** — how much of its own classifiable life a cyclone actually spends in its
own class:

| class | median share | ≥50% | ≥70% | ≥90% | class is dominant |
|---|---|---|---|---|---|
| `EC` (2,754) | 0.83 | 2,444 | 1,820 | 1,095 | 2,614 (95%) |
| `SC` (173) | 0.74 | 157 | 97 | 41 | 166 (96%) |
| `TC` (2) | 0.34 | 0 | 0 | 0 | 1 (50%) |

The intuition that a "subtropical cyclone" should spend most of its life subtropical is
therefore **well supported for `SC`** — it is the dominant class in 95% of them, with a
median share of two thirds — and **not supported for `TC`**, where the label rests on a
single 36-h run in a cyclone that is subtropical for most of its life. That is one more
reason to treat the two `TC` cyclones as candidates rather than identifications.

Among classifiable timesteps, the pure-`SC` composition is 69.8% subtropical / 19.1%
extratropical / 10.1% unclassified / 1.0% tropical, against 23.1% / 62.7% / 12.4% / 1.7%
for the full eligible population — near mirror images. This is why
`fig6_phase_space_by_ep_single_state_sc.png` shows the density of the **subtropical-classified timesteps
only**, with the rest as grey context: plotting all their timesteps reproduces something
close to the whole-population cloud and hides the classification.

Columns `genesis_state`, `genesis_onset_h`, `pure_genesis`, `dominant_class` and
`frac_EC` / `frac_SC` / `frac_TC` carry all of this per cyclone in
`phase_classification.csv` and `cyclone_lists_by_class.csv`.

### C3. Indeterminate is distinct from insufficient coverage

Median CPS-record lifetime by class: `EC_like` **60 h**, `SC_like` 84 h,
indeterminate 99 h, `SC` 105 h, `EC` 111 h, `TC` 119 h, `TC_like` 179 h, `ST` 183 h and
`SD` 187 h. A record shorter than 39 h cannot hold a state for 36 consecutive hours once
the unclassifiable genesis timestep is accounted for. Step 3 finds 92 short records among
the characteristic plus indeterminate classes in the EP-labelled population; most of the
558 indeterminate cases are therefore structurally ambiguous rather than merely short.
All 558 nevertheless pass the coverage gate; missing or unusable CPS is represented by
`no_data` only in the all-track audit, never by `undetermined` in the official population.

### C4. Energy Pattern × phase class

All counts below are **post-guard** (caveat C-xi). The unguarded numbers, and the reversal
between them, are recorded at the end of this section.

| | `EC` | `SC` | `TC` | `ST` | `SD` | `EC_like` | `SC_like` | undet. |
|---|---|---|---|---|---|---|---|---|
| **EP1** (482) | 62.7% | **1.2%** | 0.0% | 1.0% | 0.2% | 17.8% | 8.5% | 8.5% |
| **EP2** (767) | 56.8% | **1.8%** | 0.0% | 1.8% | 0.3% | 18.1% | 7.4% | 13.6% |
| **EP3** (2,141) | 59.1% | **5.0%** | 0.0% | 1.5% | 0.5% | 16.9% | 7.6% | 9.3% |

$\chi^2 = 46.08$, dof = 16, $p = 9.45\times10^{-5}$, Cramér's V = 0.082 (Cochran's condition
violated — 8 of 27 expected counts below 5; the table-wide test is indicative only). Cells
with $|z| > 2$: **EP3 × `SC` at $z = +3.0$**, **EP1 × `SC` at $z = -2.9$**, EP2 × `SC` at
$z = -2.8$, EP2 × undetermined at $z = +3.0$.

**The signal is in `SC`, and it is monotonic in the energetics.** Fisher exact, each EP
against the other two pooled, Holm-corrected over the nine contrasts of C4/fig8:

| | `SC` rate | ×EPALL | OR | p | Holm |
|---|---|---|---|---|---|
| **EP1** | **6/482 (1.24%)** | **0.33** | 0.29 | $6.93\times10^{-4}$ | ✓ |
| **EP2** | **14/767 (1.83%)** | **0.48** | 0.41 | $7.73\times10^{-4}$ | ✓ |
| **EP3** | **108/2,141 (5.04%)** | **1.34** | 3.26 | $1.04\times10^{-7}$ | ✓ |

All three survive correction — the only place in this analysis where that happens.

**`ST` carries no significant signal.** EP1 0.69×, EP2 1.21×, EP3 0.99×; all raw
$p$-values are at least 0.40 and none survives correction.

**Interpretation.** The ordering follows the LEC signature directly: **the weaker a
cyclone's baroclinic energetics, the more likely it is to be subtropical.** EP3, the
weak/background pattern, holds 5.0% subtropical against 1.2% for EP1, the high-conversion
exporting pattern — a factor of **4.1**. That is what a diabatically driven, convectively
maintained system should look like in an energy-cycle framework: it does not run on
baroclinic conversion, so it appears in the cluster that has little of it.

`SC or ST` reproduces the same ordering (EP1 0.43×, EP3 1.24×, both surviving Holm).

**The reversal, and why it is the guards.** Before the subtropical guards the headline was
the opposite: `SC` was flat (ratios 0.93–1.04, nothing significant) and `ST` carried the
result (EP2 1.36×, $p = 5.5\times10^{-4}$, the only Holm survivor). Both statements came
from the same data and the same thresholds; only the guards differ.

The reading is that the unguarded `ST` signal was **warm-seclusion contamination**. EP2 is
the moderate-conversion, energy-importing pattern — the one whose cyclones are most likely
to run a full baroclinic life cycle and occlude into a warm seclusion. Removing seclusions
removed the signal. What survives is a statement about *being* subtropical, not about
*becoming* one, and it is stronger and cleaner than the result it replaced.

The earlier note in this section — *"EP3 hosts the systems born hybrid; EP2 hosts the
systems that become hybrid"* — survives only in its first half. The second half is
withdrawn.

**Expressed against the pooled population** (`fig8_ep_relative_subtropical.png`), with
EPALL = EP1 + EP2 + EP3 = 3,390 — the corrected, coverage-eligible EP population:

| | `SC` rate | ×EPALL | `ST` rate | ×EPALL | `SC` or `ST` | ×EPALL |
|---|---|---|---|---|---|---|
| EPALL | 3.78% | 1.00 | 1.50% | 1.00 | 5.28% | 1.00 |
| EP1 | 1.24% | **0.33** | 1.04% | 0.69 | 2.28% | **0.43** |
| EP2 | 1.83% | **0.48** | 1.83% | 1.21 | 3.65% | 0.69 |
| EP3 | 5.04% | **1.34** | 1.49% | 0.99 | 6.54% | **1.24** |

The ratio is a **descriptive effect size only**: each EP is nested in EPALL, so it is not
an independent comparison. Inference stays with the EP-versus-other-two Fisher contrast.

**Multiple comparisons.** Nine contrasts are tested (3 outcomes × 3 EPs), Holm-corrected.
Five survive: all three `SC` contrasts, and `SC or ST` for EP1 and EP3. Figures encode the
raw $p$ in the star level and Holm survival in the marker fill, so the two are never
conflated.

### C5. What the transitions look like in the phase space

`ET` (TC → EC, strict sense) and `TT` are both **empty by construction**: the catalogue
holds no tropical cyclone to transition from or to. The two transitions that occur are:

| | n | cold core / tilted | hybrid | symmetric warm core | unclassified |
|---|---|---|---|---|---|
| `ST` (EC → SC) | 58 | 52.24% | 39.58% | 0.76% | 7.42% |
| `SD` (SC → EC) | 22 | 47.88% | 42.52% | 0.3% | 9.31% |

(percentages of each class's timesteps by per-timestep structure)

The two are near-mirror images in composition, as they should be — the same two states
visited in opposite order — and the ~2% and ~1% of symmetric-warm-core timesteps are
transient excursions that never reach the 36-h gate. `figures/cps_analysis/fig7_transition_trajectories.png`
shows the paths, with every timestep marked by the structure it holds, in the convention of
the case-study literature (Hart 2003; Reboita et al. 2024 and de Souza et al. 2026 on Akará).

Note that `SD` is the pathway the earlier draft scheme folded into `ET`. Under the canonical
naming, which follows Evans and Hart (2003) in reserving `ET` for TC → EC, it is a class of
its own.

### C6. Region control

The `SC` enrichment is geographically concentrated rather than uniform: within LA-PLATA
the rates are 1.0% / 3.4% / 9.3% for EP1–EP3, and within SE-BR they are
5.8% / 3.2% / 17.4%. `ST` has no global EP signal. The stratification therefore supports
the EP3–`SC` association in the two subtropical sectors while warning against a basin-wide
causal reading.

### C7. Where each type forms and where it lives

**[PRELIMINARY]** — read off the step-9 maps; no test has been applied to any of the
contrasts below. Counts are over the 3,390-cyclone corrected, coverage-eligible EP
population (see Step 9).

**The classes separate geographically, and by more than the guards impose.** Median genesis
position, with peak density from the EPALL panels:

| class | n | median genesis | genesis peak <br> [events/10⁶ km²/yr] | whole-life peak <br> [cyclone days/10⁶ km²/yr] | genesis region |
|---|---|---|---|---|---|
| `EC` | 2,003 | 42.8°S, 61.1°W | 18.61 | 15.23 | 60% ARG |
| `SC` | 128 | 28.8°S, 48.1°W | 1.19 | 4.23 | 63% SE-BR, 34% LA-PLATA |
| `ST` | 51 | 31.5°S, 55.9°W | 0.41 | 0.61 | 47% SE-BR, 47% LA-PLATA |
| `SD` | 14 | 26.1°S, 48.3°W | 0.25 | 0.58 | 86% SE-BR |
| `SC_like` | 261 | **46.3°S, 62.4°W** | 3.24 | 3.70 | mid-latitude |

The `SC` genesis band at 20–40°S is imposed by the guards, so its position is not an
independent result; **its longitude and its narrowness are**. The subtropical genesis maximum
sits offshore of southeastern Brazil, and `ST` — which is *not* subject to a genesis-band
guard — lands in the same sector, ~3° poleward and ~6° west, i.e. on the extratropical side
of the same corridor. That is the geography the transition name already implies.

**`SC` is confined; `ST` is not.** 99.7% of `SC` positions fall inside the map frame
(80°W–60°E, 70°S–15°S) against 91.2% for `ST` and 94.3% for `EC` — and `SC` is the only class
whose whole-life peak (4.23) is **larger** than its genesis peak (1.19). A subtropical cyclone
stays in the box it was born in and spends its life there; an `ST` cyclone is a mid-latitude
system that keeps travelling after acquiring the structure, and its residence-time field is
smeared along the storm track to beyond 60°E.

**`SC_like` is a different population, not a weaker `SC`.** Its median genesis is at
**46.3°S**, 17.5° poleward of `SC`, and its density fields are those of the `EC` population.
Whatever the hybrid characteristics of those 261 cyclones represent, it is not an unresolved
subtropical class — which is the geographic form of the argument for keeping the `*_like`
names distinct (C1, C-xi).

**By Energy Pattern, the anomalies are of shape, not of rate.** Within `EC` the EP2 panel is
enhanced over the LA-PLATA/SE-BR sector and EP3 is enhanced poleward of 40°S, the same
contrast the medians give (C6). Within `SC` only EP2 and EP3 have enough cyclones to draw at
all (14 and 108); EP1 has **six**, which is the C4 result — EP1 rarely produces subtropical
cyclones — arriving as an empty panel rather than as a statistic.

### C8. CPS coverage diagnostic (separate from the CPS × EP result)

Of the 6,789 reference tracks, 6,776 have a CPS file. Exactly 2,790/6,776 files are complete
(41.17%) and 3,986/6,776 are incomplete (58.83%); 15 files have no usable CPS interval.
Together with the 13 absent files, `no_data` contains 28 cyclones. The official duration
gate includes 6,157/6,789 cyclones (90.69%): 2,790 complete and 3,367 eligible incomplete.
It excludes 632 (9.31%): 604 with usable coverage below 75% plus the 28 `no_data` cases.

Among incomplete CPS files, including the 15 zero-coverage files, coverage has mean 0.874,
standard deviation 0.230, minimum 0, quartiles 0.923/0.972/0.986 and maximum 0.997. The
requested bins contain 206 / 232 / 194 / 181 / 3,186 / 2,790 cyclones for
<25% / 25–<50% / 50–<75% / 75–<90% / 90–<100% / 100%, respectively. Complete tables by
bin, EP and diagnostic class are in `coverage_by_bin*.csv`, `coverage_by_ep.csv` and
`coverage_by_class.csv`; every percentage carries its denominator.

There is no detectable class or EP concentration between the 2,790 complete and 3,367
eligible-incomplete cyclones: phase class $\chi^2=1.87$, $p=0.985$, bias-corrected
Cramér's V = 0; EP $\chi^2=0.576$, $p=0.750$, V = 0. Inclusion is likewise similar across
the corrected EP populations: 88.0% for EP1, 89.2% for EP2 and 88.8% for EP3.

The principal EP result is stable to stricter coverage thresholds. `SC` rates for
EP1/EP2/EP3 are 1.43%/1.19%/4.76% at 100%, 1.27%/1.85%/4.90% at $\ge90\%$, and
1.24%/1.83%/5.04% at the official $\ge75\%$ threshold. Corresponding sample sizes are
210/337/966, 472/755/2,103 and 482/767/2,141. The coverage diagnostic does not alter the
methodology; it only quantifies the selection.

### C9. Attribution of the rerun changes

The pre-rerun audit found 314 of the 3,812 CPS-linked cyclones with a changed EP assignment:
13 moved out of old EP1, 207 out of old EP2 and 94 out of old EP3. The historical
old→corrected transition matrix was 428/12/1 from old EP1; 99/771/108 from old EP2; and
18/76/2,299 from old EP3. The regenerated audit now compares every one of the 3,820
corrected EP IDs directly with `phase_classification_all.csv` and reports zero mismatches;
the 314 reassigned systems are therefore represented by their corrected label in every
downstream product.

The two effects can be separated numerically. Changing only the EP association, before the
coverage gate, changes the CPS-linked denominators from 441/978/2,393 to 545/859/2,408 and
the `SC` rates from 3/441 (0.68%), 19/978 (1.94%), 112/2,393 (4.68%) to 7/545 (1.28%),
14/859 (1.63%), 113/2,408 (4.69%). Applying the coverage gate then yields the official
482/767/2,141 denominators and 6/482 (1.24%), 14/767 (1.83%), 108/2,141 (5.04%). Thus the
large denominator redistribution is caused by the corrected clustering; the coverage gate
mainly trims the sample and removes six otherwise classified `SC` cyclones (1/0/5 by EP).

---

## Caveats and Limitations

**Canonical analysis**

C-i. **`TT` and `ET` are empty, and `TC` holds two unverified candidates.** This is the
correct answer for this catalogue, not a failure: its genesis boxes exclude every
documented South Atlantic tropical system. The two `TC` cyclones (19911137, 19980144) have
shallow warm cores ($-V_T^U$ 16–28) and have not been inspected. Do not report them as
identified tropical cyclones.

C-ii. **`undetermined` is not missing data.** It contains 558/6,157 eligible cyclones
(9.1%) that have sufficient CPS coverage but no dominant persistent structure. The 28
systems with zero usable coverage or no CPS file are recorded separately as `no_data`.

C-iii. **The EP × phase-class chi-square is indicative table-wide** because 8 of 27
expected counts are below 5. The focal Fisher contrasts and Holm correction support the
`SC` result; no `ST` contrast is significant.

C-iv. **`SD` is not an established term.** "Subtropical decay" for SC → EC is named in this
work. `ST`, `TT` and `ET` all carry published definitions; `SD` does not.

C-v. **The persistence gate is a choice with consequences.** At 36 h it is the
Guishard/Gozzo value, but it sets the `indeterminate` fraction and therefore every
percentage in the tables. The sensitivity suite quantifies the dependence.

**Inherited from the sensitivity work** (full statements in
`sensitivity/SCIENTIFIC_NOTES.md`)

C-vi. **The tropical class is warm-seclusion contamination under any rule short of the full
protocol** — median latitude −57.8°, 88% of timesteps in mature/decay, median onset 75 h
after genesis. The canonical tropical-transition test exists to remove it.

C-vii. **The catalogue cannot contain South Atlantic tropical cyclones.** Catarina, Anita,
Arani, Deni, Guará and Iba all form outside the ARG / LA-PLATA / SE-BR genesis boxes;
Raoni, Yakecan, Akará and Biguá postdate the record. `TT` and `ET` being empty is a property
of the population, not a failure of the method.

C-viii. **The subtropical count is threshold-sensitive by a factor of 6–8** across the six
sets tested, at every level of strictness. Any subtropical number must be quoted with its
threshold set attached.

C-ix. **The 500-km CPS radius may not represent the small, shallow SE-BR systems well** — a
caveat Conrado et al. (2024) raise about their own work. Separately, 13 tracks have no CPS
file, 15 files have no usable interval and 604 cyclones have usable coverage below 75%; the
coverage gate and `no_data` distinction make those losses explicit.

C-xi. **The subtropical classes are guarded; before 2026-08-10 they were not.** The
warm-seclusion filter originally ran only inside `if r["code"] != "TC": continue`, so a
persistent SUBTROPICAL run was accepted on the 36 h gate alone — the one criterion a
Shapiro–Keyser occlusion satisfies without difficulty. `GENESIS_LAT_BAND` (Gozzo criterion
1) existed in `cps_criteria.py` and was read by no canonical script. The diagnosis, from
the unguarded output:

| | n | median lat of run | onset | onset phase | peak already passed |
|---|---|---|---|---|---|
| rejected warm seclusions (tropical) | 12 | −61.5° | 112 h | end of cycle | — |
| unguarded `ST` | 298 | −57.9° | 102 h | 78% mature/decay | **67%** |
| unguarded `SC` | 409 | −39.1° | 33 h | 58% incipient/intensif. | 30% |
| unguarded `SD` | 47 | −37.4° | 18 h | 73% incipient/intensif. | 11% |

`ST` was indistinguishable from the rejected seclusions on every axis, and travelled 16.6°
poleward between genesis and the hybrid run (4.9° for `SC`, 2.7° for `SD`).

**Three guards were added** (`cps_criteria.SC_*`), applied to every persistent hybrid run:
the Gozzo genesis band, the ocean clause, and an intensity-peak test. The peak test is the
physical discriminator the CPS itself cannot supply: a diabatically built warm core
re-energises the system, so peak intensity follows the structure, whereas a mechanically
secluded warm core is the terminal stage and the peak has already passed. Runs beginning
more than `SC_MAX_HOURS_PAST_PEAK` = 12 h after the vorticity peak are rejected.

Of the 784 persistent hybrid runs in the eligible population: **260 accepted, 386 rejected
as `genesis_out_of_band`, 138 rejected as `warm_seclusion`.** Per-run verdicts and
`run_code` are in
`phase_states.csv`, so every rejection remains inspectable.

| class | historical unguarded, pre-coverage | guarded and coverage-eligible |
|---|---|---|
| `SC` | 409 | **173** |
| `ST` | 298 | **58** |
| `SD` | 47 | **22** |
| `SC_like` | 372 | 493 |

**This is the change that made the analysis agree with the literature.** Cyclones with an
accepted subtropical state: 253 over 42 years = **6.0 per year**, against Gozzo et al.'s
**7.2 per year**. Unguarded the same quantity was 18.0 per year — two and a half times the
published rate.

**The 24 h onset criterion is still not a gate, and deliberately so** (see Methodology
(iii)): it filters on type of genesis and excludes transitions by construction.

*Historical note.* An earlier version of this caveat argued against `ST` from the onset
criterion. That argument was wrong — a category error — and has been replaced by the peak
test above.

C-x. **The CPS parameters are classified unsmoothed, and the literature is split on this.**
Hart (2003) applies a temporal filter to his own diagrams: *"For each of the three phase
parameters, a 24-h running mean smoother is applied to remove short-term noise in the
evolution resulting from the coarse grid resolution of the gridded analyses and the
inability to diagnose cyclone movement between grid points"* (his section 2b, *Cyclone
phase diagram construction*) — the
motivation is instrumental (2.5° NCEP–NCAR grid), not physical. Bieli et al. (2019) make
the opposite choice for an objective climatology and state it explicitly: *"For this study,
no smoothing was applied to the CPS parameters"*, reserving the 24-h running mean for
display only (*"a 24-h running mean has been used for plotting"*). The South Atlantic
subtropical literature this protocol follows — Evans and Guishard (2009), Gozzo et al.
(2014), Conrado et al. (2024) — describes no temporal smoothing at all; it controls
short-term noise through a **persistence requirement** instead (36 consecutive hours),
which is the route taken here. The two devices are not equivalent: a running mean can
carry a structure across a gap it never actually held, whereas the persistence gate can
only discard. The gate is therefore the conservative choice, at the cost of rejecting real
but briefly interrupted hybrid episodes — which is what the `*_like` characteristic classes
were introduced to record. **Not tested here**: whether a 9-point (24 h at 3-hourly)
running mean changes the class counts.

C-xii. **The density maps of the rare classes rest on very few cyclones, and a KDE hides
that.** A Gaussian kernel of ~318 km draws a smooth, confident-looking field from any sample
whatever. `SD`/EPALL is 14 cyclones, and `ST`/EP2 and `SC`/EP2 are 14 each; the fields are drawn
because they clear the 10-cyclone floor, not because they are stable. Two consequences: read
the anomaly panels of the rare classes as suggestive only — no confidence interval is
attached to any of them — and remember that the whole-life maps count 3-hourly positions of
the same trajectory, so their effective sample is the cyclone count in the panel corner and
not the position count. The `SC`/EP1, `ST`/EP1 and `SD`/EP2 panels are shown as raw points
for exactly this reason; the difference between 6 cyclones and 14 is one of degree.

---

## Next Steps

1. **Visually validate the canonical classes case by case.** Step 7 draws a sampled
   gallery — one cyclone per class × year × region, 618 individual CPS diagrams under
   `figures/cps_analysis/cases/<CLASS>/` — and the full track_id lists are in
   `results/cps_analysis/cyclone_lists_by_class.{csv,txt}`. Priority order: the 2 `TC`
   cyclones, the 138 subtropical runs rejected as warm seclusions, the 22 `SD`, then a
   sample of the 173 `SC`. This is
   the step Gozzo et al. performed manually and we have not.

2. **Add the gale criterion.** `SIZE` (equivalent radius of 925-hPa winds >= 17 m/s) is
   already in the database, so Guishard et al.'s (2009) gale requirement can be applied
   without new computation - useful for a like-for-like comparison against their North
   Atlantic 4/yr.

3. **Test the diabatic hypothesis.** Compare $G_e$, $BA_e$ and $BK_e$ between the
   early-onset (EP3-like) and late-onset (EP1/EP2-like) hybrid populations. If the
   early-onset systems show enhanced diabatic generation and weak baroclinic conversion,
   the structural correlation in section 3 gains a mechanism. All the LEC data is already
   in `results/`.

4. **Resolve the seclusion population explicitly.** The late-onset warm-core cyclones are
   interesting in their own right - they are candidate Shapiro-Keyser warm seclusions, and
   EP1/EP2 are enriched in them. A dedicated seclusion diagnostic (rather than treating
   them as tropical contamination) would be a second paper-scale result.

5. **Retain the 13 absent CPS series as `no_data`.** Regenerating them would require a
   separate ERA5 acquisition/reprocessing task and is outside this rerun.

6. **Sensitivity to the CPS radius**, if the ERA5 subsets are ever regenerated: recompute
   with 300 km for the shallow SE-BR systems.

---

## References

Beven, J. L. (1997). A study of three "hybrid" storms. *Preprints, 22nd Conf. on Hurricanes
and Tropical Meteorology*, Amer. Meteor. Soc., 645-646. [cited via Gozzo et al. 2014]

Bieli, M., Camargo, S. J., Sobel, A. H., Evans, J. L., & Hall, T. (2019). A global
climatology of extratropical transition. Part I: Characteristics across basins.
*J. Climate*, **32**(12), 3557-3582.
doi:[10.1175/JCLI-D-17-0518.1](https://doi.org/10.1175/JCLI-D-17-0518.1)

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

Hoskins, B. J., & Hodges, K. I. (2005). A new perspective on Southern Hemisphere storm
tracks. *J. Climate*, **18**(20), 4108-4129.
doi:[10.1175/JCLI3570.1](https://doi.org/10.1175/JCLI3570.1)

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

### 2026-08-06 - Initial CPS classification and EP cross-reference

First complete pass. Population validated against Gozzo et al. (2014) at the relaxed end
(9.3 subtropical/yr vs their 7.2) and against Evans and Braun (2012) at the strict end
(1.8/yr with GUISHARD09 thresholds vs their 1.2). Main findings: (i) the CPS "tropical" class in this catalogue is
warm-seclusion contamination - median latitude -57.7 deg, 93% of timesteps in mature+decay,
median onset 75 h after genesis - and collapses to 0-1 cyclones under all six threshold
sets once the Guishard/Gozzo 24-h onset criterion is applied; (ii) the EP association
reverses with strictness - EP2 leads in warm cores *acquired* late in the life cycle, EP3
leads by ~10x in structures present *from genesis* (Fisher OR 9.81, p = 1.8e-10),
identifying EP3 as the host of the genuinely subtropical population.

### 2026-09-29 - Coverage-gated rerun with corrected EP mapping

The current analysis of record uses 6,157 cyclones with at least 75% duration-weighted CPS
coverage and the corrected Energy Pattern association. The complete all-track audit retains
all 6,789 reference tracks, separates 28 `no_data` cases from 604 insufficient-coverage
cases, and verifies all 3,820 corrected EP IDs with zero mapping mismatches. The official
EP sample is 482/767/2,141; `SC` occurs in 6/14/108 cases (1.24%/1.83%/5.04%). The rerun
also regenerates the sensitivity suite only from coverage-eligible tracks.
