#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: Figures of the Ck decomposition for every Energy Pattern.

Three figures, each answering one of the questions of step 2 and each now
covering EP1, EP2 and EP3 side by side instead of EP1 alone:

``ck_subterms_vertical_profiles.png``
    Mean pressure-level profile of the total C_K and of its five subterms,
    one panel per Energy Pattern, intensification phase. Shows *where* in the
    troposphere each mechanism acts and whether the EPs differ in vertical
    structure or only in amplitude.

``ck_subterms_boxplots.png``
    Distribution of the vertically integrated subterms per Energy Pattern
    during intensification. Boxes are notched, so non-overlapping notches
    indicate a median difference consistent with the tests of step 2.

``ck_subterms_lifecycle.png``
    Phase-by-phase evolution of the ensemble-mean subterms, one panel per
    Energy Pattern, showing which mechanism leads intensification and which
    sustains the mature phase.

Inputs
------
    results/ck_subterms_corrected/subterms_by_cyclone.csv     (step 1)
    results/ck_subterms_corrected/subterm_statistics.csv      (step 2)
    data/corrected/vertical_phase_means_corrected.parquet     (profiles)

Outputs
-------
    figures/ck_subterms_corrected/*.png

Usage
-----
    python scripts/ck_subterms_analysis/step3_subterm_figures.py
    python scripts/ck_subterms_analysis/step3_subterm_figures.py --allow-partial

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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import corrected_lec as clec  # noqa: E402
from scripts.utils import ep_mapping as em  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "results" / "ck_subterms_corrected"
FIGURES_DIR = PROJECT_ROOT / "figures" / "ck_subterms_corrected"

DPI = 300

#: One colour per subterm, kept distinct from the EP palette so a reader never
#: confuses "which pattern" with "which mechanism".
SUBTERM_COLORS = {
    "Ck_1": "#264653",
    "Ck_2": "#2a9d8f",
    "Ck_3": "#e9c46a",
    "Ck_4": "#f4a261",
    "Ck_5": "#e76f51",
}

PHASE_ORDER = clec.PHASES

#: Pressure-level values are per-Pa densities (~1e-4). Rendering them as the
#: contribution of a 100 hPa layer keeps the axis readable without changing the
#: quantity: 1 W m-2 Pa-1 = 1e4 W m-2 per 100 hPa.
PER_100HPA = 1.0e4


def _style() -> None:
    plt.rcParams.update({
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 10,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "axes.grid": True,
        "grid.alpha": 0.25,
    })


def _ep_labels(table: pd.DataFrame) -> list[str]:
    """Energy Patterns present, in canonical order."""
    present = set(table["ep_label"])
    return [em.EP_LABELS[ep] for ep in em.ALL_EPS if em.EP_LABELS[ep] in present]


def figure_vertical_profiles(profiles: pd.DataFrame, assignments: pd.DataFrame) -> Path:
    """Mean vertical profile of C_K and its subterms, per Energy Pattern."""
    intensifying = profiles[profiles["phase"] == "intensification"].merge(
        assignments[["track_id", "ep"]], on="track_id", how="inner"
    )
    intensifying["ep_label"] = intensifying["ep"].map(em.EP_LABELS)
    labels = _ep_labels(intensifying)

    figure, axes = plt.subplots(
        1, len(labels), figsize=(4.4 * len(labels), 6.4), sharey=True, sharex=True
    )
    axes = np.atleast_1d(axes)

    for axis, ep_label in zip(axes, labels):
        subset = intensifying[intensifying["ep_label"] == ep_label]
        n_cyclones = subset["track_id"].nunique()

        total = subset[subset["term"] == "Ck"].groupby("level_hpa")["value"].mean()
        axis.plot(
            total.to_numpy() * PER_100HPA, total.index.to_numpy(),
            color="black", linewidth=2.4, label=r"$C_K$", zorder=5,
        )
        for stem in clec.CK_SUBTERMS:
            profile = subset[subset["term"] == stem].groupby("level_hpa")["value"].mean()
            axis.plot(
                profile.to_numpy() * PER_100HPA, profile.index.to_numpy(),
                color=SUBTERM_COLORS[stem], linewidth=1.6,
                label=clec.CK_SUBTERM_MATH[stem],
            )

        axis.axvline(0.0, color="grey", linewidth=0.8, linestyle="--")
        axis.set_title(f"{ep_label} (N = {n_cyclones})")
        axis.set_xlabel(r"$C_K$ contribution (W m$^{-2}$ per 100 hPa)")

    axes[0].set_ylabel("Pressure (hPa)")
    axes[0].invert_yaxis()
    axes[0].legend(loc="lower left", frameon=True, framealpha=0.9)
    figure.suptitle(
        "Vertical structure of the barotropic conversion and its subterms "
        "— intensification phase",
        y=0.98,
    )
    figure.tight_layout()

    path = FIGURES_DIR / "ck_subterms_vertical_profiles.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def figure_boxplots(table: pd.DataFrame) -> Path:
    """Distribution of the integrated subterms per Energy Pattern."""
    intensifying = table[table["phase"] == "intensification"]
    labels = _ep_labels(intensifying)

    figure, axis = plt.subplots(figsize=(11, 6))
    width = 0.8 / len(labels)

    for offset, ep_label in enumerate(labels):
        subset = intensifying[intensifying["ep_label"] == ep_label]
        positions = np.arange(len(clec.CK_SUBTERMS)) + (offset - (len(labels) - 1) / 2) * width
        data = [subset[stem].dropna().to_numpy() for stem in clec.CK_SUBTERMS]
        ep_number = next(ep for ep, name in em.EP_LABELS.items() if name == ep_label)
        colour = em.EP_COLORS[ep_number]
        boxes = axis.boxplot(
            data, positions=positions, widths=width * 0.85, notch=True,
            patch_artist=True, showfliers=False, manage_ticks=False,
        )
        for patch in boxes["boxes"]:
            patch.set_facecolor(colour)
            patch.set_alpha(0.65)
        for element in ("medians", "whiskers", "caps"):
            for line in boxes[element]:
                line.set_color("black")
                line.set_linewidth(1.0)
        axis.plot([], [], color=colour, linewidth=8, alpha=0.65,
                  label=f"{ep_label} (N = {subset['track_id'].nunique()})")

    axis.axhline(0.0, color="grey", linewidth=0.9, linestyle="--")
    axis.set_xticks(np.arange(len(clec.CK_SUBTERMS)))
    axis.set_xticklabels([clec.CK_SUBTERM_MATH[stem] for stem in clec.CK_SUBTERMS])
    axis.set_ylabel(r"Integrated conversion (W m$^{-2}$)")
    axis.set_title(
        "Barotropic conversion subterms by Energy Pattern — intensification phase\n"
        r"negative values transfer energy from the mean flow to the eddy ($K_Z \to K_E$)"
    )
    axis.legend(frameon=True)
    figure.tight_layout()

    path = FIGURES_DIR / "ck_subterms_boxplots.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def figure_lifecycle(table: pd.DataFrame) -> Path:
    """Phase-by-phase evolution of the ensemble-mean subterms."""
    labels = _ep_labels(table)
    phases = [phase for phase in PHASE_ORDER if phase in set(table["phase"])]

    figure, axes = plt.subplots(
        1, len(labels), figsize=(4.4 * len(labels), 5.2), sharey=True
    )
    axes = np.atleast_1d(axes)
    positions = np.arange(len(phases))

    for axis, ep_label in zip(axes, labels):
        subset = table[table["ep_label"] == ep_label]
        means = subset.groupby("phase", observed=True)[["Ck", *clec.CK_SUBTERMS]].mean()
        means = means.reindex(phases)

        axis.plot(
            positions, means["Ck"].to_numpy(),
            color="black", linewidth=2.4, marker="o", label=r"$C_K$", zorder=5,
        )
        for stem in clec.CK_SUBTERMS:
            axis.plot(
                positions, means[stem].to_numpy(),
                color=SUBTERM_COLORS[stem], linewidth=1.6, marker="s", markersize=4,
                label=clec.CK_SUBTERM_MATH[stem],
            )

        axis.axhline(0.0, color="grey", linewidth=0.8, linestyle="--")
        axis.set_xticks(positions)
        axis.set_xticklabels([phase[:3].capitalize() for phase in phases])
        axis.set_title(f"{ep_label} (N = {subset['track_id'].nunique()})")

    axes[0].set_ylabel(r"Ensemble-mean conversion (W m$^{-2}$)")
    axes[0].legend(loc="best", frameon=True, framealpha=0.9)
    figure.suptitle("Lifecycle evolution of the barotropic conversion subterms", y=0.99)
    figure.tight_layout()

    path = FIGURES_DIR / "ck_subterms_lifecycle.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot the all-EP Ck decomposition.")
    parser.add_argument("--profiles", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    table_path = RESULTS_DIR / "subterms_by_cyclone.csv"
    if not table_path.is_file():
        raise SystemExit(
            f"missing {table_path}\n"
            "Run scripts/ck_subterms_analysis/step1_build_subterms_table.py first."
        )
    table = pd.read_csv(table_path, dtype={"track_id": str})

    source = args.profiles
    if source is None:
        source = clec.corrected_path(clec.VERTICAL_PHASE_MEANS)
        if not source.is_file() and args.allow_partial:
            source = clec.corrected_path(
                clec.VERTICAL_PHASE_MEANS.replace(".parquet", "_partial.parquet")
            )
    if not source.is_file():
        raise SystemExit(f"vertical phase means not found: {source}")
    if "_partial" in source.name and not args.allow_partial:
        raise SystemExit(f"{source.name} is a partial build; pass --allow-partial")

    profiles = pd.read_parquet(source)
    assignments = em.load_ep_assignments()

    _style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for path in (
        figure_vertical_profiles(profiles, assignments),
        figure_boxplots(table),
        figure_lifecycle(table),
    ):
        print(f"  wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
