# EP Structure Analysis: EP1, EP2, EP3 — Canonical Methodology (April 2026)

## Objective

Investigate the spatial structure of South Atlantic cyclones during intensification,
comparing Energy Patterns (EP1, EP2, EP3) and the total cyclone composite (EPALL),
using standard dynamical diagnostics.

## ⚡ CANONICAL METHODOLOGY (April 2026)

### Duration Filter
**Only cyclones with intensification phase >= 24 hours (1 day) are eligible.**

This filter removes ~28.5% of cyclones (1,087 out of 3,820), focusing the analysis
on cyclones with sufficiently long intensification phases for meaningful composite
averaging.

### Temporal Reduction
**Composites use CENTRAL TIMESTEPS ONLY, not the full intensification phase:**
- **ODD** number of timesteps → select central **3** timesteps
- **EVEN** number of timesteps → select central **2** timesteps

This reduces ERA5 download volume by **~94%** (from 121,406 to 6,884 timesteps)
while maintaining scientific representativeness of the composite structure.

### Final Sample Sizes
After >= 24h filter:
- **EP1**: 332 cyclones (was 444, removed 112 short cases = 25.2%)
- **EP2**: 776 cyclones (was 979, removed 203 short cases = 20.7%)
- **EP3**: 1,625 cyclones (was 2,397, removed 772 short cases = 32.2%)
- **EPALL**: 2,733 cyclones (was 3,820, removed 1,087 short cases = 28.5%)

**Rationale:** Short intensification phases (< 24h) may represent rapidly
transitioning systems or weakly defined intensification periods. Focusing on
>= 24h cases ensures robust phase identification and reduces noise in composites.

## Cluster Consistency

All cyclones come from the cluster assignments in `results/cluster/kmeans_clustered_data.csv`:
- **EP1** = Cluster 0 (high energy conversions)
- **EP2** = Cluster 2 (moderate conversions)
- **EP3** = Cluster 1 (weak/background energetics)

The duration filter is applied AFTER cluster assignment to maintain consistency
with the energy pattern definitions while ensuring temporal robustness.

## Anomaly Definitions (April 2026)

The analysis now uses **EPALL-relative anomalies** as the primary anomaly definition:

```
EPx_anomaly = EPx_composite - EPALL_composite
```

This isolates what distinguishes each Energy Pattern from the "average" cyclone,
rather than from a monthly climatology. The EPALL-relative anomalies are computed
for: EGR, PV (200/850 hPa), temperature advection, moisture flux divergence, SLP,
KE advection, and RK criterion.

**Exception:** AFC and BtCR diagnostics retain climatology-based decomposition
by construction (Orlanski & Katzfey 1991; Rivière 2006), as they require a
low-frequency background state for physical interpretation.

## Legacy Analysis

The previous EP1-vs-EP2 analysis (using climatology-based anomalies) is preserved
in `scripts/ep_structure_analysis_legacy/`. See `LEGACY_README.md` for details.

## Diagnostic Fields

| Field | Levels | Purpose | Key References |
|-------|--------|---------|----------------|
| **EGR** (Eady Growth Rate) | 500–850 hPa layer | Measures baroclinic instability of the background flow | Lindzen & Farrell (1980); Besson et al. (2021) |
| **PV** (Potential Vorticity) | 200 hPa | Upper-level tropopause dynamics and stratospheric intrusions | Hoskins et al. (1985); Davis & Emanuel (1991); Rossa et al. (2000) |
| **PV** (Potential Vorticity) | 850 hPa | Low-level PV anomaly associated with surface cyclone | Hoskins et al. (1985); Davis (1992); Čampa & Wernli (2012) |
| **Temperature advection** | 850 hPa | Warm/cold advection patterns linked to QG forcing for ascent | Sutcliffe (1947); Sanders & Gyakum (1980); Sinclair (1994) |
| **Specific humidity** | 975 hPa | Low-level moisture distribution | Bao et al. (2002); Schär & Wernli (1993) |
| **Moisture flux divergence** | 975 hPa | Moisture convergence/divergence → convective potential | Banacos & Schultz (2005); Lackmann (2011) |
| **SLP** (Sea Level Pressure) | Surface | Cyclone position, intensity and horizontal structure | Hoskins & Hodges (2005); Reboita et al. (2010) |
| **RK criterion** (Rayleigh-Kuo) | 250 hPa | Barotropic/baroclinic instability necessary condition | Rayleigh (1880); Kuo (1949); Charney & Stern (1962) |
| **KE advection** | 250 hPa | Kinetic energy tendency from advection in jet stream | - |
| **AFC** (Ageostrophic Flux Convergence) | 250 hPa | Eddy KE source/sink from ageostrophic pressure work | Orlanski & Katzfey (1991); Orlanski & Sheldon (1993) |

**Anomaly diagnostics** (departure from 1991–2020 WMO climatology — same decomposition as AFC):

