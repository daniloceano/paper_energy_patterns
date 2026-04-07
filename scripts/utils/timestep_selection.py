"""
Centralized Timestep Selection Utilities for EP Structure Analysis

Provides functions to select central timesteps from intensification phases
according to the canonical methodology: reducing temporal dimension to minimize
ERA5 download volume while maintaining scientific representativeness.

Methodology:
- ODD number of timesteps (N): select central 3 timesteps
- EVEN number of timesteps (N): select central 2 timesteps

This module ensures consistent temporal selection across all pipeline steps.

Author: Danilo Couto de Souza
Date: April 2026
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


def select_central_timesteps(timestamps: List[pd.Timestamp]) -> List[pd.Timestamp]:
    """
    Select central timesteps from a list of timestamps.
    
    Rules:
    - If N is odd: return central 3 timesteps
    - If N is even: return central 2 timesteps
    - If N <= 2: return all timesteps (edge case)
    - If N == 3: return all timesteps
    
    Parameters
    ----------
    timestamps : List[pd.Timestamp]
        Ordered list of timestamps during intensification phase
    
    Returns
    -------
    List[pd.Timestamp]
        Selected central timesteps (2 or 3 elements)
    
    Examples
    --------
    >>> times = pd.date_range('2000-01-01', periods=7, freq='6H')
    >>> select_central_timesteps(times)
    # Returns 3 central times (indices 2, 3, 4)
    
    >>> times = pd.date_range('2000-01-01', periods=6, freq='6H')
    >>> select_central_timesteps(times)
    # Returns 2 central times (indices 2, 3)
    """
    n = len(timestamps)
    
    # Edge cases
    if n <= 2:
        return timestamps
    
    if n == 3:
        return timestamps
    
    # Central selection
    mid_idx = n // 2
    
    if n % 2 == 1:  # ODD: select 3 central
        indices = [mid_idx - 1, mid_idx, mid_idx + 1]
    else:  # EVEN: select 2 central
        indices = [mid_idx - 1, mid_idx]
    
    return [timestamps[i] for i in indices]


def get_selected_timesteps_info(timestamps: List[pd.Timestamp]) -> dict:
    """
    Get information about selected central timesteps.
    
    Parameters
    ----------
    timestamps : List[pd.Timestamp]
        Ordered list of all timestamps during intensification
    
    Returns
    -------
    dict
        Dictionary with:
        - 'n_total': total number of timesteps
        - 'n_selected': number of selected timesteps (2 or 3)
        - 'selected_times': list of selected timestamps
        - 'selected_indices': 0-based indices of selected timesteps
        - 'start_time': first timestamp
        - 'end_time': last timestamp
        - 'duration_hours': total duration in hours
    """
    selected = select_central_timesteps(timestamps)
    
    # Find indices
    indices = [i for i, t in enumerate(timestamps) if t in selected]
    
    # Calculate duration
    if len(timestamps) > 1:
        duration_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
    else:
        duration_hours = 0.0
    
    return {
        'n_total': len(timestamps),
        'n_selected': len(selected),
        'selected_times': selected,
        'selected_indices': indices,
        'start_time': timestamps[0] if timestamps else None,
        'end_time': timestamps[-1] if timestamps else None,
        'duration_hours': duration_hours,
    }


def compute_timestep_count(start_time: pd.Timestamp, end_time: pd.Timestamp, 
                          freq_hours: int = 3) -> int:
    """
    Compute number of timesteps in a time range with given frequency.
    
    Parameters
    ----------
    start_time : pd.Timestamp
        Start of time range
    end_time : pd.Timestamp
        End of time range (inclusive)
    freq_hours : int, default=3
        Temporal frequency in hours (ERA5 native is 3-hourly for SA cyclones)
    
    Returns
    -------
    int
        Number of timesteps
    """
    duration_hours = (end_time - start_time).total_seconds() / 3600
    n_steps = int(duration_hours / freq_hours) + 1
    return n_steps


def validate_duration_filter(duration_hours: float, min_duration_hours: float = 24.0) -> bool:
    """
    Check if a cyclone's intensification duration meets the minimum threshold.
    
    Parameters
    ----------
    duration_hours : float
        Duration of intensification phase in hours
    min_duration_hours : float, default=24.0
        Minimum required duration (canonical threshold: 24h = 1 day)
    
    Returns
    -------
    bool
        True if duration >= min_duration_hours, False otherwise
    """
    return duration_hours >= min_duration_hours
