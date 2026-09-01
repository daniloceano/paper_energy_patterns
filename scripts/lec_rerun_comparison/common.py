#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.py — Shared definitions for the legacy vs corrected LEC comparison.

Holds the LEC term taxonomy (groups, display labels, units), the canonical
paths, and small helpers used by every step of this analysis.

Sign convention (same as de Souza et al. 2025, Clim. Dyn.):
    C_A > 0  : A_Z -> A_E   (baroclinic conversion feeding the eddy)
    C_K < 0  : K_Z -> K_E   (barotropic conversion feeding the eddy)
    B* > 0   : import into the computational domain
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = Path("/p1-swell/danilocs/lec_climatology_corrected_v2")
LEGACY_CACHE = BASE_DIR / "data" / "energy_cache.parquet"
LEGACY_RESULTS = BASE_DIR / "data" / "temp_lec_zenodo" / "LEC_Results_energetic-patterns"

RESULTS_DIR = BASE_DIR / "results" / "lec_rerun_comparison"
FIGURES_DIR = BASE_DIR / "figures" / "lec_rerun_comparison"
REPORT_PATH = BASE_DIR / "docs" / "lec_rerun_comparison_report.md"

CORRECTED_MEANS = RESULTS_DIR / "corrected_phase_means.parquet"
PAIRED_TABLE = RESULTS_DIR / "paired_terms.parquet"
COVERAGE_JSON = RESULTS_DIR / "coverage.json"
TERM_SUMMARY = RESULTS_DIR / "term_change_summary.csv"
PHASE_SUMMARY = RESULTS_DIR / "term_change_by_phase.csv"
REGIME_SUMMARY = RESULTS_DIR / "conversion_regime.csv"

PHASES = ["incipient", "intensification", "mature", "decay"]

# Term groups. Each entry: (ordered term list, unit label).
GROUPS: dict[str, tuple[list[str], str]] = {
    "energy": (["Az", "Ae", "Kz", "Ke"], r"J m$^{-2}$"),
    "conversion": (["Cz", "Ca", "Ck", "Ce"], r"W m$^{-2}$"),
    "generation": (["Gz", "Ge"], r"W m$^{-2}$"),
    "boundary": (["BAz", "BAe", "BKz", "BKe", "BΦZ", "BΦE"], r"W m$^{-2}$"),
    "budget": (
        [
            "∂Az/∂t (finite diff.)",
            "∂Ae/∂t (finite diff.)",
            "∂Kz/∂t (finite diff.)",
            "∂Ke/∂t (finite diff.)",
        ],
        r"W m$^{-2}$",
    ),
    "residual": (["RGz", "RKz", "RGe", "RKe"], r"W m$^{-2}$"),
}

GROUP_TITLES = {
    "energy": "Energy reservoirs",
    "conversion": "Conversion terms",
    "generation": "Generation terms",
    "boundary": "Boundary (transport) terms",
    "budget": "Energy budget tendencies",
    "residual": "Residual terms",
}

# Terms produced only by the corrected toolkit; reported, never paired.
NEW_ONLY_TERMS = ["C_overturning", "M"]

LABELS = {
    "Az": r"$A_Z$", "Ae": r"$A_E$", "Kz": r"$K_Z$", "Ke": r"$K_E$",
    "Cz": r"$C_Z$", "Ca": r"$C_A$", "Ck": r"$C_K$", "Ce": r"$C_E$",
    "Gz": r"$G_Z$", "Ge": r"$G_E$",
    "BAz": r"$BA_Z$", "BAe": r"$BA_E$", "BKz": r"$BK_Z$", "BKe": r"$BK_E$",
    "BΦZ": r"$B\Phi_Z$", "BΦE": r"$B\Phi_E$",
    "∂Az/∂t (finite diff.)": r"$\partial A_Z/\partial t$",
    "∂Ae/∂t (finite diff.)": r"$\partial A_E/\partial t$",
    "∂Kz/∂t (finite diff.)": r"$\partial K_Z/\partial t$",
    "∂Ke/∂t (finite diff.)": r"$\partial K_E/\partial t$",
    "RGz": r"$R_{G_Z}$", "RKz": r"$R_{K_Z}$",
    "RGe": r"$R_{G_E}$", "RKe": r"$R_{K_E}$",
    "C_overturning": r"$C_{ovt}$", "M": r"$M$",
}

ALL_TERMS = [term for terms, _ in GROUPS.values() for term in terms]
TERM_GROUP = {term: group for group, (terms, _) in GROUPS.items() for term in terms}
TERM_UNIT = {term: unit for terms, unit in GROUPS.values() for term in terms}

LEGACY_COLOR = "#9E7BB5"
CORRECTED_COLOR = "#4C9F70"

# Colours for the before/after Lorenz diagram, where hue encodes the version
# rather than the sign (sign is carried by the arrow direction).
DIAGRAM_LEGACY_COLOR = "#3B3B3B"
DIAGRAM_CORRECTED_COLOR = "#D1332E"

# A term counts as changed when the typical change reaches 1% of its own
# typical magnitude, or when it changes sign in more than 0.5% of the samples.
CHANGE_THRESHOLD = 0.01
FLIP_THRESHOLD = 0.5


def label(term: str) -> str:
    """LaTeX display label for a term."""
    return LABELS.get(term, term)


def nested_csv(path: Path) -> Path:
    """Resolve the Zenodo archive quirk where ``x.csv`` may be a directory."""
    inner = path / path.name
    return inner if inner.is_file() else path


def split_changed(summary) -> tuple[list[str], list[str]]:
    """Split a step-3 summary frame into (changed, unchanged) term lists."""
    mask = (summary["normalized_change"] > CHANGE_THRESHOLD) | (
        summary["sign_flip_pct"] > FLIP_THRESHOLD
    )
    return summary[mask]["term"].tolist(), summary[~mask]["term"].tolist()


def phase_of(period: str) -> str | None:
    """Map a period name (``decay 2``) onto its main phase (``decay``)."""
    raw = str(period).strip().lower()
    return next((phase for phase in PHASES if raw.startswith(phase)), None)
