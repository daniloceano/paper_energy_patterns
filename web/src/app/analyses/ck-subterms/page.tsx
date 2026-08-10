import type { Metadata } from 'next'
import { TrendingDown } from 'lucide-react'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import FigurePanel from '@/components/analysis/FigurePanel'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import { ENERGY_PATTERNS } from '@/lib/constants'
import { readManifest } from '@/lib/server-utils'
import { figureUrl } from '@/lib/utils'
import InlineMath from '@/components/analysis/InlineMath'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import { SimpleTerms, InThisStudy } from '@/components/analysis/Didactic'

/**
 * Resolve a figure URL from the manifest (or fall back to a default path).
 *
 * The manifest may contain:
 *   • A full Supabase URL   → used as-is
 *   • A relative local path → passed through figureUrl() to prepend '/'
 *   • undefined             → fall back to figureUrl(fallback)
 */
function resolveFig(manifestPath: string | undefined, fallback: string): string {
  if (!manifestPath) return figureUrl(fallback)
  if (manifestPath.startsWith('http://') || manifestPath.startsWith('https://') || manifestPath.startsWith('/')) {
    return manifestPath
  }
  // Relative path (e.g. "figures/ck_subterms/xxx.png") → convert to absolute URL
  return figureUrl(manifestPath)
}

export const metadata: Metadata = {
  title: 'Ck Subterms Analysis — EP1 Barotropic Decomposition',
  description:
    'Decomposition of barotropic energy conversion (Ck) into its five vertical-level subterms for EP1 South Atlantic extratropical cyclones.',
}

interface SubtermInfo {
  symbol: string
  name: string
  katex?: string
  description: string
}

interface DominanceEntry {
  subterm_key: string
  symbol: string
  name: string
  description: string
  count: number
  percentage: number
}

interface LecAudit {
  source: string
  ep1_cases_source: string
  n_ep1_expected: number
  n_lec_directory_found: number
  n_with_ck_total_file: number
  n_with_all_ck_subterm_files: number
  n_usable_for_dominance: number
  mean_ck_new: number
  mean_subterm_sum: number
  note: string
}

interface CkSubtermsManifest {
  title: string
  phase: string
  phase_note: string
  sample_sizes: {
    ep1_total: number
    ep1_with_lec_dir: number
    ep1_with_ck_total_file: number
    ep1_with_all_ck_subterm_files: number
    ep1_with_lec: number
    valid_for_boxplots: number
    note: string
  }
  lec_audit?: LecAudit
  normalization_method?: {
    title: string
    formula: string
    steps: string[]
  }
  subterms: SubtermInfo[]
  dominance: DominanceEntry[]
  figures: Record<string, string>
}

function loadManifest(): CkSubtermsManifest | null {
  try {
    return readManifest<CkSubtermsManifest>('ck_subterms_manifest.json')
  } catch {
    return null
  }
}

