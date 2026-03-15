import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import DiagnosticHeader from '@/components/analysis/DiagnosticHeader'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import { DIAGNOSTICS, FLUX_DIAGNOSTICS, DATASET_STATS, DIAGNOSTIC_FIGURE_SLUGS } from '@/lib/constants'
import { readManifest, figureUrl } from '@/lib/utils'
import type { DiagnosticId } from '@/lib/types'
import Image from 'next/image'

interface DiagnosticPageProps {
  params: Promise<{ diagnostic: string }>
}

// --- JSON shapes from step5 + extract_composite_site_data.py ---
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
}

interface FigureEntry {
  exists: boolean
  api_path: string
}

interface FiguresManifest {
  [diagId: string]: {
    real: FigureEntry
    anom?: FigureEntry
  }
}

function safeReadManifest<T>(filename: string, fallback: T): T {
  try {
    return readManifest<T>(filename)
  } catch {
    return fallback
  }
}

export async function generateStaticParams() {
  return Object.values(DIAGNOSTICS).map((d) => ({
    diagnostic: d.slug,
  }))
}

export async function generateMetadata({ params }: DiagnosticPageProps): Promise<Metadata> {
  const { diagnostic: slug } = await params
  const diag = Object.values(DIAGNOSTICS).find((d) => d.slug === slug)
  if (!diag) return { title: 'Not Found' }
  return {
    title: diag.name,
    description: diag.description,
  }
}

export default async function DiagnosticPage({ params }: DiagnosticPageProps) {
  const { diagnostic: slug } = await params
  const diag = Object.values(DIAGNOSTICS).find((d) => d.slug === slug)
  if (!diag) notFound()

  const isFluxDiag = FLUX_DIAGNOSTICS.includes(diag.id)

  // Load manifests (graceful fallback when not yet generated)
  const domainStats = safeReadManifest<DomainStatEntry[]>('composite_domain_stats.json', [])
  const boundaryFluxes = safeReadManifest<BoundaryFluxEntry[]>('composite_boundary_fluxes.json', [])
  const figuresManifest = safeReadManifest<FiguresManifest>('composite_figures_manifest.json', {})

  // Filter for this diagnostic
  const diagStats = domainStats.filter((s) => s.diagnostic_id === diag.id)
  const diagFluxes = boundaryFluxes.filter((f) => f.diagnostic_id === diag.id)
  const figInfo = figuresManifest[diag.id] ?? null

  const ep1Stats = diagStats.find((s) => s.ep === 'EP1')
  const ep2Stats = diagStats.find((s) => s.ep === 'EP2')
  const ep1Fluxes = diagFluxes.find((f) => f.ep === 'EP1')
  const ep2Fluxes = diagFluxes.find((f) => f.ep === 'EP2')

  const realFig = figInfo?.real
  const anomFig = figInfo?.anom
  const figSlug = DIAGNOSTIC_FIGURE_SLUGS[diag.id]

  const hasRealFigure = realFig?.exists ?? false
  const hasAnomFigure = (anomFig?.exists ?? false) && diag.hasAnomaly
  const hasStats = diagStats.length > 0

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <DiagnosticHeader
        name={diag.name}
        shortName={diag.shortName}
        level={diag.level}
        unit={diag.unit}
        description={diag.description}
        hasAnomaly={diag.hasAnomaly}
      />

      <div className="space-y-8">
        {/* Physical Objective */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Physical Objective
          </h2>
          <p className="text-sm leading-relaxed text-slate-600">
            {diag.physicalObjective}
          </p>
        </section>

        {/* Formula */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Formula
          </h2>
          <FormulaBlock
            formula={diag.formula}
            terms={diag.formulaTerms}
            references={diag.references}
            label={`${diag.shortName} — ${diag.level}`}
          />
        </section>

        {/* Composite maps */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Composite Maps — EP1 vs EP2
          </h2>

          {hasRealFigure ? (
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
                <p className="text-xs text-slate-500">
                  Storm-centred {DATASET_STATS.domainSize} composite. Left: EP1. Right: EP2.
                  Source: <code>figures/ep_structure/{figSlug?.real}</code>
                </p>
              </div>
              <div className="p-4">
                <Image
                  src={figureUrl(realFig!.api_path)}
                  alt={`${diag.name} composite — EP1 vs EP2`}
                  width={1200}
                  height={600}
                  className="w-full rounded-lg"
                  unoptimized
                />
              </div>
            </div>
          ) : (
            <ResultSummaryCallout type="info" title="Composite figures not yet generated">
              <p>
                Run <code>scripts/ep_structure_analysis/step4_create_figures.py</code> to generate
                composite figures for {diag.name}. The expected output is{' '}
                <code>figures/ep_structure/{figSlug?.real ?? `composite_${diag.slug}.png`}</code>.
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
                      Source: <code>figures/ep_structure/{figSlug?.anom}</code>
                    </p>
                  </div>
                  <div className="p-4">
                    <Image
                      src={figureUrl(anomFig!.api_path)}
                      alt={`${diag.name} anomaly composite — EP1 vs EP2`}
                      width={1200}
                      height={600}
                      className="w-full rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/50 p-6 text-center">
                  <p className="text-sm font-medium text-amber-600">
                    {diag.shortName} anomaly composite
                  </p>
                  <p className="mt-1 text-xs text-amber-400">
                    Expected: <code>figures/ep_structure/{figSlug?.anom ?? 'composite_*_anom.png'}</code>
                  </p>
                </div>
              )}
            </div>
          )}
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
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/50">
                      <th className="px-4 py-3 text-left font-semibold text-slate-600">Pattern</th>
                      <th className="px-4 py-3 text-right font-semibold text-slate-600">North</th>
                      <th className="px-4 py-3 text-right font-semibold text-slate-600">South</th>
                      <th className="px-4 py-3 text-right font-semibold text-slate-600">East</th>
                      <th className="px-4 py-3 text-right font-semibold text-slate-600">West</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-900">EP1</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep1Fluxes?.north ?? '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep1Fluxes?.south ?? '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep1Fluxes?.east ?? '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep1Fluxes?.west ?? '—'}</td>
                    </tr>
                    <tr className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-900">EP2</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep2Fluxes?.north ?? '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep2Fluxes?.south ?? '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep2Fluxes?.east ?? '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-700">{ep2Fluxes?.west ?? '—'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="border-t border-slate-100 px-4 py-2">
                <p className="text-xs text-slate-400">
                  Mean {diag.shortName} along each edge of the {DATASET_STATS.innerDomainSize} inner domain (±7.5°).
                  Source: <code>step5_update_scientific_notes.py</code> → <code>results/ep_structure/composite_stats.json</code>.
                </p>
              </div>
            </div>
          </section>
        )}

        <FileProvenanceBadge
          files={[
            'data/era5_ep_structure/precomputed_composites_ep1.nc',
            'data/era5_ep_structure/precomputed_composites_ep2.nc',
            'scripts/ep_structure_analysis/step4_create_figures.py',
            'scripts/ep_structure_analysis/step5_update_scientific_notes.py',
            'results/ep_structure/composite_stats.json',
          ]}
          label="Source files"
        />
      </div>
    </div>
  )
}

