"""
Step 9 (CANONICAL): where each cyclone type forms and where it lives.

Spherical-KDE density maps of the phase classes, laid out as

    rows      cyclone type   ALL, then one row per phase class
    columns   EPALL, EP1, EP2, EP3

and produced for two kinds of position:

    GENESIS   the cyclogenesis point only (one position per cyclone)
    TRACK     every 3-hourly position of the whole life cycle

so the pair answers "where is this type born" and "where does it spend its
life", separately for each Energy Pattern.

What the panels show
--------------------
Two modes, both written, because they answer different questions and neither
is a substitute for the other:

  anomaly (default)   column 1 is the ABSOLUTE density of that type over EPALL;
                      columns 2-4 are the min-max normalised anomaly of the
                      type within that EP against the same type over EPALL.
                      This is the convention of the manuscript's genesis figure
                      (`scripts/main/07_figure_genesis_density_kde.py`) and it
                      isolates the SHAPE of the distribution from the sample
                      size, which matters here because the EPs are very
                      unequal in number (EP1 444, EP2 979, EP3 2,397) and the
                      rarer classes are unequal again within them.

  absolute            all four columns are absolute density on one colour
                      scale per row. Sample size is then part of what the
                      reader sees: the EP1 subtropical panel is nearly blank
                      because EP1 barely produces subtropical cyclones, which
                      is the C4 result stated as a map.

Units are cyclogenesis events / 10^6 km^2 / year for the genesis maps and
cyclone DAYS / 10^6 km^2 / year for the whole-life maps (see `cps_density`).

The EPALL population
--------------------
EPALL is the union EP1 + EP2 + EP3 = 3,812 cyclones, NOT the 6,776 of the
catalogue, for the same reason as step 8: the EP columns are read against
EPALL, so the reference has to be the population the EPs actually partition.
`--epall catalogue` switches to the full catalogue for the EPALL column, which
makes the type rows better sampled at the cost of that consistency.

Whole life means whole life
---------------------------
The TRACK maps use EVERY position of a cyclone of the given class, not only
the positions classified as that structure. A single-state SC cyclone spends a
median 0.74 of its life subtropical (C2), so its track map includes the
extratropical remainder of the life cycle. That is what "a vida toda" means and
it is the right denominator for a residence-time map; the structure-resolved
version of the same question is fig6.

Small samples
-------------
A panel with fewer than `cps_density.MIN_KDE_CYCLONES` cyclones gets its raw
positions plotted as points and no density field. The 3-hourly positions of one
cyclone are not independent samples, so the gate is on cyclone count.

Inputs:
    results/cps_analysis/phase_classification.csv   (step 2)
    results/cps_analysis/phase_timesteps.csv        (step 2)

Outputs:
    figures/cps_analysis/fig9_genesis_density_<set>_<mode>.png
    figures/cps_analysis/fig10_track_density_<set>_<mode>.png
    results/cps_analysis/density_map_samples.csv   (one row per panel drawn;
        a run restricted with --classes/--kinds writes a restricted table, so
        re-run without arguments to restore the canonical one)

Run:
    python scripts/cps_analysis/step9_density_maps.py
    python scripts/cps_analysis/step9_density_maps.py --sets identified \
        --modes anomaly --kinds genesis

Author: Danilo Couto de Souza
Date: August 2026
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cartopy.crs as ccrs

from scripts.utils.ep_mapping import ALL_EPS, EP_COLORS, get_ep_label
from scripts.cps_analysis.cps_criteria import PHASE_COLORS
from scripts.cps_analysis import cps_density as cd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "cps_analysis"
FIG_DIR = PROJECT_ROOT / "figures" / "cps_analysis"
CLASS_FILE = RESULTS_DIR / "phase_classification.csv"
TS_FILE = RESULTS_DIR / "phase_timesteps.csv"
OUT_CSV = RESULTS_DIR / "density_map_samples.csv"

# The reference row, drawn first in every figure: no class restriction.
ALL_ROW = "ALL"

# Which classes go on which figure. TC and TC_like are excluded by default:
# two cyclones each, so every panel would be a scatter of two points. Ask for
# them explicitly with --classes if a figure of the candidates is wanted.
CLASS_SETS = {
    "identified": ["EC", "SC", "ST", "SD"],
    "characteristics": ["EC_like", "SC_like", "undetermined"],
}

# Short row labels. The full definitions live in cps_criteria; these are cut to
# what fits in a rotated label beside a map.
ROW_LABELS = {
    ALL_ROW: "every cyclone",
    "EC": "extratropical throughout",
    "SC": "subtropical throughout",
    "TC": "tropical throughout",
    "ST": "subtropical transition  EC→SC",
    "SD": "subtropical decay  SC→EC",
    "EC_like": "extratropical characteristics",
    "SC_like": "hybrid characteristics",
    "TC_like": "warm-core characteristics",
    "undetermined": "no dominant structure",
}

KIND_TITLES = {
    "genesis": ("Cyclogenesis density by cyclone type and Energy Pattern",
                "one position per cyclone — the genesis point"),
    "track": ("Track density by cyclone type and Energy Pattern",
              "every 3-hourly position of the whole life cycle"),
}

KIND_UNITS = {
    "genesis": "cyclogenesis events per 10$^6$ km$^2$ per year",
    "track": "cyclone days per 10$^6$ km$^2$ per year",
}

FIG_PREFIX = {"genesis": "fig9_genesis_density", "track": "fig10_track_density"}

# --- Layout, in inches (positions are computed explicitly; no tight_layout) ---
FIG_W = 13.0
LEFT_M, RIGHT_M = 1.15, 0.25
TOP_M, BOTTOM_M = 1.35, 0.55
COL_GAP = 0.16
CBAR_PAD = 0.34     # map bottom -> colour bar top (room for the lon labels)
CBAR_H = 0.13
CBAR_LABEL_H = 0.34  # below the bar: its ticks and its label
ROW_GAP = 0.26


# =============================================================================
# DATA
# =============================================================================

def load_population(epall: str):
    """Cyclone table and its 3-hourly positions, for the chosen EPALL population."""
    cls = pd.read_csv(CLASS_FILE, usecols=["track_id", "ep", "phase_class",
                                           "genesis_lat", "genesis_lon", "year"])
    n_catalogue = len(cls)
    if epall == "clustered":
        cls = cls[cls["ep"].notna()].copy()
    cls["track_id"] = cls["track_id"].astype(int)

    ts = pd.read_csv(TS_FILE, usecols=["track_id", "lat", "lon"])
    ts = ts.dropna(subset=["lat", "lon"])
    ts["track_id"] = ts["track_id"].astype(int)
    ts = ts[ts["track_id"].isin(set(cls["track_id"]))]
    ts = ts.merge(cls[["track_id", "ep", "phase_class"]], on="track_id",
                  how="left")

    n_years = int(cls["year"].max() - cls["year"].min() + 1)
    print(f"  catalogue          {n_catalogue:,} cyclones")
    print(f"  EPALL population   {len(cls):,} cyclones "
          f"({'EP1+EP2+EP3' if epall == 'clustered' else 'whole catalogue'})")
    print(f"  positions          {len(ts):,} 3-hourly steps")
    print(f"  genesis years      {int(cls['year'].min())}–{int(cls['year'].max())} "
          f"({n_years} years)")
    return cls, ts, n_years


def subset(cls: pd.DataFrame, ts: pd.DataFrame, phase_class: str, ep):
    """Cyclones (and their positions) of one class and one EP column.

    `ep` is None for the EPALL column, otherwise 1, 2 or 3.
    """
    c = cls if phase_class == ALL_ROW else cls[cls["phase_class"] == phase_class]
    t = ts if phase_class == ALL_ROW else ts[ts["phase_class"] == phase_class]
    if ep is not None:
        c = c[c["ep"] == ep]
        t = t[t["ep"] == ep]
    return c, t


def build_densities(cls, ts, classes, kinds, n_years):
    """KDE field, positions and counts for every (kind, class, column) cell.

    Computed once and reused by both plotting modes — the KDE over 2 x 10^5
    positions is the expensive part of this step.
    """
    columns = [(get_ep_label(0), None)] + [(get_ep_label(ep), ep) for ep in ALL_EPS]
    cache, records = {}, []

    for kind in kinds:
        domain = cd.GENESIS_DOMAIN if kind == "genesis" else cd.TRACK_DOMAIN
        weight = 1.0 if kind == "genesis" else cd.TRACK_TIMESTEP_HOURS / 24.0
        print(f"\n  {kind} maps ({domain.extent}):")

        for phase_class in [ALL_ROW] + classes:
            for label, ep in columns:
                c, t = subset(cls, ts, phase_class, ep)
                n_cyc = len(c)
                if kind == "genesis":
                    lat = c["genesis_lat"].to_numpy()
                    lon = c["genesis_lon"].to_numpy()
                else:
                    lat = t["lat"].to_numpy()
                    lon = t["lon"].to_numpy()

                inside = np.mean(
                    (lon >= domain.lon_min) & (lon <= domain.lon_max) &
                    (lat >= domain.lat_min) & (lat <= domain.lat_max)
                ) if lat.size else np.nan

                field = None
                if n_cyc >= cd.MIN_KDE_CYCLONES:
                    field, _, _ = cd.compute_density(lat, lon, n_years, domain,
                                                     weight=weight)

                cache[(kind, phase_class, label)] = dict(
                    field=field, lat=lat, lon=lon, n_cyclones=n_cyc,
                    n_positions=int(lat.size), inside=inside)
                records.append(dict(
                    kind=kind, phase_class=phase_class, column=label,
                    n_cyclones=n_cyc, n_positions=int(lat.size),
                    frac_in_domain=round(float(inside), 4) if lat.size else np.nan,
                    density_max=(round(float(np.nanmax(field)), 4)
                                 if field is not None else np.nan),
                    kde_estimated=field is not None))
                print(f"    {phase_class:<14s} {label:<6s} "
                      f"{n_cyc:6,d} cyclones  {lat.size:8,d} positions"
                      + ("" if field is not None else "   [points only]"))

    return cache, pd.DataFrame(records)


# =============================================================================
# FIGURE
# =============================================================================

def layout(n_rows: int, domain: cd.Domain):
    """Explicit panel geometry: (figure, axes grid, colour-bar strip rows).

    Every panel is drawn at the true shape of the domain, so the maps fill
    their boxes instead of letterboxing inside them.
    """
    panel_w = (FIG_W - LEFT_M - RIGHT_M - 3 * COL_GAP) / 4.0
    panel_h = panel_w * domain.aspect
    row_h = panel_h + CBAR_PAD + CBAR_H + CBAR_LABEL_H
    fig_h = TOP_M + n_rows * row_h + (n_rows - 1) * ROW_GAP + BOTTOM_M

    fig = plt.figure(figsize=(FIG_W, fig_h))

    def rect(x, y_from_top, w, h):
        """Inches from the top-left corner -> matplotlib figure fractions."""
        return [x / FIG_W, 1.0 - (y_from_top + h) / fig_h, w / FIG_W, h / fig_h]

    axes, cbars = [], []
    for i in range(n_rows):
        y = TOP_M + i * (row_h + ROW_GAP)
        row_axes = []
        for j in range(4):
            x = LEFT_M + j * (panel_w + COL_GAP)
            row_axes.append(fig.add_axes(rect(x, y, panel_w, panel_h),
                                         projection=ccrs.PlateCarree()))
        axes.append(row_axes)
        cbars.append(dict(
            y=y + panel_h + CBAR_PAD, h=CBAR_H, rect=rect,
            x_first=LEFT_M, w_first=panel_w,
            x_rest=LEFT_M + panel_w + COL_GAP,
            w_rest=3 * panel_w + 2 * COL_GAP,
            x_full=LEFT_M, w_full=4 * panel_w + 3 * COL_GAP))
    return fig, axes, cbars, fig_h, panel_h


def _tick_format(vmax: float) -> str:
    if vmax < 0.1:
        return "%.3f"
    if vmax < 1.0:
        return "%.2f"
    if vmax < 10.0:
        return "%.1f"
    return "%.0f"


def _add_cbar(fig, spec, x, w, mappable, label, fmt):
    cax = fig.add_axes(spec["rect"](x, spec["y"], w, spec["h"]))
    cb = fig.colorbar(mappable, cax=cax, orientation="horizontal")
    cb.set_label(label, fontsize=8)
    cb.ax.tick_params(labelsize=7.5)
    ticks = cb.get_ticks()
    cb.set_ticks(ticks)
    # "-0.00" is a rounding artefact of the diverging scale, not a value.
    cb.set_ticklabels([(fmt % t).replace("-0.00", "0.00") for t in ticks])
    return cb


def make_figure(kind: str, classes: list, mode: str, cache: dict,
                n_years: int, epall_n: int, out_path: Path):
    """One figure: rows = cyclone type, columns = EPALL / EP1 / EP2 / EP3."""
    domain = cd.GENESIS_DOMAIN if kind == "genesis" else cd.TRACK_DOMAIN
    rows = [ALL_ROW] + classes
    columns = [(get_ep_label(0), None)] + [(get_ep_label(ep), ep) for ep in ALL_EPS]
    fig, axes, cbars, fig_h, panel_h = layout(len(rows), domain)
    letters = "abcdefghijklmnopqrstuvwxyz"
    # The row description is rotated alongside the panel, so it has to fit in
    # the panel height: the track domain is a much flatter box than the genesis
    # one.
    desc_fs = 8.5 if panel_h >= 1.6 else 6.8

    longrd, latgrd = cd.domain_grid(domain)

    for i, phase_class in enumerate(rows):
        cells = [cache[(kind, phase_class, label)] for label, _ in columns]
        colour = PHASE_COLORS.get(phase_class, "0.35")

        # --- colour scales, shared across the row -----------------------------
        if mode == "absolute":
            vmax = cd.robust_vmax([c["field"] for c in cells])
            fields = [c["field"] for c in cells]
            maxabs = None
        else:
            ref = cells[0]["field"]
            vmax = cd.robust_vmax([ref])
            norm_ref = (cd.minmax_normalize_positive(ref)
                        if ref is not None else None)
            fields = [ref]
            for c in cells[1:]:
                if c["field"] is None or norm_ref is None:
                    fields.append(None)
                else:
                    fields.append(cd.minmax_normalize_positive(c["field"])
                                  - norm_ref)
            maxabs = cd.symmetric_max(fields[1:])

        mappable_abs = mappable_anom = None

        for j, (label, ep) in enumerate(columns):
            ax = axes[i][j]
            cell = cells[j]
            cd.setup_map_axes(ax, domain, left_labels=(j == 0),
                              bottom_labels=(i == len(rows) - 1))

            field = fields[j]
            is_anomaly = (mode == "anomaly" and j > 0)
            scale = maxabs if is_anomaly else vmax
            drawable = field is not None and scale is not None and scale > 0

            if drawable and is_anomaly:
                mappable_anom = cd.draw_anomaly(ax, field, longrd, latgrd,
                                                maxabs)
            elif drawable:
                mappable_abs = cd.draw_density(ax, field, longrd, latgrd, vmax)
            elif 0 < cell["n_cyclones"] < cd.MIN_KDE_CYCLONES:
                cd.draw_points(ax, cell["lat"], cell["lon"], colour)
                cd.panel_note(ax, f"n = {cell['n_cyclones']} cyclones\n"
                                  "too few for a density estimate")
            elif cell["n_cyclones"]:
                cd.panel_note(ax, "no anomaly: the reference field is empty",
                              color="0.55")
            else:
                cd.panel_note(ax, "no cyclones", color="0.55")

            ax.text(0.018, 0.955, f"({letters[i * 4 + j]})",
                    transform=ax.transAxes, fontsize=8.5, fontweight="bold",
                    va="top", zorder=7,
                    bbox=dict(fc="white", ec="none", alpha=0.7, pad=1.2))
            ax.text(0.982, 0.955, f"n = {cell['n_cyclones']:,}",
                    transform=ax.transAxes, fontsize=8, ha="right", va="top",
                    color="0.25", zorder=7,
                    bbox=dict(fc="white", ec="none", alpha=0.7, pad=1.2))

            # On a shared absolute scale the low-count panels go faint; the
            # peak value keeps them quantitative anyway.
            if mode == "absolute" and cell["field"] is not None:
                peak = float(np.nanmax(cell["field"]))
                ax.text(0.018, 0.045, f"max {_tick_format(peak) % peak}",
                        transform=ax.transAxes, fontsize=7.5, va="bottom",
                        color="0.25", zorder=7,
                        bbox=dict(fc="white", ec="none", alpha=0.7, pad=1.2))

            if i == 0:
                ax.text(0.5, 1.10, label, transform=ax.transAxes, ha="center",
                        va="bottom", fontsize=13, fontweight="bold",
                        color=EP_COLORS[ep if ep is not None else 0])

        # --- row label and colour bars ---------------------------------------
        y_mid = np.mean([axes[i][0].get_position().y0,
                         axes[i][0].get_position().y1])
        fig.text(0.030, y_mid, phase_class, rotation=90, va="center",
                 ha="center", fontsize=13, fontweight="bold", color=colour)
        fig.text(0.058, y_mid, ROW_LABELS.get(phase_class, ""), rotation=90,
                 va="center", ha="center", fontsize=desc_fs, color="0.35")

        spec = cbars[i]
        if mode == "absolute":
            if mappable_abs is not None:
                _add_cbar(fig, spec, spec["x_full"], spec["w_full"],
                          mappable_abs, KIND_UNITS[kind], _tick_format(vmax))
        else:
            if mappable_abs is not None:
                _add_cbar(fig, spec, spec["x_first"], spec["w_first"],
                          mappable_abs, KIND_UNITS[kind], _tick_format(vmax))
            if mappable_anom is not None:
                _add_cbar(fig, spec, spec["x_rest"], spec["w_rest"],
                          mappable_anom,
                          "normalised anomaly relative to EPALL, same cyclone type",
                          "%.2f")

    # --- titles ---------------------------------------------------------------
    title, subtitle = KIND_TITLES[kind]
    fig.text(0.5, 1.0 - 0.30 / fig_h, title, ha="center", va="top",
             fontsize=17, fontweight="bold")
    mode_note = ("column 1 absolute; columns 2–4 min-max normalised anomaly "
                 "against EPALL of the same type"
                 if mode == "anomaly" else
                 "absolute density, one colour scale per row")
    fig.text(0.5, 1.0 - 0.60 / fig_h,
             f"{subtitle}  ·  {mode_note}", ha="center", va="top",
             fontsize=10, color="0.35")
    fig.text(0.5, 1.0 - 0.84 / fig_h,
             f"EPALL = EP1 ∪ EP2 ∪ EP3 = {epall_n:,} cyclones  ·  "
             f"genesis 1979–2020 ({n_years} years)  ·  "
             f"Gaussian KDE, haversine metric, bandwidth "
             f"{cd.KDE_BANDWIDTH} rad (~318 km), 2.5° grid",
             ha="center", va="top", fontsize=8.5, color="0.45")

    fig.savefig(out_path, dpi=180, facecolor="white")
    plt.close(fig)
    print(f"    {out_path.relative_to(PROJECT_ROOT)}")


# =============================================================================
# MAIN
# =============================================================================

def main(sets, modes, kinds, classes_override, epall):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 9 (CANONICAL): genesis and track density by cyclone type and EP")
    print("=" * 70)

    for f in (CLASS_FILE, TS_FILE):
        if not f.exists():
            print(f"Missing {f}. Run step 2 first.")
            return 1

    print("\nPopulation:")
    cls, ts, n_years = load_population(epall)

    if classes_override:
        figure_sets = {"custom": list(classes_override)}
    else:
        figure_sets = {name: CLASS_SETS[name] for name in sets}

    wanted = sorted({c for group in figure_sets.values() for c in group})
    missing = [c for c in wanted if c not in set(cls["phase_class"])]
    if missing:
        print(f"\n  Classes absent from this population: {', '.join(missing)}")
        wanted = [c for c in wanted if c not in missing]
        figure_sets = {k: [c for c in v if c not in missing]
                       for k, v in figure_sets.items()}

    print("\nComputing densities (KDE over the whole population is the slow part):")
    cache, samples = build_densities(cls, ts, wanted, kinds, n_years)
    samples.to_csv(OUT_CSV, index=False)
    print(f"\n  {OUT_CSV.relative_to(PROJECT_ROOT)}  ({len(samples)} cells)")

    print("\nDrawing figures:")
    for set_name, group in figure_sets.items():
        if not group:
            continue
        for kind in kinds:
            for mode in modes:
                out = FIG_DIR / f"{FIG_PREFIX[kind]}_{set_name}_{mode}.png"
                make_figure(kind, group, mode, cache, n_years, len(cls), out)

    print("\nStep 9 complete.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Genesis and whole-life density maps by cyclone type and EP.")
    ap.add_argument("--sets", nargs="+", default=list(CLASS_SETS),
                    choices=list(CLASS_SETS),
                    help="which figure sets to draw (default: both)")
    ap.add_argument("--classes", nargs="+", default=None,
                    help="explicit list of phase classes, overriding --sets "
                         "(e.g. --classes SC ST TC)")
    ap.add_argument("--kinds", nargs="+", default=["genesis", "track"],
                    choices=["genesis", "track"],
                    help="genesis point only, whole life, or both (default)")
    ap.add_argument("--modes", nargs="+", default=["anomaly", "absolute"],
                    choices=["anomaly", "absolute"],
                    help="panel convention (default: both)")
    ap.add_argument("--epall", default="clustered",
                    choices=["clustered", "catalogue"],
                    help="EPALL = EP1+EP2+EP3 (default, consistent with step 8) "
                         "or the whole 6,776-cyclone catalogue")
    args = ap.parse_args()
    sys.exit(main(args.sets, args.modes, args.kinds, args.classes, args.epall))
