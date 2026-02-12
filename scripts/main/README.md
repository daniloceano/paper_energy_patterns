# Main Figure Scripts

This directory contains scripts for generating publication-ready figures used in the Energy Patterns manuscript. Each script produces figure(s) formatted according to Scientific Reports guidelines (300 DPI, specific dimensions, consistent styling).

## Script Organization

Scripts are numbered according to the order of figures in the manuscript:

### Main Figures

- **`01_figure_tracks_genesis_frequency.py`**  
  Figure 1: Study area and workflow overview

- **`02_figure_20070643_publication.py`**  
  Figure 2: Case study — Cyclone 20070643 energetics and trajectory

- **`03_make_phase_density_2x2.py`**  
  Figure 3: Phase space density distributions (2×2 layout)

- **`04_figure_lps_combined.py`**  
  Figure 4: Lorenz Phase Space for Energy Patterns (EP1–EP3)

- **`05_figure_intensity_seasonality_trends.py`**  
  Figure 5: Energy Pattern characteristics (intensity, seasonality, trends)

- **`06_figure_genesis_density_kde.py`**  
  Figure 6: Genesis density using Kernel Density Estimation (Hoskins & Hodges method)

- **`07_figure_ep1_instability_composite.py`**  
  Figure 7: EP1 instability composite (4×3 layout: RK, PV, EGR diagnostics)

### Supplementary Figures

- **`S1_figure_pca_clustering_validation.py`**  
  Figure S1: PCA and clustering validation

- **`S2_figure_selected_tracks.py`**  
  Figure S2: Selected EP1 cyclones for instability analysis  
  *Requires: `scripts/ep1_ibc_ibt_analysis/step1_select_cases.py` (run first)*

- **`S3_figure_vertical_levels.py`**  
  Figure S3: Vertical distribution of energy conversions  
  *Requires: `scripts/ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py` (run first)*

## Usage

Each script can be executed independently:

```bash
python scripts/main/01_figure_tracks_genesis_frequency.py
python scripts/main/02_figure_20070643_publication.py
# ... etc.
```

Or generate all figures sequentially:

```bash
python scripts/main/run_all.py
```

## Dependencies

All figure scripts require:
- Processed track data: `data/tracks_SAt_filtered_with_energetics_processed.csv`
- Clustering results: `results/cluster/kmeans_clustered_data.csv`

Some scripts have additional requirements (see individual script headers for details).

## Outputs

Generated figures are saved to: `figures/main/`

## Notes

- Figures S2 and S3 depend on outputs from the EP1 instability analysis pipeline (`scripts/ep1_ibc_ibt_analysis/`). Run those preprocessing steps first before generating these supplementary figures.
- All scripts include configuration sections at the top for customizing plot parameters (colors, dimensions, labels, etc.) without modifying core logic.
- For detailed figure descriptions, methodology, and scientific interpretation, see `figures/main/README.md`.
