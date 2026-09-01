#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lec_diagram.py — Shared drawing primitives for the four-box LEC diagram.

Geometry and conventions follow `plot_LEC.py` / `plot_LEC_eofs.py` of the thesis
repository (daniloceano/danilo_thesis_iag, manuscript_lec_climatology), so the
panels read like the published diagrams:

  * boxes are the budget tendencies, Az/Kz on top and Ae/Ke below;
  * each arrow is drawn in the direction the energy actually flows, i.e. the
    canonical direction for a positive value and the reverse for a negative one;
  * arrow thickness grows with |value|.

The before/after encoding added here is the doubled arrow: for a term that
changed, the dark arrow is the legacy (published) value and the red arrow is the
corrected (rerun) value, each with its own direction and thickness. Colour
therefore encodes the version, not the sign.

Used by `step5_plot_lec_diagram.py` (phase medians) and
`step6_plot_eof_diagram.py` (EOF loadings), which differ only in the quantity
plotted, the thickness scale and the panel caption.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    DIAGRAM_CORRECTED_COLOR,
    DIAGRAM_LEGACY_COLOR,
)

BOX_SIZE = 0.4
EDGE = BOX_SIZE / 2          # box half-width
OUTER = 1.0                  # where external arrows start
PARALLEL_OFFSET = 0.115      # separation of the doubled arrows
LABEL_STEP = 0.105           # spacing between stacked label lines
PANEL_TAGS = ["(A)", "(B)", "(C)", "(D)"]

# Axis half-ranges, trimmed to what the panel actually draws: arrow tails reach
# +/-1.0 in both directions, and the label stacks above and below the vertical
# external arrows reach +/-1.275. Anything wider is white space.
XLIMIT = 1.03
YLIMIT = 1.29
PANEL_ASPECT = YLIMIT / XLIMIT

BOXES = {
    "∂Az/∂t (finite diff.)": (-0.5, 0.5),
    "∂Kz/∂t (finite diff.)": (0.5, 0.5),
    "∂Ae/∂t (finite diff.)": (-0.5, -0.5),
    "∂Ke/∂t (finite diff.)": (0.5, -0.5),
}
BOX_LABELS = {
    "∂Az/∂t (finite diff.)": r"$\partial A_Z/\partial t$",
    "∂Kz/∂t (finite diff.)": r"$\partial K_Z/\partial t$",
    "∂Ae/∂t (finite diff.)": r"$\partial A_E/\partial t$",
    "∂Ke/∂t (finite diff.)": r"$\partial K_E/\partial t$",
}

# Every arrow of the classical diagram: the canonical positive direction, the
# axis it runs along, and where its label block sits.
#   tail/head : endpoints for a POSITIVE value (reversed when negative)
#   label     : anchor of the first label line, kept clear of the doubled
#               arrows, which sit at +/- PARALLEL_OFFSET from the arrow axis
#   step      : offset between stacked label lines
#   align     : horizontal alignment of the label block
ARROWS = {
    # conversions
    "Cz": dict(tail=(-0.3, 0.5), head=(0.3, 0.5), axis="h",
               label=(0.0, 0.72), step=(0, LABEL_STEP), align="center"),
    "Ca": dict(tail=(-0.5, 0.3), head=(-0.5, -0.3), axis="v",
               label=(-0.78, LABEL_STEP), step=(0, -LABEL_STEP), align="right"),
    "Ck": dict(tail=(0.5, -0.3), head=(0.5, 0.3), axis="v",
               label=(0.78, LABEL_STEP), step=(0, -LABEL_STEP), align="left"),
    "Ce": dict(tail=(-0.3, -0.5), head=(0.3, -0.5), axis="h",
               label=(0.0, -0.72), step=(0, -LABEL_STEP), align="center"),
    # generation and residual dissipation
    "Gz": dict(tail=(-0.5, OUTER), head=(-0.5, 0.7), axis="v",
               label=(-0.5, 1.04), step=(0, LABEL_STEP), align="center"),
    "RKz": dict(tail=(0.5, OUTER), head=(0.5, 0.7), axis="v",
                label=(0.5, 1.04), step=(0, LABEL_STEP), align="center"),
    "Ge": dict(tail=(-0.5, -OUTER), head=(-0.5, -0.7), axis="v",
               label=(-0.5, -1.04), step=(0, -LABEL_STEP), align="center"),
    "RKe": dict(tail=(0.5, -OUTER), head=(0.5, -0.7), axis="v",
                label=(0.5, -1.04), step=(0, -LABEL_STEP), align="center"),
    # lateral boundary transports
    "BAz": dict(tail=(-OUTER, 0.5), head=(-0.7, 0.5), axis="h",
                label=(-0.85, 0.72), step=(0, LABEL_STEP), align="center"),
    "BAe": dict(tail=(-OUTER, -0.5), head=(-0.7, -0.5), axis="h",
                label=(-0.85, -0.72), step=(0, -LABEL_STEP), align="center"),
    "BKz": dict(tail=(OUTER, 0.5), head=(0.7, 0.5), axis="h",
                label=(0.85, 0.72), step=(0, LABEL_STEP), align="center"),
    "BKe": dict(tail=(OUTER, -0.5), head=(0.7, -0.5), axis="h",
                label=(0.85, -0.72), step=(0, -LABEL_STEP), align="center"),
}

