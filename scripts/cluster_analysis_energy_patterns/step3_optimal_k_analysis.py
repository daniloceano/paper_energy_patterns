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
from tqdm import tqdm
import pickle

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import local Gap Statistic implementation
from scripts.utils.gap_statistic import calculate_gap_statistic

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files (from step 1) - use absolute paths
RESULTS_DIR = PROJECT_ROOT / "results" / "cluster"
INPUT_FILE = "pca_scores.csv"  # Wide matrix format (all phases together)

# Output settings - use absolute paths
FIGURES_DIR = PROJECT_ROOT / "figures" / "cluster"
OUTPUT_FILE = "optimal_k_analysis.png"
OUTPUT_RESULTS_FILE = "optimal_k.txt"
DPI = 300

# Clustering parameters
RANDOM_STATE = 42
N_INIT = 50  # Number of K-Means initializations
K_MIN = 3  # Minimum number of clusters
K_MAX = 15  # Maximum number of clusters
N_PCS_TO_USE = None  # Number of PCs to use (None = all available)

# reval parameters
REVAL_N_FOLDS = 5  # Number of folds for cross-validation
REVAL_N_RAND = 50  # Number of random iterations
REVAL_N_ITER_CV = 10  # Number of cross-validation iterations
REVAL_TEST_SIZE = 0.30  # Train/test split ratio

# Gap statistic parameters (using local implementation)
USE_GAP_STATISTIC = True  # Always True (local implementation)
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


