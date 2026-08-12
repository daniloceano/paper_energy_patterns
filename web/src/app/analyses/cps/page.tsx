import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import FigurePanel from '@/components/analysis/FigurePanel'
import StatsTable from '@/components/analysis/StatsTable'
import { figureUrl } from '@/lib/utils'
import manifestData from '@/content/cps_manifest.json'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import { SimpleTerms, InThisStudy, TestFlow } from '@/components/analysis/Didactic'

export const metadata: Metadata = {
  title: 'Cyclone Phase Space — Thermal Structure of the Energy Patterns',
  description:
    'Hart (2003) cyclone phase space applied to 6,776 South Atlantic cyclones, classified into extratropical, subtropical and tropical structure under a 36 h persistence gate, and cross-referenced against the Energy Patterns.',
}

type Manifest = typeof manifestData
const manifest = manifestData as Manifest

// The nine CPS figures are committed to web/public/figures/cps/ (5 MB total).
// Serve them with an absolute path so they always come from the static public/
// directory, regardless of whether NEXT_PUBLIC_SUPABASE_FIGURES_URL is set on
// Vercel — the same approach used by the EP Differences page. The manifest
// stores relative paths ("figures/cps/..."), so a leading slash is added when
// one is missing; figureUrl() passes absolute paths through untouched.
const fig = (key: keyof Manifest['figures']) => {
  const p = manifest.figures[key]
  return figureUrl(p.startsWith('figures/') ? `/${p}` : p)
}

/** Rows of the EP-relative table for one outcome. */
function relFor(outcome: string) {
  return manifest.ep_relative.filter((r) => r.outcome === outcome)
}

function pFormat(p: number): string {
  if (p >= 0.01) return p.toFixed(3)
  return p.toExponential(1).replace('e-', ' × 10⁻').replace(/⁻(\d+)/, (_, d) =>
    '⁻' + String(d).split('').map((c) => '⁰¹²³⁴⁵⁶⁷⁸⁹'[Number(c)]).join('')
  )
}

