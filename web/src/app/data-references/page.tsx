import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import ReferenceList from '@/components/analysis/ReferenceList'
import { DATASET_STATS, KEY_REFERENCES } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Data & References',
  description:
    'Dataset description, Lorenz Energy Cycle term definitions, and the bibliography shared across all analyses.',
}

export default function DataReferencesPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Data & References"
        badge="Shared Reference"
        description="The material every analysis depends on: the ERA5 and cyclone-track dataset, the seven Lorenz Energy Cycle terms with their formulas and symbols, and the bibliography. Analysis-specific methods and statistics are documented in the Methods & Statistics panel on each analysis page."
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

        {/* Grid conventions */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">Grid Conventions</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-600">
              All spatial derivatives use centred finite differences at interior grid
              points, with one-sided differences at the domain boundaries. Distances follow
              spherical geometry:
            </p>
            <div className="mt-3">
              <FormulaBlock
                formula="dy = R_\oplus\,\Delta\varphi, \qquad dx = R_\oplus\,\cos(\varphi)\,\Delta\lambda"
                label="Grid spacing on the sphere"
                terms={{
                  'dx, dy': 'Zonal and meridional grid spacing [m]',
                  'R⊕': 'Earth’s radius, 6.371 × 10⁶ m',
                  'φ': 'Latitude',
                  'Δφ, Δλ': 'Grid increments in latitude and longitude [radians]',
                }}
                notes="The cos(φ) factor accounts for meridians converging towards the pole, so a fixed longitude increment spans a shorter distance at higher latitude."
              />
            </div>
          </div>
        </section>

        {/* Bibliography */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">References</h2>
          <ReferenceList references={KEY_REFERENCES} title="Key References" />
        </section>

        {/* Data sources */}
        <section>
          <h2 className="mb-3 text-xl font-bold text-slate-900">Data Sources</h2>
          <p className="mb-4 text-sm text-slate-600">
            The archived datasets underlying every figure on this site. Citing these DOIs
            reproduces the exact inputs used here.
          </p>
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                Cyclone Tracks and Energetics
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Combined cyclone tracks and semi-Lagrangian Lorenz Energy Cycle diagnostics
                (1979–2020, ~6,700 cyclones, 42 years).
              </p>
              <a
                href="https://doi.org/10.5281/zenodo.18133432"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
              >
                DOI: 10.5281/zenodo.18133432
              </a>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                LEC Results with Vertical Resolution
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Complete LEC results with vertical resolution (~1,500 cyclones, 32 pressure
                levels, 3-hourly).
              </p>
              <a
                href="https://doi.org/10.5281/zenodo.18243447"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
              >
                DOI: 10.5281/zenodo.18243447
              </a>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">ERA5 Reanalysis</h3>
              <p className="mt-1 text-sm text-slate-600">
                Hersbach et al. (2020). Source fields for all energetics, composites and
                phase-space diagnostics, at {DATASET_STATS.era5Resolution} horizontal
                resolution.
              </p>
              <a
                href="https://doi.org/10.1002/qj.3803"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
              >
                DOI: 10.1002/qj.3803
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
