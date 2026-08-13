# Explosive Cyclones (Bombs) by Energy Pattern

Assess the occurrence of **explosive cyclones** ("bombs") among the EP1, EP2 and EP3
cyclones of the energetic-patterns study. The bomb classification is a **surface-pressure
diagnostic** layered on top of the existing vorticity-based life cycle: cyclones are tracked
with 850-hPa relative vorticity (no central pressure), so we download ERA5 mean sea level
pressure (MSLP) along each track, assign a central pressure to every timestep, and apply the
Sanders & Gyakum (1980) normalized deepening rate (NDR) criterion.

See `SCIENTIFIC_NOTES.md` in this folder for the full methodology, equations, assumptions and
references.

---

## Where each step runs

| Step | What | Where | Parallelism |
|---|---|---|---|
| step1 | Select full EP populations (444 / 979 / 2397) + their tracks | anywhere | — |
| step2 | Download storm-following ERA5 MSLP over each full track | **remote** | **light** (CDS limits; ~6 jobs) |
| step3 | Assign central pressure (A+B gradient descent) | **remote** | **heavy** (e.g. `--workers 100`) |
| step4 | Compute NDR, classify bombs, aggregate by EP | anywhere | — |
| step5 | Results + validation figures | local (after sync) | — |
| step6 | Relative explosive frequency by EP vs EPALL (Wilson + Fisher/Holm) | anywhere | — |
| step7 | Genesis / track / deepening density maps (spherical KDE) | anywhere | — (a few minutes) |

The heavy data (`data/era5_explosive_cyclones/*.nc`) stays on the remote server and is
git-ignored. Only the lightweight tables/figures are synced back.

---

## How to run

**On the remote server** (heavy):

```bash
python scripts/explosive_cyclones_analysis/step1_select_ep_populations.py
python scripts/explosive_cyclones_analysis/step2_download_mslp_tracks.py --jobs 6
python scripts/explosive_cyclones_analysis/step3_assign_central_pressure.py --workers 100
python scripts/explosive_cyclones_analysis/step4_compute_ndr_classify.py
```

`step3` only processes cyclones whose MSLP file already exists, so it can run while `step2`
finishes the rest. Both `step2` and `step3` are resumable. `step2` retries CDS job-queue
rejections with exponential backoff and shuffles the processing order (fixed seed) so a
saturated queue doesn't silently skew the downloaded sample toward one part of the record.

To check progress while `step2` runs in the background (e.g. under `nohup`):

```bash
python scripts/explosive_cyclones_analysis/step2_1_monitor.py              # one-shot snapshot
python scripts/explosive_cyclones_analysis/step2_1_monitor.py --watch      # live refresh
```

**On the local machine** (after the remote run):

```bash
bash scripts/explosive_cyclones_analysis/sync_from_remote.sh --dry-run   # preview
bash scripts/explosive_cyclones_analysis/sync_from_remote.sh             # pull tables/figures
python scripts/explosive_cyclones_analysis/step5_figures_tables.py       # validation figures
python scripts/explosive_cyclones_analysis/step6_bomb_relative_frequency.py
python scripts/explosive_cyclones_analysis/step7_bomb_density_maps.py
```

**Smoke test** (a handful of cyclones, end-to-end):

```bash
python scripts/explosive_cyclones_analysis/run_all.py --download --process --sample 5 --workers 4
```

`run_all.py` runs only the light steps (1, 4, 5, 6, 7) by default; pass `--download` /
`--process` to include the heavy steps, and `--skip-maps` to leave out step7 (the slowest
light step).

---

## Outputs

`results/explosive_cyclones/`
- `ep_membership.csv` — track_id, cluster, ep
- `tracks_by_ep.csv` — full hourly tracks with `ep` (master input for step2/step3)
- `ep_population_summary.csv` — cyclone count per EP
- `central_pressure_timeseries.csv` — per-timestep central MSLP, offset, flags (step3)
- `ndr_by_cyclone.csv` — NDR_max, bomb flag, intensity class per cyclone (step4)
- `bomb_frequency_by_ep.csv` — aggregated bomb frequency and classes by EP (step4)
- `bomb_relative_frequency.csv` — rate, Wilson CI, ratio to EPALL, Fisher/Holm per
  (outcome, EP) (step6)
- `density_map_samples.csv` — one row per density panel drawn: counts, domain coverage,
  peak density (step7)

