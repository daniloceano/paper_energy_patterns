# HOTFIX: Restore Figure Loading (Composites & Cyclone Explorer)

**Date:** 2026-04-04  
**Issue:** Composites and Cyclone Explorer figures not displaying on production  
**Status:** ✅ RESOLVED

---

## Problem Report

After fixing the Vercel bundle size issue, **all composite and cyclone explorer figures disappeared** from the production site.

### Symptoms
- ❌ Composite maps pages show no images
- ❌ Cyclone Explorer shows no panels
- ✅ Site builds successfully
- ✅ Bundle size within limits

---

## Root Cause Analysis

### Investigation Process

1. **Checked local assets:** ✅ All figures exist
   ```bash
   # Composites: 36 PNG files in web/public/figures/ep_structure/
   # Cyclone Explorer: 498 PNG files in web/public/figures/cyclone_explorer/
   ```

2. **Checked manifests:** ✅ Manifests correct
   ```json
   // composite_figures_manifest_central_time.json
   {
     "egr": {
       "real": {
         "exists": true,
         "api_path": "figures/ep_structure/composite_egr_central_time.png"
       }
     }
   }
   ```

3. **Checked frontend code:** ✅ Logic correct
   - Uses `figureUrl()` helper
   - Proper manifest reading
   - Correct component structure

4. **Checked environment:** ⚠️ **ROOT CAUSE FOUND**
   - Vercel has `NEXT_PUBLIC_SUPABASE_FIGURES_URL` configured
   - Figures **NOT** uploaded to Supabase
   - `figureUrl()` tries to load from Supabase → **404**
   - No fallback mechanism

### Root Cause Confirmed

**The issue occurs when:**
1. `NEXT_PUBLIC_SUPABASE_FIGURES_URL` is set in Vercel
2. Figures have NOT been uploaded to Supabase yet
3. Frontend tries to load: `https://xxx.supabase.co/storage/.../composite_egr.png`
4. Supabase returns 404 (file not found)
5. Next.js Image component fails silently
6. No automatic fallback to `/figures/` (local public assets)

**Why cyclone_explorer is worse:**
- Cyclone explorer is excluded from git/Vercel (via `.vercelignore`)
- So there's NO local fallback available
- Result: 100% of cyclone panels fail

**Why composites also fail:**
- Even though composites ARE in `web/public/figures/ep_structure/`
- The Supabase URL takes precedence
- 404 on Supabase → no fallback → blank images

---

## Solution Implemented

### 1. Automatic Fallback Mechanism

Created `FallbackImage.tsx` component that:
- ✅ Tries to load from Supabase first (if URL configured)
- ✅ On 404/error, automatically falls back to `/figures/` (local)
- ✅ Shows clear error state if both fail
- ✅ Logs warnings to console for debugging

**Code:** `web/src/components/analysis/FallbackImage.tsx`

```typescript
// Automatic fallback logic
const handleError = () => {
  if (currentSrc.includes('supabase.co') && !hasError) {
    // Extract path and build local fallback
    const pathMatch = currentSrc.match(/\/storage\/v1\/object\/public\/figures\/(.+)$/)
    const relativePath = pathMatch ? pathMatch[1] : null
    const localPath = relativePath ? `/figures/${relativePath}` : fallbackSrc || src
    
    console.warn(`Failed to load from Supabase: ${currentSrc}. Falling back to: ${localPath}`)
    setCurrentSrc(localPath)
  } else {
    setHasError(true)
  }
}
```

### 2. Updated Components

**DiagnosticCompositesClient.tsx:**
```diff
- import Image from 'next/image'
+ import FallbackImage from '@/components/analysis/FallbackImage'

- <Image src={figureUrl(realFig.api_path)} ... />
+ <FallbackImage src={figureUrl(realFig.api_path)} ... />
```

**CycloneExplorerClient.tsx:**
```diff
- import Image from 'next/image'
+ import FallbackImage from '@/components/analysis/FallbackImage'

- <Image src={panelPath} fill ... />
+ <FallbackImage src={panelPath} fill ... />
```

### 3. Updated Documentation

**DEPLOYMENT.md:**
- Added critical warning about upload order
- Emphasized: Upload figures BEFORE setting env var
- Clarified fallback behavior

---

## Behavior After Fix

### Scenario 1: Supabase Configured + Figures Uploaded ✅
- Loads from Supabase (CDN)
- Fast, optimal

