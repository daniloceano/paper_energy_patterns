"""
Exploratory Analysis: Vertical Distribution of LEC Terms – EP1 vs EP2

Compares the vertical profiles of four energetic terms during intensification:
  - Ca  (baroclinic conversion)
  - Ck  (barotropic conversion)
  - Ae  (eddy available potential energy)
  - Ke  (eddy kinetic energy)

Analysis groups:
  - EP1 only  (cluster 0)
  - EP2 only  (cluster 2)
  - EP1 + EP2 combined

For each group, boxplots by pressure level are shown side-by-side to:
  i)  identify critical pressure levels (max for Ca/Ae/Ke, min for Ck)
  ii) compare whether critical levels differ between EPs

Figure layout: 4 rows (terms) × 3 columns (groups) = 12 panels.
All boxplots share the same x-axis (pressure levels, 1000→100 hPa).

Data corrections applied (Zenodo DOI: 10.5281/zenodo.18243447):
  - Ca: sign inversion    (Ca_corrected = -Ca_raw)
  - Ck: gravity division  (Ck_corrected = Ck_raw / 9.8)
  - Ae, Ke: no correction needed

Output:
  figures/exploratory/vertical_term_boxplots_ep1_ep2.png

Author: Danilo Couto de Souza
Date: February 2026
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from collections import defaultdict

# ── project root on path ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

RESULTS_DIR  = PROJECT_ROOT / "results" / "cluster"
FIGURES_DIR  = PROJECT_ROOT / "figures" / "exploratory"
TEMP_DIR     = PROJECT_ROOT / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Zenodo dataset reference
ZENODO_DOI = "10.5281/zenodo.18243447"

# Physical constant
GRAVITY = 9.8  # m/s²  (for Ck correction)

# Cluster → EP mapping (from scripts/exploratory/analyze_ep_characteristics.py)
CLUSTER_TO_EP = {0: 1, 2: 2}   # cluster 0 → EP1, cluster 2 → EP2

# Terms to analyse
TERMS = ["Ca", "Ck", "Ae", "Ke"]

# Aesthetic settings for each term
TERM_META = {
    "Ca": dict(label="Ca\n(baroclinic conversion)", unit="W m⁻²",
               color="lightcoral", edge="darkred",   marker_color="darkred",
               critical="max"),
    "Ck": dict(label="Ck\n(barotropic conversion)", unit="W m⁻²",
               color="lightblue",  edge="darkblue",  marker_color="darkblue",
               critical="min"),
    "Ae": dict(label="Ae\n(eddy APE)",              unit="J m⁻²",
               color="lightgreen", edge="darkgreen", marker_color="darkgreen",
               critical="max"),
    "Ke": dict(label="Ke\n(eddy KE)",               unit="J m⁻²",
               color="lightyellow", edge="goldenrod", marker_color="goldenrod",
               critical="max"),
}

GROUP_LABELS = {
    "EP1":      "EP1 (cluster 0)",
    "EP2":      "EP2 (cluster 2)",
    "EP1+EP2":  "EP1 + EP2 combined",
}

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 300


# ============================================================================
# HELPERS (shared with step2_vertical_levels_analysis.py)
# ============================================================================

def _resolve_csv(path: Path) -> Path | None:
    """Handle the Zenodo quirk: a *.csv entry can be a directory containing a CSV."""
    if path.is_dir():
        csvs = list(path.glob("*.csv"))
        return csvs[0] if csvs else None
    return path if path.exists() else None


def _load_term(lec_dir: Path, term: str) -> pd.DataFrame | None:
    """
    Load a vertically-resolved LEC term for a single cyclone.

    Applies the validated corrections for Ca and Ck.

    Returns
    -------
    pd.DataFrame or None
        Time-indexed, pressure-level columns (Pa), corrected values.
    """
    fp = _resolve_csv(lec_dir / f"{term}_level.csv")
    if fp is None:
        return None

    df = pd.read_csv(fp, index_col=0, parse_dates=True)

    if term == "Ca":
        df = -df            # CORRECTION 1: sign inversion
    elif term == "Ck":
        df = df / GRAVITY   # CORRECTION 2: gravity normalisation

    return df


def _get_intensification_times(lec_dir: Path):
    """Return (start, end) datetimes for the intensification phase."""
    fp = _resolve_csv(lec_dir / "periods.csv")
    if fp is None:
        return None
    periods = pd.read_csv(fp, index_col=0)
    if "intensification" not in periods.index:
        return None
    row = periods.loc["intensification"]
    return pd.to_datetime(row["start"]), pd.to_datetime(row["end"])


# ============================================================================
# CLUSTER LOADING
# ============================================================================

def get_track_ids_by_ep() -> dict[str, list]:
    """
    Return track_id lists keyed by group: 'EP1', 'EP2', 'EP1+EP2'.

    Reads kmeans_clustered_data.csv and applies CLUSTER_TO_EP mapping.
    """
    cluster_file = RESULTS_DIR / "kmeans_clustered_data.csv"
    if not cluster_file.exists():
        raise FileNotFoundError(f"Cluster file not found: {cluster_file}")

    df = pd.read_csv(cluster_file)

    ep1_ids = df.loc[df["cluster"] == 0, "track_id"].tolist()
    ep2_ids = df.loc[df["cluster"] == 2, "track_id"].tolist()

    return {
        "EP1":     ep1_ids,
        "EP2":     ep2_ids,
        "EP1+EP2": ep1_ids + ep2_ids,
    }


# ============================================================================
# VERTICAL PROFILE COLLECTION
# ============================================================================

def collect_profiles(track_ids: list, group_label: str) -> dict[str, dict[int, list]]:
    """
    Collect mean intensification-phase profiles of all four terms
    for the given cyclone list.

    Returns
    -------
    dict  term → {pressure_hPa: [values]}
    """
    by_level: dict[str, dict[int, list]] = {t: defaultdict(list) for t in TERMS}
    missing = 0

    for track_id in tqdm(track_ids, desc=f"  {group_label}", leave=False):
        lec_dir = TEMP_DIR / f"{track_id}_ERA5_track"
        if not lec_dir.exists():
            missing += 1
            continue

        times = _get_intensification_times(lec_dir)
        if times is None:
            missing += 1
            continue
        t0, t1 = times

        for term in TERMS:
            df = _load_term(lec_dir, term)
            if df is None:
                continue

            # Filter to intensification window
            sub = df.loc[(df.index >= t0) & (df.index <= t1)]
            if len(sub) == 0:
                continue

            # Mean over time
            mean_profile = sub.mean(axis=0)

            # Pa → hPa; keep ≥ 100 hPa
            p_hpa = mean_profile.index.astype(float) / 100.0
            valid = p_hpa >= 100.0
            p_hpa = p_hpa[valid]
            vals = mean_profile.values[valid]

            for p, v in zip(p_hpa, vals):
                by_level[term][int(p)].append(v)

    if missing:
        tqdm.write(f"    ({group_label}) missing/incomplete: {missing} cyclones")

    return by_level


# ============================================================================
# FIGURE
# ============================================================================

def plot_all(data: dict[str, dict[str, dict[int, list]]]):
    """
    Create the 4×3 summary figure.

    Parameters
    ----------
    data : dict
        data[group][term][pressure_hPa] = [values]
    """
    groups = ["EP1", "EP2", "EP1+EP2"]
    n_terms = len(TERMS)
    n_groups = len(groups)

    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 7, "ytick.labelsize": 8,
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    })

    fig, axes = plt.subplots(
        n_terms, n_groups,
        figsize=(5 * n_groups, 4.5 * n_terms),
        sharex="col", sharey="row",
    )

    # Collect all unique pressure levels across groups/terms for x-axis
    all_levels: set[int] = set()
    for g in groups:
        for t in TERMS:
            all_levels.update(data[g][t].keys())
    pressure_levels = sorted(all_levels, reverse=True)   # 1000 → 100 hPa
    positions = np.arange(len(pressure_levels))
    level_to_pos = {p: i for i, p in enumerate(pressure_levels)}

    for row_idx, term in enumerate(TERMS):
        meta = TERM_META[term]
        for col_idx, group in enumerate(groups):
            ax = axes[row_idx, col_idx]
            by_level = data[group][term]

            # Build ordered lists respecting pressure_levels
            plot_data = [by_level.get(p, []) for p in pressure_levels]
            plot_pos  = [level_to_pos[p] for p in pressure_levels
                         if by_level.get(p)]
            plot_vals = [by_level[p] for p in pressure_levels if by_level.get(p)]

            if not plot_vals:
                ax.set_visible(False)
                continue

            # Boxplot
            bp = ax.boxplot(
                plot_vals,
                positions=plot_pos,
                widths=0.55,
                patch_artist=True,
                showfliers=False,
                medianprops=dict(color=meta["edge"], linewidth=1.8),
                boxprops=dict(facecolor=meta["color"], edgecolor=meta["edge"], alpha=0.75),
                whiskerprops=dict(color=meta["edge"], linewidth=1.2),
                capprops=dict(color=meta["edge"], linewidth=1.2),
            )

            ax.axhline(0, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

            # Find & mark critical level
            medians = [np.median(by_level[p]) for p in pressure_levels if by_level.get(p)]
            valid_levels = [p for p in pressure_levels if by_level.get(p)]
            if meta["critical"] == "max":
                crit_idx = int(np.argmax(medians))
                crit_marker = "★"
                marker_loc = "top"
            else:
                crit_idx = int(np.argmin(medians))
                crit_marker = "★"
                marker_loc = "bottom"

            crit_level = valid_levels[crit_idx]
            crit_val   = medians[crit_idx]
            crit_pos   = level_to_pos[crit_level]
            ax.plot(crit_pos, crit_val, "*",
                    color=meta["marker_color"], markersize=12,
                    markeredgecolor="white", markeredgewidth=0.5,
                    zorder=5,
                    label=f"Critical: {crit_level} hPa")
            ax.legend(loc="best", fontsize=7, frameon=True,
                      fancybox=False, edgecolor="gray")

            # Axes decoration
            ax.set_xticks(positions)
            ax.set_xticklabels(
                [str(int(p)) for p in pressure_levels], rotation=60, ha="right"
            )
            ax.set_xlim(positions[0] - 0.7, positions[-1] + 0.7)
            ax.grid(True, alpha=0.25, linestyle=":", linewidth=0.4)

            n_sys = len({p: True for p in pressure_levels if by_level.get(p)
                         and len(by_level[p]) > 0})
            n_cases = len(by_level.get(valid_levels[0], []))
            ax.text(0.98, 0.98, f"n = {n_cases}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

            # Row label (left column only)
            if col_idx == 0:
                ax.set_ylabel(f"{meta['label']}\n({meta['unit']})", fontsize=8)

            # Column title (top row only)
            if row_idx == 0:
                n_total = len(data[group]["Ca"].get(
                    sorted(data[group]["Ca"].keys())[0], []))
                ax.set_title(
                    f"{GROUP_LABELS[group]}\n(n = {n_total} cyclones)",
                    fontsize=9, fontweight="bold", pad=6
                )

            # Bottom row: x label
            if row_idx == n_terms - 1:
                ax.set_xlabel("Pressure level (hPa)", fontsize=8)

    # Overall figure title
    fig.suptitle(
        "Vertical distribution of LEC terms during intensification\n"
        "EP1 vs EP2 (Zenodo dataset, DOI: 10.5281/zenodo.18243447)",
        fontsize=11, fontweight="bold", y=1.005
    )

    plt.tight_layout()
    out = FIGURES_DIR / "vertical_term_boxplots_ep1_ep2.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"\n✓ Figure saved: {out}")
    plt.close()
    return out


# ============================================================================
# SUMMARY TABLE
# ============================================================================

def print_critical_levels_summary(data: dict[str, dict[str, dict[int, list]]]):
    """Print a compact table of critical pressure levels per group × term."""
    print("\n" + "=" * 65)
    print("CRITICAL PRESSURE LEVELS SUMMARY")
    print("=" * 65)
    header = f"{'Term':<6}  {'Critical':<5}  " + \
             "  ".join(f"{g:<14}" for g in ["EP1", "EP2", "EP1+EP2"])
    print(header)
    print("-" * 65)

    for term in TERMS:
        meta = TERM_META[term]
        row = f"{term:<6}  {meta['critical']:<5}  "
        for group in ["EP1", "EP2", "EP1+EP2"]:
            by_level = data[group][term]
            if not by_level:
                row += f"{'N/A':<16}"
                continue
            levels = sorted(by_level.keys(), reverse=True)
            medians = [np.median(by_level[p]) for p in levels]
            if meta["critical"] == "max":
                idx = int(np.argmax(medians))
            else:
                idx = int(np.argmin(medians))
            crit_p = levels[idx]
            crit_v = medians[idx]
            row += f"{crit_p:>4} hPa ({crit_v:+.3f})  "
        print(row)

    print("=" * 65 + "\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Vertical LEC term boxplots: EP1 vs EP2 comparison"
    )
    parser.add_argument(
        "--no-corrections", action="store_true",
        help="Disable Ca/Ck data corrections (use raw values)",
    )
    args = parser.parse_args()

    if args.no_corrections:
        print("⚠️  Running WITHOUT Ca/Ck corrections (raw values)")

    print("=" * 65)
    print("VERTICAL TERM BOXPLOTS – EP1 vs EP2")
    print(f"Data: Zenodo (DOI: {ZENODO_DOI})")
    print("=" * 65)

    # ── 1. Get cyclone lists by group ─────────────────────────────────────
    print("\n[1/3] Loading cluster assignments...")
    groups = get_track_ids_by_ep()
    for g, ids in groups.items():
        if g != "EP1+EP2":
            print(f"  {g}: {len(ids)} cyclones")

    # ── 2. Collect vertical profiles ──────────────────────────────────────
    print("\n[2/3] Collecting vertical profiles (intensification phase only)...")
    data: dict[str, dict[str, dict[int, list]]] = {}

    for group_name, track_ids in groups.items():
        print(f"\n  Processing {group_name} ({len(track_ids)} cyclones):")
        data[group_name] = collect_profiles(track_ids, group_name)

    # ── 3. Plot ────────────────────────────────────────────────────────────
    print("\n[3/3] Generating figure...")
    plot_all(data)

    # ── Summary table ──────────────────────────────────────────────────────
    print_critical_levels_summary(data)


if __name__ == "__main__":
    main()
