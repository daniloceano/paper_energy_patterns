import Link from 'next/link'
import { Microscope } from 'lucide-react'

interface MethodsPanelProps {
  /** Short subtitle describing what this analysis' methods cover. */
  summary: string
  children: React.ReactNode
  /** Override the heading if an analysis has no statistical component. */
  title?: string
}

/**
 * The "Methods & Statistics" panel that sits on every analysis page.
 *
 * Methods live next to the results they produced rather than in a separate
 * tab, so a reader never has to navigate away to find out what a test does.
 * Content that is genuinely shared across analyses — the dataset, the seven
 * Lorenz Energy Cycle term definitions, and the bibliography — stays on
 * /data-references, which this panel links to.
 */
export default function MethodsPanel({
  summary,
  children,
  title = 'Methods & Statistics',
}: MethodsPanelProps) {
  return (
    <section className="mb-12 overflow-hidden rounded-2xl border border-indigo-100 bg-indigo-50/30">
      <div className="border-b border-indigo-100 bg-indigo-50/60 px-5 py-4 sm:px-6">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <Microscope className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-lg font-bold text-slate-900">{title}</h2>
            <p className="mt-0.5 text-sm text-slate-600">{summary}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4 px-5 py-5 sm:px-6">{children}</div>

      <div className="border-t border-indigo-100 bg-white/60 px-5 py-3 sm:px-6">
        <p className="text-xs text-slate-500">
          Dataset description, the seven Lorenz Energy Cycle term definitions, and the
          bibliography are shared across all analyses and live in{' '}
          <Link href="/data-references" className="font-medium text-indigo-600 hover:underline">
            Data &amp; References
          </Link>
          .
        </p>
      </div>
    </section>
  )
}
