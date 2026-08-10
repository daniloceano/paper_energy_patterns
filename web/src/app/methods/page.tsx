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
                      ['T', 'Temperature [K]'],
                      ['u, v', 'Zonal / meridional wind [m s⁻¹]'],
                      ['ω', 'Vertical pressure velocity [Pa s⁻¹]'],
                      ['q', 'Diabatic heating rate [W kg⁻¹]'],
                      ['cₚ', 'Specific heat at constant pressure [J kg⁻¹ K⁻¹]'],
                      ['g', 'Gravitational acceleration [m s⁻²]'],
                      ['R', 'Gas constant for dry air [J kg⁻¹ K⁻¹]'],
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
                title: 'Step 1: Data filtering and standardisation',
                content:
                  'Cyclones with incomplete lifecycle phases are removed. The 7 energy terms are standardised (μ=0, σ=1) independently for each phase.',
              },
              {
                title: 'Step 2: Phase-separated PCA',
                content:
                  'Independent PCA is applied per lifecycle phase (incipient, intensification, mature, decay), retaining ≥97% variance. Typically 6 out of 7 PCs are kept.',
              },
              {
                title: 'Step 3: Optimal k determination',
                content:
                  '5 cluster validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, Gap Statistic) are computed for k=3–15 and normalised. Ensemble averaging identifies k=3.',
              },
              {
                title: 'Step 4: K-Means clustering',
                content:
                  "K-Means (k=3, n_init=100, random_state=42) with K-Means++ initialisation is applied per phase. Clusters are labelled EP1, EP2, EP3 by Ck magnitude.",
              },
              {
                title: 'Step 5: ERA5 composite analysis',
                content:
                  'Storm-centred 30°×30° composites of 9 diagnostic fields are computed for EP1 and EP2 during intensification. Anomalies use 1991–2020 WMO monthly climatology.',
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
            Three questions needed a dedicated statistical treatment beyond the clustering
            step itself: (1) are EP1, EP2, and EP3 truly distinguishable in their LEC
            diagnostics and dynamical structure, and not just the nearest-centroid label of
            an underlying continuum? (2) how strongly does cyclone energetics covary with the
            dynamical fields shown in the composite pages? and (3) are the interannual
            fluctuations in EP occurrence ({DATASET_STATS.period}) genuine long-term trends,
            or consistent with sampling noise? These map onto three tracks below: inter-EP
            comparison, association analysis, and trend analysis.
          </p>

          <div className="space-y-4">
            {/* Inter-EP differences */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Testing whether Energy Patterns differ
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                For all 24 LEC terms plus 13 scalar descriptors summarising each
                storm-centred dynamical field (domain mean, mean absolute value, centre
                value, N/S/E/W sector and border means, and N–S/E–W contrasts) — 154
                variables in total — a sequential decision procedure picks the correct
                global test and post-hoc comparison based on that variable&apos;s own
                distributional properties, rather than assuming one test fits everything.
              </p>
              <div className="mt-3">
                <StatsTable
                  title="Decision procedure"
                  columns={[
                    { key: 'condition', label: 'Distribution' },
                    { key: 'global', label: 'Global test' },
                    { key: 'posthoc', label: 'Post-hoc' },
                    { key: 'effect', label: 'Effect size' },
                  ]}
                  rows={[
                    { condition: 'Normal, equal variance', global: 'One-way ANOVA', posthoc: 'Tukey HSD', effect: 'ω²' },
                    { condition: 'Normal, unequal variance', global: "Welch's ANOVA", posthoc: 'Welch t-tests (Holm)', effect: 'ω²' },
                    { condition: 'Non-normal (≥1 group)', global: 'Kruskal–Wallis', posthoc: 'Dunn (Holm)', effect: 'ε²' },
                  ]}
                  caption="Normality: Shapiro–Wilk per EP group. Homogeneity: Brown–Forsythe (median-centred Levene)."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Every one of the 154 variables tested in this study departed from normality
                in at least one EP group, so all inter-EP comparisons reported here follow
                the third row of the table: Kruskal–Wallis as the global (&quot;is there a
                difference at all?&quot;) test, and Dunn&apos;s test as the post-hoc
                (&quot;which pair differs?&quot;) step. Kruskal–Wallis pools and ranks all
                cyclones from the three EPs jointly; if EP1&apos;s values for a term such as
                C<sub>K</sub> sit systematically above EP2&apos;s and EP3&apos;s once
                everyone is sorted together, the test statistic H grows large — regardless
                of whether the underlying distributions are Gaussian, skewed, or
                multimodal, which is exactly the robustness LEC terms need.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="H = \frac{12}{N(N+1)} \sum_{c=1}^{3} \frac{R_c^2}{n_c} - 3(N+1)"
                  label="Kruskal–Wallis statistic"
                  terms={{
                    'R_c': 'Sum of joint ranks in EP c',
                    'n_c': 'Number of cyclones in EP c',
                    'N': 'Total sample size (n₁+n₂+n₃)',
                  }}
                  notes="A significant H only shows the three EPs are not all identical — it does not say which pair differs. That requires the Dunn post-hoc step."
                />
              </div>
            </div>

            {/* Effect size */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Effect size: how large the difference is, not just whether it exists
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                With EP sample sizes from a few hundred to over two thousand cyclones, even
                physically trivial differences can reach statistical significance. Effect
                size quantifies the practical magnitude of a difference, independent of
                sample size, and is reported alongside every global and pairwise comparison.
              </p>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <FormulaBlock
                  formula="\varepsilon^2 = \frac{H - k + 1}{N - k}"
                  label="Epsilon² (global, Kruskal–Wallis)"
                  terms={{ 'k': 'Number of EPs (3)' }}
                />
                <FormulaBlock
                  formula="r_{rb} = 1 - \frac{2U}{n_i\,n_j}"
                  label="Rank-biserial r (pairwise, Dunn)"
                  terms={{ 'U': 'Mann–Whitney U statistic' }}
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                In practice, <em>r<sub>rb</sub></em> is the difference between the
                probability that a random cyclone from EP <em>i</em> exceeds one from EP{' '}
                <em>j</em>, and the reverse probability — a genuinely probabilistic effect
                size, not just a rescaled test statistic. Its sign shows which EP has the
                larger value; e.g. a positive EP1-vs-EP2 contrast for C<sub>K</sub> means
                EP1 has systematically larger (more positive) barotropic conversion.
              </p>
              <div className="mt-3">
                <StatsTable
                  columns={[
                    { key: 'mag', label: 'Magnitude' },
                    { key: 'eps', label: 'ε² (Rea & Parker, 1992)' },
                    { key: 'rrb', label: '|r_rb| (Cohen, 1988)' },
                  ]}
                  rows={[
                    { mag: 'Negligible', eps: '< 0.01', rrb: '< 0.10' },
                    { mag: 'Small', eps: '0.01 – 0.06', rrb: '0.10 – 0.30' },
                    { mag: 'Medium', eps: '0.06 – 0.14', rrb: '0.30 – 0.50' },
                    { mag: 'Large', eps: '≥ 0.14', rrb: '≥ 0.50' },
                  ]}
                />
              </div>
            </div>

            <ResultSummaryCallout type="warning" title="A significant p-value is not a big difference">
              <p>
                A <em>p</em>-value only says how surprising the data would be if there were
                truly no difference — it says nothing about magnitude. With hundreds to
                thousands of cyclones per EP, tests here are highly powered: even small,
                physically marginal differences can register as &quot;significant&quot; at
                <em> p</em> &lt; 0.05. Throughout this study, adjusted <em>p</em>-values are
                used as a screening step to flag candidates, while effect size and
                consistency with the composite dynamical fields determine which results are
                treated as physically robust rather than exploratory.
              </p>
            </ResultSummaryCallout>

            {/* Multiple comparisons */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Correcting for multiple comparisons
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                Testing 154 variables, each with up to 3 pairwise contrasts, inflates the
                chance of false positives: at α = 0.05, roughly 8 of 154 independent tests
                would appear &quot;significant&quot; by chance alone even if no true
                differences existed. Two corrections are applied, at different levels:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-slate-600">
                <li>
                  <strong className="text-slate-800">Holm (within a variable):</strong> the
                  three Dunn pairwise contrasts (EP1–EP2, EP1–EP3, EP2–EP3) are corrected
                  sequentially, controlling the probability of <em>any</em> false positive
                  among that variable&apos;s three contrasts.
                </li>
                <li>
                  <strong className="text-slate-800">Benjamini–Hochberg FDR (across variables):</strong>{' '}
                  the global Kruskal–Wallis <em>p</em>-values are corrected within each
                  analysis block (LEC terms vs. dynamical descriptors, corrected
                  separately), controlling the <em>expected proportion</em> of false
                  discoveries among all variables flagged as significant.
                </li>
              </ul>
              <div className="mt-3">
                <FormulaBlock
                  formula="p_{(i^{*})} \le \frac{i^{*}}{m}\,q"
                  label="Benjamini–Hochberg criterion"
                  terms={{
                    'p_{(1)} \\le \\dots \\le p_{(m)}': 'Sorted p-values across the m variables in a block',
                    'i^{*}': 'Largest rank satisfying the inequality',
                    'q': 'Target FDR level (0.05)',
                  }}
                  notes="All variables with rank ≤ i* are declared significant at FDR level q."
                />
              </div>
            </div>

            {/* Association */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Linking cyclone energetics to dynamical structure
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                For each pair of a canonical LEC term and a scalar descriptor of a
                dynamical field, both Pearson&apos;s <em>r</em> (linear association) and
                Spearman&apos;s <em>ρ</em> (monotonic association, computed on ranks) are
                calculated. Spearman&apos;s <em>ρ</em> is the primary interpretive metric
                because it is more robust to the skewed, heavy-tailed distributions typical
                of LEC terms.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="r = \frac{\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i-\bar{x})^2}\sqrt{\sum_{i=1}^{n}(y_i-\bar{y})^2}}"
                  label="Pearson correlation coefficient"
                  notes="Spearman's ρ uses the identical formula computed on the within-variable ranks of x and y instead of their raw values."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                If larger west-sector cold-air advection is systematically associated with
                larger eddy APE (A<sub>e</sub>), the correlation is positive; if stronger
                advection instead coincides with weaker A<sub>e</sub>, it is negative. When{' '}
                <em>r</em> and <em>ρ</em> disagree substantially (|<em>r</em>| − |<em>ρ</em>|
                &gt; 0.10 in absolute difference), that is treated as a flag for a
                non-linear-but-monotonic relationship — for example, an association that
                strengthens sharply only past some threshold, physically plausible for
                processes such as frontogenesis.
              </p>
            </div>

            {/* Trends */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Trends in Energy-Pattern occurrence
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                Annual cyclone counts per EP ({DATASET_STATS.years} years,{' '}
                {DATASET_STATS.period}) are tested for monotonic trends with the
                Mann–Kendall test, which only asks whether later years tend to exceed
                earlier ones across all pairs — no assumption of linearity or normality is
                required, which suits a short, count-based series.
              </p>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <FormulaBlock
                  formula="S = \sum_{i=1}^{n-1}\sum_{j=i+1}^{n} \mathrm{sign}(x_j - x_i)"
                  label="Mann–Kendall statistic"
                />
                <FormulaBlock
                  formula="\hat{\beta} = \mathrm{median}\left\{\frac{y_j - y_i}{x_j - x_i} : i < j\right\}"
                  label="Theil–Sen slope"
                  notes="Median of all pairwise slopes — far less sensitive to a single anomalous year than an ordinary-least-squares fit."
                />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Because Mann–Kendall assumes independent observations, residual
                autocorrelation (after removing the Theil–Sen trend) is checked with a
                Ljung–Box test at lag h = 10. None of the three EPs showed significant
                autocorrelation (EP1 <em>p</em> = 0.16; EP2 <em>p</em> = 0.13; EP3{' '}
                <em>p</em> = 0.05, marginal), so the original Mann–Kendall test is reported
                for all EPs rather than a variance-corrected variant. As a robustness check,
                the Hamed–Rao, Yue–Wang, pre-whitening, and trend-free pre-whitening
                variants were also computed — all yielded the same conclusions about which
                EPs show a significant trend.
              </p>
            </div>

            {/* Cross-link */}
            <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-5">
              <p className="text-sm text-slate-700">
                See the interactive significance heatmaps, effect-size heatmaps, volcano
                plots, and the PREDEP/Pearson/Spearman dependence explorer built on this
                same framework in{' '}
                <Link href="/analyses/field-dependence" className="font-medium text-indigo-600 hover:underline">
                  LEC–Field Dependence
                </Link>.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
