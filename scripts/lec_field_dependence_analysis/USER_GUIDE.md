# User Guide — LEC Field Dependence Pipeline

> **For daily use.** Start here.
>
> → Methodology and scientific decisions: [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md)
> → Technical reference and step details: [README.md](README.md)
> → Error diagnosis and known issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## The main workflow

```
[local]   A. (optional) clean previous outputs
[local]   B. sync your local results to server   (steps 1–3 must be done)
[server]  C. run the full pipeline in background
[local]   D. monitor from your laptop
[local]   E. transfer results back when done
```

Steps 1–3 are lightweight (no ERA5 needed) and run locally.
Steps 4–9 are heavy (require per-cyclone ERA5 files) and run on the remote server.

---

## A — Clean previous outputs

Use this when you want a completely fresh run from scratch.

**See what would be deleted (safe, no changes):**
```bash
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --all
```

**Actually delete everything:**
```bash
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --all --yes
```

**Delete only specific scopes:**
```bash
# Intermediate chunk files only (keep final merged results)
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --chunks --yes

# Logs only
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --logs --yes

# Results + figures (keep logs)
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --results --figures --yes
```

The script never touches anything outside `results/lec_field_dependence/`,
`figures/lec_field_dependence/`, and the pipeline's own log files.

You can also use the `--clean` flag inside the orchestrator to clean immediately
before a run:
```bash
# Clean + run in one command
bash run_pipeline.sh --era5-dir /data/era5/ --clean --background
```

---

## B — Run steps 1–3 locally (one-time, or after data changes)

```bash
cd ~/Documents/Programs_and_scripts/paper_energy_patterns
conda activate paper_energy_patterns

python scripts/lec_field_dependence_analysis/step1_consolidate_metadata.py
python scripts/lec_field_dependence_analysis/step2_build_lec_table.py
python scripts/lec_field_dependence_analysis/step3_map_era5_fields.py
```

Then sync the results folder to the remote server:
```bash
rsync -avz --progress \
    results/lec_field_dependence/ \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/results/lec_field_dependence/
```

---

## C — Run the full pipeline on the remote server

SSH into the server, then:

```bash
cd /discos-varal/swell/p1-swell/danilocs/paper_energy_patterns
conda activate paper_energy_patterns

# Standard run: 16 parallel chunks per step, 4 workers per chunk
bash scripts/lec_field_dependence_analysis/run_pipeline.sh \
    --era5-dir /path/to/era5/ \
    --background
```

The `--background` flag detaches the pipeline from your SSH session (nohup).
It prints the process PID and the path to the live log, then exits immediately.
The pipeline keeps running even if you close the terminal.

**High-parallelism run (for large servers):**
```bash
bash scripts/lec_field_dependence_analysis/run_pipeline.sh \
    --era5-dir /path/to/era5/ \
    --n-chunks 32 --workers 8 \
    --background
```

**Pipeline execution model:** steps run **sequentially** — each step finishes
completely before the next one starts. Within each heavy step (4, 5, 7),
`--n-chunks` parallel background jobs run simultaneously. This gives high
throughput without any risk of inter-step conflicts.

---

## D — Monitor execution (from your laptop)

Open a second terminal, SSH into the server, and run the monitor:

```bash
# Live refresh every 15 seconds (press Ctrl+C to stop)
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch

# Snapshot (no refresh)
python scripts/lec_field_dependence_analysis/monitor_pipeline.py

# Show last log lines for running steps
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch --log-tail
```

Status icons: `✓ DONE` · `▶ RUNNING` · `◑ PARTIAL` · `✗ FAILED` · `· PENDING`

You can also tail the orchestrator log directly:
```bash
tail -f logs/orchestrator_*.log
```

---

## E — Transfer results to your local machine

When the pipeline finishes, run the interactive transfer script locally:

```bash
bash scripts/lec_field_dependence_analysis/transfer_guide_scp.sh
```

It will verify pipeline outputs on the server, then guide you through
transferring CSVs, figures, and logs section by section.

For a quick manual transfer of just the essential CSVs and figures:
```bash
# Results
rsync -avz --progress \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/results/lec_field_dependence/ \
    results/lec_field_dependence/

# Figures
rsync -avz --progress \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/figures/lec_field_dependence/ \
    figures/lec_field_dependence/
```

---

## Re-running part of the pipeline

**Resume an interrupted run (skip finished steps):**
```bash
bash run_pipeline.sh --era5-dir /path/to/era5/ --skip-done --background
```

**Run only specific steps:**
```bash
bash run_pipeline.sh --era5-dir /path/to/era5/ --only 7,7b,8,8b --background
```

**Run significance tests only (locally, no ERA5 needed):**
```bash
python scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py --lec-only
python scripts/lec_field_dependence_analysis/step8b_significance_figures.py
```

---

## When the pipeline fails

By default the pipeline **does not stop** when a step fails — it continues and
records every failure. At the end, the orchestrator log prints a summary:

```
✗  PIPELINE FINISHED WITH 2 FAILED STEP(S)
   Failed steps:
     ✗  [step4]  2/16 chunks failed  logs: logs/step4_chunk*_.log
     ✗  [step6]  exit=1  log: logs/step6_....log
   To re-run only failed steps, use --only <steps> --skip-done
```

**Steps to take:**
1. Open the log file shown for the failed step.
2. Find the Python traceback or error message.
3. Consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for known issues.
4. Fix and re-run only the failed steps:
   ```bash
   bash run_pipeline.sh --era5-dir /path/to/era5/ --only 4,6 --skip-done --background
   ```

If you want the pipeline to halt immediately at the first failure:
```bash
bash run_pipeline.sh --era5-dir /path/to/era5/ --stop-on-error --background
```

---

## Quick-reference: all orchestrator flags

| Flag | Default | What it does |
|------|---------|--------------|
| `--era5-dir PATH` | — | **Required.** Per-cyclone ERA5 directory |
| `--background` | off | Detach under nohup (survives SSH disconnect) |
| `--clean` | off | Wipe previous results + logs before running |
| `--dry-run` | off | With `--clean`: preview deletions, don't delete |
| `--n-chunks N` | 16 | Parallel jobs per heavy step (4, 5, 7) |
| `--workers N` | 4 | CPU workers inside each chunk job |
| `--skip-done` | off | Skip steps whose outputs already exist |
| `--only STEPS` | all | Run only listed steps, e.g. `"4,5,6"` |
| `--stop-on-error` | off | Halt at first failure (default: continue all) |
| `--conda-env NAME` | `paper_energy_patterns` | Conda environment name |
