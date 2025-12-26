"""
Example analysis script
Demonstrates basic data loading and analysis workflow
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scripts.utils.load_data import load_tracks, load_energy_by_cyclone

# Setup directories relative to project root
FIGURES_DIR = project_root / "figures" / "example"
RESULTS_DIR = project_root / "results" / "example"
FIGURES_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("Example Analysis: Cyclone Track Statistics")
print("=" * 60)
print()

# Load data
print("Loading cyclone tracks...")
tracks = load_tracks()
print(f"✓ Loaded {len(tracks):,} records from {tracks['track_id'].nunique():,} cyclones")
print()

# Basic statistics
print("Computing statistics by life cycle phase...")
stats = tracks.groupby('period').agg({
    'track_id': 'count',
    'vor42': ['mean', 'std', 'min', 'max']
}).round(2)

print("\nStatistics by period:")
print(stats)
print()

# Save results
output_file = RESULTS_DIR / "statistics_by_period.csv"
stats.to_csv(output_file)
print(f"✓ Statistics saved to {output_file}")
print()

# Create visualization
print("Creating visualization...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Count by period
period_counts = tracks['period'].value_counts()
period_counts.plot(kind='bar', ax=axes[0], color='steelblue')
axes[0].set_title('Number of Observations by Life Cycle Phase')
axes[0].set_xlabel('Phase')
axes[0].set_ylabel('Count')
axes[0].tick_params(axis='x', rotation=45)

# Plot 2: Vorticity distribution by period
tracks.boxplot(column='vor42', by='period', ax=axes[1])
axes[1].set_title('Vorticity Distribution by Phase')
axes[1].set_xlabel('Phase')
axes[1].set_ylabel('Relative Vorticity')
axes[1].tick_params(axis='x', rotation=45)
plt.suptitle('')  # Remove default title

plt.tight_layout()
fig_file = FIGURES_DIR / "example_analysis.png"
plt.savefig(fig_file, dpi=300, bbox_inches='tight')
print(f"✓ Figure saved to {fig_file}")
print()

# Example: Load energy data for one cyclone
print("Loading energy data for one cyclone...")
track_id = tracks['track_id'].iloc[0]
energy = load_energy_by_cyclone(track_id)

if energy is not None:
    print(f"✓ Successfully loaded energy data for {track_id}")
    print(f"  Shape: {energy.shape}")
    print(f"  Columns: {list(energy.columns)}")
else:
    print(f"⚠️  Could not load energy data for {track_id}")

print()
print("=" * 60)
print("✅ Example analysis complete!")
print("=" * 60)
