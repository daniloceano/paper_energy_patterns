"""
I/O utilities for the LEC–field dependence analysis pipeline.

Centralises file paths, data loading, and the Zenodo directory quirk
handler used throughout the pipeline steps.

Author: Danilo Couto de Souza
Date: April 2026
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict

# ---------------------------------------------------------------------------
# Canonical paths (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_FILE = PROJECT_ROOT / "results" / "cluster" / "kmeans_clustered_data.csv"
EP_CASES_DIR = PROJECT_ROOT / "results" / "ep_structure"
LEC_ZENODO_DIR = PROJECT_ROOT / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"
ERA5_EP_DIR = PROJECT_ROOT / "data" / "era5_ep_structure"

# Allow isolated test runs by setting LEC_TEST_RESULTS_DIR in the environment.
# The smoke test (run_smoke_test.sh) uses this to redirect outputs to a temp
# directory so it never touches the production results/ folder.
_test_results_override = os.environ.get("LEC_TEST_RESULTS_DIR", "")
RESULTS_DIR = Path(_test_results_override) if _test_results_override else \
    PROJECT_ROOT / "results" / "lec_field_dependence"

FIGURES_DIR = PROJECT_ROOT / "figures" / "lec_field_dependence"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure output dirs exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Zenodo quirk handler
# ---------------------------------------------------------------------------

def resolve_csv(path: Path) -> Optional[Path]:
    """
    Handle Zenodo quirk where a ``*.csv`` path is actually a directory
    containing a CSV of the same name.

    Parameters
    ----------
    path : Path
        Expected CSV file path.

    Returns
    -------
    Path or None
        Resolved path to the actual CSV, or None if not found.
    """
    if path.is_dir():
        inner = path / path.name
        if inner.exists():
            return inner
        csvs = list(path.glob("*.csv"))
        return csvs[0] if csvs else None
    return path if path.exists() else None


# ---------------------------------------------------------------------------
# EP cases loaders
# ---------------------------------------------------------------------------

def load_ep_cases(ep: int) -> pd.DataFrame:
    """Load filtered EP cases from results/ep_structure/."""
    from scripts.utils.ep_mapping import EP_ABBREVS
    abbrev = EP_ABBREVS[ep]
    path = EP_CASES_DIR / f"{abbrev}_cases.csv"
    return pd.read_csv(path)


def load_all_ep_cases() -> pd.DataFrame:
    """Load and concatenate EP1, EP2, EP3 cases."""
    from scripts.utils.ep_mapping import ALL_EPS
    frames = []
    for ep in ALL_EPS:
        df = load_ep_cases(ep)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_cluster_assignments() -> pd.DataFrame:
    """Load cluster assignments with EP labels."""
    from scripts.utils.ep_mapping import CLUSTER_TO_EP
    df = pd.read_csv(CLUSTER_FILE)
    df["ep"] = df["cluster"].map(CLUSTER_TO_EP)
    return df


# ---------------------------------------------------------------------------
# LEC data loader (per-cyclone, phase-averaged from GitHub)
# ---------------------------------------------------------------------------

def _select_central_indices(n: int) -> list:
    """
    Select central timestep indices using the canonical ep_structure rule.

    Consistent with scripts/utils/timestep_selection.py::select_central_timesteps:
      - N odd  → 3 central: [N//2 - 1, N//2, N//2 + 1]
      - N even → 2 central: [N//2 - 1, N//2]
      - N <= 3 → all
    """
    if n <= 3:
        return list(range(n))
    mid = n // 2
    if n % 2 == 1:
        return [mid - 1, mid, mid + 1]
    else:
        return [mid - 1, mid]


def load_lec_from_zenodo(track_id: str) -> Optional[pd.DataFrame]:
    """
    Load LEC time series from Zenodo and return the mean over the central
    timesteps of the intensification phase.

    Uses the canonical ep_structure temporal selection:
      - Odd  N timesteps → 3 central (indices N//2-1, N//2, N//2+1)
      - Even N timesteps → 2 central (indices N//2-1, N//2)
      - N ≤ 3            → all timesteps

    This ensures temporal consistency with the ERA5 dynamic fields, which
    are extracted at the single central timestep of the intensification phase.

    Parameters
    ----------
    track_id : str
        Cyclone ID (e.g., '19790135').

    Returns
    -------
    pd.DataFrame or None
        Single-row DataFrame with columns = LEC terms,
        values = mean over central timesteps of intensification.
        Returns None if data unavailable or window is empty.
    """
    lec_dir = LEC_ZENODO_DIR / f"{track_id}_ERA5_track"
    if not lec_dir.exists():
        return None

    # Load periods
    periods_path = resolve_csv(lec_dir / "periods.csv")
    if periods_path is None:
        return None
    periods = pd.read_csv(periods_path, index_col=0)
    if "intensification" not in periods.index:
        return None

    intens = periods.loc["intensification"]
    t_start = pd.to_datetime(intens["start"])
    t_end = pd.to_datetime(intens["end"])

    # Load full LEC results
    results_name = f"{track_id}_ERA5_track_results.csv"
    results_path = resolve_csv(lec_dir / results_name)
    if results_path is None:
        return None

    try:
        df = pd.read_csv(results_path, index_col=0)
    except Exception:
        return None

    df.index = pd.to_datetime(df.index)
    # Filter to intensification phase
    mask = (df.index >= t_start) & (df.index <= t_end)
    df_intens = df.loc[mask]

    if len(df_intens) == 0:
        return None

    # Select central timesteps (canonical ep_structure rule)
    central_idx = _select_central_indices(len(df_intens))
    df_central = df_intens.iloc[central_idx]

    mean_vals = df_central.mean(numeric_only=True)
    result = mean_vals.to_frame().T
    result.index = [track_id]
    result.index.name = "track_id"
    return result


# LEC term names (canonical order, from the results CSV)
LEC_TERMS_FULL = [
    "Az", "Ae", "Kz", "Ke",
    "Cz", "Ca", "Ck", "Ce",
    "BAz", "BAe", "BKz", "BKe",
    "BΦZ", "BΦE",
    "Gz", "Ge",
    "∂Az/∂t (finite diff.)", "∂Ae/∂t (finite diff.)",
    "∂Kz/∂t (finite diff.)", "∂Ke/∂t (finite diff.)",
    "RGz", "RKz", "RGe", "RKe",
]

# Subset of core LEC terms used in the original PCA-clustering
# Source: scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py → ENERGY_VARS
# Exactly 7 terms, used across 4 phases (28 features) for the K-Means Energy Pattern classification.
# This is the **canonical** set for the article analysis.
LEC_TERMS_CORE = [
    "Ca",   # Zonal APE → Eddy APE (baroclinic conversion — dominant in intensification)
    "Ck",   # Eddy KE → Zonal KE (barotropic conversion)
    "BAe",  # Boundary flux of eddy APE
    "BKe",  # Boundary flux of eddy KE
    "Ae",   # Eddy available potential energy reservoir
    "Ke",   # Eddy kinetic energy reservoir
    "Ge",   # Generation of eddy APE
]



# ---------------------------------------------------------------------------
# Dynamic field variable registry
# ---------------------------------------------------------------------------

# Fields of interest for the main PREDEP analysis (dynamic fields)
# Maps a human-readable key → NetCDF variable name in the composite files
DYNAMIC_FIELDS_ABSOLUTE = {
    "pv_850":       "pv_850",
    "pv_200":       "pv_200",
    "adv_T_850":    "adv_T_850",
    "afc_250":      "afc_250",
    "ke_adv_250":   "ke_adv_250",
}

# EPALL-relative anomaly versions (suffix _minus_epall in composite files)
DYNAMIC_FIELDS_ANOMALY = {
    "pv_850_minus_epall":    "pv_850_minus_epall",
    "pv_200_minus_epall":    "pv_200_minus_epall",
    "adv_T_850_minus_epall": "adv_T_850_minus_epall",
    "afc_250_minus_epall":   "afc_250_minus_epall",
    "ke_adv_250_minus_epall":"ke_adv_250_minus_epall",
}

# Combined for convenience
DYNAMIC_FIELDS_ALL = {**DYNAMIC_FIELDS_ABSOLUTE, **DYNAMIC_FIELDS_ANOMALY}


# ---------------------------------------------------------------------------
# Human-readable label formatting
# ---------------------------------------------------------------------------
# Maps internal field keys → short scientific labels for figures
FIELD_DISPLAY_NAMES: Dict[str, str] = {
    "pv_850":                   "PV 850",
    "pv_200":                   "PV 200",
    "adv_T_850":                "AdvT 850",
    "afc_250":                  "AFC 250",
    "ke_adv_250":               "KE adv 250",
    "pv_850_anom_epall":        "PV 850 anom",
    "pv_200_anom_epall":        "PV 200 anom",
    "adv_T_850_anom_epall":     "AdvT 850 anom",
    "afc_250_anom_epall":       "AFC 250 anom",
    "ke_adv_250_anom_epall":    "KE adv 250 anom",
    # Legacy keys (composite files use _minus_epall)
    "pv_850_minus_epall":       "PV 850 anom",
    "pv_200_minus_epall":       "PV 200 anom",
    "adv_T_850_minus_epall":    "AdvT 850 anom",
    "afc_250_minus_epall":      "AFC 250 anom",
    "ke_adv_250_minus_epall":   "KE adv 250 anom",
}

FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "domain_mean":    "domain mean",
    "centre_value":   "centre value",
    "border_north":   "border N",
    "border_south":   "border S",
    "border_east":    "border E",
    "border_west":    "border W",
    "contrast_ew":    "E\u2013W contrast",
    "contrast_sn":    "S\u2013N contrast",
    "quadrant_ne":    "NE quadrant",
    "quadrant_nw":    "NW quadrant",
    "quadrant_se":    "SE quadrant",
    "quadrant_sw":    "SW quadrant",
    "domain_abs_mean": "domain |mean|",
}


def format_display_label(field_key: str, feature: str) -> str:
    """
    Build a human-readable label from a field key and feature name.

    Examples
    --------
    >>> format_display_label("pv_850", "domain_mean")
    'PV 850 — domain mean'
    >>> format_display_label("afc_250_anom_epall", "contrast_sn")
    'AFC 250 anom — S–N contrast'
    """
    field_label = FIELD_DISPLAY_NAMES.get(field_key, field_key)
    feat_label = FEATURE_DISPLAY_NAMES.get(feature, feature)
    return f"{field_label} — {feat_label}"
