import type { Metadata } from 'next'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import FigurePanel from '@/components/analysis/FigurePanel'
import InlineMath from '@/components/analysis/InlineMath'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import verticalData from '@/content/vertical_structure.json'

export const metadata: Metadata = {
  title: 'Vertical Structure of Energy Conversions',
  description:
    'Corrected pressure-level structure of baroclinic and barotropic energy conversion for EP1, EP2, and EP3 cyclones.',
}

const EP_IDS = ['EP1', 'EP2', 'EP3'] as const

function signed(value: number, digits = 2) {
  return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(digits)}`
}

export default function VerticalStructurePage() {
  const ep1 = verticalData.patterns.EP1
  const ep2 = verticalData.patterns.EP2
  const ep3 = verticalData.patterns.EP3

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Vertical Structure of Energy Conversions"
        subtitle="Corrected intensification-phase profiles"
        badge="Complete Corrected Population"
        description={`Pressure-level distributions of baroclinic and barotropic conversion for all ${verticalData.population.total.toLocaleString()} corrected cyclones, separated into EP1, EP2, and EP3.`}
      />

      <div className="space-y-10">
        <ResultSummaryCallout type="result" title="Complete and internally consistent profiles">
          <p>
            Every corrected cyclone is represented at {verticalData.population.levels_available}{' '}
            pressure levels. Exact integration checks were possible for{' '}
            {verticalData.validation.single_interval_cyclones_checked.toLocaleString()} cyclones
            with one intensification interval ({verticalData.validation.comparison_rows.toLocaleString()}{' '}
            term comparisons); the maximum absolute discrepancy was{' '}
            {verticalData.validation.maximum_absolute_error.toExponential(2)} W m⁻².
          </p>
        </ResultSummaryCallout>

        <MethodsPanel summary="How the pressure-level profiles, column integrals, dominant levels, and signs are defined.">
          <div className="space-y-3 text-sm leading-relaxed text-slate-600">
            <p>
              Profiles are cyclone means over the intensification phase. The plotted quantity is
              the pressure integrand ({verticalData.units.profile}); integrating it from 10 to
              1,000 hPa gives the column conversion in {verticalData.units.integrated}.
            </p>
            <p>
              <InlineMath expr="C_A>0" /> transfers zonal available potential energy to eddy
              available potential energy. <InlineMath expr="C_K<0" /> transfers zonal kinetic
              energy to eddy kinetic energy, while <InlineMath expr="C_K>0" /> represents the
              reverse transfer. Stars mark the pressure level with the largest absolute median
              profile value for each Energy Pattern; they do not represent a significance test.
            </p>
            <p>
              The figure displays {verticalData.population.display_range_hpa[0]}–
              {verticalData.population.display_range_hpa[1]} hPa. The omitted 10–100 hPa layer
              contributes less than 0.04 W m⁻² to the EP-mean column conversions.
            </p>
          </div>
        </MethodsPanel>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Column totals and dominant levels</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Pattern</th>
                  <th className="px-4 py-3">N</th>
                  <th className="px-4 py-3">Mean C<sub>A</sub></th>
                  <th className="px-4 py-3">Dominant C<sub>A</sub> level</th>
                  <th className="px-4 py-3">Mean C<sub>K</sub></th>
                  <th className="px-4 py-3">Dominant C<sub>K</sub> level</th>
                  <th className="px-4 py-3">Prevailing C<sub>K</sub> sign</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {EP_IDS.map((epId) => {
                  const pattern = verticalData.patterns[epId]
                  const ckNegative = pattern.Ck.negative_percentage
                  const prevailingNegative = ckNegative >= 50
                  return (
                    <tr key={epId}>
                      <td className="px-4 py-3 font-semibold text-slate-900">{epId}</td>
                      <td className="px-4 py-3">{pattern.n.toLocaleString()}</td>
                      <td className="px-4 py-3">{signed(pattern.Ca.column_mean)} W m⁻²</td>
                      <td className="px-4 py-3">{pattern.Ca.dominant_level_hpa} hPa</td>
                      <td className="px-4 py-3">{signed(pattern.Ck.column_mean)} W m⁻²</td>
                      <td className="px-4 py-3">{pattern.Ck.dominant_level_hpa} hPa</td>
                      <td className="px-4 py-3">
                        {prevailingNegative ? 'Negative' : 'Positive'} ({
                          (prevailingNegative
                            ? pattern.Ck.negative_percentage
                            : pattern.Ck.positive_percentage
                          ).toFixed(1)
                        }%)
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Pressure-level distributions</h2>
          <FigurePanel
            src="/figures/main/vertical_levels.png"
            alt="Corrected pressure-level distributions of baroclinic and barotropic conversion for EP1, EP2, and EP3"
            caption="Corrected intensification-phase profiles. Boxes show the interquartile range across cyclones, central lines are medians, whiskers extend to 1.5 times the interquartile range, and stars identify the largest absolute median profile value within each Energy Pattern. Outliers are omitted from display only."
            source="scripts/main/figure_vertical_levels.py"
          />
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Physical interpretation</h2>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-xl border border-red-200 bg-red-50/50 p-5">
              <h3 className="font-bold text-red-800">EP1 — dual energy supply</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Mean column <InlineMath expr="C_A" /> is {ep1.Ca.column_mean.toFixed(2)} W m⁻².
                Its lower- and middle-tropospheric contributions are comparable ({
                  ep1.Ca.layers.lower_700_1000.mean.toFixed(2)
                } and {ep1.Ca.layers.middle_400_700.mean.toFixed(2)} W m⁻²). Mean{' '}
                <InlineMath expr="C_K" /> is {signed(ep1.Ck.column_mean)} W m⁻², with{' '}
                {ep1.Ck.negative_percentage.toFixed(1)}% of cyclones negative and the strongest
                median profile at {ep1.Ck.dominant_level_hpa} hPa.
              </p>
            </div>
            <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5">
              <h3 className="font-bold text-blue-800">EP2 — upper-level kinetic-energy export</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                EP2 retains strong positive <InlineMath expr="C_A" /> ({
                  ep2.Ca.column_mean.toFixed(2)
                } W m⁻²), but mean <InlineMath expr="C_K" /> reverses sign to{' '}
                {signed(ep2.Ck.column_mean)} W m⁻². The 100–400 hPa layer contributes{' '}
                {signed(ep2.Ck.layers.upper_100_400.mean)} W m⁻², and the largest median profile
                occurs at {ep2.Ck.dominant_level_hpa} hPa.
              </p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
              <h3 className="font-bold text-emerald-800">EP3 — weak, vertically compensating Ck</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Mean column <InlineMath expr="C_A" /> is only {ep3.Ca.column_mean.toFixed(2)} W m⁻².
                For <InlineMath expr="C_K" />, a positive upper-layer contribution ({
                  signed(ep3.Ck.layers.upper_100_400.mean)
                } W m⁻²) is offset by a negative lower-layer contribution ({
                  signed(ep3.Ck.layers.lower_700_1000.mean)
                } W m⁻²), leaving a near-zero column mean of {signed(ep3.Ck.column_mean)} W m⁻².
              </p>
            </div>
          </div>
        </section>

        <ResultSummaryCallout type="result" title="Main result">
          <p>
            The Energy Patterns differ in vertical organisation, not only in total conversion
            amplitude. EP1 combines strong baroclinic conversion with a deep negative{' '}
            <InlineMath expr="C_K" /> structure centred near 400 hPa. EP2 remains baroclinic but
            exhibits a positive upper-tropospheric <InlineMath expr="C_K" /> maximum near 300 hPa.
            EP3 has weak <InlineMath expr="C_A" /> and vertically opposing <InlineMath expr="C_K" />
            contributions that nearly cancel in the column integral.
          </p>
        </ResultSummaryCallout>

        <p className="text-xs leading-relaxed text-slate-400">
          Sources: <code>{verticalData.source}</code> ({verticalData.source_sha256.slice(0, 12)}…)
          and <code>{verticalData.cluster_source}</code>. Results are descriptive population
          summaries for the corrected clustering.
        </p>
      </div>
    </div>
  )
}
