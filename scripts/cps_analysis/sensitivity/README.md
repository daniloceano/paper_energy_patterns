# CPS Sensitivity Tests

**These are not the canonical analysis.** They are the exploratory runs that established
the methodology now implemented in `../step2_classify_phases.py` and downstream. They are
kept for reference, for the paper's sensitivity discussion, and so that the design choices
in the canonical analysis can be traced back to the evidence that motivated them.

The canonical results live in `results/cps_analysis/` and `figures/cps_analysis/`.
Everything produced here goes to the `sensitivity/` subfolder of each.

---

## What is here

| Script | What it tests |
|---|---|
| `s1_classify_cyclone_types.py` | **Six threshold sets × four identification rules.** Three South Atlantic sets (C01, GOZZO14, C03) and three cross-basin controls (YANASE14 global, CAVICCHIA19 Australian ECLs, GUISHARD09 North Atlantic), each under `type_any`, `type_persistent`, `type_protocol`, `type_strict`. |
| `s2_ep_crosstab.py` | EP × thermal type for every combination, with region stratification and genesis-band conditioning. |
| `s3_lifecycle_timing.py` | **The warm-seclusion diagnosis.** Life-cycle phase composition of each class, onset relative to genesis, attrition as the rules tighten. |
| `s4_distributions.py` | Seasonal, interannual, geographic and life-cycle-property distributions. |
| `s5_episodes_and_cases.py` | Every episode with start/end dates, plus the check against documented named cyclones (Bapo, Cari, Catarina, Anita, Arani, Deni, Eçaí, Guará, Iba, Raoni, Yakecan, Akará, Biguá). |

Run with:

```bash
python scripts/cps_analysis/sensitivity/run_sensitivity.py
```

Requires `results/cps_analysis/cps_timesteps.csv` from step 1 of the canonical pipeline.

---

## What these tests established

Each of these findings is the reason for a specific choice in the canonical analysis.

**1. Persistence alone does not exclude warm seclusions.** Under `type_persistent`
(≥ 36 h) the tropical class still held 16 cyclones, at a median latitude of **−57.7°** with
**93% of timesteps in the mature/decay phases** and a median onset of **75 h after
genesis**. A Shapiro–Keyser seclusion is a real, sustained structure — it passes a
persistence filter comfortably.
→ *Canonical consequence: the tropical-transition test.*

**2. The genesis-relative onset criterion is what removes them.** Adding Guishard et al.'s
(2009) 24-h clause collapsed the tropical class to **0–1 cyclones under all six threshold
sets**, including the three from other basins.
→ *Canonical consequence: the timing evidence is real, but see finding 4 for how it was
finally implemented.*

**3. The threshold choice is not the dominant uncertainty for the tropical class, but it is
for the subtropical one.** Subtropical counts range over a factor of 6–8 between threshold
sets at every level of strictness (131–796 persistent, 13–104 strict). Tropical counts
collapse to 0–1 regardless.
→ *Canonical consequence: one threshold set is fixed and stated (de Souza et al. 2026);
the sensitivity spread is reported rather than hidden.*

**4. A genesis-latitude gate does not stop seclusions.** Six of the sixteen persistent
tropical runs belong to cyclones that formed **inside** the 20–40°S band, travelled ~30°
poleward, and only then acquired a warm core at 55–62°S.
→ *Canonical consequence: the geographic test is applied to the tropical run itself, not to
genesis.*

**5. A life-cycle-phase rule alone is not safe.** Accepting a tropical run when it falls in
the incipient/intensification phase admitted exactly one case — track **20160337, at
−54.7°S**, subsequently checked against satellite imagery and confirmed to be a classic
extratropical cyclone.
→ *Canonical consequence: the phase of the tropical run is recorded as a diagnostic, never
used as a gate.*

**6. Secondary intensification does not discriminate.** Only 14.0% of cyclones with a
tropical timestep show a secondary life-cycle labelling, *below* the 18.5% population
baseline.
→ *Canonical consequence: not used.*

**7. Raw timestep sequences oscillate.** 158 distinct class sequences; the commonest
non-pure one is EC → SC → EC (775 cyclones); 24.2% of the population shows ≥ 4
alternations. A "genesis as X, later Y" rule has no defined answer for these.
→ *Canonical consequence: states are persistence-gated before any sequence is built.*

**8. External validation.** Of thirteen documented named cyclones, only two are actually
testable against this catalogue — **Bapo (2015) and Cari (2015)** — and **both are
classified subtropical**. The rest form outside the genesis boxes (Anita, Arani, Deni,
Guará, Iba, Catarina — nearest track 1,634 km away) or postdate it (Raoni 2021, Yakecan
2022, Akará 2024, Biguá 2024).
→ *Canonical consequence: the population is an extratropical catalogue; its counts describe
thermal structure within it, not a basin climatology.*

**9. Two-sided B.** The two-sided subtropical bound (−25 < B < 25) retains 97.1% of
subtropical timesteps; the 2.9% it removes sit at a median latitude of −45.8° and are
decay-dominated.
→ *Canonical consequence: two-sided bound adopted, matching de Souza et al. (2026).*
