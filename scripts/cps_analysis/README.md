# Cyclone Phase Space (CPS) Analysis

Computes the Hart (2003) Cyclone Phase Space diagnostics — thermal wind asymmetry (`B`)
and lower/upper thermal wind (`VTL`, `VTU`) — for every cyclone track in the study, and
classifies each system into a **single persistent state** or a **phase transition**. The resulting
classes are cross-referenced against the **Energy Patterns (EP1/EP2/EP3)** from the K-Means
clustering on Lorenz Energy Cycle diagnostics.

Science notes are split to match:
`SCIENTIFIC_NOTES.md` is the canonical record (framework, equations, methodology, canonical
results, caveats); `sensitivity/SCIENTIFIC_NOTES.md` is the exploratory record.

---

## Canonical analysis vs sensitivity tests

| | Canonical | Sensitivity |
|---|---|---|
| Scripts | `step1..step8` in this folder | `sensitivity/` |
| Thresholds | **one set** (de Souza et al. 2026) | six sets × four identification rules |
| Outputs | `results/cps_analysis/`, `figures/cps_analysis/` | the `sensitivity/` subfolder of each |
| Status | **the analysis of record** | reference only; motivates the canonical design |

`sensitivity/README.md` lists the nine findings from those tests and, for each, the specific
canonical design choice it motivated.

---

## Provenance

The CPS calculator and the per-cyclone diagram script were written by
**Andres Rodriguez (IAG-USP)**, who also ran the full computation over the 6,789-cyclone
population — a multi-month job:

| File | Author | Status |
|---|---|---|
| `cps_calculator_era5tocsv.py` | A. Rodriguez | preserved, unmodified |
| `cps_plots_csv_gris.py` | A. Rodriguez | preserved, unmodified |
| `csv_output/` (6,776 CSVs) | A. Rodriguez | **irreplaceable** — the per-cyclone ERA5 NetCDFs were not retained |

**Do not delete `csv_output/`**: the ERA5 inputs it came from are gone, so regenerating it
means re-downloading and re-processing the whole archive.

---

## The canonical classification

**Thresholds** (`cps_criteria.CANONICAL`), following de Souza et al. (2026), who take
extratropical/tropical from Wood et al. (2023) and subtropical from Gozzo et al. (2014):

| Class | `B` [m] | `VTL` | `VTU` |
|---|---|---|---|
| extratropical | > 10 | < 0 | < 0 |
| subtropical | −25 < B < 25 | > −50 | < −10 |
| tropical | < 10 | > 0 | > 0 |

**Persistence gate.** A class counts as a *state* of the cyclone only when held for
**≥ 36 consecutive hours** (Guishard et al. 2009; Gozzo et al. 2014). Without this gate the
raw labels oscillate — 158 distinct sequences, the commonest non-pure one being EC→SC→EC —
and a "genesis as X, later Y" rule has no defined answer.

**Classes.**

| Code | Meaning |
|---|---|
| `EC` / `SC` / `TC` | a single persistent state (**not** "pure" — see below) |
| `ST` | subtropical transition, EC → SC (Reboita et al. 2022) |
| `SD` | subtropical decay, SC → EC |
| `TT` | tropical transition, EC or SC → TC (Davis & Bosart 2003, 2004) |
| `ET` | extratropical transition, TC → EC (Evans & Hart 2003) |
| `EC_like` / `SC_like` / `TC_like` | characteristics shown but never sustained 36 h |
| `undetermined` | no dominant structure |

`ET` is kept to its established meaning — Evans & Hart (2003): *"the storm evolves **from a
tropical cyclone** to a baroclinic system"* — so SC → EC gets its own name (`SD`) rather
than being folded in.

**The tropical-transition test.** Every persistent tropical run is tested. It is a genuine
`TT` if **either**:

the **tropical run itself** must lie **equatorward of 40°S** and be ≥ 50% over ocean.
Otherwise it is a **warm seclusion** (if preceded by an extratropical state) or an
**indeterminate warm core**, and is removed from the state sequence. The preceding state is
recorded as a pathway descriptor but does not bypass the test — the Shapiro–Keyser occlusion
passes through hybrid structure too, so "preceded by subtropical" is what a seclusion does
as well. Only the poleward bound is used: Iba formed at ~20°S, on the edge of the
Guishard/Gozzo band, so an equatorward bound would exclude the most plausibly tropical
cases.

