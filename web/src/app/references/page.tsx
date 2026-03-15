import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ReferenceList from '@/components/analysis/ReferenceList'
import { KEY_REFERENCES } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'References',
  description: 'Key bibliographic references and data sources.',
}

export default function ReferencesPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="References"
        badge="Bibliography"
        description="Key bibliographic references used in the energy pattern classification and composite structure analysis."
      />

      <div className="space-y-8">
        <ReferenceList
          references={KEY_REFERENCES}
          title="Key References"
        />

        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Data Sources
          </h2>
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Cyclone Tracks and Energetics
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Combined cyclone tracks and semi-Lagrangian Lorenz Energy Cycle diagnostics
                (1979–2020, ~6,700 cyclones, 42 years).
              </p>
              <a
                href="https://doi.org/10.5281/zenodo.18133432"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
              >
                DOI: 10.5281/zenodo.18133432
              </a>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                LEC Results with Vertical Resolution
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Complete LEC results with vertical resolution (~1,500 cyclones, 32 pressure
                levels, 3-hourly).
              </p>
              <a
                href="https://doi.org/10.5281/zenodo.18243447"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
              >
                DOI: 10.5281/zenodo.18243447
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
