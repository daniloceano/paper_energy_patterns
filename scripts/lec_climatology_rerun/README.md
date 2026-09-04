# Corrected LEC climatology rerun

This workflow recomputes, without overwriting published/legacy outputs, the
semi-Lagrangian Lorenz Energy Cycle climatology used by the article. The rerun
is required because LorenzCycleToolKit 2.0.0 corrected equations and numerical
handling that change scientific results (notably `Ca`, the fifth `Ck` subterm,
`BPhi_Z`, `BPhi_E`, vertical-level alignment, time tendencies, and NaNs).

The production toolkit is immutable: the workflow creates a detached worktree
at commit `d38cda7e37d8e8a3a937a5919640a94bef19e34a`. That commit contains the
2.0.0 correction commit `d07707767c2962fed0475ff4573e7d15a97f8c69`. There is
no automatic `git pull`.

## Audited scientific chain

```text
Atlantic Extratropical Cyclone Tracks Database (1979-2020)
  -> ARG, LA-PLATA, and SE-BR genesis selection: 6,789 cyclones
  -> CycloPhaser phase averages in tracked data/energy_cache.parquet
  -> complete ordered lifecycle + finite Ca,Ck,BAe,BKe,Ae,Ke,Ge: 3,820 cyclones
  -> frozen article lifecycle windows from Zenodo 10.5281/zenodo.18243447
  -> complete 1-hourly positions from Zenodo 10.5281/zenodo.18133432
  -> exact 3-hour UTC positions (hours divisible by 3; no floor/round shift)
  -> ERA5 pressure-level data (u,v,t,w,z)
  -> 15 x 15 degree moving LEC box
  -> LorenzCycleToolKit -t -r, pinned corrected commit
  -> validated per-cyclone integrated and pressure-level CSVs
  -> energy_cache_corrected.parquet (only after all 3,820 are COMPLETE)
  -> PCA / k-means / figures (separate; never on partial data)
```

`results/ep_structure/ep1_cases.csv` is not a population source. It contains a
downstream EP1 subset (332 cases in the current checkout). EP structure also
excludes intensification phases shorter than 24 hours, reducing EPALL from
3,820 to 2,733; that filter does not belong in this rerun.

The source of truth is the committed `data/energy_cache.parquet` plus the
selection implemented in `prepare.population_from_cache`. Preparation writes a
frozen manifest, hashes cache/source/tracks, and records both repository commits.

## ERA5 and LEC configuration

- Time resolution: 3 hours.
- Moving computational domain: 15 x 15 degrees centered at each track point.
- CDS envelope: the full track range plus 15 degrees on every side, matching
  the toolkit downloader.
- Requested levels: 37 levels from 1 to 1000 hPa.
- Actual toolkit control volume: 32 levels from 10 to 1000 hPa. The manuscript
  currently says 100-1000 hPa; code and archived vertical outputs show
  10-1000 hPa. Resolve this in the manuscript, not by silently changing data.
- Variables: geopotential, temperature, vertical velocity, and both winds.
- Flags: moving framework (`-t`), residuals (`-r`), verbose logs (`-v`), ERA5
  namelist (`--cdsapi`), and 3-hour data.
- Lifecycle windows are frozen from the article's archived per-cyclone
  `periods.csv` files (Zenodo DOI 10.5281/zenodo.18243447). Re-running a newer
  CycloPhaser would silently change the population/aggregation independently
  of the LEC equation correction. Secondary cycles are retained: the corrected
  cache will contain 15,829 main-phase period rows, not just 3,820 x 4 rows.

## Storage, state, and validation

Recommended run root:

```text
/p1-swell/danilocs/lec_climatology_corrected_v2/
  config.json  provenance.json  population_manifest.csv  state.sqlite3
  tracks/  phase_windows/  era5/  lec_results/  logs/  worker_progress/  invalid_outputs/
  LorenzCycleToolkit-pinned/
```

