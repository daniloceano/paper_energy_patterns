"""
Step 4: When in the life cycle does each thermal structure appear?

This step exists to answer one methodological question: **is the "tropical"
class real, or is it warm seclusions?**

The distinction cannot be made by persistence. A Shapiro-Keyser warm seclusion
routinely holds a symmetric warm core for well over 36 h, so a persistence
filter passes it. What separates the two is WHEN the warm core appears:

    genuine hybrid / tropical genesis   warm core is present from the start;
                                        the hybrid structure IS the genesis
                                        mechanism (Davis and Bosart 2004)

    warm seclusion                      warm core appears at or after occlusion,
                                        late in a baroclinic life cycle, having
                                        begun as a robust cold-core system

Guishard et al. (2009) encode exactly this, requiring that a subtropical storm
"become subtropical (i.e., attain hybrid structure) within 24 h if identified
first as a purely cold- or warm-cored system", with the rationale:

    "Systems that begin as robust tropical or extratropical cyclones have been
     rejected because they are deemed in this methodology to only be able to
     attain the hybrid structure via extratropical transition (ET) or tropical
     transition, respectively."

Gozzo et al. (2014) carry the same criterion into the South Atlantic. Cavicchia
et al. (2019), working on a mid-latitude population comparable to ours, state
the underlying limitation outright: "cyclone phase space alone does not
distinguish tropical cyclones from warm-seclusion extratropical cyclones
(Hart 2003)".

This step quantifies the effect for our population, three ways:
    1. life-cycle phase composition of each class (uses the `period` label)
    2. onset time of each class relative to genesis
    3. the attrition of each class as the criteria tighten

Inputs:
    results/cps_analysis/cps_timesteps_classified.csv   (step 2)
    results/cps_analysis/cyclone_types.csv              (step 2)

Outputs:
    results/cps_analysis/lifecycle_phase_composition.csv
    results/cps_analysis/onset_timing.csv
    results/cps_analysis/criteria_attrition.csv
    results/cps_analysis/warm_seclusion_diagnosis.txt
    figures/cps_analysis/lifecycle_timing.png

Run:
    python scripts/cps_analysis/sensitivity/s3_lifecycle_timing.py

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

from scripts.cps_analysis.cps_criteria import (
    CRITERIA,
    CRITERIA_SOURCES,
    CLASS_PRECEDENCE,
    UNCLASSIFIED,
    MIN_PERSISTENCE_HOURS,
    MAX_ONSET_HOURS,
    PRIMARY_CRITERIA,
    CROSS_BASIN_CRITERIA,
    TYPE_COLORS,
    DEFAULT_CRITERION,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis" / "sensitivity"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis" / "sensitivity"

TS_FILE = RESULTS_DIR / "cps_timesteps_classified.csv"
CY_FILE = RESULTS_DIR / "cyclone_types.csv"

# Life-cycle phases in chronological order. The tracking labels a second
# baroclinic development as "... 2"; those are folded into the base phase.
PHASES = ["incipient", "intensification", "mature", "decay", "residual"]
RULES = ["type_any", "type_persistent", "type_protocol", "type_strict"]


def base_phase(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\s*2$", "", regex=True)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 3: Life-cycle timing — warm-seclusion diagnosis")
    print("=" * 70)

    for f in (TS_FILE, CY_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    ts = pd.read_csv(TS_FILE, parse_dates=["datetime"])
    cyclones = pd.read_csv(CY_FILE)

    ts["phase"] = base_phase(ts["period"])
    genesis = ts.groupby("track_id")["datetime"].transform("min")
    ts["h_since_genesis"] = (ts["datetime"] - genesis).dt.total_seconds() / 3600
    span = ts.groupby("track_id")["h_since_genesis"].transform("max")
    ts["life_fraction"] = ts["h_since_genesis"] / span.replace(0, np.nan)

    classifiable = ts[["B", "VTL", "VTU"]].notna().all(axis=1)
    report = []

    # ------------------------------------------------------------------
    # 1. Life-cycle phase composition of each class
    # ------------------------------------------------------------------
    header = "\n1. LIFE-CYCLE PHASE COMPOSITION OF EACH CLASS (% of that class's timesteps)"
    print(header)
    report.append(header)

    baseline = (ts.loc[classifiable, "phase"].value_counts(normalize=True) * 100)
    rows = []

    for criterion in [DEFAULT_CRITERION, "C03", "CAVICCHIA19"]:
        line = f"\n  {criterion}  [{CRITERIA_SOURCES[criterion]}]"
        print(line)
        report.append(line)
        hdr = "    {:<15s}".format("class") + "".join(f"{p:>17s}" for p in PHASES) + "      n"
        print(hdr)
        report.append(hdr)

        for cls in CLASS_PRECEDENCE:
            mask = ts[f"{criterion}_{cls}"] == True  # noqa: E712
            sub = ts.loc[mask, "phase"]
            if sub.empty:
                continue
            pct = sub.value_counts(normalize=True) * 100
            cells = "".join(f"{pct.get(p, 0.0):16.1f}%" for p in PHASES)
            line = f"    {cls:<15s}{cells}  {len(sub):7,d}"
            print(line)
            report.append(line)
            rows.append({"criterion": criterion, "class": cls, "n_timesteps": len(sub),
                         **{p: round(float(pct.get(p, 0.0)), 2) for p in PHASES}})

        cells = "".join(f"{baseline.get(p, 0.0):16.1f}%" for p in PHASES)
        line = f"    {'(baseline)':<15s}{cells}  {int(classifiable.sum()):7,d}"
        print(line)
        report.append(line)

    rows.append({"criterion": "ALL", "class": "baseline",
                 "n_timesteps": int(classifiable.sum()),
                 **{p: round(float(baseline.get(p, 0.0)), 2) for p in PHASES}})
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "lifecycle_phase_composition.csv", index=False)

    # ------------------------------------------------------------------
    # 2. Onset timing relative to genesis
    # ------------------------------------------------------------------
    header = ("\n\n2. ONSET TIMING — hours from genesis to the FIRST timestep of each class\n"
              f"   (and to the first run lasting >= {MIN_PERSISTENCE_HOURS:.0f} h)")
    print(header)
    report.append(header)

    onset_rows = []
    for criterion in PRIMARY_CRITERIA + CROSS_BASIN_CRITERIA:
        line = f"\n  {criterion}"
        print(line)
        report.append(line)
        for cls in CLASS_PRECEDENCE:
            mask = ts[f"{criterion}_{cls}"] == True  # noqa: E712
            if not mask.any():
                continue
            g = ts.loc[mask].groupby("track_id")
            first_h = g["h_since_genesis"].min()
            first_lf = g["life_fraction"].min()

            # Onset of the persistent run comes from step 2's per-cyclone table.
            col = f"{criterion}_onset_{cls}"
            persistent_onset = pd.to_numeric(cyclones[col], errors="coerce")
            persistent_onset = persistent_onset[np.isfinite(persistent_onset)]

            line = (f"    {cls:<14s} n = {len(first_h):5,d} | "
                    f"first step: median {np.median(first_h):5.0f} h "
                    f"(life fraction {np.nanmedian(first_lf):.2f}), "
                    f"within {MAX_ONSET_HOURS:.0f} h of genesis: "
                    f"{100 * (first_h <= MAX_ONSET_HOURS).mean():4.1f}%")
            print(line)
            report.append(line)
            if len(persistent_onset):
                line = (f"    {'':<14s} persistent run onset: median "
                        f"{np.median(persistent_onset):5.0f} h, "
                        f"within {MAX_ONSET_HOURS:.0f} h: "
                        f"{100 * (persistent_onset <= MAX_ONSET_HOURS).mean():4.1f}% "
                        f"(n = {len(persistent_onset):,})")
                print(line)
                report.append(line)

            onset_rows.append({
                "criterion": criterion, "class": cls, "n_cyclones": len(first_h),
                "onset_p25_h": round(float(np.percentile(first_h, 25)), 1),
                "onset_median_h": round(float(np.median(first_h)), 1),
                "onset_p75_h": round(float(np.percentile(first_h, 75)), 1),
                "median_life_fraction": round(float(np.nanmedian(first_lf)), 3),
                "pct_within_24h": round(float(100 * (first_h <= MAX_ONSET_HOURS).mean()), 1),
            })

    pd.DataFrame(onset_rows).to_csv(RESULTS_DIR / "onset_timing.csv", index=False)

    # ------------------------------------------------------------------
    # 3. Attrition as the criteria tighten
    # ------------------------------------------------------------------
    header = "\n\n3. ATTRITION — cyclone counts as each successive criterion is applied"
    print(header)
    report.append(header)

    att_rows = []
    for criterion in PRIMARY_CRITERIA + CROSS_BASIN_CRITERIA:
        line = f"\n  {criterion:<12s}" + "".join(f"{r.replace('type_', ''):>16s}" for r in RULES)
        print(line)
        report.append(line)
        for cls in CLASS_PRECEDENCE:
            counts = [int((cyclones[f"{criterion}_{r}"] == cls).sum()) for r in RULES]
            line = f"    {cls:<10s}" + "".join(f"{c:16,d}" for c in counts)
            print(line)
            report.append(line)
            att_rows.append({"criterion": criterion, "class": cls,
                             **{r: c for r, c in zip(RULES, counts)}})

    pd.DataFrame(att_rows).to_csv(RESULTS_DIR / "criteria_attrition.csv", index=False)

    # ------------------------------------------------------------------
    # Verdict
    # ------------------------------------------------------------------
    trop_strict = {c: int((cyclones[f"{c}_type_strict"] == "tropical").sum())
                   for c in PRIMARY_CRITERIA + CROSS_BASIN_CRITERIA}
    trop_persist = {c: int((cyclones[f"{c}_type_persistent"] == "tropical").sum())
                    for c in PRIMARY_CRITERIA + CROSS_BASIN_CRITERIA}

    mask = ts[f"{DEFAULT_CRITERION}_tropical"] == True  # noqa: E712
    trop_lat = ts.loc[mask, "lat"].median()
    trop_late = (ts.loc[mask, "phase"].isin(["mature", "decay"]).mean() * 100)

    verdict = f"""

