# Energy Pattern Definitions

This document defines the three Energy Patterns (EPs) identified through K-Means clustering analysis.

## Overview

Energy Patterns are defined based on the mean conversion from potential to kinetic energy (Ck) across all lifecycle phases. Since Ck represents the Barotropic conversion (typically negative values indicating conversion from zonal kinetic to eddy kinetic energy), the patterns reflect different intensities of barotropic processes.

## Pattern Definitions

### EP1: Strong Barotropic Conversion
### EP1: Strong Barotropic Conversion
- **Mean Ck**: -16.48 W/m² (lowest/most negative)
- **Cluster ID**: 0
- **Frequency**: 444 cyclones (11.6%)
- **Characteristics**: 
  - Dominated by strong barotropic conversions
  - Pronounced conversion from available potential energy to kinetic energy
  - Represents cyclones with strong barotropic energetics and typically higher barotropic forcing

### EP2: Mixed Barotropic and Baroclinic Conversions
- **Mean Ck**: -3.49 W/m² (middle)
- **Cluster ID**: 2
- **Frequency**: 979 cyclones (25.6%)
- **Characteristics**:
  - Exhibits a mixture of barotropic and baroclinic energy conversions
  - Intermediate conversion magnitudes from potential to kinetic energy
  - Represents cyclones where both barotropic and baroclinic processes contribute meaningfully to development and intensity
  - Represents moderately barotropic cyclones
### EP3: Weak Energetics and Lower Intensity (on average)
- **Mean Ck**: -1.71 W/m² (highest/least negative)
- **Cluster ID**: 1
- **Frequency**: 2397 cyclones (62.7%)
- **Characteristics**:
  - Overall weak energetic conversions (small mean Ck)
  - Lower average intensity compared with EP1/EP2
  - Represents the most frequent pattern with relatively weak barotropic and baroclinic activity on average
  - Minimal conversion from available potential energy to kinetic energy
  - Represents weakly barotropic or more barotropic cyclones

## Cluster to Energy Pattern Mapping

```
Cluster 0  →  EP1 (Strong Barotropic)
Cluster 2  →  EP2 (Moderate Barotropic)
Cluster 1  →  EP3 (Weak Barotropic)
```

## Visualization

For each Energy Pattern, Lorenz Phase Space (LPS) diagrams show all cyclones belonging to that pattern:

### Mixed LPS (Ck vs Ca)
- Shows the relationship between conversion and generation of available potential energy
- Default view: Fixed limits for cross-EP comparison
- Zoom view: Custom limits for detailed EP-specific analysis

### Imports LPS (BAe vs BKe)
- Shows the relationship between boundary fluxes of available potential and kinetic energy
- Default view: Fixed limits for cross-EP comparison
- Zoom view: Custom limits for detailed EP-specific analysis

## Files

### Scripts
- `scripts/exploratory/plot_ep_lps_diagrams.py`: Generate LPS diagrams for each EP

### Figures (12 total)
Each EP has 4 figures:
- `figures/exploratory/ep{1,2,3}_lps_mixed_default.png`
- `figures/exploratory/ep{1,2,3}_lps_mixed_zoom.png`
- `figures/exploratory/ep{1,2,3}_lps_imports_default.png`
- `figures/exploratory/ep{1,2,3}_lps_imports_zoom.png`

### Data
- `results/cluster/kmeans_clustered_data.csv`: Cluster assignments for all cyclones
- `results/cluster/kmeans_centroids_energy.csv`: Centroid characteristics for each cluster

## Methodology

1. **Clustering**: K-Means clustering (k=3) applied to PCA-reduced wide matrix (28 energy features = 7 terms × 4 phases)
2. **EP Assignment**: Based on mean Ck values across all phases, sorted from lowest to highest
3. **Visualization**: Sequential phase trajectories (Incipient → Intensification → Mature → Decay) plotted in Lorenz Phase Space using lorenz-phase-space v1.3.0

## References

For the clustering methodology and energy term definitions, see:
- `scripts/cluster/README.md`: Clustering pipeline documentation
- `data/DATA_STRUCTURE.md`: Energy term definitions and data structure
