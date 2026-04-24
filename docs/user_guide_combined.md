# Repository User Guide

**Paper: Energetic Patterns of Cyclones in the Southwestern Atlantic**

*Auto-generated from repository READMEs*

---

## Section: Project Overview

> Source: `README.md`

# Energetic Patterns of Cyclones in the Southwestern Atlantic

This repository organises all scripts, data, and results for the paper on energetic patterns of South Atlantic extratropical cyclones, based on Chapter 6 of the PhD thesis. Cyclones are classified into three Energy Patterns (EP1, EP2, EP3) via PCA-based K-Means clustering of Lorenz Energy Cycle diagnostics during the intensification phase. The **current scientific focus** is `scripts/ep_structure_analysis/`, which performs composite analysis of ERA5 reanalysis fields to characterise the atmospheric structure of EP1 (N=444) and EP2 (N=979) cyclones during intensification.

---

## 
### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/daniloceano/paper_energy_patterns.git
cd paper_energy_patterns

# Create conda environment and install dependencies
bash setup_environment.sh

# Activate environment
conda activate paper_energy_patterns
```

### 2. Preprocess Data (Run Once)

```bash
# Download and cache all energy data for fast access
python scripts/preprocess_data/run_all.py
```

Expected outputs: `data/tracks_SAt_filtered_with_energetics_processed.csv`, `data/energy_cache.parquet`

### 3. Run Cluster Analysis (Energy Patterns)

```bash
python scripts/cluster_analysis_energy_patterns/run_all.py
```

Outputs clustering results to `results/cluster/` and figures to `figures/`.

### 4. Generate Final Paper Figures

```bash
python scripts/main/run_all.py
```

Outputs publication-ready figures to `figures/main/`.

---

## 
```
.
 data/                                    # Input and processed data
 energy_cache.parquet                 # Preprocessed energy data (generated)   
 era5_ep_structure/                   # ERA5 composites for ep_structure_analysis   
 precomputed_composites_ep1.nc      
 precomputed_composites_ep2.nc      
 README.md   
 docs/                                    # Generated documentation PDFs
 scientific_notes_cluster_analysis.pdf   
 scientific_notes_ep_structure.pdf   
 user_guide_repository_readmes.pdf   # Auto-generated (see below)   
 figures/                                 # Generated figures
 exploratory/                         # Exploratory figures   
 main/                                # Final publication figures   
 results/                                 # Analysis results
 cluster/                             # Cluster assignments and models   
 scripts/                                 # All analysis scripts
 cluster_analysis_energy_patterns/    # PCA + K-Means clustering pipeline   
 ck_subterms_analysis/                # Barotropic conversion (Ck) decomposition   
 documentation/                       # Compile READMEs into a PDF user guide   
 ep_structure_analysis CURRENT FOCUS: ERA5 composite analysis/               #    
 exploratory/                         # Preliminary exploratory scripts   
 main/                                # Final publication figure scripts   
 preprocess_data/                     # Data download and preprocessing   
 setup_and_examples/                  # Environment verification and templates   
 utils/                               # Shared utility functions   
 activate.sh                              # Quick environment activation
 requirements.txt
 setup_environment.sh
```

See `scripts/README.md` for detailed information on each subdirectory.

---

## 
### Cyclone Tracks and Energetics

- **DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)
- **Description**: Combined cyclone tracks and semi-Lagrangian Lorenz Energy Cycle diagnostics (2020, ~6,700 cyclones, 42 years)1979
- **Access**: Downloaded automatically by `scripts/preprocess_data/extract_tracks_from_zenodo.py`

### LEC Results with Vertical Resolution

- **DOI**: [10.5281/zenodo.18243447](https://doi.org/10.5281/zenodo.18243447)
- **Description**: Complete LEC results with vertical resolution (~1,500 cyclones, 32 pressure levels, 3-hourly)
- **Access**: Downloaded automatically by `scripts/preprocess_data/download_lec_from_zenodo.py`

---

echo Configuration## 

All scripts use a header-level configuration  no command-line arguments needed:block 

```python
# Example configuration (top of any script)
SAMPLE_SIZE = 0        # Number of cyclones (0 = all)
USE_PARALLEL = True    # Enable parallel processing
N_WORKERS = 8          # Workers (adjust for your system)
DPI = 300              # Figure output quality
```

---

## 
### 1. Energy Pattern Classification (`scripts/cluster_analysis_energy_patterns/`)

Normalises LEC energy variables, applies PCA by lifecycle phase, determines the optimal number of clusters via Gap Statistic, and classifies each cyclone into one of three Energy Patterns using K-Means. Key results: EP1 (11.6%, 444  high conversions; EP2 (25.6%, 979  moderate conversions; EP3 (62. weak/background energetics.7%) cyclones) cyclones) 

### 2 Spatial Structure Analysis (`scripts/ep_structure_ *Current Focus*analysis/`) . 

Composite ERA5 analysis of EP1 and EP2 cyclones during intensification. Uses a storm-centred domain at 0.resolution to compute EGR (850 hPa), PV (200/850 hPa), temperature advection (850 hPa), moisture flux divergence (975 hPa), SLP, RK criterion (250 hPa), KE advection (250 hPa), and AFC (250 hPa), plus anomalies relative to the 2020 WMO climatology. Data stored in `data/era5_ep_structure/`.1991500253030

### 3. Barotropic Conversion Decomposition (`scripts/ck_subterms_analysis/`)

Decomposes the barotropic conversion term (Ck) into its three subterms for EP1 cyclones, which present the largest barotropic conversions in the dataset.

### 4. Final Paper Figures (`scripts/main/`)

Scripts numbered 07 (main figures) and S3 (supplementary) generate publication-ready figures at 300 DPI according to Scientific Reports guidelines.S101

---

## 
### First Time

```bash
bash setup_environment.sh
```

The script creates the `paper_energy_patterns` conda environment (Python 3.13), installs all packages from `requirements.txt`, and verifies the installation.

### Daily Use

```bash
source activate.sh
# or
conda activate paper_energy_patterns
```

### Verify Installation

```bash
python scripts/setup_and_examples/verify_environment.py
```

---

## 
A consolidated user guide (`docs/user_guide_repository_readmes.pdf`) is auto-generated from all repository READMEs. To regenerate it:

```bash
python scripts/documentation/compile_docs.py
```

Requires `pandoc` and `pdflatex` on your system.


---

## Section: Data

> Source: `data/README.md`

# Data Directory

## Input Data (Accessed from Zenodo)

Input data **does not need to be downloaded** - accessed directly via URL:

### Cyclone Tracks and Energetics (Integrated Dataset)
- **DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)
- **Direct URL**: https://zenodo.org/records/18133432/files/tracks_SAt_filtered_with_energetics.csv
- **Citation**: de Souza, D., & Gramcianinov, C. (2026). Southwestern Atlantic Cyclone Tracks and Semi-Lagrangian Lorenz Energy Cycle (LEC) diagnostics (1979–2020) [Data set]. Zenodo.
- **Description**: Complete dataset combining cyclone tracks with semi-Lagrangian Lorenz Energy Cycle diagnostics
- **Period**: 1979-2020 (42 years)
- **Format**: Long format CSV (each row = one time step of one cyclone)
- **Size**: 180.8 MB
- **Temporal Resolution**:
  - Track variables (position, vorticity): 1-hourly
  - Energy variables (LEC terms): 3-hourly

#### Main Columns:

**Identification and Location:**
  - `track_id`: Unique cyclone identifier (format: YYYYNNNN)
  - `date`: UTC timestamp
  - `lon vor`, `lat vor`: Cyclone center coordinates (degrees)
  - `vor42`: Filtered 850 hPa vorticity (×10⁵ s⁻¹, positive values)
  - `region`: Genesis region (ARG, LA-PLATA, SE-BR)
  - `period`: Life cycle phase (incipient, intensification, mature, decay)

**Energy Reservoirs (J m⁻²):**
  - `Az`, `Ae`, `Kz`, `Ke`

**Conversion Terms (W m⁻²):**
  - `Cz`, `Ca`, `Ce`, `Ck`

**Boundary Terms (W m⁻²):**
  - `BAz`, `BAe`, `BKz`, `BKe` (flux terms)
  - `BΦZ`, `BΦE` (pressure-work terms)

**Generation Terms (W m⁻²):**
  - `Gz`, `Ge` (diabatic generation)

**Tendencies (W m⁻²):**
  - `∂Az/∂t`, `∂Ae/∂t`, `∂Kz/∂t`, `∂Ke/∂t`

**Residuals (W m⁻²):**
  - `RGz`, `RGe`, `RKz`, `RKe`

#### Key Features:
- **Semi-Lagrangian**: 15°×15° storm-following control volume
- **Quality Controlled**: Minimum lifetime/displacement thresholds applied
- **Phase Attribution**: Objective life-cycle segmentation using CycloPhaser
- **Missing Values**: Some timestamps may contain NaN for energy terms

## Processed Data (This directory)

Use this folder to save:
- Intermediate processed data
- Aggregations and statistics
- Data subsets for specific analyses
- Classification/clustering results

**Note**: Don't version very large files. Use `.gitignore` as needed.


---

## Section: Scripts

> Source: `scripts/README.md`

# Scripts Directory

This directory contains all analysis scripts organised by purpose. The subdirectories range from preprocessing and utility functions to the final publication figure scripts and the current scientific analysis pipeline.

---

## Directory Structure

```
scripts/
 main Final publication figure scripts (07, S3)S101/                               # 
 exploratory/                        # Preliminary exploratory scripts (not in paper)
 cluster_analysis_energy_patterns/   # PCA + K-Means Energy Pattern classification
 ep_structure_analysis CURRENT FOCUS: ERA5 composite analysis (EP1 vs EP2)/              # 
 ck_subterms_analysis/               # Ck decomposition into subterms for EP1
 preprocess_data/                    # Data download and preprocessing
 utils/                              # Shared utility functions
 setup_and_examples/                 # Environment verification and script templates
 documentation/                      # Compile all READMEs into a consolidated PDF