**The subtropical identification test.** Every persistent hybrid run is tested too — it
was not, until 2026-08-10, and caveat C-xi in the science notes records what that cost. A
run is accepted as `SC` only if all three hold:

1. **genesis between 20°S and 40°S** — Gozzo et al. (2014), criterion 1;
2. **≥ 50% of the run over ocean** — Gozzo criterion 3;
3. **the run begins no more than 12 h after the cyclone's intensity peak.**

(3) is the warm-seclusion guard, and it is physical rather than geographic: a diabatically
built warm core re-energises the system, so peak intensity *follows* the structure, whereas
a Shapiro–Keyser seclusion is the terminal stage and the peak has already passed. Rejected
runs are recorded as `genesis_out_of_band` or `warm_seclusion` with their original
`run_code`, so nothing is silently discarded.

Guishard et al.'s **24 h onset criterion is deliberately not a gate**: it selects systems
*born* hybrid and so excludes transitions by construction, which would be a category error
applied to `ST`. It is kept as the descriptive flag `pure_genesis`.

Two design points, both forced by the sensitivity evidence:

- The geographic test is on the **run**, not on genesis. Six of sixteen persistent tropical
  runs belong to cyclones that formed *inside* the band, moved ~30° poleward, and only then
  acquired a warm core at 55–62°S.
- The **life-cycle phase** of the run is **recorded but never used as a gate**. A phase-only
  rule admits exactly one case — track 20160337 at −54.7°S — confirmed from satellite
  imagery to be a classic extratropical cyclone.

---

## Results at a glance

Whole population (6,776 cyclones, genesis 1979–2020):

| Class | n | % |
|---|---|---|
| `EC` single-state extratropical | 2,926 | 43.2% |
| `SC` single-state subtropical | 182 | 2.7% |
| `TC` single-state tropical | 2 | 0.0% |
| `ST` subtropical transition | 60 | 0.9% |
| `SD` subtropical decay | 22 | 0.3% |
| `EC_like`  | 2,398 | 35.4% |
| `SC_like`  | 548 | 8.1% |
| `TC_like`  | 2 | 0.0% |
| `undetermined`  | 636 | 9.4% |
| `TT` / `ET` | 0 | 0.0% |

Of the 804 persistent hybrid runs, **271 were accepted**; **395** were rejected as `genesis_out_of_band` (Gozzo criterion 1 / ocean) and **138** as `warm_seclusion` (intensity-peak guard). The tropical guard additionally rejected 12 warm seclusions and 2 indeterminate warm cores. Every rejection keeps its `run_code` and verdict in `phase_states.csv`.

**Validation.** 264 cyclones reach an accepted subtropical state over 42 years = **6.3 per year**, against Gozzo et al. (2014) **7.2 per year**. Without the guards the same quantity is 18.0 per year.

The `*_like` classes keep the 36-h literature threshold intact for the named classes while
still saying what a cyclone showed: `SC_like` means *hybrid characteristics, not sustained*,
not *subtropical*. Most of them are short-lived — median lifetime 42 h against 99–186 h for
the named classes.

**Why the single-state classes are not called "pure".** In the South Atlantic literature
"pure" qualifies the *cyclogenesis*: Silva et al. (2022) call Guará a *"gênese subtropical
pura"* and Reboita et al. (2021) title their paper *"the first pure tropical
cyclogenesis"*. Silva et al. also report that Guará — the exemplar — *later became
extratropical and decayed*. So "pure subtropical" never meant "subtropical all its life",
and Guará would be `SD` in this scheme, Lexi `ST`, exactly as they describe them.

Two quantities are therefore reported separately instead of being folded into one label:

- **genesis type** — `genesis_state`, `genesis_onset_h`, `pure_genesis` (first persistent
  state in place within 24 h). SC genesis: 206 cyclones, 118 of them within 24 h.