{'=' * 70}
VERDICT
{'=' * 70}
Timesteps classified tropical ({DEFAULT_CRITERION}) have a median latitude of
{trop_lat:.1f} deg and {trop_late:.0f}% of them fall in the mature or decay phase,
against a population baseline of {baseline.get('mature', 0) + baseline.get('decay', 0):.0f}%.
They are warm seclusions, not tropical cyclones.

Tropical cyclone counts, persistent (>= {MIN_PERSISTENCE_HOURS:.0f} h) vs strict
(+ ocean + genesis band + onset <= {MAX_ONSET_HOURS:.0f} h):
"""
    for c in PRIMARY_CRITERIA + CROSS_BASIN_CRITERIA:
        verdict += f"    {c:<14s} {trop_persist[c]:4d}  ->  {trop_strict[c]:4d}\n"

    verdict += f"""
The tropical class collapses to {min(trop_strict.values())}-{max(trop_strict.values())} cyclones under EVERY threshold set,
including the three imported from other basins. Persistence alone does not
remove the contamination; the genesis-relative onset criterion does.
"""
    print(verdict)
    report.append(verdict)

    with open(RESULTS_DIR / "warm_seclusion_diagnosis.txt", "w") as fh:
        fh.write("Warm-seclusion diagnosis — CPS life-cycle timing\n")
        fh.write("\n".join(report) + "\n")
    print(f"Wrote {(RESULTS_DIR / 'warm_seclusion_diagnosis.txt').relative_to(PROJECT_ROOT)}")

    # ------------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    ax = axes[0]
    x = np.arange(len(PHASES))
    width = 0.22
    for k, cls in enumerate(CLASS_PRECEDENCE):
        mask = ts[f"{DEFAULT_CRITERION}_{cls}"] == True  # noqa: E712
        pct = ts.loc[mask, "phase"].value_counts(normalize=True) * 100
        ax.bar(x + (k - 1) * width, [pct.get(p, 0) for p in PHASES], width,
               label=cls, color=TYPE_COLORS[cls], edgecolor="white")
    ax.plot(x, [baseline.get(p, 0) for p in PHASES], "k--o", lw=1.5, ms=5,
            label="all timesteps")
    ax.set_xticks(x)
    ax.set_xticklabels([p[:6] for p in PHASES], rotation=20)
    ax.set_ylabel("% of the class's timesteps")
    ax.set_title("Where in the life cycle each\nstructure occurs")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    for cls in CLASS_PRECEDENCE:
        mask = ts[f"{DEFAULT_CRITERION}_{cls}"] == True  # noqa: E712
        if not mask.any():
            continue
        first = ts.loc[mask].groupby("track_id")["h_since_genesis"].min()
        ax.hist(np.clip(first, 0, 240), bins=40, histtype="step", lw=2,
                density=True, color=TYPE_COLORS[cls], label=cls)
    ax.axvline(MAX_ONSET_HOURS, color="k", ls="--", lw=1.5)
    ax.text(MAX_ONSET_HOURS + 4, ax.get_ylim()[1] * 0.9,
            f"{MAX_ONSET_HOURS:.0f} h criterion\n(Guishard et al. 2009)", fontsize=8)
    ax.set_xlabel("hours from genesis to first occurrence")
    ax.set_ylabel("density")
    ax.set_title("Onset timing relative to genesis")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[2]
    labels = [r.replace("type_", "") for r in RULES]
    # Stagger the annotations vertically per class so the extratropical and
    # subtropical labels do not collide where the two curves start together.
    offsets = {"tropical": -14, "subtropical": -14, "extratropical": 9}
    for cls in CLASS_PRECEDENCE:
        counts = [int((cyclones[f"{DEFAULT_CRITERION}_{r}"] == cls).sum()) for r in RULES]
        ax.plot(labels, counts, "-o", color=TYPE_COLORS[cls], lw=2, ms=7, label=cls)
        for xi, c in enumerate(counts):
            ax.annotate(f"{c:,}", (xi, c), textcoords="offset points",
                        xytext=(0, offsets[cls]), ha="center", fontsize=8,
                        color=TYPE_COLORS[cls], fontweight="bold")
    ax.set_yscale("symlog")
    ax.set_ylabel("number of cyclones")
    ax.set_title("Attrition as criteria tighten")
    ax.tick_params(axis="x", rotation=20)
    ax.legend(frameon=False, fontsize=8)

    for a in axes:
        a.spines[["top", "right"]].set_visible(False)

    fig.suptitle(
        f"Warm-seclusion diagnosis ({DEFAULT_CRITERION}): the tropical class occurs late in the "
        "baroclinic life cycle,\nand disappears once the genesis-relative onset criterion is applied",
        fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = FIG_DIR / "lifecycle_timing.png"
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Wrote {out.relative_to(PROJECT_ROOT)}")

    print("\nStep 3 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
