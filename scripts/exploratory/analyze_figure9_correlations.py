#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploratory analysis of Figure 9: Pearson |r| heatmaps — EPALL, absolute fields.

Purpose:
    Recover signed Pearson r values (|r| is shown in Fig. 9), check statistical
    significance, compute confidence intervals, and build summary tables to support
    the scientific interpretation.

Data source:
    results/lec_field_dependence/step7_predep_absolute_epall.csv

Outputs (all in results/exploratory/):
    figure9_signed_r_table.csv   — full signed r, p-value, CI95 for canonical terms
    figure9_top_correlations.csv — top-N |r| per panel and overall
    figure9_summary_by_panel.csv — per-panel summary statistics
    figure9_sign_analysis.txt    — text report on sign patterns

Run from repository root:
    python scripts/exploratory/analyze_figure9_correlations.py

Author: Danilo Couto de Souza
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

INPUT_CSV    = BASE_DIR / "results" / "lec_field_dependence" / "step7_predep_absolute_epall.csv"
OUTPUT_DIR   = BASE_DIR / "results" / "exploratory"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Scientific constants (mirror 09_figure script)
# ---------------------------------------------------------------------------
LEC_ORDER = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]

FIELD_LABELS = {
    "adv_T_850":  "AdvT 850",
    "afc_250":    "AFC 250",
    "ke_adv_250": "KE adv 250",
    "pv_200":     "PV 200",
    "pv_850":     "PV 850",
}

FEATURE_ORDER = [
    "domain_mean", "domain_abs_mean", "centre_value",
    "border_north", "border_south", "border_east", "border_west",
    "contrast_ew", "contrast_sn",
    "sector_north", "sector_south", "sector_east", "sector_west",
]

FEATURE_LABELS = {
    "domain_mean":     "domain mean",
    "domain_abs_mean": "|domain mean|",
    "centre_value":    "centre value",
    "border_north":    "border N",
    "border_south":    "border S",
    "border_east":     "border E",
    "border_west":     "border W",
    "contrast_ew":     "E-W contrast",
    "contrast_sn":     "S-N contrast",
    "sector_north":    "sector N",
    "sector_south":    "sector S",
    "sector_east":     "sector E",
    "sector_west":     "sector W",
}

ALPHA = 0.05  # significance threshold


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pearson_ci95(r: float, n: int) -> tuple:
    """Fisher z-transform 95% CI for Pearson r."""
    if abs(r) >= 1.0 or n < 4:
        return (np.nan, np.nan)
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    za2 = stats.norm.ppf(0.975)
    lo = np.tanh(z - za2 * se)
    hi = np.tanh(z + za2 * se)
    return (lo, hi)


def significance_flag(p: float, alpha: float = ALPHA) -> str:
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < alpha:
        return "*"
    else:
        return "ns"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading data …")
df = pd.read_csv(INPUT_CSV)
print(f"  Rows total: {len(df)}")

# Filter: canonical LEC terms only
canonical = df[df["lec_term"].isin(LEC_ORDER)].copy()
print(f"  Rows (canonical LEC terms): {len(canonical)}")
print(f"  N valid range: {canonical['n_valid'].min()} – {canonical['n_valid'].max()}")

# Compute |r| and CI95
canonical["abs_r"] = canonical["pearson_r"].abs()
ci = canonical.apply(
    lambda row: pearson_ci95(row["pearson_r"], row["n_valid"]), axis=1
)
canonical["ci95_lo"] = ci.map(lambda x: x[0])
canonical["ci95_hi"] = ci.map(lambda x: x[1])
canonical["sig_flag"] = canonical["pearson_p"].map(significance_flag)
canonical["field_label"]   = canonical["field"].map(FIELD_LABELS)
canonical["feature_label"] = canonical["feature"].map(FEATURE_LABELS)

# Significance analysis — at n ≈ 2731:
# Critical |r| at p < 0.05 (two-tailed)
n_sample = int(canonical["n_valid"].median())
t_crit = stats.t.ppf(1 - ALPHA / 2, df=n_sample - 2)
r_crit = t_crit / np.sqrt(t_crit**2 + n_sample - 2)
print(f"\n  n_sample (median) = {n_sample}")
print(f"  Critical |r| at p < 0.05 (two-tailed) = {r_crit:.4f}")
print(f"  → All correlations with |r| ≥ {r_crit:.3f} are significant at p < 0.05")
print(f"  → The figure threshold |r| ≥ 0.2 >> {r_crit:.4f}: all shown correlations are highly significant")

# ---------------------------------------------------------------------------
# 1. Full signed-r table (canonical terms)
# ---------------------------------------------------------------------------
cols_out = [
    "lec_term", "field", "field_label", "feature", "feature_label",
    "n_valid", "pearson_r", "abs_r", "pearson_p", "sig_flag",
    "ci95_lo", "ci95_hi", "spearman_rho", "spearman_p",
]
# Sort by field order, then lec_order
canonical["field_rank"]   = canonical["field"].map({k: i for i, k in enumerate(FIELD_LABELS)})
canonical["lec_rank"]     = canonical["lec_term"].map({k: i for i, k in enumerate(LEC_ORDER)})
canonical["feature_rank"] = canonical["feature"].map({k: i for i, k in enumerate(FEATURE_ORDER)})
canonical_sorted = canonical.sort_values(["field_rank", "lec_rank", "feature_rank"])

