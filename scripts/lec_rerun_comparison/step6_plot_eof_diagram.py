#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step6_plot_eof_diagram.py — Before/after EOF loadings on the LEC diagram.

Replicates the EOF diagram of the thesis (`plot_LEC_eofs.py`, from the EOFs
computed by `eof_analysis_with_track_id.py` in
daniloceano/energetic_patterns_cyclones_south_atlantic) and adds the corrected
rerun as a second, red arrow wherever a loading moved.

Method, identical to the published analysis
-------------------------------------------
For each life-cycle phase, the matrix of cyclones x 24 LEC terms is centred and
divided by the sample standard deviation, and the EOFs are the eigenvectors of
the resulting correlation matrix scaled by the square root of their eigenvalue.
A loading is therefore the correlation between the term and the unit-variance
principal component, bounded in [-1, 1]. This reproduces the published
`eofs.csv` and `variance_fraction.csv` to the precision at which they are
stored (max |Δ| ~1e-4, explained variances 20.79 / 28.63 / 28.47 / 29.03 % for
EOF 1).

Two things differ from the published figure, both deliberate:

  * both sides are recomputed on the paired sample of this comparison (the
    cyclones the rerun has finished), not on the full published population, so
    that legacy and corrected differ only by the toolkit correction. The legacy
    loadings are therefore close to, but not identical to, the published ones.
  * the sign of an EOF is arbitrary and the rank of a mode is not stable when
    two modes explain similar variance (EOF 2 and EOF 3 are within ~1% of each
    other). Corrected modes are therefore matched to legacy modes by maximum
    absolute pattern correlation, one to one, and then sign-flipped to agree.
    Any rank swap is recorded in `eof_variance.csv` and printed. Without this
    the comparison would be meaningless.

BΦZ, BΦE, RGz and RGe take part in the EOF but have no place in the classical
four-box diagram; their loadings are written to the CSV instead.

Usage
-----
    python scripts/lec_rerun_comparison/step6_plot_eof_diagram.py
    python scripts/lec_rerun_comparison/step6_plot_eof_diagram.py --eof 2 --tol 0.10

Outputs
-------
    figures/lec_rerun_comparison/eof<N>_diagram_before_after.png / .pdf
    results/lec_rerun_comparison/eof_loadings.csv    all modes, all terms
    results/lec_rerun_comparison/eof_variance.csv    explained variance and
                                                     pattern correlation

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import linear_sum_assignment  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    ALL_TERMS,
    DIAGRAM_CORRECTED_COLOR,
    DIAGRAM_LEGACY_COLOR,
    FIGURES_DIR,
    PAIRED_TABLE,
    PHASES,
    RESULTS_DIR,
)
from scripts.lec_rerun_comparison.lec_diagram import (  # noqa: E402
    DRAWN_TERMS,
    OMITTED_TERMS,
    PANEL_TAGS,
    draw_panel,
    panel_grid,
    wrap_note,
)

TITLE_BAND = 1.30      # inches reserved above the grid (three-line title)
BOTTOM_BAND = 1.50     # inches reserved for the legend and the two footnotes

LOADINGS_CSV = RESULTS_DIR / "eof_loadings.csv"
VARIANCE_CSV = RESULTS_DIR / "eof_variance.csv"
N_MODES = 8


def width_of(value: float) -> float:
    """Arrow width in points for an EOF loading, which lives in [-1, 1].

    The cap is tied to lec_diagram.PARALLEL_OFFSET: the two arrowheads of a
    doubled term must not overlap.
    """
    return min(1.5 + 8.0 * abs(value), 8.5)


def compute_eof(frame: pd.DataFrame, terms: list[str], n_modes: int = N_MODES):
    """Correlation-matrix EOFs, as in the published analysis.

    Returns the loadings (n_modes x n_terms) and the explained variance
    fractions.
    """
    values = frame[terms].astype(float)
    standardized = (values - values.mean(axis=0)) / values.std(axis=0)
    covariance = np.cov(standardized.to_numpy(), rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1][:n_modes]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    loadings = (eigenvectors * np.sqrt(eigenvalues)).T
    return loadings, eigenvalues / np.trace(covariance)


