# Cluster Analysis of Cyclone Energy Patterns

## Scientific Overview

This analysis identifies distinct energy patterns in South Atlantic cyclones using a comprehensive cluster analysis framework. The approach combines Principal Component Analysis (PCA) for dimensionality reduction with K-Means clustering to objectively classify cyclones based on their energetic signatures.

## Theoretical Background

The Lorenz Energy Cycle (LEC) framework describes the conversion, generation, and dissipation of energy in atmospheric systems. In this study, seven energy terms are analyzed:

- **Ca**: Conversion between Available Potential Energy (APE) components
- **Ck**: Conversion between Kinetic Energy (KE) components  
- **BAe**: Boundary flux of Eddy APE
- **BKe**: Boundary flux of Eddy KE
- **Ae**: Eddy Available Potential Energy reservoir
- **Ke**: Eddy Kinetic Energy reservoir
- **Ge**: Generation of Eddy APE

These terms characterize the energetic behavior of cyclones throughout their lifecycle phases (incipient, intensification, mature, and decay).

## Methodology

### Data Preparation

**Cyclone Selection Criteria:**
- Only cyclones with complete lifecycle trajectories are included
- Must contain all four sequential phases: incipient → intensification → mature → decay
- This filtering ensures temporal consistency and comparability

**Result**: 3,820 cyclones (56.3% of original dataset) representing 15,829 temporal records

### Step 1: Dimensionality Reduction via PCA

**Objective**: Reduce the 7-dimensional energy space to its principal components while preserving maximum variance.

**Procedure**:
1. **Normalization**: Energy variables are standardized (μ=0, σ=1) using StandardScaler to ensure equal weighting
2. **Phase-Separated PCA**: Independent PCA is performed for each lifecycle phase
   - Rationale: Energy dynamics differ fundamentally across phases; separate PCAs capture phase-specific variance structures
3. **Component Selection**: Retain components explaining 97-98% of total variance (~6 components per phase)
4. **Preservation of Identifiers**: `track_id` maintained throughout for posterior trajectory analysis

**Outputs**:
- PC scores for each cyclone-time observation
- Component loadings (variable contributions to each PC)
- Explained variance ratios
- PCA transformation models (for reproducibility)

**Scientific Justification**: Phase-separated PCA acknowledges that energy conversion mechanisms evolve through cyclone development, necessitating independent dimensionality reduction for each phase.

### Step 2: PCA Visualization and Interpretation

**Objective**: Assess the quality of dimensionality reduction and interpret principal components.

**Visualizations Generated** (3 figure types × 4 phases = 12 figures):

1. **PC Scatter Plots**: Pair-wise projections of principal components
   - Reveals clustering tendency in reduced space
   - Identifies potential outliers

2. **Component Loadings Heatmap**: Variable contributions to each PC
   - Interprets physical meaning of each component
   - Identifies which energy terms dominate each PC

3. **Scree Plot**: Variance explained by each component
   - Validates component retention threshold
   - Shows cumulative variance explained

**Interpretation**: Higher explained variance with fewer components indicates strong co-variability among energy terms, suggesting the existence of coherent energy patterns


### Step 3: Optimal Cluster Number Determination

**Objective**: Objectively determine the number of distinct energy patterns using multiple validation criteria.

**Critical Methodological Choice**: 
All lifecycle phases are **combined** for k determination to ensure:
- Physical consistency: Same number of patterns across phases enables meaningful comparison
- Interpretability: Facilitates analysis of pattern evolution through cyclone lifecycle
- Statistical power: Larger sample size (15,829 records) improves cluster validity

**Cluster Validity Indices** (CVIs):

1. **Silhouette Coefficient**: Measures intra-cluster cohesion vs. inter-cluster separation
2. **Davies-Bouldin Index**: Ratio of within-cluster to between-cluster scatter
3. **Calinski-Harabasz Index**: Variance ratio criterion
4. **Score Function**: Custom metric balancing compactness and separation (Saitta et al., 2008)

