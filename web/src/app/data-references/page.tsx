import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight, Database, FileCheck2 } from 'lucide-react'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ReferenceList from '@/components/analysis/ReferenceList'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import StatsTable from '@/components/analysis/StatsTable'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import { DATASET_STATS, KEY_REFERENCES } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Data & References',
  description:
    'Dataset inventory, provenance, DOI records, and bibliography for the Energy Patterns analyses.',
}

const DATA_SOURCES = [
  {
    title: 'Cyclone tracks and archived energetics',
    description:
      'Cyclone tracks and semi-Lagrangian Lorenz Energy Cycle diagnostics for the South Atlantic study population.',
    href: 'https://doi.org/10.5281/zenodo.18133432',
    label: 'DOI: 10.5281/zenodo.18133432',
    status: 'Primary archived source',
  },
  {
    title: 'ERA5 reanalysis',
    description:
      `Atmospheric source fields for the energy diagnostics, storm-centred composites, pressure diagnostics, and phase-space analyses at ${DATASET_STATS.era5Resolution} horizontal resolution.`,
    href: 'https://doi.org/10.1002/qj.3803',
    label: 'DOI: 10.1002/qj.3803',
    status: 'Primary reanalysis source',
  },
  {
    title: 'Archived LEC vertical-resolution collection',
    description:
      'Earlier vertical-resolution archive retained for provenance. Current full-population vertical and Ck results on this site come from the corrected rerun products, not from this partial archive.',
    href: 'https://doi.org/10.5281/zenodo.18243447',
    label: 'DOI: 10.5281/zenodo.18243447',
    status: 'Reference archive — superseded for current results',
  },
] as const

export default function DataReferencesPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Data & References"
        badge="Provenance & Bibliography"
        description="Data inventory, sample sizes, provenance, DOI records, and the bibliography shared across the project. Scientific procedures and equations are maintained separately on the Methodology page."
      />

      <div className="space-y-10">
        <ResultSummaryCallout type="info" title="Methodology is documented separately">
          <p>
            Lifecycle processing, the corrected Lorenz Energy Cycle equations, feature
            construction, and numerical conventions now live in{' '}
            <Link href="/methodology" className="font-medium text-indigo-600 hover:underline">
              Methodology
            </Link>
            . Methods and statistical choices unique to one result remain on its analysis page.
          </p>
        </ResultSummaryCallout>

        <section>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-indigo-600" />
            <h2 className="text-xl font-bold text-slate-900">Dataset inventory</h2>
          </div>
          <div className="mt-4">
            <StatsTable
              columns={[
                { key: 'property', label: 'Property' },
                { key: 'value', label: 'Value' },
              ]}
              rows={[
                { property: 'Track catalogue period', value: DATASET_STATS.period },
                { property: 'Duration', value: `${DATASET_STATS.years} years` },
                { property: 'Cyclones in the three genesis regions', value: DATASET_STATS.totalCyclones.toLocaleString() },
                { property: 'Complete standard lifecycle', value: `${DATASET_STATS.filteredCyclones.toLocaleString()} (${DATASET_STATS.filterPercentage}%)` },
                { property: 'Track temporal resolution', value: '1-hourly' },
                { property: 'Energy temporal resolution', value: '3-hourly' },
                { property: 'ERA5 horizontal resolution', value: DATASET_STATS.era5Resolution },
                { property: 'LEC storm-centred domain', value: DATASET_STATS.innerDomainSize },
                { property: 'Composite analysis domain', value: DATASET_STATS.domainSize },
                { property: 'WMO climatology baseline', value: DATASET_STATS.climatologyPeriod },
              ]}
            />
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900">Analysis populations</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Different analyses use different scientifically defined subsets. These counts are
            listed here as data inventory; the selection rules are explained in Methodology or
            beside the corresponding results.
          </p>
          <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Population</th>
                  <th className="px-4 py-3">N</th>
                  <th className="px-4 py-3">Used by</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {[
                  ['Regional track catalogue', '6,789', 'Study source population'],
                  ['Complete four-phase lifecycle', '3,820', 'LEC clustering, vertical structure, Ck subterms'],
                  ['Intensification ≥ 24 h', '2,733', 'ERA5 composites and LEC–field dependence'],
                  ['CPS records available', '6,776', 'Cyclone Phase Space'],
                ].map(([population, count, use]) => (
                  <tr key={population}>
                    <td className="px-4 py-3 font-medium text-slate-900">{population}</td>
                    <td className="px-4 py-3 tabular-nums">{count}</td>
                    <td className="px-4 py-3">{use}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900">Data sources and provenance</h2>
          <div className="mt-4 space-y-3">
            {DATA_SOURCES.map((source) => (
              <div key={source.href} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900">{source.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{source.description}</p>
                  </div>
                  <span className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                    {source.status}
                  </span>
                </div>
                <a
                  href={source.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:underline"
                >
                  {source.label}
                  <ArrowRight className="h-3.5 w-3.5" />
                </a>
              </div>
            ))}

            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
              <div className="flex items-center gap-2">
                <FileCheck2 className="h-4 w-4 text-emerald-700" />
                <h3 className="font-semibold text-emerald-900">Corrected full-population LEC products</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Current clustering, vertical-structure, and Ck-subterm results use the corrected
                rerun cache and its frozen phase windows. Each published analysis records its
                exact source product and validation checks beside the result.
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">References</h2>
          <ReferenceList references={KEY_REFERENCES} title="Key References" />
        </section>
      </div>
    </div>
  )
}
