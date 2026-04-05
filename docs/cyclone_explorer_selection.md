# Cyclone Explorer Selection Criteria

## Overview
The Cyclone Explorer displays the **10 most intense cyclones from each energy pattern** (EP1 and EP2), for a total of 20 cyclones.

## Intensity Metric
Intensity is defined by the **maximum relative vorticity at 850 hPa (vor42)** during the cyclone's lifecycle.

-      sUnit: 10
- Higher values indicate stronger cyclones
- This is a standard metric for measuring cyclone intensity in the Southern Hemisphere

## Selection Process
1. For each cyclone in the dataset, extract the time series of relative vorticity at 850 hPa
2. Identify the peak value (maximum vor42) for each cyclone
3. Rank cyclones by this peak intensity value
4. Select the top 10 from EP1 and top 10 from EP2

## EP1 Top 10 Most Intense Cyclones (ranked by max vor42)

| Rank | Track ID | ))))))))) | Intensification Period | Duration | Center Lat/Lon |Max      svor42 (10
|------|----------|----------------------|----------------------|----------|----------------|
| 1 | 19920472 | 15.95 | 1992-06-05 to 1992-06-07 | 33h | -37.-39.|94
| 2 | 19820917 | 15.38 | 1982-10-12 to 1982-10-14 | 48h | -35.-49.|49
| 3 | 19920418 | 14.98 | 1992-05-19 to 1992-05-22 | 69h | -41.18.|97
| 4 | 20020335 | 14.49 | 2002-04-24 to 2002-04-26 | 54h | -40.-27.|88
| 5 | 19800725 | 13.94 | 1980-08-16 to 1980-08-18 | 39h | -34.-42.|33
| 6 | 20140201 | 13.82 | 2014-03-15 to 2014-03-16 | 36h | -42.-44.|00
| 7 | 19790644 | 13.79 | 1979-07-25 to 1979-07-27 | 48h | -37.-31.|35
| 8 | 19790135 | 13.68 | 1979-02-20 to 1979-02-22 | 39h | -41.-36.|53
| 9 | 20121159 | 13.50 | 2012-12-31 to 2013-01-01 | 33h | -43.-50.|91
| 10 | 20010428 | 13.43 | 2001-05-16 to 2001-05-21 | 120h | -29.-41.|02

## EP2 Top 10 Most Intense Cyclones (ranked by max vor42)

| Rank | Track ID | ))))))))) | Intensification Period | Duration | Center Lat/Lon |Max      svor42 (10
|------|----------|----------------------|----------------------|----------|----------------|
| 1 | 19950629 | 15.53 | 1995-07-15 to 1995-07-17 | 42h | -42.-39.|53
| 2 | 20070643 | 15.48 | 2007-07-25 to 2007-07-26 | 36h | -34.-39.|43
| 3 | 19870253 | 15.30 | 1987-04-01 to 1987-04-02 | 27h | -43.-33.|98
| 4 | 20080717 | 15.09 | 2008-08-17 to 2008-08-19 | 45h | -51.-31.|36
| 5 | 19860298 | 15.03 | 1986-04-23 to 1986-04-27 | 111h | -40.-46.|27
| 6 | 20130191 | 14.98 | 2013-03-09 to 2013-03-11 | 36h | -46.-52.|18
| 7 | 20070798 | 14.90 | 2007-09-07 to 2007-09-11 | 105h | -32.-21.|86
| 8 | 20190008 | 14.75 | 2019-01-02 to 2019-01-04 | 30h | -43.-42.|89
| 9 | 20020495 | 14.74 | 2002-06-09 to 2002-06-10 | 27h | -41.-43.|95
| 10 | 20000465 | 14.72 | 2000-05-30 to 2000-06-01 | 48h | -34.-35.|08

## Data Files
- Selection files: `results/ep_structure/ep1_top10_intense_final.csv` and `ep2_top10_intense_final.csv`
- Combined selection: `results/ep_structure/top10_intense_selection.csv`
- Manifest: `web/src/content/cyclone_explorer_manifest.json`
- Figures: `web/public/figures/cyclone_explorer/ep{1,2}/{track_id}/`

## Last Updated
2026-04-05
