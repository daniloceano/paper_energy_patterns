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
finishes the rest. Both `step2` and `step3` are resumable.

**On the local machine** (after the remote run):

```bash
bash scripts/explosive_cyclones_analysis/sync_from_remote.sh --dry-run   # preview
bash scripts/explosive_cyclones_analysis/sync_from_remote.sh             # pull tables/figures
python scripts/explosive_cyclones_analysis/step5_figures_tables.py       # figures
```

**Smoke test** (a handful of cyclones, end-to-end):

```bash
python scripts/explosive_cyclones_analysis/run_all.py --download --process --sample 5 --workers 4
```

`run_all.py` runs only the light steps (1, 4, 5) by default; pass `--download` / `--process`
to include the heavy steps.

---

## Outputs

`results/explosive_cyclones/`
- `ep_membership.csv` — track_id, cluster, ep
- `tracks_by_ep.csv` — full hourly tracks with `ep` (master input for step2/step3)
- `ep_population_summary.csv` — cyclone count per EP
- `central_pressure_timeseries.csv` — per-timestep central MSLP, offset, flags (step3)
- `ndr_by_cyclone.csv` — NDR_max, bomb flag, intensity class per cyclone (step4)
- `bomb_frequency_by_ep.csv` — aggregated bomb frequency and classes by EP (step4)

`figures/explosive_cyclones/`
- `fig_bomb_frequency_by_ep`, `fig_ndr_distribution_by_ep`, `fig_intensity_class_by_ep` — results
- `fig_offset_distribution`, `fig_flag_fraction_by_phase` — method validation

---

## Key parameters (edit at the top of each step)

- Search radii: `R0_DEG = 3.0`, `R1_DEG = 5.0`; continuity `MAX_JUMP_DEG = 4.0` (step3)
- Download box buffer `BOX_BUFFER_DEG = 6.0`, time padding `TIME_PAD_HOURS = 12` (step2)
- Deepening window `WINDOW_H = 24` (centred), gap fill `GAP_FILL_H = 2` (step4)
- NDR uses **sin(latitude)**, reference **60°**; bomb threshold **1 Bergeron**;
  classes weak [1.0, 1.3) / moderate [1.3, 1.8] / intense (>1.8) (step4)

## Reused utilities

- `scripts/utils/load_data.py` — `load_tracks()`
- `scripts/utils/ep_mapping.py` — `CLUSTER_TO_EP`, `EP_COUNTS`, `EP_COLORS`, labels
- Download/validation pattern adapted from `scripts/ep_structure_analysis/step2_download_era5_parallel.py`
