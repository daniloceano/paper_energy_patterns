import type { Metadata } from 'next'
import { GitCompareArrows, Search } from 'lucide-react'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import AnalysisCardGrid from '@/components/analysis/AnalysisCardGrid'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import Breadcrumbs from '@/components/layout/Breadcrumbs'

export const metadata: Metadata = {
  title: 'LEC–Field Dependence',
  description:
    'How well do dynamical field features predict the energetics of individual South Atlantic cyclones?',
}

export default function FieldDependencePage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="LEC–Field Dependence Analysis"
        badge="PREDEP"
        subtitle="Predictive Dependence between Dynamical Fields and Lorenz Energy Cycle"
        description="Investigates, at the individual-cyclone level, how much scalar features extracted from ERA5 dynamical fields help predict Lorenz Energy Cycle terms during the intensification phase. Uses the PREDEP metric (Assunção et al. 2025) alongside Pearson and Spearman correlations as baseline references."
      />

      <div className="mb-8 space-y-4">
        <ResultSummaryCallout type="result" title="Key Finding">
          <p>
            All 24 LEC terms differ significantly across EP1, EP2, and EP3.
            The strongest predictive associations (PREDEP &gt; 0.70) are found in EP3
            for barotropic conversion (BKz) predicted by upper-level kinetic energy
            advection and ageostrophic flux convergence. Canonical LEC terms used in
            the cluster analysis (Ca, Ck, Ge, BAe, BKe, Ae, Ke) show moderate-to-strong
            predictability from all five dynamical fields.
          </p>
        </ResultSummaryCallout>

        <ResultSummaryCallout type="info" title="Analysis Framework">
          <ul className="list-inside list-disc space-y-1 text-sm">
            <li>
              <strong>2,733 cyclones</strong> (EP1 = 330, EP2 = 776, EP3 = 1,625) during
              the intensification phase, sampled at central timesteps.
            </li>
            <li>
              <strong>5 dynamical fields</strong>: PV at 850 and 200 hPa, temperature
              advection at 850 hPa, AFC and KE advection at 250 hPa.
            </li>
            <li>
              <strong>13 spatial features</strong> per field: domain mean, centre value,
              4 borders, 2 contrasts, 4 quadrants, and absolute domain mean.
            </li>
            <li>
              <strong>Direction</strong>: LEC term = response (Y), dynamical
              feature = predictor (X). PREDEP answers: &quot;how much does the feature
              reduce prediction uncertainty of the LEC term?&quot;
            </li>
          </ul>
        </ResultSummaryCallout>
      </div>

      <AnalysisCardGrid
        columns={2}
        cards={[
          {
            title: 'EP Differences',
            description:
              'Are Energy Patterns statistically different? Significance heatmaps, effect-size analysis, volcano plots, and rankings quantifying how strongly LEC terms and dynamical features discriminate between EP1, EP2, and EP3.',
            href: '/analyses/field-dependence/ep-differences',
            icon: GitCompareArrows,
          },
          {
            title: 'Dependence Explorer',
            description:
              'Interactive exploration of PREDEP, Pearson, and Spearman metrics. Reference heatmaps, filterable drill-down by field, feature, LEC term, and EP, with on-demand scatterplots.',
            href: '/analyses/field-dependence/dependence-explorer',
            icon: Search,
          },
        ]}
      />
    </div>
  )
}