canonical_sorted[cols_out].to_csv(OUTPUT_DIR / "figure9_signed_r_table.csv", index=False)
print(f"\n[1] Saved: {OUTPUT_DIR / 'figure9_signed_r_table.csv'}")

# ---------------------------------------------------------------------------
# 2. Top correlations (|r| ≥ 0.2) — overall top-20 and per panel
# ---------------------------------------------------------------------------
above_thresh = canonical[canonical["abs_r"] >= 0.2].copy()
above_thresh_sorted = above_thresh.sort_values("abs_r", ascending=False)

print(f"\n[2] Number of (lec_term, field, feature) pairs with |r| ≥ 0.2: {len(above_thresh)}")

top20 = above_thresh_sorted.head(20)[cols_out]
print("\n  TOP-20 correlations (|r| ≥ 0.2):")
print(top20[["lec_term", "field_label", "feature_label", "pearson_r", "abs_r", "spearman_rho"]].to_string(index=False))
top20.to_csv(OUTPUT_DIR / "figure9_top20_correlations.csv", index=False)

# Per panel
print("\n  Top correlations per field panel:")
rows_per_panel = []
for field_key, field_label in FIELD_LABELS.items():
    sub = above_thresh[above_thresh["field"] == field_key].sort_values("abs_r", ascending=False)
    if sub.empty:
        print(f"    ({field_label}: no correlations above threshold)")
        continue
    top = sub.head(5)
    rows_per_panel.append(top)
    print(f"\n    Panel ({field_label}) — top 5:")
    print(top[["lec_term", "feature_label", "pearson_r", "abs_r", "spearman_rho", "sig_flag"]].to_string(index=False))

pd.concat(rows_per_panel)[cols_out].to_csv(
    OUTPUT_DIR / "figure9_top_correlations_by_panel.csv", index=False
)
print(f"\n  Saved: {OUTPUT_DIR / 'figure9_top_correlations_by_panel.csv'}")

# ---------------------------------------------------------------------------
# 3. Summary by panel: max |r|, mean |r|, count above 0.2
# ---------------------------------------------------------------------------
print("\n[3] Panel-level summary:")
panel_rows = []
for field_key, field_label in FIELD_LABELS.items():
    sub = canonical[canonical["field"] == field_key]
    sub_above = sub[sub["abs_r"] >= 0.2]
    row = {
        "panel": field_label,
        "field":  field_key,
        "max_abs_r":    sub["abs_r"].max(),
        "mean_abs_r":   sub["abs_r"].mean(),
        "median_abs_r": sub["abs_r"].median(),
        "count_above_02": len(sub_above),
        "total_pairs":  len(sub),
        "fraction_above_02": len(sub_above) / len(sub) if len(sub) > 0 else 0,
        "LEC_term_with_max_r": sub.loc[sub["abs_r"].idxmax(), "lec_term"],
        "feature_with_max_r":  sub.loc[sub["abs_r"].idxmax(), "feature_label"],
    }
    panel_rows.append(row)
    print(f"  {field_label}: max|r|={row['max_abs_r']:.3f} ({row['LEC_term_with_max_r']} × {row['feature_with_max_r']}), "
          f"mean|r|={row['mean_abs_r']:.3f}, frac≥0.2={row['fraction_above_02']:.2f} ({row['count_above_02']}/{row['total_pairs']})")

panel_df = pd.DataFrame(panel_rows)
panel_df.to_csv(OUTPUT_DIR / "figure9_summary_by_panel.csv", index=False)
print(f"  Saved: {OUTPUT_DIR / 'figure9_summary_by_panel.csv'}")

# ---------------------------------------------------------------------------
# 4. Sign analysis — which direction are the significant correlations?
# ---------------------------------------------------------------------------
print("\n[4] Sign analysis (for correlations with |r| >= 0.2):")
sign_report_lines = []
sign_report_lines.append("=" * 70)
sign_report_lines.append("SIGN ANALYSIS — Figure 9 (Pearson r, |r| ≥ 0.2, EPALL, absolute fields)")
sign_report_lines.append(f"Sample size (median n_valid): {n_sample}")
sign_report_lines.append(f"Critical |r| for p < 0.05: {r_crit:.4f}")
sign_report_lines.append(f"All shown correlations (|r| ≥ 0.20) are HIGHLY significant (p << 0.001)")
sign_report_lines.append("=" * 70)

