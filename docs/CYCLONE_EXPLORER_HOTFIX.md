# Cyclone Explorer Hotfix Documentation

## Overview

This document describes the hotfix applied to the Cyclone Explorer feature to enable
deployment while addressing infrastructure and scientific accuracy concerns.

## Problem Summary

### 1. Vercel Function Size Limit (Root Cause)

The `api/figures` serverless function was ~1GB, far exceeding Vercel's 300MB limit.

**Root cause:** The route used `fs.readFileSync` with paths like:
```javascript
const REPO_ROOT = path.resolve(process.cwd(), '..')
const fullPath = path.join(REPO_ROOT, normalised)
```

This caused Vercel's bundler to include the entire parent directory (including ~1GB of figures)
in the serverless function bundle.

**Solution:** Removed the `api/figures` route entirely. Static assets are now served from:
- `web/public/figures/` for committed assets
- Supabase Storage for large assets (preferred production flow)

### 2. Storm-Centering Issue

**Finding:** A scientific audit revealed that only 15% of timesteps were properly storm-centered
(cyclone within 2° of domain center).

**Root cause:** ERA5 data is downloaded with a **fixed 30°×30° domain** centered on the cyclone's 
average position during the intensification phase. When the cyclone moves significantly, it 
approaches or exceeds the domain edges, causing:
- Incomplete data extraction (subdomain truncated at boundaries)
- Visual appearance of cyclone "drifting" off-center in figures

**Design decision:** This is the standard composite approach for synoptic studies. The domain
is intentionally fixed to maintain consistent spatial reference. However, for a temporal 
explorer, this creates UX issues.

**Solution for hotfix:** Selected 20 cyclones (10 EP1 + 10 EP2) with the best storm-centering
quality (lowest mean distance to domain center across all timesteps).

## Hotfix Implementation

### Selected Cyclones

**EP1 (10 cyclones):**
| track_id | Mean dist (km) |
|----------|----------------|
| 20040394 | 30.9 |
| 20030388 | 51.5 |
| 19800580 | 84.6 |
| 19870687 | 88.1 |
| 19800695 | 94.7 |
| 19800296 | 95.1 |
| 20170520 | 98.8 |
| 20100690 | 116.5 |
| 20140006 | 116.7 |
| 19870656 | 117.0 |

**EP2 (10 cyclones):**
| track_id | Mean dist (km) |
|----------|----------------|
| 19920330 | 59.9 |
| 19900437 | 85.3 |
| 20140797 | 85.8 |
| 19800134 | 107.0 |
| 20060280 | 110.5 |
| 19860238 | 114.8 |
| 20120705 | 121.2 |
| 19820891 | 122.8 |
| 19790842 | 128.3 |
| 20140648 | 129.8 |

### Files Modified

1. **Removed:** `web/src/app/api/figures/route.ts`
   - Was serving files from external directories, causing bundle bloat

2. **Modified:** `web/src/components/analysis/ScientificNoteLinkCard.tsx`
   - Changed PDF links from `/api/figures?path=...` to direct `/{path}` URLs

3. **Added:** `web/public/docs/*.pdf`
   - Copied PDFs to public directory for static serving

4. **Modified:** `scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py`
   - Added `--track-ids` and `--selection-file` arguments for selective generation

5. **Added:** `scripts/web/generate_hotfix_manifest.py`
   - Generates lightweight manifest for subset of cyclones

6. **Modified:** `web/src/content/cyclone_explorer_manifest.json`
   - Reduced from 22MB to 138KB (20 cyclones instead of 1400+)

7. **Modified:** `web/src/app/analyses/cyclone-explorer/page.tsx`
   - Added warning banner for limited preview mode

8. **Modified:** `web/src/lib/types.ts`
   - Added `is_hotfix_subset` and `hotfix_note` to manifest metadata type

### Data Files

- `results/ep_structure/hotfix_subset_selection.csv` — List of selected cyclones
- `results/ep_structure/storm_centering_audit.csv` — Full audit results
- `results/ep_structure/storm_centering_audit_report.txt` — Audit summary

## How to Expand to Full Dataset

1. **Regenerate panels for all cyclones:**
   ```bash
   python scripts/ep_structure_analysis/step6_generate_cyclone_explorer_panels.py --jobs 8
   ```

2. **Upload to Supabase Storage:**
   ```bash
   python scripts/web/upload_figures_to_supabase.py --path figures/cyclone_explorer
   ```

3. **Regenerate full manifest:**
   ```bash
   python scripts/web/extract_cyclone_explorer_data.py
   ```

4. **Update environment variable:**
   Set `NEXT_PUBLIC_SUPABASE_FIGURES_URL` to serve assets from Supabase.

## Future Considerations

1. **Storm-centering improvements:** Consider:
   - Downloading larger ERA5 domains (e.g., 50°×50°) with more buffer
   - Implementing per-timestep domain extraction (more storage, better UX)
   - Adding visual indicators when cyclone approaches domain edges

2. **Asset serving:** The preferred production flow is Supabase Storage. The hotfix
   commits a subset to `web/public/` for simplicity, but this should be migrated
   to Supabase for production.

3. **Manifest size:** For full dataset, consider lazy-loading cyclone data via API
   instead of bundling all 1400+ cyclones in the initial page load.

---

*Generated: April 2026*
*Author: Danilo Couto de Souza*
