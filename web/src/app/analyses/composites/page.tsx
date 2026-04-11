import type { Metadata } from 'next'
import { Layers } from 'lucide-react'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { DIAGNOSTIC_LIST, DATASET_STATS, ENERGY_PATTERNS } from '@/lib/constants'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Composite Analysis',
  description: 'ERA5 composite analysis of EP1, EP2, EP3, and EPALL atmospheric structure.',
}

export default function CompositesPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Composite Analysis"
        subtitle="EP Structure — ERA5 Reanalysis"
        badge="EP1 / EP2 / EP3 / EPALL"
        description={`Storm-centred ${DATASET_STATS.domainSize} composites of 10 diagnostic fields at key atmospheric levels, computed from ERA5 reanalysis at ${DATASET_STATS.era5Resolution} resolution. EP1 (N=${ENERGY_PATTERNS.EP1.count}), EP2 (N=${ENERGY_PATTERNS.EP2.count}), and EP3 (N=${ENERGY_PATTERNS.EP3.count}) composites are compared during the intensification phase alongside EPALL (all cyclones combined). EPALL-relative anomalies (EPx − EPALL) isolate what distinguishes each pattern from the climatological cyclone population.`}
      />

      <div className="space-y-8">
        <ResultSummaryCallout type="info" title="Scientific Objective">
          <p>
            Understand the atmospheric structure and dynamical characteristics that distinguish
            high-energy (EP1), moderate-energy (EP2), and weak-energy (EP3) cyclones from each
            other and from the full population (EPALL). This analysis reveals how differences in
            energy conversions relate to distinct patterns of baroclinic instability, upper-level
            forcing, moisture supply, and jet-stream interaction.
          </p>
        </ResultSummaryCallout>

        <ResultSummaryCallout type="info" title="Composite Methods">
          <p>
            Composites are centred on the intensification midpoint of each cyclone
            (typically 2–3 timesteps per case), isolating the most active moment of deepening.
          </p>
          <p className="mt-2">
            Each diagnostic page shows two figure panels:
          </p>
          <ul className="mt-2 list-inside list-disc text-sm">
            <li>
              <strong>Total field (2×2 panel):</strong> EP1 / EP2 / EP3 / EPALL composites side-by-side
            </li>
            <li>
              <strong>EPALL-relative anomaly (1×3 panel):</strong> EP1 − EPALL | EP2 − EPALL | EP3 − EPALL,
              isolating what distinguishes each pattern from the full cyclone population
              (available for most diagnostics)
            </li>
          </ul>
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
            <code>data/era5_ep_structure/precomputed_composites_ep1.nc</code>,{' '}
            <code>precomputed_composites_ep2.nc</code>,{' '}
            <code>precomputed_composites_ep3.nc</code>, and{' '}
            <code>precomputed_composites_epall.nc</code> (Xarray/NetCDF4 format). EPALL-relative
            anomaly variables (e.g. <code>egr_minus_epall</code>) are stored inside EP1/EP2/EP3
            files. Figures are generated by{' '}
            <code>scripts/ep_structure_analysis/step4_create_figures.py</code>.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
