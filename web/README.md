# Energy Patterns Web — Interactive Research Explorer

Interactive Next.js application for exploring the results of the Energy Patterns paper on South Atlantic extratropical cyclones.

## Stack

- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **Database:** Supabase (PostgreSQL)
- **Deploy:** Vercel

## Local Setup

### Prerequisites

- Node.js ≥ 18
- npm ≥ 9

### Install & Run

```bash
cd web
npm install
npm run dev
```

The app runs at [http://localhost:3000](http://localhost:3000).

### Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Required variables:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key |
| `NEXT_PUBLIC_SITE_URL` | Site URL (default: http://localhost:3000) |

> The site works without Supabase—all scientific content is served from static manifests and repository files. Supabase adds metadata persistence for future features.

### Generate Site Data

Before running the site, generate manifests from the repository results:

```bash
# From repo root
python scripts/web/build_site_manifest.py
python scripts/web/extract_cluster_site_data.py
python scripts/web/extract_composite_site_data.py
```

These scripts read from `results/`, `figures/`, `data/`, and `docs/` and output JSON manifests to `web/src/content/`.

## Build

```bash
npm run build
```

## Typecheck

```bash
npm run typecheck
```

## Deploy to Vercel

1. Import the repository on [vercel.com](https://vercel.com)
2. Set the **Root Directory** to `web`
3. Set the **Framework Preset** to `Next.js`
4. Add environment variables from `.env.example`
5. Deploy

### Vercel Settings

| Setting | Value |
|---------|-------|
| Root Directory | `web` |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Install Command | `npm install` |

## Architecture

```
web/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Landing page
│   │   ├── about/             # About page
│   │   ├── analyses/          # Analysis pages
│   │   │   ├── cluster/       # Cluster analysis (5 steps)
│   │   │   └── composites/    # Composite analysis (9 diagnostics)
│   │   ├── api/figures/       # API route to serve repo figures
│   │   ├── docs/              # Documentation page
│   │   ├── methods/           # Data & Methods page
│   │   └── references/        # References page
│   ├── components/
│   │   ├── analysis/          # Scientific components
│   │   └── layout/            # Layout components
│   ├── content/               # Generated JSON manifests
│   └── lib/                   # Types, constants, utilities
├── public/                    # Static assets
├── .env.example               # Environment variable template
├── next.config.js             # Next.js configuration
├── package.json
├── postcss.config.js
└── tsconfig.json
```

## Data Flow

```
Scientific Pipeline (Python)
  └── scripts/ generate → results/, figures/, data/
       └── scripts/web/ extract → web/src/content/*.json
            └── web/ reads manifests + serves figures via API
                 └── PDFs continue to be generated independently
```

## Relationship with Scientific Pipeline

- **This site reads from the existing outputs** — it never modifies scientific data
- **PDFs remain the authoritative written record** — the site complements them
- **Figures are served from the repository** via the `/api/figures` route
- **No scientific logic runs in the web app** — all computation stays in Python

## Supabase

Database schema is in `supabase/migrations/`. To apply:

```bash
# Using Supabase CLI
supabase db push
# Or apply manually
psql $DATABASE_URL < supabase/migrations/20250315_initial_schema.sql
```

The schema stores metadata (diagnostics, figures, domain stats, references, glossary). Currently the site uses static JSON manifests, with Supabase as an optional enhancement.
