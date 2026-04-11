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
    anom_clim?: FigureEntry
    anom_epall?: FigureEntry
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
  figSlug: { real: string; anom_clim?: string; anom_epall?: string; diff?: string }
  isFluxDiag: boolean
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
  const ep3Stats = diagStats.find((s) => s.ep === 'EP3')
  const epallStats = diagStats.find((s) => s.ep === 'EPALL')
  const ep1Fluxes = diagFluxes.find((f) => f.ep === 'EP1')
  const ep2Fluxes = diagFluxes.find((f) => f.ep === 'EP2')
  const ep3Fluxes = diagFluxes.find((f) => f.ep === 'EP3')
  const epallFluxes = diagFluxes.find((f) => f.ep === 'EPALL')

  const realFig = figInfo?.real
  const anomClimFig = figInfo?.anom_clim
  const anomEpallFig = figInfo?.anom_epall
  const diffFig = figInfo?.diff
  const hasRealFigure = realFig?.exists ?? false
  const hasClimAnomFigure = anomClimFig?.exists ?? false
  const hasAnomFigure = (anomEpallFig?.exists ?? false) && diag.hasAnomaly
  const hasDiffFigure = diffFig?.exists ?? false
  const hasStats = diagStats.length > 0

  const realFigFilename = figSlug.real
  const anomClimFigFilename = figSlug.anom_clim
  const anomEpallFigFilename = figSlug.anom_epall
  const diffFigFilename = figSlug.diff

  return (
    <div className="space-y-8">
      {/* Mode Switcher */}

      {/* Composite maps */}
      <section>
        <h2 className="mb-3 text-lg font-bold text-slate-900">
          Composite Maps — EP1 / EP2 / EP3 / EPALL
        </h2>

        {/* Figure 1: Total field */}
        {hasRealFigure ? (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
              <p className="text-xs font-medium text-slate-600">
                Total field — EP1 | EP2 | EP3 | EPALL
              </p>
              <p className="mt-0.5 text-xs text-slate-500">
                Storm-centred {DATASET_STATS.domainSize} composites at the intensification
                midpoint (2–3 timesteps per case). 2×2 panel: EP1 (top-left), EP2 (top-right),
                EP3 (bottom-left), EPALL (bottom-right).
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Source: <code>figures/ep_structure/{realFigFilename}</code>
              </p>
            </div>
            <div className="p-4">
              <FallbackImage
                src={figureUrl(realFig!.api_path)}
                alt={`${diag.name} composite — EP1 / EP2 / EP3 / EPALL`}
                width={1200}
                height={1200}
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

        {/* Figure 2: Climatology-relative anomaly */}
        {(hasClimAnomFigure || anomClimFigFilename) && (
          <div className="mt-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-700">
              Climatology-Relative Anomaly
              <span className="ml-2 text-xs font-normal text-slate-400">
                X&prime; = X − X̄<sub>clim</sub> &nbsp;·&nbsp; 1991–2020 ERA5 monthly climatology
              </span>
            </h3>
            {hasClimAnomFigure ? (
              <div className="overflow-hidden rounded-xl border border-sky-200 bg-white">
                <div className="border-b border-sky-100 bg-sky-50 px-4 py-3">
                  <p className="text-xs text-sky-800">
                    <strong>Reference: 1991–2020 ERA5 monthly climatology.</strong>{' '}
                    Removes the seasonal mean state; isolates the cyclone&apos;s synoptic-scale
                    eddy signal. Positive values = above climatological background; negative
                    values = below. Wind vectors show eddy component (u&prime;, v&prime;).
                  </p>
                  <p className="mt-1 text-xs text-sky-500">
                    Source: <code>figures/ep_structure/{anomClimFigFilename}</code>
                  </p>
                </div>
                <div className="p-4">
                  <FallbackImage
                    src={figureUrl(anomClimFig!.api_path)}
                    alt={`${diag.name} climatology-relative anomaly — EP1 / EP2 / EP3 / EPALL`}
                    width={1200}
                    height={500}
                    className="w-full rounded-lg"
                    key={anomClimFig!.api_path}
                  />
                </div>
              </div>
            ) : (
              <div className="rounded-xl border-2 border-dashed border-sky-300 bg-sky-50/50 p-6 text-center">
                <p className="text-sm font-medium text-sky-600">
                  {diag.shortName} climatology-relative anomaly
                </p>
                <p className="mt-1 text-xs text-sky-400">
                  Expected: <code>figures/ep_structure/{anomClimFigFilename ?? 'composite_*_anom.png'}</code>
                </p>
              </div>
            )}
          </div>
        )}

        {/* Figure 3: EPALL-relative anomaly */}
        {diag.hasAnomaly && (
          <div className="mt-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-700">
              EPALL-Relative Anomaly
              <span className="ml-2 text-xs font-normal text-slate-400">
                EPx − EPALL &nbsp;·&nbsp; reference = all 2730 intensifying cyclones
              </span>
            </h3>
            {hasAnomFigure ? (
              <div className="overflow-hidden rounded-xl border border-amber-200 bg-white">
                <div className="border-b border-amber-100 bg-amber-50 px-4 py-3">
                  <p className="text-xs text-amber-700">
                    <strong>Reference: EPALL composite</strong> (all intensifying cyclones).
                    Positive = EPx exceeds the typical intensifying cyclone; negative = weaker
                    than typical. EPALL column omitted (identically zero by construction).{' '}
                    <strong>1×3 panel:</strong> EP1 − EPALL | EP2 − EPALL | EP3 − EPALL.
                    Diverging colormap centred at zero; shared scale across all three panels.
                  </p>
                  <p className="mt-1 text-xs text-amber-500">
                    Source: <code>figures/ep_structure/{anomEpallFigFilename}</code>
                  </p>
                </div>
                <div className="p-4">
                  <FallbackImage
                    src={figureUrl(anomEpallFig!.api_path)}
                    alt={`${diag.name} EPALL-relative anomaly — EP1−EPALL / EP2−EPALL / EP3−EPALL`}
                    width={1200}
                    height={500}
                    className="w-full rounded-lg"
                    key={anomEpallFig!.api_path}
                  />
                </div>
              </div>
            ) : (
              <div className="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/50 p-6 text-center">
                <p className="text-sm font-medium text-amber-600">
                  {diag.shortName} EPALL-relative anomaly
                </p>
                <p className="mt-1 text-xs text-amber-400">
                  Expected: <code>figures/ep_structure/{anomEpallFigFilename ?? 'composite_*_anom_epall.png'}</code>
                </p>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Domain statistics */}
      <section>
        <h2 className="mb-3 text-lg font-bold text-slate-900">
          Domain Statistics — Total Field
        </h2>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
            <h4 className="text-sm font-semibold text-slate-700">
              Mean composite values inside/outside {DATASET_STATS.innerDomainSize} domain [{diag.unit}]
            </h4>
            <p className="mt-0.5 text-xs text-slate-400">
              Total field · intensification midpoint · central-timestep composites
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
                <tr className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-medium text-slate-900">EP3</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {ep3Stats?.inside_15x15 ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {ep3Stats?.outside_15x15 ?? '—'}
                  </td>
                </tr>
                <tr className="hover:bg-slate-50/50 bg-slate-50/30">
                  <td className="px-4 py-3 font-medium text-slate-500 italic">EPALL</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-500">
                    {epallStats?.inside_15x15 ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-500">
                    {epallStats?.outside_15x15 ?? '—'}
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
                Mean flux along each boundary of the {DATASET_STATS.innerDomainSize} domain [{diag.unit}]
              </h4>
              <p className="mt-0.5 text-xs text-slate-400">
                Total field + climatology-relative anomaly (X&prime; = X − X̄<sub>clim</sub>, 1991–2020) · central-timestep composites
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
                      <th key={`a${i}`} className="px-3 py-1 text-right text-xs font-medium text-sky-500">clim. anom&prime;</th>,
                    ])}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {([
                    ['EP1', ep1Fluxes, false],
                    ['EP2', ep2Fluxes, false],
                    ['EP3', ep3Fluxes, false],
                    ['EPALL', epallFluxes, true],
                  ] as [string, typeof ep1Fluxes, boolean][]).map(([label, f, isAll]) => (
                    <tr key={label} className={`hover:bg-slate-50/50${isAll ? ' bg-slate-50/30' : ''}`}>
                      <td className={`px-4 py-3 font-medium ${isAll ? 'text-slate-500 italic' : 'text-slate-900'}`}>{label}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.north ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-sky-600">{f?.north_anom ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.south ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-sky-600">{f?.south_anom ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.east ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-sky-600">{f?.east_anom ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-700">{f?.west ?? '—'}</td>
                      <td className="px-3 py-3 text-right tabular-nums text-sky-600">{f?.west_anom ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-slate-100 px-4 py-2">
              <p className="text-xs text-slate-400">
                Mean {diag.shortName} along each edge of the {DATASET_STATS.innerDomainSize} inner domain (±7.5°).
                EPALL = all-cyclone composite (reference population).{' '}
                <span className="font-medium text-sky-500">clim. anom&prime;</span>
                {' '}= X&prime; = X − X̄<sub>clim</sub>, departure from the ERA5 {DATASET_STATS.climatologyPeriod} monthly climatology (where available).
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
