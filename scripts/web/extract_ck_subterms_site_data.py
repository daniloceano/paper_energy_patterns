#!/usr/bin/env python3
"""Publish the corrected all-EP Ck decomposition as a website manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "results" / "ck_subterms_corrected"
MAPPING_FILE = REPO_ROOT / "results" / "cluster" / "cluster_to_ep.json"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

SUBTERM_LABELS = {
    "Ck_1": {
        "symbol": "C_K^{(A)}",
        "name": "Term (A)",
        "description": "Eddy momentum flux against the meridional shear of the zonal wind.",
    },
    "Ck_2": {
        "symbol": "C_K^{(B)}",
        "name": "Term (B)",
        "description": "Meridional flux of eddy kinetic energy against the gradient of mean meridional wind.",
    },
    "Ck_3": {
        "symbol": "C_K^{(C)}",
        "name": "Term (C)",
        "description": "Curvature contribution from zonal eddy kinetic energy and mean meridional wind.",
    },
    "Ck_4": {
        "symbol": "C_K^{(D)}",
        "name": "Term (D)",
        "description": "Vertical flux of zonal eddy momentum against the shear of mean zonal wind.",
    },
    "Ck_5": {
        "symbol": "C_K^{(E)}",
        "name": "Term (E)",
        "description": "Vertical flux of meridional eddy momentum against the shear of mean meridional wind.",
    },
}

FIGURE_PATHS = {
    "vertical_profiles": "figures/ck_subterms_corrected/ck_subterms_vertical_profiles.png",
    "boxplots": "figures/ck_subterms_corrected/ck_subterms_boxplots.png",
    "lifecycle": "figures/ck_subterms_corrected/ck_subterms_lifecycle.png",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"required corrected Ck result is missing: {path}")
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _figure_urls() -> dict[str, str]:
    base = os.environ.get("SUPABASE_FIGURES_URL") or os.environ.get(
        "NEXT_PUBLIC_SUPABASE_FIGURES_URL"
    )
    if not base:
        return FIGURE_PATHS.copy()
    base = base.rstrip("/")
    return {
        key: f"{base}/{path.removeprefix('figures/')}"
        for key, path in FIGURE_PATHS.items()
    }


def extract_manifest() -> dict:
    mapping = json.loads(MAPPING_FILE.read_text())
    if "corrected" not in str(mapping.get("source_cache", "")):
        raise RuntimeError("refusing to publish Ck results from a legacy clustering")

    table = _read_csv(RESULTS_DIR / "subterms_by_cyclone.csv")
    dominance_rows = _read_csv(RESULTS_DIR / "dominance_frequency.csv")
    statistics_rows = _read_csv(RESULTS_DIR / "subterm_statistics.csv")
    contrast_rows = _read_csv(RESULTS_DIR / "ep_contrasts.csv")

    track_ids = {row["track_id"] for row in table}
    expected = int(mapping["n_cyclones"])
    if len(track_ids) != expected:
        raise RuntimeError(
            f"refusing partial website manifest: {len(track_ids)}/{expected} cyclones"
        )
    expected_phases = {"incipient", "intensification", "mature", "decay"}
    observed_phases = {row["phase"] for row in table}
    if observed_phases != expected_phases or len(table) != expected * len(expected_phases):
        raise RuntimeError(
            "refusing incomplete Ck lifecycle results: "
            f"phases={sorted(observed_phases)}, rows={len(table)}"
        )
    row_keys = {(row["track_id"], row["phase"]) for row in table}
    if len(row_keys) != len(table):
        raise RuntimeError("refusing Ck results with duplicate cyclone-phase rows")

    worst_closure = max(float(row["ck_closure_relative"]) for row in table)
    if worst_closure > 1.0e-6:
        raise RuntimeError(
            f"refusing Ck results that fail closure: {worst_closure:.3e}"
        )
    ep_counts = {f"EP{ep}": int(n) for ep, n in mapping["ep_counts"].items()}
    expected_ep_labels = set(ep_counts)
    dominance = []
    for row in dominance_rows:
        if row["phase"] != "intensification" or row["ep_label"] not in expected_ep_labels:
            continue
        dominance.append(
            {
                "ep": row["ep_label"],
                "subterm_key": row["term"],
                "subterm_label": row["label"],
                "count": int(row["n_dominant"]),
                "total": int(row["n_total"]),
                "percentage": round(100.0 * float(row["fraction"]), 1),
                "description": row["description"],
            }
        )

    intensification_totals = []
    intensification_stats = []
    for row in statistics_rows:
        if row["phase"] != "intensification" or row["ep_label"] not in expected_ep_labels:
            continue
        record = {
            "ep": row["ep_label"],
            "term_key": row["term"],
            "term_label": row["label"],
            "n": int(row["n"]),
            "mean": float(row["mean"]),
            "median": float(row["median"]),
            "q25": float(row["q25"]),
            "q75": float(row["q75"]),
        }
        if row["term"] == "Ck":
            intensification_totals.append(record)
        else:
            intensification_stats.append(record)

    contrasts = []
    for row in contrast_rows:
        if row["phase"] != "intensification":
            continue
        contrasts.append(
            {
                "subterm_key": row["term"],
                "subterm_label": row["label"],
                "contrast": row["contrast"],
                "median_left": float(row["median_left"]),
                "median_right": float(row["median_right"]),
                "p_fdr": float(row["p_fdr"]),
                "significant": row["significant"].strip().lower() == "true",
                "effect_size_r": float(row["effect_size_r"]),
                "effect_magnitude": row["effect_magnitude"],
            }
        )

    source_profiles = REPO_ROOT / "data" / "corrected" / "vertical_phase_means_corrected.parquet"
    manifest = {
        "analysis": "ck_subterms_corrected",
        "title": "Corrected Ck Subterms — All Energy Patterns",
        "phase": "intensification",
        "source_cache": mapping["source_cache"],
        "source_profiles": str(source_profiles.relative_to(REPO_ROOT)),
        "source_profiles_sha256": _sha256(source_profiles),
        "population": {
            "total": expected,
            "energy_patterns": ep_counts,
            "phase_rows": len(table),
            "worst_closure_relative": worst_closure,
            "closure_tolerance": 1.0e-6,
        },
        "sign_convention": (
            "Negative Ck transfers kinetic energy from the mean flow to the eddy "
            "(KZ → KE); the dominant subterm is the most negative contribution, "
            "while all-positive decompositions are classified separately."
        ),
        "subterms": [
            {"key": key, **metadata} for key, metadata in SUBTERM_LABELS.items()
        ],
        "dominance": dominance,
        "intensification_totals": intensification_totals,
        "intensification_statistics": intensification_stats,
        "contrasts": contrasts,
        "figures": _figure_urls(),
    }

    WEB_CONTENT.mkdir(parents=True, exist_ok=True)
    output = WEB_CONTENT / "ck_subterms_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ {output.relative_to(REPO_ROOT)}")
    print(f"  corrected population: {expected} cyclones; closure={worst_closure:.3e}")
    return manifest


if __name__ == "__main__":
    extract_manifest()
