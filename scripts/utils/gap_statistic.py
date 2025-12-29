"""
Gap Statistic implementation for optimal k selection.

Reference:
Tibshirani, R., Walther, G., & Hastie, T. (2001).
"Estimating the number of clusters in a data set via the gap statistic".
Journal of the Royal Statistical Society: Series B, 63(2), 411-423.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from typing import Tuple
import pandas as pd


def calculate_gap_statistic(
    X: np.ndarray,
    k_range: range,
    n_refs: int = 30,
    random_state: int = 42,
    n_init: int = 10
) -> Tuple[pd.DataFrame, int]:
    """
    Calculate Gap Statistic for a range of k values.
    
    Parameters
    ----------
    X : np.ndarray
        Data matrix (n_samples, n_features)
    k_range : range
        Range of k values to test
    n_refs : int, default=30
        Number of reference datasets to generate
    random_state : int, default=42
        Random seed for reproducibility
    n_init : int, default=10
        Number of K-Means initializations
        
    Returns
    -------
    gap_df : pd.DataFrame
        DataFrame with columns: k, gap_value, gap_std, log_wk
    optimal_k : int
        Optimal k according to Tibshirani criterion
    """
    n_samples, n_features = X.shape
    
    # Storage for results
    results = []
    
    # Calculate bounds for uniform reference distribution
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    
    rng = np.random.RandomState(random_state)
    
    for k in k_range:
        # Calculate observed WCSS (within-cluster sum of squares)
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        kmeans.fit(X)
        log_wk = np.log(kmeans.inertia_)
        
        # Generate reference datasets and calculate their WCSS
        log_wk_refs = []
        for _ in range(n_refs):
            # Generate uniform random reference data
            X_ref = rng.uniform(X_min, X_max, size=X.shape)
            
            # Cluster reference data
            kmeans_ref = KMeans(n_clusters=k, random_state=rng.randint(0, 10000), n_init=n_init)
            kmeans_ref.fit(X_ref)
            log_wk_refs.append(np.log(kmeans_ref.inertia_))
        
        # Calculate Gap statistic
        log_wk_refs = np.array(log_wk_refs)
        gap = log_wk_refs.mean() - log_wk
        
        # Calculate standard deviation with correction factor
        sd = log_wk_refs.std()
        sk = sd * np.sqrt(1 + 1/n_refs)
        
        results.append({
            'k': k,
            'gap_value': gap,
            'gap_std': sk,
            'log_wk': log_wk
        })
    
    # Create DataFrame
    gap_df = pd.DataFrame(results)
    
    # Find optimal k using Tibshirani criterion:
    # Choose smallest k such that Gap(k) >= Gap(k+1) - s_{k+1}
    optimal_k = k_range[0]
    for i in range(len(gap_df) - 1):
        gap_k = gap_df.iloc[i]['gap_value']
        gap_k_plus_1 = gap_df.iloc[i + 1]['gap_value']
        s_k_plus_1 = gap_df.iloc[i + 1]['gap_std']
        
        if gap_k >= gap_k_plus_1 - s_k_plus_1:
            optimal_k = gap_df.iloc[i]['k']
            break
    else:
        # If no k satisfies criterion, choose k with maximum Gap
        optimal_k = gap_df.loc[gap_df['gap_value'].idxmax(), 'k']
    
    return gap_df, int(optimal_k)


def plot_gap_statistic(gap_df: pd.DataFrame, optimal_k: int, ax=None):
    """
    Plot Gap Statistic with error bars.
    
    Parameters
    ----------
    gap_df : pd.DataFrame
        Output from calculate_gap_statistic
    optimal_k : int
        Optimal k value
    ax : matplotlib.axes.Axes, optional
        Axes to plot on
    """
    import matplotlib.pyplot as plt
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.errorbar(
        gap_df['k'],
        gap_df['gap_value'],
        yerr=gap_df['gap_std'],
        marker='o',
        capsize=5,
        capthick=2,
        linewidth=2,
        markersize=8,
        color='steelblue'
    )
    
    ax.axvline(optimal_k, color='red', linestyle='--', linewidth=2, 
               label=f'Optimal k = {optimal_k}')
    ax.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax.set_ylabel('Gap Statistic', fontsize=12)
    ax.set_title('Gap Statistic vs Number of Clusters', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    return ax
