import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import CycloneExplorerClient from './CycloneExplorerClient'
import manifestData from '@/content/cyclone_explorer_manifest.json'
import type { CycloneExplorerManifest } from '@/lib/types'

const FEATURED_CYCLONES = [
  {
    trackId: '19790135',
    title: 'EP1 reference cyclone',
    subtitle: 'Long-lived case with dynamic assets available in the subset validation.',
  },
  {
    trackId: '19790205',
    title: 'EP1 mature case',
    subtitle: 'Extended intensification phase, useful to inspect temporal evolution.',
  },
  {
    trackId: '19800411',
    title: 'EP1 spring case',
    subtitle: 'Compact EP1 event with a clear intensification window.',
  },
  {
    trackId: '19790048',
    title: 'EP2 reference cyclone',
    subtitle: 'Long-lived EP2 event with dynamic assets available in the subset validation.',
  },
  {
    trackId: '19790669',
    title: 'EP2 mature case',
    subtitle: 'Representative EP2 cyclone with a broader temporal window.',
  },
  {
    trackId: '19790933',
    title: 'EP2 transition case',
    subtitle: 'Useful to compare synoptic and dynamic fields in late spring conditions.',
  },
] as const

export const metadata: Metadata = {
  title: 'Cyclone Explorer',
  description: 'Explore individual EP1 and EP2 cyclones through time during intensification.',
}

export default function CycloneExplorerPage() {
  const manifest = manifestData as CycloneExplorerManifest
  
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Cyclone Explorer"
        subtitle="Individual Cyclone Temporal Analysis"
        badge="EP1 & EP2"
        description={`Explore the temporal evolution of individual EP1 (N=${manifest.metadata.ep1_count}) and EP2 (N=${manifest.metadata.ep2_count}) cyclones during intensification. Switch between Synoptic fields (baseline meteorological structure) and Dynamic fields (baroclinic/barotropic diagnostics) at each timestep.`}
      />

      <div className="space-y-6">
        {manifest.metadata.is_hotfix_subset && (
          <ResultSummaryCallout type="warning" title="Limited Preview">
            <p>
              This explorer currently shows a curated subset of 10 cyclones per energy pattern, 
              selected for optimal storm-centering quality. The full dataset (~1400 cyclones) 
              will be available after infrastructure improvements. Current selection prioritizes 
              cases where the cyclone remains well-centered within the 30°×30° domain throughout 
              the intensification phase.
            </p>
          </ResultSummaryCallout>
        )}

        <ResultSummaryCallout type="info" title="How to Use">
          <p>
            Select an Energy Pattern (EP1 or EP2) and a cyclone from the dropdown. Use the 
            temporal slider to navigate through the intensification phase. The track map 
            highlights the current position. In the right panel, choose between Synoptic fields 
            and Dynamic fields, then select the dynamic product when applicable.
          </p>
        </ResultSummaryCallout>

        <CycloneExplorerClient
          manifest={manifest}
          featuredCases={[]}
        />

        <ResultSummaryCallout type="info" title="Field Groups">
          <ul className="list-inside list-disc space-y-1 text-sm">
            <li><strong>Synoptic fields:</strong> Baseline meteorological environment (SLP, temperature, humidity, geopotential) in cyclone-centered coordinates.</li>
            <li><strong>Dynamic fields:</strong> Diagnostics linked to cyclone dynamic structure, including PV, temperature advection, AFC, KE-advection anomaly, RK criterion and barotropic critical-region context.</li>
          </ul>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
