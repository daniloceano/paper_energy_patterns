'use client'

import katex from 'katex'
import 'katex/dist/katex.min.css'

interface FormulaBlockProps {
  formula: string
  terms?: Record<string, string>
  references?: string[]
  notes?: string
  label?: string
}

export default function FormulaBlock({
  formula,
  terms,
  references,
  notes,
  label,
}: FormulaBlockProps) {
  const html = katex.renderToString(formula, {
    throwOnError: false,
    displayMode: true,
  })

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      {label && (
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {label}
          </h4>
        </div>
      )}
      <div className="px-6 py-5">
        <div
          className="flex justify-center overflow-x-auto py-2 text-lg"
          dangerouslySetInnerHTML={{ __html: html }}
        />

        {terms && Object.keys(terms).length > 0 && (
          <div className="mt-4 space-y-1 border-t border-slate-100 pt-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Where
            </p>
            <dl className="space-y-1">
              {Object.entries(terms).map(([symbol, desc]) => (
                <div key={symbol} className="flex gap-2 text-sm">
                  <dt className="shrink-0 font-mono font-semibold text-indigo-600">
                    {symbol}
                  </dt>
                  <dd className="text-slate-600">= {desc}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {notes && (
          <p className="mt-3 border-t border-slate-100 pt-3 text-sm text-slate-500">
            {notes}
          </p>
        )}

        {references && references.length > 0 && (
          <div className="mt-3 border-t border-slate-100 pt-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              References
            </p>
            <ul className="mt-1 space-y-0.5">
              {references.map((ref) => (
                <li key={ref} className="text-sm text-slate-500">
                  {ref}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
