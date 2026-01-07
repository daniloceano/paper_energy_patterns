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

Five complementary indices are computed to objectively determine the optimal number of clusters:

1. **Silhouette Coefficient** (Rousseeuw, 1987)
   - **Range**: [-1, 1] (higher is better)
   - **Measures**: Balance between intra-cluster cohesion and inter-cluster separation
   - **Interpretation**: Values near +1 indicate well-separated clusters; near 0 indicates overlapping clusters; negative values indicate misclassification
   - **Formula**: $s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$ where $a(i)$ is mean intra-cluster distance and $b(i)$ is mean nearest-cluster distance
   - **Reference**: Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65.

2. **Davies-Bouldin Index** (Davies & Bouldin, 1979)
   - **Range**: [0, ∞) (lower is better)
   - **Measures**: Average similarity ratio between each cluster and its most similar cluster
   - **Interpretation**: Lower values indicate better cluster separation and compactness
   - **Formula**: $DB = \frac{1}{k}\sum_{i=1}^{k}\max_{j\neq i}\left(\frac{\sigma_i + \sigma_j}{d(c_i, c_j)}\right)$ where $\sigma_i$ is within-cluster scatter and $d(c_i, c_j)$ is between-centroid distance
   - **Reference**: Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 1(2), 224-227.

3. **Calinski-Harabasz Index** (Variance Ratio Criterion) (Caliński & Harabasz, 1974)
   - **Range**: [0, ∞) (higher is better)
   - **Measures**: Ratio of between-cluster variance to within-cluster variance
   - **Interpretation**: Higher values indicate denser, well-separated clusters
   - **Formula**: $CH = \frac{\text{trace}(B_k)}{\text{trace}(W_k)} \times \frac{n-k}{k-1}$ where $B_k$ is between-cluster dispersion matrix and $W_k$ is within-cluster dispersion
   - **Reference**: Caliński, T., & Harabasz, J. (1974). A dendrite method for cluster analysis. *Communications in Statistics - Theory and Methods*, 3(1), 1-27.

4. **Score Function (SF)** (Saitta et al., 2008)
   - **Range**: (0, 1) (higher is better)
   - **Measures**: Logarithmic ratio of between-cluster to within-cluster distances, bounded by sigmoid function
   - **Interpretation**: Balances cluster compactness and separation in a normalized scale
   - **Formula**: $SF = \frac{1}{1 + e^{-\ln(bcd/wcd)}}$ where $bcd$ is between-cluster distance and $wcd$ is within-cluster distance
   - **Reference**: Saitta, S., Raphael, B., & Smith, I. F. C. (2008). A comprehensive validity index for clustering. *Intelligent Data Analysis*, 12(6), 529-548.

5. **Gap Statistic** (Tibshirani et al., 2001)
   - **Range**: [0, ∞) (higher is better)
   - **Measures**: Compares within-cluster dispersion to that expected under null reference distribution
   - **Interpretation**: Optimal k maximizes the gap between observed and expected dispersion
   - **Formula**: $\text{Gap}(k) = E_n^*[\log(W_k)] - \log(W_k)$ where $E_n^*$ is expectation under null (uniform) distribution and $W_k$ is pooled within-cluster sum of squares
   - **Reference**: Tibshirani, R., Walther, G., & Hastie, T. (2001). Estimating the number of clusters in a data set via the gap statistic. *Journal of the Royal Statistical Society: Series B (Statistical Methodology)*, 63(2), 411-423.

**Integration Method**:
- All indices normalized to [0,1] range using min-max scaling: $\text{normalized} = \frac{x - \min}{\max - \min}$
- Indices where "lower is better" (Davies-Bouldin) are inverted: $\text{inverted} = 1 - \text{normalized}$
- Mean index computed as unweighted average across all normalized CVIs
- Optimal k selected by maximizing mean normalized index
- Multiple indices approach reduces bias from any single criterion and provides robust validation

**Result**: **k = 3** clusters identified as optimal for the combined dataset

**Methodological Rationale**: The convergence of five independent validation criteria on k=3 provides strong statistical evidence for three distinct energy patterns in the dataset, minimizing the subjectivity inherent in selecting a single validation metric.

### Step 4: K-Means Clustering Application

**Objective**: Assign each cyclone observation to one of the identified energy patterns.

**Procedure**:
1. **Phase-Separated Clustering**: K-Means applied independently to each phase's PC space
   - Uses k=3 (determined from Step 3) for all phases
   - Ensures consistency while respecting phase-specific variance structures
   
2. **Centroid Calculation**: Cluster centroids computed in both:
   - PC space (for algorithmic purposes)
   - Original energy space (for physical interpretation via inverse PCA transformation)

3. **Multiple Initializations**: n_init=100 ensures stable convergence to global optimum

**Cluster Distribution by Phase**:
- Distribution statistics saved in `kmeans_summary_{phase}.csv`
- Cluster proportions vary across lifecycle phases
- Energy Pattern membership tracked through cyclone evolution

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

1. **Three Distinct Energy Patterns**: Objective analysis using five independent cluster validity indices identifies k=3 as optimal, indicating three archetypal energy configurations in South Atlantic cyclones

2. **Phase-Dependent Distribution**: Cluster membership varies systematically through lifecycle phases, with detailed statistics available in phase-specific summary files

3. **Objective Classification**: Multi-index validation approach provides robust, reproducible classification independent of subjective interpretation

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

### Theoretical Framework
- Lorenz, E. N. (1955). Available potential energy and the maintenance of the general circulation. *Tellus*, 7(2), 157-167. https://doi.org/10.3402/tellusa.v7i2.8796

### Cluster Validity Indices
- Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65. https://doi.org/10.1016/0377-0427(87)90125-7
- Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 1(2), 224-227. https://doi.org/10.1109/TPAMI.1979.4766909
- Caliński, T., & Harabasz, J. (1974). A dendrite method for cluster analysis. *Communications in Statistics - Theory and Methods*, 3(1), 1-27. https://doi.org/10.1080/03610927408827101
- Saitta, S., Raphael, B., & Smith, I. F. C. (2008). A comprehensive validity index for clustering. *Intelligent Data Analysis*, 12(6), 529-548. https://doi.org/10.3233/IDA-2008-12604
- Tibshirani, R., Walther, G., & Hastie, T. (2001). Estimating the number of clusters in a data set via the gap statistic. *Journal of the Royal Statistical Society: Series B (Statistical Methodology)*, 63(2), 411-423. https://doi.org/10.1111/1467-9868.00293

## Authors & Contact

Danilo Couto de Souza  
danilo.oceano@gmail.com

---

*Last updated: January 2026*

---

## Troubleshooting

### "Optimal k file not found"
Make sure to run step 3 before step 4.

### "PCA models not available"
Step 1 must complete successfully to generate the models file.

### "reval not available"
The reval package is optional. If not installed, step 3 will skip stability analysis and use the five primary indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, and Gap Statistic).

### "lorenz-phase-space not available"
The lorenz-phase-space package is optional. Step 5 will use simplified Lorenz diagrams if the package is not available.

### Memory issues
If you encounter memory errors, reduce `REVAL_N_RAND` in step 3 or `N_INIT` in step 4.

---

## Contact

For questions or issues with the cluster analysis pipeline, please refer to the main project README or contact the authors.
