import type { Metadata } from 'next'
import Link from 'next/link'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { DATASET_STATS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Methods',
  description: 'Methodology, energy terms, and data description.',
}

/** Intuitive restatement of a technical point — the "what is this number telling me?" layer. */
function SimpleTerms({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-3 rounded-lg border-l-4 border-indigo-300 bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
        In simple terms
      </p>
      <div className="mt-1 text-sm leading-relaxed text-slate-600">{children}</div>
    </div>
  )
}

/** Concrete application to this study's cyclones, EPs, LEC terms, or dynamical fields. */
function InThisStudy({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-3 rounded-lg border-l-4 border-emerald-300 bg-emerald-50/50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
        In this study
      </p>
      <div className="mt-1 text-sm leading-relaxed text-slate-600">{children}</div>
    </div>
  )
}

/** Compact left-to-right pipeline of statistical steps. */
function TestFlow({ steps }: { steps: string[] }) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2">
      {steps.map((s, i) => (
        <span key={s} className="flex items-center gap-2">
          <span className="rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 ring-1 ring-indigo-100">
            {s}
          </span>
          {i < steps.length - 1 && (
            <span aria-hidden="true" className="text-slate-300">→</span>
          )}
        </span>
      ))}
    </div>
  )
}

export default function MethodsPage() {

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Data & Methods"
        badge="Methodology"
        description="Description of the dataset, energy terms from the Lorenz Energy Cycle, and the methodological pipeline used to classify cyclones into Energy Patterns and analyse their atmospheric structure."
      />

      <div className="space-y-10">
        {/* Dataset */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">Dataset</h2>
          <StatsTable
            columns={[
              { key: 'property', label: 'Property' },
              { key: 'value', label: 'Value' },
            ]}
            rows={[
              { property: 'Source', value: 'Zenodo DOI: 10.5281/zenodo.18133432' },
              { property: 'Period', value: DATASET_STATS.period },
              { property: 'Duration', value: `${DATASET_STATS.years} years` },
              { property: 'Total cyclones', value: DATASET_STATS.totalCyclones.toLocaleString() },
              { property: 'Filtered (complete lifecycle)', value: `${DATASET_STATS.filteredCyclones.toLocaleString()} (${DATASET_STATS.filterPercentage}%)` },
              { property: 'Track temporal resolution', value: '1-hourly' },
              { property: 'Energy temporal resolution', value: '3-hourly' },
              { property: 'ERA5 spatial resolution', value: DATASET_STATS.era5Resolution },
              { property: 'Storm-centred domain', value: DATASET_STATS.domainSize },
              { property: 'Climatology baseline', value: `${DATASET_STATS.climatologyPeriod} (WMO)` },
            ]}
          />
        </section>

        {/* Unified Lorenz Energy Cycle Terms — ordered: AE, KE, GE, Ca, Ck, BAE, BKE */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Lorenz Energy Cycle Terms
          </h2>
          <p className="mb-4 text-sm text-slate-600">
            Seven terms from the semi-Lagrangian Lorenz Energy Cycle framework are computed
            for the storm-centred domain at each timestep and averaged per lifecycle phase.
            They serve both as clustering features (all seven) and as energy budget diagnostics.
            Formulas follow{' '}
            <span className="font-medium text-slate-700">Brennan &amp; Vincent (1980)</span>,{' '}
            <span className="font-medium text-slate-700">Michaelides (1987)</span>, and{' '}
            <span className="font-medium text-slate-700">Michaelides et al. (1999)</span>.
          </p>

          <div className="space-y-4">
            {/* AE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">Ae</span>
                <h3 className="font-semibold text-slate-900">Eddy Available Potential Energy</h3>
                <span className="text-xs text-slate-400">[J m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Available potential energy associated with eddy temperature perturbations — the
                reservoir that can be released by baroclinic instability.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="A_E = \int_{p_t}^{p_b} \frac{\left[(T)_\lambda^{2}\right]_{\lambda \phi}}{2[\sigma]_{\lambda \phi}} \, dp"
                  label="Ae formula"
                />
              </div>
            </div>

            {/* KE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">Ke</span>
                <h3 className="font-semibold text-slate-900">Eddy Kinetic Energy</h3>
                <span className="text-xs text-slate-400">[J m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Kinetic energy of the eddy wind components — grows as barotropic and baroclinic
                conversions feed the cyclone circulation.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="K_E = \int_{p_t}^{p_b} \frac{\left[(u)_\lambda^2 + (v)_\lambda^2\right]_{\lambda \phi}}{2g} \, dp"
                  label="Ke formula"
                />
              </div>
            </div>

            {/* GE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">Ge</span>
                <h3 className="font-semibold text-slate-900">Eddy APE Generation</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Diabatic creation of eddy APE — primarily through latent heat release in deep
                convection. Positive G<sub>E</sub> enhances the thermal contrast driving
                baroclinic development.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="G_E = \int_{p_t}^{p_b} \frac{\left[(q)_\lambda (T)_\lambda\right]_{\lambda \phi}}{c_p[\sigma]_{\lambda \phi}} \, dp"
                  label="Ge formula"
                />
              </div>
            </div>

            {/* Ca */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">Ca</span>
                <h3 className="font-semibold text-slate-900">Baroclinic Conversion</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Conversion from zonal APE to eddy APE via temperature gradients. C<sub>a</sub> &gt; 0
                indicates baroclinic energy extraction from the mean flow.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="C_a = \int_{p_b}^{p_t} \frac{R}{p\sigma} \left[ (\omega)_\lambda (T)_\lambda \frac{\partial \langle T \rangle_\lambda}{\partial \phi} \right] dp"
                  label="Ca formula"
                />
              </div>
            </div>

            {/* Ck */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">Ck</span>
                <h3 className="font-semibold text-slate-900">Barotropic Conversion</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Conversion from zonal KE to eddy KE via horizontal wind shear. C<sub>k</sub> &lt; 0
                indicates barotropic energy extraction from the mean flow (EP1 hallmark).
              </p>
              <div className="mt-3">
                  <FormulaBlock
                    formula={`\\begin{split}
  C_K = \\int_{p_t}^{p_b} \\frac{1}{g} & \\Bigg( \\underbrace{ \\left[ \\frac{\\cos\\phi}{a} (u)_{\\lambda} (v)_{\\lambda} \\frac{\\partial}{\\partial\\phi} \\left(\\frac{[u]_{\\lambda}}{\\cos\\phi}\\right) \\right]_{\\lambda\\phi}}_{\\text{(A)}} + \\underbrace{\\left[ \\frac{(v)_{\\lambda}^2}{a} \\frac{\\partial [v]_{\\lambda}}{\\partial\\phi}\\right]_{\\lambda\\phi}}_{\\text{(B)}} + \\underbrace{\\left[ \\frac{\\tan\\phi}{a} (u)_{\\lambda}^2 [v]_{\\lambda}\\right]_{\\lambda\\phi}}_{\\text{(C)}}\\\\
  & + \\underbrace{ \\left[(\\omega)_{\\lambda}  (u)_{\\lambda} \\frac{\\partial [u]_{\\lambda}}{\\partial p}\\right]_{\\lambda\\phi}}_{\\text{(D)}} + \\underbrace{ \\left[(\\omega)_{\\lambda}  (v)_{\\lambda} \\frac{\\partial [v]_{\\lambda}}{\\partial p}\\right]_{\\lambda\\phi}}_{\\text{(E)}} \\Bigg)  dp
  \\end{split}`}
                    label="Ck formula"
                    terms={{
                      '(A)': 'Eddy momentum flux × meridional gradient of zonal mean (barotropic instability)',
                      '(B)': 'Meridional flux of eddy KE with meridional wind',
                      '(C)': 'Meridional flux of zonal KE (tanφ term)',
                      '(D)': 'Vertical flux related to zonal wind shear',
                      '(E)': 'Vertical flux related to meridional wind shear',
                    }}
                  />
              </div>
            </div>

            {/* BAE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">BAe</span>
                <h3 className="font-semibold text-slate-900">Eddy APE Boundary Flux</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Transport of eddy APE across lateral and vertical domain boundaries. Negative
                BAE (energy export) is characteristic of EP1; positive BAE (energy import) of EP2.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula={`\\mathrm{BAE} = c_1 \\int_{p_1}^{p_2} \\int_{\\varphi_1}^{\\varphi_2}
\\frac{1}{2[\\sigma]_{\\lambda \\varphi}}\\left[u(T)_\\lambda^2\\right]_{\\lambda_1}^{\\lambda_2}
d\\varphi\\, dp
\\;+\\; c_2 \\int_{p_1}^{p_2}
\\frac{\\left[(T)_\\lambda^2 v\\right]_\\lambda \\cos\\varphi}{2[\\sigma]_{\\lambda \\varphi}}
\\bigg|_{\\varphi_1}^{\\varphi_2} dp
\\;-\\; \\left(\\frac{\\left[\\omega(T)_\\lambda^2\\right]_{\\lambda \\varphi}}{2[\\sigma]_{\\lambda \\varphi}}\\right)_{p_1}^{p_2}`}
                  label="BAe formula"
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Three integrals: zonal (East–West), meridional (North–South), and vertical boundaries.
                c₁, c₂: spherical geometry constants.
              </p>
            </div>

            {/* BKE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">BKe</span>
                <h3 className="font-semibold text-slate-900">Eddy KE Boundary Flux</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Transport of eddy KE across domain boundaries. Negative BKE in EP1 cyclones
                reflects strong energy export (downstream effect); positive BKE in EP2 indicates
                energy import from the surrounding flow.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula={`\\mathrm{BKE} = c_1 \\int_{p_1}^{p_2} \\int_{\\varphi_1}^{\\varphi_2}
\\frac{u\\left[(u)_\\lambda^2+(v)_\\lambda^2\\right]}{2g}
\\bigg|_{\\lambda_1}^{\\lambda_2}
d\\varphi\\, dp
\\;+\\; c_2 \\int_{p_1}^{p_2}
\\frac{\\left[v\\cos\\varphi\\left[(u)_\\lambda^2+(v)_\\lambda^2\\right]\\right]_\\lambda}{2g}
\\bigg|_{\\varphi_1}^{\\varphi_2} dp
\\;-\\; \\left(\\frac{\\left[\\omega\\left[(u)_\\lambda^2+(v)_\\lambda^2\\right]\\right]_{\\lambda \\varphi}}{2g}\\right)_{p_1}^{p_2}`}
                  label="BKe formula"
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Same three-integral structure as BAE. Spherical geometry constants c₁, c₂ as above.
              </p>
            </div>

            {/* Symbol reference */}
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-5">
              <h3 className="mb-3 text-sm font-semibold text-slate-700">Symbol Reference</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs text-slate-600">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="py-1.5 pr-4 text-left font-semibold text-slate-700">Symbol</th>
                      <th className="py-1.5 text-left font-semibold text-slate-700">Definition</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {([
                      ['(·)λ', 'Eddy component (departure from zonal mean)'],
                      ['[·]λφ', 'Domain-area average'],
                      ['σ', 'Static stability: σ = −(α/θ)(∂θ/∂p)'],
                      ['θ', 'Potential temperature [K]'],
                      ['α', 'Specific volume [m³ kg⁻¹]'],
                      ['T', 'Temperature [K]'],
                      ['u, v', 'Zonal / meridional wind [m s⁻¹]'],
                      ['ω', 'Vertical pressure velocity [Pa s⁻¹]'],
                      ['q', 'Diabatic heating rate [W kg⁻¹]'],
                      ['cₚ', 'Specific heat at constant pressure [J kg⁻¹ K⁻¹]'],
                      ['g', 'Gravitational acceleration [m s⁻²]'],
                      ['R', 'Gas constant for dry air [J kg⁻¹ K⁻¹]'],
                      ['a', 'Earth’s radius [m]'],
                      ['p', 'Pressure — the vertical coordinate [Pa]'],
                      ['φ', 'Latitude'],
                      ['λ', 'Longitude'],
                      ['p_t, p_b', 'Top and bottom pressure bounds of integration'],
                      ['p₁, p₂, φ₁, φ₂', 'Lateral boundary levels (pressure, latitude)'],
                      ['λ₁, λ₂', 'Lateral boundary longitudes'],
                      ['c₁, c₂', 'Spherical geometry constants (zonal / meridional)'],
                    ] as [string, string][]).map(([sym, def]) => (
                      <tr key={sym}>
                        <td className="py-1 pr-4 font-mono">{sym}</td>
                        <td className="py-1">{def}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Anomaly Methodology */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Climatological Anomaly Methodology
          </h2>
          <p className="mb-4 text-sm text-slate-600">
            Several diagnostic composites are presented as <strong>anomalies</strong> relative
            to a monthly climatological baseline. This isolates the synoptic-scale signal
            associated with each Energy Pattern from the seasonal background state.
          </p>

          <div className="space-y-4">
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="mb-2 font-semibold text-slate-900">Climatological Baseline</h3>
              <ul className="list-disc space-y-2 pl-5 text-sm text-slate-600">
                <li>
                  <strong>Period:</strong> {DATASET_STATS.climatologyPeriod} (WMO standard 30-year
                  reference period)
                </li>
                <li>
                  <strong>Resolution:</strong> Monthly means computed from ERA5 reanalysis at
                  {' '}{DATASET_STATS.era5Resolution} spatial resolution
                </li>
                <li>
                  <strong>Coverage:</strong> Full ERA5 domain; interpolated to the storm-centred
                  30°×30° domain at composite time
                </li>
              </ul>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="mb-2 font-semibold text-slate-900">Anomaly Calculation</h3>
              <p className="text-sm text-slate-600 mb-3">
                For each cyclone at time <em>t</em> (month <em>m</em>), the storm-centred
                field anomaly is:
              </p>
              <FormulaBlock
                formula="X'(x, y, p, t) = X(x, y, p, t) - \overline{X}_m(x, y, p)"
                label="Anomaly definition"
              />
              <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-slate-600">
                <li><em>X</em> — instantaneous ERA5 field (temperature, wind, PV, …)</li>
                <li><em>X̄ₘ</em> — monthly mean climatology for month <em>m</em></li>
                <li><em>X′</em> — anomaly field used in the composite</li>
              </ul>
              <p className="mt-3 text-sm text-slate-500">
                The composite anomaly for an Energy Pattern is the average of{' '}
                <em>X′</em> across all contributing cyclone events. This removes the seasonal
                signal and highlights the dynamical structure specific to each EP.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="mb-2 font-semibold text-slate-900">Real vs Anomaly Panels</h3>
              <p className="text-sm text-slate-600">
                Throughout the composite analysis pages, figures are presented in two variants:
              </p>
              <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-slate-600">
                <li>
                  <strong>Real (absolute):</strong> composite of the full instantaneous field —
                  shows the mean atmospheric state centred on EP cyclones
                </li>
                <li>
                  <strong>Anomaly:</strong> composite of <em>X′</em> — isolates the cyclone-relative
                  signal from the seasonal background; positive/negative anomalies reveal
                  anomalous warm/cold, high/low PV, divergent/convergent regions
                </li>
              </ul>
              <p className="mt-2 text-xs text-slate-400">
                Source: <code>scripts/ep_structure_analysis/step4_create_figures.py</code>{' '}
                and <code>step5_update_scientific_notes.py</code>
              </p>
            </div>
          </div>
        </section>


        {/* Methodology */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Methodology
          </h2>
          <MethodologyAccordion
            items={[
              {
                title: 'Step 1: Data filtering and feature matrix',
                content:
                  'Cyclones with incomplete lifecycle phases are removed (3,820 of 6,789 retained). Each cyclone\'s 7 energy terms are averaged within each of the 4 lifecycle phases and pivoted into a single wide matrix of 28 features (7 terms × 4 phases) per cyclone, then standardised (μ=0, σ=1) with scikit-learn\'s StandardScaler.',
              },
              {
                title: 'Step 2: Global PCA across terms and phases',
                content:
                  'A single PCA is applied jointly across all 28 standardised features — not separately per phase — so that correlations between energy terms and between lifecycle phases are captured together. The first 15 principal components are retained, explaining ≈90% of the cumulative variance.',
              },
              {
                title: 'Step 3: Optimal k determination',
                content:
                  '5 cluster validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, Gap Statistic) are computed for k=3–15 and normalised. Ensemble averaging identifies k=3.',
              },
              {
                title: 'Step 4: K-Means clustering',
                content:
                  'K-Means (k=3, n_init=100, random_state=42) with K-Means++ initialisation is applied once, on the retained 15-component PCA space (not per phase). Clusters are labelled EP1, EP2, EP3 by Ck magnitude.',
              },
              {
                title: 'Step 5: ERA5 composite analysis',
                content:
                  'Storm-centred 30°×30° composites of 9 diagnostic fields are computed for EP1, EP2, and EP3 during intensification, and compared against the full-population composite (EPALL). Anomalies use 1991–2020 WMO monthly climatology.',
              },
              {
                title: 'Grid calculations',
                content:
                  'Spherical geometry: dy = R_⊕ × Δφ, dx = R_⊕ × cos(φ) × Δλ, where R_⊕ = 6.371 × 10⁶ m. All spatial derivatives use centred differences.',
              },
            ]}
          />
        </section>

        {/* Statistical Analysis */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Statistical Analysis
          </h2>
          <p className="mb-4 text-sm text-slate-600">
            Four questions needed a dedicated statistical treatment beyond the clustering
            step itself: (1) are EP1, EP2, and EP3 truly distinguishable in their LEC
            diagnostics and dynamical structure, and not just the nearest-centroid label of
            an underlying continuum? (2) how strongly does cyclone energetics covary with the
            dynamical fields shown in the composite pages? (3) are the interannual
            fluctuations in EP occurrence ({DATASET_STATS.period}) genuine long-term trends,
            or consistent with sampling noise? and (4) is an Energy Pattern more or less
            likely than the pooled population to be subtropical, or to undergo a subtropical
            transition? These map onto the four tracks below: inter-EP comparison,
            association analysis, trend analysis, and the Cyclone Phase Space contingency
            analysis.
          </p>
          <p className="mb-4 text-sm text-slate-600">
            Three of these four tracks share the same logical skeleton, and it is worth
            stating it once before the details. A <strong>global test</strong> asks whether
            any difference exists at all; if it is significant, a <strong>post-hoc
            test</strong> localises which specific groups differ; a{' '}
            <strong>multiple-comparison correction</strong> keeps the extra tests from
            manufacturing false positives; and an <strong>effect size</strong> reports how
            large the difference actually is, independent of how many cyclones were
            sampled. Only the statistical machinery changes between tracks — continuous
            variables use ranks, the phase-space analysis uses counts.
          </p>

          <div className="space-y-4">
            {/* Inter-EP differences */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                1 · Testing whether Energy Patterns differ
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                For all 24 LEC terms plus 13 scalar descriptors summarising each
                storm-centred dynamical field (domain mean, mean absolute value, centre
                value, N/S/E/W sector and border means, and N–S/E–W contrasts) — 154
                variables in total — a sequential decision procedure picks the correct
                global test and post-hoc comparison based on that variable&apos;s own
                distributional properties, rather than assuming one test fits everything.
                The population here is the {(2733).toLocaleString()} cyclones that survive
                the ≥ 24 h intensification filter used for the composites (EP1 = 332,
                EP2 = 776, EP3 = 1,625); the Cyclone Phase Space analysis in track 7 uses a
                different, larger population and is stated separately there.
                Two screening tests drive the choice: <strong>Shapiro–Wilk</strong>, which
                compares each EP&apos;s sorted values against what a normal distribution
                would produce (a small <em>p</em> means &quot;not Gaussian&quot;), and{' '}
                <strong>Brown–Forsythe</strong>, a version of Levene&apos;s test run on each
                value&apos;s absolute deviation from its group <em>median</em>, which asks
                whether the three EPs have comparable spread. Median-centring matters here
                because LEC terms are typically skewed — near zero for weak systems, with a
                long tail for intense conversions.
              </p>
              <div className="mt-3">
                <StatsTable
                  title="Decision procedure — which route a variable takes"
                  columns={[
                    { key: 'condition', label: 'Screening result' },
                    { key: 'global', label: 'Global test' },
                    { key: 'posthoc', label: 'Post-hoc' },
                    { key: 'correction', label: 'Correction' },
                    { key: 'effect', label: 'Effect size' },
                  ]}
                  rows={[
                    { condition: 'Normal, equal variance', global: 'One-way ANOVA', posthoc: 'Tukey HSD', correction: 'built into Tukey', effect: 'ω² / Cohen’s d' },
                    { condition: 'Normal, unequal variance', global: 'Welch’s ANOVA', posthoc: 'Welch t-tests', correction: 'Holm', effect: 'ω² / Cohen’s d' },
                    { condition: 'Non-normal (≥1 group)', global: 'Kruskal–Wallis', posthoc: 'Dunn', correction: 'Holm', effect: 'ε² / rank-biserial r' },
                  ]}
                  caption="Normality: Shapiro–Wilk within each EP. Homogeneity of variance: Brown–Forsythe (median-centred Levene). Effect sizes are listed as global / pairwise. In this dataset all 154 variables took the third route."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Every one of the 154 variables tested departed from normality in at least
                one EP group, so all inter-EP comparisons reported on this site follow the
                third row. The full chain actually executed is therefore:
              </p>
              <TestFlow
                steps={[
                  'Shapiro–Wilk',
                  'Brown–Forsythe',
                  'Kruskal–Wallis (global)',
                  'Dunn (post-hoc)',
                  'Holm + FDR',
                  'ε² / rank-biserial r',
                ]}
              />
              <p className="mt-4 text-sm text-slate-600">
                The two ANOVA routes remain in the pipeline because the test is chosen per
                variable, not fixed in advance — but no variable in this dataset reached
                them, so nothing reported here rests on a parametric assumption.
              </p>

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                Global test — Kruskal–Wallis
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                <strong>Question answered:</strong> is there evidence that at least one EP
                differs from the others on this variable?{' '}
                <strong>Null hypothesis (H₀):</strong> the values of EP1, EP2, and EP3 are
                all drawn from the same underlying distribution.{' '}
                <strong>Alternative (H₁):</strong> at least one EP is stochastically shifted
                — its values tend to sit systematically higher or lower than the others.
                All cyclones from the three EPs are pooled and ranked together (ties get the
                average rank), and the test asks whether each EP&apos;s ranks are spread
                around the overall average rank or clumped high or low.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="H = \frac{12}{N(N+1)} \sum_{c=1}^{3} \frac{R_c^2}{n_c} - 3(N+1)"
                  label="Kruskal–Wallis statistic"
                  terms={{
                    'H': 'Kruskal–Wallis test statistic (dimensionless, ≥ 0)',
                    'c': 'Index over the three Energy Patterns (c = 1, 2, 3)',
                    'n_c': 'Number of cyclones in EP c',
                    'R_c': 'Sum of the joint ranks of all cyclones in EP c',
                    'N': 'Total number of cyclones across all EPs (N = n₁ + n₂ + n₃)',
                    '12, 3': 'Normalising constants that make H follow a χ² distribution under H₀',
                    'Σ': 'Sum taken over the three Energy Patterns',
                  }}
                  notes="Under H₀, H follows a χ² distribution with 2 degrees of freedom (number of groups − 1). H ≈ 0 means the EP rank distributions are indistinguishable; large H means at least one EP sits systematically high or low. The p-value is the χ² tail probability beyond the observed H."
                />
              </div>
              <SimpleTerms>
                <p>
                  Line up all {DATASET_STATS.filteredCyclones.toLocaleString()} cyclones
                  from weakest to strongest on the variable of interest, and number them
                  1, 2, 3, … That number is the rank. Now look at where each EP&apos;s
                  cyclones landed. If EP1, EP2, and EP3 are scattered evenly through the
                  queue, their average ranks are all near the middle and{' '}
                  <em>H</em> stays small. If EP1&apos;s cyclones cluster at the strong end
                  while EP3&apos;s cluster at the weak end, the average ranks pull apart
                  and <em>H</em> grows. Because the test only uses the order of the
                  cyclones and never their raw values, a few extreme outliers cannot
                  distort it — which is exactly what LEC terms need, since their
                  distributions are skewed rather than bell-shaped.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  A significant Kruskal–Wallis result for barotropic conversion{' '}
                  <em>C</em><sub>k</sub> tells us the three EPs are not all drawing{' '}
                  <em>C</em><sub>k</sub> from the same distribution. That is genuinely
                  useful — it means the energetic clustering captured something real about
                  barotropic conversion — but it is also the limit of what this test can
                  say. It cannot tell us whether EP1 is the outlier, whether EP2 and EP3
                  are similar to each other, or which pair drives the difference. For that,
                  the post-hoc step below is required.
                </p>
              </InThisStudy>

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                Post-hoc test — Dunn
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                <strong>When it runs:</strong> only if the global Kruskal–Wallis test is
                significant. Running post-hoc contrasts after a non-significant global test
                would inflate false positives, so the pipeline skips them.{' '}
                <strong>What it compares:</strong> the three pairwise contrasts EP1×EP2,
                EP1×EP3, and EP2×EP3.{' '}
                <strong>How:</strong> Dunn reuses the <em>same joint ranking</em> already
                computed for the global test — it does not re-rank each pair in isolation,
                which is what makes it the correct companion to Kruskal–Wallis rather than
                running three separate Mann–Whitney tests. It converts the difference
                between two EPs&apos; mean ranks into a <em>z</em> score.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="z_{ij} = \frac{\bar{R}_i - \bar{R}_j}{\sqrt{\left[\dfrac{N(N+1)}{12} - \dfrac{\sum_t (t^3-t)}{12(N-1)}\right]\left(\dfrac{1}{n_i}+\dfrac{1}{n_j}\right)}}"
                  label="Dunn pairwise statistic"
                  terms={{
                    'z_ij': 'Standardised difference between EP i and EP j (dimensionless)',
                    'i, j': 'The two Energy Patterns being contrasted (e.g. i = EP1, j = EP2)',
                    'R̄_i': 'Mean joint rank of the cyclones in EP i',
                    'R̄_j': 'Mean joint rank of the cyclones in EP j',
                    'n_i, n_j': 'Number of cyclones in EP i and EP j',
                    'N': 'Total number of cyclones across all three EPs',
                    't': 'Size of each group of tied values; the Σ term corrects the variance for ties',
                  }}
                  notes="The denominator is the standard error of the rank difference expected under H₀. The two-sided p-value is read from the standard normal distribution: p = 2 × P(Z > |z_ij|). Sign convention: z_ij > 0 means EP i ranks higher than EP j."
                />
              </div>
              <SimpleTerms>
                <p>
                  Kruskal–Wallis is the smoke alarm: it tells you something is burning
                  somewhere in the building. Dunn walks the corridors and tells you which
                  room. Concretely, the global test can only support the statement{' '}
                  <em>&quot;there is evidence that at least one EP differs from the
                  others&quot;</em>; only the post-hoc contrasts support the far more useful
                  statement <em>&quot;EP1 differs specifically from EP2, while EP2 and EP3
                  do not differ from each other.&quot;</em> Reporting the second conclusion
                  on the strength of the first alone is one of the most common errors in
                  applied statistics.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  For <em>C</em><sub>k</sub>, the post-hoc contrasts are what allow the
                  result to be stated as &quot;EP1 has significantly stronger barotropic
                  conversion than both EP2 and EP3&quot; rather than the vague &quot;the
                  EPs differ in <em>C</em><sub>k</sub>&quot;. The pairwise effect-size
                  heatmaps on the{' '}
                  <Link href="/analyses/field-dependence/ep-differences" className="text-indigo-600 hover:underline">
                    EP Differences
                  </Link>{' '}
                  page are built directly from these three Dunn contrasts, one column per
                  contrast.
                </p>
              </InThisStudy>
            </div>

            {/* Effect size */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                2 · Effect size: how large the difference is, not just whether it exists
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                A <em>p</em>-value answers a yes/no question — is there evidence of a
                difference? — and its answer depends heavily on how many cyclones were
                sampled. An effect size answers the quantitative question — how big is that
                difference? — and is designed <em>not</em> to grow simply because the sample
                is large. Because the EP samples entering these tests are large and uneven
                (EP1 = 332, EP2 = 776, EP3 = 1,625 cyclones), both numbers are reported for
                every global and pairwise comparison, and the effect size carries the
                interpretive weight.
              </p>

              <h4 className="mt-4 text-sm font-semibold text-slate-800">
                Global effect size — epsilon squared (ε²)
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                Accompanies the Kruskal–Wallis global test. It rescales <em>H</em> into the
                approximate fraction of the total rank variation that is explained by
                knowing which EP a cyclone belongs to — the rank-based analogue of the
                &quot;variance explained&quot; statistics used with ANOVA.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="\varepsilon^2 = \frac{H - k + 1}{N - k}"
                  label="Epsilon squared — global effect size"
                  terms={{
                    'ε²': 'Proportion of rank variation explained by EP membership (dimensionless, 0 to 1)',
                    'H': 'Kruskal–Wallis statistic from the equation above',
                    'k': 'Number of groups compared (k = 3 Energy Patterns)',
                    'N': 'Total number of cyclones across all EPs',
                  }}
                  notes="Range 0 to 1. ε² = 0 means EP membership tells you nothing about the variable; ε² = 1 means EP membership determines it completely. Unlike H itself, ε² does not grow just because more cyclones were added."
                />
              </div>
              <SimpleTerms>
                <p>
                  ε² answers: <em>if I tell you which Energy Pattern a cyclone belongs to,
                  how much better can you guess its C<sub>a</sub>?</em> An ε² of 0.30 means
                  EP membership accounts for roughly 30% of the rank spread in{' '}
                  <em>C</em><sub>a</sub> — substantial. An ε² of 0.005 means that knowing
                  the EP barely helps at all, even if the <em>p</em>-value is
                  vanishingly small.
                </p>
              </SimpleTerms>

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                Pairwise effect size — rank-biserial correlation (r<sub>rb</sub>)
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                Accompanies each Dunn pairwise contrast. Unlike ε², it is{' '}
                <strong>signed</strong>, so it reports both how large the difference is and
                which of the two EPs is larger.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="r_{rb} = 1 - \frac{2U}{n_i\,n_j}"
                  label="Rank-biserial correlation — pairwise effect size"
                  terms={{
                    'r_rb': 'Rank-biserial correlation for the contrast EP i vs EP j (dimensionless, −1 to +1)',
                    'U': 'Mann–Whitney U statistic — the number of cyclone pairs (one from each EP) in which the EP j member has the larger value',
                    'n_i, n_j': 'Number of cyclones in EP i and EP j',
                    'n_i × n_j': 'Total number of cross-EP cyclone pairs that can be formed',
                  }}
                  notes="Range −1 to +1. r_rb = +1: every cyclone in EP i exceeds every cyclone in EP j (complete separation). r_rb = 0: the two EPs overlap so thoroughly that a cyclone from either is equally likely to be the larger. r_rb = −1: the reverse of +1."
                />
              </div>
              <SimpleTerms>
                <p>
                  Pick one cyclone at random from EP1 and one at random from EP2, and ask
                  which has the stronger <em>C</em><sub>k</sub>. Do this for every possible
                  pairing. <em>r<sub>rb</sub></em> is simply the probability that EP1 wins
                  minus the probability that EP2 wins. A value of +0.50 means EP1 wins 75%
                  of the time and EP2 wins 25% — a large, practically meaningful gap. A
                  value of +0.04 means EP1 wins 52% of the time: technically a difference,
                  but you would be hard pressed to tell two individual cyclones apart on
                  that basis.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  The sign carries the physics. A positive EP1×EP2 contrast for{' '}
                  <em>C</em><sub>k</sub> means EP1 cyclones convert kinetic energy
                  barotropically more strongly than EP2 cyclones — the signature that
                  defines EP1. The discrete colour bins on the effect-size heatmaps use
                  exactly the thresholds below, with grey reserved for |r<sub>rb</sub>| &lt;
                  0.10 so that negligible effects are visually separated from meaningful
                  ones even when they are statistically significant.
                </p>
              </InThisStudy>
              <div className="mt-3">
                <StatsTable
                  title="Magnitude conventions used throughout this site"
                  columns={[
                    { key: 'mag', label: 'Magnitude' },
                    { key: 'eps', label: 'ε² — global' },
                    { key: 'rrb', label: '|r_rb| — pairwise' },
                  ]}
                  rows={[
                    { mag: 'Negligible', eps: '< 0.01', rrb: '< 0.10' },
                    { mag: 'Small', eps: '0.01 – 0.06', rrb: '0.10 – 0.30' },
                    { mag: 'Medium', eps: '0.06 – 0.14', rrb: '0.30 – 0.50' },
                    { mag: 'Large', eps: '≥ 0.14', rrb: '≥ 0.50' },
                  ]}
                  caption="ε² bins follow Rea & Parker (1992); |r_rb| bins follow Cohen (1988). These are field-wide reporting conventions, not physical laws — they are a shared vocabulary for describing magnitude, and a 'small' effect on a term as noisy as Ge may still be physically informative. Magnitude should always be read together with the physical plausibility of the result."
                />
              </div>
            </div>

            {/* p-value vs effect size */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                3 · What a <em>p</em>-value does and does not mean
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                A <em>p</em>-value is the probability of observing a test statistic at least
                as extreme as the one obtained, <em>assuming the null hypothesis is exactly
                true</em>. When <em>p</em> &lt; α (α = 0.05 throughout this study), chance
                alone is an unlikely explanation for the pattern, and we treat that as
                evidence against H₀.
              </p>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                    What p &lt; 0.05 does mean
                  </p>
                  <p className="mt-1.5 text-sm text-slate-600">
                    The observed difference would be unlikely to arise from sampling
                    variability alone if the EPs really were identical on this variable.
                  </p>
                </div>
                <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-amber-700">
                    What it does <em>not</em> mean
                  </p>
                  <p className="mt-1.5 text-sm text-slate-600">
                    It is not the probability that H₀ is true, not proof that H₁ is true,
                    not a measure of how large the difference is, and not evidence that the
                    difference matters physically. Equally, <em>p</em> ≥ 0.05 does not prove
                    the EPs are identical — it only means the evidence is insufficient.
                  </p>
                </div>
              </div>
              <SimpleTerms>
                <p>
                  The <em>p</em>-value is sensitive to sample size in a way that effect size
                  is not. Suppose EP1 and EP3 differ in mean <em>A</em><sub>e</sub> by an
                  amount so small it would never change how you interpret a synoptic chart.
                  With 40 cyclones per group that difference is invisible to the test
                  (<em>p</em> ≈ 0.4). With 332 and 1,625 cyclones — the actual EP1 and EP3
                  sample sizes in this analysis — the very same difference can return{' '}
                  <em>p</em> &lt; 0.001. Nothing about the atmosphere changed; only the
                  statistical power did. This is why a small <em>p</em> paired with a
                  near-zero effect size means &quot;a real but tiny difference&quot;, not
                  &quot;an important result&quot;.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  Adjusted <em>p</em>-values are used as a <strong>screening step</strong>{' '}
                  to flag which of the 154 variables deserve a closer look. Effect sizes
                  (ε², r<sub>rb</sub>) and consistency with the composite dynamical fields
                  then decide which flagged results are treated as physically robust. A
                  finding is presented as solid only when all three agree: statistically
                  significant, non-negligible effect size, and physically coherent with the
                  PV, EGR, and AFC structure seen in the composites. Results that clear only
                  the significance bar are reported as exploratory. This is why the volcano
                  plots on the EP Differences page put effect size on one axis and
                  significance on the other — the upper-right corner is where both agree.
                </p>
              </InThisStudy>
            </div>

            {/* Multiple comparisons */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                4 · Correcting for multiple comparisons
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                Every additional test is another opportunity for a false positive. Testing
                154 variables, each with up to 3 pairwise contrasts, means that even if no
                true difference existed anywhere, roughly 5% of tests — about 8 of the 154
                global tests — would still cross <em>p</em> &lt; 0.05 by chance. Two
                corrections are applied at two different levels, because they control two
                different things.
              </p>

              <h4 className="mt-4 text-sm font-semibold text-slate-800">
                Holm — within a variable (familywise error rate)
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                Applied to the three Dunn contrasts of a single variable. The three raw{' '}
                <em>p</em>-values are sorted smallest to largest and tested against
                progressively less strict thresholds — α/3 for the smallest, α/2 for the
                next, α for the largest — stopping as soon as one fails, after which all
                remaining contrasts are declared non-significant. It controls the{' '}
                <strong>familywise error rate</strong>: the probability of making{' '}
                <em>even one</em> false claim among those three contrasts.
              </p>

              <h4 className="mt-4 text-sm font-semibold text-slate-800">
                Benjamini–Hochberg — across variables (false discovery rate)
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                Applied to the global Kruskal–Wallis <em>p</em>-values, separately within
                each analysis block (the 24 LEC terms and the dynamical descriptors are
                corrected as distinct families, since they represent conceptually different
                sets of hypotheses).
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="p_{(i^{*})} \le \frac{i^{*}}{m}\,q"
                  label="Benjamini–Hochberg criterion"
                  terms={{
                    'p₍ᵢ₎': 'The i-th smallest p-value in the block, after sorting p₍₁₎ ≤ p₍₂₎ ≤ … ≤ p₍ₘ₎',
                    'i': 'Rank of a p-value within the sorted list (1 = smallest)',
                    'i*': 'The largest rank i for which the inequality still holds',
                    'm': 'Total number of variables tested in that block',
                    'q': 'Target false discovery rate (q = 0.05 here)',
                  }}
                  notes="Every variable with rank ≤ i* is declared significant. The adjusted value reported per variable (often called a q-value) is the smallest FDR level at which that variable would still be called significant."
                />
              </div>
              <SimpleTerms>
                <p>
                  The two corrections answer different questions. Holm is strict: it asks{' '}
                  <em>&quot;what threshold keeps me from making even a single false claim
                  in this family?&quot;</em> — appropriate for three pre-specified contrasts
                  where any error matters. Benjamini–Hochberg is a screening tool: it asks{' '}
                  <em>&quot;of everything I flag as interesting, what fraction am I willing
                  to have wrong?&quot;</em> Setting <em>q</em> = 0.05 accepts that about 5%
                  of the flagged variables may be false discoveries, in exchange for far
                  more power to find the real ones. That trade is the right one when
                  screening 154 variables to decide which few deserve physical
                  interpretation; it would be the wrong one for testing a single
                  pre-registered hypothesis.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  Both corrections make results <em>harder</em> to call significant, never
                  easier: an adjusted <em>p</em> is always ≥ its raw value. The practical
                  consequence appears in the CPS results below, where one contrast has a raw{' '}
                  <em>p</em> = 0.017 — nominally significant — but a Holm-adjusted{' '}
                  <em>p</em> = 0.139, and is therefore <em>not</em> reported as an
                  established result.
                </p>
              </InThisStudy>
            </div>

            {/* Association */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                5 · Linking cyclone energetics to dynamical structure
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                This track asks a different kind of question from the EP comparisons: not
                &quot;do these groups differ?&quot; but &quot;does knowing something about a
                cyclone&apos;s dynamical field tell me something about its energetics?&quot;
                Each pairing takes one scalar descriptor of a dynamical field as the
                predictor <em>X</em> and one LEC term as the response <em>Y</em>. Three
                complementary metrics are computed for every pair, each sensitive to a
                different kind of relationship.
              </p>

              <h4 className="mt-4 text-sm font-semibold text-slate-800">
                Pearson <em>r</em> — linear association
              </h4>
              <div className="mt-2">
                <FormulaBlock
                  formula="r = \frac{\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i-\bar{x})^2}\sqrt{\sum_{i=1}^{n}(y_i-\bar{y})^2}}"
                  label="Pearson correlation coefficient"
                  terms={{
                    'r': 'Pearson correlation coefficient (dimensionless, −1 to +1)',
                    'i': 'Index over cyclones, i = 1 … n',
                    'n': 'Number of cyclones in the sample (n = 2,733 for the EPALL analysis)',
                    'x_i': 'Value of the dynamical-field descriptor for cyclone i (the predictor)',
                    'y_i': 'Value of the LEC term for cyclone i (the response)',
                    'x̄, ȳ': 'Sample means of the predictor and the response',
                  }}
                  notes="Range −1 to +1. |r| = 1 is a perfect straight-line relationship; r = 0 means no linear relationship (though a curved one may still exist). Sensitive to outliers and blind to non-linear structure."
                />
              </div>

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                Spearman <em>ρ</em> — monotonic association
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                Computed with the identical formula, but applied to the <em>ranks</em> of{' '}
                <em>x</em> and <em>y</em> rather than their raw values: each <em>x<sub>i</sub></em>{' '}
                is replaced by its position when the predictor is sorted, and likewise for{' '}
                <em>y<sub>i</sub></em>. It therefore requires only that the two quantities
                move together consistently — not that they do so along a straight line —
                and inherits the same −1 to +1 range and sign convention. This robustness
                to skewed, heavy-tailed distributions is why <em>ρ</em> is preferred over{' '}
                <em>r</em> whenever the two disagree.
              </p>
              <SimpleTerms>
                <p>
                  Rank the cyclones from lowest to highest northern-sector warm advection.
                  Separately, rank the same cyclones from lowest to highest{' '}
                  <em>A</em><sub>e</sub>. If cyclones tend to hold similar positions in both
                  queues — the ones near the top of one are near the top of the other —{' '}
                  <em>ρ</em> is positive and large. If the queues are close to reversed,{' '}
                  <em>ρ</em> is negative. If the two orderings are unrelated, <em>ρ</em> ≈ 0.
                  Pearson asks the stricter question of whether the relationship also plots
                  as a straight line.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  A <strong>positive</strong> <em>ρ</em> between the E–W contrast of{' '}
                  PV<sub>200</sub> and <em>C</em><sub>a</sub> means cyclones with a stronger
                  trough-west / ridge-east upper-level configuration also tend to have
                  stronger baroclinic conversion — consistent with classical
                  upper-level forcing of baroclinic growth. A <strong>negative</strong>{' '}
                  <em>ρ</em> between north-sector temperature advection and{' '}
                  <em>A</em><sub>e</sub> means cyclones with stronger cold advection on
                  their poleward side tend to hold <em>more</em> eddy available potential
                  energy — the sign follows from the advection being negative when cold,
                  so it reads physically as &quot;a sharper thermal contrast accompanies a
                  larger APE reservoir&quot;. When <em>r</em> and <em>ρ</em> disagree by
                  more than 0.10 in absolute value, the pair is flagged (hatched in the
                  correlation figures) as non-linear but still monotonic — plausible for
                  frontogenetic processes that intensify sharply past a threshold in the
                  thermal gradient.
                </p>
              </InThisStudy>

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                PREDEP (α<sub>Y|X</sub>) — general predictive dependence
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                Both correlation coefficients assume the relationship has a consistent
                direction. PREDEP (Assunção et al., 2025) drops that assumption entirely: it
                measures how much knowing the predictor reduces the uncertainty in
                predicting the response, capturing non-linear and even non-monotonic
                dependence that both <em>r</em> and <em>ρ</em> would report as
                approximately zero. It is the primary metric of the{' '}
                <Link href="/analyses/field-dependence/dependence-explorer" className="text-indigo-600 hover:underline">
                  dependence explorer
                </Link>, with <em>r</em> and <em>ρ</em> retained as interpretable baselines.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="\alpha_{Y|X} = \frac{S_{Y|X} - S_{Y}}{S_{Y|X}}"
                  label="PREDEP — predictive dependence"
                  terms={{
                    'α (Y|X)': 'PREDEP of the response Y given the predictor X (dimensionless, 0 to 1)',
                    'X': 'Predictor — a scalar descriptor of a dynamical field (e.g. AFC₂₅₀ domain mean)',
                    'Y': 'Response — a LEC term (e.g. Ke)',
                    'S_Y': 'Marginal prediction rate: how well Y can be predicted from its own distribution alone, ignoring X',
                    'S_(Y|X)': 'Conditional prediction rate: how well Y can be predicted once the value of X is known',
                  }}
                  notes="Range 0 to 1, and unsigned — it reports strength of dependence, not direction. α = 0 if and only if X and Y are statistically independent. α = 0.60 means that knowing X reduces the prediction loss for Y by 60% relative to not knowing it. PREDEP is asymmetric — α(Y|X) is not in general equal to α(X|Y) — and this study always runs it as dynamical feature → LEC term."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Both prediction rates are estimated non-parametrically. The estimator uses
                the identity <em>E</em>[<em>f</em>(<em>Y</em>)] = <em>f<sub>W</sub></em>(0),
                where <em>W</em> = <em>Y</em>₁ − <em>Y</em>₂ is the difference between two
                independent draws of <em>Y</em>: the density of that difference evaluated at
                zero is estimated by kernel density estimation over bootstrap pairs. The
                conditional rate applies the same procedure inside bins of{' '}
                <em>X</em> defined by Ward hierarchical clustering, weighted by the fraction
                of cyclones in each bin. Pairs with fewer than 30 cyclones are not computed.
              </p>
              <SimpleTerms>
                <p>
                  Think of it as a prediction game. First, guess a cyclone&apos;s{' '}
                  <em>K</em><sub>e</sub> knowing only how <em>K</em><sub>e</sub> is
                  distributed across the whole population — you will be wrong by some
                  typical amount. Now play again, but this time you are told the
                  cyclone&apos;s upper-level AFC first. PREDEP is the fraction of your
                  prediction error that this extra information removes. Zero means the AFC
                  told you nothing; 0.7 means it removed 70% of your uncertainty.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  Comparing the three metrics is itself diagnostic. When PREDEP ≈ |<em>r</em>|
                  ≈ |<em>ρ</em>|, the dependence is essentially linear and the correlation
                  sign can be read physically. When PREDEP is substantially larger than
                  both, the dynamical feature genuinely constrains the LEC term but not in a
                  single consistent direction — for example a descriptor where both strongly
                  positive and strongly negative values accompany large{' '}
                  <em>K</em><sub>e</sub>, which a correlation averages away to near zero.
                  Note that a high PREDEP is a statement about statistical predictability,
                  not causality: cyclone energetics and dynamical fields are mutually
                  coupled, and the physical direction must come from theory, not from α.
                </p>
              </InThisStudy>
              <p className="mt-4 text-sm text-slate-500">
                <strong>Shared caveats.</strong> These descriptors are contemporaneous,
                storm-centred, and spatially aggregated, so they diagnose covariability
                across the cyclone population rather than a mechanism in any individual
                storm. The descriptors of a given field are also not independent of one
                another — a border mean and the sector mean on the same flank share
                information — so the number of effectively independent tests is smaller than
                the number of pairs, and nominal significance should be read conservatively
                in a field-significance sense. With n = 2,733, essentially every displayed
                correlation is statistically significant, which is precisely why magnitude
                and physical coherence, not <em>p</em>-values, drive the interpretation here.
              </p>
            </div>

            {/* Trends */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                6 · Trends in Energy-Pattern occurrence
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                Annual cyclone counts per EP ({DATASET_STATS.years} values per EP, one per
                year, {DATASET_STATS.period}) are tested for monotonic trends with the
                Mann–Kendall test. <strong>H₀:</strong> the annual counts are independent
                and identically distributed — no trend. <strong>H₁:</strong> there is a
                monotonic increase or decrease. The test counts, over every pair of years,
                whether the later year had more cyclones than the earlier one, and sums
                those verdicts, so it assumes neither linearity nor normality — well suited
                to a short count series.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="S = \sum_{i=1}^{n-1}\sum_{j=i+1}^{n} \mathrm{sign}(x_j - x_i)"
                  label="Mann–Kendall statistic"
                  terms={{
                    'S': 'Mann–Kendall statistic (dimensionless; positive = upward tendency, negative = downward)',
                    'i, j': 'Indices over years, with j always later than i',
                    'n': `Number of years in the series (n = ${DATASET_STATS.years})`,
                    'x_i, x_j': 'Annual cyclone count for that EP in years i and j',
                    'sign(·)': 'Returns +1 if the later year is higher, −1 if lower, 0 if tied',
                  }}
                  notes="Under H₀, S is centred on zero. It is standardised as Z = (S − 1)/√Var(S) for S > 0 (with sign and tie corrections) and compared against the standard normal distribution to obtain the p-value. S says whether a trend exists and its direction, but not its magnitude — that requires the Theil–Sen slope."
                />
              </div>
              <div className="mt-3">
                <FormulaBlock
                  formula="\hat{\beta} = \mathrm{median}\left\{\frac{y_j - y_i}{x_j - x_i} : i < j\right\}"
                  label="Theil–Sen slope — trend magnitude"
                  terms={{
                    'β̂': 'Estimated trend magnitude, in cyclones per year',
                    'i, j': 'Indices over years, with j later than i',
                    'x_i, x_j': 'The years themselves (used as the abscissa)',
                    'y_i, y_j': 'Annual cyclone counts in years i and j',
                    'median{·}': 'Median taken over all pairs of years with i < j',
                  }}
                  notes="Units: cyclones yr⁻¹. Because it is the median of all pairwise slopes rather than a least-squares fit, a single anomalously active or quiet year cannot drag the estimate. The 95% confidence interval is taken from the distribution of those pairwise slopes; an interval that excludes zero is consistent with a detected trend."
                />
              </div>
              <SimpleTerms>
                <p>
                  Mann–Kendall and Theil–Sen split the question in two. Mann–Kendall answers{' '}
                  <em>&quot;is this EP genuinely becoming more or less frequent, or is the
                  year-to-year scatter just noise?&quot;</em> Theil–Sen answers{' '}
                  <em>&quot;if so, by how many cyclones per year?&quot;</em> Both work on
                  comparisons between pairs of years rather than on the raw counts, which is
                  what makes them resistant to one exceptional season.
                </p>
              </SimpleTerms>
              <div className="mt-4">
                <FormulaBlock
                  formula="Q(h) = n(n+2)\sum_{k=1}^{h} \frac{\hat{\rho}_k^{\,2}}{n-k}"
                  label="Ljung–Box statistic — independence check"
                  terms={{
                    'Q(h)': 'Ljung–Box portmanteau statistic (dimensionless)',
                    'h': 'Maximum lag tested (h = 10 here)',
                    'k': 'Lag index, k = 1 … h',
                    'n': `Length of the series (n = ${DATASET_STATS.years} years)`,
                    'ρ̂_k': 'Sample autocorrelation of the detrended residuals at lag k',
                  }}
                  notes="Compared against a χ² distribution with h degrees of freedom. A significant Q(h) means the residuals still carry year-to-year structure and are not independent, which would make the Mann–Kendall p-value anticonservative (too easily significant)."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Mann–Kendall assumes independent observations, so residual autocorrelation
                is checked before its <em>p</em>-value is trusted: the Theil–Sen trend is
                removed and the residuals are tested with Ljung–Box. None of the three EPs
                showed significant autocorrelation (EP1 <em>p</em> = 0.16; EP2{' '}
                <em>p</em> = 0.13; EP3 <em>p</em> = 0.05, marginally above the threshold),
                so the original Mann–Kendall test is reported for all EPs rather than a
                variance-corrected variant that would sacrifice power without cause. As a
                robustness check, the Hamed–Rao, Yue–Wang, pre-whitening, and trend-free
                pre-whitening variants were also computed and archived — all yielded the
                same conclusions about which EPs show a significant trend.
              </p>
            </div>

            {/* CPS contingency statistics */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                7 · Cyclone Phase Space: are some Energy Patterns more subtropical?
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                <strong>Scientific purpose.</strong> The Cyclone Phase Space (CPS; Hart,
                2003) describes a cyclone&apos;s thermal structure through three parameters
                — <em>B</em>, the 900–600 hPa thickness asymmetry across the storm-motion
                axis, and the lower- and upper-tropospheric thermal winds{' '}
                −<em>V</em><sub>T</sub><sup>L</sup> and −<em>V</em><sub>T</sub><sup>U</sup>,
                which diagnose whether each layer holds a warm or cold core. Applying
                thresholds to these parameters at each timestep, and requiring a state to
                persist for at least 36 h, classifies every cyclone as extratropical (EC),
                subtropical (SC), undergoing subtropical transition (ST), and so on. The
                statistical question is then categorical rather than continuous:{' '}
                <em>is a cyclone of a given Energy Pattern more likely than the pooled
                population to be subtropical, or to become subtropical?</em>
              </p>
              <p className="mt-3 text-sm text-slate-600">
                This changes the statistical machinery. The outcome is no longer a
                continuous LEC term but a count of cyclones falling into classes, so the
                rank-based tests above do not apply. The population also differs from
                tracks 1–5: because no ≥ 24 h intensification filter is needed here, all{' '}
                <strong>3,812 EP-labelled cyclones</strong> are used (EP1 = 441, EP2 = 978,
                EP3 = 2,393). Note that the pooled reference &quot;EPALL&quot; in this track
                means the union EP1 + EP2 + EP3, not the full catalogue — only clustered
                cyclones carry an Energy Pattern, so the reference must be the same
                population the EPs partition. The logic of the chain, however, is identical
                to track 1:
              </p>
              <TestFlow
                steps={[
                  'χ² contingency (global)',
                  "Cramér's V (global effect)",
                  'Fisher exact (post-hoc)',
                  'Holm',
                  'Odds ratio (pairwise effect)',
                ]}
              />

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                Global test — χ² test of independence
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                <strong>H₀:</strong> Energy Pattern and CPS phase class are independent —
                knowing a cyclone&apos;s EP tells you nothing about which phase class it
                falls into. <strong>H₁:</strong> the two are associated. The test compares
                the observed count in every EP × class cell against the count expected if
                the row and column totals were combined independently.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="\chi^2 = \sum_{i}\sum_{j} \frac{(O_{ij} - E_{ij})^2}{E_{ij}}, \qquad E_{ij} = \frac{R_i\,C_j}{n}"
                  label="Chi-square statistic for a contingency table"
                  terms={{
                    'χ²': 'Chi-square statistic (dimensionless, ≥ 0)',
                    'i': 'Row index — the Energy Pattern (EP1, EP2, EP3)',
                    'j': 'Column index — the CPS phase class (EC, SC, ST, SD, …)',
                    'O_ij': 'Observed number of cyclones in EP i with phase class j',
                    'E_ij': 'Expected count in that cell if EP and phase class were independent',
                    'R_i': 'Row total — all cyclones in EP i',
                    'C_j': 'Column total — all cyclones of phase class j',
                    'n': 'Grand total of EP-labelled classified cyclones (n = 3,812)',
                  }}
                  notes="Compared against a χ² distribution with (rows − 1)(columns − 1) degrees of freedom. χ² ≈ 0 means observed counts match the independence expectation; large χ² means at least one cell is over- or under-populated relative to chance."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Two diagnostics accompany the test. <strong>Standardised residuals</strong>,
                <em> z<sub>ij</sub></em> = (<em>O<sub>ij</sub></em> − <em>E<sub>ij</sub></em>)
                / √<em>E<sub>ij</sub></em>, locate <em>which</em> cells drive a significant
                result; cells with |<em>z</em>| &gt; 2 are flagged. And{' '}
                <strong>Cochran&apos;s condition</strong> is checked — the χ² approximation
                becomes unreliable when more than 20% of cells have an expected count below
                5. In the full EP × phase-class table, 7 of 27 cells fall below that
                threshold, so the condition is violated and reported as such; this is
                precisely why the inferential claims rest on the exact test below rather
                than on χ² alone.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="V = \sqrt{\frac{\chi^2}{n\,(\min(r,\,c) - 1)}}"
                  label="Cramér's V — global effect size"
                  terms={{
                    'V': "Cramér's V, the strength of association (dimensionless, 0 to 1)",
                    'χ²': 'Chi-square statistic from above',
                    'n': 'Grand total of cyclones in the table',
                    'r, c': 'Number of rows (3 EPs) and columns (phase classes) in the table',
                    'min(r, c)': 'The smaller of the two dimensions — this is what bounds V at 1',
                  }}
                  notes="Range 0 to 1, unsigned. V = 0: no association at all. V = 1: phase class is perfectly determined by EP. Conventionally V ≈ 0.1 is a weak association, 0.3 moderate, 0.5 strong. Like ε², it does not inflate with sample size."
                />
              </div>
              <InThisStudy>
                <p>
                  The full EP × phase-class table gives χ² = 39.69 on 16 degrees of freedom,{' '}
                  <em>p</em> = 8.6 × 10⁻⁴ — highly significant — but Cramér&apos;s{' '}
                  <em>V</em> = 0.072, a weak association. This is the clearest example on
                  this site of why both numbers must be read together: Energy Pattern and
                  thermal phase class are genuinely, non-randomly related, yet EP membership
                  explains only a small part of which phase class a cyclone ends up in. The
                  standardised residuals then point to where that modest association lives —
                  most strongly EP2 × ST (92 observed vs 67.5 expected, <em>z</em> = +3.0).
                </p>
              </InThisStudy>

              <h4 className="mt-5 text-sm font-semibold text-slate-800">
                Post-hoc test — Fisher&apos;s exact test
              </h4>
              <p className="mt-2 text-sm text-slate-600">
                <strong>What it compares:</strong> each EP against the other two pooled, on
                a single binary outcome (e.g. &quot;did this cyclone undergo a subtropical
                transition, yes or no?&quot;), giving a 2×2 table.{' '}
                <strong>Why Fisher rather than χ²:</strong> Fisher&apos;s test computes the{' '}
                <em>exact</em> probability of the observed table from the hypergeometric
                distribution instead of relying on a large-sample approximation, so it stays
                valid precisely where χ² fails — with small cell counts, which is the
                situation here (only 24 EP1 cyclones undergo subtropical transition).{' '}
                <strong>Why against the other two pooled:</strong> comparing an EP against
                EPALL would be invalid, because each EP is nested inside EPALL — the
                comparison would partly compare the group with itself. Contrasting EP1
                against EP2+EP3 gives two genuinely independent samples.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="\mathrm{OR} = \frac{a\,/\,(n_A - a)}{b\,/\,(n_B - b)}"
                  label="Odds ratio — pairwise effect size"
                  terms={{
                    'OR': 'Odds ratio (dimensionless, 0 to ∞; no effect at OR = 1)',
                    'a': 'Cyclones in the focal EP showing the outcome (e.g. EP2 cyclones that underwent ST)',
                    'n_A': 'Total cyclones in the focal EP',
                    'n_A − a': 'Cyclones in the focal EP not showing the outcome',
                    'b': 'Cyclones in the other two EPs pooled showing the outcome',
                    'n_B': 'Total cyclones in the other two EPs pooled',
                  }}
                  notes="OR > 1: the outcome is more likely in the focal EP than in the rest. OR = 1: equally likely. OR < 1: less likely. OR = 2 means the odds are doubled — not that the probability doubles, which is a common misreading when the outcome is not rare."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Frequencies within each EP are reported with{' '}
                <strong>Wilson score 95% intervals</strong> rather than the textbook
                (Wald) interval, because several outcome counts are small and near-zero
                proportions would otherwise produce intervals extending below zero — an
                impossible frequency. Nine contrasts are tested in total (3 EPs × 3
                outcomes: SC, ST, and their union), and{' '}
                <strong>Holm correction</strong> is applied across all nine.
              </p>
              <SimpleTerms>
                <p>
                  χ² tells you that Energy Pattern and thermal phase class are related
                  somewhere in the table. Fisher&apos;s exact test then asks the specific,
                  answerable question — <em>is EP2 more prone to subtropical transition than
                  EP1 and EP3 combined?</em> — and the odds ratio says by how much. Exactly
                  as with Kruskal–Wallis and Dunn, the global test locates a signal and the
                  post-hoc test names it.
                </p>
              </SimpleTerms>
              <InThisStudy>
                <p>
                  Of the nine contrasts, only <strong>EP2 × ST</strong> survives Holm
                  correction: 9.41% of EP2 cyclones undergo subtropical transition versus
                  6.03% of the others, OR = 1.62, raw <em>p</em> = 5.5 × 10⁻⁴, Holm-adjusted{' '}
                  <em>p</em> = 5.0 × 10⁻³. The EP3 depletion in ST is nominally significant
                  (raw <em>p</em> = 0.017) but does <em>not</em> survive correction
                  (Holm <em>p</em> = 0.139), and is therefore not reported as an established
                  result — a concrete illustration of what the correction in track 4 buys.
                  Because EP2 forms further equatorward than EP1 and EP3, and hybrid
                  structure is itself a subtropical-latitude phenomenon, the association is
                  additionally re-tested within each genesis region (ARG, LA-PLATA, SE-BR);
                  an association that persists inside each region is not merely a
                  geographic artefact.
                </p>
              </InThisStudy>
              <p className="mt-4 text-sm text-slate-500">
                <strong>How to read the CPS figures.</strong> In the relative-frequency
                figure, panel (a) shows each EP&apos;s absolute frequency with its Wilson
                interval, and panel (b) the ratio to the EPALL rate. That ratio is a{' '}
                <em>descriptive</em> effect size only — the numerator is nested in the
                denominator — so significance is never read from it; it comes from the
                Fisher contrasts. Filled markers indicate contrasts that survive Holm
                correction, open markers those that are only nominally significant. Full
                results are on the{' '}
                <Link href="/analyses/cps" className="text-indigo-600 hover:underline">
                  Cyclone Phase Space
                </Link>{' '}
                page.
              </p>
            </div>

            {/* Synthesis */}
            <ResultSummaryCallout type="info" title="Putting it together">
              <p>
                Across all four tracks the same discipline applies. A global test
                (Kruskal–Wallis, Mann–Kendall, χ²) establishes only that{' '}
                <em>something</em> is there; a post-hoc test (Dunn, Fisher) says{' '}
                <em>where</em>; a correction (Holm, Benjamini–Hochberg) keeps the extra
                questions honest; and an effect size (ε², r<sub>rb</sub>, Cramér&apos;s{' '}
                <em>V</em>, odds ratio, or the correlation magnitude itself) says whether the
                difference is large enough to matter. A result is presented as robust on
                this site only when statistical significance, a non-negligible effect size,
                and physical consistency with the composite fields all point the same way.
                Where they diverge — a tiny <em>p</em> with a negligible effect, or a
                nominal significance that dissolves under correction — the result is
                reported as exploratory, and said to be so.
              </p>
            </ResultSummaryCallout>

            {/* Cross-link */}
            <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-5">
              <p className="text-sm text-slate-700">
                See these methods applied: significance and effect-size heatmaps, volcano
                plots, and the PREDEP / Pearson / Spearman explorer in{' '}
                <Link href="/analyses/field-dependence" className="font-medium text-indigo-600 hover:underline">
                  LEC–Field Dependence
                </Link>
                ; the χ² and Fisher contingency results in{' '}
                <Link href="/analyses/cps" className="font-medium text-indigo-600 hover:underline">
                  Cyclone Phase Space
                </Link>
                .
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
