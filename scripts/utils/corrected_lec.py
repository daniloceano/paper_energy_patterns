#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
corrected_lec.py — Single access point to the corrected LEC climatology.

Every downstream analysis of this paper must read its energetics through this
module. The corrected rerun (``scripts/lec_climatology_rerun``, LorenzCycleToolKit
2.0.0, pinned commit ``d38cda7e``) is the only scientific truth for the article;
the legacy Zenodo archive and ``data/energy_cache.parquet`` are kept solely as
the *before* side of ``scripts/lec_rerun_comparison`` and must never feed a
result, table, or figure again.

Why a shared module
-------------------
The legacy scripts each re-implemented the vertical-level conventions inline,
and they did not agree with each other. The conventions below were verified
empirically against the pinned toolkit output and are re-checkable at any time
with :func:`verify_conventions`:

1. Most vertical files integrate directly in pressure to the matching column of
   the integrated results file. The legacy ``Ca = -Ca_level`` sign flip
   (``main/05_figure_vertical_levels.py``) compensated a bug that 2.0.0 fixed:
   applying it to corrected data would reintroduce the error with the opposite
   sign. No term needs a sign correction any more.
2. Some files omit their normalising factor and must be divided by
   :data:`VERTICAL_SCALE` to integrate to their integrated counterpart:
   ``Ck`` and its five subterms by ``g = 9.80665``, and ``Kz``/``Ke`` by
   ``2g``. Legacy code used ``9.8`` for Ck, a 0.07 % high bias, and never
   handled the reservoirs at all; this module uses the toolkit's own constant.
3. Only the ``Ck`` decomposition is additive: ``Ck = sum(Ck_1..Ck_5)`` holds to
   round-off. ``Ca = -(Ca_1 + Ca_2)`` also closes, with the global sign flip.
   ``Ce_1/Ce_2`` and ``Cz_1/Cz_2`` are toolkit *intermediates*, not components
   -- ``Ce_1`` is a constant factor -- and must never be plotted as a
   decomposition. See :data:`ADDITIVE_DECOMPOSITIONS`.

All rules are enforced here so no script has to know them.

Layout consumed
---------------
``<run-root>/`` (server-only, produced by the rerun)::

    state.sqlite3                       per-cyclone state machine
    phase_windows/<track_id>.csv        frozen article lifecycle windows
    tracks/track_<track_id>.txt         3-hourly positions fed to the toolkit
    lec_results/<track_id>_ERA5_track/
        <track_id>_ERA5_track_results.csv       integrated terms per timestep
        periods.csv                             windows as used by the toolkit
        results_vertical_levels/<stem>_pressure_level.csv

``data/corrected/`` (repository, built by ``scripts/lec_climatology_rerun``)
holds the derived products that workstation scripts read without the run root.

Environment
-----------
``PAPER_LEC_RUN_ROOT``    override the rerun run root
``PAPER_CORRECTED_DATA``  override the derived-product directory

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── locations ─────────────────────────────────────────────────────────────────

DEFAULT_RUN_ROOT = Path("/p1-swell/danilocs/lec_climatology_corrected_v2")
DEFAULT_CORRECTED_DATA = PROJECT_ROOT / "data" / "corrected"

#: Population targeted by the rerun (see ``<run-root>/provenance.json``).
EXPECTED_POPULATION = 3820

# Derived products written by scripts/lec_climatology_rerun/build_*.py
ENERGY_CACHE = "energy_cache_corrected.parquet"
TRACKS_WITH_ENERGETICS = "tracks_with_energetics_corrected.csv"
VERTICAL_PHASE_MEANS = "vertical_phase_means_corrected.parquet"
PROVENANCE = "provenance_corrected.json"

# ── physical and naming conventions ───────────────────────────────────────────

#: Gravity used by LorenzCycleToolKit for the vertical integrals.
GRAVITY = 9.80665

PHASES = ["incipient", "intensification", "mature", "decay"]

#: Ck decomposition, in the order of the C_K equation of the manuscript.
CK_SUBTERMS = ["Ck_1", "Ck_2", "Ck_3", "Ck_4", "Ck_5"]

#: Divisor each vertical file needs to integrate to its integrated counterpart.
#: Absent stems need no rescaling. Verified by :func:`verify_conventions`.
VERTICAL_SCALE: dict[str, float] = {
    "Kz": 2.0 * GRAVITY,
    "Ke": 2.0 * GRAVITY,
    "Ck": GRAVITY,
    **{stem: GRAVITY for stem in CK_SUBTERMS},
}

