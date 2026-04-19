'use client'

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import type { LfdPredepRow, LfdTopAssociation, LfdScatterData } from '@/lib/types'
import { LFD_DYNAMIC_FIELDS, LFD_SPATIAL_FEATURES, LFD_CANONICAL_TERMS, LFD_EP_COLORS } from '@/lib/constants'

// LFD figures are committed to web/public/figures/lec_field_dependence/.
// Use absolute paths to bypass figureUrl's Supabase substitution —
// these assets are always available from Vercel's static CDN.
const lfd = (path: string) => `/figures/lec_field_dependence/${path}`

// ── Types ───────────────────────────────────────────────
type Metric = 'predep' | 'pearson' | 'spearman'
type Scope = 'canonical' | 'all'
type FieldType = 'absolute' | 'anomaly'

interface Props {
  topAssociations: { all: LfdTopAssociation[]; canonical: LfdTopAssociation[] }
}

const METRIC_LABELS: Record<Metric, string> = {
  predep: 'PREDEP',
  pearson: '|Pearson r|',
  spearman: '|Spearman ρ|',
}

const EP_LABELS: Record<number, string> = { 1: 'EP1', 2: 'EP2', 3: 'EP3' }

const ALL_FIELDS = Object.keys(LFD_DYNAMIC_FIELDS)
const ALL_FEATURES = Object.keys(LFD_SPATIAL_FEATURES)

// Anomaly field names in the data append "_anom_epall" to the base field key.
function resolveField(fieldKey: string, fieldType: FieldType): string {
  return fieldType === 'absolute' ? fieldKey : `${fieldKey}_anom_epall`
}

function getMetricValue(row: LfdPredepRow, metric: Metric): number | null {
  if (metric === 'predep') return row.predep
  if (metric === 'pearson') return row.pearson_r != null ? Math.abs(row.pearson_r) : null
  if (metric === 'spearman') return row.spearman_rho != null ? Math.abs(row.spearman_rho) : null
  return null
}

// ── Colour helpers (grey → yellow → orange → red, 0.1 steps) ──
function metricColor(val: number | null): string {
  if (val == null || val < 0.1) return '#b3b3b3'
  if (val < 0.2) return '#ffff99'
  if (val < 0.3) return '#ffe64d'
  if (val < 0.4) return '#ffcc00'
  if (val < 0.5) return '#ffb300'
  if (val < 0.6) return '#ff9900'
  if (val < 0.7) return '#ff7300'
  if (val < 0.8) return '#ff4d00'
  if (val < 0.9) return '#e62600'
  return '#cc0000'
}

function metricTextColor(val: number | null): string {
  if (val == null || val < 0.5) return '#1e293b'
  return '#ffffff'
}

