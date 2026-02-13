NORMALIZATION METHODS COMPARISON
======================================================================

Generated: 2026-02-12 21:20:48.182370
Dataset: 3820 cyclones (1979-2020)


1_minmax: Min-Max Normalization
  Description: Scale each field to [0,1] then subtract
  File: 1_minmax_genesis_density.png

2_zscore: Z-Score (Standardization)
  Description: Standardize to mean=0, std=1 then subtract
  File: 2_zscore_genesis_density.png

3_fractional_weighted: Fractional Weighted Anomaly
  Description: (P_EP / P_All) - fraction_expected
  File: 3_fractional_weighted_genesis_density.png

4_kl_divergence: Kullback-Leibler Divergence
  Description: P * log(P/Q) - information surprise
  File: 4_kl_divergence_genesis_density.png

5_percentile: Rank-Based (Percentile)
  Description: Convert to percentile ranks [0,1] then subtract
  File: 5_percentile_genesis_density.png

6_dog_filter: Difference of Gaussians
  Description: Spatial bandpass filter (σ=0.5 - σ=2.0)
  File: 6_dog_filter_genesis_density.png

7_clr_compositional: CLR (Compositional Data)
  Description: Centered log-ratio transformation
  File: 7_clr_compositional_genesis_density.png

======================================================================

RECOMMENDATIONS:

1. Min-Max: Best for intuitive interpretation
2. Z-Score: Best for statistical rigor
3. Fractional Weighted: Best when considering expected frequencies
4. KL Divergence: Best for information-theoretic interpretation
5. Percentile: Best for robustness to outliers
6. DoG Filter: Best for spatial structure analysis
7. CLR: Best for compositional data theory

For publication, Min-Max or Z-Score are recommended.
