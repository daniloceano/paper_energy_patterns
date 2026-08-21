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

Downloads start at 2 and may rise to 8 after clean completion windows. HTTP
429/5xx, timeouts, and network degradation lower the limit and cool down keys;
authentication failures quarantine a key for six hours. Retries use capped
exponential backoff plus jitter (7 download/3 compute attempts). This is
resilience, not quota bypass.

Compute has an independent initial limit of 8. With 112 logical CPUs, 1 TiB
RAM, and 130 TiB free, this is conservative for the real pilot. Adjust only
after measured RAM/I/O/runtime. Backpressure caps buffered cases at 16.

Before the pilot, discover accounts whose owners accepted the official ERA5
licence. The preflight submits only one tiny request per account, records no
credential value, and disables unlicensed accounts for 30 days:

```bash
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.preflight_keys \
  --run-root "$RUN"
```

The 2026-08-21 server preflight found 2 authorized accounts out of 39; 36
required licence acceptance and 1 failed authentication. Accounts in either
hard-disabled state remain excluded until the preflight is explicitly rerun.

## Initialize and validate pilots

Run in the `paper_energy_patterns` conda environment:

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.prepare \
  --run-root "$RUN" \
  --track-source /p1-swell/danilocs/paper_energy_patterns/data/tracks_SAt_filtered_with_energetics_processed.csv \
  --periods-source /p1-swell/danilocs/paper_energy_patterns/data/temp_lec_zenodo/LEC_Results_energetic-patterns \
  --ep1-cases /p1-swell/danilocs/paper_energy_patterns/results/ep_structure/ep1_cases.csv \
  --download-workers 2 --max-download-workers 8 --compute-workers 8
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline \
  provision --run-root "$RUN"
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline \
  pilot --run-root "$RUN"
```

Preparation chooses minimum-duration, median-duration, 99th-percentile long,
and EP1 cases. The upper-tail case avoids using the globe-spanning absolute
maximum as an unrepresentative CDS/storage benchmark. Production remains
locked until every pilot is `COMPLETE`:

```bash
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline \
  approve-production --run-root "$RUN"
```

## Persistent operations

Start/resume (same command after a shutdown):

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
tmux new-session -d -s lec-climatology \
  "cd /p1-swell/danilocs/paper_energy_patterns_corrected && exec conda run --no-capture-output -n paper_energy_patterns python -m scripts.lec_climatology_rerun.pipeline production --run-root '$RUN' >>'$RUN/logs/scheduler.log' 2>&1"
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

The ETA uses `cumulative_active_runtime`, advanced only by the running
scheduler. Shutdown days do not count. Once pilots exist, robust per-timestep
costs drive the estimate and uncertainty interval.

## Rebuild downstream products (only after 3,820 COMPLETE)

The cache builder refuses partial state:

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
conda run -n paper_energy_patterns python -m scripts.lec_climatology_rerun.build_corrected_cache \
  --run-root "$RUN"
PAPER_ENERGY_CACHE="$RUN/processed/energy_cache_corrected.parquet" \
  conda run --no-capture-output -n paper_energy_patterns \
  python scripts/cluster_analysis_energy_patterns/run_all.py
```

Review the corrected cache and new clustering before generating/replacing
scientific figures. Publish corrected artifacts as a separately versioned
dataset rather than overwriting the legacy dataset in place.
