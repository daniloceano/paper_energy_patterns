# Scripts Directory

This directory contains all analysis scripts organized by purpose.

## Structure

```
scripts/
├── utils/                  # Utility functions (data loading, clustering, etc.)
│   ├── __init__.py
│   ├── load_data.py       # Functions to load data from GitHub
│   ├── preprocess_data.py # Data preprocessing utilities
│   └── gap_statistic.py   # Gap Statistic implementation (Tibshirani et al. 2001)
│
├── setup_and_examples/    # Setup and example scripts
│   ├── __init__.py
│   ├── verify_environment.py   # Verify package installation
│   ├── example_analysis.py     # Example analysis workflow
│   └── template_analysis.py    # Template for new analyses
│
├── exploratory/           # Exploratory analyses (work in progress)
│   └── __init__.py
│
└── main/                  # Main analyses for the paper
    └── __init__.py
```

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
