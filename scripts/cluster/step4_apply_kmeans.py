"""Step 4: Apply K-Means clustering with optimal k.

This script applies K-Means clustering to the PCA-transformed data using
the optimal k determined in step 3. It saves cluster labels and centroids.
"""

from __future__ import annotations

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import pickle

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input files (from previous steps)
RESULTS_DIR = "results/cluster"
INPUT_PREFIX = "pca"
OPTIMAL_K_FILE = "optimal_k.txt"

# Phases to cluster (will use same k for all phases)
PHASES = ['incipient', 'intensification', 'mature', 'decay']

# K-Means parameters
USE_OPTIMAL_K = True  # If False, use MANUAL_K
MANUAL_K = 4  # Manual k value (if USE_OPTIMAL_K is False)
N_PCS_TO_USE = None  # Number of PCs to use (None = all available)
RANDOM_STATE = 42
N_INIT = 100  # Number of initializations (more = more stable)

# Output prefix
OUTPUT_PREFIX = "kmeans"

# ============================================================================


def load_optimal_k(results_dir: Path, optimal_k_file: str) -> int:
    """Load optimal k from file.
    
    Args:
        results_dir: Results directory
        optimal_k_file: Filename containing optimal k
        
    Returns:
        Optimal k value
    """
    optimal_k_path = results_dir / optimal_k_file
    if not optimal_k_path.exists():
        raise FileNotFoundError(
            f"Optimal k file not found: {optimal_k_path}\n"
            "Please run step3_optimal_k_analysis.py first."
        )
    
    with open(optimal_k_path, 'r') as f:
        optimal_k = int(f.read().strip())
    
    return optimal_k


def apply_kmeans(X: np.ndarray, k: int, random_state: int = 42,
                n_init: int = 100) -> tuple:
    """Apply K-Means clustering.
    
    Args:
        X: Data array
        k: Number of clusters
        random_state: Random state for reproducibility
        n_init: Number of initializations
        
    Returns:
        Tuple of (labels, kmeans_model)
    """
    print("=" * 70)
    print(f"Applying K-Means clustering with k={k}")
    print("=" * 70)
    print(f"Data shape: {X.shape}")
    print(f"Number of initializations: {n_init}")
    print()
    
    kmeans = KMeans(n_clusters=k, random_state=random_state, 
                   n_init=n_init, max_iter=1000)
    
    print("Fitting K-Means...", end=' ')
    labels = kmeans.fit_predict(X)
    print("✓")
    
    # Display cluster statistics
    print()
    print("Cluster statistics:")
    unique_labels, counts = np.unique(labels, return_counts=True)
    for label, count in zip(unique_labels, counts):
        percentage = count / len(labels) * 100
        print(f"  Cluster {label}: {count:5d} samples ({percentage:5.1f}%)")
    
    print()
    print(f"✓ Inertia (within-cluster sum of squares): {kmeans.inertia_:.2f}")
    print()
    
    return labels, kmeans