| Anomaly Field | Level | Output variable | Climatology group |
|---------------|-------|-----------------|-------------------|
| **PV′** | 200 hPa | `pv_200_anom` | `pv200` (175/200/225 hPa, u,v,t) |
| **PV′** | 850 hPa | `pv_850_anom` | `pv850` (825/850/875 hPa, u,v,t) |
| **Temp advection′** | 850 hPa | `adv_T_850_anom` | `pv850` (u,v,t at 850 hPa) |
| **Moisture flux div′** | 975 hPa | `div_q_975_anom` | `mfd975` (975 hPa, u,v,q) |
| **KE advection′** | 250 hPa | `ke_adv_250_anom` | `250hPa` (u,v at 250 hPa) |
| **SLP′** | Surface | `msl_anom` | `slp` (msl, single-level) |

> **Note:** EGR is not decomposed (layer-mean nature makes eddy decomposition ill-defined).
> AFC is already an anomaly field by construction (uses $\phi'$ and $\vec{v}'$).

### Level selection rationale

- **EGR (250–850 hPa):** The 250–850 hPa layer captures the main tropospheric
  baroclinic zone. This layer-mean approach is standard since Hoskins & Valdes (1990)
  and has been widely applied in Southern Hemisphere cyclone studies (Simmonds & Lim,
  2009; Gramcianinov et al., 2019). The growth rate σ = 0.31·f/N·|∂V/∂z| integrates
  the static stability (N) and vertical wind shear over the full depth of the
  troposphere.

- **PV at 200 hPa:** The dynamic tropopause is traditionally defined as the 2 PVU
  surface, typically found near 200 hPa in midlatitudes (Hoskins et al., 1985).
  Upper-level PV anomalies (tropopause folds) are precursors for rapid cyclogenesis
  (Davis & Emanuel, 1991; Rossa et al., 2000). The 200 hPa level is widely used in
  extratropical cyclone composites (e.g., Dacre et al., 2012; Catto et al., 2010).

- **PV at 850 hPa:** Low-level PV anomalies are generated by diabatic heating
  (latent heat release) and are a key component of the "PV tower" structure in
  explosively deepening cyclones (Čampa & Wernli, 2012; Martínez-Alvarado et al.,
  2016). The 850 hPa level is standard for characterizing the lower-tropospheric
  cyclone circulation.

- **Temperature advection at 850 hPa:** The 850 hPa level is the standard
  reference for thermal advection in synoptic analysis (e.g., Sanders & Gyakum,
  1980; Sinclair, 1994). Warm air advection (WAA) ahead of the surface cyclone
  is a primary quasi-geostrophic forcing for upward motion (Sutcliffe, 1947;
  Trenberth, 1978), while cold air advection (CAA) in the rear contributes to
  frontal structure and cyclone deepening.

- **SLP:** Standard field for cyclone tracking and composite analysis (Hoskins &
  Hodges, 2005; Reboita et al., 2010).

- **Moisture fields at 975 hPa:** The 975 hPa level captures near-surface moisture
  transport while remaining above the planetary boundary layer turbulence. Moisture
  flux divergence (∇·(qV)) identifies regions of moisture convergence (negative
  values) associated with convective potential and latent heat release, a key
  diabatic process in cyclone intensification (Banacos & Schultz, 2005; Lackmann,
  2011). The calculation uses MetPy's spherical geometry-aware gradient operators
  and physical constants to ensure consistency.

- **RK criterion at 250 hPa:** The Rayleigh-Kuo stability criterion provides a
  necessary condition for barotropic and baroclinic instability. Computed as
  ∂q/∂y = β - ∂²u/∂y², where negative values indicate regions satisfying the
  instability criterion. The 250 hPa level is chosen as representative of the
  jet stream, where barotropic processes are strongest.

- **KE advection at 250 hPa:** Kinetic energy advection (-V · ∇KE) quantifies
  the tendency for KE to increase or decrease due to advection within the jet
  stream. Positive values indicate regions where the flow is accelerating, while
  negative values indicate deceleration. Computed at 250 hPa to capture jet-level
  dynamics.

- **AFC at 250 hPa:** Ageostrophic Flux Convergence (Orlanski & Katzfey, 1991;
  Orlanski & Sheldon, 1993) quantifies how ageostrophic pressure work
  redistributes eddy kinetic energy. A **temporal decomposition** is used:
  the 30-year monthly climatology (1991–2020, WMO standard) serves as the base
  state (V_m, Φ_m), and the instantaneous departure is the eddy perturbation.
  This is deliberately independent of the area-mean decomposition used in the
  Lorenz Energy Cycle analysis to avoid circular validation. Positive AFC
  indicates an eddy KE source; negative values indicate a sink.

## Pipeline Steps

### Step 1: Select Cyclone Tracks (`step1_select_ep_tracks.py`)

Selects eligible cyclones for each Energy Pattern with >= 24h intensification.

