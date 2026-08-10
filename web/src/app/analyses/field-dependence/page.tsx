import type { Metadata } from 'next'
import { GitCompareArrows, Search } from 'lucide-react'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import AnalysisCardGrid from '@/components/analysis/AnalysisCardGrid'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import { SimpleTerms, InThisStudy, TestFlow } from '@/components/analysis/Didactic'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'LEC–Field Dependence',
  description:
    'How well do dynamical field features predict the energetics of individual South Atlantic cyclones?',
}

export default function FieldDependencePage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="LEC–Field Dependence Analysis"
        badge="PREDEP"
        subtitle="Predictive Dependence between Dynamical Fields and Lorenz Energy Cycle"
        description="Investigates, at the individual-cyclone level, how much scalar features extracted from ERA5 dynamical fields help predict Lorenz Energy Cycle terms during the intensification phase. Uses the PREDEP metric (Assunção et al. 2025) alongside Pearson and Spearman correlations as baseline references."
      />

      <div className="mb-8 space-y-4">
        <ResultSummaryCallout type="result" title="Key Finding">
          <p>
            All 24 LEC terms differ significantly across EP1, EP2, and EP3.
            The strongest predictive associations (PREDEP &gt; 0.70) are found in EP3
            for barotropic conversion (BKz) predicted by upper-level kinetic energy
            advection and ageostrophic flux convergence. Canonical LEC terms used in
            the cluster analysis (Ca, Ck, Ge, BAe, BKe, Ae, Ke) show moderate-to-strong
            predictability from all five dynamical fields.
          </p>
        </ResultSummaryCallout>

        <ResultSummaryCallout type="info" title="Analysis Framework">
          <ul className="list-inside list-disc space-y-1 text-sm">
            <li>
              <strong>2,733 cyclones</strong> (EP1 = 330, EP2 = 776, EP3 = 1,625) during
              the intensification phase, sampled at central timesteps.
            </li>
            <li>
              <strong>5 dynamical fields</strong>: PV at 850 and 200 hPa, temperature
              advection at 850 hPa, AFC and KE advection at 250 hPa.
            </li>
            <li>
              <strong>13 spatial features</strong> per field: domain mean, centre value,
              4 borders, 2 contrasts, 4 quadrants, and absolute domain mean.
            </li>
            <li>
              <strong>Direction</strong>: LEC term = response (Y), dynamical
              feature = predictor (X). PREDEP answers: &quot;how much does the feature
              reduce prediction uncertainty of the LEC term?&quot;
            </li>
          </ul>
        </ResultSummaryCallout>
      </div>

      <MethodsPanel summary="How the 154 scalar variables are tested for EP differences, and how the association between dynamical fields and LEC terms is quantified.">
        <p className="text-sm text-slate-600">
          This analysis answers two questions with two different statistical machineries.
          First, <strong>do the Energy Patterns differ</strong> on each LEC term and each
          dynamical descriptor? Second, <strong>how strongly does a dynamical field
          predict a LEC term</strong> across individual cyclones? The first is a
          group-comparison problem, the second an association problem.
        </p>
        <p className="text-sm text-slate-600">
          Both share one discipline. A <strong>global test</strong> asks whether any
          difference exists at all; a <strong>post-hoc test</strong> localises which groups
          differ; a <strong>multiple-comparison correction</strong> keeps the extra tests
          from manufacturing false positives; and an <strong>effect size</strong> reports
          how large the difference actually is, independent of how many cyclones were
          sampled.
        </p>
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
            EP2 = 776, EP3 = 1,625); the{' '}
            <Link href="/analyses/cps" className="text-indigo-600 hover:underline">
              Cyclone Phase Space
            </Link>{' '}
            analysis uses a different, larger population and states it separately.
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
              consequence is visible in the{' '}
              <Link href="/analyses/cps" className="text-indigo-600 hover:underline">
                Cyclone Phase Space
              </Link>{' '}
              results, where one contrast has a raw <em>p</em> = 0.017 — nominally
              significant — but a Holm-adjusted <em>p</em> = 0.139, and is therefore{' '}
              <em>not</em> reported as an established result.
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

      </MethodsPanel>
      <AnalysisCardGrid
        columns={2}
        cards={[
          {
            title: 'EP Differences',
            description:
              'Are Energy Patterns statistically different? Significance heatmaps, effect-size analysis, volcano plots, and rankings quantifying how strongly LEC terms and dynamical features discriminate between EP1, EP2, and EP3.',
            href: '/analyses/field-dependence/ep-differences',
            icon: GitCompareArrows,
          },
          {
            title: 'Dependence Explorer',
            description:
              'Interactive exploration of PREDEP, Pearson, and Spearman metrics. Reference heatmaps, filterable drill-down by field, feature, LEC term, and EP, with on-demand scatterplots.',
            href: '/analyses/field-dependence/dependence-explorer',
            icon: Search,
          },
        ]}
      />
    </div>
  )
}
