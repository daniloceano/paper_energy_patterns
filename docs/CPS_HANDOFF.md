# CPS handoff after repository cleanup

Prepared on 2026-09-28. This is an operational handoff, not a new CPS analysis.

## Start here

- GitHub: `https://github.com/daniloceano/paper_energy_patterns`.
- Workstation checkout: `/Users/danilocoutodesouza/Documents/Programs_and_scripts/paper_energy_patterns`.
- Server: SSH alias `swell`; checkout `/p1-swell/danilocs/paper_energy_patterns`.
- Both checkouts use `main`, synchronized with GitHub after cleanup. The last
  scientific merge is `7eba356`; the subsequent cleanup commit adds this handoff.
- `paper_large_sample_size` is a different repository. Some old conversation
  environments start there: explicitly set the working directory above.
- Official site: `https://paper-energy-patterns.vercel.app` (Vercel production
  follows `main`). The completed LEC–field deployment at `7eba356` succeeded.
- The previous refresh branches and temporary server worktrees have been retired.
  Start the CPS work from current `main`, in a new `codex/` branch. Do not reuse
  the archived checkout paths or replay old stashes.

## User's working rules

1. Work incrementally on code, computational results, and a dedicated CPS site
   section. Present each completed increment for approval.
2. `docs/energy_patterns_clim_dyn/` is only an occasional, read-only backup of
   the Overleaf project. Agents must never modify, regenerate, compile,
   synchronize, rename, delete, or copy files into that directory. Overleaf is
   the sole manuscript workspace and canonical source; Danilo updates the
   repository backup manually. GitHub remains canonical for code and
   computational results.
3. Leave new CPS changes local for review. Do not infer permission for new
   commits, push, merge, or publication from the completed cleanup authorization.
4. End each task with context, a PASS/FAIL verification verdict, changed files
   and reasons, and an ordered "O que falta / o que você precisa fazer" list.
5. Satellite images of the ten cyclones closest to each EP centroid are a later,
   separate conversation. The CPS front does not start that work.

## Verified environment

On `swell`, use the existing scientific environment explicitly:

```bash
ssh swell
cd /p1-swell/danilocs/paper_energy_patterns
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLBACKEND=Agg
/home/danilocs/.conda/envs/paper_energy_patterns/bin/python --version
/home/danilocs/.conda/envs/paper_energy_patterns/bin/python scripts/cps_analysis/run_all.py --help
```

Verified: Python 3.13.11, pandas 2.3.3, imports of numpy, scipy, matplotlib,
cartopy, scikit-learn, statsmodels, xarray, tqdm and netCDF4; imports of the CPS
criteria, plotting, density and database modules; corrected-clustering provenance
check. `--help` was exercised without running the scientific pipeline.

`/opt/anaconda3/bin/conda` is the functioning Conda installation. If activation is
preferred, source `/opt/anaconda3/etc/profile.d/conda.sh`, then
`conda activate /home/danilocs/.conda/envs/paper_energy_patterns`.
Do not use `/p1-swell/danilocs/miniconda3/bin/conda`: its launcher references an
unavailable `/discos-varal/...` path. No global Conda configuration was changed.
The default server Python is a different environment; `PYTHONNOUSERSITE=1`
avoids unrelated user-site packages shadowing the project environment.

Workstation Python `/Users/danilocoutodesouza/anaconda3/bin/python` also passes
the CPS dependency imports. Node v25.8.1 and npm 11.11.0 are available via
`/opt/homebrew/bin`. The existing `web/node_modules` is installed; the scientific
release already passed the site build. Run site checks from `web/` and avoid
rerunning global environment setup on either established checkout.

## Data inventory and populations

All relative paths below are relative to the checkout, on both machines unless
marked server-only. Raw input checksums were compared across machines.

| Input | Location and verified state |
|---|---|
| Original CPS diagnostics | `scripts/cps_analysis/csv_output/CPS_*.csv`: 6,776 files; all SHA-256 hashes match workstation/server |
| Corrected clustering | `results/cluster/kmeans_clustered_data.csv`: 3,820 rows; SHA-256 `b40dec26ec849ff1fa2d4171db0d9e7579ff1e94b52583f3fadc480b01c5d1da` on both machines |
| EP mapping | `results/cluster/cluster_to_ep.json`: EP1=548, EP2=860, EP3=2,412; cluster 0→EP2, 1→EP3, 2→EP1 |
| Corrected LEC derived products | `data/corrected/`, including `energy_cache_corrected.parquet` and `tracks_with_energetics_corrected.csv` |
| Full corrected LEC run | Server-only `/p1-swell/danilocs/lec_climatology_corrected_v2`; workflow maintained in the separate `lec-climatology-rerun` repository |
| ERA5 composite/LEC–field subset | 2,733 cases: EP1=421, EP2=650, EP3=1,662. This is not the whole clustering population or a predefined CPS denominator |
| Expanded AFC climatology | Server-only `data/era5_ep_structure/afc_climatology_expanded/` |
| Derived ERA5 fields | Server-only `data/era5_ep_structure/derived_corrected_2to3/` |
| Existing CPS outputs | `results/cps_analysis/` and `figures/cps_analysis/`; retained as previous-run outputs, not certified for the corrected populations |

