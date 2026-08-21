# Corrected LEC climatology rerun audit

Audit date: 2026-08-21.

## Population and dependencies

- Tracked `data/energy_cache.parquet`: 25,000 phase rows, 6,789 cyclones.
- Ordered complete-lifecycle rule: 3,820 systems; all seven clustering
  variables are finite after phase aggregation.
- PCA/K-Means outputs: the same 3,820 IDs; EP1=444, EP2=979, EP3=2,397.
- `ep1_cases.csv`: 332 cases. EP structure adds a 24-hour intensification
  filter and is not a climatology source.
- Clustering builds 28 features (seven terms x four phases). EP assignments
  feed article figures, vertical/Ck analyses, statistics, composites, and web
  exports.

Complete positions come from the 631,009-row, 6,789-cyclone processed extract
of Zenodo DOI 10.5281/zenodo.18133432. Preparation records its hash. The old
mutable GitHub raw URL is insufficient provenance and is not a production pin.

## Why the EP1 workflow was not generalized

The old workflow selects a downstream EP1 subset, automatically runs `git
pull`, couples CDS and compute in five jobs, sometimes equates a directory with
completion, replaces destinations, has no durable state machine/active clock,
and uses process-wide CDS configuration. The corrected workflow freezes
commits, isolates outputs/credentials, separates queues, validates content,
applies backpressure, and resumes from SQLite.

## Toolkit and server

- Source: `/p1-swell/danilocs/LorenzCycleToolkit`, audited on `main`.
- Pinned: `d38cda7e37d8e8a3a937a5919640a94bef19e34a`.
- Contained correction/release 2.0.0:
  `d07707767c2962fed0475ff4573e7d15a97f8c69`.
- `CHANGELOG.md` explicitly records numerical corrections to `Ca`, `Ck`,
  boundary geopotential fluxes, averaging, vertical headers, tendencies, and
  NaN handling. The server analytic equation suite passed 49/49.
- Production uses a clean detached worktree and never pulls.
- Resources: 112 logical CPUs, 1 TiB RAM, 130 TiB available on `/p1-swell`.
- Credentials: 39 token lines. Permission was tightened from `0644` to `0600`;
  no value was printed or copied.

## Configuration and discrepancies

- Exact 3-hour UTC positions from the hourly track archive.
- Moving 15 x 15 degree domain; ERA5 `u`, `v`, `t`, `w`, `z`; residuals on.
- 37 requested levels (1-1000 hPa); 32 analysis levels (10-1000 hPa).
- Integrated and pressure-level outputs are mandatory.

The manuscript says 100-1000 hPa and one caption says 6-hourly, while code and
archived results use 10-1000 hPa and 3-hourly data. These method/documentation
discrepancies require author review after the corrected database completes.

