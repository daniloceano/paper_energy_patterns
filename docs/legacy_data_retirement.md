# Retiring the legacy LEC data

Status of the migration from the legacy (article) Lorenz Energy Cycle results to
the corrected climatology maintained in
[`lec-climatology-rerun`](https://github.com/daniloceano/lec-climatology-rerun)
(LorenzCycleToolKit 2.0.0, pinned commit `d38cda7e`). The production run reached
3,820/3,820 validated cyclones on 2026-09-09.

**Policy.** The corrected rerun is the only scientific truth for this article.
The legacy artefacts were removed from this repository in October 2026. Their
*before* comparison survives only in the independent rerun repository and must
not feed any result, table or figure here. Anything else that reads them is a
defect.

---

## 1. Removed legacy artefacts

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

Built by `scripts/lec_climatology_rerun/build_*.py` in the independent rerun
repository, written into this repository's `data/corrected/`, and read through
`scripts/utils/corrected_lec.py`:

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
| `Ca` vertical sign | `Ca = -Ca_level` (`main/figure_vertical_levels.py`) | `Ca_pressure_level` integrates to `+Ca` | **Remove the flip.** Keeping it reintroduces the fixed bug with the opposite sign. |
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
on a legacy clustering. The file currently on disk is stamped with
`data/corrected/energy_cache_corrected.parquet`; the old cache and its mapping
were removed.

---

## 6. Migration completed

The October 2026 refresh rebuilt and validated the corrected cache, PCA and
clustering, Energy Pattern mapping, ERA5 structure products, LEC–field
dependence, vertical structure, and Ck decomposition. The current populations
are EP1 = 548, EP2 = 860, and EP3 = 2,412 (3,820 total).

All 13 publication figures in `figures/main/` were regenerated on `swell`.
The Ck table contains 15,280 cyclone-phase rows for all 3,820 cyclones and its
worst relative closure residual is 3.127e-10. Website figures and JSON products
were then rebuilt from the same corrected outputs.

The active scripts that need local track positions now read
`data/corrected/tracks_with_energetics_corrected.csv`. Legacy acquisition and
comparison scripts remain only as provenance and must not be used to regenerate
article outputs.

For a future refresh, run the corrected builders in `lec-climatology-rerun`,
then the cluster and downstream analysis pipelines, followed by:

```bash
python scripts/main/run_all.py
python scripts/web/prepare_site.py --skip-science --no-commit --no-upload
```

The protected `docs/energy_patterns_clim_dyn/` tree is an Overleaf backup and
is never a destination for this workflow.

---

## 7. Manuscript checks that remain in Overleaf

The computations and repository figures are current. These interpretation and
wording checks belong in the canonical Overleaf project, not its protected local
backup:

1. **Vertical extent.** Code and corrected output use 10–1000 hPa; the manuscript
   says 100–1000 hPa. Resolve in the text, not by trimming data.
2. **Ck subterm dominance.** Replace any old EP1-only percentages with the
   corrected all-pattern statistics in `results/ck_subterms_corrected/`.
3. **`Ca` sign.** Any manuscript statement about the vertical `Ca` structure was
   made through the legacy sign flip and needs re-reading against corrected
   profiles.
