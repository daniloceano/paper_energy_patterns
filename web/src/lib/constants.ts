// Site-wide constants and scientific data

import type {
  EnergyPattern,
  EnergyTermInfo,
  EnergyTerm,
  Diagnostic,
  DiagnosticId,
  AnalysisStep,
  DocumentInfo,
  Reference,
} from './types'

// --- Site metadata ---
export const SITE_TITLE = 'Energy Patterns of South Atlantic Cyclones'
export const SITE_DESCRIPTION =
  'Interactive exploration of energetic patterns of extratropical cyclones in the Southwestern Atlantic, based on Lorenz Energy Cycle diagnostics and ERA5 reanalysis composites.'

// --- Energy Patterns ---
export const ENERGY_PATTERNS: Record<string, EnergyPattern> = {
  EP1: {
    id: 'EP1',
    label: 'EP1 — Strong Conversions / Energy Exporters',
    count: 444,
    percentage: 11.6,
    meanCk: -16.48,
    description:
      'Most energetically active cyclones. Strong barotropic and baroclinic conversions. Tend to export energy (negative boundary fluxes). Genesis concentrated at the Brazil-Malvinas Confluence and SE-Brazil shelf.',
    color: '#e63946',
  },
  EP2: {
    id: 'EP2',
    label: 'EP2 — Intermediate Conversions / Energy Importers',
    count: 979,
    percentage: 25.6,
    meanCk: -3.49,
    description:
      'Moderately energetic cyclones coupled to jet stream dynamics. Tend to import energy (positive boundary fluxes), drawing energy from the large-scale flow. Genesis mainly in the La Plata region.',
    color: '#457b9d',
  },
  EP3: {
    id: 'EP3',
    label: 'EP3 — Weak Energetics',
    count: 2397,
    percentage: 62.7,
    meanCk: -1.71,
    description:
      'Typical transient cyclones representing the climatological background. Minimal energy conversions and weak intensity.',
    color: '#a8dadc',
  },
}

// --- Energy Term Metadata ---
export const ENERGY_TERM_INFO: Record<EnergyTerm, EnergyTermInfo> = {
  Ca: {
    symbol: 'C_a',
    name: 'Baroclinic Conversion',
    description:
      'Conversion from zonal APE to eddy APE via temperature gradients. Ca > 0 indicates baroclinic energy extraction.',
    unit: 'W m⁻²',
    formula:
      'C_a = \\int_{p_b}^{p_t} \\frac{R}{p\\sigma} \\left[ (\\omega)_\\lambda (T)_\\lambda \\frac{\\partial \\langle T \\rangle_\\lambda}{\\partial \\phi} \\right] dp',
  },
  Ck: {
    symbol: 'C_k',
    name: 'Barotropic Conversion',
    description:
      'Conversion from zonal KE to eddy KE via horizontal wind shear. Ck < 0 indicates barotropic energy extraction from the mean flow.',
    unit: 'W m⁻²',
    formula:
      'C_k = \\int_{p_b}^{p_t} \\left[ (u)_\\lambda (v)_\\lambda \\frac{\\partial \\langle u \\rangle_\\lambda}{\\partial y} \\right] dp',
  },
  Ge: {
    symbol: 'G_e',
    name: 'Eddy APE Generation',
    description:
      'Diabatic heating creating eddy available potential energy, primarily through latent heat release in convective processes.',
    unit: 'W m⁻²',
  },
  BAe: {
    symbol: '\\partial A_e',
    name: 'Eddy APE Boundary Flux',
    description:
      'Transport of eddy available potential energy across domain boundaries. Positive values indicate energy import.',
    unit: 'W m⁻²',
  },
  BKe: {
    symbol: '\\partial K_e',
    name: 'Eddy KE Boundary Flux',
    description:
      'Transport of eddy kinetic energy across domain boundaries. Positive values indicate energy import.',
    unit: 'W m⁻²',
  },
  Ae: {
    symbol: 'A_e',
    name: 'Eddy APE Reservoir',
    description:
      'Available potential energy associated with eddy temperature perturbations.',
    unit: 'J m⁻²',
  },
  Ke: {
    symbol: 'K_e',
    name: 'Eddy KE Reservoir',
    description:
      'Kinetic energy associated with eddy wind perturbations.',
    unit: 'J m⁻²',
  },
}

