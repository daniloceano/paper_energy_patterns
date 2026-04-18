# TROUBLESHOOTING — LEC–Field Dependence Pipeline

Common issues, root causes, and fixes encountered during development and auditing.

---

## B1 (CRITICAL, FIXED): Step 7b finds zero anomaly feature columns

**Symptom:** Step 7b logs `Anomaly feature columns: 0` and skips the anomaly block entirely, even though `step6_integrated_anomaly.csv` has the expected columns.

**Root cause:** Step 5 creates anomaly columns using `DYNAMIC_FIELDS_ABSOLUTE` keys with `_anom_epall` suffix (e.g., `pv_850_anom_epall__domain_mean`). Step 7b was iterating over `DYNAMIC_FIELDS_ANOMALY` keys which use `_minus_epall` (e.g., `pv_850_minus_epall__domain_mean`). The naming conventions did not match.

**Fix:** Changed step 7b section C to build anomaly field keys from `DYNAMIC_FIELDS_ABSOLUTE` with `_anom_epall` suffix, matching step 5's output convention.

**Verification:** Run `python step7b_ep_significance_tests.py` (full mode, not `--lec-only`) and check that the log shows a non-zero count for `Anomaly feature columns`.

---

## B2 (CRITICAL, FIXED): Steps 4/5 silently produce nothing when using a dry-run manifest

**Symptom:** Steps 4 and 5 log `Nothing to process. Done.` and exit with code 0, producing no output CSV. Pipeline appears successful but has no results.

**Root cause:** Step 3 in dry-run mode (without `--era5-dir`) set all manifest entries to `era5_available=False`. Steps 4 and 5 filtered on this column: `manifest = manifest[manifest["era5_available"]]`, yielding 0 rows.

**Fix:** Steps 4 and 5 now check if ALL cases are `era5_available=False`. If so, they log a warning and skip the filter (the extraction functions already handle missing files gracefully with `_status: file_not_found`).

**How to avoid:** When running steps manually on the remote server, re-run step 3 with `--era5-dir /path/to/era5/` before running steps 4–5. The orchestrator (`run_pipeline.sh`) does this automatically.

---

## B3 (MINOR, FIXED): Step 7 had dead/confusing field_registry code

**Symptom:** No runtime error, but confusing code in step 7 where `field_registry` was assigned twice (second overwrote first) and never used.

**Fix:** Removed the unused `field_registry` variable. Step 7 discovers feature columns dynamically from the CSV headers (columns containing `__`), making the registry unnecessary.

---

## B4 (MINOR, FIXED): Step 5 --workers argument silently ignored

**Symptom:** `python step5_... --workers 8` runs serially despite the flag.

**Root cause:** Step 5 uses a global `_EPALL_FIELDS` dict loaded in the main process. `ProcessPoolExecutor` workers would not share this global state. The extraction loop was always serial, but the `--workers` argument was accepted without warning.

**Fix:** Step 5 now logs a warning when `--workers > 1` is passed, explaining that orchestrator-level chunking (`--chunk / --n-chunks`) is the intended parallelism mechanism.

---

## B5 (MINOR, FIXED): Transfer guide missing step 7 PREDEP result files

**Symptom:** After running `transfer_guide_scp.sh`, the local machine is missing `step7_predep_absolute.csv` and `step7_predep_anomaly.csv` — the primary PREDEP results.

**Fix:** Added both files to the `ESSENTIAL_FILES` list in `transfer_guide_scp.sh`.

---

## B6 (DOC, FIXED): SCIENTIFIC_NOTES.md had duplicated Step 7b section

**Symptom:** The "Inter-EP Statistical Significance Testing (Step 7b)" section (~80 lines including rationale, decision tree, effect sizes, and limitations) appeared twice in SCIENTIFIC_NOTES.md.

**Fix:** Removed the second (duplicate) occurrence.

---

## B7 (DOC, FIXED): README unclear about step 3 dry-run → remote workflow

**Symptom:** README said "Steps 1–3 run locally" without warning that step 3's dry-run manifest would break steps 4–5 on the remote server if used directly.

**Fix:** Added a warning box in the README explaining that step 3 must be re-run on the remote server with `--era5-dir` before steps 4–5 when running manually (the orchestrator handles this automatically).

---

## Common Operational Issues

### Pipeline appears stuck at step 4/5

**Check:** Use the monitor to see chunk-level status:
```bash
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch --log-tail
```

If individual chunks are completing but slowly, this is normal — 2733 cases × feature extraction is computationally intensive. If no progress for >30 minutes, check individual chunk logs in `logs/`.

### Step 7 runs out of memory

**Cause:** With `--workers 32`, each worker loads a copy of the integrated CSV. For large datasets, this is memory-intensive.

**Fix:** Reduce workers: `--workers 4` or use chunking: `--chunk 0 --n-chunks 10`.

### Step 4/5 has many "file_not_found" failures

**Cause:** Per-cyclone ERA5 files don't exist for all track IDs. This is expected if the ERA5 extraction was done for a subset.

**Check:** The QA guard in step 4/5 will exit with code 1 if ALL cases are `file_not_found`, indicating the `--era5-dir` path is wrong. A partial failure rate is normal.

### Step 8 figures look wrong / empty

**Cause:** Step 7 chunk files haven't been merged. Step 8 reads both `step7_predep_absolute.csv` and chunk files `step7_predep_absolute_chunk*.csv`.

**Fix:** After all chunks complete, run `step6_integrate_tables.py` to ensure tables are merged, then re-run step 8.

### "ModuleNotFoundError: No module named 'scripts'"

**Cause:** Running from wrong directory. All scripts must be run from the project root.

**Fix:**
```bash
cd /path/to/paper_energy_patterns
python scripts/lec_field_dependence_analysis/stepN_...py
```

### SSH/SCP connection issues with transfer guide

**Cause:** SSH key path or remote host may be wrong.

**Fix:** Edit the `REMOTE_USER`, `REMOTE_HOST`, `SSH_KEY`, and `REMOTE_BASE` variables at the top of `transfer_guide_scp.sh`.

---

## Diagnostic Commands

```bash
# Verify pipeline outputs
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --verify

# Quick status
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --no-color

# Run pipeline in background (survives SSH disconnect)
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --background
# → prints PID and nohup log path, then exits; pipeline keeps running

# Then monitor progress
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch

# Wipe all previous results and logs, then run from scratch
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --clean
# Cleans: results/lec_field_dependence/  figures/lec_field_dependence/
#         logs/step*  logs/orchestrator*  logs/nohup_pipeline*  logs/pipeline.{pid,status}

# Preview what --clean would delete without actually deleting anything
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --clean --dry-run

# Combine: wipe + run in background
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --clean --background

# Halt on first failure instead of continuing (old behaviour)
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --stop-on-error

# Re-run only specific steps after a partial failure
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --only 6,7,7b --skip-done

# Check step 3 manifest (is era5_available all False = dry-run?)
python -c "import pandas as pd; m=pd.read_csv('results/lec_field_dependence/step3_era5_field_manifest.csv'); print(m['era5_available'].value_counts())"

# Check step 6 integrated columns (verify anomaly naming)
python -c "import pandas as pd; df=pd.read_csv('results/lec_field_dependence/step6_integrated_anomaly.csv'); print([c for c in df.columns if '__' in c][:10])"

# Re-run LEC-only significance (fast, local)
python scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py --lec-only
python scripts/lec_field_dependence_analysis/step8b_significance_figures.py
```
