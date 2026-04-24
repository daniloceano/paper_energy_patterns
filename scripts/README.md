# Scripts Directory

This directory contains all analysis scripts organised by purpose. The subdirectories range from preprocessing and utility functions to the final publication figure scripts and the current scientific analysis pipeline.

---

## Directory Structure

```
scripts/
├── main/                               # Final publication figure scripts (01–07, S1–S3)
├── exploratory/                        # Preliminary exploratory scripts (not in paper)
├── cluster_analysis_energy_patterns/   # PCA + K-Means Energy Pattern classification
├── ep_structure_analysis/              # ERA5 composite analysis (EP1, EP2, EP3, EPALL)
├── lec_field_dependence_analysis/      # PREDEP: individual-cyclone LEC–field predictive dependence
├── ck_subterms_analysis/               # Ck decomposition into subterms for EP1
├── preprocess_data/                    # Data download and preprocessing
├── utils/                              # Shared utility functions
├── web/                                # Scripts to build and update the results website
├── setup_and_examples/                 # Environment verification and script templates
└── documentation/                      # Compile all READMEs into a consolidated PDF
```

---

## Directory Descriptions

### `main/` — Final Publication Figure Scripts

Repository of final publication-ready figure scripts, numbered by figure order (01–07 main figures, S1–S3 supplementary). Output goes to `figures/main/`.

**Main scripts:**

| Script | Figure |
|--------|--------|
| `01_figure_tracks_genesis_frequency.py` | Fig 1: Study area and workflow |
| `02_figure_20070643_publication.py` | Fig 2: Case study cyclone 20070643 |
| `03_make_phase_density_2x2.py` | Fig 3: Phase space density (2×2) |
| `04_figure_lps_combined.py` | Fig 4: Lorenz Phase Space for EP1–EP3 |
| `05_figure_intensity_seasonality_trends.py` | Fig 5: EP intensity, seasonality, trends |
| `06_figure_genesis_density_kde.py` | Fig 6: Genesis density (KDE) |
| `07_figure_ep1_ep2_dynamical_composites.py` | Fig 7: EPALL-relative dynamical composites (3×3, EP1/EP2/EP3) |
| `S1_figure_pca_clustering_validation.py` | Fig S1: PCA/clustering validation |
| `S2_figure_vertical_levels.py` | Fig S2: Vertical Ca/Ck distributions for EP1, EP2, and EP3 |
| `run_all.py` | Run all figure scripts sequentially |

**Inputs:** `data/tracks_SAt_filtered_with_energetics_processed.csv`, `results/cluster/kmeans_clustered_data.csv`; Fig 7 additionally requires composites from `data/era5_ep_structure/`; Fig S2 requires the Zenodo LEC archive in `data/temp_lec_zenodo/`.

**Outputs:** `figures/main/`

---

### `exploratory/` — Preliminary Exploratory Scripts

General preliminary exploratory scripts. These predate or support the main pipeline but are not directly used in the final paper.

**Scripts:**

| Script | Description |
|--------|-------------|
| `analyze_ep_characteristics.py` | EP characteristic statistics |
| `density_diagrams_with_ge.py` | Density diagrams including Ge term |
| `exploring_clustering.ipynb` | Interactive clustering exploration |
| `exploring_pca.ipynb` | Interactive PCA exploration |
| `figure_genesis_density_relative_kde.py` | Relative genesis density |
| `figure_minmax_vs_zscore_comparison.py` | Normalisation method comparison |
| `figure_most_intense_cyclone_lps.py` | Most intense cyclone LPS |
| `figure_three_intense_cyclones_individual.py` | Three intense cyclones individual plots |
| `figure_three_intense_cyclones_individual_zoom.py` | Zoomed versions |
| `kde_pairplot.py` | KDE pairwise plot of energy terms |
| `plot_ep_lps_diagrams.py` | LPS diagrams per energy pattern |
| `plot_pv_jet_composite.py` | PV and jet composite |
| `precompute_composites.py` | Early composite precomputation prototype |
| `scatter_density.py` | Scatter density plots |
| `vertical_term_boxplots_ep1_ep2.py` | Vertical term boxplots EP1 vs EP2 |