// ── Component ───────────────────────────────────────────
export default function DependenceExplorerClient({ topAssociations }: Props) {
  // Filters
  const [metric, setMetric] = useState<Metric>('predep')
  const [scope, setScope] = useState<Scope>('canonical')
  const [fieldType, setFieldType] = useState<FieldType>('absolute')
  const [selectedEp, setSelectedEp] = useState<number>(1)

  // Drill-down selection
  const [selectedField, setSelectedField] = useState<string>(ALL_FIELDS[0])
  const [selectedFeature, setSelectedFeature] = useState<string>(ALL_FEATURES[0])
  const [selectedLecTerm, setSelectedLecTerm] = useState<string>('Ca')

  // Predep data (fetched client-side to avoid 3MB HTML serialisation)
  const [predep, setPredep] = useState<LfdPredepRow[]>([])
  const [predepLoading, setPredepLoading] = useState(true)
  const [predepError, setPredepError] = useState<string | null>(null)

  // Scatter data (loaded on demand — 5–7 MB)
  const [scatterData, setScatterData] = useState<LfdScatterData | null>(null)
  const [scatterLoading, setScatterLoading] = useState(false)
  const [scatterError, setScatterError] = useState<string | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // ── Fetch predep data on mount ────────────────────────
  useEffect(() => {
    let cancelled = false
    setPredepLoading(true)
    setPredepError(null)
    fetch('/data/lfd_predep.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data: LfdPredepRow[]) => {
        if (!cancelled) {
          setPredep(data)
          setPredepLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setPredepError(`Failed to load analysis data: ${err instanceof Error ? err.message : String(err)}`)
          setPredepLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [])

  // Available LEC terms based on scope and loaded data
  const lecTerms = useMemo(() => {
    if (scope === 'canonical') return [...LFD_CANONICAL_TERMS]
    if (predep.length === 0) return [...LFD_CANONICAL_TERMS]
    const all = new Set(predep.map((r) => r.lec_term))
    return Array.from(all).sort()
  }, [scope, predep])

  // Ensure selectedLecTerm is valid when scope/data changes
  useEffect(() => {
    if (!lecTerms.includes(selectedLecTerm)) {
      setSelectedLecTerm(lecTerms[0] || 'Ca')
    }
  }, [lecTerms, selectedLecTerm])

  // ── Filtered PREDEP data ──────────────────────────────
  const filteredPredep = useMemo(() => {
    return predep.filter((r) => {
      if (r.field_type !== fieldType) return false
      if (scope === 'canonical' && !r.is_canonical) return false
      return true
    })
  }, [predep, fieldType, scope])

  // ── Column keys for heatmap (use resolved field names so anomaly works) ──
  const columnKeys = useMemo(() => {
    const keys: string[] = []
    for (const field of ALL_FIELDS) {
      const resolvedField = resolveField(field, fieldType)
      for (const feature of ALL_FEATURES) {
        keys.push(`${resolvedField}__${feature}`)
      }
    }
    return keys
  }, [fieldType])

  // ── Heatmap data: build matrix for selected EP ────────
  const heatmapData = useMemo(() => {
    const epRows = filteredPredep.filter((r) => r.ep === selectedEp)
    const lookup: Record<string, Record<string, number | null>> = {}
    for (const r of epRows) {
      const key = `${r.field}__${r.feature}`
      if (!lookup[r.lec_term]) lookup[r.lec_term] = {}
      lookup[r.lec_term][key] = getMetricValue(r, metric)
    }
    return lookup
  }, [filteredPredep, selectedEp, metric])

  // ── Drill-down: specific predep row ──────────────────
  const drilldownRow = useMemo(() => {
    const resolvedField = resolveField(selectedField, fieldType)
    return filteredPredep.find(
      (r) =>
        r.ep === selectedEp &&
        r.field === resolvedField &&
        r.feature === selectedFeature &&
        r.lec_term === selectedLecTerm
    ) ?? null
  }, [filteredPredep, selectedEp, selectedField, selectedFeature, selectedLecTerm, fieldType])

  // ── Top associations ──────────────────────────────────
  const topList = scope === 'canonical' ? topAssociations.canonical : topAssociations.all
  const topForEp = useMemo(() => topList.filter((t) => t.ep === selectedEp), [topList, selectedEp])

  // ── Load scatter data on demand ───────────────────────
  const loadScatter = useCallback(async () => {
    setScatterLoading(true)
    setScatterError(null)
    try {
      const resp = await fetch(`/data/lfd_scatter_${fieldType}.json`)
      if (!resp.ok) throw new Error(`HTTP ${resp.status} — scatter data unavailable`)
      const data = await resp.json() as LfdScatterData
      setScatterData(data)
    } catch (err: unknown) {
      setScatterError(err instanceof Error ? err.message : 'Failed to load scatter data')
    } finally {
      setScatterLoading(false)
    }
  }, [fieldType])

  // Clear scatter data when field type changes
  useEffect(() => {
    setScatterData(null)
    setScatterError(null)
  }, [fieldType])

  // ── Draw scatter on canvas ────────────────────────────
  useEffect(() => {
    if (!scatterData) return

    // Use requestAnimationFrame to ensure canvas has layout dimensions
    const rafId = requestAnimationFrame(() => {
      const canvas = canvasRef.current
      if (!canvas) return

      const width = canvas.clientWidth || canvas.offsetWidth
      const height = canvas.clientHeight || canvas.offsetHeight
      if (width === 0 || height === 0) return

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const dpr = window.devicePixelRatio || 1
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.scale(dpr, dpr)

      const resolvedField = resolveField(selectedField, fieldType)
      const featureCol = `${resolvedField}__${selectedFeature}`
      const lecCol = selectedLecTerm

      const points = scatterData.cyclones
        .filter((c) => c.ep === selectedEp)
        .map((c) => ({ x: c[featureCol] as number | null, y: c[lecCol] as number | null }))
        .filter((p) => p.x != null && p.y != null) as { x: number; y: number }[]

      if (points.length === 0) {
        ctx.clearRect(0, 0, width, height)
        ctx.fillStyle = '#94a3b8'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('No data for this selection', width / 2, height / 2)
        return
      }

      const xVals = points.map((p) => p.x)
      const yVals = points.map((p) => p.y)
      const xMin = Math.min(...xVals), xMax = Math.max(...xVals)
      const yMin = Math.min(...yVals), yMax = Math.max(...yVals)
      const xRange = xMax - xMin || 1
      const yRange = yMax - yMin || 1

      const pad = { top: 20, right: 20, bottom: 45, left: 65 }
      const pw = width - pad.left - pad.right
      const ph = height - pad.top - pad.bottom

      const toX = (v: number) => pad.left + ((v - xMin) / xRange) * pw
      const toY = (v: number) => pad.top + ph - ((v - yMin) / yRange) * ph

      ctx.clearRect(0, 0, width, height)
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, width, height)

      // Grid
      ctx.strokeStyle = '#e2e8f0'
      ctx.lineWidth = 0.5
      for (let i = 0; i <= 4; i++) {
        const y = pad.top + (ph * i) / 4
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke()
        const x = pad.left + (pw * i) / 4
        ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, pad.top + ph); ctx.stroke()
      }

      // Axis tick labels
      ctx.fillStyle = '#64748b'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      for (let i = 0; i <= 4; i++) {
        const xv = xMin + (xRange * i) / 4
        ctx.fillText(xv.toExponential(1), toX(xv), height - 5)
      }
      ctx.textAlign = 'right'
      for (let i = 0; i <= 4; i++) {
        const yv = yMin + (yRange * i) / 4
        ctx.fillText(yv.toExponential(1), pad.left - 5, toY(yv) + 4)
      }

      // Axis titles
      ctx.fillStyle = '#334155'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      const xLabel = `${LFD_DYNAMIC_FIELDS[selectedField]?.label ?? selectedField} — ${LFD_SPATIAL_FEATURES[selectedFeature] ?? selectedFeature}`
      ctx.fillText(xLabel, width / 2, height - 25)
      ctx.save()
      ctx.translate(14, height / 2)
      ctx.rotate(-Math.PI / 2)
      ctx.fillText(selectedLecTerm, 0, 0)
      ctx.restore()

      // Points
      const epColor = LFD_EP_COLORS[selectedEp] ?? '#6366f1'
      ctx.fillStyle = epColor + '99'
      for (const p of points) {
        ctx.beginPath()
        ctx.arc(toX(p.x), toY(p.y), 2.5, 0, Math.PI * 2)
        ctx.fill()
      }

      // N label
      ctx.fillStyle = '#64748b'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(`N = ${points.length}`, width - pad.right, pad.top - 5)
    })

    return () => cancelAnimationFrame(rafId)
  }, [scatterData, selectedEp, selectedField, selectedFeature, selectedLecTerm, fieldType])

  // ── Heatmap cell click ────────────────────────────────
  function handleCellClick(lecTerm: string, colKey: string) {
    const sepIdx = colKey.indexOf('__')
    if (sepIdx === -1) return
    const resolvedField = colKey.slice(0, sepIdx)
    const feature = colKey.slice(sepIdx + 2)
    // Strip _anom_epall suffix to get the base field key
    const baseField = resolvedField.replace(/_anom_epall$/, '')
    if (ALL_FIELDS.includes(baseField)) setSelectedField(baseField)
    if (ALL_FEATURES.includes(feature)) setSelectedFeature(feature)
    setSelectedLecTerm(lecTerm)
  }

  // ── Scope label ───────────────────────────────────────
  const scopeLabel = scope === 'canonical' ? 'canonical' : 'all'

  return (
    <div className="mt-8 space-y-8">
      {/* ── Global Controls ──────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Metric */}
        <div className="flex rounded-lg border border-slate-200 text-sm">
          {(['predep', 'pearson', 'spearman'] as Metric[]).map((m) => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              className={`px-3 py-1.5 first:rounded-l-lg last:rounded-r-lg ${metric === m ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
            >
              {METRIC_LABELS[m]}
            </button>
          ))}
        </div>

        {/* Scope */}
        <div className="flex rounded-lg border border-slate-200 text-sm">
          <button
            onClick={() => setScope('canonical')}
            className={`rounded-l-lg px-3 py-1.5 ${scope === 'canonical' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            Canonical
          </button>
          <button
            onClick={() => setScope('all')}
            className={`rounded-r-lg px-3 py-1.5 ${scope === 'all' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            All terms
          </button>
        </div>

        {/* Field type */}
        <div className="flex rounded-lg border border-slate-200 text-sm">
          <button
            onClick={() => setFieldType('absolute')}
            className={`rounded-l-lg px-3 py-1.5 ${fieldType === 'absolute' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            Absolute
          </button>
          <button
            onClick={() => setFieldType('anomaly')}
            className={`rounded-r-lg px-3 py-1.5 ${fieldType === 'anomaly' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            Anomaly
          </button>
        </div>

        {/* EP */}
        <div className="flex rounded-lg border border-slate-200 text-sm">
          {[1, 2, 3].map((ep) => (
            <button
              key={ep}
              onClick={() => setSelectedEp(ep)}
              className={`px-3 py-1.5 first:rounded-l-lg last:rounded-r-lg ${selectedEp === ep ? 'text-white' : 'text-slate-600 hover:bg-slate-50'}`}
              style={selectedEp === ep ? { backgroundColor: LFD_EP_COLORS[ep] } : {}}
            >
              {EP_LABELS[ep]}
            </button>
          ))}
        </div>
      </div>

      {/* ── Reference Heatmaps (static figures) ──────── */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">
          Reference Heatmaps — {EP_LABELS[selectedEp]}
        </h2>
        <p className="mb-4 text-sm text-slate-500">
          Static pipeline heatmaps for PREDEP, |Pearson|, and |Spearman| — {scopeLabel} terms,
          {fieldType} values. Click any cell in the interactive heatmap below to drill down.
        </p>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">PREDEP</div>
            <img
              src={lfd(`${scopeLabel}/heatmap_predep_ep${selectedEp}_${fieldType}_${scopeLabel}.png`)}
              alt={`PREDEP heatmap EP${selectedEp} ${fieldType}`}
              className="w-full"
              loading="lazy"
              onError={(e) => { (e.target as HTMLImageElement).alt = 'Figure not available' }}
            />
          </div>
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">|Pearson r|</div>
            <img
              src={lfd(`diagnostics/correlation_heatmaps/${scopeLabel}/heatmap_pearson_ep${selectedEp}_${fieldType}_${scopeLabel}.png`)}
              alt={`Pearson heatmap EP${selectedEp} ${fieldType}`}
              className="w-full"
              loading="lazy"
              onError={(e) => { (e.target as HTMLImageElement).alt = 'Figure not available' }}
            />
          </div>
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">|Spearman ρ|</div>
            <img
              src={lfd(`diagnostics/correlation_heatmaps/${scopeLabel}/heatmap_spearman_ep${selectedEp}_${fieldType}_${scopeLabel}.png`)}
              alt={`Spearman heatmap EP${selectedEp} ${fieldType}`}
              className="w-full"
              loading="lazy"
              onError={(e) => { (e.target as HTMLImageElement).alt = 'Figure not available' }}
            />
          </div>
        </div>
      </section>

      {/* ── Interactive Heatmap ──────────────────────── */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">
          Interactive Heatmap — {METRIC_LABELS[metric]}, {EP_LABELS[selectedEp]}, {fieldType}
        </h2>
        <p className="mb-4 text-sm text-slate-500">
          Click any cell to populate the explorer below with that field × feature × LEC term.
        </p>

        {predepLoading && (
          <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-slate-400">
            Loading analysis data (2.7 MB)…
          </div>
        )}
        {predepError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {predepError}
          </div>
        )}
        {!predepLoading && !predepError && (
          <>
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="text-xs">
                <thead>
                  <tr>
                    <th className="sticky left-0 z-10 bg-white px-2 py-1 text-left font-medium text-slate-600">
                      LEC
                    </th>
                    {ALL_FIELDS.map((field) => (
                      <th
                        key={field}
                        colSpan={ALL_FEATURES.length}
                        className="border-l border-slate-200 px-1 py-1 text-center font-medium text-slate-600"
                      >
                        {LFD_DYNAMIC_FIELDS[field]?.label ?? field}
                      </th>
                    ))}
                  </tr>
                  <tr>
                    <th className="sticky left-0 z-10 bg-white px-2 py-1" />
                    {ALL_FIELDS.flatMap((field) =>
                      ALL_FEATURES.map((feature) => (
                        <th
                          key={`${field}__${feature}`}
                          className="border-l border-slate-100 px-0.5 py-0.5 text-center font-normal text-slate-400"
                          style={{ writingMode: 'vertical-rl', fontSize: '9px', maxHeight: '60px' }}
                        >
                          {LFD_SPATIAL_FEATURES[feature] ?? feature}
                        </th>
                      ))
                    )}
                  </tr>
                </thead>
                <tbody>
                  {lecTerms.map((lec) => (
                    <tr key={lec}>
                      <td className="sticky left-0 z-10 bg-white px-2 py-1 font-medium text-slate-800">
                        {lec}
                      </td>
                      {columnKeys.map((col) => {
                        const val = heatmapData[lec]?.[col] ?? null
                        const [resolvedF] = col.split('__')
                        const baseF = (resolvedF ?? '').replace(/_anom_epall$/, '')
                        const isSelected =
                          lec === selectedLecTerm &&
                          baseF === selectedField &&
                          col.endsWith(`__${selectedFeature}`)
                        return (
                          <td
                            key={col}
                            className={`cursor-pointer border border-slate-100 px-0 py-0 text-center transition-all hover:ring-2 hover:ring-inset hover:ring-indigo-400 ${isSelected ? 'ring-2 ring-inset ring-indigo-600' : ''}`}
                            style={{
                              backgroundColor: metricColor(val),
                              color: metricTextColor(val),
                              minWidth: '16px',
                              height: '20px',
                              fontSize: '8px',
                            }}
                            title={`${lec} × ${col.replace('__', ' — ')}: ${val?.toFixed(3) ?? 'N/A'}`}
                            onClick={() => handleCellClick(lec, col)}
                          >
                            {val != null && val >= 0.1 ? val.toFixed(2) : ''}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Legend */}
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-500">
              <span>0</span>
              {[0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95].map((v) => (
                <div
                  key={v}
                  className="h-3 w-6 rounded-sm"
                  style={{ backgroundColor: metricColor(v) }}
                />
              ))}
              <span>1</span>
            </div>
          </>
        )}
      </section>

      {/* ── Drill-Down Explorer ──────────────────────── */}
      <section className="grid gap-6 lg:grid-cols-2">
        {/* Left: Selectors + Metrics */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Detail Explorer</h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Dynamic Field</label>
              <select
                value={selectedField}
                onChange={(e) => setSelectedField(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                {ALL_FIELDS.map((f) => (
                  <option key={f} value={f}>{LFD_DYNAMIC_FIELDS[f]?.label ?? f}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Spatial Feature</label>
              <select
                value={selectedFeature}
                onChange={(e) => setSelectedFeature(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                {ALL_FEATURES.map((f) => (
                  <option key={f} value={f}>{LFD_SPATIAL_FEATURES[f] ?? f}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">LEC Term</label>
              <select
                value={selectedLecTerm}
                onChange={(e) => setSelectedLecTerm(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                {lecTerms.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Energy Pattern</label>
              <select
                value={selectedEp}
                onChange={(e) => setSelectedEp(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                {[1, 2, 3].map((ep) => (
                  <option key={ep} value={ep}>{EP_LABELS[ep]}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Metric card */}
          {predepLoading ? (
            <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-400">
              Loading data…
            </div>
          ) : drilldownRow ? (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-2 text-sm font-medium text-slate-700">
                {drilldownRow.display} → {drilldownRow.lec_term}
                <span className="ml-2 text-xs text-slate-400">
                  ({EP_LABELS[drilldownRow.ep]}, {drilldownRow.field_type}, N = {drilldownRow.n ?? '—'})
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <MetricCard label="PREDEP" value={drilldownRow.predep} active={metric === 'predep'} />
                <MetricCard
                  label="|Pearson r|"
                  value={drilldownRow.pearson_r != null ? Math.abs(drilldownRow.pearson_r) : null}
                  active={metric === 'pearson'}
                  sub={drilldownRow.pearson_p != null ? `p = ${drilldownRow.pearson_p < 0.001 ? drilldownRow.pearson_p.toExponential(1) : drilldownRow.pearson_p.toFixed(4)}` : undefined}
                />
                <MetricCard
                  label="|Spearman ρ|"
                  value={drilldownRow.spearman_rho != null ? Math.abs(drilldownRow.spearman_rho) : null}
                  active={metric === 'spearman'}
                  sub={drilldownRow.spearman_p != null ? `p = ${drilldownRow.spearman_p < 0.001 ? drilldownRow.spearman_p.toExponential(1) : drilldownRow.spearman_p.toFixed(4)}` : undefined}
                />
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
              No data for this selection.
            </div>
          )}

          {/* Top associations sidebar */}
          {topForEp.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">
                Top Associations — {EP_LABELS[selectedEp]} ({scopeLabel})
              </h3>
              <div className="max-h-48 space-y-1 overflow-y-auto text-xs">
                {topForEp.slice(0, 10).map((t, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      // Strip _anom_epall suffix to get base field key
                      const baseF = t.field.replace(/_anom_epall$/, '')
                      if (ALL_FIELDS.includes(baseF)) setSelectedField(baseF)
                      if (ALL_FEATURES.includes(t.feature)) setSelectedFeature(t.feature)
                      setSelectedLecTerm(t.lec_term)
                    }}
                    className="block w-full rounded px-2 py-1 text-left hover:bg-indigo-50"
                  >
                    <span className="font-medium text-slate-700">{t.display}</span>
                    <span className="text-slate-400"> → {t.lec_term}</span>
                    <span className="float-right font-mono text-indigo-600">
                      {t.predep?.toFixed(3)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Scatterplot */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Scatterplot</h2>
            {!scatterData && !scatterLoading && !scatterError && (
              <button
                onClick={loadScatter}
                className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700"
              >
                Load scatter data
              </button>
            )}
            {scatterLoading && (
              <span className="text-sm text-slate-400">Loading scatter data (5–7 MB)…</span>
            )}
            {scatterData && !scatterLoading && (
              <span className="text-xs text-green-600">✓ Loaded ({fieldType})</span>
            )}
          </div>

          {scatterError && (
            <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {scatterError}
              <button
                onClick={loadScatter}
                className="ml-3 text-red-600 underline hover:no-underline"
              >
                Retry
              </button>
            </div>
          )}

          <div className="rounded-lg border border-slate-200 bg-white" style={{ height: 400 }}>
            {!scatterData ? (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-slate-400">
                <span>Click &quot;Load scatter data&quot; to enable interactive scatterplots</span>
                <span className="text-xs">~5–7 MB download per field type</span>
              </div>
            ) : (
              <canvas
                ref={canvasRef}
                className="h-full w-full"
                style={{ display: 'block', width: '100%', height: '100%' }}
              />
            )}
          </div>
          {scatterData && drilldownRow && (
            <p className="mt-2 text-xs text-slate-500">
              {LFD_DYNAMIC_FIELDS[selectedField]?.label ?? selectedField} — {LFD_SPATIAL_FEATURES[selectedFeature] ?? selectedFeature} (x)
              vs {selectedLecTerm} (y) for {EP_LABELS[selectedEp]} cyclones.
              Each dot = one cyclone during intensification.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

// ── Metric display card ─────────────────────────────────
function MetricCard({
  label,
  value,
  active,
  sub,
}: {
  label: string
  value: number | null
  active: boolean
  sub?: string
}) {
  const color = metricColor(value)
  return (
    <div
      className={`rounded-lg border p-3 text-center ${active ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200'}`}
    >
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div
        className="mt-1 text-2xl font-bold"
        style={{ color: color === '#b3b3b3' ? '#94a3b8' : color }}
      >
        {value != null ? value.toFixed(3) : '—'}
      </div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </div>
  )
}


