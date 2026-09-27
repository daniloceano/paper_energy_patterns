import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import StatsTable from '@/components/analysis/StatsTable'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import optimalKData from '@/content/cluster_step3_data.json'

export const metadata: Metadata = {
  title: 'Step 3 — Optimal k',
}

export default function Step3Page() {
  const ensembleRanking = [...optimalKData.normalized_indices]
    .sort((a, b) => Number(b.mean_index) - Number(a.mean_index))
    .slice(0, 5)
    .map((row) => ({
      k: row.k,
      ensemble: Number(row.mean_index).toFixed(3),
      stability: Number(row.Stability_reval).toFixed(3),
    }))

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Optimal Number of Clusters"
        subtitle="Step 3 of 5"
        badge="Cluster Analysis"
        description={`Five internal validity indices and cross-validated clustering stability are computed for k = 3 to 15. Their normalised ensemble selects k = ${optimalKData.optimal_k}.`}
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
              { index: 'Reval stability', criterion: 'Prediction stability under repeated cross-validation', direction: 'Maximise' },
            ]}
            caption="All six criteria are normalised to [0, 1] before averaging; Davies–Bouldin is reversed so that larger always means better."
          />
        </section>

        <MethodologyAccordion
          items={[
            {
              title: 'Normalisation and averaging',
              content:
                'Each criterion is normalised to the [0, 1] range across all tested k values. Davies–Bouldin is inverted because smaller is better. Reval is already expressed as stability (1 minus validation misclassification), so it is not inverted. The average of all six normalised criteria identifies the selected k.',
            },
            {
              title: 'Range tested',
              content:
                'k = 3 to 15, evaluated on the 15-component global PCA representation. The candidate range is fixed before inspecting the scores.',
            },
            {
              title: `Decision for k = ${optimalKData.optimal_k}`,
              content:
                `The ensemble average reaches its maximum at k = ${optimalKData.optimal_k}. The choice follows the pre-defined numerical rule rather than a physical label imposed on the groups.`,
            },
          ]}
        />

        {/* Figure */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Validation Plot
          </h2>
          <FigurePanel
            src="/figures/cluster/optimal_k_analysis.png"
            alt="Optimal k analysis showing six cluster validation criteria"
            caption={`Six normalised validation criteria as a function of k. The selected solution is k = ${optimalKData.optimal_k}.`}
            source="figures/cluster/optimal_k_analysis.png"
          />
        </section>

        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Highest Ensemble Scores
          </h2>
          <StatsTable
            columns={[
              { key: 'k', label: 'k' },
              { key: 'ensemble', label: 'Mean of six criteria' },
              { key: 'stability', label: 'Normalised Reval stability' },
            ]}
            rows={ensembleRanking}
            highlightColumn="ensemble"
            caption="Values are normalised across the tested k range; the first row is the deterministic ensemble choice."
          />
        </section>

        <ResultSummaryCallout type="result" title="Step 3 Result">
          <p>
            <strong>k = {optimalKData.optimal_k}</strong> is selected by the mean of five
            internal validity indices and repeated cross-validated Reval stability.
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
