import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import StatsTable from '@/components/analysis/StatsTable'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import { DATASET_STATS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Step 1 — Case Selection & Features',
}

export default function Step1Page() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Case Selection, Pre-processing & Features"
        subtitle="Step 1 of 5"
        badge="Cluster Analysis"
        description="Filter cyclones for complete lifecycle phases, standardise 7 Lorenz Energy Cycle terms, and prepare the feature matrix for PCA dimensionality reduction."
      />

      <div className="space-y-8">
        {/* Data source */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Data Source</h2>
          <p className="text-sm leading-relaxed text-slate-600">
            Cyclone tracks and semi-Lagrangian LEC diagnostics from{' '}
            <a
              href="https://doi.org/10.5281/zenodo.18133432"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:underline"
            >
              Zenodo (DOI: 10.5281/zenodo.18133432)
            </a>
            . The dataset spans {DATASET_STATS.period} ({DATASET_STATS.years} years) with{' '}
            {DATASET_STATS.totalCyclones.toLocaleString()} cyclones in the South Atlantic domain.
          </p>
        </section>

        {/* Filtering criteria */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Filtering Criteria
          </h2>
          <MethodologyAccordion
            items={[
              {
                title: 'Complete lifecycle requirement',
                content:
                  'Only cyclones with all 4 lifecycle phases (incipient, intensification, mature, decay) and valid energy data are retained. This ensures a consistent feature vector for each cyclone across all phases.',
              },
              {
                title: 'Energy data availability',
                content:
                  'Each cyclone must have valid LEC diagnostics (Ca, Ck, Ge, BAe, BKe, Ae, Ke) for all 4 lifecycle phases. Missing or incomplete energy records lead to exclusion.',
              },
              {
                title: 'Result of filtering',
                content: `From ${DATASET_STATS.totalCyclones.toLocaleString()} original cyclones, ${DATASET_STATS.filteredCyclones.toLocaleString()} (${DATASET_STATS.filterPercentage}%) pass the filter, producing ${DATASET_STATS.phaseRecords.toLocaleString()} phase records (${DATASET_STATS.filteredCyclones.toLocaleString()} × 4 phases).`,
              },
            ]}
          />
        </section>

        {/* Features */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Energy Features (7 Terms)
          </h2>
          <StatsTable
            columns={[
              { key: 'symbol', label: 'Symbol' },
              { key: 'name', label: 'Name' },
              { key: 'type', label: 'Type' },
              { key: 'unit', label: 'Unit' },
            ]}
            rows={[
              { symbol: 'Ca', name: 'Baroclinic Conversion', type: 'Conversion', unit: 'W m⁻²' },
              { symbol: 'Ck', name: 'Barotropic Conversion', type: 'Conversion', unit: 'W m⁻²' },
              { symbol: 'Ge', name: 'Eddy APE Generation', type: 'Generation', unit: 'W m⁻²' },
              { symbol: 'BAe', name: 'Eddy APE Boundary Flux', type: 'Flux', unit: 'W m⁻²' },
              { symbol: 'BKe', name: 'Eddy KE Boundary Flux', type: 'Flux', unit: 'W m⁻²' },
              { symbol: 'Ae', name: 'Eddy APE Reservoir', type: 'Reservoir', unit: 'J m⁻²' },
              { symbol: 'Ke', name: 'Eddy KE Reservoir', type: 'Reservoir', unit: 'J m⁻²' },
            ]}
            caption="All terms are standardised (μ=0, σ=1) before PCA."
          />
        </section>

        {/* Summary */}
        <ResultSummaryCallout type="result" title="Step 1 Result">
          <p>
            {DATASET_STATS.filteredCyclones.toLocaleString()} cyclones retained with
            complete lifecycle data. Feature matrix: {DATASET_STATS.phaseRecords.toLocaleString()}{' '}
            rows × 7 standardised energy columns, ready for phase-separated PCA.
          </p>
        </ResultSummaryCallout>

        {/* Provenance */}
        <FileProvenanceBadge
          files={[
            'scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py',
            'data/tracks_SAt_filtered_with_energetics_processed.csv',
            'data/energy_cache.parquet',
          ]}
          label="Input / Script"
        />
        <FileProvenanceBadge
          files={[
            'results/cluster/pca_full_data.csv',
            'results/cluster/pca_full_data_{phase}.csv',
          ]}
          label="Outputs"
        />
      </div>
    </div>
  )
}