- **dominance** — `dominant_class`, `frac_EC`/`frac_SC`/`frac_TC`. The `SC` class spends a
  median 0.74 of its life subtropical and SC is its dominant class in 96% of cases; the two
  `TC` cyclones spend a median of only 0.34 tropical, one more reason to treat them as
  candidates.

Because a pure-`SC` cyclone is still non-subtropical for about a third of its life, the
pure-SC figure shows the density of the **subtropical-classified timesteps only**, with the
rest as grey context.

**By Energy Pattern**, the signal is in `SC` and it is monotonic in the energetics:
**the weaker a cyclone's baroclinic conversion, the more likely it is to be subtropical.**

| | `SC` rate | ×EPALL | OR vs rest | p | survives Holm |
|---|---|---|---|---|---|
| EP1 (high conversions, exports) | 0.68% | 0.19 | 0.18 | 1.1×10⁻⁴ | ✓ |
| EP2 (moderate, imports) | 1.94% | 0.55 | 0.48 | 1.7×10⁻³ | ✓ |
| EP3 (weak / background) | 4.68% | 1.33 | 3.62 | <10⁻⁵ | ✓ |

A factor of **7** between EP3 and EP1, and all three contrasts survive Holm correction over
the nine tested. `ST` carries **no** significant signal after the guards (largest contrast
EP2, p = 0.11).

Before the subtropical guards this result was the opposite — `SC` flat, `ST` carrying an
EP2 enrichment. Same data, same thresholds; the difference is the guards, and the reading is
that the old `ST` signal was warm-seclusion contamination. See C4 and C-xi.

---

## How to run

```bash
python scripts/cps_analysis/run_all.py                       # canonical
python scripts/cps_analysis/sensitivity/run_sensitivity.py   # sensitivity tests
```

Step by step:

```bash
python scripts/cps_analysis/make_reference_diagram.py     # schematic, no data
python scripts/cps_analysis/step1_build_cps_database.py   # shared by both
python scripts/cps_analysis/step2_classify_phases.py
python scripts/cps_analysis/step3_ep_phases.py
python scripts/cps_analysis/step4_phase_figures.py
python scripts/cps_analysis/step5_phase_space_figures.py
python scripts/cps_analysis/step6_transition_trajectories.py
python scripts/cps_analysis/step7_case_diagrams.py
python scripts/cps_analysis/step8_ep_relative_frequency.py
python scripts/cps_analysis/step9_density_maps.py
```

### Region shading

Every CPS diagram in the analysis shades the **projection of each canonical class** onto the
plane being drawn, at high transparency: blue extratropical, green subtropical, red
tropical. (Green rather than yellow: a faint yellow between the blue and the red regions
blends into both, and the overlap grey stops reading as an overlap.) Because each panel is
a two-dimensional slice of a three-dimensional
classification, the shading is what the class can claim with the third parameter left free.

**Grey marks where more than one class can claim a point** — a real property of the
definitions, not a drawing artefact. A point with 10 < B < 25 and −50 < −V_T^L < 0 satisfies
both the extratropical and the subtropical spec; there the timestep precedence
(tropical > subtropical > extratropical) decides. Blank corners belong to no cyclone type:
the "warm tilted", "cold shallow" and "warm symmetrical" regions.

The shading logic lives in `cps_plotting.shade_class_regions`, so it is defined once and
every figure inherits changes to the thresholds automatically.
`fig0_cps_reference.png` is that schematic on its own, with no data plotted over it — the
figure to look at first, and the one to check a threshold against.

### Where each type forms and where it lives

`step9` maps the population: **rows are cyclone types, columns are EPALL / EP1 / EP2 / EP3**,
and the same layout is drawn twice —

| kind | positions used | unit |
|---|---|---|
| **genesis** (`fig9`) | the cyclogenesis point only, one per cyclone | cyclogenesis events / 10⁶ km² / year |
| **whole life** (`fig10`) | every 3-hourly position of the track | cyclone days / 10⁶ km² / year |

