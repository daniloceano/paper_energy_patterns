/**
 * Server-only utilities that use Node.js `fs`.
 *
 * IMPORTANT — bundle size:
 *   Import this file ONLY from server components or page.tsx files.
 *   Do NOT import it from any shared component or client component.
 *   Do NOT add repoRoot() or any path.resolve(cwd, '..') here —
 *   that pattern causes Next.js NFT to bundle the entire repo's
 *   parent directory into each serverless function.
 *
 * All paths here must stay within the web/ directory (process.cwd()
 * during build = the web/ directory).
 */

import fs from 'fs'
import path from 'path'

/**
 * Read a JSON manifest from web/src/content/.
 * The filename is just the basename, e.g. 'ck_subterms_manifest.json'.
 */
export function readManifest<T>(filename: string): T {
  const filePath = path.join(process.cwd(), 'src', 'content', filename)
  const raw = fs.readFileSync(filePath, 'utf-8')
  return JSON.parse(raw) as T
}
