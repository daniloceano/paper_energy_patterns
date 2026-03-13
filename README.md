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
