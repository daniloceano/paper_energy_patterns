'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'
import { Fragment } from 'react'

const ROUTE_LABELS: Record<string, string> = {
  analyses: 'Analyses',
  cluster: 'Cluster Analysis',
  composites: 'Composites',
  docs: 'Documentation',
  'data-references': 'Data & References',
  about: 'About',
  'step-1-case-selection-preprocessing-features': 'Step 1 — Selection & Features',
  'step-2-pca': 'Step 2 — PCA',
  'step-3-optimal-k': 'Step 3 — Optimal k',
  'step-4-clustering-lps': 'Step 4 — Clustering & LPS',
  'step-5-results': 'Step 5 — Results',
  'field-dependence': 'LEC–Field Dependence',
  'ep-differences': 'EP Differences',
  'dependence-explorer': 'Dependence Explorer',
  'ck-subterms': 'Ck Subterms',
  // Without this the fallback title-cases the segment into "Cps".
  cps: 'Cyclone Phase Space',
}

export default function Breadcrumbs() {
  const pathname = usePathname()
  if (pathname === '/') return null

  const segments = pathname.split('/').filter(Boolean)
  const crumbs = segments.map((seg, i) => ({
    label: ROUTE_LABELS[seg] || seg.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    href: '/' + segments.slice(0, i + 1).join('/'),
    isLast: i === segments.length - 1,
  }))

  return (
    <nav aria-label="Breadcrumb" className="mb-6">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-slate-500">
        <li>
          <Link href="/" className="flex items-center gap-1 hover:text-indigo-600">
            <Home className="h-3.5 w-3.5" />
            <span className="sr-only">Home</span>
          </Link>
        </li>
        {crumbs.map((crumb) => (
          <Fragment key={crumb.href}>
            <li>
              <ChevronRight className="h-3.5 w-3.5 text-slate-300" />
            </li>
            <li>
              {crumb.isLast ? (
                <span className="font-medium text-slate-900">{crumb.label}</span>
              ) : (
                <Link href={crumb.href} className="hover:text-indigo-600">
                  {crumb.label}
                </Link>
              )}
            </li>
          </Fragment>
        ))}
      </ol>
    </nav>
  )
}
