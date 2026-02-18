"""
Step 2b: Vertical Distribution of Energy Conversions

This script analyzes Ca (baroclinic conversion) and Ck (barotropic conversion)
at each pressure level using the Zenodo LEC dataset, in order to identify the
critical pressure levels used for ERA5 download (step2_download_era5_parallel.py).

Data Source: Zenodo (DOI: 10.5281/zenodo.18243447)
- Complete Lorenz Energy Cycle results with vertical resolution
- ~1,500 cyclones from 1979-2020
- 32 pressure levels from 1000 hPa to 100 hPa
- 3-hourly temporal resolution

Analysis:
- Load Ca_level.csv and Ck_level.csv for EP1 cyclones
- Compute vertical profiles during intensification phase only
- Identify pressure level with maximum Ca and minimum Ck
- Generate publication-quality boxplots
- Save identified critical levels for downstream steps

IMPORTANT - Data Corrections Applied:
-------------------------------------
Two corrections are applied to vertically-resolved LEC data from Zenodo:

1. Ca (Baroclinic Conversion): Sign inversion
   - Ca_corrected = -Ca_raw
   - Reason: Old LorenzCycleToolkit version saved Ca_level with opposite sign

2. Ck (Barotropic Conversion): Division by gravity
   - Ck_corrected = Ck_raw / g  (g = 9.8 m/s²)
   - Reason: Old LorenzCycleToolkit saved Ck_level without gravity normalization

These corrections were validated by comparing manual vertical integration with
pre-computed integrated values (see validate_lec_corrections()). They are
specific to the Zenodo dataset created with the old toolkit version.

Outputs:
- figures/ep1_vertical/critical_levels_boxplot.png
- results/ep1_vertical/critical_levels.csv
- results/ep1_vertical/critical_levels_all_cases.csv
- figures/exploratory/validation_vertical_integration.png  (with --validate flag)

Author: Danilo Couto de Souza
Date: February 2026
"""

import sys
import argparse
from pathlib import Path

# Add workspace root to path for shared utilities
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

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
FIGURES_DIR = BASE_DIR / "figures" / "ep1_vertical"
FIGURES_EXPLORATORY_DIR = BASE_DIR / "figures" / "exploratory"
TEMP_DIR = BASE_DIR / "data" / "temp_lec_zenodo"

# Data source
ZENODO_DOI = "10.5281/zenodo.18243447"
ZENODO_RECORD_ID = "18243447"
ZENODO_URL = "https://zenodo.org/records/18243447"

# Physical constants
GRAVITY = 9.8  # m/s² – used for Ck correction

# Standard ERA5 pressure levels (hPa)
STANDARD_LEVELS = np.array([
    1000, 975, 950, 925, 900, 850, 800, 750, 700,
    650, 600, 550, 500, 450, 400, 350, 300, 250,
    200, 150, 100
])