**Canonical methodology:**
1. Loads cluster assignments (EP1/EP2/EP3)
2. Filters for intensification duration >= 24 hours
3. Selects CENTRAL timesteps only (2 or 3 per cyclone)
4. Generates track visualizations

**Output:**
- `results/ep_structure/ep{1,2,3,all}_cases.csv` (eligible cases with selected timesteps)
- `results/ep_structure/ep{1,2,3}_top10_intense.csv` (10 most intense per EP)
- `figures/ep_structure/tracks/ep{1,2,3}_tracks_overview.png`

**Execution:**
```bash
python scripts/ep_structure_analysis/step1_select_ep_tracks.py
```

### Step 2: Download ERA5 Data

**Option A (Fresh Download):** `step2_download_era5_parallel.py`

Downloads ERA5 reanalysis for eligible cyclones using ONLY central timesteps.

**Variables:** u, v, t, z, q (pressure levels: 175, 200, 225, 250, 500, 825, 850, 875, 975), msl (surface)

**Domain:** 30° × 30° centered on cyclone

**Temporal:** Only the 2-3 central timesteps per cyclone (~94% reduction vs full intensification)

**Execution:**
```bash
python scripts/ep_structure_analysis/step2_download_era5_parallel.py --jobs 10
```

**Option B (OPTIONAL - Reuse Legacy):** `step2b_reuse_legacy_era5.py`

Operational shortcut to reuse ERA5 data from legacy analysis when available.

**Purpose:** Avoid re-downloading data already obtained for EP1/EP2 in previous analysis.

> **EP3 coverage: NONE.** The legacy analysis only covered EP1 and EP2.
> `step2b` cannot reuse any EP3 cases. EP3 must always be downloaded via `step2_download_era5_parallel.py`.

**Strategy:**
- Checks if legacy ERA5 file exists for each eligible cyclone
- Verifies file contains required central timesteps
- Extracts only those timesteps to canonical location
- Reports reuse success rate per EP group

**Execution:**
```bash
# Dry run (report only, no file operations)
python scripts/ep_structure_analysis/step2b_reuse_legacy_era5.py --dry-run

# Actual reuse (EP1 and EP2 only — EP3 will show 0% coverage)
python scripts/ep_structure_analysis/step2b_reuse_legacy_era5.py

# Monitor reuse progress while step2b runs
python scripts/ep_structure_analysis/step2c_monitor.py --mode reuse --watch

# Then download missing/EP3 cases:
python scripts/ep_structure_analysis/step2_download_era5_parallel.py --jobs 10
```

**Note:** This step is NOT required for the canonical pipeline. It's purely a time-saving
convenience when legacy data exists. The canonical flow is: step1 → step2 (fresh download) → step3.


### Step 3: Precompute Composites (`step3_precompute_composites.py`)

Computes spatial composites for all diagnostic fields.

**Methodology:**
- Loads ERA5 data for each cyclone (2-3 central timesteps)
- Computes diagnostic fields (EGR, PV, advection, etc.)
- Averages across selected timesteps within each cyclone
- Averages across all cyclones in each EP group
- Computes EPALL composite (union of all EPs)
- Computes EPALL-relative anomalies (EPx - EPALL)

**Output:** `data/era5_ep_structure/precomputed_composites_ep{1,2,3,all}.nc`

**Execution:**
```bash
python scripts/ep_structure_analysis/step3_precompute_composites.py --jobs 4
```

### Step 4: Generate Figures (`step4_create_figures.py`)

Creates publication-quality composite figures for all diagnostic fields.

**Output:** `figures/ep_structure/composite_*.png`

**Execution:**
```bash
python scripts/ep_structure_analysis/step4_create_figures.py
```

### Step 5: Update Scientific Notes (`step5_update_scientific_notes.py`)

Updates SCIENTIFIC_NOTES.md with composite statistics and generates PDF.

**Output:** 
- `SCIENTIFIC_NOTES.md` (updated)
- `results/ep_structure/composite_stats.json`
- `docs/scientific_notes_ep_structure.pdf`

**Execution:**
```bash
python scripts/ep_structure_analysis/step5_update_scientific_notes.py
```

### Step 6: Generate Cyclone Explorer Panels (`step6_generate_cyclone_explorer_panels.py`)

Creates individual panels for each timestep of each cyclone (for web visualization).

**Output:** `figures/cyclone_explorer/ep{1,2,3}/{track_id}/panel_t{NNN}.png`

**Execution:**
```bash
python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py --jobs 4
```

## Output File Naming

