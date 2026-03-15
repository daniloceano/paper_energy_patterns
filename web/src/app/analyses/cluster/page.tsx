import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import StepTimeline from '@/components/analysis/StepTimeline'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { CLUSTER_STEPS, ENERGY_PATTERNS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Cluster Analysis',
  description:
    'PCA + K-Means clustering of Lorenz Energy Cycle diagnostics to identify three Energy Patterns.',
}

export default function ClusterPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Cluster Analysis"
        subtitle="Energy Pattern Classification"
        badge="Analysis Pipeline"
        description="South Atlantic extratropical cyclones are classified into three Energy Patterns (EP1, EP2, EP3) using PCA-based K-Means clustering on 7 Lorenz Energy Cycle terms across 4 lifecycle phases. The pipeline processes 3,820 cyclones with complete lifecycles from 1979–2020."
      />

      <div className="flex gap-10">
        {/* Sidebar timeline */}
        <div className="hidden w-64 shrink-0 lg:block">
          <div className="sticky top-24">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Analysis Steps
            </h3>
            <StepTimeline
              steps={CLUSTER_STEPS.map((s) => ({
                number: s.number,
                title: s.title,
                shortTitle: s.shortTitle,
                href: `/analyses/cluster/${s.slug}`,
                completed: true,
              }))}
            />
          </div>
        </div>

        {/* Main content */}
        <div className="min-w-0 flex-1 space-y-8">
          <ResultSummaryCallout type="result" title="Key Result">
            <p>
              Three distinct Energy Patterns were identified with k = 3 (optimal via
              5-index ensemble). <strong>EP1</strong> (N={ENERGY_PATTERNS.EP1.count},{' '}
              {ENERGY_PATTERNS.EP1.percentage}%): strong barotropic and baroclinic
              conversions. <strong>EP2</strong> (N={ENERGY_PATTERNS.EP2.count},{' '}
              {ENERGY_PATTERNS.EP2.percentage}%): intermediate, externally forced.{' '}
              <strong>EP3</strong> (N={ENERGY_PATTERNS.EP3.count},{' '}
              {ENERGY_PATTERNS.EP3.percentage}%): weak background energetics.
            </p>
          </ResultSummaryCallout>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-slate-900">Pipeline Overview</h2>
            <p className="text-sm leading-relaxed text-slate-600">
              The cluster analysis follows a five-step pipeline. Each step builds on the
              previous one, from raw energy data filtering through PCA dimensionality
              reduction to final K-Means classification and Lorenz Phase Space
              visualisation.
            </p>
          </div>

          {/* Steps grid */}
          <div className="grid gap-4 sm:grid-cols-2">
            {CLUSTER_STEPS.map((step) => (
              <a
                key={step.slug}
                href={`/analyses/cluster/${step.slug}`}
                className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                    {step.number}
                  </span>
                  <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600">
                    {step.shortTitle}
                  </h3>
                </div>
                <p className="text-sm text-slate-500">{step.description}</p>
                <p className="mt-2 text-xs text-slate-400">
                  {step.figures.length} figure(s) · {step.outputs.length} output(s)
                </p>
              </a>
            ))}
          </div>

          {/* Mobile timeline */}
          <div className="lg:hidden">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">
              Step Navigation
            </h3>
            <StepTimeline
              steps={CLUSTER_STEPS.map((s) => ({
                number: s.number,
                title: s.title,
                shortTitle: s.shortTitle,
                href: `/analyses/cluster/${s.slug}`,
                completed: true,
              }))}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
