"""
Step 9: Update Documentation

Generates a final summary of what was implemented and what remains
pending (remote execution).  This step is informational — it does not
modify SCIENTIFIC_NOTES.md or README.md automatically, but produces
a status report for the analyst to review.

Output:
  results/lec_field_dependence/step9_pipeline_status.txt

Run:
  python scripts/lec_field_dependence_analysis/step9_update_docs.py

Author: Danilo Couto de Souza
Updated: September 2026
"""

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from scripts.lec_field_dependence_analysis.utils_io import RESULTS_DIR, FIGURES_DIR

OUTPUT = RESULTS_DIR / "step9_pipeline_status.txt"


def check_file(path: Path) -> str:
    """Return ✓ if exists, ✗ otherwise."""
    return "✓" if path.exists() else "✗"


def check_step7(field_type: str) -> str:
    """
    Check step 7 PREDEP output — accepts EITHER a merged file or chunk files.

    When run_pipeline.sh uses --n-chunks > 1 (the default), step7 only
    writes chunk files (step7_predep_{type}_chunk*.csv) — the merged file
    is never produced.  step8 reads the chunk files directly, so this is
    the expected normal state.
    """
    merged = RESULTS_DIR / f"step7_predep_{field_type}.csv"
    if merged.exists():
        return "✓"
    chunks = list(RESULTS_DIR.glob(f"step7_predep_{field_type}_chunk*.csv"))
    if chunks:
        return f"✓ ({len(chunks)} chunks)"
    return "✗"


def csv_row_count(path: Path) -> int:
    """Count data rows without loading a full result table into memory."""
    if not path.exists():
        return 0
    with path.open(newline="") as handle:
        return sum(1 for _ in csv.reader(handle)) - 1


def ep_counts() -> Counter:
    """Read the current corrected-population counts from step 1."""
    path = RESULTS_DIR / "step1_eligible_cases.csv"
    counts: Counter = Counter()
    if not path.exists():
        return counts
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            counts[int(row["ep"])] += 1
    return counts


