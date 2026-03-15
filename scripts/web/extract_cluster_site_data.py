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
"""

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results" / "cluster"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

PHASES = ["incipient", "intensification", "mature", "decay"]


def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def read_csv_safe(filepath):
    """Read CSV and return list of dicts, or empty list if missing."""
    if not filepath.exists():
        return []
    with open(filepath) as f:
        return list(csv.DictReader(f))


def extract_step2_pca():
    """Extract PCA results per phase."""
    data = {"phases": {}}

    for phase in PHASES:
        phase_data = {}

        # Explained variance
        rows = read_csv_safe(RESULTS_DIR / f"pca_explained_variance_{phase}.csv")
        if rows:
            phase_data["explained_variance"] = [
                float(r.get("explained_variance_ratio", r.get("explained_variance", 0)))
                for r in rows
            ]
            phase_data["cumulative_variance"] = []
            cumsum = 0.0
            for v in phase_data["explained_variance"]:
                cumsum += v
                phase_data["cumulative_variance"].append(round(cumsum, 6))

        # Loadings
        rows = read_csv_safe(RESULTS_DIR / f"pca_loadings_{phase}.csv")
        if rows:
            phase_data["loadings"] = rows

        data["phases"][phase] = phase_data

    output = WEB_CONTENT / "cluster_step2_data.json"
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def extract_step3_optimal_k():
    """Extract optimal k analysis results."""
    data = {"optimal_k": None, "raw_indices": [], "normalized_indices": []}

    k_file = RESULTS_DIR / "optimal_k.txt"
    if k_file.exists():
        data["optimal_k"] = int(k_file.read_text().strip())

    data["raw_indices"] = read_csv_safe(RESULTS_DIR / "optimal_k_raw_indices.csv")
    data["normalized_indices"] = read_csv_safe(
        RESULTS_DIR / "optimal_k_normalized_indices.csv"
    )

    output = WEB_CONTENT / "cluster_step3_data.json"
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def extract_step4_clustering():
    """Extract K-Means results per phase."""
    data = {"phases": {}, "aggregate": {}}

    for phase in PHASES:
        phase_data = {}

        # Centroids in energy space
        rows = read_csv_safe(RESULTS_DIR / f"kmeans_centroids_energy_{phase}.csv")
        if rows:
            phase_data["centroids_energy"] = rows

        # Summary
        rows = read_csv_safe(RESULTS_DIR / f"kmeans_summary_{phase}.csv")
        if rows:
            phase_data["summary"] = rows

        data["phases"][phase] = phase_data

    # Aggregate
    rows = read_csv_safe(RESULTS_DIR / "kmeans_centroids_energy.csv")
    if rows:
        data["aggregate"]["centroids_energy"] = rows

    rows = read_csv_safe(RESULTS_DIR / "kmeans_summary.csv")
    if rows:
        data["aggregate"]["summary"] = rows

    output = WEB_CONTENT / "cluster_step4_data.json"
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")


def main():
    print("Extracting cluster analysis data for site...")
    ensure_output_dir()
    extract_step2_pca()
    extract_step3_optimal_k()
    extract_step4_clustering()
    print("Done.")


if __name__ == "__main__":
    main()
