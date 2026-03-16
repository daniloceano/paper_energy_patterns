import type { Metadata } from 'next'
import { TrendingDown } from 'lucide-react'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ResultSummaryCallout from '@/components/analysis/ResultSummaryCallout'
import FigurePanel from '@/components/analysis/FigurePanel'
import { ENERGY_PATTERNS } from '@/lib/constants'
import { readManifest, figureUrl } from '@/lib/utils'

export const metadata: Metadata = {
  title: 'Ck Subterms Analysis — EP1 Barotropic Decomposition',
  description:
    'Decomposition of barotropic energy conversion (Ck) into its five vertical-level subterms for EP1 South Atlantic extratropical cyclones.',
}

interface SubtermInfo {
  symbol: string
  name: string
  description: string
}

interface DominanceEntry {
  subterm_key: string
  symbol: string
  name: string
  description: string
  count: number
  percentage: number
}

interface CkSubtermsManifest {
  title: string
  phase: string
  phase_note: string
  sample_sizes: { ep1_total: number; ep1_with_lec: number; valid: number }
  validation: {
    mean_ck_zenodo_corrected: number
    mean_ck_new: number
    mean_subterm_sum: number
    mean_rel_error_pct: number
    note: string
  }
  subterms: SubtermInfo[]
  dominance: DominanceEntry[]
  figures: Record<string, string>
}

function loadManifest(): CkSubtermsManifest | null {
  try {
    return readManifest<CkSubtermsManifest>('ck_subterms_manifest.json')
  } catch {
    return null
  }
}

