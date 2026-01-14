import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import zipfile
import tarfile
import io
from tqdm import tqdm
from glob import glob
import scipy.integrate as integrate

# Configuration
BASE_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "ep1_vertical"
TEMP_DIR = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Data source information
ZENODO_DOI = "10.5281/zenodo.18243447"
ZENODO_RECORD_ID = "18243447"
ZENODO_URL = "https://zenodo.org/records/18243447"

print(f"Data source: Zenodo (DOI: {ZENODO_DOI})")
print(f"URL: {ZENODO_URL}")
print()

from step2_vertical_levels_analysis import get_ep1_cyclones, get_intensification_phase_times

# Get all cyclone directories
all_cyclones = glob(str(TEMP_DIR / "*_ERA5_track"))
print(f"Found LEC data for {len(all_cyclones)} cyclones.")

ep1_track_ids = get_ep1_cyclones()
print(f"Identified {len(ep1_track_ids)} EP1 cyclones from Step 1 selection.\n")

# Filter to only EP1 cyclones with LEC data
ep1_cyclones_with_lec = [int(cid.split('/')[-1].split('_')[0]) for cid in all_cyclones if int(cid.split('/')[-1].split('_')[0]) in ep1_track_ids]
print(f"Identified {len(ep1_cyclones_with_lec)} EP1 cyclones with LEC data.\n")

# Get directories for selected EP1 cyclones
selected_ep1_dirs = [cid for cid in all_cyclones if int(cid.split('/')[-1].split('_')[0]) in ep1_cyclones_with_lec]
print(f"Identified {len(selected_ep1_dirs)} EP1 cyclones with LEC data.\n")

# Loop trhough each directory and get Ca_level.csv and Ck_level.csv
ca_by_level = pd.DataFrame()
ck_by_level = pd.DataFrame()
ca_integrated = pd.DataFrame()
for ep1_dir in tqdm(selected_ep1_dirs):
    track_id = int(ep1_dir.split('/')[-1].split('_')[0])
    
    # Load Ca_level.csv
    ca_file = Path(ep1_dir) / "Ca_level.csv" / "Ca_level.csv"
    if ca_file.exists():
        ca_data = pd.read_csv(ca_file, index_col=0, parse_dates=True)
        # Get intensification phase times
        intensification_times = get_intensification_phase_times(TEMP_DIR, track_id)
        # Compute mean Ca during intensification phase
        ca_intensification = ca_data.loc[intensification_times[0]:intensification_times[1]]
        ca_mean = ca_intensification.mean()
        ca_by_level = pd.concat([ca_by_level, ca_mean.rename(track_id)], axis=1)
        # Integrate each line using the trapezoidal rule - axis=1 because each line represents a different height
        levels = ca_intensification.columns.values.astype(float)
        integrated = np.trapezoid(y=ca_intensification.values, x=levels, axis=1)
        integrated_series = pd.Series(integrated, index=ca_intensification.index)
        mean_integral = integrated_series.mean()
        # Get original integrate values
        integrated_df = pd.read_csv(Path(ep1_dir) / f"{track_id}_ERA5_track_results.csv" / f"{track_id}_ERA5_track_results.csv", index_col=0, parse_dates=True)
        original_integral = integrated_df.loc[intensification_times[0]:intensification_times[1], 'Ca'].mean()
    
    # Load Ck_level.csv
    ck_file = Path(ep1_dir) / "Ck_level.csv" / "Ck_level.csv"
    if ck_file.exists():
        ck_data = pd.read_csv(ck_file, index_col=0, parse_dates=True)
        # Get intensification phase times
        intensification_times = get_intensification_phase_times(TEMP_DIR, track_id)
        # Compute mean Ck during intensification phase
        ck_intensification = ck_data.loc[intensification_times[0]:intensification_times[1]]
        ck_mean = ck_intensification.mean()
        ck_by_level = pd.concat([ck_by_level, ck_mean.rename(track_id)], axis=1)

print("Completed loading Ca and Ck data for selected EP1 cyclones.\n")
print("Number of files with Ca_level.csv:", len(ca_by_level.columns))
print("Number of files with Ck_level.csv:", len(ck_by_level.columns))

# Compute median Ca and Ck by pressure level
pressure_levels = ca_by_level.index.tolist()
ca_median = ca_by_level.median(axis=1)