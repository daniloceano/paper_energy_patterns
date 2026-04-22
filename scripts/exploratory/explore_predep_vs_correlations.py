"""
Exploratory figure: PREDEP vs Pearson vs Spearman comparison scatterplots.

Loads all step7 PREDEP chunk results (absolute + anomaly) and plots three
side-by-side scatterplots:
  1. Pearson r  vs  Spearman ρ
  2. Pearson r  vs  PREDEP
  3. Spearman ρ vs  PREDEP

Each subplot shows a 1:1 reference line. Points are coloured by field type
(absolute vs anomaly).

Output: figures/exploratory/explore_predep_vs_correlations.png
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── project root ──────────────────────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

RESULTS_DIR = project_root / "results" / "lec_field_dependence"
FIGURES_DIR = project_root / "figures" / "exploratory"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── load data ─────────────────────────────────────────────────────────────────
def load_chunks(field_type: str) -> pd.DataFrame:
    chunks = sorted(RESULTS_DIR.glob(f"step7_predep_{field_type}_chunk*.csv"))
    if not chunks:
        raise FileNotFoundError(f"No step7 chunks found for field_type={field_type}")
    return pd.concat([pd.read_csv(c) for c in chunks], ignore_index=True)

df_abs = load_chunks("absolute")
df_abs["field_type"] = "absolute"

df_anom = load_chunks("anomaly")
df_anom["field_type"] = "anomaly"

df = pd.concat([df_abs, df_anom], ignore_index=True)

# Use absolute value of Pearson r and Spearman ρ for a fair comparison with
# PREDEP (which is non-negative).  Raw signed values are also kept.
df["pearson_abs"] = df["pearson_r"].abs()
df["spearman_abs"] = df["spearman_rho"].abs()

print(f"Total rows: {len(df)}  (absolute: {len(df_abs)}, anomaly: {len(df_anom)})")
print(df[["predep", "pearson_r", "spearman_rho"]].describe())

# ── colours ───────────────────────────────────────────────────────────────────
COLORS = {"absolute": "#2166ac", "anomaly": "#d6604d"}
ALPHA = 0.25
SIZE = 8

# ── figure ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

panels = [
    ("pearson_r", "spearman_rho", "Pearson $r$", "Spearman $\\rho$"),
    ("pearson_r", "predep",       "Pearson $r$", "PREDEP"),
    ("spearman_rho", "predep",    "Spearman $\\rho$", "PREDEP"),
]

for ax, (xcol, ycol, xlabel, ylabel) in zip(axes, panels):
    for ftype, color in COLORS.items():
        sub = df[df["field_type"] == ftype]
        ax.scatter(
            sub[xcol], sub[ycol],
            c=color, alpha=ALPHA, s=SIZE,
            label=ftype, rasterized=True,
        )

    # 1:1 line spanning the full data range
    all_vals = pd.concat([df[xcol], df[ycol]])
    lim_min, lim_max = all_vals.min(), all_vals.max()
    margin = 0.05 * (lim_max - lim_min)
    lims = (lim_min - margin, lim_max + margin)
    ax.plot(lims, lims, "k--", lw=1.0, label="1:1")
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_aspect("equal")
    ax.legend(fontsize=9, markerscale=2)

fig.suptitle(
    "Pearson / Spearman / PREDEP comparison — all EP × field × feature combinations",
    fontsize=11, y=1.01,
)
fig.tight_layout()

out = FIGURES_DIR / "explore_predep_vs_correlations.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nFigure saved → {out}")
plt.close(fig)