// --- Diagnostics ---
export const DIAGNOSTICS: Record<DiagnosticId, Diagnostic> = {
  egr: {
    id: 'egr',
    slug: 'egr',
    name: 'Eady Growth Rate',
    shortName: 'EGR',
    level: '500–850 hPa',
    unit: 'day⁻¹',
    description:
      'The Eady Growth Rate quantifies baroclinic instability by relating vertical wind shear to static stability. Higher EGR values indicate environments more favourable for cyclone intensification through baroclinic processes.',
    physicalObjective:
      'Assess the baroclinic instability environment surrounding EP1 and EP2 cyclones during intensification.',
    formula:
      '\\sigma_{EGR} = 0.31 \\frac{|f|}{N} \\left|\\frac{\\partial \\vec{V}}{\\partial z}\\right|',
    formulaTerms: {
      f: 'Coriolis parameter (s⁻¹)',
      N: 'Brunt-Väisälä frequency (s⁻¹)',
      '∂V/∂z': 'Vertical wind shear between 500 and 850 hPa',
    },
    references: ['Eady (1949)', 'Lindzen and Farrell (1980)'],
    hasAnomaly: false,
  },
  'pv-200': {
    id: 'pv-200',
    slug: 'pv-200',
    name: 'Potential Vorticity at 200 hPa',
    shortName: 'PV 200',
    level: '200 hPa',
    unit: 'PVU',
    description:
      'Upper-level PV identifies tropopause dynamics and stratospheric intrusions. The 2 PVU surface defines the dynamical tropopause, and PV anomalies at this level reveal upper-level forcing mechanisms for surface cyclogenesis.',
    physicalObjective:
      'Characterise upper-level tropopause dynamics and stratospheric intrusion signatures for EP1 vs EP2.',
    formula:
      'PV = -g \\left(\\zeta_\\theta + f\\right) \\frac{\\partial \\theta}{\\partial p}',
    formulaTerms: {
      g: 'Gravitational acceleration (m s⁻²)',
      ζ_θ: 'Relative vorticity on isentropic surfaces (s⁻¹)',
      f: 'Coriolis parameter (s⁻¹)',
      '∂θ/∂p': 'Vertical gradient of potential temperature (K Pa⁻¹)',
    },
    references: ['Hoskins et al. (1985)', 'Ertel (1942)'],
    hasAnomaly: true,
  },
  'pv-850': {
    id: 'pv-850',
    slug: 'pv-850',
    name: 'Potential Vorticity at 850 hPa',
    shortName: 'PV 850',
    level: '850 hPa',
    unit: 'PVU',
    description:
      'Low-level PV identifies diabatic PV generation, surface friction, and frontal structures. Concentrated PV anomalies at low levels are signatures of latent heat release and boundary layer processes.',
    physicalObjective:
      'Identify low-level diabatic PV generation and frontal signatures for EP1 vs EP2.',
    formula:
      'PV = -g \\left(\\zeta_\\theta + f\\right) \\frac{\\partial \\theta}{\\partial p}',
    formulaTerms: {
      g: 'Gravitational acceleration (m s⁻²)',
      ζ_θ: 'Relative vorticity on isentropic surfaces (s⁻¹)',
      f: 'Coriolis parameter (s⁻¹)',
      '∂θ/∂p': 'Vertical gradient of potential temperature (K Pa⁻¹)',
    },
    references: ['Hoskins et al. (1985)'],
    hasAnomaly: true,
  },
  'temperature-advection': {
    id: 'temperature-advection',
    slug: 'temperature-advection',
    name: 'Temperature Advection at 850 hPa',
    shortName: 'Temp Adv 850',
    level: '850 hPa',
    unit: 'K h⁻¹',
    description:
      'Temperature advection at 850 hPa identifies warm and cold sectors around cyclones. Warm advection ahead of the warm front drives baroclinic conversion, while cold advection behind the cold front shapes the cyclone lifecycle.',
    physicalObjective:
      'Map the warm/cold advection structure and its role in baroclinic energy conversion for EP1 vs EP2.',
    formula:
      '\\text{advT} = -\\vec{V} \\cdot \\nabla T = -\\left(u\\frac{\\partial T}{\\partial x} + v\\frac{\\partial T}{\\partial y}\\right)',
    formulaTerms: {
      V: 'Horizontal wind vector (m s⁻¹)',
      T: 'Temperature (K)',
      u: 'Zonal wind component (m s⁻¹)',
      v: 'Meridional wind component (m s⁻¹)',
    },
    references: ['Holton and Hakim (2013)'],
    hasAnomaly: true,
  },
  'moisture-flux-divergence': {
    id: 'moisture-flux-divergence',
    slug: 'moisture-flux-divergence',
    name: 'Moisture Flux Divergence at 975 hPa',
    shortName: 'MFD 975',
    level: '975 hPa',
    unit: 'g kg⁻¹ s⁻¹',
    description:
      'Moisture flux divergence at the surface identifies regions of moisture convergence (negative values) where latent heat release fuels cyclone intensification, and divergence where drying occurs.',
    physicalObjective:
      'Evaluate the moisture convergence patterns and their connection to diabatic generation (Ge) for EP1 vs EP2.',
    formula:
      '\\nabla \\cdot (q\\vec{V}) = \\frac{\\partial (qu)}{\\partial x} + \\frac{\\partial (qv)}{\\partial y}',
    formulaTerms: {
      q: 'Specific humidity (kg kg⁻¹)',
      V: 'Horizontal wind vector (m s⁻¹)',
      u: 'Zonal wind component (m s⁻¹)',
      v: 'Meridional wind component (m s⁻¹)',
    },
    references: ['Trenberth and Guillemot (1995)'],
    hasAnomaly: true,
  },
  slp: {
    id: 'slp',
    slug: 'slp',
    name: 'Sea Level Pressure',
    shortName: 'SLP',
    level: 'Surface',
    unit: 'hPa',
    description:
      'Sea level pressure composites show the cyclone structure, intensity, and spatial extent. The minimum SLP indicates the cyclone centre, and the pressure gradient reveals the intensity of the circulation.',
    physicalObjective:
      'Compare cyclone intensity and spatial structure between EP1 and EP2.',
    formula: 'SLP = p_s \\exp\\left(\\frac{g z_s}{R T_v}\\right)',
    formulaTerms: {
      p_s: 'Surface pressure (Pa)',
      g: 'Gravitational acceleration (m s⁻²)',
      z_s: 'Surface elevation (m)',
      R: 'Gas constant for dry air (J kg⁻¹ K⁻¹)',
      T_v: 'Virtual temperature (K)',
    },
    references: ['ERA5 documentation'],
    hasAnomaly: true,
  },
  'rk-criterion': {
    id: 'rk-criterion',
    slug: 'rk-criterion',
    name: 'Rayleigh-Kuo Criterion at 250 hPa',
    shortName: 'RK 250',
    level: '250 hPa',
    unit: 's⁻¹',
    description:
      'The Rayleigh-Kuo criterion identifies regions where the meridional gradient of absolute vorticity changes sign — a necessary condition for barotropic instability. Negative values indicate instability regions.',
    physicalObjective:
      'Locate barotropic instability regions in the upper troposphere for EP1 vs EP2 and relate to barotropic conversion (Ck).',
    formula:
      'RK = \\beta - \\frac{\\partial^2 u}{\\partial y^2}',
    formulaTerms: {
      β: 'Meridional gradient of planetary vorticity (s⁻¹ m⁻¹)',
      u: 'Zonal wind (m s⁻¹)',
      '∂²u/∂y²': 'Second derivative of zonal wind in meridional direction',
    },
    references: ['Rayleigh (1880)', 'Kuo (1949)'],
    hasAnomaly: false,
  },
  'ke-advection': {
    id: 'ke-advection',
    slug: 'ke-advection',
    name: 'Kinetic Energy Advection at 250 hPa',
    shortName: 'KE Adv 250',
    level: '250 hPa',
    unit: 'm² s⁻³',
    description:
      'Kinetic energy advection at the upper troposphere indicates local acceleration (positive) or deceleration (negative) of the flow. This diagnostic reveals the kinetic energy redistribution by the jet stream.',
    physicalObjective:
      'Evaluate upper-level kinetic energy redistribution and jet-stream interaction for EP1 vs EP2.',
    formula:
      '\\text{KE}_{\\text{adv}} = -\\vec{V} \\cdot \\nabla\\left(\\frac{1}{2}(u^2 + v^2)\\right)',
    formulaTerms: {
      V: 'Horizontal wind vector (m s⁻¹)',
      u: 'Zonal wind component (m s⁻¹)',
      v: 'Meridional wind component (m s⁻¹)',
      KE: 'Kinetic energy per unit mass (m² s⁻²)',
    },
    references: ['Orlanski and Katzfey (1991)'],
    hasAnomaly: true,
  },
  afc: {
    id: 'afc',
    slug: 'afc',
    name: 'Ageostrophic Flux Convergence at 250 hPa',
    shortName: 'AFC 250',
    level: '250 hPa',
    unit: 'm² s⁻³',
    description:
      'The ageostrophic flux convergence represents the work done by ageostrophic eddy winds on the eddy geopotential field. Positive values indicate eddy kinetic energy sources; negative values indicate sinks.',
    physicalObjective:
      'Quantify upper-level ageostrophic forcing and its role as eddy KE source/sink for EP1 vs EP2.',
    formula:
      'AFC = -\\nabla \\cdot (\\vec{v}_{ag}\' \\, \\phi\')',
    formulaTerms: {
      "v_ag'": 'Ageostrophic eddy wind (m s⁻¹)',
      "φ'": 'Eddy geopotential (m² s⁻²)',
    },
    references: ['Orlanski and Katzfey (1991)', 'Chang (1993)'],
    hasAnomaly: false,
  },
}

