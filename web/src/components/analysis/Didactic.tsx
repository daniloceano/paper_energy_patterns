/**
 * Didactic primitives shared by the per-analysis "Methods & Statistics" panels.
 *
 * The intent is a consistent reading rhythm across every analysis page:
 *
 *     prose  →  equation (FormulaBlock)  →  symbol definitions  →
 *     SimpleTerms (intuition)  →  InThisStudy (meteorological example)
 *
 * All three are plain server components (no hooks), so they can be rendered
 * directly inside the static analysis pages.
 */

/** Intuitive restatement of a technical point — the "what is this number telling me?" layer. */
export function SimpleTerms({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-3 rounded-lg border-l-4 border-indigo-300 bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
        In simple terms
      </p>
      <div className="mt-1 text-sm leading-relaxed text-slate-600">{children}</div>
    </div>
  )
}

/** Concrete application to this study's cyclones, EPs, LEC terms, or dynamical fields. */
export function InThisStudy({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-3 rounded-lg border-l-4 border-emerald-300 bg-emerald-50/50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
        In this study
      </p>
      <div className="mt-1 text-sm leading-relaxed text-slate-600">{children}</div>
    </div>
  )
}

/** Compact left-to-right pipeline of statistical steps. */
export function TestFlow({ steps }: { steps: string[] }) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2">
      {steps.map((s, i) => (
        <span key={s} className="flex items-center gap-2">
          <span className="rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 ring-1 ring-indigo-100">
            {s}
          </span>
          {i < steps.length - 1 && (
            <span aria-hidden="true" className="text-slate-300">→</span>
          )}
        </span>
      ))}
    </div>
  )
}