**Inputs:** `data/energy_cache.parquet`, `results/cluster/kmeans_clustered_data.csv`

**Outputs:** `figures/exploratory/`

---

### `cluster_analysis_energy_patterns/` — Energy Pattern Classification

Scripts for generating the Energy Patterns via PCA + K-Means clustering of Lorenz Energy Cycle diagnostics during the intensification phase.

**Pipeline (run in order):**

1. `step1_normalize_and_pca.py` — Normalise energy variables and apply PCA by lifecycle phase
2. `step2_plot_pca_results.py` — Visualise PCA loadings and explained variance
3. `step3_optimal_k_analysis.py` — Determine optimal k via Gap Statistic
4. `step4_apply_kmeans.py` — Apply K-Means (k=3) and assign Energy Patterns
5. `step5_plot_energy_patterns.py` — Composite statistics and LPS diagrams
6. `step6_generate_scientific_notes_pdf.py` — Convert SCIENTIFIC_NOTES.md to PDF

**Inputs:** `data/energy_cache.parquet`, `data/tracks_SAt_filtered_with_energetics_processed.csv`

**Outputs:** `results/cluster/` (CSV assignments, PCA/KMeans model pickles), `figures/`, `docs/scientific_notes_cluster_analysis.pdf`

**Key results (cluster analysis):** EP1 (11.6%, N=444), EP2 (25.6%, N=979), EP3 (62.7%, N=2,397). After ≥ 24 h duration filter (ep_structure_analysis): EP1 N=332, EP2 N=776, EP3 N=1,625, EPALL N=2,733.

---

### `ep_structure_analysis/` — Spatial Structure Analysis (Current Scientific Focus)

Composite analysis of ERA5 reanalysis fields to understand the atmospheric structure of EP1, EP2, EP3, and EPALL (all cyclones combined) during intensification. The primary figure output uses **EPALL-relative anomalies** (EP − EPALL) to isolate what is dynamically distinctive about each energy pattern.

#### Scientific Summary

**Objective:** Investigate atmospheric structural differences among the three Energy Patterns and relative to a generic intensifying South Atlantic cyclone (EPALL).

**Sample:** Cyclones with intensification phase ≥ 24 h, after applying a duration filter that removes ~28.5% of cases (short intensification phases). Final sample sizes: EP1 (N=332), EP2 (N=776), EP3 (N=1,625), EPALL (N=2,733). Composites use central intensification timesteps only.

**ERA5 data:** 0.25° resolution, storm-centred 30°×30° domain, 6-hourly. Pressure-level variables: u, v, t, z, q at levels 175–975 hPa. Single-level variable: msl.

**Diagnostics computed:**

| Diagnostic | Level(s) | Description |
|------------|----------|-------------|
| EGR (Eady Growth Rate) | 500–850 hPa | Baroclinic instability measure |
| PV (Potential Vorticity) | 200 hPa | Upper-level tropopause dynamics |
| PV | 850 hPa | Low-level diabatic PV anomaly |
| Temperature Advection | 850 hPa | Warm/cold advection patterns |
| Moisture Flux Divergence | 975 hPa | Near-surface moisture convergence |
| SLP | Surface | Cyclone intensity and horizontal structure |
| RK criterion (Rayleigh-Kuo) | 250 hPa | Barotropic/baroclinic instability condition |
| KE Advection | 250 hPa | Jet-level kinetic energy tendency |
| AFC (Ageostrophic Flux Convergence) | 250 hPa | Eddy KE redistribution |

Anomaly versions (departure from 1991–2020 WMO climatology) are computed for PV (200/850 hPa), temperature advection, moisture flux divergence, KE advection, and SLP.

**Pipeline:**

