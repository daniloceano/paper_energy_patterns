import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import FigurePanel from '@/components/analysis/FigurePanel'
import EpDifferencesClient from './EpDifferencesClient'

import significanceData from '@/content/lfd_significance.json'
import pairwiseData from '@/content/lfd_pairwise.json'
import type { LfdSignificanceRow, LfdPairwiseRow } from '@/lib/types'

// LFD figures are committed to web/public/figures/lec_field_dependence/.
// Use absolute paths so they always load from the static public/ directory,
// regardless of whether NEXT_PUBLIC_SUPABASE_FIGURES_URL is set on Vercel.
const lfd = (name: string) => `/figures/lec_field_dependence/${name}`

export const metadata: Metadata = {
  title: 'EP Differences — LEC Field Dependence',
  description: 'Statistical significance and effect size of EP differences for LEC terms and dynamical features.',
}

export default function EpDifferencesPage() {
  const significance = significanceData as LfdSignificanceRow[]
  const pairwise = pairwiseData as LfdPairwiseRow[]

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="EP Differences"
        subtitle="Do Energy Patterns Differ Statistically?"
        badge="Significance & Effect Size"
        description="Kruskal-Wallis omnibus tests and Dunn post-hoc pairwise comparisons quantify whether and how strongly EP1, EP2, and EP3 differ on every LEC term and dynamical feature."
      />

      {/* ── Methodology ───────────────────────────────────── */}
      <div className="mb-8">
        <MethodologyAccordion
          items={[
            {
              title: 'What is being compared?',
              content:
                'For each variable (LEC term or dynamical feature), the distributions of values across EP1, EP2, and EP3 are compared. A global test checks whether at least one EP differs. If significant, pairwise contrasts identify which specific EP pairs differ.',
            },
            {
              title: 'How to interpret effect size',
              content:
                'Effect size (ε² for omnibus; rank-biserial r for pairwise) measures the practical magnitude of the difference, independent of sample size. ε² < 0.01 is negligible; 0.01–0.06 is small; 0.06–0.14 is medium; > 0.14 is large. Rank-biserial r ranges from −1 to +1: its absolute value indicates overlap between the two groups (|r| ≈ 0 = nearly identical; |r| ≈ 1 = complete separation). In the heatmaps, values < 0.1 are shown in grey to mark negligible effects.',
            },
            {
              title: 'Why p-value alone is not enough',
              content:
                'With 2,733 cyclones, even trivially small differences reach statistical significance (p < 0.05). Effect size separates genuine scientific relevance from mere statistical significance. The ranking and volcano plots are designed to emphasise variables that are both statistically significant and have large effect sizes.',
            },
            {
              title: 'Testing pipeline',
              content:
                'All distributions are non-normal (Shapiro-Wilk) → Kruskal-Wallis omnibus test (non-parametric). Post-hoc: Dunn test with Holm correction for multiple comparisons. FDR correction applied across all ~150 variables. Effect sizes: ε² (omnibus) and rank-biserial r (pairwise).',
            },
            {
              title: 'Canonical vs Exploratory',
              content:
                'Canonical analysis uses the 7 LEC terms from the EP clustering (Ca, Ck, Ge, BAe, BKe, Ae, Ke) — these are the terms most directly relevant to the paper\'s classification. Exploratory analysis includes all 24 LEC terms (zonal + eddy reservoirs, conversions, boundary fluxes, residuals, tendencies). The exploratory set validates that EP differences extend beyond the clustering features.',
            },
          ]}
        />
      </div>

      {/* ── Significance Heatmaps ────────────────────────── */}
      <section className="mb-12">
        <h2 className="mb-2 text-xl font-semibold text-slate-900">Significance Heatmaps</h2>
        <p className="mb-6 text-sm text-slate-600">
          Red cells indicate statistically significant differences (p &lt; 0.05 after Holm correction)
          between EP pairs. Columns represent the three contrasts: EP1 vs EP2, EP1 vs EP3, EP2 vs EP3.
        </p>
        <div className="grid gap-6 md:grid-cols-1">
          <FigurePanel
            src={lfd('significance_heatmap_lec_terms.png')}
            alt="Significance heatmap — LEC terms"
            caption="Pairwise significance for all 24 LEC terms. Nearly all contrasts are significant, confirming robust EP separation."
            source="figures/lec_field_dependence/significance_heatmap_lec_terms.png"
          />
          <div className="grid gap-6 md:grid-cols-2">
            <FigurePanel
              src={lfd('significance_heatmap_absolute_features.png')}
              alt="Significance heatmap — absolute features"
              caption="Absolute-field features: most dynamical features differ significantly across EPs."
              source="figures/lec_field_dependence/significance_heatmap_absolute_features.png"
            />
            <FigurePanel
              src={lfd('significance_heatmap_anomaly_features.png')}
              alt="Significance heatmap — anomaly features"
              caption="Anomaly-field features (EPALL-relative): pattern broadly mirrors absolute fields."
              source="figures/lec_field_dependence/significance_heatmap_anomaly_features.png"
            />
          </div>
        </div>
      </section>

      {/* ── Effect Size Heatmaps ─────────────────────────── */}
      <section className="mb-12">
        <h2 className="mb-2 text-xl font-semibold text-slate-900">Effect Size Heatmaps</h2>
        <p className="mb-6 text-sm text-slate-600">
          Rank-biserial <em>r</em> for each variable × EP contrast. Warm colours = large effect
          (strong EP differentiation); grey cells = |r| &lt; 0.1 (negligible). Effect size measures
          practical magnitude — unlike p-values, it does not inflate with sample size.
        </p>
        <div className="grid gap-6 md:grid-cols-1">
          <FigurePanel
            src={lfd('effect_size_heatmap_lec_terms.png')}
            alt="Effect size heatmap — LEC terms"
            caption="Pairwise effect sizes for LEC terms. Ke, RKe, Ce, and Ca show the largest inter-EP differences."
            source="figures/lec_field_dependence/effect_size_heatmap_lec_terms.png"
          />
          <div className="grid gap-6 md:grid-cols-2">
            <FigurePanel
              src={lfd('effect_size_heatmap_absolute_features.png')}
              alt="Effect size heatmap — absolute features"
              caption="Absolute-field feature effect sizes across EP contrasts."
              source="figures/lec_field_dependence/effect_size_heatmap_absolute_features.png"
            />
            <FigurePanel
              src={lfd('effect_size_heatmap_anomaly_features.png')}
              alt="Effect size heatmap — anomaly features"
              caption="Anomaly-field feature effect sizes."
              source="figures/lec_field_dependence/effect_size_heatmap_anomaly_features.png"
            />
          </div>
        </div>
      </section>

      {/* ── Volcano Plots ────────────────────────────────── */}
      <section className="mb-12">
        <h2 className="mb-2 text-xl font-semibold text-slate-900">Volcano Plots</h2>
        <p className="mb-6 text-sm text-slate-600">
          Effect size (x) vs statistical significance (−log₁₀ p, y). Points in the upper-right
          quadrant are both highly significant <em>and</em> have large effects — these
          are the variables that most robustly distinguish EPs.
        </p>
        <div className="grid gap-6 md:grid-cols-3">
          <FigurePanel
            src={lfd('volcano_lec_terms.png')}
            alt="Volcano plot — LEC terms"
            caption="LEC terms"
            source="figures/lec_field_dependence/volcano_lec_terms.png"
          />
          <FigurePanel
            src={lfd('volcano_absolute_features.png')}
            alt="Volcano plot — absolute features"
            caption="Absolute features"
            source="figures/lec_field_dependence/volcano_absolute_features.png"
          />
          <FigurePanel
            src={lfd('volcano_anomaly_features.png')}
            alt="Volcano plot — anomaly features"
            caption="Anomaly features"
            source="figures/lec_field_dependence/volcano_anomaly_features.png"
          />
        </div>
      </section>

      {/* ── Rankings ─────────────────────────────────────── */}
      <section className="mb-12">
        <h2 className="mb-2 text-xl font-semibold text-slate-900">Effect Size Rankings</h2>
        <p className="mb-6 text-sm text-slate-600">
          Top 20 variables by omnibus effect size (ε²). These variables show the strongest
          overall discrimination across all three EPs simultaneously.
        </p>
        <div className="grid gap-6 md:grid-cols-3">
          <FigurePanel
            src={lfd('effect_ranking_lec_terms.png')}
            alt="Effect ranking — LEC terms"
            caption="LEC terms"
            source="figures/lec_field_dependence/effect_ranking_lec_terms.png"
          />
          <FigurePanel
            src={lfd('effect_ranking_absolute_features.png')}
            alt="Effect ranking — absolute features"
            caption="Absolute features"
            source="figures/lec_field_dependence/effect_ranking_absolute_features.png"
          />
          <FigurePanel
            src={lfd('effect_ranking_anomaly_features.png')}
            alt="Effect ranking — anomaly features"
            caption="Anomaly features"
            source="figures/lec_field_dependence/effect_ranking_anomaly_features.png"
          />
        </div>
      </section>

      {/* ── Interactive Table ─────────────────────────────── */}
      <section className="mb-12">
        <h2 className="mb-4 text-xl font-semibold text-slate-900">Interactive Data Table</h2>
        <p className="mb-6 text-sm text-slate-600">
          Browse all significance and effect-size results. Filter by variable type and
          canonical/exploratory scope. Sort by any column to find the most discriminating variables.
        </p>
        <EpDifferencesClient
          significance={significance}
          pairwise={pairwise}
        />
      </section>
    </div>
  )
}
