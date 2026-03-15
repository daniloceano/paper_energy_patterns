interface DiagnosticHeaderProps {
  name: string
  shortName: string
  level: string
  unit: string
  description: string
  hasAnomaly: boolean
}

export default function DiagnosticHeader({
  name,
  shortName,
  level,
  unit,
  description,
  hasAnomaly,
}: DiagnosticHeaderProps) {
  return (
    <div className="mb-8 rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-indigo-50/30 p-8">
      <div className="flex flex-wrap items-start gap-3">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          {name}
        </h1>
        <div className="flex gap-2">
          <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">
            {level}
          </span>
          <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
            {unit}
          </span>
          {hasAnomaly && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
              + Anomaly
            </span>
          )}
        </div>
      </div>
      <p className="mt-4 max-w-3xl text-sm leading-relaxed text-slate-600">
        {description}
      </p>
    </div>
  )
}
