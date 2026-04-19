# TROUBLESHOOTING — LEC–Field Dependence Pipeline

> **For day-to-day usage, see [USER_GUIDE.md](USER_GUIDE.md).**
> This document covers known bugs, root causes, and diagnostic commands.

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

## B5 (MINOR, FIXED): Step 8 figures wrong / empty

This was previously tracked but has been consolidated into the [Operational Issues](#step-8-figures-look-wrong--empty) section below.

---

## B6 (DOC, FIXED): SCIENTIFIC_NOTES.md had duplicated Step 7b section

**Symptom:** The "Inter-EP Statistical Significance Testing (Step 7b)" section (~80 lines including rationale, decision tree, effect sizes, and limitations) appeared twice in SCIENTIFIC_NOTES.md.

**Fix:** Removed the second (duplicate) occurrence.

---

## B7 (DOC, FIXED): README unclear about step 3 dry-run → remote workflow

**Symptom:** README said "Steps 1–3 run locally" without warning that step 3's dry-run manifest would break steps 4–5 on the remote server if used directly.

**Fix:** Added a warning box in the README explaining that step 3 must be re-run on the remote server with `--era5-dir` before steps 4–5 when running manually (the orchestrator handles this automatically).

---

## B8 (CRITICAL, FIXED): Steps 4/5 produce all-NaN ERA5 dynamic features

**Symptom:** Steps 4 and 5 complete without error. The output CSVs exist and have the correct number of rows. But all ERA5-derived feature columns (`pv_850__*`, `pv_200__*`, `adv_T_850__*`, `afc_250__*`, `ke_adv_250__*`) are entirely NaN. Downstream PREDEP values (step 7) are also NaN or 0 for all these features.

Running `python monitor_pipeline.py --verify` shows:
```
✗  step4_features_absolute.csv — ... only X% non-null (sparse extraction!)
   → Root cause: step 3b was likely not run before steps 4/5.
```

**Root cause:** The raw per-cyclone ERA5 files (`{track_id}_era5.nc`) contain the instantaneous multi-level fields downloaded from the CDS API: `u`, `v`, `t`, `z`, `q` at pressure levels 175/200/225/250/500/825/850/875/975 hPa, plus `msl` at single level. They do **not** contain the derived dynamic diagnostics (`pv_850`, `pv_200`, `adv_T_850`, `afc_250`, `ke_adv_250`). The old steps 4 and 5 silently filled NaN for any variable not found in the file — no crash, no loud error.

**Fix (implemented in this codebase):** A new preprocessing step, **step 3b** (`step3b_derive_era5_fields.py`), must be run between step 3 and step 4. Step 3b reads each raw ERA5 file, applies the validated diagnostic functions from `ep_structure_analysis/step3_precompute_composites.py`, and saves the computed fields to `{derived_dir}/{track_id}_era5_derived.nc`. Steps 4 and 5 now read from these derived files and fail loudly (with `sys.exit(1)` and a clear message) if the derived directory is missing or empty.

**Recovery steps for existing all-NaN results:**
```bash
# 1. Run step 3b on the server
python step3b_derive_era5_fields.py \
    --era5-dir /data/era5/ --derived-dir /data/era5/derived/

# 2. Delete the all-NaN feature CSVs
rm results/lec_field_dependence/step4_features_absolute*.csv
rm results/lec_field_dependence/step5_features_anomaly*.csv
rm results/lec_field_dependence/step6_integrated*.csv
rm results/lec_field_dependence/step7_predep*.csv

# 3. Re-run from step 4
bash run_pipeline.sh --era5-dir /data/era5/ --derived-dir /data/era5/derived/ \
    --only 4,5,6,7,7b,8,8b,9
```

**How to detect going forward:** `python monitor_pipeline.py --verify` checks the non-null rate of feature columns and now explicitly warns if step 3b manifest is missing.

---

## Common Operational Issues

### Pipeline appears stuck at step 3b / 4 / 5

**Check:** Use the monitor to see chunk-level status:
```bash
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch --log-tail
```

If individual chunks are completing but slowly, this is normal — 2733 cases × feature extraction is computationally intensive. If no progress for >30 minutes, check individual chunk logs in `logs/`.

### Step 7 runs out of memory

**Cause:** With `--workers 32`, each worker loads a copy of the integrated CSV. For large datasets, this is memory-intensive.

**Fix:** Reduce workers: `--workers 4` or use chunking: `--chunk 0 --n-chunks 10`.

### Step 4/5 exits with "CRITICAL: Derived directory does not exist"

**Cause:** Step 3b was either not run or used a different `--derived-dir` than what step 4/5 are now pointing to.

**Fix:** Run step 3b first with the same `--derived-dir`:
```bash
python step3b_derive_era5_fields.py --era5-dir /path/to/era5/ --derived-dir /path/to/derived/
python step4_extract_features_absolute.py --era5-dir /path/to/era5/ --derived-dir /path/to/derived/
```

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

### SSH/rsync connection issues

**Cause:** SSH key path or remote host may be wrong.

**Fix:** Edit the `REMOTE_USER`, `REMOTE_HOST`, `SSH_KEY`, and `REMOTE_BASE` variables at the top of `sync_from_remote.sh`.

---

## Diagnostic Commands

```bash
# Verify pipeline outputs
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --verify

# Quick status
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --no-color

# ── Cleaning ──────────────────────────────────────────────────────────────────

# Preview all files that would be deleted (safe — no changes)
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --all

# Full clean (results + figures + logs)
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --all --yes

# Scoped: chunks only, logs only, etc.
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --chunks --yes
bash scripts/lec_field_dependence_analysis/clean_pipeline_outputs.sh --logs --yes

# ── Running ───────────────────────────────────────────────────────────────────

# Run pipeline in background (survives SSH disconnect)
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --background
# → prints PID and nohup log path, then exits; pipeline keeps running

# Clean + run in one command
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --clean --background

# Halt on first failure instead of continuing (default: continue all)
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --stop-on-error

# Re-run only specific steps after a partial failure
bash scripts/lec_field_dependence_analysis/run_pipeline.sh --era5-dir /path/to/era5/ --only 6,7,7b --skip-done

# Then monitor progress
python scripts/lec_field_dependence_analysis/monitor_pipeline.py --watch

# ── Diagnostics ───────────────────────────────────────────────────────────────

# Check step 3 manifest (is era5_available all False = dry-run?)
python -c "import pandas as pd; m=pd.read_csv('results/lec_field_dependence/step3_era5_field_manifest.csv'); print(m['era5_available'].value_counts())"

# Check step 6 integrated columns (verify anomaly naming)
python -c "import pandas as pd; df=pd.read_csv('results/lec_field_dependence/step6_integrated_anomaly.csv'); print([c for c in df.columns if '__' in c][:10])"

# Re-run LEC-only significance (fast, local)
python scripts/lec_field_dependence_analysis/step7b_ep_significance_tests.py --lec-only
python scripts/lec_field_dependence_analysis/step8b_significance_figures.py
```
