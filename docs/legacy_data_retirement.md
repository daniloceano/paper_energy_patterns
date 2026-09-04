# Retiring the legacy LEC data

Status of the migration from the legacy (article) Lorenz Energy Cycle results to
the corrected climatology produced by `scripts/lec_climatology_rerun`
(LorenzCycleToolKit 2.0.0, pinned commit `d38cda7e`).

**Policy.** The corrected rerun is the only scientific truth for this article.
The legacy artefacts survive for exactly one purpose — the *before* side of
`scripts/lec_rerun_comparison` — and must not feed any other result, table or
figure. Anything else that reads them is a defect.

---

## 1. The legacy artefacts

| Artefact | What it holds | Verdict |
|---|---|---|
| `data/energy_cache.parquet` | Phase-mean LEC terms, 3,820 cyclones | **Legacy.** Superseded equations. |
| `data/temp_lec_zenodo/LEC_Results_energetic-patterns/` | Per-cyclone legacy results, `*_level.csv` verticals, `periods.csv` | **Mixed.** Results and verticals are legacy; `periods.csv` is the *frozen window* source, deliberately reused by the rerun. |
| `data/tracks_SAt_filtered_with_energetics_processed.csv` | 1-hourly positions + `vor42` + legacy LEC columns | **Mixed.** Positions and `vor42` are tracking data and remain valid; `Kz, Ke, Ck, Ca, BAe, BKe, Ge` are legacy. |
| `results/cluster/*` | PCA/k-means Energy Patterns | **Derived legacy.** Must be regenerated. |
| `results/ep_structure/ep{1,2,3,all}_cases.csv` | EP populations + intensification windows | **Derived legacy.** Regenerate after re-clustering. |
| `results/ck_analysis/*`, `results/ck_subterms/*` | EP1-only Ck side run | **Legacy and superseded** — see §4. |
| `results/lec_field_dependence/*` | PREDEP tables built on the Zenodo LEC | **Derived legacy.** Rebuild. |

The frozen lifecycle windows are *not* legacy energetics. The rerun deliberately
reuses them (`<run-root>/phase_windows/`, hashed in `provenance.json`) so that the
only difference between the two datasets is the equation correction. Read them
from the run root, not from `data/temp_lec_zenodo/`.

---

## 2. Replacements

Built by `scripts/lec_climatology_rerun/build_*.py` into `data/corrected/`, and
read through `scripts/utils/corrected_lec.py`:

| New product | Replaces | Builder |
|---|---|---|
| `energy_cache_corrected.parquet` | `data/energy_cache.parquet` | `build_corrected_cache.py` |
| `tracks_with_energetics_corrected.csv` | `tracks_SAt_filtered_with_energetics_processed.csv` | `build_corrected_tracks.py` |
| `vertical_phase_means_corrected.parquet` | `data/temp_lec_zenodo/.../{Ca,Ck}_level.csv` | `build_corrected_vertical_levels.py` |

`scripts/utils/corrected_lec.py` is the single access point. It resolves the run
root, exposes the state machine, reads integrated terms, frozen windows and
pressure-level profiles, and — critically — owns the unit conventions of §3.

---

## 3. Conventions that changed, and one that did not

Verified empirically against the pinned toolkit output; re-checkable any time
with `corrected_lec.verify_conventions(track_id)`, which passes to ~1e-13.

| Rule | Legacy code | Corrected data | Action |
|---|---|---|---|
| `Ca` vertical sign | `Ca = -Ca_level` (`main/05_figure_vertical_levels.py`) | `Ca_pressure_level` integrates to `+Ca` | **Remove the flip.** Keeping it reintroduces the fixed bug with the opposite sign. |
| `Ck` vertical scale | `Ck_level / 9.8` | Still omits `1/g` | **Keep**, but with `g = 9.80665`. The legacy `9.8` was a 0.07 % high bias. |
| `Kz`, `Ke` vertical scale | never handled | Omit `1/(2g)` | **New:** divide by `2g`. |
| `Ck` decomposition | n/a (EP1 side run only) | `Ck = Σ Ck_1..Ck_5` closes to round-off | Usable directly; closure is asserted. |
| `Ca` decomposition | n/a | `Ca = -(Ca_1 + Ca_2)` | Usable with the global sign. |
| `Ce_1/Ce_2`, `Cz_1/Cz_2` | n/a | **Not** decompositions — `Ce_1` is a constant factor and the pairs do not sum to their parent | **Never plot as subterms.** |

`M` is a mass-residual diagnostic whose vertical file has no fixed ratio to its
integrated column; it is excluded from the checks.

---

## 4. Ck subterms — now available for every Energy Pattern