def orient(loadings: np.ndarray) -> np.ndarray:
    """Make the largest-magnitude loading of every mode positive."""
    dominant = np.take_along_axis(
        loadings, np.abs(loadings).argmax(axis=1)[:, None], axis=1
    ).ravel()
    return loadings * np.where(dominant < 0, -1.0, 1.0)[:, None]


def match_modes(reference: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pair target modes with reference modes, ignoring rank and sign.

    Mode rank is not stable when two modes explain similar variance, so the
    pairing maximises the total absolute pattern correlation rather than
    assuming corrected mode k belongs with legacy mode k. Returns the target
    order and the sign each matched mode needs to agree with its reference.
    """
    correlation = np.corrcoef(reference, target)[: len(reference), len(reference):]
    rows, columns = linear_sum_assignment(-np.abs(correlation))
    order = columns[np.argsort(rows)]
    signs = np.sign(correlation[np.arange(len(order)), order])
    signs[signs == 0] = 1.0
    return order, signs


def wide_frames(paired: pd.DataFrame, terms: list[str]):
    keys = ["track_id", "period", "phase"]
    legacy = paired.pivot_table(index=keys, columns="term", values="legacy")
    corrected = paired.pivot_table(index=keys, columns="term", values="corrected")
    return legacy[terms], corrected[terms]


def analyse(paired: pd.DataFrame, terms: list[str]):
    """EOFs per phase for both versions, sign-aligned, plus their diagnostics."""
    legacy_wide, corrected_wide = wide_frames(paired, terms)
    loadings, variance = [], []
    for phase in PHASES:
        mask = legacy_wide.index.get_level_values("phase") == phase
        legacy_modes, legacy_evf = compute_eof(legacy_wide[mask], terms)
        corrected_modes, corrected_evf = compute_eof(corrected_wide[mask], terms)
        legacy_modes = orient(legacy_modes)
        order, signs = match_modes(legacy_modes, orient(corrected_modes))
        corrected_modes = orient(corrected_modes)[order] * signs[:, None]
        corrected_evf = corrected_evf[order]
        for mode in range(legacy_modes.shape[0]):
            for index, term in enumerate(terms):
                loadings.append(
                    {
                        "phase": phase,
                        "eof": mode + 1,
                        "term": term,
                        "legacy": legacy_modes[mode, index],
                        "corrected": corrected_modes[mode, index],
                        "diff": corrected_modes[mode, index] - legacy_modes[mode, index],
                    }
                )
            variance.append(
                {
                    "phase": phase,
                    "eof": mode + 1,
                    "n": int(mask.sum()),
                    "explained_variance_legacy": 100 * legacy_evf[mode],
                    "explained_variance_corrected": 100 * corrected_evf[mode],
                    "corrected_mode_rank": int(order[mode]) + 1,
                    "rank_swapped": bool(order[mode] != mode),
                    "pattern_correlation": float(
                        np.corrcoef(legacy_modes[mode], corrected_modes[mode])[0, 1]
                    ),
                    "max_abs_loading_change": float(
                        np.abs(corrected_modes[mode] - legacy_modes[mode]).max()
                    ),
                }
            )
    return pd.DataFrame(loadings), pd.DataFrame(variance)


def footnote(loadings: pd.DataFrame, eof: int) -> str:
    block = loadings[(loadings["eof"] == eof) & (loadings["term"].isin(OMITTED_TERMS))]
    if block.empty:
        return ""
    worst = block.loc[block["diff"].abs().idxmax()]
    return (
        f"{', '.join(OMITTED_TERMS)} take part in the EOF but have no place in the "
        f"classical diagram; their loadings are in results/lec_rerun_comparison/"
        f"eof_loadings.csv (largest change: {worst['term']} "
        f"{worst['legacy']:+.2f} → {worst['corrected']:+.2f} during {worst['phase']})."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--eof", type=int, default=1, help="mode to draw (1-based)")
    parser.add_argument("--tol", type=float, default=0.05,
                        help="minimum |Δloading| for an arrow to be doubled")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()

    if not PAIRED_TABLE.is_file():
        raise SystemExit(f"{PAIRED_TABLE} not found; run step 1 first")
    paired = pd.read_parquet(PAIRED_TABLE)
    terms = [term for term in ALL_TERMS if term in set(paired["term"])]

    loadings, variance = analyse(paired, terms)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    loadings.to_csv(LOADINGS_CSV, index=False, float_format="%.6g")
    variance.to_csv(VARIANCE_CSV, index=False, float_format="%.6g")

    selected = loadings[loadings["eof"] == args.eof]
    print(f"\nEOF {args.eof}: legacy vs corrected")
    print(
        variance[variance["eof"] == args.eof][
            ["phase", "n", "explained_variance_legacy", "explained_variance_corrected",
             "corrected_mode_rank", "rank_swapped", "pattern_correlation",
             "max_abs_loading_change"]
        ].to_string(index=False, float_format=lambda v: f"{v:.3f}")
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    figure, axes = panel_grid(
        panel_width=6.0, title_inches=TITLE_BAND, bottom_inches=BOTTOM_BAND
    )
    height = figure.get_size_inches()[1]
    for ax, phase, tag in zip(axes.flat, PHASES, PANEL_TAGS):
        block = selected[selected["phase"] == phase].set_index("term")
        drawn = [term for term in DRAWN_TERMS if term in block.index]
        changed = {term for term in drawn if abs(block.loc[term, "diff"]) >= args.tol}
        row = variance[(variance["eof"] == args.eof) & (variance["phase"] == phase)].iloc[0]
        draw_panel(
            ax,
            legacy=block["legacy"],
            corrected=block["corrected"],
            changed=changed,
            center_lines=[
                (tag, 15, "black", "bold"),
                (f"EOF {args.eof}", 12, "0.25", "normal"),
                (phase, 11.5, "0.25", "normal"),
                ("Exp. Var.", 10.5, "0.25", "normal"),
                (f"{row['explained_variance_legacy']:.2f}%", 11, DIAGRAM_LEGACY_COLOR, "bold"),
                (f"{row['explained_variance_corrected']:.2f}%", 11,
                 DIAGRAM_CORRECTED_COLOR, "bold"),
            ] + ([(f"(corrected mode {int(row['corrected_mode_rank'])})", 10,
                   DIAGRAM_CORRECTED_COLOR, "normal")] if row["rank_swapped"] else []),
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
        f"EOF {args.eof} of the Lorenz Energy Cycle before and after the toolkit "
        f"correction\nloadings (correlation with the PC); doubled arrows mark "
        f"|Δ| ≥ {args.tol:.2f}",
        fontsize=17,
        y=1 - 0.28 / height,
        va="top",
    )
    figure.text(
        0.5, 0.70 / height,
        wrap_note("Arrows point in the direction implied by the sign of the "
                  "loading; thickness scales with |loading|. Both modes are "
                  "recomputed on the paired sample and sign-aligned."),
        ha="center", va="top", fontsize=11, color="0.3",
    )
    note = footnote(loadings, args.eof)
    if note:
        figure.text(0.5, 0.36 / height, wrap_note(note), ha="center", va="top",
                    fontsize=11, color="0.3")

    stem = FIGURES_DIR / f"eof{args.eof}_diagram_before_after"
    figure.savefig(f"{stem}.png", dpi=180, bbox_inches="tight")
    if not args.no_pdf:
        figure.savefig(f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)
    print(f"\nwrote {stem}.png")
    print(f"wrote {LOADINGS_CSV}")
    print(f"wrote {VARIANCE_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
