# Deployment Guide — Energy Patterns Web Explorer

This guide explains how to publish the web application to [Vercel](https://vercel.com) and how to manage the generated figure assets using Supabase Storage, so that **binary figures never need to be committed to the Git repository**.

---

## Architecture Overview

```
Scientific Pipeline (local)
  ↓ step4_create_figures.py  → figures/cluster/*.png, figures/ep_structure/*.png
  ↓ step5_update_scientific_notes.py → results/ep_structure/composite_stats.json

Upload Script (local, run once after pipeline)
  ↓ scripts/web/upload_figures_to_supabase.py → Supabase Storage bucket "figures"

Web App (Vercel)
  ↓ reads NEXT_PUBLIC_SUPABASE_FIGURES_URL env var
  ↓ renders images as: https://<project>.supabase.co/storage/v1/object/public/figures/<path>
```

**Key principle:** The Git repository contains only code, manifests (small JSON files), and documentation. Generated binary figures live in Supabase Storage and are referenced by public URL.

**Local development:** Figures are served directly from the local filesystem via the `/api/figures` route — no upload needed.

---

## Part 1 — Supabase Storage Setup

Do this once for your Supabase project.

### 1.1 Create the bucket

1. Go to [app.supabase.com](https://app.supabase.com) → your project.
2. Click **Storage** in the left sidebar.
3. Click **New bucket**.
4. Name: `figures`
5. Access: **Public** (uncheck "Private bucket").
6. Click **Save**.

### 1.2 Set bucket policy (public read)

The bucket must allow anonymous reads so the web site can load images without authentication.

If the bucket was created as Public (step above), this is automatic.

To verify or set manually, go to **Storage** → `figures` bucket → **Policies**, and confirm there is a policy like:

```sql
-- Allow public read of all objects in the figures bucket
CREATE POLICY "Public read"
ON storage.objects FOR SELECT
USING (bucket_id = 'figures');
```

### 1.3 Get your Service Role Key

For **uploading** (write access), you need the service role key:

1. Go to your Supabase project → **Settings** → **API**.
2. Copy the **service_role** key (not the anon key).
3. **Never commit this key.** Use it only locally for uploads.

---

## Part 2 — Uploading Figures

Do this after running the scientific pipeline, whenever figures are regenerated.

### 2.1 Prerequisites

```bash
# 1. Run the scientific pipeline to generate figures
python scripts/ep_structure_analysis/step4_create_figures.py
python scripts/cluster_analysis_energy_patterns/run_pipeline.py  # or equivalent

# 2. Install the Supabase Python SDK
pip install supabase
```

### 2.2 Set environment variables

```bash
export SUPABASE_URL=https://<project-ref>.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
```

### 2.3 Dry run (preview)

```bash
python scripts/web/upload_figures_to_supabase.py --dry-run
```

### 2.4 Upload

```bash
# First upload (skip existing files)
python scripts/web/upload_figures_to_supabase.py

# Re-run after figures are regenerated (overwrite)
python scripts/web/upload_figures_to_supabase.py --overwrite

# Upload specific directories only
python scripts/web/upload_figures_to_supabase.py --dirs cluster main ep_structure
```

### 2.5 Bucket structure

The upload script mirrors the `figures/` directory structure into the bucket, stripping the leading `figures/`:

| Local path | Supabase object key | Public URL |
|-----------|--------------------|-|
| `figures/cluster/pca_variance_wide.png` | `cluster/pca_variance_wide.png` | `https://<project>.supabase.co/storage/v1/object/public/figures/cluster/pca_variance_wide.png` |
| `figures/ep_structure/composite_egr.png` | `ep_structure/composite_egr.png` | `https://<project>.supabase.co/storage/v1/object/public/figures/ep_structure/composite_egr.png` |
| `figures/main/4_lps_combined.png` | `main/4_lps_combined.png` | `https://<project>.supabase.co/storage/v1/object/public/figures/main/4_lps_combined.png` |

---

## Part 3 — Deploying to Vercel

### 3.1 Push the repository to GitHub

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

### 3.2 Import project in Vercel

1. Go to [vercel.com/new](https://vercel.com/new).
2. Click **Import Git Repository** and select this repo.

### 3.3 Configure Root Directory

> **Critical.** The Next.js app is in `web/`, not the repo root.

In the **Configure Project** screen, click the pencil icon next to **Root Directory** and type `web`.

| Setting | Value |
|---------|-------|
| Root Directory | `web` |
| Framework Preset | Next.js (auto-detected) |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Install Command | `npm install` |

### 3.4 Configure Environment Variables

In the Vercel project → **Settings** → **Environment Variables**, add:

| Variable | Value | Required |
|----------|-------|---------|
| `NEXT_PUBLIC_SUPABASE_FIGURES_URL` | `https://<project-ref>.supabase.co/storage/v1/object/public/figures` | **Yes — for figures to appear** |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<project-ref>.supabase.co` | Only if using Supabase DB |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Only if using Supabase DB |
| `NEXT_PUBLIC_SITE_URL` | `https://your-site.vercel.app` | Optional |

The `NEXT_PUBLIC_SUPABASE_FIGURES_URL` is the most important variable — without it, figures will not load on Vercel.

### 3.5 Deploy

Click **Deploy**. Vercel will install dependencies and run `next build`. The build itself does NOT require figures — they are referenced by URL at runtime.

---

## Part 4 — How It Works End to End

### In production (Vercel)

The `figureUrl()` utility in `web/src/lib/utils.ts` detects the `NEXT_PUBLIC_SUPABASE_FIGURES_URL` env var:

```
figureUrl('figures/cluster/pca_variance_wide.png')
  → https://<project>.supabase.co/storage/v1/object/public/figures/cluster/pca_variance_wide.png
```

The browser fetches the image directly from Supabase CDN. No server-side filesystem access. No large files in git.

### In local development

Without `NEXT_PUBLIC_SUPABASE_FIGURES_URL` set in `.env.local`, the fallback is:

```
figureUrl('figures/cluster/pca_variance_wide.png')
  → /api/figures?path=figures%2Fcluster%2Fpca_variance_wide.png
```

The `/api/figures` route (in `web/src/app/api/figures/route.ts`) reads the file from the local filesystem at `<repo-root>/figures/cluster/pca_variance_wide.png`. The figures must exist on disk but do NOT need to be committed to git.

---

## Part 5 — Automatic Deploys and Update Flow

After the first setup, pushing to `main` auto-deploys:

```bash
git add .
git commit -m "Update analysis pages"
git push
# → Vercel automatically rebuilds and deploys
```

**When to re-upload figures:**
Figures only need to be re-uploaded when the scientific pipeline generates new or changed figures:

```bash
# After re-running step4 or cluster pipeline:
python scripts/web/upload_figures_to_supabase.py --overwrite
# No git commit or Vercel redeploy needed for figure changes — Supabase Storage serves them live.
```

---

## Part 6 — What Must Be Committed to Git

| Path | Must commit? | Why |
|------|-------------|-----|
| `web/src/content/*.json` | ✅ Yes | Manifest files read at build time |
| `results/ep_structure/composite_stats.json` | ✅ Yes | Stats from step5, read at build time |
| `web/.env.example` | ✅ Yes | Documents required env vars |
| `figures/**/*.png` | ❌ No | Uploaded to Supabase Storage instead |
| `data/**/*.nc` | ❌ No | Large ERA5 files — not needed by web |
| `web/.env.local` | ❌ No | Contains secrets — use Vercel env vars |
| `web/node_modules/` | ❌ No | Installed by Vercel |
| `web/.next/` | ❌ No | Built by Vercel |

---

## Part 7 — Preparing a Full Deploy (Step by Step)

```bash
# 1. Run scientific pipeline to generate figures
python scripts/ep_structure_analysis/step4_create_figures.py
python scripts/ep_structure_analysis/step5_update_scientific_notes.py --no-pdf

# 2. Update web manifests
python scripts/web/build_site_manifest.py
python scripts/web/extract_cluster_site_data.py
python scripts/web/extract_composite_site_data.py

# 3. Upload figures to Supabase Storage
export SUPABASE_URL=https://<project-ref>.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
python scripts/web/upload_figures_to_supabase.py --overwrite

# 4. Commit manifests (JSON files) — NOT figures
git add web/src/content/ results/ep_structure/composite_stats.json
git commit -m "Update web manifests"
git push
# → Vercel auto-deploys
```

---

## Part 8 — Verifying a Deploy

1. Go to Vercel → Deployments → click latest → **Build Logs**.
2. Visit the deployed site.
3. Navigate to `/analyses/cluster/step-2-pca`:
   - If figures appear: ✅ Supabase Storage is configured correctly.
   - If broken icons: Check that `NEXT_PUBLIC_SUPABASE_FIGURES_URL` is set in Vercel env vars AND figures were uploaded.
4. Navigate to `/analyses/composites/egr`:
   - If domain stats table shows values: ✅ `composite_stats.json` is committed and step5 has been run.
   - If table shows `—`: Run `step5_update_scientific_notes.py`, then `extract_composite_site_data.py`, then commit and push.

### Debug: Check Supabase URL manually

Open this URL in your browser (replace with your values):
```
https://<project-ref>.supabase.co/storage/v1/object/public/figures/cluster/pca_variance_wide.png
```
If it loads an image: the bucket is public and the file was uploaded correctly.
If 404: the file was not uploaded. Run the upload script.
If 400/401: the bucket is private. Make it public in Supabase Storage settings.

---

## Part 9 — Redeploy

To trigger a redeploy without code changes:

```bash
git commit --allow-empty -m "trigger redeploy"
git push
```

Or in Vercel dashboard → Deployments → ⋯ → **Redeploy**.

---

## Part 10 — Source of Truth Reference

| What | Source | Who generates it |
|------|--------|-----------------|
| Composite figures (EP1 vs EP2) | `figures/ep_structure/composite_*.png` | `step4_create_figures.py` |
| Domain statistics (inside/outside 15×15) | `results/ep_structure/composite_stats.json` | `step5_update_scientific_notes.py` |
| Boundary flux tables (N/S/E/W) | `results/ep_structure/composite_stats.json` | `step5_update_scientific_notes.py` |
| Scientific Notes text | `scripts/ep_structure_analysis/SCIENTIFIC_NOTES.md` | `step5_update_scientific_notes.py` |
| Cluster figures | `figures/cluster/*.png` | cluster analysis pipeline |
| Web manifests (domain stats, figures catalog) | `web/src/content/*.json` | `scripts/web/extract_composite_site_data.py` |
| Supabase Storage (figures CDN) | Supabase bucket `figures` | `scripts/web/upload_figures_to_supabase.py` |

**Domain definitions** (used in step5 and displayed in the web):
- **inside 15×15**: mean within the central ±7.5° LEC subdomain (cyclone-centred)
- **outside 15×15**: mean over the full 30×30° domain (full composite domain)
- **Boundary fluxes** (North/South/East/West): mean of the field along each edge of the ±7.5° inner box, at ERA5 0.25° resolution (tolerance ±0.25°)
- Applicable to: Temperature Advection 850, Moisture Flux Divergence 975, KE Advection 250, AFC 250
- Not applicable to: EGR (no flux direction), PV 200/850 (scalar PV, not flux), SLP (pressure, not flux), RK criterion (vorticity gradient)

---

## Quick Reference

```bash
# Setup (once)
# 1. Create bucket 'figures' (public) in Supabase Storage
# 2. In Vercel: set NEXT_PUBLIC_SUPABASE_FIGURES_URL

# After each pipeline run
python scripts/web/upload_figures_to_supabase.py --overwrite
python scripts/web/extract_composite_site_data.py
git add web/src/content/ results/ep_structure/composite_stats.json && git push

# Local dev
cd web && npm run dev   # figures served from local disk via /api/figures
```
