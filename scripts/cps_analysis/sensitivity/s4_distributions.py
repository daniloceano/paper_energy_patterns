"""
Step 5: Distributions of cyclone thermal type by Energy Pattern.

Exploratory characterisation of the classified population: how the thermal
types distribute in season, year, genesis location, intensity, lifetime and
structural persistence, and how those distributions differ between EP1, EP2
and EP3.

Which labelling is used
-----------------------
The headline rule here is `type_persistent` (>= 36 consecutive hours), because
it is the most permissive rule that still requires a SUSTAINED structure and it
retains enough cyclones per cell for distributional statistics. The `tropical`
class is reported but must be read as "deep symmetric warm core" — step 4
establishes that under this rule it is dominated by warm seclusions. The strict
rule (`type_strict`), which removes that contamination, leaves too few tropical
cyclones for distributional work and is used only for counts.

Seasons follow the Southern Hemisphere convention used elsewhere in the project:
DJF summer, MAM autumn, JJA winter, SON spring.

Inputs:
    results/cps_analysis/cps_timesteps_classified.csv   (step 2)
    results/cps_analysis/cyclone_types.csv              (step 2)

Outputs:
    results/cps_analysis/distribution_seasonal.csv
    results/cps_analysis/distribution_annual.csv
    results/cps_analysis/distribution_properties.csv
    results/cps_analysis/distribution_statistics.txt
    figures/cps_analysis/dist_seasonal_annual.png
    figures/cps_analysis/dist_properties.png
    figures/cps_analysis/dist_genesis_map.png
    figures/cps_analysis/dist_persistence.png

Run:
    python scripts/cps_analysis/sensitivity/s4_distributions.py

Author: Danilo Couto de Souza
Date: August 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label
from scripts.cps_analysis.cps_criteria import (
    CLASS_PRECEDENCE,
    UNCLASSIFIED,
    MIN_PERSISTENCE_HOURS,
    TYPE_COLORS,
    DEFAULT_CRITERION,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis" / "sensitivity"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis" / "sensitivity"

TS_FILE = RESULTS_DIR / "cps_timesteps_classified.csv"
CY_FILE = RESULTS_DIR / "cyclone_types.csv"

RULE = "type_persistent"
TYPE_ORDER = CLASS_PRECEDENCE + [UNCLASSIFIED]

SEASONS = ["DJF", "MAM", "JJA", "SON"]
SEASON_OF_MONTH = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
                   6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def build_cyclone_table() -> pd.DataFrame:
    """One row per cyclone: type label, EP, and life-cycle properties."""
    ts = pd.read_csv(
        TS_FILE,
        usecols=["track_id", "datetime", "lat", "lon", "vor42", "SIZE", "region"],
        parse_dates=["datetime"],
    )
    g = ts.groupby("track_id")
    props = pd.DataFrame({
        "genesis_time": g["datetime"].min(),
        "lifetime_h": (g["datetime"].max() - g["datetime"].min()).dt.total_seconds() / 3600,
        "max_vor42": g["vor42"].max(),
        "max_size_km": g["SIZE"].max(),
        "min_lat": g["lat"].min(),
        "max_lat": g["lat"].max(),
    })

    cy = pd.read_csv(CY_FILE).set_index("track_id")
    df = cy.join(props)
    df["month"] = df["genesis_time"].dt.month
    df["season"] = df["month"].map(SEASON_OF_MONTH)
    df["year"] = df["genesis_time"].dt.year
    df["type"] = df[f"{DEFAULT_CRITERION}_{RULE}"]
    df["hybrid_hours"] = df[f"{DEFAULT_CRITERION}_hours_subtropical"]
    df["warm_hours"] = df[f"{DEFAULT_CRITERION}_hours_tropical"]
    return df.reset_index()


def kruskal_report(df: pd.DataFrame, value: str, group: str, label: str) -> list:
    """Kruskal-Wallis across groups, with pairwise Mann-Whitney if significant.

    Non-parametric throughout: none of these distributions (lifetime, vorticity,
    persistence hours) is normal, and the group sizes are very unequal.
    """
    groups = [g[value].dropna().values for _, g in df.groupby(group) if len(g) >= 8]
    names = [str(k) for k, g in df.groupby(group) if len(g) >= 8]
    if len(groups) < 2:
        return [f"    {label}: too few populated groups"]

    stat, p = kruskal(*groups)
    lines = [f"    {label}: Kruskal-Wallis H = {stat:.1f}, p = {p:.2e}"]
    for name, vals in zip(names, groups):
        lines.append(f"      {name:<16s} n = {len(vals):5,d}  median = {np.median(vals):8.1f}")

    if p < 0.05 and len(groups) > 1:
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                u, pu = mannwhitneyu(groups[i], groups[j], alternative="two-sided")
                # rank-biserial correlation as effect size
                r = 1 - 2 * u / (len(groups[i]) * len(groups[j]))
                flag = "*" if pu < 0.05 else " "
                lines.append(f"      {names[i]} vs {names[j]}: p = {pu:.2e} "
                             f"rank-biserial r = {r:+.3f} {flag}")
    return lines


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 4: Distributions by thermal type and Energy Pattern")
    print("=" * 70)

    for f in (TS_FILE, CY_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    df = build_cyclone_table()
    ep = df[df["ep"].notna()].copy()
    ep["ep"] = ep["ep"].astype(int)
    ep["ep_label"] = ep["ep"].map(get_ep_label)

    print(f"\nPopulation: {len(df):,} cyclones ({len(ep):,} with an EP label)")
    print(f"Labelling : {DEFAULT_CRITERION} / {RULE} "
          f"(>= {MIN_PERSISTENCE_HOURS:.0f} consecutive hours)")

    report = []

    # ------------------------------------------------------------------
    # 1. Seasonal
    # ------------------------------------------------------------------
    head = "\n\n1. SEASONAL DISTRIBUTION (% of each EP x type group by season of genesis)"
    print(head)
    report.append(head)

    seasonal = (ep.groupby(["ep_label", "type", "season"]).size()
                .rename("n").reset_index())
    seasonal["pct_within_group"] = seasonal.groupby(["ep_label", "type"])["n"].transform(
        lambda s: 100 * s / s.sum())
    seasonal.to_csv(RESULTS_DIR / "distribution_seasonal.csv", index=False)

    for cls in ["subtropical", "tropical"]:
        sub = seasonal[seasonal["type"] == cls]
        if sub.empty:
            continue
        piv = sub.pivot_table(index="ep_label", columns="season",
                              values="pct_within_group", fill_value=0)
        piv = piv.reindex(columns=SEASONS, fill_value=0)
        line = f"\n  {cls}:\n" + piv.round(1).to_string()
        print(line)
        report.append(line)

    # Whole-population seasonality of the subtropical class, for comparison
    # against Gozzo et al. (2014), who report an austral-summer maximum.
    sub_all = df[df["type"] == "subtropical"]["season"].value_counts(normalize=True) * 100
    line = ("\n  subtropical, whole population (%): "
            + "  ".join(f"{s}={sub_all.get(s, 0):.1f}" for s in SEASONS))
    print(line)
    report.append(line)

    # ------------------------------------------------------------------
    # 2. Interannual
    # ------------------------------------------------------------------
    head = "\n\n2. INTERANNUAL COUNTS"
    print(head)
    report.append(head)

    annual = (df.groupby(["year", "type"]).size().rename("n").reset_index())
    annual.to_csv(RESULTS_DIR / "distribution_annual.csv", index=False)
    piv = annual.pivot_table(index="year", columns="type", values="n", fill_value=0)
    for cls in TYPE_ORDER:
        if cls in piv.columns:
            v = piv[cls]
            line = (f"  {cls:<14s} mean {v.mean():6.1f}/yr  sd {v.std():5.1f}  "
                    f"range {v.min():.0f}-{v.max():.0f}")
            print(line)
            report.append(line)

    # ------------------------------------------------------------------
    # 3. Properties by type, and by EP within type
    # ------------------------------------------------------------------
    head = "\n\n3. LIFE-CYCLE PROPERTIES"
    print(head)
    report.append(head)

    metrics = [("lifetime_h", "lifetime [h]"),
               ("max_vor42", "max |vorticity| [1e-5 /s]"),
               ("max_size_km", "max gale radius [km]"),
               ("hybrid_hours", "longest hybrid spell [h]")]

    for col, label in metrics:
        line = f"\n  {label} — across thermal types:"
        print(line)
        report.append(line)
        lines = kruskal_report(ep, col, "type", "by type")
        print("\n".join(lines))
        report.extend(lines)

        line = f"\n  {label} — across EPs:"
        print(line)
        report.append(line)
        lines = kruskal_report(ep, col, "ep_label", "by EP")
        print("\n".join(lines))
        report.extend(lines)

    props = (ep.groupby(["ep_label", "type"])
             .agg(n=("track_id", "size"),
                  lifetime_median=("lifetime_h", "median"),
                  vor_median=("max_vor42", "median"),
                  size_median=("max_size_km", "median"),
                  hybrid_hours_median=("hybrid_hours", "median"))
             .round(1).reset_index())
    props.to_csv(RESULTS_DIR / "distribution_properties.csv", index=False)
    line = "\n  Medians by EP x type:\n" + props.to_string(index=False)
    print(line)
    report.append(line)

    with open(RESULTS_DIR / "distribution_statistics.txt", "w") as fh:
        fh.write("Distributions by thermal type and Energy Pattern\n")
        fh.write(f"Labelling: {DEFAULT_CRITERION} / {RULE}\n")
        fh.write("\n".join(report) + "\n")
    print(f"\nWrote {(RESULTS_DIR / 'distribution_statistics.txt').relative_to(PROJECT_ROOT)}")

    # ==================================================================
    # FIGURES
    # ==================================================================
    print("\nGenerating figures ...")

    # --- Seasonal + annual ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    ax = axes[0]
    x = np.arange(12)
    for cls in CLASS_PRECEDENCE:
        sub = df[df["type"] == cls]
        if sub.empty:
            continue
        counts = sub["month"].value_counts(normalize=True).reindex(range(1, 13), fill_value=0) * 100
        ax.plot(x, counts.values, "-o", ms=4, lw=2, color=TYPE_COLORS[cls], label=cls)
    ax.set_xticks(x)
    ax.set_xticklabels(MONTHS)
    ax.set_ylabel("% of the class")
    ax.set_xlabel("month of genesis")
    ax.set_title("Annual cycle by thermal type")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    width = 0.25
    xs = np.arange(len(SEASONS))
    for k, e in enumerate(ALL_EPS):
        sub = ep[(ep["ep"] == e) & (ep["type"] == "subtropical")]
        if sub.empty:
            continue
        pct = sub["season"].value_counts(normalize=True).reindex(SEASONS, fill_value=0) * 100
        # Sample size in the legend: EP1 has only a few dozen subtropical
        # cyclones, so its seasonal percentages are far noisier than EP3's.
        ax.bar(xs + (k - 1) * width, pct.values, width,
               color=EP_COLORS[e], label=f"{get_ep_label(e)} (n={len(sub)})",
               edgecolor="white")
    ax.set_xticks(xs)
    ax.set_xticklabels(SEASONS)
    ax.set_ylabel("% of the EP's subtropical cyclones")
    ax.set_title("Seasonality of subtropical cyclones,\nby Energy Pattern")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[2]
    piv = annual.pivot_table(index="year", columns="type", values="n", fill_value=0)
    for cls in CLASS_PRECEDENCE:
        if cls not in piv.columns:
            continue
        ax.plot(piv.index, piv[cls], "-", lw=1.4, color=TYPE_COLORS[cls], label=cls, alpha=0.8)
        # 5-year running mean to expose low-frequency behaviour
        ax.plot(piv.index, piv[cls].rolling(5, center=True).mean(), "-",
                lw=2.8, color=TYPE_COLORS[cls])
    ax.set_yscale("symlog")
    ax.set_xlabel("year")
    ax.set_ylabel("cyclones per year")
    ax.set_title("Interannual counts\n(thick: 5-yr running mean)")
    ax.legend(frameon=False, fontsize=8)

    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Seasonal and interannual distribution — {DEFAULT_CRITERION}, "
                 f">= {MIN_PERSISTENCE_HOURS:.0f} h persistence",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dist_seasonal_annual.png", dpi=200, facecolor="white")
    plt.close(fig)
    print(f"  {(FIG_DIR / 'dist_seasonal_annual.png').relative_to(PROJECT_ROOT)}")

    # --- Property distributions ---
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    for ax, (col, label) in zip(axes.ravel(), metrics):
        data, labels, colors = [], [], []
        for cls in CLASS_PRECEDENCE:
            for e in ALL_EPS:
                sub = ep[(ep["type"] == cls) & (ep["ep"] == e)][col].dropna()
                if len(sub) >= 8:
                    data.append(sub.values)
                    labels.append(f"{get_ep_label(e)}\n{cls[:5]}")
                    colors.append(TYPE_COLORS[cls])
        if not data:
            continue
        bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6)
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.65)
        for med in bp["medians"]:
            med.set_color("black")
            med.set_linewidth(1.6)
        ax.set_xticklabels(labels, fontsize=7.5)
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Life-cycle properties by Energy Pattern and thermal type\n"
                 "(boxes: quartiles, whiskers 1.5 IQR, outliers hidden)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dist_properties.png", dpi=200, facecolor="white")
    plt.close(fig)
    print(f"  {(FIG_DIR / 'dist_properties.png').relative_to(PROJECT_ROOT)}")

    # --- Genesis map ---
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature

        fig, axes = plt.subplots(1, 3, figsize=(16, 5.5),
                                 subplot_kw={"projection": ccrs.PlateCarree()})
        for ax, cls in zip(axes, CLASS_PRECEDENCE):
            sub = df[df["type"] == cls]
            ax.set_extent([-75, -15, -60, -18], crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND, facecolor="#f0f0f0")
            ax.add_feature(cfeature.COASTLINE, lw=0.5)
            ax.scatter(sub["genesis_lon"], sub["genesis_lat"], s=6, alpha=0.35,
                       color=TYPE_COLORS[cls], transform=ccrs.PlateCarree(),
                       edgecolors="none")
            ax.set_title(f"{cls}  (n = {len(sub):,})", color=TYPE_COLORS[cls],
                         fontweight="bold")
            gl = ax.gridlines(draw_labels=True, lw=0.3, color="grey", alpha=0.4)
            gl.top_labels = gl.right_labels = False
        fig.suptitle("Genesis position by thermal type "
                     f"({DEFAULT_CRITERION}, >= {MIN_PERSISTENCE_HOURS:.0f} h persistence)",
                     fontsize=12, fontweight="bold")
        fig.tight_layout()
        fig.savefig(FIG_DIR / "dist_genesis_map.png", dpi=200, facecolor="white")
        plt.close(fig)
        print(f"  {(FIG_DIR / 'dist_genesis_map.png').relative_to(PROJECT_ROOT)}")
    except Exception as exc:
        print(f"  genesis map skipped ({type(exc).__name__}: {str(exc)[:60]})")

    # --- Persistence distributions ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))

    ax = axes[0]
    bins = np.arange(0, 168 + 6, 6)
    for e in ALL_EPS:
        vals = ep.loc[ep["ep"] == e, "hybrid_hours"].dropna()
        ax.hist(np.clip(vals, 0, 168), bins=bins, histtype="step", lw=2,
                density=True, color=EP_COLORS[e], label=get_ep_label(e))
    ax.axvline(MIN_PERSISTENCE_HOURS, color="k", ls="--", lw=1.5)
    ax.text(MIN_PERSISTENCE_HOURS + 3, ax.get_ylim()[1] * 0.85,
            f"{MIN_PERSISTENCE_HOURS:.0f} h", fontsize=9)
    ax.set_xlabel("longest continuous hybrid (subtropical) spell [h]")
    ax.set_ylabel("density")
    ax.set_title("How long each EP sustains hybrid structure")
    ax.legend(frameon=False, fontsize=9)

    ax = axes[1]
    thresholds = np.arange(0, 121, 6)
    for e in ALL_EPS:
        vals = ep.loc[ep["ep"] == e, "hybrid_hours"].dropna().values
        frac = [(vals >= t).mean() * 100 for t in thresholds]
        ax.plot(thresholds, frac, "-", lw=2.2, color=EP_COLORS[e], label=get_ep_label(e))
    ax.axvline(MIN_PERSISTENCE_HOURS, color="k", ls="--", lw=1.5)
    ax.set_xlabel("persistence threshold [h]")
    ax.set_ylabel("% of the EP exceeding the threshold")
    ax.set_title("Sensitivity of the subtropical count\nto the persistence threshold")
    ax.legend(frameon=False, fontsize=9)

    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Hybrid-structure persistence by Energy Pattern", fontsize=12,
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dist_persistence.png", dpi=200, facecolor="white")
    plt.close(fig)
    print(f"  {(FIG_DIR / 'dist_persistence.png').relative_to(PROJECT_ROOT)}")

    print("\nStep 4 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
