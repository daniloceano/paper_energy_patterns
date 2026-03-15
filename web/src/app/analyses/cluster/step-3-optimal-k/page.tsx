import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import StatsTable from '@/components/analysis/StatsTable'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'

export const metadata: Metadata = {
  title: 'Step 3 — Optimal k',
}

export default function Step3Page() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Optimal Number of Clusters"
        subtitle="Step 3 of 5"
        badge="Cluster Analysis"
        description="Five cluster validity indices are computed for k = 3 to 15 and averaged after normalisation. The ensemble consensus identifies k = 3 as the optimal number of clusters."
      />

      <div className="space-y-8">
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Cluster Validity Indices
          </h2>
          <StatsTable
            columns={[
              { key: 'index', label: 'Index' },
              { key: 'criterion', label: 'Criterion' },
              { key: 'direction', label: 'Optimal Direction' },
            ]}
            rows={[
              { index: 'Silhouette', criterion: 'Cohesion vs separation', direction: 'Maximise' },
              { index: 'Davies-Bouldin', criterion: 'Cluster similarity', direction: 'Minimise' },
              { index: 'Calinski-Harabasz', criterion: 'Between/within variance ratio', direction: 'Maximise' },
              { index: 'Score Function', criterion: 'Composite cluster quality', direction: 'Maximise' },
              { index: 'Gap Statistic', criterion: 'Within-cluster dispersion vs null', direction: 'Maximise' },
            ]}
            caption="All indices are normalised to [0, 1] before averaging."
          />
        </section>

        <MethodologyAccordion
          items={[
            {
              title: 'Normalisation and averaging',
              content:
                'Each index is normalised to the [0, 1] range across all tested k values. For indices where smaller is better (e.g., Davies-Bouldin), the normalised score is inverted. The average normalised score identifies the k with the best overall performance.',
            },
            {
              title: 'Range tested',
              content:
                'k = 3 to 15, evaluated on the PCA-reduced phase-separated data. k = 2 is excluded as it would only distinguish "strong" from "weak" without revealing intermediate patterns.',
            },
            {
              title: 'Decision for k = 3',
              content:
                'The ensemble average peaks at k = 3, with consistent support across most individual indices. This aligns with the physical expectation of strong, intermediate, and weak energetic profiles.',
            },
          ]}
        />

        {/* Figure */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Validation Plot
          </h2>
          <FigurePanel
            src="/api/figures?path=figures/cluster/optimal_k_analysis.png"
            alt="Optimal k analysis showing 5 cluster validity indices"
            caption="Five cluster validity indices as a function of k. The vertical dashed line at k = 3 indicates the optimal value selected by ensemble averaging."
            source="figures/cluster/optimal_k_analysis.png"
          />
        </section>

        <ResultSummaryCallout type="result" title="Step 3 Result">
          <p>
            <strong>k = 3</strong> is selected as the optimal number of clusters via
            5-index ensemble consensus. This produces three distinct Energy Patterns
            with clear physical separation.
          </p>
        </ResultSummaryCallout>

        <FileProvenanceBadge
          files={[
            'scripts/cluster_analysis_energy_patterns/step3_optimal_k_analysis.py',
          ]}
          label="Script"
        />
        <FileProvenanceBadge
          files={[
            'results/cluster/optimal_k.txt',
            'results/cluster/optimal_k_raw_indices.csv',
            'results/cluster/optimal_k_normalized_indices.csv',
          ]}
          label="Outputs"
        />
      </div>
    </div>
  )
}