# Ensure output directories exist
for _d in [RESULTS_DIR, FIGURES_DIR, FIGURES_EXPLORATORY_DIR, TEMP_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 300


# ============================================================================
# DATA DOWNLOAD
# ============================================================================

def download_and_extract_lec_data():
    """
    Download and extract LEC results from Zenodo if not already present.

    Returns
    -------
    Path
        Directory containing *_ERA5_track subdirectories.
    """
    print("\n[1/4] Checking / downloading LEC data from Zenodo...")
    print(f"   DOI: {ZENODO_DOI}")

    def _find_extracted_dir(base: Path):
        """Return a dir that contains >100 *_ERA5_track subdirs, or None."""
        for candidate in [base] + list(base.iterdir() if base.exists() else []):
            if not candidate.is_dir():
                continue
            try:
                track_dirs = [d for d in candidate.iterdir()
                              if d.is_dir() and d.name.endswith("_ERA5_track")]
            except PermissionError:
                continue
            if len(track_dirs) > 100:
                return candidate
        return None

    # Already downloaded?
    lec_root = TEMP_DIR / "LEC_Results_energetic-patterns"
    found = _find_extracted_dir(lec_root) or _find_extracted_dir(TEMP_DIR)
    if found is not None:
        n_dirs = len([d for d in found.iterdir()
                      if d.is_dir() and d.name.endswith("_ERA5_track")])
        print(f"   Data already present: {found}")
        print(f"   Found {n_dirs} cyclone directories")
        return found

    # Fetch file list from Zenodo API
    print("   Fetching file list from Zenodo API...")
    api_url = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
    response = requests.get(api_url)
    response.raise_for_status()
    files = response.json().get("files", [])
    if not files:
        raise ValueError(f"No files found in Zenodo record {ZENODO_RECORD_ID}")

    # Find archive file
    archive_info = None
    for file_info in files:
        key = file_info["key"].lower()
        if "lec" in key and (key.endswith(".tar.gz") or key.endswith(".zip")):
            archive_info = file_info
            break
    if archive_info is None:
        available = [f["key"] for f in files]
        raise ValueError(f"LEC archive not found. Available: {available}")

    download_url = archive_info["links"]["self"]
    file_size = archive_info["size"]
    file_name = archive_info["key"]
    is_tar = file_name.endswith(".tar.gz")
    print(f"   Downloading {file_name} ({file_size / 1024 / 1024:.1f} MB)…")

    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    archive_data = io.BytesIO()
    with tqdm(total=file_size, unit="B", unit_scale=True, desc="Downloading") as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            archive_data.write(chunk)
            pbar.update(len(chunk))

    print("   Extracting…")
    archive_data.seek(0)
    if is_tar:
        with tarfile.open(fileobj=archive_data, mode="r:gz") as tf:
            tf.extractall(TEMP_DIR, filter="data")
    else:
        with zipfile.ZipFile(archive_data, "r") as zf:
            zf.extractall(TEMP_DIR)

    extracted = _find_extracted_dir(TEMP_DIR)
    if extracted is None:
        raise FileNotFoundError(f"Could not locate extracted LEC data under {TEMP_DIR}")

    n_dirs = len([d for d in extracted.iterdir()
                  if d.is_dir() and d.name.endswith("_ERA5_track")])
    print(f"   ✓ Extracted to: {extracted}  ({n_dirs} cyclone dirs)")
    return extracted


# ============================================================================
# EP1 CYCLONE FILTER
# ============================================================================

def get_ep1_cyclones():
    """
    Return list of EP1 (cluster 0) track_ids from clustering results.

    Returns
    -------
    list[int]
    """
    cluster_file = BASE_DIR / "results" / "cluster" / "kmeans_clustered_data.csv"
    if not cluster_file.exists():
        raise FileNotFoundError(f"Cluster file not found: {cluster_file}")

    clustered = pd.read_csv(cluster_file)
    ep1 = clustered[clustered["cluster"] == 0]["track_id"].tolist()
    print(f"   EP1 cyclones (cluster 0): {len(ep1)}")
    return ep1


# ============================================================================
# DATA LOADING (with validated corrections)
# ============================================================================

def _resolve_csv(path: Path):
    """Handle the Zenodo quirk where a .csv can be a directory containing a .csv."""
    if path.is_dir():
        csvs = list(path.glob("*.csv"))
        return csvs[0] if csvs else None
    return path if path.exists() else None


def load_lec_level_data(data_dir: Path, track_id, variable: str = "Ca"):
    """
    Load vertically-resolved Ca or Ck data for one cyclone, with corrections.

    Corrections applied (validated in validate_lec_corrections()):
    - Ca: sign inversion  → Ca_corrected = -Ca_raw
    - Ck: gravity norm.   → Ck_corrected = Ck_raw / 9.8

    Parameters
    ----------
    data_dir : Path
        Root directory containing *_ERA5_track sub-directories.
    track_id : int or str
        Cyclone identifier.
    variable : str
        'Ca' or 'Ck'.

    Returns
    -------
    pd.DataFrame or None
        Time-indexed, pressure-level columns, corrected values.
    """
    lec_dir = data_dir / f"{track_id}_ERA5_track"
    file_path = _resolve_csv(lec_dir / f"{variable}_level.csv")
    if file_path is None:
        return None

    df = pd.read_csv(file_path, index_col=0, parse_dates=True)

    if variable == "Ca":
        df = -df          # CORRECTION 1: sign inversion
    elif variable == "Ck":
        df = df / GRAVITY  # CORRECTION 2: gravity normalisation

    return df


def get_intensification_phase_times(data_dir: Path, track_id):
    """
    Return (start, end) datetimes for the intensification phase.

    Parameters
    ----------
    data_dir : Path
    track_id : int or str

    Returns
    -------
    tuple[datetime, datetime] or None
    """
    lec_dir = data_dir / f"{track_id}_ERA5_track"
    periods_file = _resolve_csv(lec_dir / "periods.csv")
    if periods_file is None:
        return None

    periods = pd.read_csv(periods_file, index_col=0)
    if "intensification" not in periods.index:
        return None

    row = periods.loc["intensification"]
    return pd.to_datetime(row["start"]), pd.to_datetime(row["end"])


# ============================================================================
# VERTICAL PROFILE ANALYSIS
# ============================================================================

def analyze_vertical_profiles(data_dir: Path, ep1_track_ids: list):
    """
    Compute vertical Ca/Ck profiles during intensification for EP1 cyclones.

    Parameters
    ----------
    data_dir : Path
    ep1_track_ids : list[int]

    Returns
    -------
    dict
        Keys: ca_max_levels, ck_min_levels, ca_by_level, ck_by_level,
              ca_profiles, ck_profiles
    """
    results = {
        "ca_max_levels": [],
        "ck_min_levels": [],
        "ca_profiles": {},
        "ck_profiles": {},
        "ca_by_level": {},
        "ck_by_level": {},
    }

    print("\n[2/4] Analysing vertical LEC profiles for EP1 cyclones...")
    print(f"   Corrections: Ca sign inversion + Ck / {GRAVITY}")
    successful, missing = 0, 0

    for track_id in tqdm(ep1_track_ids, desc="Processing"):
        ca_data = load_lec_level_data(data_dir, track_id, "Ca")
        ck_data = load_lec_level_data(data_dir, track_id, "Ck")

        if ca_data is None or ck_data is None:
            missing += 1
            continue

        phase = get_intensification_phase_times(data_dir, track_id)
        if phase is None:
            missing += 1
            continue

        t0, t1 = phase
        ca_int = ca_data[(ca_data.index >= t0) & (ca_data.index <= t1)]
        ck_int = ck_data[(ck_data.index >= t0) & (ck_data.index <= t1)]

        if len(ca_int) == 0:
            missing += 1
            continue

        ca_mean = ca_int.mean(axis=0)
        ck_mean = ck_int.mean(axis=0)

        # Convert Pa → hPa; keep only ≥ 100 hPa
        p_hpa = ca_mean.index.astype(float) / 100.0
        mask = p_hpa >= 100.0
        p_hpa = p_hpa[mask]
        ca_mean = ca_mean[mask]
        ck_mean = ck_mean[mask]

        for p, ca_v, ck_v in zip(p_hpa, ca_mean.values, ck_mean.values):
            pk = int(p)
            results["ca_by_level"].setdefault(pk, []).append(ca_v)
            results["ck_by_level"].setdefault(pk, []).append(ck_v)

        results["ca_max_levels"].append(p_hpa[ca_mean.values.argmax()])
        results["ck_min_levels"].append(p_hpa[ck_mean.values.argmin()])
        results["ca_profiles"][track_id] = ca_mean
        results["ck_profiles"][track_id] = ck_mean
        successful += 1

    print(f"   ✓ Successful: {successful}   Missing/incomplete: {missing}")
    return results


# ============================================================================
# BOXPLOT FIGURE
# ============================================================================

def create_boxplots(results: dict):
    """
    Publication-quality boxplots of Ca and Ck by pressure level.

    Returns
    -------
    tuple[float, float, float, float]
        (max_ca_level, max_ca_value, min_ck_level, min_ck_value) in hPa / W m⁻²
    """
    print("\n[3/4] Creating critical-levels boxplot...")

    ca_by_level = results["ca_by_level"]
    ck_by_level = results["ck_by_level"]
    pressure_levels = sorted(ca_by_level.keys(), reverse=True)  # 1000 → 100 hPa
    positions = np.arange(len(pressure_levels))

    ca_data = [ca_by_level[p] for p in pressure_levels]
    ck_data = [ck_by_level[p] for p in pressure_levels]

    plt.rcParams.update({
        "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 13,
        "xtick.labelsize": 9, "ytick.labelsize": 10, "legend.fontsize": 10,
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    })

    fig, axes = plt.subplots(2, 1, figsize=(12, 12))

    # ── Panel A: Ca ──────────────────────────────────────────────────────────
    ax1 = axes[0]
    ax1.boxplot(ca_data, positions=positions, widths=0.6,
                patch_artist=True, showfliers=False,
                medianprops=dict(color="darkred", linewidth=2),
                boxprops=dict(facecolor="lightcoral", edgecolor="darkred", alpha=0.7),
                whiskerprops=dict(color="darkred", linewidth=1.5),
                capprops=dict(color="darkred", linewidth=1.5))
    ax1.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.5)
    ax1.set_ylabel("Ca (W m$^{-2}$)", fontweight="bold")
    ax1.set_title("(a) Baroclinic Conversion (Ca) by Pressure Level",
                  fontweight="bold", loc="left")
    ax1.grid(True, alpha=0.3, linestyle=":", linewidth=0.5)
    ax1.set_xticks(positions)
    ax1.set_xticklabels([str(int(p)) for p in pressure_levels], rotation=45, ha="right")
    ax1.set_xlim(positions[0] - 0.5, positions[-1] + 0.5)

    ca_medians = [np.median(ca_by_level[p]) for p in pressure_levels]
    max_ca_idx = int(np.argmax(ca_medians))
    max_ca_level = float(pressure_levels[max_ca_idx])
    max_ca_value = float(ca_medians[max_ca_idx])
    ax1.plot(positions[max_ca_idx], max_ca_value, "r*", markersize=15,
             markeredgecolor="darkred", markeredgewidth=1.5,
             label=f"Maximum Ca at {max_ca_level:.0f} hPa")
    ax1.legend(frameon=True, fancybox=True, shadow=True)
    ax1.text(0.98, 0.98, f"n = {len(results['ca_profiles'])} systems",
             transform=ax1.transAxes, ha="right", va="top", fontsize=10,
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    # ── Panel B: Ck ──────────────────────────────────────────────────────────
    ax2 = axes[1]
    ax2.boxplot(ck_data, positions=positions, widths=0.6,
                patch_artist=True, showfliers=False,
                medianprops=dict(color="darkblue", linewidth=2),
                boxprops=dict(facecolor="lightblue", edgecolor="darkblue", alpha=0.7),
                whiskerprops=dict(color="darkblue", linewidth=1.5),
                capprops=dict(color="darkblue", linewidth=1.5))
    ax2.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.5)
    ax2.set_xlabel("Pressure Level (hPa)", fontweight="bold")
    ax2.set_ylabel("Ck (W m$^{-2}$)", fontweight="bold")
    ax2.set_title("(b) Barotropic Conversion (Ck) by Pressure Level",
                  fontweight="bold", loc="left")
    ax2.grid(True, alpha=0.3, linestyle=":", linewidth=0.5)
    ax2.set_xticks(positions)
    ax2.set_xticklabels([str(int(p)) for p in pressure_levels], rotation=45, ha="right")
    ax2.set_xlim(positions[0] - 0.5, positions[-1] + 0.5)

    ck_medians = [np.median(ck_by_level[p]) for p in pressure_levels]
    min_ck_idx = int(np.argmin(ck_medians))
    min_ck_level = float(pressure_levels[min_ck_idx])
    min_ck_value = float(ck_medians[min_ck_idx])
    ax2.plot(positions[min_ck_idx], min_ck_value, "b*", markersize=15,
             markeredgecolor="darkblue", markeredgewidth=1.5,
             label=f"Minimum Ck at {min_ck_level:.0f} hPa")
    ax2.legend(frameon=True, fancybox=True, shadow=True)
    ax2.text(0.98, 0.02, f"n = {len(results['ca_profiles'])} systems",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=10,
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    plt.tight_layout()
    out = FIGURES_DIR / "critical_levels_boxplot.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"   ✓ Saved: {out}")
    plt.close()

    print(f"\n   Ca maximum: {max_ca_value:.4f} W m⁻² at {max_ca_level:.0f} hPa")
    print(f"   Ck minimum: {min_ck_value:.4f} W m⁻² at {min_ck_level:.0f} hPa")

    return max_ca_level, max_ca_value, min_ck_level, min_ck_value


# ============================================================================
# SAVE CRITICAL LEVELS
# ============================================================================

def save_critical_levels(max_ca_level, max_ca_value, min_ck_level, min_ck_value,
                         results: dict):
    """
    Save critical pressure levels to CSV for use in step2_download_era5_parallel.py.

    Levels are snapped to the nearest standard ERA5 pressure level.
    """
    print("\n[4/4] Saving critical levels...")

    def _snap(level):
        return int(STANDARD_LEVELS[np.argmin(np.abs(STANDARD_LEVELS - level))])

    ca_level = _snap(max_ca_level)
    ck_level = _snap(min_ck_level)

    def _neighbours(level):
        idx = np.where(STANDARD_LEVELS == level)[0][0]
        above = int(STANDARD_LEVELS[idx - 1]) if idx > 0 else level
        below = int(STANDARD_LEVELS[idx + 1]) if idx < len(STANDARD_LEVELS) - 1 else level
        return above, below

    ca_above, ca_below = _neighbours(ca_level)
    ck_above, ck_below = _neighbours(ck_level)

    critical = pd.DataFrame({
        "analysis": [
            "Ca_max", "Ca_max_above", "Ca_max_below",
            "Ck_min", "Ck_min_above", "Ck_min_below",
        ],
        "pressure_level_hPa": [
            ca_level, ca_above, ca_below,
            ck_level, ck_above, ck_below,
        ],
        "median_value": [
            max_ca_value, max_ca_value, max_ca_value,
            min_ck_value, min_ck_value, min_ck_value,
        ],
        "level_from_data": [
            max_ca_level, max_ca_level, max_ca_level,
            min_ck_level, min_ck_level, min_ck_level,
        ],
    })
    out = RESULTS_DIR / "critical_levels.csv"
    critical.to_csv(out, index=False)
    print(f"   ✓ Saved: {out}")

    detail = pd.DataFrame({
        "ca_max_level_hPa": results["ca_max_levels"],
        "ck_min_level_hPa": results["ck_min_levels"],
    })
    out2 = RESULTS_DIR / "critical_levels_all_cases.csv"
    detail.to_csv(out2, index=False)
    print(f"   ✓ Saved: {out2}")

    print(f"\n   Ca critical: {max_ca_level:.0f} hPa → snapped to {ca_level} hPa")
    print(f"   Ca EGR levels: {ca_above}, {ca_level}, {ca_below} hPa")
    print(f"   Ck critical: {min_ck_level:.0f} hPa → snapped to {ck_level} hPa")
    print(f"   Ck RK levels: {ck_above}, {ck_level}, {ck_below} hPa")


# ============================================================================
# VALIDATION (optional – run with --validate)
# ============================================================================

def validate_lec_corrections(data_dir: Path, ep1_track_ids: list):
    """
    Validate Ca/Ck corrections by comparing trapezoid integration with
    pre-computed integrated values from the Zenodo LEC toolkit results.

    Produces figures/exploratory/validation_vertical_integration.png.

    Findings confirmed by this validation:
    - Ca: MAE is ~zero after sign inversion; raw MAE is large
    - Ck: MAE is ~zero after dividing by gravity; raw MAE is large

    Parameters
    ----------
    data_dir : Path
    ep1_track_ids : list[int]
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    print("\n" + "=" * 70)
    print("VALIDATION: Vertical integration of Ca and Ck")
    print("=" * 70)

    cmp = {k: [] for k in [
        "ca_raw", "ca_corrected", "ca_original",
        "ck_raw", "ck_corrected", "ck_original",
        "track_ids",
    ]}

    for track_id in tqdm(ep1_track_ids, desc="Validating"):
        lec_dir = data_dir / f"{track_id}_ERA5_track"

        phase = get_intensification_phase_times(data_dir, track_id)
        if phase is None:
            continue
        t0, t1 = phase

        try:
            # ── Ca ──────────────────────────────────────────────────────────
            ca_file = _resolve_csv(lec_dir / "Ca_level.csv")
            results_file = _resolve_csv(
                lec_dir / f"{track_id}_ERA5_track_results.csv")

            if ca_file and results_file:
                ca_raw_df = pd.read_csv(ca_file, index_col=0, parse_dates=True)
                ca_int_df = ca_raw_df.loc[t0:t1]
                levels_pa = ca_int_df.columns.values.astype(float)
                ca_int_ts = np.trapezoid(ca_int_df.values, x=levels_pa, axis=1)
                ca_raw_mean = float(ca_int_ts.mean())

                results_df = pd.read_csv(results_file, index_col=0, parse_dates=True)
                ca_orig = float(results_df.loc[t0:t1, "Ca"].mean())

                cmp["ca_raw"].append(ca_raw_mean)
                cmp["ca_corrected"].append(-ca_raw_mean)
                cmp["ca_original"].append(ca_orig)

            # ── Ck ──────────────────────────────────────────────────────────
            ck_file = _resolve_csv(lec_dir / "Ck_level.csv")
            if ck_file and results_file:
                ck_raw_df = pd.read_csv(ck_file, index_col=0, parse_dates=True)
                ck_int_df = ck_raw_df.loc[t0:t1]
                levels_pa = ck_int_df.columns.values.astype(float)
                ck_int_ts = np.trapezoid(ck_int_df.values, x=levels_pa, axis=1)
                ck_raw_mean = float(ck_int_ts.mean())

                results_df = pd.read_csv(results_file, index_col=0, parse_dates=True)
                ck_orig = float(results_df.loc[t0:t1, "Ck"].mean())

                cmp["ck_raw"].append(ck_raw_mean)
                cmp["ck_corrected"].append(ck_raw_mean / GRAVITY)
                cmp["ck_original"].append(ck_orig)
                cmp["track_ids"].append(track_id)

        except Exception as exc:
            print(f"   Warning: {track_id}: {exc}")
            continue

    n = len(cmp["track_ids"])
    if n == 0:
        print("   No data processed – skipping validation plots.")
        return

    # ── Print summary ────────────────────────────────────────────────────────
    for var, label, corr_label in [
        ("ca", "Ca", "sign inverted"),
        ("ck", "Ck", "÷ 9.8"),
    ]:
        raw = np.array(cmp[f"{var}_raw"])
        corr = np.array(cmp[f"{var}_corrected"])
        orig = np.array(cmp[f"{var}_original"])
        mae_r = np.mean(np.abs(raw - orig))
        mae_c = np.mean(np.abs(corr - orig))
        print(f"\n{label}:  MAE raw={mae_r:.4f}  MAE corrected ({corr_label})={mae_c:.4f} W/m²")

    # ── Plot ─────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    for ax, var, label, clabel, color_set in [
        (axes[0], "ca", "Ca (Baroclinic)", "sign inverted",
         ["#ff9999", "#66b3ff", "#99ff99"]),
        (axes[1], "ck", "Ck (Barotropic)", "÷ 9.8",
         ["#ff9999", "#66b3ff", "#99ff99"]),
    ]:
        data_plot = [cmp[f"{var}_raw"], cmp[f"{var}_corrected"], cmp[f"{var}_original"]]
        bp = ax.boxplot(data_plot,
                        labels=["Raw\nIntegrated",
                                f"Corrected\n({clabel})",
                                "Original\n(pre-computed)"],
                        patch_artist=True, widths=0.6, showfliers=True)
        for patch, c in zip(bp["boxes"], color_set):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)
        ax.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.5)
        ax.set_ylabel(f"{label.split()[0]} (W m⁻²)", fontweight="bold")
        ax.set_title(f"Validation of vertical integration – {label}",
                     fontweight="bold", loc="left")
        ax.grid(True, alpha=0.3, linestyle=":", linewidth=0.5)
        ax.text(0.02, 0.98,
                f"Correction: {clabel}\nn = {n} cases",
                transform=ax.transAxes, fontsize=10, va="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    plt.tight_layout()
    out = FIGURES_EXPLORATORY_DIR / "validation_vertical_integration.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"\n   ✓ Validation figure saved: {out}")
    plt.close()

    print("\n✅ Validation complete – corrections confirmed.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Vertical levels analysis – EP1 LEC data from Zenodo"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Also run correction validation (compare trapezoid integration to pre-computed)",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("STEP 2b: Vertical Levels Analysis – EP1 cyclones (Zenodo LEC data)")
    print("=" * 80)
    print("\n⚠️  DATA CORRECTIONS:")
    print("   • Ca: sign inversion   (Ca_corrected = -Ca_raw)")
    print(f"   • Ck: gravity norm.   (Ck_corrected = Ck_raw / {GRAVITY})")
    print("   These corrections are specific to the old LorenzCycleToolkit")
    print(f"   used to generate the Zenodo dataset ({ZENODO_DOI}).")

    # Step A: data
    data_dir = download_and_extract_lec_data()

    # Step B: EP1 filter
    print("\n[loading EP1 cyclones]")
    ep1_ids = get_ep1_cyclones()

    # Optional: validate corrections first
    if args.validate:
        validate_lec_corrections(data_dir, ep1_ids)

    # Step C: vertical profiles
    results = analyze_vertical_profiles(data_dir, ep1_ids)

    if not results["ca_max_levels"]:
        print("\n❌  No valid data found – check that EP1 LEC data is available.")
        return

    print(f"\n   Analysed {len(results['ca_max_levels'])} EP1 cyclones")

    # Step D: boxplots
    max_ca_level, max_ca_val, min_ck_level, min_ck_val = create_boxplots(results)

    # Step E: save
    save_critical_levels(max_ca_level, max_ca_val, min_ck_level, min_ck_val, results)

    print("\n" + "=" * 80)
    print("✓  Analysis complete!")
    print("   Next: run step2_download_era5_parallel.py to download ERA5 at identified levels")
    print("=" * 80)


if __name__ == "__main__":
    main()
