import type { Metadata } from 'next'
import { BarChart3, Layers, TrendingDown } from 'lucide-react'
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
        description="Two complementary analyses characterise the energetic patterns of South Atlantic cyclones: (1) PCA-based clustering identifies three Energy Patterns from Lorenz Energy Cycle diagnostics, and (2) ERA5 composite analysis reveals the atmospheric structure differences between EP1 and EP2 during intensification."
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
        ]}
      />
    </div>
  )
}
