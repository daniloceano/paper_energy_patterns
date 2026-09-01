#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step2_plot_split_violins.py — Split violins of legacy vs corrected LEC terms.

One figure per LEC term family (energy, conversion, generation, boundary,
budget, residual). Each panel is one term; within a panel the x-axis is the
life-cycle phase and each violin is split: the left half is the legacy
(published) value and the right half is the corrected (rerun) value for the
very same cyclone-phase samples. Inner quartile lines and the zero line make
sign changes readable at a glance.

Distributions are trimmed to a symmetric percentile window (default 2.5-97.5 of the
pooled legacy+corrected sample of each panel) so that the kernel densities stay
legible; the number of samples outside the window is annotated. Trimming is a
display choice only - every statistic in step 3 uses the full sample.

Usage
-----
    python scripts/lec_rerun_comparison/step2_plot_split_violins.py
    python scripts/lec_rerun_comparison/step2_plot_split_violins.py --group conversion
    python scripts/lec_rerun_comparison/step2_plot_split_violins.py --trim 2 --no-pdf

Outputs (figures/lec_rerun_comparison/)
---------------------------------------
    violin_<group>.png / .pdf     one per term family
    signflip_heatmap.png / .pdf   sign-change rate per term and phase

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
import seaborn as sns  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    CORRECTED_COLOR,
    FIGURES_DIR,
    GROUPS,
    GROUP_TITLES,
    LEGACY_COLOR,
    PAIRED_TABLE,
    PHASES,
    label,
)

PALETTE = {"legacy": LEGACY_COLOR, "corrected": CORRECTED_COLOR}
HUE_ORDER = ["legacy", "corrected"]


def load_paired() -> pd.DataFrame:
    if not PAIRED_TABLE.is_file():
        raise FileNotFoundError(f"{PAIRED_TABLE} not found; run step 1 first")
    return pd.read_parquet(PAIRED_TABLE)


def to_long(frame: pd.DataFrame) -> pd.DataFrame:
    long = frame.melt(
        ["track_id", "period", "phase", "term"],
        value_vars=["legacy", "corrected"],
        var_name="version",
        value_name="value",
    )
    long["phase"] = pd.Categorical(long["phase"], categories=PHASES, ordered=True)
    return long


def panel(ax, data: pd.DataFrame, term: str, unit: str, trim: float) -> None:
    low, high = np.nanpercentile(data["value"], [trim, 100 - trim])
    span = high - low
    low, high = low - 0.03 * span, high + 0.03 * span
    inside = data[data["value"].between(low, high)]
    hidden = len(data) - len(inside)

    sns.violinplot(
        data=inside,
        x="phase",
        y="value",
        hue="version",
        hue_order=HUE_ORDER,
        order=PHASES,
        split=True,
        gap=0.06,
        inner="quart",
        cut=0,
        density_norm="width",
        linewidth=0.7,
        palette=PALETTE,
        ax=ax,
    )
    ax.axhline(0.0, color="0.25", linewidth=0.8, linestyle="--", zorder=0)
    ax.set_title(f"{label(term)}", fontsize=13, pad=4)
    ax.set_xlabel("")
    ax.set_ylabel(unit, fontsize=9)
    ax.set_ylim(low, high)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", labelsize=8)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 4), useMathText=True)
    ax.yaxis.get_offset_text().set_fontsize(8)
    if hidden:
        ax.text(
            0.015,
            0.975,
            f"{100 * hidden / len(data):.1f}% outside range",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=7,
            color="0.4",
        )
    if ax.get_legend():
        ax.get_legend().remove()
    sns.despine(ax=ax)


def plot_group(long: pd.DataFrame, group: str, n_cyclones: int, trim: float, pdf: bool) -> None:
    terms, unit = GROUPS[group]
    terms = [term for term in terms if term in set(long["term"])]
    if not terms:
        print(f"  skipping {group}: no paired terms")
        return
    columns = 2 if len(terms) <= 4 else 3
    rows = int(np.ceil(len(terms) / columns))
    figure, axes = plt.subplots(
        rows, columns, figsize=(5.0 * columns, 3.5 * rows), squeeze=False
    )
    for ax, term in zip(axes.flat, terms):
        panel(ax, long[long["term"] == term], term, unit, trim)
    for ax in axes.flat[len(terms):]:
        ax.set_visible(False)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=PALETTE[v], edgecolor="0.3", linewidth=0.6)
        for v in HUE_ORDER
    ]
    figure.legend(
        handles,
        ["legacy (left half)", "corrected (right half)"],
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=11,
        bbox_to_anchor=(0.5, -0.005),
    )
    figure.suptitle(
        f"{GROUP_TITLES[group]} — legacy vs corrected LEC ({n_cyclones:,} cyclones)",
        fontsize=14,
    )
    figure.tight_layout(rect=(0, 0.035, 1, 0.97))
    stem = FIGURES_DIR / f"violin_{group}"
    figure.savefig(f"{stem}.png", dpi=200, bbox_inches="tight")
    if pdf:
        figure.savefig(f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)
    print(f"  wrote {stem}.png")


def plot_signflip(paired: pd.DataFrame, pdf: bool) -> None:
    """Heatmap of the fraction of cyclone-phases whose term changed sign."""
    valid = paired[(paired["legacy"] != 0) & (paired["corrected"] != 0)].copy()
    valid["flip"] = np.sign(valid["legacy"]) != np.sign(valid["corrected"])
    table = (
        valid.pivot_table(index="term", columns="phase", values="flip", aggfunc="mean")
        .reindex(columns=PHASES)
        .mul(100)
    )
    order = [term for terms, _ in GROUPS.values() for term in terms if term in table.index]
    table = table.reindex(order)

    figure, ax = plt.subplots(figsize=(7.4, 0.32 * len(table) + 1.8))
    sns.heatmap(
        table,
        annot=True,
        fmt=".0f",
        cmap="rocket_r",
        vmin=0,
        vmax=max(50.0, float(np.nanmax(table.to_numpy()))),
        cbar_kws={"label": "sign changes (% of cyclone-phases)"},
        linewidths=0.4,
        linecolor="white",
        annot_kws={"fontsize": 8},
        ax=ax,
    )
    ax.set_yticklabels([label(term) for term in table.index], rotation=0, fontsize=10)
    ax.set_xticklabels([phase.capitalize() for phase in table.columns], fontsize=10)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Sign changes between legacy and corrected LEC", fontsize=12, pad=8)
    figure.tight_layout()
    stem = FIGURES_DIR / "signflip_heatmap"
    figure.savefig(f"{stem}.png", dpi=200, bbox_inches="tight")
    if pdf:
        figure.savefig(f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)
    print(f"  wrote {stem}.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--group", choices=sorted(GROUPS), help="plot a single term family")
    parser.add_argument("--trim", type=float, default=2.5, help="display percentile trim")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()

    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.25, "font.size": 10})
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    paired = load_paired()
    long = to_long(paired)
    n_cyclones = paired["track_id"].nunique()
    groups = [args.group] if args.group else list(GROUPS)
    for group in groups:
        plot_group(long, group, n_cyclones, args.trim, not args.no_pdf)
    plot_signflip(paired, not args.no_pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
