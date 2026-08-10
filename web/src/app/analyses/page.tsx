import type { Metadata } from 'next'
import { BarChart3, Layers, TrendingDown, GitCompareArrows, Tornado } from 'lucide-react'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import AnalysisCardGrid from '@/components/analysis/AnalysisCardGrid'
import Breadcrumbs from '@/components/layout/Breadcrumbs'

export const metadata: Metadata = {
  title: 'Analyses',
  description: 'Overview of cluster analysis and composite structure analysis.',
}

export default function AnalysesPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Analyses"
        badge="Research Pipeline"
        description="Complementary analyses characterise the energetic patterns of South Atlantic cyclones. PCA-based clustering identifies three Energy Patterns from Lorenz Energy Cycle diagnostics; ERA5 composites reveal the atmospheric structure behind them; the barotropic conversion is decomposed into its subterms; the statistical dependence between dynamical fields and energy terms is quantified; and the cyclone phase space places each system's thermal structure against its energetics."
      />

      <AnalysisCardGrid
        columns={2}
        cards={[
          {
            title: 'Cluster Analysis — Energy Patterns',
            description:
              'PCA dimensionality reduction, optimal cluster determination, K-Means classification, and Lorenz Phase Space visualisation of EP1, EP2, EP3.',
            href: '/analyses/cluster',
            icon: BarChart3,
          },
          {
            title: 'Composite Analysis — EP Structure',
            description:
              'Storm-centred ERA5 composites comparing EP1 vs EP2 atmospheric structure across 9 diagnostic fields: EGR, PV, temperature advection, moisture flux, SLP, and more.',
            href: '/analyses/composites',
            icon: Layers,
          },
          {
            title: 'Ck Subterms Analysis — EP1 Barotropic Decomposition',
            description:
              'Decomposition of barotropic energy conversion (Ck) into five subterms (A–E) for EP1 cyclones. Genesis density maps and dominance classification by intensification-phase subterm.',
            href: '/analyses/ck-subterms',
            icon: TrendingDown,
          },
          {
            title: 'LEC–Field Dependence',
            description:
              'Statistical dependence between ERA5 dynamical fields and Lorenz Energy Cycle terms. EP-level differences (Kruskal–Wallis, effect sizes, volcano plots) and per-cyclone dependence metrics (PREDEP, Pearson, Spearman) with interactive exploration.',
            href: '/analyses/field-dependence',
            icon: GitCompareArrows,
          },
          {
            title: 'Cyclone Phase Space — Thermal Structure',
            description:
              'Hart (2003) phase space for 6,776 cyclones: extratropical, subtropical and tropical structure under a 36 h persistence gate and a warm-seclusion filter, cross-referenced against the Energy Patterns. EP2 shows 1.36× the pooled rate of subtropical transition.',
            href: '/analyses/cps',
            icon: Tornado,
          },
        ]}
      />
    </div>
  )
}
