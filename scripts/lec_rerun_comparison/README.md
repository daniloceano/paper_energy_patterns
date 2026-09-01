# Legacy vs corrected LEC comparison

Compares the published Lorenz Energy Cycle climatology against the corrected
rerun produced by [`scripts/lec_climatology_rerun`](../lec_climatology_rerun),
so the effect of the LorenzCycleToolKit 2.0.0 correction can be judged before
any downstream product (PCA, k-means, EP figures) is regenerated.

The comparison runs while the rerun is still in progress: it uses whatever
cyclones are already in state `COMPLETE` and can be re-run at any time.

## What is compared, and why it is a fair comparison

Both sides are phase means of the same quantity for the same cyclones:

| | legacy | corrected |
|---|---|---|
| source | `data/energy_cache.parquet` | `<run-root>/lec_results/<id>_ERA5_track/` |
| toolkit | LorenzCycleToolKit pre-2.0.0 | pinned commit containing the 2.0.0 correction |
| lifecycle windows | article windows (Zenodo 10.5281/zenodo.18243447) | the same windows, frozen by `prepare.py` |
| time steps | 3-hourly | the same 3-hourly steps |
| control volume | 15° × 15° moving box, 32 levels (10–1000 hPa) | identical |

Pairs are matched on `(track_id, period)`, so secondary periods (`decay 2`)
match their own counterpart; `residual` rows are dropped, as in the rerun cache
builder. Step 1 additionally re-aggregates a random sample of the archived
Zenodo results and confirms that `energy_cache.parquet` is exactly that
aggregation (agreement to ~1e-14), which is what makes the two sides
comparable. Every remaining difference comes from the equation and numerical
correction alone.

## Running it

From the repository root, in the `paper_energy_patterns` environment, on the
server that hosts the run root:

```bash
conda run --no-capture-output -n paper_energy_patterns \
  python scripts/lec_rerun_comparison/run_all.py
```

Individual steps, in execution order:

| Step | Script | Produces |
|---|---|---|
| 1 | `step1_build_comparison_table.py` | `results/lec_rerun_comparison/paired_terms.parquet`, `corrected_phase_means.parquet`, `coverage.json` |
| 2 | `step2_plot_split_violins.py` | `figures/lec_rerun_comparison/violin_<group>.png`, `signflip_heatmap.png` |
| 3 | `step3_summary_stats.py` | `term_change_summary.csv`, `term_change_by_phase.csv`, `conversion_regime.csv` |
| 5 | `step5_plot_lec_diagram.py` | `figures/lec_rerun_comparison/lec_diagram_before_after.png` |
| 6 | `step6_plot_eof_diagram.py --eof 1..4` | `figures/lec_rerun_comparison/eof<N>_diagram_before_after.png`, `eof_loadings.csv`, `eof_variance.csv` |
| 4 | `step4_write_report.py` | `docs/lec_rerun_comparison_report.md` |
| 7 | `step7_build_report_pdf.py` | `docs/lec_rerun_comparison_report.pdf` |

Steps 5 and 6 run before step 4 so that the report can point at figures that
exist; step 7 runs after it. Steps 5 and 6 draw through `lec_diagram.py`, which
holds the shared geometry.

Step 7 produces the version to circulate: the Markdown report with the figures
embedded, rendered to a single PDF. There is no pandoc or LaTeX in this
environment, so it is built with ReportLab (`pip install reportlab`) over the
subset of Markdown the report uses, with DejaVu taken from matplotlib so the LEC
symbols survive. Only the figures that carry a result are embedded — the
conversion, boundary and residual violins, the sign-change heatmap, the LEC
diagram and the EOF 1 diagram; the unchanged violins and the EOF 2-4 diagrams
are referenced by path.

Step 1 caches the corrected phase means and only reads the cyclones it has not
seen yet, so repeated runs are cheap; `--refresh` forces a full rebuild. Step 4
regenerates the report entirely from the step 1 and 3 tables, so the report
text follows the data rather than the other way round.

## Reading the figures

One figure per LEC term family. Each panel is one term; within a panel the
x-axis is the life-cycle phase and every violin is split — **left half legacy,
right half corrected**, from the same cyclone-phase samples. Dotted lines are
quartiles, the dashed horizontal line is zero. Distributions are trimmed to a
symmetric percentile window for display (`--trim`, default 2.5); the share of
samples outside the window is annotated in each panel. Trimming never affects
the statistics in step 3.

`lec_diagram_before_after.png` is the classical four-box Lorenz diagram, one
panel per phase, drawn with the geometry and conventions of `plot_LEC.py` in the
thesis repository (`daniloceano/danilo_thesis_iag`,
`manuscript_lec_climatology`): boxes are the budget tendencies, each arrow points
in the direction the energy actually flows, and thickness scales with |median|.
Where a term changed, the arrow is **doubled** — dark is the legacy value, red is
the corrected one — so a reversal such as `Ck` during the incipient and
intensification phases shows up as two arrows pointing at each other. Colour
encodes the version here, not the sign. `BΦZ`, `BΦE`, `RGz` and `RGe` have no
place in the classical diagram and are given in the figure footnote instead.

`eof1_diagram_before_after.png` is the same diagram carrying EOF 1 loadings
instead of medians, replicating `plot_LEC_eofs.py` of the thesis. The EOFs are
the eigenvectors of the correlation matrix of the 24 standardised terms, scaled
by the square root of their eigenvalue, exactly as in
`eof_analysis_with_track_id.py` of `energetic_patterns_cyclones_south_atlantic`;
the implementation reproduces the published `eofs.csv` and variance fractions to
~1e-4. Both versions are recomputed on the paired sample so they differ only by
the correction, which is why the legacy explained variances are close to, but
not identical to, the published ones. EOF signs are arbitrary, so the legacy
mode is oriented to make its largest loading positive — which reproduces the
published EOF 1 orientation in all four phases — and the corrected mode is then
aligned to it. `run_all.py` produces modes 1 to 4, matching Figures 5 to 8 of the
Clim. Dyn. article; `--tol` sets how large a loading change has to be before the
arrow is doubled.

Rank is not stable for the higher modes: EOF 2 and EOF 3 explain similar
variance, and the correction is enough to swap them in some phases. Corrected
modes are therefore matched to legacy modes by maximum absolute pattern
correlation (one to one, over the first eight modes) rather than by rank. When
the match is not rank-preserving the panel says so — "(corrected mode 3)" — and
`eof_variance.csv` carries `corrected_mode_rank` and `rank_swapped`.

`signflip_heatmap.png` gives the percentage of cyclone-phases whose term changed
sign between the two versions — the change that alters the physical reading of
the energy cycle rather than just its magnitude.

## Notes

- Requires the rerun state database, so it must run on the server holding
  `--run-root` (default `/p1-swell/danilocs/lec_climatology_corrected_v2`).
- `C_overturning` and `M` exist only in the corrected output and are reported in
  `coverage.json` rather than paired.
- Sign convention follows de Souza et al. (2025): `Ca` > 0 feeds eddy APE,
  `Ck` < 0 feeds eddy KE, `B*` > 0 is import into the domain.