CK_SUBTERM_LABELS = {
    "Ck_1": "Ck_A",
    "Ck_2": "Ck_B",
    "Ck_3": "Ck_C",
    "Ck_4": "Ck_D",
    "Ck_5": "Ck_E",
}

CK_SUBTERM_MATH = {
    "Ck_1": r"$C_K^{(A)}$",
    "Ck_2": r"$C_K^{(B)}$",
    "Ck_3": r"$C_K^{(C)}$",
    "Ck_4": r"$C_K^{(D)}$",
    "Ck_5": r"$C_K^{(E)}$",
}

CK_SUBTERM_DESCRIPTIONS = {
    "Ck_1": "Eddy momentum flux against the meridional shear of the zonal wind",
    "Ck_2": "Meridional flux of eddy KE against the meridional gradient of [v]",
    "Ck_3": "Curvature (tan phi) flux of zonal eddy KE",
    "Ck_4": "Vertical flux of zonal eddy momentum against the shear of [u]",
    "Ck_5": "Vertical flux of meridional eddy momentum against the shear of [v]",
}

#: Ca splits additively once the global sign is applied: Ca = -(Ca_1 + Ca_2).
CA_SUBTERMS = ["Ca_1", "Ca_2"]

#: Toolkit intermediates, NOT decompositions: Ce_1 and Cz_1 are constant
#: factors, and the pairs do not sum to their parent term. Never plot these as
#: subterm contributions.
CE_INTERMEDIATES = ["Ce_1", "Ce_2"]
CZ_INTERMEDIATES = ["Cz_1", "Cz_2"]

#: Decompositions verified to close, as ``parent: (sign, components)``.
ADDITIVE_DECOMPOSITIONS: dict[str, tuple[float, list[str]]] = {
    "Ck": (1.0, CK_SUBTERMS),
    "Ca": (-1.0, CA_SUBTERMS),
}

#: Every stem available under results_vertical_levels/.
VERTICAL_TERMS = [
    "Az", "Ae", "Kz", "Ke",
    "Cz", "Ca", "Ck", "Ce", "C_overturning",
    "Gz", "Ge", "M",
    *CZ_INTERMEDIATES, *CA_SUBTERMS, *CE_INTERMEDIATES, *CK_SUBTERMS,
]

#: Terms carried by the integrated results file, grouped as in the manuscript.
INTEGRATED_TERMS = [
    "Az", "Ae", "Kz", "Ke",
    "Cz", "Ca", "Ck", "Ce", "C_overturning",
    "BAz", "BAe", "BKz", "BKe", "BΦZ", "BΦE", "M",
    "Gz", "Ge",
    "∂Az/∂t (finite diff.)", "∂Ae/∂t (finite diff.)",
    "∂Kz/∂t (finite diff.)", "∂Ke/∂t (finite diff.)",
    "RGz", "RKz", "RGe", "RKe",
]

#: The seven terms the article's PCA/k-means classification is built on.
PCA_TERMS = ["Ca", "Ck", "BAe", "BKe", "Ae", "Ke", "Ge"]


class RerunIncomplete(RuntimeError):
    """Raised when a publication product is requested from a partial rerun."""


# ── locations ─────────────────────────────────────────────────────────────────

def run_root() -> Path:
    """Root of the corrected rerun (server-only)."""
    return Path(os.environ.get("PAPER_LEC_RUN_ROOT", DEFAULT_RUN_ROOT))


def corrected_data_dir() -> Path:
    """Directory holding the derived corrected products read by figure scripts."""
    return Path(os.environ.get("PAPER_CORRECTED_DATA", DEFAULT_CORRECTED_DATA))


def corrected_path(name: str) -> Path:
    """Absolute path of a derived corrected product."""
    return corrected_data_dir() / name


def result_dir(track_id: str | int) -> Path:
    """Toolkit output directory of one cyclone."""
    return run_root() / "lec_results" / f"{track_id}_ERA5_track"


def has_run_root() -> bool:
    """True when the rerun state database is reachable from this machine."""
    return (run_root() / "state.sqlite3").is_file()


# ── run state ─────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    database = run_root() / "state.sqlite3"
    if not database.is_file():
        raise FileNotFoundError(
            f"rerun state database not found: {database}. Steps that read the "
            "run root must execute on the server that hosts it."
        )
    return sqlite3.connect(f"file:{database}?mode=ro", uri=True)


def state_counts() -> dict[str, int]:
    """Histogram of the rerun state machine."""
    conn = _connect()
    try:
        return dict(conn.execute("SELECT state, COUNT(*) FROM cyclones GROUP BY state"))
    finally:
        conn.close()


