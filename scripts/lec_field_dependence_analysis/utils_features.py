"""
Feature extraction utilities for LEC–field dependence analysis.

Functions to compute scalar summaries from 2D storm-centred fields.
The 30°×30° domain is divided into sub-regions for physically
interpretable features: domain mean, border means, cardinal-sector means,
contrasts, and centre value.

All functions expect a 2D numpy array whose axes correspond to the
x (121) and y (121) coordinates of the precomputed composites
(0.25° resolution). The domain centre (index 60, 60) is the cyclone
position.

Author: Danilo Couto de Souza
Date: April 2026
"""

import numpy as np
from typing import Dict


# ---------------------------------------------------------------------------
# Domain geometry constants
# ---------------------------------------------------------------------------
GRID_SIZE = 121          # 30° / 0.25° + 1
CENTRE_IDX = 60          # Domain centre (cyclone position)
INNER_HALF = 30          # Half-width of 15°×15° inner box (in grid points)

# Inner 15°×15° box indices (centred on cyclone)
INNER_SLICE = slice(CENTRE_IDX - INNER_HALF, CENTRE_IDX + INNER_HALF + 1)

# Border strip THICKNESS in grid points.
# 5 points = 1.25° by cell-centre convention (5 × 0.25°), or 1.0° point-to-point
# (4 intervals × 0.25°). The strip spans the FULL 15° (61 pts) along each edge.
# So border_north = inner[:5, :] → shape (5, 61) = 1.25° thick × 15° wide.
BORDER_WIDTH = 5


def _inner(field: np.ndarray) -> np.ndarray:
    """Extract the inner 15°×15° sub-domain centred on the cyclone."""
    return field[INNER_SLICE, INNER_SLICE]


# ---------------------------------------------------------------------------
# Scalar feature functions
# ---------------------------------------------------------------------------

def domain_mean(field: np.ndarray) -> float:
    """Mean over the inner 15°×15° box."""
    return float(np.nanmean(_inner(field)))


def centre_value(field: np.ndarray) -> float:
    """Value at the cyclone centre (single grid point)."""
    return float(field[CENTRE_IDX, CENTRE_IDX])


def border_north_mean(field: np.ndarray) -> float:
    """Mean over the northern border strip of the inner box."""
    inner = _inner(field)
    return float(np.nanmean(inner[:BORDER_WIDTH, :]))


def border_south_mean(field: np.ndarray) -> float:
    """Mean over the southern border strip of the inner box."""
    inner = _inner(field)
    return float(np.nanmean(inner[-BORDER_WIDTH:, :]))


def border_east_mean(field: np.ndarray) -> float:
    """Mean over the eastern border strip of the inner box."""
    inner = _inner(field)
    return float(np.nanmean(inner[:, -BORDER_WIDTH:]))


def border_west_mean(field: np.ndarray) -> float:
    """Mean over the western border strip of the inner box."""
    inner = _inner(field)
    return float(np.nanmean(inner[:, :BORDER_WIDTH]))


def contrast_east_west(field: np.ndarray) -> float:
    """East minus West border mean (zonal contrast)."""
    return border_east_mean(field) - border_west_mean(field)


def contrast_south_north(field: np.ndarray) -> float:
    """South minus North border mean (meridional contrast)."""
    return border_south_mean(field) - border_north_mean(field)


# ---------------------------------------------------------------------------
# Cardinal-sector functions (half of the inner box)
# ---------------------------------------------------------------------------
# Each sector covers one full half of the inner 15°×15° box.
# This is more physically meaningful for LEC diagnostics than the corner
# quadrants, because the LEC captures zonal (E–W) and meridional (N–S)
# energy contrasts rather than diagonal ones.
#
# Orientation convention (matches NumPy array layout after INNER_SLICE):
#   inner[0, :]  → northernmost row
#   inner[-1, :] → southernmost row
#   inner[:, 0]  → westernmost column
#   inner[:, -1] → easternmost column

def sector_north_mean(field: np.ndarray) -> float:
    """Mean over the northern half of the inner box."""
    inner = _inner(field)
    mid = inner.shape[0] // 2
    return float(np.nanmean(inner[:mid, :]))


def sector_south_mean(field: np.ndarray) -> float:
    """Mean over the southern half of the inner box."""
    inner = _inner(field)
    mid = inner.shape[0] // 2
    return float(np.nanmean(inner[mid:, :]))


def sector_east_mean(field: np.ndarray) -> float:
    """Mean over the eastern half of the inner box."""
    inner = _inner(field)
    mid = inner.shape[1] // 2
    return float(np.nanmean(inner[:, mid:]))


def sector_west_mean(field: np.ndarray) -> float:
    """Mean over the western half of the inner box."""
    inner = _inner(field)
    mid = inner.shape[1] // 2
    return float(np.nanmean(inner[:, :mid]))


def domain_abs_mean(field: np.ndarray) -> float:
    """Mean of the absolute value over the inner box (useful for signed fields)."""
    return float(np.nanmean(np.abs(_inner(field))))


# ---------------------------------------------------------------------------
# Feature registry
# ---------------------------------------------------------------------------

# Ordered dict of feature_name → extraction function
FEATURE_REGISTRY: Dict[str, callable] = {
    "domain_mean":       domain_mean,
    "centre_value":      centre_value,
    "border_north":      border_north_mean,
    "border_south":      border_south_mean,
    "border_east":       border_east_mean,
    "border_west":       border_west_mean,
    "contrast_ew":       contrast_east_west,
    "contrast_sn":       contrast_south_north,
    "sector_north":      sector_north_mean,
    "sector_south":      sector_south_mean,
    "sector_east":       sector_east_mean,
    "sector_west":       sector_west_mean,
    "domain_abs_mean":   domain_abs_mean,
}


def extract_all_features(field: np.ndarray) -> Dict[str, float]:
    """
    Compute all registered scalar features from a 2D field.

    Parameters
    ----------
    field : np.ndarray
        2D array of shape (121, 121) — storm-centred spatial field.

    Returns
    -------
    dict
        {feature_name: scalar_value}
    """
    return {name: func(field) for name, func in FEATURE_REGISTRY.items()}


def get_feature_names():
    """Return ordered list of feature names."""
    return list(FEATURE_REGISTRY.keys())
