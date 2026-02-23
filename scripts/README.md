# Scripts Directory

This directory contains all analysis scripts organized by purpose.

## Structure

```
scripts/
├── utils/                              # Utility functions (data loading, preprocessing, etc.)
│   ├── __init__.py
│   ├── load_data.py                    # Functions to load data from GitHub
│   ├── preprocess_data.py              # Data preprocessing utilities
│   └── gap_statistic.py                # Gap Statistic implementation (Tibshirani et al. 2001)
│
├── setup_and_examples/                 # Setup and example scripts
│   ├── __init__.py
│   ├── verify_environment.py           # Verify package installation
│   ├── example_analysis.py             # Example analysis workflow
│   └── template_analysis.py            # Template for new analyses
│
├── exploratory/                        # Exploratory analyses (work in progress)
│   └── __init__.py
│
├── main/                               # Main analyses for the paper
│   └── __init__.py
│
├── cluster_analysis_energy_patterns/   # Energy Pattern classification (PCA + K-Means)
│   ├── step1_pca_analysis.py           # PCA by cyclone phase
│   ├── step2_determine_optimal_k.py    # Gap statistic analysis
│   ├── step3_kmeans_clustering.py      # K-Means clustering (k=3)
│   ├── step4_analyze_clusters.py       # Cluster statistics & visualization
│   ├── step5_lorenz_phasespace.py      # LPS analysis (conversions vs boundary fluxes)
│   ├── SCIENTIFIC_NOTES.md             # Complete scientific documentation
│   └── generate_scientific_notes_pdf.py # Convert to PDF
│
├── ep_structure_analysis/              # Spatial structure comparison (EP1 vs EP2)
│   ├── step1_select_ep1_ep2_cases.py   # Select cases from EP1 and EP2
│   ├── step2_download_era5.py          # Download ERA5 reanalysis data
│   ├── step3_precompute_composites.py  # Compute spatial composites
│   ├── step4_create_figures.py         # Generate composite figures
│   ├── SCIENTIFIC_NOTES.md             # Complete scientific documentation
│   └── generate_scientific_notes_pdf.py # Convert to PDF
│
├── ep1_ibc_ibt_analysis/               # EP1 vertical structure & instability
│   ├── step1_select_ep1_cases.py       # Select EP1 cases
│   ├── step2_track_ep1_cyclones.py     # Extract EP1 cyclone tracks
│   ├── step3_download_era5.py          # Download ERA5 data (7 pressure levels)
│   ├── step4_calculate_instabilities.py # Compute EGR, RK, APE diagnostics
│   ├── step4.1_consolidate_instability_results.py # Summarize statistics
│   ├── step5_create_figures.py         # Generate composite figures
│   └── generate_pdf_documentation.py   # Convert documentation to PDF
│
├── ck_subterms_analysis/               # Ck subterm analysis
│   └── ...
│
└── preprocess_data/                    # Data preprocessing scripts
    └── __init__.py
```

## Analysis Pipelines

### 1. Energy Pattern Classification (Cluster Analysis)

**Purpose:** Classify cyclones into energy patterns using energetics during intensification phase.

**Pipeline:**
1. `step1_pca_analysis.py` - Reduce dimensionality of energy variables by phase
2. `step2_determine_optimal_k.py` - Determine optimal number of clusters (k=3)
3. `step3_kmeans_clustering.py` - Classify cyclones into 3 Energy Patterns
4. `step4_analyze_clusters.py` - Compute statistics and visualize patterns
5. `step5_lorenz_phasespace.py` - Analyze energetics in Lorenz Phase Space

**Outputs:**
- `results/cluster/`: Cluster assignments, statistics, PCA loadings
- `figures/cluster/`: Composite plots, LPS diagrams
- `docs/scientific_notes_cluster_analysis.pdf`: Complete scientific documentation

**Key Results:**
- EP1 (11.6%): High conversions, energy exporters
- EP2 (25.6%): Moderate conversions, energy importers
- EP3 (62.7%): Low conversions, energy self-contained

### 2. Spatial Structure Analysis (EP1 vs EP2)

**Purpose:** Compare atmospheric structure of EP1 and EP2 cyclones using ERA5 composites.