### Scenario 2: Supabase Configured + Figures NOT Uploaded ✅
- Tries Supabase → 404
- **Automatically falls back to `/figures/`**
- Composites: ✅ Load from local public/
- Cyclone Explorer: ⚠️ Still fails (not in public/)
- Console warning logged

### Scenario 3: Supabase NOT Configured ✅
- Loads from `/figures/` directly
- Composites: ✅ Work
- Cyclone Explorer: ⚠️ Fails (not in public/)

### Scenario 4: Both Fail ✅
- Shows clear error UI
- Error logged to console
- User sees "Failed to load image"

---

## Proper Deployment Flow

### ✅ CORRECT ORDER

```bash
# 1. Upload figures to Supabase
python scripts/web/upload_figures_to_supabase.py

# 2. Set env var in Vercel
# NEXT_PUBLIC_SUPABASE_FIGURES_URL = https://xxx.supabase.co/storage/v1/object/public/figures

# 3. Deploy
git push
```

### ❌ WRONG ORDER (causes regression)

```bash
# 1. Set env var in Vercel FIRST ❌
# NEXT_PUBLIC_SUPABASE_FIGURES_URL = https://xxx.supabase.co/...

# 2. Deploy (figures fail because not in Supabase yet) ❌
git push

# 3. Upload later ❌
python scripts/web/upload_figures_to_supabase.py
```

---

## Files Modified

1. **`web/src/components/analysis/FallbackImage.tsx`** (created)
   - New component with automatic fallback logic

2. **`web/src/components/analysis/DiagnosticCompositesClient.tsx`** (modified)
   - Replaced `Image` with `FallbackImage`

3. **`web/src/app/analyses/cyclone-explorer/CycloneExplorerClient.tsx`** (modified)
   - Replaced `Image` with `FallbackImage`

4. **`web/DEPLOYMENT.md`** (updated)
   - Added critical warning about upload order
   - Clarified fallback behavior
   - Emphasized Supabase upload requirement

5. **`web/HOTFIX_FIGURES.md`** (this document)
   - Root cause analysis
   - Solution documentation

---

## Impact

### Before Hotfix ❌
- Composites: BLANK (Supabase 404, no fallback)
- Cyclone Explorer: BLANK (Supabase 404, no fallback)
- User experience: BROKEN
- Console: Silent failures

### After Hotfix ✅
- Composites: WORKING (falls back to `/figures/ep_structure/`)
- Cyclone Explorer: **Needs Supabase upload** (not in public/)
- User experience: RESTORED (composites) / IMPROVED (error messages)
- Console: Helpful warnings

---

## Next Steps for Full Resolution

### For Composites: ✅ RESOLVED
- Fallback to local `/figures/ep_structure/` works
- No action needed (unless you want Supabase CDN benefits)

### For Cyclone Explorer: 🔄 ACTION REQUIRED
- **Must upload to Supabase** (not in public/ by design)
- Run: `python scripts/web/upload_figures_to_supabase.py --dirs cyclone_explorer`
- Then panels will load from Supabase

---

## Prevention

### Developer Checklist

When deploying a new instance:

- [ ] Create Supabase project
- [ ] Create `figures` bucket (public)
- [ ] Upload ALL figures: `python scripts/web/upload_figures_to_supabase.py`
- [ ] Verify uploads: `--dry-run` first
- [ ] **ONLY THEN** set `NEXT_PUBLIC_SUPABASE_FIGURES_URL` in Vercel
- [ ] Deploy
- [ ] Verify images load in production

### Monitoring

Check browser console for warnings:
```
Failed to load from Supabase: https://xxx.supabase.co/storage/.../composite_egr.png
Falling back to: /figures/ep_structure/composite_egr.png
```

If you see these, it means:
- Supabase is configured
- But files are missing
- Fallback is working (for files in public/)

---

## Lessons Learned

1. **Env vars must match reality:** Don't set `SUPABASE_FIGURES_URL` before uploading
2. **Silent failures are bad:** Image components should log/show errors
3. **Fallback is essential:** Never rely on single source without backup
4. **Documentation must be clear:** Emphasize order of operations
5. **Test production scenario:** Local dev may work even when production fails

---

**Resolved by:** Automatic fallback mechanism + documentation  
**Tested:** Build passes, composites load with fallback  
**Status:** Composites ✅ | Cyclone Explorer 🔄 (needs Supabase upload)
