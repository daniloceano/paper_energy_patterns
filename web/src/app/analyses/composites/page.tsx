import type { Metadata } from 'next'
import { Layers } from 'lucide-react'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { DIAGNOSTIC_LIST, DATASET_STATS, ENERGY_PATTERNS } from '@/lib/constants'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Composite Analysis',
  description: 'ERA5 composite analysis comparing EP1 vs EP2 atmospheric structure.',
}

export default function CompositesPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Composite Analysis"
        subtitle="EP Structure — ERA5 Reanalysis"
        badge="EP1 vs EP2"
        description={`Storm-centred ${DATASET_STATS.domainSize} composites of 9 diagnostic fields at key atmospheric levels, computed from ERA5 reanalysis at ${DATASET_STATS.era5Resolution} resolution. EP1 (N=${ENERGY_PATTERNS.EP1.count}) and EP2 (N=${ENERGY_PATTERNS.EP2.count}) composites are compared during the intensification phase. Anomalies are computed relative to the ${DATASET_STATS.climatologyPeriod} WMO monthly climatology.`}
      />

      <div className="space-y-8">
        <ResultSummaryCallout type="info" title="Scientific Objective">
          <p>
            Understand the atmospheric structure and dynamical characteristics that distinguish
            high-energy (EP1) from moderate-energy (EP2) cyclones. This analysis reveals how
            differences in energy conversions relate to distinct patterns of baroclinic instability,
            upper-level forcing, moisture supply, and jet-stream interaction.
          </p>
        </ResultSummaryCallout>

        <ResultSummaryCallout type="info" title="Composite Methods">
          <p>
            Each diagnostic page offers three composite methods:
          </p>
          <ul className="mt-2 list-inside list-disc text-sm">
            <li>
              <strong>Full Intensification:</strong> mean over all 6-hourly timesteps during the intensification phase
            </li>
            <li>
              <strong>Central Time:</strong> single timestep at the temporal midpoint of the intensification phase
            </li>
            <li>
              <strong>10 Most Intense:</strong> composites from the 10 most intense cyclones of each pattern (based on peak relative vorticity)
            </li>
          </ul>
          <p className="mt-2">
            Use the toggle on each diagnostic page to switch between methods and compare results.
            Each page also shows an <strong>EP1 − EP2 difference map</strong> using diverging colormaps
            to highlight where the two patterns differ most strongly.
          </p>
        </ResultSummaryCallout>

        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Domain Definition
          </h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600">
            <ul className="space-y-2">
              <li>
                <strong>Full domain:</strong> {DATASET_STATS.domainSize} storm-centred at{' '}
                {DATASET_STATS.era5Resolution} resolution (120 × 120 grid points)
              </li>
              <li>
                <strong>Inner domain ({DATASET_STATS.innerDomainSize}):</strong> The central{' '}
                {DATASET_STATS.innerDomainSize} subdomain centred on the cyclone. Used for
                &ldquo;inside&rdquo; domain statistics.
              </li>
              <li>
                <strong>Outer ring:</strong> The area between the full {DATASET_STATS.domainSize}{' '}
                domain and the inner {DATASET_STATS.innerDomainSize}. Used for &ldquo;outside&rdquo;
                domain statistics.
              </li>
              <li>
                <strong>Boundaries (N/S/E/W):</strong> The four edges of the inner{' '}
                {DATASET_STATS.innerDomainSize} domain. For flux/advection diagnostics, each
                boundary value represents the mean along that edge.
              </li>
            </ul>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Available Diagnostics
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {DIAGNOSTIC_LIST.map((diag) => (
              <Link
                key={diag.id}
                href={`/analyses/composites/${diag.slug}`}
                className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 transition-colors group-hover:bg-indigo-600 group-hover:text-white">
                    <Layers className="h-4 w-4" />
                  </div>
                  <div className="flex gap-1.5">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                      {diag.level}
                    </span>
                    {diag.hasAnomaly && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-600">
                        +anom
                      </span>
                    )}
                  </div>
                </div>
                <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600">
                  {diag.name}
                </h3>
                <p className="mt-1 text-xs text-slate-500">{diag.shortName} [{diag.unit}]</p>
              </Link>
            ))}
          </div>
        </section>

        <ResultSummaryCallout type="info" title="Data Source">
          <p>
            All composites are pre-computed and stored in{' '}
            <code>data/era5_ep_structure/precomputed_composites_ep1.nc</code> and{' '}
            <code>precomputed_composites_ep2.nc</code> (Xarray/NetCDF4 format). Figures are
            generated by <code>scripts/ep_structure_analysis/step4_create_figures.py</code>.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
