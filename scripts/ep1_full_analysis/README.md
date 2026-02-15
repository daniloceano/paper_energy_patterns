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

### Step 3: Precompute Composites and Diagnostics
```bash
python scripts/ep1_full_analysis/step3_precompute_composites.py
```
- **PRECOMPUTES** composites of all downloaded variables AND diagnostic fields
- Computes instability diagnostics:
  - **EGR** (Eady Growth Rate) at Ca level (975 hPa)
  - **∂η/∂y** (Rayleigh-Kuo gradient) at Ck level (350 hPa), both 2D and zonal mean
  - **PV** (Potential Vorticity) at both Ca (975 hPa) and Ck (350 hPa) levels
- Avoids reprocessing in future analyses
- Saves spatial composites by domain to `data/era5_ep1_full/precomputed_composites.nc`

### Step 4: Compute Instabilities Time Series (Optional)
```bash
python scripts/ep1_full_analysis/step4_compute_instabilities_all_times.py
```
- **OPTIONAL:** Computes diagnostics for **ALL intensification times** of each individual cyclone
- Useful for analyzing temporal evolution patterns
- Not required for composite figures (step5) since diagnostics are already in step3
- Saves temporal results to `results/ep1_full/instabilities/`

### Step 5: Create Figures
```bash
python scripts/ep1_full_analysis/step5_create_figures.py
```
- Generates 4-panel composite figures for each domain
- **Panel layout:**
  - **(a)** 2D map of ∂η/∂y (RK criterion) at Ck level (350 hPa)
  - **(b)** Zonal mean profile of ∂η/∂y
  - **(c)** PV at Ca level (975 hPa, shaded) + PV at Ck level (350 hPa, contours) + 250 hPa wind vectors
  - **(d)** EGR at Ca level (975 hPa, shaded) + SLP contours + wind vectors at Ca level
- Uses precomputed data from step3 for efficiency
- Saves to `figures/ep1_full/composite/`

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
- Executes pipeline automatically (steps 1-3, 5)
- **Step 4 is optional** (time series analysis) - run separately if needed
- Generates composite figures ready for publication

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
