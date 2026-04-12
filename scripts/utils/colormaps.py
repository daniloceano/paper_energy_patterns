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
    '#003c30', '#01665e', '#35978f', '#80cdc1', '#c7eae5', '#f5f5f5', # green side (negative KE advection)
    '#f7f7f7', '#d8daeb', '#b2abd2', '#8073ac', '#542788', '#2d004b' # purple-blue side (positive KE advection)
]
CMAP_KE_ADV = LinearSegmentedColormap.from_list('ke_adv', KE_ADV_COLORS)

# ── EGR total field colormap (sequential: white → orange-red → dark red) ──────
EGR_TOTAL_COLORS = [
    '#FFFFFF', '#FFFACC', '#FFEB80', '#FFD133', '#FFAD00',   # light to orange
    '#FF8000', '#FA4C00', '#E61A00', '#BF001A', '#8C0033',   # orange to dark red
]
CMAP_EGR_TOTAL = LinearSegmentedColormap.from_list('egr_total', EGR_TOTAL_COLORS)

# ── Moisture flux divergence colormap (diverging: blue-green → neutral → brown) 
MOISTURE_FLUX_COLORS = [
    '#003c30', '#01665e', '#35978f', '#80cdc1', '#c7eae5',   # wet side (more moisture)
    '#f5f5f5',                                                 # neutral
    '#f6e8c3', '#dfc27d', '#bf812d', '#8c510a', '#543005',   # dry side (less moisture)
]
CMAP_MOISTURE_FLUX = LinearSegmentedColormap.from_list('moisture_flux', MOISTURE_FLUX_COLORS)

# ── RK criterion colormap (diverging: purple → gray → brown) ──────────────────
RK_COLORS = [
    '#2C1D4F', '#3C6795', '#AABFD3', '#D8E4E6',   # purple side (negative RK)
    '#D7E2E0', '#BBC6B7', '#7E895C', '#434E05',  # brown side (positive RK)
]
CMAP_RK = LinearSegmentedColormap.from_list('rk_criterion', RK_COLORS)