```
# Composites (NetCDF)
data/era5_ep_structure/precomputed_composites_ep1.nc
data/era5_ep_structure/precomputed_composites_ep2.nc
data/era5_ep_structure/precomputed_composites_ep3.nc
data/era5_ep_structure/precomputed_composites_epall.nc

# Figures (PNG)
figures/ep_structure/composite_egr.png                  # Total composites (EP1/EP2/EP3)
figures/ep_structure/composite_egr_anom_epall.png       # EPALL-relative anomalies
figures/ep_structure/composite_pv200.png
figures/ep_structure/composite_pv850_anom_epall.png
...

# Statistics (JSON)
results/ep_structure/composite_stats.json

# Web visualization
figures/cyclone_explorer/ep1/{track_id}/panel_t000.png
figures/cyclone_explorer/ep2/{track_id}/panel_t001.png
...
```
|------|--------|--------|-------------|
| 1 | `step1_select_ep_tracks.py` | Local/Remote | Select EP1, EP2, EP3 cyclone tracks and create EPALL composite list |
| 2 | `step2_download_era5_parallel.py` | **Remote** | Download ERA5 data (parallel, with patching) |
| 2.1 | `step2_1_download_era5_monthly_means.py` | **Remote** | Download ERA5 monthly means → 30-year climatologies for AFC/BtCR diagnostics (4 variable groups: 250hPa, pv200, pv850, mfd975). Smart completeness check automatically skips already-downloaded months. |
| 2M | `step2c_monitor.py` | Local/Remote | **Monitor download progress** (see below) |
| 3 | `step3_precompute_composites.py` | **Remote** | Compute field composites (EGR, PV, adv_T, SLP, RK, KE_adv) for EP1, EP2, EP3, EPALL + EPALL-relative anomalies |
| 4 | `step4_create_figures.py` | Local | Create EP1, EP2, EP3, EPALL composite figures + EPALL-relative anomaly figures |
| 5 | `step5_update_scientific_notes.py` | Local | Populate SCIENTIFIC_NOTES.md with regional statistics + generate PDF |
| 6 | `step6_generate_cyclone_explorer_panels.py` | Local/Remote | Generate individual cyclone multi-panel figures for temporal exploration |

### Cyclone Explorer (`step6`)

The Cyclone Explorer provides temporal visualization of individual cyclones during their intensification phase. It generates multi-panel figures for each timestep of each cyclone.

Important note on centering and domains:
- ERA5 files are downloaded once per cyclone as a bounding box that covers the entire intensification phase (see `step2`); this produces NetCDF domains often larger than the plotting panel.
- Panel generation (`step6`) now extracts a 30°×30° view centered on the cyclone for each timestep and overlays a dashed 15°×15° box to indicate the LEC/composite region. Previously a single fixed centre per cyclone was used for all timesteps, which could make the cyclone drift relative to the figure.
- The code has been updated so that each panel is centered on the cyclone position at that timestep (nearest track point), ensuring the 30° view follows the cyclone through time while explicitly showing the 15° analysis box.

**Purpose:**
- Explore individual cyclone structure evolution through time
- Visualize meteorological fields at each 6-hourly timestep
- Highlight cyclone center on track

**Panel layout (2×2):**
| Panel | Field | Level/Description |
|-------|-------|-------------------|
| Top-left | SLP + Winds | Sea level pressure (shaded) + 850 hPa wind vectors |
| Top-right | Temperature | Temperature at 850 hPa (°C) |
| Bottom-left | Specific humidity | Specific humidity at 975 hPa (g/kg) |
| Bottom-right | Geopotential | Geopotential height at 500 hPa (m) |

**Output:**
- `figures/cyclone_explorer/ep1/{track_id}/panel_t{NNN}.png` — EP1 timestep panels
- `figures/cyclone_explorer/ep2/{track_id}/panel_t{NNN}.png` — EP2 timestep panels
- `figures/cyclone_explorer/ep3/{track_id}/panel_t{NNN}.png` — EP3 timestep panels
- `web/src/content/cyclone_explorer_manifest.json` — Manifest for web integration

**Usage:**
```bash
# Generate panels for all cyclones with ERA5 data (parallel)
python -m scripts.ep_structure_analysis.step6_generate_cyclone_explorer_panels --jobs 4

# Generate for subset (testing)
python -m scripts.ep_structure_analysis.step6_generate_cyclone_explorer_panels --subset 5

# Extract manifest for web
python -m scripts.web.extract_cyclone_explorer_data
```

**Manifest structure:**
```json
{
  "metadata": {...},
  "cyclones": {
    "track_id": {
      "track_id": "19790585",
      "ep_label": "EP1",
      "metadata": {
        "intensification_start": "...",
        "intensification_end": "...",
        "n_timesteps": 8,
        "center_lat": -38.13,
        "center_lon": -29.19
      },
      "track": {"lats": [...], "lons": [...]},
      "timesteps": [
        {"index": 0, "time": "...", "track_idx": 27, "has_panel": true},
        ...
      ]
    }
  }
}
```

### Monthly climatology download (`step2_1_download_era5_monthly_means.py`)

Downloads 12-month ERA5 climatologies (1991–2020) for all anomaly diagnostics, organized into four groups:

