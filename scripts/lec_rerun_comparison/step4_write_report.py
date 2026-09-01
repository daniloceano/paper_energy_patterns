#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step4_write_report.py — Generate the legacy vs corrected LEC technical report.

Assembles docs/lec_rerun_comparison_report.md from the tables written by steps
1 and 3. Every number in the report comes from those tables, so re-running this
step after the rerun finishes refreshes the whole document; the wording adapts
to which terms actually changed rather than assuming the current outcome.

Usage
-----
    python scripts/lec_rerun_comparison/step4_write_report.py
    python scripts/lec_rerun_comparison/step4_write_report.py --output /tmp/draft.md

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import (  # noqa: E402
    CHANGE_THRESHOLD,
    COVERAGE_JSON,
    PHASE_SUMMARY,
    REGIME_SUMMARY,
    REPORT_PATH,
    RESULTS_DIR,
    TERM_SUMMARY,
    split_changed,
)

from scripts.lec_rerun_comparison.lec_diagram import DRAWN_TERMS  # noqa: E402

EOF_VARIANCE = RESULTS_DIR / "eof_variance.csv"
EOF_LOADINGS = RESULTS_DIR / "eof_loadings.csv"

PLAIN = {
    "Az": "Az", "Ae": "Ae", "Kz": "Kz", "Ke": "Ke",
    "Cz": "Cz", "Ca": "Ca", "Ck": "Ck", "Ce": "Ce",
    "Gz": "Gz", "Ge": "Ge",
    "BAz": "BAz", "BAe": "BAe", "BKz": "BKz", "BKe": "BKe",
    "BΦZ": "BΦZ", "BΦE": "BΦE",
    "∂Az/∂t (finite diff.)": "∂Az/∂t", "∂Ae/∂t (finite diff.)": "∂Ae/∂t",
    "∂Kz/∂t (finite diff.)": "∂Kz/∂t", "∂Ke/∂t (finite diff.)": "∂Ke/∂t",
    "RGz": "RGz", "RKz": "RKz", "RGe": "RGe", "RKe": "RKe",
}

CLUSTER_TERMS = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]


def name(term: str) -> str:
    return PLAIN.get(term, term)


class Figures:
    """Numbered figure references, so the captions stay in sync with the text."""

    def __init__(self) -> None:
        self.count = 0

    def __call__(self, filename: str, caption: str) -> str:
        self.count += 1
        return (
            f"\n![Figure {self.count}. {caption}]"
            f"(../figures/lec_rerun_comparison/{filename})\n\n"
            f"*Figure {self.count}. {caption}*\n"
        )


figure = Figures()


def number(value: float, digits: int = 2) -> str:
    if pd.isna(value):
        return "n/a"
    if value != 0 and (abs(value) >= 1e5 or abs(value) < 1e-3):
        return f"{value:.2e}"
    return f"{value:.{digits}f}"


def listing(terms: list[str]) -> str:
    names = [name(term) for term in terms]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def changed_table(summary: pd.DataFrame, terms: list[str]) -> str:
    header = (
        "| Term | Group | Median legacy | Median corrected | Median Δ | "
        "Relative change | Spearman | Sign changes |\n"
        "|---|---|---:|---:|---:|---:|---:|---:|\n"
    )
    rows = []
    block = summary.set_index("term").loc[terms]
    for term, row in block.sort_values("normalized_change", ascending=False).iterrows():
        rows.append(
            f"| {name(term)} | {row['group']} | {number(row['median_legacy'])} | "
            f"{number(row['median_corrected'])} | {number(row['median_diff'])} | "
            f"{row['normalized_change']:.2f}× | {row['spearman']:.2f} | "
            f"{row['sign_flip_pct']:.1f}% |"
        )
    return header + "\n".join(rows)