# Gap Statistic agora usa implementação em scripts/utils/gap_statistic.py


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
    
    for k in tqdm(k_range, desc="Computing indices", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [k={postfix}]'):
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
    
    df_results = pd.DataFrame(results)
    
    # Compute Gap Statistic (if requested)
    if use_gap:
        print("\nComputing Gap Statistic (local implementation)...")
        gap_df, optimal_k_gap = calculate_gap_statistic(
            X, 
            k_range=k_range,
            n_refs=n_refs,
            random_state=42,
            n_init=10
        )
        # Merge gap values into results
        df_results = df_results.merge(
            gap_df[['k', 'gap_value']],
            on='k',
            how='left'
        )
        df_results.rename(columns={'gap_value': 'Gap_Statistic'}, inplace=True)
        print(f"✓ Gap Statistic optimal k: {optimal_k_gap}")
    
    print()
    return df_results


def compute_reval_stability(X: np.ndarray, k_range: range,
                           n_folds: int = 5, n_rand: int = 50,
                           n_iter_cv: int = 10, test_size: float = 0.30) -> dict:
    """Compute clustering stability using reval (metodologia do notebook).
    
    Args:
        X: Data array
        k_range: Range of k values to test
        n_folds: Number of folds for cross-validation
        n_rand: Number of random iterations
        n_iter_cv: Number of cross-validation iterations
        test_size: Train/test split ratio
        
    Returns:
        Dictionary with stability values for each k
    """
    try:
        from reval.best_nclust_cv import FindBestClustCV
        
        print("=" * 70)
        print("Computing stability using reval")
        print("=" * 70)
        print(f"Testing k range: {list(k_range)}")
        
        # Split data (Reval requer train/test split)
        print(f"Splitting data (train/test = {1-test_size:.0%}/{test_size:.0%})...")
        X_train, X_test = train_test_split(X, test_size=test_size, random_state=42)
        print(f"  Train: {X_train.shape}, Test: {X_test.shape}")
        
        # Configurar objetos
        classifier = KNeighborsClassifier()
        kmeans = KMeans(random_state=42, n_init=10)
        
        # Criar objeto Reval
        reval_obj = FindBestClustCV(
            nfold=n_folds,
            nclust_range=list(k_range),
            s=classifier,
            c=kmeans,
            nrand=n_rand
        )
        
        # Executar análise com barra de progresso
        print(f"\nRunning {n_iter_cv} iterations of {n_folds}-fold CV...")
        with tqdm(total=1, desc="Reval CV", bar_format='{l_bar}{bar}| {elapsed}') as pbar:
            metrics, nbest = reval_obj.best_nclust(X_train, iter_cv=n_iter_cv)
            pbar.update(1)
        
        print(f"\n✓ Reval analysis complete!")
        print(f"  Best k suggested by Reval: {nbest}")
        
        # Extrair stability scores do cv_results_
        # ms_val = misclassification validation (menor = mais estável)
        # Converter para stability: 1 - ms_val (maior = melhor)
        stability_dict = {}
        for k in k_range:
            k_results = reval_obj.cv_results_[reval_obj.cv_results_['ncl'] == k]
            if len(k_results) > 0:
                ms_val_mean = k_results['ms_val'].mean()
                stability = 1.0 - ms_val_mean
                stability = max(0.0, min(1.0, stability))  # Garantir [0, 1]
                stability_dict[k] = stability
            else:
                stability_dict[k] = 0.5  # Default
        
        print(f"\nStability scores extracted for {len(stability_dict)} k values")
        print()
        
        return stability_dict
        
    except ImportError:
        print("⚠️  reval not available, skipping stability analysis")
        print()
        return None
    except Exception as e:
        print(f"⚠️  Error in reval analysis: {e}")
        import traceback
        traceback.print_exc()
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
    print("Step 3: Determining optimal k (Wide Matrix Format)")
    print("=" * 70)
    print(f"Results directory: {results_dir}")
    print(f"Figures directory: {figures_dir}")
    print(f"k range: {K_MIN} to {K_MAX}")
    print(f"Format: Wide matrix (all phases together)")
    print()
    
    # Load PCA scores (wide matrix format)
    scores_file = results_dir / INPUT_FILE
    print(f"Loading PCA scores from: {scores_file}")
    
    if not scores_file.exists():
        print(f"\n❌ Error: File not found: {scores_file}")
        print("Please run step1_normalize_and_pca.py first.")
        return 1
    
    df_pca = pd.read_csv(scores_file, index_col=0)
    print(f"  ✓ Loaded: {len(df_pca)} samples")
    print()
    
    # Get PC columns
    pc_cols = [col for col in df_pca.columns if col.startswith('PC')]
    if N_PCS_TO_USE is not None:
        pc_cols = pc_cols[:N_PCS_TO_USE]
    
    print(f"Using {len(pc_cols)} principal components")
    print(f"  PCs: {', '.join(pc_cols[:5])}{'...' if len(pc_cols) > 5 else ''}")
    print()
    
    X = df_pca[pc_cols].values
    k_range = range(K_MIN, K_MAX + 1)
    
    print(f"Data shape: {X.shape}")
    print(f"  Samples: {X.shape[0]}")
    print(f"  Features (PCs): {X.shape[1]}")
    print()
    
    # Compute all indices
    print("Computing cluster validity indices...")
    df_results = compute_all_indices(X, k_range, use_gap=USE_GAP_STATISTIC,
                                    n_refs=GAP_N_REFS)
    
    # Compute stability (reval)
    print("Computing stability (reval)...")
    stability_dict = compute_reval_stability(X, k_range, 
                                            n_folds=REVAL_N_FOLDS,
                                            n_rand=REVAL_N_RAND,
                                            n_iter_cv=REVAL_N_ITER_CV,
                                            test_size=REVAL_TEST_SIZE)
    
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
    print(f"Optimal k: {optimal_k}")
    print(f"Data format: Wide matrix (28 features = 7 terms × 4 phases)")
    print(f"Total samples: {len(df_pca)}")
    print()
    print("Files created:")
    print(f"  - {OUTPUT_FILE} (visualization)")
    print(f"  - {OUTPUT_RESULTS_FILE} (optimal k value)")
    print(f"  - optimal_k_raw_indices.csv")
    print(f"  - optimal_k_normalized_indices.csv")
    print()
    print("Next step:")
    print("  4. Run step4_apply_kmeans.py to cluster the data")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
