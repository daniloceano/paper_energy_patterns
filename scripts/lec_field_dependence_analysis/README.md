# LEC–Field Dependence Analysis

> **→ Day-to-day use:** see [USER_GUIDE.md](USER_GUIDE.md) — clean, run, monitor, transfer.
> **→ Errors and debugging:** see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
> **→ Methodology and scientific decisions:** see [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md).

Investigates, at the individual-cyclone level, the predictive dependence between Lorenz Energy Cycle (LEC) terms and dynamic/meteorological scalar features derived from ERA5 composite fields, using the **PREDEP** measure (Assunção et al. 2025).

---

## Scientific Question

**How much do the spatial features of the dynamical fields help predict the energetic behaviour of individual South Atlantic cyclones, and does this relationship differ across Energy Patterns?**

---

## PREDEP Direction

The primary analysis direction is:

$$\alpha_{\text{LEC} \mid \text{feature}} = \frac{S_{\text{LEC} \mid \text{feature}} - S_{\text{LEC}}}{S_{\text{LEC} \mid \text{feature}}}$$

- **X** = scalar feature from dynamic field (predictor)
- **Y** = LEC term (response)

This answers: *"how much does the dynamic feature reduce prediction uncertainty of the LEC term?"*

PREDEP is **asymmetric** — this direction is the primary analysis.  The reverse direction is not computed by default.

---

## Sample

Cyclones from all three Energy Patterns that pass the ≥ 24h intensification duration filter (canonical ep_structure methodology):

| EP | N (ep_structure) | Description |
|----|-----------------|-------------|
| EP1 | 332 | High energy conversions |
| EP2 | 776 | Moderate conversions |
| EP3 | 1,625 | Weak/background energetics |

Final eligible count may be smaller after intersection with LEC data availability.

---

## Dynamic Fields of Interest

**Absolute fields** (from per-cyclone ERA5):
- `pv_850` — Potential Vorticity at 850 hPa
- `pv_200` — Potential Vorticity at 200 hPa  
- `adv_T_850` — Temperature Advection at 850 hPa
- `afc_250` — Ageostrophic Flux Convergence at 250 hPa
- `ke_adv_250` — KE Advection at 250 hPa

**EPALL-relative anomaly fields** (cyclone_i − EPALL composite):
Same fields, subtracting the EPALL composite mean.

---

## Scalar Features

Extracted from a 15°×15° inner box centred on the cyclone within the storm-centred domain:

| Feature | Description |
|---------|-------------|
| `domain_mean` | Mean over inner 15°×15° box |
| `centre_value` | Value at cyclone centre |
| `border_north` | Mean of northern strip |
| `border_south` | Mean of southern strip |
| `border_east` | Mean of eastern strip |
| `border_west` | Mean of western strip |
| `contrast_ew` | East − West border mean |
| `contrast_sn` | South − North border mean |
| `quadrant_ne` | NE quadrant mean |
| `quadrant_nw` | NW quadrant mean |
| `quadrant_se` | SE quadrant mean |
| `quadrant_sw` | SW quadrant mean |
| `domain_abs_mean` | Mean of |field| (for signed variables) |

---

## Pipeline

### Steps that run locally

> **⚠️ Step 3 note:** When running locally without `--era5-dir`, step 3 creates a
> manifest with all cases marked `era5_available=False` (dry-run mode). If using the
> **orchestrator** (`run_pipeline.sh`), step 3 is automatically re-run on the remote
> server with `--era5-dir`, so this is handled. If running steps **manually**, re-run
> step 3 on the remote server with `--era5-dir /path/to/era5/` before steps 3b–5.

| Step | Script | Description | Input | Output |
|------|--------|-------------|-------|--------|
| 1 | `step1_consolidate_metadata.py` | Build eligible cases table | `results/ep_structure/`, LEC Zenodo | `step1_eligible_cases.csv` |
| 2 | `step2_build_lec_table.py` | LEC central-timestep means per cyclone | LEC Zenodo | `step2_lec_means.csv` |
| 3 | `step3_map_era5_fields.py` | Map ERA5 field availability (dry-run locally) | Step 1 output | `step3_era5_field_manifest.csv` |

### Steps that require remote/HPC

> **⚠️ Step 3b must run before steps 4 and 5.** It derives the dynamic diagnostic fields
> (`pv_850`, `pv_200`, `adv_T_850`, `ke_adv_250`, `afc_250`) from the raw ERA5 per-cyclone
> NetCDFs. Steps 4 and 5 read from the derived files and will **fail explicitly** if the
> derived directory is missing or empty.

