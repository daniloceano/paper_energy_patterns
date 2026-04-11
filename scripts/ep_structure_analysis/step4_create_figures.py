"""
Step 4: Create EP1, EP2, EP3, and EPALL Composite Comparison Figures

For each diagnostic field, creates multi-panel composite figures:

  TOTAL FIELD FIGURES (4 panels):
    - EP1, EP2, EP3, EPALL

  EPALL-RELATIVE ANOMALY FIGURES (3 panels):
    - EP1 - EPALL, EP2 - EPALL, EP3 - EPALL

Fields plotted (total fields):
  1. EGR (500–850 hPa, Besson et al. 2021) — shaded
  2. PV at 200 hPa                         — shaded + 2 PVU contour
  3. PV at 850 hPa                         — shaded
  4. Temperature advection 850             — shaded (warm red / cold blue)
  5. Moisture flux + divergence 975        — panels with specific humidity and divergence
  6. SLP                                   — contours
  7. RK criterion at 250 hPa              — shaded (negative = unstable)
  8. KE advection at 250 hPa              — shaded (positive = acceleration)
  9. AFC at 250 hPa (Orlanski & Katzfey 1991) — shaded (positive = eddy KE source)
  10. BtCR at 250 hPa                       — barotropic critical region

EPALL-relative anomaly fields (NEW April 2026):
  - EPx anomaly = EPx composite - EPALL composite
  - This isolates what distinguishes each EP from the "average" cyclone
  - Applied to: EGR, PV, temperature advection, moisture flux, SLP, etc.

Each panel includes a 15°×15° dashed box indicating the LEC computation domain.

Output:
  figures/ep_structure/composite_*.png

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings
import logging
import argparse
from datetime import datetime

from scripts.utils.ep_mapping import ALL_EPS, EP_LABELS, EP_COLORS, EPALL_LABEL

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"
FIGURES_DIR = PROJECT_ROOT / "figures" / "ep_structure"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DPI = 300
DOMAIN_SIZE = 30.0  # degrees
LEC_BOX_HALF = 7.5  # 15°×15° centred box

# Plotting style
plt.rcParams.update({
    "font.size": 10,
    "font.family": "sans-serif",
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 100,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "axes.grid": False,
})

# Vector plot parameters
VECTOR_SKIP = 16
VECTOR_SCALE = 250
VECTOR_WIDTH = 0.004

EP_PANEL_COLORS = {"EP1": "gold", "EP2": "dodgerblue", "EP3": "limegreen", "EPALL": "gray"}
EP_PANEL_LABELS = {"EP1": "EP1 (High conversions)", "EP2": "EP2 (Moderate)", "EP3": "EP3 (Weak)", "EPALL": "All Cyclones"}


# ============================================================================
# HELPERS
# ============================================================================

def _safe_symmetric_levels(absmax, n_levels=21, min_absmax=1e-10):
    """
    Create symmetric contour levels, handling edge case where absmax is zero.
    
    Parameters
    ----------
    absmax : float
        Maximum absolute value for symmetric range.
    n_levels : int
        Number of contour levels.
    min_absmax : float
        Minimum absmax to prevent invalid contour levels.
    
    Returns
    -------
    np.ndarray
        Contour levels from -absmax to absmax.
    """
    if np.isnan(absmax) or absmax < min_absmax:
        absmax = min_absmax
    return np.linspace(-absmax, absmax, n_levels)


def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"ep_structure_figures_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )
    return log_file


def load_composites():
    """Load precomputed EP1, EP2, EP3, and EPALL composites (canonical central-timestep method)."""
    datasets = {}
    # Load canonical composites (no mode suffix)
    for ep in ["ep1", "ep2", "ep3", "epall"]:
        f = DATA_DIR / f"precomputed_composites_{ep}.nc"
        if not f.exists():
            logging.warning(f"   ⚠ File not found: {f.name}")
            continue
        datasets[ep.upper()] = xr.open_dataset(f)
        mb = f.stat().st_size / 1024 ** 2
        logging.info(f"   Loaded {ep.upper()}: {f.name} ({mb:.1f} MB)")
    
    if not datasets:
        logging.error("❌ No composite files found. Expected precomputed_composites_{ep1,ep2,ep3,epall}.nc")
        logging.error("   Run step3_precompute_composites.py first.")
        return None
    return datasets


def _add_lec_box(ax):
    """Add dashed 15°×15° LEC domain box centred at origin."""
    rect = mpatches.Rectangle(
        (-LEC_BOX_HALF, -LEC_BOX_HALF),
        2 * LEC_BOX_HALF,
        2 * LEC_BOX_HALF,
        linewidth=1.5,
        edgecolor="black",
        facecolor="none",
        linestyle="--",
        zorder=10,
        label="LEC domain (15°×15°)",
    )
    ax.add_patch(rect)


def _figure_path(base_name):
    """Return the figure output path for a given base filename."""
    stem = base_name.replace(".png", "")
    return FIGURES_DIR / f"{stem}.png"


def _decorate_ax(ax, title, xlabel=True, ylabel=True):
    """Common axis decoration."""
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_aspect("equal")
    if xlabel:
        ax.set_xlabel("Relative Longitude (°)")
    if ylabel:
        ax.set_ylabel("Relative Latitude (°)")
    _add_lec_box(ax)
    ax.axhline(0, color="gray", lw=0.5, ls=":", alpha=0.5)
    ax.axvline(0, color="gray", lw=0.5, ls=":", alpha=0.5)


def _add_cbar(fig, ax, im, label):
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.1)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label(label, fontsize=9)
    return cbar


def _get_available_eps(datasets):
    """Return list of available EP keys in standard order."""
    all_possible = ["EP1", "EP2", "EP3", "EPALL"]
    return [ep for ep in all_possible if ep in datasets]


def _create_multipanel_fig(n_panels, panel_width=7, panel_height=6):
    """Create figure with variable number of panels."""
    if n_panels <= 2:
        fig, axes = plt.subplots(1, n_panels, figsize=(panel_width * n_panels, panel_height))
    elif n_panels <= 4:
        ncols = 2
        nrows = (n_panels + 1) // 2
        fig, axes = plt.subplots(nrows, ncols, figsize=(panel_width * ncols, panel_height * nrows))
        axes = axes.flatten()
    else:
        ncols = 3
        nrows = (n_panels + 2) // 3
        fig, axes = plt.subplots(nrows, ncols, figsize=(panel_width * ncols, panel_height * nrows))
        axes = axes.flatten()
    
    if n_panels == 1:
        axes = [axes]
    return fig, axes


# ============================================================================
# FIGURE FUNCTIONS
# ============================================================================

def figure_wind250(datasets):
    """250 hPa total wind composite: EP1, EP2, EP3, EPALL (Bentley style).

    Produces wind-speed shading using a Bentley-inspired colormap that only
    assigns colour to winds ≥ 30 m/s (jet threshold); sub-threshold regions
    appear white.  The palette transitions from light blue (30 m/s) through
    dark blue, pink, and red to dark gray (≥ 100 m/s), approximating the
    style used in Bentley et al. (2009).  Wind barbs are sub-sampled every
    ~3° of the storm-relative grid and a solid contour marks 30 m/s.

    Coordinates are storm-relative (x = Δlon, y = Δlat from cyclone centre),
    consistent with all other composite figures in this module.
    """
    logging.info("  Creating 250 hPa total wind composite figure (Bentley style)...")

    eps = _get_available_eps(datasets)
    if "u_250" not in datasets[eps[0]] or "v_250" not in datasets[eps[0]]:
        logging.warning("    ⚠  u_250/v_250 not in composites — skipping wind250 figure")
        return

    # Bentley-inspired colormap: only ≥ 30 m/s receives colour; below → white
    _bentley_colors = [
        (0.85, 0.92, 1.00),   # 30 m/s : very light blue
        (0.53, 0.81, 0.98),   # 40 m/s : sky blue
        (0.20, 0.60, 0.90),   # 50 m/s : medium blue
        (0.10, 0.35, 0.75),   # 60 m/s : dark blue
        (0.95, 0.70, 0.80),   # 70 m/s : light pink
        (0.90, 0.30, 0.40),   # 80 m/s : red-pink
        (0.65, 0.05, 0.10),   # 90 m/s : deep red
        (0.35, 0.35, 0.35),   # 100 m/s: dark gray
    ]
    cmap_bentley = LinearSegmentedColormap.from_list("bentley_wind", _bentley_colors)
    cmap_bentley.set_under("white")     # below 30 m/s → white (invisible)

    jet_threshold = 30                  # m/s
    levels = np.arange(30, 115, 5)

    fig, axes = _create_multipanel_fig(len(eps))

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        u = ds["u_250"].values
        v = ds["v_250"].values
        wspd = np.hypot(u, v)

        # Wind-speed shading (only ≥ 30 m/s receives colour)
        im = ax.contourf(x, y, wspd, levels=levels, cmap=cmap_bentley, extend="max")

        # 30 m/s jet-core contour
        ax.contour(x, y, wspd, levels=[jet_threshold],
                   colors="black", linewidths=1.4, linestyles="solid")

        # Wind barbs — sub-sample every ~8 grid points (~2–3° at 0.25° res)
        step = max(1, len(x) // 16)
        skip = slice(None, None, step)
        ax.barbs(
            x[skip], y[skip],
            u[skip, skip], v[skip, skip],
            length=5, barbcolor="black", flagcolor="black", linewidth=0.6,
        )

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — 250 hPa wind (m s⁻¹)  [n={n}]",
                     ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "Wind speed (m s⁻¹)")

    fig.suptitle("250 hPa Total Wind — composite mean (Bentley style)",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_wind250.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_egr(datasets):
    """EGR composite: EP1, EP2, EP3, EPALL with 850 hPa wind vectors.

    EGR is computed over the 500–850 hPa layer following Besson et al. (2021).
    """
    logging.info("  Creating EGR composite figure (500–850 hPa layer)...")

    eps = _get_available_eps(datasets)
    if "egr" not in datasets[eps[0]]:
        logging.warning("    ⚠  EGR not in composites — skipping")
        return

    fig, axes = _create_multipanel_fig(len(eps))

    vmin, vmax = None, None
    for ep in eps:
        ds = datasets[ep]
        d = ds["egr"].values
        lo = np.nanpercentile(d, 1)
        hi = np.nanpercentile(d, 99)
        vmin = lo if vmin is None else min(vmin, lo)
        vmax = hi if vmax is None else max(vmax, hi)

    clevels = np.linspace(max(vmin, 0), vmax, 21)  # EGR ≥ 0

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        im = ax.contourf(x, y, ds["egr"].values, levels=clevels, cmap="YlOrRd", extend="both")

        # 850 hPa winds (lower boundary of the EGR layer)
        if "u_850" in ds and "v_850" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_850"].values[::s, ::s], ds["v_850"].values[::s, ::s],
                      color="black", alpha=0.8, scale=100, width=VECTOR_WIDTH)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — EGR 500–850 hPa  [n={n}]", ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "EGR (day⁻¹)")

    fig.suptitle("Eady Growth Rate (500–850 hPa, Besson et al. 2021)",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_egr.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_pv200(datasets):
    """PV at 200 hPa: EP1, EP2, EP3, EPALL with 250 hPa wind vectors."""
    logging.info("  Creating PV@200 hPa composite figure...")

    eps = _get_available_eps(datasets)
    fig, axes = _create_multipanel_fig(len(eps))

    # Common colour scale
    vmin, vmax = None, None
    for ep in eps:
        d = datasets[ep]["pv_200"].values * 1e6  # PVU
        lo, hi = np.nanpercentile(d, 2), np.nanpercentile(d, 98)
        vmin = lo if vmin is None else min(vmin, lo)
        vmax = hi if vmax is None else max(vmax, hi)
    clevels = np.linspace(vmin, vmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values
        pv = ds["pv_200"].values * 1e6

        im = ax.contourf(x, y, pv, levels=clevels, cmap="RdYlBu_r", extend="both")

        # 2 PVU contour (dynamical tropopause)
        cs = ax.contour(x, y, pv, levels=[2.0], colors="black", linewidths=2, linestyles="--")
        ax.clabel(cs, inline=True, fontsize=9, fmt="%.0f PVU")

        # 250 hPa winds
        if "u_250" in ds and "v_250" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_250"].values[::s, ::s], ds["v_250"].values[::s, ::s],
                      color="gray", alpha=0.8, scale=VECTOR_SCALE, width=VECTOR_WIDTH)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — PV at 200 hPa  [n={n}]", ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "PV (PVU)")

    fig.suptitle("Potential Vorticity at 200 hPa", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_pv200.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_pv850(datasets):
    """PV at 850 hPa: EP1, EP2, EP3, EPALL with 850 hPa wind vectors."""
    logging.info("  Creating PV@850 hPa composite figure...")

    eps = _get_available_eps(datasets)
    fig, axes = _create_multipanel_fig(len(eps))

    vmin, vmax = None, None
    for ep in eps:
        d = datasets[ep]["pv_850"].values * 1e6
        lo, hi = np.nanpercentile(d, 2), np.nanpercentile(d, 98)
        vmin = lo if vmin is None else min(vmin, lo)
        vmax = hi if vmax is None else max(vmax, hi)
    clevels = np.linspace(vmin, vmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values
        pv = ds["pv_850"].values * 1e6

        im = ax.contourf(x, y, pv, levels=clevels, cmap="RdYlBu_r", extend="both")

        # 850 hPa winds
        if "u_850" in ds and "v_850" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_850"].values[::s, ::s], ds["v_850"].values[::s, ::s],
                      color="black", alpha=0.7, scale=100, width=VECTOR_WIDTH)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — PV at 850 hPa  [n={n}]", ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "PV (PVU)")

    fig.suptitle("Potential Vorticity at 850 hPa", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_pv850.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_advT850(datasets):
    """Temperature advection at 850 hPa: EP1, EP2, EP3, EPALL."""
    logging.info("  Creating temp advection @850 hPa composite figure...")

    eps = _get_available_eps(datasets)
    fig, axes = _create_multipanel_fig(len(eps))

    # Symmetric colour scale
    absmax = 0
    for ep in eps:
        d = datasets[ep]["adv_T_850"].values * 3600  # K/h
        absmax = max(absmax, np.nanpercentile(np.abs(d), 98))
    clevels = _safe_symmetric_levels(absmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values
        advT = ds["adv_T_850"].values * 3600  # K/h

        im = ax.contourf(x, y, advT, levels=clevels, cmap="RdBu_r", extend="both")
        ax.contour(x, y, advT, levels=[0], colors="black", linewidths=1.2)

        # 850 hPa winds
        if "u_850" in ds and "v_850" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_850"].values[::s, ::s], ds["v_850"].values[::s, ::s],
                      color="black", alpha=0.7, scale=100, width=VECTOR_WIDTH)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — T advection at 850 hPa  [n={n}]", ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "−V·∇T (K h⁻¹)")

    fig.suptitle("Temperature Advection at 850 hPa", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_advT850.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_moisture(datasets):
    """Moisture and moisture flux divergence at 975 hPa: EP1, EP2, EP3, EPALL."""
    logging.info("  Creating moisture flux composite figure...")

    eps = _get_available_eps(datasets)
    nrows = 2  # q_975 and div_q_975
    ncols = len(eps)
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 12))
    if ncols == 1:
        axes = axes.reshape(nrows, 1)

    # Row 1: Specific humidity (g/kg) with wind vectors
    q_min, q_max = None, None
    for ep in eps:
        ds = datasets[ep]
        if "q_975" in ds:
            q975_gkg = ds["q_975"].values * 1000.0
            lo, hi = np.nanpercentile(q975_gkg, 5), np.nanpercentile(q975_gkg, 95)
            q_min = lo if q_min is None else min(q_min, lo)
            q_max = hi if q_max is None else max(q_max, hi)
    q_levels = np.linspace(q_min or 0, q_max or 1, 21)
    
    for i, ep in enumerate(eps):
        ax = axes[0, i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        if "q_975" not in ds:
            ax.text(0.5, 0.5, "q_975 not available", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12)
            continue

        # Convert to g/kg
        q975_gkg = ds["q_975"].values * 1000.0
        
        im = ax.contourf(x, y, q975_gkg, levels=q_levels, cmap="YlGnBu", extend="both")
        
        # 975 hPa wind vectors
        if "u_975" in ds and "v_975" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_975"].values[::s, ::s], ds["v_975"].values[::s, ::s],
                      color="black", alpha=0.7, scale=80, width=VECTOR_WIDTH)
        
        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — q at 975 hPa  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "q (g kg⁻¹)")
    
    # Row 2: Moisture flux divergence (g kg⁻¹ s⁻¹)
    # Symmetric color scale
    absmax_div = 0
    for ep in eps:
        if "div_q_975" in datasets[ep]:
            d = datasets[ep]["div_q_975"].values
            absmax_div = max(absmax_div, np.nanpercentile(np.abs(d), 95))
    
    div_levels = np.linspace(-absmax_div, absmax_div, 21) if absmax_div > 0 else np.linspace(-1e-10, 1e-10, 21)
    
    for i, ep in enumerate(eps):
        ax = axes[1, i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        if "div_q_975" not in ds:
            ax.text(0.5, 0.5, "div_q_975 not available", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12)
            continue

        div_q = ds["div_q_975"].values
        
        im = ax.contourf(x, y, div_q, levels=div_levels, cmap="RdBu_r", extend="both")
        
        if absmax_div > 0:
            # Contour convergence zones (negative divergence)
            cs_conv = ax.contour(x, y, div_q, levels=[-absmax_div*0.5, -absmax_div*0.25],
                                 colors="blue", linewidths=1.5, linestyles="--")
            ax.clabel(cs_conv, inline=True, fontsize=8, fmt="%.1e")
            
            # Contour divergence zones (positive divergence)
            cs_div = ax.contour(x, y, div_q, levels=[absmax_div*0.25, absmax_div*0.5],
                                colors="red", linewidths=1.5, linestyles="--")
            ax.clabel(cs_div, inline=True, fontsize=8, fmt="%.1e")
        
        # 975 hPa wind vectors
        if "u_975" in ds and "v_975" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_975"].values[::s, ::s], ds["v_975"].values[::s, ::s],
                      color="black", alpha=0.6, scale=80, width=VECTOR_WIDTH)
        
        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — Moisture flux div at 975 hPa  [n={n}]",
                     ylabel=(i == 0))
        _add_cbar(fig, ax, im, "∇·(qV) (g kg⁻¹ s⁻¹)")
    
    fig.suptitle("Low-Level Moisture Transport at 975 hPa", 
                 fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    out = _figure_path("composite_moisture_flux.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_slp(datasets):
    """SLP composite: EP1, EP2, EP3, EPALL with 850 hPa wind vectors."""
    logging.info("  Creating SLP composite figure...")

    eps = _get_available_eps(datasets)
    fig, axes = _create_multipanel_fig(len(eps))

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        if "msl" not in ds:
            ax.text(0.5, 0.5, "SLP not available", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12)
            continue

        msl_hpa = ds["msl"].values / 100.0
        slp_levels = np.arange(
            np.floor(np.nanmin(msl_hpa) / 2) * 2,
            np.ceil(np.nanmax(msl_hpa) / 2) * 2 + 2,
            2,
        )

        cs = ax.contour(x, y, msl_hpa, levels=slp_levels, colors="black", linewidths=1.2)
        ax.clabel(cs, inline=True, fontsize=8, fmt="%.0f")

        # Fill with subtle colourmap
        im = ax.contourf(x, y, msl_hpa, levels=slp_levels, cmap="coolwarm_r", alpha=0.4, extend="both")

        # 850 hPa winds
        if "u_850" in ds and "v_850" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_850"].values[::s, ::s], ds["v_850"].values[::s, ::s],
                      color="black", alpha=0.7, scale=100, width=VECTOR_WIDTH)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — SLP + 850 hPa wind  [n={n}]", ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "SLP (hPa)")

    fig.suptitle("Sea Level Pressure", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_slp.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_rk_criterion(datasets):
    """Rayleigh-Kuo criterion at 250 hPa: EP1, EP2, EP3, EPALL."""
    logging.info("  Creating RK criterion @250 hPa composite figure...")
    
    eps = _get_available_eps(datasets)
    # Check if RK criterion exists
    if "rk_criterion_250" not in datasets[eps[0]]:
        logging.warning("    ⚠️  RK criterion not in composites - skipping")
        return

    fig, axes = _create_multipanel_fig(len(eps))

    # Symmetric color scale around zero
    absmax = 0
    for ep in eps:
        data = datasets[ep]["rk_criterion_250"].values
        absmax = max(absmax, np.nanmax(np.abs(data)))
    clevels = _safe_symmetric_levels(absmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        
        rk = ds["rk_criterion_250"].values
        x = ds.coords["x"].values
        y = ds.coords["y"].values
        
        # Shaded: RK criterion (negative = unstable)
        im = ax.contourf(x, y, rk, levels=clevels, cmap="RdBu_r", extend="both")
        
        # Zero contour
        ax.contour(x, y, rk, levels=[0], colors="black", linewidths=1.5, linestyles="-")
        
        # Wind vectors at 250 hPa
        if "u_250" in ds and "v_250" in ds:
            u = ds["u_250"].values
            v = ds["v_250"].values
            skip = slice(None, None, VECTOR_SKIP)
            ax.quiver(
                x[skip], y[skip], u[skip, skip], v[skip, skip],
                scale=VECTOR_SCALE, width=VECTOR_WIDTH, color="gray", alpha=0.6, zorder=5
            )
        
        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — RK criterion at 250 hPa  [n={n}]",
                     xlabel=True, ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "RK criterion (s⁻¹ m⁻¹)")

    fig.suptitle("Rayleigh-Kuo Instability Criterion at 250 hPa", 
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_rk_criterion.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_ke_advection(datasets):
    """Kinetic energy advection at 250 hPa: EP1, EP2, EP3, EPALL."""
    logging.info("  Creating KE advection @250 hPa composite figure...")
    
    eps = _get_available_eps(datasets)
    # Check if KE advection exists
    if "ke_adv_250" not in datasets[eps[0]]:
        logging.warning("    ⚠️  KE advection not in composites - skipping")
        return

    fig, axes = _create_multipanel_fig(len(eps))

    # Symmetric color scale
    absmax = 0
    for ep in eps:
        data = datasets[ep]["ke_adv_250"].values
        absmax = max(absmax, np.nanmax(np.abs(data)))
    clevels = _safe_symmetric_levels(absmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        
        ke_adv = ds["ke_adv_250"].values
        x = ds.coords["x"].values
        y = ds.coords["y"].values
        
        # Shaded: KE advection
        im = ax.contourf(x, y, ke_adv, levels=clevels, cmap="PuOr_r", extend="both")
        
        # Zero contour
        ax.contour(x, y, ke_adv, levels=[0], colors="black", linewidths=1.5, linestyles="-")
        
        # Wind vectors at 250 hPa
        if "u_250" in ds and "v_250" in ds:
            u = ds["u_250"].values
            v = ds["v_250"].values
            skip = slice(None, None, VECTOR_SKIP)
            ax.quiver(
                x[skip], y[skip], u[skip, skip], v[skip, skip],
                scale=VECTOR_SCALE, width=VECTOR_WIDTH, color="gray", alpha=0.6, zorder=5
            )
        
        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — KE advection at 250 hPa  [n={n}]",
                     xlabel=True, ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, "KE advection (m² s⁻³)")

    fig.suptitle("Kinetic Energy Advection at 250 hPa", 
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path("composite_ke_advection.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_afc(datasets):
    """AFC at 250 hPa: EP1, EP2, EP3 comparison, with total composite 250 hPa wind vectors.

    AFC = −∇·(v_ag' φ')  where v_ag' = v' − v_g' is the ageostrophic eddy wind
    and φ' = Φ − Φm is the geopotential departure from the 30-year monthly
    climatology.  Positive values indicate convergence of ageostrophic
    geopotential flux → source of eddy kinetic energy.

    Wind vectors overlaid are the **total** composite-mean 250 hPa wind
    (u_250, v_250), not the eddy perturbation.

    NOTE: AFC uses climatology-based decomposition by construction (Orlanski &
    Katzfey 1991). It is NOT converted to EPALL-relative anomalies because
    the ageostrophic flux requires a climatological reference.

    Reference: Orlanski & Katzfey (1991), Orlanski & Sheldon (1993).
    """
    logging.info("  Creating AFC @250 hPa composite figure...")

    # Get EPs that have AFC data
    eps = [ep for ep in ["EP1", "EP2", "EP3"] if ep in datasets and "afc_250" in datasets[ep]]
    
    if not eps:
        logging.warning(
            "    ⚠  afc_250 not in any composites — skipping.\n"
            "      Run step2_1 (download climatology) then re-run step3."
        )
        return

    n_panels = len(eps)
    fig, axes = _create_multipanel_fig(n_panels, panel_width=7, panel_height=6)
    if n_panels == 1:
        axes = [axes]

    # Symmetric colour scale: use 98th-percentile of |AFC| across all EPs
    absmax = 0.0
    for ep in eps:
        d = datasets[ep]["afc_250"].values
        absmax = max(absmax, np.nanpercentile(np.abs(d), 98))
    
    # Safety: ensure valid contour levels
    if absmax < 1e-10:
        absmax = 1e-5  # fallback for all-zero data
    clevels = _safe_symmetric_levels(absmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x = ds.coords["x"].values
        y = ds.coords["y"].values
        afc = ds["afc_250"].values

        # Shaded AFC
        im = ax.contourf(x, y, afc, levels=clevels, cmap="RdBu_r", extend="both")

        # Zero contour
        ax.contour(x, y, afc, levels=[0], colors="black", linewidths=1.5, linestyles="-")

        # 250 hPa wind vectors
        if "u_250" in ds and "v_250" in ds:
            skip = slice(None, None, VECTOR_SKIP)
            ax.quiver(
                x[skip], y[skip],
                ds["u_250"].values[skip, skip], ds["v_250"].values[skip, skip],
                scale=VECTOR_SCALE, width=VECTOR_WIDTH, color="gray", alpha=0.6, zorder=5,
            )

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — AFC at 250 hPa + 250 hPa total wind  [n={n}]",
                     xlabel=True, ylabel=(i == 0))
        _add_cbar(fig, ax, im, "AFC (m² s⁻³)")

    # Hide unused axes if any
    for j in range(len(eps), len(axes)):
        axes[j].set_visible(False)

    ep_list = ", ".join(eps)
    fig.suptitle(
        f"Ageostrophic Flux Convergence at 250 hPa (Orlanski & Katzfey 1991) — {ep_list}",
        fontsize=13, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    out = _figure_path("composite_afc_250.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


# ============================================================================
# ANOMALY FIGURE FUNCTIONS (EPALL-relative)
# ============================================================================

def _epall_anom_fig(datasets, var_key, scale_factor, unit_label, suptitle, out_name,
                    cmap="RdBu_r"):
    """1×3 EPALL-relative anomaly figure: EP1−EPALL | EP2−EPALL | EP3−EPALL.

    Parameters
    ----------
    datasets     : dict with keys "EP1", "EP2", "EP3" → xr.Dataset
    var_key      : base variable name (without _minus_epall suffix)
    scale_factor : multiply raw values before plotting (e.g. 3600 for K/s→K/h)
    unit_label   : colorbar label string
    suptitle     : figure super-title
    out_name     : output filename (no directory)
    cmap         : diverging colormap name
    """
    anom_key = f"{var_key}_minus_epall"
    eps = [ep for ep in ["EP1", "EP2", "EP3"] if ep in datasets and anom_key in datasets[ep]]
    if not eps:
        logging.warning(f"    ⚠  {anom_key} not in composites — skipping EPALL-relative figure")
        return

    n_eps = len(eps)
    fig, axes_arr = plt.subplots(1, n_eps, figsize=(6 * n_eps, 6))
    axes = list(axes_arr) if n_eps > 1 else [axes_arr]

    # Symmetric colour limits from 98th-percentile of |anomaly| across all EPs
    absmax = 0.0
    for ep in eps:
        d = datasets[ep][anom_key].values * scale_factor
        absmax = max(absmax, np.nanpercentile(np.abs(d), 98))
    if absmax == 0.0:
        absmax = 1e-10
    clevels = _safe_symmetric_levels(absmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.coords["x"].values, ds.coords["y"].values
        data = ds[anom_key].values * scale_factor

        im = ax.contourf(x, y, data, levels=clevels, cmap=cmap, extend="both")
        ax.contour(x, y, data, levels=[0], colors="black", linewidths=1.2)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} − EPALL  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, unit_label)

    fig.suptitle(suptitle, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path(out_name)
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_egr_epall_anom(datasets):
    """EGR EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating EGR EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="egr",
        scale_factor=1.0,
        unit_label="EGR − EPALL (day⁻¹)",
        suptitle="Eady Growth Rate — EPx − EPALL Anomaly",
        out_name="composite_egr_anom_epall.png",
        cmap="RdBu_r",
    )