```

---

## Directory Descriptions

### ` Final Publication Figure Scriptsmain/` 

Repository of final publication-ready figure scripts, numbered by figure order (07 main figures, S3 supplementary). Output goes to `figures/main/`.S101

**Main scripts:**

| Script | Figure |
|--------|--------|
| `01_figure_tracks_genesis_frequency.py` | Fig 1: Study area and workflow |
| `02_figure_20070643_publication.py` | Fig 2: Case study cyclone 20070643 |
| `03_make_phase_density_2x2.py` | Fig 3: Phase space density (22) |
| `04_figure_lps_combined.py` | Fig 4: Lorenz Phase Space for EP3 |EP1
| `05_figure_intensity_seasonality_trends.py` | Fig 5: EP intensity, seasonality, trends |
| `06_figure_genesis_density_kde.py` | Fig 6: Genesis density (KDE) |
| `07_figure_ep1_instability_composite.py` | Fig 7: EP1 instability composite |
| `S1_figure_pca_clustering_validation.py` | Fig S1: PCA/clustering validation |
| `S2_figure_vertical_levels.py` | Fig S2: Vertical Ca/Ck distributions for EP1, EP2, and EP3 |
| `run_all.py` | Run all figure scripts sequentially |

**Inputs:** `data/tracks_SAt_filtered_with_energetics_processed.csv`, `results/cluster/kmeans_clustered_data.csv`; Fig S2 requires the Zenodo LEC archive in `data/temp_lec_zenodo/`.

**Outputs:** `figures/main/`

---

### ` Preliminary Exploratory Scriptsexploratory/` 

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

### `cluster_analysis_energy_ Energy Pattern Classificationpatterns/` 

Scripts for generating the Energy Patterns via PCA + K-Means clustering of Lorenz Energy Cycle diagnostics during the intensification phase.

**Pipeline (run in order):**

1. `step1_normalize_and_pca. Normalise energy variables and apply PCA by lifecycle phasepy` 
2. `step2_plot_pca_results. Visualise PCA loadings and explained variancepy` 
3. `step3_optimal_k_analysis. Determine optimal k via Gap Statisticpy` 
4. `step4_apply_kmeans. Apply K-Means (k=3) and assign Energy Patternspy` 
5. `step5_plot_energy_patterns. Composite statistics and LPS diagramspy` 
6. `step6_generate_scientific_notes_pdf. Convert SCIENTIFIC_NOTES.md to PDFpy` 

**Inputs:** `data/energy_cache.parquet`, `data/tracks_SAt_filtered_with_energetics_processed.csv`

**Outputs:** `results/cluster/` (CSV assignments, PCA/KMeans model pickles), `figures/`, `docs/scientific_notes_cluster_analysis.pdf`

**Key results:** EP1 (11.6%, N=444), EP2 (25.6%, N=979), EP3 (62.7%)

---

###   Current Scientific Focus)

Composite analysis of ERA5 reanalysis fields to understand the atmospheric structure of EP1 (N=444) and EP2 (N=979) cyclones during intensification. EP3 is excluded because it represents less intense, climatological-background cyclones.

#### Scientific Summary

**Objective:** Investigate what structural differences in the large-scale atmospheric environment distinguish EP1 (high-conversion) from EP2 (moderate-conversion) cyclones.

**Sample:** All 444 EP1 and 979 EP2 cyclones identified by `cluster_analysis_energy_patterns`, using intensification-phase timesteps only.

**ERA5 data:** 0.resolution, storm-centred domain, 6-hourly. Pressure-level variables: u, v, t, z, q at 975 hPa. Single-level variable: msl.175303025

**Diagnostics computed:**

| Diagnostic | Level(s) | Description |
|------------|----------|-------------|
| EGR (Eady Growth Rate) | 850 hPa | Baroclinic instability measure |500
| PV (Potential Vorticity) | 200 hPa | Upper-level tropopause dynamics |
| PV | 850 hPa | Low-level diabatic PV anomaly |
| Temperature Advection | 850 hPa | Warm/cold advection patterns |
| Moisture Flux Divergence | 975 hPa | Near-surface moisture convergence |
| SLP | Surface | Cyclone intensity and horizontal structure |
| RK criterion (Rayleigh-Kuo) | 250 hPa | Barotropic/baroclinic instability condition |
| KE Advection | 250 hPa | Jet-level kinetic energy tendency |
| AFC (Ageostrophic Flux Convergence) | 250 hPa | Eddy KE redistribution |

Anomaly versions (departure from 2020 WMO climatology) are computed for PV (200/850 hPa), temperature advection, moisture flux divergence, KE advection, and SLP.1991

**Pipeline:**

1. `step1_select_ep_tracks. Select EP1/EP2 tracks from cluster resultspy` 
2. `step2_download_era5_parallel. Download ERA5 fields (run **remotely**)py` 
3. `step2_1_download_era5_monthly_means. Download monthly mean climatology (run **remotely**)py` 
4. `step3_precompute_composites. Compute composites (run **remotely**)py` 
5. `step4_create_figures. Create composite figures (run **locally**)py` 
6. `step5_update_scientific_notes. Update SCIENTIFIC_NOTES.md and regenerate PDF (run **locally**)py` 

**Inputs:** `results/cluster/kmeans_clustered_data.csv`, ERA5 via CDS API

**Outputs:** `data/era5_ep_structure/precomputed_composites_ep1.nc`, `data/era5_ep_structure/precomputed_composites_ep2.nc`, `figures/`, `docs/scientific_notes_ep_structure.pdf`

---

### `ck_subterms_ Barotropic Conversion Decompositionanalysis/` 

16.48 )).W m

**Pipeline:**

1. `step1_prepare_tracks. Convert EP1 cyclone tracks to LorenzCycleToolkit formatpy` 
2. `step2_run_lec_toolkit. Run LorenzCycleToolkit with automatic ERA5 downloadpy` 
3. `step2_monitor_ck. Monitor job progresspy` 

**Prerequisite:** Cluster results `results/cluster/kmeans_clustered_data.csv` (from `cluster_analysis_energy_patterns`).

**Inputs:** `results/cluster/kmeans_clustered_data.csv`, ERA5 (auto-downloaded by toolkit)

**Outputs:** `data/ck_analysis/`, `results/ck_analysis/`

---

### `preprocess_ Data Download and Preprocessingdata/` 

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

### ` Shared Utility Functionsutils/` 

Shared utility functions used across the repository.

| Module | Description |
|--------|-------------|
| `load_data.py` | Load cyclone tracks and energy data |
| `gap_statistic.py` | Gap Statistic implementation (Tibshirani et al. 2001) |

---

### `setup_and_ Environment Verification and Templatesexamples/` 

| Script | Description |
|--------|-------------|
| `verify_environment.py` | Check all required packages are installed |
| `example_analysis.py` | Minimal working example of a complete analysis |
| `template_analysis.py` | Boilerplate template for new scripts |

---

### ` Documentation Compilerdocumentation/` 

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


---

## Section: scripts/main

> Source: `scripts/main/README.md`

# Main Figure Scripts

This directory contains scripts for generating publication-ready figures used in the Energy Patterns manuscript. Each script produces figure(s) formatted according to Scientific Reports guidelines (300 DPI, specific dimensions, consistent styling).

## Script Organization

Scripts are numbered according to the order of figures in the manuscript:

### Main Figures

- **`01_figure_tracks_genesis_frequency.py`**  
  Figure 1: Study area and workflow overview

- **`02_figure_20070643_publication.py`**  
  Figure 2: Case study — Cyclone 20070643 energetics and trajectory

- **`03_make_phase_density_2x2.py`**  
  Figure 3: Phase space density distributions (2×2 layout)

- **`04_figure_lps_combined.py`**  
  Figure 4: Lorenz Phase Space for Energy Patterns (EP1–EP3)

- **`05_figure_intensity_seasonality_trends.py`**  
  Figure 5: Energy Pattern characteristics (intensity, seasonality, trends)

- **`06_figure_genesis_density_kde.py`**  
  Figure 6: Genesis density using Kernel Density Estimation (Hoskins & Hodges method)

- **`07_figure_ep1_instability_composite.py`**  
  Figure 7: EP1 instability composite (4×3 layout: RK, PV, EGR diagnostics)

### Supplementary Figures

- **`S1_figure_pca_clustering_validation.py`**  
  Figure S1: PCA and clustering validation

- **`S2_figure_vertical_levels.py`**  
  Figure S2: Vertical distribution of energy conversions (Ca and Ck) for EP1, EP2, and EP3 cyclones — three side-by-side boxes per pressure level  
  *Requires: Zenodo LEC archive in `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` (DOI: 10.5281/zenodo.18243447)*

## Usage

Each script can be executed independently:

```bash
python scripts/main/01_figure_tracks_genesis_frequency.py
python scripts/main/02_figure_20070643_publication.py
# ... etc.
```

Or generate all figures sequentially:

```bash
python scripts/main/run_all.py
```

## Dependencies

All figure scripts require:
- Processed track data: `data/tracks_SAt_filtered_with_energetics_processed.csv`
- Clustering results: `results/cluster/kmeans_clustered_data.csv`

Some scripts have additional requirements (see individual script headers for details).

## Outputs

Generated figures are saved to: `figures/main/`

## Notes

- Figures S2 and S3 depend on outputs from the `ep_structure_analysis` pipeline (`scripts/ep_structure_analysis/`). Run steps 1–3 of that pipeline first to generate the composites in `data/era5_ep_structure/`.
- All scripts include configuration sections at the top for customizing plot parameters (colors, dimensions, labels, etc.) without modifying core logic.
- For detailed figure descriptions, methodology, and scientific interpretation, see `figures/main/README.md`.


---

## Section: scripts/exploratory

> Source: `scripts/exploratory/README.md`

# Exploratory Scripts

General preliminary exploratory scripts used during the investigation phase of the project. These scripts are **not part of the final paper pipeline** — they predate or informally support the main analyses but are not called by any production pipeline.

---

## Purpose

This directory holds scripts that were used to:
- Explore the energy term distributions across Energy Patterns
- Compare normalisation approaches before selecting the final method
- Prototype composite calculations
- Generate informal figures for internal scientific discussion

---

## Scripts

| Script | Description |
|--------|-------------|
| `analyze_ep_characteristics.py` | Compute and tabulate statistical characteristics of each Energy Pattern |
| `density_diagrams_with_ge.py` | Density diagrams including the diabatic generation term Ge |
| `exploring_clustering.ipynb` | Interactive Jupyter notebook for K-Means clustering exploration |
| `exploring_pca.ipynb` | Interactive Jupyter notebook for PCA exploration |
| `figure_genesis_density_relative_kde.py` | Relative genesis density maps using KDE |
| `figure_minmax_vs_zscore_comparison.py` | Comparison of min-max vs z-score normalisation on clustering outcome |
| `figure_most_intense_cyclone_lps.py` | Lorenz Phase Space diagram for the single most intense cyclone |
| `figure_three_intense_cyclones_individual.py` | Individual LPS diagrams for three intense cyclones |
| `figure_three_intense_cyclones_individual_zoom.py` | Zoomed versions of the three intense cyclone plots |
| `kde_pairplot.py` | KDE pairwise contour plot matrix for selected energy terms across lifecycle phases |
| `plot_ep_lps_diagrams.py` | LPS diagrams grouped by Energy Pattern |
| `plot_pv_jet_composite.py` | Early prototype composite of PV and jet-stream fields |
| `precompute_composites.py` | Early prototype for precomputing ERA5 composites (superseded by `ep_structure_analysis/step3_precompute_composites.py`) |
| `scatter_density.py` | Scatter density plots of energy term pairs |
| `vertical_term_boxplots_ep1_ep2.py` | Box plots of vertical energy terms comparing EP1 and EP2 |

---

## Inputs

- `data/energy_cache.parquet` — Preprocessed energy data (generated by `scripts/preprocess_data/preprocess_data.py`)
- `results/cluster/kmeans_clustered_data.csv` — Cluster assignments (generated by `scripts/cluster_analysis_energy_patterns/`)

---

## Outputs

Figures are saved to `figures/exploratory/`. Results (if any) go to `results/exploratory/`.

---

## Notes

- Scripts in this directory are standalone — they do not depend on each other.
- No `run_all.py` orchestration is provided; run individual scripts as needed.
- For the final paper figure scripts, see `scripts/main/`.


---

## Section: scripts/cluster_analysis_energy_patterns

> Source: `scripts/cluster_analysis_energy_patterns/README.md`

# Cluster Analysis of Cyclone Energy Patterns

**Objective:** Identify and characterize distinct energetic patterns in South Atlantic cyclones through objective clustering analysis.

---

## 📄 Scientific Documentation

**Complete methodology, results, and interpretation:**  
→ [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md)

**Generate PDF version:**
```bash
python scripts/cluster_analysis_energy_patterns/generate_scientific_notes_pdf.py
```

**Output:** `docs/scientific_notes_cluster_analysis.pdf`

**Requirements:**
- Pandoc: `brew install pandoc` (macOS) or `sudo apt install pandoc` (Linux)
- XeLaTeX: `brew install basictex` (macOS) or `sudo apt install texlive-xetex` (Linux)

---

## 🎯 Quick Summary

This analysis uses **PCA + K-Means clustering** to objectively classify South Atlantic cyclones into three distinct **Energy Patterns (EPs)** based on Lorenz Energy Cycle diagnostics.

**Key Energy Terms:**
- **Ca**: Baroclinic conversion (APE → eddy APE)
- **Ck**: Barotropic conversion (KE → eddy KE)  
- **Ge**: Eddy APE generation
- **BAe/BKe**: Boundary fluxes (energy import/export)
- **Ae/Ke**: Energy reservoirs

**Results:**
- **EP1 (11.6%)**: Strong barotropic and baroclinic conversions (mean Ck = -16.48 W m⁻²)
- **EP2 (25.6%)**: Intermediate conversions (mean Ck = -3.49 W m⁻²)
- **EP3 (62.7%)**: Weak energetics (mean Ck = -1.71 W m⁻²)

See [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) for complete analysis.

---

## 🚀 Pipeline

### Run All Steps

```bash
# Complete pipeline (Steps 1-5)
python scripts/cluster_analysis_energy_patterns/run_all.py
```

### Individual Steps

**Step 1: Normalize and PCA**
```bash
python scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py
```
- Filters cyclones with complete lifecycles (3,820 cyclones, 56.3%)
- Phase-separated PCA (97% variance retained)
- Output: `results/cluster_analysis_energy_patterns/pca_*`

**Step 2: Plot PCA Results**
```bash
python scripts/cluster_analysis_energy_patterns/step2_plot_pca_results.py
```
- PC scatter plots, loadings heatmaps, scree plots
- Output: `figures/cluster_analysis_energy_patterns/pca_*`

**Step 3: Optimal k Analysis**
```bash
python scripts/cluster_analysis_energy_patterns/step3_optimal_k_analysis.py
```
- 5 cluster validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, Gap Statistic)
- Mean normalized score → **k = 3** optimal
- Output: `figures/cluster_analysis_energy_patterns/optimal_k_*`

**Step 4: Apply K-Means**
```bash
python scripts/cluster_analysis_energy_patterns/step4_apply_kmeans.py
```
- K-Means (k=3, n_init=100) on each phase
- Centroid reconstruction to original energy space
- Output: `results/cluster_analysis_energy_patterns/kmeans_*`

**Step 5: Plot Energy Patterns**
```bash
python scripts/cluster_analysis_energy_patterns/step5_plot_energy_patterns.py
```
- Lorenz Phase Space diagrams (Conversion + Imports)
- Zoom views for detailed pattern comparison
- Output: `figures/cluster_analysis_energy_patterns/lps_*`

---

## 📊 Methodology Summary

### Data Filtering
- **Original:** 6,789 cyclones
- **Filtered:** 3,820 cyclones (complete lifecycle: incipient → intensification → mature → decay)
- **Total records:** 15,280 (3,820 × 4 phases)

### Dimensionality Reduction
- **Input:** 7 energy terms (Ca, Ck, Ge, BAe, BKe, Ae, Ke)
- **Method:** Phase-separated PCA
- **Output:** ~6 PCs per phase (97% variance)

### Clustering
- **Method:** K-Means (k=3, determined by 5 cluster validity indices)
- **Application:** Phase-separated clustering
- **Output:** 3 Energy Patterns (EP1, EP2, EP3)

### Visualization
- **Lorenz Phase Space (LPS):**  
  1. Conversion LPS: Ck (barotropic) vs Ca (baroclinic)
  2. Imports LPS: BAe (APE flux) vs BKe (KE flux)

See [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) for detailed methodology
- Quadrant analysis reveals conversion direction and efficiency
- Marker characteristics add information about energy magnitude and generation

**Why LPS instead of bar plots/heatmaps?**: 
Energy terms have fundamentally different scales and physical meanings. The Lorenz Phase Space framework provides a physically meaningful visualization that respects the relationships between energy conversions and fluxes, rather than attempting direct magnitude comparisons across disparate variables.

## Results Structure

### Data Files (39 files)

**PCA Results** (20 files):
```
results/cluster/
├── pca_scores_{phase}.csv           # PC coordinates (includes track_id)
├── pca_full_data_{phase}.csv        # Original + scaled + PCs
├── pca_models_{phase}.pkl           # PCA & StandardScaler objects
├── pca_loadings_{phase}.csv         # Variable loadings on PCs
└── pca_explained_variance_{phase}.csv  # Variance explained by each PC
```

**Optimal K Analysis** (3 files):
```
results/cluster/
├── optimal_k.txt                    # Single value: k=3
├── optimal_k_raw_indices.csv        # Raw CVI values for k=3 to 15
└── optimal_k_normalized_indices.csv # Normalized & averaged CVIs
```

**Clustering Results** (16 files):
```
results/cluster/
├── kmeans_clustered_data_{phase}.csv    # Original data + cluster labels
├── kmeans_centroids_pc_{phase}.csv      # Centroids in PC space
├── kmeans_centroids_energy_{phase}.csv  # Centroids in energy space
├── kmeans_model_{phase}.pkl             # KMeans model object
---

