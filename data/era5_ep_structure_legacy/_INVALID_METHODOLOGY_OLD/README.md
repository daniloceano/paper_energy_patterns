# ⚠️ INVALID COMPOSITES - DO NOT USE

These composite files were generated with an **INCORRECT methodology** and have been invalidated.

## Problem

The old pipeline used a **FIXED domain center** for each cyclone (the mean position during intensification phase), instead of the correct methodology which requires:

- **Storm-centered per timestep**: Each timestep's domain must be centered on the actual cyclone position at that instant

## Impact

- Only ~15% of timesteps were adequately storm-centered (within 222 km)
- Mean distance between cyclone center and domain center: 1,079 km
- Maximum distance: 8,788 km
- This completely invalidates the composite analysis

## Audit Reference

See audit artifacts in:
- `results/ep_structure/ep_structure_method_audit_per_timestep.csv`
- `results/ep_structure/ep_structure_method_audit_summary.json`
- `results/ep_structure/ep_structure_method_audit_report.txt`

## Correct Methodology (implemented 2026-04-03)

The corrected pipeline in `scripts/ep_structure_analysis/step3_precompute_composites.py` now:
1. Loads cyclone center position from track data for each timestep
2. Extracts storm-centered subdomain for each timestep
3. Computes diagnostics on correctly centered grids
4. Aggregates all storm-centered timesteps into composite

## Date Invalidated

2026-04-03

## Files in this directory

- `precomputed_composites_ep1_central_time.nc`
- `precomputed_composites_ep1_full_intensification.nc`
- `precomputed_composites_ep2_central_time.nc`
- `precomputed_composites_ep2_full_intensification.nc`