export const DIAGNOSTIC_LIST = Object.values(DIAGNOSTICS)

// --- Cluster Analysis Steps ---
export const CLUSTER_STEPS: AnalysisStep[] = [
  {
    number: 1,
    slug: 'step-1-case-selection-preprocessing-features',
    title: 'Case Selection, Pre-processing & Features',
    shortTitle: 'Selection & Features',
    description:
      'Filter cyclones with complete lifecycle phases, standardise 7 energy terms, and prepare features for dimensionality reduction.',
    inputs: [
      'data/tracks_SAt_filtered_with_energetics_processed.csv',
      'data/energy_cache.parquet',
    ],
    outputs: [
      'results/cluster/pca_full_data.csv',
      'results/cluster/pca_full_data_{phase}.csv',
    ],
    scripts: ['scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py'],
    figures: [],
  },
  {
    number: 2,
    slug: 'step-2-pca',
    title: 'Principal Component Analysis',
    shortTitle: 'PCA',
    description:
      'Independent PCA per lifecycle phase, retaining ≥97% variance. Typically 6 PCs per phase capture the essential variance of the 7 energy terms.',
    inputs: ['results/cluster/pca_full_data_{phase}.csv'],
    outputs: [
      'results/cluster/pca_scores_{phase}.csv',
      'results/cluster/pca_loadings_{phase}.csv',
      'results/cluster/pca_explained_variance_{phase}.csv',
      'results/cluster/pca_models.pkl',
    ],
    scripts: [
      'scripts/cluster_analysis_energy_patterns/step1_normalize_and_pca.py',
      'scripts/cluster_analysis_energy_patterns/step2_plot_pca_results.py',
    ],
    figures: [
      'figures/cluster/pca_variance_wide.png',
      'figures/cluster/pca_loadings_wide.png',
      'figures/cluster/pca_correlation_wide.png',
      'figures/cluster/pca_scatter_wide.png',
    ],
  },
  {
    number: 3,
    slug: 'step-3-optimal-k',
    title: 'Optimal Number of Clusters',
    shortTitle: 'Optimal k',
    description:
      'Five cluster validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz, Score Function, Gap Statistic) are computed for k = 3–15 and averaged after normalisation. The ensemble consensus identifies k = 3 as optimal.',
    inputs: ['results/cluster/pca_scores_{phase}.csv'],
    outputs: [
      'results/cluster/optimal_k.txt',
      'results/cluster/optimal_k_raw_indices.csv',
      'results/cluster/optimal_k_normalized_indices.csv',
    ],
    scripts: [
      'scripts/cluster_analysis_energy_patterns/step3_optimal_k_analysis.py',
    ],
    figures: ['figures/cluster/optimal_k_analysis.png'],
  },
  {
    number: 4,
    slug: 'step-4-clustering-lps',
    title: 'Clustering & Lorenz Phase Space',
    shortTitle: 'Clustering & LPS',
    description:
      'K-Means (k=3, n_init=100) applied per lifecycle phase. Clusters are labelled as EP1, EP2, EP3 based on energy conversion magnitudes. Lorenz Phase Space diagrams visualise the distinct energetic signatures.',
    inputs: [
      'results/cluster/pca_scores_{phase}.csv',
      'results/cluster/optimal_k.txt',
    ],
    outputs: [
      'results/cluster/kmeans_clustered_data_{phase}.csv',
      'results/cluster/kmeans_centroids_pc_{phase}.csv',
      'results/cluster/kmeans_centroids_energy_{phase}.csv',
      'results/cluster/kmeans_summary_{phase}.csv',
      'results/cluster/kmeans_model.pkl',
    ],
    scripts: [
      'scripts/cluster_analysis_energy_patterns/step4_apply_kmeans.py',
      'scripts/cluster_analysis_energy_patterns/step5_plot_energy_patterns.py',
    ],
    figures: [
      'figures/cluster/lps_conversion_default.png',
      'figures/cluster/lps_conversion_zoom.png',
      'figures/cluster/lps_imports_default.png',
      'figures/cluster/lps_imports_zoom.png',
    ],
  },
  {
    number: 5,
    slug: 'step-5-results',
    title: 'Results & Summary',
    shortTitle: 'Results',
    description:
      'Summary of identified Energy Patterns with their physical characteristics, geographical distribution, seasonality, and intensity metrics. This section will be expanded in a future iteration with additional exploratory analyses.',
    inputs: [
      'results/cluster/kmeans_summary.csv',
      'results/cluster/kmeans_centroids_energy.csv',
    ],
    outputs: [],
    scripts: [],
    figures: [
      'figures/main/4_lps_combined.png',
      'figures/main/5_ep_intensity_seasonality_trends.png',
      'figures/main/6_ep_genesis_density_kde.png',
    ],
  },
]

