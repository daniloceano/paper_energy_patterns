"""
Analysis Template
Copy this template to create new analysis scripts
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scripts.utils.load_data import load_tracks, load_energy_by_cyclone

# Setup directories relative to project root
FIGURES_DIR = project_root / "figures"
RESULTS_DIR = project_root / "results"
FIGURES_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Plot style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')


def main():
    """Main analysis function"""
    
    print("=" * 60)
    print("Analysis: [YOUR ANALYSIS NAME]")
    print("=" * 60)
    print()
    
    # Load data
    print("Loading data...")
    tracks = load_tracks()
    print(f"✓ Loaded {len(tracks):,} track records")
    print()
    
    # Your analysis here
    # ...
    
    # Example: Load energy data for specific cyclones
    # track_ids = tracks['track_id'].unique()[:10]
    # for track_id in track_ids:
    #     energy = load_energy_by_cyclone(track_id)
    #     if energy is not None:
    #         # Process energy data
    #         pass
    
    # Save results
    # results_df.to_csv(RESULTS_DIR / "your_results.csv", index=False)
    # print(f"✓ Results saved to {RESULTS_DIR / 'your_results.csv'}")
    
    # Create visualization
    # fig, ax = plt.subplots(figsize=(10, 6))
    # ... your plot code ...
    # plt.savefig(FIGURES_DIR / "your_figure.png", dpi=300, bbox_inches='tight')
    # print(f"✓ Figure saved to {FIGURES_DIR / 'your_figure.png'}")
    
    print()
    print("=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
