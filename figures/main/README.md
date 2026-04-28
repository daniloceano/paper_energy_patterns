# figures/main — Publication Figures

This directory contains publication-ready figures for the manuscript on energetic patterns
of South Atlantic extratropical cyclones. All figures are generated at 300 DPI by the
scripts in [`scripts/main/`](../../scripts/main/).

## Documentation

Full documentation, execution instructions, and upstream dependencies are in:

**[`scripts/main/README.md`](../../scripts/main/README.md)**

Scientific notes, variable definitions, equations, sign conventions, and literature
references are in:

**[`scripts/main/SCIENTIFIC_NOTES.md`](../../scripts/main/SCIENTIFIC_NOTES.md)**

---

## Figure Index

| File | Script | Description |
|------|--------|-------------|
| `1_tracks_genesis_frequency.png` | `01_figure_tracks_genesis_frequency.py` | Cyclone tracks by region + genesis-frequency sunburst |
| `2_20070643_lps_track_publication.png` | `02_figure_20070643_publication.py` | Case study — cyclone 20070643 LPS and track |
| `3_phase_density_2x2.png` | `03_make_phase_density_2x2.py` | Phase-space density by lifecycle phase (2×2) |
| `4_lps_combined.png` | `04_figure_lps_combined.py` | Lorenz Phase Space for EP1–EP3 (Conversion + Imports) |
| `5_ck_subterms_vertical_profiles.png` | `05_figure_ck_subterms_vertical_profiles.py` | C_K vertical profiles + integrated subterms for EP1 (barotropic instability) |
| `6_ep_intensity_seasonality_trends.png` | `06_figure_intensity_seasonality_trends.py` | EP intensity, seasonal distribution, and interannual trends |
| `7_ep_genesis_density_kde.png` | `07_figure_genesis_density_kde.py` | Genesis density using KDE (Hoskins & Hodges method) |
| `8_dynamical_composites_epall_relative.png` | `08_figure_ep1_ep2_dynamical_composites.py` | EPALL-relative dynamical composites — 3×3 layout |
| `9_pearson_epall_by_field_type.png` | `09_figure_pearson_epall_by_field_type.py` | Pearson \|r\| heatmaps by field type (AdvT, AFC, KE adv, PV200, PV850) — EPALL anomaly, canonical LEC terms |
| `S1_pca_clustering_validation.png` | `S1_figure_pca_clustering_validation.py` | PCA variance + optimal-*k* cluster validation |
| `S2_vertical_levels.png` | `S2_figure_vertical_levels.py` | Vertical Ca/Ck distributions for EP1, EP2, and EP3 cyclones |
