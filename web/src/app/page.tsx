import Link from 'next/link'
import {
  BarChart3,
  Layers,
  Database,
  BookOpen,
  Microscope,
  Activity,
  CloudLightning,
  Code2,
  FileCheck2,
  FileClock,
  FileWarning,
  Workflow,
  ArrowRight,
  BetweenVerticalStart,
  GitCompareArrows,
  GitBranch,
  Tornado,
  TrendingDown,
} from 'lucide-react'
import { ENERGY_PATTERNS, DATASET_STATS } from '@/lib/constants'

const METHODOLOGICAL_FLOW = [
  {
    step: '1',
    title: 'Tracks & Study Sample',
    desc: 'Select 6,789 cyclone tracks with genesis in ARG, LA-PLATA, and SE-BR from the 1979–2020 catalogue.',
    icon: Database,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Included in draft',
    manuscriptStatus: 'included',
  },
  {
    step: '2',
    title: 'Lifecycle Normalisation',
    desc: 'Detect incipient, intensification, mature, and decay phases; retain 3,820 cyclones with a complete standard lifecycle.',
    icon: Activity,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Included in draft',
    manuscriptStatus: 'included',
  },
  {
    step: '3',
    title: 'Corrected LEC Diagnostics',
    desc: 'Compute seven eddy-development terms in a storm-following 15° × 15° domain and average them by lifecycle phase.',
    icon: BarChart3,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Revision required',
    manuscriptStatus: 'revision',
  },
  {
    step: '4',
    title: 'PCA + K-Means Classification',
    desc: 'Standardise 28 phase-resolved features, retain 15 principal components, select k = 3, and assign EP1, EP2, and EP3.',
    icon: GitBranch,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Revision required',
    manuscriptStatus: 'revision',
  },
  {
    step: '5',
    title: 'Energy-Pattern Climatology',
    desc: 'Characterise lifecycle energetics, intensity, seasonality, trends, and genesis-density differences for each Energy Pattern.',
    icon: Microscope,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Revision required',
    manuscriptStatus: 'revision',
  },
  {
    step: '6',
    title: 'Vertical Structure & Ck Subterms',
    desc: 'Resolve corrected Ca and Ck pressure-level profiles and decompose Ck into five mechanisms for EP1, EP2, EP3, and EPALL.',
    icon: Layers,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Revision required',
    manuscriptStatus: 'revision',
  },
  {
    step: '7',
    title: 'Storm-Centred ERA5 Composites',
    desc: 'For 2,733 cyclones with intensification lasting at least 24 h, compare EP-relative dynamical fields on a 30° × 30° grid.',
    icon: Layers,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Included in draft',
    manuscriptStatus: 'included',
  },
  {
    step: '8',
    title: 'LEC–Field Dependence',
    desc: 'Relate LEC terms to scalar features derived from the ERA5 fields using Pearson, Spearman, PREDEP, and EP contrasts.',
    icon: Activity,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Included in draft',
    manuscriptStatus: 'included',
  },
  {
    step: '9',
    title: 'Cyclone Phase Space',
    desc: 'Classify thermal structure and persistent phase transitions for 6,776 cyclones, then compare their occurrence across EPs.',
    icon: GitBranch,
    code: 'Implemented',
    codeStatus: 'complete',
    manuscript: 'Integration pending',
    manuscriptStatus: 'missing',
  },
  {
    step: '10',
    title: 'Explosive Cyclones',
    desc: 'Derive storm-centre pressure and normalized deepening rate to compare bomb frequency, severity, and spatial density across EPs.',
    icon: CloudLightning,
    code: 'Full run pending',
    codeStatus: 'pending',
    manuscript: 'Integration pending',
    manuscriptStatus: 'missing',
  },
] as const

const CODE_STATUS_STYLES = {
  complete: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  pending: 'border-amber-200 bg-amber-50 text-amber-700',
} as const

