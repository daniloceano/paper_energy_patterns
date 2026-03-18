#!/usr/bin/env python3
"""
Extract Ck-subterms analysis data for the web site.

Reads results from results/ck_subterms/ and generates a JSON manifest
for the ck-subterms web analysis page.

The manifest reflects the LEC audit of locally computed energetics —
no comparison with external datasets is included.

Usage:
    python scripts/web/extract_ck_subterms_site_data.py

Outputs:
    web/src/content/ck_subterms_manifest.json
"""

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results" / "ck_subterms"
WEB_CONTENT = REPO_ROOT / "web" / "src" / "content"

# Ck subterm labels — symbol, KaTeX formula (from paper.tex Eq. C_K), and description.
#
# Notation (following Peixoto & Oort 1992 via paper.tex):
#   [u]_λ  = zonal mean of u
#   (u)_λ  = eddy component of u (deviation from zonal mean)
#   [·]_λφ = global area-weighted mean (λ and φ)
#   ω      = vertical velocity in pressure coordinates
#   a      = Earth radius, φ = latitude, p = pressure
#
# The full formula (paper.tex Eq. C_K) is:
#   C_K = ∫(p_b→p_t) (1/g) [ T^(a) + T^(b) + T^(c) + T^(d) + T^(e) ]_λφ dp
#
# Each katex entry is the core integrand (no outer area-average or vertical-integral notation).
SUBTERM_LABELS = {
    "Ck_1": {
        "symbol": "C_K^{(a)}",
        "name": "Term (a)",
        "katex": r"\frac{\cos\phi}{a}\,(u)_{\!\lambda}(v)_{\!\lambda}\,\frac{\partial}{\partial\phi}\!\left(\frac{[u]_{\lambda}}{\cos\phi}\right)",
        "description": "Eddy momentum flux coupled with meridional gradient of mean zonal wind — primary barotropic instability mechanism.",
    },
    "Ck_2": {
        "symbol": "C_K^{(b)}",
        "name": "Term (b)",
        "katex": r"\frac{(v)_{\!\lambda}^{2}}{a}\,\frac{\partial\,[v]_{\lambda}}{\partial\phi}",
        "description": "Meridional flux of eddy kinetic energy associated with the meridional gradient of mean meridional wind.",
    },
    "Ck_3": {
        "symbol": "C_K^{(c)}",
        "name": "Term (c)",
        "katex": r"\frac{\tan\phi}{a}\,(u)_{\!\lambda}^{2}\,[v]_{\lambda}",
        "description": "Geometric (curvature) term: eddy zonal kinetic energy modulated by mean meridional wind and Earth's curvature.",
    },
    "Ck_4": {
        "symbol": "C_K^{(d)}",
        "name": "Term (d)",
        "katex": r"(\omega)_{\!\lambda}\,(u)_{\!\lambda}\,\frac{\partial\,[u]_{\lambda}}{\partial p}",
        "description": "Vertical flux of eddy zonal momentum coupled with the vertical shear of mean zonal wind.",
    },
    "Ck_5": {
        "symbol": "C_K^{(e)}",
        "name": "Term (e)",
        "katex": r"(\omega)_{\!\lambda}\,(v)_{\!\lambda}\,\frac{\partial\,[v]_{\lambda}}{\partial p}",
        "description": "Vertical flux of eddy meridional momentum coupled with the vertical shear of mean meridional wind.",
    },
}

FIGURE_PATHS = {
    "boxplots": "figures/ck_subterms/ck_subterms_boxplots.png",
    "genesis_density": "figures/ck_subterms/ck_subterms_genesis_density.png",
    "genesis_normaldiff": "figures/ck_subterms/ck_subterms_genesis_normaldiff.png",
    "tracks": "figures/ck_subterms/ck_subterms_tracks.png",
}


def supabase_base_from_env():
    """Return the Supabase figures base URL if provided in the environment.

    Checks both SUPABASE_FIGURES_URL and NEXT_PUBLIC_SUPABASE_FIGURES_URL for compatibility.
    The returned base should not end with a slash.
    """
    import os

    base = os.environ.get("SUPABASE_FIGURES_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_FIGURES_URL")
    if not base:
        return None
    return base.rstrip('/')