// --- Documents ---
export const DOCUMENTS: DocumentInfo[] = [
  {
    id: 'scientific-notes-cluster',
    title: 'Scientific Notes — Cluster Analysis',
    description:
      'Comprehensive methodology, theoretical background, and results for the PCA + K-Means energy pattern classification.',
    type: 'pdf',
    path: 'docs/scientific_notes_cluster_analysis.pdf',
    generatedFrom:
      'scripts/cluster_analysis_energy_patterns/SCIENTIFIC_NOTES.md',
  },
  {
    id: 'scientific-notes-ep-structure',
    title: 'Scientific Notes — EP Structure Analysis',
    description:
      'Scientific interpretation of ERA5 composite analysis comparing the atmospheric structure of EP1 and EP2 cyclones.',
    type: 'pdf',
    path: 'docs/scientific_notes_ep_structure.pdf',
    generatedFrom: 'scripts/ep_structure_analysis/SCIENTIFIC_NOTES.md',
  },
  {
    id: 'user-guide',
    title: 'User Guide — Repository READMEs',
    description:
      'Auto-generated consolidated user guide compiled from all repository README files.',
    type: 'pdf',
    path: 'docs/user_guide_repository_readmes.pdf',
    generatedFrom: 'scripts/documentation/compile_docs.py',
  },
]

