-- Migration: Initial schema for Energy Patterns web application
-- Supabase / PostgreSQL
-- This schema stores metadata for the interactive site, not raw scientific data.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ANALYSES
-- ============================================================
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    short_title TEXT,
    description TEXT,
    badge TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO analyses (slug, title, short_title, description, badge, sort_order) VALUES
('cluster', 'Cluster Analysis — Energy Patterns', 'Cluster Analysis', 'PCA-based K-Means clustering of Lorenz Energy Cycle diagnostics to classify cyclones into three Energy Patterns.', 'Classification', 1),
('composites', 'Composite Analysis — EP Structure', 'EP Structure', 'Storm-centred ERA5 composite analysis comparing EP1 vs EP2 atmospheric structure during intensification.', 'EP1 vs EP2', 2);

-- ============================================================
-- ANALYSIS STEPS (for cluster analysis)
-- ============================================================
CREATE TABLE analysis_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    short_title TEXT,
    description TEXT,
    inputs TEXT[],
    outputs TEXT[],
    scripts TEXT[],
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (analysis_id, step_number)
);

-- ============================================================
-- DIAGNOSTICS (for composite analysis)
-- ============================================================
CREATE TABLE diagnostics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    level TEXT NOT NULL,
    unit TEXT NOT NULL,
    description TEXT,
    physical_objective TEXT,
    has_anomaly BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO diagnostics (slug, name, short_name, level, unit, description, physical_objective, has_anomaly, sort_order) VALUES
('egr', 'Eady Growth Rate', 'EGR', '500–850 hPa', 'day⁻¹', 'Baroclinic instability measure relating vertical wind shear to static stability.', 'Assess baroclinic instability environment for EP1 vs EP2.', FALSE, 1),
('pv-200', 'Potential Vorticity at 200 hPa', 'PV 200', '200 hPa', 'PVU', 'Upper-level PV for tropopause dynamics and stratospheric intrusions.', 'Characterise upper-level forcing for EP1 vs EP2.', TRUE, 2),
('pv-850', 'Potential Vorticity at 850 hPa', 'PV 850', '850 hPa', 'PVU', 'Low-level PV for diabatic generation and frontal structures.', 'Identify low-level diabatic PV generation for EP1 vs EP2.', TRUE, 3),
('temperature-advection', 'Temperature Advection at 850 hPa', 'Temp Adv 850', '850 hPa', 'K h⁻¹', 'Temperature advection for warm/cold sectors.', 'Map warm/cold advection structure for EP1 vs EP2.', TRUE, 4),
('moisture-flux-divergence', 'Moisture Flux Divergence at 975 hPa', 'MFD 975', '975 hPa', 'g kg⁻¹ s⁻¹', 'Surface moisture convergence/divergence.', 'Evaluate moisture convergence patterns for EP1 vs EP2.', TRUE, 5),
('slp', 'Sea Level Pressure', 'SLP', 'Surface', 'hPa', 'Cyclone intensity and horizontal structure.', 'Compare cyclone intensity and spatial structure.', TRUE, 6),
('rk-criterion', 'Rayleigh-Kuo Criterion at 250 hPa', 'RK 250', '250 hPa', 's⁻¹', 'Necessary condition for barotropic instability.', 'Locate upper-level barotropic instability regions.', FALSE, 7),
('ke-advection', 'Kinetic Energy Advection at 250 hPa', 'KE Adv 250', '250 hPa', 'm² s⁻³', 'Upper-level KE redistribution by jet stream.', 'Evaluate KE redistribution and jet interaction.', TRUE, 8),
('afc', 'Ageostrophic Flux Convergence at 250 hPa', 'AFC 250', '250 hPa', 'm² s⁻³', 'Work done by ageostrophic eddy winds on geopotential.', 'Quantify ageostrophic forcing as eddy KE source/sink.', FALSE, 9);

-- ============================================================
-- FORMULAS
-- ============================================================
CREATE TABLE formulas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnostic_id UUID REFERENCES diagnostics(id) ON DELETE CASCADE,
    latex TEXT NOT NULL,
    terms JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- REFERENCES
