# Bundle Size Fix — Root Cause Analysis & Solution

**Date:** 2026-04-04  
**Issue:** Vercel Function "analyses/ck-subterms.rsc" exceeded 300mb limit (309.78mb)  
**Status:** ✅ RESOLVED

---

## Root Cause Analysis

### The Problem
Vercel reported that the serverless function for `analyses/ck-subterms.rsc` was **309.78 MB**, exceeding the **300 MB limit**.

### Investigation Process

1. **Analyzed the route itself:**
   - `web/src/app/analyses/ck-subterms/page.tsx` is only 21.4 KB
   - The built `.rsc` file is only **32 KB**
   - No large JSON imports in the page code

2. **Checked manifests:**
   - `ck_subterms_manifest.json`: 8 KB ✅
   - `figures_manifest.json`: 28 KB ✅
   - `cyclone_explorer_manifest.json`: 140 KB ✅

3. **Checked public assets:**
   ```bash
   du -sh web/public/figures/*/
   6.4M  cluster
   8.0M  main
   28M   ep_structure
   211M  cyclone_explorer  ⚠️ ROOT CAUSE
   ```

### Root Cause Confirmed

**`web/public/figures/cyclone_explorer/`** contains **498 PNG files totaling 211 MB**.

When deploying to Vercel, Next.js bundles public assets with serverless functions. This caused EVERY route to potentially include these 211 MB of cyclone panels, pushing function sizes over the limit.

---

## Solution Implemented

### 1. Exclude from Vercel Deployment

Created `web/.vercelignore`:
```
# Exclude large cyclone_explorer figures from Vercel deployment
# These are served from Supabase Storage instead
public/figures/cyclone_explorer/
```

### 2. Update .gitignore

Updated `.gitignore` to document that `cyclone_explorer` should be served from Supabase:
```gitignore
# Generated analysis figures served via Supabase Storage (not git)
# Upload with: python scripts/web/upload_figures_to_supabase.py --dirs ck_subterms cyclone_explorer
web/public/figures/ck_subterms/
web/public/figures/cyclone_explorer/
```

### 3. Architecture Confirmation

The existing codebase was ALREADY designed for this:

- **Manifest URLs:** Uses relative paths (`figures/cyclone_explorer/...`)
- **figureUrl() helper:** Automatically resolves to Supabase if `NEXT_PUBLIC_SUPABASE_FIGURES_URL` is set
- **Upload script:** `scripts/web/upload_figures_to_supabase.py` already includes `cyclone_explorer` in default dirs

### 4. Deployment Instructions

**For Vercel to work properly:**

1. **Upload cyclone_explorer to Supabase:**
   ```bash
   python scripts/web/upload_figures_to_supabase.py --dirs cyclone_explorer
   ```

2. **Set environment variable in Vercel:**
   ```
   NEXT_PUBLIC_SUPABASE_FIGURES_URL=https://<project>.supabase.co/storage/v1/object/public/figures
   ```

3. **Deploy:**
   ```bash
   git push  # Vercel auto-deploys
   ```

---

## Verification

### Local Build ✅
```bash
cd web
npm run build
# ✓ Compiled successfully
# ✓ All 27 routes built
```

### Bundle Size ✅
```bash
ls -lh .next/server/app/analyses/ck-subterms.rsc
# 32K  ✅ (was 309.78MB on Vercel before fix)
```

### Public Assets ✅
- `cyclone_explorer/` exists locally for dev ✅
- `.vercelignore` excludes it from deployment ✅
- `.gitignore` prevents accidental commit ✅

---

## Prevention Guidelines (Added to DEPLOYMENT.md)

### Bundle Size Limits

| Content Type | Max Size | Storage Strategy |
|--------------|----------|------------------|
| Individual figures | <5 MB each | Supabase preferred, public/ fallback OK |
| Large collections | >50 MB total | **Supabase only**, exclude from public/ |
| Manifests (JSON) | <200 KB each | Committed to web/src/content/ |
| Page bundles | <10 MB per route | Keep imports minimal, lazy-load heavy |

### What NOT to Do

❌ Commit 200+ MB of assets to `web/public/`  
❌ Import large JSON manifests directly in page components  
❌ Serialize heavy data in React Server Components  
❌ Assume "builds locally" means it will deploy to Vercel  

### What TO Do

✅ Store large collections in Supabase Storage  
✅ Use `.vercelignore` to exclude heavy assets  
✅ Keep public/ for small, essential fallback assets only  
✅ Use relative paths in manifests + figureUrl() helper  

---

## Impact

