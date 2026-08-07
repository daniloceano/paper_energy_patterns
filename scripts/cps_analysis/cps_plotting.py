"""
Shared drawing helpers for the CPS diagrams.

The point of `shade_class_regions` is that the canonical class definitions are
three-dimensional (B, -V_T^L, -V_T^U) while every CPS diagram is a
two-dimensional slice of that space. Shading the PROJECTION of each class onto
the plane being drawn tells the reader which part of the picture each class can
possibly claim, without pretending the third parameter is not there.

    plane B vs -V_T^L      the -V_T^U condition is free, so the projection is
                           just the B and -V_T^L bounds
    plane -V_T^U vs -V_T^L the B condition is free

Because the class specs OVERLAP by construction - a point with
10 < B < 25 and -50 < -V_T^L < 0 satisfies both the extratropical and the
subtropical spec - a cell claimed by more than one class is shaded GREY. That
grey is not decoration: it is where the classification is genuinely ambiguous
and the timestep precedence (tropical > subtropical > extratropical) decides the
label. Cells claimed by no class are left blank; those are the "warm tilted",
"cold shallow" and "warm symmetrical" corners that carry no cyclone type.

Author: Danilo Couto de Souza
Date: August 2026
"""

from typing import Dict, Tuple

import numpy as np
from matplotlib.colors import to_rgb

from scripts.cps_analysis.cps_criteria import (
    CANONICAL,
    CANONICAL_PRECEDENCE,
    PHASE_COLORS,
)

CODE = {"tropical": "TC", "subtropical": "SC", "extratropical": "EC"}

# Grey for cells that more than one class can claim.
AMBIGUOUS_COLOR = "#8a8a8a"

# Faint by design: the shading is a backdrop for the data, not a layer competing
# with it.
DEFAULT_ALPHA = 0.13
GRID = 420


def _mask(values: np.ndarray, interval: Tuple) -> np.ndarray:
    lo, hi = interval
    m = np.ones_like(values, dtype=bool)
    if lo is not None:
        m &= values > lo
    if hi is not None:
        m &= values < hi
    return m


def shade_class_regions(ax, xparam: str, yparam: str,
                        alpha: float = DEFAULT_ALPHA, zorder: float = 0):
    """Shade the projection of each canonical class onto this plane.

    Args:
        ax: target axes, with its limits already set.
        xparam, yparam: which CPS parameters the axes carry ("B", "VTL", "VTU").
        alpha: shading opacity. Faint on purpose.
        zorder: drawn below the data.

    Returns:
        dict mapping class code -> colour, for building a legend.
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    xs = np.linspace(x0, x1, GRID)
    ys = np.linspace(y0, y1, GRID)
    X, Y = np.meshgrid(xs, ys)
    values = {xparam: X, yparam: Y}

    masks = {}
    for cls in CANONICAL_PRECEDENCE:
        m = np.ones_like(X, dtype=bool)
        for param, interval in CANONICAL[cls].items():
            if param in values:            # the free parameter imposes nothing
                m &= _mask(values[param], interval)
        masks[cls] = m

    count = sum(m.astype(int) for m in masks.values())
    rgba = np.zeros((*X.shape, 4))

    for cls, m in masks.items():
        sole = m & (count == 1)
        rgba[sole, :3] = to_rgb(PHASE_COLORS[CODE[cls]])
        rgba[sole, 3] = alpha

    over = count >= 2
    rgba[over, :3] = to_rgb(AMBIGUOUS_COLOR)
    rgba[over, 3] = alpha

    ax.imshow(rgba, extent=(x0, x1, y0, y1), origin="lower", aspect="auto",
              interpolation="nearest", zorder=zorder)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)

    return {CODE[c]: PHASE_COLORS[CODE[c]] for c in CANONICAL_PRECEDENCE}


def region_legend_handles(include_ambiguous: bool = True) -> list:
    """Patch handles describing the shaded regions."""
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=PHASE_COLORS["EC"], alpha=0.35, edgecolor="none",
              label="extratropical region"),
        Patch(facecolor=PHASE_COLORS["SC"], alpha=0.35, edgecolor="none",
              label="subtropical region"),
        Patch(facecolor=PHASE_COLORS["TC"], alpha=0.35, edgecolor="none",
              label="tropical region"),
    ]
    if include_ambiguous:
        handles.append(Patch(facecolor=AMBIGUOUS_COLOR, alpha=0.35,
                             edgecolor="none",
                             label="claimed by more than one class"))
    return handles