## 📁 Results Structure

### Data Files
```
results/cluster_analysis_energy_patterns/
├── pca_scores_{phase}.csv              # PC scores for each cyclone
├── pca_loadings_{phase}.csv            # Variable contributions to PCs
├── pca_variance_{phase}.csv            # Explained variance ratios
├── pca_models.pkl                      # Saved PCA transformations
├── optimal_k_scores.csv                # CVI scores for k=2..10
├── kmeans_clustered_data_{phase}.csv   # Cluster assignments
├── kmeans_centroids_{phase}.csv        # Cluster centroids (PC space)
├── kmeans_centroids_energy_{phase}.csv # Centroids (original energy space)
└── kmeans_summary_{phase}.csv          # Cluster statistics
```

### Figures
```
figures/cluster_analysis_energy_patterns/
├── pca/
│   ├── scatter_{phase}.png       # PC pair-wise plots
│   ├── loadings_{phase}.png      # Variable loadings heatmaps
│   └── variance_{phase}.png      # Scree plots
├── optimal_k_analysis.png        # CVI comparison (k=2..10)
└── lps_conversion_zoom.png       # Conversion LPS (Ck vs Ca)
└── lps_imports_zoom.png          # Imports LPS (BAe vs BKe)
```

---

## 📖 References

**Lorenz Energy Cycle:**
- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.