| Step | Script | Description | Input | Output |
|------|--------|-------------|-------|--------|
| **3b** | `step3b_derive_era5_fields.py` | **Derive dynamic fields from raw ERA5** | Raw `*_era5.nc` (per-cyclone) | `{derived-dir}/*_era5_derived.nc`, `step3b_derived_field_manifest.csv` |
| 4 | `step4_extract_features_absolute.py` | Extract scalar features from absolute derived fields | `*_era5_derived.nc` (from step 3b) | `step4_features_absolute.csv` |
| 5 | `step5_extract_features_anomaly.py` | Extract features from EPALL-relative anomalies | `*_era5_derived.nc` + EPALL composite | `step5_features_anomaly.csv` |
| 6 | `step6_integrate_tables.py` | Merge cases + LEC + features | Steps 1-5 | `step6_integrated_*.csv` |
| 7 | `step7_compute_predep.py` | Compute PREDEP for all combinations | Step 6 | `step7_predep_*.csv` |
| 7b | `step7b_ep_significance_tests.py` | Statistical significance between EPs | Steps 1-2 (LEC) + Step 6 (features) | `step7b_diagnostic_table.csv`, `step7b_pairwise_table.csv` |
| 8 | `step8_synthesis_figures.py` | PREDEP heatmaps, rankings, comparisons | Step 7 | `figures/lec_field_dependence/` |
| 8b | `step8b_significance_figures.py` | Significance heatmaps, volcano plots, rankings | Step 7b | `figures/lec_field_dependence/` |
| 9 | `step9_update_docs.py` | Generate pipeline status report | All | `step9_pipeline_status.txt` |

---

## Running on the Remote Server (single command)

> **See [USER_GUIDE.md](USER_GUIDE.md) for the full operational workflow.**

### Before running on the server: local smoke test (recommended)

Download 6 real representative cyclones and validate the pipeline logic locally
before committing to a full server run:

```bash
# Download test data (one-time, ~few hundred MB):
bash scripts/lec_field_dependence_analysis/fetch_test_data.sh

# Run smoke test — exercises step3b → 4 → 5 → 6 → 7 in an isolated temp dir
bash scripts/lec_field_dependence_analysis/run_smoke_test.sh
```

See [`data/test/lec_field_dependence/README.md`](../../data/test/lec_field_dependence/README.md)
for details on which cyclones are included and why they were chosen.

Use the provided orchestrator to run steps 3b–9 in one shot.  Steps 1–3 must have been completed locally first.

```bash
# Activate the conda environment
conda activate paper_energy_patterns

# Full pipeline — 16 parallel chunks per step, 4 workers per chunk, detached
bash run_pipeline.sh --era5-dir /path/to/era5/ --background

# Custom derived-dir (default: {era5-dir}/derived/)
bash run_pipeline.sh --era5-dir /data/era5/ --derived-dir /scratch/derived/ --background

# Clean previous outputs first, then run
bash run_pipeline.sh --era5-dir /data/era5/ --clean --background

# With custom parallelism
bash run_pipeline.sh --era5-dir /data/era5/ --n-chunks 32 --workers 8 --background

# Resume an interrupted run (skip steps with existing outputs)
bash run_pipeline.sh --era5-dir /data/era5/ --skip-done --background

# Run only specific steps
bash run_pipeline.sh --era5-dir /data/era5/ --only 7,7b,8,8b --background
```

**Pipeline execution model:** steps run **sequentially** (each step finishes before
the next starts).  Within each heavy step (4, 5, 7) up to `--n-chunks` parallel
background jobs run simultaneously — this is the in-step parallelism.

Options summary:

| Option | Default | Description |
|--------|---------|-------------|
| `--era5-dir PATH` | — | **Required.** Directory with per-cyclone ERA5 files |
| `--background` | off | Detach under nohup (survives SSH disconnect) |
| `--clean` | off | Wipe previous results + logs before running |
| `--dry-run` | off | With `--clean`: preview deletions, don't delete |
| `--n-chunks N` | 16 | Parallel background jobs **within** each heavy step |
| `--workers N` | 4 | CPU workers per chunk (within-chunk parallelism) |
| `--skip-done` | off | Skip steps whose output files already exist |
| `--only STEPS` | all | Run only listed steps, e.g. `"4,5,6"` or `"7b,8b"` |
| `--stop-on-error` | off | Halt at first failure (default: continue all steps) |

