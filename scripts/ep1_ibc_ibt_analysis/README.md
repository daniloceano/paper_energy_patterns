# EP1 Cyclones Analysis

Complete analysis of **ALL** Energy Pattern 1 (EP1) cyclones during their entire intensification phase.

## 📚 Key Documentation

- **[README.md](README.md)** (this file) - Pipeline overview and usage
- **[STATUS.md](STATUS.md)** - Implementation status and features
- **[VERTICAL_LEVELS.md](VERTICAL_LEVELS.md)** - ⭐ Detailed rationale for pressure level selection
- **[SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md)** - Physical methodology and interpretation template

## Differences from Previous `ep1_ibc_ibt_analysis` (archived)

This pipeline **REPLACES** the older `ep1_ibc_ibt_analysis` (now `ep1_ibc_ibt_analysis_OLD_20260216`).

| Aspect | Old Analysis | New Analysis (this) |
|---------|------------------------|----------------------------|
| **Cyclones** | Selected subset (94 cases) | ALL EP1 cyclones |
| **Spatial criterion** | Intensification center in 60°W-45°W, 45°S-30°S | All EP1 cyclones |
| **Times analyzed** | Central time of intensification | ALL intensification times |
| **Pressure levels** | 7 levels | 8 levels + omega |
| **Upper-level analysis** | 250 hPa jet | **200 hPa dynamic tropopause** |
| **Data** | `data/era5_ep1_OLD/` | `data/era5_ep1/` |
| **Results** | `results/ep1_vertical_OLD/` | `results/ep1_vertical/` |
| **Figures** | `figures/ep1_vertical_OLD/` | `figures/ep1_vertical/` |

## Estrutura do Pipeline

### Step 1: Select All EP1 Cyclones
```bash
python scripts/ep1_ibc_ibt_analysis/step1_select_all_ep1.py
```
- Selects ALL EP1 cyclones
- No spatial restriction (different from previous analysis)
- Saves list to `results/ep1_vertical/all_ep1_cases.csv`

### Step 2: Download ERA5 Data (Parallel)
```bash
# Default: 2 parallel jobs (CDS API recommended limit)
python scripts/ep1_ibc_ibt_analysis/step2_download_era5_parallel.py

# Custom parallelization (not recommended > 4 due to CDS API limits)
python scripts/ep1_ibc_ibt_analysis/step2_download_era5_parallel.py --jobs 2

# With nohup for background execution
nohup python scripts/ep1_ibc_ibt_analysis/step2_download_era5_parallel.py &> download.log &
# Log file automatically created in logs/step2_download_YYYYMMDD_HHMMSS.log
```
- Downloads ERA5 for all EP1 cyclones
- **Includes Sea Level Pressure (SLP)**
- **8 pressure levels + omega**: 1000, 975, 950, 400, 350, 300, 250, 200 hPa
- **Omega (ω)** at all levels for vertical motion and PV calculation
- **Parallel download** (default: 2 jobs, respecting CDS API limits)
- **Logging**: Progress tracking with timestamps, estimated time remaining
- **Automatic retry**: Validates existing files, re-downloads corrupted data
- Saves to `data/era5_ep1/`

**CDS API Constraints:**
- Maximum 2-4 simultaneous requests per user account
- Default `--jobs 2` respects this limit
- Higher values may cause "Number queued requests... temporarily limited" errors

### Step 3: Precompute Composites and Diagnostics
```bash
# Default: uses min(3, cpu_count) parallel jobs
python scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py

# Custom parallelization
python scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py --jobs 4

# With nohup for background execution
nohup python scripts/ep1_ibc_ibt_analysis/step3_precompute_composites.py --jobs 4 &
# Log file automatically created in logs/step3_precompute_YYYYMMDD_HHMMSS.log
```
- **PRECOMPUTES** composites of all downloaded variables AND diagnostic fields
- **Parallel processing**: Domain-level parallelization with progress tracking (tqdm)
- **Logging**: Timestamped logs for monitoring long-running computations
- **Separate files per domain**: Creates `precomputed_composites_{domain}.nc` for efficient transfer
- Computes instability diagnostics:
  - **EGR** (Eady Growth Rate) at Ca level (975 hPa)
  - **∂η/∂y** (Rayleigh-Kuo gradient) at Ck level (350 hPa), both 2D and zonal mean
  - **PV** (Potential Vorticity) at both Ca (975 hPa) and Ck (350 hPa) levels
  - **PV at 200 hPa** (dynamic tropopause, 2 PVU surface) using omega
