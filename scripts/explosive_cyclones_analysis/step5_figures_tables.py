"""
Step 5: Figures and tables for explosive-cyclone occurrence by Energy Pattern.

Results figures:
    fig_bomb_frequency_by_ep        % explosive per EP (life cycle vs intensification)
    fig_ndr_distribution_by_ep      NDR_max distribution per EP (boxplot)
    fig_intensity_class_by_ep       intensity-class composition per EP (stacked bar)

Validation figures (method sanity checks):
    fig_offset_distribution         vor-centre -> MSLP-minimum distance histogram
    fig_flag_fraction_by_phase      assignment flags by life-cycle phase

Inputs (results/explosive_cyclones/): ndr_by_cyclone.csv, bomb_frequency_by_ep.csv,
central_pressure_timeseries.csv, tracks_by_ep.csv

Run (local, after sync_from_remote.sh):
    python scripts/explosive_cyclones_analysis/step5_figures_tables.py

Author: Danilo Couto de Souza
Date: June 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.utils.ep_mapping import ALL_EPS, get_ep_label, get_ep_color

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RES_DIR = PROJECT_ROOT / "results" / "explosive_cyclones"
FIG_DIR = PROJECT_ROOT / "figures" / "explosive_cyclones"
DPI = 300


def _save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {name}.png / .pdf")


def fig_bomb_frequency(agg):
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(ALL_EPS))
    w = 0.38
    life = [agg.loc[agg["ep"] == ep, "pct_bomb_lifecycle"].iloc[0] for ep in ALL_EPS]
    intd = [agg.loc[agg["ep"] == ep, "pct_bomb_intensification"].iloc[0] for ep in ALL_EPS]
    colors = [get_ep_color(ep) for ep in ALL_EPS]
    ax.bar(x - w / 2, life, w, color=colors, edgecolor="k", label="life cycle")
    ax.bar(x + w / 2, intd, w, color=colors, edgecolor="k", alpha=0.55, hatch="//",
           label="intensification")
    ax.set_xticks(x, [get_ep_label(ep) for ep in ALL_EPS])
    ax.set_ylabel("Explosive cyclones (%)")
    ax.set_title("Bomb frequency by Energy Pattern")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, "fig_bomb_frequency_by_ep")


def fig_ndr_distribution(ndr):
    fig, ax = plt.subplots(figsize=(6, 4))
    data, colors = [], []
    for ep in ALL_EPS:
        v = ndr.loc[ndr["ep"] == ep, "ndr_max_lifecycle"].replace([np.inf, -np.inf], np.nan).dropna()
        data.append(v.values)
        colors.append(get_ep_color(ep))
    bp = ax.boxplot(data, patch_artist=True, showfliers=False,
                    medianprops=dict(color="k"))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.7)
    ax.axhline(1.0, color="red", ls="--", lw=1, label="1 Bergeron (bomb threshold)")
    ax.set_xticklabels([get_ep_label(ep) for ep in ALL_EPS])
    ax.set_ylabel(r"$NDR_{max}$ (Bergeron)")
    ax.set_title("Maximum normalized deepening rate by EP")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, "fig_ndr_distribution_by_ep")


def fig_intensity_class(ndr):
    classes = ["weak", "moderate", "intense"]
    hatch = {"weak": "", "moderate": "..", "intense": "xx"}
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, ep in enumerate(ALL_EPS):
        e = ndr[ndr["ep"] == ep]
        n = len(e)
        bottom = 0
        for cls in classes:
            pct = 100 * (e["intensity_class"] == cls).sum() / n if n else 0
            ax.bar(i, pct, bottom=bottom, color=get_ep_color(ep), alpha=0.8,
                   edgecolor="k", hatch=hatch[cls],
                   label=cls if i == 0 else None)
            bottom += pct
    ax.set_xticks(range(len(ALL_EPS)), [get_ep_label(ep) for ep in ALL_EPS])
    ax.set_ylabel("Explosive cyclones (% of EP)")
    ax.set_title("Explosive intensity class composition by EP")
    ax.legend(frameon=False, title="class")
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, "fig_intensity_class_by_ep")


def fig_offset_distribution(cp):
    valid = cp[cp["central_mslp"].notna()]
    fig, ax = plt.subplots(figsize=(6, 4))
    for ep in ALL_EPS:
        v = valid.loc[valid["ep"] == ep, "offset_deg"].dropna()
        ax.hist(v, bins=np.arange(0, 5.25, 0.25), histtype="step", density=True,
                color=get_ep_color(ep), lw=1.8, label=get_ep_label(ep))
    ax.axvline(3.0, color="gray", ls="--", lw=1, label="R0 = 3°")
    ax.set_xlabel("vorticity-centre → MSLP-minimum distance (°)")
    ax.set_ylabel("density")
    ax.set_title("Central-pressure assignment offset (validation)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, "fig_offset_distribution")


def fig_flag_by_phase(cp, tracks):
    if tracks is None:
        return
    t = tracks.copy()
    t["time"] = pd.to_datetime(t["date"])
    t["phase"] = t["period"].astype(str).str.split().str[0]
    m = cp.merge(t[["track_id", "time", "phase"]], on=["track_id", "time"], how="left")
    m["flag_grp"] = np.where(m["flag"] == "ok", "ok",
                     np.where(m["flag"] == "expanded", "expanded",
                     np.where(m["flag"] == "jump", "jump", "no_min/none")))
    order = ["incipient", "intensification", "mature", "decay", "residual"]
    phases = [p for p in order if p in m["phase"].unique()]
    grps = ["ok", "expanded", "jump", "no_min/none"]
    colors = {"ok": "#2c7", "expanded": "#fc3", "jump": "#f80", "no_min/none": "#c33"}
    fig, ax = plt.subplots(figsize=(6.5, 4))
    bottom = np.zeros(len(phases))
    for grp in grps:
        fr = []
        for ph in phases:
            sub = m[m["phase"] == ph]
            fr.append(100 * (sub["flag_grp"] == grp).mean() if len(sub) else 0)
        ax.bar(phases, fr, bottom=bottom, label=grp, color=colors[grp], edgecolor="k", lw=0.3)
        bottom += np.array(fr)
    ax.set_ylabel("timesteps (%)")
    ax.set_title("Assignment flags by life-cycle phase (validation)")
    ax.legend(frameon=False, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _save(fig, "fig_flag_fraction_by_phase")


def main():
    ndr_f = RES_DIR / "ndr_by_cyclone.csv"
    agg_f = RES_DIR / "bomb_frequency_by_ep.csv"
    cp_f = RES_DIR / "central_pressure_timeseries.csv"
    if not ndr_f.exists() or not agg_f.exists():
        print(f"❌ Missing step4 outputs in {RES_DIR}. Run step4 first.")
        return 1

    ndr = pd.read_csv(ndr_f)
    agg = pd.read_csv(agg_f)
    cp = pd.read_csv(cp_f, parse_dates=["time"]) if cp_f.exists() else None
    tracks_f = RES_DIR / "tracks_by_ep.csv"
    tracks = pd.read_csv(tracks_f) if tracks_f.exists() else None

    print("=" * 70)
    print("STEP 5: Figures and tables")
    print("=" * 70)

    fig_bomb_frequency(agg)
    fig_ndr_distribution(ndr)
    fig_intensity_class(ndr)
    if cp is not None:
        fig_offset_distribution(cp)
        fig_flag_by_phase(cp, tracks)

    print(f"\n✓ Figures written to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
