# Data Directory

## Input Data (Accessed from GitHub)

Input data **does not need to be downloaded** - accessed directly via URL:

### 1. Cyclone Tracks
- **URL**: https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/refs/heads/master/tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv
- **Description**: Complete tracks of filtered cyclones with life cycle period information
- **Main columns**:
  - `track_id`: Unique cyclone ID
  - `date`: Observation date/time
  - `lon vor`, `lat vor`: Vortex center coordinates
  - `vor42`: Relative vorticity
  - `region`: Geographic region
  - `period`: Life cycle phase (incipient, intensification, mature, decay, residual)

### 2. Energy by Period
- **Base URL**: https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/master/csv_database_energy_by_periods/
- **Format**: `{track_id}_averages.csv` (e.g., `19790001_averages.csv`)
- **Description**: Averages of energy components for each life cycle phase
- **Coverage**: All ~6,700 cyclones have corresponding energy files (100% coverage)

## Processed Data (This directory)

Use this folder to save:
- Intermediate processed data
- Aggregations and statistics
- Data subsets for specific analyses
- Classification/clustering results

**Note**: Don't version very large files. Use `.gitignore` as needed.
