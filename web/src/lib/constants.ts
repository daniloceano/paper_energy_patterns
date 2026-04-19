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
      'Assess the baroclinic instability environment surrounding EP1, EP2, EP3, and EPALL cyclones during intensification, and identify how the instability signal differs across patterns.',
    formula:
      '\\sigma_{EGR} = 0.31 \\frac{|f|}{N} \\left|\\frac{\\partial \\vec{V}}{\\partial z}\\right|',
    formulaTerms: {
      f: 'Coriolis parameter (s⁻¹)',
      N: 'Brunt-Väisälä frequency (s⁻¹)',
      '∂V/∂z': 'Vertical wind shear between 500 and 850 hPa',
    },
    references: ['Eady (1949)', 'Lindzen and Farrell (1980)'],
    hasAnomaly: true,
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
      'Characterise upper-level tropopause dynamics and stratospheric intrusion signatures for EP1, EP2, EP3, and EPALL.',
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
      'Identify low-level diabatic PV generation and frontal signatures for EP1, EP2, EP3, and EPALL.',
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
      'Map the warm/cold advection structure and its role in baroclinic energy conversion for EP1, EP2, EP3, and EPALL.',
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
      'Evaluate the moisture convergence patterns and their connection to diabatic generation (Ge) for EP1, EP2, EP3, and EPALL.',
    formula:
      '\\nabla \\cdot (q\\vec{V}) = \\frac{\\partial (qu)}{\\partial x} + \\frac{\\partial (qv)}{\\partial y}',
    formulaTerms: {
      q: 'Specific humidity (kg kg⁻¹)',
      V: 'Horizontal wind vector (m s⁻¹)',
      u: 'Zonal wind component (m s⁻¹)',
      v: 'Meridional wind component (m s⁻¹)',
    },
    references: ['Trenberth and Guillemot (1995)'],
    hasAnomaly: false,
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
      'Compare cyclone intensity and spatial structure across EP1, EP2, EP3, and EPALL.',
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
      'The Rayleigh-Kuo criterion identifies regions where the meridional gradient of absolute vorticity changes sign — a necessary condition for barotropic instability. Negative values indicate instability regions. Shown as total composite only (no EPALL-relative anomaly): RK = β − ∂²ū/∂y² depends on the large-scale flow and is used as a diagnostic of the background environment, not a field expected to be differenced across energy patterns.',
    physicalObjective:
      'Locate barotropic instability regions in the upper troposphere across EP1, EP2, EP3, and EPALL and relate to barotropic conversion (Ck). Only the total composite is shown — no anomaly or EPALL-relative difference is presented for RK.',
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
      'Evaluate upper-level kinetic energy redistribution and jet-stream interaction for EP1, EP2, EP3, and EPALL.',
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
      'Quantify upper-level ageostrophic forcing and its role as eddy KE source/sink for EP1, EP2, EP3, and EPALL.',
    formula:
      'AFC = -\\nabla \\cdot (\\vec{v}_{ag}\' \\, \\phi\')',
    formulaTerms: {
      "v_ag'": 'Ageostrophic eddy wind (m s⁻¹)',
      "φ'": 'Eddy geopotential (m² s⁻²)',
    },
    references: ['Orlanski and Katzfey (1991)', 'Chang (1993)'],
    hasAnomaly: true,
  },
  btcr: {
    id: 'btcr',
    slug: 'btcr',
    name: 'Barotropic Critical Region at 250 hPa',
    shortName: 'BtCR 250',
    level: '250 hPa',
    unit: '×10⁻⁹ s⁻²',
    description:
      'Effective deformation Δₘ = σₘ² − ζₘ² of the climatological background flow at 250 hPa. Positive values identify jet-exit zones where deformation dominates rotation — the Barotropic Critical Region (BtCR) — where synoptic disturbances are forced into orientations that enable efficient energy extraction or loss.',
    physicalObjective:
      'Identify whether EP1, EP2, and EP3 cyclones develop preferentially in BtCR environments (Δₘ > 0) that can amplify or suppress their growth via barotropic processes.',
    formula:
      '\\Delta_m = \\sigma_m^2 - \\zeta_m^2, \\quad \\sigma_m = \\sqrt{St^2 + Sh^2}',
    formulaTerms: {
      'Δₘ': 'Effective deformation (s⁻²); positive = deformation dominates',
      'σₘ': 'Total deformation magnitude (s⁻¹)',
      'ζₘ': 'Background relative vorticity (s⁻¹)',
      St: 'Stretching deformation (s⁻¹)',
      Sh: 'Shearing deformation (s⁻¹)',
    },
    references: ['Rivière (2006)'],
    hasAnomaly: false,
  },
  // --- Geopotential Height ---
  'z-250': {
    id: 'z-250',
    slug: 'z-250',
    name: 'Geopotential Height at 250 hPa',
    shortName: 'HGT 250',
    level: '250 hPa',
    unit: 'gpm',
    description:
      'Geopotential height at 250 hPa characterises the large-scale upper-tropospheric wave pattern. Troughs and ridges at this level directly modulate upper-level divergence, which drives surface cyclone intensification through the quasi-geostrophic omega equation.',
    physicalObjective:
      'Compare the upper-tropospheric geopotential height pattern for EP1, EP2, EP3, and EPALL during intensification, and quantify departures from the climatological mean and from the full cyclone population (EPALL).',
    formula: 'Z = \\frac{\\Phi}{g_0}',
    formulaTerms: {
      'Φ': 'Geopotential (m² s⁻²)',
      'g₀': 'Standard gravity (9.80665 m s⁻²)',
    },
    references: ['ERA5 documentation', 'Holton and Hakim (2013)'],
    hasAnomaly: true,
  },
  'z-500': {
    id: 'z-500',
    slug: 'z-500',
    name: 'Geopotential Height at 500 hPa',
    shortName: 'HGT 500',
    level: '500 hPa',
    unit: 'gpm',
    description:
      'Geopotential height at 500 hPa represents mid-tropospheric synoptic forcing. This level is traditionally used to identify atmospheric wave amplitude, trough depth, and the overall intensity of baroclinic systems. Deep 500 hPa troughs are closely associated with strong surface cyclones.',
    physicalObjective:
      'Evaluate mid-tropospheric wave amplitude and trough depth for EP1, EP2, EP3, and EPALL during intensification, highlighting differences in the baroclinic wave structure across energy patterns.',
    formula: 'Z = \\frac{\\Phi}{g_0}',
    formulaTerms: {
      'Φ': 'Geopotential (m² s⁻²)',
      'g₀': 'Standard gravity (9.80665 m s⁻²)',
    },
    references: ['ERA5 documentation', 'Holton and Hakim (2013)'],
    hasAnomaly: true,
  },
  'z-850': {
    id: 'z-850',
    slug: 'z-850',
    name: 'Geopotential Height at 850 hPa',
    shortName: 'HGT 850',
    level: '850 hPa',
    unit: 'gpm',
    description:
      'Geopotential height at 850 hPa reflects low-tropospheric thickness and thermal structure. Anomalies at this level indicate warm-core or cold-core characteristics, and the trough axis position relative to the surface cyclone centre provides information on cyclone vertical tilt.',
    physicalObjective:
      'Characterise low-tropospheric geopotential structure and vertical tilt for EP1, EP2, EP3, and EPALL during intensification. Anomaly fields reveal the warm/cold-core contribution to geopotential.',
    formula: 'Z = \\frac{\\Phi}{g_0}',
    formulaTerms: {
      'Φ': 'Geopotential (m² s⁻²)',
      'g₀': 'Standard gravity (9.80665 m s⁻²)',
    },
    references: ['ERA5 documentation', 'Holton and Hakim (2013)'],
    hasAnomaly: true,
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
      'Scientific interpretation of ERA5 composite analysis of EP1, EP2, EP3, and EPALL cyclone atmospheric structure and EPALL-relative anomalies.',
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
  {
    id: 'brennan-vincent-1980',
    authors: 'Brennan, F. E. and Vincent, D. G.',
    year: 1980,
    title: 'Zonal and eddy components of the synoptic-scale energy budget during intensification of Hurricane Carmen (1974)',
    journal: 'Mon. Weather Rev. 108(7):954–965',
    doi: '10.1175/1520-0493(1980)108<0954:ZAECOT>2.0.CO;2',
  },
  {
    id: 'michaelides-1987',
    authors: 'Michaelides, S. C.',
    year: 1987,
    title: 'Limited area energetics of Genoa cyclogenesis',
    journal: 'Mon. Weather Rev. 115(1):13–26',
    doi: '10.1175/1520-0493(1987)115<0013:LAEOGC>2.0.CO;2',
  },
  {
    id: 'michaelides-1999',
    authors: 'Michaelides, S. C., Prezerakos, N. G., and Flocas, H. A.',
    year: 1999,
    title: 'Quasi-Lagrangian energetics of an intense Mediterranean cyclone',
    journal: 'Q. J. R. Meteorol. Soc. 125(553):139–168',
    doi: '10.1002/qj.49712555307',
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
// anom_clim  = climatology-relative anomaly  (X' = X − X̄_clim, 1991–2020 ERA5)
// anom_epall = EPALL-relative anomaly         (EPx − EPALL composite)
export const DIAGNOSTIC_FIGURE_SLUGS: Record<DiagnosticId, { real: string; anom_clim?: string; anom_epall?: string; diff?: string }> = {
  egr:                        { real: 'composite_egr.png',            anom_clim: 'composite_egr_anom.png',                 anom_epall: 'composite_egr_anom_epall.png',          diff: 'composite_egr_diff.png' },
  'pv-200':                   { real: 'composite_pv200.png',        anom_clim: 'composite_pv200_anom.png',               anom_epall: 'composite_pv200_anom_epall.png',        diff: 'composite_pv200_diff.png' },
  'pv-850':                   { real: 'composite_pv850.png',        anom_clim: 'composite_pv850_anom.png',               anom_epall: 'composite_pv850_anom_epall.png',        diff: 'composite_pv850_diff.png' },
  'temperature-advection':    { real: 'composite_advT850.png',      anom_clim: 'composite_advT850_anom.png',             anom_epall: 'composite_advT850_anom_epall.png',      diff: 'composite_advT850_diff.png' },
  'moisture-flux-divergence': { real: 'composite_moisture_flux.png',anom_clim: 'composite_moisture_flux_anom.png',                                                            diff: 'composite_moisture_flux_diff.png' },
  slp:                        { real: 'composite_slp.png',          anom_clim: 'composite_slp_anom.png',                 anom_epall: 'composite_slp_anom_epall.png',          diff: 'composite_slp_diff.png' },
  'rk-criterion':             { real: 'composite_rk_criterion.png',                                                                                                            diff: 'composite_rk_criterion_diff.png' },
  'ke-advection':             { real: 'composite_ke_advection.png', anom_clim: 'composite_ke_advection_anom.png',        anom_epall: 'composite_ke_advection_anom_epall.png', diff: 'composite_ke_advection_diff.png' },
  afc:                        { real: 'composite_afc_250.png',                                                               anom_epall: 'composite_afc_anom_epall.png',          diff: 'composite_afc_diff.png' },
  btcr:                       { real: 'composite_btcr.png',                                                                                                                    diff: 'composite_btcr_diff.png' },
  // Geopotential Height — total + climatology anomaly + EPALL-relative anomaly at all three levels
  'z-250':                    { real: 'composite_z250hpa.png',      anom_clim: 'composite_z250hpa_anom.png',             anom_epall: 'composite_z250hpa_anom_epall.png' },
  'z-500':                    { real: 'composite_z500hpa.png',      anom_clim: 'composite_z500hpa_anom.png',             anom_epall: 'composite_z500hpa_anom_epall.png' },
  'z-850':                    { real: 'composite_z850hpa.png',      anom_clim: 'composite_z850hpa_anom.png',             anom_epall: 'composite_z850hpa_anom_epall.png' },
}

// --- Flux/Advection diagnostics that need boundary tables ---
export const FLUX_DIAGNOSTICS: DiagnosticId[] = [
  'temperature-advection',
  'moisture-flux-divergence',
  'ke-advection',
  'afc',
]

// --- LEC Field Dependence ---

export const LFD_DYNAMIC_FIELDS: Record<string, { label: string; level: string }> = {
  pv_850: { label: 'PV 850', level: '850 hPa' },
  pv_200: { label: 'PV 200', level: '200 hPa' },
  adv_T_850: { label: 'AdvT 850', level: '850 hPa' },
  afc_250: { label: 'AFC 250', level: '250 hPa' },
  ke_adv_250: { label: 'KE adv 250', level: '250 hPa' },
}

export const LFD_SPATIAL_FEATURES: Record<string, string> = {
  domain_mean: 'Domain mean',
  centre_value: 'Centre value',
  border_north: 'Border N',
  border_south: 'Border S',
  border_east: 'Border E',
  border_west: 'Border W',
  contrast_ew: 'E-W contrast',
  contrast_sn: 'S-N contrast',
  quadrant_ne: 'Quadrant NE',
  quadrant_nw: 'Quadrant NW',
  quadrant_se: 'Quadrant SE',
  quadrant_sw: 'Quadrant SW',
  domain_abs_mean: 'Domain |mean|',
}

export const LFD_CANONICAL_TERMS = ['Ca', 'Ck', 'Ge', 'BAe', 'BKe', 'Ae', 'Ke'] as const

export const LFD_EP_CONTRASTS = ['EP1 vs EP2', 'EP1 vs EP3', 'EP2 vs EP3'] as const

export const LFD_EP_COLORS: Record<number, string> = {
  1: '#e63946',
  2: '#457b9d',
  3: '#a8dadc',
}
