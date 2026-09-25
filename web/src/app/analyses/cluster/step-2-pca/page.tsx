import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import pcaData from '@/content/cluster_step2_data.json'

export const metadata: Metadata = {
  title: 'Step 2 — PCA',
}

export default function Step2Page() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Principal Component Analysis"
        subtitle="Step 2 of 5"
        badge="Cluster Analysis"
        description={`A single PCA reduces the 28-dimensional term-by-phase energy space to ${pcaData.n_components} components while retaining ${(pcaData.retained_variance * 100).toFixed(1)}% of the joint variance.`}
      />

      <div className="space-y-8">
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Rationale</h2>
          <p className="text-sm leading-relaxed text-slate-600">
            PCA is applied once to the global 28-feature matrix. Keeping all four lifecycle
            phases in the same row allows the components to represent both relationships among
            energy terms and the way those relationships evolve from incipient to decay.
          </p>
        </section>

        <MethodologyAccordion
          items={[
            {
              title: 'Global wide-matrix approach',
              content:
                `One PCA model is fitted to 7 terms × 4 phases. The first ${pcaData.n_components} components retain ${(pcaData.retained_variance * 100).toFixed(1)}% of the total standardised variance.`,
            },
            {
              title: 'Standardisation',
              content:
                'Input features are standardised (mean=0, σ=1) before PCA. This prevents energy terms with larger magnitudes (e.g., reservoirs in J m⁻²) from dominating the variance over conversion terms (W m⁻²).',
            },
            {
              title: 'Interpretation of PCs',
              content:
                'The first few PCs typically capture the overall energy magnitude (PC1) and the conversion-flux balance (PC2–3). Higher PCs capture residual inter-term correlations.',
            },
          ]}
        />

        {/* Figures */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            PCA Results
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <FigurePanel
              src="/figures/cluster/pca_variance_wide.png"
              alt="PCA explained variance by phase"
              caption={`Explained and cumulative variance for the global PCA. ${pcaData.n_components} components retain ${(pcaData.retained_variance * 100).toFixed(1)}% of the variance.`}
              source="figures/cluster/pca_variance_wide.png"
            />
            <FigurePanel
              src="/figures/cluster/pca_loadings_wide.png"
              alt="PCA loadings heatmap for term-by-phase features"
              caption="Loadings of the 28 term-by-phase features on the retained principal components."
              source="figures/cluster/pca_loadings_wide.png"
            />
            <FigurePanel
              src="/figures/cluster/pca_correlation_wide.png"
              alt="Correlation matrix of the 28 energy features"
              caption="Correlation matrix across energy terms and lifecycle phases."
              source="figures/cluster/pca_correlation_wide.png"
            />
            <FigurePanel
              src="/figures/cluster/pca_scatter_wide.png"
              alt="PCA scatter plot"
              caption="Cyclone distribution across the leading global principal components."
              source="figures/cluster/pca_scatter_wide.png"
            />
          </div>
        </section>

        <ResultSummaryCallout type="result" title="Step 2 Result">
          <p>
            PCA reduces the 28-dimensional global energy space to {pcaData.n_components}{' '}
            components, retaining {(pcaData.retained_variance * 100).toFixed(1)}% of the
            variance. This single representation feeds both cluster validation and K-Means.
          </p>
        </ResultSummaryCallout>

        <FileProvenanceBadge
          files={[
            'scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py',
            'scripts/cluster_analysis_energy_patterns/step2_plot_pca_results.py',
          ]}
          label="Scripts"
        />
        <FileProvenanceBadge
          files={[
            'results/cluster/pca_scores.csv',
            'results/cluster/pca_loadings.csv',
            'results/cluster/pca_explained_variance.csv',
            'results/cluster/pca_models.pkl',
          ]}
          label="Outputs"
        />
      </div>
    </div>
  )
}
