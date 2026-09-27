import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import StatsTable from '@/components/analysis/StatsTable'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import { ENERGY_PATTERNS } from '@/lib/constants'
import optimalKData from '@/content/cluster_step3_data.json'

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
        description={`One K-Means solution (k=${optimalKData.optimal_k}, n_init=100) is applied to the global lifecycle representation. Clusters are ranked by intensification-phase conversion magnitude, and Lorenz Phase Space visualises their trajectories.`}
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
              { param: 'k', value: `${optimalKData.optimal_k} (from Step 3)` },
              { param: 'n_init', value: '100 independent initialisations' },
              { param: 'random_state', value: '42 (reproducibility)' },
              { param: 'Application', value: 'One global run on 15 PCA components' },
            ]}
          />
        </section>

        {/* Cluster labelling */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Cluster Labelling
          </h2>
          <p className="text-sm leading-relaxed text-slate-600">
            K-Means cluster numbers are arbitrary. After fitting, the centroids are reconstructed
            from PC space to the original 28 energy features and ranked by{' '}
            |C<sub>a,int</sub>| + |C<sub>k,int</sub>|. The largest combined magnitude is EP1,
            the intermediate value is EP2, and the smallest is EP3. This mapping is written to a
            versioned result file and consumed by every downstream view.
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
              { key: 'ca', label: 'Mean Ca,int (W m⁻²)' },
              { key: 'ck', label: 'Mean Ck,int (W m⁻²)' },
              { key: 'character', label: 'Character' },
            ]}
            rows={Object.values(ENERGY_PATTERNS).map((ep) => ({
              id: ep.id,
              count: ep.count.toLocaleString(),
              pct: ep.percentage.toFixed(1),
              ca: ep.meanCa.toFixed(2),
              ck: ep.meanCk.toFixed(2),
              character:
                ep.id === 'EP1'
                  ? 'Strongest combined |Ca,int| + |Ck,int|'
                  : ep.id === 'EP2'
                    ? 'Intermediate combined conversion magnitude'
                    : 'Weakest combined conversion magnitude',
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
            The corrected solution separates two different high-conversion regimes rather than a
            simple strong-to-weak sequence in C<sub>k</sub>. EP1 combines C<sub>a,int</sub> ={' '}
            {ENERGY_PATTERNS.EP1.meanCa.toFixed(2)} and C<sub>k,int</sub> ={' '}
            {ENERGY_PATTERNS.EP1.meanCk.toFixed(2)} W m⁻²; EP2 combines{' '}
            {ENERGY_PATTERNS.EP2.meanCa.toFixed(2)} and{' '}
            {ENERGY_PATTERNS.EP2.meanCk.toFixed(2)} W m⁻²; EP3 has the smallest combined
            conversion magnitude. Under the toolkit sign convention, negative C<sub>k</sub>{' '}
            transfers kinetic energy from the zonal flow to eddies, while positive C<sub>k</sub>{' '}
            transfers it from eddies to the zonal flow. Dynamical interpretations beyond these
            measured centroids are reserved for the downstream analyses.
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
            'results/cluster/kmeans_clustered_data.csv',
            'results/cluster/kmeans_centroids_energy.csv',
            'results/cluster/kmeans_summary.csv',
            'results/cluster/cluster_to_ep.json',
          ]}
          label="Outputs"
        />
      </div>
    </div>
  )
}
