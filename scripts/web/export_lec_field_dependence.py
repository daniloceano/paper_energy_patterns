"""
Export LEC field dependence pipeline results for the web application.

Reads pipeline CSV outputs and generates:
  1. JSON data files in web/src/content/
  2. Copies figures to web/public/figures/lec_field_dependence/

Run from project root:
    python scripts/web/export_lec_field_dependence.py
"""

import csv
import json
import shutil
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "lec_field_dependence"
FIGURES_SRC = ROOT / "figures" / "lec_field_dependence"
CONTENT_DST = ROOT / "web" / "src" / "content"
PUBLIC_DATA_DST = ROOT / "web" / "public" / "data"
FIGURES_DST = ROOT / "web" / "public" / "figures" / "lec_field_dependence"

# Canonical LEC terms (used in the clustering)
CANONICAL_TERMS = {"Ca", "Ck", "Ge", "BAe", "BKe", "Ae", "Ke"}

# ── Helpers ──────────────────────────────────────────────────────

def read_csv(path: Path) -> list[dict]:
    """Read CSV, return list of dicts."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(val: str, default=None):
    """Parse float, return default on failure."""
    try:
        v = float(val)
        if v != v:  # NaN check
            return default
        return round(v, 6)
    except (ValueError, TypeError):
        return default


def safe_int(val: str, default=None):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def format_display(field: str, feature: str) -> str:
    """Create human-readable label: 'PV 850 — domain mean'."""
    FIELD_LABELS = {
        "pv_850": "PV 850",
        "pv_200": "PV 200",
        "adv_T_850": "AdvT 850",
        "afc_250": "AFC 250",
        "ke_adv_250": "KE adv 250",
    }
    FEATURE_LABELS = {
        "domain_mean": "domain mean",
        "centre_value": "centre value",
        "border_north": "border N",
        "border_south": "border S",
        "border_east": "border E",
        "border_west": "border W",
        "contrast_ew": "E-W contrast",
        "contrast_sn": "S-N contrast",
        "quadrant_ne": "quadrant NE",
        "quadrant_nw": "quadrant NW",
        "quadrant_se": "quadrant SE",
        "quadrant_sw": "quadrant SW",
        "domain_abs_mean": "domain |mean|",
    }
    fl = FIELD_LABELS.get(field, field)
    ftl = FEATURE_LABELS.get(feature, feature)
    return f"{fl} — {ftl}"


# ── Export functions ─────────────────────────────────────────────

def export_predep() -> list[dict]:
    """Merge all step7 PREDEP chunks + EPALL into a single JSON-friendly list."""
    rows = []

    def _read_file(chunk_file: Path, field_type: str):
        for r in read_csv(chunk_file):
            predep_val = safe_float(r.get("predep"))
            if predep_val is None:
                continue
            rows.append({
                "ep": int(r["ep"]),
                "lec_term": r["lec_term"],
                "field": r["field"],
                "feature": r["feature"],
                "field_type": field_type,
                "n": safe_int(r.get("n_valid")),
                "predep": predep_val,
                "pearson_r": safe_float(r.get("pearson_r")),
                "pearson_p": safe_float(r.get("pearson_p")),
                "spearman_rho": safe_float(r.get("spearman_rho")),
                "spearman_p": safe_float(r.get("spearman_p")),
                "display": format_display(
                    r["field"].replace("_anom_epall", ""),
                    r["feature"]
                ),
                "is_canonical": r["lec_term"] in CANONICAL_TERMS,
            })

    for chunk_file in sorted(RESULTS.glob("step7_predep_*_chunk*.csv")):
        field_type = "absolute" if "_absolute_" in chunk_file.name else "anomaly"
        _read_file(chunk_file, field_type)

    # EPALL files (ep=0, all cyclones pooled)
    for ftype in ("absolute", "anomaly"):
        epall_file = RESULTS / f"step7_predep_{ftype}_epall.csv"
        if epall_file.exists():
            _read_file(epall_file, ftype)

    print(f"  PREDEP: {len(rows)} rows")
    return rows


def export_significance() -> list[dict]:
    """Export step7b diagnostic table."""
    rows = []
    for r in read_csv(RESULTS / "step7b_diagnostic_table.csv"):
        rows.append({
            "variable": r["variable"],
            "display_name": r.get("display_name", r["variable"]),
            "var_type": r["var_type"],
            "field_origin": r.get("field_origin", ""),
            "field_type": r.get("field_type", ""),
            "n_ep1": safe_int(r.get("n_EP1")),
            "n_ep2": safe_int(r.get("n_EP2")),
            "n_ep3": safe_int(r.get("n_EP3")),
            "global_test": r.get("global_test", ""),
            "global_stat": safe_float(r.get("global_stat")),
            "global_p": safe_float(r.get("global_p_adjusted")),
            "effect_size_name": r.get("effect_size_name", ""),
            "effect_size": safe_float(r.get("effect_size")),
            "decision": r.get("decision", ""),
            "is_canonical": r["variable"] in CANONICAL_TERMS,
        })
    print(f"  Significance: {len(rows)} rows")
    return rows


def export_pairwise() -> list[dict]:
    """Export step7b pairwise contrasts."""
    rows = []
    for r in read_csv(RESULTS / "step7b_pairwise_table.csv"):
        rows.append({
            "variable": r["variable"],
            "display_name": r.get("display_name", r["variable"]),
            "var_type": r["var_type"],
            "field_type": r.get("field_type", ""),
            "contrast": r["contrast"],
            "test_name": r.get("test_name", ""),
            "p_adjusted": safe_float(r.get("p_value_adjusted")),
            "effect_size": safe_float(r.get("effect_size")),
            "effect_size_name": r.get("effect_size_name", ""),
            "mean_1": safe_float(r.get("mean_1")),
            "mean_2": safe_float(r.get("mean_2")),
            "direction": r.get("direction", ""),
            "n_1": safe_int(r.get("n_1")),
            "n_2": safe_int(r.get("n_2")),
            "is_canonical": r["variable"] in CANONICAL_TERMS,
        })
    print(f"  Pairwise: {len(rows)} rows")
    return rows


def export_scatter_data():
    """Export per-cyclone data for scatterplots (canonical terms only).
    
    Saved as a public static JSON file (not imported at build time)
    because the data is ~2700 rows × 73 columns.
    Values rounded to 2 decimals to reduce size.
    """
    SCATTER_DST = ROOT / "web" / "public" / "data"
    SCATTER_DST.mkdir(parents=True, exist_ok=True)

    for field_type in ("absolute", "anomaly"):
        src = RESULTS / f"step6_integrated_{field_type}.csv"
        if not src.exists():
            print(f"  WARNING: {src} not found, skipping {field_type} scatter data")
            continue

        raw_rows = read_csv(src)
        headers = list(raw_rows[0].keys()) if raw_rows else []

        # Identify feature columns (field__feature pattern)
        feature_cols = [h for h in headers if "__" in h]
        lec_cols = sorted(CANONICAL_TERMS & set(headers))

        cyclones = []
        for r in raw_rows:
            ep = safe_int(r.get("ep"))
            if ep is None:
                continue
            entry = {"ep": ep}
            for lec in lec_cols:
                v = safe_float(r.get(lec))
                entry[lec] = round(v, 2) if v is not None else None
            for fc in feature_cols:
                v = safe_float(r.get(fc))
                entry[fc] = round(v, 2) if v is not None else None
            cyclones.append(entry)

        result = {
            "field_type": field_type,
            "feature_columns": feature_cols,
            "lec_columns": lec_cols,
            "cyclones": cyclones,
        }
        out_path = SCATTER_DST / f"lfd_scatter_{field_type}.json"
        with open(out_path, "w") as f:
            json.dump(result, f)
        print(f"  Scatter {field_type}: {len(cyclones)} cyclones → {out_path.name}")


def export_top_associations() -> dict:
    """Export step8 top associations (all + canonical)."""
    out = {"all": [], "canonical": []}
    for variant, key in [
        ("step8_top_associations.csv", "all"),
        ("step8_top_associations_canonical.csv", "canonical"),
    ]:
        src = RESULTS / variant
        if not src.exists():
            continue
        for r in read_csv(src):
            out[key].append({
                "ep": int(r["ep"]),
                "lec_term": r["lec_term"],
                "field": r["field"],
                "feature": r["feature"],
                "field_type": r.get("field_type", "absolute"),
                "predep": safe_float(r.get("predep")),
                "pearson_r": safe_float(r.get("pearson_r")),
                "spearman_rho": safe_float(r.get("spearman_rho")),
                "display": format_display(
                    r["field"].replace("_anom_epall", ""),
                    r["feature"]
                ),
            })
    print(f"  Top associations: {len(out['all'])} all, {len(out['canonical'])} canonical")
    return out


def export_summary() -> list[dict]:
    """Export step8 summary table."""
    rows = []
    for r in read_csv(RESULTS / "step8_summary_table.csv"):
        rows.append({
            "ep": int(r["ep"]),
            "field_type": r["field_type"],
            "lec_term": r["lec_term"],
            "mean": safe_float(r.get("mean")),
            "median": safe_float(r.get("median")),
            "max": safe_float(r.get("max")),
            "count": safe_int(r.get("count")),
            "is_canonical": r["lec_term"] in CANONICAL_TERMS,
        })
    print(f"  Summary: {len(rows)} rows")
    return rows


def copy_figures():
    """Copy all pipeline figures to web/public/."""
    if not FIGURES_SRC.exists():
        print("  WARNING: source figures directory not found")
        return

    if FIGURES_DST.exists():
        shutil.rmtree(FIGURES_DST)
    FIGURES_DST.mkdir(parents=True, exist_ok=True)

    count = 0
    for src_file in FIGURES_SRC.rglob("*.png"):
        rel = src_file.relative_to(FIGURES_SRC)
        dst = FIGURES_DST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst)
        count += 1

    print(f"  Figures: {count} PNG files copied")


# ── Main ─────────────────────────────────────────────────────────

def main():
    CONTENT_DST.mkdir(parents=True, exist_ok=True)

    print("Exporting LEC field dependence data for web...")

    # 1. PREDEP data — written to both content/ (build-time) and public/data/ (client-fetch)
    predep = export_predep()
    with open(CONTENT_DST / "lfd_predep.json", "w") as f:
        json.dump(predep, f)
    PUBLIC_DATA_DST.mkdir(parents=True, exist_ok=True)
    with open(PUBLIC_DATA_DST / "lfd_predep.json", "w") as f:
        json.dump(predep, f)

    # 2. Significance
    significance = export_significance()
    with open(CONTENT_DST / "lfd_significance.json", "w") as f:
        json.dump(significance, f)

    # 3. Pairwise
    pairwise = export_pairwise()
    with open(CONTENT_DST / "lfd_pairwise.json", "w") as f:
        json.dump(pairwise, f)

    # 4. Scatter data (goes to web/public/data/, not content/)
    export_scatter_data()

    # 5. Top associations
    top = export_top_associations()
    with open(CONTENT_DST / "lfd_top_associations.json", "w") as f:
        json.dump(top, f)

    # 6. Summary
    summary = export_summary()
    with open(CONTENT_DST / "lfd_summary.json", "w") as f:
        json.dump(summary, f)

    # 7. Figures
    copy_figures()

    print("\n✓ Export complete.")
    print(f"  JSON (build-time):  {CONTENT_DST}/lfd_*.json")
    print(f"  JSON (client-fetch): {PUBLIC_DATA_DST}/lfd_predep.json + lfd_scatter_*.json")
    print(f"  Figures: {FIGURES_DST}/")


if __name__ == "__main__":
    main()
