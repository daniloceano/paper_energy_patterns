"""Tests for the physical classification of corrected Ck subterms."""

import pandas as pd
import pytest

from scripts.ck_subterms_analysis.step1_build_subterms_table import (
    add_diagnostics,
    integrate_profiles,
)


def test_all_positive_subterms_are_not_labelled_as_eddy_feeding():
    table = pd.DataFrame(
        {
            "Ck": [15.0, -2.0],
            "Ck_1": [1.0, -3.0],
            "Ck_2": [2.0, 0.2],
            "Ck_3": [3.0, 0.2],
            "Ck_4": [4.0, 0.3],
            "Ck_5": [5.0, 0.3],
        }
    )

    classified = add_diagnostics(table)

    assert classified.loc[0, "dominant_subterm"] == "none"
    assert classified.loc[0, "dominant_label"] == "None (all positive)"
    assert classified.loc[1, "dominant_subterm"] == "Ck_1"


def test_pressure_profiles_use_compatible_trapezoidal_integration():
    profiles = pd.DataFrame(
        {
            "track_id": ["1", "1"],
            "phase": ["intensification", "intensification"],
            "term": ["Ck", "Ck"],
            "level_hpa": [100.0, 200.0],
            "value": [2.0e-4, 2.0e-4],
        }
    )

    integrated = integrate_profiles(profiles)

    assert integrated.loc[0, "Ck"] == pytest.approx(2.0)
