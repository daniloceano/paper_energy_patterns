import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import DiagnosticHeader from '@/components/analysis/DiagnosticHeader'
import DiagnosticNav from '@/components/analysis/DiagnosticNav'
import FormulaBlock from '@/components/analysis/FormulaBlock'
import FileProvenanceBadge from '@/components/analysis/FileProvenanceBadge'
import DiagnosticCompositesClient from '@/components/analysis/DiagnosticCompositesClient'
import { DIAGNOSTICS, FLUX_DIAGNOSTICS, DIAGNOSTIC_FIGURE_SLUGS } from '@/lib/constants'

// Direct JSON imports (bundled at build time, no fs.readFileSync at runtime)
import fullStatsData from '@/content/composite_domain_stats_full_intensification.json'
import fullFluxesData from '@/content/composite_boundary_fluxes_full_intensification.json'
import fullFiguresData from '@/content/composite_figures_manifest_full_intensification.json'
import centralStatsData from '@/content/composite_domain_stats_central_time.json'
import centralFluxesData from '@/content/composite_boundary_fluxes_central_time.json'
import centralFiguresData from '@/content/composite_figures_manifest_central_time.json'
// Intense 10 data (stub files created, will be populated when data is generated)
import intense10StatsData from '@/content/composite_domain_stats_intense_10.json'
import intense10FluxesData from '@/content/composite_boundary_fluxes_intense_10.json'
import intense10FiguresData from '@/content/composite_figures_manifest_intense_10.json'

// Force static generation at build time
export const dynamic = 'force-static'

interface DiagnosticPageProps {
  params: Promise<{ diagnostic: string }>
}

// --- JSON shapes from step5 + extract_composite_site_data.py ---
interface DomainStatEntry {
  diagnostic_id: string
  ep: string
  unit: string
  inside_15x15: string | null
  outside_15x15: string | null
}

interface BoundaryFluxEntry {
  diagnostic_id: string
  ep: string
  unit: string
  north: string | null
  south: string | null
  east: string | null
  west: string | null
  north_anom?: string | null
  south_anom?: string | null
  east_anom?: string | null
  west_anom?: string | null
}

interface FigureEntry {
  exists: boolean
  api_path: string
}

interface FiguresManifest {
  [diagId: string]: {
    real: FigureEntry
    anom?: FigureEntry
    diff?: FigureEntry
  }
}

export async function generateStaticParams() {
  return Object.values(DIAGNOSTICS).map((d) => ({
    diagnostic: d.slug,
  }))
}

export async function generateMetadata({ params }: DiagnosticPageProps): Promise<Metadata> {
  const { diagnostic: slug } = await params
  const diag = Object.values(DIAGNOSTICS).find((d) => d.slug === slug)
  if (!diag) return { title: 'Not Found' }
  return {
    title: diag.name,
    description: diag.description,
  }
}

export default async function DiagnosticPage({ params }: DiagnosticPageProps) {
  const { diagnostic: slug } = await params
  const diag = Object.values(DIAGNOSTICS).find((d) => d.slug === slug)
  if (!diag) notFound()

  const isFluxDiag = FLUX_DIAGNOSTICS.includes(diag.id)

  // Use directly imported JSON data (bundled at build time)
  const fullStats = fullStatsData as DomainStatEntry[]
  const fullFluxes = fullFluxesData as BoundaryFluxEntry[]
  const fullFigures = fullFiguresData as FiguresManifest
  const centralStats = centralStatsData as DomainStatEntry[]
  const centralFluxes = centralFluxesData as BoundaryFluxEntry[]
  const centralFigures = centralFiguresData as FiguresManifest
  // Intense 10 (may be empty if files don't exist yet)
  const intense10Stats = intense10StatsData as DomainStatEntry[]
  const intense10Fluxes = intense10FluxesData as BoundaryFluxEntry[]
  const intense10Figures = intense10FiguresData as FiguresManifest

  const figSlug = DIAGNOSTIC_FIGURE_SLUGS[diag.id]

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      
      {/* Navigation between diagnostics */}
      <div className="mb-6">
        <DiagnosticNav currentSlug={diag.slug} />
      </div>
      
      <DiagnosticHeader
        name={diag.name}
        shortName={diag.shortName}
        level={diag.level}
        unit={diag.unit}
        description={diag.description}
        hasAnomaly={diag.hasAnomaly}
      />

      <div className="space-y-8">
        {/* Physical Objective */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Physical Objective
          </h2>
          <p className="text-sm leading-relaxed text-slate-600">
            {diag.physicalObjective}
          </p>
        </section>

        {/* Formula */}
        <section>
          <h2 className="mb-3 text-lg font-bold text-slate-900">
            Formula
          </h2>
          <FormulaBlock
            formula={diag.formula}
            terms={diag.formulaTerms}
            references={diag.references}
            label={`${diag.shortName} — ${diag.level}`}
          />
        </section>

        {/* Client component with mode toggle */}
        <DiagnosticCompositesClient
          diag={diag}
          figSlug={figSlug}
          isFluxDiag={isFluxDiag}
          fullFigures={fullFigures}
          fullStats={fullStats}
          fullFluxes={fullFluxes}
          centralFigures={centralFigures}
          centralStats={centralStats}
          centralFluxes={centralFluxes}
          intense10Figures={intense10Figures}
          intense10Stats={intense10Stats}
          intense10Fluxes={intense10Fluxes}
        />

        <FileProvenanceBadge
          files={[
            'data/era5_ep_structure/precomputed_composites_ep1.nc',
            'data/era5_ep_structure/precomputed_composites_ep2.nc',
            'scripts/ep_structure_analysis/step4_create_figures.py',
            'scripts/ep_structure_analysis/step5_update_scientific_notes.py',
            'results/ep_structure/composite_stats_full_intensification.json',
            'results/ep_structure/composite_stats_central_time.json',
          ]}
          label="Source files"
        />
      </div>
    </div>
  )
}