Legacy Ck/EP1 results, Zenodo data, and the old cache are never overwritten.
SQLite uses WAL, `synchronous=FULL`, and a single scheduler writer. States are
`PENDING`, `DOWNLOAD_QUEUED`, `DOWNLOADING`, `DOWNLOADED`, `COMPUTE_QUEUED`,
`COMPUTING`, `VALIDATING`, `COMPLETE`, `FAILED_RETRYABLE`, and `FAILED_FINAL`.

Restart reconciles active states by opening artifacts; a directory alone never
means completion. NetCDF checks cover variables, coordinates, levels,
timestamps, dimensions, and readability. LEC checks cover named integrated
terms, finite values, tracks/periods, pressure-level CSVs/timestamps, and the
toolkit completion marker. `.part` paths are renamed only after validation;
invalid results are quarantined.

ERA5 is deleted only after validated `COMPLETE`, because requests, tracks,
hashes, and commits remain reproducible. Set `cleanup_era5_after_complete` to
`false` in `config.json` before starting if intermediates must be retained.

## CDS keys and parallelism

The server has 39 token-plus-label lines in `/p1-swell/danilocs/cds-keys`, mode `0600`.
Only the first whitespace-delimited token is used; the human label is ignored.
Values never enter the repository, database, logs, commands, or monitor. Each
download subprocess gets a unique temporary mode-`0700` `HOME` with one
mode-`0600` `.cdsapirc`, removed on exit. Labels are only `key-001`, etc.

Downloads start at 16 and may rise to 22 after clean completion windows. HTTP
429/5xx, timeouts, and network degradation lower the limit and cool down keys;
authentication failures quarantine a key for six hours. Retries use capped
exponential backoff plus jitter (7 download/3 compute attempts). This is
resilience, not quota bypass.

The two stages are sized from measurement, not symmetry. On 2026-08-24 a
cyclone took a median 496 s to download and 28 s to compute, so a download
worker feeds roughly seventeen compute workers and CDS is the only real
constraint: the server sat at load 4.6 of 112 CPUs and 22 GiB of 1007 GiB.
Downloads are therefore capped at 22 with 27 authorized accounts, leaving five
spare for cooldown rotation, while compute stays at 8 and is still oversized.
Backpressure caps buffered cases at 44, about 7 GiB at 170 MiB per cyclone.
Raise the download ceiling only alongside the authorized-account count.

Before the pilot, discover accounts whose owners accepted the official ERA5
licence. The preflight submits one tiny request per account and records no
credential value. Licence and authentication verdicts arrive with the
submission response, so it neither waits for the job nor downloads a result,
and it releases the queued job; a full 39-account sweep costs seconds per
account. Anything that is not a licence or authentication verdict is retried,
so a flaky CDS cannot demote a good account. Unlicensed accounts are disabled
for 30 days:

```bash
python scripts/lec_climatology_rerun/preflight_keys.py --run-root "$RUN"
```

Re-run it whenever account owners report accepting the licence. The 2026-08-21
sweep found 2 authorized accounts of 39; by 2026-08-25 that had reached 27,
with 11 awaiting licence acceptance and 1 failing authentication. Accounts in
either hard-disabled state stay excluded until the preflight is rerun.

## Initialize and validate pilots

Run in the `paper_energy_patterns` conda environment:

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.prepare \
  --run-root "$RUN" \
  --track-source /p1-swell/danilocs/paper_energy_patterns/data/tracks_SAt_filtered_with_energetics_processed.csv \
  --periods-source /p1-swell/danilocs/paper_energy_patterns/data/temp_lec_zenodo/LEC_Results_energetic-patterns \
  --ep1-cases /p1-swell/danilocs/paper_energy_patterns/results/ep_structure/ep1_cases.csv \
  --download-workers 16 --max-download-workers 22 --compute-workers 8
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline \
  provision --run-root "$RUN"
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline \
  pilot --run-root "$RUN"
```

Preparation chooses minimum-duration, median-duration, upper-5%-duration long,
and EP1 cases. The long case has the smallest CDS envelope within that upper
tail, isolating lifecycle length from globe-spanning spatial-footprint cost.
Production remains
locked until every pilot is `COMPLETE`:

```bash
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline \
  approve-production --run-root "$RUN"
