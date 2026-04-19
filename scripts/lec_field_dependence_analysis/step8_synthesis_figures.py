"""
Step 8: Generate Synthesis Figures and Summary Tables

Produces interpretable outputs from the PREDEP results, in two analysis
families separated into dedicated subdirectories:

  all_terms/       — All 24 LEC terms (exploratory; complete analysis)
  canonical/       — Only the 7 terms that entered the PCA-K-Means
                     classification (Ca, Ck, BAe, BKe, Ae, Ke, Ge).
                     This is the primary set for the article.

Figures generated for each family × field type (absolute / anomaly):
  1. Heatmaps: PREDEP (rows = LEC term, columns = field × feature)
     — discrete scale 0.2 steps; values < 0.10 shown in light grey
  2. Top-N associations bar chart (all EPs combined)
  3. Top-N associations bar chart per EP (separate figures)
  4. EP1/EP2/EP3 comparison (mean PREDEP per LEC term)
  5. Absolute vs Anomaly comparison table

Run:
  python scripts/lec_field_dependence_analysis/step8_synthesis_figures.py
  python scripts/lec_field_dependence_analysis/step8_synthesis_figures.py --term-set canonical

Author: Danilo Couto de Souza
Date: April 2026
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib as mpl

from scripts.lec_field_dependence_analysis.utils_io import (
    RESULTS_DIR, FIGURES_DIR, LOG_DIR, LEC_TERMS_CORE, LEC_TERMS_FULL,
    format_display_label,
)
from scripts.utils.ep_mapping import EP_LABELS, EP_COLORS, ALL_EPS, ALL_EPS_WITH_EPALL

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DPI = 300
FIGSIZE_HEATMAP = (16, 9)
FIGSIZE_BAR = (12, 6)
TOP_N = 20  # Top N associations to highlight

# ── Discrete colour scale for PREDEP heatmaps ────────────────────────────
# Values < 0.10 → light grey (negligible)
# Steps of 0.10 from 0.10 to 1.00
PREDEP_THRESHOLDS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.01]
PREDEP_COLORS     = ["#b3b3b3",  # <0.10 → grey
                      "#ffff99",  # 0.10–0.20  light yellow
                      "#ffe64d",  # 0.20–0.30  yellow-light
                      "#ffcc00",  # 0.30–0.40  yellow
                      "#ffb300",  # 0.40–0.50  yellow-orange
                      "#ff9900",  # 0.50–0.60  orange
                      "#ff7300",  # 0.60–0.70  orange-dark
                      "#ff4d00",  # 0.70–0.80  dark orange
                      "#e62600",  # 0.80–0.90  red-orange
                      "#cc0000"]  # >0.90      red

def _make_predep_cmap():
    """Return a ListedColormap with 10 bins: grey for <0.10, then 0.10-step red bins."""
    cmap = mcolors.ListedColormap(PREDEP_COLORS)
    norm = mcolors.BoundaryNorm([0.0] + PREDEP_THRESHOLDS, cmap.N)
    return cmap, norm


def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"lec_field_step8_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def load_predep_results() -> pd.DataFrame:
    """Load and merge all PREDEP result files (absolute + anomaly, chunks + epall)."""
    frames = []
    for ftype in ["absolute", "anomaly"]:
        base = RESULTS_DIR / f"step7_predep_{ftype}.csv"
        if base.exists():
            df = pd.read_csv(base)
            df["field_type"] = ftype
            frames.append(df)
        # Per-EP chunk files (EP1/EP2/EP3, generated on server)
        for chunk_f in sorted(RESULTS_DIR.glob(f"step7_predep_{ftype}_chunk*.csv")):
            df = pd.read_csv(chunk_f)
            df["field_type"] = ftype
            frames.append(df)
        # EPALL file (ep=0, all cyclones pooled — generated locally with --ep 0)
        epall_f = RESULTS_DIR / f"step7_predep_{ftype}_epall.csv"
        if epall_f.exists():
            df = pd.read_csv(epall_f)
            df["field_type"] = ftype
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    # Drop duplicates (from merged + chunk coexistence)
    combined = combined.drop_duplicates(
        subset=["ep", "lec_term", "field", "feature", "field_type"],
        keep="first",
    )
    return combined


def _col_order(df: pd.DataFrame) -> list:
    """
    Consistent column ordering for heatmaps:
    group by field, then sort features alphabetically within each field.
    """
    labels = df["col_label"].unique()
    # Extract field name (before newline)
    return sorted(labels, key=lambda s: (s.split("\n")[0], s.split("\n")[1] if "\n" in s else ""))


def plot_heatmap_field_vs_lec(
    df: pd.DataFrame,
    ep: int,
    field_type: str,
    out_dir: Path,
    term_label: str = "all",
):
    """
    Heatmap: rows = LEC terms, columns = field__feature, values = PREDEP.
    Discrete color scale: grey for <0.10, then 0.20-step bins.
    """
    sub = df[(df["ep"] == ep) & (df["field_type"] == field_type) & df["predep"].notna()].copy()
    if len(sub) == 0:
        return

    sub["col_label"] = sub.apply(
        lambda r: format_display_label(r["field"], r["feature"]), axis=1
    )
    pivot = sub.pivot_table(index="lec_term", columns="col_label", values="predep")

    if pivot.empty:
        return

    # Reorder columns consistently
    ordered_cols = _col_order(sub[["col_label"]].drop_duplicates())
    ordered_cols = [c for c in ordered_cols if c in pivot.columns]
    pivot = pivot[ordered_cols]

    # Build discrete cmap + norm
    cmap, norm = _make_predep_cmap()

    fig, ax = plt.subplots(figsize=FIGSIZE_HEATMAP)
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, norm=norm)

    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=90, fontsize=6)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=8)

    # Colorbar with discrete tick labels
    cbar = plt.colorbar(im, ax=ax, pad=0.02, fraction=0.025)
    cbar.set_label(r"PREDEP $\alpha_{\mathrm{LEC\,|\,feature}}$", fontsize=10)
    tick_vals = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
    cbar.set_ticks(tick_vals)
    cbar.set_ticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"])

    ep_label = EP_LABELS[ep]
    ax.set_title(
        f"PREDEP — {ep_label} | {field_type.capitalize()} Fields "
        f"({'canonical' if term_label == 'canonical' else 'all terms'})",
        fontsize=13, fontweight="bold", pad=12,
    )
    fig.tight_layout()

    fname = f"heatmap_predep_{ep_label.lower().replace(' ', '_')}_{field_type}_{term_label}.png"
    outpath = out_dir / fname
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def plot_top_associations(
    df: pd.DataFrame,
    field_type: str,
    out_dir: Path,
    term_label: str = "all",
):
    """Bar chart of top PREDEP associations across all EPs."""
    sub = df[(df["field_type"] == field_type) & df["predep"].notna()].copy()
    if len(sub) == 0:
        return

    sub["label"] = (
        sub["ep"].map(EP_LABELS) + "  |  "
        + sub["lec_term"] + "  ×  "
        + sub.apply(lambda r: format_display_label(r["field"], r["feature"]), axis=1)
    )
    top = sub.nlargest(TOP_N, "predep")

    fig, ax = plt.subplots(figsize=FIGSIZE_BAR)
    colors = [EP_COLORS.get(row["ep"], "gray") for _, row in top.iterrows()]
    ax.barh(range(len(top)), top["predep"].values, color=colors, edgecolor="black", linewidth=0.4)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["label"].values, fontsize=7.5)
    ax.set_xlabel(r"PREDEP $\alpha_{\mathrm{LEC\,|\,feature}}$", fontsize=11)
    ax.set_title(
        f"Top {TOP_N} PREDEP Associations — {field_type.capitalize()} ({term_label})",
        fontsize=12, fontweight="bold",
    )
    ax.set_xlim(0, 1)
    ax.axvline(0.1, color="gray", linestyle="--", linewidth=0.8, label="0.10 threshold")
    ax.axvline(0.3, color="#fc9272", linestyle="--", linewidth=0.8, label="0.30")
    ax.axvline(0.5, color="#ef3b2c", linestyle="--", linewidth=0.8, label="0.50")
    ax.legend(fontsize=7, loc="lower right")
    ax.invert_yaxis()
    fig.tight_layout()

    fname = f"top_predep_{field_type}_{term_label}.png"
    outpath = out_dir / fname
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def plot_top_associations_per_ep(
    df: pd.DataFrame,
    field_type: str,
    out_dir: Path,
    term_label: str = "all",
):
    """Bar chart of top PREDEP associations for each EP separately (including EPALL)."""
    eps_in_data = sorted(df["ep"].unique())
    for ep in [e for e in ALL_EPS_WITH_EPALL if e in eps_in_data]:
        sub = df[
            (df["field_type"] == field_type) & (df["ep"] == ep) & df["predep"].notna()
        ].copy()
        if len(sub) == 0:
            continue

        sub["label"] = (
            sub["lec_term"] + "  ×  "
            + sub.apply(lambda r: format_display_label(r["field"], r["feature"]), axis=1)
        )
        top = sub.nlargest(TOP_N, "predep")

        fig, ax = plt.subplots(figsize=FIGSIZE_BAR)
        color = EP_COLORS.get(ep, "gray")
        ax.barh(range(len(top)), top["predep"].values, color=color,
                edgecolor="black", linewidth=0.4)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top["label"].values, fontsize=7.5)
        ax.set_xlabel(r"PREDEP $\alpha_{\mathrm{LEC\,|\,feature}}$", fontsize=11)
        ep_label = EP_LABELS[ep]
        ax.set_title(
            f"Top {TOP_N} PREDEP — {ep_label} | {field_type.capitalize()} ({term_label})",
            fontsize=12, fontweight="bold",
        )
        ax.set_xlim(0, 1)
        ax.axvline(0.1, color="gray", linestyle="--", linewidth=0.8, label="0.10 threshold")
        ax.axvline(0.3, color="#fc9272", linestyle="--", linewidth=0.8, label="0.30")
        ax.axvline(0.5, color="#ef3b2c", linestyle="--", linewidth=0.8, label="0.50")
        ax.legend(fontsize=7, loc="lower right")
        ax.invert_yaxis()
        fig.tight_layout()

        fname = f"top_predep_{ep_label.lower().replace(' ', '_')}_{field_type}_{term_label}.png"
        outpath = out_dir / fname
        fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
        plt.close(fig)
        logging.info(f"   Saved: {outpath}")


def plot_ep_comparison(
    df: pd.DataFrame,
    field_type: str,
    out_dir: Path,
    term_label: str = "all",
):
    """For each LEC term, grouped bar chart comparing mean PREDEP across EPs."""
    sub = df[(df["field_type"] == field_type) & df["predep"].notna()]
    if len(sub) == 0:
        return

    summary = sub.groupby(["ep", "lec_term"])["predep"].mean().reset_index()
    pivot = summary.pivot(index="lec_term", columns="ep", values="predep")

    if pivot.empty:
        return

    # Determine which EPs are present (may include ep=0 EPALL)
    eps_in_data = [e for e in ALL_EPS_WITH_EPALL if e in pivot.columns]
    n_eps = len(eps_in_data)
    fig, ax = plt.subplots(figsize=(13, 5))
    x = np.arange(len(pivot))
    width = max(0.15, 0.7 / max(n_eps, 1))
    for i, ep in enumerate(eps_in_data):
        if ep in pivot.columns:
            vals = pivot[ep].fillna(0).values
            ax.bar(x + i * width, vals, width, label=EP_LABELS[ep],
                   color=EP_COLORS[ep], edgecolor="black", linewidth=0.3)

    ax.set_xticks(x + width * (n_eps - 1) / 2)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(r"Mean PREDEP $\alpha_{\mathrm{LEC\,|\,feature}}$", fontsize=10)
    ax.set_ylim(0, 1)
    ax.axhline(0.1, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_title(
        f"EP Comparison — {field_type.capitalize()} ({term_label})",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=9)
    fig.tight_layout()

    fname = f"ep_comparison_{field_type}_{term_label}.png"
    outpath = out_dir / fname
    fig.savefig(outpath, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logging.info(f"   Saved: {outpath}")


def _generate_figures_for_term_set(
    df: pd.DataFrame,
    term_set: str,
    out_dir: Path,
):
    """
    Generate all figures for one term set (all or canonical).
    Filters df by LEC terms belonging to the set.
    """
    if term_set == "canonical":
        df = df[df["lec_term"].isin(LEC_TERMS_CORE)].copy()
        logging.info(f"   Canonical filter applied: {len(LEC_TERMS_CORE)} terms, {len(df)} rows")
    else:
        logging.info(f"   All-terms set: {len(df)} rows")

    if len(df) == 0:
        logging.warning(f"   No data for term set '{term_set}'. Skipping.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    for ftype in df["field_type"].unique():
        logging.info(f"\n  [{term_set} / {ftype}]")
        # Generate heatmap for each EP including EPALL (ep=0)
        eps_in_data = sorted(df["ep"].unique())
        for ep in [e for e in ALL_EPS_WITH_EPALL if e in eps_in_data]:
            plot_heatmap_field_vs_lec(df, ep, ftype, out_dir, term_label=term_set)
        plot_top_associations(df, ftype, out_dir, term_label=term_set)
        plot_top_associations_per_ep(df, ftype, out_dir, term_label=term_set)
        plot_ep_comparison(df, ftype, out_dir, term_label=term_set)


def main():
    parser = argparse.ArgumentParser(
        description="Step 8: Synthesis figures and summary tables for PREDEP results."
    )
    parser.add_argument(
        "--term-set",
        choices=["all", "canonical", "both"],
        default="both",
        help=(
            "Which term set to analyse. "
            "'all' = all 24 LEC terms (exploratory). "
            "'canonical' = 7 clustering terms only (article). "
            "'both' = generate both (default)."
        ),
    )
    args = parser.parse_args()

    setup_logging()
    logging.info("=" * 70)
    logging.info("STEP 8: SYNTHESIS FIGURES — LEC–FIELD DEPENDENCE ANALYSIS")
    logging.info("LEC method : central timesteps (canonical ep_structure rule)")
    logging.info("=" * 70)

    df = load_predep_results()
    if len(df) == 0:
        logging.error(
            "No PREDEP results found. Run step7 first."
        )
        return

    logging.info(f"Loaded {len(df)} PREDEP results")
    logging.info(f"Field types: {df['field_type'].unique().tolist()}")
    logging.info(f"EPs: {sorted(df['ep'].unique().tolist())}")
    logging.info(f"LEC terms: {sorted(df['lec_term'].unique().tolist())}")

    # Subdirectories per term set
    term_sets_to_run = (
        ["all", "canonical"] if args.term_set == "both" else [args.term_set]
    )

    for term_set in term_sets_to_run:
        out_dir = FIGURES_DIR / term_set
        logging.info(f"\n{'='*60}")
        logging.info(f"Term set: {term_set.upper()} → {out_dir}")
        _generate_figures_for_term_set(df, term_set, out_dir)

    # ── Summary tables (global, all terms) ──────────────────────────────
    logging.info("\n--- Summary tables (all terms) ---")

    top_all = df[df["predep"].notna()].nlargest(50, "predep")
    top_all.to_csv(RESULTS_DIR / "step8_top_associations.csv", index=False)
    logging.info("   Saved: step8_top_associations.csv")

    top_canonical = (
        df[df["predep"].notna() & df["lec_term"].isin(LEC_TERMS_CORE)]
        .nlargest(50, "predep")
    )
    top_canonical.to_csv(RESULTS_DIR / "step8_top_associations_canonical.csv", index=False)
    logging.info("   Saved: step8_top_associations_canonical.csv")

    summary = df[df["predep"].notna()].groupby(
        ["ep", "field_type", "lec_term"]
    )["predep"].agg(["mean", "median", "max", "count"]).reset_index()
    summary.to_csv(RESULTS_DIR / "step8_summary_table.csv", index=False)
    logging.info("   Saved: step8_summary_table.csv")

    # Absolute vs Anomaly comparison
    if len(df["field_type"].unique()) > 1:
        abs_mean = (df[df["field_type"] == "absolute"]
                    .groupby(["ep", "lec_term"])["predep"].mean().reset_index()
                    .rename(columns={"predep": "predep_absolute"}))
        anom_mean = (df[df["field_type"] == "anomaly"]
                     .groupby(["ep", "lec_term"])["predep"].mean().reset_index()
                     .rename(columns={"predep": "predep_anomaly"}))
        comparison = abs_mean.merge(anom_mean, on=["ep", "lec_term"], how="outer")
        comparison.to_csv(RESULTS_DIR / "step8_abs_vs_anom_comparison.csv", index=False)
        logging.info("   Saved: step8_abs_vs_anom_comparison.csv")

    logging.info("\n✓ Step 8 complete.")


if __name__ == "__main__":
    main()
