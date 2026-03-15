import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import { DATASET_STATS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'About',
  description: 'Project context, data provenance, and repository information.',
}

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="About This Project"
        badge="Context"
        description="This interactive site accompanies the paper on energetic patterns of extratropical cyclones in the Southwestern Atlantic. It is based on Chapter 6 of a PhD thesis and provides a navigable, visual exploration of the results."
      />

      <div className="space-y-8">
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Research Context
          </h2>
          <div className="prose prose-sm prose-slate max-w-none">
            <p>
              Extratropical cyclones are key elements of midlatitude weather and climate.
              In the South Atlantic, these systems exhibit a wide range of energetic
              behaviours during their lifecycle, from weak transient disturbances to
              intense storms with large barotropic and baroclinic energy conversions.
            </p>
            <p>
              This project uses the <strong>Lorenz Energy Cycle</strong> framework to
              quantify the energetics of {DATASET_STATS.totalCyclones.toLocaleString()}{' '}
              cyclones tracked over {DATASET_STATS.years} years ({DATASET_STATS.period}).
              Seven energy terms—conversions (C<sub>a</sub>, C<sub>k</sub>), generation
              (G<sub>e</sub>), boundary fluxes (∂A<sub>e</sub>, ∂K<sub>e</sub>), and
              reservoirs (A<sub>e</sub>, K<sub>e</sub>)—are computed in a semi-Lagrangian
              framework following each cyclone.
            </p>
            <p>
              PCA-based K-Means clustering identifies three distinct <strong>Energy
              Patterns</strong>. Subsequent ERA5 composite analysis reveals the atmospheric
              structure differences between EP1 (strong conversions) and EP2 (intermediate)
              cyclones during intensification.
            </p>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Repository
          </h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">
            <p>
              <strong>GitHub:</strong>{' '}
              <a
                href="https://github.com/daniloceano/paper_energy_patterns"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline"
              >
                daniloceano/paper_energy_patterns
              </a>
            </p>
            <p className="mt-2">
              The repository contains all scripts, data references, results, and
              documentation. This web layer is a subproject inside <code>web/</code> that
              reads from the existing scientific outputs without modifying them.
            </p>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Architecture
          </h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">
            <ul className="space-y-2">
              <li><code>scripts/</code> — Scientific analysis pipelines (Python)</li>
              <li><code>data/</code> — Input data and ERA5 composites</li>
              <li><code>results/</code> — Analysis outputs (CSV, pickle)</li>
              <li><code>figures/</code> — Generated figures (PNG)</li>
              <li><code>docs/</code> — PDF documentation</li>
              <li><code>web/</code> — This Next.js application</li>
              <li><code>supabase/</code> — Database migrations</li>
              <li><code>scripts/web/</code> — Data extraction for the site</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  )
}
