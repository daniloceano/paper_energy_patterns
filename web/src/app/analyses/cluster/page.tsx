import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import StepTimeline from '@/components/analysis/StepTimeline'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import { CLUSTER_STEPS, ENERGY_PATTERNS, DATASET_STATS } from '@/lib/constants'
import MethodsPanel from '@/components/analysis/MethodsPanel'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import StatsTable from '@/components/analysis/StatsTable'
import { SimpleTerms, InThisStudy } from '@/components/analysis/Didactic'

export const metadata: Metadata = {
  title: 'Cluster Analysis',
  description:
    'PCA + K-Means clustering of Lorenz Energy Cycle diagnostics to identify three Energy Patterns.',
}

export default function ClusterPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Cluster Analysis"
        subtitle="Energy Pattern Classification"
        badge="Analysis Pipeline"
        description="South Atlantic extratropical cyclones are classified into three Energy Patterns (EP1, EP2, EP3) using PCA-based K-Means clustering on 7 Lorenz Energy Cycle terms across 4 lifecycle phases. The pipeline processes 3,820 cyclones with complete lifecycles from 1979–2020."
      />

      <div className="flex gap-10">
        {/* Sidebar timeline */}
        <div className="hidden w-64 shrink-0 lg:block">
          <div className="sticky top-24">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Analysis Steps
            </h3>
            <StepTimeline
              steps={CLUSTER_STEPS.map((s) => ({
                number: s.number,
                title: s.title,
                shortTitle: s.shortTitle,
                href: `/analyses/cluster/${s.slug}`,
                completed: true,
              }))}
            />
          </div>
        </div>

        {/* Main content */}
        <div className="min-w-0 flex-1 space-y-8">
          <ResultSummaryCallout type="result" title="Key Result">
            <p>
              Three distinct Energy Patterns were identified with k = 3 (optimal via
              5-index ensemble). <strong>EP1</strong> (N={ENERGY_PATTERNS.EP1.count},{' '}
              {ENERGY_PATTERNS.EP1.percentage}%): strong barotropic and baroclinic
              conversions. <strong>EP2</strong> (N={ENERGY_PATTERNS.EP2.count},{' '}
              {ENERGY_PATTERNS.EP2.percentage}%): intermediate, externally forced.{' '}
              <strong>EP3</strong> (N={ENERGY_PATTERNS.EP3.count},{' '}
              {ENERGY_PATTERNS.EP3.percentage}%): weak background energetics.
            </p>
          </ResultSummaryCallout>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-slate-900">Pipeline Overview</h2>
            <p className="text-sm leading-relaxed text-slate-600">
              The cluster analysis follows a five-step pipeline. Each step builds on the
              previous one, from raw energy data filtering through PCA dimensionality
              reduction to final K-Means classification and Lorenz Phase Space
              visualisation.
            </p>
          </div>

          {/* Methods & Statistics */}
          <MethodsPanel summary="How the 28-feature matrix is built and reduced, how k is chosen objectively, and how interannual trends in EP occurrence are tested.">
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                1 · Building the feature matrix
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                Only cyclones with a complete lifecycle are kept ({DATASET_STATS.filteredCyclones.toLocaleString()}{' '}
                of {DATASET_STATS.totalCyclones.toLocaleString()}). For each cyclone the
                seven eddy-related LEC terms are averaged within each of the four lifecycle
                phases and laid out as a single row, giving 7 × 4 = <strong>28
                features</strong> per cyclone. Every column is then standardised to zero
                mean and unit variance.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="z_{ij} = \frac{x_{ij} - \mu_j}{s_j}"
                  label="Standardisation (StandardScaler)"
                  terms={{
                    'z_ij': 'Standardised value of feature j for cyclone i (dimensionless)',
                    'x_ij': 'Raw value of feature j for cyclone i',
                    'μ_j': 'Mean of feature j across all cyclones',
                    's_j': 'Standard deviation of feature j across all cyclones',
                    'i': 'Cyclone index, i = 1 … N',
                    'j': 'Feature index, j = 1 … 28 (one per term × phase combination)',
                  }}
                  notes="Standardisation is essential here because the LEC terms carry different units and magnitudes — energy reservoirs in J m⁻² and conversions in W m⁻². Without it, whichever term happened to have the largest numerical range would dominate the clustering for purely dimensional reasons."
                />
              </div>
              <SimpleTerms>
                <p>
                  The 28 features are a fingerprint of how a cyclone handled energy over its
                  whole life — not just how intense it got, but whether it converted
                  baroclinically early and barotropically late, whether it imported or
                  exported eddy energy, and so on. Clustering on that fingerprint is what
                  makes the classification process-based rather than intensity-based.
                </p>
              </SimpleTerms>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                2 · Dimensionality reduction with PCA
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                A <strong>single, global PCA</strong> is applied jointly across all 28
                standardised features — not separately per phase — so that correlations
                between energy terms and between lifecycle phases are captured together.
                Principal components are ordered by the variance they explain, and the first{' '}
                <strong>15 components</strong> are retained, covering ≈ 90% of the
                cumulative variance.
              </p>
              <SimpleTerms>
                <p>
                  The 28 features are heavily redundant: a cyclone with strong{' '}
                  <em>C</em><sub>a</sub> during intensification usually also has strong{' '}
                  <em>C</em><sub>a</sub> at maturity, and large <em>A</em><sub>e</sub>
                  {' '}tends to accompany large <em>K</em><sub>e</sub>. PCA rewrites those 28
                  correlated numbers as 15 independent ones that carry almost the same
                  information. Clustering in that compressed space is both faster and less
                  distorted by redundancy — an issue known as the curse of dimensionality.
                </p>
              </SimpleTerms>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                3 · Choosing the number of clusters objectively
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                K-Means requires the number of clusters to be fixed in advance, so choosing
                it by eye would make the whole result subjective. Instead, five cluster
                validity indices — each measuring compactness and separation differently —
                are computed for every candidate k from 3 to 15, rescaled to a common 0–1
                range, and averaged into a single ensemble score. The k that maximises the
                ensemble is selected.
              </p>
              <div className="mt-3">
                <StatsTable
                  title="Cluster validity indices"
                  columns={[
                    { key: 'idx', label: 'Index' },
                    { key: 'opt', label: 'Optimum' },
                    { key: 'what', label: 'What it measures' },
                  ]}
                  rows={[
                    { idx: 'Silhouette', opt: 'Max', what: 'Cohesion within a cluster against separation from the nearest other cluster' },
                    { idx: 'Davies–Bouldin', opt: 'Min', what: 'Worst-case similarity between a cluster and its most similar neighbour' },
                    { idx: 'Calinski–Harabasz', opt: 'Max', what: 'Ratio of between-cluster to within-cluster dispersion' },
                    { idx: 'Score Function', opt: 'Max', what: 'Bounded combination of compactness and separation' },
                    { idx: 'Gap statistic', opt: 'Max', what: 'Observed dispersion against that expected under a random null reference' },
                  ]}
                  caption="Davies–Bouldin is inverted before averaging so that higher is better for every index. The ensemble consistently selects k = 3."
                />
              </div>
              <SimpleTerms>
                <p>
                  Any single index can be fooled by a particular data geometry. Requiring
                  five indices that disagree by construction to nonetheless point at the
                  same answer is a much stronger argument than quoting whichever one gave
                  the most convenient result.
                </p>
              </SimpleTerms>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                4 · K-Means clustering
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                K-Means partitions the cyclones in the retained 15-component PCA space by
                minimising the total squared distance from each cyclone to its cluster
                centre.
              </p>
              <div className="mt-3">
                <FormulaBlock
                  formula="\mathcal{J} = \sum_{c=1}^{C}\sum_{i \in \mathcal{I}_c}\left\lVert \mathbf{y}_i - \boldsymbol{\mu}_c \right\rVert^2"
                  label="Within-cluster sum of squares"
                  terms={{
                    'J': 'Objective function minimised by the algorithm',
                    'C': 'Number of clusters (C = 3)',
                    'c': 'Cluster index',
                    'I_c': 'Set of cyclones assigned to cluster c',
                    'y_i': 'PCA-score vector of cyclone i (15 components)',
                    'μ_c': 'Centroid of cluster c — the mean position of its members',
                    '‖·‖²': 'Squared Euclidean distance in PCA space',
                  }}
                  notes="Run with k-means++ initialisation and 100 restarts (random_state = 42), keeping the best solution. The restarts matter because K-Means converges to a local minimum that depends on where the centroids start."
                />
              </div>
              <InThisStudy>
                <p>
                  The three resulting clusters are labelled EP1, EP2 and EP3 by the
                  magnitude of their barotropic conversion <em>C</em><sub>k</sub>. Note
                  what this procedure does <em>not</em> assume: nothing about intensity,
                  season, or genesis region enters the clustering. That EP1 turns out to be
                  the most intense group, and EP2 the most prone to subtropical transition,
                  are findings about the energetics — not inputs to it.
                </p>
              </InThisStudy>
            </div>

            {/* Trends */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900">
                5 · Trends in Energy-Pattern occurrence
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

          </MethodsPanel>
          {/* Steps grid */}
          <div className="grid gap-4 sm:grid-cols-2">
            {CLUSTER_STEPS.map((step) => (
              <a
                key={step.slug}
                href={`/analyses/cluster/${step.slug}`}
                className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                    {step.number}
                  </span>
                  <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600">
                    {step.shortTitle}
                  </h3>
                </div>
                <p className="text-sm text-slate-500">{step.description}</p>
                <p className="mt-2 text-xs text-slate-400">
                  {step.figures.length} figure(s) · {step.outputs.length} output(s)
                </p>
              </a>
            ))}
          </div>

          {/* Mobile timeline */}
          <div className="lg:hidden">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">
              Step Navigation
            </h3>
            <StepTimeline
              steps={CLUSTER_STEPS.map((s) => ({
                number: s.number,
                title: s.title,
                shortTitle: s.shortTitle,
                href: `/analyses/cluster/${s.slug}`,
                completed: true,
              }))}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