1. `step1_select_ep_tracks.py` — Select EP1/EP2/EP3 tracks from cluster results
2. `step2_download_era5_parallel.py` — Download ERA5 pressure-level and single-level fields (run **remotely**)
3. `step2b_reuse_legacy_era5.py` — Reuse previously downloaded ERA5 data where available (run **remotely**)
4. `step2c_monitor.py` — Monitor download progress (run **remotely**)
5. `step2d_download_era5_monthly_means.py` — Download 1991–2020 monthly mean climatology (run **remotely**)
6. `step3_precompute_composites.py` — Compute storm-relative composites for all EPs (run **remotely**)
7. `step4_create_figures.py` — Create per-diagnostic composite figures (run **locally**)
8. `step4b_create_dynamical_composites.py` — Create dynamical composite figures (run **locally**)
9. `step5_update_scientific_notes.py` — Update SCIENTIFIC_NOTES.md and regenerate PDF (run **locally**)
10. `step6_generate_cyclone_explorer_panels.py` — Generate per-cyclone panels for the results website (run **locally**)

**Inputs:** `results/cluster/kmeans_clustered_data.csv`, ERA5 via CDS API

**Outputs:** `data/era5_ep_structure/precomputed_composites_ep{1,2,3,all}.nc`, `figures/ep_structure/`, `docs/scientific_notes_ep_structure.pdf`

---

### `lec_field_dependence_analysis/` — PREDEP: Individual-Cyclone LEC–Field Dependence

Investigates, at the individual-cyclone level, the predictive dependence (PREDEP, Assunção et al. 2025) between LEC terms and scalar features derived from ERA5 dynamical fields. Analysis direction: X = dynamic feature, Y = LEC term.

**Pipeline (9 steps + 2 significance steps):**

| Step | Script | Local/Remote |
|------|--------|-------------|
| 1 | `step1_consolidate_metadata.py` | Local |
| 2 | `step2_build_lec_table.py` | Local |
| 3 | `step3_map_era5_fields.py` | Local (dry-run) |
| 4 | `step4_extract_features_absolute.py` | **Remote** |
| 5 | `step5_extract_features_anomaly.py` | **Remote** |
| 6 | `step6_integrate_tables.py` | Remote |
| 7 | `step7_compute_predep.py` | Remote |
| 7b | `step7b_ep_significance_tests.py` | Local (`--lec-only`) / Remote (full) |
| 8 | `step8_synthesis_figures.py` | Local |
| 8b | `step8b_significance_figures.py` | Local |
| 9 | `step9_update_docs.py` | Local |

Steps 4–7 support `--chunk/--n-chunks` for HPC job arrays and `--workers` for multiprocessing.
Step 7b runs Shapiro-Wilk → Levene → ANOVA/Welch/Kruskal-Wallis → Tukey/Dunn post-hoc → FDR correction per variable.

**Inputs:** `results/ep_structure/`, LEC Zenodo (`data/temp_lec_zenodo/`), per-cyclone ERA5 fields (remote only)

**Outputs:** `results/lec_field_dependence/`, `figures/lec_field_dependence/`

See `scripts/lec_field_dependence_analysis/README.md` and `SCIENTIFIC_NOTES.md` for full details.

---

### `ck_subterms_analysis/` — Barotropic Conversion Decomposition

Decomposes the barotropic conversion term (Ck) into its three subterms for EP1 cyclones (N=444), which present the largest barotropic conversions in the dataset (mean Ck = −16.48 W m⁻²).

**Pipeline:**

1. `step1_prepare_tracks.py` — Convert EP1 cyclone tracks to LorenzCycleToolkit format
2. `step2_run_lec_toolkit.py` — Run LorenzCycleToolkit with automatic ERA5 download
3. `step2_monitor_ck.py` — Monitor job progress

**Prerequisite:** Cluster results `results/cluster/kmeans_clustered_data.csv` (from `cluster_analysis_energy_patterns`).

**Inputs:** `results/cluster/kmeans_clustered_data.csv`, ERA5 (auto-downloaded by toolkit)

**Outputs:** `data/ck_analysis/`, `results/ck_analysis/`

---

### `preprocess_data/` — Data Download and Preprocessing

Scripts for downloading and preprocessing the input data from Zenodo.