`figures/explosive_cyclones/`
- `fig_bomb_frequency_by_ep`, `fig_ndr_distribution_by_ep`, `fig_intensity_class_by_ep` — results
- `fig_offset_distribution`, `fig_flag_fraction_by_phase` — method validation
- `fig6_bomb_relative_frequency` — **canonical frequency figure**: explosive rate within each
  EP with Wilson intervals, and its ratio to the pooled EPALL population (step6)
- `fig7a_genesis_density_<set>_<mode>`, `fig7b_track_density_<set>_<mode>`,
  `fig7c_deepening_density_<set>_<mode>` — density maps, with `set` ∈ {explosive, intensity}
  and `mode` ∈ {anomaly, absolute} (step7)

---

## The two aggregate analyses (steps 6–7)

Both are built to the template of the CPS analysis (`scripts/cps_analysis/step8` and
`step9`), so the explosive and subtropical results are read the same way.

**step6 — relative frequency.** Panel (a) is the explosive rate within each EP with Wilson
95% intervals; panel (b) is its ratio to EPALL. The outcomes are a *nested* severity ladder
on the same NDR (≥ 1.0 bomb, ≥ 1.3 moderate-or-intense, ≥ 1.8 intense), so a ratio that
grows along the ladder means the EP is enriched in the **severe tail**, not merely in the
count of bombs. The ratio is a descriptive effect size (each EP is nested in EPALL); the
inferential claim comes from Fisher's exact test of each EP against the other two pooled,
Holm-corrected over the nine contrasts.

> **Denominator.** step6 counts only the cyclones with an *assessable* NDR, i.e. a
> central-pressure series that supports a full 24 h window. step4 instead keeps every
> processed cyclone and so reads a missing NDR as "not a bomb". The unassessable fraction is
> not uniform across EPs (EP3 ~3.3%, EP2 ~1.2%), and EP3 is the low-frequency pattern, so
> the step4 convention slightly exaggerates the contrast. step6 prints both.

**step7 — density maps.** Rows are cyclone class, columns are EPALL / EP1 / EP2 / EP3, for
three kinds of position:

| Kind | Positions | Units | Answers |
|---|---|---|---|
| `genesis` | the cyclogenesis point | events / 10⁶ km² / yr | where is a bomb born |
| `track` | the whole life cycle | cyclone days / 10⁶ km² / yr | where does it live |
| `deepening` | the time of maximum NDR | events / 10⁶ km² / yr | where does it explode |

The estimator is imported from `scripts/cps_analysis/cps_density.py`, not re-implemented, so
these maps, the CPS maps and the manuscript genesis figure are the same calculation
(Gaussian KDE, haversine metric, bandwidth 0.05 rad ≈ 318 km, 2.5° Hoskins–Hodges grid).
The tracks here are **hourly**, unlike the 3-hourly CPS series; step7 subsamples them to
`--cadence` (default 3 h) and weights by `cadence/24`, which leaves the density unchanged in
expectation while making the KDE ~3× cheaper.

---

## Key parameters (edit at the top of each step)

- Search radii: `R0_DEG = 3.0`, `R1_DEG = 5.0`; continuity `MAX_JUMP_DEG = 4.0` (step3)
- Download box buffer `BOX_BUFFER_DEG = 6.0`, time padding `TIME_PAD_HOURS = 12` (step2)
- Deepening window `WINDOW_H = 24` (centred), gap fill `GAP_FILL_H = 2` (step4)
- NDR uses **sin(latitude)**, reference **60°**; bomb threshold **1 Bergeron**;
  classes weak [1.0, 1.3) / moderate [1.3, 1.8) / intense (≥ 1.8) (step4)
- Severity ladder and α = 0.05 with Holm correction (step6)
- KDE bandwidth, grid and map domains: `scripts/cps_analysis/cps_density.py`; track
  subsample `--cadence 3` (step7)

## Reused utilities

- `scripts/utils/load_data.py` — `load_tracks()`
- `scripts/utils/ep_mapping.py` — `CLUSTER_TO_EP`, `EP_COUNTS`, `EP_COLORS`, labels
- `scripts/cps_analysis/cps_density.py` — spherical KDE, map domains and panel helpers (step7)
- Download/validation pattern adapted from `scripts/ep_structure_analysis/step2_download_era5_parallel.py`
- Frequency-figure template adapted from `scripts/cps_analysis/step8_ep_relative_frequency.py`
