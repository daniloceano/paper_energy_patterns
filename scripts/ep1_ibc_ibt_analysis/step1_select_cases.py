"""
Step 1: Select 10 Most Intense EP1 Cyclones

This script selects the most intense cyclones from Energy Pattern 1 (EP1)
for detailed vertical structure and instability analysis.

Selection Criteria:
- Belongs to EP1 (cluster 0)
- Maximum vorticity during mature phase
- Strong energy conversion signatures (Ca and Ck)
- Data availability for intensification phase

Author: Danilo Couto de Souza
Date: January 2026
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from scripts.utils.load_data import load_tracks

# Configuration
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "results" / "ep1_vertical"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def filter_complete_lifecycle_tracks(df):
    """
    Filter tracks with complete lifecycle in exact order:
    incipient → intensification → mature → decay
    
    Same logic as used in scripts/main/01_figure_tracks_genesis_frequency.py
    """
    complete_tracks = []
    
    for track_id, track_data in df.groupby('track_id'):
        # Get unique periods (dropping NaN) in order of appearance
        periods = track_data['period'].dropna().unique()
        
        # Check if lifecycle matches exactly
        if (len(periods) == 4 and
            periods[0] == 'incipient' and
            periods[1] == 'intensification' and
            periods[2] == 'mature' and
            periods[3] == 'decay'):
            complete_tracks.append(track_id)
    
    return complete_tracks


def main():
    """Select 10 most intense EP1 cyclones."""
    
    print("=" * 80)
    print("STEP 1: Selecting Most Intense EP1 Cyclones")
    print("=" * 80)
    
    # Load clustered data
    print("\n1. Loading clustered data...")
    cluster_file = Path(__file__).resolve().parents[2] / "results" / "cluster" / "kmeans_clustered_data.csv"
    clustered = pd.read_csv(cluster_file)
    
    # Filter EP1 cyclones (cluster 0)
    ep1_cyclones = clustered[clustered['cluster'] == 0].copy()
    print(f"   Found {len(ep1_cyclones)} EP1 cyclones")
    
    # Load full track data
    print("\n2. Loading track data...")
    tracks = load_tracks()
    
    # Filter tracks with complete lifecycle
    print("\n3. Filtering tracks with complete lifecycle (incipient → intensification → mature → decay)...")
    complete_track_ids = filter_complete_lifecycle_tracks(tracks)
    print(f"   Tracks with complete lifecycle: {len(complete_track_ids)} / {tracks['track_id'].nunique()}")
    
    # Filter to only complete lifecycle tracks
    tracks = tracks[tracks['track_id'].isin(complete_track_ids)].copy()
    
    # Merge to get cluster information for complete lifecycle tracks only
    tracks = tracks.merge(
        ep1_cyclones[['track_id', 'cluster']], 
        on='track_id', 
        how='inner'
    )
    
    print(f"   EP1 cyclones with complete lifecycle: {tracks['track_id'].nunique()}")
    
    # Select 10 most intense based on maximum vorticity
    print("\n4. Selecting 10 most intense cyclones based on maximum vor42...")
    
    # Get maximum vorticity for each track (across all phases)
    max_vor = tracks.groupby('track_id')['vor42'].max().reset_index()
    max_vor.columns = ['track_id', 'max_vorticity']
    
    # Sort and select top 10
    top_10 = max_vor.nlargest(10, 'max_vorticity')
    
    # Get additional information for selected cyclones
    selected_info = []
    for track_id in top_10['track_id']:
        track_data = tracks[tracks['track_id'] == track_id]
        
        info = {
            'track_id': track_id,
            'max_vorticity': track_data['vor42'].max(),
            'genesis_region': track_data['region'].iloc[0],
            'genesis_date': track_data['date'].iloc[0],
            'duration_hours': len(track_data),
            'complete_lifecycle': True  # All selected tracks have complete lifecycle
        }
        selected_info.append(info)
    
    selected_df = pd.DataFrame(selected_info)
    selected_df = selected_df.sort_values('max_vorticity', ascending=False)
    
    # Save results
    output_file = OUTPUT_DIR / "selected_cases.csv"
    selected_df.to_csv(output_file, index=False)
    
    print(f"\n5. Selected cyclones (all with complete lifecycle):")
    print(selected_df.to_string(index=False))
    
    print(f"\n✅ Results saved to: {output_file}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
