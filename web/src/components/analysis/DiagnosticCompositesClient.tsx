'use client'

import { useMemo } from 'react'
// Mode switcher removed - using canonical method only
import FallbackImage from '@/components/analysis/FallbackImage'
import { figureUrl } from '@/lib/client-utils'
import { DATASET_STATS } from '@/lib/constants'
import type { Diagnostic } from '@/lib/types'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'

// --- Manifest types ---
interface FigureEntry {
  exists: boolean
  api_path: string
}

interface FiguresManifest {
  [diagId: string]: {
    real: FigureEntry
    anom?: FigureEntry
    diff?: FigureEntry
  }
}

interface DomainStatEntry {
  diagnostic_id: string
  ep: string
  unit: string
  inside_15x15: string | null
  outside_15x15: string | null
}

interface BoundaryFluxEntry {
  diagnostic_id: string
  ep: string
  unit: string
  north: string | null
  south: string | null
  east: string | null
  west: string | null
  north_anom?: string | null
  south_anom?: string | null
  east_anom?: string | null
  west_anom?: string | null
}

// --- Props ---
interface DiagnosticCompositesClientProps {
  diag: Diagnostic
  figSlug: { real: string; anom?: string; diff?: string }
  isFluxDiag: boolean
  // Canonical method data (central timesteps only)
  figures: FiguresManifest
  stats: DomainStatEntry[]
  fluxes: BoundaryFluxEntry[]
}

