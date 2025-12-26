"""Step 3: Determine optimal number of clusters (k).

This script implements a comprehensive approach to determine the optimal k
by computing multiple cluster validity indices (CVIs) and combining them:
- Silhouette Score
- Davies-Bouldin Index
- Calinski-Harabasz Index
- Score Function (SF)
- Gap Statistic
- Stability (using reval)

All indices are normalized to [0,1] range and averaged to find the optimal k.

Note: This analysis uses ALL phases combined to determine a single optimal k
that will be applied consistently across all lifecycle phases, ensuring
physically meaningful comparisons between energy patterns.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
import pickle

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files (from step 1)
RESULTS_DIR = "results/cluster"
INPUT_PREFIX = "pca"

# Phases to load (will combine all phases for a single k determination)
PHASES = ['incipient', 'intensification', 'mature', 'decay']

# Output settings
FIGURES_DIR = "figures/cluster"
OUTPUT_FILE = "optimal_k_analysis.png"  # Single figure for all phases combined
OUTPUT_RESULTS_FILE = "optimal_k.txt"   # Single k value for all phases
DPI = 300

# Clustering parameters
K_MIN = 2  # Minimum number of clusters
K_MAX = 12  # Maximum number of clusters
N_PCS_TO_USE = None  # Number of PCs to use (None = all available)

# reval parameters
REVAL_N_FOLDS = 2  # Number of folds for cross-validation
REVAL_N_RAND = 100  # Number of random iterations
REVAL_N_ITER_CV = 10  # Number of cross-validation iterations

# Gap statistic parameters (optional - requires custom implementation)
USE_GAP_STATISTIC = False  # Set to True if gap statistic implementation available
GAP_N_REFS = 30  # Number of reference datasets for Gap statistic

# ============================================================================


def score_function(X: np.ndarray, labels: np.ndarray) -> float:
    """Compute the Score Function (SF) for clustering.
    
    Based on Saitta et al. (2008). Higher values indicate better clustering.
    Bounded in (0, 1).
    
    Args:
        X: Data array of shape (n_samples, n_features)
        labels: Cluster labels for each point
        
    Returns:
        SF value (higher is better)
    """
    X = np.asarray(X)
    labels = np.asarray(labels)
    n = len(X)
    k = len(np.unique(labels))
    
    # Overall centroid
    ztot = np.mean(X, axis=0)
    
    # bcd: weighted average squared distance from cluster centroids to overall centroid
    bcd_sum = 0
    for c in np.unique(labels):
        mask = labels == c
        nc = np.sum(mask)
        zc = np.mean(X[mask], axis=0)
        bcd_sum += nc * np.sum((zc - ztot) ** 2)
    bcd = bcd_sum / (n * k)
    
    # wcd: mean over clusters of root mean squared distance of points to their centroid
    wcd_sum = 0
    for c in np.unique(labels):
        mask = labels == c
        nc = np.sum(mask)
        zc = np.mean(X[mask], axis=0)
        wcd_sum += np.sqrt(np.sum((X[mask] - zc) ** 2) / nc)
    wcd = wcd_sum / k
    
    # Score function
    if bcd == 0 or wcd == 0:
        return 0
    return 1 / (1 + np.exp(-np.log(bcd / wcd)))


def compute_gap_statistic_simple(X: np.ndarray, k_max: int, n_refs: int = 30) -> np.ndarray:
    """Simplified Gap Statistic computation.
    
    Args:
        X: Data array
        k_max: Maximum number of clusters
        n_refs: Number of reference datasets
        
    Returns:
        Array of gap values for k=1 to k_max
    """
    n, d = X.shape
    gaps = []
    
    # Get data range for each dimension
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    
    for k in range(1, k_max + 1):
        # Compute Within-cluster sum of squares for real data
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        wk = 0
        for c in range(k):
            mask = labels == c
            if mask.sum() > 0:
                cluster_data = X[mask]
                centroid = cluster_data.mean(axis=0)
                wk += ((cluster_data - centroid) ** 2).sum()
        
        # Compute expected Wk from reference datasets
        wkbs = []
        for _ in range(n_refs):
            # Generate uniform random reference data
            X_ref = np.random.uniform(mins, maxs, size=(n, d))
            kmeans_ref = KMeans(n_clusters=k, random_state=None, n_init=5)
            labels_ref = kmeans_ref.fit_predict(X_ref)
            
            wkb = 0
            for c in range(k):
                mask = labels_ref == c
                if mask.sum() > 0:
                    cluster_data = X_ref[mask]
                    centroid = cluster_data.mean(axis=0)
                    wkb += ((cluster_data - centroid) ** 2).sum()
            wkbs.append(np.log(wkb))
        
        # Gap statistic
        gap = np.mean(wkbs) - np.log(wk)
        gaps.append(gap)
    
    return np.array(gaps)


def compute_all_indices(X: np.ndarray, k_range: range, 
                       use_gap: bool = False, n_refs: int = 30) -> pd.DataFrame:
    """Compute all cluster validity indices for a range of k.
    
    Args:
        X: Data array
        k_range: Range of k values to test
        use_gap: Whether to compute Gap statistic
        n_refs: Number of reference datasets for Gap statistic
        
    Returns:
        DataFrame with all indices
    """
    print("=" * 70)
    print("Computing cluster validity indices")
    print("=" * 70)
    print(f"Testing k from {min(k_range)} to {max(k_range)}")
    print(f"Data shape: {X.shape}")
    print()
    
    results = []
    
    for k in k_range:
        print(f"Computing indices for k={k}...", end=' ')
        
        # Fit KMeans
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = kmeans.fit_predict(X)
        
        # Compute indices
        sil = silhouette_score(X, labels)
        db = davies_bouldin_score(X, labels)
        ch = calinski_harabasz_score(X, labels)
        sf = score_function(X, labels)
        
        results.append({
            'k': k,
            'Silhouette': sil,
            'Davies-Bouldin': db,
            'Calinski-Harabasz': ch,
            'SF': sf
        })
        print("✓")
    
    # Compute Gap Statistic (if requested)
    if use_gap:
        print("\nComputing Gap Statistic...")
        gaps = compute_gap_statistic_simple(X, max(k_range), n_refs)
        for i, k in enumerate(k_range):
            results[i]['Gap_Statistic'] = gaps[k-1]  # gaps is 0-indexed
        print("✓")
    
    df_results = pd.DataFrame(results)
    print()
    return df_results


def compute_reval_stability(X: np.ndarray, k_range: range,
                           n_folds: int = 2, n_rand: int = 100,
                           n_iter_cv: int = 10) -> dict:
    """Compute clustering stability using reval.
    
    Args:
        X: Data array
        k_range: Range of k values to test
        n_folds: Number of folds for cross-validation
        n_rand: Number of random iterations
        n_iter_cv: Number of cross-validation iterations
        
    Returns:
        Dictionary with stability values for each k
    """
    try:
        from reval.best_nclust_cv import FindBestClustCV
        
        print("=" * 70)
        print("Computing stability using reval")
        print("=" * 70)
        
        classifier = KNeighborsClassifier()
        kmeans = KMeans(random_state=42, n_init=10)
        
        # Split data
        X_tr, X_ts = train_test_split(X, test_size=0.30, random_state=42)
        
        # Find best number of clusters
        findbestclust = FindBestClustCV(
            nfold=n_folds,
            nclust_range=list(k_range),
            s=classifier,
            c=kmeans,
            nrand=n_rand
        )
        
        print(f"Running cross-validation with {n_iter_cv} iterations...")
        metrics, nbest = findbestclust.best_nclust(X_tr, iter_cv=n_iter_cv)
        
        # Extract stability values (mean across iterations)
        stability_dict = {}
        for i, k in enumerate(k_range):
            # Reval returns stability metrics per k
            # Lower values indicate more stable clustering
            if hasattr(metrics, '__getitem__'):
                stability_dict[k] = np.mean(metrics[i]) if len(metrics) > i else 1.0
            else:
                stability_dict[k] = 1.0  # Default if metrics not available
        
        print(f"✓ reval analysis complete. Best k suggested: {nbest}")
        print()
        
        return stability_dict
        
    except ImportError:
        print("⚠️  reval not available, skipping stability analysis")
        print()
        return None
    except Exception as e:
        print(f"⚠️  Error in reval analysis: {e}")
        print()
        return None


def normalize_and_find_optimal_k(df_results: pd.DataFrame, 
                                 stability_dict: dict = None) -> tuple:
    """Normalize all indices and find optimal k by averaging.
    
    Args:
        df_results: DataFrame with cluster validity indices
        stability_dict: Dictionary with stability values (optional)
        
    Returns:
        Tuple of (df_normalized, optimal_k)
    """
    print("=" * 70)
    print("Normalizing indices and finding optimal k")
    print("=" * 70)
    
    df_norm = df_results.copy()
    
    # Get columns to normalize (exclude 'k')
    cols_to_normalize = [col for col in df_norm.columns if col != 'k']
    
    # Add stability if available
    if stability_dict is not None:
        df_norm['Stability_reval'] = df_norm['k'].map(stability_dict)
        cols_to_normalize.append('Stability_reval')
    
    # Min-max normalization [0, 1]
    for col in cols_to_normalize:
        min_val = df_norm[col].min()
        max_val = df_norm[col].max()
        if max_val - min_val > 0:
            df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
        else:
            df_norm[col] = 0.5
    
    # Invert indices where lower is better
    cols_invert = ['Davies-Bouldin']
    if 'Stability_reval' in df_norm.columns:
        cols_invert.append('Stability_reval')
    
    for col in cols_invert:
        if col in df_norm.columns:
            df_norm[col] = 1 - df_norm[col]
    
    # Compute mean across all indices
    metric_cols = [col for col in df_norm.columns if col != 'k']
    df_norm['mean_index'] = df_norm[metric_cols].mean(axis=1)
    
    # Find optimal k (maximum mean index)
    best_idx = df_norm['mean_index'].idxmax()
    optimal_k = int(df_norm.loc[best_idx, 'k'])
    best_mean = df_norm.loc[best_idx, 'mean_index']
    
    print(f"✓ Optimal k = {optimal_k} (mean normalized index = {best_mean:.3f})")
    print()
    
    print("Normalized index ranking:")
    df_sorted = df_norm.sort_values('mean_index', ascending=False)
    for idx, row in df_sorted.head(5).iterrows():
        print(f"  k={int(row['k']):2d}: mean={row['mean_index']:.3f}")
    print()
    
    return df_norm, optimal_k


def plot_optimal_k_analysis(df_results: pd.DataFrame, df_norm: pd.DataFrame,
                           optimal_k: int, output_file: Path, dpi: int = 300):
    """Create visualization of optimal k analysis.
    
    Args:
        df_results: DataFrame with raw indices
        df_norm: DataFrame with normalized indices
        optimal_k: Optimal k value
        output_file: Output file path
        dpi: DPI for figure
    """
    print("=" * 70)
    print("Creating optimal k visualization")
    print("=" * 70)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=dpi)
    
    # Plot 1: Raw indices
    ax = axes[0, 0]
    for col in df_results.columns:
        if col != 'k':
            ax.plot(df_results['k'], df_results[col], marker='o', label=col)
    ax.set_xlabel('Number of clusters (k)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Index value', fontsize=11, fontweight='bold')
    ax.set_title('Raw Cluster Validity Indices', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Normalized indices
    ax = axes[0, 1]
    metric_cols = [col for col in df_norm.columns if col not in ['k', 'mean_index']]
    for col in metric_cols:
        ax.plot(df_norm['k'], df_norm[col], marker='o', label=col, alpha=0.6)
    
    # Plot mean index
    ax.plot(df_norm['k'], df_norm['mean_index'], 
           marker='o', linewidth=3, markersize=8, color='black', label='Mean Index')
    
    # Highlight optimal k
    ax.axvline(optimal_k, color='red', linestyle='--', linewidth=2, 
              label=f'Optimal k={optimal_k}')
    
    optimal_mean = df_norm[df_norm['k'] == optimal_k]['mean_index'].values[0]
    ax.scatter([optimal_k], [optimal_mean], color='red', s=200, zorder=5,
              marker='*', edgecolors='darkred', linewidths=2)
    
    ax.set_xlabel('Number of clusters (k)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Normalized index (higher is better)', fontsize=11, fontweight='bold')
    ax.set_title('Normalized Indices with Mean', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)
    
    # Plot 3: Bar chart of mean index by k
    ax = axes[1, 0]
    colors = ['red' if k == optimal_k else 'steelblue' for k in df_norm['k']]
    bars = ax.bar(df_norm['k'], df_norm['mean_index'], color=colors, alpha=0.7)
    ax.set_xlabel('Number of clusters (k)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Mean normalized index', fontsize=11, fontweight='bold')
    ax.set_title('Mean Index by k (Optimal Highlighted)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    # Plot 4: Heatmap of normalized indices
    ax = axes[1, 1]
    heatmap_data = df_norm[metric_cols + ['mean_index']].T
    heatmap_data.columns = df_norm['k'].astype(int).astype(str)
    
    sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='RdYlGn', 
               vmin=0, vmax=1, center=0.5, cbar_kws={'label': 'Normalized value'},
               ax=ax, linewidths=0.5)
    
    ax.set_xlabel('Number of clusters (k)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Index', fontsize=11, fontweight='bold')
    ax.set_title('Normalized Index Heatmap', fontsize=12, fontweight='bold')
    
    # Highlight optimal k column
    optimal_col = list(heatmap_data.columns).index(str(optimal_k))
    ax.add_patch(plt.Rectangle((optimal_col, 0), 1, len(heatmap_data),
                               fill=False, edgecolor='red', linewidth=3))
    
    # Main title
    fig.suptitle(f'Optimal Number of Clusters Analysis (k = {optimal_k})',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # Save figure
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Figure saved to: {output_file}")
    print()


def save_results(df_results: pd.DataFrame, df_norm: pd.DataFrame,
                optimal_k: int, results_dir: Path):
    """Save optimal k analysis results.
    
    Args:
        df_results: DataFrame with raw indices
        df_norm: DataFrame with normalized indices
        optimal_k: Optimal k value
        results_dir: Results directory
    """
    print("=" * 70)
    print("Saving results")
    print("=" * 70)
    
    # Save raw indices
    raw_file = results_dir / "optimal_k_raw_indices.csv"
    df_results.to_csv(raw_file, index=False)
    print(f"✓ Raw indices saved to: {raw_file.name}")
    
    # Save normalized indices
    norm_file = results_dir / "optimal_k_normalized_indices.csv"
    df_norm.to_csv(norm_file, index=False)
    print(f"✓ Normalized indices saved to: {norm_file.name}")
    
    # Save optimal k
    optimal_k_file = results_dir / OUTPUT_RESULTS_FILE
    with open(optimal_k_file, 'w') as f:
        f.write(f"{optimal_k}\n")
    print(f"✓ Optimal k saved to: {optimal_k_file.name}")
    print()


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    figures_dir = Path(FIGURES_DIR)
    
    print("=" * 70)
    print("Step 3: Determining optimal k for all phases combined")
    print("=" * 70)
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"Number of phases to load: {len(PHASES)}")
    print(f"k range: {K_MIN} to {K_MAX}")
    print()
    
    # Load and combine PCA scores from all phases
    print("Loading PCA scores from all phases...")
    all_data = []
    phase_info = []
    
    for phase in PHASES:
        scores_file = results_dir / f"{INPUT_PREFIX}_scores_{phase}.csv"
        df_phase = pd.read_csv(scores_file)
        
        # Add phase information for reference
        df_phase['phase'] = phase
        all_data.append(df_phase)
        phase_info.append(f"  - {phase.title():16s}: {len(df_phase):5d} samples")
        
        print(f"  ✓ Loaded {phase}: {len(df_phase)} samples")
    
    # Combine all phases
    df_combined = pd.concat(all_data, ignore_index=True)
    print()
    print(f"Total combined samples: {len(df_combined)}")
    print()
    
    # Get PC columns
    pc_cols = [col for col in df_combined.columns if col.startswith('PC')]
    if N_PCS_TO_USE is not None:
        pc_cols = pc_cols[:N_PCS_TO_USE]
    
    print(f"Using {len(pc_cols)} principal components: {pc_cols}")
    print()
    
    X = df_combined[pc_cols].values
    k_range = range(K_MIN, K_MAX + 1)
    
    # Compute all indices
    print("Computing cluster validity indices on combined data...")
    df_results = compute_all_indices(X, k_range, use_gap=USE_GAP_STATISTIC,
                                    n_refs=GAP_N_REFS)
    
    # Compute stability (reval)
    print("Computing stability (reval) on combined data...")
    stability_dict = compute_reval_stability(X, k_range, 
                                            n_folds=REVAL_N_FOLDS,
                                            n_rand=REVAL_N_RAND,
                                            n_iter_cv=REVAL_N_ITER_CV)
    
    # Normalize and find optimal k
    print("Normalizing indices and finding optimal k...")
    df_norm, optimal_k = normalize_and_find_optimal_k(df_results, stability_dict)
    
    # Plot results
    output_file = figures_dir / OUTPUT_FILE
    print("Creating visualization...")
    plot_optimal_k_analysis(df_results, df_norm, optimal_k, output_file, dpi=DPI)
    
    # Save results
    save_results(df_results, df_norm, optimal_k, results_dir)
    
    # Print summary
    print("=" * 70)
    print("✅ Step 3 complete!")
    print("=" * 70)
    print(f"Optimal k (for all phases): {optimal_k}")
    print()
    print("Phase distribution:")
    for info in phase_info:
        print(info)
    print()
    print("Next step:")
    print("  4. Run step4_apply_kmeans.py to cluster the data")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
