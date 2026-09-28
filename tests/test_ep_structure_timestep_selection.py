"""Tests for the canonical central-time selection used by ERA5 composites."""

import pandas as pd
import pytest

from scripts.ep_structure_analysis.timestep_selection import (
    selected_timestep_indices,
)


def test_selection_ignores_extra_legacy_hours():
    available = pd.to_datetime(
        ["2001-01-01 00:00", "2001-01-01 03:00", "2001-01-01 06:00"]
    )

    assert selected_timestep_indices(
        available,
        ["2001-01-01 03:00", "2001-01-01 06:00"],
    ) == [1, 2]


def test_selection_rejects_missing_time():
    available = pd.to_datetime(["2001-01-01 00:00", "2001-01-01 03:00"])

    with pytest.raises(ValueError, match="0 matching NetCDF timesteps"):
        selected_timestep_indices(available, ["2001-01-01 06:00"])


def test_selection_rejects_duplicate_time_coordinate():
    available = pd.to_datetime(["2001-01-01 03:00", "2001-01-01 03:00"])

    with pytest.raises(ValueError, match="2 matching NetCDF timesteps"):
        selected_timestep_indices(available, ["2001-01-01 03:00"])
