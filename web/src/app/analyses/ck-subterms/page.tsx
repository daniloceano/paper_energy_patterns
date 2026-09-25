import type { Metadata } from 'next'
import { TrendingDown } from 'lucide-react'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import InlineMath from '@/components/analysis/InlineMath'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import { readManifest } from '@/lib/server-utils'
import { figureUrl } from '@/lib/utils'

export const metadata: Metadata = {
  title: 'Corrected Ck Subterms — All Energy Patterns',
  description:
    'Corrected decomposition of barotropic energy conversion into five subterms for all South Atlantic cyclone Energy Patterns.',
}

interface SubtermInfo {
  key: string
  symbol: string
  name: string
  description: string
}

interface DominanceEntry {
  ep: string
  subterm_key: string
  subterm_label: string
  count: number
  total: number
  percentage: number
  description: string
}

interface CkSubtermsManifest {
  analysis: 'ck_subterms_corrected'
  title: string
  phase: string
  source_cache: string
  population: {
    total: number
    energy_patterns: Record<string, number>
    phase_rows: number
    worst_closure_relative: number
    closure_tolerance: number
  }
  sign_convention: string
  subterms: SubtermInfo[]
  dominance: DominanceEntry[]
  figures: {
    vertical_profiles: string
    boxplots: string
    lifecycle: string
  }
}

function loadManifest(): CkSubtermsManifest | null {
  try {
    const manifest = readManifest<CkSubtermsManifest>('ck_subterms_manifest.json')
    return manifest.analysis === 'ck_subterms_corrected' && manifest.population
      ? manifest
      : null
  } catch {
    return null
  }
}

function resolveFigure(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('/')) {
    return path
  }
  return figureUrl(path)
}

export default function CkSubtermsPage() {
  const manifest = loadManifest()

  if (!manifest) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <Breadcrumbs />
        <AnalysisHero
          title="Ck Subterms Analysis"
          badge="Corrected Reanalysis"
          description="The corrected all-pattern results are being regenerated. The previous partial EP1 analysis has been withdrawn to prevent legacy values from being presented as current results."
        />
        <ResultSummaryCallout type="warning" title="Corrected manifest not available">
          <p>Run the corrected Ck pipeline and the website extraction step before publishing this page.</p>
        </ResultSummaryCallout>
      </div>
    )
  }

  const epEntries = Object.entries(manifest.population.energy_patterns).sort(
    ([left], [right]) => left.localeCompare(right),
  )
  const dominanceByEp = epEntries.map(([ep]) => ({
    ep,
    rows: manifest.dominance.filter((entry) => entry.ep === ep),
  }))

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Ck Subterms Analysis"
        subtitle="Corrected Barotropic Conversion — All Energy Patterns"
        badge="Complete Corrected Population"
        description={`The corrected Lorenz Energy Cycle rerun decomposes Ck into five physical contributions for all ${manifest.population.total.toLocaleString()} cyclones. Dominance is evaluated during intensification and compared across every Energy Pattern.`}
      />

      <div className="space-y-10">
        <ResultSummaryCallout type="result" title="Population and numerical closure">
          <p>
            All {manifest.population.total.toLocaleString()} corrected cyclones are included across{' '}
            {manifest.population.phase_rows.toLocaleString()} cyclone-phase records. The largest
            relative residual in <InlineMath expr="C_K=\sum_{i=1}^{5}C_K^{(i)}" /> is{' '}
            {manifest.population.worst_closure_relative.toExponential(2)}, below the acceptance
            tolerance of {manifest.population.closure_tolerance.toExponential(1)}.
          </p>
        </ResultSummaryCallout>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Corrected population</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {epEntries.map(([ep, count]) => (
              <div key={ep} className="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm">
                <p className="text-2xl font-bold text-indigo-700">{count.toLocaleString()}</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">{ep}</p>
                <p className="text-xs text-slate-400">
                  {(100 * count / manifest.population.total).toFixed(1)}% of the population
                </p>
              </div>
            ))}
          </div>
        </section>

        <MethodsPanel summary="How the corrected pressure-level terms are integrated, checked, and classified during cyclone intensification.">
          <FormulaBlock
            label="Barotropic conversion decomposition"
            formula={String.raw`C_K = \sum_{i=1}^{5} C_K^{(i)} = \int_{p_b}^{p_t}\frac{1}{g}\left[\sum_{i=1}^{5}T^{(i)}\right]_{\lambda\phi}\,dp`}
            terms={{
              'C_K < 0': 'the mean flow transfers kinetic energy to the eddy (K_Z → K_E)',
              'C_K > 0': 'the eddy transfers kinetic energy to the mean flow (K_E → K_Z)',
              '[·]_λφ': 'area-weighted horizontal mean',
            }}
            notes="For each cyclone and phase, the dominant growth contribution is the most negative of the five vertically integrated subterms. Results are descriptive population summaries; dominance percentages are not hypothesis tests."
          />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {manifest.subterms.map((subterm) => (
              <div key={subterm.key} className="rounded-xl border border-slate-200 bg-white p-4">
                <p className="font-semibold text-indigo-700">
                  <InlineMath expr={subterm.symbol} /> — {subterm.name}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">{subterm.description}</p>
              </div>
            ))}
          </div>
        </MethodsPanel>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Dominant intensification mechanism
          </h2>
          <div className="grid gap-5 lg:grid-cols-3">
            {dominanceByEp.map(({ ep, rows }) => (
              <div key={ep} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="mb-4 text-base font-bold text-slate-900">{ep}</h3>
                <div className="space-y-3">
                  {rows.map((entry) => (
                    <div key={entry.subterm_key}>
                      <div className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-medium text-slate-700">{entry.subterm_label}</span>
                        <span className="flex items-center gap-1 font-semibold text-indigo-700">
                          <TrendingDown className="h-3.5 w-3.5" />
                          {entry.percentage.toFixed(1)}%
                        </span>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
                        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${entry.percentage}%` }} />
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        {entry.count.toLocaleString()} of {entry.total.toLocaleString()} cyclones
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Vertical structure</h2>
          <FigurePanel
            src={resolveFigure(manifest.figures.vertical_profiles)}
            alt="Corrected vertical profiles of total Ck and its five subterms for every Energy Pattern"
            caption="Ensemble-mean pressure-level profiles during intensification. Each panel shows one Energy Pattern; negative contributions transfer kinetic energy from the mean flow to the cyclone-scale eddy."
            source="scripts/ck_subterms_analysis/step3_subterm_figures.py"
          />
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Integrated distributions</h2>
          <FigurePanel
            src={resolveFigure(manifest.figures.boxplots)}
            alt="Corrected distributions of integrated Ck subterms by Energy Pattern"
            caption="Vertically integrated intensification-phase subterms for all corrected cyclones, grouped by Energy Pattern. Boxes are notched and outliers are omitted from display only."
            source="scripts/ck_subterms_analysis/step3_subterm_figures.py"
          />
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Lifecycle evolution</h2>
          <FigurePanel
            src={resolveFigure(manifest.figures.lifecycle)}
            alt="Corrected lifecycle evolution of Ck and its five subterms for every Energy Pattern"
            caption="Ensemble-mean total Ck and subterm contributions from genesis through decay for each corrected Energy Pattern."
            source="scripts/ck_subterms_analysis/step3_subterm_figures.py"
          />
        </section>

        <ResultSummaryCallout type="info" title="Provenance">
          <p>
            Values come exclusively from the complete corrected LEC rerun and its frozen phase
            windows. The page refuses partial products or a clustering manifest whose source cache
            is not marked as corrected.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
