/**
 * Client-safe utility functions.
 * These functions do NOT use Node.js modules (fs, path) and can be safely
 * imported in client components.
 */

/**
 * Build URL for a figure asset.
 * Checks for NEXT_PUBLIC_SUPABASE_FIGURES_URL to optionally serve from Supabase Storage.
 */
export function figureUrl(relativePath: string): string {
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://') || relativePath.startsWith('/')) {
    return relativePath
  }

  const storageBase = process.env.NEXT_PUBLIC_SUPABASE_FIGURES_URL
  if (storageBase) {
    // Strip leading "figures/" — the bucket root already corresponds to figures/
    const bucketPath = relativePath.replace(/^figures\//, '')
    return `${storageBase.replace(/\/$/, '')}/${bucketPath}`
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