def main():
    counts = ep_counts()
    total_cases = sum(counts.values())
    predep_rows = sum(
        csv_row_count(RESULTS_DIR / f"step7_predep_{field_type}{suffix}.csv")
        for field_type in ("absolute", "anomaly")
        for suffix in ("", "_epall")
    )
    figure_count = len(list(FIGURES_DIR.rglob("*.png")))

    lines = [
        "=" * 70,
        "LEC–FIELD DEPENDENCE ANALYSIS — Pipeline Status Report",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 70,
        "",
        "STEP STATUS",
        "-----------",
        "",
        f"  Step 1 (metadata):        {check_file(RESULTS_DIR / 'step1_eligible_cases.csv')}",
        f"  Step 2 (LEC table):       {check_file(RESULTS_DIR / 'step2_lec_means.csv')}",
        f"  Step 3 (ERA5 manifest):   {check_file(RESULTS_DIR / 'step3_era5_field_manifest.csv')}",
        f"  Step 3b (derived fields): {check_file(RESULTS_DIR / 'step3b_derived_field_manifest.csv')}",
        f"  Step 4 (abs features):    {check_file(RESULTS_DIR / 'step4_features_absolute.csv')}",
        f"  Step 5 (anom features):   {check_file(RESULTS_DIR / 'step5_features_anomaly.csv')}",
        f"  Step 6 (integration):     {check_file(RESULTS_DIR / 'step6_integrated_all.csv')}",
        f"  Step 7 (PREDEP abs):      {check_step7('absolute')}",
        f"  Step 7 (PREDEP anom):     {check_step7('anomaly')}",
        f"  Step 7 (PREDEP EPALL):    {check_file(RESULTS_DIR / 'step7_predep_absolute_epall.csv')}",
        f"  Step 7b (EP tests):       {check_file(RESULTS_DIR / 'step7b_diagnostic_table.csv')}",
        f"  Step 8 (synthesis):       {check_file(RESULTS_DIR / 'step8_summary_table.csv')}",
        f"  Step 8b (figures):        {'✓' if figure_count else '✗'} ({figure_count} PNGs)",
        "",
        "CURRENT DATASET",
        "---------------",
        "",
        f"  Corrected population: EP1 = {counts.get(1, 0)}, EP2 = {counts.get(2, 0)}, "
        f"EP3 = {counts.get(3, 0)}; total = {total_cases}",
        f"  PREDEP rows: {predep_rows} (absolute + anomaly; EP1–EP3 + EPALL)",
        "  Temporal window: exact 2–3 central intensification timestamps per cyclone",
        "  Dynamic fields: PV 850, PV 200, AdvT 850, AFC 250, and KE advection 250",
        "",
        "REMOTE EXECUTION DEPENDENCIES",
        "------------------------------",
        "",
        "Steps that require or materially benefit from the remote/HPC server:",
        "  • Step 3b: Reads the raw ERA5 archive and writes per-cyclone derived fields",
        "  • Steps 4–5: Extract features from all per-cyclone fields",
        "  • Step 7: PREDEP computation over all EP populations",
        "",
        "Steps that can run locally:",
        "  • Step 1: Uses ep_structure results + LEC Zenodo data",
        "  • Step 2: Uses LEC Zenodo data only",
        "  • Step 3: Builds the exact-time ERA5 manifest",
        "  • Steps 6, 7b, 8, and 8b: Use synchronized tabular results",
        "  • Step 9: Generates this status report",
        "",
        "RECOMMENDED REMOTE EXECUTION SEQUENCE",
        "--------------------------------------",
        "",
        "# On local machine first:",
        "python scripts/lec_field_dependence_analysis/step1_consolidate_metadata.py",
        "python scripts/lec_field_dependence_analysis/step2_build_lec_table.py",
        "python scripts/lec_field_dependence_analysis/step3_map_era5_fields.py",
        "",
        "# Transfer steps 1–3 to the isolated remote worktree, then run:",
        "bash scripts/lec_field_dependence_analysis/run_pipeline.sh \\",
        "  --era5-dir /path/to/raw/era5 \\",
        "  --derived-dir /path/to/derived/fields \\",
        "  --tracks-file /path/to/corrected_tracks.csv \\",
        "  --afc-climatology /path/to/expanded_afc_climatology.nc \\",
        "  --n-chunks 16 --workers 4 --stop-on-error",
        "",
        "# Transfer results back, then locally:",
        "python scripts/web/export_lec_field_dependence.py",
        "",
        "FOR HPC WITH JOB ARRAYS (chunked execution):",
        "  step4: --chunk $SLURM_ARRAY_TASK_ID --n-chunks $SLURM_ARRAY_TASK_COUNT",
        "  step5: --chunk $SLURM_ARRAY_TASK_ID --n-chunks $SLURM_ARRAY_TASK_COUNT",
        "  step7: --chunk $SLURM_ARRAY_TASK_ID --n-chunks $SLURM_ARRAY_TASK_COUNT",
        "  (Each step supports --chunk/--n-chunks for SLURM job arrays)",
        "",
        "KNOWN LIMITATIONS",
        "-----------------",
        "",
        "1. The 2–3 central timestamps are a deliberate mature-structure proxy;",
        "   they do not describe the full intensification-phase evolution.",
        "2. The EP populations are unbalanced; EP1 is the smallest group and its",
        "   pairwise estimates have greater uncertainty.",
        "3. PREDEP confidence intervals have not yet been computed.",
        "4. Latitude/longitude are not controlled, so geographic confounding remains",
        "   possible for some field–LEC associations.",
        "",
    ]

    OUTPUT.write_text("\n".join(lines))
    print(f"Pipeline status written to: {OUTPUT}")


if __name__ == "__main__":
    main()