def save_results(df_pca: pd.DataFrame, labels: np.ndarray, kmeans: KMeans,
                pc_cols: list, energy_vars: list, pca_model: object,
                scaler: object, results_dir: Path, prefix: str, phase: str):
    """Save clustering results for a specific phase.
    
    Args:
        df_pca: DataFrame with PC scores
        labels: Cluster labels
        kmeans: Fitted KMeans model
        pc_cols: List of PC column names used
        energy_vars: List of original energy variable names
        pca_model: PCA model (for inverse transform)
        scaler: Scaler model (for inverse transform)
        results_dir: Results directory
        prefix: Output file prefix
        phase: Phase name (for file naming)
    """
    print(f"  Saving results for {phase}...")
    
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Add cluster labels to dataframe
    df_clustered = df_pca.copy()
    df_clustered['cluster'] = labels
    
    # Save clustered data
    clustered_file = results_dir / f"{prefix}_clustered_data_{phase}.csv"
    df_clustered.to_csv(clustered_file, index=False)
    print(f"    ✓ Clustered data: {clustered_file.name}")
    
    # Save cluster centroids (in PC space)
    centroids_pc = pd.DataFrame(
        kmeans.cluster_centers_,
        columns=pc_cols
    )
    centroids_pc['cluster'] = range(len(centroids_pc))
    centroids_pc_file = results_dir / f"{prefix}_centroids_pc_{phase}.csv"
    centroids_pc.to_csv(centroids_pc_file, index=False)
    print(f"    ✓ Centroids (PC space): {centroids_pc_file.name}")
    
    # Inverse transform centroids to original energy space
    if pca_model is not None and scaler is not None:
        # Expand centroids to full PC space if needed
        n_components_full = pca_model.n_components_
        n_components_used = len(pc_cols)
        
        if n_components_used < n_components_full:
            # Pad with zeros for unused components
            centroids_full = np.zeros((len(centroids_pc), n_components_full))
            centroids_full[:, :n_components_used] = kmeans.cluster_centers_
        else:
            centroids_full = kmeans.cluster_centers_
        
        # Inverse transform: PC space -> scaled space -> original space
        centroids_scaled = pca_model.inverse_transform(centroids_full)
        centroids_original = scaler.inverse_transform(centroids_scaled)
        
        centroids_energy = pd.DataFrame(
            centroids_original,
            columns=energy_vars
        )
        centroids_energy['cluster'] = range(len(centroids_energy))
        
        centroids_energy_file = results_dir / f"{prefix}_centroids_energy_{phase}.csv"
        centroids_energy.to_csv(centroids_energy_file, index=False)
        print(f"    ✓ Centroids (energy space): {centroids_energy_file.name}")
    else:
        print("    ⚠️  PCA/Scaler models not available, skipping energy space centroids")
    
    # Save KMeans model
    model_file = results_dir / f"{prefix}_model_{phase}.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump({
            'kmeans': kmeans,
            'n_clusters': kmeans.n_clusters,
            'pc_cols': pc_cols,
            'inertia': kmeans.inertia_
        }, f)
    print(f"    ✓ KMeans model: {model_file.name}")
    
    # Save cluster summary
    summary = {
        'phase': phase,
        'n_clusters': kmeans.n_clusters,
        'n_samples': len(labels),
        'n_features_used': len(pc_cols),
        'inertia': kmeans.inertia_,
        'n_init': kmeans.n_init,
        'random_state': kmeans.random_state
    }
    
    # Add cluster sizes
    unique_labels, counts = np.unique(labels, return_counts=True)
    for label, count in zip(unique_labels, counts):
        summary[f'cluster_{label}_size'] = int(count)
        summary[f'cluster_{label}_percentage'] = float(count / len(labels) * 100)
    
    summary_df = pd.DataFrame([summary])
    summary_file = results_dir / f"{prefix}_summary_{phase}.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"    ✓ Summary: {summary_file.name}")
    
    print()


def main():
    """Main execution function."""
    results_dir = Path(RESULTS_DIR)
    
    print("=" * 70)
    print("Step 4: Applying K-Means clustering to each phase")
    print("=" * 70)
    
    # Determine k
    if USE_OPTIMAL_K:
        k = load_optimal_k(results_dir, OPTIMAL_K_FILE)
        print(f"Using optimal k from file: k={k}")
    else:
        k = MANUAL_K
        print(f"Using manual k: k={k}")
    
    print(f"Number of phases to cluster: {len(PHASES)}")
    print()
    
    for phase in PHASES:
        print(f"\n{'=' * 70}")
        print(f"Processing Phase: {phase.upper()}")
        print(f"{'=' * 70}")
        
        # Load PCA scores for this phase
        scores_file = results_dir / f"{INPUT_PREFIX}_scores_{phase}.csv"
        df_pca = pd.read_csv(scores_file)
        print(f"  Loaded PC scores: {scores_file.name}")
        print(f"    Shape: {df_pca.shape}")
        
        # Get PC columns
        pc_cols = [col for col in df_pca.columns if col.startswith('PC')]
        if N_PCS_TO_USE is not None:
            pc_cols = pc_cols[:N_PCS_TO_USE]
        
        print(f"  Using {len(pc_cols)} principal components: {pc_cols}")
        
        X = df_pca[pc_cols].values
        
        # Load PCA model and scaler (for inverse transform)
        models_file = results_dir / f"{INPUT_PREFIX}_models_{phase}.pkl"
        if models_file.exists():
            with open(models_file, 'rb') as f:
                models = pickle.load(f)
            pca_model = models['pca']
            scaler = models['scaler']
            energy_vars = models['energy_vars']
            print(f"  Loaded PCA model and scaler: {models_file.name}")
        else:
            print(f"  ⚠️  PCA models file not found for {phase}")
            pca_model = None
            scaler = None
            energy_vars = []
        
        # Apply K-Means
        print(f"  Applying K-Means clustering with k={k}...")
        labels, kmeans = apply_kmeans(X, k, random_state=RANDOM_STATE, n_init=N_INIT)
        
        # Print cluster distribution
        unique_labels, counts = np.unique(labels, return_counts=True)
        print(f"  Cluster distribution:")
        for label, count in zip(unique_labels, counts):
            print(f"    Cluster {label}: {count:5d} samples ({count/len(labels)*100:5.1f}%)")
        
        # Save results
        save_results(df_pca, labels, kmeans, pc_cols, energy_vars, 
                    pca_model, scaler, results_dir, OUTPUT_PREFIX, phase)
    
    print("\n" + "=" * 70)
    print("✅ Step 4 complete!")
    print("=" * 70)
    print(f"Clustered {len(PHASES)} phases with k={k} clusters each")
    print()
    print("Next step:")
    print("  5. Run step5_plot_energy_patterns.py to visualize cluster centroids")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
