#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create the publication figure for cyclone 20070643 from source data.

The three panels are drawn directly in this script:

* (a) conversion Lorenz Phase Space (Ck x Ca);
* (b) imports Lorenz Phase Space (BAe x BKe);
* (c) cyclone track, coloured by vorticity and sized by Ke.

No pre-rendered exploratory images are read. Keeping the panel construction
here makes scientific and layout changes reproducible in a single execution.

Input
-----
data/corrected/tracks_with_energetics_corrected.csv

Output
------
figures/main/cyclone_20070643_lps_track.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from scripts.utils import corrected_lec as clec  # noqa: E402


# -----------------------------------------------------------------------------
# Editable figure configuration
# -----------------------------------------------------------------------------

TRACK_ID = "20070643"
OUTPUT_FILE = BASE_DIR / "figures" / "main" / f"cyclone_{TRACK_ID}_lps_track.png"

DPI = 300
FIGSIZE = (13, 9)
FONT_FAMILY = "DejaVu Sans"

# Use ``None`` to derive compact limits from the displayed data. Replace either
# value with a ``(minimum, maximum)`` tuple when a fixed comparison range is needed.
LPS_LIMITS = {
    "conversion": {"x": None, "y": None},
    "imports": {"x": None, "y": None},
}
LPS_LIMIT_PADDING = 0.12
# Areas in points squared, shared by the plotted data and the Ke legend.
LPS_MARKER_SIZES = np.array([70, 130, 210, 310, 430], dtype=float)
LPS_Y_LABEL_X = -0.08
LPS_REFERENCE_COLOR = "#CCCCCC"
LPS_CONNECTION_COLOR = "0.55"

TRACK_PADDING_DEGREES = 5
TRACK_MARKER_SIZE_RANGE = (30, 300)
TRACK_LEGEND_MARKER_SCALE = 0.55
TRACK_CMAP = "YlOrRd"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [FONT_FAMILY, "Arial", "Helvetica"],
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
    }
)


# -----------------------------------------------------------------------------
# Data preparation
# -----------------------------------------------------------------------------

def load_track(track_id: str = TRACK_ID) -> pd.DataFrame:
    """Load one cyclone from the complete corrected track product."""
    tracks = clec.read_corrected_tracks()
    track = tracks.loc[tracks["track_id"].astype(str) == str(track_id)].copy()
    if track.empty:
        raise ValueError(f"Cyclone {track_id} is absent from corrected tracks")

    required = {
        "date", "lon vor", "lat vor", "vor42", "Ck", "Ca", "BAe", "BKe", "Ge", "Ke"
    }
    missing = sorted(required - set(track.columns))
    if missing:
        raise ValueError(f"Corrected tracks lack required columns: {missing}")

    return track.sort_values("date").reset_index(drop=True)


def prepare_lps_data(track: pd.DataFrame) -> pd.DataFrame:
    """Return complete six-hourly LPS records, matching the original figure."""
    columns = ["Ck", "Ca", "BAe", "BKe", "Ge", "Ke"]
    energy = track.dropna(subset=columns).iloc[::2].copy()
    if len(energy) < 2:
        raise ValueError("At least two complete LEC records are required for the LPS panels")
    return energy.reset_index(drop=True)