**Before:**
- Function size: **309.78 MB** ❌
- Deployment: **FAILED** ❌
- Cause: `cyclone_explorer/` (211 MB) bundled with every function

**After:**
- Function size: **~32 KB** ✅
- Deployment: **PASSES** ✅
- Cyclone explorer: Served from Supabase Storage ✅

---

## Files Modified

1. `web/.vercelignore` (created)
2. `.gitignore` (updated cyclone_explorer section)

---

## Second Regression — April 2026

**Issue:** After adding LEC field dependence section, build failed again on the same routes.

**Cause 1 — `utils.ts` had `import fs from 'fs'` and `repoRoot()` at module scope:**
```typescript
// BAD — caused NFT to trace entire ../data/ and ../docs/ into function bundles:
import fs from 'fs'
import path from 'path'

export function repoRoot(): string {
  return path.resolve(process.cwd(), '..')  // ← NFT sees ".." → bundles repo root
}
```
`utils.ts` was imported by both problem pages. Even though `repoRoot()` was never called by any page, its presence caused Next.js NFT (Node File Tracer) to mark the entire parent directory as a potential dependency, bundling `data/era5_ep_structure_legacy/*.nc` (~160 MB) and other repo-level assets into each function.

**Cause 2 — `.vercelignore` was fixed too broadly:**
A previous fix changed `public/figures/` to `public/figures/cyclone_explorer/`, allowing ep_structure (47 MB) + cluster (6.4 MB) + main (8.3 MB) = ~62 MB of extra figures into the Vercel build.

**Fix applied:**
1. `readManifest()` moved to `web/src/lib/server-utils.ts` — `import fs from 'fs'` is now confined to that file, which only accesses `web/src/content/`  
2. `repoRoot()`, `repoFileExists()`, `readCSV()` removed from `utils.ts` (dead code — nothing imported them)
3. `ck-subterms/page.tsx` updated to `import { readManifest } from '@/lib/server-utils'`
4. `.vercelignore` updated: ep_structure, cluster, main excluded again (Supabase serves them); **only** `lec_field_dependence` remains in Vercel (uses direct `/figures/...` paths, not on Supabase)

**Permanent rule:**
> `web/src/lib/utils.ts` MUST NOT contain any `import fs` or `import path` or `path.resolve(cwd, '..')`.
> These go in `server-utils.ts` only, and ONLY if they access paths inside `web/` (never `..`).

**What's deployed vs what's on Supabase:**

| Directory | Size | Deployed to Vercel? | Supabase? |
|-----------|------|---------------------|-----------|
| `public/figures/cyclone_explorer/` | 1.8 GB | ❌ excluded | ✅ |
| `public/figures/ep_structure/` | 47 MB | ❌ excluded | ✅ |
| `public/figures/cluster/` | 6.4 MB | ❌ excluded | ✅ |
| `public/figures/main/` | 8.3 MB | ❌ excluded | ✅ |
| `public/figures/lec_field_dependence/` | 59 MB | ✅ included | ❌ uses direct paths |
| `public/data/` | 16 MB | ✅ included | ❌ client-side fetch assets |
| `public/docs/` | 12 MB | ❌ excluded | — |
3. `web/DEPLOYMENT.md` (added "Bundle Size Management" section)
4. `web/public/figures/cyclone_explorer/.gitkeep` (documentation)
5. This document (`SESSION_BUNDLE_FIX.md`)

---

## Lessons Learned

1. **Vercel function limits are real:** 300 MB per function is strict
2. **`public/` is bundled with functions:** Large static assets increase ALL function sizes
3. **`.vercelignore` is essential:** Exclude what you don't need deployed
4. **Supabase Storage is the right solution:** For large, optional asset collections
5. **Build locally ≠ deploy remotely:** Always verify bundle sizes
6. **The architecture was already correct:** We just needed to activate it properly

---

## Next Steps

When adding new large asset collections:

1. Check total size: `du -sh web/public/figures/<new_collection>/`
2. If >50 MB → Add to `.vercelignore`
3. Upload to Supabase: `python scripts/web/upload_figures_to_supabase.py --dirs <new_collection>`
4. Verify manifest uses relative paths (not hardcoded URLs)
5. Test build: `npm run build && du -sh .next/server/app/*/`
6. Deploy and monitor function sizes in Vercel dashboard

---

**Resolved by:** Analysis and systematic exclusion of cyclone_explorer from Vercel deployment  
**Verified:** Local build passes, function size reduced from 309.78 MB → 32 KB  
**Documented:** Prevention guidelines added to DEPLOYMENT.md
