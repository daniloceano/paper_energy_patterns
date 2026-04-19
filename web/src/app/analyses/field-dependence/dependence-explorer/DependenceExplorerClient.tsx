'use client'

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import type { LfdPredepRow, LfdTopAssociation, LfdScatterData } from '@/lib/types'
import { LFD_DYNAMIC_FIELDS, LFD_SPATIAL_FEATURES, LFD_CANONICAL_TERMS, LFD_EP_COLORS } from '@/lib/constants'
import { figureUrl } from '@/lib/client-utils'

// ── Types ───────────────────────────────────────────────
type Metric = 'predep' | 'pearson' | 'spearman'
type Scope = 'canonical' | 'all'
type FieldType = 'absolute' | 'anomaly'

interface Props {
  predep: LfdPredepRow[]
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

function getMetricValue(row: LfdPredepRow, metric: Metric): number | null {
  if (metric === 'predep') return row.predep
  if (metric === 'pearson') return row.pearson_r != null ? Math.abs(row.pearson_r) : null
  if (metric === 'spearman') return row.spearman_rho != null ? Math.abs(row.spearman_rho) : null
  return null
}

// ── Colour helpers (grey → yellow → orange → red scale, 0.1 steps) ──
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
export default function DependenceExplorerClient({ predep, topAssociations }: Props) {
  // Filters
  const [metric, setMetric] = useState<Metric>('predep')
  const [scope, setScope] = useState<Scope>('canonical')
  const [fieldType, setFieldType] = useState<FieldType>('absolute')
  const [selectedEp, setSelectedEp] = useState<number>(1)

  // Drill-down selection
  const [selectedField, setSelectedField] = useState<string>(ALL_FIELDS[0])
  const [selectedFeature, setSelectedFeature] = useState<string>(ALL_FEATURES[0])
  const [selectedLecTerm, setSelectedLecTerm] = useState<string>('Ca')

  // Scatter data (loaded on demand)
  const [scatterData, setScatterData] = useState<LfdScatterData | null>(null)
  const [scatterLoading, setScatterLoading] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Available LEC terms based on scope
  const lecTerms = useMemo(() => {
    if (scope === 'canonical') return [...LFD_CANONICAL_TERMS]
    const all = new Set(predep.map((r) => r.lec_term))
    return Array.from(all).sort()
  }, [scope, predep])

  // Ensure selectedLecTerm is valid
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

  // ── Heatmap data: build matrix for selected EP ────────
  const heatmapData = useMemo(() => {
    const epRows = filteredPredep.filter((r) => r.ep === selectedEp)
    // Build lookup: lec_term → field__feature → value
    const lookup: Record<string, Record<string, number | null>> = {}
    for (const r of epRows) {
      const key = `${r.field}__${r.feature}`
      if (!lookup[r.lec_term]) lookup[r.lec_term] = {}
      lookup[r.lec_term][key] = getMetricValue(r, metric)
    }
    return lookup
  }, [filteredPredep, selectedEp, metric])

  // Column keys for heatmap
  const columnKeys = useMemo(() => {
    const keys: string[] = []
    for (const field of ALL_FIELDS) {
      for (const feature of ALL_FEATURES) {
        keys.push(`${field}__${feature}`)
      }
    }
    return keys
  }, [])

  // ── Drill-down: specific row from PREDEP ──────────────
  const drilldownRow = useMemo(() => {
    return filteredPredep.find(
      (r) =>
        r.ep === selectedEp &&
        r.field === selectedField &&
        r.feature === selectedFeature &&
        r.lec_term === selectedLecTerm
    ) ?? null
  }, [filteredPredep, selectedEp, selectedField, selectedFeature, selectedLecTerm])

  // ── Top associations for context ──────────────────────
  const topList = scope === 'canonical' ? topAssociations.canonical : topAssociations.all
  const topForEp = useMemo(() => topList.filter((t) => t.ep === selectedEp), [topList, selectedEp])

  // ── Load scatter data on demand ───────────────────────
  const loadScatter = useCallback(async () => {
    if (scatterLoading) return
    setScatterLoading(true)
    try {
      const resp = await fetch(`/data/lfd_scatter_${fieldType}.json`)
      if (resp.ok) {
        const data = await resp.json()
        setScatterData(data as LfdScatterData)
      }
    } catch {
      // Scatter data not available — silent fail
    } finally {
      setScatterLoading(false)
    }
  }, [fieldType, scatterLoading])

  // Reload scatter when field type changes
  useEffect(() => {
    setScatterData(null)
  }, [fieldType])

  // ── Draw scatter on canvas ────────────────────────────
  useEffect(() => {
    if (!scatterData || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const width = canvas.clientWidth
    const height = canvas.clientHeight
    canvas.width = width * dpr
    canvas.height = height * dpr
    ctx.scale(dpr, dpr)

    const featureCol = `${selectedField}__${selectedFeature}`
    const lecCol = selectedLecTerm

    // Filter to selected EP
    const points = scatterData.cyclones
      .filter((c) => c.ep === selectedEp)
      .map((c) => ({
        x: c[featureCol] as number | null,
        y: c[lecCol] as number | null,
      }))
      .filter((p) => p.x != null && p.y != null) as { x: number; y: number }[]

    if (points.length === 0) {
      ctx.clearRect(0, 0, width, height)
      ctx.fillStyle = '#94a3b8'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('No data for this selection', width / 2, height / 2)
      return
    }

    // Compute bounds
    const xVals = points.map((p) => p.x)
    const yVals = points.map((p) => p.y)
    const xMin = Math.min(...xVals)
    const xMax = Math.max(...xVals)
    const yMin = Math.min(...yVals)
    const yMax = Math.max(...yVals)
    const xRange = xMax - xMin || 1
    const yRange = yMax - yMin || 1

    const pad = { top: 20, right: 20, bottom: 45, left: 65 }
    const pw = width - pad.left - pad.right
    const ph = height - pad.top - pad.bottom

    const toX = (v: number) => pad.left + ((v - xMin) / xRange) * pw
    const toY = (v: number) => pad.top + ph - ((v - yMin) / yRange) * ph

    // Clear
    ctx.clearRect(0, 0, width, height)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    // Grid lines
    ctx.strokeStyle = '#e2e8f0'
    ctx.lineWidth = 0.5
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (ph * i) / 4
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke()
      const x = pad.left + (pw * i) / 4
      ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, pad.top + ph); ctx.stroke()
    }

    // Axis labels
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
    ctx.fillText(`${LFD_DYNAMIC_FIELDS[selectedField]?.label ?? selectedField} — ${LFD_SPATIAL_FEATURES[selectedFeature] ?? selectedFeature}`, width / 2, height - 25)
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
  }, [scatterData, selectedEp, selectedField, selectedFeature, selectedLecTerm])