export default function CkSubtermsPage() {
  const manifest = loadManifest()
  const n_ep1 = manifest?.sample_sizes.ep1_total ?? ENERGY_PATTERNS.EP1.count
  const n_valid = manifest?.sample_sizes.valid ?? 385
  const dominance = manifest?.dominance ?? []

  const figures = {
    boxplots_subterms: figureUrl('figures/ck_subterms/ck_subterms_boxplots_subterms.png'),
    boxplots_total: figureUrl('figures/ck_subterms/ck_subterms_boxplots_total.png'),
    genesis_density: figureUrl('figures/ck_subterms/ck_subterms_genesis_density.png'),
    genesis_normaldiff: figureUrl('figures/ck_subterms/ck_subterms_genesis_normaldiff.png'),
    tracks: figureUrl('figures/ck_subterms/ck_subterms_tracks.png'),
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Ck Subterms Analysis"
        subtitle="EP1 — Barotropic Energy Conversion Decomposition"
        badge="EP1 Validation"
        description={`Decomposition of the barotropic kinetic energy conversion (Ck) into five subterms for EP1 cyclones (N=${n_ep1}). Dominance classification uses the intensification-phase mean of each subterm. Negative Ck indicates energy transfer from eddies to the mean flow.`}
      />

      <div className="space-y-10">
        {/* Scientific overview */}
        <ResultSummaryCallout type="info" title="Scientific Objective">
          <p>
            The barotropic conversion term C<sub>K</sub> represents the exchange of kinetic energy
            between cyclone-scale eddies and the background mean flow. In EP1 (the most energetically
            active cluster), C<sub>K</sub> is strongly <strong>negative</strong> during
            intensification (mean ≈ −16.5 W m⁻²), meaning that{' '}
            <em>eddies transfer energy to the mean flow</em> (K<sub>E</sub> → K<sub>Z</sub>). EP1
            cyclones are therefore strong energy exporters, not typical barotropic-instability
            systems (which would have C<sub>K</sub> &gt; 0). This analysis decomposes C<sub>K</sub>{' '}
            into five subterms (A–E) to identify which dynamical mechanism dominates this
            eddy-to-mean-flow energy export during EP1 intensification, and whether genesis
            location is systematically linked to a particular subterm.
          </p>
        </ResultSummaryCallout>

        {/* Methodology */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Methodology</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600 space-y-3">
            <p>
              <strong>Sign convention (paper.tex):</strong>{' '}
              C<sub>K</sub> &lt; 0 → K<sub>E</sub> → K<sub>Z</sub> (eddies transfer energy to
              the mean flow). C<sub>K</sub> &gt; 0 → K<sub>Z</sub> → K<sub>E</sub> (barotropic
              instability; mean flow accelerates eddies). EP1 cyclones have large negative C<sub>K</sub>
              — they are energy exporters, not barotropic-instability-driven systems.
            </p>
            <p>
              <strong>Subterm definition (paper.tex Eq. C_K):</strong> C<sub>K</sub> is
              vertically integrated and decomposed into five terms (A–E) arising from horizontal
              and vertical gradients of the background zonal and meridional wind. Each term is
              vertically integrated over pressure levels using{' '}
              <code className="rounded bg-slate-100 px-1">∑ (value × Δp / g)</code>, where
              Δp is the pressure-level interval (Pa) and g = 9.8 m s⁻².
            </p>
            <p>
              <strong>Phase:</strong> The <em>intensification</em> phase is used for all
              dominance classification. Intensification windows are taken from{' '}
              <code className="rounded bg-slate-100 px-1">results/ep1_full/all_ep1_cases.csv</code>.
            </p>
            <p>
              <strong>Normalization for density anomaly maps:</strong> Relative anomaly =
              minmax_normalize(dominant-group density) − minmax_normalize(all-EP1 density).
              Same formula as Figure 6 (genesis density KDE) in the paper. A shared diverging
              colorbar spans the maximum absolute anomaly across all valid subterm panels.
            </p>
          </div>
        </section>

        {/* Subterm metadata */}
        {manifest?.subterms && manifest.subterms.length > 0 && (
          <section>
            <h2 className="mb-4 text-lg font-bold text-slate-900">Ck Subterms (A–E)</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {manifest.subterms.map((s, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs">
                      {String.fromCharCode(65 + i)}
                    </span>
                    <span className="text-sm font-semibold text-slate-800">{s.symbol}</span>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{s.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Dominance distribution */}
        {dominance.length > 0 && (
          <section>
            <h2 className="mb-4 text-lg font-bold text-slate-900">
              Dominance Distribution (N={n_valid})
            </h2>
            <div className="grid gap-3 sm:grid-cols-3">
              {dominance.filter((d) => d.count > 0).map((d) => (
                <div
                  key={d.subterm_key}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-indigo-700">{d.symbol}</span>
                    <TrendingDown className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="text-2xl font-bold text-slate-900">{d.count}</p>
                  <p className="text-xs text-slate-500">{d.percentage}% of EP1 cyclones</p>
                  <p className="mt-1 text-xs text-slate-400 leading-relaxed">{d.name}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Figure 1a — Subterm Boxplots */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 1a — Ck Subterms (A–E) Boxplots</h2>
          <FigurePanel
            src={figures.boxplots_subterms}
            alt="Boxplots of Ck subterms A–E for EP1 cyclones during intensification (shared y-axis)"
            caption={`Distribution of each C_K subterm (A–E) for the ${n_valid} EP1 cyclones during the intensification phase (shared y-axis). Values are intensification-phase means (vertically integrated, W m⁻²). Negative values indicate K_E → K_Z energy transfer. Whiskers = 5th–95th percentile.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 1b — Total Ck Boxplot */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 1b — Total C_K Boxplot</h2>
          <FigurePanel
            src={figures.boxplots_total}
            alt="Boxplot of total Ck for EP1 cyclones during intensification"
            caption={`Distribution of total C_K for the ${n_valid} EP1 cyclones during the intensification phase (W m⁻²). Separated from the subterm figure to allow independent scaling. Negative values = K_E → K_Z (eddies export energy to mean flow). Whiskers = 5th–95th percentile.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 2 — Genesis density maps */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 2 — Genesis Density by Dominant Subterm</h2>
          <FigurePanel
            src={figures.genesis_density}
            alt="Genesis density maps: all EP1 and subsets by dominant Ck subterm"
            caption={`Multi-panel genesis density maps (KDE, Hoskins &amp; Hodges 2005 method). Top-left: all EP1 cyclones (N=${n_valid}). Remaining panels: cyclones where the named subterm is dominant during intensification. Units: cyclones / 10⁶ km² / year.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 3 — Normalized difference maps */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 3 — Normalized Genesis Density Anomaly</h2>
          <FigurePanel
            src={figures.genesis_normaldiff}
            alt="Normalized-difference genesis density maps relative to all EP1"
            caption="Normalized genesis density anomaly: minmax_normalize(dominant-subterm density) − minmax_normalize(all-EP1 density). Positive (red) regions indicate preferential genesis for a given subterm relative to the full EP1 population; negative (blue) regions indicate suppressed genesis. Same normalization as Figure 6 of the paper."
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Figure 4 — Full tracks */}
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">Figure 4 — EP1 Full Tracks</h2>
          <FigurePanel
            src={figures.tracks}
            alt="Full tracks of all EP1 systems and subsets by dominant Ck subterm"
            caption={`Full cyclone tracks for all EP1 systems (N=${n_valid}) and subsets where each subterm dominates. Background tracks shown in grey for context. Coloured tracks correspond to the dominant-subterm subset.`}
            source="scripts/ck_subterms_analysis/step3_validate_and_figures.py"
          />
        </section>

        {/* Validation note */}
        {manifest?.validation && (
          <ResultSummaryCallout type="warning" title="Validation Note">
            <p>
              {manifest.validation.note}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Mean new LEC Ck: {manifest.validation.mean_ck_new.toFixed(2)} W/m² |{' '}
              Mean subterm sum: {manifest.validation.mean_subterm_sum.toFixed(2)} W/m²
            </p>
          </ResultSummaryCallout>
        )}

        {/* Data source */}
        <ResultSummaryCallout type="info" title="Data Sources">
          <ul className="space-y-1 text-sm">
            <li>
              <strong>New LEC results:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/ck_analysis/lec_results/</code>{' '}
              — 385 EP1 cyclones with Ck subterms at vertical levels
            </li>
            <li>
              <strong>Intensification phases:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/ep1_full/all_ep1_cases.csv</code>
            </li>
            <li>
              <strong>Cluster assignments:</strong>{' '}
              <code className="rounded bg-slate-100 px-1">results/cluster/kmeans_clustered_data.csv</code>{' '}
              (cluster 0 = EP1)
            </li>
            <li>
              <strong>Tracks:</strong> Zenodo dataset (7439 cyclones) via{' '}
              <code className="rounded bg-slate-100 px-1">scripts/utils/load_data.py</code>
            </li>
          </ul>
        </ResultSummaryCallout>
      </div>
    </div>
  )
}
