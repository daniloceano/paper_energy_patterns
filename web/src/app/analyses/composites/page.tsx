import type { Metadata } from 'next'
import { Layers, MountainSnow } from 'lucide-react'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { DIAGNOSTIC_LIST, DATASET_STATS, ENERGY_PATTERNS } from '@/lib/constants'
import Link from 'next/link'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import { SimpleTerms, InThisStudy } from '@/components/analysis/Didactic'

export const metadata: Metadata = {
  title: 'Composite Analysis',
  description: 'ERA5 composite analysis of EP1, EP2, EP3, and EPALL atmospheric structure.',
}

export default function CompositesPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Composite Analysis"
        subtitle="EP Structure — ERA5 Reanalysis"
        badge="EP1 / EP2 / EP3 / EPALL"
        description={`Storm-centred ${DATASET_STATS.domainSize} composites of 10 diagnostic fields at key atmospheric levels, computed from ERA5 reanalysis at ${DATASET_STATS.era5Resolution} resolution. EP1 (N=${ENERGY_PATTERNS.EP1.count}), EP2 (N=${ENERGY_PATTERNS.EP2.count}), and EP3 (N=${ENERGY_PATTERNS.EP3.count}) composites are compared during the intensification phase alongside EPALL (all cyclones combined). EPALL-relative anomalies (EPx − EPALL) isolate what distinguishes each pattern from the climatological cyclone population.`}
      />

      <div className="space-y-8">
        <ResultSummaryCallout type="info" title="Scientific Objective">
          <p>
            Understand the atmospheric structure and dynamical characteristics that distinguish
            high-energy (EP1), moderate-energy (EP2), and weak-energy (EP3) cyclones from each
            other and from the full population (EPALL). This analysis reveals how differences in
            energy conversions relate to distinct patterns of baroclinic instability, upper-level
            forcing, moisture supply, and jet-stream interaction.
          </p>
        </ResultSummaryCallout>

        {/* Methods & Statistics */}
        <MethodsPanel summary="How the storm-centred composites are built, which cyclones enter them, and what the two different anomaly definitions mean.">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">
              1 · Building a storm-centred composite
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              For each cyclone, ERA5 fields are extracted on a{' '}
              {DATASET_STATS.domainSize} grid centred on the cyclone position at the
              <strong> midpoint of its intensification phase</strong> — the most active
              moment of deepening. Where the intensification phase has an odd number of
              timesteps the three central steps are used, and where it is even, the two
              central ones. The composite for a group is the arithmetic mean of that field
              across all its cyclones.
            </p>
            <p className="mt-3 text-sm text-slate-600">
              The {DATASET_STATS.domainSize} domain is deliberately wider than the{' '}
              {DATASET_STATS.innerDomainSize} box used for the Lorenz Energy Cycle
              computation, so that the environment surrounding the LEC domain — upstream
              troughs, downstream ridges, the jet — is visible alongside the dynamics
              inside it.
            </p>
            <SimpleTerms>
              <p>
                Averaging many cyclones after aligning them on their centres keeps whatever
                is consistently in the same place relative to the storm (a trough to the
                west, a warm sector to the east) and averages away whatever is not. The
                composite is therefore a picture of the <em>typical</em> structure of a
                group, not of any individual cyclone.
              </p>
            </SimpleTerms>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">
              2 · Which cyclones enter the composites
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              Cyclones whose intensification phase lasted less than <strong>24 h</strong>{' '}
              are excluded. Very short intensification phases place the central timestep
              uncomfortably close to the incipient or mature stages, whose energetics — and
              therefore whose dynamical fields — behave differently, so including them
              would blur the very signal the composite is meant to isolate.
            </p>
            <div className="mt-3">
              <StatsTable
                title="Sample sizes after the ≥ 24 h filter"
                columns={[
                  { key: 'grp', label: 'Group' },
                  { key: 'before', label: 'Before', align: 'right' },
                  { key: 'after', label: 'After', align: 'right' },
                ]}
                rows={[
                  { grp: 'EP1', before: '444', after: '332' },
                  { grp: 'EP2', before: '979', after: '776' },
                  { grp: 'EP3', before: '2,397', after: '1,625' },
                  { grp: 'All (EPALL)', before: '3,820', after: '2,733' },
                ]}
                caption="This filtered population is also the one used by the LEC–field dependence analysis, so the two are directly comparable."
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">
              3 · Two different anomalies — and why the distinction matters
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              Two anomaly definitions appear on these pages, and they answer different
              questions. Reading one as if it were the other is the commonest way to
              misinterpret a composite figure.
            </p>
            <div className="mt-3">
              <FormulaBlock
                formula="X'_{\mathrm{clim}}(x,y,p,t) = X(x,y,p,t) - \overline{X}_m(x,y,p)"
                label="Climatology-relative anomaly"
                terms={{
                  "X'_clim": 'Departure from the seasonal background state',
                  'X': 'Instantaneous ERA5 field for the cyclone (temperature, wind, PV, …)',
                  'X̄_m': `Monthly mean climatology for calendar month m, over ${DATASET_STATS.climatologyPeriod}`,
                  'x, y, p': 'Storm-centred horizontal coordinates and pressure level',
                  't': 'Time of the composite timestep; m is its calendar month',
                }}
                notes="Answers: how unusual is this cyclone relative to the season it formed in? For events spanning two months, the background is a weighted mean of the two monthly climatologies to avoid an artificial jump at the month boundary."
              />
            </div>
            <div className="mt-3">
              <FormulaBlock
                formula="X'_{\mathrm{EPALL}} = \overline{X}_{\mathrm{EP}i} - \overline{X}_{\mathrm{EPALL}}"
                label="EPALL-relative anomaly"
                terms={{
                  "X'_EPALL": 'Departure of one Energy Pattern from the full cyclone population',
                  'X̄_EPi': 'Composite mean of field X over the cyclones of EP i',
                  'X̄_EPALL': 'Composite mean of the same field over all 2,733 cyclones',
                }}
                notes="Answers: what makes this Energy Pattern different from a typical cyclone? Because the reference is itself a cyclone composite, a zero anomaly does not mean 'no cyclone signal' — it means 'the same signal every cyclone has'."
              />
            </div>
            <SimpleTerms>
              <p>
                Climatology-relative asks <em>&quot;how does this differ from a quiet day in
                the same month?&quot;</em>; EPALL-relative asks <em>&quot;how does this
                differ from an ordinary cyclone?&quot;</em>. A strong closed low is
                dramatic in the first and can vanish in the second, because every cyclone
                has one.
              </p>
            </SimpleTerms>
            <InThisStudy>
              <p>
                This is why the EP1 upper-level PV signature is described as{' '}
                <em>streamer-like</em> rather than as a PV streamer: it is an
                EPALL-relative anomaly, so it shows that EP1 has more elongated upper-level
                PV structure <em>than other cyclones do</em>, not that an absolute PV
                streamer is present. Likewise the EP3 fields, which look like a weak mirror
                image of EP2, indicate a weaker-than-average version of the canonical
                pattern — not a reversed circulation.
              </p>
            </InThisStudy>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">
              4 · Statistical treatment of the composite fields
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              The composites themselves are presented as fields, not as significance maps.
              Rather than testing every grid point — which would raise a severe
              multiple-comparison problem and produce maps whose stippling is dominated by
              spatial autocorrelation — each field is reduced to 13 physically
              interpretable scalar descriptors (domain mean, mean absolute value, centre
              value, cardinal sector and border means, and the N–S and E–W contrasts).
              Those scalars are what get tested for EP differences and correlated against
              the LEC terms.
            </p>
            <InThisStudy>
              <p>
                The full inferential treatment of those descriptors — the Kruskal–Wallis and
                Dunn tests, effect sizes, multiple-comparison corrections, and the
                correlation and PREDEP metrics — is documented in{' '}
                <Link href="/analyses/field-dependence" className="text-indigo-600 hover:underline">
                  LEC–Field Dependence
                </Link>
                . The one statistical marking that does appear on these figures is the
                Rayleigh–Kuo hatching, which flags where the meridional gradient of absolute
                vorticity reverses sign in the <em>total</em> composite field. It is a
                necessary — not sufficient — condition for barotropic instability, so it
                should be read as background dynamical context rather than as evidence of
                barotropic growth.
              </p>
            </InThisStudy>
          </div>
        </MethodsPanel>

        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Domain Definition
          </h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600">
            <ul className="space-y-2">
              <li>
                <strong>Full domain:</strong> {DATASET_STATS.domainSize} storm-centred at{' '}
                {DATASET_STATS.era5Resolution} resolution (120 × 120 grid points)
              </li>
              <li>
                <strong>Inner domain ({DATASET_STATS.innerDomainSize}):</strong> The central{' '}
                {DATASET_STATS.innerDomainSize} subdomain centred on the cyclone. Used for
                &ldquo;inside&rdquo; domain statistics.
              </li>
              <li>
                <strong>Outer ring:</strong> The area between the full {DATASET_STATS.domainSize}{' '}
                domain and the inner {DATASET_STATS.innerDomainSize}. Used for &ldquo;outside&rdquo;
                domain statistics.
              </li>
              <li>
                <strong>Boundaries (N/S/E/W):</strong> The four edges of the inner{' '}
                {DATASET_STATS.innerDomainSize} domain. For flux/advection diagnostics, each
                boundary value represents the mean along that edge.
              </li>
            </ul>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Available Diagnostics
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {DIAGNOSTIC_LIST.filter((d) => !['z-250', 'z-500', 'z-850'].includes(d.id)).map((diag) => (
              <Link
                key={diag.id}
                href={`/analyses/composites/${diag.slug}`}
                className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 transition-colors group-hover:bg-indigo-600 group-hover:text-white">
                    <Layers className="h-4 w-4" />
                  </div>
                  <div className="flex gap-1.5">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                      {diag.level}
                    </span>
                    {diag.hasAnomaly && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-600">
                        +anom
                      </span>
                    )}
                  </div>
                </div>
                <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600">
                  {diag.name}
                </h3>
                <p className="mt-1 text-xs text-slate-500">{diag.shortName} [{diag.unit}]</p>
              </Link>
            ))}
          </div>
        </section>

        {/* Geopotential Height section */}
        <section>
          <h2 className="mb-1 text-lg font-bold text-slate-900">
            Geopotential Height
          </h2>
          <p className="mb-4 text-sm text-slate-500 leading-relaxed">
            Storm-centred composites of geopotential height at three pressure levels. Each level
            provides a different vertical perspective on the synoptic wave pattern: 250 hPa captures
            upper-tropospheric ridge/trough structure, 500 hPa reflects mid-tropospheric wave
            amplitude, and 850 hPa characterises low-tropospheric thermal structure and vertical
            tilt. All three levels include total composites, climatology-relative anomalies
            (Z&prime; = Z − Z̄<sub>clim</sub>), and EPALL-relative anomalies (EP<em>x</em> − EPALL).
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {DIAGNOSTIC_LIST.filter((d) => ['z-250', 'z-500', 'z-850'].includes(d.id)).map((diag) => (
              <Link
                key={diag.id}
                href={`/analyses/composites/${diag.slug}`}
                className="group rounded-xl border border-emerald-200 bg-white p-5 shadow-sm transition-all hover:border-emerald-400 hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 transition-colors group-hover:bg-emerald-600 group-hover:text-white">
                    <MountainSnow className="h-4 w-4" />
                  </div>
                  <div className="flex gap-1.5">
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-600">
                      {diag.level}
                    </span>
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-600">
                      +anom
                    </span>
                  </div>
                </div>
                <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-emerald-700">
                  {diag.name}
                </h3>
                <p className="mt-1 text-xs text-slate-500">{diag.shortName} [{diag.unit}]</p>
                <p className="mt-2 text-xs text-slate-400">
                  total · clim anom · EPALL anom
                </p>
              </Link>
            ))}
          </div>
        </section>

        {/* Dynamical Composites card */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Multi-Field Overview
          </h2>
          <Link
            href="/analyses/composites/dynamical"
            className="group flex flex-col rounded-xl border border-teal-200 bg-white p-5 shadow-sm transition-all hover:border-teal-400 hover:shadow-md"
          >
            <div className="flex items-start justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-100 text-teal-600 transition-colors group-hover:bg-teal-600 group-hover:text-white">
                <Layers className="h-4 w-4" />
              </div>
              <div className="flex gap-1.5">
                <span className="rounded-full bg-teal-100 px-2 py-0.5 text-xs text-teal-600">
                  exploratory
                </span>
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-600">
                  3 figures
                </span>
              </div>
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-teal-700">
              Dynamical Composites
            </h3>
            <p className="mt-1 text-xs text-slate-500 leading-relaxed">
              Multi-field overview: PV (200 / 850 hPa), EGR, T-advection, AFC, KE-advection,
              and barotropic RK diagnostics for EP1, EP2, EP3, and EPALL in a single figure.
              Three variants: total fields, climatology-relative anomaly, and EPALL-relative anomaly.
            </p>
          </Link>
        </section>

        <ResultSummaryCallout type="info" title="Data Source">
          <p>
            All composites are pre-computed and stored in{' '}
            <code>data/era5_ep_structure/precomputed_composites_ep1.nc</code>,{' '}
            <code>precomputed_composites_ep2.nc</code>,{' '}
            <code>precomputed_composites_ep3.nc</code>, and{' '}
            <code>precomputed_composites_epall.nc</code> (Xarray/NetCDF4 format). EPALL-relative
            anomaly variables (e.g. <code>egr_minus_epall</code>) are stored inside EP1/EP2/EP3
            files. Figures are generated by{' '}
            <code>scripts/ep_structure_analysis/step4_create_figures.py</code>.
          </p>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
