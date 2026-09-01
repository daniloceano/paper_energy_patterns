#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step5_plot_lec_diagram.py — Before/after Lorenz Energy Cycle box diagram.

Draws the classical four-box LEC diagram, one panel per life-cycle phase, with
the legacy and the corrected median of every term shown together. Geometry and
conventions come from `lec_diagram.py`, which follows `plot_LEC.py` of the
thesis repository: arrows point in the direction the energy actually flows and
their thickness scales with |median|. Where a term changed, the arrow is
doubled — dark is legacy, red is corrected.

The classical diagram has no place for BΦZ, BΦE, RGz and RGe, so those four are
listed in a footnote rather than silently dropped.

Usage
-----
    python scripts/lec_rerun_comparison/step5_plot_lec_diagram.py
    python scripts/lec_rerun_comparison/step5_plot_lec_diagram.py --no-pdf

Outputs (figures/lec_rerun_comparison/)
---------------------------------------
    lec_diagram_before_after.png / .pdf

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    DIAGRAM_CORRECTED_COLOR,
    DIAGRAM_LEGACY_COLOR,
    FIGURES_DIR,
    PHASE_SUMMARY,
    PHASES,
    TERM_SUMMARY,
    split_changed,
)
from scripts.lec_rerun_comparison.lec_diagram import (  # noqa: E402
    OMITTED_TERMS,
    PANEL_TAGS,
    draw_panel,
    panel_grid,
    wrap_note,
)

TITLE_BAND = 0.95      # inches reserved above the grid
BOTTOM_BAND = 1.50     # inches reserved for the legend and the two footnotes


def width_of(value: float) -> float:
    """Arrow width in points for a term median in W m⁻².

    The cap is tied to lec_diagram.PARALLEL_OFFSET: the two arrowheads of a
    doubled term must not overlap.
    """
    return min(1.8 + 1.15 * abs(value), 8.5)


def footnote(pooled: pd.DataFrame) -> str:
    parts = [
        f"{term} {pooled.loc[term, 'median_legacy']:.2f} → "
        f"{pooled.loc[term, 'median_corrected']:.2f}"
        for term in OMITTED_TERMS
        if term in pooled.index
    ]
    if not parts:
        return ""
    return (
        "Changed terms with no place in the classical diagram "
        "(medians over all phases, W m⁻²):  " + " · ".join(parts)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()

    for path in (PHASE_SUMMARY, TERM_SUMMARY):
        if not path.is_file():
            raise SystemExit(f"{path} not found; run steps 1 and 3 first")

    by_phase = pd.read_csv(PHASE_SUMMARY)
    pooled = pd.read_csv(TERM_SUMMARY)
    changed = set(split_changed(pooled)[0])
    pooled = pooled.set_index("term")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    figure, axes = panel_grid(
        panel_width=6.0, title_inches=TITLE_BAND, bottom_inches=BOTTOM_BAND
    )
    height = figure.get_size_inches()[1]
    for ax, phase, tag in zip(axes.flat, PHASES, PANEL_TAGS):
        values = by_phase[by_phase["phase"] == phase].set_index("term")
        draw_panel(
            ax,
            legacy=values["median_legacy"],
            corrected=values["median_corrected"],
            changed=changed,
            center_lines=[
                (tag, 15, "black", "bold"),
                (phase, 12, "0.25", "normal"),
            ],
            width_of=width_of,
        )

    handles = [
        plt.Line2D([], [], color=DIAGRAM_LEGACY_COLOR, linewidth=4,
                   label="legacy (published)"),
        plt.Line2D([], [], color=DIAGRAM_CORRECTED_COLOR, linewidth=4,
                   label="corrected (rerun)"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
                  fontsize=13, bbox_to_anchor=(0.5, 0.95 / height))
    figure.suptitle(
        "Lorenz Energy Cycle before and after the toolkit correction\n"
        "phase medians (W m⁻²); doubled arrows mark terms that changed",
        fontsize=17,
        y=1 - 0.28 / height,
        va="top",
    )
    figure.text(
        0.5, 0.70 / height,
        wrap_note("Arrows point in the direction the energy flows; thickness "
                  "scales with |median|. Unchanged terms carry a single arrow."),
        ha="center", va="top", fontsize=11, color="0.3",
    )
    note = footnote(pooled)
    if note:
        figure.text(0.5, 0.36 / height, wrap_note(note), ha="center", va="top",
                    fontsize=11, color="0.3")

    stem = FIGURES_DIR / "lec_diagram_before_after"
    figure.savefig(f"{stem}.png", dpi=180, bbox_inches="tight")
    if not args.no_pdf:
        figure.savefig(f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)
    print(f"wrote {stem}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
