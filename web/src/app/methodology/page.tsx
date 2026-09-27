import type { Metadata } from 'next'
import Link from 'next/link'
import {
  Activity,
  ArrowRight,
  BarChart3,
  CloudLightning,
  Database,
  Layers,
  Workflow,
} from 'lucide-react'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import { DATASET_STATS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Methodology',
  description:
    'Shared methodology for cyclone selection, lifecycle normalisation, corrected Lorenz Energy Cycle diagnostics, Energy Pattern classification, and explosive-cyclone identification.',
}

const LEC_TERMS = [
  {
    key: 'Ae',
    title: 'Eddy Available Potential Energy',
    unit: 'J m⁻²',
    description:
      'Thermal energy reservoir associated with departures from the zonal-mean temperature field.',
    formula: String.raw`A_E = \int_{p_t}^{p_b} \frac{\left[(T)_\lambda^{2}\right]_{\lambda \phi}}{2[\sigma]_{\lambda \phi}} \, dp`,
  },
  {
    key: 'Ke',
    title: 'Eddy Kinetic Energy',
    unit: 'J m⁻²',
    description: 'Kinetic energy of the cyclone-scale zonal and meridional wind departures.',
    formula: String.raw`K_E = \int_{p_t}^{p_b} \frac{\left[(u)_\lambda^2 + (v)_\lambda^2\right]_{\lambda \phi}}{2g} \, dp`,
  },
  {
    key: 'Ge',
    title: 'Eddy APE Generation',
    unit: 'W m⁻²',
    description: 'Diabatic generation of eddy available potential energy.',
    formula: String.raw`G_E = \int_{p_t}^{p_b} \frac{\left[(q)_\lambda (T)_\lambda\right]_{\lambda \phi}}{c_p[\sigma]_{\lambda \phi}} \, dp`,
  },
  {
    key: 'Ca',
    title: 'Baroclinic Conversion',
    unit: 'W m⁻²',
    description:
      'Transfer from zonal to eddy available potential energy; positive values feed the eddy reservoir.',
    formula: String.raw`C_A = \int_{p_b}^{p_t} \frac{R}{p\sigma} \left[ (\omega)_\lambda (T)_\lambda \frac{\partial \langle T \rangle_\lambda}{\partial \phi} \right] dp`,
  },
  {
    key: 'Ck',
    title: 'Barotropic Conversion',
    unit: 'W m⁻²',
    description:
      'Kinetic-energy transfer between the mean flow and the cyclone-scale eddy; negative values feed the eddy in this convention.',
    formula: String.raw`\begin{split}
C_K = \int_{p_t}^{p_b} \frac{1}{g} & \Bigg( \underbrace{ \left[ \frac{\cos\phi}{a} (u)_{\lambda} (v)_{\lambda} \frac{\partial}{\partial\phi} \left(\frac{[u]_{\lambda}}{\cos\phi}\right) \right]_{\lambda\phi}}_{\text{(A)}} + \underbrace{\left[ \frac{(v)_{\lambda}^2}{a} \frac{\partial [v]_{\lambda}}{\partial\phi}\right]_{\lambda\phi}}_{\text{(B)}} + \underbrace{\left[ \frac{\tan\phi}{a} (u)_{\lambda}^2 [v]_{\lambda}\right]_{\lambda\phi}}_{\text{(C)}}\\
& + \underbrace{ \left[(\omega)_{\lambda} (u)_{\lambda} \frac{\partial [u]_{\lambda}}{\partial p}\right]_{\lambda\phi}}_{\text{(D)}} + \underbrace{ \left[(\omega)_{\lambda} (v)_{\lambda} \frac{\partial [v]_{\lambda}}{\partial p}\right]_{\lambda\phi}}_{\text{(E)}} \Bigg) dp
\end{split}`,
    terms: {
      '(A)': 'Horizontal eddy momentum flux against meridional zonal-wind shear',
      '(B)': 'Meridional eddy kinetic-energy flux',
      '(C)': 'Curvature contribution',
      '(D)': 'Vertical flux of zonal eddy momentum',
      '(E)': 'Vertical flux of meridional eddy momentum',
    },
  },
  {
    key: 'BAe',
    title: 'Eddy APE Boundary Flux',
    unit: 'W m⁻²',
    description: 'Net transport of eddy available potential energy through the moving domain boundaries.',
    formula: String.raw`\mathrm{BAE} = c_1 \int_{p_1}^{p_2} \int_{\varphi_1}^{\varphi_2}
\frac{u(T)_\lambda^2}{2[\sigma]_{\lambda \varphi}}\bigg|_{\lambda_1}^{\lambda_2} d\varphi\,dp
+ c_2 \int_{p_1}^{p_2}\frac{[(T)_\lambda^2v]_\lambda\cos\varphi}{2[\sigma]_{\lambda\varphi}}\bigg|_{\varphi_1}^{\varphi_2}dp
- \left(\frac{[\omega(T)_\lambda^2]_{\lambda\varphi}}{2[\sigma]_{\lambda\varphi}}\right)_{p_1}^{p_2}`,
  },
  {
    key: 'BKe',
    title: 'Eddy KE Boundary Flux',
    unit: 'W m⁻²',
    description: 'Net transport of eddy kinetic energy through the moving domain boundaries.',
    formula: String.raw`\mathrm{BKE} = c_1 \int_{p_1}^{p_2} \int_{\varphi_1}^{\varphi_2}
\frac{u[(u)_\lambda^2+(v)_\lambda^2]}{2g}\bigg|_{\lambda_1}^{\lambda_2}d\varphi\,dp
+ c_2 \int_{p_1}^{p_2}\frac{[v\cos\varphi((u)_\lambda^2+(v)_\lambda^2)]_\lambda}{2g}\bigg|_{\varphi_1}^{\varphi_2}dp
- \left(\frac{[\omega((u)_\lambda^2+(v)_\lambda^2)]_{\lambda\varphi}}{2g}\right)_{p_1}^{p_2}`,
  },
] as const

