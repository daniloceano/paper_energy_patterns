import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

const REPO_ROOT = path.resolve(process.cwd(), '..')

const MIME_TYPES: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.pdf': 'application/pdf',
}

const ALLOWED_DIRS = ['figures', 'docs', 'results', 'data']

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const relativePath = searchParams.get('path')

  if (!relativePath) {
    return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 })
  }

  // Security: prevent directory traversal
  const normalised = path.normalize(relativePath)
  if (normalised.includes('..') || path.isAbsolute(normalised)) {
    return NextResponse.json({ error: 'Invalid path' }, { status: 403 })
  }

  // Only allow serving from known directories
  const topDir = normalised.split(path.sep)[0]
  if (!ALLOWED_DIRS.includes(topDir)) {
    return NextResponse.json({ error: 'Access denied' }, { status: 403 })
  }

  const fullPath = path.join(REPO_ROOT, normalised)
  if (!fs.existsSync(fullPath)) {
    return NextResponse.json({ error: 'File not found' }, { status: 404 })
  }

  const ext = path.extname(fullPath).toLowerCase()
  const contentType = MIME_TYPES[ext] || 'application/octet-stream'

  const fileBuffer = fs.readFileSync(fullPath)
  return new NextResponse(fileBuffer, {
    headers: {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=3600, immutable',
    },
  })
}
