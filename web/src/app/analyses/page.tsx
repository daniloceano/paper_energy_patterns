import type { Metadata } from 'next'
import { BarChart3, Layers, TrendingDown, GitCompareArrows, Tornado, BetweenVerticalStart } from 'lucide-react'
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
        description="Complementary analyses characterise the energetic patterns of South Atlantic cyclones. PCA-based clustering identifies three Energy Patterns from Lorenz Energy Cycle diagnostics; corrected pressure-level profiles reveal their vertical energy pathways; ERA5 composites show the atmospheric structure behind them; the barotropic conversion is decomposed into its subterms; and field dependence and cyclone phase space connect energetics to dynamical and thermal structure."
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
              'Storm-centred ERA5 composites comparing EP1, EP2, EP3, and EPALL across 13 diagnostics, including EGR, PV, temperature advection, moisture, SLP, and geopotential height.',
            href: '/analyses/composites',
            icon: Layers,
          },
          {
            title: 'Vertical Structure — Ca and Ck',
            description:
              'Corrected pressure-level distributions of baroclinic and barotropic conversion for all 3,820 cyclones, showing distinct vertical energy pathways in EP1, EP2, and EP3.',
            href: '/analyses/vertical-structure',
            icon: BetweenVerticalStart,
          },
          {
            title: 'Ck Subterms Analysis — Corrected All-Pattern Decomposition',
            description:
              'Corrected decomposition of barotropic energy conversion (Ck) into five subterms (A–E), with vertical profiles, distributions, lifecycle evolution, and intensification-phase dominance for every Energy Pattern.',
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