ARROW_LABELS = {
    "Cz": r"$C_Z$", "Ca": r"$C_A$", "Ck": r"$C_K$", "Ce": r"$C_E$",
    "Gz": r"$G_Z$", "Ge": r"$G_E$", "RKz": r"$R_{K_Z}$", "RKe": r"$R_{K_E}$",
    "BAz": r"$BA_Z$", "BAe": r"$BA_E$", "BKz": r"$BK_Z$", "BKe": r"$BK_E$",
}

# Terms the classical four-box diagram has no place for.
OMITTED_TERMS = ["BΦZ", "BΦE", "RGz", "RGe"]

DRAWN_TERMS = list(BOXES) + list(ARROWS)


def wrap_note(text: str, width: int = 132) -> str:
    """Wrap a footnote so it does not end up wider than the figure itself.

    ``savefig(bbox_inches="tight")`` grows the canvas to fit whatever is widest,
    so a single long footnote line silently pads white space onto both sides of
    every panel. 132 characters at 11 pt fits the panel grid.
    """
    return textwrap.fill(text, width)


def panel_grid(panel_width: float = 6.0, rows: int = 2, columns: int = 2,
               title_inches: float = 0.95, bottom_inches: float = 1.05,
               gap: float = 0.42, margin: float = 0.18):
    """A panel grid whose axes match PANEL_ASPECT exactly.

    The panels use ``set_aspect("equal")``, so any mismatch between the figure
    geometry and the data aspect comes back as white margins inside every
    panel. Everything here is therefore laid out in inches — panel size, the
    gaps between panels, and the title and legend bands — and converted to
    figure fractions at the end. ``tight_layout`` is deliberately not used: it
    reasons about the allotted boxes rather than the aspect-corrected axes, and
    leaves the panels either overlapping or adrift.

    Returns the figure and the axes array.
    """
    panel_height = panel_width * PANEL_ASPECT
    figure_width = 2 * margin + columns * panel_width + (columns - 1) * gap
    grid_height = rows * panel_height + (rows - 1) * gap
    figure_height = grid_height + title_inches + bottom_inches

    figure, axes = plt.subplots(rows, columns, figsize=(figure_width, figure_height))
    figure.subplots_adjust(
        left=margin / figure_width,
        right=1 - margin / figure_width,
        bottom=bottom_inches / figure_height,
        top=1 - title_inches / figure_height,
        wspace=gap / panel_width,
        hspace=gap / panel_height,
    )
    return figure, axes