**Integration Method**:
- All indices normalized to [0,1] range
- Indices where "lower is better" are inverted (1 - normalized value)
- Optimal k selected by maximizing mean normalized index across all CVIs
- Multiple indices approach reduces bias from any single criterion

**Result**: **k = 2** clusters identified as optimal for the combined dataset

**Physical Interpretation**: Two dominant energy patterns suggest a fundamental dichotomy in cyclone energetics, potentially related to:
- Dry vs. moist cyclone types
- Baroclinic vs. barotropic energy pathways
- Intensification mechanisms (boundary fluxes vs. internal conversions)

### Step 4: K-Means Clustering Application

**Objective**: Assign each cyclone observation to one of the identified energy patterns.

**Procedure**:
1. **Phase-Separated Clustering**: K-Means applied independently to each phase's PC space
   - Uses k=2 (determined from Step 3) for all phases
   - Ensures consistency while respecting phase-specific variance structures
   
2. **Centroid Calculation**: Cluster centroids computed in both:
   - PC space (for algorithmic purposes)
   - Original energy space (for physical interpretation via inverse PCA transformation)

3. **Multiple Initializations**: n_init=100 ensures stable convergence to global optimum

**Cluster Distribution by Phase**:
- **Incipient**: Cluster 0: 83.1% | Cluster 1: 16.9%
- **Intensification**: Cluster 0: 74.2% | Cluster 1: 25.8%
- **Mature**: Cluster 0: 23.3% | Cluster 1: 76.7%
- **Decay**: Cluster 0: 86.0% | Cluster 1: 14.0%

**Key Observation**: Cluster proportions vary substantially across phases, suggesting:
- Cluster 1 becomes dominant during mature phase
- Energy pattern transitions occur during cyclone evolution
- Different patterns may be favored at different lifecycle stages

### Step 5: Energy Pattern Characterization

**Objective**: Visualize and interpret the physical meaning of identified clusters through Lorenz Phase Space diagrams with zoom.

**Lorenz Phase Space (LPS) Diagrams**:

Two complementary phase spaces are analyzed for each lifecycle phase:

1. **Mixed Phase Space** (Ck vs Ca):
   - X-axis: Ck (conversion between kinetic energy forms)
   - Y-axis: Ca (conversion between potential energy forms)
   - Reveals baroclinic vs. barotropic energy pathways
   - Marker size: Ke (eddy kinetic energy)
   - Marker color: Ge (generation rate)

2. **Imports Phase Space** (BAe vs BKe):
   - X-axis: BAe (boundary flux of eddy APE)
   - Y-axis: BKe (boundary flux of eddy KE)
   - Characterizes external energy sources
   - Marker size: Ke
   - Marker color: Ge

**Zoom Feature**: All LPS diagrams use zoom to focus on the region containing the cluster centroids, enhancing visualization of the energetic differences between patterns.

