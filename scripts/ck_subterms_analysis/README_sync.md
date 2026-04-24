# Sync Guide — Ck Subterms Analysis

Scripts: `scripts/ck_subterms_analysis/`

---

## What is synced

| Source (remote) | Destination (local) | Content |
|---|---|---|
| `results/ck_analysis/` | `results/ck_analysis/` | `*.csv`, `*.txt`, `*.md`, `*.json`, `*.parquet`, `*.feather` — excludes `lec_results/` |
| `results/ck_subterms/` | `results/ck_subterms/` | Audit tables from `step3_validate_and_figures.py` |
| `figures/ck_analysis/` | `figures/ck_analysis/` | All generated figures |
| `figures/ck_subterms/` | `figures/ck_subterms/` | Boxplot / web figures from step3 |

## What is NOT synced

- `results/ck_analysis/lec_results/` — raw LorenzCycleToolkit outputs (~100s GB)
- `data/ck_analysis/era5/` — raw ERA5 data
- `*.nc`, `*.grib`, `*.grb`, `*.zarr`, `*.idx` — binary climate data
- `__pycache__/`, `*.pyc`, large log files

---

## Configuration

Edit the variables at the top of `sync_from_remote.sh`:

```bash
REMOTE_USER="danilocs"
REMOTE_HOST="master.iag.usp.br"
SSH_KEY="$HOME/Documents/Master/id_rsa.danilocs"
REMOTE_BASE="/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns"
```

---

## Running the sync

### Dry run (preview only — no files copied)

```bash
bash scripts/ck_subterms_analysis/sync_from_remote.sh --dry-run
```

### Full sync

```bash
bash scripts/ck_subterms_analysis/sync_from_remote.sh
```

### Also sync pipeline logs

```bash
bash scripts/ck_subterms_analysis/sync_from_remote.sh --logs
```

---

## Before syncing: generate summary CSVs on the remote

If `results/ck_analysis/subterms_by_cyclone.csv` (or equivalent) does not yet
exist on the remote, run the summarisation script **on the remote server** first:

```bash
# On the remote server:
cd /path/to/paper_energy_patterns
python scripts/ck_subterms_analysis/build_ck_subterms_summary.py

# Quick test (first 20 cyclones):
python scripts/ck_subterms_analysis/build_ck_subterms_summary.py --limit 20 --verbose
```

This reads `results/ck_analysis/lec_results/` and produces:

| File | Description |
|---|---|
| `results/ck_analysis/subterms_by_cyclone.csv` | One row per cyclone, phase-mean Ck_1..5 |
| `results/ck_analysis/subterms_by_phase.csv` | Tidy (track_id, phase, subterm, value) |
| `results/ck_analysis/ck_subterms_boxplot_input.csv` | Long format for boxplot |
| `results/ck_analysis/summary_build_report.md` | Validation report |

---

## After syncing: plot the boxplot locally

```bash
# Default: intensification phase
python scripts/ck_subterms_analysis/plot_ck_subterms_boxplot.py

# Another phase
python scripts/ck_subterms_analysis/plot_ck_subterms_boxplot.py --phase mature
```

Outputs:
- `figures/ck_analysis/ck_subterms_boxplot_intensification.png`
- `figures/ck_analysis/ck_subterms_boxplot_intensification.pdf`

---

## Typical workflow

```
[Remote server]
  python scripts/ck_subterms_analysis/build_ck_subterms_summary.py

[Local machine]
  bash scripts/ck_subterms_analysis/sync_from_remote.sh --dry-run   # preview
  bash scripts/ck_subterms_analysis/sync_from_remote.sh             # sync
  python scripts/ck_subterms_analysis/plot_ck_subterms_boxplot.py   # figure
```