The decomposition used to be EP1-only (444 cyclones) because obtaining it
required a separate toolkit run: the archived article results carried only the
total `C_K`. The corrected rerun writes `Ck_1` … `Ck_5` pressure-level files for
**all 3,820 cyclones**, so the analysis extends to EP1, EP2, EP3 and EPALL at no
extra computational cost.

- **New pipeline:** `scripts/ck_subterms_analysis/` → `results/ck_subterms_corrected/`,
  `figures/ck_subterms_corrected/`. Three steps: build table, statistics, figures.
- **Retired:** the side-run drivers now live in
  `scripts/ck_subterms_analysis/deprecated_ep1_side_run/`. They wrote into
  `results/ck_analysis/` and predate the 2.0.0 corrections.
- **Expect different numbers.** The earlier EP1 result (Ck_E dominant in 43 % of
  cases, Ck_B 38 %, Ck_A 19 %, with a hypothesis that Ck_A would carry 70–80 %)
  is provisional on two counts: the corrections and the widened population.
  Treat the regenerated `statistics_report.md` as the result and revisit the
  manuscript text, rather than reconciling new output to old claims.

---

## 5. The cluster → Energy Pattern mapping

`scripts/utils/ep_mapping.py` used to hardcode `{0: EP1, 1: EP3, 2: EP2}` and the
counts `444 / 979 / 2397`. **K-means cluster indices are arbitrary**: re-running
the clustering on the corrected cache reshuffles them, and a frozen table would
silently relabel every Energy Pattern in every downstream figure — a failure that
produces plausible-looking wrong figures rather than an error.

The mapping is now *derived* from the cluster centroids and persisted next to the
clustering it describes, in `results/cluster/cluster_to_ep.json`:

> EP1 → strongest intensification-phase conversions, ranked by `|Ca_int| + |Ck_int|`,
> then EP2, then EP3.

That rule reproduces the article mapping exactly when applied to the legacy
centroids, so the convention is unchanged — only its provenance is. The file also
records which energy cache the clustering consumed, so
`ep_mapping.assert_corrected_clustering()` can refuse to build an article result
on a legacy clustering. The file currently on disk is stamped
`data/energy_cache.parquet (LEGACY - superseded)` and will be overwritten by
`step4_apply_kmeans.py` on the next run.

---

## 6. Work remaining, by script

### Done

| Script | Change |
|---|---|
| `scripts/utils/corrected_lec.py` | **New.** Single access point; owns the conventions of §3. |
| `scripts/utils/ep_mapping.py` | Mapping derived from centroids, lineage-stamped, lazily resolved. |
| `scripts/lec_climatology_rerun/build_corrected_tracks.py` | **New.** |
| `scripts/lec_climatology_rerun/build_corrected_vertical_levels.py` | **New.** |
| `scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py` | Defaults to the corrected cache; legacy is no longer a fallback. |
| `scripts/cluster_analysis_energy_patterns/step4_apply_kmeans.py` | Writes `cluster_to_ep.json` with the cache lineage. |
| `scripts/ck_subterms_analysis/` | Rewritten for all EPs; side run deprecated. |

### To do — blocking the article

| Script | Reads | Required change |
|---|---|---|
| `main/05_figure_vertical_levels.py` | `temp_lec_zenodo/{Ca,Ck}_level.csv`, hardcoded `-Ca` and `/9.8` | Read `vertical_phase_means_corrected.parquet` via `corrected_lec`; **delete both hacks** (§3). |
| `main/S3_figure_ck_subterms_vertical_profiles.py` | `results/ck_analysis/`, `ep1_cases.csv`, `temp_lec_zenodo` | Repoint to `results/ck_subterms_corrected/`; can now show all EPs, not EP1 alone. |
| `ep_structure_analysis/step1_select_ep_tracks.py` | `temp_lec_zenodo/*/periods.csv`, `kmeans_clustered_data.csv` | Read windows from `<run-root>/phase_windows/`; rerun after re-clustering. |
| `ep_structure_analysis/step2*`–`step6*` | `ep{1,2,3,all}_cases.csv` | Rerun after step 1; ERA5 composites can be reused where the case lists are unchanged, but the *populations will change* with the new clustering. |
| `lec_field_dependence_analysis/utils_io.py` (`load_lec_from_zenodo`) | `temp_lec_zenodo` | Replace with a corrected reader; it is the single LEC entry point of that pipeline. |
| `lec_field_dependence_analysis/step1`, `step2`, `step6`, `step7`, `step7b` | the above | Rerun once `utils_io` is repointed. |
| `main/09`, `S2`, `S4` | `results/lec_field_dependence/` | Rerun after the PREDEP pipeline. |
| `cluster_analysis_energy_patterns/step2`–`step5` | `results/cluster/` | Rerun; no code change. |
| `main/01`, `06`, `07`, `S1` | `results/cluster/` | Rerun after re-clustering. |
| `main/02`, `03`, `04` | Composed PNGs from `figures/exploratory/` and `figures/cluster/` | Regenerate the upstream panels first (`cluster/step5_plot_energy_patterns.py`, `exploratory/figure_three_intense_cyclones_individual_zoom.py`, `exploratory/density_diagrams_with_ge.py`), which all read legacy energetics. |
| `explosive_cyclones_analysis/step1`, `step4` | `CLUSTER_TO_EP`, `EP_COUNTS` | Now resolve from `cluster_to_ep.json`; rerun after re-clustering. `step1` compares counts against `EP_COUNTS` — that check becomes a tautology and should be dropped or re-aimed. |
| `cps_analysis/step1_build_cps_database.py` | `CLUSTER_TO_EP` | Rerun after re-clustering. |
| `web/extract_ck_subterms_site_data.py` | `results/ck_analysis/` | Repoint to `results/ck_subterms_corrected/`. |
| `web/extract_cluster_site_data.py`, `prepare_site.py` | `results/cluster/`, figures | Rerun last, after every figure is regenerated. |