**Run order:**

```bash
python scripts/preprocess_data/run_all.py
# or individually:
python scripts/preprocess_data/download_lec_from_zenodo.py
python scripts/preprocess_data/extract_tracks_from_zenodo.py
python scripts/preprocess_data/preprocess_data.py
```

**Outputs:** `data/tracks_SAt_filtered_with_energetics_processed.csv`, `data/energy_cache.parquet`, `data/temp_lec_zenodo/`

---

### `utils/` — Shared Utility Functions

Shared utility functions used across the repository.

| Module | Description |
|--------|-------------|
| `load_data.py` | Load cyclone tracks and energy data |
| `gap_statistic.py` | Gap Statistic implementation (Tibshirani et al. 2001) |
| `colormaps.py` | Custom diverging colormaps (`CMAP_PV_ANOM`, `CMAP_AFC`) used across figures |
| `ep_mapping.py` | Mapping between cluster labels and EP names/colours |
| `timestep_selection.py` | Central-timestep selection logic for composite pipeline |

---

### `setup_and_examples/` — Environment Verification and Templates

| Script | Description |
|--------|-------------|
| `verify_environment.py` | Check all required packages are installed |
| `example_analysis.py` | Minimal working example of a complete analysis |
| `template_analysis.py` | Boilerplate template for new scripts |

---

### `web/` — Results Website Scripts

Scripts to build and update the [Vercel + Supabase results website](https://paper-energy-patterns.vercel.app). These scripts extract data from local analysis outputs and push it to the web frontend.

| Script | Description |
|--------|-------------|
| `prepare_site.py` | Master orchestrator: runs extraction scripts and copies figures |
| `extract_composite_site_data.py` | Generates `composite_figures_manifest.json` from `figures/ep_structure/` |
| `extract_cluster_site_data.py` | Extracts cluster/LPS data for the web frontend |
| `extract_ck_subterms_site_data.py` | Extracts Ck subterm data for the web frontend |
| `extract_cyclone_explorer_data.py` | Extracts per-cyclone panel data for the Cyclone Explorer |
| `copy_figures_to_web.py` | Copies figure files into `web/public/figures/` |
| `upload_figures_to_supabase.py` | Uploads figures to Supabase Storage |
| `build_site_manifest.py` | Builds general site asset manifest |
| `generate_hotfix_manifest.py` | Patches the manifest after hotfix figure updates |

**Workflow:**
```bash
python scripts/web/prepare_site.py        # full site update
cd web && npx next build && vercel --prod  # deploy
```

---

### `documentation/` — Documentation Compiler

Contains `compile_docs.py`, which collects all repository READMEs and generates `docs/user_guide_repository_readmes.pdf`.

```bash
python scripts/documentation/compile_docs.py
```

---

## How Imports Work

All scripts use absolute imports from the project root:

```python
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]  # adjust depth as needed
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.utils.load_data import load_tracks
```

This ensures scripts work from **any working directory**:
- From project root: `python scripts/main/01_figure_tracks_genesis_frequency.py`
- From scripts dir: `python main/01_figure_tracks_genesis_frequency.py`

Depth reference: scripts in `scripts/` use `.parents[1]`; scripts in `scripts/subdir/` use `.parents[2]`.

---

## Directory Setup

All scripts automatically create their output directories:

```python
project_root = Path(__file__).resolve().parents[2]
FIGURES_DIR = project_root / "figures" / "my_analysis"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
```

---

## Running Scripts

```bash
# From project root
python scripts/main/run_all.py
python scripts/cluster_analysis_energy_patterns/run_all.py

# From any subdirectory (imports resolve automatically)
cd scripts/main
python 01_figure_tracks_genesis_frequency.py
```

---

## Available Utilities

```python
from scripts.utils.load_data import (
    load_tracks,              # Load all cyclone tracks
    load_energy_by_cyclone,   # Load energy for one cyclone
    load_all_energy_data,     # Load energy for multiple cyclones
)
from scripts.utils.gap_statistic import GapStatistic
```
