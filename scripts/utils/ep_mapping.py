"""
Energy Pattern Mapping Utilities

Single source of truth for cluster -> Energy Pattern mappings.

Why this module no longer hardcodes the mapping
-----------------------------------------------
K-means cluster indices are arbitrary: they depend on the initialisation and on
the data. The article's mapping (cluster 0 -> EP1, 1 -> EP3, 2 -> EP2) was a
property of the *legacy* clustering run. Re-running the clustering on the
corrected LEC climatology reshuffles those indices, and a hardcoded table would
then silently relabel every Energy Pattern in every downstream figure.

The mapping is therefore *derived* from the cluster centroids and persisted next
to the clustering it describes, in ``results/cluster/cluster_to_ep.json``:

    EP1 -> strongest intensification-phase conversions
    EP2 -> intermediate
    EP3 -> weakest ("day-to-day" cyclones)

ranked by ``|Ca_int| + |Ck_int|``, which is the definition the manuscript uses.
That rule reproduces the article's mapping exactly when applied to the legacy
centroids, so the convention is unchanged -- only its provenance is.

``step4_apply_kmeans.py`` writes the file; every consumer reads it. Counts and
percentages likewise come from the clustering that is actually on disk, never
from constants baked into this module.

Usage:
    from scripts.utils.ep_mapping import (
        CLUSTER_TO_EP, EP_TO_CLUSTER, EP_LABELS, EP_COLORS, ALL_EPS
    )

    ep_label = CLUSTER_TO_EP[cluster_id]   # e.g. 0 -> 1 (EP1)
    cluster_id = EP_TO_CLUSTER[1]

    # publication scripts should additionally assert the data lineage
    from scripts.utils.ep_mapping import assert_corrected_clustering
    assert_corrected_clustering()

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLUSTER_DIR = PROJECT_ROOT / "results" / "cluster"
MAPPING_FILE = CLUSTER_DIR / "cluster_to_ep.json"
CENTROIDS_FILE = CLUSTER_DIR / "kmeans_centroids_energy.csv"

#: Terms ranked to order the Energy Patterns, in the intensification phase.
RANKING_TERMS = ["Ca_int", "Ck_int"]

# =============================================================================
# STATIC IDENTITY (independent of any clustering run)
# =============================================================================

ALL_EPS: List[int] = [1, 2, 3]  # EP1, EP2, EP3 only (clustered groups)

# EPALL as ep=0: all cyclones pooled regardless of cluster assignment.
# Not a "cluster" — use only where pool-level analysis makes sense
# (PREDEP, Pearson, Spearman on the full sample).
EPALL_EP: int = 0
ALL_EPS_WITH_EPALL: List[int] = [0, 1, 2, 3]  # 0 = EPALL, 1/2/3 = clustered EPs

EP_LABELS: Dict[int, str] = {
    0: "EPALL",  # All cyclones pooled (not a cluster)
    1: "EP1",
    2: "EP2",
    3: "EP3",
}

EP_ABBREVS: Dict[int, str] = {
    0: "epall",
    1: "ep1",
    2: "ep2",
    3: "ep3",
}

EPALL_LABEL = "EPALL"
EPALL_ABBREV = "epall"

# =============================================================================
# VISUALIZATION DEFAULTS
# =============================================================================

# Color palette for each EP (consistent across all figures).
#
# This is the palette the manuscript's main figures already use — figures 6
# (intensity/seasonality/trends) and 7 (genesis density) hardcoded it as the
# matplotlib tab10 triple. The module previously carried a different palette
# (gold / dodgerblue / forestgreen), so an EP was one colour in the paper and
# another in every supporting analysis. The paper figures win.
EP_COLORS: Dict[int, str] = {
    0: "#666666",  # EPALL - neutral grey (pooled, not a cluster)
    1: "#1f77b4",  # EP1 - blue
    2: "#ff7f0e",  # EP2 - orange
    3: "#2ca02c",  # EP3 - green
}

EP_COLORS_EXTENDED: Dict[str, str] = {
    "EPALL": "#666666",
    "EP1": "#1f77b4",
    "EP2": "#ff7f0e",
    "EP3": "#2ca02c",
}

# =============================================================================
# SCIENTIFIC DESCRIPTIONS
# =============================================================================

EP_DESCRIPTIONS: Dict[int, str] = {
    1: "High barotropic and baroclinic conversions; exports energy to surroundings",
    2: "Moderate balanced conversions; imports energy from large-scale environment",
    3: "Weak energetics representing typical 'day-to-day' cyclones",
}


# =============================================================================
# DERIVATION AND PERSISTENCE
# =============================================================================

class ClusterMappingMissing(FileNotFoundError):
    """Raised when no clustering run has published a cluster -> EP mapping."""


def derive_cluster_to_ep(centroids: pd.DataFrame) -> Dict[int, int]:
    """Rank cluster centroids into Energy Patterns.

    Parameters
    ----------
    centroids
        ``kmeans_centroids_energy.csv``: one row per cluster, a ``cluster``
        column, and the wide term-by-phase columns.

    Returns
    -------
    dict
        ``{cluster_id: ep_number}``, EP1 being the strongest conversions.
    """
    missing = [term for term in RANKING_TERMS if term not in centroids.columns]
    if missing:
        raise ValueError(
            f"centroids lack the ranking terms {missing}; cannot order the "
            "Energy Patterns. Columns present: {list(centroids.columns)[:8]}..."
        )
    magnitude = sum(centroids[term].abs() for term in RANKING_TERMS)
    order = centroids.assign(_magnitude=magnitude).sort_values(
        "_magnitude", ascending=False
    )
    return {
        int(row.cluster): ep
        for ep, row in zip(ALL_EPS, order.itertuples(index=False))
    }


def write_cluster_mapping(
    centroids: pd.DataFrame,
    labels: pd.Series,
    source_cache: str,
    path: Path = MAPPING_FILE,
) -> Path:
    """Persist the derived mapping alongside the clustering that produced it.

    ``source_cache`` records which energy cache the clustering consumed, so a
    downstream script can tell a corrected run from a legacy one.
    """
    mapping = derive_cluster_to_ep(centroids)
    counts = labels.value_counts().to_dict()
    total = int(labels.size)
    payload = {
        "cluster_to_ep": {str(cluster): ep for cluster, ep in mapping.items()},
        "ranking_terms": RANKING_TERMS,
        "ranking_rule": "descending |Ca_int| + |Ck_int|; EP1 strongest",
        "source_cache": str(source_cache),
        "n_cyclones": total,
        "ep_counts": {
            str(ep): int(counts.get(cluster, 0)) for cluster, ep in mapping.items()
        },
        "ep_percentages": {
            str(ep): round(100.0 * counts.get(cluster, 0) / total, 4)
            for cluster, ep in mapping.items()
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def load_mapping(path: Path = MAPPING_FILE) -> dict:
    """Read the persisted mapping payload."""
    if not path.is_file():
        raise ClusterMappingMissing(
            f"no cluster -> EP mapping at {path}. Run "
            "scripts/cluster_analysis_energy_patterns/step4_apply_kmeans.py, "
            "which derives it from the centroids of the clustering on disk."
        )
    return json.loads(path.read_text())


def mapping_source() -> str:
    """Energy cache the current clustering was built from."""
    return str(load_mapping().get("source_cache", "unknown"))


def is_corrected_clustering() -> bool:
    """True when the clustering on disk came from the corrected LEC cache."""
    return "corrected" in mapping_source()


def assert_corrected_clustering() -> None:
    """Guard for publication scripts: refuse a legacy clustering.

    The corrected rerun is the only scientific truth for this article. A figure
    built on ``data/energy_cache.parquet`` would carry the superseded LEC
    equations even if every other input were current.
    """
    source = mapping_source()
    if "corrected" not in source:
        raise RuntimeError(
            f"the clustering on disk was built from {source!r}, not the "
            "corrected LEC climatology. Rebuild it with "
            "scripts/cluster_analysis_energy_patterns/run_all.py against "
            "data/corrected/energy_cache_corrected.parquet before producing "
            "any article result."
        )


def _derived(name: str):
    """Resolve a mapping-derived constant on first access."""
    payload = load_mapping()
    if name == "CLUSTER_TO_EP":
        return {int(cluster): int(ep) for cluster, ep in payload["cluster_to_ep"].items()}
    if name == "EP_TO_CLUSTER":
        return {int(ep): int(cluster) for cluster, ep in payload["cluster_to_ep"].items()}
    if name == "EP_COUNTS":
        return {int(ep): int(count) for ep, count in payload["ep_counts"].items()}
    if name == "EP_PERCENTAGES":
        return {int(ep): float(pct) for ep, pct in payload["ep_percentages"].items()}
    raise AttributeError(name)


_DERIVED_NAMES = {"CLUSTER_TO_EP", "EP_TO_CLUSTER", "EP_COUNTS", "EP_PERCENTAGES"}


def __getattr__(name: str):
    """Resolve clustering-dependent constants lazily (PEP 562).

    Keeps ``from scripts.utils.ep_mapping import CLUSTER_TO_EP`` working while
    guaranteeing the value describes the clustering currently on disk rather
    than a table frozen in this file.
    """
    if name in _DERIVED_NAMES:
        return _derived(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(list(globals()) + list(_DERIVED_NAMES))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_ep_from_cluster(cluster_id: int) -> int:
    """Convert cluster ID to Energy Pattern number."""
    mapping = _derived("CLUSTER_TO_EP")
    if cluster_id not in mapping:
        raise ValueError(f"Unknown cluster ID: {cluster_id}. Valid: {list(mapping)}")
    return mapping[cluster_id]


def get_cluster_from_ep(ep_num: int) -> int:
    """Convert Energy Pattern number to cluster ID."""
    mapping = _derived("EP_TO_CLUSTER")
    if ep_num not in mapping:
        raise ValueError(f"Unknown EP number: {ep_num}. Valid: {list(mapping)}")
    return mapping[ep_num]


def get_ep_label(ep_num: int) -> str:
    """Get label string for an Energy Pattern (e.g., 'EP1')."""
    if ep_num not in EP_LABELS:
        raise ValueError(f"Unknown EP number: {ep_num}. Valid: {list(EP_LABELS.keys())}")
    return EP_LABELS[ep_num]


def get_ep_abbrev(ep_num: int) -> str:
    """Get lowercase abbreviation for an Energy Pattern (e.g., 'ep1')."""
    if ep_num not in EP_ABBREVS:
        raise ValueError(f"Unknown EP number: {ep_num}. Valid: {list(EP_ABBREVS.keys())}")
    return EP_ABBREVS[ep_num]


def get_ep_color(ep_num: int) -> str:
    """Get visualization color for an Energy Pattern."""
    if ep_num not in EP_COLORS:
        raise ValueError(f"Unknown EP number: {ep_num}. Valid: {list(EP_COLORS.keys())}")
    return EP_COLORS[ep_num]


def load_ep_assignments(path: Optional[Path] = None) -> pd.DataFrame:
    """Per-cyclone Energy Pattern assignment of the clustering on disk.

    Returns ``track_id`` (str), ``cluster`` and ``ep``.
    """
    path = path or CLUSTER_DIR / "kmeans_clustered_data.csv"
    if not path.is_file():
        raise ClusterMappingMissing(f"clustering output not found: {path}")
    frame = pd.read_csv(path, usecols=["track_id", "cluster"], dtype={"track_id": str})
    frame["ep"] = frame["cluster"].map(_derived("CLUSTER_TO_EP"))
    if frame["ep"].isna().any():
        raise ValueError("cluster labels absent from the persisted cluster -> EP mapping")
    frame["ep"] = frame["ep"].astype(int)
    return frame
