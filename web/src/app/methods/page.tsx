import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import MethodologyAccordion from '@/components/analysis/MethodologyAccordion'
import { ENERGY_TERM_INFO, DATASET_STATS } from '@/lib/constants'
import type { EnergyTerm } from '@/lib/types'

export const metadata: Metadata = {
  title: 'Methods',
  description: 'Methodology, energy terms, and data description.',
}

export default function MethodsPage() {
  const termEntries = Object.entries(ENERGY_TERM_INFO) as [EnergyTerm, typeof ENERGY_TERM_INFO[EnergyTerm]][]

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

        {/* Energy terms */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Lorenz Energy Cycle Terms
          </h2>
          <p className="mb-6 text-sm text-slate-600">
            Seven terms from the semi-Lagrangian Lorenz Energy Cycle are used as features
            for clustering. Each term is computed for the storm-centred domain at each
            timestep and averaged per lifecycle phase.
          </p>

          <div className="space-y-4">
            {termEntries.map(([key, info]) => (
              <div
                key={key}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">
                    {key}
                  </span>
                  <h3 className="font-semibold text-slate-900">{info.name}</h3>
                  <span className="text-xs text-slate-400">[{info.unit}]</span>
                </div>
                <p className="mt-2 text-sm text-slate-600">{info.description}</p>
                {info.formula && (
                  <div className="mt-3">
                    <FormulaBlock formula={info.formula} label={`${key} formula`} />
                  </div>
                )}
              </div>
            ))}
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

        {/* Boundary flux and energy reservoir formulas */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Energy Reservoir and Boundary Flux Formulas
          </h2>
          <p className="mb-4 text-sm text-slate-600">
            The following quantities quantify the energy budget of the storm-centred domain.
            They are derived from the semi-Lagrangian Lorenz Energy Cycle framework
            (Michaelides 1987; Muñoz &amp; Garreaud 2005), adapted to a limited-area
            storm-following domain.
          </p>

          <div className="space-y-6">
            {/* AE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="mb-2 flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">A_E</span>
                <h3 className="font-semibold text-slate-900">Eddy Available Potential Energy</h3>
                <span className="text-xs text-slate-400">[J m⁻²]</span>
              </div>
              <p className="mb-3 text-sm text-slate-600">
                Available potential energy associated with eddy temperature perturbations — the
                reservoir of energy that can be released by baroclinic instability.
              </p>
              <FormulaBlock
                formula="A_E = \int_{p_t}^{p_b} \frac{\left[(T)_\lambda^{2}\right]_{\lambda \phi}}{2[\sigma]_{\lambda \phi}} \, dp"
                label="Eddy APE"
              />
            </div>

            {/* KE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="mb-2 flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">K_E</span>
                <h3 className="font-semibold text-slate-900">Eddy Kinetic Energy</h3>
                <span className="text-xs text-slate-400">[J m⁻²]</span>
              </div>
              <p className="mb-3 text-sm text-slate-600">
                Kinetic energy associated with the eddy wind components — grows as the cyclone
                deepens and barotropic/baroclinic conversions feed the circulation.
              </p>
              <FormulaBlock
                formula="K_E = \int_{p_t}^{p_b} \frac{\left[(u)_\lambda^2 + (v)_\lambda^2\right]_{\lambda \phi}}{2g} \, dp"
                label="Eddy KE"
              />
            </div>

            {/* GE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="mb-2 flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">G_E</span>
                <h3 className="font-semibold text-slate-900">Eddy APE Generation</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mb-3 text-sm text-slate-600">
                Diabatic creation of eddy APE, primarily through latent heat release in deep
                convection. Positive G<sub>E</sub> indicates cyclogenetic heating enhancing the
                thermal contrast.
              </p>
              <FormulaBlock
                formula="G_E = \int_{p_t}^{p_b} \frac{\left[(q)_\lambda (T)_\lambda\right]_{\lambda \phi}}{c_p[\sigma]_{\lambda \phi}} \, dp"
                label="Eddy APE generation"
              />
            </div>

            {/* BAE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="mb-2 flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">BAE</span>
                <h3 className="font-semibold text-slate-900">Eddy APE Boundary Flux</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mb-3 text-sm text-slate-600">
                Transport of eddy available potential energy across the lateral and vertical
                boundaries of the storm-centred domain. Positive BAE means APE is being
                imported from outside the domain; negative means export. EP1 cyclones tend
                toward negative BAE (energy exporters); EP2 toward positive (importers).
              </p>
              <FormulaBlock
                formula={`\\mathrm{BAE} = c_1 \\int_{p_1}^{p_2} \\int_{\\varphi_1}^{\\varphi_2}
\\frac{1}{2[\\sigma]_{\\lambda \\varphi}}\\left[u(T)_\\lambda^2\\right]_{\\lambda_1}^{\\lambda_2}
d\\varphi\\, dp
\\;+\\; c_2 \\int_{p_1}^{p_2}
\\frac{1}{2[\\sigma]_{\\lambda \\varphi}}
\\left(\\left[(T)_\\lambda^2 v\\right]_\\lambda \\cos\\varphi\\right)_{\\varphi_1}^{\\varphi_2} dp
\\;-\\; \\left(\\frac{\\left[\\omega(T)_\\lambda^2\\right]_{\\lambda \\varphi}}{2[\\sigma]_{\\lambda \\varphi}}\\right)_{p_1}^{p_2}`}
                label="Eddy APE boundary flux"
              />
              <p className="mt-3 text-xs text-slate-500">
                c₁ and c₂ are geometric constants accounting for spherical grid spacing.
                The three integrals correspond to zonal (East-West), meridional (North-South),
                and vertical boundary contributions respectively.
              </p>
            </div>

            {/* BKE */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="mb-2 flex items-center gap-3">
                <span className="rounded-lg bg-indigo-100 px-2.5 py-1 font-mono text-sm font-bold text-indigo-700">BKE</span>
                <h3 className="font-semibold text-slate-900">Eddy KE Boundary Flux</h3>
                <span className="text-xs text-slate-400">[W m⁻²]</span>
              </div>
              <p className="mb-3 text-sm text-slate-600">
                Transport of eddy kinetic energy across the domain boundaries. Negative BKE
                in EP1 cyclones reflects strong energy export (downstream effect); positive
                BKE in EP2 indicates that the cyclone draws kinetic energy from its
                surroundings (energy import, consistent with external forcing).
              </p>
              <FormulaBlock
                formula={`\\mathrm{BKE} = c_1 \\int_{p_1}^{p_2} \\int_{\\varphi_1}^{\\varphi_2}
\\frac{1}{2g}\\left(u\\left[(u)_\\lambda^2+(v)_\\lambda^2\\right]\\right)_{\\lambda_1}^{\\lambda_2}
d\\varphi\\, dp
\\;+\\; c_2 \\int_{p_1}^{p_2}
\\frac{1}{2g}
\\left(\\left[v\\cos\\varphi\\left[(u)_\\lambda^2+(v)_\\lambda^2\\right]\\right]_\\lambda\\right)_{\\varphi_1}^{\\varphi_2} dp
\\;-\\; \\left(\\frac{1}{2g}\\left[\\omega\\left[(u)_\\lambda^2+(v)_\\lambda^2\\right]\\right]_{\\lambda \\varphi}\\right)_{p_1}^{p_2}`}
                label="Eddy KE boundary flux"
              />
              <p className="mt-3 text-xs text-slate-500">
                As in BAE, the three integrals correspond to zonal, meridional, and vertical
                boundary contributions. Spherical geometry constants c₁, c₂ as defined above.
              </p>
            </div>

            {/* Symbol table */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="mb-3 font-semibold text-slate-900">Symbol Reference</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs text-slate-600">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="py-2 pr-4 text-left font-semibold text-slate-700">Symbol</th>
                      <th className="py-2 pr-4 text-left font-semibold text-slate-700">Definition</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {[
                      ['(·)λ', 'Eddy (longitudinal departure from zonal mean)'],
                      ['[·]λφ', 'Domain-averaged quantity'],
                      ['σ', 'Static stability parameter σ = −(α/θ)(∂θ/∂p)'],
                      ['T', 'Temperature [K]'],
                      ['u, v', 'Zonal / meridional wind [m s⁻¹]'],
                      ['ω', 'Vertical velocity in pressure coordinates [Pa s⁻¹]'],
                      ['q', 'Diabatic heating rate [W kg⁻¹]'],
                      ['cₚ', 'Specific heat at constant pressure [J kg⁻¹ K⁻¹]'],
                      ['g', 'Gravitational acceleration [m s⁻²]'],
                      ['p_t, p_b', 'Top and bottom pressure levels of integration'],
                      ['p₁, p₂, φ₁, φ₂', 'Domain boundary levels (pressure, latitude)'],
                      ['λ₁, λ₂', 'Domain boundary longitudes'],
                      ['c₁, c₂', 'Spherical geometry constants (zonal/meridional)'],
                    ].map(([sym, def]) => (
                      <tr key={sym}>
                        <td className="py-1.5 pr-4 font-mono">{sym}</td>
                        <td className="py-1.5">{def}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
      </div>
    </div>
  )
}
