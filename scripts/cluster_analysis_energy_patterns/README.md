# Cluster Analysis of Cyclone Energy Patterns

**Objective:** Identify and characterize distinct energetic patterns in South Atlantic cyclones through objective clustering analysis.

---

## 📄 Scientific Documentation

**Complete methodology, results, and interpretation:**  
→ [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md)

**Generate PDF version:**
```bash
python scripts/cluster_analysis_energy_patterns/generate_scientific_notes_pdf.py
```

**Output:** `docs/scientific_notes_cluster_analysis.pdf`

**Requirements:**
- Pandoc: `brew install pandoc` (macOS) or `sudo apt install pandoc` (Linux)
- XeLaTeX: `brew install basictex` (macOS) or `sudo apt install texlive-xetex` (Linux)

---

## 🎯 Quick Summary

This analysis uses **PCA + K-Means clustering** to objectively classify South Atlantic cyclones into three distinct **Energy Patterns (EPs)** based on Lorenz Energy Cycle diagnostics.

**Key Energy Terms:**
- **Ca**: Baroclinic conversion (APE → eddy APE)
- **Ck**: Barotropic conversion (KE → eddy KE)  
- **Ge**: Eddy APE generation
- **BAe/BKe**: Boundary fluxes (energy import/export)
- **Ae/Ke**: Energy reservoirs

**Results:**
- **EP1 (11.6%)**: Strong barotropic and baroclinic conversions (mean Ck = -16.48 W m⁻²)
- **EP2 (25.6%)**: Intermediate conversions (mean Ck = -3.49 W m⁻²)
- **EP3 (62.7%)**: Weak energetics (mean Ck = -1.71 W m⁻²)

See [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) for complete analysis.

---

## 🚀 Pipeline

### Run All Steps

```bash
# Complete pipeline (Steps 1-5)
python scripts/cluster_analysis_energy_patterns/run_all.py
```

### Individual Steps

**Step 1: Normalize and PCA**
```bash
python scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py
```
- Filters cyclones with complete lifecycles (3,820 cyclones, 56.3%)
- Phase-separated PCA (97% variance retained)
- Output: `results/cluster_analysis_energy_patterns/pca_*`

**Step 2: Plot PCA Results**
```bash
python scripts/cluster_analysis_energy_patterns/step2_plot_pca_results.py
```
- PC scatter plots, loadings heatmaps, scree plots
- Output: `figures/cluster_analysis_energy_patterns/pca_*`

**Step 3: Optimal k Analysis**
```bash
python scripts/cluster_analysis_energy_patterns/step3_optimal_k_analysis.py
```
- 5 cluster validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, Gap Statistic)
- Mean normalized score → **k = 3** optimal
- Output: `figures/cluster_analysis_energy_patterns/optimal_k_*`

**Step 4: Apply K-Means**
```bash
python scripts/cluster_analysis_energy_patterns/step4_apply_kmeans.py
```
- K-Means (k=3, n_init=100) on each phase
- Centroid reconstruction to original energy space
- Output: `results/cluster_analysis_energy_patterns/kmeans_*`

**Step 5: Plot Energy Patterns**
```bash
python scripts/cluster_analysis_energy_patterns/step5_plot_energy_patterns.py
```
- Lorenz Phase Space diagrams (Conversion + Imports)
- Zoom views for detailed pattern comparison
- Output: `figures/cluster_analysis_energy_patterns/lps_*`

---

## 📊 Methodology Summary

### Data Filtering
- **Original:** 6,789 cyclones
- **Filtered:** 3,820 cyclones (complete lifecycle: incipient → intensification → mature → decay)
- **Total records:** 15,280 (3,820 × 4 phases)

### Dimensionality Reduction
- **Input:** 7 energy terms (Ca, Ck, Ge, BAe, BKe, Ae, Ke)
- **Method:** Phase-separated PCA
- **Output:** ~6 PCs per phase (97% variance)

### Clustering
- **Method:** K-Means (k=3, determined by 5 cluster validity indices)
- **Application:** Phase-separated clustering
- **Output:** 3 Energy Patterns (EP1, EP2, EP3)