export default function CkSubtermsPage() {
  const manifest = loadManifest()
  const n_ep1 = manifest?.sample_sizes.ep1_total ?? ENERGY_PATTERNS.EP1.count
  const n_lec = manifest?.sample_sizes.ep1_with_lec ?? 385
  const n_lec_dirs = manifest?.sample_sizes.ep1_with_lec_dir ?? n_lec
  const n_ck_subs = manifest?.sample_sizes.ep1_with_all_ck_subterm_files ?? n_lec
  const dominance = manifest?.dominance ?? []
  const lec_audit = manifest?.lec_audit

  const figures = {
    boxplots:         resolveFig(manifest?.figures?.boxplots,          'figures/ck_subterms/ck_subterms_boxplots.png'),
    genesis_density:  resolveFig(manifest?.figures?.genesis_density,   'figures/ck_subterms/ck_subterms_genesis_density.png'),
    genesis_normaldiff: resolveFig(manifest?.figures?.genesis_normaldiff, 'figures/ck_subterms/ck_subterms_genesis_normaldiff.png'),
    tracks:           resolveFig(manifest?.figures?.tracks,            'figures/ck_subterms/ck_subterms_tracks.png'),
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Ck Subterms Analysis"
        subtitle="EP1 — Barotropic Energy Conversion Decomposition"
        badge="LEC Audit"
        description={`Decomposition of the barotropic kinetic energy conversion (Ck) into five subterms for EP1 cyclones. Total EP1 population: N=${n_ep1}. Cyclones with complete, validated LEC subterm data (used for boxplots and dominance classification): N=${n_lec}. Genesis density and track panels use the full N=${n_ep1} population. Negative Ck indicates barotropic instability: mean flow transfers energy to eddies (K_Z → K_E).`}
      />

      <div className="space-y-10">
        {/* Scientific overview */}
        <ResultSummaryCallout type="info" title="Scientific Objective">
          <p>
            The barotropic conversion term C<sub>K</sub> represents the exchange of kinetic energy
            between cyclone-scale eddies and the background mean flow. In EP1 (the most energetically
            active cluster), C<sub>K</sub> is strongly <strong>negative</strong> during
            intensification (mean ≈ −16.5 W m⁻²), indicating{' '}
            <em>barotropic instability</em>: the mean flow transfers energy to the eddies (K<sub>Z</sub> → K<sub>E</sub>).
            EP1 cyclones are therefore strongly driven by barotropic instability. This analysis
            decomposes C<sub>K</sub>{' '}
            into five subterms (A–E) to identify which dynamical mechanism dominates this
            mean-to-eddy energy transfer during EP1 intensification, and whether genesis
            location is systematically linked to a particular subterm.
          </p>
        </ResultSummaryCallout>

        {/* LEC Audit metrics */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">LEC Results Audit</h2>
          <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-5 text-sm leading-relaxed text-slate-700 space-y-3">
            <p>
              Each EP1 cyclone is audited against its locally computed LEC results in{' '}
              <code className="rounded bg-white px-1 border border-emerald-200">results/ck_analysis/lec_results/</code>.
              Eligibility requires the presence and integrity of all six pressure-level CSV files
              ({' '}<code className="rounded bg-white px-1 border border-emerald-200">Ck_pressure_level.csv</code> and{' '}
              <code className="rounded bg-white px-1 border border-emerald-200">Ck_1..5_pressure_level.csv</code>)
              and at least one timestep within the intensification window.
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mt-3">
              {[
                { label: 'EP1 expected', value: n_ep1, note: 'full population' },
                { label: 'LEC dirs found', value: n_lec_dirs, note: `${Math.round(100 * n_lec_dirs / n_ep1)}% of EP1` },
                { label: 'With all Ck_1..5', value: n_ck_subs, note: `${Math.round(100 * n_ck_subs / n_ep1)}% of EP1` },
                { label: 'Valid for dominance', value: n_lec, note: `used in figures` },
              ].map((item) => (
                <div key={item.label} className="rounded-lg border border-emerald-200 bg-white p-3 text-center">
                  <p className="text-2xl font-bold text-emerald-700">{item.value}</p>
                  <p className="text-xs font-semibold text-slate-700 mt-0.5">{item.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{item.note}</p>
                </div>
              ))}
            </div>
            {lec_audit && (
              <p className="text-xs text-slate-500 mt-2">{lec_audit.note}</p>
            )}
          </div>
        </section>

        {/* Methods & Statistics */}
        <MethodsPanel summary="How the barotropic conversion is decomposed, how a dominant subterm is assigned to each cyclone, and how the genesis-density anomalies are normalised.">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="mb-3 font-semibold text-slate-900">Sign convention and subterm definition</h3>
            <SimpleTerms>
              <p>
                The sign of C<sub>K</sub> is the single most error-prone part of reading these
                figures. C<sub>K</sub> is defined as the conversion <em>from</em> eddy
                <em> to</em> mean-flow kinetic energy, so a <strong>negative</strong> value means
                energy flows the other way — the mean flow is feeding the eddy, which is
                barotropic instability and is what makes a cyclone grow. EP1 cyclones have
                large negative C<sub>K</sub>: the jet is doing work on the storm.
              </p>
            </SimpleTerms>
          </div>
          {/* Methodology */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-slate-900">Methodology</h2>
            <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600 space-y-3">
              <p>
                <strong>Sign convention (paper.tex):</strong>{' '}
                C<sub>K</sub> &lt; 0 → K<sub>Z</sub> → K<sub>E</sub> (mean flow transfers energy
                to the eddies; barotropic instability). C<sub>K</sub> &gt; 0 → K<sub>E</sub> → K<sub>Z</sub>{' '}
                (eddies transfer energy to mean flow). EP1 cyclones have large negative C<sub>K</sub>
                — they are strongly driven by barotropic instability (mean flow feeds eddies).
              </p>
              <p>
                <strong>Subterm definition (paper.tex Eq. C<sub>K</sub>):</strong> C<sub>K</sub> is
                vertically integrated and decomposed into five terms (a–e) arising from horizontal
                and vertical gradients of the background zonal and meridional wind (see the{' '}
                <em>C<sub>K</sub> Decomposition</em> section below for the full formula).
                Each term is vertically integrated over pressure levels using{' '}
                <InlineMath expr="\int_{p_b}^{p_t}\!\frac{1}{g}\,[\cdot]_{\lambda\phi}\,dp" />,
                where <InlineMath expr="g = 9.8\,\mathrm{m\,s^{-2}}" />.
              </p>
              <p>
                <strong>Phase:</strong> The <em>intensification</em> phase is used for all
                dominance classification. Intensification windows are taken from{' '}
                <code className="rounded bg-slate-100 px-1">results/ep_structure/ep1_cases.csv</code>.
              </p>
              <p>
                <strong>LEC audit:</strong> Cases are audited from the directories in{' '}
                <code className="rounded bg-slate-100 px-1">results/ck_analysis/lec_results/</code>.
                Eligibility depends on the presence and integrity of{' '}
                <code className="rounded bg-slate-100 px-1">Ck_pressure_level.csv</code> and{' '}
                <code className="rounded bg-slate-100 px-1">Ck_1…Ck_5_pressure_level.csv</code>.
                Dominance is only computed when all required files exist, are non-empty, and
                contain valid data within the intensification window.
              </p>
              <p>
                <strong>Sample sizes:</strong>{' '}
                Total EP1 population = <strong>N={n_ep1}</strong> (from{' '}
                <code className="rounded bg-slate-100 px-1">ep_structure/ep1_cases.csv</code>).
                Cyclones with complete, valid LEC output = <strong>N={n_lec}</strong>.
                Boxplots and dominance classification use N={n_lec}.
                The &#34;All EP1&#34; genesis density and track panels use the full N={n_ep1} population.
              </p>
            </div>
          </section>

          {/* Normalization methodology — mathematical formulation */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-slate-900">
              Normalization Methodology — Genesis Density Anomaly (Figure 3)
            </h2>

            {/* Step 1: KDE genesis density field */}
            <div className="mb-4">
              <p className="mb-2 text-sm font-semibold text-slate-700">
                Step 1 — Kernel Density Estimation (Hoskins &amp; Hodges 2005)
              </p>
              <FormulaBlock
                formula={String.raw`\rho(\varphi,\lambda) = \sum_{i=1}^{N} K_\sigma\!\left(d(\varphi,\lambda;\,\varphi_i,\lambda_i)\right)`}
                terms={{
                  'd': 'haversine (great-circle) distance between grid point (φ,λ) and genesis point i',
                  'K_σ': 'Gaussian kernel with bandwidth σ = 0.05 rad',
                  'N': `number of cyclones in the set (N = ${n_ep1} for all-EP1; N = N_k for subterm-k subset)`,
                }}
                notes={`Two density fields are computed: ρ_all(φ,λ) from all N=${n_ep1} EP1 genesis points, and ρ_k(φ,λ) from the N_k genesis points of cyclones where subterm k is dominant.`}
              />
            </div>

            {/* Step 2: Min-Max normalization */}
            <div className="mb-4">
              <p className="mb-2 text-sm font-semibold text-slate-700">
                Step 2 — Min-Max Normalization (positive values only)
              </p>
              <FormulaBlock
                formula={String.raw`\hat{\rho}(\varphi,\lambda) = \begin{cases} \dfrac{\rho(\varphi,\lambda) - \rho_{\min}^{+}}{\rho_{\max}^{+} - \rho_{\min}^{+}} & \text{if } \rho(\varphi,\lambda) > 0 \\ 0 & \text{otherwise} \end{cases}`}
                terms={{
                  'ρ_min⁺': 'minimum density over all grid points where ρ > 0',
                  'ρ_max⁺': 'maximum density over all grid points where ρ > 0',
                }}
                notes="Applied independently to ρ_all → ρ̂_all and to each ρ_k → ρ̂_k. Zero and negative density values are clamped to 0."
              />
            </div>

            {/* Step 3: Relative anomaly */}
            <div className="mb-4">
              <p className="mb-2 text-sm font-semibold text-slate-700">
                Step 3 — Relative Genesis Density Anomaly
              </p>
              <FormulaBlock
                formula={String.raw`\Delta\hat{\rho}_k(\varphi,\lambda) = \hat{\rho}_k(\varphi,\lambda) - \hat{\rho}_{\mathrm{all}}(\varphi,\lambda)`}
                notes="Positive (red): cyclones dominated by subterm k show preferential genesis relative to all EP1. Negative (blue): suppressed genesis. A shared diverging colorbar spans [−Δmax, +Δmax] where Δmax = max|Δρ̂_k| across all subterm panels."
              />
            </div>

            {/* Interpretation note */}
            <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-xs text-slate-600 leading-relaxed">
              <strong>Interpretation note:</strong> The normalization removes differences in subset size (N<sub>k</sub> varies from 0 to {n_lec} depending on the dominant subterm) and differences in absolute genesis density amplitude, allowing direct spatial comparison of preferred genesis regions across subterms. A value of +1 indicates that the subterm subset&apos;s genesis density is at maximum relative to its own spatial range; a value of 0 indicates the background EP1 level; a value of −1 indicates complete suppression relative to the all-EP1 baseline.
            </div>
          </section>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">Statistical treatment — descriptive, not inferential</h3>
            <p className="mt-2 text-sm text-slate-600">
              Each cyclone is assigned a <strong>dominant subterm</strong>: the subterm with
              the most negative intensification-phase mean, i.e. the one contributing most
              strongly to eddy growth. A <strong>dominance margin</strong> — the gap between
              the leading subterm and the runner-up — records how clear-cut that assignment
              was. The reported percentages are then simple frequencies of the dominant
              subterm across the population.
            </p>
            <p className="mt-3 text-sm text-slate-600">
              No hypothesis test is applied in this analysis, and none of the percentages
              carries a <em>p</em>-value. The boxplots show the full distribution of each
              subterm rather than a mean with an error bar, precisely so that the spread and
              the overlap between subterms remain visible without implying a formal test.
            </p>
            <InThisStudy>
              <p>
                This matters for how the dominance percentages should be read. That term E
                leads in a plurality of EP1 cyclones, followed by term B and then term A,
                describes <em>this</em> population; it is not a claim that term E is
                significantly more often dominant than term B. Where a cyclone&apos;s
                dominance margin is small, the leading subterm is close to arbitrary, and
                the physically meaningful statement is that several subterms contribute
                comparably.
              </p>
            </InThisStudy>
          </div>
        </MethodsPanel>

        {/* Full C_K formula + subterm definitions */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            C<sub>K</sub> Decomposition — Full Formula (paper.tex Eq.&nbsp;C<sub>K</sub>)
          </h2>
          <FormulaBlock
            label="Barotropic conversion C_K (vertically integrated)"
            formula={
              String.raw`C_K = \int_{p_b}^{p_t} \frac{1}{g}\Bigl[\,T^{(a)} + T^{(b)} + T^{(c)} + T^{(d)} + T^{(e)}\,\Bigr]_{\!\lambda\phi}\,dp`
            }
            terms={{
              '[·]_λφ': 'global area-weighted mean over longitude (λ) and latitude (φ)',
              'g': 'gravitational acceleration (9.8 m s⁻²)',
              'p_b, p_t': 'lower and upper pressure bounds of the integration',
            }}
            notes="Notation: [u]_λ = zonal mean of u; (u)_λ = eddy component (deviation from zonal mean); ω = vertical velocity in pressure coordinates; a = Earth radius."
          />

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {(manifest?.subterms ?? []).map((s, i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs">
                    {String.fromCharCode(65 + i)}
                  </span>
                  <span className="text-sm font-semibold text-slate-800">
                    <InlineMath expr={s.symbol} />
                  </span>
                </div>
                {s.katex && (
                  <div className="mb-2 overflow-x-auto rounded bg-slate-50 px-2 py-1.5 text-sm">
                    <InlineMath expr={`\\displaystyle ${s.katex}`} />
                  </div>
                )}
                <p className="text-xs text-slate-500 leading-relaxed">{s.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Dominance distribution */}
        {dominance.length > 0 && (
          <section>
            <h2 className="mb-4 text-lg font-bold text-slate-900">
              Dominance Distribution (N={n_lec} cyclones with valid LEC data)
            </h2>
            <div className="grid gap-3 sm:grid-cols-3">
              {dominance.filter((d) => d.count > 0).map((d) => (
                <div
                  key={d.subterm_key}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-indigo-700"><InlineMath expr={d.symbol} /></span>
                    <TrendingDown className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="text-2xl font-bold text-slate-900">{d.count}</p>
                  <p className="text-xs text-slate-500">{d.percentage}% of cyclones with valid LEC data</p>
                  <p className="mt-1 text-xs text-slate-400 leading-relaxed">{d.name}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Figure 1 — Combined Boxplots */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 1 — C<sub>K</sub> Boxplots: Subterms (a) and Total (b)</h2>
          <FigurePanel
            src={figures.boxplots}
            alt="Combined boxplot: C_K subterms (a-e) in left panel, total C_K in right panel"
            caption={`Two-panel figure. Left panel (a): distribution of each C_K subterm (a–e) during the intensification phase (N=${n_lec} cyclones with valid LEC data). Right panel (b): total C_K. Both panels share W m⁻² on the y-axis but are independently scaled. Negative values indicate K_Z → K_E energy transfer (barotropic instability). Whiskers = 5th–95th percentile.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 2 — Genesis density maps */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 2 — Genesis Density by Dominant Subterm</h2>
          <FigurePanel
            src={figures.genesis_density}
            alt="Genesis density maps: all EP1 and subsets by dominant Ck subterm"
            caption={`Multi-panel genesis density maps (KDE, Hoskins & Hodges 2005 method). Top-left: all EP1 cyclones (N=${n_ep1}, full population). Remaining panels: cyclones where the named subterm is dominant during intensification (N per panel shown in title). Per-panel colorbars; units: cyclones / 10⁶ km² / year.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 3 — Normalized difference maps */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 3 — Normalized Genesis Density Anomaly</h2>
          <FigurePanel
            src={figures.genesis_normaldiff}
            alt="Normalized-difference genesis density maps relative to all EP1"
            caption="Normalized genesis density anomaly: minmax_normalize(dominant-subterm density) − minmax_normalize(all-EP1 density). Positive (red) regions indicate preferential genesis for a given subterm relative to the full EP1 population; negative (blue) regions indicate suppressed genesis. Same normalization as Figure 6 of the paper."
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 4 — Full tracks */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 4 — EP1 Full Tracks</h2>
          <FigurePanel
            src={figures.tracks}
            alt="Full tracks of all EP1 systems and subsets by dominant Ck subterm"
            caption={`Full cyclone tracks for all EP1 systems (N=${n_ep1}, full population) and subsets where each subterm dominates (N per panel shown in title). Background tracks shown in grey. Gold segments = intensification phase; green dots = genesis; red crosses = lysis.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Data source */}
        <ResultSummaryCallout type="info" title="Data Sources">
          <ul className="space-y-1 text-sm">
            <li>
              <strong>LEC results (locally computed energetics):</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/ck_analysis/lec_results/</code>{' '}
              — {n_lec} EP1 cyclones with complete Ck subterms at vertical levels (out of {n_ep1} total EP1)
            </li>
            <li>
              <strong>Intensification phases:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/ep_structure/ep1_cases.csv</code>
              {' '}(produced by <code className="rounded bg-slate-100 px-1">scripts/ep_structure_analysis/</code>)
            </li>
            <li>
              <strong>Audit files:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/ck_subterms/lec_audit_per_cyclone.csv</code>,{' '}
              <code className="rounded bg-slate-100 px-1">lec_audit_summary.json</code>,{' '}
              <code className="rounded bg-slate-100 px-1">lec_audit_report.txt</code>
            </li>
            <li>
              <strong>Tracks:</strong> ERA5-based tracking database via{' '}
              <code className="rounded bg-slate-100 px-1">scripts/utils/load_data.py</code>
            </li>
          </ul>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}