def complete_track_ids() -> list[str]:
    """Track ids whose corrected results passed validation."""
    conn = _connect()
    try:
        return [
            row[0]
            for row in conn.execute(
                "SELECT track_id FROM cyclones WHERE state='COMPLETE' ORDER BY track_id"
            )
        ]
    finally:
        conn.close()


def is_run_complete() -> bool:
    """True when every cyclone of the population is validated COMPLETE."""
    counts = state_counts()
    return counts.get("COMPLETE", 0) == sum(counts.values()) == EXPECTED_POPULATION


def require_complete(context: str) -> list[str]:
    """Return every track id, refusing to proceed while the rerun is partial.

    Publication products must never be built from a growing subset: the
    population would depend on the moment the script ran. Exploratory work can
    call :func:`complete_track_ids` directly and label the output partial.
    """
    counts = state_counts()
    total = sum(counts.values())
    done = counts.get("COMPLETE", 0)
    if done != total or total != EXPECTED_POPULATION:
        raise RerunIncomplete(
            f"{context}: the corrected rerun is not finished "
            f"({done}/{total} COMPLETE, expected {EXPECTED_POPULATION}). "
            f"States: {counts}. Re-run once the climatology completes, or pass "
            "--allow-partial for a clearly labelled exploratory build."
        )
    return complete_track_ids()


# ── readers ───────────────────────────────────────────────────────────────────

def read_integrated(track_id: str | int) -> pd.DataFrame:
    """Vertically integrated LEC terms of one cyclone, indexed by time.

    Values are exactly as written by the pinned toolkit: no sign flip, no
    gravity rescaling, no unit change.
    """
    path = result_dir(track_id) / f"{track_id}_ERA5_track_results.csv"
    frame = pd.read_csv(path, index_col=0)
    frame.index = pd.to_datetime(frame.index, errors="coerce")
    if frame.index.isna().any():
        raise ValueError(f"unparseable timestamps in {path}")
    frame.index.name = "time"
    return frame


def read_phase_windows(track_id: str | int) -> pd.DataFrame:
    """Frozen lifecycle windows of one cyclone.

    Indexed by period name (``intensification``, ``decay 2``, ...) with
    ``start``/``end`` timestamps. The run root's ``phase_windows/`` copy is
    preferred: it is the hashed, provenance-tracked freeze of the article
    windows. The toolkit's own ``periods.csv`` is the fallback.
    """
    frozen = run_root() / "phase_windows" / f"{track_id}.csv"
    path = frozen if frozen.is_file() else result_dir(track_id) / "periods.csv"
    frame = pd.read_csv(path, index_col=0)
    frame.index = frame.index.astype(str).str.strip().str.lower()
    frame.index.name = "period"
    for column in ("start", "end"):
        frame[column] = pd.to_datetime(frame[column])
    return frame[["start", "end"]]


def phase_of(period: str) -> Optional[str]:
    """Main phase of a period name (``decay 2`` -> ``decay``)."""
    raw = str(period).strip().lower()
    return next((phase for phase in PHASES if raw.startswith(phase)), None)


def read_vertical(
    track_id: str | int,
    term: str,
    *,
    in_hpa: bool = False,
    rescale: bool = True,
) -> pd.DataFrame:
    """Pressure-level series of one term: rows are times, columns pressure.

    Parameters
    ----------
    term
        A stem of :data:`VERTICAL_TERMS`, e.g. ``"Ca"`` or ``"Ck_5"``.
    in_hpa
        Return columns in hPa instead of the native Pa. :func:`vertical_integral`
        expects Pa, so keep the default when integrating.
    rescale
        Apply the :data:`VERTICAL_SCALE` divisor the toolkit omits from some
        files (``g`` for the Ck family, ``2g`` for ``Kz``/``Ke``). Disable only
        to inspect the raw toolkit output.

    The returned field integrates in pressure to the matching column of
    :func:`read_integrated`; no sign correction is applied or needed.
    """
    path = result_dir(track_id) / "results_vertical_levels" / f"{term}_pressure_level.csv"
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"missing corrected vertical file: {path}")
    frame = pd.read_csv(path, index_col=0)
    frame.index = pd.to_datetime(frame.index, errors="coerce")
    if frame.index.isna().any():
        raise ValueError(f"unparseable timestamps in {path}")
    frame.index.name = "time"
    frame.columns = frame.columns.astype(float)
    frame = frame.sort_index(axis=1)
    if rescale:
        frame = frame / VERTICAL_SCALE.get(term, 1.0)
    if in_hpa:
        frame.columns = frame.columns / 100.0
    return frame


