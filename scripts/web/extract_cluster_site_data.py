#!/usr/bin/env python3
"""
Extract cluster analysis data for the web site.

Reads PCA and K-Means results from results/cluster/ and generates
structured JSON for each analysis step.

Usage:
    python scripts/web/extract_cluster_site_data.py

Outputs:
    web/src/content/cluster_step1_data.json
    web/src/content/cluster_step2_data.json
    web/src/content/cluster_step3_data.json
    web/src/content/cluster_step4_data.json
    web/src/content/energy_patterns.json
"""

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results" / "cluster"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def read_csv_safe(filepath):
    """Read CSV and return list of dicts, or empty list if missing."""
    if not filepath.exists():
        return []
    with open(filepath) as f:
        return list(csv.DictReader(f))


def read_csv_required(filepath):
    """Read a non-empty CSV or stop publication of an incomplete analysis."""
    rows = read_csv_safe(filepath)
    if not rows:
        raise FileNotFoundError(f"required non-empty clustering result is missing: {filepath}")
    return rows


def extract_step2_pca():
    """Extract results from the single global 28-feature PCA."""
    variance_rows = read_csv_required(RESULTS_DIR / "pca_explained_variance.csv")
    loadings = read_csv_required(RESULTS_DIR / "pca_loadings.csv")
    feature_columns = [
        column
        for column in loadings[0]
        if column and column != "PC" and not column.lower().startswith("unnamed")
    ]
    if len(feature_columns) != 28:
        raise ValueError(
            f"global PCA must contain 28 term-by-phase features, found {len(feature_columns)}"
        )
    explained_variance = [float(row["explained_variance_ratio"]) for row in variance_rows]
    cumulative_variance = [
        float(row["cumulative_variance_ratio"]) for row in variance_rows
    ]
    data = {
        "approach": "global_wide_matrix",
        "n_input_features": len(feature_columns),
        "n_components": len(variance_rows),
        "retained_variance": cumulative_variance[-1] if cumulative_variance else None,
        "explained_variance": explained_variance,
        "cumulative_variance": cumulative_variance,
        "loadings": loadings,
    }

    output = WEB_CONTENT / "cluster_step2_data.json"
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def extract_step3_optimal_k():
    """Extract optimal k analysis results."""
    k_file = RESULTS_DIR / "optimal_k.txt"
    if not k_file.is_file():
        raise FileNotFoundError(f"missing optimal-k result: {k_file}")
    optimal_k = int(k_file.read_text().strip())
    raw_indices = read_csv_required(RESULTS_DIR / "optimal_k_raw_indices.csv")
    normalized_indices = read_csv_required(
        RESULTS_DIR / "optimal_k_normalized_indices.csv"
    )
    required_columns = {"Stability_reval", "mean_index"}
    missing = required_columns.difference(normalized_indices[0])
    if missing:
        raise ValueError(
            f"optimal-k ensemble lacks required corrected criteria: {sorted(missing)}"
        )
    ensemble_winner = int(
        max(normalized_indices, key=lambda row: float(row["mean_index"]))["k"]
    )
    if ensemble_winner != optimal_k:
        raise ValueError(
            f"optimal_k.txt says {optimal_k}, but ensemble maximum is {ensemble_winner}"
        )
    data = {
        "optimal_k": optimal_k,
        "raw_indices": raw_indices,
        "normalized_indices": normalized_indices,
    }

    output = WEB_CONTENT / "cluster_step3_data.json"
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def extract_step4_clustering():
    """Extract the single global K-Means solution."""
    data = {
        "approach": "global_wide_matrix",
        "centroids_energy": read_csv_required(RESULTS_DIR / "kmeans_centroids_energy.csv"),
        "summary": read_csv_required(RESULTS_DIR / "kmeans_summary.csv"),
    }

    output = WEB_CONTENT / "cluster_step4_data.json"
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def extract_energy_patterns():
    """Publish site-wide EP counts and corrected intensification centroids."""
    mapping_path = RESULTS_DIR / "cluster_to_ep.json"
    centroids_path = RESULTS_DIR / "kmeans_centroids_energy.csv"
    if not mapping_path.is_file() or not centroids_path.is_file():
        raise FileNotFoundError(
            "corrected cluster mapping and energy centroids are required for the site"
        )

    mapping = json.loads(mapping_path.read_text())
    if "corrected" not in str(mapping.get("source_cache", "")):
        raise RuntimeError("refusing to publish Energy Patterns from legacy clustering")

    centroids = {int(row["cluster"]): row for row in read_csv_required(centroids_path)}
    cluster_to_ep = {
        int(cluster): int(ep) for cluster, ep in mapping["cluster_to_ep"].items()
    }
    if set(cluster_to_ep.values()) != {1, 2, 3}:
        raise ValueError("the web application requires exactly the three EP1–EP3 groups")
    if set(cluster_to_ep) != set(centroids):
        raise ValueError("cluster mapping and centroid rows do not cover the same clusters")
    if sum(int(value) for value in mapping["ep_counts"].values()) != int(
        mapping["n_cyclones"]
    ):
        raise ValueError("Energy Pattern counts do not sum to the corrected population")

    patterns = {}
    ep_to_cluster = {ep: cluster for cluster, ep in cluster_to_ep.items()}
    for ep in sorted(ep_to_cluster):
        cluster = ep_to_cluster[ep]
        centroid = centroids[cluster]
        patterns[f"EP{ep}"] = {
            "count": int(mapping["ep_counts"][str(ep)]),
            "percentage": float(mapping["ep_percentages"][str(ep)]),
            "meanCk": float(centroid["Ck_int"]),
            "meanCa": float(centroid["Ca_int"]),
        }

    output = WEB_CONTENT / "energy_patterns.json"
    output.write_text(json.dumps(patterns, indent=2) + "\n")
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def main():
    print("Extracting cluster analysis data for site...")
    ensure_output_dir()
    extract_step2_pca()
    extract_step3_optimal_k()
    extract_step4_clustering()
    extract_energy_patterns()
    print("Done.")


if __name__ == "__main__":
    main()
