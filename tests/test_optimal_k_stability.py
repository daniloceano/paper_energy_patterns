"""Regression tests for the combined cluster-validity score."""

import pandas as pd

from scripts.cluster_analysis_energy_patterns.step3_optimal_k_analysis import (
    normalize_and_find_optimal_k,
)


def test_higher_reval_stability_is_preferred():
    """A converted Reval stability score is already higher-is-better."""
    raw = pd.DataFrame(
        {
            "k": [3, 4],
            "Silhouette": [0.5, 0.5],
            "Davies-Bouldin": [1.0, 1.0],
            "Calinski-Harabasz": [10.0, 10.0],
            "SF": [0.5, 0.5],
            "Gap_Statistic": [0.5, 0.5],
        }
    )

    normalized, optimal_k = normalize_and_find_optimal_k(
        raw, stability_dict={3: 0.9, 4: 0.1}
    )

    stability = normalized.set_index("k")["Stability_reval"]
    assert stability.loc[3] > stability.loc[4]
    assert optimal_k == 3