def figure_pv200_epall_anom(datasets):
    """PV@200 EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating PV@200 EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="pv_200",
        scale_factor=1e6,
        unit_label="PV − EPALL (PVU)",
        suptitle="Potential Vorticity at 200 hPa — EPx − EPALL Anomaly",
        out_name="composite_pv200_anom_epall.png",
        cmap="RdBu_r",
    )


def figure_pv850_epall_anom(datasets):
    """PV@850 EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating PV@850 EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="pv_850",
        scale_factor=1e6,
        unit_label="PV − EPALL (PVU)",
        suptitle="Potential Vorticity at 850 hPa — EPx − EPALL Anomaly",
        out_name="composite_pv850_anom_epall.png",
        cmap="RdBu_r",
    )


def figure_advT850_epall_anom(datasets):
    """Temperature advection EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating temperature advection EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="adv_T_850",
        scale_factor=3600.0,
        unit_label="(−V·∇T) − EPALL (K h⁻¹)",
        suptitle="Temperature Advection at 850 hPa — EPx − EPALL Anomaly",
        out_name="composite_advT850_anom_epall.png",
        cmap="RdBu_r",
    )


def figure_slp_epall_anom(datasets):
    """SLP EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating SLP EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="msl",
        scale_factor=0.01,  # Pa to hPa
        unit_label="SLP − EPALL (hPa)",
        suptitle="Sea Level Pressure — EPx − EPALL Anomaly",
        out_name="composite_slp_anom_epall.png",
        cmap="RdBu_r",
    )


