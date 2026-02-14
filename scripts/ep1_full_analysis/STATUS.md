# EP1 Full Analysis - Implementation Status

**Date:** February 13, 2026  
**Goal:** Complete analysis of ALL EP1 cyclones with all intensification times

## ✅ Implemented

### Directory Structure
- ✅ `scripts/ep1_full_analysis/` - Analysis scripts
- ✅ `data/era5_ep1_full/` - Downloaded ERA5 data
- ✅ `results/ep1_full/` - Analysis results
- ✅ `figures/ep1_full/` - Generated figures

### Complete Scripts

#### ✅ Step 1: `step1_select_all_ep1.py`
**Status:** ✅ READY TO USE

**Functionality:**
- Selects ALL EP1 cyclones (cluster 0)
- No spatial filtering (different from `ep1_ibc_ibt_analysis`)
- Filters only by complete lifecycle: incipient → intensification → mature → decay
- Extracts intensification phase information

**Output:**
- `results/ep1_full/all_ep1_cases.csv`
- `figures/ep1_full/tracks/all_ep1_tracks_overview.png`

**Usage:**
```bash
python scripts/ep1_full_analysis/step1_select_all_ep1.py
```

---

#### ✅ Step 2: `step2_download_era5_parallel.py`
**Status:** ✅ READY TO USE

**Functionality:**
- Parallel ERA5 data download (customizable via `--jobs N`)
- **INCLUDES Mean Sea Level Pressure (SLP/MSLP)** ✨
- All standard pressure levels: 1000-250 hPa
- Validates existing files
- Automatic retry of failed downloads

**Downloaded variables:**
- **Pressure levels:** u, v, t, z, q
- **Single level:** msl (Mean Sea Level Pressure) ✨

**Pressure levels (targeted based on Ca/Ck analysis):**
```
1000, 975, 950 hPa  → EGR at 975 hPa (maximum Ca)
400, 350, 300 hPa   → Diagnostics at 350 hPa (minimum Ck)
250 hPa             → Upper-level jet overlays

Total: 7 levels (reduced from 14 for efficiency)
```

**Output:**
- `data/era5_ep1_full/{track_id}_era5.nc` (merged pressure + single-level)
- `data/era5_ep1_full/{track_id}_metadata.csv`

**Usage:**
```bash
# Default: 2 parallel jobs (CDS API safe limit)
python scripts/ep1_full_analysis/step2_download_era5_parallel.py

# Custom: specify number of jobs (max 2-4 recommended)
python scripts/ep1_full_analysis/step2_download_era5_parallel.py --jobs 2

# Background execution with nohup
nohup python scripts/ep1_full_analysis/step2_download_era5_parallel.py &
# Logs saved to: logs/step2_download_YYYYMMDD_HHMMSS.log
```

⚠️ **IMPORTANT:** CDS API limits: 2-4 simultaneous requests per user. Default `--jobs 2` respects this constraint.

---

#### ✅ Step 3: `step3_precompute_composites.py`
**Status:** ✅ READY TO USE

**Functionality:**
- Precomputes spatial composites (domain averages)
- **ALL downloaded variables** (including SLP)
- **ALL pressure levels**
- Avoids reprocessing in future analyses
- Domain-specific dimensions (avoids conflicts)

**Output:**
- `data/era5_ep1_full/precomputed_composites.nc` (~5-10 GB estimated)

**Domains:**
- Local: 5° × 5°
- Mesoscale: 15° × 15°
- Synoptic: 30° × 30°

**Usage:**
```bash
python scripts/ep1_full_analysis/step3_precompute_composites.py
```

---

#### ✅ `run_all.py`
**Status:** ✅ COMPLETE (all steps functional)

**Functionality:**
- Executes complete pipeline automatically
- Steps 1-5 fully implemented

**Usage:**
```bash
python scripts/ep1_full_analysis/run_all.py
```

---

#### ✅ `README.md`
Complete documentation explaining:
- Differences between `ep1_ibc_ibt_analysis` and `ep1_full_analysis`
- Pipeline structure
- Variables and pressure levels
- Resource usage (parallelization, storage)

---

## ✅ All Steps Implemented

### Step 4: `step4_compute_instabilities_all_times.py`
**Status:** ✅ COMPLETE

**Functionality:**
- Processes **ALL timesteps** of intensification (not just temporal center)
- Saves time series of:
  - Rayleigh-Kuo criterion
  - Eady Growth Rate
  - Baroclinic PV
- Output: `results/ep1_full/instabilities/{track_id}_timeseries.nc`

**Key implementation:**
```python
# Original (ep1_ibc_ibt_analysis):
t_idx = len(ds.valid_time) // 2  # Temporal center only
ds_t = ds.isel(valid_time=t_idx)

# New (ep1_full_analysis):
# Loop over ALL times
for t_idx in range(len(ds.valid_time)):
    ds_t = ds.isel(valid_time=t_idx)
    # Compute instabilities...
    # Save timeseries
```

**Usage:**
```bash
python scripts/ep1_full_analysis/step4_compute_instabilities_all_times.py
```

