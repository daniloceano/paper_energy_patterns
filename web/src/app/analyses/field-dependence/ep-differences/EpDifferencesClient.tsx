'use client'

import { useState, useMemo } from 'react'
import type { LfdSignificanceRow, LfdPairwiseRow } from '@/lib/types'

interface Props {
  significance: LfdSignificanceRow[]
  pairwise: LfdPairwiseRow[]
}

type ViewMode = 'omnibus' | 'pairwise'
type ScopeFilter = 'all' | 'canonical' | 'exploratory'
type TypeFilter = 'all' | 'LEC term' | 'dynamic feature'
type SortKey = string
type SortDir = 'asc' | 'desc'

export default function EpDifferencesClient({ significance, pairwise }: Props) {
  const [view, setView] = useState<ViewMode>('omnibus')
  const [scope, setScope] = useState<ScopeFilter>('canonical')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [sortKey, setSortKey] = useState<SortKey>('effect_size')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  // ── Omnibus table ──────────────────────────────────────
  const omnibusRows = useMemo(() => {
    let rows = [...significance]
    if (scope === 'canonical') rows = rows.filter((r) => r.is_canonical)
    if (scope === 'exploratory') rows = rows.filter((r) => !r.is_canonical)
    if (typeFilter === 'LEC term') rows = rows.filter((r) => r.var_type === 'LEC term')
    if (typeFilter === 'dynamic feature') rows = rows.filter((r) => r.var_type !== 'LEC term')

    rows.sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[sortKey]
      const bv = (b as unknown as Record<string, unknown>)[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv))
      return sortDir === 'desc' ? -cmp : cmp
    })
    return rows
  }, [significance, scope, typeFilter, sortKey, sortDir])

  // ── Pairwise table ─────────────────────────────────────
  const pairwiseRows = useMemo(() => {
    let rows = [...pairwise]
    if (scope === 'canonical') rows = rows.filter((r) => r.is_canonical)
    if (scope === 'exploratory') rows = rows.filter((r) => !r.is_canonical)
    if (typeFilter === 'LEC term') rows = rows.filter((r) => r.var_type === 'LEC term')
    if (typeFilter === 'dynamic feature') rows = rows.filter((r) => r.var_type !== 'LEC term')

    rows.sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[sortKey]
      const bv = (b as unknown as Record<string, unknown>)[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv))
      return sortDir === 'desc' ? -cmp : cmp
    })
    return rows
  }, [pairwise, scope, typeFilter, sortKey, sortDir])

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir(sortDir === 'desc' ? 'asc' : 'desc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  function SortIndicator({ col }: { col: string }) {
    if (sortKey !== col) return <span className="ml-1 text-slate-300">↕</span>
    return <span className="ml-1">{sortDir === 'desc' ? '↓' : '↑'}</span>
  }

  function fmtP(p: number | null): string {
    if (p == null) return '—'
    if (p < 1e-100) return '< 1e-100'
    if (p < 0.001) return p.toExponential(1)
    return p.toFixed(4)
  }

  function fmtEffect(e: number | null): string {
    if (e == null) return '—'
    return Math.abs(e).toFixed(4)
  }

  function effectBadge(e: number | null): string {
    if (e == null) return 'bg-slate-100 text-slate-500'
    const abs = Math.abs(e)
    if (abs >= 0.14) return 'bg-red-100 text-red-800'
    if (abs >= 0.06) return 'bg-orange-100 text-orange-800'
    if (abs >= 0.01) return 'bg-yellow-100 text-yellow-800'
    return 'bg-slate-100 text-slate-500'
  }

  return (
    <div>
      {/* ── Controls ──────────────────────────────────── */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {/* View toggle */}
        <div className="flex rounded-lg border border-slate-200 text-sm">
          <button
            onClick={() => { setView('omnibus'); setSortKey('effect_size') }}
            className={`px-3 py-1.5 ${view === 'omnibus' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'} rounded-l-lg`}
          >
            Omnibus
          </button>
          <button
            onClick={() => { setView('pairwise'); setSortKey('effect_size') }}
            className={`px-3 py-1.5 ${view === 'pairwise' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'} rounded-r-lg`}
          >
            Pairwise
          </button>
        </div>

        {/* Scope */}
        <select
          value={scope}
          onChange={(e) => setScope(e.target.value as ScopeFilter)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700"
        >
          <option value="canonical">Canonical (7 terms)</option>
          <option value="all">All variables</option>
          <option value="exploratory">Exploratory only</option>
        </select>

        {/* Type */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700"
        >
          <option value="all">All types</option>
          <option value="LEC term">LEC terms</option>
          <option value="dynamic feature">Dynamic features</option>
        </select>

        <span className="text-xs text-slate-400">
          {view === 'omnibus' ? omnibusRows.length : pairwiseRows.length} rows
        </span>
      </div>

      {/* ── Omnibus Table ─────────────────────────────── */}
      {view === 'omnibus' && (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <Th col="display_name" label="Variable" />
                <Th col="var_type" label="Type" />
                <Th col="global_test" label="Test" />
                <Th col="global_p" label="p (adj)" />
                <Th col="effect_size" label="Effect (ε²)" />
                <th className="px-3 py-2 text-left font-medium text-slate-600">Decision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {omnibusRows.map((r, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">{r.display_name}</td>
                  <td className="px-3 py-2 text-slate-500">{r.var_type}</td>
                  <td className="px-3 py-2 text-slate-500">{r.global_test}</td>
                  <td className="px-3 py-2 font-mono text-xs">{fmtP(r.global_p)}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${effectBadge(r.effect_size)}`}>
                      {fmtEffect(r.effect_size)}
                    </span>
                  </td>
                  <td className="max-w-xs truncate px-3 py-2 text-xs text-slate-500" title={r.decision}>
                    {r.decision}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Pairwise Table ────────────────────────────── */}
      {view === 'pairwise' && (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <Th col="display_name" label="Variable" />
                <Th col="contrast" label="Contrast" />
                <Th col="p_adjusted" label="p (adj)" />
                <Th col="effect_size" label="|r|" />
                <Th col="direction" label="Direction" />
                <Th col="mean_1" label="Mean₁" />
                <Th col="mean_2" label="Mean₂" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pairwiseRows.map((r, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">{r.display_name}</td>
                  <td className="px-3 py-2 text-slate-600">{r.contrast}</td>
                  <td className="px-3 py-2 font-mono text-xs">{fmtP(r.p_adjusted)}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${effectBadge(r.effect_size)}`}>
                      {fmtEffect(r.effect_size)}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">{r.direction}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.mean_1?.toExponential(2) ?? '—'}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.mean_2?.toExponential(2) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )

  function Th({ col, label }: { col: string; label: string }) {
    return (
      <th
        className="cursor-pointer select-none px-3 py-2 text-left font-medium text-slate-600 hover:text-indigo-600"
        onClick={() => handleSort(col)}
      >
        {label}
        <SortIndicator col={col} />
      </th>
    )
  }
}