**Cluster Validation:**
- Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *J. Comput. Appl. Math.*, 20, 53-65.
- Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. *IEEE TPAMI*, 1(2), 224-227.
- Caliński, T., & Harabasz, J. (1974). A dendrite method for cluster analysis. *Comm. Stat. Theory Methods*, 3(1), 1-27.
- Tibshirani, R., Walther, G., & Hastie, T. (2001). Estimating the number of clusters via the gap statistic. *J. R. Stat. Soc. B*, 63(2), 411-423.
- Saitta, S., Raphael, B., & Smith, I. F. C. (2008). A comprehensive validity index for clustering. *Intell. Data Anal.*, 12(6), 529-548.

**South Atlantic Cyclones:**
- Reboita, M. S., et al. (2010). South Atlantic Ocean cyclogenesis climatology simulated by RegCM3. *Clim. Dyn.*, 35, 1331-1347.
- Gramcianinov, C. B., et al. (2020). Analysis of Atlantic extratropical storm tracks in 41 years of ERA5 and CFSR/CFSv2. *Ocean Eng.*, 216, 108111.

---

**Author:** Danilo Couto de Souza  
**Date:** February 2026  
**Last Updated:** February 23, 2026


---

## Section: scripts/ep_structure_analysis

> Source: `scripts/ep_structure_analysis/README.md`

# EP Structure Analysis: EP1 vs EP2 Cyclone Comparison

## Objective

Investigate the spatial structure of EP1 and EP2 cyclones during intensification,
using standard dynamical diagnostics to understand what distinguishes each energy
pattern structurally.

## Important: Consistency with Cluster Analysis

**CRITICAL:** All cyclones used in this analysis come directly from the cluster
assignments in `results/cluster/kmeans_clustered_data.csv`. The clustering was
performed on cyclones already filtered for complete lifecycle (incipient →
intensification → mature → decay). Therefore:

- **NO additional lifecycle filtering** is applied in this pipeline
- **ALL 444 EP1 cyclones** from cluster 0 are used (100% consistency)
- **ALL 979 EP2 cyclones** from cluster 2 are used (100% consistency)

This ensures that the structural analysis describes the **exact same cyclones**
used to define the energy patterns, maintaining methodological consistency
throughout the study.

## Diagnostic Fields

| Field | Levels | Purpose | Key References |
|-------|--------|---------|----------------|
| **EGR** (Eady Growth Rate) | 500–850 hPa layer | Measures baroclinic instability of the background flow | Lindzen & Farrell (1980); Besson et al. (2021) |
| **PV** (Potential Vorticity) | 200 hPa | Upper-level tropopause dynamics and stratospheric intrusions | Hoskins et al. (1985); Davis & Emanuel (1991); Rossa et al. (2000) |
| **PV** (Potential Vorticity) | 850 hPa | Low-level PV anomaly associated with surface cyclone | Hoskins et al. (1985); Davis (1992); Čampa & Wernli (2012) |
| **Temperature advection** | 850 hPa | Warm/cold advection patterns linked to QG forcing for ascent | Sutcliffe (1947); Sanders & Gyakum (1980); Sinclair (1994) |
| **Specific humidity** | 975 hPa | Low-level moisture distribution | Bao et al. (2002); Schär & Wernli (1993) |
| **Moisture flux divergence** | 975 hPa | Moisture convergence/divergence → convective potential | Banacos & Schultz (2005); Lackmann (2011) |
| **SLP** (Sea Level Pressure) | Surface | Cyclone position, intensity and horizontal structure | Hoskins & Hodges (2005); Reboita et al. (2010) |
| **RK criterion** (Rayleigh-Kuo) | 250 hPa | Barotropic/baroclinic instability necessary condition | Rayleigh (1880); Kuo (1949); Charney & Stern (1962) |
| **KE advection** | 250 hPa | Kinetic energy tendency from advection in jet stream | - |
| **AFC** (Ageostrophic Flux Convergence) | 250 hPa | Eddy KE source/sink from ageostrophic pressure work | Orlanski & Katzfey (1991); Orlanski & Sheldon (1993) |

**Anomaly diagnostics** (departure from 1991–2020 WMO climatology — same decomposition as AFC):

| Anomaly Field | Level | Output variable | Climatology group |
|---------------|-------|-----------------|-------------------|
| **PV′** | 200 hPa | `pv_200_anom` | `pv200` (175/200/225 hPa, u,v,t) |
| **PV′** | 850 hPa | `pv_850_anom` | `pv850` (825/850/875 hPa, u,v,t) |
| **Temp advection′** | 850 hPa | `adv_T_850_anom` | `pv850` (u,v,t at 850 hPa) |
| **Moisture flux div′** | 975 hPa | `div_q_975_anom` | `mfd975` (975 hPa, u,v,q) |
| **KE advection′** | 250 hPa | `ke_adv_250_anom` | `250hPa` (u,v at 250 hPa) |
| **SLP′** | Surface | `msl_anom` | `slp` (msl, single-level) |

> **Note:** EGR is not decomposed (layer-mean nature makes eddy decomposition ill-defined).
> AFC is already an anomaly field by construction (uses $\phi'$ and $\vec{v}'$).

### Level selection rationale

- **EGR (250–850 hPa):** The 250–850 hPa layer captures the main tropospheric
  baroclinic zone. This layer-mean approach is standard since Hoskins & Valdes (1990)
  and has been widely applied in Southern Hemisphere cyclone studies (Simmonds & Lim,
  2009; Gramcianinov et al., 2019). The growth rate σ = 0.31·f/N·|∂V/∂z| integrates
  the static stability (N) and vertical wind shear over the full depth of the
  troposphere.

- **PV at 200 hPa:** The dynamic tropopause is traditionally defined as the 2 PVU
  surface, typically found near 200 hPa in midlatitudes (Hoskins et al., 1985).
  Upper-level PV anomalies (tropopause folds) are precursors for rapid cyclogenesis
  (Davis & Emanuel, 1991; Rossa et al., 2000). The 200 hPa level is widely used in
  extratropical cyclone composites (e.g., Dacre et al., 2012; Catto et al., 2010).

- **PV at 850 hPa:** Low-level PV anomalies are generated by diabatic heating
  (latent heat release) and are a key component of the "PV tower" structure in
  explosively deepening cyclones (Čampa & Wernli, 2012; Martínez-Alvarado et al.,
  2016). The 850 hPa level is standard for characterizing the lower-tropospheric
  cyclone circulation.

- **Temperature advection at 850 hPa:** The 850 hPa level is the standard
  reference for thermal advection in synoptic analysis (e.g., Sanders & Gyakum,
  1980; Sinclair, 1994). Warm air advection (WAA) ahead of the surface cyclone
  is a primary quasi-geostrophic forcing for upward motion (Sutcliffe, 1947;
  Trenberth, 1978), while cold air advection (CAA) in the rear contributes to
  frontal structure and cyclone deepening.

- **SLP:** Standard field for cyclone tracking and composite analysis (Hoskins &
  Hodges, 2005; Reboita et al., 2010).

- **Moisture fields at 975 hPa:** The 975 hPa level captures near-surface moisture
  transport while remaining above the planetary boundary layer turbulence. Moisture
  flux divergence (∇·(qV)) identifies regions of moisture convergence (negative
  values) associated with convective potential and latent heat release, a key
  diabatic process in cyclone intensification (Banacos & Schultz, 2005; Lackmann,
  2011). The calculation uses MetPy's spherical geometry-aware gradient operators
  and physical constants to ensure consistency.

- **RK criterion at 250 hPa:** The Rayleigh-Kuo stability criterion provides a
  necessary condition for barotropic and baroclinic instability. Computed as
  ∂q/∂y = β - ∂²u/∂y², where negative values indicate regions satisfying the
  instability criterion. The 250 hPa level is chosen as representative of the
  jet stream, where barotropic processes are strongest.

- **KE advection at 250 hPa:** Kinetic energy advection (-V · ∇KE) quantifies
  the tendency for KE to increase or decrease due to advection within the jet
  stream. Positive values indicate regions where the flow is accelerating, while
  negative values indicate deceleration. Computed at 250 hPa to capture jet-level
  dynamics.

