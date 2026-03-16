import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import StatsTable from '@/components/analysis/StatsTable'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import { ENERGY_PATTERNS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Step 4 — Clustering & LPS',
}

export default function Step4Page() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Clustering & Lorenz Phase Space"
        subtitle="Step 4 of 5"
        badge="Cluster Analysis"
        description="K-Means (k=3, n_init=100) is applied per lifecycle phase. Clusters are labelled as EP1, EP2, EP3 based on energy conversion magnitudes. The Lorenz Phase Space provides a physical visualisation of each pattern."
      />

      <div className="space-y-8">
        {/* K-Means method */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">K-Means Configuration</h2>
          <StatsTable
            columns={[
              { key: 'param', label: 'Parameter' },
              { key: 'value', label: 'Value' },
            ]}
            rows={[
              { param: 'Algorithm', value: "Lloyd's K-Means with K-Means++ init" },
              { param: 'k', value: '3 (from Step 3)' },
              { param: 'n_init', value: '100 (convergence guarantee)' },
              { param: 'random_state', value: '42 (reproducibility)' },
              { param: 'Application', value: 'Phase-separated (4 independent runs)' },
            ]}
          />
        </section>

        {/* Cluster labelling */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Cluster Labelling
          </h2>
          <p className="text-sm leading-relaxed text-slate-600">
            After clustering, the three groups are labelled based on the magnitude of their
            barotropic conversion (C<sub>k</sub>) and overall energetic intensity. The
            centroids are reconstructed from PC space back to the original energy space to
            enable physical interpretation.
          </p>
        </section>

        {/* EP summary */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Energy Pattern Summary
          </h2>
          <StatsTable
            columns={[
              { key: 'id', label: 'Pattern' },
              { key: 'count', label: 'N' },
              { key: 'pct', label: '%' },
              { key: 'ck', label: 'Mean Ck (W m⁻²)' },
              { key: 'character', label: 'Character' },
            ]}
            rows={Object.values(ENERGY_PATTERNS).map((ep) => ({
              id: ep.id,
              count: ep.count,
              pct: ep.percentage,
              ck: ep.meanCk,
              character:
                ep.id === 'EP1'
                  ? 'Strong conversions, energy exporter'
                  : ep.id === 'EP2'
                    ? 'Intermediate, energy importer'
                    : 'Weak, background',
            }))}
            highlightColumn="ck"
          />
        </section>

        {/* LPS figures */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Lorenz Phase Space Diagrams
          </h2>
          <p className="mb-4 text-sm text-slate-600">
            The LPS plots the conversion terms against each other, revealing the energetic
            trajectory of each pattern. &ldquo;Conversion&rdquo; shows C<sub>k</sub> vs C<sub>a</sub>;
            &ldquo;Imports&rdquo; shows BA<sub>e</sub> vs BK<sub>e</sub>.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <FigurePanel
              src="/figures/cluster/lps_conversion_default.png"
              alt="LPS Conversion diagram (Ck vs Ca)"
              caption="Lorenz Phase Space — Conversion terms (Ck vs Ca) for EP1, EP2, EP3."
              source="figures/cluster/lps_conversion_default.png"
            />
            <FigurePanel
              src="/figures/cluster/lps_imports_default.png"
              alt="LPS Imports diagram (BAe vs BKe)"
              caption="Lorenz Phase Space — Boundary fluxes (BAe vs BKe) for EP1, EP2, EP3."
              source="figures/cluster/lps_imports_default.png"
            />
            <FigurePanel
              src="/figures/cluster/lps_conversion_zoom.png"
              alt="LPS Conversion diagram zoomed"
              caption="Zoomed view of the conversion LPS, highlighting EP2 and EP3 separation."
              source="figures/cluster/lps_conversion_zoom.png"
            />
            <FigurePanel
              src="/figures/cluster/lps_imports_zoom.png"
              alt="LPS Imports diagram zoomed"
              caption="Zoomed view of the imports LPS."
              source="figures/cluster/lps_imports_zoom.png"
            />
          </div>
        </section>

        {/* Physical interpretation */}
        <ResultSummaryCallout type="result" title="Physical Interpretation">
          <p>
            <strong>EP1</strong> cyclones are energy exporters with the largest barotropic (C<sub>k</sub> = {ENERGY_PATTERNS.EP1.meanCk} W m⁻²)
            and baroclinic conversions, extracting energy from both horizontal shear and temperature gradients.
            They contribute to downstream cyclogenesis via negative boundary fluxes.{' '}
            <strong>EP2</strong> cyclones are energy importers with moderate conversions, coupled to jet
            stream dynamics.{' '}
            <strong>EP3</strong> represents the climatological background with weak energetics.
          </p>
        </ResultSummaryCallout>

        <FileProvenanceBadge
          files={[
            'scripts/cluster_analysis_energy_patterns/step4_apply_kmeans.py',
            'scripts/cluster_analysis_energy_patterns/step5_plot_energy_patterns.py',
          ]}
          label="Scripts"
        />
        <FileProvenanceBadge
          files={[
            'results/cluster/kmeans_clustered_data_{phase}.csv',
            'results/cluster/kmeans_centroids_energy_{phase}.csv',
            'results/cluster/kmeans_summary_{phase}.csv',
          ]}
          label="Outputs"
        />
      </div>
    </div>
  )
}
