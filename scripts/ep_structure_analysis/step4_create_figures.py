"""
Step 4: Create EP1 vs EP2 Composite Comparison Figures

For each diagnostic field, creates a side-by-side composite figure:
  Left  panel: EP1
  Right panel: EP2

Fields plotted:
  1. EGR (250–850 hPa)        — shaded
  2. PV at 200 hPa            — shaded + 2 PVU contour
  3. PV at 850 hPa            — shaded
  4. Temperature advection 850 — shaded (warm red / cold blue)
  5. SLP                      — contours

Each panel includes a 15°×15° dashed box indicating the LEC computation domain.

Output:
  figures/ep_structure/composite_egr.png
  figures/ep_structure/composite_pv200.png
  figures/ep_structure/composite_pv850.png
  figures/ep_structure/composite_advT850.png
  figures/ep_structure/composite_slp.png

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings
import logging
from datetime import datetime

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

EP_COLORS = {"EP1": "gold", "EP2": "dodgerblue"}
EP_LABELS = {"EP1": "EP1", "EP2": "EP2"}


# ============================================================================
# HELPERS
# ============================================================================

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
    """Load precomputed EP1 and EP2 composites."""
    datasets = {}
    for ep in ["ep1", "ep2"]:
        f = DATA_DIR / f"precomputed_composites_{ep}.nc"
        if not f.exists():
            logging.error(f"❌ File not found: {f}")
            logging.error("   Run step3_precompute_composites.py first.")
            return None
        datasets[ep.upper()] = xr.open_dataset(f)
        mb = f.stat().st_size / 1024 ** 2
        logging.info(f"   Loaded {ep.upper()}: {f.name} ({mb:.1f} MB)")
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


# ============================================================================
# FIGURE FUNCTIONS
# ============================================================================

def figure_egr(datasets):
    """EGR composite: EP1 vs EP2, with 850 hPa wind vectors."""
    logging.info("  Creating EGR composite figure...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    vmin, vmax = None, None
    for ep in ["EP1", "EP2"]:
        ds = datasets[ep]
        d = ds["egr"].values
        lo = np.nanpercentile(d, 1)
        hi = np.nanpercentile(d, 99)
        vmin = lo if vmin is None else min(vmin, lo)
        vmax = hi if vmax is None else max(vmax, hi)

    clevels = np.linspace(vmin, vmax, 21)

    for i, ep in enumerate(["EP1", "EP2"]):
        ax = axes[i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        im = ax.contourf(x, y, ds["egr"].values, levels=clevels, cmap="YlOrRd", extend="both")

        # 850 hPa winds
        if "u_850" in ds and "v_850" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_850"].values[::s, ::s], ds["v_850"].values[::s, ::s],
                      color="black", alpha=0.8, scale=100, width=VECTOR_WIDTH)

        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — EGR (250–850 hPa)  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "EGR (day⁻¹)")

        mean_val = np.nanmean(ds["egr"].values)
        ax.text(0.03, 0.97, f"Mean: {mean_val:.2f} day⁻¹",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    fig.suptitle("Eady Growth Rate — EP1 vs EP2", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "composite_egr.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_pv200(datasets):
    """PV at 200 hPa: EP1 vs EP2, with 250 hPa wind vectors."""
    logging.info("  Creating PV@200 hPa composite figure...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Common colour scale
    vmin, vmax = None, None
    for ep in ["EP1", "EP2"]:
        d = datasets[ep]["pv_200"].values * 1e6  # PVU
        lo, hi = np.nanpercentile(d, 2), np.nanpercentile(d, 98)
        vmin = lo if vmin is None else min(vmin, lo)
        vmax = hi if vmax is None else max(vmax, hi)
    clevels = np.linspace(vmin, vmax, 21)

    for i, ep in enumerate(["EP1", "EP2"]):
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
        _decorate_ax(ax, f"{ep} — PV at 200 hPa  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "PV (PVU)")

    fig.suptitle("Potential Vorticity at 200 hPa — EP1 vs EP2", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "composite_pv200.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_pv850(datasets):
    """PV at 850 hPa: EP1 vs EP2, with 850 hPa wind vectors."""
    logging.info("  Creating PV@850 hPa composite figure...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    vmin, vmax = None, None
    for ep in ["EP1", "EP2"]:
        d = datasets[ep]["pv_850"].values * 1e6
        lo, hi = np.nanpercentile(d, 2), np.nanpercentile(d, 98)
        vmin = lo if vmin is None else min(vmin, lo)
        vmax = hi if vmax is None else max(vmax, hi)
    clevels = np.linspace(vmin, vmax, 21)

    for i, ep in enumerate(["EP1", "EP2"]):
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
        _decorate_ax(ax, f"{ep} — PV at 850 hPa  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "PV (PVU)")

    fig.suptitle("Potential Vorticity at 850 hPa — EP1 vs EP2", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "composite_pv850.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_advT850(datasets):
    """Temperature advection at 850 hPa: EP1 vs EP2."""
    logging.info("  Creating temp advection @850 hPa composite figure...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Symmetric colour scale
    absmax = 0
    for ep in ["EP1", "EP2"]:
        d = datasets[ep]["adv_T_850"].values * 3600  # K/h
        absmax = max(absmax, np.nanpercentile(np.abs(d), 98))
    clevels = np.linspace(-absmax, absmax, 21)

    for i, ep in enumerate(["EP1", "EP2"]):
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
        _decorate_ax(ax, f"{ep} — Temp advection at 850 hPa  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "−V·∇T (K h⁻¹)")

    fig.suptitle("Temperature Advection at 850 hPa — EP1 vs EP2", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "composite_advT850.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_moisture(datasets):
    """Moisture and moisture flux divergence at 975 hPa: EP1 vs EP2."""
    logging.info("  Creating moisture flux composite figure...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Row 1: Specific humidity (g/kg) with wind vectors
    for i, ep in enumerate(["EP1", "EP2"]):
        ax = axes[0, i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        if "q_975" not in ds:
            ax.text(0.5, 0.5, "q_975 not available", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12)
            continue

        # Convert to g/kg
        q975_gkg = ds["q_975"].values * 1000.0
        
        # Determine common color scale
        if i == 0:
            q_min = np.nanpercentile(q975_gkg, 5)
            q_max = np.nanpercentile(q975_gkg, 95)
        
        q_levels = np.linspace(q_min, q_max, 21)
        
        im = ax.contourf(x, y, q975_gkg, levels=q_levels, cmap="YlGnBu", extend="both")
        
        # 975 hPa wind vectors
        if "u_975" in ds and "v_975" in ds:
            s = VECTOR_SKIP
            ax.quiver(x[::s], y[::s], ds["u_975"].values[::s, ::s], ds["v_975"].values[::s, ::s],
                      color="black", alpha=0.7, scale=80, width=VECTOR_WIDTH)
        
        n = int(ds.attrs.get("n_cases", "?"))
        _decorate_ax(ax, f"{ep} — Specific Humidity at 975 hPa  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "q (g kg⁻¹)")
        
        q_mean = np.nanmean(q975_gkg)
        ax.text(0.03, 0.97, f"Mean: {q_mean:.2f} g/kg",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))
    
    # Row 2: Moisture flux divergence (g kg⁻¹ s⁻¹)
    # Symmetric color scale
    absmax_div = 0
    for ep in ["EP1", "EP2"]:
        if "div_q_975" in datasets[ep]:
            d = datasets[ep]["div_q_975"].values
            absmax_div = max(absmax_div, np.nanpercentile(np.abs(d), 95))
    
    div_levels = np.linspace(-absmax_div, absmax_div, 21)
    
    for i, ep in enumerate(["EP1", "EP2"]):
        ax = axes[1, i]
        ds = datasets[ep]
        x, y = ds.x.values, ds.y.values

        if "div_q_975" not in ds:
            ax.text(0.5, 0.5, "div_q_975 not available", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12)
            continue

        div_q = ds["div_q_975"].values
        
        im = ax.contourf(x, y, div_q, levels=div_levels, cmap="RdBu_r", extend="both")
        
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
        _decorate_ax(ax, f"{ep} — Moisture Flux Divergence at 975 hPa  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "∇·(qV) (g kg⁻¹ s⁻¹)")
        
        # Note on convergence/divergence
        ax.text(0.03, 0.03, "Blue dashed: convergence\nRed dashed: divergence",
                transform=ax.transAxes, fontsize=8, va="bottom",
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))
    
    fig.suptitle("Low-Level Moisture Transport at 975 hPa — EP1 vs EP2", 
                 fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    out = FIGURES_DIR / "composite_moisture_flux.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


def figure_slp(datasets):
    """SLP composite: EP1 vs EP2, with 850 hPa wind vectors."""
    logging.info("  Creating SLP composite figure...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    for i, ep in enumerate(["EP1", "EP2"]):
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
        _decorate_ax(ax, f"{ep} — Sea Level Pressure  [n={n}]", ylabel=(i == 0))
        _add_cbar(fig, ax, im, "SLP (hPa)")

        slp_min = np.nanmin(msl_hpa)
        ax.text(0.03, 0.97, f"Min: {slp_min:.1f} hPa",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    fig.suptitle("Sea Level Pressure — EP1 vs EP2", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "composite_slp.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    logging.info(f"    ✓ {out.name}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    log_file = setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 4: CREATE COMPOSITE FIGURES – EP1 vs EP2")
    logging.info("=" * 70)

    datasets = load_composites()
    if datasets is None:
        return

    # Verify required variables
    for ep, ds in datasets.items():
        required = ["egr", "pv_200", "pv_850", "adv_T_850"]
        missing = [v for v in required if v not in ds]
        if missing:
            logging.error(f"❌ Missing variables in {ep}: {missing}")
            return

    logging.info("\nCreating figures...")

    figure_egr(datasets)
    figure_pv200(datasets)
    figure_pv850(datasets)
    figure_advT850(datasets)
    figure_moisture(datasets)
    figure_slp(datasets)

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
