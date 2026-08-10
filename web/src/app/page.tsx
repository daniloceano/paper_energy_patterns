import Link from 'next/link'
import {
  BarChart3,
  Layers,
  Database,
  BookOpen,
  Microscope,
  ArrowRight,
  GitBranch,
} from 'lucide-react'
import { ENERGY_PATTERNS, DATASET_STATS } from '@/lib/constants'

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
              href="/methods"
              className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/20"
            >
              Methodology
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
                      N = {ep.count} ({ep.percentage}%)
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">
                  {ep.description}
                </p>
                <p className="mt-2 text-xs text-slate-400">
                  Mean C<sub>k</sub> = {ep.meanCk} W m⁻²
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Methodological flow */}
      <section className="border-t border-slate-200 bg-slate-50 px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-bold text-slate-900">
            Methodological Flow
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            From raw cyclone tracks to composite atmospheric structure analysis.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                step: '1',
                title: 'Data & Filtering',
                desc: 'Download Zenodo tracks, filter for complete lifecycles (3,820 cyclones)',
                icon: Database,
              },
              {
                step: '2',
                title: 'PCA + Clustering',
                desc: 'Normalise 7 energy terms, apply PCA, K-Means (k=3) → EP1, EP2, EP3',
                icon: BarChart3,
              },
              {
                step: '3',
                title: 'ERA5 Composites',
                desc: 'Storm-centred 30°×30° composites of 9 diagnostic fields at key levels',
                icon: Layers,
              },
              {
                step: '4',
                title: 'Structure Analysis',
                desc: 'Compare EP1 vs EP2 structure: real fields, anomalies, domain statistics',
                icon: Microscope,
              },
            ].map((item) => {
              const Icon = item.icon
              return (
                <div
                  key={item.step}
                  className="rounded-xl border border-slate-200 bg-white p-5"
                >
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                      {item.step}
                    </span>
                    <Icon className="h-4 w-4 text-indigo-500" />
                  </div>
                  <h3 className="font-semibold text-slate-900">{item.title}</h3>
                  <p className="mt-1 text-sm text-slate-500">{item.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Navigation cards */}
      <section className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-bold text-slate-900">
            Explore the Research
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Three entry points. The analyses index is the single place where every
            analysis is listed, so nothing goes missing here as the work grows.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: 'Analyses',
                desc: 'Clustering, ERA5 composites, Ck subterms, LEC–field dependence, and the cyclone phase space',
                href: '/analyses',
                icon: BarChart3,
              },
              {
                title: 'Methods',
                desc: 'Dataset, energy terms, anomaly methodology, and boundary flux formulas',
                href: '/methods',
                icon: Microscope,
              },
              {
                title: 'References',
                desc: 'Key bibliographic references and data sources',
                href: '/references',
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
                  atmospheric structure differences between EP1 (strong conversions,
                  energy exporters) and EP2 (intermediate conversions, energy importers)
                  during intensification.
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
