# Cyclone Phase Space (CPS) Analysis

Computes the Hart (2003) Cyclone Phase Space diagnostics — thermal wind
asymmetry (B) and lower/upper thermal wind (VTL, VTU) — for each cyclone
track using ERA5 geopotential and wind fields, and plots the classic
CPS diagrams (VTL vs B, VTL vs VTU).

## Scripts

- `cps_calculator_era5tocsv.py` — reads a per-cyclone ERA5 NetCDF (z, u, v)
  and its track file, computes B/VTL/VTU/SIZE at each matched time step,
  and writes a CSV.
- `cps_plots_csv_gris.py` — reads a CPS CSV and generates the two-panel
  phase-space diagram (grey markers; no intensity/pressure encoding).

## Usage

```bash
python cps_calculator_era5tocsv.py \
    --nc cyclone_tracks/<track_id>_era5.nc \
    --track cyclone_tracks/cyclone_<track_id>.txt \
    --dt 3 \
    --output csv_output/CPS_<track_id>.csv

python cps_plots_csv_gris.py \
    --csv csv_output/CPS_<track_id>.csv \
    --output cps_output/CPS_<track_id>.png
```

Track file format: `AAAAMMDDHH[MM] lat lon ...` (space-separated, one
record per line).

## Outputs (not versioned)

Per-cyclone inputs and outputs are git-ignored (regenerable, ~6800 files,
~100 MB total):

- `cyclone_tracks/` — per-cyclone track files (input)
- `csv_output/` — per-cyclone CPS CSVs (`time, B_left, B_right, dir, SIZE, VTL, VTU`)
- `cps_output/` — per-cyclone CPS diagram PNGs

Regenerate by looping the two scripts above over the full track/track-ID
population (see `scripts/utils/load_data.py` for the canonical track source).
