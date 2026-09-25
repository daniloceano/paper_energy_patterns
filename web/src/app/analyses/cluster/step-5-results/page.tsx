import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
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

        <ResultSummaryCallout type="result" title="Summary">
          <p>
            The cluster analysis successfully identifies three physically distinct Energy Patterns
            from {Object.values(ENERGY_PATTERNS).reduce((sum, ep) => sum + ep.count, 0).toLocaleString()}{' '}
            South Atlantic cyclones. EP1 contains {ENERGY_PATTERNS.EP1.percentage.toFixed(1)}%,
            EP2 {ENERGY_PATTERNS.EP2.percentage.toFixed(1)}%, and EP3{' '}
            {ENERGY_PATTERNS.EP3.percentage.toFixed(1)}%. Their names encode the descending
            intensification-phase |C<sub>a</sub>| + |C<sub>k</sub>| ranking; causal atmospheric
            interpretations are evaluated separately in later analyses.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
