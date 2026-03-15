#!/usr/bin/env python3
"""
Build site manifest JSON files from repository results.

Reads CSV results from results/cluster/ and generates structured JSON
manifests in web/src/content/ for consumption by the Next.js application.

Usage:
    python scripts/web/build_site_manifest.py

Outputs:
    web/src/content/cluster_manifest.json
    web/src/content/figures_manifest.json
    web/src/content/documents_manifest.json
"""

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"


def ensure_output_dir():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)


def build_cluster_manifest():
    """Read cluster analysis results and build a manifest."""
    results_dir = REPO_ROOT / "results" / "cluster"
    manifest = {
        "optimal_k": None,
        "phases": ["incipient", "intensification", "mature", "decay"],
        "energy_terms": ["Ca", "Ck", "Ge", "BAe", "BKe", "Ae", "Ke"],
        "pca": {},
        "kmeans_summary": {},
    }

    # Read optimal k
    optimal_k_file = results_dir / "optimal_k.txt"
    if optimal_k_file.exists():
        manifest["optimal_k"] = int(optimal_k_file.read_text().strip())

    # Read PCA explained variance per phase
    for phase in manifest["phases"]:
        ev_file = results_dir / f"pca_explained_variance_{phase}.csv"
        if ev_file.exists():
            import csv
            with open(ev_file) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            manifest["pca"][phase] = {
                "explained_variance": [
                    float(r.get("explained_variance_ratio", r.get("explained_variance", 0)))
                    for r in rows
                ],
                "n_components": len(rows),
            }

    # Read K-Means summary per phase
    for phase in manifest["phases"]:
        summary_file = results_dir / f"kmeans_summary_{phase}.csv"
        if summary_file.exists():
            import csv
            with open(summary_file) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            manifest["kmeans_summary"][phase] = rows

    # Read aggregate summary
    summary_file = results_dir / "kmeans_summary.csv"
    if summary_file.exists():
        import csv
        with open(summary_file) as f:
            reader = csv.DictReader(f)
            manifest["kmeans_summary"]["aggregate"] = list(reader)

    output_path = WEB_CONTENT / "cluster_manifest.json"
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  ✓ {output_path.relative_to(REPO_ROOT)}")


def build_figures_manifest():
    """Scan figures/ directory and build a catalogue."""
    figures_dir = REPO_ROOT / "figures"
    catalogue = []

    for png_file in sorted(figures_dir.rglob("*.png")):
        relative = str(png_file.relative_to(REPO_ROOT))
        parts = png_file.relative_to(figures_dir).parts

        category = parts[0] if len(parts) > 1 else "root"
        catalogue.append({
            "filename": png_file.name,
            "path": relative,
            "category": category,
            "api_url": f"/api/figures?path={relative}",
        })

    output_path = WEB_CONTENT / "figures_manifest.json"
    with open(output_path, "w") as f:
        json.dump(catalogue, f, indent=2)
    print(f"  ✓ {output_path.relative_to(REPO_ROOT)} ({len(catalogue)} figures)")


def build_documents_manifest():
    """Catalogue available PDFs and markdown documents."""
    docs_dir = REPO_ROOT / "docs"
    documents = []

    if docs_dir.exists():
        for pdf_file in sorted(docs_dir.glob("*.pdf")):
            relative = str(pdf_file.relative_to(REPO_ROOT))
            documents.append({
                "filename": pdf_file.name,
                "path": relative,
                "type": "pdf",
                "api_url": f"/api/figures?path={relative}",
            })

    # Also catalogue SCIENTIFIC_NOTES.md files
    for notes_file in sorted(REPO_ROOT.rglob("SCIENTIFIC_NOTES.md")):
        relative = str(notes_file.relative_to(REPO_ROOT))
        documents.append({
            "filename": notes_file.name,
            "path": relative,
            "type": "markdown",
            "parent_dir": str(notes_file.parent.relative_to(REPO_ROOT)),
        })

    output_path = WEB_CONTENT / "documents_manifest.json"
    with open(output_path, "w") as f:
        json.dump(documents, f, indent=2)
    print(f"  ✓ {output_path.relative_to(REPO_ROOT)} ({len(documents)} documents)")


def main():
    print("Building site manifests...")
    ensure_output_dir()
    build_cluster_manifest()
    build_figures_manifest()
    build_documents_manifest()
    print("Done.")


if __name__ == "__main__":
    main()
