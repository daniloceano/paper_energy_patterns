"""Canonical time matching for the ERA5 composite pipeline.

This small module exists because reusable legacy NetCDF files can contain
hours beyond the 2--3 central times selected by step 1.  Keeping the matching
rule independent from the MetPy-heavy composite implementation makes that
scientifically important boundary directly testable in lightweight local and
continuous-integration environments.
"""

import numpy as np
import pandas as pd


def selected_timestep_indices(available_times, selected_times):
    """Map canonical central times to unique NetCDF indices.

    Every requested time must have exactly one match within the pipeline's
    one-minute timestamp tolerance.  Extra legacy hours are intentionally
    ignored.
    """
    available = pd.DatetimeIndex(pd.to_datetime(available_times))
    requested = [pd.Timestamp(value) for value in selected_times]
    if not requested:
        raise ValueError("selected_times is empty")

    indices = []
    for requested_time in requested:
        offsets = np.abs(available - requested_time)
        matches = np.flatnonzero(offsets <= pd.Timedelta(minutes=1))
        if len(matches) != 1:
            raise ValueError(
                f"selected time {requested_time.isoformat()} has "
                f"{len(matches)} matching NetCDF timesteps; expected exactly one"
            )
        indices.append(int(matches[0]))

    if len(set(indices)) != len(indices):
        raise ValueError("selected_times map to duplicate NetCDF timesteps")
    return indices