const MANUSCRIPT_STATUS_STYLES = {
  included: 'border-sky-200 bg-sky-50 text-sky-700',
  revision: 'border-amber-200 bg-amber-50 text-amber-700',
  missing: 'border-rose-200 bg-rose-50 text-rose-700',
} as const

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="border-b border-slate-200 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 px-4 py-20 text-white sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <span className="mb-4 inline-block rounded-full bg-indigo-500/20 px-4 py-1.5 text-sm font-medium text-indigo-300">
            Interactive Research Explorer
          </span>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Energetic Patterns of Cyclones
            <br />
            <span className="text-indigo-400">
              in the Southwestern Atlantic
            </span>
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-relaxed text-slate-300">
            Extratropical cyclones in the South Atlantic exhibit distinct energetic
            signatures during their lifecycle. Using <strong>Lorenz Energy Cycle</strong>{' '}
            diagnostics on {DATASET_STATS.totalCyclones.toLocaleString()} cyclones over{' '}
            {DATASET_STATS.years} years ({DATASET_STATS.period}), we classify them into
            three <strong>Energy Patterns</strong> (EP1, EP2, EP3) via PCA-based K-Means
            clustering, then characterise their atmospheric structure through ERA5
            composite analysis.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/analyses"
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-indigo-700"
            >
              Explore Analyses
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/data-references"
              className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/20"
            >
              Data &amp; References
            </Link>
          </div>
        </div>
      </section>

      {/* Key numbers */}
      <section className="border-b border-slate-200 bg-slate-50 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-5xl grid-cols-2 gap-6 sm:grid-cols-4">
          {[
            { value: DATASET_STATS.filteredCyclones.toLocaleString(), label: 'Cyclones analysed' },
            { value: DATASET_STATS.years.toString(), label: 'Years of data' },
            { value: '7', label: 'Energy terms' },
            { value: '9', label: 'Diagnostic fields' },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl font-bold text-indigo-600">{stat.value}</p>
              <p className="mt-1 text-sm text-slate-500">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Energy Patterns overview */}
      <section className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-bold text-slate-900">
            Three Energy Patterns
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            PCA + K-Means clustering on 7 Lorenz Energy Cycle terms identifies three
            distinct energetic profiles across {DATASET_STATS.lifecyclePhases} lifecycle phases.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {Object.values(ENERGY_PATTERNS).map((ep) => (
              <div
                key={ep.id}
                className="rounded-xl border-2 p-6"
                style={{ borderColor: ep.color + '40' }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-white"
                    style={{ backgroundColor: ep.color }}
                  >
                    {ep.id}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{ep.label}</p>
                    <p className="text-xs text-slate-500">
                      N = {ep.count.toLocaleString()} ({ep.percentage.toFixed(1)}%)
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">
                  {ep.description}
                </p>
                <p className="mt-2 text-xs text-slate-400">
                  C<sub>a,int</sub> = {ep.meanCa.toFixed(2)} · C<sub>k,int</sub> ={' '}
                  {ep.meanCk.toFixed(2)} W m⁻²
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Methodological flow */}
      <section
        id="methodological-flow"
        className="scroll-mt-20 border-t border-slate-200 bg-slate-50 px-4 py-16 sm:px-6 lg:px-8"
      >
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Methodological Flow &amp; Project Status
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-500">
                The complete research path, from the source tracks to the complementary
                thermal-structure and explosive-development analyses. Status labels distinguish
                implemented scientific code from what is already represented—or still needs
                revision or integration—in the manuscript draft.
              </p>
            </div>
            <div className="shrink-0 rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600 shadow-sm">
              <p className="font-semibold text-slate-800">Status key</p>
              <div className="mt-2 space-y-1.5">
                <p><span className="font-semibold text-emerald-700">Code/results:</span> implemented end to end</p>
                <p><span className="font-semibold text-amber-700">Full run pending:</span> pipeline exists; final outputs do not</p>
                <p><span className="font-semibold text-sky-700">Manuscript included:</span> method/results are present in the draft</p>
                <p><span className="font-semibold text-rose-700">Integration pending:</span> no method/results section yet</p>
              </div>
            </div>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {METHODOLOGICAL_FLOW.map((item) => {
              const Icon = item.icon
              return (
                <div
                  key={item.step}
                  className="flex min-h-64 flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
                >
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                      {item.step}
                    </span>
                    <Icon className="h-4 w-4 text-indigo-500" />
                  </div>
                  <h3 className="font-semibold text-slate-900">{item.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-slate-500">{item.desc}</p>
                  <div className="mt-auto space-y-2 pt-5">
                    <div className="flex items-center justify-between gap-3">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
                        <Code2 className="h-3.5 w-3.5" /> Code/results
                      </span>
                      <span className={`rounded-full border px-2 py-1 text-[11px] font-semibold ${CODE_STATUS_STYLES[item.codeStatus]}`}>
                        {item.code}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
                        {item.manuscriptStatus === 'included' ? (
                          <FileCheck2 className="h-3.5 w-3.5" />
                        ) : item.manuscriptStatus === 'revision' ? (
                          <FileClock className="h-3.5 w-3.5" />
                        ) : (
                          <FileWarning className="h-3.5 w-3.5" />
                        )}
                        Manuscript
                      </span>
                      <span className={`rounded-full border px-2 py-1 text-[11px] font-semibold ${MANUSCRIPT_STATUS_STYLES[item.manuscriptStatus]}`}>
                        {item.manuscript}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <p className="mt-5 text-xs leading-relaxed text-slate-500">
            “Revision required” marks analyses whose corrected code/results are available but
            have deliberately not been transferred to the manuscript in this update cycle.
          </p>
        </div>
      </section>

      {/* Navigation cards */}
      <section className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-bold text-slate-900">
            Explore the Research
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Open each analysis directly from the homepage. Analysis-specific methods stay next
            to their results, while shared methodology remains separate from data provenance and
            the bibliography.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: 'Energy Patterns',
                desc: 'PCA, optimal cluster determination, K-Means classification, lifecycle energetics, intensity, seasonality, trends, and genesis density.',
                href: '/analyses/cluster',
                icon: BarChart3,
              },
              {
                title: 'Vertical Structure — Ca and Ck',
                desc: 'Corrected pressure-level distributions showing the vertical energy pathways of EP1, EP2, EP3, and the pooled population.',
                href: '/analyses/vertical-structure',
                icon: BetweenVerticalStart,
              },
              {
                title: 'Ck Subterms',
                desc: 'Corrected all-pattern decomposition of barotropic conversion into five mechanisms, with profiles, distributions, and lifecycle evolution.',
                href: '/analyses/ck-subterms',
                icon: TrendingDown,
              },
              {
                title: 'ERA5 Composites',
                desc: 'Storm-centred atmospheric structure across EGR, PV, temperature advection, moisture, SLP, instability, and kinetic-energy diagnostics.',
                href: '/analyses/composites',
                icon: Layers,
              },
              {
                title: 'LEC–Field Dependence',
                desc: 'EP differences and per-cyclone dependence between dynamical fields and Lorenz Energy Cycle terms.',
                href: '/analyses/field-dependence',
                icon: GitCompareArrows,
              },
              {
                title: 'Cyclone Phase Space',
                desc: 'Thermal structure, persistent phase transitions, and subtropical occurrence across the Energy Patterns.',
                href: '/analyses/cps',
                icon: Tornado,
              },
              {
                title: 'Methodology',
                desc: 'Shared processing sequence, corrected LEC equations, feature construction, explosive-cyclone identification, and numerical conventions.',
                href: '/methodology',
                icon: Workflow,
              },
              {
                title: 'Data & References',
                desc: 'Dataset inventory, analysis populations, provenance, bibliography, and DOI records.',
                href: '/data-references',
                icon: BookOpen,
              },
            ].map((card) => {
              const Icon = card.icon
              return (
                <Link
                  key={card.href}
                  href={card.href}
                  className="group rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
                >
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 transition-colors group-hover:bg-indigo-600 group-hover:text-white">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600">
                    {card.title}
                  </h3>
                  <p className="mt-1.5 text-sm text-slate-500">{card.desc}</p>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* About / Context section — absorbed from /about */}
      <section className="border-t border-slate-200 bg-slate-50 px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-bold text-slate-900">About This Project</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            Research context, data provenance, and repository information.
          </p>

          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            {/* Research context */}
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <h3 className="mb-3 font-semibold text-slate-900">Research Context</h3>
              <div className="space-y-3 text-sm leading-relaxed text-slate-600">
                <p>
                  Extratropical cyclones are key elements of midlatitude weather and climate.
                  In the South Atlantic, these systems exhibit a wide range of energetic
                  behaviours — from weak transient disturbances to intense storms with large
                  barotropic and baroclinic energy conversions.
                </p>
                <p>
                  This project uses the <strong>Lorenz Energy Cycle</strong> framework to
                  quantify the energetics of {DATASET_STATS.totalCyclones.toLocaleString()}{' '}
                  cyclones tracked over {DATASET_STATS.years} years ({DATASET_STATS.period}).
                  Seven energy terms are computed in a semi-Lagrangian framework following
                  each cyclone.
                </p>
                <p>
                  PCA-based K-Means clustering identifies three distinct{' '}
                  <strong>Energy Patterns</strong>. ERA5 composite analysis reveals the
                  atmospheric structure differences among groups ranked by their combined
                  intensification-phase baroclinic and barotropic conversion magnitudes.
                </p>
              </div>
            </div>

            {/* Repository */}
            <div className="space-y-4">
              <div className="rounded-xl border border-slate-200 bg-white p-6">
                <div className="mb-3 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-indigo-500" />
                  <h3 className="font-semibold text-slate-900">Repository</h3>
                </div>
                <p className="text-sm text-slate-600">
                  <a
                    href="https://github.com/daniloceano/paper_energy_patterns"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-indigo-600 hover:underline"
                  >
                    daniloceano/paper_energy_patterns
                  </a>
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  All scripts, data references, results, and documentation. This web layer
                  lives in <code className="text-xs">web/</code> and reads from existing
                  scientific outputs without modifying them.
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-6">
                <h3 className="mb-3 font-semibold text-slate-900">Repository Structure</h3>
                <ul className="space-y-1 text-xs text-slate-500 font-mono">
                  {[
                    ['scripts/', 'Scientific analysis pipelines (Python)'],
                    ['data/', 'Input data and ERA5 composites'],
                    ['results/', 'Analysis outputs (CSV, pickle)'],
                    ['figures/', 'Generated figures (PNG)'],
                    ['docs/', 'PDF documentation'],
                    ['web/', 'This Next.js application'],
                    ['scripts/web/', 'Data extraction for the site'],
                  ].map(([path, desc]) => (
                    <li key={path} className="flex gap-2">
                      <span className="w-28 shrink-0 text-slate-700">{path}</span>
                      <span>{desc}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
