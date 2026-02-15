# Remote Execution Guide: EP1 Full Analysis

Complete guide for running the analysis pipeline on a remote server (master.iag.usp.br) and transferring only necessary files to local machine for figure generation.

## 📋 Overview

**What runs on server:**
- Steps 1-3: Case selection, ERA5 download, composite precomputation

**What runs locally:**
- Step 4: Figure generation (uses precomputed composites)

**Data transfer:** Only ~100-300 MB (3 domain composite files) instead of ~50-80 GB (raw ERA5 files)

**Storage optimization:** Transfer only 0.2-0.6% of total data volume

---

## 🖥️ Remote Server Execution

### 1. Initial Setup

```bash
# Connect to remote server (with SSH key authentication)
ssh -i ~/Documents/Master/id_rsa.danilocs danilocs@master.iag.usp.br

# Navigate to project directory
cd /discos-varal/swell/p1-swell/danilocs/paper_energy_patterns

# Activate conda environment
conda activate paper_energy

# Check available CPUs for parallelization
python -c "import multiprocessing; print(f'Available CPUs: {multiprocessing.cpu_count()}')"
```

### 2. Run Pipeline with nohup

#### Step 1: Select All EP1 Cyclones (fast, ~1 min)

```bash
python scripts/ep1_full_analysis/step1_select_all_ep1.py
```

**Output:** `results/ep1_full/all_ep1_cases.csv`

#### Step 2: Download ERA5 (parallelized, ~6-12 hours)

```bash
# Run with nohup for background execution
nohup python scripts/ep1_full_analysis/step2_download_era5_parallel.py --jobs 2 > download.log 2>&1 &

# Monitor progress
tail -f logs/step2_download_*.log

# Check if running
ps aux | grep step2_download
```

**⚠️ CDS API limits:** Use `--jobs 2` (max 4) to avoid "too many requests" errors.

**Output:** `data/era5_ep1_full/*_era5.nc` (~50-80 GB total)

#### Step 3: Precompute Composites + Diagnostics (parallelized, ~3-6 hours)

```bash
# Run with nohup for background execution
nohup python scripts/ep1_full_analysis/step3_precompute_composites.py --jobs 4 > precompute.log 2>&1 &

# Monitor progress
tail -f logs/step3_precompute_*.log

# Check if running
ps aux | grep step3_precompute
```

**Parallelization:** Uses domain-level parallelization (3 domains: local, mesoscale, synoptic)

**Output:** 
- `data/era5_ep1_full/precomputed_composites_local.nc` (~30-100 MB)
- `data/era5_ep1_full/precomputed_composites_mesoscale.nc` (~30-100 MB)
- `data/era5_ep1_full/precomputed_composites_synoptic.nc` (~30-100 MB)
- **Total: ~100-300 MB** ✅

### 3. Monitor Progress

```bash
# View real-time logs
tail -f logs/step3_precompute_*.log

# Check all running Python processes
ps aux | grep python | grep ep1_full_analysis

# Check disk usage
du -sh data/era5_ep1_full/

# Verify output files exist
ls -lh data/era5_ep1_full/precomputed_composites_*.nc
```

### 4. Troubleshooting

**Process killed unexpectedly:**
```bash
# Check system logs
dmesg | tail -50

# Check available memory
free -h

# Check disk space
df -h
```

**Log file not updating:**
```bash
# Process might have finished - check exit status
echo $?  # 0 = success, non-zero = error

# List all log files sorted by date
ls -lt logs/step*.log | head -10
```

**Restart from failure:**
```bash
# Step2 validates existing files and skips them automatically
# Step3 can be rerun without data loss (will overwrite composites)
```

---

## 📦 File Transfer to Local Machine

### Method: SCP with SSH Key Authentication

**⚠️ Important:** You will be prompted for password in **TWO separate windows** during transfer.

### Option 1: Interactive Script (Recommended)

```bash
# On LOCAL machine
cd ~/Documents/Programs_and_scripts/paper_energy_patterns

# Run transfer script (prompts for each section)
bash scripts/ep1_full_analysis/transfer_guide_scp.sh
```

The script will:
1. Transfer essential files (precomputed composites, ~100-300 MB)
2. Optionally transfer logs, results, figures
3. Show summary of transferred data

### Option 2: Manual Commands

#### Essential Files (Required for figure generation)

```bash
# Transfer precomputed composites (3 domain files)
scp -i ~/Documents/Master/id_rsa.danilocs -C \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/data/era5_ep1_full/precomputed_composites_*.nc \
    ~/Documents/Programs_and_scripts/paper_energy_patterns/data/era5_ep1_full/
```

**Note:** `-C` flag enables compression for faster transfer.

#### Optional Files

```bash
# Transfer results metadata (~1-10 MB)
scp -i ~/Documents/Master/id_rsa.danilocs -C -r \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/results/ep1_full/ \
    ~/Documents/Programs_and_scripts/paper_energy_patterns/results/

# Transfer logs (~1-5 MB)
scp -i ~/Documents/Master/id_rsa.danilocs -C \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/logs/step*.log \
    ~/Documents/Programs_and_scripts/paper_energy_patterns/logs/

# Transfer figures if generated on remote (~5-15 MB)
scp -i ~/Documents/Master/id_rsa.danilocs -C -r \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/figures/ep1_full/ \
    ~/Documents/Programs_and_scripts/paper_energy_patterns/figures/
```