def lps_size_encoding(ke: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Encode Ke with the five quantile classes used by zoomed LPS plots."""
    thresholds = ke.quantile([0.2, 0.4, 0.6, 0.8]).to_numpy(dtype=float)
    minimum = float(np.nanmin(np.abs(thresholds)))
    order = 10 ** np.floor(np.log10(minimum)) if minimum > 0 else 1.0
    thresholds = np.round(thresholds / (order / 100.0)) * (order / 100.0)

    size_index = np.searchsorted(thresholds, ke.to_numpy(dtype=float), side="left")
    sizes = LPS_MARKER_SIZES[np.clip(size_index, 0, len(LPS_MARKER_SIZES) - 1)]
    return sizes, thresholds


def ge_color_encoding(ge: pd.Series) -> tuple[BoundaryNorm, np.ndarray]:
    """Create a discrete, zero-centred Ge normalization shared by panels a-b."""
    max_abs = float(np.ceil(np.nanmax(np.abs(ge.to_numpy(dtype=float)))))
    max_abs = max(max_abs, 1.0)
    boundaries = np.linspace(-max_abs, max_abs, 11)
    return BoundaryNorm(boundaries, ncolors=cmocean.cm.curl.N), boundaries


def padded_data_limits(
    values: pd.Series | np.ndarray,
    *,
    padding: float = LPS_LIMIT_PADDING,
    include_zero: bool = True,
) -> tuple[float, float]:
    """Return finite data limits with proportional padding."""
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise ValueError("Cannot derive axis limits from empty or non-finite data")

    lower = float(np.min(finite))
    upper = float(np.max(finite))
    if include_zero:
        lower = min(lower, 0.0)
        upper = max(upper, 0.0)

    span = upper - lower
    if np.isclose(span, 0.0):
        span = max(abs(lower), 1.0)
    margin = span * padding
    return lower - margin, upper + margin


# -----------------------------------------------------------------------------
# Lorenz Phase Space panels
# -----------------------------------------------------------------------------

def plot_lps_panel(
    ax: plt.Axes,
    energy: pd.DataFrame,
    *,
    lps_type: str,
    x_column: str,
    y_column: str,
    x_label: str,
    y_label: str,
    marker_sizes: np.ndarray,
    color_norm: BoundaryNorm,
):
    """Draw one editable Lorenz Phase Space panel on an existing axis."""
    x = energy[x_column].to_numpy(dtype=float)
    y = energy[y_column].to_numpy(dtype=float)
    ge = energy["Ge"].to_numpy(dtype=float)

    configured_limits = LPS_LIMITS[lps_type]
    x_limits = configured_limits["x"] or padded_data_limits(x)
    y_limits = configured_limits["y"] or padded_data_limits(y)
    ax.set_xlim(*x_limits)
    ax.set_ylim(*y_limits)

    # Reference axes reproduce the zoomed lorenz-phase-space visual grammar.
    if lps_type == "conversion":
        x_diagonal = np.linspace(0, x_limits[0], 100)
        ax.plot(
            x_diagonal,
            -x_diagonal,
            color=LPS_REFERENCE_COLOR,
            linestyle=":",
            linewidth=2,
            zorder=0,
        )
    ax.axhline(0, color=LPS_REFERENCE_COLOR, linewidth=8, zorder=1)
    ax.axvline(0, color=LPS_REFERENCE_COLOR, linewidth=8, zorder=1)

    ax.plot(x, y, color=LPS_CONNECTION_COLOR, alpha=0.55, linewidth=1.4, zorder=2)

    peak = int(np.nanargmax(energy["Ke"].to_numpy(dtype=float)))
    ax.scatter(
        x[peak],
        y[peak],
        s=marker_sizes[peak] * 1.10,
        facecolors="none",
        edgecolors="black",
        linewidths=2.5,
        zorder=4,
    )
    scatter = ax.scatter(
        x,
        y,
        c=ge,
        s=marker_sizes,
        cmap=cmocean.cm.curl,
        norm=color_norm,
        edgecolors="black",
        linewidths=0.8,
        alpha=0.9,
        zorder=3,
    )

    ax.text(x[0], y[0], "A", ha="center", va="center", fontsize=17, zorder=5)
    ax.text(x[-1], y[-1], "Z", ha="center", va="center", fontsize=17, zorder=5)

    ax.set_xlabel(x_label, labelpad=6)
    ax.set_ylabel(y_label, labelpad=0)
    ax.yaxis.set_label_coords(LPS_Y_LABEL_X, 0.5)
    ax.tick_params(direction="out")
    return scatter


def add_lps_colorbar(fig: plt.Figure, cax: plt.Axes, scatter, boundaries: np.ndarray) -> None:
    """Add the Ge colorbar shared by both LPS panels."""
    cbar = fig.colorbar(scatter, cax=cax, ticks=boundaries, spacing="uniform")
    cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    cbar.set_label(r"Ge ($W\,m^{-2}$)", rotation=270, labelpad=17)
    cbar.ax.tick_params(labelsize=8)


def add_lps_size_legend(ax: plt.Axes, thresholds: np.ndarray) -> None:
    """Add the Ke marker-size legend in a dedicated side axis."""
    labels = [*(f"< {value / 1e5:.1f}" for value in thresholds), f"> {thresholds[-1] / 1e5:.1f}"]
    handles = [
        ax.scatter([], [], s=size, color="#383838", edgecolors="none")
        for size in LPS_MARKER_SIZES
    ]
    ax.axis("off")
    ax.legend(
        handles,
        labels,
        title=r"Ke ($10^5\,J\,m^{-2}$)",
        loc="center left",
        frameon=False,
        labelspacing=1.45,
        handletextpad=1.1,
        borderaxespad=0,
        fontsize=8,
        title_fontsize=9,
    )


# -----------------------------------------------------------------------------
# Track panel
# -----------------------------------------------------------------------------

def _linear_marker_sizes(values: np.ndarray, low: float, high: float) -> np.ndarray:
    """Scale finite values to a marker-size interval, including constant data."""
    vmin = float(np.nanmin(values))
    vmax = float(np.nanmax(values))
    if np.isclose(vmin, vmax):
        return np.full(values.shape, (low + high) / 2.0)
    return low + (high - low) * (values - vmin) / (vmax - vmin)


def plot_track_panel(fig: plt.Figure, ax: plt.Axes, track: pd.DataFrame) -> None:
    """Draw the geographic trajectory directly from corrected track records."""
    plotted = track.sort_values("date").copy()
    plotted["vor42"] = plotted["vor42"].ffill().bfill()
    sampled = plotted.loc[plotted["Ke"].notna()].dropna(
        subset=["lon vor", "lat vor", "vor42", "Ke"]
    )
    if sampled.empty:
        raise ValueError("Cyclone track has no valid three-hourly Ke records")

    lons = sampled["lon vor"].to_numpy(dtype=float)
    lats = sampled["lat vor"].to_numpy(dtype=float)
    vor = sampled["vor42"].to_numpy(dtype=float)
    ke = sampled["Ke"].to_numpy(dtype=float)
    sizes = _linear_marker_sizes(ke, *TRACK_MARKER_SIZE_RANGE)

    ax.set_extent(
        [
            float(np.nanmin(lons)) - TRACK_PADDING_DEGREES,
            float(np.nanmax(lons)) + TRACK_PADDING_DEGREES,
            float(np.nanmin(lats)) - TRACK_PADDING_DEGREES,
            float(np.nanmax(lats)) + TRACK_PADDING_DEGREES,
        ],
        crs=ccrs.PlateCarree(),
    )
    ax.add_feature(cfeature.LAND, facecolor="lightgray", edgecolor="black", linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue", alpha=0.3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle=":")

    gridlines = ax.gridlines(
        draw_labels=True,
        dms=True,
        x_inline=False,
        y_inline=False,
        linewidth=0.45,
        alpha=0.5,
        linestyle="--",
    )
    gridlines.top_labels = False
    gridlines.right_labels = False
    gridlines.xlabel_style = {"size": 8}
    gridlines.ylabel_style = {"size": 8}

    ax.plot(
        lons,
        lats,
        color="black",
        linewidth=1.6,
        alpha=0.7,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    scatter = ax.scatter(
        lons,
        lats,
        c=vor,
        s=sizes,
        cmap=TRACK_CMAP,
        vmin=float(np.nanmin(vor)),
        vmax=float(np.nanmax(vor)),
        edgecolors="black",
        linewidths=0.7,
        alpha=0.9,
        transform=ccrs.PlateCarree(),
        zorder=2,
    )
    ax.scatter(
        lons[0],
        lats[0],
        s=260,
        marker="o",
        color="limegreen",
        edgecolors="black",
        linewidths=2,
        transform=ccrs.PlateCarree(),
        zorder=3,
    )
    ax.scatter(
        lons[-1],
        lats[-1],
        s=260,
        marker="X",
        color="red",
        edgecolors="black",
        linewidths=2,
        transform=ccrs.PlateCarree(),
        zorder=3,
    )

    colorbar = fig.colorbar(
        scatter,
        ax=ax,
        orientation="vertical",
        pad=0.025,
        shrink=0.90,
        aspect=28,
    )
    colorbar.set_label(
        r"Vorticity ($10^{-5}\,s^{-1}$)",
        rotation=270,
        fontweight="bold",
        labelpad=16,
    )
    colorbar.ax.tick_params(labelsize=8)

    ke_min = float(np.nanmin(ke))
    ke_max = float(np.nanmax(ke))
    ke_values = [ke_min, (ke_min + ke_max) / 2.0, ke_max]
    size_values = np.linspace(*TRACK_MARKER_SIZE_RANGE, 3)
    handles = [
        ax.scatter(
            [],
            [],
            s=size * TRACK_LEGEND_MARKER_SCALE,
            color="gray",
            edgecolors="black",
            linewidths=0.7,
            label=f"Ke={value / 1e5:.1f}",
        )
        for value, size in zip(ke_values, size_values)
    ]
    handles.extend(
        [
            Line2D(
                [],
                [],
                marker="o",
                linestyle="none",
                markerfacecolor="limegreen",
                markeredgecolor="black",
                markersize=9,
                label="Genesis",
            ),
            Line2D(
                [],
                [],
                marker="X",
                linestyle="none",
                markerfacecolor="red",
                markeredgecolor="black",
                markersize=9,
                label="Lysis",
            ),
        ]
    )
    ax.legend(
        handles=handles,
        loc="lower left",
        framealpha=0.95,
        edgecolor="black",
        labelspacing=1.0,
        handletextpad=0.7,
        fontsize=8,
    )
def add_panel_label(ax: plt.Axes, label: str, *, corner: str = "left") -> None:
    """Place a bold panel label inside the requested upper corner."""
    if corner not in {"left", "right"}:
        raise ValueError("corner must be 'left' or 'right'")
    x = 0.02 if corner == "left" else 0.98
    horizontal_alignment = "left" if corner == "left" else "right"
    ax.text(
        x,
        0.98,
        label,
        transform=ax.transAxes,
        fontsize=15,
        fontweight="bold",
        ha=horizontal_alignment,
        va="top",
        zorder=10,
    )


# -----------------------------------------------------------------------------
# Figure assembly
# -----------------------------------------------------------------------------

def create_figure(track: pd.DataFrame) -> plt.Figure:
    """Create all three panels from data and return the unsaved figure."""
    energy = prepare_lps_data(track)
    marker_sizes, size_thresholds = lps_size_encoding(energy["Ke"])
    color_norm, color_boundaries = ge_color_encoding(energy["Ge"])

    fig = plt.figure(figsize=FIGSIZE)
    outer = fig.add_gridspec(
        2,
        1,
        height_ratios=[1.55, 1.0],
        left=0.07,
        right=0.95,
        bottom=0.08,
        top=0.95,
        wspace=0.15,
    )
    top = outer[0].subgridspec(1, 2, width_ratios=[2.0, 0.17], wspace=0.035)
    lps_panels = top[0, 0].subgridspec(1, 2, wspace=0.2)
    side = top[0, 1].subgridspec(2, 1, height_ratios=[1.05, 1.0], hspace=0.14)
    colorbar_row = side[0, 0].subgridspec(1, 2, width_ratios=[0.18, 0.82])

    ax_conversion = fig.add_subplot(lps_panels[0, 0])
    ax_imports = fig.add_subplot(lps_panels[0, 1])
    colorbar_ax = fig.add_subplot(colorbar_row[0, 0])
    size_legend_ax = fig.add_subplot(side[1, 0])
    ax_track = fig.add_subplot(outer[1], projection=ccrs.PlateCarree())

    conversion_scatter = plot_lps_panel(
        ax_conversion,
        energy,
        lps_type="conversion",
        x_column="Ck",
        y_column="Ca",
        x_label=r"Ck ($W\,m^{-2}$)",
        y_label=r"Ca ($W\,m^{-2}$)",
        marker_sizes=marker_sizes,
        color_norm=color_norm,
    )
    plot_lps_panel(
        ax_imports,
        energy,
        lps_type="imports",
        x_column="BAe",
        y_column="BKe",
        x_label=r"BAe ($W\,m^{-2}$)",
        y_label=r"BKe ($W\,m^{-2}$)",
        marker_sizes=marker_sizes,
        color_norm=color_norm,
    )
    add_lps_colorbar(fig, colorbar_ax, conversion_scatter, color_boundaries)
    add_lps_size_legend(size_legend_ax, size_thresholds)

    plot_track_panel(fig, ax_track, track)

    add_panel_label(ax_conversion, "(a)")
    add_panel_label(ax_imports, "(b)")
    add_panel_label(ax_track, "(c)", corner="right")
    return fig


def main() -> int:
    """Load corrected data, build the figure once, and save it at 300 DPI."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    track = load_track(TRACK_ID)
    figure = create_figure(track)
    figure.savefig(OUTPUT_FILE, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    print(f"Saved: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
