import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import CycloneExplorerClient from './CycloneExplorerClient'
import manifestData from '@/content/cyclone_explorer_manifest.json'
import type { CycloneExplorerManifest } from '@/lib/types'

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
        description={`Explore the temporal evolution of individual EP1 (N=${manifest.metadata.ep1_count}) and EP2 (N=${manifest.metadata.ep2_count}) cyclones during their intensification phase. Visualise track progression, sea level pressure, temperature, moisture, and geopotential fields at 6-hourly intervals.`}
      />

      <div className="space-y-6">
        <ResultSummaryCallout type="info" title="How to Use">
          <p>
            Select an Energy Pattern (EP1 or EP2) and a cyclone from the dropdown. Use the 
            temporal slider to navigate through the intensification phase. The track map 
            highlights the current position, and the multi-panel figure shows atmospheric 
            fields at each timestep.
          </p>
        </ResultSummaryCallout>

        <CycloneExplorerClient manifest={manifest} />

        <ResultSummaryCallout type="info" title="Panel Fields">
          <ul className="list-inside list-disc space-y-1 text-sm">
            <li><strong>Top-left:</strong> Sea Level Pressure (SLP) with 850 hPa wind vectors</li>
            <li><strong>Top-right:</strong> Temperature at 850 hPa (°C)</li>
            <li><strong>Bottom-left:</strong> Specific humidity at 975 hPa (g/kg)</li>
            <li><strong>Bottom-right:</strong> Geopotential height at 500 hPa (m)</li>
          </ul>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
