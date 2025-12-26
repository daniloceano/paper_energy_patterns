# Deployment Instructions for Server

## 📦 Initial Setup on Server

```bash
# 1. Clone the repository
git clone https://github.com/daniloceano/paper_energy_patterns.git
cd paper_energy_patterns

# 2. Create conda environment
bash setup_environment.sh
# Answer 'y' if prompted

# 3. Activate environment
conda activate paper_energy_patterns

# 4. Verify installation
python scripts/setup_and_examples/verify_environment.py
```

## 🚀 Data Preprocessing (Run Once)

This is the CRITICAL step for performance! Run with all 50 cores:

```bash
# Edit the configuration in scripts/utils/preprocess_data.py
# Make sure: N_WORKERS = 50

python scripts/utils/preprocess_data.py
```

**Expected performance:**
- Processing time: ~10-15 minutes with 50 cores
- Output file: `data/energy_cache.parquet` (~50-100 MB)
- Speedup for analyses: 1000x faster than loading from GitHub

**Bottleneck identification:**
The script will print detailed timing for each step:
- STEP 1: Loading track IDs (~5 seconds)
- STEP 2: Processing cyclones (main bottleneck - watch the rate)
- STEP 3: Combining data (~10 seconds)
- STEP 4: Type conversion (~5 seconds)
- Saving cache (~5 seconds)

## 📊 Running Analyses

After preprocessing, analyses are FAST!

### Example: KDE Pairplot

```bash
# Edit scripts/exploratory/kde_pairplot.py
SAMPLE_SIZE = 0      # Process ALL cyclones
USE_PARALLEL = True
N_WORKERS = 50       # Use all cores

# Run
python scripts/exploratory/kde_pairplot.py
```

## 🔄 Push Results Back to GitHub

```bash
# After running analyses, commit results
git add figures/exploratory/*.png
git add results/exploratory/*.csv
git commit -m "Add exploratory analysis results"
git push
```

## ⚡ Performance Benchmarks

### Without Cache (Direct GitHub Loading)
- 1 cyclone: ~0.15 seconds
- 6,700 cyclones: ~16 minutes (sequential)
- 6,700 cyclones: ~20 seconds (50 cores) ❌ Still slow due to network I/O

### With Cache (Preprocessed Parquet)
- Load ALL 6,700 cyclones: <1 second ✅
- Then process with 50 cores: blazing fast! 🚀

## 🐛 Troubleshooting

### Preprocessing is slow
Check the "Processing rate" in the output:
- Expected: 50-100 cyclones/second (with 50 cores)
- If slower: network bottleneck (GitHub API limits)
- Solution: Run during off-peak hours or add retry logic

### Out of Memory
If processing fails with OOM:
```python
# Reduce workers temporarily
N_WORKERS = 25  # Use half the cores
```

### Cache not found
If analysis scripts can't find cache:
```bash
ls -lh data/energy_cache.parquet
# If missing, run: python scripts/utils/preprocess_data.py
```

## 📋 Checklist Before First Run

- [ ] Repository cloned
- [ ] Conda environment created and activated
- [ ] All packages verified with verify_environment.py
- [ ] N_WORKERS set to 50 in preprocess_data.py
- [ ] Preprocessing completed (energy_cache.parquet exists)
- [ ] Test analysis runs successfully with SAMPLE_SIZE=10
- [ ] Ready for full run with SAMPLE_SIZE=0

## 🎯 Recommended Workflow

1. **Local Testing** (on laptop):
   ```python
   SAMPLE_SIZE = 10-20  # Quick test
   USE_PARALLEL = False
   ```

2. **Server Preprocessing** (once):
   ```bash
   python scripts/utils/preprocess_data.py
   # Takes ~15 min, creates cache
   ```

3. **Server Analysis** (uses cache):
   ```python
   SAMPLE_SIZE = 0      # All data
   USE_PARALLEL = True
   N_WORKERS = 50
   ```

4. **Download Results**:
   ```bash
   scp -r server:paper_energy_patterns/figures/ ./
   scp -r server:paper_energy_patterns/results/ ./
   ```

## 📞 Support

If you encounter issues:
1. Check the detailed timing prints in the output
2. Verify network connectivity to GitHub
3. Check available disk space (~1 GB needed)
4. Monitor CPU usage (should be near 5000% with 50 cores)
