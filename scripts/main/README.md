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

- **`07_figure_ep1_ep2_dynamical_composites.py`**
  Figure 7: EP1 vs EP2 dynamical composites (3×2 layout — see full description below)

### Supplementary Figures

- **`S1_figure_pca_clustering_validation.py`**  
  Figure S1: PCA and clustering validation

- **`S2_figure_selected_tracks.py`**  
  Figure S2: Selected EP1 cyclones used in the spatial structure analysis  
  *Requires: `data/era5_ep_structure/precomputed_composites_ep1.nc` (produced by `scripts/ep_structure_analysis/step3_precompute_composites.py`)*

- **`S3_figure_vertical_levels.py`**  
  Figure S3: Vertical distribution of energy conversions for EP1 cyclones  
  *Requires: `data/era5_ep_structure/precomputed_composites_ep1.nc` (produced by `scripts/ep_structure_analysis/step3_precompute_composites.py`)*

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

- Figures S2, S3, and 7 depend on outputs from the `ep_structure_analysis` pipeline (`scripts/ep_structure_analysis/`). Run steps 1–3 of that pipeline first to generate the composites in `data/era5_ep_structure/`.
- All scripts include configuration sections at the top for customizing plot parameters (colors, dimensions, labels, etc.) without modifying core logic.
- For detailed figure descriptions, methodology, and scientific interpretation, see `figures/main/README.md`.
