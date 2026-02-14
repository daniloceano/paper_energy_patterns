# EP1 Full Cyclones Analysis

Complete analysis of **ALL** Energy Pattern 1 (EP1) cyclones during their entire intensification phase.

## 📚 Key Documentation

- **[README.md](README.md)** (this file) - Pipeline overview and usage
- **[STATUS.md](STATUS.md)** - Implementation status and features
- **[VERTICAL_LEVELS.md](VERTICAL_LEVELS.md)** - ⭐ Detailed rationale for pressure level selection
- **[SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md)** - Physical methodology and interpretation template

## Differences from `ep1_ibc_ibt_analysis`

| Aspect | `ep1_ibc_ibt_analysis` | `ep1_full_analysis` (this) |
|---------|------------------------|----------------------------|
| **Cyclones** | Selected subset (94 cases) | ALL EP1 cyclones |
| **Spatial criterion** | Intensification center in 60°W-45°W, 45°S-30°S | All EP1 cyclones |
| **Times analyzed** | Central time of intensification | ALL intensification times |
| **Data** | `data/era5_ep1/` | `data/era5_ep1_full/` |
| **Results** | `results/ep1_vertical/` | `results/ep1_full/` |
| **Figures** | `figures/ep1_vertical/` | `figures/ep1_full/` |

## Estrutura do Pipeline

### Step 1: Select All EP1 Cyclones
```bash
python scripts/ep1_full_analysis/step1_select_all_ep1.py
```
- Selects ALL EP1 cyclones
- No spatial restriction (different from previous analysis)
- Saves list to `results/ep1_full/all_ep1_cases.csv`

### Step 2: Download ERA5 Data (Parallel)
```bash
# Default: 2 parallel jobs (CDS API recommended limit)
python scripts/ep1_full_analysis/step2_download_era5_parallel.py

# Custom parallelization (not recommended > 4 due to CDS API limits)
python scripts/ep1_full_analysis/step2_download_era5_parallel.py --jobs 2

# With nohup for background execution
nohup python scripts/ep1_full_analysis/step2_download_era5_parallel.py &> download.log &
# Log file automatically created in logs/step2_download_YYYYMMDD_HHMMSS.log
```
- Downloads ERA5 for all EP1 cyclones
- **Includes Sea Level Pressure (SLP)**
- **Parallel download** (default: 2 jobs, respecting CDS API limits)
- **Logging**: Progress tracking with timestamps, estimated time remaining
- **Automatic retry**: Validates existing files, re-downloads corrupted data
- Saves to `data/era5_ep1_full/`

**CDS API Constraints:**
- Maximum 2-4 simultaneous requests per user account
- Default `--jobs 2` respects this limit
- Higher values may cause "Number queued requests... temporarily limited" errors

### Step 3: Precompute Composites
```bash
python scripts/ep1_full_analysis/step3_precompute_composites.py
```
- **PRECOMPUTES** composites of all downloaded variables
- Avoids reprocessing in future analyses
- Saves spatial means by domain to `data/era5_ep1_full/composites.nc`

### Step 4: Compute Instabilities (All Times)
```bash
python scripts/ep1_full_analysis/step4_compute_instabilities_all_times.py
```
- Computes diagnostics for **ALL intensification times**
- Rayleigh-Kuo criterion, Eady Growth Rate
- Saves temporal results to `results/ep1_full/instabilities/`

### Step 5: Create Figures
```bash
python scripts/ep1_full_analysis/step5_create_figures.py
```
- Generates composite and time series figures
- **Modified visualizations:**
  - PV composites: Shaded PV(975 hPa) + green contours PV(250 hPa) + gray wind vectors at 250 hPa
  - EGR composites: Shaded EGR + black SLP contours + black wind vectors at 975 hPa
- Saves to `figures/ep1_full/`

### Step 6: Generate Scientific Documentation
```bash
python scripts/ep1_full_analysis/update_scientific_notes.py
```
- **Auto-generates** scientific report with analysis results
- Reads computed statistics from steps 4-5
- Populates template with:
  - EGR and Rayleigh-Kuo statistics
  - Physical interpretations
  - Dataset characteristics
- Output: `SCIENTIFIC_NOTES_POPULATED.md`

### Run All
```bash
python scripts/ep1_full_analysis/run_all.py
```
- Executes entire pipeline automatically (steps 1-5)
- Run step 6 separately after analysis completes

## Downloaded Variables

- **u, v**: Zonal and meridional wind components
- **t**: Temperature
- **z**: Geopotential
- **q**: Specific humidity
- **msl**: Mean Sea Level Pressure

## Pressure Levels

**Targeted levels based on Ca/Ck vertical analysis** (from `ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py`):\n\n| Level Range | Purpose | Diagnostic |
|-------------|---------|------------|
| **1000, 975, 950 hPa** | EGR at 975 hPa | Maximum Ca (baroclinic) |
| **400, 350, 300 hPa** | Diagnostics at 350 hPa | Minimum Ck (barotropic) |
| **250 hPa** | Upper-level jet | Plot overlays |

**Total: 7 pressure levels + SLP**

> 📖 **See [VERTICAL_LEVELS.md](VERTICAL_LEVELS.md) for detailed rationale and comparison with full tropospheric coverage**

### Rationale

Preliminary analysis of EP1 cyclones identified:
- **Maximum baroclinic conversion (Ca)**: 975 hPa
- **Minimum barotropic conversion (Ck)**: 350 hPa

For calculating diagnostics at these levels, we need adjacent levels for vertical derivatives. The 250 hPa level is included for visualization of upper-level jet interactions.

**Efficiency: ~50% reduction in data volume** compared to downloading all 14 standard levels.

## Analysis Domains

- **Local**: 5° × 5° centered on cyclone
- **Mesoscale**: 15° × 15°
- **Synoptic**: 30° × 30°

## Resource Usage

### Parallel Download
- Default: `n_jobs = multiprocessing.cpu_count() - 1`
- Customizable via `--jobs N` argument
- Ideal for multi-core servers

### Estimated Storage
- **~50-80 GB** for all EP1 cyclones (7 targeted pressure levels + SLP)
- Precomputed composites: ~3-5 GB
- **Total: ~100-150 GB** (significantly reduced via targeted level selection)

### Efficiency Note
By using only necessary pressure levels identified in preliminary Ca/Ck analysis, we reduce data volume by ~50% compared to downloading all 14 standard levels, while preserving all diagnostic capabilities.

## Authors

Danilo Couto de Souza  
February 2026
