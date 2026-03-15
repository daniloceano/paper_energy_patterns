import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import DiagnosticHeader from '@/components/analysis/DiagnosticHeader'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import { DIAGNOSTICS, FLUX_DIAGNOSTICS, DATASET_STATS } from '@/lib/constants'
import type { DiagnosticId } from '@/lib/types'

interface DiagnosticPageProps {
  params: Promise<{ diagnostic: string }>
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

        {/* Composite figures placeholder */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Composite Maps — EP1 vs EP2
          </h2>
          <ResultSummaryCallout type="info" title="Composite Visualisation">
            <p>
              Composite figures for {diag.name} are generated from{' '}
              <code>data/era5_ep_structure/precomputed_composites_ep*.nc</code> via{' '}
              <code>scripts/ep_structure_analysis/step4_create_figures.py</code>.
              The figures show storm-centred {DATASET_STATS.domainSize} composites for
              EP1 (N={DATASET_STATS.filteredCyclones > 0 ? '444' : '—'}) and EP2 (N=979)
              during the intensification phase.
            </p>
          </ResultSummaryCallout>

          <div className="mt-4 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <p className="text-sm font-medium text-slate-500">
              Composite figure for {diag.shortName}
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Run <code>scripts/web/extract_composite_site_data.py</code> to generate
              figure assets, then reference them here.
            </p>
          </div>

          {diag.hasAnomaly && (
            <div className="mt-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-700">
                Anomaly Composite
              </h3>
              <div className="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/50 p-8 text-center">
                <p className="text-sm font-medium text-amber-600">
                  {diag.shortName} anomaly composite (relative to {DATASET_STATS.climatologyPeriod} climatology)
                </p>
                <p className="mt-1 text-xs text-amber-400">
                  Available once composite figures are extracted.
                </p>
              </div>
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
                    <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-medium text-slate-900">EP2</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="border-t border-slate-100 px-4 py-2">
              <p className="text-xs text-slate-400">
                Populate by running <code>scripts/web/extract_composite_site_data.py</code>.
                &ldquo;Inside&rdquo; = mean within the central {DATASET_STATS.innerDomainSize} subdomain.
                &ldquo;Outside&rdquo; = mean in the annular ring between {DATASET_STATS.domainSize} and {DATASET_STATS.innerDomainSize}.
              </p>
            </div>
          </div>
        </section>

        {/* Boundary flux table for flux diagnostics */}
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
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                    </tr>
                    <tr className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-900">EP2</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-500">—</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="border-t border-slate-100 px-4 py-2">
                <p className="text-xs text-slate-400">
                  Each boundary value is the spatial mean of {diag.shortName} along the
                  corresponding edge of the {DATASET_STATS.innerDomainSize} inner domain.
                  Positive = outward flux; Negative = inward flux.
                  Populate by running <code>scripts/web/extract_composite_site_data.py</code>.
                </p>
              </div>
            </div>
          </section>
        )}

        <FileProvenanceBadge
          files={[
            'data/era5_ep_structure/precomputed_composites_ep1.nc',
            'data/era5_ep_structure/precomputed_composites_ep2.nc',
            'scripts/ep_structure_analysis/step3_precompute_composites.py',
            'scripts/ep_structure_analysis/step4_create_figures.py',
          ]}
          label="Source files"
        />
      </div>
    </div>
  )
}