All step logs are saved to `logs/` with timestamped filenames.

## Cleaning Previous Outputs

```bash
# Preview what would be deleted (safe, no changes)
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --all

# Actually delete everything (fresh start)
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --all --yes

# Scoped cleanup: --results | --chunks | --figures | --logs
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --logs --yes
```

## Monitoring Execution

In a second terminal (local or on the server), run the status monitor:

```bash
# Snapshot of current pipeline status
python monitor_pipeline.py

# Live-refresh every 15 seconds (press Ctrl+C to stop)
python monitor_pipeline.py --watch

# Faster refresh + show last log lines for running steps
python monitor_pipeline.py --watch --interval 5 --log-tail

# No colours (for logging to file or non-TTY terminals)
python monitor_pipeline.py --no-color
```

Example output:
```
╔════════════════════════════════════════════════════════════════════════╗
║          LEC Field Dependence Pipeline — Status Monitor               ║
║  Last refresh: 2026-04-17 16:00:00                                    ║
╚════════════════════════════════════════════════════════════════════════╝

STEP   DESCRIPTION                       STATUS      PROGRESS / DETAIL
─────────────────────────────────────────────────────────────────────────
1      Consolidate metadata              ✓ DONE      1/1 files            14:00:01
2      Build LEC table                   ✓ DONE      1/1 files            14:00:12
3      Map ERA5 fields                   ✓ DONE      1/1 files            14:00:43
4      Extract absolute features         ▶ RUNNING   8 chunks done so far 15:58:22
5      Extract anomaly features          · PENDING   —                    —
...
```

Status icons: `✓ DONE`, `▶ RUNNING`, `◑ PARTIAL` (chunks done, not merged), `✗ FAILED`, `· PENDING`

```bash
cd /path/to/paper_energy_patterns
python scripts/lec_field_dependence_analysis/step1_consolidate_metadata.py
python scripts/lec_field_dependence_analysis/step2_build_lec_table.py
python scripts/lec_field_dependence_analysis/step3_map_era5_fields.py

# Significance tests on LEC terms only (runs locally, no ERA5 needed)
python scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py --lec-only
python scripts/lec_field_dependence_analysis/step8b_significance_figures.py
```

## Running on Remote/HPC (steps 4-8)

```bash
# Feature extraction (supports --chunk/--n-chunks for job arrays)
python step4_extract_features_absolute.py --era5-dir /path/to/era5/ --workers 32
python step5_extract_features_anomaly.py --era5-dir /path/to/era5/ --workers 32

# Integration and PREDEP
python step6_integrate_tables.py
python step7_compute_predep.py --field-type absolute --workers 32
python step7_compute_predep.py --field-type anomaly --workers 32
# For smoke tests with small samples: --min-n 2 (default: 30)

# Full significance tests (LEC + all features)
python step7b_ep_significance_tests.py

# Figures (can run locally after transferring results back)
python step8_synthesis_figures.py
python step8b_significance_figures.py
```

### Chunked HPC Execution (SLURM example)

```bash
# Step 4 with 100 chunks
for i in $(seq 0 99); do
  python step4_extract_features_absolute.py --era5-dir /data/era5/ \
    --chunk $i --n-chunks 100 --workers 4
done

# Step 7 with 10 chunks per field type
for i in $(seq 0 9); do
  python step7_compute_predep.py --field-type absolute --chunk $i --n-chunks 10
done
```

All steps are **restart-friendly**: they detect already-processed outputs and skip them.

---

## Output Structure