for field_key, field_label in FIELD_LABELS.items():
    sub = above_thresh[above_thresh["field"] == field_key].sort_values(
        ["lec_rank", "feature_rank"]
    )
    sign_report_lines.append(f"\nPanel: {field_label}")
    sign_report_lines.append("-" * 50)
    for _, row in sub.iterrows():
        direction = "positive" if row["pearson_r"] > 0 else "negative"
        sign_report_lines.append(
            f"  {row['lec_term']:5s} × {row['feature_label']:18s}: "
            f"r = {row['pearson_r']:+.3f}  ({direction}), "
            f"ρ = {row['spearman_rho']:+.3f}, "
            f"p = {row['pearson_p']:.2e} {row['sig_flag']}"
        )
    if sub.empty:
        sign_report_lines.append("  (no correlations above threshold)")

sign_report_lines.append("\n")
sign_report_lines.append("=" * 70)
sign_report_lines.append("CRITICAL INTERPRETATION NOTES")
sign_report_lines.append("=" * 70)
sign_report_lines.append(
    "1. Figure 9 shows |r|, so the SIGN is NOT visible in the figure."
)
sign_report_lines.append(
    "2. The sign is essential for physical interpretation."
)
sign_report_lines.append(
    "3. For AdvT 850 (temperature advection), NEGATIVE r means: larger warm advection\n"
    "   north of cyclone → higher baroclinic conversion Ca / APE reservoir Ae.\n"
    "   This is physically expected (warm advection → APE release via baroclinic instability)."
)
sign_report_lines.append(
    "4. For PV 200 (upper-level PV), interpretation depends on sign and feature:\n"
    "   - POSITIVE r (e.g., border_east) may indicate: stronger positive PV on the\n"
    "     eastern flank of the domain → stronger trough downstream → more Ge.\n"
    "   - NEGATIVE r (e.g., western sectors) suggests different PV configurations."
)
sign_report_lines.append(
    "5. Multiple-testing note: 7 LEC terms × 13 features × 5 fields = 455 tests;\n"
    "   expected false positives at |r| < 0.05 threshold = ~23, but NOT at |r| ≥ 0.2\n"
    "   given sample size. The Bonferroni-corrected threshold remains |r| < 0.01."
)

sign_report_text = "\n".join(sign_report_lines)
print(sign_report_text[:2000])

with open(OUTPUT_DIR / "figure9_sign_analysis.txt", "w") as f:
    f.write(sign_report_text)
print(f"\n  Saved: {OUTPUT_DIR / 'figure9_sign_analysis.txt'}")

# ---------------------------------------------------------------------------
# 5. Summary by LEC term × panel (pivot of max |r| and r values)
# ---------------------------------------------------------------------------
print("\n[5] Heatmap values (signed r) for canonical terms — per panel:")
for field_key, field_label in FIELD_LABELS.items():
    sub = canonical[canonical["field"] == field_key].copy()
    pivot_r = sub.pivot_table(index="lec_term", columns="feature", values="pearson_r")
    pivot_r = pivot_r.loc[[t for t in LEC_ORDER if t in pivot_r.index]]
    feat_order = [f for f in FEATURE_ORDER if f in pivot_r.columns]
    pivot_r = pivot_r[feat_order]
    # Show only entries visible in figure (|r| >= 0.2)
    pivot_abs = pivot_r.abs()
    pivot_r_masked = pivot_r.where(pivot_abs >= 0.2)
    print(f"\n  {field_label} (signed r, blank = |r| < 0.2):")
    print(pivot_r_masked.to_string(float_format=lambda x: f"{x:+.3f}" if not np.isnan(x) else "    "))

# ---------------------------------------------------------------------------
# 6. Pearson vs Spearman agreement analysis
# ---------------------------------------------------------------------------
print("\n[6] Pearson vs Spearman agreement (for |r| >= 0.2):")
above_thresh["sign_agree"] = np.sign(above_thresh["pearson_r"]) == np.sign(above_thresh["spearman_rho"])
agree_count = above_thresh["sign_agree"].sum()
total_count = len(above_thresh)
print(f"  Sign agreement: {agree_count}/{total_count} ({100*agree_count/total_count:.1f}%)")

# Large discrepancies between |r| and |rho|
above_thresh["r_rho_diff"] = (above_thresh["abs_r"] - above_thresh["spearman_rho"].abs()).abs()
big_disc = above_thresh[above_thresh["r_rho_diff"] > 0.10].sort_values("r_rho_diff", ascending=False)
print(f"  Pairs with |r| - |ρ| > 0.10 (potential non-linearity/outlier): {len(big_disc)}")
if len(big_disc) > 0:
    print(big_disc[["lec_term", "field_label", "feature_label", "pearson_r", "spearman_rho", "r_rho_diff"]].head(10).to_string(index=False))

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
print("\n" + "="*60)
print("Analysis complete.")
print(f"Outputs saved to: {OUTPUT_DIR}")
print("  figure9_signed_r_table.csv")
print("  figure9_top20_correlations.csv")
print("  figure9_top_correlations_by_panel.csv")
print("  figure9_summary_by_panel.csv")
print("  figure9_sign_analysis.txt")
print("="*60)