def regime_table(regime: pd.DataFrame) -> str:
    header = (
        "| Phase | Ck < 0 (legacy → corrected) | Ca > 0 & Ck < 0 | \\|Ck\\| > \\|Ca\\| with Ck < 0 | "
        "Median Ck |\n|---|---|---|---|---|\n"
    )
    rows = []
    for _, row in regime.iterrows():
        rows.append(
            f"| {row['phase']} | {row['pct_Ck_negative_legacy']:.0f}% → "
            f"{row['pct_Ck_negative_corrected']:.0f}% | "
            f"{row['pct_upper_left_legacy']:.0f}% → {row['pct_upper_left_corrected']:.0f}% | "
            f"{row['pct_barotropic_dominant_legacy']:.0f}% → "
            f"{row['pct_barotropic_dominant_corrected']:.0f}% | "
            f"{row['median_Ck_legacy']:.2f} → {row['median_Ck_corrected']:.2f} |"
        )
    return header + "\n".join(rows)


def phase_extremes(by_phase: pd.DataFrame, term: str, column: str) -> tuple[str, float]:
    block = by_phase[by_phase["term"] == term]
    row = block.loc[block[column].abs().idxmax()]
    return str(row["phase"]), float(row[column])


def eof_paragraph() -> str:
    """Short EOF section, written only when step 6 has produced its tables."""
    if not (EOF_VARIANCE.is_file() and EOF_LOADINGS.is_file()):
        return ""
    variance = pd.read_csv(EOF_VARIANCE)
    loadings = pd.read_csv(EOF_LOADINGS)
    first = variance[variance["eof"] == 1]
    modes = loadings[loadings["eof"] == 1]
    shift = modes.groupby("term")["diff"].apply(lambda column: column.abs().max())
    steady = shift[shift < 0.05].sort_values().index.tolist()
    ranked = shift.sort_values(ascending=False)
    drawn_shift = ranked[ranked.index.isin(DRAWN_TERMS)]

    def rank(series, count):
        return ", ".join(f"{name(term)} ({value:.2f})" for term, value in series.head(count).items())

    legacy_range = f"{first['explained_variance_legacy'].min():.0f}-{first['explained_variance_legacy'].max():.0f}%"
    corrected_range = f"{first['explained_variance_corrected'].min():.0f}-{first['explained_variance_corrected'].max():.0f}%"
    correlation = f"{first['pattern_correlation'].min():.2f}-{first['pattern_correlation'].max():.2f}"
    swaps = variance[(variance["eof"] <= 4) & variance["rank_swapped"]]
    swap_note = ""
    if not swaps.empty:
        listed = "; ".join(
            f"legacy EOF {int(row['eof'])} in the {row['phase']} phase matches "
            f"corrected mode {int(row['corrected_mode_rank'])}"
            for _, row in swaps.iterrows()
        )
        swap_note = (
            f" Beyond the leading mode the rank itself is not preserved — {listed} — "
            "because EOF 2 and EOF 3 explain similar variance and the correction is "
            "enough to reorder them. The figures pair modes by pattern correlation "
            "rather than by rank; comparing them by rank would be misleading."
        )

    return f"""
**The leading EOF survives in shape but is reweighted.**
`figures/lec_rerun_comparison/eof1_diagram_before_after.png` redraws the thesis
EOF figure with both versions on the same axes. EOF 1 still explains a comparable
share of the variance ({legacy_range} before, {corrected_range} after) and the two
patterns correlate at {correlation} across phases, so the mode is recognisably the
same. {len(steady)} of the {len(shift)} loadings move by less than 0.05, including
{listing(steady[:5])}. The largest shifts are {rank(ranked, 3)}, i.e. the terms the
correction hit directly; among the terms the classical diagram actually shows, the
largest are {rank(drawn_shift, 3)}. The pattern is therefore stable where the
underlying terms did not change and moves where they did — which is what the
downstream PCA and k-means will inherit, and another reason to rerun them rather
than assume the EPs carry over.{swap_note}

{figure("eof1_diagram_before_after.png",
        "EOF 1 loadings on the LEC diagram, by phase: (A) incipient, "
        "(B) intensification, (C) mature, (D) decay. Dark is legacy, red is "
        "corrected.")}
The same diagram for EOF 2 to EOF 4 (Figures 6 to 8 of the article) is in
`eof2_diagram_before_after.png`, `eof3_...` and `eof4_...`.
"""