**The original CPS CSVs are irreplaceable without a new ERA5 download and
recomputation.** Their source NetCDF archive was not retained. They are ignored
by Git but have matching copies on both machines and a separate backup archive.
Never use `git clean -fdx` or discard ignored directories to make a checkout clean.

Final local `results/ep_structure`, `figures/ep_structure`,
`results/lec_field_dependence` and `figures/lec_field_dependence` were copied into
the main server checkout, with per-file SHA-256 verification. Their older server
versions were moved into the cleanup archive, not mixed with the refreshed files.
Other scientific data directories were preserved in place.

## CPS work still required

The CPS code, exporter and `/analyses/cps` route already exist. Their presence
does not mean the corrected CPS analysis is implemented and validated.

Begin with `scripts/cps_analysis/README.md`, `SCIENTIFIC_NOTES.md`,
`step1_build_cps_database.py`, `cps_criteria.py`,
`scripts/web/extract_cps_site_data.py`, and `web/src/app/analyses/cps/`.

- Audit the existing CPS inputs and joins against the corrected clustering;
  explicitly report missing IDs, sampling times and final denominators.
- Do not reuse the historical CPS denominator of 3,812 or substitute the
  2,733 ERA5 subset. Determine the CPS overlap with the current 3,820 clustered
  cyclones. Historical README/scientific-note counts remain pending review.
- `step1_build_cps_database.py` currently loads track metadata through
  `scripts/utils/load_data.py`, which reads a public GitHub CSV. Check that
  lineage against corrected/local tracks before recomputation. Network access
  and the semantics of this join remain part of the CPS audit.
- Reuse the original per-cyclone CPS CSVs and existing scripts. Do not begin
  by downloading ERA5 or running the old calculator.
- Keep canonical analysis and sensitivity results distinct. Validate the
  criteria and persistence rules before presenting new results on the site.
- The existing `sync_from_remote.sh` defaults to the older `master.iag.usp.br`
  route and `/discos-varal/...` paths. For this machine, use `ssh swell` and the
  verified `/p1-swell/...` checkout; adapt the helper deliberately if needed.
- Implement/review one scientific increment at a time, then update the dedicated
  CPS site section and request approval. No CPS calculations were rerun during
  cleanup, and no fresh CPS scientific conclusions were approved here.

## Cleanup and recovery

Server archive:
`/p1-swell/danilocs/repository_archives/2026-09-28-cps-handoff/`.

Workstation archive:
`/Users/danilocoutodesouza/Documents/Programs_and_scripts/repository_archives/2026-09-28-cps-handoff/`.

- `repository-before-cleanup.bundle` (server) and `local-before-cleanup.bundle`
  (workstation) preserve Git history, deleted branch tips and the latest stashes.
- `older-stash.bundle` preserves the additional server stash `976a941` and
  requires base commit `aaba6a1`, available in the full server bundle.
- `era5-composites-refresh.tar` and `lec-field-dependence-refresh.tar` preserve
  complete retired worktrees, including ignored results/figures/logs. They were
  compared against the originals before removal.
- `main-before-update.tar` and `main-uncommitted.patch` preserve the server
  files potentially replaced during its fast-forward to approved `main`.
- `main-generated-before-update/` holds the four older output directories
  replaced by the final workstation results.
- `cps-original-inputs.tar` and `cps-original-inputs.sha256` are backed up on both
  machines; the manifest covers all 6,776 CSVs.
- `current-analysis-outputs.tar`, its checksum manifest, and the server
  verification log record the restored final scientific outputs.
- The workstation's old stash `a327e75` was also exported to
  `local-legacy-energy-cache.tar` and `.patch`; it is historical and must not
  replace the corrected energy cache.
- PR #1 was closed without merging and its branch deleted. `pr-1.json` and the
  workstation bundle preserve its description and history.

Recover into a **new directory**, not over the active checkout. For a Git
snapshot use `git clone <full-bundle> <new-directory>`. For a retired worktree,
extract its tar into a recovery directory; its `.git` file points to a retired
registration, so recover selected data/files or establish a new Git checkout
instead of treating that `.git` file as active. No garbage collection or
destructive force-push was used.
