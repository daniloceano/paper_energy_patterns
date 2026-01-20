# Analysis Scripts

This directory contains analysis scripts for the paper on energetic patterns of cyclones.

## Script Structure

All analysis scripts follow a common pattern:
- **Configuration section at the top**: Edit variables here instead of using command-line arguments
- **Easy promotion to main analysis**: Change output directories from `results/` to `results/main/`
- **Parallel processing support**: Enable for cluster/large-scale runs
- **Sample size control**: Test locally with small samples, run full dataset on cluster

## Available Scripts

### `download_lec_from_zenodo.py`

Downloads the complete LEC (Lorenz Energy Cycle) results dataset from Zenodo.

**Data Source:** Zenodo (DOI: 10.5281/zenodo.18243447)
- Complete Lorenz Energy Cycle results with vertical resolution
- ~1,500 cyclones from 1979-2020
- 32 pressure levels from 1000 hPa to 100 hPa
- 3-hourly temporal resolution

**Output location:** `data/temp_lec_zenodo/LEC_Results_energetic-patterns/`

**Usage:**
```bash
python scripts/analysis/download_lec_from_zenodo.py
```

**Notes:**
- The script checks if data is already downloaded and skips re-downloading
- Download size: ~1-2 GB (archive file)
- Extraction creates ~6,700 directories (one per cyclone)
- This is a prerequisite for scripts in `ep1_ibc_ibt_analysis/`

### `extract_tracks_from_zenodo.py`

Extracts tracks and energetics from the remote Zenodo CSV and creates a smaller,
processed CSV for fast local reads used by plotting scripts.

**Output:** `data/tracks_SAt_filtered_with_energetics_processed.csv`

**Usage:**
```bash
python scripts/analysis/extract_tracks_from_zenodo.py
```

### `exploratory_kde_pairplot.py`

Creates a pairwise KDE contour plot matrix for selected energy terms across life-cycle phases.

**Configuration variables:**
```python
SAMPLE_SIZE = 800          # Number of cyclones (0 = all)
USE_PARALLEL = False       # Enable parallel processing
N_WORKERS = 4              # Parallel workers (if USE_PARALLEL=True)
RESULTS_DIR = "results"    # Output directory for CSVs
FIGURES_DIR = "figures"    # Output directory for figures
DPI = 200                  # Figure DPI (300+ for publication)
SAVE_FIGURE = True         # Set False to skip saving
```

**Usage:**

1. **Local testing** (small sample):
   ```python
   # In exploratory_kde_pairplot.py, set:
   SAMPLE_SIZE = 50
   USE_PARALLEL = False
   ```
   Then run: `python scripts/analysis/exploratory_kde_pairplot.py`

2. **Full run** (all data):
   ```python
   # In exploratory_kde_pairplot.py, set:
   SAMPLE_SIZE = 0  # 0 means all available cyclones
   USE_PARALLEL = False
   ```
   Then run: `python scripts/analysis/exploratory_kde_pairplot.py`

3. **Cluster run** (parallel, full dataset):
   ```python
   # In exploratory_kde_pairplot.py, set:
   SAMPLE_SIZE = 0
   USE_PARALLEL = True
   N_WORKERS = 8  # Adjust based on cluster resources
   ```
   Then run: `python scripts/analysis/exploratory_kde_pairplot.py`

4. **Promote to main analysis**:
   ```python
   # In exploratory_kde_pairplot.py, change:
   RESULTS_DIR = "results/main"
   FIGURES_DIR = "figures/main"
   DPI = 300  # Higher quality for publication
   ```

**Output:**
- `results/energy_sample.csv` - Energy data sample used
- `figures/exploratory_kde_pairplot.png` - Pairwise KDE plot

## Best Practices

1. **Always test locally first** with `SAMPLE_SIZE = 50` or similar
2. **Check output** before running full dataset
3. **Use parallel processing** on cluster for large datasets
4. **Increase DPI** (300-600) when generating final publication figures
5. **Keep exploratory results separate** from main results (use different directories)
6. **Document configuration** in git commits when promoting analyses to main

## Phase Colors

The project uses consistent colors across all analyses:
- **Incipient**: Blue (`#1f77b4`)
- **Intensification**: Yellow/Gold (`#ffbf00`)
- **Mature**: Red (`#d62728`)
- **Decay**: Green (`#2ca02c`)

These follow Scientific Reports styling guidelines for clarity and accessibility.
