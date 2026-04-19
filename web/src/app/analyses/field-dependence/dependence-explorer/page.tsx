import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import DependenceExplorerClient from './DependenceExplorerClient'

import predepData from '@/content/lfd_predep.json'
import topData from '@/content/lfd_top_associations.json'
import type { LfdPredepRow, LfdTopAssociation } from '@/lib/types'

export const metadata: Metadata = {
  title: 'Dependence Explorer — LEC Field Dependence',
  description: 'Interactive exploration of PREDEP, Pearson and Spearman metrics between dynamical fields and LEC terms.',
}

export default function DependenceExplorerPage() {
  const predep = predepData as LfdPredepRow[]
  const top = topData as { all: LfdTopAssociation[]; canonical: LfdTopAssociation[] }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Dependence Explorer"
        subtitle="PREDEP, Pearson & Spearman"
        badge="Interactive"
        description="Explore how scalar features from ERA5 dynamical fields predict Lorenz Energy Cycle terms. PREDEP (Assunção et al. 2025) is the primary metric; Pearson and Spearman correlations serve as linear and rank-based baselines."
      />

      {/* ── Methodology ───────────────────────────────────── */}
      <div className="mb-8">
        <MethodologyAccordion
          items={[
            {
              title: 'What is PREDEP?',
              content:
                'PREDEP (α_{Y|X}) measures how much knowing the predictor X reduces the uncertainty in predicting the response Y. It is non-parametric, captures non-linear and non-monotonic relationships, is bounded in [0, 1], and equals zero if and only if X and Y are independent. α = 0.60 means predicting the LEC term from the dynamical feature reduces prediction error by 60% compared to predicting without it.',
            },
            {
              title: 'PREDEP vs Pearson vs Spearman',
              content:
                'Pearson r measures linear association only; Spearman ρ captures monotonic (but possibly non-linear) rank association. PREDEP captures any functional or non-functional statistical dependence. When PREDEP ≫ |Pearson|, the relationship is non-linear. When PREDEP ≈ |Pearson| ≈ |Spearman|, the relationship is approximately linear.',
            },
            {
              title: 'Direction of the analysis',
              content:
                'The analysis direction is LEC term = Y (response), dynamical feature = X (predictor). PREDEP is asymmetric: α_{Y|X} ≠ α_{X|Y}. This direction answers: "how much does the dynamical feature reduce prediction uncertainty of the LEC term?"',
            },
            {
              title: 'PREDEP does not imply causality',
              content:
                'A high PREDEP value means the feature is statistically predictive of the LEC term, not that the feature physically causes the energetic behaviour. Cyclone energetics and dynamical fields are coupled — the relationship may be causal, reverse-causal, or driven by a common atmospheric state. Physical interpretation must come from theory.',
            },
            {
              title: 'How to read the heatmaps',
              content:
                'Rows = LEC terms, columns = dynamical field × spatial feature combinations. Colour encodes metric value from 0 to 1. Grey cells (< 0.1) indicate negligible association. The heatmaps serve as a macro overview; use the explorer below to drill into specific cells.',
            },
            {
              title: 'Canonical vs Exploratory',
              content:
                'Canonical: the 7 LEC terms used in the EP clustering (Ca, Ck, Ge, BAe, BKe, Ae, Ke) — the primary analysis. Exploratory: all 24 LEC terms (reservoirs, conversions, boundary fluxes, residuals, tendencies) — for broader validation. Toggle between sets using the scope filter.',
            },
          ]}
        />
      </div>

      <ResultSummaryCallout type="info" title="How to Use">
        <p className="text-sm">
          The <strong>reference heatmaps</strong> at the top show PREDEP, |Pearson r|, and |Spearman ρ|
          for each EP and field type. Below, the <strong>interactive explorer</strong> lets you select
          a specific field, feature, LEC term, and EP to see the metric values and an on-demand
          scatterplot of the underlying per-cyclone data.
        </p>
      </ResultSummaryCallout>

      {/* ── Explorer ──────────────────────────────────────── */}
      <DependenceExplorerClient
        predep={predep}
        topAssociations={top}
      />
    </div>
  )
}
