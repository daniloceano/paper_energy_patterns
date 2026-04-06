'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { DIAGNOSTIC_LIST } from '@/lib/constants'
import { useMemo } from 'react'

interface DiagnosticNavProps {
  currentSlug: string
}

export default function DiagnosticNav({ currentSlug }: DiagnosticNavProps) {
  const pathname = usePathname()
  
  const { prevDiag, nextDiag, currentIndex } = useMemo(() => {
    const idx = DIAGNOSTIC_LIST.findIndex(d => d.slug === currentSlug)
    return {
      currentIndex: idx,
      prevDiag: idx > 0 ? DIAGNOSTIC_LIST[idx - 1] : null,
      nextDiag: idx < DIAGNOSTIC_LIST.length - 1 ? DIAGNOSTIC_LIST[idx + 1] : null,
    }
  }, [currentSlug])

  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      {/* Previous button */}
      {prevDiag ? (
        <Link
          href={`/analyses/composites/${prevDiag.slug}`}
          className="group flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-100"
        >
          <svg className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span className="hidden sm:inline">{prevDiag.shortName}</span>
        </Link>
      ) : (
        <div className="w-20" />
      )}

      {/* Current diagnostic indicator + dropdown */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">
          {currentIndex + 1} / {DIAGNOSTIC_LIST.length}
        </span>
        <select
          value={currentSlug}
          onChange={(e) => {
            window.location.href = `/analyses/composites/${e.target.value}`
          }}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          {DIAGNOSTIC_LIST.map((d) => (
            <option key={d.id} value={d.slug}>
              {d.shortName} — {d.level}
            </option>
          ))}
        </select>
      </div>

      {/* Next button */}
      {nextDiag ? (
        <Link
          href={`/analyses/composites/${nextDiag.slug}`}
          className="group flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-100"
        >
          <span className="hidden sm:inline">{nextDiag.shortName}</span>
          <svg className="h-4 w-4 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      ) : (
        <div className="w-20" />
      )}
    </div>
  )
}