// --- Key References ---
export const KEY_REFERENCES: Reference[] = [
  {
    id: 'lorenz-1955',
    authors: 'Lorenz, E. N.',
    year: 1955,
    title: 'Available potential energy and the maintenance of the general circulation',
    journal: 'Tellus',
    doi: '10.3402/tellusa.v7i2.8796',
  },
  {
    id: 'eady-1949',
    authors: 'Eady, E. T.',
    year: 1949,
    title: 'Long waves and cyclone waves',
    journal: 'Tellus',
    doi: '10.3402/tellusa.v1i3.8507',
  },
  {
    id: 'hoskins-1985',
    authors: 'Hoskins, B. J., McIntyre, M. E., and Robertson, A. W.',
    year: 1985,
    title: 'On the use and significance of isentropic potential vorticity maps',
    journal: 'Q. J. R. Meteorol. Soc.',
    doi: '10.1002/qj.49711147002',
  },
  {
    id: 'orlanski-1991',
    authors: 'Orlanski, I. and Katzfey, J.',
    year: 1991,
    title: 'The life cycle of a cyclone wave in the Southern Hemisphere',
    journal: 'J. Atmos. Sci.',
    doi: '10.1175/1520-0469(1991)048<1972:TLCOAC>2.0.CO;2',
  },
  {
    id: 'holton-2013',
    authors: 'Holton, J. R. and Hakim, G. J.',
    year: 2013,
    title: 'An Introduction to Dynamic Meteorology',
    journal: 'Academic Press, 5th edition',
  },
  {
    id: 'rayleigh-1880',
    authors: 'Rayleigh, Lord',
    year: 1880,
    title: 'On the stability, or instability, of certain fluid motions',
    journal: 'Proc. London Math. Soc.',
  },
  {
    id: 'kuo-1949',
    authors: 'Kuo, H. L.',
    year: 1949,
    title: 'Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere',
    journal: 'J. Meteor.',
  },
  {
    id: 'chang-1993',
    authors: 'Chang, E. K. M.',
    year: 1993,
    title: 'Downstream development of baroclinic waves as inferred from regression analysis',
    journal: 'J. Atmos. Sci.',
    doi: '10.1175/1520-0469(1993)050<2038:DDOBWA>2.0.CO;2',
  },
]

