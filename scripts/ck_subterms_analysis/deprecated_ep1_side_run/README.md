# Deprecated — EP1-only Ck side run

**Do not run anything in this directory.**

These scripts drove a dedicated LorenzCycleToolKit run over the 444 EP1
cyclones, the only way to obtain the `Ck` decomposition when the article's
archived results carried the total term alone. They wrote into
`results/ck_analysis/` and `figures/ck_subterms/`.

They are superseded on two counts:

1. **Coverage.** The corrected climatology rerun
   (`scripts/lec_climatology_rerun`) computes `Ck_1` … `Ck_5` for all 3,820
   cyclones, so the decomposition exists for EP1, EP2, EP3 and EPALL without
   any further ERA5 download or toolkit execution.
2. **Correctness.** That side run predates the LorenzCycleToolKit 2.0.0
   corrections. Its outputs in `results/ck_analysis/` carry the superseded
   equations and must not reach the article.

The replacement is `scripts/ck_subterms_analysis/`, which reads the rerun
products through `scripts/utils/corrected_lec.py` and writes to
`results/ck_subterms_corrected/` and `figures/ck_subterms_corrected/`.

The files are kept only as a record of how the EP1 numbers quoted in earlier
drafts were produced.
