"""
Exploratory Analysis: Mean Vorticity Change Rate by Energy Pattern

Computes the mean rate of vorticity change during the intensification phase
for each Energy Pattern (EP1, EP2, EP3), using EXACTLY the same central
timesteps adopted in the canonical composites (step1_select_ep_tracks.py).

=============================================================================
DATA SOURCE
=============================================================================
- EP case lists: results/ep_structure/ep{1,2,3}_cases.csv
  (already contain pre-computed `selected_times` for each cyclone)

- Cyclone tracks: data/tracks_SAt_filtered_with_energetics_processed.csv
  (local file; variable `vor42` = relative vorticity at 850 hPa, positive
   for cyclonic systems in the Southern Hemisphere, units: × 10⁻⁵ s⁻¹)

Alternative online source (used if local file unavailable):
  load_tracks() from scripts.utils.load_data (fetches from GitHub)

=============================================================================
METRIC DEFINITION
=============================================================================
For each cyclone, the vorticity change rate is calculated as:

    rate = (vor42_last − vor42_first) / Δt

where:
  - vor42_first : vorticity at the first selected central timestep
  - vor42_last  : vorticity at the last selected central timestep
  - Δt          : time difference between last and first selected timestep,
                  in hours

For 2 selected timesteps (N_total even): Δt = 1 hour
For 3 selected timesteps (N_total odd) : Δt = 2 hours

=============================================================================
SIGN CONVENTION
=============================================================================
`vor42` is stored as positive values for cyclonic (cyclone-tracking) systems
in the Southern Hemisphere (values in × 10⁻⁵ s⁻¹).

Therefore:
  POSITIVE rate → vorticity increasing → INTENSIFICATION (deepening cyclone)
  NEGATIVE rate → vorticity decreasing → WEAKENING (filling cyclone)

Since the selected timesteps are central to the intensification phase, most
values are expected to be positive (cyclone still deepening at the midpoint
of intensification). However, some scatter near zero or negative values are
possible, especially for short-lived or weakly intensifying systems, or for
cases where the central timesteps straddle the vorticity peak.

=============================================================================
TEMPORAL WINDOW
=============================================================================
CANONICAL RULE (April 2026, same as composites):
  - ODD total timesteps  → 3 central timesteps selected
  - EVEN total timesteps → 2 central timesteps selected
  - Minimum duration filter: ≥ 24 hours intensification

These are the same `selected_times` stored in the ep_cases.csv files.

=============================================================================
OUTPUTS
=============================================================================
  figures/exploratory/vorticity_change_rate_by_ep_boxplot.png
  results/exploratory/vorticity_change_rate_by_ep.csv   (optional)

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from scipy import stats

from scripts.utils.ep_mapping import ALL_EPS, EP_LABELS, EP_COLORS, get_ep_label, get_ep_color

# =============================================================================
# Configuration
# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_EP_DIR    = PROJECT_ROOT / "results" / "ep_structure"
TRACKS_FILE       = PROJECT_ROOT / "data" / "tracks_SAt_filtered_with_energetics_processed.csv"
FIGURES_DIR       = PROJECT_ROOT / "figures" / "exploratory"
RESULTS_EXP_DIR   = PROJECT_ROOT / "results" / "exploratory"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_EXP_DIR.mkdir(parents=True, exist_ok=True)

DPI = 150  # Exploratory quality (not paper-quality)

# Vorticity column in the tracks file
VOR_COL = "vor42"


# =============================================================================
# Data Loading
# =============================================================================

def load_ep_cases():
    """
    Load canonical case files for EP1, EP2, EP3.
    Returns dict {ep_num: DataFrame}.
    """
    ep_data = {}
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        case_file = RESULTS_EP_DIR / f"{ep_label.lower()}_cases.csv"
        if not case_file.exists():
            print(f"  ⚠  {case_file.name} not found, skipping EP{ep_num}")
            continue
        df = pd.read_csv(case_file)
        ep_data[ep_num] = df
        print(f"  ✓  {ep_label}: {len(df)} cases loaded from {case_file.name}")
    return ep_data


def load_tracks_subset(track_ids: set) -> pd.DataFrame:
    """
    Load the tracks CSV, keeping only rows for the requested track_ids.
    Reads in chunks to handle the large file efficiently.

    Returns DataFrame with columns: track_id, date (datetime64), vor42.
    """
    print(f"\n  Loading tracks for {len(track_ids)} cyclones from:")
    print(f"    {TRACKS_FILE}")

    needed_cols = ["track_id", "date", VOR_COL]

    # Try to detect actual column names (the header might differ slightly)
    header = pd.read_csv(TRACKS_FILE, nrows=0).columns.tolist()
    vor_col_actual = VOR_COL  # default
    date_col_actual = "date"  # default

    # Flexible matching for vorticity column
    vor_candidates = [c for c in header if "vor42" in c.lower() or c.lower() == "vor42"]
    if vor_candidates:
        vor_col_actual = vor_candidates[0]
    else:
        # Broader search for any vorticity-like column
        vor_candidates = [c for c in header if "vor" in c.lower() and "850" in c.lower()]
        if vor_candidates:
            vor_col_actual = vor_candidates[0]
        else:
            raise ValueError(
                f"Cannot find vorticity column in tracks. Headers: {header[:20]}"
            )

    date_candidates = [c for c in header if c.lower() in ("date", "time", "datetime")]
    if date_candidates:
        date_col_actual = date_candidates[0]

    track_col_candidates = [c for c in header if "track" in c.lower()]
    track_col_actual = track_col_candidates[0] if track_col_candidates else header[0]

    print(f"    Using columns: track='{track_col_actual}', date='{date_col_actual}', vorticity='{vor_col_actual}'")

    # Read in chunks and filter to relevant track_ids
    chunksize = 100_000
    chunks = []
    for chunk in pd.read_csv(
        TRACKS_FILE,
        usecols=[track_col_actual, date_col_actual, vor_col_actual],
        chunksize=chunksize,
        dtype={track_col_actual: str, vor_col_actual: float},
    ):
        filtered = chunk[chunk[track_col_actual].isin(track_ids)]
        if not filtered.empty:
            chunks.append(filtered)

    if not chunks:
        raise ValueError("No tracks found for the requested track_ids. Check track_id format.")

    tracks = pd.concat(chunks, ignore_index=True)
    tracks.rename(
        columns={track_col_actual: "track_id", date_col_actual: "date", vor_col_actual: VOR_COL},
        inplace=True,
    )
    tracks["date"] = pd.to_datetime(tracks["date"])
    tracks = tracks.sort_values(["track_id", "date"]).reset_index(drop=True)
    print(f"  ✓  {len(tracks)} track records loaded, {tracks['track_id'].nunique()} unique cyclones")
    return tracks


# =============================================================================
# Metric computation
# =============================================================================

def parse_selected_times(selected_str: str) -> list[pd.Timestamp]:
    """Parse comma-separated timestamp string from ep_cases.csv."""
    return [pd.Timestamp(t.strip()) for t in selected_str.split(",")]


def compute_rate_for_case(row, tracks_by_id: dict) -> float | None:
    """
    Compute vorticity change rate (× 10⁻⁵ s⁻¹ h⁻¹) for one cyclone.

    Rate = (vor_last - vor_first) / Δt_hours

    Returns None if vorticity data is missing for the selected timesteps.
    """
    track_id = str(row["track_id"])
    selected_times = parse_selected_times(row["selected_times"])

    if len(selected_times) < 2:
        return None  # Cannot compute a rate with a single point

    t_first = selected_times[0]
    t_last  = selected_times[-1]

    if track_id not in tracks_by_id:
        return None

    track_df = tracks_by_id[track_id]

    # Match timestamps (allow up to 30-minute tolerance for floating-point edges)
    def get_vor(ts: pd.Timestamp):
        dt = (track_df["date"] - ts).abs()
        closest_idx = dt.idxmin()
        if dt[closest_idx] > pd.Timedelta(minutes=30):
            return np.nan
        return track_df.loc[closest_idx, VOR_COL]

    vor_first = get_vor(t_first)
    vor_last  = get_vor(t_last)

    if np.isnan(vor_first) or np.isnan(vor_last):
        return None

    dt_hours = (t_last - t_first).total_seconds() / 3600.0
    if dt_hours < 0.5:
        return None  # Guard: degenerate case (should not happen)

    return (vor_last - vor_first) / dt_hours


# =============================================================================
# Main pipeline
# =============================================================================

def main():
    print("=" * 70)
    print("Exploratory Analysis: Vorticity Change Rate by Energy Pattern")
    print("=" * 70)

    # --- 1. Load EP case files ---
    print("\n[1] Loading EP case files...")
    ep_data = load_ep_cases()
    if not ep_data:
        raise RuntimeError("No EP case files found. Run step1_select_ep_tracks.py first.")

    # --- 2. Collect all track_ids ---
    all_track_ids = set()
    for df in ep_data.values():
        all_track_ids.update(df["track_id"].astype(str).tolist())
    print(f"\n  Total unique track_ids to load: {len(all_track_ids)}")

    # --- 3. Load vorticity data ---
    tracks_df = load_tracks_subset(all_track_ids)
    tracks_by_id = {tid: grp.reset_index() for tid, grp in tracks_df.groupby("track_id")}

    # --- 4. Compute rate for each cyclone ---
    print("\n[2] Computing vorticity change rates...")
    results = []

    for ep_num, df in ep_data.items():
        ep_label = get_ep_label(ep_num)  # e.g., "EP1"
        n_total = len(df)
        n_ok = 0
        n_missing = 0

        for _, row in df.iterrows():
            rate = compute_rate_for_case(row, tracks_by_id)
            if rate is not None:
                results.append({"ep": ep_num, "ep_label": ep_label, "track_id": row["track_id"], "rate": rate})
                n_ok += 1
            else:
                n_missing += 1

        print(f"  {ep_label}: {n_ok}/{n_total} rates computed ({n_missing} missing vorticity data)")

    if not results:
        raise RuntimeError("No rates computed. Check vorticity data availability.")

    results_df = pd.DataFrame(results)

    # --- 5. Summary statistics ---
    print("\n[3] Summary statistics (× 10⁻⁵ s⁻¹ h⁻¹):")
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        subset = results_df[results_df["ep"] == ep_num]["rate"]
        if subset.empty:
            continue
        print(
            f"  {ep_label}: n={len(subset):4d}  "
            f"median={subset.median():+7.4f}  "
            f"mean={subset.mean():+7.4f}  "
            f"std={subset.std():.4f}"
        )

    # --- 6. Save CSV ---
    out_csv = RESULTS_EXP_DIR / "vorticity_change_rate_by_ep.csv"
    results_df.to_csv(out_csv, index=False)
    print(f"\n  ✓  CSV saved: {out_csv}")

    # --- 7. Generate box plot ---
    print("\n[4] Generating figure...")
    _plot_boxplot(results_df)


def _plot_boxplot(results_df: pd.DataFrame):
    """Create and save box plot of vorticity change rates by EP."""
    fig, ax = plt.subplots(figsize=(8, 6))

    ep_rates = []
    ep_labels_ordered = []
    ep_colors_ordered = []
    n_by_ep = {}

    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        color    = get_ep_color(ep_num)
        subset   = results_df[results_df["ep"] == ep_num]["rate"].dropna()
        ep_rates.append(subset.values)
        ep_labels_ordered.append(ep_label)
        ep_colors_ordered.append(color)
        n_by_ep[ep_label] = len(subset)

    # --- Box plot ---
    bp = ax.boxplot(
        ep_rates,
        notch=False,
        vert=True,
        patch_artist=True,
        widths=0.5,
        medianprops=dict(color="black", linewidth=2.5),
        whiskerprops=dict(linewidth=1.5),
        capprops=dict(linewidth=1.5),
        flierprops=dict(marker=".", markersize=3, alpha=0.4, markeredgewidth=0),
    )

    for patch, color in zip(bp["boxes"], ep_colors_ordered):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # --- Strip plot (jittered individual points) ---
    for i, (rates, color) in enumerate(zip(ep_rates, ep_colors_ordered), start=1):
        jitter = np.random.default_rng(seed=42).uniform(-0.18, 0.18, size=len(rates))
        ax.scatter(
            i + jitter,
            rates,
            color=color,
            alpha=0.15,
            s=8,
            edgecolors="none",
            zorder=2,
        )

    # --- Zero reference line ---
    ax.axhline(0, color="gray", linewidth=1, linestyle="--", alpha=0.7, label="Zero rate (no change)")

    # --- Annotations: n counts (below the top whisker for each EP) ---
    for i, (ep_label, rates, color) in enumerate(zip(ep_labels_ordered, ep_rates, ep_colors_ordered), start=1):
        p97 = np.percentile(rates, 99.5)
        ax.text(
            i,
            p97 + 0.02,
            f"n = {n_by_ep[ep_label]}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="dimgray",
        )

    # --- Labels, title ---
    ax.set_xticks(range(1, len(ALL_EPS) + 1))
    ax.set_xticklabels(ep_labels_ordered, fontsize=13)
    ax.set_ylabel(
        "Vorticity change rate  (× 10⁻⁵ s⁻¹ h⁻¹)",
        fontsize=11,
    )
    ax.set_title(
        "Mean Vorticity Change Rate by Energy Pattern\n"
        "(central timesteps of intensification phase)",
        fontsize=12,
        fontweight="bold",
    )

    # --- Kruskal-Wallis test ---
    groups = [results_df[results_df["ep"] == ep_num]["rate"].dropna().values for ep_num in ALL_EPS]
    if all(len(g) >= 3 for g in groups):
        stat, pval = stats.kruskal(*groups)
        significance = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns"))
        ax.text(
            0.98, 0.02,
            f"Kruskal-Wallis: H = {stat:.1f}, p = {pval:.2e} ({significance})",
            transform=ax.transAxes,
            ha="right", va="bottom",
            fontsize=8.5,
            color="dimgray",
        )

    # --- Method note ---
    ax.text(
        0.01, 0.02,
        (
            "Metric: (vor₄₂_last − vor₄₂_first) / Δt\n"
            "Positive = intensifying  |  Negative = weakening\n"
            "Window: 2−3 central timesteps (canonical Apr 2026)"
        ),
        transform=ax.transAxes,
        ha="left", va="bottom",
        fontsize=7.5,
        color="dimgray",
        style="italic",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7, edgecolor="lightgray"),
    )

    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    out_path = FIGURES_DIR / "vorticity_change_rate_by_ep_boxplot.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓  Figure saved: {out_path}")


if __name__ == "__main__":
    main()
