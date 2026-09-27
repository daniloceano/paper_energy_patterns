import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { ENERGY_PATTERNS } from '@/lib/constants'
import exploratoryData from '@/content/energy_pattern_exploratory.json'

const EP_IDS = ['EP1', 'EP2', 'EP3'] as const

export const metadata: Metadata = {
  title: 'Step 5 — Results',
}

export default function Step5Page() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Results & Summary"
        subtitle="Step 5 of 5"
        badge="Cluster Analysis"
        description="Summary of the corrected Energy Pattern classification, its population sizes, and its intensification-phase conversion centroids."
      />

      <div className="space-y-8">
        {/* EP overview cards */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Energy Pattern Profiles
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {Object.values(ENERGY_PATTERNS).map((ep) => (
              <div
                key={ep.id}
                className="rounded-xl border-l-4 bg-white p-5 shadow-sm"
                style={{ borderLeftColor: ep.color }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-white"
                    style={{ backgroundColor: ep.color }}
                  >
                    {ep.id}
                  </span>
                  <div>
                    <p className="text-sm font-bold text-slate-900">{ep.id}</p>
                    <p className="text-xs text-slate-500">
                      N = {ep.count.toLocaleString()} · {ep.percentage.toFixed(1)}%
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600">{ep.description}</p>
                <p className="mt-2 text-xs font-medium text-slate-400">
                  C<sub>a,int</sub> = {ep.meanCa.toFixed(2)} · C<sub>k,int</sub> ={' '}
                  {ep.meanCk.toFixed(2)} W m⁻²
                </p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-bold text-slate-900">
            Intensity, Seasonality &amp; Trends
          </h2>
          <p className="mb-4 text-sm leading-relaxed text-slate-600">
            These diagnostics use the same 3,820 cyclones and corrected EP assignments as the
            clustering above. Intensity is the maximum track vorticity magnitude; season is defined
            at genesis; trends use annual counts from 1979–2020.
          </p>
          <div className="mb-4 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Pattern</th>
                  <th className="px-4 py-3">Mean maximum intensity</th>
                  <th className="px-4 py-3">Genesis peak</th>
                  <th className="px-4 py-3">Annual-count trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {EP_IDS.map((epId) => {
                  const result = exploratoryData[epId]
                  return (
                    <tr key={epId}>
                      <td className="px-4 py-3 font-semibold text-slate-900">{epId}</td>
                      <td className="px-4 py-3">
                        {result.intensity.mean.toFixed(2)} × 10⁻⁵ s⁻¹
                      </td>
                      <td className="px-4 py-3">
                        {result.peakSeason} ({result.peakSeasonPercent.toFixed(1)}%)
                      </td>
                      <td className="px-4 py-3">
                        Not significant (p = {result.trend.pValue.toFixed(3)})
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <FigurePanel
            src="/figures/main/ep_intensity_seasonality_trends.png"
            alt="Corrected EP intensity distributions, seasonal genesis frequencies, and annual-count trends"
            caption="Figure 6. Maximum intensity, seasonal genesis distribution, and interannual occurrence for the corrected EP classification. Dashed trend lines are not significant at p < 0.05."
            source="figures/main/ep_intensity_seasonality_trends.png"
          />
        </section>

        <section>
          <h2 className="mb-2 text-lg font-bold text-slate-900">
            Genesis Density
          </h2>
          <p className="mb-4 text-sm leading-relaxed text-slate-600">
            The all-cyclone panel shows absolute kernel density. Each EP panel shows its normalized
            density minus the normalized all-cyclone density, so red regions indicate relative
            enhancement and blue regions relative reduction.
          </p>
          <FigurePanel
            src="/figures/main/ep_genesis_density_kde.png"
            alt="Corrected kernel density estimates of cyclone genesis for all cyclones and each Energy Pattern"
            caption="Figure 7. Kernel density estimate of genesis locations for all cyclones and EP-relative normalized anomalies for EP1, EP2, and EP3."
            source="figures/main/ep_genesis_density_kde.png"
          />
        </section>

        <ResultSummaryCallout type="result" title="Summary">
          <p>
            The cluster analysis successfully identifies three physically distinct Energy Patterns
            from {Object.values(ENERGY_PATTERNS).reduce((sum, ep) => sum + ep.count, 0).toLocaleString()}{' '}
            South Atlantic cyclones. EP1 contains {ENERGY_PATTERNS.EP1.percentage.toFixed(1)}%,
            EP2 {ENERGY_PATTERNS.EP2.percentage.toFixed(1)}%, and EP3{' '}
            {ENERGY_PATTERNS.EP3.percentage.toFixed(1)}%. Their names encode the descending
            intensification-phase |C<sub>a</sub>| + |C<sub>k</sub>| ranking. EP1 and EP2 have
            comparable mean maximum intensity (9.01 and 9.15 × 10⁻⁵ s⁻¹), whereas EP3
            is weaker (6.43 × 10⁻⁵ s⁻¹). EP1 and EP2 peak in JJA, while EP3 peaks in
            DJF. No EP has a significant monotonic trend in annual occurrence at p &lt; 0.05.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