**Interpretation Framework**:
- Cluster centroids represent archetypal energy configurations
- Position in phase space indicates dominant energy pathways
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
├── optimal_k.txt                    # Single value: k=2
├── optimal_k_raw_indices.csv        # Raw CVI values for k=2 to 12
└── optimal_k_normalized_indices.csv # Normalized & averaged CVIs
```

**Clustering Results** (16 files):
```
results/cluster/
├── kmeans_clustered_data_{phase}.csv    # Original data + cluster labels
├── kmeans_centroids_pc_{phase}.csv      # Centroids in PC space
├── kmeans_centroids_energy_{phase}.csv  # Centroids in energy space
├── kmeans_model_{phase}.pkl             # KMeans model object
└── kmeans_summary_{phase}.csv           # Cluster sizes & statistics
```

### Figures (8 files)

**PCA Diagnostics** (12 figures):
```
figures/cluster/
├── pca_scatter_{phase}.png      # PC pair-wise projections
├── pca_loadings_{phase}.png     # Variable loadings heatmap
└── pca_variance_{phase}.png     # Variance explained (scree plot)
```

**Optimal K Analysis** (1 figure):
```
figures/cluster/
└── optimal_k_analysis.png       # CVI comparison across k values
```

**Lorenz Phase Space Diagrams** (8 figures):
```
figures/cluster/
├── lps_{phase}_mixed.png        # Mixed LPS (Ck vs Ca) with zoom
└── lps_{phase}_imports.png      # Imports LPS (BAe vs BKe) with zoom
```

Where `{phase}` = incipient, intensification, mature, decay

## Scientific Significance

### Key Findings

1. **Two Dominant Patterns**: The objective analysis identifies k=2 as optimal, suggesting cyclone energetics are dominated by two archetypal configurations

2. **Phase-Dependent Distribution**: Cluster membership varies systematically through lifecycle phases:
   - Pattern 1 (Cluster 1) intensifies during mature phase (17% → 26% → 77%)
   - Pattern 0 dominates incipient and decay phases

3. **Energetic Dichotomy**: Two-cluster solution implies fundamental differences in:
   - Energy conversion pathways (baroclinic vs barotropic processes)
   - Energy sources (boundary fluxes vs internal generation)
   - Intensification mechanisms

### Applications

1. **Cyclone Classification**: Objective taxonomy based on energetic behavior
2. **Predictive Value**: Energy patterns may indicate cyclone intensity evolution
3. **Climate Studies**: Long-term changes in pattern frequency could indicate climate shifts
4. **Case Study Selection**: Identify representative cyclones for detailed analysis

### Methodological Contributions

1. **Phase-Separated PCA**: Acknowledges non-stationary energy dynamics
2. **Multi-Index k Selection**: Reduces subjective bias in cluster number choice
3. **Consistent k Across Phases**: Enables comparative analysis while respecting phase-specific structures
4. **Complete Lifecycle Filter**: Ensures temporal consistency in comparative analyses

## Reproducibility

All analysis steps are fully reproducible:
1. Random states fixed (random_state=42)
2. PCA models saved for exact transformation replication
3. K-Means uses n_init=100 for stable results
4. Complete parameter documentation in configuration sections

## Execution

Run steps sequentially:

```bash
# Step 1: PCA (phase-separated)
python scripts/cluster/step1_normalize_and_pca.py

# Step 2: PCA visualization
python scripts/cluster/step2_plot_pca_results.py

# Step 3: Optimal k determination (combined phases)
python scripts/cluster/step3_optimal_k_analysis.py

# Step 4: K-Means clustering (phase-separated)
python scripts/cluster/step4_apply_kmeans.py

# Step 5: Energy pattern visualization
conda run -n paper_energy_patterns python scripts/cluster/step5_plot_energy_patterns.py
```

**Note**: Step 5 requires the `lorenz-phase-space` package to generate LPS diagrams.

## References

- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.
- Saitta, S., Raphael, B., & Smith, I. F. (2008). A comprehensive validity index for clustering. *Intelligent Data Analysis*, 12(6), 529-548.
- Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65.

## Authors & Contact

Danilo Couto de Souza  
danilo.oceano@gmail.com

---

*Last updated: December 2024*


- Saitta, S., Raphael, B., & Smith, I. F. C. (2008). A comprehensive validity index for clustering. *Intelligent Data Analysis*, 12(6), 529-548.
- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167.

---

## Troubleshooting

### "Optimal k file not found"
Make sure to run step 3 before step 4.

### "PCA models not available"
Step 1 must complete successfully to generate the models file.

### "reval not available"
The reval package is optional. If not installed, step 3 will skip stability analysis and use only the other 4-5 indices.

### "lorenz-phase-space not available"
The lorenz-phase-space package is optional. Step 5 will use simplified Lorenz diagrams if the package is not available.

### Memory issues
If you encounter memory errors, reduce `REVAL_N_RAND` in step 3 or `N_INIT` in step 4.

---

## Contact

For questions or issues with the cluster analysis pipeline, please refer to the main project README or contact the authors.