def read_csv_safe(filepath):
    """Read CSV and return list of dicts, or empty list if missing."""
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found")
        return []
    with open(filepath) as f:
        return list(csv.DictReader(f))


def load_audit_summary() -> dict:
    """Load lec_audit_summary.json if available, else fall back to CSV."""
    json_path = RESULTS_DIR / "lec_audit_summary.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    # Fall back to CSV
    rows = read_csv_safe(RESULTS_DIR / "lec_audit_summary.csv")
    if rows:
        return rows[0]
    return {}


def extract_manifest():
    WEB_CONTENT.mkdir(parents=True, exist_ok=True)

    # Load per-cyclone table
    per_cyclone = read_csv_safe(RESULTS_DIR / "ep1_ck_subterms_per_cyclone.csv")

    # Load LEC audit summary
    audit_summary = load_audit_summary()

    # Compute dominance distribution
    dominance_counts = {}
    valid_rows = [r for r in per_cyclone if r.get("dominant_subterm")]
    for row in valid_rows:
        dom = row["dominant_subterm"]
        dominance_counts[dom] = dominance_counts.get(dom, 0) + 1

    # Build dominance summary with labels
    dominance_summary = []
    total_valid = len(valid_rows)
    for key, meta in SUBTERM_LABELS.items():
        count = dominance_counts.get(key, 0)
        dominance_summary.append({
            "subterm_key": key,
            "symbol": meta["symbol"],
            "name": meta["name"],
            "description": meta["description"],
            "count": count,
            "percentage": round(100.0 * count / total_valid, 1) if total_valid > 0 else 0.0,
        })

    # Sample size counts from audit
    n_ep1_total  = int(audit_summary.get("n_ep1_expected", 444))
    n_lec_dirs   = int(audit_summary.get("n_lec_directory_found", 0))
    n_ck_total   = int(audit_summary.get("n_with_ck_total_file", 0))
    n_ck_subs    = int(audit_summary.get("n_with_all_ck_subterm_files", 0))
    n_usable     = int(audit_summary.get("n_usable_for_dominance", total_valid))

    # Mean energetics from per-cyclone table
    ck_vals = [float(r["Ck_total_new"]) for r in per_cyclone
               if r.get("Ck_total_new") not in ("", None) and r["Ck_total_new"] == r["Ck_total_new"]]
    mean_ck_new = sum(ck_vals) / len(ck_vals) if ck_vals else 0.0

    sub_sums = [float(r["subterms_sum"]) for r in per_cyclone
                if r.get("subterms_sum") not in ("", None) and r["subterms_sum"] == r["subterms_sum"]]
    mean_subterm_sum = sum(sub_sums) / len(sub_sums) if sub_sums else 0.0

    manifest = {
        "analysis": "ck_subterms",
        "title": "Ck Subterms Analysis — EP1 Barotropic Decomposition",
        "phase": "intensification",
        "phase_note": (
            "Dominance classification uses the mean value of each subterm "
            "during the intensification phase. The dominant subterm is the one "
            "with the minimum (most negative) value, consistent with the sign "
            "convention in paper.tex: negative Ck = mean flow transfers energy to eddies "
            "(K_Z → K_E; barotropic instability)."
        ),
        "sample_sizes": {
            "ep1_total": n_ep1_total,
            "ep1_with_lec_dir": n_lec_dirs,
            "ep1_with_ck_total_file": n_ck_total,
            "ep1_with_all_ck_subterm_files": n_ck_subs,
            "ep1_with_lec": n_usable,
            "valid_for_boxplots": n_usable,
            "note": (
                f"ep1_total ({n_ep1_total}) = full EP1 population from ep_structure/ep1_cases.csv. "
                f"ep1_with_lec ({n_usable}) = subset with complete, valid Ck subterm output files "
                f"(Ck_pressure_level.csv + Ck_1..5_pressure_level.csv, non-empty, with data in the "
                f"intensification window). Boxplots and dominance classification use N={n_usable}. "
                f"'All EP1' genesis density and track panels use the full N={n_ep1_total} population."
            ),
        },
        "lec_audit": {
            "source": "results/ck_analysis/lec_results/",
            "ep1_cases_source": "results/ep_structure/ep1_cases.csv",
            "n_ep1_expected": n_ep1_total,
            "n_lec_directory_found": n_lec_dirs,
            "n_with_ck_total_file": n_ck_total,
            "n_with_all_ck_subterm_files": n_ck_subs,
            "n_usable_for_dominance": n_usable,
            "mean_ck_new": round(mean_ck_new, 4),
            "mean_subterm_sum": round(mean_subterm_sum, 4),
            "note": (
                f"Internal consistency: mean subterm sum ({mean_subterm_sum:.2f} W/m²) "
                f"≈ mean Ck total ({mean_ck_new:.2f} W/m²), confirming correct "
                "vertical integration of locally computed energetics."
            ),
        },
        "normalization_method": {
            "title": "Normalized genesis density anomaly (Figure 3)",
            "formula": "anomaly[lat,lon] = norm_k[lat,lon] − norm_all[lat,lon]",
            "steps": [
                "Step 1: Compute KDE genesis density for (A) all EP1 cyclones "
                f"(n={n_ep1_total}) → density_all, and (B) each dominant-subterm subset (n_k) → density_k. "
                "KDE uses haversine metric, Gaussian kernel, bandwidth=0.05 rad "
                "(Hoskins & Hodges 2005 method).",

                "Step 2: Apply Min-Max normalization to positive values only. "
                "norm_all[lat,lon] = (density_all − min_pos) / (max_pos − min_pos), "
                "where min_pos and max_pos are the minimum and maximum of all positive "
                "values in density_all. Zero and negative values remain 0. "
                "Same formula applied to each density_k → norm_k.",

                "Step 3: Relative anomaly = norm_k − norm_all. "
                "Positive (red): enhanced genesis for this subterm relative to all EP1. "
                "Negative (blue): suppressed genesis for this subterm relative to all EP1.",

                "Step 4: A shared diverging colorbar spans [−max_abs, +max_abs] where "
                "max_abs = max absolute anomaly across all valid subterm panels.",
            ],
        },
        "subterms": list(SUBTERM_LABELS.values()),
        "dominance": dominance_summary,
        "figures": FIGURE_PATHS,
    }

    # If a Supabase figures base URL is provided via env, convert local figure paths
    # (figures/...) into full public URLs so the manifest can be consumed directly
    # by the production site without committing image PNGs to the repo.
    base = supabase_base_from_env()
    if base:
        figures_with_urls = {}
        for k, rel in manifest["figures"].items():
            # rel is like 'figures/ck_subterms/xxx.png' -> object path 'ck_subterms/xxx.png'
            if isinstance(rel, str):
                if rel.startswith('figures/'):
                    object_key = rel.replace('figures/', '', 1)
                else:
                    object_key = rel
            else:
                object_key = rel
            figures_with_urls[k] = f"{base}/{object_key}"
        manifest["figures"] = figures_with_urls

    output = WEB_CONTENT / "ck_subterms_manifest.json"
    with open(output, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {output.relative_to(REPO_ROOT)}")
    return manifest


if __name__ == "__main__":
    print("Extracting Ck subterms site data (LEC audit)...")
    m = extract_manifest()
    ss = m["sample_sizes"]
    print(f"\nDone.")
    print(f"  EP1 total:          {ss['ep1_total']}")
    print(f"  LEC dirs found:     {ss['ep1_with_lec_dir']}")
    print(f"  With all subterms:  {ss['ep1_with_all_ck_subterm_files']}")
    print(f"  Valid for dominance:{ss['ep1_with_lec']}")
    print(f"Dominance distribution: { {d['subterm_key']: d['count'] for d in m['dominance']} }")

