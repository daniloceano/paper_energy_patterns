# Paper: Energetic Patterns of Cyclones in the Southwestern Atlantic

Repository to organize scripts and results for the paper based on Chapter 6 of the PhD thesis.

## 🚀 Quick Start

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
# This caches all energy data locally for fast access
# Recommended to run on server with many cores (adjust N_WORKERS in script)
python scripts/utils/preprocess_data.py
```

Expected output: `data/energy_cache.parquet` (~50-100 MB, loads in <1 second)

### 3. Run Analyses
```bash
# Example: KDE pairplot analysis
python scripts/exploratory/kde_pairplot.py
```

## 📁 Structure

```
.
├── data/                       # Cached/processed data
│   ├── energy_cache.parquet   # Preprocessed energy data (generated)
│   └── README.md              # Data documentation
├── scripts/                    # Analysis scripts
│   ├── utils/                 # Utility functions
│   │   ├── load_data.py       # Data loading from GitHub
│   │   └── preprocess_data.py # Data preprocessing & caching
│   ├── setup_and_examples/    # Setup verification and examples
│   ├── exploratory/           # Exploratory analyses
│   │   └── kde_pairplot.py    # KDE pairwise plot
│   └── main/                  # Main paper analyses (promoted from exploratory)
├── figures/                    # Generated figures
│   ├── exploratory/           # Exploratory figures
│   └── main/                  # Main paper figures
├── results/                    # Analysis results (CSVs, etc.)
│   ├── exploratory/           # Exploratory results
│   └── main/                  # Main paper results
└── README.md
```

See `scripts/README.md` for detailed information about script organization and usage.

## 📊 Data Sources

### Energetic Patterns (Main Analysis)

Data is accessed directly from GitHub (no manual download needed):

- **Cyclone tracks**: [tracks_SAt_filtered_with_periods.csv](https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/refs/heads/master/tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv)
- **Energy by phase**: [csv_database_energy_by_periods/](https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/master/csv_database_energy_by_periods/)
  - Format: `{track_id}_averages.csv`
  - Coverage: ~6,700 cyclones (100% coverage)

**Note**: Raw data loading is slow (~0.15s per cyclone). Use `preprocess_data.py` to create a local cache for 1000x faster access.

### ERA5 Data (EP1 Instability Analysis)

For EP1 cyclone instability diagnostics, ERA5 reanalysis data is downloaded from Copernicus CDS:

- **Pressure levels**: 250, 300, 350, 400, 950, 975, 1000 hPa
  - 250 hPa: Jet stream analysis (wind barbs)
  - 975 hPa: Maximum available conversion (Ca)
  - 350 hPa: Minimum baroclinic conversion (Ck)
- **Variables**: u, v, t, z, q (winds, temperature, geopotential, specific humidity)
- **Domains**: Local (5°×5°), Mesoscale (15°×15°), Synoptic (30°×30°)
- **Storage**: `data/era5_ep1/{track_id}_era5.nc` + `{track_id}_metadata.csv`

See `data/ERA5_STRUCTURE.md` for detailed information on the ERA5 data structure and variables.

## ⚙️ Configuration

All analysis scripts use header configuration (no command-line arguments needed):

```python
# Example: scripts/exploratory/kde_pairplot.py
SAMPLE_SIZE = 100    # Number of cyclones (0 = all)
USE_PARALLEL = True  # Enable parallel processing
N_WORKERS = 50       # Adjust for your system
DPI = 300           # Figure quality
```

## 🖥️ Running on Server

For best performance with ~6,700 cyclones:

1. **Preprocessing** (run once):
   ```bash
   # Edit scripts/utils/preprocess_data.py:
   N_WORKERS = 50  # Use all 50 cores
   
   # Run (takes ~15 minutes with 50 cores)
   python scripts/utils/preprocess_data.py
   ```

2. **Analysis** (uses cached data):
   ```bash
   # Edit your analysis script:
   USE_PARALLEL = True
   N_WORKERS = 50
   
   # Run analysis (much faster with cache)
   python scripts/exploratory/your_analysis.py
   ```

## � EP1 Instability Analysis Pipeline

For EP1 cyclone type instability diagnostics:

### 1. Download ERA5 Data
```bash
python scripts/ep1_ibc_ibt_analysis/step3_download_era5.py
```

**Features**:
- Downloads ERA5 data at 7 pressure levels for all EP1 cases
- **Automatic validation**: Checks existing files before downloading
  - Verifies all required variables present
  - Checks all pressure levels available
  - Detects corrupted files (>50% NaN values)
  - Validates temporal dimension consistency
- **Smart skip**: Only downloads missing or invalid files
- Includes 250 hPa for jet stream analysis

### 2. Calculate Instabilities
```bash
python scripts/ep1_ibc_ibt_analysis/step4_calculate_instabilities.py
python scripts/ep1_ibc_ibt_analysis/step4.1_consolidate_instability_results.py
```

**Output**: `results/ep1_vertical/instabilities/summary_statistics.txt`
- Available potential energy (APE) per area
- Eddy growth rate (EGR) diagnostics  
- Richardson number (RK) criterion satisfaction by domain:
  ```
  RK criterion (2D field) satisfied for:
    local       ( 5°): 45/94 cases (47.9%)
    mesoscale   (15°): 68/94 cases (72.3%)
    synoptic    (30°): 82/94 cases (87.2%)
  ```

### 3. Generate Composites
```bash
python scripts/ep1_ibc_ibt_analysis/step5_create_figures.py
```

**Output**: `figures/ep1_vertical/composites/`
- Three-panel composite figures for each case
- Panel (a): Virtual temperature (Ck: 350 hPa)
- Panel (b): Virtual temperature (Ca: 975 hPa)
- Panel (c): Baroclinic PV (975 hPa) + **Jet stream wind barbs (250 hPa)**

### 4. Documentation
```bash
python scripts/ep1_ibc_ibt_analysis/generate_pdf_documentation.py
```

**Output**: `docs/Chapter_EP1_Instability_Diagnostics_Scientific_Notes.pdf`
- Converts `SCIENTIFIC_NOTES_STEP4.md` to professional PDF
- Includes table of contents, numbered sections, references
- Covers: EGR derivation, RK criterion, physical constants, quality controls

## 📈 Performance Tips

- **Always preprocess first**: Speeds up subsequent analyses by 1000x
- **Use parallel processing**: Set `N_WORKERS` to match available cores
- **Test locally**: Use small `SAMPLE_SIZE` (10-50) for quick testing
- **Full run on server**: Set `SAMPLE_SIZE = 0` and `N_WORKERS = 50`
- **ERA5 downloads**: step3 automatically validates and skips existing valid files

## Setup

### First Time Setup
```bash
# Run the setup script
bash setup_environment.sh
```

The script will automatically:
- Check if `paper_energy_patterns` conda environment exists
- Create it if needed (with Python 3.13)
- Install all required packages from requirements.txt
- Verify all packages are present
- Activate the environment

### Daily Use
```bash
# Quick activation
source activate.sh

# Or manually
conda activate paper_energy_patterns

# Deactivate when done
conda deactivate
```

### Verify Installation
```bash
python scripts/verify_environment.py
```