#### Files to SKIP (Keep on Server)

```bash
# ❌ DO NOT transfer raw ERA5 files (~50-80 GB)
# These stay on server: data/era5_ep1_full/*_era5.nc
```

---

## 💻 Local Figure Generation

### 1. Verify Transferred Files

```bash
# On LOCAL machine
cd ~/Documents/Programs_and_scripts/paper_energy_patterns

# Check precomputed composites exist
ls -lh data/era5_ep1_full/precomputed_composites_*.nc

# Expected output:
# precomputed_composites_local.nc      (~30-100 MB)
# precomputed_composites_mesoscale.nc  (~30-100 MB)
# precomputed_composites_synoptic.nc   (~30-100 MB)
```

### 2. Generate Figures

```bash
# Activate conda environment
conda activate paper_energy

# Run figure generation (~5 minutes)
python scripts/ep1_full_analysis/step4_create_figures.py
```

**Output:** `figures/ep1_full/composite/composite_{local,mesoscale,synoptic}.png`

### 3. Check Results

```bash
# List generated figures
ls -lh figures/ep1_full/composite/

# Open figures (macOS)
open figures/ep1_full/composite/composite_mesoscale.png

# Check log file
tail -50 logs/step4_figures_*.log
```

---

## 📊 Data Transfer Summary

| Location | Content | Size | Purpose |
|----------|---------|------|---------|
| **Remote Server** | ERA5 raw files (`*_era5.nc`) | ~50-80 GB | Computed by step2 |
| **Remote Server** | Precomputed composites (3 files) | ~100-300 MB | Computed by step3 |
| **Transfer → Local** | Precomputed composites | ~100-300 MB | **Required** for figures |
| **Local Machine** | Generated figures | ~5-15 MB | Final output |

**Key insight:** Transfer only 0.2-0.6% of total data volume while maintaining full analysis capability.

---

## 🔍 Troubleshooting

### Transfer Issues

**Problem:** "Permission denied (publickey)"
```bash
# Verify SSH key exists and permissions
ls -l ~/Documents/Master/id_rsa.danilocs
# Should be: -rw------- (600 permissions)

# Fix permissions if needed
chmod 600 ~/Documents/Master/id_rsa.danilocs
```

**Problem:** "No such file or directory"
```bash
# Verify remote path
ssh -i ~/Documents/Master/id_rsa.danilocs danilocs@master.iag.usp.br \
    "ls /discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/data/era5_ep1_full/"
```

**Problem:** Two password prompts appearing
- This is expected behavior for this server configuration
- Keep both authentication windows ready during transfer

### Figure Generation Issues

**Problem:** "File not found: precomputed_composites_*.nc"
```bash
# List what you have
ls data/era5_ep1_full/precomputed_composites_*.nc

# If missing, re-transfer from server (see transfer section)
```

**Problem:** "Missing required variables"
```bash
# Check variable contents
python -c "import xarray as xr; ds = xr.open_dataset('data/era5_ep1_full/precomputed_composites_mesoscale.nc'); print(list(ds.data_vars))"

# If variables are missing, you need to re-run step3 on server
```

---

## 📝 Complete Workflow Summary

### On Remote Server:
```bash
# 1. Initial setup
ssh -i ~/Documents/Master/id_rsa.danilocs danilocs@master.iag.usp.br
cd /discos-varal/swell/p1-swell/danilocs/paper_energy_patterns
conda activate paper_energy

# 2. Run compute-intensive steps
python scripts/ep1_full_analysis/step1_select_all_ep1.py
nohup python scripts/ep1_full_analysis/step2_download_era5_parallel.py --jobs 2 > download.log 2>&1 &
nohup python scripts/ep1_full_analysis/step3_precompute_composites.py --jobs 4 > precompute.log 2>&1 &

# 3. Monitor
tail -f logs/step3_precompute_*.log
```

### On Local Machine:
```bash
# 1. Transfer essential files
cd ~/Documents/Programs_and_scripts/paper_energy_patterns
bash scripts/ep1_full_analysis/transfer_guide_scp.sh

# 2. Generate figures
conda activate paper_energy
python scripts/ep1_full_analysis/step4_create_figures.py

# 3. View results
open figures/ep1_full/composite/composite_mesoscale.png
```

---

## 🎯 Best Practices

1. **Always use `nohup` for long-running steps** - Prevents interruption if SSH connection drops
2. **Monitor logs actively** - Use `tail -f` to catch errors early
3. **Verify outputs before transfer** - Check file sizes with `ls -lh`
4. **Transfer only what you need** - Skip raw ERA5 files (~50-80 GB)
5. **Keep SSH key secure** - Verify permissions (600) on `id_rsa.danilocs`

---

**Author:** Danilo Couto de Souza  
**Last Updated:** February 2026
