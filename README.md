# Energetic Patterns of Cyclones in the Southwestern Atlantic

This repository organises all scripts, data, and results for the paper on energetic patterns of South Atlantic extratropical cyclones, based on Chapter 6 of the PhD thesis. Cyclones are classified into three Energy Patterns (EP1, EP2, EP3) via PCA-based K-Means clustering of Lorenz Energy Cycle diagnostics during the intensification phase. The **current scientific focus** is `scripts/ep_structure_analysis/`, which performs composite analysis of ERA5 reanalysis fields to characterise the atmospheric structure of EP1 (N=444) and EP2 (N=979) cyclones during intensification.

---

## Quick Start

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

### 2. Preprocess Data (Optional, Run Once)

**For most analyses**: Skip this step - scripts load data directly from GitHub

**Required only for**:
- Clustering pipeline → Run `python scripts/preprocess_data/preprocess_data.py` (creates energy_cache.parquet)
- Vertical analysis (S3) → Run `python scripts/preprocess_data/download_lec_from_zenodo.py`

```bash
# Quick: Just what's needed for clustering
python scripts/preprocess_data/preprocess_data.py  # ~5 min, 6 MB

# Full: Everything (if doing vertical/exploratory analyses)
python scripts/preprocess_data/run_all.py  # ~15 min, ~1.3 GB
```

Expected outputs: 
- `data/energy_cache.parquet` (required for clustering)
- `data/tracks_SAt_filtered_with_energetics_processed.csv` (optional)
- `data/temp_lec_zenodo/` (optional, for S3 figure)

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

## Repository Structure

```
.
├── data/                                   # Input and processed data
│   ├── energy_cache.parquet               # Preprocessed energy data (generated)
│   ├── era5_ep_structure/                 # ERA5 composites for ep_structure_analysis
│   │   ├── precomputed_composites_ep1.nc
│   │   └── precomputed_composites_ep2.nc
│   └── README.md
├── docs/                                   # Generated documentation PDFs
│   ├── scientific_notes_cluster_analysis.pdf
│   ├── scientific_notes_ep_structure.pdf
│   └── user_guide_repository_readmes.pdf  # Auto-generated (see below)
├── figures/                                # Generated figures
│   ├── exploratory/                       # Exploratory figures
│   └── main/                             # Final publication figures
├── results/                                # Analysis results
│   └── cluster/                          # Cluster assignments and models
├── scripts/                                # All analysis scripts
│   ├── cluster_analysis_energy_patterns/ # PCA + K-Means clustering pipeline
│   ├── ck_subterms_analysis/             # Barotropic conversion (Ck) decomposition
│   ├── documentation/                    # Compile READMEs into a PDF user guide
│   ├── ep_structure_analysis/            # CURRENT FOCUS: ERA5 composite analysis
│   ├── exploratory/                      # Preliminary exploratory scripts
│   ├── main/                             # Final publication figure scripts
│   ├── preprocess_data/                  # Data download and preprocessing
│   ├── setup_and_examples/              # Environment verification and templates
│   ├── utils/                            # Shared utility functions
│   └── web/                             # Data extraction scripts for the web site
├── supabase/                               # Database migrations for Supabase
│   └── migrations/
├── web/                                    # Interactive Next.js web application
│   ├── src/app/                          # App Router pages
│   ├── src/components/                   # Reusable UI components
│   ├── src/content/                      # Generated JSON manifests
│   ├── src/lib/                          # Types, constants, utilities
│   └── README.md                         # Web setup & deploy instructions
├── activate.sh                             # Quick environment activation
├── requirements.txt
└── setup_environment.sh
```

See `scripts/README.md` for detailed information on each subdirectory.

---

## Data Sources

**Note**: Most scripts access data directly from GitHub without manual downloads. Preprocessing scripts cache data locally for faster repeated access.

### Primary Source: GitHub (Auto-loaded by Scripts)

**Cyclone Tracks**: `https://github.com/daniloceano/energetic_patterns_cyclones_south_atlantic`
- **Access**: `load_tracks()` from `scripts/utils/load_data.py`
- **Contents**: ~1,500 cyclones (1979-2020), track positions, lifecycle phases
- **Used By**: Main figures (01, 05, 06, S2)
- **No download needed**: Scripts fetch directly from GitHub

