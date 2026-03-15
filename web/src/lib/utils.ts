// Utility helpers for data loading and formatting

import fs from 'fs'
import path from 'path'

/** Root of the repository (parent of web/) */
export function repoRoot(): string {
  return path.resolve(process.cwd(), '..')
}

/** Read a JSON manifest from web/src/content/ */
export function readManifest<T>(filename: string): T {
  const filePath = path.join(process.cwd(), 'src', 'content', filename)
  const raw = fs.readFileSync(filePath, 'utf-8')
  return JSON.parse(raw) as T
}

/** Check if a file exists relative to repo root */
export function repoFileExists(relativePath: string): boolean {
  return fs.existsSync(path.join(repoRoot(), relativePath))
}

/** Read CSV file and return parsed rows */
export function readCSV(relativePath: string): Record<string, string>[] {
  const filePath = path.join(repoRoot(), relativePath)
  if (!fs.existsSync(filePath)) return []
  const content = fs.readFileSync(filePath, 'utf-8')
  const lines = content.trim().split('\n')
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map((h) => h.trim())
  return lines.slice(1).map((line) => {
    const values = line.split(',').map((v) => v.trim())
    const row: Record<string, string> = {}
    headers.forEach((h, i) => {
      row[h] = values[i] ?? ''
    })
    return row
  })
}

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
