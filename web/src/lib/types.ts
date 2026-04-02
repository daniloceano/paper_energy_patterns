// Domain types for the Energy Patterns scientific web application

// --- Energy Pattern Types ---
export type EnergyPatternId = 'EP1' | 'EP2' | 'EP3'

export interface EnergyPattern {
  id: EnergyPatternId
  label: string
  count: number
  percentage: number
  meanCk: number
  description: string
  color: string
}

// --- Lifecycle Phase ---
export type LifecyclePhase = 'incipient' | 'intensification' | 'mature' | 'decay'

export const LIFECYCLE_PHASES: LifecyclePhase[] = [
  'incipient',
  'intensification',
  'mature',
  'decay',
]

// --- Energy Terms ---
export type EnergyTerm = 'Ca' | 'Ck' | 'Ge' | 'BAe' | 'BKe' | 'Ae' | 'Ke'

export const ENERGY_TERMS: EnergyTerm[] = [
  'Ca',
  'Ck',
  'Ge',
  'BAe',
  'BKe',
  'Ae',
  'Ke',
]

export interface EnergyTermInfo {
  symbol: string
  name: string
  description: string
  unit: string
  formula?: string
}

// --- Diagnostic Types ---
export type DiagnosticId =
  | 'egr'
  | 'pv-200'
  | 'pv-850'
  | 'temperature-advection'
  | 'moisture-flux-divergence'
  | 'slp'
  | 'rk-criterion'
  | 'ke-advection'
  | 'afc'
  | 'btcr'

export interface Diagnostic {
  id: DiagnosticId
  slug: string
  name: string
  shortName: string
  level: string
  unit: string
  description: string
  physicalObjective: string
  formula: string
  formulaTerms: Record<string, string>
  references: string[]
  hasAnomaly: boolean
  colormap?: string
  range?: [number, number]
}

// --- Figure Types ---
export interface Figure {
  id: string
  filename: string
  path: string
  title: string
  caption: string
  altText: string
  source: string
  analysisStep?: string
  diagnostic?: DiagnosticId
  energyPattern?: EnergyPatternId
  width?: number
  height?: number
}

export interface FigureGroup {
  id: string
  title: string
  description: string
  figures: Figure[]
}

// --- Analysis Step Types ---
export interface AnalysisStep {
  number: number
  slug: string
  title: string
  shortTitle: string
  description: string
  inputs: string[]
  outputs: string[]
  scripts: string[]
  figures: string[]
}

// --- Statistics Types ---
export interface DomainStatistics {
  diagnostic: DiagnosticId
  energyPattern: EnergyPatternId
  insideMean: number
  outsideMean: number
  insideStd?: number
  outsideStd?: number
  unit: string
}

export interface BoundaryFlux {
  diagnostic: DiagnosticId
  energyPattern: EnergyPatternId
  north: number
  south: number
  east: number
  west: number
  unit: string
}

// --- PCA Types ---
export interface PCAResult {
  phase: LifecyclePhase
  explainedVariance: number[]
  cumulativeVariance: number[]
  loadings: Record<string, number[]>
  nComponents: number
}

// --- Cluster Types ---
export interface ClusterSummary {
  phase: LifecyclePhase
  cluster: number
  energyPattern: EnergyPatternId
  count: number
  centroids: Record<EnergyTerm, number>
  means: Record<EnergyTerm, number>
  stds: Record<EnergyTerm, number>
}

// --- Reference ---
export interface Reference {
  id: string
  authors: string
  year: number
  title: string
  journal: string
  doi?: string
  url?: string
}

// --- Navigation ---
export interface NavItem {
  label: string
  href: string
  icon?: string
  children?: NavItem[]
}

// --- Document ---
export interface DocumentInfo {
  id: string
  title: string
  description: string
  type: 'pdf' | 'markdown' | 'notebook'
  path: string
  generatedFrom?: string
}

// --- Cyclone Explorer Types ---
export interface CycloneTimestep {
  index: number
  time: string
  track_point_index: number
  panel_image: string
  has_panel: boolean
}

export interface CycloneMetadata {
  intensification_start: string
  intensification_end: string
  duration_hours: number
  n_timesteps: number
  center_lat: number
  center_lon: number
}

export interface CycloneTrack {
  lats: number[]
  lons: number[]
}

export interface CycloneData {
  track_id: string
  ep_label: 'EP1' | 'EP2'
  metadata: CycloneMetadata
  track: CycloneTrack
  timesteps: CycloneTimestep[]
  available_fields: string[]
}

export interface CycloneExplorerManifest {
  metadata: {
    generated_at: string
    total_cyclones: number
    ep1_count: number
    ep2_count: number
  }
  cyclones: Record<string, CycloneData>
}
