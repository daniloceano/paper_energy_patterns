"""
Colormap definitions for energy pattern composites.

Provides consistent, centralized colormap definitions used across figures.
"""

from matplotlib.colors import LinearSegmentedColormap

# ── PV anomaly colormap (diverging: blue → neutral → red) ──────────────────
PV_ANOM_COLORS = [
    '#011462', '#106294', '#A7C9DA',   # blue side  (negative anomaly)
    '#E8E1DD',                          # neutral
    '#CDB7B6', '#935B5E', '#5B020A',   # red side   (positive anomaly)
]
CMAP_PV_ANOM = LinearSegmentedColormap.from_list('pv_anom', PV_ANOM_COLORS)

# ── PV total field colormap (sequential: light → dark blue) ────────────────
PV_TOTAL_COLORS = [
    '#f8f9ff', '#dce4f5', '#b9caeb', '#8aaad7',
    '#5b84bc', '#3060a0', '#1a3e7a', '#0b2557', '#040f33',
]
CMAP_PV_TOTAL = LinearSegmentedColormap.from_list('pv_total', PV_TOTAL_COLORS[::-1])

# ── AFC uses PV anomaly colormap for consistency ───────────────────────────
CMAP_AFC = CMAP_PV_ANOM

# ── KE advection colormap (diverging: purple-blue → yellow-green → dark) ────
KE_ADV_COLORS = [
    '#19253D', '#5777BA',  '#98A8E1', '#DBD7FE',   # blue/purple side (negative)
    '#D9E49A', '#899365', '#374030', '#0E1615',   # yellow/green/brown side (positive)
]
CMAP_KE_ADV = LinearSegmentedColormap.from_list('ke_adv', KE_ADV_COLORS)