**Pipeline:**
1. `step1_select_ep1_ep2_cases.py` - Select representative cases
2. `step2_download_era5.py` - Download ERA5 reanalysis (30° domains)
3. `step3_precompute_composites.py` - Compute spatial composites (444 EP1, 979 EP2 cases)
4. `step4_create_figures.py` - Generate diagnostic figures

**Outputs:**
- `results/ep_structure/`: Composite statistics
- `figures/ep_structure/`: Spatial composite figures (EGR, PV, advection, moisture, SLP)
- `docs/scientific_notes_ep_structure.pdf`: Complete scientific documentation

**Diagnostics:**
- Eady Growth Rate (250–850 hPa): Baroclinic instability
- Potential Vorticity (200/850 hPa): Upper/lower dynamics
- Temperature Advection (850 hPa): Thermal structure
- Moisture Flux Divergence (975 hPa): Moisture budget
- Sea Level Pressure: Horizontal structure

### 3. EP1 Vertical Structure & Instability

**Purpose:** Analyze vertical structure and instability diagnostics for EP1 cyclones.

**Pipeline:**
1. `step1_select_ep1_cases.py` - Select EP1 intensification cases
2. `step2_track_ep1_cyclones.py` - Extract cyclone tracks
3. `step3_download_era5.py` - Download ERA5 at 7 pressure levels (with validation)
4. `step4_calculate_instabilities.py` - Compute EGR, RK criterion, APE
5. `step4.1_consolidate_instability_results.py` - Summarize statistics
6. `step5_create_figures.py` - Generate three-panel composite figures

**Outputs:**
- `results/ep1_vertical/instabilities/`: Diagnostic statistics
- `figures/ep1_vertical/composites/`: Three-panel composites (Tv@350hPa, Tv@975hPa, PV+jets@250hPa)
- `docs/Chapter_EP1_Instability_Diagnostics_Scientific_Notes.pdf`: Scientific documentation

**Key Diagnostics:**
- Eady Growth Rate (EGR): Baroclinic instability intensity
- Richardson-Kuo (RK) criterion: Spatial satisfaction
- Available Potential Energy (APE): Per-area energetics

## How Imports Work

All scripts use absolute imports from the project root. Each script includes:

```python
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]  # Adjust number based on depth
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now you can import from scripts package
from scripts.utils.load_data import load_tracks
```

This ensures scripts work from **any location**:
- From project root: `python scripts/main/my_analysis.py`
- From scripts dir: `python main/my_analysis.py`
- From subdirs: `python my_analysis.py`

## Directory Setup

All scripts automatically create output directories:

```python
project_root = Path(__file__).resolve().parents[2]
FIGURES_DIR = project_root / "figures"
RESULTS_DIR = project_root / "results"
FIGURES_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
```

## Creating New Scripts

### For exploratory analyses:
1. Copy `setup_and_examples/template_analysis.py` to `exploratory/`
2. Rename and modify as needed
3. Run from anywhere: `python scripts/exploratory/your_analysis.py`

### For main paper analyses:
1. Copy `setup_and_examples/template_analysis.py` to `main/`
2. Rename and modify as needed
3. Run from anywhere: `python scripts/main/your_analysis.py`

### Adjust path depth if needed:
- Scripts in `scripts/`: `.parents[1]` (1 level up)
- Scripts in `scripts/subdir/`: `.parents[2]` (2 levels up)
- Scripts in `scripts/subdir/subsubdir/`: `.parents[3]` (3 levels up)

## Running Scripts

### From project root:
```bash
python scripts/setup_and_examples/verify_environment.py
python scripts/setup_and_examples/example_analysis.py
python scripts/main/your_analysis.py
```

### From any subdirectory:
```bash
cd scripts/main
python your_analysis.py
```

The import system automatically finds the project root!

## Available Utilities

### Data Loading (`scripts.utils.load_data`)
```python
from scripts.utils.load_data import (
    load_tracks,              # Load all cyclone tracks
    load_energy_by_cyclone,   # Load energy for one cyclone
    load_all_energy_data      # Load energy for multiple cyclones
)
```

## Adding New Utilities

Create new utility modules in `scripts/utils/`:

1. Create the file: `scripts/utils/my_utils.py`
2. Add functions to the file
3. Update `scripts/utils/__init__.py`:
   ```python
   from .my_utils import my_function
   __all__ = [..., 'my_function']
   ```
4. Use anywhere:
   ```python
   from scripts.utils.my_utils import my_function
   ```