def figure_ke_advection_epall_anom(datasets):
    """KE advection EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating KE advection EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="ke_adv_250",
        scale_factor=1.0,
        unit_label="KE adv − EPALL (m² s⁻³)",
        suptitle="Kinetic Energy Advection at 250 hPa — EPx − EPALL Anomaly",
        out_name="composite_ke_advection_anom_epall.png",
        cmap="PuOr_r",
    )


def figure_rk_criterion_epall_anom(datasets):
    """RK criterion EPALL-relative anomaly: EP1−EPALL | EP2−EPALL | EP3−EPALL."""
    logging.info("  Creating RK criterion EPALL-relative anomaly figure...")
    _epall_anom_fig(
        datasets,
        var_key="rk_criterion_250",
        scale_factor=1.0,
        unit_label="RK − EPALL (s⁻¹ m⁻¹)",
        suptitle="Rayleigh-Kuo Criterion at 250 hPa — EPx − EPALL Anomaly",
        out_name="composite_rk_criterion_anom_epall.png",
        cmap="RdBu_r",
    )


# ============================================================================
# LEGACY CLIMATOLOGY-BASED ANOMALY FIGURES (kept for AFC, BtCR)
# ============================================================================

def _anom_fig(datasets, var_key, scale_factor, unit_label, suptitle, out_name,
              cmap="RdBu_r", wind_u=None, wind_v=None, wind_scale=None):
    """Generic multi-panel climatology-based anomaly figure builder.
    
    NOTE: This is the legacy climatology-based anomaly definition.
    Kept for diagnostics that inherently require climatological decomposition
    (AFC, BtCR).

    Parameters
    ----------
    datasets     : dict with EP keys → xr.Dataset
    var_key      : variable name inside each dataset
    scale_factor : multiply raw values before plotting (e.g. 3600 for K/s→K/h)
    unit_label   : colorbar label string
    suptitle     : figure super-title
    out_name     : output filename (no directory)
    cmap         : diverging colormap name
    wind_u/v     : variable keys for optional quiver overlay
    wind_scale   : quiver scale (default: VECTOR_SCALE)
    """
    eps = [ep for ep in ["EP1", "EP2", "EP3"] if ep in datasets and var_key in datasets[ep]]
    if not eps:
        logging.warning(f"    ⚠  {var_key} not in composites — skipping anomaly figure")
        return

    fig, axes = _create_multipanel_fig(len(eps), panel_width=6, panel_height=6)

    # Symmetric colour limits from 98th-percentile of |anomaly| across all EPs
    absmax = 0.0
    for ep in eps:
        d = datasets[ep][var_key].values * scale_factor
        absmax = max(absmax, np.nanpercentile(np.abs(d), 98))
    if absmax == 0.0:
        absmax = 1e-10  # guard against all-zero fields
    clevels = _safe_symmetric_levels(absmax, 21)
    wscale = wind_scale if wind_scale is not None else VECTOR_SCALE

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.coords["x"].values, ds.coords["y"].values
        data = ds[var_key].values * scale_factor

        im = ax.contourf(x, y, data, levels=clevels, cmap=cmap, extend="both")
        ax.contour(x, y, data, levels=[0], colors="black", linewidths=1.2)

        if wind_u and wind_v and wind_u in ds and wind_v in ds:
            skip = slice(None, None, VECTOR_SKIP)
            ax.quiver(
                x[skip], y[skip],
                ds[wind_u].values[skip, skip], ds[wind_v].values[skip, skip],
                scale=wscale, width=VECTOR_WIDTH, color="gray", alpha=0.6, zorder=5,
            )

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep}  [n={n}]", ylabel=(i % 2 == 0))
        _add_cbar(fig, ax, im, unit_label)

    fig.suptitle(suptitle, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path(out_name)  # Use _figure_path to add mode suffix
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_pv200_anom(datasets):
    """PV anomaly at 200 hPa: climatology-based (legacy)."""
    logging.info("  Creating PV anomaly @200 hPa (climatology-based)...")
    _anom_fig(
        datasets,
        var_key="pv_200_anom",
        scale_factor=1e6,
        unit_label="ΔPV (PVU)",
        suptitle="PV Anomaly at 200 hPa (departure from 1991–2020 climatology)",
        out_name="composite_pv200_anom.png",
        cmap="RdBu_r",
        wind_u="u_250_prime",
        wind_v="v_250_prime",
        wind_scale=VECTOR_SCALE,
    )


def figure_pv850_anom(datasets):
    """PV anomaly at 850 hPa: climatology-based (legacy)."""
    logging.info("  Creating PV anomaly @850 hPa (climatology-based)...")
    _anom_fig(
        datasets,
        var_key="pv_850_anom",
        scale_factor=1e6,
        unit_label="ΔPV (PVU)",
        suptitle="PV Anomaly at 850 hPa (departure from 1991–2020 climatology)",
        out_name="composite_pv850_anom.png",
        cmap="RdBu_r",
        wind_u="u_850_prime",
        wind_v="v_850_prime",
        wind_scale=100,
    )


def figure_advT850_anom(datasets):
    """Temperature advection anomaly at 850 hPa: climatology-based (legacy)."""
    logging.info("  Creating temp advection anomaly @850 hPa (climatology-based)...")
    _anom_fig(
        datasets,
        var_key="adv_T_850_anom",
        scale_factor=3600.0,
        unit_label="Δ(−V·∇T) (K h⁻¹)",
        suptitle="Temperature Advection Anomaly at 850 hPa (departure from climatology)",
        out_name="composite_advT850_anom.png",
        cmap="RdBu_r",
        wind_u="u_850_prime",
        wind_v="v_850_prime",
        wind_scale=100,
    )


def figure_moisture_anom(datasets):
    """Moisture flux divergence anomaly at 975 hPa: EP1 vs EP2, with 975 hPa anomaly wind vectors."""
    logging.info("  Creating moisture flux divergence anomaly @975 hPa composite figure...")
    _anom_fig(
        datasets,
        var_key="div_q_975_anom",
        scale_factor=1.0,
        unit_label="Δ∇·(q′V′) (g kg⁻¹ s⁻¹)",
        suptitle="Moisture Flux Divergence Anomaly at 975 hPa (departure from climatology) — EP1 vs EP2",
        out_name="composite_moisture_flux_anom.png",
        cmap="BrBG_r",
        wind_u="u_975_prime",
        wind_v="v_975_prime",
        wind_scale=80,
    )


def figure_ke_advection_anom(datasets):
    """Kinetic energy advection anomaly at 250 hPa: EP1 vs EP2, with 250 hPa anomaly wind vectors."""
    logging.info("  Creating KE advection anomaly @250 hPa composite figure...")
    _anom_fig(
        datasets,
        var_key="ke_adv_250_anom",
        scale_factor=1.0,
        unit_label="ΔKE adv (m² s⁻³)",
        suptitle="KE Advection Anomaly at 250 hPa (departure from climatology) — EP1 vs EP2",
        out_name="composite_ke_advection_anom.png",
        cmap="PuOr_r",
        wind_u="u_250_prime",
        wind_v="v_250_prime",
        wind_scale=VECTOR_SCALE,
    )


def figure_slp_anom(datasets):
    """SLP anomaly: EP1 vs EP2, with 850 hPa wind vectors."""
    logging.info("  Creating SLP anomaly composite figure...")
    _anom_fig(
        datasets,
        var_key="msl_anom",
        scale_factor=1.0 / 100.0,    # Pa → hPa
        unit_label="ΔSLP (hPa)",
        suptitle="Sea Level Pressure Anomaly (departure from 1991–2020 climatology) — EP1 vs EP2",
        out_name="composite_slp_anom.png",
        cmap="RdBu_r",
        wind_u="u_850_prime",
        wind_v="v_850_prime",
        wind_scale=100,
    )


def figure_btcr(datasets):
    """
    Barotropic Critical Region (BtCR) composite: EP1, EP2, EP3 comparison.

    Shading: Effective deformation Δm = σ_m² − ζ_m² (×10⁻⁹ s⁻²).
      Positive  (warm) : deformation dominates → BtCR candidate region
      Negative  (cool) : rotation dominates

    Dilatation axis vectors: unit arrows in both ± directions (axis, not
    vector) where Δm > 0, showing how the background jet tends to tilt/
    stretch a traversing disturbance.  Overlaid on wind speed contours of
    the climatological 250 hPa wind.

    Both diagnostics are computed from the 30-year WMO monthly climatological
    winds (1991–2020) — the low-frequency surrogate used in place of a
    per-case 8-day running mean (Rivière 2006).

    NOTE: BtCR uses climatology-based decomposition by construction. It is
    NOT converted to EPALL-relative anomalies.

    References
    ----------
    Rivière, G., 2006: J. Atmos. Sci., 63, 1764–1775.
    """
    logging.info("  Creating BtCR composite figure (250 hPa)...")

    # Get EPs that have BtCR data
    eps = [ep for ep in ["EP1", "EP2", "EP3"] if ep in datasets and "btcr_delta_m" in datasets[ep]]
    
    if not eps:
        logging.warning("   ⚠  btcr_delta_m absent — skipping BtCR figure (run step2_1 first)")
        return

    SCALE = 1e9      # s⁻²  →  10⁻⁹ s⁻²
    SKIP  = VECTOR_SKIP

    n_panels = len(eps)
    fig, axes = _create_multipanel_fig(n_panels, panel_width=7, panel_height=6)
    if n_panels == 1:
        axes = [axes]

    # ── Common colour scale (symmetric about zero) ─────────────────────
    absmax = 0.0
    for ep in eps:
        arr = datasets[ep]["btcr_delta_m"].values * SCALE
        absmax = max(absmax, np.nanpercentile(np.abs(arr), 98))
    clevels = _safe_symmetric_levels(absmax, 41)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]

        dm   = ds["btcr_delta_m"].values  * SCALE           # (ny, nx)
        ang  = ds["btcr_dil_angle"].values                   # radians; NaN where Δm ≤ 0

        x = ds.coords["x"].values
        y = ds.coords["y"].values
        X, Y = np.meshgrid(x, y)

        # Shading: full Δm field (diverging, centered at 0)
        im = ax.contourf(X, Y, dm, levels=clevels, cmap="RdBu_r", extend="both")
        ax.contour(X, Y, dm, levels=[0.0], colors="black", linewidths=1.2)  # zero line

        # Climatological 250 hPa wind speed contours for jet reference,
        # taken from the composite mean (which uses instantaneous winds
        # but approximates the mean jet structure)
        if "u_250" in ds.data_vars and "v_250" in ds.data_vars:
            u_250 = ds["u_250"].sel(level=250).values if "level" in ds["u_250"].dims \
                    else ds["u_250"].values
            v_250 = ds["v_250"].sel(level=250).values if "level" in ds["v_250"].dims \
                    else ds["v_250"].values
            ws = np.sqrt(u_250 ** 2 + v_250 ** 2)
            ax.contour(X, Y, ws,
                       levels=np.arange(20, 80, 10),
                       colors="dimgray", linewidths=0.8, linestyles="--", alpha=0.6)

        # Dilatation axis vectors (where Δm > 0)
        # Plot as headless barbs: forward (+) and backward (−) arrows to
        # represent an axial (unsigned) direction, not a vector.
        ax_sm  = X[::SKIP, ::SKIP]
        ay_sm  = Y[::SKIP, ::SKIP]
        ang_sm = ang[::SKIP, ::SKIP]
        mask = ~np.isnan(ang_sm)

        if np.any(mask):
            cos_a = np.where(mask, np.cos(ang_sm), np.nan)
            sin_a = np.where(mask, np.sin(ang_sm), np.nan)
            # Scale = 0.5 → unit vector spans 2° (1° each side, pivot='middle')
            # Both + and − directions drawn to represent an axis, not a vector.
            for sign in (+1, -1):
                ax.quiver(
                    ax_sm, ay_sm,
                    sign * cos_a, sign * sin_a,
                    scale=0.5, scale_units="xy",
                    headwidth=0, headlength=0, headaxislength=0,
                    width=0.002, color="k", alpha=0.7,
                    pivot="middle",
                )

        _decorate_ax(ax, f"{ep} — BtCR (250 hPa)", ylabel=(i == 0))
        _add_cbar(fig, ax, im, r"$\Delta_m \times 10^{9}$ (s$^{-2}$)")

    # Hide unused axes if any
    for j in range(len(eps), len(axes)):
        axes[j].set_visible(False)

    ep_list = ", ".join(eps)
    fig.suptitle(
        f"Barotropic Critical Region — Δm = σ_m² − ζ_m² at 250 hPa (Rivière 2006) — {ep_list}",
        fontsize=13, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    out = _figure_path("composite_btcr.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


# ============================================================================
# EP1 − EP2 DIFFERENCE FIGURE FUNCTIONS
# ============================================================================

def _diff_fig(datasets, var_key, scale_factor, unit_label, suptitle, out_name,
              cmap="RdBu_r", n_levels=21):
    """Generic single-panel (EP1 − EP2) difference figure builder.

    Parameters
    ----------
    datasets     : dict with keys "EP1", "EP2" → xr.Dataset
    var_key      : variable name inside each dataset
    scale_factor : multiply raw values before plotting
    unit_label   : colorbar label string
    suptitle     : figure super-title
    out_name     : output filename (no directory)
    cmap         : diverging colormap name
    n_levels     : number of contour levels (odd for symmetric)
    """
    if var_key not in datasets["EP1"] or var_key not in datasets["EP2"]:
        logging.warning(f"    ⚠  {var_key} not in both composites — skipping difference figure")
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    ds1 = datasets["EP1"]
    ds2 = datasets["EP2"]
    x, y = ds1.coords["x"].values, ds1.coords["y"].values

    data1 = ds1[var_key].values * scale_factor
    data2 = ds2[var_key].values * scale_factor
    diff = data1 - data2  # EP1 − EP2

    # Symmetric colour limits from 98th-percentile of |difference|
    absmax = np.nanpercentile(np.abs(diff), 98)
    if absmax == 0.0:
        absmax = 1e-10
    clevels = _safe_symmetric_levels(absmax, n_levels)

    im = ax.contourf(x, y, diff, levels=clevels, cmap=cmap, extend="both")
    ax.contour(x, y, diff, levels=[0], colors="black", linewidths=1.5)

    n1 = int(ds1.attrs.get("n_cases", "?"))
    n2 = int(ds2.attrs.get("n_cases", "?"))
    _decorate_ax(ax, f"EP1 (n={n1}) − EP2 (n={n2})", ylabel=True)
    _add_cbar(fig, ax, im, unit_label)

    fig.suptitle(suptitle, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = _figure_path(out_name)
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_egr_diff(datasets):
    """EGR difference: EP1 − EP2."""
    logging.info("  Creating EGR difference figure (EP1 − EP2)...")
    _diff_fig(
        datasets,
        var_key="egr",
        scale_factor=1.0,
        unit_label="ΔEGR (day⁻¹)",
        suptitle="Eady Growth Rate Difference (EP1 − EP2)",
        out_name="composite_egr_diff.png",
        cmap="RdBu_r",
    )


def figure_pv200_diff(datasets):
    """PV at 200 hPa difference: EP1 − EP2."""
    logging.info("  Creating PV@200 hPa difference figure (EP1 − EP2)...")
    _diff_fig(
        datasets,
        var_key="pv_200",
        scale_factor=1e6,
        unit_label="ΔPV (PVU)",
        suptitle="Potential Vorticity at 200 hPa Difference (EP1 − EP2)",
        out_name="composite_pv200_diff.png",
        cmap="RdBu_r",
    )


def figure_pv850_diff(datasets):
    """PV at 850 hPa difference: EP1 − EP2."""
    logging.info("  Creating PV@850 hPa difference figure (EP1 − EP2)...")
    _diff_fig(
        datasets,
        var_key="pv_850",
        scale_factor=1e6,
        unit_label="ΔPV (PVU)",
        suptitle="Potential Vorticity at 850 hPa Difference (EP1 − EP2)",
        out_name="composite_pv850_diff.png",
        cmap="RdBu_r",
    )


def figure_advT850_diff(datasets):
    """Temperature advection at 850 hPa difference: EP1 − EP2."""
    logging.info("  Creating temp advection @850 hPa difference figure (EP1 − EP2)...")
    _diff_fig(
        datasets,
        var_key="adv_T_850",
        scale_factor=3600.0,
        unit_label="Δ(−V·∇T) (K h⁻¹)",
        suptitle="Temperature Advection at 850 hPa Difference (EP1 − EP2)",
        out_name="composite_advT850_diff.png",
        cmap="RdBu_r",
    )


def figure_moisture_diff(datasets):
    """Moisture flux divergence at 975 hPa difference: EP1 − EP2."""
    logging.info("  Creating moisture flux divergence @975 hPa difference figure (EP1 − EP2)...")
    _diff_fig(
        datasets,
        var_key="div_q_975",
        scale_factor=1.0,
        unit_label="Δ∇·(qV) (g kg⁻¹ s⁻¹)",
        suptitle="Moisture Flux Divergence at 975 hPa Difference (EP1 − EP2)",
        out_name="composite_moisture_flux_diff.png",
        cmap="BrBG_r",
    )


def figure_slp_diff(datasets):
    """SLP difference: EP1 − EP2."""
    logging.info("  Creating SLP difference figure (EP1 − EP2)...")
    _diff_fig(
        datasets,
        var_key="msl",
        scale_factor=1.0 / 100.0,  # Pa → hPa
        unit_label="ΔSLP (hPa)",
        suptitle="Sea Level Pressure Difference (EP1 − EP2)",
        out_name="composite_slp_diff.png",
        cmap="RdBu_r",
    )


def figure_rk_criterion_diff(datasets):
    """Rayleigh-Kuo criterion at 250 hPa difference: EP1 − EP2."""
    logging.info("  Creating RK criterion @250 hPa difference figure (EP1 − EP2)...")
    if "rk_criterion_250" not in datasets["EP1"]:
        logging.warning("    ⚠  rk_criterion_250 not in composites — skipping difference figure")
        return
    _diff_fig(
        datasets,
        var_key="rk_criterion_250",
        scale_factor=1e5,  # same as absolute figure
        unit_label="ΔRK (×10⁻⁵ s⁻¹)",
        suptitle="Rayleigh-Kuo Criterion at 250 hPa Difference (EP1 − EP2)",
        out_name="composite_rk_criterion_diff.png",
        cmap="RdBu_r",
    )


def figure_ke_advection_diff(datasets):
    """KE advection at 250 hPa difference: EP1 − EP2."""
    logging.info("  Creating KE advection @250 hPa difference figure (EP1 − EP2)...")
    if "ke_adv_250" not in datasets["EP1"]:
        logging.warning("    ⚠  ke_adv_250 not in composites — skipping difference figure")
        return
    _diff_fig(
        datasets,
        var_key="ke_adv_250",
        scale_factor=1.0,
        unit_label="ΔKE adv (m² s⁻³)",
        suptitle="Kinetic Energy Advection at 250 hPa Difference (EP1 − EP2)",
        out_name="composite_ke_advection_diff.png",
        cmap="PuOr_r",
    )


def figure_afc_diff(datasets):
    """AFC at 250 hPa difference: EP1 − EP2."""
    logging.info("  Creating AFC @250 hPa difference figure (EP1 − EP2)...")
    if "afc_250" not in datasets["EP1"]:
        logging.warning("    ⚠  afc_250 not in composites — skipping difference figure")
        return
    _diff_fig(
        datasets,
        var_key="afc_250",
        scale_factor=1.0,
        unit_label="ΔAFC (m² s⁻³)",
        suptitle="Ageostrophic Flux Convergence at 250 hPa Difference (EP1 − EP2)",
        out_name="composite_afc_diff.png",
        cmap="RdBu_r",
    )


def figure_btcr_diff(datasets):
    """BtCR delta_m difference: EP1 − EP2."""
    logging.info("  Creating BtCR difference figure (EP1 − EP2)...")
    if "btcr_delta_m" not in datasets["EP1"]:
        logging.warning("    ⚠  btcr_delta_m not in composites — skipping difference figure")
        return
    _diff_fig(
        datasets,
        var_key="btcr_delta_m",
        scale_factor=1e9,
        unit_label="ΔΔm (×10⁻⁹ s⁻²)",
        suptitle="Barotropic Critical Region (Δm) Difference (EP1 − EP2)",
        out_name="composite_btcr_diff.png",
        cmap="RdBu_r",
    )


def figure_wind250_anom(datasets):
    """250 hPa wind speed anomaly: EP1, EP2, EP3 comparison, diverging shading.

    Wind speed anomaly is defined as:
        wspd_anom = |V_total| − |V_climatology|
                  = sqrt(u² + v²) − sqrt((u − u′)² + (v − v′)²)

    where V_total = (u_250, v_250) and V_climatology = (u_250 − u_250_prime,
    v_250 − v_250_prime).  This is derived entirely from fields already stored
    in the composite dataset; no additional step3 computation needed.

    NOTE: This uses climatology-based anomalies (departure from monthly mean),
    NOT EPALL-relative anomalies. The eddy wind decomposition requires a
    climatological reference for physical interpretation.

    Positive values: EP case has stronger upper-level winds than climatology.
    Negative values: EP case has weaker upper-level winds than climatology.
    """
    logging.info("  Creating 250 hPa wind speed anomaly composite figure...")

    # Get EPs that have the required wind fields
    eps = [ep for ep in ["EP1", "EP2", "EP3"] 
           if ep in datasets and "u_250" in datasets[ep] and "u_250_prime" in datasets[ep]]
    
    if not eps:
        logging.warning(
            "    ⚠  u_250 or u_250_prime not in composites — skipping wind250_anom figure"
        )
        return

    n_panels = len(eps)
    fig, axes = _create_multipanel_fig(n_panels, panel_width=7, panel_height=6)
    if n_panels == 1:
        axes = [axes]

    # Symmetric colour scale from 98th-percentile across all EPs
    absmax = 0.0
    for ep in eps:
        ds = datasets[ep]
        u = ds["u_250"].values
        v = ds["v_250"].values
        up = ds["u_250_prime"].values
        vp = ds["v_250_prime"].values
        u_clim = u - up
        v_clim = v - vp
        anom = np.hypot(u, v) - np.hypot(u_clim, v_clim)
        absmax = max(absmax, np.nanpercentile(np.abs(anom), 98))
    if absmax == 0.0:
        absmax = 1e-10
    clevels = _safe_symmetric_levels(absmax, 21)

    for i, ep in enumerate(eps):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.coords["x"].values, ds.coords["y"].values

        u = ds["u_250"].values
        v = ds["v_250"].values
        up = ds["u_250_prime"].values
        vp = ds["v_250_prime"].values
        u_clim = u - up
        v_clim = v - vp
        wspd_anom = np.hypot(u, v) - np.hypot(u_clim, v_clim)

        im = ax.contourf(x, y, wspd_anom, levels=clevels, cmap="RdBu_r", extend="both")
        ax.contour(x, y, wspd_anom, levels=[0], colors="black", linewidths=1.2)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax,
                     f"{ep} — Wind speed anomaly at 250 hPa (|V| − |V̅ₘ|)  [n={n}]",
                     ylabel=(i == 0))
        _add_cbar(fig, ax, im, "Δ|V| (m s⁻¹)")

    # Hide unused axes if any
    for j in range(len(eps), len(axes)):
        axes[j].set_visible(False)

    ep_list = ", ".join(eps)
    fig.suptitle(
        f"250 hPa Wind Speed Anomaly (|V| − |V̅ₘ|) — {ep_list}",
        fontsize=13, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    out = _figure_path("composite_wind250_anom.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Create EP structure composite figures (canonical method)")
    args = parser.parse_args()
    
    log_file = setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 4: CREATE COMPOSITE FIGURES – EP1, EP2, EP3, EPALL")
    logging.info("=" * 70)
    logging.info(f"   Method: Central timesteps (canonical Apr 2026)")

    datasets = load_composites()
    if datasets is None:
        return

    eps = _get_available_eps(datasets)
    logging.info(f"   Available EPs: {', '.join(eps)}")

    # Verify required (always-present) variables
    for ep, ds in datasets.items():
        required = ["egr", "pv_200", "pv_850", "adv_T_850"]
        missing = [v for v in required if v not in ds]
        if missing:
            logging.warning(f"   ⚠ Missing required variables in {ep}: {missing}")

    # Check for EPALL-relative anomaly variables (new April 2026)
    epall_anom_vars = [
        "egr_minus_epall", "pv_200_minus_epall", "pv_850_minus_epall",
        "adv_T_850_minus_epall", "msl_minus_epall", "ke_adv_250_minus_epall",
    ]
    for ep in ["EP1", "EP2", "EP3"]:
        if ep in datasets:
            present = [v for v in epall_anom_vars if v in datasets[ep]]
            if present:
                logging.info(f"   {ep}: EPALL-relative anomalies available ({len(present)} vars)")
            else:
                logging.info(f"   {ep}: No EPALL-relative anomalies found")

    # Optional diagnostics — warn but continue
    optional = [
        "rk_criterion_250", "ke_adv_250", "afc_250",
        # climatology-based anomaly fields (legacy)
        "pv_200_anom", "pv_850_anom", "adv_T_850_anom",
        "div_q_975_anom", "ke_adv_250_anom", "msl_anom",
        # eddy winds for anomaly overlays (X' = X − X̅_m)
        "u_250_prime", "v_250_prime",
        "u_850_prime", "v_850_prime",
        "u_975_prime", "v_975_prime",
        # BtCR fields (require step2_1 250 hPa climatology)
        "btcr_delta_m", "btcr_dil_angle",
    ]
    for ep, ds in datasets.items():
        absent = [v for v in optional if v not in ds]
        if absent:
            logging.warning(f"   ⚠  {ep}: optional fields absent (will be skipped): {absent[:5]}...")

    logging.info("\nCreating total-field figures (EP1, EP2, EP3, EPALL)...")

    figure_wind250(datasets)
    figure_egr(datasets)
    figure_pv200(datasets)
    figure_pv850(datasets)
    figure_advT850(datasets)
    figure_moisture(datasets)
    figure_slp(datasets)
    figure_rk_criterion(datasets)
    figure_ke_advection(datasets)
    figure_afc(datasets)

    logging.info("\nCreating EPALL-relative anomaly figures (EP1−EPALL | EP2−EPALL | EP3−EPALL)...")
    # NOTE: RK criterion is intentionally excluded from EPALL-relative anomaly figures.
    # RK = β − ∂²ū/∂y² is a property of the large-scale background flow used to diagnose
    # barotropic critical regions; it is shown only as total composite field (not differenced).

    figure_egr_epall_anom(datasets)
    figure_pv200_epall_anom(datasets)
    figure_pv850_epall_anom(datasets)
    figure_advT850_epall_anom(datasets)
    figure_slp_epall_anom(datasets)
    figure_ke_advection_epall_anom(datasets)

    logging.info("\nCreating climatology-based anomaly figures (legacy, where available)...")

    figure_pv200_anom(datasets)
    figure_pv850_anom(datasets)
    figure_advT850_anom(datasets)
    figure_moisture_anom(datasets)
    figure_ke_advection_anom(datasets)
    figure_slp_anom(datasets)
    figure_wind250_anom(datasets)

    logging.info("\nCreating BtCR figures (climatology-dependent)...")
    figure_btcr(datasets)

    logging.info("\nCreating EP1 − EP2 difference figures (legacy)...")
    # NOTE: RK criterion diff is intentionally excluded — RK is shown as total field only.
    figure_egr_diff(datasets)
    figure_pv200_diff(datasets)
    figure_pv850_diff(datasets)
    figure_advT850_diff(datasets)
    figure_moisture_diff(datasets)
    figure_slp_diff(datasets)
    figure_ke_advection_diff(datasets)
    figure_afc_diff(datasets)
    figure_btcr_diff(datasets)

    # Close datasets
    for ds in datasets.values():
        ds.close()

    logging.info("\n" + "=" * 70)
    logging.info("✓ STEP 4 COMPLETE")
    logging.info("=" * 70)
    logging.info(f"Figures saved in: {FIGURES_DIR}")
    logging.info(f"Log: {log_file}")


if __name__ == "__main__":
    main()