### Visualization
- **Lorenz Phase Space (LPS):**  
  1. Conversion LPS: Ck (barotropic) vs Ca (baroclinic)
  2. Imports LPS: BAe (APE flux) vs BKe (KE flux)

See [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) for detailed methodology
- Quadrant analysis reveals conversion direction and efficiency
- Marker characteristics add information about energy magnitude and generation

**Why LPS instead of bar plots/heatmaps?**: 
Energy terms have fundamentally different scales and physical meanings. The Lorenz Phase Space framework provides a physically meaningful visualization that respects the relationships between energy conversions and fluxes, rather than attempting direct magnitude comparisons across disparate variables.

## Results Structure

### Data Files (39 files)

**PCA Results** (20 files):
```
results/cluster/
├── pca_scores_{phase}.csv           # PC coordinates (includes track_id)
├── pca_full_data_{phase}.csv        # Original + scaled + PCs
├── pca_models_{phase}.pkl           # PCA & StandardScaler objects
├── pca_loadings_{phase}.csv         # Variable loadings on PCs
└── pca_explained_variance_{phase}.csv  # Variance explained by each PC
```

**Optimal K Analysis** (3 files):
```
results/cluster/
├── optimal_k.txt                    # Single value: k=3
├── optimal_k_raw_indices.csv        # Raw CVI values for k=3 to 15
└── optimal_k_normalized_indices.csv # Normalized & averaged CVIs
```

**Clustering Results** (16 files):
```
results/cluster/
├── kmeans_clustered_data_{phase}.csv    # Original data + cluster labels
├── kmeans_centroids_pc_{phase}.csv      # Centroids in PC space
├── kmeans_centroids_energy_{phase}.csv  # Centroids in energy space
├── kmeans_model_{phase}.pkl             # KMeans model object
---

## 📁 Results Structure

### Data Files
```
results/cluster_analysis_energy_patterns/
├── pca_scores_{phase}.csv              # PC scores for each cyclone
├── pca_loadings_{phase}.csv            # Variable contributions to PCs
├── pca_variance_{phase}.csv            # Explained variance ratios
├── pca_models.pkl                      # Saved PCA transformations
├── optimal_k_scores.csv                # CVI scores for k=2..10
├── kmeans_clustered_data_{phase}.csv   # Cluster assignments
├── kmeans_centroids_{phase}.csv        # Cluster centroids (PC space)
├── kmeans_centroids_energy_{phase}.csv # Centroids (original energy space)
└── kmeans_summary_{phase}.csv          # Cluster statistics
```

### Figures
```
figures/cluster_analysis_energy_patterns/
├── pca/
│   ├── scatter_{phase}.png       # PC pair-wise plots
│   ├── loadings_{phase}.png      # Variable loadings heatmaps
│   └── variance_{phase}.png      # Scree plots
├── optimal_k_analysis.png        # CVI comparison (k=2..10)
└── lps_conversion_zoom.png       # Conversion LPS (Ck vs Ca)
└── lps_imports_zoom.png          # Imports LPS (BAe vs BKe)
```

---

## 📖 References

**Lorenz Energy Cycle:**
- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.

**Cluster Validation:**
- Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *J. Comput. Appl. Math.*, 20, 53-65.
- Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. *IEEE TPAMI*, 1(2), 224-227.
- Caliński, T., & Harabasz, J. (1974). A dendrite method for cluster analysis. *Comm. Stat. Theory Methods*, 3(1), 1-27.
- Tibshirani, R., Walther, G., & Hastie, T. (2001). Estimating the number of clusters via the gap statistic. *J. R. Stat. Soc. B*, 63(2), 411-423.
- Saitta, S., Raphael, B., & Smith, I. F. C. (2008). A comprehensive validity index for clustering. *Intell. Data Anal.*, 12(6), 529-548.

**South Atlantic Cyclones:**
- Reboita, M. S., et al. (2010). South Atlantic Ocean cyclogenesis climatology simulated by RegCM3. *Clim. Dyn.*, 35, 1331-1347.
- Gramcianinov, C. B., et al. (2020). Analysis of Atlantic extratropical storm tracks in 41 years of ERA5 and CFSR/CFSv2. *Ocean Eng.*, 216, 108111.

---

**Author:** Danilo Couto de Souza  
**Date:** February 2026  
**Last Updated:** February 23, 2026
