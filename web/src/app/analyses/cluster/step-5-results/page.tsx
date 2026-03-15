import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { ENERGY_PATTERNS } from '@/lib/constants'

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
        description="Summary of identified Energy Patterns with their physical characteristics, including intensity metrics, geographical distribution, and seasonality."
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
                      N = {ep.count} · {ep.percentage}%
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600">{ep.description}</p>
                <p className="mt-2 text-xs font-medium text-slate-400">
                  Mean C<sub>k</sub> = {ep.meanCk} W m⁻²
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Publication figures */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Publication Figures
          </h2>
          <div className="space-y-4">
            <FigurePanel
              src="/api/figures?path=figures/main/4_lps_combined.png"
              alt="Combined Lorenz Phase Space for EP1, EP2, EP3"
              caption="Combined LPS diagram showing the three Energy Patterns in both conversion and import spaces. Publication-ready figure."
              source="figures/main/4_lps_combined.png"
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FigurePanel
                src="/api/figures?path=figures/main/5_ep_intensity_seasonality_trends.png"
                alt="EP intensity, seasonality, and trends"
                caption="Intensity metrics, seasonal distribution, and interannual trends by Energy Pattern."
                source="figures/main/5_ep_intensity_seasonality_trends.png"
              />
              <FigurePanel
                src="/api/figures?path=figures/main/6_ep_genesis_density_kde.png"
                alt="Genesis density KDE maps by EP"
                caption="Kernel density estimation of genesis locations for each Energy Pattern."
                source="figures/main/6_ep_genesis_density_kde.png"
              />
            </div>
          </div>
        </section>

        {/* Extension point callout */}
        <ResultSummaryCallout type="warning" title="Future Extension — Detailed Results">
          <p>
            This section will be expanded in a future iteration with additional results from
            the exploratory analysis pipeline (<code>scripts/exploratory/</code>). Planned additions:
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            <li>Detailed EP1 vs EP2 intensity comparison (vorticity, pressure, deepening rate)</li>
            <li>Seasonal and interannual variability breakdown</li>
            <li>Genesis region analysis by EP</li>
            <li>Individual EP Lorenz Phase Space diagrams from <code>figures/exploratory/lps_diagrams_by_ep/</code></li>
            <li>Case study examples (three most intense cyclones)</li>
            <li>Density diagrams with diabatic generation (Ge)</li>
          </ul>
          <p className="mt-2 text-xs text-slate-500">
            Available figures: <code>figures/exploratory/lps_diagrams_by_ep/</code> (18 files),{' '}
            <code>figures/exploratory/ep_analysis/</code> (4 plots + CSV),{' '}
            <code>figures/exploratory/density_ge/</code> (20+ plots).
          </p>
        </ResultSummaryCallout>

        <ResultSummaryCallout type="result" title="Summary">
          <p>
            The cluster analysis successfully identifies three physically distinct Energy Patterns
            from {(3820).toLocaleString()} South Atlantic cyclones. EP1 (11.6%) represents the most
            energetically active systems, EP2 (25.6%) captures intermediate externally-forced cyclones,
            and EP3 (62.7%) the weak climatological background. These patterns form the basis for
            the subsequent composite structure analysis.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
