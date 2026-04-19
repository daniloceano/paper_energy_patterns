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
Date: April 2026
"""

import sys
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


def main():
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
        f"  Step 2 (LEC table):       {check_file(RESULTS_DIR / 'step2_lec_intensification_means.csv')}",
        f"  Step 3 (ERA5 manifest):   {check_file(RESULTS_DIR / 'step3_era5_field_manifest.csv')}",
        f"  Step 4 (abs features):    {check_file(RESULTS_DIR / 'step4_features_absolute.csv')}",
        f"  Step 5 (anom features):   {check_file(RESULTS_DIR / 'step5_features_anomaly.csv')}",
        f"  Step 6 (integration):     {check_file(RESULTS_DIR / 'step6_integrated_absolute.csv')}",
        f"  Step 7 (PREDEP abs):      {check_step7('absolute')}",
        f"  Step 7 (PREDEP anom):     {check_step7('anomaly')}",
        f"  Step 8 (synthesis):       {check_file(RESULTS_DIR / 'step8_summary_table.csv')}",
        "",
        "REMOTE EXECUTION DEPENDENCIES",
        "------------------------------",
        "",
        "Steps that require the remote/HPC server:",
        "  • Step 4: Per-cyclone ERA5 fields (--era5-dir required)",
        "  • Step 5: Per-cyclone ERA5 fields + EPALL composite",
        "  • Step 7: Requires integrated tables from steps 4-6",
        "  • Step 8: Requires PREDEP results from step 7",
        "",
        "Steps that can run locally:",
        "  • Step 1: Uses ep_structure results + LEC Zenodo data",
        "  • Step 2: Uses LEC Zenodo data only",
        "  • Step 3: Dry-run mode (generates manifest template)",
        "  • Step 6: Merges whatever is available",
        "  • Step 9: This status report",
        "",
        "RECOMMENDED REMOTE EXECUTION SEQUENCE",
        "--------------------------------------",
        "",
        "# On local machine first:",
        "python scripts/lec_field_dependence_analysis/step1_consolidate_metadata.py",
        "python scripts/lec_field_dependence_analysis/step2_build_lec_table.py",
        "python scripts/lec_field_dependence_analysis/step3_map_era5_fields.py",
        "",
        "# Transfer results/ to remote, then on remote:",
        "python step4_extract_features_absolute.py --era5-dir /path/to/era5/ --workers 32",
        "python step5_extract_features_anomaly.py --era5-dir /path/to/era5/ --workers 32",
        "python step6_integrate_tables.py",
        "python step7_compute_predep.py --field-type absolute --workers 32",
        "python step7_compute_predep.py --field-type anomaly --workers 32",
        "",
        "# Transfer results back, then locally:",
        "python step8_synthesis_figures.py",
        "python step9_update_docs.py",
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
        "1. Temporal mismatch: LEC means cover full intensification phase,",
        "   while ERA5 fields represent central timesteps only.",
        "2. PREDEP bootstrap estimation can be noisy with N < 100.",
        "3. EP3 has ~1600 cases (robust), EP2 ~770 (adequate), EP1 ~330 (marginal).",
        "4. Feature extraction assumes 121×121 grid — verify if per-cyclone",
        "   ERA5 files match this resolution.",
        "",
    ]

    OUTPUT.write_text("\n".join(lines))
    print(f"Pipeline status written to: {OUTPUT}")


if __name__ == "__main__":
    main()
