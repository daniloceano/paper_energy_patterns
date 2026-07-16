// Utility helpers for formatting and figure URL resolution.
//
// IMPORTANT — bundle size:
//   This file has NO Node.js fs/path imports.
//   Functions that read files (readManifest) live in server-utils.ts.
//   Never add import fs / import path here — it would cause Next.js NFT
//   to trace the entire parent repository into every serverless function.

/** Get the URL for a figure.
 *
 * In production (Vercel), set NEXT_PUBLIC_SUPABASE_FIGURES_URL to point to the
 * Supabase Storage public base URL for the 'figures' bucket, e.g.:
 *   https://<project>.supabase.co/storage/v1/object/public/figures
 *
 * The relativePath argument is always in the form "figures/<subpath>".
 * The function strips the leading "figures/" so the bucket path is just "<subpath>".
 *
 * Figures are committed to web/public/figures/ as static Next.js assets.
 * They are served at /figures/<path> on Vercel without any external service.
 *
 * To override with Supabase Storage (optional), set NEXT_PUBLIC_SUPABASE_FIGURES_URL
 * in the Vercel dashboard. The site works fine without it.
 *
 * Examples:
 *   figureUrl('figures/cluster/pca_variance_wide.png')
 *     → default: /figures/cluster/pca_variance_wide.png  (web/public/figures/...)
 *     → supabase: https://<project>.supabase.co/storage/v1/object/public/figures/cluster/pca_variance_wide.png
 */
export function figureUrl(relativePath: string): string {
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://') || relativePath.startsWith('/')) {
    return relativePath
  }

  const storageBase = process.env.NEXT_PUBLIC_SUPABASE_FIGURES_URL
  if (storageBase) {
    // Strip leading "figures/" — the bucket root already corresponds to figures/
    const bucketPath = relativePath.replace(/^figures\//, '')
    const url = `${storageBase.replace(/\/$/, '')}/${bucketPath}`
    // Guard against a misconfigured env var (e.g. trailing slash baked into
    // NEXT_PUBLIC_SUPABASE_FIGURES_URL) producing "co//storage/..." — collapse
    // any run of slashes that doesn't follow the "https:" scheme separator.
    return url.replace(/([^:])\/{2,}/g, '$1/')
  }
  // Default: serve from web/public/figures/ (committed static assets, no API route needed)
  return `/${relativePath}`
}

/** Format a number for display */
export function formatNumber(n: number, decimals = 2): string {
  return n.toFixed(decimals)
}

/** Format scientific notation */
export function formatScientific(n: number, decimals = 3): string {
  if (Math.abs(n) < 0.001 || Math.abs(n) > 10000) {
    return n.toExponential(decimals)
  }
  return n.toFixed(decimals)
}

/** Capitalize first letter */
export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

/** Slugify a string */
export function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}
