"""
Exploratory Analysis: Ca, Ck, Ge Distributions at Phase Start vs Phase End

The LPS diagrams (main figure 4, cluster analysis) plot phase-averaged values
of the LEC terms — one point per cyclone per phase. This script checks how
representative that average is by comparing the distribution of Ca, Ck and Ge
at the FIRST vs LAST valid 3-hourly timestep of the intensification and
decay phases. If start and end distributions diverge strongly, the phase
mean in the LPS diagrams is smoothing over a real within-phase evolution.

Data sources:
- Track phase labels (1-hourly): scripts.utils.load_data.load_tracks()
  ('period' column, from GitHub tracks_SAt_filtered_with_periods.csv)
- Energy terms (3-hourly, NaN at intermediate hours):
  data/tracks_SAt_filtered_with_energetics_processed.csv
  (local cache of Zenodo DOI 10.5281/zenodo.18133432)

Both sources are merged on (track_id, date). Values are used as-is: this is
the same vertically-integrated, semi-Lagrangian LEC pipeline that feeds
data/energy_cache.parquet (verified to reproduce identical phase means for a
sample cyclone) and scripts/main/04_figure_lps_combined.py. No sign/gravity
correction is applied here — that correction only applies to the separately
vertically-RESOLVED Zenodo archive (temp_lec_zenodo/*_level.csv), not to
these vertically-integrated values.

Population: complete-lifecycle cyclones only (the same set used to build
energy_cache.parquet), restricted per phase to cyclones with >=2 valid
energy timesteps in that phase (so "start" and "end" are genuinely two
different observations, not a single point compared to itself).

Outputs:
    - figures/exploratory/ca_ck_ge_start_vs_end_distributions.png
    - results/exploratory/ca_ck_ge_start_vs_end_stats.csv

Author: Danilo Couto de Souza
Date: August 2026
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from scripts.utils.load_data import load_tracks
from scripts.preprocess_data.preprocess_data import load_cache

# ============================================================================
# CONFIGURATION
# ============================================================================

ENERGETICS_FILE = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"

FIGURES_DIR = PROJECT_ROOT / "figures" / "exploratory"
RESULTS_DIR = PROJECT_ROOT / "results" / "exploratory"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DPI = 200
MIN_VALID_TIMESTEPS = 2  # per cyclone-phase, to have a real start != end pair

TERMS = ["Ca", "Ck", "Ge"]
PHASES = ["intensification", "decay"]

TERM_META = {
    "Ca": dict(label="Ca", desc="baroclinic conversion (Az→Ae)"),
    "Ck": dict(label="Ck", desc="barotropic conversion (Ke→Kz)"),
    "Ge": dict(label="Ge", desc="generation of Ae"),
}

PHASE_LABELS = {
    "intensification": "Intensification phase",
    "mature": "Mature phase",
    "decay": "Decay phase",
}

BOUNDARY_COLORS = {"start": "#1b7837", "end": "#762a83"}  # green / purple, colorblind-safe

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = DPI


# ============================================================================
# DATA ASSEMBLY
# ============================================================================

def load_phase_labeled_energetics() -> pd.DataFrame:
    """Merge 1-hourly phase labels onto the 3-hourly Ca/Ck/Ge series.

    Returns:
        DataFrame with columns [track_id, date, period, Ca, Ck, Ge],
        restricted to complete-lifecycle cyclones and rows with valid
        energy values.
    """
    print("Loading complete-lifecycle cyclone population (energy_cache.parquet)...")
    cache = load_cache()
    complete_ids = set(cache["track_id"].astype(str).unique())
    print(f"  ✓ {len(complete_ids)} complete-lifecycle cyclones")

    print("Loading track phase labels...")
    tracks = load_tracks()
    tracks["date"] = pd.to_datetime(tracks["date"])
    tracks["track_id"] = tracks["track_id"].astype(str)
    tracks["period"] = tracks["period"].astype(str).str.strip().str.lower()

    print(f"Loading energy terms from {ENERGETICS_FILE.name}...")
    energetics = pd.read_csv(ENERGETICS_FILE)
    energetics["date"] = pd.to_datetime(energetics["date"])
    energetics["track_id"] = energetics["track_id"].astype(str)
    energetics = energetics[energetics["track_id"].isin(complete_ids)]

    # Ca/Ck/Ge (and the other energy columns) are populated together every
    # 3 hours and NaN at intermediate hourly steps -- drop the NaN rows.
    energetics = energetics.dropna(subset=TERMS)
    print(f"  ✓ {len(energetics)} valid 3-hourly energy records")

    merged = energetics.merge(
        tracks[["track_id", "date", "period"]], on=["track_id", "date"], how="left"
    )
    n_unmatched = merged["period"].isna().sum()
    if n_unmatched:
        print(f"  ⚠️  {n_unmatched} records had no matching phase label (dropped)")
    merged = merged.dropna(subset=["period"])

    return merged[["track_id", "date", "period"] + TERMS]


def extract_start_end(df: pd.DataFrame, phase: str) -> pd.DataFrame:
    """For a given phase, extract the first and last valid energy record
    per cyclone (chronologically), keeping only cyclones with >= MIN_VALID_TIMESTEPS.

    Uses an exact match on `period` (not a startswith match) so that
    secondary re-intensification/re-maturation episodes (e.g. "mature 2")
    are excluded from the primary phase boundary.

    Returns:
        Long-form DataFrame with columns [track_id, boundary, Ca, Ck, Ge],
        boundary in {"start", "end"}.
    """
    sub = df[df["period"] == phase].sort_values(["track_id", "date"])
    counts = sub.groupby("track_id").size()
    keep_ids = counts[counts >= MIN_VALID_TIMESTEPS].index
    sub = sub[sub["track_id"].isin(keep_ids)]

    first_rows = sub.groupby("track_id", as_index=False).first()
    last_rows = sub.groupby("track_id", as_index=False).last()
    first_rows["boundary"] = "start"
    last_rows["boundary"] = "end"

    out = pd.concat([first_rows, last_rows], ignore_index=True)
    return out[["track_id", "boundary"] + TERMS]


# ============================================================================
# STATISTICS
# ============================================================================

def paired_stats(start_end: pd.DataFrame, term: str) -> dict:
    """Wilcoxon signed-rank test on paired start/end values for one term."""
    wide = start_end.pivot(index="track_id", columns="boundary", values=term)
    wide = wide.dropna()
    start_vals = wide["start"].values
    end_vals = wide["end"].values

    stat, p = stats.wilcoxon(start_vals, end_vals)

    return {
        "term": term,
        "n_pairs": len(wide),
        "start_mean": np.mean(start_vals),
        "start_median": np.median(start_vals),
        "end_mean": np.mean(end_vals),
        "end_median": np.median(end_vals),
        "median_diff_end_minus_start": np.median(end_vals) - np.median(start_vals),
        "wilcoxon_stat": stat,
        "wilcoxon_p": p,
    }


# ============================================================================
# PLOTTING
# ============================================================================

def plot_panel(ax, start_end: pd.DataFrame, term: str, phase_stats: dict):
    """KDE overlay of start vs end distributions for one term/phase."""
    all_vals = start_end[term].dropna()
    xlim = np.percentile(all_vals, [0.5, 99.5])

    for boundary, color in BOUNDARY_COLORS.items():
        vals = start_end.loc[start_end["boundary"] == boundary, term].dropna()
        sns.kdeplot(vals, ax=ax, color=color, fill=True, alpha=0.3, linewidth=1.8,
                    label=boundary, warn_singular=False, clip=xlim)
        ax.axvline(vals.median(), color=color, linestyle="--", linewidth=1.2, alpha=0.8)

    ax.axvline(0, color="black", linewidth=0.7, alpha=0.5)
    ax.set_xlim(xlim)

    p = phase_stats["wilcoxon_p"]
    p_str = "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
    ax.text(
        0.97, 0.95,
        f"n = {phase_stats['n_pairs']}\n{p_str}",
        transform=ax.transAxes, ha="right", va="top", fontsize=8,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.7, edgecolor="lightgray"),
    )

    ax.set_ylabel("Density")
    ax.set_xlabel(f"{term} (W m⁻²)")


def make_figure(all_start_end: dict, all_stats: dict) -> Path:
    fig, axes = plt.subplots(len(PHASES), len(TERMS), figsize=(13, 7.5))

    for row, phase in enumerate(PHASES):
        for col, term in enumerate(TERMS):
            ax = axes[row, col]
            plot_panel(ax, all_start_end[phase], term, all_stats[phase][term])

            if row == 0:
                ax.set_title(f"{TERM_META[term]['label']}\n({TERM_META[term]['desc']})",
                             fontsize=11, fontweight="bold")
            if col == 0:
                ax.annotate(
                    PHASE_LABELS[phase], xy=(-0.32, 0.5), xycoords="axes fraction",
                    fontsize=11, fontweight="bold", rotation=90, va="center", ha="center",
                )

    handles = [
        plt.Line2D([0], [0], color=BOUNDARY_COLORS["start"], lw=3, label="Phase start"),
        plt.Line2D([0], [0], color=BOUNDARY_COLORS["end"], lw=3, label="Phase end"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.02),
               frameon=False, fontsize=10)

    fig.suptitle(
        "Ca, Ck, Ge: distribution at phase start vs phase end\n"
        "(dashed lines = medians; compare against phase-mean LPS diagrams)",
        fontsize=12, y=1.08,
    )

    fig.tight_layout()
    out_path = FIGURES_DIR / "ca_ck_ge_start_vs_end_distributions.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("Ca, Ck, Ge — start vs end of phase distributions")
    print("=" * 70)

    df = load_phase_labeled_energetics()

    all_start_end = {}
    all_stats = {}
    stats_rows = []

    for phase in PHASES:
        print(f"\n--- {phase} ---")
        start_end = extract_start_end(df, phase)
        n_cyclones = start_end["track_id"].nunique()
        print(f"  ✓ {n_cyclones} cyclones with >= {MIN_VALID_TIMESTEPS} valid timesteps")
        all_start_end[phase] = start_end

        phase_stats = {}
        for term in TERMS:
            s = paired_stats(start_end, term)
            phase_stats[term] = s
            stats_rows.append({"phase": phase, **s})
            print(f"  {term}: start median={s['start_median']:.2f}, "
                  f"end median={s['end_median']:.2f}, "
                  f"Δ={s['median_diff_end_minus_start']:+.2f}, "
                  f"Wilcoxon p={s['wilcoxon_p']:.4g}")
        all_stats[phase] = phase_stats

    stats_df = pd.DataFrame(stats_rows)
    stats_path = RESULTS_DIR / "ca_ck_ge_start_vs_end_stats.csv"
    stats_df.to_csv(stats_path, index=False)
    print(f"\n✓ Stats saved to {stats_path}")

    fig_path = make_figure(all_start_end, all_stats)
    print(f"✓ Figure saved to {fig_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