The estimator is the spherical KDE already used for the manuscript's genesis-density figure
(`scripts/main/07_figure_genesis_density_kde.py`, after Hoskins & Hodges 2005): Gaussian
kernel, haversine metric, bandwidth 0.05 rad (~318 km), 2.5° grid. It lives in
`cps_density.py` so the two figure families cannot drift apart. Whole-life density is
expressed in **cyclone days** — each 3-hourly position counts as 1/8 of a day — so the number
does not depend on the sampling cadence.

Each kind is drawn in two modes, because they answer different questions:

- **anomaly** (the manuscript convention) — column 1 is the absolute density of that type over
  EPALL; columns 2–4 are the min-max normalised anomaly of the type *within that EP* against
  the same type over EPALL. This compares **shape**, which is what is wanted when the EPs are
  very unequal in number.
- **absolute** — all four columns on one colour scale per row, peak value annotated. Sample
  size is then part of what the reader sees: the EP1 subtropical panel is nearly blank because
  EP1 barely produces subtropical cyclones, i.e. the C4 result stated as a map.

Two figure sets, to keep the panel count readable:

```
fig9_genesis_density_identified_{anomaly,absolute}.png        ALL, EC, SC, ST, SD
fig9_genesis_density_characteristics_{anomaly,absolute}.png   ALL, EC_like, SC_like, undetermined
fig10_track_density_identified_{anomaly,absolute}.png
fig10_track_density_characteristics_{anomaly,absolute}.png
```

Three things to keep in mind when reading them:

- **EPALL here is EP1 ∪ EP2 ∪ EP3 = 3,812 cyclones**, not the 6,776 of the catalogue — the same
  denominator as `step8`, and required because the EP columns are read against it. `--epall
  catalogue` switches to the full catalogue at the cost of that consistency.
- **Whole life means whole life.** The `fig10` maps use every position of a cyclone of that
  class, not only the positions holding that structure; a single-state `SC` cyclone spends a
  median 0.74 of its life subtropical, so the rest of its track is in the map. That is the right
  denominator for a residence-time map — the structure-resolved question is what `fig6` answers.
- **A panel with fewer than 10 cyclones gets its raw positions as points and no density field.**
  The gate is on cyclone count, not position count: the 3-hourly positions of one cyclone are
  not independent samples. `SC`/EP1 (3 cyclones), `ST`/EP1 (5) and `SD`/EP2 (3) are drawn this
  way, and `SD`/EP1 is empty.

Domains differ by kind: genesis uses the manuscript frame (75°W–20°W, 55°S–20°S); the tracks
run far east and south of the genesis boxes, so `fig10` uses 80°W–60°E, 70°S–15°S, which holds
96.1% of all 3-hourly positions. `TC` and `TC_like` are off both figures by default (two
cyclones each); `--classes TC TC_like SC` puts them on.

`results/cps_analysis/density_map_samples.csv` records, for every panel drawn, the cyclone and
position counts, the fraction of positions inside the domain, the peak density and whether a
KDE was estimated at all.

### The case gallery

`step7` draws one cyclone per **(phase class × year of genesis × genesis region)**,
sampled at random with a fixed seed — 628 figures spanning every class, every year and
every region in which that class occurs. Each is a single-cyclone CPS diagram in the
case-study convention: trajectory line, one marker per 3-hourly timestep coloured by the
structure it holds, endpoints A and Z, dates labelled.

The class appears in both the directory and the filename, so a figure stays identifiable
once detached from its folder:

```
figures/cps_analysis/cases/TC/cps_TC_1998_LA-PLATA_19980144.png
figures/cps_analysis/cases/ST/cps_ST_1979_SE-BR_19790594.png
figures/cps_analysis/cases/SC_like/cps_SC_like_1979_ARG_19791045.png
```

| class | figures | | class | figures |
|---|---|---|---|---|
| `EC` | 126 | | `SD` | 40 |
| `EC_like` | 124 | | `ST` | 105 |
| `SC` | 120 | | `TC` | 2 |
| `SC_like` | 105 | | `TC_like` | 2 |
| `undetermined` | 116 | | | |

Restrict to some classes, or reshuffle the draw:

