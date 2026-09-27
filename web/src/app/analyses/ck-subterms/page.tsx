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

interface StatisticEntry {
  ep: string
  term_key: string
  term_label: string
  n: number
  mean: number
  median: number
  q25: number
  q75: number
}

interface ContrastEntry {
  subterm_key: string
  subterm_label: string
  contrast: string
  median_left: number
  median_right: number
  p_fdr: number
  significant: boolean
  effect_size_r: number
  effect_magnitude: string
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
  intensification_totals: StatisticEntry[]
  intensification_statistics: StatisticEntry[]
  contrasts: ContrastEntry[]
  figures: {
    vertical_profiles: string
    boxplots: string
    lifecycle: string
  }
}

function signed(value: number, digits = 2) {
  return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(digits)}`
}

function formatProbability(value: number) {
  return value < 0.001 ? value.toExponential(2) : value.toFixed(3)
}

function loadManifest(): CkSubtermsManifest | null {
  try {
    const manifest = readManifest<CkSubtermsManifest>('ck_subterms_manifest.json')
    return manifest.analysis === 'ck_subterms_corrected' &&
      manifest.population &&
      Array.isArray(manifest.intensification_totals) &&
      Array.isArray(manifest.intensification_statistics) &&
      Array.isArray(manifest.contrasts)
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

  // These corrected figures are committed under web/public/figures. Keeping
  // their URLs site-local prevents the optional global Supabase override from
  // pointing this page at objects that have not been uploaded to that bucket.
  return `/${path}`
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
  const statistics = [...manifest.intensification_totals, ...manifest.intensification_statistics]
  const statistic = (ep: string, term: string) => {
    const entry = statistics.find((row) => row.ep === ep && row.term_key === term)
    if (!entry) {
      throw new Error(`Missing intensification statistic for ${ep} ${term}`)
    }
    return entry
  }
  const dominancePercentage = (ep: string, term: string) =>
    manifest.dominance.find((entry) => entry.ep === ep && entry.subterm_key === term)?.percentage ?? 0

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
            formula={String.raw`C_K = \sum_{i=1}^{5} C_K^{(i)} = \int_{p_t}^{p_b}\frac{1}{g}\left[\sum_{i=1}^{5}T^{(i)}\right]_{\lambda\phi}\,dp`}
            terms={{
              'C_K < 0': 'the mean flow transfers kinetic energy to the eddy (K_Z → K_E)',
              'C_K > 0': 'the eddy transfers kinetic energy to the mean flow (K_E → K_Z)',
              '[·]_λφ': 'area-weighted horizontal mean',
            }}
            notes="For each cyclone and phase, the strongest mean-flow-to-eddy contribution is the most negative of the five vertically integrated subterms. Cases in which all five are positive are reported separately rather than being labelled as barotropically unstable. Results are descriptive population summaries; percentages are not hypothesis tests."
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
            Intensification-phase means
          </h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Pattern</th>
                  <th className="px-4 py-3">Total C<sub>K</sub></th>
                  {manifest.subterms.map((subterm) => (
                    <th key={subterm.key} className="px-4 py-3">
                      <InlineMath expr={subterm.symbol} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {epEntries.map(([ep]) => (
                  <tr key={ep}>
                    <td className="px-4 py-3 font-semibold text-slate-900">{ep}</td>
                    <td className="px-4 py-3">{signed(statistic(ep, 'Ck').mean)} W m⁻²</td>
                    {manifest.subterms.map((subterm) => (
                      <td key={subterm.key} className="px-4 py-3">
                        {signed(statistic(ep, subterm.key).mean)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            Subterm cells are in W m⁻². Negative values feed the cyclone-scale eddy; positive
            values return kinetic energy to the mean flow.
          </p>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Intensification contribution classification
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
          <h2 className="mb-4 text-lg font-bold text-slate-900">Physical interpretation</h2>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-xl border border-red-200 bg-red-50/50 p-5">
              <h3 className="font-bold text-red-800">EP1 — horizontal-shear supply</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Total <InlineMath expr="C_K" /> is {signed(statistic('EP1', 'Ck').mean)} W m⁻².
                Terms <InlineMath expr="C_K^{(B)}" /> ({signed(statistic('EP1', 'Ck_2').mean)})
                and <InlineMath expr="C_K^{(A)}" /> ({signed(statistic('EP1', 'Ck_1').mean)})
                provide the negative conversion. Term B is the strongest negative contribution
                in {dominancePercentage('EP1', 'Ck_2').toFixed(1)}% of cyclones.
              </p>
            </div>
            <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5">
              <h3 className="font-bold text-blue-800">EP2 — kinetic-energy export</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Total <InlineMath expr="C_K" /> reverses to {signed(statistic('EP2', 'Ck').mean)}
                W m⁻². The largest positive mean contribution is the vertical meridional-momentum
                term <InlineMath expr="C_K^{(E)}" /> ({signed(statistic('EP2', 'Ck_5').mean)}
                W m⁻²); {dominancePercentage('EP2', 'none').toFixed(1)}% of cyclones have all five
                subterms positive.
              </p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
              <h3 className="font-bold text-emerald-800">EP3 — opposing mechanisms</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                The near-zero total ({signed(statistic('EP3', 'Ck').mean)} W m⁻²) is a
                compensation: negative terms A and B ({signed(statistic('EP3', 'Ck_1').mean)} and{' '}
                {signed(statistic('EP3', 'Ck_2').mean)} W m⁻²) are offset mainly by positive term E
                ({signed(statistic('EP3', 'Ck_5').mean)} W m⁻²).
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Between-pattern contrasts
          </h2>
          <p className="mb-4 text-sm leading-relaxed text-slate-600">
            Pairwise Mann–Whitney tests use Benjamini–Hochberg correction across the 15
            intensification-phase comparisons. The effect is the rank-biserial correlation.
          </p>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Subterm</th>
                  <th className="px-4 py-3">Contrast</th>
                  <th className="px-4 py-3">Medians</th>
                  <th className="px-4 py-3">FDR p</th>
                  <th className="px-4 py-3">Effect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {manifest.contrasts.map((contrast) => (
                  <tr key={`${contrast.subterm_key}-${contrast.contrast}`}>
                    <td className="px-4 py-3 font-semibold text-slate-900">
                      {contrast.subterm_label}
                    </td>
                    <td className="px-4 py-3">{contrast.contrast}</td>
                    <td className="px-4 py-3">
                      {signed(contrast.median_left, 3)} / {signed(contrast.median_right, 3)}
                    </td>
                    <td className="px-4 py-3">
                      {contrast.significant ? <strong>{formatProbability(contrast.p_fdr)}</strong> : formatProbability(contrast.p_fdr)}
                    </td>
                    <td className="px-4 py-3">
                      {signed(contrast.effect_size_r, 3)} ({contrast.effect_magnitude})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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

        <ResultSummaryCallout type="result" title="Main result">
          <p>
            The Energy Patterns differ in barotropic mechanism, not only in amplitude. EP1 is
            sustained by strong negative horizontal-shear terms A and B; EP2 is dominated in the
            ensemble mean by positive vertical-momentum term E; and EP3 combines weaker opposing
            contributions that nearly cancel in the column total.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
