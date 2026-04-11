import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import FallbackImage from '@/components/analysis/FallbackImage'
import { figureUrl } from '@/lib/utils'
import manifestData from '@/content/dynamical_composites_manifest.json'

export const metadata: Metadata = {
  title: 'Dynamical Composites',
  description:
    'Exploratory multi-field composites of PV, temperature advection, AFC, KE advection, and barotropic diagnostics for EP1, EP2, EP3, and EPALL cyclones.',
}

export default function DynamicalCompositesPage() {
  const manifest = manifestData

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />

      <AnalysisHero
        title="Dynamical Composites"
        subtitle="Multi-Field EP1 / EP2 / EP3 / EPALL Overview"
        badge="Exploratory"
        description={`Storm-centred 30°×30° composites of key dynamical fields at the intensification midpoint (central timestep). Three figure variants are presented: total fields, climatology-relative anomalies, and EPALL-relative anomalies. EP1 (N=${manifest.metadata.n_ep1}), EP2 (N=${manifest.metadata.n_ep2}), EP3 (N=${manifest.metadata.n_ep3}), EPALL (N=${manifest.metadata.n_epall}).`}
      />

      <div className="space-y-10">

        {/* Methodology callout */}
        <ResultSummaryCallout type="info" title="What is shown in each figure">
          <div className="space-y-3 text-sm leading-relaxed">
            <p>
              Each figure is a <strong>3-row, multi-column composite</strong>. Rows represent three
              dynamical layers of the cyclone structure:
            </p>
            <ul className="list-inside list-disc space-y-1 pl-2">
              <li>
                <strong>Row 1 — Upper troposphere (200 hPa):</strong> PV shading + EGR contours
                (≥ 0.5 day⁻¹, total) + 250 hPa wind vectors. Captures upper-level trough
                structure and baroclinic growth rate.
              </li>
              <li>
                <strong>Row 2 — Lower troposphere (850 hPa):</strong> PV shading + temperature
                advection contours (blue dashed = cold, red solid = warm) + 850 hPa wind +
                SLP contours. Captures the thermal steering environment.
              </li>
              <li>
                <strong>Row 3 — Jet-level dynamics (250 hPa):</strong> AFC shading + wind vectors
                (≥ 30 m/s threshold) + Rayleigh-Kuo sign-reversal hatching (barotropic critical
                region) + KE-advection contours (forestgreen = positive/import,
                gold dashed = negative/export).
              </li>
            </ul>
            <p className="mt-2">
              The <strong>LEC computation domain</strong> (dashed box, ±7.5° from cyclone centre)
              and cyclone centre (★) are marked in every panel.
            </p>
          </div>
        </ResultSummaryCallout>

        <ResultSummaryCallout type="info" title="Three anomaly references — key differences">
          <div className="space-y-2 text-sm leading-relaxed">
            <p>
              <strong>Figure 1 (Total fields)</strong> shows raw composite values: what the
              atmosphere looks like on average for each energy pattern at peak intensification.
              EPALL is the reference population of all 2730 intensifying cyclones.
            </p>
            <p>
              <strong>Figure 2 (Climatology-relative anomaly)</strong> removes the 1991–2020
              ERA5 monthly climatology. This isolates the cyclone signal from the background
              seasonal mean state. Anomaly wind vectors (u′, v′) show the eddy component of
              the circulation. This is the standard meteorological anomaly definition.
            </p>
            <p>
              <strong>Figure 3 (EPALL-relative anomaly)</strong> uses the EPALL composite as
              reference instead of the climatology. Each field is computed as EPx − EPALL,
              so positive values mean &ldquo;more than a typical intensifying cyclone&rdquo;
              and negative values mean &ldquo;less than typical.&rdquo; EPALL is omitted as a
              column (it is identically zero by construction). AFC has no EPALL-relative version
              (its decomposition requires a climatological base state by construction;
              Orlanski &amp; Katzfey 1991) — the total AFC is shown instead.
            </p>
          </div>
        </ResultSummaryCallout>

        {/* ─── Figure 1: Total fields ─────────────────────────────────────────── */}
        <section>
          <h2 className="mb-1 text-lg font-bold text-slate-900">
            Figure 1 — Total Fields
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            4 columns: EP1 | EP2 | EP3 | EPALL
          </p>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
              <p className="text-xs text-slate-600">
                <strong>Row 1</strong> — PV at 200 hPa (RdYlBu_r shading) + EGR contours
                (≥ 0.5 day⁻¹) + 250 hPa total wind vectors (threshold: ≥ 25 m/s).
                Captures upper-level trough depth and baroclinic instability.
              </p>
              <p className="mt-1 text-xs text-slate-600">
                <strong>Row 2</strong> — PV at 850 hPa (RdYlBu_r shading) + temperature
                advection contours (blue dashed = cold, red solid = warm) + 850 hPa total wind
                + SLP reference contours (2 hPa interval).
              </p>
              <p className="mt-1 text-xs text-slate-600">
                <strong>Row 3</strong> — AFC at 250 hPa (RdBu_r shading) + 250 hPa total wind
                (≥ 30 m/s) + RK meridional sign-reversal hatching (barotropic critical region) +
                KE-advection contours.
              </p>
            </div>
            <div className="p-4">
              <FallbackImage
                src={figureUrl(manifest.figures.total.api_path)}
                alt="Dynamical Composites — Total Fields EP1 / EP2 / EP3 / EPALL"
                width={2000}
                height={1300}
                className="w-full rounded-lg"
              />
            </div>
          </div>
        </section>

        {/* ─── Figure 2: Climatology-relative anomaly ─────────────────────────── */}
        <section>
          <h2 className="mb-1 text-lg font-bold text-slate-900">
            Figure 2 — Climatology-Relative Anomaly Fields
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            4 columns: EP1 | EP2 | EP3 | EPALL &nbsp;·&nbsp;
            X′ = X − X̄<sub>clim</sub> (1991–2020 ERA5 monthly climatology)
          </p>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
              <p className="text-xs text-slate-600">
                <strong>Row 1</strong> — PV anomaly at 200 hPa (RdBu_r shading, symmetric) +
                total EGR contours + 250 hPa anomaly wind vectors (u′, v′ = departure from
                1991–2020 climatology). Highlights the upper-level PV perturbation associated
                with each energy pattern.
              </p>
              <p className="mt-1 text-xs text-slate-600">
                <strong>Row 2</strong> — PV anomaly at 850 hPa + T-adv anomaly contours +
                850 hPa anomaly wind + SLP reference. The asymmetric T-adv anomaly reveals
                differential warm/cold sector thermal structure by energy pattern.
              </p>
              <p className="mt-1 text-xs text-slate-600">
                <strong>Row 3</strong> — AFC (total, not anomaly — uses climatological
                decomposition by construction) + 250 hPa anomaly wind + RK hatching +
                KE-advection anomaly contours.
              </p>
            </div>
            <div className="p-4">
              <FallbackImage
                src={figureUrl(manifest.figures.anom.api_path)}
                alt="Dynamical Composites — Climatology-Relative Anomaly Fields"
                width={2000}
                height={1300}
                className="w-full rounded-lg"
              />
            </div>
          </div>
        </section>

        {/* ─── Figure 3: EPALL-relative anomaly ──────────────────────────────── */}
        <section>
          <h2 className="mb-1 text-lg font-bold text-slate-900">
            Figure 3 — EPALL-Relative Anomaly
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            3 columns: EP1 − EPALL | EP2 − EPALL | EP3 − EPALL &nbsp;·&nbsp;
            EPALL omitted (identically zero by construction)
          </p>
          <div className="overflow-hidden rounded-xl border border-amber-200 bg-white">
            <div className="border-b border-amber-100 bg-amber-50 px-4 py-3">
              <p className="text-xs text-amber-800">
                <strong>Reference: EPALL composite</strong> (all 2730 intensifying cyclones).
                Positive values indicate fields stronger than the typical intensifying cyclone;
                negative values weaker than typical. This is distinct from the climatological
                anomaly — here the reference is the cyclone population itself, not the
                multi-year monthly mean state.
              </p>
              <p className="mt-2 text-xs text-slate-600">
                <strong>Row 1</strong> — (PV@200) − EPALL + total EGR contours +
                (u, v)_250 − EPALL wind vectors. Reveals how upper-level PV structure
                of each energy pattern differs from the typical cyclone.
              </p>
              <p className="mt-1 text-xs text-slate-600">
                <strong>Row 2</strong> — (PV@850) − EPALL + (T-adv) − EPALL contours +
                (u, v)_850 − EPALL wind + SLP reference. Captures the differential baroclinic
                environment relative to the full cyclone population.
              </p>
              <p className="mt-1 text-xs text-slate-600">
                <strong>Row 3</strong> — AFC total (no EPALL-relative version; uses
                climatological decomposition — Orlanski &amp; Katzfey 1991) +
                (u, v)_250 − EPALL wind + <strong>RK total sign-reversal hatching</strong>{' '}
                (total composite, not EPALL-relative — RK = β − ∂²ū/∂y² is a background-flow
                diagnostic; shown as total field only) + (KE-adv) − EPALL contours.
                Shows how barotropic energy exchange and jet interaction differ from the mean cyclone.
              </p>
            </div>
            <div className="p-4">
              <FallbackImage
                src={figureUrl(manifest.figures.epall_anom.api_path)}
                alt="Dynamical Composites — EPALL-Relative Anomaly (EP1−EPALL / EP2−EPALL / EP3−EPALL)"
                width={1500}
                height={1300}
                className="w-full rounded-lg"
              />
            </div>
          </div>
        </section>

        {/* Data source */}
        <ResultSummaryCallout type="info" title="Data source and method">
          <p className="text-sm leading-relaxed">
            Composites are computed from ERA5 reanalysis at 0.25° resolution over the
            1979–2023 period. Each case is centred on the intensification midpoint
            (central timestep of the intensification phase). Pre-computed NetCDF files:
            <code className="ml-1">data/era5_ep_structure/precomputed_composites_ep*.nc</code>.
            Figures generated by{' '}
            <code>scripts/exploratory/explore_dynamical_composites.py</code>.
            EPALL-relative anomaly variables (e.g. <code>pv_200_minus_epall</code>) are
            stored in the EP1/EP2/EP3 composite files by step 3 of the pipeline.
          </p>
        </ResultSummaryCallout>

      </div>
    </div>
  )
}