- **AFC at 250 hPa:** Ageostrophic Flux Convergence (Orlanski & Katzfey, 1991;
  Orlanski & Sheldon, 1993) quantifies how ageostrophic pressure work
  redistributes eddy kinetic energy. A **temporal decomposition** is used:
  the 30-year monthly climatology (1991–2020, WMO standard) serves as the base
  state (V_m, Φ_m), and the instantaneous departure is the eddy perturbation.
  This is deliberately independent of the area-mean decomposition used in the
  Lorenz Energy Cycle analysis to avoid circular validation. Positive AFC
  indicates an eddy KE source; negative values indicate a sink.

## Pipeline Structure

### Steps

| Step | Script | Run on | Description |
|------|--------|--------|-------------|
| 1 | `step1_select_ep_tracks.py` | Local/Remote | Select EP1 and EP2 cyclone tracks |
| 2 | `step2_download_era5_parallel.py` | **Remote** | Download ERA5 data (parallel, with patching) |
| 2.1 | `step2_1_download_era5_monthly_means.py` | **Remote** | Download ERA5 monthly means → 30-year climatologies for all anomaly diagnostics (4 variable groups: 250hPa, pv200, pv850, mfd975). Smart completeness check automatically skips already-downloaded months. |
| 2M | `step2_monitor.py` | Local/Remote | **Monitor download progress** (see below) |
| 3 | `step3_precompute_composites.py` | **Remote** | Compute field composites (EGR, PV, adv_T, SLP, RK, KE_adv) |
| 4 | `step4_create_figures.py` | Local | Create EP1 vs EP2 composite figures |
| 5 | `step5_update_scientific_notes.py` | Local | Populate SCIENTIFIC_NOTES.md with regional statistics + generate PDF |

### Monthly climatology download (`step2_1_download_era5_monthly_means.py`)

Downloads 12-month ERA5 climatologies (1991–2020) for all anomaly diagnostics, organized into four groups:

| Group | Levels (hPa) | Variables | Output file |
|-------|-------------|-----------|-------------|
| `250hPa` | 250 | u, v, z | `era5_climatology_250hPa.nc` |
| `pv200` | 175, 200, 225 | u, v, t | `era5_climatology_pv200.nc` |
| `pv850` | 825, 850, 875 | u, v, t | `era5_climatology_pv850.nc` |
| `mfd975` | 975 | u, v, q | `era5_climatology_mfd975.nc` |
| `slp` | surface | msl | `era5_climatology_slp.nc` |

```bash
# Download all groups (auto-skips valid existing files)
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py

# Download specific groups only
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py --groups pv200 pv850 mfd975

# Only recompute climatology files from already-downloaded raw data
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py --clim-only

# Force re-download of specific months (e.g. June and July)
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py --force-months 6 7
```

> The `250hPa` group reuses existing `era5_raw_month{MM}.nc` files without re-downloading, preserving backward compatibility.

### Download monitor (`step2_monitor.py`)

`step2_monitor.py` scans `data/era5_ep_structure/` and reports completeness at the
finest available granularity: one **slot** = one (variable, pressure-level) pair.

```
Slots per case = 5 pressure vars × 9 levels  +  1 SLP  =  46 slots total
```

**Features:**
- **Process detection**: Automatically detects if `step2_download_era5_parallel.py` 
  is running and shows PID, runtime, CPU%, and memory usage (requires `psutil`)
- **Per-variable table**: how many cases have that variable with all 9 levels
- **Per-level table**: how many cases have that level with all 5 variables
- **Composite check**: whether `precomputed_composites_ep{1,2}.nc` (step 3 output)
  already exist

```bash
# Install psutil for process detection (optional but recommended)
pip install psutil

# One-shot report (shows current state and exits)
python scripts/ep_structure_analysis/step2_monitor.py

# Live watch while step 2 is running (refresh every 60 s)
python scripts/ep_structure_analysis/step2_monitor.py --watch

# Faster refresh (every 30 s)
python scripts/ep_structure_analysis/step2_monitor.py --watch --interval 30

# No terminal clear — safe for nohup / log capture
python scripts/ep_structure_analysis/step2_monitor.py --watch --no-clear
```

Example output (with download process active):

```
══════════════════════════════════════════════════════════════════════════════
  ERA5 EP STRUCTURE — DOWNLOAD MONITOR
  Scanned : 2026-02-20 14:30:00  (3.2 s)
  Dir     : …/data/era5_ep_structure
  Slots   : 46 per case  = 5 pressure vars × 9 levels + 1 SLP
  ⬇ DOWNLOAD ACTIVE  PID=12345  Runtime=2h 15m 30s  CPU=45.2%  RAM=512MB
══════════════════════════════════════════════════════════════════════════════

  EP1  slots  [████████████░░░░░░░░░░░░░░░░░░]    5520/20424  (27.0%)
       cases  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]     120/444   (27.0%)  (fully complete)
       detail  ✓ complete: 120  ⚑ partial: 150  ✗ missing: 174
       disk    45.2 GB

  EP2  slots  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]   12150/45034  (27.0%)
       cases  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]     264/979   (27.0%)  (fully complete)
       detail  ✓ complete: 264  ⚑ partial: 330  ✗ missing: 385
       disk    98.5 GB
…
```

### Scientific Documentation

#### PDF generation

Generate a professional PDF version of SCIENTIFIC_NOTES.md:

```bash
python scripts/ep_structure_analysis/generate_scientific_notes_pdf.py
```