---

### Step 5: `step5_create_figures.py`
**Status:** ✅ COMPLETE

**Functionality:**
- Creates spatial composites with modified overlays:
  - **PV plots:** Shaded PV(975 hPa), green contours PV(250 hPa), gray wind vectors at 250 hPa
  - **EGR plots:** Shaded EGR, black SLP contours, black wind vectors at 975 hPa
- Time series statistics (mean ± std across all cases)
- Uses precomputed composites for efficiency

**Generated figures:**
- Spatial composites (all domains)
- Time series diagnostics throughout intensification
- Mean evolution plots

**Usage:**
```bash
python scripts/ep1_full_analysis/step5_create_figures.py
```

---

## 📊 Comparison: ep1_ibc_ibt_analysis vs ep1_full_analysis

| Aspect | `ep1_ibc_ibt_analysis` | `ep1_full_analysis` |
|---------|------------------------|---------------------|
| **Cyclones** | 94 selected | ALL EP1 |
| **Spatial filter** | 60°W-45°W, 45°S-30°S | None |
| **Times analyzed** | Intensification center | ALL times |
| **SLP** | ❌ No | ✅ Yes |
| **Parallel download** | ❌ No | ✅ Yes (customizable) |
| **Precomputed composites** | ⚠️ Partial (exploratory) | ✅ Yes (complete) |
| **Data** | `data/era5_ep1/` | `data/era5_ep1_full/` |
| **Results** | `results/ep1_vertical/` | `results/ep1_full/` |
| **Figures** | `figures/ep1_vertical/` | `figures/ep1_full/` |

---

## 🚀 How to Run

### Complete pipeline:

```bash
# Run all steps automatically
python scripts/ep1_full_analysis/run_all.py
```

### Individual steps:

```bash
# 1. Select all EP1 cyclones
python scripts/ep1_full_analysis/step1_select_all_ep1.py

# 2. Download ERA5 (parallel, e.g., 8 workers)
python scripts/ep1_full_analysis/step2_download_era5_parallel.py --jobs 8

# 3. Precompute composites
python scripts/ep1_full_analysis/step3_precompute_composites.py

# 4. Compute instabilities for all timesteps
python scripts/ep1_full_analysis/step4_compute_instabilities_all_times.py

# 5. Create figures
python scripts/ep1_full_analysis/step5_create_figures.py

# 6. Generate scientific documentation
python scripts/ep1_full_analysis/update_scientific_notes.py
```

---

## 💾 Storage Estimation

- **ERA5 files:** ~50-80 GB (all EP1, all times, 7 targeted levels + SLP)
- **Precomputed composites:** ~5-10 GB
- **Instability results (step4):** ~10-20 GB (time series)
- **Figures:** ~500 MB

**Total estimated:** ~100-150 GB (reduced via targeted level selection)

---

## ⚙️ Remote Server Configuration

### To maximize parallel download on server:

```bash
# Discover number of CPUs
python -c "import multiprocessing as mp; print(mp.cpu_count())"

# Use all minus 1
python scripts/ep1_full_analysis/step2_download_era5_parallel.py --jobs 15

# Or use default (auto-detects)
python scripts/ep1_full_analysis/step2_download_era5_parallel.py
```

### Screen session (to avoid losing progress if disconnected):

```bash
# Start screen
screen -S ep1_download

# Run download
python scripts/ep1_full_analysis/step2_download_era5_parallel.py

# Detach: Ctrl+A, D
# Reattach: screen -r ep1_download
```

---

## ✨ Implemented Features

1. **✅ Customizable parallel download** 
   - Argument `--jobs N`
   - Default: 2 (respects CDS API limits)
   - Max recommended: 2-4 (CDS API constraint)

2. **✅ SLP included**
   - Mean Sea Level Pressure downloaded and merged automatically
   - Available in all NetCDF files

3. **✅ Complete precomputed composites**
   - All variables, all levels
   - Domain-specific dimensions (avoids xarray conflicts)

4. **✅ Robust file validation**
   - Checks completeness (variables, levels, timesteps)
   - Detects corruption (excessive NaN)
   - Automatic re-download of invalid files

5. **✅ Clear documentation**
   - README explaining differences
   - STATUS showing what's ready
   - Usage instructions

6. **✅ Modified visualizations**
   - PV plots with 250 hPa contours and wind vectors
   - EGR plots with SLP contours and 975 hPa winds

7. **✅ Scientific documentation**
   - Auto-generated report with analysis results
   - Physical interpretations and statistics

8. **✅ Optimized vertical level selection**
   - Based on Ca/Ck vertical analysis (step2_vertical_levels_analysis.py)
   - 7 targeted levels instead of 14 (50% data reduction)
   - See VERTICAL_LEVELS.md for detailed rationale

9. **✅ Production-ready logging**
   - Automatic log files with timestamps
   - Progress tracking (completed/remaining/estimated time)
   - Compatible with nohup for background execution
   - CDS API error handling and retry logic

---

**Author:** GitHub Copilot  
**Date:** February 13, 2026