def shift(point: tuple[float, float], axis: str, amount: float) -> tuple[float, float]:
    """Offset a point perpendicular to the arrow axis."""
    if axis == "h":
        return (point[0], point[1] + amount)
    return (point[0] + amount, point[1])


def draw_arrow(ax, spec: dict, value: float, color: str, offset: float, width: float) -> None:
    tail, head = spec["tail"], spec["head"]
    if value < 0:
        tail, head = head, tail
    tail = shift(tail, spec["axis"], offset)
    head = shift(head, spec["axis"], offset)
    ax.annotate(
        "",
        xy=head,
        xytext=tail,
        arrowprops=dict(
            facecolor=color,
            edgecolor=color,
            width=width,
            headwidth=width * 2.3,
            headlength=width * 2.3,
        ),
        annotation_clip=False,
    )


def draw_stack(ax, anchor, step, align, lines, fontsize=11) -> None:
    """Write a stacked label block that always reads top to bottom."""
    x, y = anchor
    dx, dy = step
    positions = [(x + index * dx, y + index * dy) for index in range(len(lines))]
    if dy > 0:
        positions.reverse()
    for (px, py), (text, color) in zip(positions, lines):
        ax.text(px, py, text, ha=align, va="center", fontsize=fontsize,
                color=color, fontweight="bold", clip_on=False)


def draw_panel(ax, legacy, corrected, changed, center_lines, width_of, value_format="{:.2f}") -> None:
    """Draw one before/after panel.

    legacy, corrected : mappings term -> value (corrected is read only for the
                        terms listed in `changed`)
    changed           : terms to draw with a doubled arrow and two values
    center_lines      : list of (text, fontsize, colour, weight) for the middle
    width_of          : callable mapping a value to an arrow width in points
    """
    ax.set_xlim(-XLIMIT, XLIMIT)
    ax.set_ylim(-YLIMIT, YLIMIT)
    ax.set_aspect("equal")
    ax.axis("off")

    for term, (cx, cy) in BOXES.items():
        ax.add_patch(
            patches.Rectangle(
                (cx - EDGE, cy - EDGE), BOX_SIZE, BOX_SIZE,
                fill=True, color="skyblue", ec="black", linewidth=1.4, zorder=2,
            )
        )
        lines = [(BOX_LABELS[term], "black"),
                 (value_format.format(legacy[term]), DIAGRAM_LEGACY_COLOR)]
        if term in changed:
            lines.append((value_format.format(corrected[term]), DIAGRAM_CORRECTED_COLOR))
            anchor, step = (cx, cy + 0.085), (0, -0.085)
        else:
            anchor, step = (cx, cy + 0.055), (0, -0.12)
        for (px, py), (text, color) in zip(
            [(anchor[0] + i * step[0], anchor[1] + i * step[1]) for i in range(len(lines))],
            lines,
        ):
            ax.text(px, py, text, ha="center", va="center", fontsize=11,
                    color=color, fontweight="bold", zorder=3)

    for term, spec in ARROWS.items():
        value = float(legacy[term])
        lines = [(ARROW_LABELS[term], "black"),
                 (value_format.format(value), DIAGRAM_LEGACY_COLOR)]
        if term in changed:
            new = float(corrected[term])
            draw_arrow(ax, spec, value, DIAGRAM_LEGACY_COLOR, -PARALLEL_OFFSET, width_of(value))
            draw_arrow(ax, spec, new, DIAGRAM_CORRECTED_COLOR, PARALLEL_OFFSET, width_of(new))
            lines.append((value_format.format(new), DIAGRAM_CORRECTED_COLOR))
        else:
            draw_arrow(ax, spec, value, DIAGRAM_LEGACY_COLOR, 0.0, width_of(value))
        draw_stack(ax, spec["label"], spec["step"], spec["align"], lines)

    span = 0.082
    top = (len(center_lines) - 1) / 2 * span
    for index, (text, size, color, weight) in enumerate(center_lines):
        ax.text(0, top - index * span, text, ha="center", va="center",
                fontsize=size, color=color, fontweight=weight)