```bash
python scripts/cps_analysis/step7_case_diagrams.py --classes TC SC ST
python scripts/cps_analysis/step7_case_diagrams.py --seed 7
```

The gallery is ~116 MB and git-ignored like every other figure. Which cyclone was drawn
for each combination is recorded in `results/cps_analysis/case_diagram_index.csv`.

**On `ET` and `TT` being empty.** Both are zero by construction of the catalogue, which
contains no tropical cyclone to transition from or to. The two transitions that do occur are
`ST` (EC → SC, 60) and `SD` (SC → EC, 22) — the latter is what the earlier draft scheme
called `ET`. `step6` plots both.

### Bringing the outputs home

The pipeline runs on the server; `sync_from_remote.sh` pulls the outputs to a local machine
over a single SSH connection (one password prompt), never overwriting a local file that is
newer and never deleting anything:

```bash
bash scripts/cps_analysis/sync_from_remote.sh --dry-run   # see what would come
bash scripts/cps_analysis/sync_from_remote.sh             # ~20 MB: tables + fig0–fig10
bash scripts/cps_analysis/sync_from_remote.sh --cases     # + the 628-figure gallery
bash scripts/cps_analysis/sync_from_remote.sh --inputs    # + csv_output/, as a backup
```

The default skips the two heavy things: the per-timestep databases (`*timesteps*.csv`,
~155 MB with the sensitivity ones) and `cases/` (106 MB). `--timesteps`, `--cases`,
`--inputs`, `--logs` add them back; `--all` takes everything. `--inputs` is worth running
once for its own sake — `csv_output/` is irreplaceable and lives on one server.

To print the threshold sets that will be applied:

```bash
python scripts/cps_analysis/cps_criteria.py
```

To regenerate the original per-cyclone diagnostics (needs the ERA5 NetCDFs, which are
**not** retained):

```bash
python scripts/cps_analysis/cps_calculator_era5tocsv.py \
    --nc <track_id>_era5.nc --track cyclone_tracks/cyclone_<track_id>.txt \
    --dt 3 --output csv_output/CPS_<track_id>.csv
```

---

## Data

**Population.** 6,776 cyclones with a CPS series, of which **3,812** carry an EP label
(the clustering covers 3,820; 8 have no CPS file). Genesis years **1979–2020 (42 years)**;
the last track runs into 7 January 2021.

**Cadence.** CPS is 3-hourly; the underlying tracks are hourly.

**Missing genesis step.** The calculator emits the GrADS sentinel `-999000000` at the first
timestep of every cyclone — storm motion, hence `B`, is undefined without a previous
position. The genesis state is therefore never observed directly; everything is evaluated
from +3 h.

**Sign convention.** `B = B_left - B_right`, which applies Hart's Southern Hemisphere factor
`h = -1`. `VTL`/`VTU` hold Hart's signed `-V_T^L` / `-V_T^U`, so positive means warm core.

---

## Folder map

```
cps_analysis/
├── README.md                       this file
├── SCIENTIFIC_NOTES.md             methods, provenance, results, caveats
├── cps_criteria.py                 all thresholds (canonical + sensitivity sets)
├── cps_plotting.py                 shared region shading for every CPS diagram
├── cps_density.py                  shared spherical KDE + map panels (step 9)
├── make_reference_diagram.py       the schematic of the class regions (no data)
├── cps_calculator_era5tocsv.py     [A. Rodriguez] ERA5 → CPS parameters
├── cps_plots_csv_gris.py           [A. Rodriguez] per-cyclone CPS diagram
├── step1_build_cps_database.py     consolidate + join metadata   (shared)
├── step2_classify_phases.py        CANONICAL phase classification
├── step3_ep_phases.py              CANONICAL EP × phase class
├── step4_phase_figures.py          CANONICAL figures
├── step5_phase_space_figures.py    2x4 CPS diagrams, EPALL + EP1/EP2/EP3
├── step6_transition_trajectories.py  transition paths, marker per timestep
├── step7_case_diagrams.py          individual CPS diagrams, sampled gallery
├── step8_ep_relative_frequency.py  SC and ST frequency per EP vs EPALL
├── step9_density_maps.py           genesis and track density, type x EP
├── run_all.py                      run the canonical pipeline
├── sync_from_remote.sh             pull results + figures to a local machine
├── sensitivity/                    the exploratory tests
│   ├── README.md                   the nine findings and what each decided
│   └── SCIENTIFIC_NOTES.md         exploratory science record
├── cyclone_tracks/                 per-cyclone track files (git-ignored)
├── csv_output/                     per-cyclone CPS CSVs (git-ignored, IRREPLACEABLE)
└── cps_output/                     per-cyclone CPS diagrams (git-ignored, 1979 only)
```

