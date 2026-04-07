# Legacy EP Structure Analysis (EP1 vs EP2)

> ⚠️ **LEGACY/ARCHIVED** — This directory contains the historical EP1 vs EP2 analysis implementation that was superseded in April 2026 by a new canonical analysis covering all three Energy Patterns (EP1, EP2, EP3).

## What This Analysis Was

This legacy analysis compared **EP1 (N=444)** and **EP2 (N=979)** cyclones during intensification, using **climatology-based anomalies** (departures from the 1991–2020 WMO monthly mean climatology).

### Key Characteristics

- **Scope**: EP1 vs EP2 comparison only (EP3 not analyzed)
- **Anomaly Definition**: `field - monthly_climatology` (climatological decomposition)
- **Sample**:
  - EP1: 444 cyclones (cluster 0, 11.6%)
  - EP2: 979 cyclones (cluster 2, 25.6%)
  - EP3: *not included* (2,397 cyclones, cluster 1, 62.7%)

### Why It Was Superseded

1. **Incomplete EP coverage**: The analysis excluded EP3, which represents the majority (62.7%) of cyclones.
2. **Climatological anomalies**: Using monthly climatology as the reference meant anomalies reflected departures from the seasonal background, not from the cyclone population itself.
3. **Scientific reinterpretation**: The new canonical analysis defines anomalies as **deviations from the TOTAL cyclone composite (EPALL)**, which better isolates what distinguishes each Energy Pattern from the "average" cyclone.

## New Canonical Analysis

The new implementation lives at `scripts/ep_structure_analysis/` and:

- Includes **EP1, EP2, EP3, and EPALL** (total composite)
- Defines anomalies as **EPx - EPALL** (cyclone-relative)
- Maintains all original diagnostics (EGR, PV, temperature advection, etc.)
- Preserves climatology-based calculations only where scientifically required (AFC, BtCR)

## Preserved Files

| File | Description |
|------|-------------|
| `step1_select_ep_tracks.py` | EP1/EP2 track selection (legacy) |
| `step2_download_era5_parallel.py` | ERA5 download pipeline |
| `step2_1_download_era5_monthly_means.py` | Climatology download for anomalies |
| `step3_precompute_composites.py` | Composite computation (EP1/EP2 only) |
| `step4_create_figures.py` | Figure generation (EP1 vs EP2 panels) |
| `step5_update_scientific_notes.py` | Stats and documentation generation |
| `step6_generate_cyclone_explorer_panels.py` | Per-cyclone panel generation |
| `README.md` | Original pipeline documentation |
| `SCIENTIFIC_NOTES.md` | Original scientific methodology notes |

## Legacy Data Products

Legacy outputs are preserved in:
- `data/era5_ep_structure_legacy/` — Precomputed composites, climatology files
- `figures/ep_structure_legacy/` — Generated composite figures
- `docs/scientific_notes_ep_structure_legacy.pdf` — Scientific documentation

## Reproducibility

To reproduce the legacy analysis (if needed):

```bash
cd scripts/ep_structure_analysis_legacy
python step1_select_ep_tracks.py
python step2_download_era5_parallel.py
python step2_1_download_era5_monthly_means.py
python step3_precompute_composites.py --mode full_intensification
python step4_create_figures.py --mode full_intensification
python step5_update_scientific_notes.py --mode full_intensification
```

**Note**: Running this will require adjusting import paths since the scripts reference `scripts.ep_structure_analysis.*`.

---

**Migration Date**: April 2026  
**Author**: Danilo Couto de Souza
