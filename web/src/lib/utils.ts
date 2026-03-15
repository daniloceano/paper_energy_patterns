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

/** Get the public URL for a figure served via the API route */
export function figureUrl(relativePath: string): string {
  return `/api/figures?path=${encodeURIComponent(relativePath)}`
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
