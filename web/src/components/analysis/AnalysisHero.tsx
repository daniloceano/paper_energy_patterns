import { type ReactNode } from 'react'

interface AnalysisHeroProps {
  title: string
  subtitle?: string
  description: string
  badge?: string
  children?: ReactNode
}

export default function AnalysisHero({
  title,
  subtitle,
  description,
  badge,
  children,
}: AnalysisHeroProps) {
  return (
    <div className="mb-10 rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-indigo-50/30 p-8 sm:p-10">
      {badge && (
        <span className="mb-3 inline-block rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-indigo-700">
          {badge}
        </span>
      )}
      <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
        {title}
      </h1>
      {subtitle && (
        <p className="mt-2 text-lg font-medium text-indigo-600">{subtitle}</p>
      )}
      <p className="mt-4 max-w-3xl text-base leading-relaxed text-slate-600">
        {description}
      </p>
      {children && <div className="mt-6">{children}</div>}
    </div>
  )
}