def vertical_integral(profile: pd.DataFrame) -> pd.Series:
    """Integrate a Pa-indexed pressure-level frame into W m-2 (or J m-2).

    Trapezoidal in pressure, matching the toolkit's own integration. The frame
    must come from :func:`read_vertical` with ``in_hpa=False``.
    """
    levels = profile.columns.to_numpy(dtype=float)
    return pd.Series(
        np.trapezoid(profile.to_numpy(dtype=float), levels, axis=1),
        index=profile.index,
        name=profile.columns.name,
    )


# ── aggregation ───────────────────────────────────────────────────────────────

def window_mean(series: pd.Series, start, end) -> float:
    """Mean of a time series inside a closed lifecycle window."""
    inside = series.loc[(series.index >= start) & (series.index <= end)]
    return float(inside.mean()) if len(inside) else float("nan")


def phase_mean_profiles(
    track_id: str | int,
    terms: Iterable[str],
    *,
    phases: Iterable[str] = PHASES,
    windows: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Phase-mean vertical profiles of one cyclone.

    Returns a long frame with ``track_id, phase, term, level_hpa, value``.
    Secondary periods (``decay 2``) are folded into their main phase by
    averaging the timesteps of every period that maps onto it, so the result
    matches the phase aggregation of the corrected energy cache.
    """
    windows = read_phase_windows(track_id) if windows is None else windows
    wanted = set(phases)
    records: list[dict] = []
    for term in terms:
        profile = read_vertical(track_id, term)
        levels_hpa = profile.columns.to_numpy(dtype=float) / 100.0
        for phase in phases:
            spans = [
                (row["start"], row["end"])
                for period, row in windows.iterrows()
                if phase_of(period) == phase and phase in wanted
            ]
            if not spans:
                continue
            mask = np.zeros(len(profile), dtype=bool)
            for start, end in spans:
                mask |= (profile.index >= start) & (profile.index <= end)
            if not mask.any():
                continue
            means = profile.loc[mask].mean(axis=0).to_numpy(dtype=float)
            records.extend(
                {
                    "track_id": str(track_id),
                    "phase": phase,
                    "term": term,
                    "level_hpa": level,
                    "value": value,
                }
                for level, value in zip(levels_hpa, means)
            )
    return pd.DataFrame.from_records(records)


# ── self-check ────────────────────────────────────────────────────────────────

def verify_conventions(track_id: str | int, tolerance: float = 1e-6) -> dict[str, float]:
    """Check the vertical-file conventions against the integrated results.

    Confirms, for one cyclone, that every vertical field returned by
    :func:`read_vertical` integrates to its integrated counterpart, and that
    each entry of :data:`ADDITIVE_DECOMPOSITIONS` closes. Returns the worst
    relative error per check. Raises ``AssertionError`` when a convention has
    drifted, which would mean the toolkit output changed and this module must
    be revisited before any vertical product is trusted.

    ``M`` is excluded: it is a mass-residual diagnostic whose vertical file has
    no fixed ratio to the integrated column.
    """
    integrated = read_integrated(track_id)
    errors: dict[str, float] = {}
    for term in ("Az", "Ae", "Kz", "Ke", "Cz", "Ca", "Ck", "Ce",
                 "C_overturning", "Gz", "Ge"):
        if term not in integrated.columns:
            continue
        recomputed = vertical_integral(read_vertical(track_id, term))
        reference = integrated[term].reindex(recomputed.index)
        scale = np.nanmax(np.abs(reference.to_numpy())) or 1.0
        errors[term] = float(np.nanmax(np.abs(recomputed - reference)) / scale)

    for parent, (sign, components) in ADDITIVE_DECOMPOSITIONS.items():
        parts = sum(
            vertical_integral(read_vertical(track_id, stem)) for stem in components
        )
        total = vertical_integral(read_vertical(track_id, parent))
        scale = np.nanmax(np.abs(total.to_numpy())) or 1.0
        errors[f"{parent}_closure"] = float(
            np.nanmax(np.abs(sign * parts - total)) / scale
        )

    broken = {term: error for term, error in errors.items() if error > tolerance}
    if broken:
        raise AssertionError(
            f"corrected vertical-level conventions no longer hold for {track_id}: "
            f"{broken}. Re-derive them before trusting any vertical product."
        )
    return errors


if __name__ == "__main__":  # pragma: no cover - manual check
    ids = complete_track_ids()
    print(f"run root          : {run_root()}")
    print(f"corrected data    : {corrected_data_dir()}")
    print(f"state             : {state_counts()}")
    print(f"complete cyclones : {len(ids)} / {EXPECTED_POPULATION}")
    if ids:
        print(f"conventions ({ids[0]}): {verify_conventions(ids[0])}")