```
results/cps_analysis/
├── cps_timesteps.csv               consolidated timestep database (step 1, shared)
├── phase_timesteps.csv             + canonical per-timestep class
├── phase_states.csv                one row per persistent state, with the TT verdict
├── phase_classification.csv        one row per cyclone
├── phase_definitions.txt           thresholds and rules actually applied
├── ep_phase_crosstab.csv           EP × phase class
├── ep_phase_summary.csv            tidy long form
├── ep_phase_statistics.txt         chi-square, Fisher, region control
├── transition_trajectory_summary.csv  per-timestep structure mix of ST and SD
├── cyclone_lists_by_class.csv      one row per cyclone: id, EP, region, genesis, sequence
├── cyclone_lists_by_class.txt      the same grouped by class, track_ids only
├── case_diagram_index.csv          which cyclone was drawn for each combination
├── density_map_samples.csv         per-panel counts and peak density (step 9)
└── sensitivity/                    outputs of the sensitivity tests

figures/cps_analysis/
├── fig0_cps_reference.png          the class regions, schematic, no data
├── fig1_phase_composition.png      phase class by EP
├── fig2_phase_space.png            CPS occupancy, canonical thresholds
├── fig3_transitions.png            onset, duration, seasonality
├── fig4_tropical_runs.png          the TT test, visually
├── fig5_phase_space_by_ep.png      2x4 CPS diagram, all cyclones
├── fig6_phase_space_by_ep_single_state_sc.png
│                                   2x4 CPS diagram, single-state SC only
├── fig7_transition_trajectories.png  ST and SD paths, structure per timestep
├── fig8_ep_relative_subtropical.png  candidate manuscript figure: SC and ST
│                                   frequency per EP against EPALL
├── fig9_genesis_density_<set>_<mode>.png   cyclogenesis density, type × EP
├── fig10_track_density_<set>_<mode>.png    whole-life density, type × EP
│                                   set  = identified | characteristics
│                                   mode = anomaly | absolute
├── cases/                          one sampled case per class × year × region
│   ├── EC/  EC_like/  SC/  SC_like/  SD/  ST/  TC/  TC_like/  undetermined/
│   └── e.g. TC/cps_TC_1998_LA-PLATA_19980144.png
└── sensitivity/                    figures from the sensitivity tests
```

`cyclone_tracks/`, `csv_output/` and `cps_output/` are git-ignored (~102 MB, ~13,600 files),
as are all `results/` CSVs and `figures/` PNGs.

---

## Status

- CPS parameters computed for 6,776 / 6,789 cyclones (99.8%); **13 missing**, mostly 2009.
- Canonical pipeline (reference diagram + steps 1–9) complete and reproducible from
  `csv_output/` alone.
- Sensitivity suite complete and preserved under `sensitivity/`.
- Externally checked against documented named cyclones: **Bapo (2015) and Cari (2015) are
  both classified subtropical**. Most other named systems form outside the catalogue's
  genesis boxes; Raoni, Yakecan, Akará and Biguá postdate it.
- **Open**: the 2 accepted tropical runs (19911137, 19980144) and the 182 single-state SC cyclones
  have not been inspected case by case.

## Environment

`pandas`, `numpy`, `scipy`, `matplotlib`, `tqdm`, `scikit-learn` (the KDE in step 9),
`statsmodels` (step 8), `xarray` (calculator only), and `cartopy` for the land/ocean mask and
the step-9 maps. If cartopy's Natural Earth shapefile is unavailable offline, the
ocean clause of the TT test is skipped and the run reports that it did so.