-- ============================================================
CREATE TABLE "references" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cite_key TEXT UNIQUE NOT NULL,
    authors TEXT NOT NULL,
    year INTEGER NOT NULL,
    title TEXT NOT NULL,
    journal TEXT NOT NULL,
    doi TEXT,
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- FIGURES
-- ============================================================
CREATE TABLE figures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    title TEXT,
    caption TEXT,
    alt_text TEXT,
    source_script TEXT,
    analysis_step_id UUID REFERENCES analysis_steps(id) ON DELETE SET NULL,
    diagnostic_id UUID REFERENCES diagnostics(id) ON DELETE SET NULL,
    energy_pattern TEXT CHECK (energy_pattern IN ('EP1', 'EP2', 'EP3')),
    figure_type TEXT CHECK (figure_type IN ('real', 'anomaly', 'combined', 'validation', 'publication')),
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- FIGURE GROUPS
-- ============================================================
CREATE TABLE figure_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE figure_group_items (
    figure_group_id UUID REFERENCES figure_groups(id) ON DELETE CASCADE,
    figure_id UUID REFERENCES figures(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    PRIMARY KEY (figure_group_id, figure_id)
);

-- ============================================================
-- DOMAIN STATISTICS (inside/outside 15x15)
-- ============================================================
CREATE TABLE domain_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnostic_id UUID REFERENCES diagnostics(id) ON DELETE CASCADE,
    energy_pattern TEXT NOT NULL CHECK (energy_pattern IN ('EP1', 'EP2')),
    inside_mean DOUBLE PRECISION,
    outside_mean DOUBLE PRECISION,
    inside_std DOUBLE PRECISION,
    outside_std DOUBLE PRECISION,
    unit TEXT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (diagnostic_id, energy_pattern, is_anomaly)
);

COMMENT ON TABLE domain_statistics IS 'Mean values inside/outside the 15°×15° inner domain. "Inside" = central 15°×15° subdomain centred on cyclone. "Outside" = annular ring between 30°×30° and 15°×15°.';

-- ============================================================
-- BOUNDARY FLUX TABLES (N/S/E/W of 15x15 domain)
-- ============================================================
CREATE TABLE boundary_flux_tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnostic_id UUID REFERENCES diagnostics(id) ON DELETE CASCADE,
    energy_pattern TEXT NOT NULL CHECK (energy_pattern IN ('EP1', 'EP2')),
    north DOUBLE PRECISION,
    south DOUBLE PRECISION,
    east DOUBLE PRECISION,
    west DOUBLE PRECISION,
    unit TEXT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (diagnostic_id, energy_pattern, is_anomaly)
);

COMMENT ON TABLE boundary_flux_tables IS 'Mean flux along each boundary of the 15°×15° inner domain. For flux/advection diagnostics only.';

-- ============================================================
-- SUMMARY TABLES
-- ============================================================
CREATE TABLE summary_tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context TEXT NOT NULL,
    title TEXT NOT NULL,
    columns JSONB NOT NULL,
    rows JSONB NOT NULL,
    caption TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- DOCUMENTS
-- ============================================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    doc_type TEXT CHECK (doc_type IN ('pdf', 'markdown', 'notebook')),
    relative_path TEXT NOT NULL,
    generated_from TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- GLOSSARY
-- ============================================================
CREATE TABLE glossary_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term TEXT UNIQUE NOT NULL,
    abbreviation TEXT,
    definition TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO glossary_terms (term, abbreviation, definition, category) VALUES
('Lorenz Energy Cycle', 'LEC', 'Framework for partitioning atmospheric energy into zonal-mean and eddy components, with conversion, generation, and boundary flux terms.', 'Theory'),
('Energy Pattern', 'EP', 'Classification of cyclones by their energetic signature across lifecycle phases, identified via PCA + K-Means clustering.', 'Classification'),
('Eady Growth Rate', 'EGR', 'Measure of baroclinic instability: σ = 0.31 (|f|/N) |∂V/∂z|.', 'Diagnostic'),
('Potential Vorticity', 'PV', 'Conserved quantity combining vorticity and static stability. 1 PVU = 10⁻⁶ K m² kg⁻¹ s⁻¹.', 'Diagnostic'),
('Ageostrophic Flux Convergence', 'AFC', 'Work done by ageostrophic eddy winds on the eddy geopotential field.', 'Diagnostic'),
('Rayleigh-Kuo Criterion', 'RK', 'Necessary condition for barotropic instability: β − ∂²u/∂y² changes sign.', 'Diagnostic'),
('Principal Component Analysis', 'PCA', 'Dimensionality reduction technique that finds orthogonal axes of maximum variance.', 'Statistics');

-- ============================================================
-- ROW-LEVEL SECURITY (basic, permissive for reads)
-- ============================================================
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostics ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulas ENABLE ROW LEVEL SECURITY;
ALTER TABLE "references" ENABLE ROW LEVEL SECURITY;
ALTER TABLE figures ENABLE ROW LEVEL SECURITY;
ALTER TABLE figure_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE figure_group_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE domain_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE boundary_flux_tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE summary_tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE glossary_terms ENABLE ROW LEVEL SECURITY;

-- Allow public read access for the site
CREATE POLICY "Allow public read" ON analyses FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON analysis_steps FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON diagnostics FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON formulas FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON "references" FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON figures FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON figure_groups FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON figure_group_items FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON domain_statistics FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON boundary_flux_tables FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON summary_tables FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON documents FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON glossary_terms FOR SELECT USING (true);