| Group | Levels (hPa) | Variables | Output file |
|-------|-------------|-----------|-------------|
| `250hPa` | 250 | u, v, z | `era5_climatology_250hPa.nc` |
| `pv200` | 175, 200, 225 | u, v, t | `era5_climatology_pv200.nc` |
| `pv850` | 825, 850, 875 | u, v, t | `era5_climatology_pv850.nc` |
| `mfd975` | 975 | u, v, q | `era5_climatology_mfd975.nc` |
| `slp` | surface | msl | `era5_climatology_slp.nc` |

```bash
# Download all groups (auto-skips valid existing files)
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py

# Download specific groups only
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py --groups pv200 pv850 mfd975

# Only recompute climatology files from already-downloaded raw data
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py --clim-only

# Force re-download of specific months (e.g. June and July)
python scripts/ep_structure_analysis/step2_1_download_era5_monthly_means.py --force-months 6 7
```

> The `250hPa` group reuses existing `era5_raw_month{MM}.nc` files without re-downloading, preserving backward compatibility.

### Download monitor (`step2c_monitor.py`)

`step2c_monitor.py` scans `data/era5_ep_structure/` and reports completeness.
It supports two modes:

| Mode | Use with | Description |
|------|----------|-------------|
| `download` (default) | `step2_download_era5_parallel.py` | Full slot-level monitoring (variable × level per case) for all EPs |
| `reuse` | `step2b_reuse_legacy_era5.py` | Simple file existence check for legacy reuse |

**Canonical methodology (April 2026):**
- Supports EP1, EP2, EP3 (and EPALL composites)
- Only cyclones with >= 24h intensification are included
- Only central timesteps (2-3) are downloaded per case

**download mode features:**
- **Process detection**: Automatically detects if `step2_download_era5_parallel.py` 
  is running and shows PID, runtime, CPU%, and memory usage (requires `psutil`)
- **All EPs tracked**: Shows progress for EP1, EP2, and EP3 (previously only EP1/EP2)
- **Per-variable table**: how many cases have that variable with all 9 levels
- **Per-level table**: how many cases have that level with all 5 variables
- **Composite check**: whether `precomputed_composites_ep{1,2,3,all}.nc` (step 3 output) exist

**reuse mode features:**
- Simple file existence check (fast, no NetCDF header parsing)
- Shows found/missing counts per EP group (EP1, EP2, EP3)
- Clearly indicates that **EP3 has no legacy coverage** and requires fresh download
- Useful for tracking step2b progress

```bash
# Install psutil for process detection (optional but recommended)
pip install psutil

# Monitor fresh download progress (default) — includes EP1, EP2, EP3
python scripts/ep_structure_analysis/step2c_monitor.py

# Monitor legacy reuse progress (step2b)
python scripts/ep_structure_analysis/step2c_monitor.py --mode reuse

# Live watch while step 2 or step2b is running (refresh every 60 s)
python scripts/ep_structure_analysis/step2c_monitor.py --watch
python scripts/ep_structure_analysis/step2c_monitor.py --mode reuse --watch

# Faster refresh (every 30 s)
python scripts/ep_structure_analysis/step2c_monitor.py --watch --interval 30

# No terminal clear — safe for nohup / log capture
python scripts/ep_structure_analysis/step2c_monitor.py --watch --no-clear
```

> **EP3 note (reuse mode):** EP3 has zero legacy ERA5 files available. The legacy
> analysis only covered EP1 and EP2. The reuse monitor will show EP3 with 0% coverage
> and will always direct you to use `step2_download_era5_parallel.py` for EP3.

Example output (with download process active):

```
══════════════════════════════════════════════════════════════════════════════
  ERA5 EP STRUCTURE — DOWNLOAD MONITOR
  Scanned : 2026-02-20 14:30:00  (3.2 s)
  Dir     : …/data/era5_ep_structure
  Slots   : 46 per case  = 5 pressure vars × 9 levels + 1 SLP
  ⬇ DOWNLOAD ACTIVE  PID=12345  Runtime=2h 15m 30s  CPU=45.2%  RAM=512MB
══════════════════════════════════════════════════════════════════════════════

  EP1  slots  [████████████░░░░░░░░░░░░░░░░░░]    5520/20424  (27.0%)
       cases  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]     120/444   (27.0%)  (fully complete)
       detail  ✓ complete: 120  ⚑ partial: 150  ✗ missing: 174
       disk    45.2 GB

  EP2  slots  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]   12150/45034  (27.0%)
       cases  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░]     264/979   (27.0%)  (fully complete)
       detail  ✓ complete: 264  ⚑ partial: 330  ✗ missing: 385
       disk    98.5 GB
…
```

### Scientific Documentation

#### Anomaly notation (EP′)

Several composite fields are computed as **anomalies relative to the ERA5 1991–2020
monthly climatology** (WMO standard reference period). These are denoted with a prime
symbol (′) both in figures and in statistical outputs:

| Notation | Meaning |
|----------|---------|
| **EP1** | Composite using the *total* field (raw ERA5 value centred on cyclone) |
| **EP1′** | Composite using the *anomaly* field: X′ = X − X̄ₘ, where X̄ₘ is the ERA5 30-year monthly mean (1991–2020) interpolated to the cyclone location and timestamp |
| **EP2** | Same as EP1 for the EP2 sample |
| **EP2′** | Same as EP1′ for the EP2 sample |

The anomaly decomposition isolates the **synoptic-scale eddy signal** from the
seasonal cycle and background climatology. For linear diagnostics (temperature
advection, KE advection), X′ = X(u′, v′, T′) exactly. For non-linear diagnostics
(PV, moisture flux divergence), the full anomaly is computed as exact subtraction:
PV′ = PV(total) − PV(climatology).

> **Note on AFC:** AFC is already computed from eddy winds (φ′, v⃗′), so it is
> by construction an anomaly field. No additional anomaly version is generated.

Both total and anomaly statistics are exported to:
- `results/ep_structure/composite_stats.json` — fields `north`/`north_anom`, etc.
- `web/src/content/composite_boundary_fluxes.json` — same structure for the web
- `web/src/content/composite_domain_stats.json` — `inside_15x15` and `inside_15x15_anom`
- `scripts/ep_structure_analysis/SCIENTIFIC_NOTES.md` — section 4.15 summary table

#### PDF generation

Generate a professional PDF version of SCIENTIFIC_NOTES.md:

```bash
python scripts/ep_structure_analysis/generate_scientific_notes_pdf.py
```

