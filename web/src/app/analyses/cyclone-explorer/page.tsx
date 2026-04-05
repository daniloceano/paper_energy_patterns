import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import CycloneExplorerClient from './CycloneExplorerClient'
import manifestData from '@/content/cyclone_explorer_manifest.json'
import type { CycloneExplorerManifest } from '@/lib/types'

// Featured cyclones: top 3 most intense from each EP based on max vor42
const FEATURED_CYCLONES = [
  {
    trackId: '19920472',
    title: 'EP1 #1 most intense',
    subtitle: 'Maximum relative vorticity at 850 hPa: 15.95 ×10⁻⁵ s⁻¹',
  },
  {
    trackId: '19820917',
    title: 'EP1 #2 most intense',
    subtitle: 'Maximum relative vorticity at 850 hPa: 15.38 ×10⁻⁵ s⁻¹',
  },
  {
    trackId: '19920418',
    title: 'EP1 #3 most intense',
    subtitle: 'Maximum relative vorticity at 850 hPa: 14.98 ×10⁻⁵ s⁻¹',
  },
  {
    trackId: '19950629',
    title: 'EP2 #1 most intense',
    subtitle: 'Maximum relative vorticity at 850 hPa: 15.53 ×10⁻⁵ s⁻¹',
  },
  {
    trackId: '20070643',
    title: 'EP2 #2 most intense',
    subtitle: 'Maximum relative vorticity at 850 hPa: 15.48 ×10⁻⁵ s⁻¹',
  },
  {
    trackId: '19870253',
    title: 'EP2 #3 most intense',
    subtitle: 'Maximum relative vorticity at 850 hPa: 15.30 ×10⁻⁵ s⁻¹',
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

        <ResultSummaryCallout type="info" title="Selection Criteria">
          <p>
            This explorer shows the <strong>10 most intense cyclones from each energy pattern</strong> (EP1 and EP2), 
            selected based on maximum relative vorticity at 850 hPa (vor42) during the intensification phase. 
            Intensity is defined by the peak absolute value of relative vorticity (units: 10⁻⁵ s⁻¹), 
            a standard metric for cyclone strength in the Southern Hemisphere.
          </p>
        </ResultSummaryCallout>

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