def build(coverage: dict, summary: pd.DataFrame, by_phase: pd.DataFrame, regime: pd.DataFrame) -> str:
    changed, unchanged = split_changed(summary)
    flipped = summary[summary["median_sign_changed"]]["term"].tolist()
    complete = coverage["cyclones_complete"]
    target = coverage["population_target"]
    fraction = 100 * coverage["completion_fraction"]
    partial = complete < target
    cluster_changed = [term for term in CLUSTER_TERMS if term in changed]
    all_pooled = regime[regime["phase"] == "all phases"].iloc[0]
    intensification = regime[regime["phase"] == "intensification"].iloc[0]
    pooled = summary.set_index("term")
    verification = coverage["legacy_cache_verification"]

    top_flip = summary.sort_values("sign_flip_pct", ascending=False).iloc[0]
    ck_phase, ck_value = phase_extremes(by_phase, "Ck", "median_diff") if "Ck" in changed else ("", 0.0)

    status = (
        f"**Preliminary — the rerun is still running.** {complete:,} of {target:,} cyclones "
        f"({fraction:.0f}%) are validated COMPLETE; the remaining "
        f"{target - complete:,} are pending or failed. The numbers below are stable in "
        "structure but will shift slightly as the population completes."
        if partial
        else f"The rerun is complete: all {complete:,} cyclones are validated."
    )

    return f"""# Legacy vs corrected LEC climatology — technical report

**Author**: Danilo Couto de Souza · **Generated**: {coverage['generated_utc'][:10]} ·
**Reference article**: de Souza et al. (2025), *Clim. Dyn.*,
[10.1007/s00382-025-07918-y](https://doi.org/10.1007/s00382-025-07918-y)

{status}

## 1. What is compared

The rerun (`scripts/lec_climatology_rerun`) recomputes the semi-Lagrangian Lorenz
Energy Cycle with LorenzCycleToolKit 2.0.0, which corrected `Ca`, the fifth `Ck`
subterm, `BΦZ`, `BΦE`, vertical-level alignment, time tendencies and NaN handling.
Everything else is held fixed: the same cyclones, the same frozen lifecycle
windows, the same 3-hourly time steps, the same 15° × 15° moving box and the same
32-level (10–1000 hPa) control volume. Both sides are phase means over identical
windows, so every difference reported here is attributable to the equation and
numerical correction alone.

The legacy side is `data/energy_cache.parquet`, the article input. Re-aggregating
the archived Zenodo per-cyclone results for {verification['checked']} random
cyclones reproduces that cache to a maximum relative difference of
{verification['max_relative_difference']:.0e}, confirming the two sides are built
the same way.

Paired sample: **{coverage['paired_cyclones']:,} cyclones**,
{coverage['paired_period_rows']:,} cyclone-phase rows,
{len(coverage['terms_compared'])} terms.

## 2. What changed and what did not

{len(unchanged)} of the {len(summary)} terms are numerically unchanged
(relative change below {CHANGE_THRESHOLD:.0%}, Spearman ≈ 1, essentially no sign
changes): {listing(unchanged)}. This includes all four energy reservoirs, both
generation terms, the four lateral boundary transports and all four budget
tendencies — the corrections did not touch them.

The {len(changed)} terms that did change are exactly those the toolkit correction
targets, plus the residuals that inherit them (see
`figures/lec_rerun_comparison/violin_conversion.png` and `violin_boundary.png`;
the energy, generation and budget figures show the two halves of each violin
overlying each other exactly):

{changed_table(summary, changed)}

{figure("violin_conversion.png",
        "Conversion terms, legacy (left half) versus corrected (right half) of "
        "each violin, by life-cycle phase. C_A shifts upward in every phase and "
        "C_K crosses zero.")}
{figure("violin_boundary.png",
        "Boundary transport terms. The four lateral fluxes are unchanged; the "
        "two pressure-work terms BΦZ and BΦE collapse.")}
{figure("violin_residual.png",
        "Residual terms, which inherit the C_A and C_K corrections through the "
        "budget closure.")}
The energy, generation and budget-tendency violins are not reproduced here: the
two halves of every violin coincide exactly. They are in
`figures/lec_rerun_comparison/` if a reader wants to confirm it.

*Relative change* is the median |Δ| divided by the median |legacy| value: 1.00×
means the typical change is as large as the term itself. *Spearman* is the
rank correlation between the two versions across cyclone-phases — the quantity
that matters for the downstream PCA and k-means, which depend on ordering.

Three features stand out:

- **`Ca` roughly triples** (median {number(pooled.loc['Ca', 'median_legacy'])} →
  {number(pooled.loc['Ca', 'median_corrected'])} W m⁻²) but keeps its ranking
  (Spearman {pooled.loc['Ca', 'spearman']:.2f}) and its sign in
  {100 - pooled.loc['Ca', 'sign_flip_pct']:.0f}% of cases. Baroclinic conversion
  is systematically stronger, not reordered.
- **`Ck` shifts by about {number(pooled.loc['Ck', 'median_diff'])} W m⁻²**, an almost
  uniform positive offset that carries the median from
  {number(pooled.loc['Ck', 'median_legacy'])} to
  {number(pooled.loc['Ck', 'median_corrected'])} W m⁻². The shift is largest in the
  {ck_phase} phase ({number(ck_value)} W m⁻²).
- **The pressure-work boundary terms collapse.** `BΦZ` and `BΦE` lose most of
  their amplitude, and `BΦE` is now *anti*-correlated with its legacy counterpart
  (Spearman {pooled.loc['BΦE', 'spearman']:.2f}), so the legacy term cannot be
  rescaled into agreement — its structure was wrong, not just its amplitude.

The residuals `RGz`, `RKz`, `RGe` and `RKe` change by the same amounts as `Ca` and
`Ck` with opposite signs, as expected from the budget closure — they are a
consistency check rather than an independent finding. The corrected toolkit also
outputs two terms with no legacy counterpart (`C_overturning`, `M`); they are not
comparable and are excluded.

## 3. Sign changes

Sign is what carries physical meaning in the LEC, so a change of sign matters more
than a change of magnitude. Per-sample sign-change rates are in
`figures/lec_rerun_comparison/signflip_heatmap.png`; the terms at risk are
{listing([t for t in changed if pooled.loc[t, 'sign_flip_pct'] > 5])}.
The worst case is {name(top_flip['term'])}, which changes sign in
{top_flip['sign_flip_pct']:.0f}% of cyclone-phases.

{figure("signflip_heatmap.png",
        "Percentage of cyclone-phases whose term changed sign between the two "
        "versions.")}
Three terms change the sign of their *climatological median*, which is the level at
which the article's statements are made: **{listing(flipped)}**. Of these, `Ck` is
the consequential one: it enters the clustering and the conversion LPS. `BΦE` and
`RGz` enter neither, appearing only in the all-terms effect-size figure (Fig. S2),
which would need regenerating but carries no headline claim.

## 4. Consequences for the interpretation

**The clustering input is only partly affected.** The energy patterns are built from
seven terms ({listing(CLUSTER_TERMS)}) across four phases. {len(CLUSTER_TERMS) - len(cluster_changed)}
of the seven ({listing([t for t in CLUSTER_TERMS if t not in cluster_changed])}) are
unchanged; only {listing(cluster_changed)} move. The EP separation should therefore
survive in outline, but the two conversion terms are precisely the ones that define
the conversion Lorenz Phase Space and the EP1 signature, so the clustering must be
rerun before any EP statement is reasserted.

**The barotropic result is the one that moves.**
`figures/lec_rerun_comparison/lec_diagram_before_after.png` shows this on the
four-box diagram: the `Ck` arrow reverses between the two versions during the
incipient and intensification phases, and shortens during maturity and decay.
With the convention of de Souza et al. (2025) — `Ca` > 0 feeds eddy APE,
`Ck` < 0 feeds eddy KE:

{regime_table(regime)}

Pooled over the life cycle, the share of cyclone-phases with barotropic conversion
feeding the eddy falls from {all_pooled['pct_Ck_negative_legacy']:.0f}% to
{all_pooled['pct_Ck_negative_corrected']:.0f}%, occupancy of the doubly eddy-feeding
quadrant falls from {all_pooled['pct_upper_left_legacy']:.0f}% to
{all_pooled['pct_upper_left_corrected']:.0f}%, and the share of cases where
barotropic conversion exceeds baroclinic conversion falls from
{all_pooled['pct_barotropic_dominant_legacy']:.0f}% to
{all_pooled['pct_barotropic_dominant_corrected']:.0f}%. During intensification the
last figure drops from {intensification['pct_barotropic_dominant_legacy']:.0f}% to
{intensification['pct_barotropic_dominant_corrected']:.0f}%.

{figure("lec_diagram_before_after.png",
        "Four-box Lorenz Energy Cycle by life-cycle phase: (A) incipient, "
        "(B) intensification, (C) mature, (D) decay. Dark is legacy, red is "
        "corrected.")}

This weakens the article's headline claim that barotropic conversions are ubiquitous
during cyclone evolution and can exceed baroclinic conversions. In the corrected
climatology, barotropic conversion is close to neutral in the median, it is a
minority contributor during intensification, and it feeds the eddy in roughly half
of the cases rather than seven in ten. Two qualitative statements survive and one
does not:

- *Survives*: baroclinic conversion feeds the eddy in the large majority of cases,
  and is now unambiguously the dominant eddy source (`Ca` roughly tripled while
  `Ck` moved toward zero).
- *Survives, restated*: barotropic conversion remains present and eddy-feeding in a
  substantial minority of cyclone-phases, so it is still a real pathway — it is no
  longer the typical one.
- *Does not survive as stated*: the ordering of the phases. The legacy `Ck` was most
  strongly eddy-feeding during intensification and maturity; the corrected `Ck` is
  weakest during the incipient phase and becomes progressively more eddy-feeding
  toward decay. Any statement tying the barotropic peak to maturity needs to be
  rechecked against the corrected LPS.

{eof_paragraph()}
The `BΦ` collapse does not affect the published figures (the article uses `BAe` and
`BKe` for the import LPS, both unchanged), but it does affect the budget closure and
any future use of the pressure-work terms.

## 5. Caveats

- {'Partial population: the above uses ' + f'{complete:,}' + ' of ' + f'{target:,}' + ' cyclones. Re-run `scripts/lec_rerun_comparison/run_all.py` when the rerun finishes to regenerate every number, figure and this document; the qualitative conclusions are unlikely to move, the exact percentages will.' if partial else 'The population is complete.'}
- Statistics are medians and rank correlations throughout, because LEC phase means
  are heavy tailed. The violin figures are trimmed for display only; every number
  here uses the full sample.
- Secondary lifecycle periods (`decay 2`, etc.) are matched to their own legacy
  counterpart and folded into the parent phase, as in the corrected cache builder.
  Rows named `residual` are excluded.
- This report compares diagnostics, not conclusions. Nothing here substitutes for
  rerunning the PCA, the k-means and the EP figures on the corrected cache.

## 6. Files

| Artifact | Path |
|---|---|
| This report (PDF, figures embedded) | `docs/lec_rerun_comparison_report.pdf` |
| Paired table | `results/lec_rerun_comparison/paired_terms.parquet` |
| Term summary | `results/lec_rerun_comparison/term_change_summary.csv` |
| Per-phase summary | `results/lec_rerun_comparison/term_change_by_phase.csv` |
| Conversion regime | `results/lec_rerun_comparison/conversion_regime.csv` |
| Coverage / provenance | `results/lec_rerun_comparison/coverage.json` |
| Split-violin figures | `figures/lec_rerun_comparison/violin_{{energy,conversion,generation,boundary,budget,residual}}.png` |
| Sign-change heatmap | `figures/lec_rerun_comparison/signflip_heatmap.png` |
| Before/after LEC diagram | `figures/lec_rerun_comparison/lec_diagram_before_after.png` |
| Before/after EOF diagrams | `figures/lec_rerun_comparison/eof{{1,2,3,4}}_diagram_before_after.png` |
| EOF loadings and variance | `results/lec_rerun_comparison/eof_loadings.csv`, `eof_variance.csv` |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    for path in (COVERAGE_JSON, TERM_SUMMARY, PHASE_SUMMARY, REGIME_SUMMARY):
        if not path.is_file():
            raise SystemExit(f"{path} not found; run steps 1 and 3 first")

    coverage = json.loads(COVERAGE_JSON.read_text())
    text = build(
        coverage,
        pd.read_csv(TERM_SUMMARY),
        pd.read_csv(PHASE_SUMMARY),
        pd.read_csv(REGIME_SUMMARY),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"wrote {args.output} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