export default function CpsPage() {
  const pop = manifest.population
  const crit = manifest.criteria
  const named = manifest.classes.filter((c) => c.kind === 'single_state' || c.kind === 'transition')
  const scRows = relFor('SC')
  const ep3 = scRows.find((r) => r.ep === 'EP3')
  const ep1 = scRows.find((r) => r.ep === 'EP1')

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Cyclone Phase Space"
        subtitle="Thermal structure of the Energy Patterns"
        badge="CPS · Hart (2003)"
        description={`Every one of the ${pop.catalogue.toLocaleString()} tracked cyclones is placed in the Hart (2003) cyclone phase space at ${pop.timestep_hours}-hourly resolution and classified as extratropical, subtropical or tropical, subject to a ${crit.persistence_hours} h persistence requirement. The resulting classes are cross-referenced against the three Energy Patterns to ask whether a cyclone's energetics relate to its thermal structure. Genesis ${pop.genesis_first} to ${pop.genesis_last}.`}
      />

      <div className="space-y-12">
        {/* ---------------- Methods & Statistics ---------------- */}
        <MethodsPanel summary="How thermal structure is measured and classified, and how the association between Energy Pattern and phase class is tested.">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="font-semibold text-slate-900">
            1 · Measuring thermal structure — the three CPS parameters
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            The Cyclone Phase Space (Hart, 2003) describes a cyclone with three numbers
            computed at every timestep inside a 500 km radius of the centre: one for
            frontal asymmetry and two for the thermal structure of the lower and upper
            troposphere.
          </p>
          <div className="mt-3">
            <FormulaBlock
              formula="B = h\left[\overline{(Z_{600}-Z_{900})}_{R} - \overline{(Z_{600}-Z_{900})}_{L}\right]"
              label="B — thermal asymmetry"
              terms={{
                'B': 'Storm-motion-relative thickness asymmetry [m]',
                'Z₆₀₀, Z₉₀₀': 'Geopotential height at 600 and 900 hPa [m]',
                'R, L': 'Right and left 500 km semicircles relative to the direction of storm motion',
                'overbar': 'Area average over the semicircle',
                'h': 'Hemisphere factor: +1 in the Northern Hemisphere, −1 in the Southern Hemisphere',
              }}
              notes="B > 0 means the cyclone is thermally asymmetric — a frontal structure, with warm air on one flank and cold on the other. B ≈ 0 means a thermally symmetric core, the signature of tropical and subtropical systems."
            />
          </div>
          <div className="mt-3">
            <FormulaBlock
              formula="-V_T = \frac{\partial\,(\Delta Z)}{\partial \ln p}, \qquad \Delta Z = Z_{\max} - Z_{\min}"
              label="−V_T — thermal wind (lower and upper layers)"
              terms={{
                '−V_T': 'Thermal wind parameter for a layer [m per unit ln p]',
                'ΔZ': 'Geopotential height range within 500 km of the centre at a given level [m]',
                'Z_max, Z_min': 'Maximum and minimum geopotential height inside that radius',
                'p': 'Pressure [hPa]',
                '−V_T^L': 'Lower-tropospheric value, fitted over 900 → 600 hPa',
                '−V_T^U': 'Upper-tropospheric value, fitted over 600 → 300 hPa',
              }}
              notes="Obtained as the slope of an ordinary least-squares fit of ΔZ against ln p across the levels of the layer. −V_T > 0 indicates a warm core in that layer, −V_T < 0 a cold core."
            />
          </div>
          <SimpleTerms>
            <p>
              A cyclone whose height gradient weakens with altitude is warm-cored; one
              whose gradient strengthens with altitude is cold-cored. The two thermal-wind
              parameters ask that question separately for the bottom and the top half of
              the troposphere, and <em>B</em> asks a third, independent question: is the
              storm lopsided in temperature (frontal) or symmetric? A classical
              extratropical cyclone is asymmetric and cold-cored at both levels; a
              tropical cyclone is symmetric and warm-cored at both; a subtropical cyclone
              sits in between — symmetric and warm-cored below, but still cold-cored aloft.
            </p>
          </SimpleTerms>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="font-semibold text-slate-900">
            2 · From parameters to classes — thresholds and the persistence gate
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            Thresholds on the three parameters classify each timestep. Every threshold is
            transcribed from a peer-reviewed source; none is tuned to this dataset.
          </p>
          <div className="mt-3">
            <StatsTable
              title="Canonical thresholds"
              columns={[
                { key: 'cls', label: 'Class' },
                { key: 'b', label: 'B [m]' },
                { key: 'vtl', label: '−V_T^L' },
                { key: 'vtu', label: '−V_T^U' },
              ]}
              rows={[
                { cls: 'Tropical', b: '< 10', vtl: '> 0', vtu: '> 0' },
                { cls: 'Subtropical', b: '−25 to 25', vtl: '> −50', vtu: '< −10' },
                { cls: 'Extratropical', b: '> 10', vtl: '< 0', vtu: '< 0' },
              ]}
              caption="Following de Souza et al. (2026): Wood et al. (2023) for the extratropical and tropical bounds, Gozzo et al. (2014) for the subtropical ones. The class definitions overlap, so a fixed precedence (tropical → subtropical → extratropical) resolves ambiguous timesteps."
            />
          </div>
          <p className="mt-3 text-sm text-slate-600">
            A class counts as a <strong>state</strong> of the cyclone only if it is held
            for at least <strong>36 consecutive hours</strong>. This gate is what makes
            the scheme workable: without it, most cyclones visit two or more classes and
            the commonest sequence is a brief EC → SC → EC excursion, which is a
            transient wobble rather than a transition. Cyclones are then labelled by their
            sequence of persistent states — <strong>EC</strong> (extratropical
            throughout), <strong>SC</strong> (subtropical throughout),{' '}
            <strong>ST</strong> (subtropical transition, EC → SC), <strong>SD</strong>{' '}
            (subtropical decay, SC → EC), and so on.
          </p>
          <SimpleTerms>
            <p>
              The persistence gate is the difference between saying &quot;this cyclone
              briefly looked subtropical on one analysis time&quot; and &quot;this cyclone
              <em> was</em> subtropical&quot;. Structures that appear but never last 36 h
              are recorded separately as <em>characteristic</em> classes (EC_like,
              SC_like) — a cyclone there is not being called subtropical, only noted as
              showing hybrid characteristics.
            </p>
          </SimpleTerms>
          </div>

          {/* CPS contingency statistics */}
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">
              3 · Testing the association with the Energy Patterns
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
              the LEC–field dependence analysis: because no ≥ 24 h intensification
              filter is needed here, all{' '}
              <strong>3,812 EP-labelled cyclones</strong> are used (EP1 = 441, EP2 = 978,
              EP3 = 2,393). Note that the pooled reference &quot;EPALL&quot; in this track
              means the union EP1 + EP2 + EP3, not the full catalogue — only clustered
              cyclones carry an Energy Pattern, so the reference must be the same
              population the EPs partition. The logic of the chain, however, is identical
              to the rank-based chain used for the LEC terms:
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
                result — a concrete illustration of what multiple-comparison correction
              buys.
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
              correction, open markers those that are only nominally significant. The
              figures and the full contrast table follow below.
            </p>
          </div>

        </MethodsPanel>
        {/* ---------------- Headline ---------------- */}
        <ResultSummaryCallout type="result" title="Main result">
          <p>
            <strong>The weaker a cyclone&apos;s baroclinic energetics, the more likely it is
            to be subtropical.</strong> The subtropical rate rises monotonically from{' '}
            {ep1?.rate_pct}% in EP1 (high conversions, exports energy) to{' '}
            {ep3?.rate_pct}% in EP3 (weak, background energetics) — a factor of{' '}
            {ep1 && ep3 ? (ep3.rate_pct / ep1.rate_pct).toFixed(0) : '7'}, or{' '}
            <strong>{ep1?.ratio.toFixed(2)}×</strong> and{' '}
            <strong>{ep3?.ratio.toFixed(2)}×</strong> the pooled rate. All three contrasts
            survive Holm correction over the nine tested, the only place in this analysis
            where that happens. That is what a diabatically driven, convectively maintained
            system should look like in an energy-cycle framework: it does not run on
            baroclinic conversion, so it appears in the cluster that has little of it.
          </p>
          <p className="mt-2">
            The transition class <code>ST</code> carries no significant signal. Before the
            subtropical guards described below, the result was the opposite — flat{' '}
            <code>SC</code>, and an EP2 enrichment in <code>ST</code>. Same data, same
            thresholds; the difference is the guards, and the reading is that the earlier
            signal was warm-seclusion contamination.
          </p>
        </ResultSummaryCallout>

        {/* ---------------- Provenance ---------------- */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Provenance</h2>
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm leading-relaxed text-slate-700">
            <p>
              The per-cyclone CPS parameters were computed by{' '}
              <strong>{manifest.provenance.cps_computed_by}</strong>. {manifest.provenance.note}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Calculator preserved unmodified at{' '}
              <code className="rounded bg-white px-1 border border-amber-200">
                {manifest.provenance.calculator}
              </code>
              . Everything downstream is regenerated by{' '}
              <code className="rounded bg-white px-1 border border-amber-200">
                {manifest.generated_from}
              </code>
              .
            </p>
          </div>
        </section>

        {/* ---------------- How to read the diagrams ---------------- */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">How to read the diagrams</h2>
          <p className="mb-4 text-sm leading-relaxed text-slate-600">
            The phase space has three parameters: <strong>B</strong>, the storm-motion-relative
            900–600 hPa thickness asymmetry (frontal versus symmetric structure), and the
            lower and upper thermal winds <strong>−V<sub>T</sub><sup>L</sup></strong>{' '}
            (900–600 hPa) and <strong>−V<sub>T</sub><sup>U</sup></strong> (600–300 hPa),
            positive for a warm core. Each panel of every diagram is a two-dimensional slice
            of that three-dimensional space, so the shaded regions are the projection of each
            class with the third parameter left free.
          </p>

          <div className="mb-5 grid gap-3 sm:grid-cols-3">
            {crit.classes.map((c) => (
              <div
                key={c.code}
                className="rounded-xl border-2 bg-white p-4"
                style={{ borderColor: c.color + '55' }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold text-white"
                    style={{ backgroundColor: c.color }}
                  >
                    {c.code}
                  </span>
                  <span className="text-sm font-semibold capitalize text-slate-900">{c.name}</span>
                </div>
                <ul className="mt-3 space-y-0.5 font-mono text-xs text-slate-600">
                  {c.terms.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <FigurePanel
            src={fig('reference')}
            alt="Reference diagram of the canonical cyclone phase space class regions"
            caption={`Schematic of the class regions, carrying no data. Grey marks where more than one class can claim a point — a real property of the definitions, where the timestep precedence (${crit.precedence.join(' > ')}) decides. Blank corners belong to no cyclone type.`}
            source="scripts/cps_analysis/make_reference_diagram.py"
          />
        </section>

        {/* ---------------- Protocol ---------------- */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Classification protocol</h2>
          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600">
            <p>
              <strong>Thresholds.</strong> {crit.source}. A timestep satisfying more than one
              class specification is resolved by precedence: {crit.precedence.join(' > ')}.
            </p>
            <p>
              <strong>Persistence gate.</strong> A cyclone is only <em>identified</em> as a
              class when it holds that structure for <strong>{crit.persistence_hours} consecutive
              hours</strong> — Guishard et al. (2009), &ldquo;more than one diurnal cycle&rdquo;,
              adopted for the South Atlantic by Gozzo et al. (2014). The CPS parameters are used
              unsmoothed; the literature that this protocol follows controls short-term noise
              through persistence rather than through a running mean.
            </p>
            <p>
              <strong>Warm-seclusion filter.</strong> The phase space alone cannot separate a
              tropical cyclone from a Shapiro–Keyser warm seclusion: the occlusion sequence
              passes through hybrid and then symmetric warm-core structure, and it does so for
              well over {crit.persistence_hours} h. A persistent warm core is therefore only
              accepted as tropical when the run sits equatorward of{' '}
              {Math.abs(crit.tt_max_poleward_lat)}°S and spends at least{' '}
              {Math.round(crit.tt_min_ocean_fraction * 100)}% of its time over ocean. In this
              population the filter rejected{' '}
              <strong>{manifest.runs.tropical_seclusion} warm seclusions</strong> and{' '}
              {manifest.runs.tropical_indeterminate} indeterminate warm cores.
            </p>
            <p>
              <strong>The same guard, for the subtropical class.</strong> Until 2026-08-10 the
              seclusion filter ran only on tropical runs, and a persistent hybrid run was
              accepted on the persistence gate alone — the one criterion a Shapiro–Keyser
              occlusion satisfies without difficulty. Every hybrid run is now tested on three
              clauses: genesis between{' '}
              {Math.abs(manifest.guards.genesis_band[1])}°S and{' '}
              {Math.abs(manifest.guards.genesis_band[0])}°S (Gozzo criterion 1),{' '}
              {Math.round(manifest.guards.min_ocean_fraction * 100)}% of the run over ocean,
              and the run beginning no more than {manifest.guards.max_hours_past_peak} h after
              the cyclone&apos;s own intensity peak. The last is the physical discriminator:
              a diabatically built warm core re-energises the system, so peak intensity
              follows the structure, whereas a secluded warm core is the terminal stage and
              the peak has already passed. Of{' '}
              {manifest.runs.subtropical_accepted + manifest.runs.subtropical_out_of_band + manifest.runs.subtropical_seclusion}{' '}
              persistent hybrid runs, <strong>{manifest.runs.subtropical_accepted} were
              accepted</strong>; {manifest.runs.subtropical_out_of_band} failed the genesis
              or ocean clause and {manifest.runs.subtropical_seclusion} were rejected as warm
              seclusions.
            </p>
            <p>
              <strong>Characteristic classes.</strong> A cyclone that never sustains a structure
              for {crit.persistence_hours} h is not structureless. When one structure dominates
              at least {Math.round(crit.min_dominance * 100)}% of its classifiable timesteps it
              is labelled <code className="rounded bg-slate-100 px-1">*_like</code> — a statement
              about <em>characteristics</em>, not an identification. The literature threshold is
              left untouched for the named classes.
            </p>
          </div>
        </section>

        {/* ---------------- Class composition ---------------- */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Classification of the {pop.catalogue.toLocaleString()} cyclones
          </h2>

          <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {named
              .filter((c) => c.n > 0)
              .map((c) => (
                <div key={c.code} className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex items-center justify-between">
                    <span
                      className="rounded-md px-2 py-0.5 text-xs font-bold text-white"
                      style={{ backgroundColor: c.color }}
                    >
                      {c.code}
                    </span>
                    <span className="text-xs text-slate-400">{c.pct}%</span>
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">{c.n.toLocaleString()}</p>
                  <p className="mt-1 text-xs leading-relaxed text-slate-500">{c.label}</p>
                </div>
              ))}
          </div>

          <StatsTable
            title="Full classification"
            columns={[
              { key: 'code', label: 'Class' },
              { key: 'label', label: 'Meaning' },
              { key: 'n', label: 'n', align: 'right' },
              { key: 'pct', label: '%', align: 'right' },
            ]}
            rows={manifest.classes.map((c) => ({
              code: c.code,
              label: c.label,
              n: c.n.toLocaleString(),
              pct: c.pct.toFixed(1),
            }))}
            caption={`TT (tropical transition) and ET (extratropical transition, TC → EC in the strict sense of Evans and Hart 2003) are empty by construction: the genesis boxes of this catalogue exclude every documented South Atlantic tropical system, so there is no tropical cyclone to transition from or to. The *_like classes describe characteristics that never reached the ${crit.persistence_hours} h gate.`}
          />

          <div className="mt-5">
            <FigurePanel
              src={fig('composition')}
              alt="Phase-class composition of each Energy Pattern"
              caption="Left: phase-class composition of each Energy Pattern. Right: the transition classes alone, which are the scientifically interesting part and invisible in the stacked bars."
              source="scripts/cps_analysis/step4_phase_figures.py"
            />
          </div>
        </section>

        {/* ---------------- Headline figure ---------------- */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Subtropical structure by Energy Pattern
          </h2>
          <FigurePanel
            src={fig('ep_relative')}
            alt="Subtropical frequency of each Energy Pattern relative to the pooled population"
            caption={`(a) Frequency within each Energy Pattern with Wilson 95% intervals, against the pooled EPALL reference. (b) The same expressed as a ratio to EPALL, on a log scale. EPALL is the union EP1 + EP2 + EP3 = ${pop.ep_labelled.toLocaleString()} cyclones — not the full catalogue, since only clustered cyclones carry an Energy Pattern. Because each EP is nested in that reference, the ratio is a descriptive effect size; significance comes from Fisher's exact test of each EP against the other two pooled, Holm-corrected over the nine contrasts.`}
            source="scripts/cps_analysis/step8_ep_relative_frequency.py"
          />

          <div className="mt-5">
            <StatsTable
              title="Single-state subtropical (SC) — each EP against the other two pooled"
              columns={[
                { key: 'ep', label: 'EP' },
                { key: 'rate', label: 'rate', align: 'right' },
                { key: 'ci', label: '95% CI', align: 'center' },
                { key: 'ratio', label: '×EPALL', align: 'right' },
                { key: 'or', label: 'OR', align: 'right' },
                { key: 'p', label: 'p', align: 'right' },
                { key: 'holm', label: 'Holm', align: 'center' },
              ]}
              rows={scRows.map((r) => ({
                ep: r.ep,
                rate: `${r.rate_pct}% (${r.k}/${r.n})`,
                ci: `${r.rate_lo_pct}–${r.rate_hi_pct}%`,
                ratio: r.ratio.toFixed(2),
                or: r.odds_ratio.toFixed(2),
                p: pFormat(r.p),
                holm: r.significant_holm ? '✓ survives' : '—',
              }))}
              caption={`EPALL rate ${scRows[0]?.epall_rate_pct}%. All three contrasts survive Holm correction over the nine tested — the only place in this analysis where that happens. The ordering is monotonic in the Energy Patterns' baroclinic conversion.`}
            />
          </div>
        </section>

        {/* ---------------- Phase space occupancy ---------------- */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Where each Energy Pattern sits</h2>
          <FigurePanel
            src={fig('phase_space_by_ep')}
            alt="Cyclone phase space diagrams for EPALL and each Energy Pattern"
            caption="Every classifiable timestep, as a density of the fraction of each column's timesteps per bin on a shared logarithmic scale, so the columns compare directly despite very unequal sample sizes. Top row: B against the lower thermal wind. Bottom row: upper against lower thermal wind."
            source="scripts/cps_analysis/step5_phase_space_figures.py"
          />
          <div className="mt-5">
            <FigurePanel
              src={fig('single_state_sc')}
              alt="Cyclone phase space restricted to the single-state subtropical cyclones"
              caption="Restricted to the cyclones whose only persistent state is subtropical. The density shows only their subtropical-classified timesteps; the grey dots are the rest of their life. Plotting all their timesteps would reproduce something close to the whole-population cloud and hide the classification — these cyclones spend a large part of their life in other structures, just never for 36 consecutive hours."
              source="scripts/cps_analysis/step5_phase_space_figures.py"
            />
          </div>
        </section>

        {/* ---------------- Transitions ---------------- */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">What a transition looks like</h2>
          <FigurePanel
            src={fig('trajectories')}
            alt="Phase-space trajectories of the transitioning cyclones"
            caption="Each marker is one 3-hourly timestep, coloured by the structure it holds at that moment; lines connect a cyclone's successive timesteps. The convention of the case-study literature, applied to a whole class at once so the shape of a transition can be read as a population. ST is the extratropical-to-subtropical pathway, SD its reverse."
            source="scripts/cps_analysis/step6_transition_trajectories.py"
          />
          <div className="mt-5">
            <FigurePanel
              src={fig('transitions')}
              alt="Where subtropical structure appears in the life cycle, how long it lasts, and when in the year"
              caption="Timing is expressed in life-cycle phase rather than hours from genesis: the phases come from the project's own vorticity-based segmentation, independent of the CPS, and they normalise for very unequal cyclone lifetimes."
              source="scripts/cps_analysis/step4_phase_figures.py"
            />
          </div>
        </section>

        {/* ---------------- Warm seclusion filter ---------------- */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">The warm-seclusion problem</h2>
          <p className="mb-4 text-sm leading-relaxed text-slate-600">
            This is the step that decides whether the analysis reports tropical cyclones that
            are not there. Persistence alone does not solve it — a warm seclusion routinely
            holds symmetric warm-core structure far beyond the gate. The rejected runs in this
            population sit at 54–68°S, deep in the Southern Ocean, and reach their warm core a
            median 75 h after genesis, at the end of a baroclinic life cycle.
          </p>
          <FigurePanel
            src={fig('tropical_runs')}
            alt="Every persistent tropical run, accepted or rejected by the tropical-transition test"
            caption={`Every persistent tropical run in the catalogue. The shaded band is where a warm core is accepted as tropical (equatorward of ${Math.abs(crit.tt_max_poleward_lat)}°S). The equatorward bound is deliberately absent: Iba, the first documented pure tropical cyclogenesis in the western South Atlantic, formed at about 20°S, and a system further equatorward is more plausible as tropical, not less.`}
            source="scripts/cps_analysis/step4_phase_figures.py"
          />
        </section>

        {/* ---------------- Caveats ---------------- */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Caveats</h2>
          <ResultSummaryCallout type="warning" title="Read before quoting any number here">
            <ul className="list-disc space-y-2 pl-4 text-sm">
              <li>
                <strong>The two TC cyclones are candidates, not identifications.</strong> They
                have shallow warm cores and have not been inspected case by case. Do not report
                them as identified South Atlantic tropical cyclones.
              </li>
              <li>
                <strong>TT and ET are empty by construction.</strong> Catarina, Anita, Arani,
                Deni, Guará and Iba all form outside this catalogue&apos;s genesis boxes; Raoni,
                Yakecan, Akará and Biguá postdate the record. This is a property of the
                population, not a failure of the method.
              </li>
              <li>
                <strong>The subtropical count is threshold-sensitive by a factor of 6–8</strong>{' '}
                across the six threshold sets tested, at every level of strictness. Any
                subtropical number must be quoted with its threshold set attached.
              </li>
              <li>
                <strong>Multiple comparisons matter here.</strong> Nine contrasts were tested.
                Only EP2 × ST survives Holm correction; the other two nominally significant
                results do not.
              </li>
              <li>
                <strong>The 500 km CPS radius may not represent small, shallow systems well</strong>{' '}
                — a caveat Conrado et al. (2024) raise about their own work — and 13 cyclones
                (0.2%) have no CPS series at all.
              </li>
            </ul>
          </ResultSummaryCallout>
        </section>

        {/* ---------------- Validation status ---------------- */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Validation status</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600">
            <p>
              A gallery of <strong>{manifest.gallery.n_figures}</strong> single-cyclone phase
              diagrams — one sampled case per class × year of genesis × genesis region, across{' '}
              {manifest.gallery.n_classes} classes — is generated for case-by-case visual
              validation, the step Gozzo et al. performed manually and this analysis has not yet
              completed. It lives in the repository rather than on this site.
            </p>
            <p className="mt-2">
              Two independent checks against the literature do pass: the relaxed protocol gives
              9.3 subtropical cyclones per year against Gozzo et al.&apos;s 7.2, and the strict
              Guishard threshold set gives 1.8 per year against Evans and Braun&apos;s 1.2, with
              the DJF maximum reproduced in both. The named South Atlantic subtropical cyclones
              Bapo and Cari are both classified subtropical.
            </p>
          </div>
        </section>

        {/* ---------------- Sources ---------------- */}
        <ResultSummaryCallout type="info" title="Scripts and outputs">
          <ul className="space-y-1 text-sm">
            <li>
              <strong>Pipeline:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">scripts/cps_analysis/</code> — reference
              diagram plus steps 1–8, run by{' '}
              <code className="rounded bg-slate-100 px-1">run_all.py</code>
            </li>
            <li>
              <strong>Thresholds, gates and colours:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">scripts/cps_analysis/cps_criteria.py</code>{' '}
              — the single source of truth, with the source quote for every threshold set
            </li>
            <li>
              <strong>Science record:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">scripts/cps_analysis/SCIENTIFIC_NOTES.md</code>{' '}
              (canonical) and{' '}
              <code className="rounded bg-slate-100 px-1">scripts/cps_analysis/sensitivity/</code>{' '}
              (the six threshold sets tested, kept as a record of what motivated the canonical design)
            </li>
            <li>
              <strong>Per-cyclone lists:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/cps_analysis/cyclone_lists_by_class.csv</code>
            </li>
            <li>
              <strong>This page:</strong> every number is read from{' '}
              <code className="rounded bg-slate-100 px-1">web/src/content/cps_manifest.json</code>,
              regenerated by{' '}
              <code className="rounded bg-slate-100 px-1">scripts/web/extract_cps_site_data.py</code>
            </li>
          </ul>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
