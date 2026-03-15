import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import { ENERGY_TERM_INFO, DATASET_STATS } from '@/lib/constants'
import type { EnergyTerm } from '@/lib/types'

export const metadata: Metadata = {
  title: 'Methods',
  description: 'Methodology, energy terms, and data description.',
}

export default function MethodsPage() {
  const termEntries = Object.entries(ENERGY_TERM_INFO) as [EnergyTerm, typeof ENERGY_TERM_INFO[EnergyTerm]][]

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Data & Methods"
        badge="Methodology"
        description="Description of the dataset, energy terms from the Lorenz Energy Cycle, and the methodological pipeline used to classify cyclones into Energy Patterns and analyse their atmospheric structure."
      />

      <div className="space-y-10">
        {/* Dataset */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">Dataset</h2>
          <StatsTable
            columns={[
              { key: 'property', label: 'Property' },
              { key: 'value', label: 'Value' },
            ]}
            rows={[
              { property: 'Source', value: 'Zenodo DOI: 10.5281/zenodo.18133432' },
              { property: 'Period', value: DATASET_STATS.period },
              { property: 'Duration', value: `${DATASET_STATS.years} years` },
              { property: 'Total cyclones', value: DATASET_STATS.totalCyclones.toLocaleString() },
              { property: 'Filtered (complete lifecycle)', value: `${DATASET_STATS.filteredCyclones.toLocaleString()} (${DATASET_STATS.filterPercentage}%)` },
              { property: 'Track temporal resolution', value: '1-hourly' },
              { property: 'Energy temporal resolution', value: '3-hourly' },
              { property: 'ERA5 spatial resolution', value: DATASET_STATS.era5Resolution },
              { property: 'Storm-centred domain', value: DATASET_STATS.domainSize },
              { property: 'Climatology baseline', value: `${DATASET_STATS.climatologyPeriod} (WMO)` },
            ]}
          />
        </section>

        {/* Energy terms */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Lorenz Energy Cycle Terms
          </h2>
          <p className="mb-6 text-sm text-slate-600">
            Seven terms from the semi-Lagrangian Lorenz Energy Cycle are used as features
            for clustering. Each term is computed for the storm-centred domain at each
            timestep and averaged per lifecycle phase.
          </p>

          <div className="space-y-4">
            {termEntries.map(([key, info]) => (
              <div
                key={key}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">
                    {key}
                  </span>
                  <h3 className="font-semibold text-slate-900">{info.name}</h3>
                  <span className="text-xs text-slate-400">[{info.unit}]</span>
                </div>
                <p className="mt-2 text-sm text-slate-600">{info.description}</p>
                {info.formula && (
                  <div className="mt-3">
                    <FormulaBlock formula={info.formula} label={`${key} formula`} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Methodology */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Methodology
          </h2>
          <MethodologyAccordion
            items={[
              {
                title: 'Step 1: Data filtering and standardisation',
                content:
                  'Cyclones with incomplete lifecycle phases are removed. The 7 energy terms are standardised (μ=0, σ=1) independently for each phase.',
              },
              {
                title: 'Step 2: Phase-separated PCA',
                content:
                  'Independent PCA is applied per lifecycle phase (incipient, intensification, mature, decay), retaining ≥97% variance. Typically 6 out of 7 PCs are kept.',
              },
              {
                title: 'Step 3: Optimal k determination',
                content:
                  '5 cluster validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, Gap Statistic) are computed for k=3–15 and normalised. Ensemble averaging identifies k=3.',
              },
              {
                title: 'Step 4: K-Means clustering',
                content:
                  "K-Means (k=3, n_init=100, random_state=42) with K-Means++ initialisation is applied per phase. Clusters are labelled EP1, EP2, EP3 by Ck magnitude.",
              },
              {
                title: 'Step 5: ERA5 composite analysis',
                content:
                  'Storm-centred 30°×30° composites of 9 diagnostic fields are computed for EP1 and EP2 during intensification. Anomalies use 1991–2020 WMO monthly climatology.',
              },
              {
                title: 'Grid calculations',
                content:
                  'Spherical geometry: dy = R_⊕ × Δφ, dx = R_⊕ × cos(φ) × Δλ, where R_⊕ = 6.371 × 10⁶ m. All spatial derivatives use centred differences.',
              },
            ]}
          />
        </section>
      </div>
    </div>
  )
}