// --- Dataset Statistics ---
export const DATASET_STATS = {
  totalCyclones: 6789,
  filteredCyclones: 3820,
  filterPercentage: 56.3,
  period: '1979–2020',
  years: 42,
  phaseRecords: 15280,
  energyTerms: 7,
  lifecyclePhases: 4,
  era5Resolution: '0.25°',
  domainSize: '30° × 30°',
  innerDomainSize: '15° × 15°',
  climatologyPeriod: '1991–2020',
}

// Mapping from diagnostic id to step4_create_figures.py output filename (in figures/ep_structure/)
export const DIAGNOSTIC_FIGURE_SLUGS: Record<DiagnosticId, { real: string; anom?: string }> = {
  egr:                     { real: 'composite_egr.png' },
  'pv-200':                { real: 'composite_pv200.png',         anom: 'composite_pv200_anom.png' },
  'pv-850':                { real: 'composite_pv850.png',         anom: 'composite_pv850_anom.png' },
  'temperature-advection': { real: 'composite_advT850.png',       anom: 'composite_advT850_anom.png' },
  'moisture-flux-divergence': { real: 'composite_moisture_flux.png', anom: 'composite_moisture_flux_anom.png' },
  slp:                     { real: 'composite_slp.png',           anom: 'composite_slp_anom.png' },
  'rk-criterion':          { real: 'composite_rk_criterion.png' },
  'ke-advection':          { real: 'composite_ke_advection.png',  anom: 'composite_ke_advection_anom.png' },
  afc:                     { real: 'composite_afc_250.png' },
}

// --- Flux/Advection diagnostics that need boundary tables ---
export const FLUX_DIAGNOSTICS: DiagnosticId[] = [
  'temperature-advection',
  'moisture-flux-divergence',
  'ke-advection',
  'afc',
]