- Avoids reprocessing in future analyses
- Saves to `data/era5_ep1/precomputed_composites_{local,mesoscale,synoptic}.nc`

### Step 4: Create Figures
```bash
python scripts/ep1_ibc_ibt_analysis/step4_create_figures.py
# Log file automatically created in logs/step4_figures_YYYYMMDD_HHMMSS.log
```
- Generates 4-panel composite figures for each domain
- **Logging**: Timestamped logs with file sizes and generation status including PV ranges
- **Panel layout:**
  - **(a)** 2D map of ∂η/∂y (RK criterion) at Ck level (350 hPa)
  - **(b)** Zonal mean profile of ∂η/∂y
  - **(c)** PV at Ca level (975 hPa, shaded) + PV at Ck level (350 hPa, contours) + **200 hPa wind vectors** (dynamic tropopause)
  - **(d)** EGR at Ca level (975 hPa, shaded) + SLP contours + wind vectors at Ca level
- Uses precomputed data from step3 for efficiency
- Reads separate files per domain: `precomputed_composites_{domain}.nc`
- Saves to `figures/ep1_vertical/composite/`

### Step 5: Generate Scientific Documentation
```bash
python scripts/ep1_ibc_ibt_analysis/update_scientific_notes.py
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
python scripts/ep1_vertical_analysis/run_all.py
```
- Executes pipeline automatically (steps 1-4)
- Generates composite figures ready for publication

## 🚀 Remote Server Execution

**For compute-intensive steps (2 and 3), remote execution is recommended:**

### Quick Start

1. **On remote server:**
```bash
# Activate environment
cd ~/paper_energy_patterns
conda activate paper_energy

# Step 2: Download ERA5 (parallel, ~6-12 hours)
nohup python scripts/ep1_vertical_analysis/step2_download_era5_parallel.py --jobs 2 &

# Step 3: Precompute diagnostics (parallel, ~3-6 hours)
nohup python scripts/ep1_vertical_analysis/step3_precompute_composites.py --jobs 4 &

# Monitor progress
tail -f logs/step2_download_*.log
tail -f logs/step3_precompute_*.log
```

2. **Transfer only processed data (~5-10 GB):**
```bash
# On local machine
rsync -avz --progress user@server:/path/to/data/era5_ep1/precomputed_composites.nc \
  data/era5_ep1/

# Transfer results if needed
rsync -avz --progress user@server:/path/to/results/ep1_vertical/ results/ep1_vertical/
```

3. **Generate figures locally:**
```bash
python scripts/ep1_vertical_analysis/step5_create_figures.py
```

### Why This Workflow?

| Item | Remote (50-80 GB) | Transfer (5-10 GB) | Local |
|------|-------------------|---------------------|-------|
| **ERA5 raw files** | ✓ Download | ❌ Skip | ❌ |
| **precomputed_composites.nc** | ✓ Compute | ✓ Transfer | ✓ Figures |
| **Time saved** | 6-18 hours compute | ~30 min transfer | ~5 min figures |

**Storage optimization:** Transfer only 10-15% of total data volume while maintaining full analysis capability.

### Detailed Guide

**See [REMOTE_EXECUTION_GUIDE.md](REMOTE_EXECUTION_GUIDE.md)** for:
- Complete nohup command examples with SSH key authentication
- File transfer with SCP (`transfer_guide_scp.sh`)
- SSH connection management for master.iag.usp.br
- Two-window password authentication workflow
- Troubleshooting common issues
- Log file monitoring strategies

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
- **ERA5 raw files**: ~50-80 GB (7 targeted pressure levels + SLP)
- **Precomputed composites**: ~100-300 MB total (3 separate domain files)
- **Figures**: ~5-15 MB
- **Total**: ~50-85 GB (significantly reduced via targeted level selection)

### Efficiency Note
By using only necessary pressure levels identified in preliminary Ca/Ck analysis, we reduce data volume by ~50% compared to downloading all 14 standard levels, while preserving all diagnostic capabilities.

## Authors

Danilo Couto de Souza  
February 2026