**Requirements:**
- [Pandoc](https://pandoc.org/) (Markdown → PDF converter)
- LaTeX distribution (pdflatex, for PDF rendering)

**Install on macOS:**
```bash
brew install pandoc basictex
```

**Install on Linux:**
```bash
sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```

**Output:** `docs/scientific_notes_ep_structure.pdf`

The script:
- ✅ Automatically checks for pandoc and pdflatex
- ✅ Tries eisvogel template first (fancy), falls back to basic
- ✅ Opens the PDF automatically after generation (optional)
- ✅ Works on macOS, Linux, and Windows

#### Code verification tests

Verify that spherical grid spacing and gradient calculations work correctly:

```python
# Run test suite
import numpy as np
from step3_precompute_composites import compute_spherical_grid_spacing

# Test 1: Uniform field → zero gradient
lat = np.linspace(-30, 30, 10)
lon = np.linspace(-30, 30, 10)
dx, dy, lat_2d, lon_2d = compute_spherical_grid_spacing(lat, lon)

T = np.ones_like(lat_2d)  # uniform temperature
dT_dx = np.gradient(T, axis=1) / dx
dT_dy = np.gradient(T, axis=0) / dy[:, np.newaxis]

assert np.allclose(dT_dx, 0)
assert np.allclose(dT_dy, 0)
print("✅ Test 1 passed: uniform field → zero gradient")

# Test 2: Reversed latitude coordinates
lat_rev = np.linspace(30, -30, 10)  # decreasing (some datasets have this)
dx_rev, dy_rev, _, _ = compute_spherical_grid_spacing(lat_rev, lon)
# Should still give correct physical spacing (positive)
assert np.all(dy_rev > 0)
print("✅ Test 2 passed: reversed latitude → correct spacing")

# Test 3: Linear latitude gradient
T_linear = lat_2d.copy()  # Temperature = latitude
dT_dy_analytic = 1.0 / (111320.0)  # 1°/distance (approximate)
dT_dy_numeric = np.gradient(T_linear, axis=0) / dy[:, np.newaxis]
# Should be approximately constant
assert np.std(dT_dy_numeric) / np.mean(np.abs(dT_dy_numeric)) < 0.1
print("✅ Test 3 passed: linear gradient → consistent derivative")
```

**Expected typical values** (for sanity checks during processing):

| Diagnostic | Typical Range | Units |
|------------|---------------|-------|
| EGR (250–850 hPa) | 0.3 – 1.5 | day⁻¹ |
| PV @ 200 hPa | 1 – 5 | PVU |
| PV @ 850 hPa | 0.1 – 1.0 | PVU |
| Temperature advection @ 850 hPa | ±2 – 5 | K h⁻¹ |
| Moisture flux divergence @ 975 hPa | ±5 – 20 | g kg⁻¹ s⁻¹ |
| SLP minimum | 950 – 995 | hPa |

If values fall far outside these ranges, check:
- Coordinate orientation (latitude increasing vs. decreasing)
- Unit consistency (K vs. °C, Pa vs. hPa)
- Domain extent (should be 30° × 30° centered on cyclone)

See [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) Section 7 for full quality control details.

### Remote server execution

Steps 2–3 require significant compute/storage and should run on the remote server:

```bash
# On remote server (master.iag.usp.br)
cd /discos-varal/swell/p1-swell/danilocs/paper_energy_patterns

# Step 1 (can run locally or remotely)
python scripts/ep_structure_analysis/step1_select_ep_tracks.py

# Step 2 – download ERA5 (use nohup for long-running download)
nohup python scripts/ep_structure_analysis/step2_download_era5_parallel.py --jobs 4 &

# Monitor download progress in another terminal
python scripts/ep_structure_analysis/step2_monitor.py --watch

# Step 3 – precompute composites
nohup python scripts/ep_structure_analysis/step3_precompute_composites.py &
```

### Transfer to local machine

```bash
# Transfer precomputed composites only (~100-300 MB vs ~30-60 GB raw ERA5)
bash scripts/ep_structure_analysis/transfer_guide_scp.sh
```

Or manually:
```bash
scp -i ~/Documents/Master/id_rsa.danilocs -C \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/data/era5_ep_structure/precomputed_composites_\*.nc \
    ./data/era5_ep_structure/
```

### Local execution (after transfer)

```bash
# Step 4 – create figures
python scripts/ep_structure_analysis/step4_create_figures.py

# Step 5 – update scientific notes with regional statistics
python scripts/ep_structure_analysis/step5_update_scientific_notes.py

# Step 5 – with PDF generation (requires pandoc + xelatex)
python scripts/ep_structure_analysis/step5_update_scientific_notes.py --pdf
```

**Step 5 computes:**
- Global statistics (mean, std, min, max)
- Regional statistics: Full 30×30° domain, Central 15×15° LEC domain, NW/NE/SW/SE quadrants  
- Populates all `{PLACEHOLDER}` variables in SCIENTIFIC_NOTES.md
- Optionally generates PDF via pandoc

## ERA5 Variables Downloaded

**Pressure levels (hPa):** 175, 200, 225, 250, 500, 825, 850, 875, 975

| Levels | Purpose |
|--------|---------||
| 250, 850 | EGR layer bounds (vertical wind shear + static stability) |
| 175, 200, 225 | PV at 200 hPa (centered finite difference for ∂θ/∂p) |
| 825, 850, 875 | PV at 850 hPa (centered finite difference for ∂θ/∂p) |
| 850 | Temperature advection (u, v, T at 850 hPa) |
| 500 | Mid-tropospheric reference for stability profile |
| 975 | Low-level moisture flux (u, v, q at 975 hPa) |

**Pressure-level variables:** u, v, t, z (geopotential), q (specific humidity)

**Single-level variables:** msl (mean sea level pressure)

**Domain:** 30° × 30° centred on cyclone track centre during intensification

## Output

### Data
- `data/era5_ep_structure/` — raw ERA5 files (remote only) + precomputed composites
- `results/ep_structure/` — case lists, statistics

### Figures
- `figures/ep_structure/` — EP1 vs EP2 composite comparison panels

  **Total-field figures:**
  - `composite_egr.png` — Eady Growth Rate (250–850 hPa)
  - `composite_pv200.png` — PV at 200 hPa + 250 hPa wind vectors
  - `composite_pv850.png` — PV at 850 hPa + 850 hPa wind vectors
  - `composite_advT850.png` — Temperature advection at 850 hPa
  - `composite_moisture_flux.png` — Specific humidity + moisture flux divergence at 975 hPa
  - `composite_slp.png` — Sea level pressure
  - `composite_rk_criterion.png` — Rayleigh-Kuo criterion at 250 hPa
  - `composite_ke_advection.png` — Kinetic energy advection at 250 hPa
  - `composite_afc_250.png` — AFC at 250 hPa (eddy by construction)

  **Anomaly figures** (departure from 1991–2020 climatology; require `step2_1` multi-group download):
  - `composite_pv200_anom.png` — PV′ at 200 hPa + 250 hPa wind vectors
  - `composite_pv850_anom.png` — PV′ at 850 hPa + 850 hPa wind vectors
  - `composite_advT850_anom.png` — Temperature advection anomaly at 850 hPa
  - `composite_moisture_flux_anom.png` — Moisture flux divergence anomaly at 975 hPa
  - `composite_ke_advection_anom.png` — KE advection anomaly at 250 hPa
  - `composite_slp_anom.png` — SLP anomaly + 850 hPa wind vectors

  Each figure shows EP1 (left) vs EP2 (right). 15°×15° dashed box marks the LEC domain.

### Logs
- `logs/ep_structure_*.log` — detailed execution logs

## Data Storage

| Component | Size | Location |
|-----------|------|----------|
| Raw ERA5 (EP1 + EP2) | ~30-60 GB | Remote server only |
| Precomputed composites | ~100-300 MB | Local + remote |
| Figures | ~5-15 MB | Local |

## Cluster → EP Mapping

From `scripts/exploratory/analyze_ep_characteristics.py`:

| Cluster | Energy Pattern | Ck Characteristic |
|---------|---------------|-------------------|
| 0 | EP1 | Strong baroclinic and barotropic |
| 2 | EP2 | Intermediate conversions and strong imports of energy |
| 1 | EP3 | Day-to-day cyclones |

## References

- Banacos, P. C., & Schultz, D. M. (2005). The use of moisture flux convergence in forecasting convective initiation: Historical and operational perspectives. *Weather and Forecasting*, 20(3), 351–366.
- Bao, J.-W., Michelson, S. A., Persson, P. O. G., Djalalova, I. V., & Wilczak, J. M. (2002). Observed and WRF-simulated low-level winds in a high-ozone episode during the Central California Ozone Study. *Journal of Applied Meteorology and Climatology*, 41(9), 941–961.
- Čampa, J., & Wernli, H. (2012). A PV perspective on the vertical structure of mature midlatitude cyclones in the Northern Hemisphere. *Journal of the Atmospheric Sciences*, 69(2), 725–740.
- Catto, J. L., Shaffrey, L. C., & Hodges, K. I. (2010). Can climate models capture the structure of extratropical cyclones? *Journal of Climate*, 23(7), 1621–1635.
- Charney, J. G., & Stern, M. E. (1962). On the stability of internal baroclinic jets in a rotating atmosphere. *Journal of the Atmospheric Sciences*, 19(2), 159–172.
- Dacre, H. F., Hawcroft, M. K., Stringer, M. A., & Hodges, K. I. (2012). An extratropical cyclone atlas. *Bulletin of the American Meteorological Society*, 93(10), 1497–1502.
- Davis, C. A. (1992). A potential-vorticity diagnosis of the importance of initial structure and condensational heating in observed extratropical cyclogenesis. *Monthly Weather Review*, 120(11), 2409–2428.
- Davis, C. A., & Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. *Monthly Weather Review*, 119(8), 1929–1953.
- Gramcianinov, C. B., Hodges, K. I., & Camargo, R. (2019). The properties and genesis environments of South Atlantic cyclones. *Climate Dynamics*, 53, 4115–4140.
- Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Quarterly Journal of the Royal Meteorological Society*, 111(470), 877–946.
- Hoskins, B. J., & Valdes, P. J. (1990). On the existence of storm-tracks. *Journal of the Atmospheric Sciences*, 47(15), 1854–1864.
- Hoskins, B. J., & Hodges, K. I. (2005). A new perspective on Southern Hemisphere storm tracks. *Journal of Climate*, 18(20), 4108–4129.
- Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *Journal of Meteorology*, 6(2), 105–122.
- Lackmann, G. M. (2011). *Midlatitude Synoptic Meteorology: Dynamics, Analysis, and Forecasting*. American Meteorological Society.
- Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *Journal of the Atmospheric Sciences*, 37(7), 1648–1654.
- Martínez-Alvarado, O., Gray, S. L., & Methven, J. (2016). Diabatic processes and the evolution of two contrasting extratropical cyclones. *Monthly Weather Review*, 144(9), 3251–3276.
- Rayleigh, Lord (1880). On the stability, or instability, of certain fluid motions. *Proceedings of the London Mathematical Society*, s1-11(1), 57–72.
- Reboita, M. S., da Rocha, R. P., Ambrizzi, T., & Sugahara, S. (2010). South Atlantic Ocean cyclogenesis climatology simulated by regional climate model (RegCM3). *Climate Dynamics*, 35, 1331–1347.
- Rossa, A. M., Wernli, H., & Davies, H. C. (2000). Growth and decay of an extra-tropical cyclone's PV-tower. *Meteorology and Atmospheric Physics*, 73, 139–156.
- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb." *Monthly Weather Review*, 108(10), 1589–1606.
- Schär, C., & Wernli, H. (1993). Structure and evolution of an isolated semi-geostrophic cyclone. *Quarterly Journal of the Royal Meteorological Society*, 119(514), 57–90.
- Simmonds, I., & Lim, E.-P. (2009). Biases in the calculation of Southern Hemisphere mean baroclinic eddy growth rate. *Geophysical Research Letters*, 36(1), L01707.
- Sinclair, M. R. (1994). An objective cyclone climatology for the Southern Hemisphere. *Monthly Weather Review*, 122(10), 2239–2256.
- Sutcliffe, R. C. (1947). A contribution to the problem of development. *Quarterly Journal of the Royal Meteorological Society*, 73(317–318), 370–383.
- Trenberth, K. E. (1978). On the interpretation of the diagnostic quasi-geostrophic omega equation. *Monthly Weather Review*, 106(1), 131–137.

---

**Author:** Danilo Couto de Souza
**Date:** February 2026


---

## Section: scripts/ck_subterms_analysis

> Source: `scripts/ck_subterms_analysis/README.md`

# Ck Subterms Analysis: Barotropic Energy Conversion Decomposition

## Scientific Motivation

The barotropic conversion term (Ck) represents the conversion of kinetic energy between the zonal mean and eddy components. In the context of extratropical cyclones in the Southwestern Atlantic, Ck quantifies the energy transfer from eddy kinetic energy (Ke) to zonal mean kinetic energy (Kz):

$$Ck = -\overline{u'v'}\frac{\partial \overline{u}}{\partial y} - \overline{u'w'}\frac{\partial \overline{u}}{\partial p} - \overline{v'w'}\frac{\partial \overline{v}}{\partial p}$$

where:
- $u$, $v$, $w$ are zonal, meridional, and vertical wind components
- Primes ($'$) denote deviations from the area mean (eddy components)
- Overbars ($\overline{}$) denote area averages (mean state)

**Physical Interpretation**:
- **Negative Ck**: Energy flows from eddies to mean flow (Ke → Kz)
  - Typical during cyclone intensification in baroclinic zones
  - Eddy momentum fluxes decelerate the mean flow
- **Positive Ck**: Energy flows from mean flow to eddies (Kz → Ke)
  - Associated with barotropic instability
  - Mean flow accelerates the eddies

### Energy Pattern 1 (EP1) Characteristics

EP1 cyclones exhibit the strongest energetic conversions in the Southwestern Atlantic:
- **Mean Ck**: -16.48 W/m² (strongest barotropic conversion among all patterns)
- **Frequency**: 444 cyclones (11.6% of total)
- **Analysis scope**: ALL EP1 cyclones (no spatial restriction)
- **Vertical structure**: Ck minimum occurs at mid-tropospheric levels (~500-600 hPa)

## Research Questions

1. **What is the relative importance of each Ck subterm during EP1 cyclone intensification?**
   - Horizontal momentum flux: $-\overline{u'v'}\frac{\partial \overline{u}}{\partial y}$
   - Vertical momentum flux (zonal): $-\overline{u'w'}\frac{\partial \overline{u}}{\partial p}$
   - Vertical momentum flux (meridional): $-\overline{v'w'}\frac{\partial \overline{v}}{\partial p}$

2. **How do Ck subterms evolve throughout the cyclone lifecycle?**
   - Comparison across phases: incipient → intensification → mature → decay
   - Identification of dominant mechanisms in each phase

3. **Are there differences in Ck subterm contributions between different EP1 cyclones?**
   - Regional variations (genesis location, track orientation)
   - Seasonal variations (winter vs. summer systems)

4. **How does the updated LorenzCycleToolkit decomposition compare with previous results?**
   - Validation against Zenodo dataset (aggregated Ck)
   - Assessment of term-by-term contributions to total Ck

## Methodology

### Prerequisites

**IMPORTANT**: This analysis requires the cluster analysis results:
- `results/cluster/kmeans_clustered_data.csv` (produced by `scripts/cluster_analysis_energy_patterns/`)
- This file contains the EP assignments for all cyclones, including all 444 EP1 cyclones
- **No spatial restriction** — all EP1 cyclones regardless of genesis location are included

### Workflow Overview

```
Step 1: Prepare Track Files
    ↓
Step 2: Run LorenzCycleToolkit (automated ERA5 download & LEC computation)
    ↓
Step 3: Extract and Analyze Ck Subterms
    ↓
Step 4: Compare Lifecycle Evolution
    ↓
Step 5: Statistical Analysis and Visualization
```

---

### Step 1: Prepare Track Files for LorenzCycleToolkit

**Objective**: Convert ALL EP1 cyclone tracks to LorenzCycleToolkit input format.

**Input**:
- `results/cluster/kmeans_clustered_data.csv` — EP assignments from cluster analysis (444 EP1 cyclones)
- Main track database (via `load_tracks()`)

**Output Format** (one file per cyclone):
```
time;Lat;Lon
2005-08-08-0000;-22.5;-45.0
2005-08-08-0600;-23.0;-44.5
2005-08-08-1200;-23.5;-44.0
...
```

**File Naming**: `track_{track_id}.txt`
- Example: `track_20070643.txt`

**Output Directory**: `data/ck_analysis/tracks/`

**Key Considerations**:
- Time format: `YYYY-MM-DD-HHMM` (no spaces, dash before time)
- Header: `time;Lat;Lon` (capitalized)
- Coordinates: Latitude and Longitude in decimal degrees
- Delimiter: Semicolon (`;`) with NO spaces
- Data source: Full cyclone lifecycle (all phases, all timesteps)
- Temporal resolution: 3-hourly (matches project configuration)

**Script**: `step1_prepare_tracks.py`

---

### Step 2: Run LorenzCycleToolkit with ERA5 Download

**Objective**: Compute Lorenz Energy Cycle with full term decomposition using the updated toolkit version.

**LorenzCycleToolkit Configuration**:
```python
# Example configuration (to be adjusted)
from LorenzCycleToolkit import LorenzCycleAnalysis

# Initialize analysis
lec = LorenzCycleAnalysis(
    track_file='data/ck_analysis/tracks/track_20070643.txt',
    dataset='ERA5',
    auto_download=True,  # Automatically download ERA5 data
    pressure_levels='standard',  # All standard pressure levels
    spatial_filter='moving_box',  # Follow cyclone center
    box_size=15,  # 15° × 15° domain (consistent with EP1 analysis)
    decompose_terms=True  # Enable full term decomposition
)

# Run analysis
lec.compute()
lec.save_results('results/ck_analysis/lec_results/')
```

**Key Features of Updated Toolkit**:
- **Automatic ERA5 download**: No manual CDS API interaction needed
- **Term decomposition**: Separates Ck into individual subterms
- **Vertical resolution**: Maintains level-by-level information
- **Phase identification**: Uses CycloPhaser for lifecycle detection

**Output Structure** (per cyclone):
```
results/ck_analysis/lec_results/{track_id}_ERA5_track/
├── periods.csv              # Lifecycle phases
├── results.csv              # Integrated terms (all phases)
├── Ck_level.csv            # Total Ck by pressure level
├── Ck_uv_level.csv         # Horizontal momentum flux term
├── Ck_uw_level.csv         # Vertical momentum flux (zonal) term
├── Ck_vw_level.csv         # Vertical momentum flux (meridional) term
├── Ca_level.csv            # Baroclinic conversion (for reference)
└── ...                     # Other energy terms
```

**Computational Requirements**:
- **Storage**: ~500 MB per cyclone (ERA5 data + results)
- **Time**: ~30-60 min per cyclone (depending on lifecycle length)
- **Total for ALL EP1**: ~444 cyclones × 500 MB = ~222 GB
- **Processing**: Can be parallelized across cyclones

**Script**: `step2_run_lec_toolkit.py` (wrapper script)
- Iterates through prepared tracks
- Submits LorenzCycleToolkit jobs
- Monitors progress and handles errors

---

### Step 3: Extract and Analyze Ck Subterms

**Objective**: Load LEC results and extract Ck subterm contributions for all EP1 cyclones.

**Analysis Tasks**:

1. **Load Ck Subterms by Level**:
   - `Ck_uv(p)`: Horizontal momentum flux contribution
   - `Ck_uw(p)`: Vertical momentum flux (zonal) contribution
   - `Ck_vw(p)`: Vertical momentum flux (meridional) contribution
   - Validate: `Ck_total ≈ Ck_uv + Ck_uw + Ck_vw`

2. **Phase-Specific Analysis**:
   - Extract values during intensification phase only
   - Compare with mature and decay phases
   - Compute phase-averaged profiles

3. **Vertical Structure**:
   - Identify pressure level of maximum contribution for each subterm
   - Analyze vertical distribution (surface → upper troposphere)
   - Compare with Ck minimum level from Step 2 of EP1 analysis

4. **Relative Importance Metrics**:
   - Percentage contribution: $\frac{Ck_{subterm}}{Ck_{total}} \times 100\%$
   - Dominant term identification (largest absolute contribution)
   - Term consistency across cyclones (standard deviation)

**Output**:
- `results/ck_analysis/subterms_by_cyclone.csv` - Individual cyclone subterm values
- `results/ck_analysis/subterms_statistics.csv` - Ensemble statistics
- `results/ck_analysis/vertical_profiles.csv` - Mean profiles by phase

**Script**: `step3_extract_subterms.py`

---

### Step 4: Lifecycle Evolution Analysis

**Objective**: Quantify how Ck subterm contributions change throughout the cyclone lifecycle.

**Methodology**:

1. **Temporal Evolution**:
   - Time series of each subterm throughout lifecycle
   - Smoothed profiles (24h running mean)
   - Identification of transition points between phases

2. **Phase Composites**:
   - Mean subterm values by phase (incipient, intensification, mature, decay)
   - Vertical structure evolution (2D: pressure × phase)
   - Statistical significance testing (phase-to-phase changes)

3. **Energetic Pathway Analysis**:
   - Dominant mechanism identification by phase
   - Transitions: Which subterm leads intensification onset?
   - Which subterm sustains mature phase?

**Visualization**:
- Time-height cross-sections (pressure × time)
- Phase-composite boxplots (subterm × phase)
- Stacked area charts (relative contribution evolution)

**Output**:
- `figures/ck_analysis/lifecycle_evolution.png`
- `figures/ck_analysis/phase_composites.png`
- `results/ck_analysis/lifecycle_statistics.csv`

**Script**: `step4_lifecycle_analysis.py`

---

### Step 5: Statistical Analysis and Validation

**Objective**: Validate results against previous analysis and identify patterns.

**Validation**:

1. **Comparison with Zenodo Dataset**:
   - Compare aggregated Ck from new analysis with old results
   - Expected: Close agreement in total Ck values
   - Difference: New analysis provides subterm breakdown

2. **Consistency Checks**:
   - Mass budget conservation (total energy should be conserved)
   - Term magnitude reasonableness (compare with literature values)
   - Spatial averaging consistency

**Statistical Tests**:

1. **Inter-cyclone Variability**:
   - Standard deviation of subterm contributions
   - Coefficient of variation (CV = σ/μ)
   - Identification of outlier cyclones

2. **Regional/Seasonal Patterns**:
   - Subterm contributions vs. genesis latitude
   - Summer vs. winter differences (if data sufficient)
   - Track orientation effects (NE vs. SE propagation)

3. **Correlation Analysis**:
   - Subterm vs. cyclone intensity (maximum vorticity)
   - Subterm vs. lifecycle duration
   - Cross-correlations between subterms

**Output**:
- `figures/ck_analysis/validation_plots.png`
- `figures/ck_analysis/statistical_summary.png`
- `results/ck_analysis/final_report.txt`

**Script**: `step5_statistical_analysis.py`

---

## Expected Results

### Hypothesis 1: Horizontal Momentum Flux Dominance

**Expectation**: The horizontal momentum flux term ($-\overline{u'v'}\frac{\partial \overline{u}}{\partial y}$) will dominate Ck during intensification.

**Rationale**:
- EP1 cyclones occur in regions of strong baroclinicity
- Associated with strong meridional temperature gradients
- Thermal wind balance implies strong vertical wind shear
- Eddy momentum fluxes (u'v') transport momentum meridionally
- This is the "classic" barotropic conversion mechanism

**Expected Magnitude**: ~70-80% of total Ck

---

### Hypothesis 2: Vertical Level Structure

**Expectation**: Maximum Ck contributions occur at mid-tropospheric levels (500-700 hPa).

**Rationale**:
- Previous analysis shows Ck minimum at ~500-600 hPa
- This level corresponds to:
  - Maximum meridional wind shear ($\partial u/\partial y$)
  - Jet stream level in South Atlantic
  - Level of maximum eddy kinetic energy

**Implication**: Barotropic conversion is primarily a mid-tropospheric process in EP1 cyclones

---

### Hypothesis 3: Phase-Dependent Mechanisms

**Expectation**: Different subterms dominate in different lifecycle phases.

**Phase-Specific Predictions**:

1. **Incipient Phase**:
   - Weak Ck (small absolute values)
   - All subterms comparable in magnitude
   - Horizontal flux begins to dominate

2. **Intensification Phase**:
   - Horizontal momentum flux (u'v') dominates
   - Strong negative Ck (energy from eddies to mean flow)
   - Peak subterm magnitudes

3. **Mature Phase**:
   - Horizontal flux remains dominant but weakens
   - Vertical flux terms become relatively more important
   - Beginning of transition to decay

4. **Decay Phase**:
   - Weakening of all subterms
   - Possible reversal of some terms (positive contributions)
   - Dominance structure may shift

---

## Technical Notes

### Data Sources

1. **Cyclone Selection**:
   - From `results/cluster/kmeans_clustered_data.csv` (cluster analysis results)
   - 444 EP1 cyclones with complete lifecycle
   - No spatial domain restriction (all EP1 cyclones regardless of genesis location)

3. **ERA5 Reanalysis**:
   - Automatically downloaded by LorenzCycleToolkit
   - Standard pressure levels (1000-100 hPa)
   - 3-hourly temporal resolution
   - 0.25° spatial resolution

3. **Track Data**:
   - From main database via `load_tracks()`
   - Full lifecycle coverage
   - Vorticity center tracking

### LorenzCycleToolkit Updates

**New Version Features** (compared to Zenodo dataset):

1. **Term Decomposition**:
   - Previous: Only total Ck computed
   - New: Ck separated into three subterms

2. **Pressure Level Output**:
   - Previous: Single `Ck_level.csv` file
   - New: Separate files for each subterm (`Ck_uv_level.csv`, etc.)

3. **Corrections Applied**:
   - Previous version had sign/normalization issues (documented in EP1 analysis)
   - New version: Corrections already implemented
   - No post-processing corrections needed

4. **Automatic Workflow**:
   - Previous: Manual ERA5 download via CDS API
   - New: Integrated download within toolkit
   - Simplified workflow, fewer error points

### Spatial Domain Considerations

**Analysis Domain**: 15° × 15° box centered on cyclone

**Rationale**:
- Consistent with EP1 instability analysis (step3_download_era5.py)
- Large enough to capture synoptic-scale features
- Small enough to focus on cyclone-related processes
- Captures eddy momentum fluxes and mean state gradients

**Alternative Domains** (for sensitivity analysis):
- 10° × 10°: More local, emphasizes cyclone core
- 20° × 20°: More regional, includes larger-scale environment

---

## Directory Structure

```
data/ck_analysis/
├── tracks/                        # Prepared track files
│   ├── track_19790001.txt
│   ├── track_19790006.txt
│   └── ...
└── era5/                          # ERA5 data (downloaded by toolkit)
    └── {track_id}/
        └── ...

results/ck_analysis/
├── lec_results/                   # LorenzCycleToolkit output
│   └── {track_id}_ERA5_track/
│       ├── periods.csv
│       ├── results.csv
│       ├── Ck_level.csv
│       ├── Ck_uv_level.csv
│       ├── Ck_uw_level.csv
│       └── Ck_vw_level.csv
├── subterms_by_cyclone.csv       # Individual cyclone data
├── subterms_statistics.csv       # Ensemble statistics
├── vertical_profiles.csv         # Mean vertical profiles
├── lifecycle_statistics.csv      # Phase-composite statistics
└── final_report.txt              # Summary of findings

figures/ck_analysis/
├── vertical_profiles.png         # Mean profiles by subterm
├── lifecycle_evolution.png       # Time evolution composites
├── phase_composites.png          # Boxplots by phase
├── validation_plots.png          # Comparison with Zenodo data
└── statistical_summary.png       # Scatter plots and correlations
```

---

## References

### Lorenz Energy Cycle

- **Lorenz, E. N.** (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.

- **Brennan, F. E., & Vincent, D. G.** (1980). Zonal and eddy components of the synoptic-scale energy budget during intensification of Hurricane Carmen (1974). *Monthly Weather Review*, 108(7), 954-965.

### Barotropic Conversion

- **Orlanski, I., & Sheldon, J. P.** (1995). Stages in the energetics of baroclinic systems. *Tellus A*, 47(5), 605-628.

- **Dias Pinto, J. R., & da Rocha, R. P.** (2011). The energy cycle and structural evolution of cyclones over southeastern South America in three case studies. *Journal of Geophysical Research*, 116, D14104.

### South Atlantic Cyclones

- **Gan, M. A., & Rao, V. B.** (1991). Surface cyclogenesis over South America. *Monthly Weather Review*, 119(5), 1293-1302.

- **Reboita, M. S., et al.** (2010). Climatology of cyclones over the South Atlantic. *International Journal of Climatology*, 30(11), 1781-1798.

---

## Future Work

### Sensitivity Analyses

1. **Domain Size Sensitivity**:
   - Repeat analysis with 10°×10° and 20°×20° domains
   - Assess impact on subterm contributions

2. **Vertical Resolution**:
   - Use all available pressure levels vs. subset
   - Impact on vertical derivative calculations

3. **Temporal Resolution**:
   - Effect of 3-hourly vs. 6-hourly data
   - Sub-daily variability in subterm contributions

### Extended Analyses

1. **Comparison with Other Energy Patterns**:
   - EP2, EP3, EP4 cyclones
   - Identify unique features of EP1 barotropic conversion

2. **Seasonal Variability**:
   - Winter (JJA) vs. summer (DJF) differences
   - Connection to ENSO phases

3. **Trajectory Analysis**:
   - Subterm evolution along cyclone track
   - Spatial patterns of energy conversion

4. **Ageostrophic Effects**:
   - Role of ageostrophic circulation in Ck subterms
   - Connection to frontal dynamics


---

## Section: scripts/preprocess_data

> Source: `scripts/preprocess_data/README.md`

# Preprocess Data

Scripts for downloading input datasets from Zenodo and preprocessing them into formats optimised for analysis scripts.

---

## Scripts

### `download_lec_from_zenodo.py`

Downloads the complete Lorenz Energy Cycle (LEC) results dataset from Zenodo and extracts it locally.

- **Source DOI**: [10.5281/zenodo.18243447](https://doi.org/10.5281/zenodo.18243447)
- **Contents**: Complete LEC results with vertical resolution (~1,500 cyclones, 2020, 32 pressure levels, 3-hourly)1979
- **Output**: `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` (one subdirectory per cyclone)
- **Notes**: Checks for existing data and skips re-downloading. Archive is ~2 GB; extraction creates ~6,700 subdirectories.1

### `extract_tracks_from_zenodo.py`

Downloads the integrated cyclone tracks and energetics CSV from Zenodo and writes a smaller, processed version for fast local reads.

- **Source DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)
- **Output**: `data/tracks_SAt_filtered_with_energetics_processed.csv`
- **Notes**: Subsets to the columns used by plotting scripts to reduce file size.

### `preprocess_data.py`

Loads all cyclone energy data and serialises it to a Parquet cache for 1000 faster access by analysis scripts.

- **Input**: Remote GitHub CSV (accessed via `scripts/utils/load_data.py`)
- **Output**: `data/energy_cache.parquet` (~100 MB)50
- **Notes**: Supports parallel loading (`N_WORKERS` configurable in the script header). Run once; re-run only when the upstream data changes.

### `run_all.py`

Runs all three scripts above in alphabetical order. Prints progress and reports failures.

---

## Run Order

```bash
# Run everything at once (recommended)
python scripts/preprocess_data/run_all.py

# Or run individually in this order:
python scripts/preprocess_data/download_lec_from_zenodo.py
python scripts/preprocess_data/extract_tracks_from_zenodo.py
python scripts/preprocess_data/preprocess_data.py
```

---

## Outputs Summary

| File | Produced by | Used by |
|------|-------------|---------|
| `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` | `download_lec_from_zenodo.py` | `ck_subterms_analysis/` |
| `data/tracks_SAt_filtered_with_energetics_processed.csv` | `extract_tracks_from_zenodo.py` | `scripts/main/`, `cluster_analysis_energy_patterns/` |
| `data/energy_cache.parquet` | `preprocess_data.py` | `scripts/main/`, `cluster_analysis_energy_patterns/`, `scripts/exploratory/` |


---