**Requirements:**
- [Pandoc](https://pandoc.org/) (Markdown → PDF converter)
- LaTeX distribution (pdflatex, for PDF rendering)

**Install on macOS:**
```bash
brew install pandoc basictex
```

**Install on Linux:**
```bash
sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```

**Output:** `docs/scientific_notes_ep_structure.pdf`

The script:
- ✅ Automatically checks for pandoc and pdflatex
- ✅ Tries eisvogel template first (fancy), falls back to basic
- ✅ Opens the PDF automatically after generation (optional)
- ✅ Works on macOS, Linux, and Windows

#### Code verification tests

Verify that spherical grid spacing and gradient calculations work correctly:

```python
# Run test suite
import numpy as np
from step3_precompute_composites import compute_spherical_grid_spacing

# Test 1: Uniform field → zero gradient
lat = np.linspace(-30, 30, 10)
lon = np.linspace(-30, 30, 10)
dx, dy, lat_2d, lon_2d = compute_spherical_grid_spacing(lat, lon)

T = np.ones_like(lat_2d)  # uniform temperature
dT_dx = np.gradient(T, axis=1) / dx
dT_dy = np.gradient(T, axis=0) / dy[:, np.newaxis]

assert np.allclose(dT_dx, 0)
assert np.allclose(dT_dy, 0)
print("✅ Test 1 passed: uniform field → zero gradient")

# Test 2: Reversed latitude coordinates
lat_rev = np.linspace(30, -30, 10)  # decreasing (some datasets have this)
dx_rev, dy_rev, _, _ = compute_spherical_grid_spacing(lat_rev, lon)
# Should still give correct physical spacing (positive)
assert np.all(dy_rev > 0)
print("✅ Test 2 passed: reversed latitude → correct spacing")

# Test 3: Linear latitude gradient
T_linear = lat_2d.copy()  # Temperature = latitude
dT_dy_analytic = 1.0 / (111320.0)  # 1°/distance (approximate)
dT_dy_numeric = np.gradient(T_linear, axis=0) / dy[:, np.newaxis]
# Should be approximately constant
assert np.std(dT_dy_numeric) / np.mean(np.abs(dT_dy_numeric)) < 0.1
print("✅ Test 3 passed: linear gradient → consistent derivative")
```

**Expected typical values** (for sanity checks during processing):

| Diagnostic | Typical Range | Units |
|------------|---------------|-------|
| EGR (250–850 hPa) | 0.3 – 1.5 | day⁻¹ |
| PV @ 200 hPa | 1 – 5 | PVU |
| PV @ 850 hPa | 0.1 – 1.0 | PVU |
| Temperature advection @ 850 hPa | ±2 – 5 | K h⁻¹ |
| Moisture flux divergence @ 975 hPa | ±5 – 20 | g kg⁻¹ s⁻¹ |
| SLP minimum | 950 – 995 | hPa |

If values fall far outside these ranges, check:
- Coordinate orientation (latitude increasing vs. decreasing)
- Unit consistency (K vs. °C, Pa vs. hPa)
- Domain extent (should be 30° × 30° centered on cyclone)

See [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) Section 7 for full quality control details.

### Remote server execution

Steps 2–3 require significant compute/storage and should run on the remote server:

```bash
# On remote server (master.iag.usp.br)
cd /discos-varal/swell/p1-swell/danilocs/paper_energy_patterns

# Step 1 (can run locally or remotely)
python scripts/ep_structure_analysis/step1_select_ep_tracks.py

# Step 2 – download ERA5 (use nohup for long-running download)
nohup python scripts/ep_structure_analysis/step2_download_era5_parallel.py --jobs 4 &

# Monitor download progress in another terminal
python scripts/ep_structure_analysis/step2c_monitor.py --watch

# Step 3 – precompute composites (central timesteps canonical method)
nohup python scripts/ep_structure_analysis/step3_precompute_composites.py &

# Step 3 – use multiple workers for faster processing
nohup python scripts/ep_structure_analysis/step3_precompute_composites.py --jobs 8 &
```

### Transfer to local machine

```bash
# Transfer precomputed composites only (~100-300 MB vs ~30-60 GB raw ERA5)
bash scripts/ep_structure_analysis/transfer_guide_scp.sh
```

Or manually:
```bash
scp -i ~/Documents/Master/id_rsa.danilocs -C \
    danilocs@master.iag.usp.br:/discos-varal/swell/p1-swell/danilocs/paper_energy_patterns/data/era5_ep_structure/precomputed_composites_\*.nc \
    ./data/era5_ep_structure/
```

### Local execution (after transfer)

```bash
# Step 4 – create figures (canonical central timestep method)
python scripts/ep_structure_analysis/step4_create_figures.py

# Step 5 – update scientific notes with regional statistics
python scripts/ep_structure_analysis/step5_update_scientific_notes.py

# Web export – extract data for composite figures
python scripts/web/extract_composite_site_data.py
```

**Step 5 computes:**
- Global statistics (mean, std, min, max)
- Regional statistics: Full 30×30° domain, Central 15×15° LEC domain, NW/NE/SW/SE quadrants  
- Populates all `{PLACEHOLDER}` variables in SCIENTIFIC_NOTES.md
- Optionally generates PDF via pandoc

## ERA5 Variables Downloaded

**Pressure levels (hPa):** 175, 200, 225, 250, 500, 825, 850, 875, 975

| Levels | Purpose |
|--------|---------||
| 250, 850 | EGR layer bounds (vertical wind shear + static stability) |
| 175, 200, 225 | PV at 200 hPa (centered finite difference for ∂θ/∂p) |
| 825, 850, 875 | PV at 850 hPa (centered finite difference for ∂θ/∂p) |
| 850 | Temperature advection (u, v, T at 850 hPa) |
| 500 | Mid-tropospheric reference for stability profile |
| 975 | Low-level moisture flux (u, v, q at 975 hPa) |

**Pressure-level variables:** u, v, t, z (geopotential), q (specific humidity)

**Single-level variables:** msl (mean sea level pressure)

**Domain:** 30° × 30° centred on cyclone track centre during intensification

## Output

### Data
- `data/era5_ep_structure/` — raw ERA5 files (remote only) + precomputed composites
- `results/ep_structure/` — case lists, statistics

### Figures
- `figures/ep_structure/` — EP1 vs EP2 composite comparison panels

  **Total-field figures:**
  - `composite_egr.png` — Eady Growth Rate (250–850 hPa)
  - `composite_pv200.png` — PV at 200 hPa + 250 hPa wind vectors
  - `composite_pv850.png` — PV at 850 hPa + 850 hPa wind vectors
  - `composite_advT850.png` — Temperature advection at 850 hPa
  - `composite_moisture_flux.png` — Specific humidity + moisture flux divergence at 975 hPa
  - `composite_slp.png` — Sea level pressure
  - `composite_rk_criterion.png` — Rayleigh-Kuo criterion at 250 hPa
  - `composite_ke_advection.png` — Kinetic energy advection at 250 hPa
  - `composite_afc_250.png` — AFC at 250 hPa (eddy by construction)

  **Anomaly figures** (departure from 1991–2020 climatology; require `step2_1` multi-group download):
  - `composite_pv200_anom.png` — PV′ at 200 hPa + 250 hPa wind vectors
  - `composite_pv850_anom.png` — PV′ at 850 hPa + 850 hPa wind vectors
  - `composite_advT850_anom.png` — Temperature advection anomaly at 850 hPa
  - `composite_moisture_flux_anom.png` — Moisture flux divergence anomaly at 975 hPa
  - `composite_ke_advection_anom.png` — KE advection anomaly at 250 hPa
  - `composite_slp_anom.png` — SLP anomaly + 850 hPa wind vectors

  Each figure shows EP1 (left) vs EP2 (right). 15°×15° dashed box marks the LEC domain.

### Logs
- `logs/ep_structure_*.log` — detailed execution logs

## Data Storage

| Component | Size | Location |
|-----------|------|----------|
| Raw ERA5 (EP1 + EP2) | ~30-60 GB | Remote server only |
| Precomputed composites | ~100-300 MB | Local + remote |
| Figures | ~5-15 MB | Local |

## Cluster → EP Mapping

From `scripts/exploratory/analyze_ep_characteristics.py`:

| Cluster | Energy Pattern | Ck Characteristic |
|---------|---------------|-------------------|
| 0 | EP1 | Strong baroclinic and barotropic |
| 2 | EP2 | Intermediate conversions and strong imports of energy |
| 1 | EP3 | Day-to-day cyclones |

## References

- Banacos, P. C., & Schultz, D. M. (2005). The use of moisture flux convergence in forecasting convective initiation: Historical and operational perspectives. *Weather and Forecasting*, 20(3), 351–366.
- Bao, J.-W., Michelson, S. A., Persson, P. O. G., Djalalova, I. V., & Wilczak, J. M. (2002). Observed and WRF-simulated low-level winds in a high-ozone episode during the Central California Ozone Study. *Journal of Applied Meteorology and Climatology*, 41(9), 941–961.
- Čampa, J., & Wernli, H. (2012). A PV perspective on the vertical structure of mature midlatitude cyclones in the Northern Hemisphere. *Journal of the Atmospheric Sciences*, 69(2), 725–740.
- Catto, J. L., Shaffrey, L. C., & Hodges, K. I. (2010). Can climate models capture the structure of extratropical cyclones? *Journal of Climate*, 23(7), 1621–1635.
- Charney, J. G., & Stern, M. E. (1962). On the stability of internal baroclinic jets in a rotating atmosphere. *Journal of the Atmospheric Sciences*, 19(2), 159–172.
- Dacre, H. F., Hawcroft, M. K., Stringer, M. A., & Hodges, K. I. (2012). An extratropical cyclone atlas. *Bulletin of the American Meteorological Society*, 93(10), 1497–1502.
- Davis, C. A. (1992). A potential-vorticity diagnosis of the importance of initial structure and condensational heating in observed extratropical cyclogenesis. *Monthly Weather Review*, 120(11), 2409–2428.
- Davis, C. A., & Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. *Monthly Weather Review*, 119(8), 1929–1953.
- Gramcianinov, C. B., Hodges, K. I., & Camargo, R. (2019). The properties and genesis environments of South Atlantic cyclones. *Climate Dynamics*, 53, 4115–4140.
- Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Quarterly Journal of the Royal Meteorological Society*, 111(470), 877–946.
- Hoskins, B. J., & Valdes, P. J. (1990). On the existence of storm-tracks. *Journal of the Atmospheric Sciences*, 47(15), 1854–1864.
- Hoskins, B. J., & Hodges, K. I. (2005). A new perspective on Southern Hemisphere storm tracks. *Journal of Climate*, 18(20), 4108–4129.
- Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *Journal of Meteorology*, 6(2), 105–122.
- Lackmann, G. M. (2011). *Midlatitude Synoptic Meteorology: Dynamics, Analysis, and Forecasting*. American Meteorological Society.
- Lindzen, R. S., & Farrell, B. (1980). A simple approximate result for the maximum growth rate of baroclinic instabilities. *Journal of the Atmospheric Sciences*, 37(7), 1648–1654.
- Martínez-Alvarado, O., Gray, S. L., & Methven, J. (2016). Diabatic processes and the evolution of two contrasting extratropical cyclones. *Monthly Weather Review*, 144(9), 3251–3276.
- Rayleigh, Lord (1880). On the stability, or instability, of certain fluid motions. *Proceedings of the London Mathematical Society*, s1-11(1), 57–72.
- Reboita, M. S., da Rocha, R. P., Ambrizzi, T., & Sugahara, S. (2010). South Atlantic Ocean cyclogenesis climatology simulated by regional climate model (RegCM3). *Climate Dynamics*, 35, 1331–1347.
- Rossa, A. M., Wernli, H., & Davies, H. C. (2000). Growth and decay of an extra-tropical cyclone's PV-tower. *Meteorology and Atmospheric Physics*, 73, 139–156.
- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb." *Monthly Weather Review*, 108(10), 1589–1606.
- Schär, C., & Wernli, H. (1993). Structure and evolution of an isolated semi-geostrophic cyclone. *Quarterly Journal of the Royal Meteorological Society*, 119(514), 57–90.
- Simmonds, I., & Lim, E.-P. (2009). Biases in the calculation of Southern Hemisphere mean baroclinic eddy growth rate. *Geophysical Research Letters*, 36(1), L01707.
- Sinclair, M. R. (1994). An objective cyclone climatology for the Southern Hemisphere. *Monthly Weather Review*, 122(10), 2239–2256.
- Sutcliffe, R. C. (1947). A contribution to the problem of development. *Quarterly Journal of the Royal Meteorological Society*, 73(317–318), 370–383.
- Trenberth, K. E. (1978). On the interpretation of the diagnostic quasi-geostrophic omega equation. *Monthly Weather Review*, 106(1), 131–137.

---

**Author:** Danilo Couto de Souza
**Date:** February 2026