  // ── Heatmap cell click handler ────────────────────────
  function handleCellClick(lecTerm: string, colKey: string) {
    const [field, feature] = colKey.split('__')
    if (field && feature) {
      setSelectedField(field)
      setSelectedFeature(feature)
      setSelectedLecTerm(lecTerm)
    }
  }

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
          Static pipeline heatmaps for PREDEP, |Pearson|, and |Spearman| ({scope === 'canonical' ? 'canonical 7 terms' : 'all 24 terms'}).
          Click a cell in the interactive heatmap below to drill down.
        </p>
        <div className="grid gap-4 md:grid-cols-3">
          {/* PREDEP */}
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">PREDEP</div>
            <img
              src={figureUrl(`figures/lec_field_dependence/${scope === 'canonical' ? 'canonical' : 'all'}/heatmap_predep_ep${selectedEp}_${fieldType}_${scope === 'canonical' ? 'canonical' : 'all'}.png`)}
              alt={`PREDEP heatmap EP${selectedEp} ${fieldType}`}
              className="w-full"
              loading="lazy"
            />
          </div>
          {/* Pearson */}
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">|Pearson r|</div>
            <img
              src={figureUrl(`figures/lec_field_dependence/diagnostics/correlation_heatmaps/${scope === 'canonical' ? 'canonical' : 'all'}/heatmap_pearson_ep${selectedEp}_${fieldType}_${scope === 'canonical' ? 'canonical' : 'all'}.png`)}
              alt={`Pearson heatmap EP${selectedEp} ${fieldType}`}
              className="w-full"
              loading="lazy"
            />
          </div>
          {/* Spearman */}
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">|Spearman ρ|</div>
            <img
              src={figureUrl(`figures/lec_field_dependence/diagnostics/correlation_heatmaps/${scope === 'canonical' ? 'canonical' : 'all'}/heatmap_spearman_ep${selectedEp}_${fieldType}_${scope === 'canonical' ? 'canonical' : 'all'}.png`)}
              alt={`Spearman heatmap EP${selectedEp} ${fieldType}`}
              className="w-full"
              loading="lazy"
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
          Click any cell to populate the explorer below with that field × feature × LEC term combination.
        </p>
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
                    const isSelected = lec === selectedLecTerm && col === `${selectedField}__${selectedFeature}`
                    return (
                      <td
                        key={col}
                        className={`cursor-pointer border border-slate-100 px-0 py-0 text-center transition-all hover:ring-2 hover:ring-indigo-400 ${isSelected ? 'ring-2 ring-indigo-600' : ''}`}
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
          {drilldownRow ? (
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
                Top Associations — {EP_LABELS[selectedEp]} ({scope})
              </h3>
              <div className="max-h-48 space-y-1 overflow-y-auto text-xs">
                {topForEp.slice(0, 10).map((t, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      const f = t.field.replace('_anom_epall', '')
                      if (ALL_FIELDS.includes(f)) setSelectedField(f)
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
            {!scatterData && (
              <button
                onClick={loadScatter}
                disabled={scatterLoading}
                className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {scatterLoading ? 'Loading…' : 'Load scatter data'}
              </button>
            )}
            {scatterData && (
              <span className="text-xs text-green-600">✓ Data loaded ({fieldType})</span>
            )}
          </div>
          <div className="rounded-lg border border-slate-200 bg-white" style={{ height: 400 }}>
            {!scatterData ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-400">
                Click &quot;Load scatter data&quot; to enable interactive scatterplots
              </div>
            ) : (
              <canvas
                ref={canvasRef}
                className="h-full w-full"
                style={{ width: '100%', height: '100%' }}
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
  return (
    <div
      className={`rounded-lg border p-3 text-center ${active ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200'}`}
    >
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div
        className="mt-1 text-2xl font-bold"
        style={{ color: metricColor(value) === '#b3b3b3' ? '#94a3b8' : metricColor(value) }}
      >
        {value != null ? value.toFixed(3) : '—'}
      </div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </div>
  )
}