### Safe — positions only, no LEC

`ep_structure_analysis/step3_precompute_composites.py`, `step6_generate_cyclone_explorer_panels.py`,
`audit_storm_centering.py`, `diagnose_step3_failures.py`, `cps_analysis/export_cps_for_monitor.py`
and `web/generate_hotfix_manifest.py` read the legacy tracks CSV **for positions
only**. Those columns are identical in the corrected file. Repointing them is
tidiness, not correctness — but doing so removes the last reasons for the legacy
file to exist.

### Intentionally left on legacy

| Script | Why |
|---|---|
| `scripts/lec_rerun_comparison/*` | The legacy side *is* the subject: it quantifies what the correction changed. |
| `scripts/preprocess_data/*` | Documents how the legacy inputs were obtained; it is the provenance record. |
| `scripts/ep_structure_analysis_legacy/*`, `*_BACKUP.py` | Already marked legacy. |
| `scripts/exploratory/*` | Not in the paper. Anything promoted to a figure must be repointed first. |

---

## 7. Order of operations once the rerun completes

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2
cd /p1-swell/danilocs/paper_energy_patterns
E=paper_energy_patterns

# 0. confirm 3,820/3,820 COMPLETE
conda run -n $E python scripts/lec_climatology_rerun/monitor.py --run-root "$RUN"

# 1. derived products
conda run -n $E python -m scripts.lec_climatology_rerun.build_corrected_cache \
  --run-root "$RUN" --output data/corrected/energy_cache_corrected.parquet
conda run -n $E python -m scripts.lec_climatology_rerun.build_corrected_tracks --run-root "$RUN"
conda run -n $E python -m scripts.lec_climatology_rerun.build_corrected_vertical_levels --run-root "$RUN"

# 2. Energy Patterns (rewrites cluster_to_ep.json with a corrected lineage)
conda run -n $E python scripts/cluster_analysis_energy_patterns/run_all.py

# 3. analyses that depend on the Energy Patterns
conda run -n $E python scripts/ck_subterms_analysis/run_all.py
conda run -n $E python scripts/ep_structure_analysis/step1_select_ep_tracks.py
# ... then the ep_structure and lec_field_dependence pipelines

# 4. figures, then the website
conda run -n $E python scripts/main/run_all.py
conda run -n $E python scripts/web/prepare_site.py
```

The 32 `FAILED_FINAL` cyclones (CDS 5xx/timeouts, not data problems) must be
retried before step 1: every builder refuses a partial population.

```bash
conda run -n $E python -m scripts.lec_climatology_rerun.pipeline retry-failures --run-root "$RUN"
```

---

## 8. Open scientific questions raised by the migration

1. **Population size.** The rerun targets the same 3,820 cyclones, but the
   corrected terms change the PCA input, so the k-means partition — and hence
   every EP count in the manuscript — will move. The gap statistic should be
   re-run rather than assuming `k = 3` (`step3_optimal_k_analysis.py`).
2. **Vertical extent.** Code and archived output use 10–1000 hPa; the manuscript
   says 100–1000 hPa. Resolve in the text, not by trimming data.
3. **Ck subterm dominance.** See §4 — the earlier EP1 percentages are provisional.
4. **`Ca` sign.** Any manuscript statement about the vertical `Ca` structure was
   made through the legacy sign flip and needs re-reading against corrected
   profiles.
