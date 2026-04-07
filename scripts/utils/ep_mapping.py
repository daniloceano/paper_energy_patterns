"""
Energy Pattern Mapping Utilities

Single source of truth for cluster → Energy Pattern mappings.

Cluster Assignments (from K-Means clustering on LEC diagnostics):
    - Cluster 0 → EP1 (444 cyclones, 11.6%) - High energy conversions
    - Cluster 1 → EP3 (2,397 cyclones, 62.7%) - Weak/background energetics
    - Cluster 2 → EP2 (979 cyclones, 25.6%) - Moderate conversions

Usage:
    from scripts.utils.ep_mapping import (
        CLUSTER_TO_EP, EP_TO_CLUSTER, EP_LABELS, EP_COLORS, ALL_EPS
    )
    
    ep_label = CLUSTER_TO_EP[cluster_id]  # e.g., 0 → 1 (EP1)
    cluster_id = EP_TO_CLUSTER[1]         # e.g., 1 → 0

Author: Danilo Couto de Souza
Date: April 2026
"""

from typing import Dict, List

# =============================================================================
# CORE MAPPINGS (Single Source of Truth)
# =============================================================================

# Cluster ID → Energy Pattern number
CLUSTER_TO_EP: Dict[int, int] = {
    0: 1,  # cluster 0 → EP1 (high conversions)
    1: 3,  # cluster 1 → EP3 (weak/background)
    2: 2,  # cluster 2 → EP2 (moderate conversions)
}

# Energy Pattern number → Cluster ID
EP_TO_CLUSTER: Dict[int, int] = {ep: cluster for cluster, ep in CLUSTER_TO_EP.items()}

# All Energy Pattern identifiers (ordered for consistent iteration)
ALL_EPS: List[int] = [1, 2, 3]  # EP1, EP2, EP3

# Energy Pattern label strings
EP_LABELS: Dict[int, str] = {
    1: "EP1",
    2: "EP2",
    3: "EP3",
}

# Canonical abbreviations for filenames and output
EP_ABBREVS: Dict[int, str] = {
    1: "ep1",
    2: "ep2",
    3: "ep3",
}

# EPALL represents the union of all EPs (total cyclone composite)
EPALL_LABEL = "EPALL"
EPALL_ABBREV = "epall"

# =============================================================================
# VISUALIZATION DEFAULTS
# =============================================================================

# Color palette for each EP (consistent across all figures)
EP_COLORS: Dict[int, str] = {
    1: "gold",        # EP1 - warm gold
    2: "dodgerblue",  # EP2 - blue
    3: "forestgreen", # EP3 - green
}

# Extended colors including EPALL
EP_COLORS_EXTENDED: Dict[str, str] = {
    "EP1": "gold",
    "EP2": "dodgerblue",
    "EP3": "forestgreen",
    "EPALL": "gray",
}

# =============================================================================
# SCIENTIFIC DESCRIPTIONS
# =============================================================================

EP_DESCRIPTIONS: Dict[int, str] = {
    1: "High barotropic and baroclinic conversions; exports energy to surroundings",
    2: "Moderate balanced conversions; imports energy from large-scale environment",
    3: "Weak energetics representing typical 'day-to-day' cyclones",
}

EP_COUNTS: Dict[int, int] = {
    1: 444,   # EP1 count from clustering
    2: 979,   # EP2 count from clustering
    3: 2397,  # EP3 count from clustering
}

EP_PERCENTAGES: Dict[int, float] = {
    1: 11.6,
    2: 25.6,
    3: 62.7,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_ep_from_cluster(cluster_id: int) -> int:
    """Convert cluster ID to Energy Pattern number."""
    if cluster_id not in CLUSTER_TO_EP:
        raise ValueError(f"Unknown cluster ID: {cluster_id}. Valid: {list(CLUSTER_TO_EP.keys())}")
    return CLUSTER_TO_EP[cluster_id]


def get_cluster_from_ep(ep_num: int) -> int:
    """Convert Energy Pattern number to cluster ID."""
    if ep_num not in EP_TO_CLUSTER:
        raise ValueError(f"Unknown EP number: {ep_num}. Valid: {list(EP_TO_CLUSTER.keys())}")
    return EP_TO_CLUSTER[ep_num]


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