```
results/lec_field_dependence/
├── step1_eligible_cases.csv              # Eligible cyclones
├── step1_metadata_report.txt
├── step2_lec_means.csv                   # LEC means per cyclone (central timesteps)
├── step2_lec_qa_report.txt
├── step3_era5_field_manifest.csv         # ERA5 availability
├── step3_field_mapping_report.txt
├── step4_features_absolute.csv           # Absolute field features
├── step5_features_anomaly.csv            # EPALL-relative features
├── step6_integrated_absolute.csv         # Merged: cases + LEC + abs features
├── step6_integrated_anomaly.csv          # Merged: cases + LEC + anom features
├── step6_integrated_all.csv              # Full superset
├── step6_integration_qa_report.txt
├── step7_predep_absolute.csv             # PREDEP results (long format)
├── step7_predep_anomaly.csv
├── step7b_diagnostic_table.csv           # Variable-by-variable significance diagnostics
├── step7b_pairwise_table.csv             # Post-hoc pairwise comparisons
├── step7b_significance_report.txt        # Human-readable summary
├── step8_summary_table.csv               # Summary statistics
├── step8_top_associations.csv            # Top PREDEP values
├── step8_abs_vs_anom_comparison.csv
└── step9_pipeline_status.txt

figures/lec_field_dependence/
├── heatmap_predep_ep1_absolute.png
├── heatmap_predep_ep2_absolute.png
├── heatmap_predep_ep3_absolute.png
├── heatmap_predep_ep1_anomaly.png
├── heatmap_predep_ep2_anomaly.png
├── heatmap_predep_ep3_anomaly.png
├── top_predep_absolute.png
├── top_predep_anomaly.png
├── ep_comparison_absolute.png
├── ep_comparison_anomaly.png
├── significance_heatmap_lec_terms.png    # Step 8b outputs
├── significance_heatmap_absolute_features.png
├── significance_heatmap_anomaly_features.png
├── effect_size_heatmap_lec_terms.png
├── effect_size_heatmap_absolute_features.png
├── effect_size_heatmap_anomaly_features.png
├── volcano_lec_terms.png
├── volcano_absolute_features.png
├── volcano_anomaly_features.png
├── effect_ranking_lec_terms.png
├── effect_ranking_absolute_features.png
├── effect_ranking_anomaly_features.png
└── diagnostics/                          # Diagnostic-only figures (not for publication)
    ├── correlation_heatmaps/             # Pearson/Spearman |r| heatmaps
    │   ├── all/                          # All 24 LEC terms
    │   └── canonical/                    # 7 canonical terms only
    └── scatterplots/                     # LEC term × feature scatter grids
```

### Diagnostic Figures

Two additional diagnostic scripts produce figures for internal inspection only:

```bash
# Pearson/Spearman correlation heatmaps (uses step7 outputs, no recomputation)
python scripts/lec_field_dependence_analysis/diag_correlation_heatmaps.py

# LEC × feature scatterplots (uses step6 integrated tables, no recomputation)
python scripts/lec_field_dependence_analysis/diag_scatterplots.py
```

---

## Dependencies

All dependencies are already in the project's `environment.yml`.  The only additional requirement is `scipy` (for hierarchical clustering in PREDEP), which is already installed.

---

## Baseline Measures

Pearson correlation and Spearman rank correlation are computed alongside PREDEP as secondary reference benchmarks.  They are **not** the primary analysis — PREDEP is preferred because it:

1. Captures non-linear and non-functional dependencies
2. Has a direct probabilistic interpretation (% prediction loss reduction)
3. Is bounded in [0, 1]
4. Equals zero if and only if X and Y are independent

---

## Inter-EP Significance Analysis (Step 7b)

For every scalar variable (LEC terms + dynamic features), a decision-tree-based testing pipeline determines:

1. **Is there a significant difference between EP1, EP2, EP3?** (ANOVA / Welch ANOVA / Kruskal-Wallis)
2. **Which pairs differ?** (Tukey HSD / Welch t-tests / Dunn test)
3. **How large is the effect?** (ω², ε², Cohen's d, rank-biserial r)
4. **Does it survive multiple-comparison correction?** (Benjamini-Hochberg FDR)

The test selection is automatic based on normality (Shapiro-Wilk) and variance homogeneity (Levene):

```
Normal + equal var  → ANOVA     → Tukey HSD
Normal + unequal    → Welch     → Welch t-tests (Holm)
Non-normal          → Kruskal   → Dunn (Holm)
```

**LEC-only mode** (`--lec-only`) runs locally using step 1–2 outputs only; full mode also analyses dynamic features from step 6.

Outputs:
- `step7b_diagnostic_table.csv`: full audit trail per variable (normality, homogeneity, test chosen, p-value, effect size)
- `step7b_pairwise_table.csv`: all post-hoc pairwise comparisons with adjusted p-values and effect sizes
- `step7b_significance_report.txt`: human-readable summary

See `SCIENTIFIC_NOTES.md` for detailed methodology and interpretation guidance.

---

## Reference

Assunção, R., Figueiredo, F., Tinoco Junior, F. N., de Sá-Freire, L. M., & Silva, F. (2025). *An Interpretable Measure for Quantifying Predictive Dependence between Continuous Random Variables*. arXiv:2501.10815v1.

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for known issues, root causes, fixes, and diagnostic commands.