const ANALYSIS_METHODS = [
  {
    title: 'Energy Pattern classification',
    description: 'PCA, cluster validation, K-Means, LPS, and trend testing.',
    href: '/analyses/cluster',
  },
  {
    title: 'Vertical structure & Ck subterms',
    description: 'Pressure-level integration, closure tests, dominance, and EP contrasts.',
    href: '/analyses/vertical-structure',
  },
  {
    title: 'ERA5 composites',
    description: 'Storm-centred sampling, duration filter, composite fields, and anomaly definitions.',
    href: '/analyses/composites',
  },
  {
    title: 'LEC–field dependence',
    description: 'Feature extraction, Pearson/Spearman association, PREDEP, and effect sizes.',
    href: '/analyses/field-dependence',
  },
  {
    title: 'Cyclone Phase Space',
    description: 'Thermal-structure criteria, persistence gates, transitions, and frequency tests.',
    href: '/analyses/cps',
  },
] as const

export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Methodology"
        badge="Shared Scientific Framework"
        description="Methods shared across the project: cyclone selection, lifecycle normalisation, corrected Lorenz Energy Cycle diagnostics, construction of the Energy Pattern feature space, and identification of explosively deepening cyclones. Methods unique to an analysis remain beside its results."
      />

      <div className="space-y-12">
        <ResultSummaryCallout type="info" title="Scope of this page">
          <p>
            This page documents common scientific operations. Dataset provenance and DOI records
            are kept separately in <Link href="/data-references" className="font-medium text-indigo-600 hover:underline">Data &amp; References</Link>.
            Analysis-specific filtering, statistics, and sensitivity choices are documented on the
            corresponding analysis page.
          </p>
        </ResultSummaryCallout>

        <section>
          <h2 className="text-xl font-bold text-slate-900">Common processing sequence</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {[
              {
                title: '1. Track selection',
                icon: Database,
                text: `${DATASET_STATS.totalCyclones.toLocaleString()} cyclones with genesis in ARG, LA-PLATA, and SE-BR are selected from the 1979–2020 track catalogue.`,
              },
              {
                title: '2. Lifecycle normalisation',
                icon: Activity,
                text: `${DATASET_STATS.filteredCyclones.toLocaleString()} systems with the complete incipient → intensification → mature → decay sequence are retained and represented by phase means.`,
              },
              {
                title: '3. Corrected LEC computation',
                icon: Workflow,
                text: 'Energy reservoirs, conversions, generation, and boundary fluxes are computed in a 15° × 15° semi-Lagrangian domain centred on each cyclone.',
              },
              {
                title: '4. Energy Pattern feature space',
                icon: BarChart3,
                text: 'Seven LEC terms across four lifecycle phases form 28 standardised features. PCA retains 15 components before the three-pattern K-Means classification.',
              },
            ].map((step) => {
              const Icon = step.icon
              return (
                <div key={step.title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-indigo-600" />
                    <h3 className="font-semibold text-slate-900">{step.title}</h3>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{step.text}</p>
                </div>
              )
            })}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900">Corrected Lorenz Energy Cycle framework</h2>
          <p className="mt-2 max-w-4xl text-sm leading-relaxed text-slate-600">
            The project uses the corrected full-population LEC products. The seven terms below
            define the shared energetic feature space. Reservoirs are expressed in J m⁻² and
            conversion, generation, and boundary-flux terms in W m⁻².
          </p>
          <div className="mt-6 space-y-4">
            {LEC_TERMS.map((term) => (
              <div key={term.key} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">
                    {term.key}
                  </span>
                  <h3 className="font-semibold text-slate-900">{term.title}</h3>
                  <span className="text-xs text-slate-400">[{term.unit}]</span>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{term.description}</p>
                <div className="mt-4">
                  <FormulaBlock
                    formula={term.formula}
                    label={`${term.key} formula`}
                    terms={'terms' in term ? term.terms : undefined}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section id="explosive-cyclones" className="scroll-mt-24">
          <div className="flex items-center gap-2">
            <CloudLightning className="h-5 w-5 text-indigo-600" />
            <h2 className="text-xl font-bold text-slate-900">Explosive cyclone identification</h2>
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-relaxed text-slate-600">
            The bomb-cyclone analysis adds a surface-pressure diagnostic to the existing
            850-hPa-vorticity tracks. It does not redefine the lifecycle or the Energy Patterns:
            it tests how often each previously classified EP undergoes explosive central-pressure
            deepening.
          </p>

          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
            <p className="font-semibold">Correction and completion status</p>
            <p className="mt-1 leading-relaxed">
              The end-to-end pipeline and the methodological definitions below exist, but the
              EP membership must be rebuilt from the corrected classification and the remaining
              pressure inputs must be completed. The final full-population run remains pending,
              so this page documents the method without presenting preliminary output as final.
            </p>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="font-semibold text-slate-900">1. Population and pressure field</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                The analysis uses the full set of {DATASET_STATS.filteredCyclones.toLocaleString()}
                {' '}EP-classified cyclones and their hourly tracks. Hourly ERA5 mean sea-level
                pressure at 0.25° is sampled over a storm-following box covering the complete track,
                with a 6° spatial buffer and 12-hour temporal padding.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="font-semibold text-slate-900">2. Storm-centre pressure</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                At each timestep, gradient descent starts at the 850-hPa vorticity centre and follows
                its pressure basin to a local interior MSLP minimum. The primary search radius is 3°,
                expanded once to 5°; boundary minima and open waves are rejected, and centre jumps
                larger than 4° are flagged.
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="font-semibold text-slate-900">3. Normalized Deepening Rate</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Central pressure is placed on a regular hourly grid, with interior gaps of at most two
              hours interpolated. A centred 24-hour window is moved across the track, and the maximum
              latitude-adjusted deepening rate is retained both for the full lifecycle and for windows
              centred inside the intensification phase.
            </p>
            <div className="mt-4">
              <FormulaBlock
                formula={String.raw`\mathrm{NDR} = \frac{p(t)-p(t+24\,\mathrm{h})}{24\,\mathrm{hPa}}\,\frac{\sin 60^\circ}{\left|\sin \bar{\varphi}\right|}`}
                label="Sanders–Gyakum normalized deepening rate"
                terms={{
                  'p(t) − p(t+24 h)': 'Central-pressure fall over the 24-hour window; positive values denote deepening',
                  'φ̄': 'Mean latitude of the cyclone centre over that window',
                  NDR: 'Normalized deepening rate in Bergeron',
                }}
              />
            </div>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">
              The normalization uses the sine of latitude, referenced to 60°. A cyclone is explosive
              when NDR ≥ 1 Bergeron. A 6-hourly subsample is also computed for comparison with
              synoptic-resolution climatologies.
            </p>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="font-semibold text-slate-900">4. Severity and frequency</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Exclusive labels are weak (1.0 ≤ NDR &lt; 1.3), moderate
                (1.3 ≤ NDR &lt; 1.8), and intense (NDR ≥ 1.8). Frequency comparisons use the
                corresponding nested thresholds ≥ 1.0, ≥ 1.3, and ≥ 1.8. Only cyclones with a
                complete, assessable 24-hour window enter the canonical numerator and denominator.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="font-semibold text-slate-900">5. EP contrasts and spatial density</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Frequencies carry Wilson 95% intervals. Each EP is tested against the other two EPs
                pooled with Fisher&apos;s exact test and Holm correction; ratios to EPALL are descriptive
                because each EP is nested in that reference. Spherical KDE maps distinguish genesis,
                whole-track residence, and the position of maximum NDR.
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900">Numerical conventions</h2>
          <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm leading-relaxed text-slate-600">
              Horizontal derivatives use centred finite differences at interior points and
              one-sided differences at the domain boundaries. Spherical grid spacing is
              latitude dependent:
            </p>
            <div className="mt-4">
              <FormulaBlock
                formula={String.raw`dy = R_\oplus\,\Delta\varphi, \qquad dx = R_\oplus\,\cos(\varphi)\,\Delta\lambda`}
                label="Grid spacing on the sphere"
                terms={{
                  'dx, dy': 'Zonal and meridional grid spacing',
                  'R⊕': 'Earth radius',
                  'φ': 'Latitude',
                  'Δφ, Δλ': 'Latitude and longitude increments in radians',
                }}
              />
            </div>
          </div>
        </section>

        <section>
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-600" />
            <h2 className="text-xl font-bold text-slate-900">Analysis-specific methods</h2>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            These choices are kept with the results they produce, preventing a shared reference
            page from becoming an outdated mixture of unrelated pipelines.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {ANALYSIS_METHODS.map((analysis) => (
              <Link
                key={analysis.href}
                href={analysis.href}
                className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-200 hover:shadow-md"
              >
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-900 group-hover:text-indigo-700">{analysis.title}</h3>
                  <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-indigo-600" />
                </div>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">{analysis.description}</p>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
