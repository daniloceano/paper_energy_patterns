import type { Metadata } from 'next'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import AnalysisHero from '@/components/analysis/AnalysisHero'
import ScientificNoteLinkCard from '@/components/analysis/ScientificNoteLinkCard'
import { DOCUMENTS } from '@/lib/constants'

export const metadata: Metadata = {
  title: 'Documentation',
  description: 'Scientific notes, PDFs, and repository documentation.',
}

export default function DocsPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs />
      <AnalysisHero
        title="Documentation"
        badge="Scientific Notes & Guides"
        description="All documentation produced by the project, including scientific notes for each analysis pipeline and the consolidated repository user guide. PDFs are auto-generated from Markdown sources and represent the authoritative written record of methodology and results."
      />

      <div className="space-y-8">
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Scientific Notes
          </h2>
          <div className="space-y-4">
            {DOCUMENTS.filter((d) => d.id.startsWith('scientific')).map((doc) => (
              <ScientificNoteLinkCard
                key={doc.id}
                title={doc.title}
                description={doc.description}
                pdfPath={doc.path}
                sourceFile={doc.generatedFrom}
              />
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            User Guide
          </h2>
          <div className="space-y-4">
            {DOCUMENTS.filter((d) => d.id === 'user-guide').map((doc) => (
              <ScientificNoteLinkCard
                key={doc.id}
                title={doc.title}
                description={doc.description}
                pdfPath={doc.path}
                sourceFile={doc.generatedFrom}
              />
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Documentation vs Web Visualisation
          </h2>
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm leading-relaxed text-slate-600">
            <p>
              The project maintains two complementary documentation layers:
            </p>
            <ul className="mt-3 space-y-2">
              <li>
                <strong>PDFs (source of truth for written methodology):</strong> Generated from
                Markdown files in each analysis subdirectory. These contain the complete scientific
                narrative, equations, and detailed results.
              </li>
              <li>
                <strong>Web site (interactive exploration):</strong> This site reads data,
                figures, and metadata from the repository to present results in a navigable,
                visual format. It does not replace the PDFs but complements them with
                interactivity.
              </li>
            </ul>
            <p className="mt-3">
              <strong>Data flow:</strong> (1) Scientific scripts generate results → (2)
              Auxiliary scripts serialise data for the site → (3) Site consumes data/figures →
              (4) PDFs continue to be generated independently.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