```

## Persistent operations

Production runs from the ordinary server checkout at
`/p1-swell/danilocs/paper_energy_patterns`, on this branch. The run root is a
separate directory, so the checkout carries code only: switching branches or
pulling never touches downloaded ERA5, state, or results.

Start/resume (same command after a shutdown):

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
tmux new-session -d -s lec-climatology \
  "cd /p1-swell/danilocs/paper_energy_patterns && exec conda run --no-capture-output -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline production --run-root '$RUN' >>'$RUN/logs/scheduler.log' 2>&1"
```

Status/monitor, graceful stop, logs, and retry:

```bash
tmux ls
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.monitor --run-root "$RUN"
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.monitor --run-root "$RUN" --watch
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline stop --run-root "$RUN"
tail -f "$RUN/logs/scheduler.log"
tail -f "$RUN/logs/"*_compute.stderr.log
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline retry-failures --run-root "$RUN"
```

Every command above runs on the server: the run root, its SQLite state, and
the ERA5 files exist only there, so a workstation copy of the repository has
nothing to read and fails on the missing `config.json`. To check progress from
a workstation, go through ssh:

```bash
alias lecmon='ssh swell "cd /p1-swell/danilocs/paper_energy_patterns && conda run -n paper_energy_patterns python scripts/lec_climatology_rerun/monitor.py --run-root /p1-swell/danilocs/lec_climatology_corrected_v2"'
```

Scripts run either as `python -m scripts.lec_climatology_rerun.<name>` from the
repository root or as `python scripts/lec_climatology_rerun/<name>.py` from any
directory.

The ETA uses `cumulative_active_runtime`, advanced only by the running
scheduler. Shutdown days do not count. Once pilots exist, robust per-timestep
costs drive the estimate and uncertainty interval.

## Rebuild downstream products (only after 3,820 COMPLETE)

Three builders turn the run root into the artefacts the analysis scripts read.
All of them refuse partial state unless `--allow-partial` is given, which
labels the output `_partial` and is for exploration only: on a growing subset
the population would depend on the moment the script ran.

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
cd /p1-swell/danilocs/paper_energy_patterns

# 1. Phase-mean cache — input to the PCA/k-means Energy Patterns
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.build_corrected_cache \
  --run-root "$RUN" --output data/corrected/energy_cache_corrected.parquet

# 2. Per-timestep tracks + corrected energetics — LPS, case study, phase density
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.build_corrected_tracks \
  --run-root "$RUN"

# 3. Phase-mean vertical profiles, incl. the five Ck subterms for all 3,820
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.build_corrected_vertical_levels \
  --run-root "$RUN"
```

They write into `data/corrected/`, which every downstream script reads through
`scripts/utils/corrected_lec.py`:

| Product | Replaces | Consumers |
|---|---|---|
| `energy_cache_corrected.parquet` | `data/energy_cache.parquet` | cluster analysis (PCA + k-means) |
| `tracks_with_energetics_corrected.csv` | `data/tracks_SAt_filtered_with_energetics_processed.csv` | LPS diagrams, case study, phase density |
| `vertical_phase_means_corrected.parquet` | `data/temp_lec_zenodo/.../{Ca,Ck}_level.csv` | vertical-levels figure, Ck subterms for every EP |

Then rebuild the Energy Patterns and everything that depends on them:

```bash
conda run --no-capture-output -n paper_energy_patterns \
  python scripts/cluster_analysis_energy_patterns/run_all.py
conda run --no-capture-output -n paper_energy_patterns \
  python scripts/ck_subterms_analysis/run_all.py
```

`step4_apply_kmeans.py` re-derives the cluster → Energy Pattern mapping from the
new centroids and records the cache lineage in `results/cluster/cluster_to_ep.json`.
K-means indices are arbitrary, so downstream scripts read that file rather than
assuming the ordering of the previous run, and publication steps refuse to run
while it still points at the legacy cache.

`docs/legacy_data_retirement.md` tracks what remains to be repointed.

Review the corrected cache and new clustering before generating/replacing
scientific figures. Publish corrected artifacts as a separately versioned
dataset rather than overwriting the legacy dataset in place.
