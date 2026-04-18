"""
Feature extraction utilities for LEC–field dependence analysis.

Functions to compute scalar summaries from 2D storm-centred fields.
The 30°×30° domain is divided into sub-regions for physically
interpretable features: domain mean, border means, quadrant means,
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

# Border strip width (in grid points, ~1.25° = 5 grid cells)
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


def quadrant_ne_mean(field: np.ndarray) -> float:
    """Mean over the NE quadrant of the inner box."""
    inner = _inner(field)
    mid = inner.shape[0] // 2
    return float(np.nanmean(inner[:mid, mid:]))


def quadrant_nw_mean(field: np.ndarray) -> float:
    """Mean over the NW quadrant of the inner box."""
    inner = _inner(field)
    mid = inner.shape[0] // 2
    return float(np.nanmean(inner[:mid, :mid]))


def quadrant_se_mean(field: np.ndarray) -> float:
    """Mean over the SE quadrant of the inner box."""
    inner = _inner(field)
    mid = inner.shape[0] // 2
    return float(np.nanmean(inner[mid:, mid:]))


def quadrant_sw_mean(field: np.ndarray) -> float:
    """Mean over the SW quadrant of the inner box."""
    inner = _inner(field)
    mid = inner.shape[0] // 2
    return float(np.nanmean(inner[mid:, :mid]))


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
    "quadrant_ne":       quadrant_ne_mean,
    "quadrant_nw":       quadrant_nw_mean,
    "quadrant_se":       quadrant_se_mean,
    "quadrant_sw":       quadrant_sw_mean,
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
