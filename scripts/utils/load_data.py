"""
Functions to load data directly from GitHub
"""

import pandas as pd
from typing import Optional

# Data URLs
TRACKS_URL = "https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/refs/heads/master/tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv"
ENERGY_BASE_URL = "https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/master/csv_database_energy_by_periods"


def load_tracks() -> pd.DataFrame:
    """
    Load cyclone tracks CSV directly from GitHub
    
    Returns:
        DataFrame with cyclone tracks
    """
    print("Loading cyclone tracks...")
    df = pd.read_csv(TRACKS_URL)
    print(f"✓ {len(df)} records loaded")
    print(f"✓ {df['track_id'].nunique()} unique cyclones")
    return df


def load_energy_by_cyclone(track_id: str) -> Optional[pd.DataFrame]:
    """
    Load average energy data for a specific cyclone
    
    Args:
        track_id: Cyclone ID (e.g., '19790001')
    
    Returns:
        DataFrame with average energy per period, or None if not found
    """
    url = f"{ENERGY_BASE_URL}/{track_id}_averages.csv"
    try:
        # The first column contains the period names (incipient, intensification, etc.)
        df = pd.read_csv(url, index_col=0)
        # Reset index to make period a regular column
        df = df.reset_index()
        df = df.rename(columns={'index': 'period'})
        return df
    except Exception:
        # Silently return None if file not found
        return None


def load_all_energy_data(track_ids: list) -> dict:
    """
    Load energy data for multiple cyclones
    
    Args:
        track_ids: List of cyclone IDs
    
    Returns:
        Dictionary {track_id: DataFrame} with data for each cyclone
    """
    energy_data = {}
    total = len(track_ids)
    
    for i, track_id in enumerate(track_ids, 1):
        if i % 100 == 0:
            print(f"Loading {i}/{total}...")
        
        df = load_energy_by_cyclone(track_id)
        if df is not None:
            energy_data[track_id] = df
    
    print(f"✓ {len(energy_data)} cyclones loaded successfully")
    return energy_data


if __name__ == "__main__":
    # Basic test
    print("=" * 50)
    print("Data loading test")
    print("=" * 50)
    
    # Test track loading
    tracks = load_tracks()
    print(f"\nAvailable columns: {list(tracks.columns)}")
    print(f"\nFirst rows:\n{tracks.head()}")
    
    # Test loading a specific cyclone
    print("\n" + "=" * 50)
    track_id = tracks['track_id'].iloc[0]
    print(f"Testing energy loading for cyclone {track_id}")
    energy = load_energy_by_cyclone(track_id)
    if energy is not None:
        print(f"✓ Data loaded: {energy.shape}")
        print(f"\nColumns: {list(energy.columns)}")