function DiagnosticCompositesContent({
  diag,
  figSlug,
  isFluxDiag,
  figures,
  stats,
  fluxes,
}: DiagnosticCompositesClientProps) {
  // CANONICAL METHOD (April 2026): Central timesteps only - no mode switching
  const figuresManifest = figures
  const domainStats = stats
  const boundaryFluxes = fluxes

  const diagStats = useMemo(() => domainStats.filter((s) => s.diagnostic_id === diag.id), [domainStats, diag.id])
  const diagFluxes = useMemo(() => boundaryFluxes.filter((f) => f.diagnostic_id === diag.id), [boundaryFluxes, diag.id])
  
  const figInfo = figuresManifest[diag.id] ?? null
  const ep1Stats = diagStats.find((s) => s.ep === 'EP1')
  const ep2Stats = diagStats.find((s) => s.ep === 'EP2')
  const ep1Fluxes = diagFluxes.find((f) => f.ep === 'EP1')
  const ep2Fluxes = diagFluxes.find((f) => f.ep === 'EP2')

  const realFig = figInfo?.real
  const anomFig = figInfo?.anom
  const diffFig = figInfo?.diff
  const hasRealFigure = realFig?.exists ?? false
  const hasAnomFigure = (anomFig?.exists ?? false) && diag.hasAnomaly
  const hasDiffFigure = diffFig?.exists ?? false
  const hasStats = diagStats.length > 0

  // Clean filenames (no mode suffix in canonical method)
  const realFigFilename = figSlug.real
  // Anomalies do NOT get mode suffix - they're relative to climatology
  const anomFigFilename = figSlug.anom
  // Difference figures do NOT get mode suffix
  const diffFigFilename = figSlug.diff

  return (
    <div className="space-y-8">
      {/* Mode Switcher */}

      {/* Composite maps */}
      <section>
        <h2 className="mb-3 text-lg font-bold text-slate-900">
          Composite Maps — EP1 vs EP2
        </h2>

        {hasRealFigure ? (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
              <p className="text-xs text-slate-500">
                <strong>Central Timesteps Method:</strong> Composites centered on selected intensification timesteps (typically 2-3 per case).
                Storm-centred {DATASET_STATS.domainSize} composite. Left: EP1. Right: EP2.
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Source: <code>figures/ep_structure/{realFigFilename}</code>
              </p>
            </div>
            <div className="p-4">
              <FallbackImage
                src={figureUrl(realFig!.api_path)}
                alt={`${diag.name} composite — EP1 vs EP2 (Central Timesteps)`}
                width={1200}
                height={600}
                className="w-full rounded-lg"
                key={realFig!.api_path}
              />
            </div>
          </div>
        ) : (
          <ResultSummaryCallout type="info" title="Composite figures not yet generated">
            <p>
              Run <code>scripts/ep_structure_analysis/step4_create_figures.py</code> to generate
              composite figures for {diag.name}. The expected output is{' '}
              <code>figures/ep_structure/{realFigFilename}</code>.
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Then run <code>scripts/web/extract_composite_site_data.py</code> to update the web manifests.
            </p>
          </ResultSummaryCallout>
        )}

        {/* Anomaly composite */}
        {diag.hasAnomaly && (
          <div className="mt-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-700">
              Anomaly Composite
              <span className="ml-2 text-xs font-normal text-slate-400">
                (relative to {DATASET_STATS.climatologyPeriod} climatology)
              </span>
            </h3>
            {hasAnomFigure ? (
              <div className="overflow-hidden rounded-xl border border-amber-200 bg-white">
                <div className="border-b border-amber-100 bg-amber-50 px-4 py-3">
                  <p className="text-xs text-amber-700">
                    Source: <code>figures/ep_structure/{anomFigFilename}</code>
                  </p>
                </div>
                <div className="p-4">
                  <FallbackImage
                    src={figureUrl(anomFig!.api_path)}
                    alt={`${diag.name} anomaly composite — EP1 vs EP2 (Central Timesteps)`}
                    width={1200}
                    height={600}
                    className="w-full rounded-lg"
                    key={anomFig!.api_path}
                  />
                </div>
              </div>
            ) : (
              <div className="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/50 p-6 text-center">
                <p className="text-sm font-medium text-amber-600">
                  {diag.shortName} anomaly composite
                </p>
                <p className="mt-1 text-xs text-amber-400">
                  Expected: <code>figures/ep_structure/{anomFigFilename ?? 'composite_*_anom.png'}</code>
                </p>
              </div>
            )}
          </div>
        )}

        {/* EP1 − EP2 Difference composite */}
        <div className="mt-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">
            EP1 − EP2 Difference
            <span className="ml-2 text-xs font-normal text-slate-400">
              (point-by-point subtraction in storm-relative coordinates)
            </span>
          </h3>
          {hasDiffFigure ? (
            <div className="overflow-hidden rounded-xl border border-teal-200 bg-white">
              <div className="border-b border-teal-100 bg-teal-50 px-4 py-3">
                <p className="text-xs text-teal-700">
                  <strong>Diverging scale:</strong> positive (warm colors) = EP1 &gt; EP2, negative (cool colors) = EP1 &lt; EP2.
                </p>
                <p className="mt-1 text-xs text-teal-500">
                  Source: <code>figures/ep_structure/{diffFigFilename}</code>
                </p>
              </div>
              <div className="p-4">
                <FallbackImage
                  src={figureUrl(diffFig!.api_path)}
                  alt={`${diag.name} difference — EP1 minus EP2 (Central Timesteps)`}
                  width={1000}
                  height={800}
                  className="w-full max-w-2xl mx-auto rounded-lg"
                  key={diffFig!.api_path}
                />
              </div>
            </div>
          ) : (
            <div className="rounded-xl border-2 border-dashed border-teal-300 bg-teal-50/50 p-6 text-center">
              <p className="text-sm font-medium text-teal-600">
                {diag.shortName} difference (EP1 − EP2)
              </p>
              <p className="mt-1 text-xs text-teal-400">
                Expected: <code>figures/ep_structure/{diffFigFilename ?? 'composite_*_diff.png'}</code>
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Domain statistics */}
      <section>
        <h2 className="mb-3 text-lg font-bold text-slate-900">
          Domain Statistics
        </h2>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
            <h4 className="text-sm font-semibold text-slate-700">
              Mean values inside/outside {DATASET_STATS.innerDomainSize} domain [{diag.unit}]
            </h4>
            <p className="mt-0.5 text-xs text-slate-400">
              Composite method: Central Timesteps
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/50">
                  <th className="px-4 py-3 text-left font-semibold text-slate-600">Pattern</th>
                  <th className="px-4 py-3 text-right font-semibold text-slate-600">
                    Inside {DATASET_STATS.innerDomainSize}
                  </th>
                  <th className="px-4 py-3 text-right font-semibold text-slate-600">
                    Outside {DATASET_STATS.innerDomainSize}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-medium text-slate-900">EP1</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {ep1Stats?.inside_15x15 ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {ep1Stats?.outside_15x15 ?? '—'}
                  </td>
                </tr>
                <tr className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-medium text-slate-900">EP2</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {ep2Stats?.inside_15x15 ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {ep2Stats?.outside_15x15 ?? '—'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="border-t border-slate-100 px-4 py-2">
            <p className="text-xs text-slate-400">
              &ldquo;Inside&rdquo; = mean within the central {DATASET_STATS.innerDomainSize} LEC subdomain (±7.5° from cyclone centre).
              &ldquo;Outside&rdquo; = mean over the full {DATASET_STATS.domainSize} domain.
              {!hasStats && ' Run step5 + extract_composite_site_data.py to populate.'}
            </p>
          </div>
        </div>
      </section>

      {/* Boundary flux table */}
      {isFluxDiag && (
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Boundary Flux — {DATASET_STATS.innerDomainSize} Domain
          </h2>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
              <h4 className="text-sm font-semibold text-slate-700">
                Mean flux along each boundary [{diag.unit}]
              </h4>
              <p className="mt-0.5 text-xs text-slate-400">
                Composite method: Central Timesteps
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/50">
                    <th className="px-4 py-3 text-left font-semibold text-slate-600" rowSpan={2}>Pattern</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600" colSpan={2}>North</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600" colSpan={2}>South</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600" colSpan={2}>East</th>
                    <th className="px-3 py-2 text-center font-semibold text-slate-600" colSpan={2}>West</th>
                  </tr>
                  <tr className="border-b border-slate-200 bg-slate-50/50">
                    {(['North','South','East','West'] as const).flatMap((_, i) => [
                      <th key={`t${i}`} className="px-3 py-1 text-right text-xs font-medium text-slate-500">total</th>,
                      <th key={`a${i}`} className="px-3 py-1 text-right text-xs font-medium text-amber-500">anom′</th>,
                    ])}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {([['EP1', ep1Fluxes], ['EP2', ep2Fluxes]] as [string, typeof ep1Fluxes][]).map(([label, f]) => (
                    <tr key={label} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-900">{label}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.north ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-amber-600">{f?.north_anom ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.south ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-amber-600">{f?.south_anom ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.east ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-amber-600">{f?.east_anom ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.west ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-amber-600">{f?.west_anom ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-slate-100 px-4 py-2">
              <p className="text-xs text-slate-400">
                Mean {diag.shortName} along each edge of the {DATASET_STATS.innerDomainSize} inner domain (±7.5°).
                <span className="ml-1 text-amber-500 font-medium">anom′</span>
                {' '}= anomaly relative to ERA5 1991–2020 climatology.
                Source: <code>step5_update_scientific_notes.py</code> → <code>results/ep_structure/composite_stats.json</code>.
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

// Export directly without mode provider (canonical method only)
export default function DiagnosticCompositesClient(props: DiagnosticCompositesClientProps) {
  return <DiagnosticCompositesContent {...props} />
}
