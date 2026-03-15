import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'

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
        description="Independent PCA per lifecycle phase reduces the 7-dimensional energy space while retaining ≥97% of variance. Phase separation ensures that the distinct energetic behaviour of each lifecycle stage is preserved."
      />

      <div className="space-y-8">
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Rationale</h2>
          <p className="text-sm leading-relaxed text-slate-600">
            PCA is applied independently to each lifecycle phase (incipient,
            intensification, mature, decay) rather than to the combined dataset. This
            prevents the mixing of phase-specific variance structures and ensures that
            cluster assignments reflect the energetic behaviour within each phase.
          </p>
        </section>

        <MethodologyAccordion
          items={[
            {
              title: 'Phase-separated approach',
              content:
                'Each phase produces its own PCA model with its own loadings and explained variance ratios. Typically, 6 out of 7 PCs are retained per phase to capture ≥97% of variance.',
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
              src="/api/figures?path=figures/cluster/pca_variance_wide.png"
              alt="PCA explained variance by phase"
              caption="Explained variance ratio for each PC across lifecycle phases. ≥97% variance is retained."
              source="figures/cluster/pca_variance_wide.png"
            />
            <FigurePanel
              src="/api/figures?path=figures/cluster/pca_loadings_wide.png"
              alt="PCA loadings heatmap by phase"
              caption="Variable loadings on principal components for each lifecycle phase."
              source="figures/cluster/pca_loadings_wide.png"
            />
            <FigurePanel
              src="/api/figures?path=figures/cluster/pca_correlation_wide.png"
              alt="PCA correlation circle"
              caption="Correlation circle showing variable projections on the first two PCs."
              source="figures/cluster/pca_correlation_wide.png"
            />
            <FigurePanel
              src="/api/figures?path=figures/cluster/pca_scatter_wide.png"
              alt="PCA scatter plot"
              caption="Cyclone distribution in PC1-PC2 space for each lifecycle phase."
              source="figures/cluster/pca_scatter_wide.png"
            />
          </div>
        </section>

        <ResultSummaryCallout type="result" title="Step 2 Result">
          <p>
            PCA reduces the 7-dimensional energy space to ~6 PCs per phase, retaining
            ≥97% variance. The reduced representation is used as input for cluster
            validity analysis and K-Means clustering.
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
            'results/cluster/pca_scores_{phase}.csv',
            'results/cluster/pca_loadings_{phase}.csv',
            'results/cluster/pca_explained_variance_{phase}.csv',
            'results/cluster/pca_models.pkl',
          ]}
          label="Outputs"
        />
      </div>
    </div>
  )
}