### Zenodo Archives (Preprocessing Only)

#### 1. Complete Tracks with Energetics
- **DOI**: [10.5281/zenodo.18133432](https://doi.org/10.5281/zenodo.18133432)
- **Description**: Integrated tracks + energy time series (1-hourly tracks, 3-hourly energy)
- **Access**: `scripts/preprocess_data/extract_tracks_from_zenodo.py`
- **Output**: `data/tracks_SAt_filtered_with_energetics_processed.csv` (66 MB)
- **Used By**: Exploratory individual cyclone scripts

#### 2. LEC Results with Vertical Resolution
- **DOI**: [10.5281/zenodo.18243447](https://zenodo.org/records/18243447)
- **Description**: Complete LEC results with 32 vertical levels (1000-100 hPa, 3-hourly)
- **Access**: `scripts/preprocess_data/download_lec_from_zenodo.py`
- **Output**: `data/temp_lec_zenodo/` (1.2 GB)
- **Used By**: S3 figure (vertical structure), Ck subterms analysis

### Local Cache (Generated)

- **energy_cache.parquet** (6 MB): Phase-averaged energy data for clustering
  - Created by: `scripts/preprocess_data/preprocess_data.py`
  - Essential for clustering pipeline
  
- **era5_ep_structure/** (400+ MB): ERA5 composites for EP1/EP2
  - Created by: `scripts/ep_structure_analysis/` pipeline
  - Used by: Figure 07 (dynamical composites)

See `data/README.md` and `data/DATA_STRUCTURE.md` for complete documentation.

---

## Configuration

All scripts use header-level configuration. No command-line arguments are needed.

```python
# Example configuration (top of any script)
SAMPLE_SIZE = 0        # Number of cyclones (0 = all)
USE_PARALLEL = True    # Enable parallel processing
N_WORKERS = 8          # Workers (adjust for your system)
DPI = 300              # Figure output quality
```

---

## Analysis Pipelines

### 1. Energy Pattern Classification (`scripts/cluster_analysis_energy_patterns/`)

Normalises LEC energy variables, applies PCA by lifecycle phase, determines the optimal number of clusters via Gap Statistic, and classifies each cyclone into one of three Energy Patterns using K-Means. Key results: EP1 (11.6%, N=444, high conversions), EP2 (25.6%, N=979, moderate conversions), EP3 (62.7%, weak/background energetics).

### 2. Spatial Structure Analysis — *Current Focus* (`scripts/ep_structure_analysis/`)

Composite ERA5 analysis of EP1 and EP2 cyclones during intensification. Uses a storm-centred 30°×30° domain at 0.25° resolution to compute EGR (500–850 hPa), PV (200/850 hPa), temperature advection (850 hPa), moisture flux divergence (975 hPa), SLP, RK criterion (250 hPa), KE advection (250 hPa), and AFC (250 hPa), plus anomalies relative to the 1991–2020 WMO climatology. Data stored in `data/era5_ep_structure/`.

### 3. Barotropic Conversion Decomposition (`scripts/ck_subterms_analysis/`)

Decomposes the barotropic conversion term (Ck) into its three subterms for EP1 cyclones, which present the largest barotropic conversions in the dataset.

### 4. Final Paper Figures (`scripts/main/`)

Scripts numbered 01–07 (main figures) and S1–S3 (supplementary) generate publication-ready figures at 300 DPI according to Scientific Reports guidelines.

---

## Setup

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

## Interactive Web Explorer

An interactive Next.js site for visual exploration of the paper's results. See `web/README.md` for full details.

```bash
# Generate site data from results
python scripts/web/build_site_manifest.py
python scripts/web/extract_cluster_site_data.py
python scripts/web/extract_composite_site_data.py

# Run the web app
cd web && npm install && npm run dev
```

And then open http://localhost:3000. The site reads from existing results, figures, and data — it does not modify the scientific pipeline.

---

## Documentation

A consolidated user guide (`docs/user_guide_repository_readmes.pdf`) is auto-generated from all repository READMEs. To regenerate it:

```bash
python scripts/documentation/compile_docs.py
```

Requires `pandoc` and `pdflatex` on your system.
