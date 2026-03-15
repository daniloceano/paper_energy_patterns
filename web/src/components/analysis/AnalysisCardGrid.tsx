import Link from 'next/link'
import { type LucideIcon } from 'lucide-react'

interface Card {
  title: string
  description: string
  href: string
  icon: LucideIcon
  badge?: string
}

interface AnalysisCardGridProps {
  cards: Card[]
  columns?: 2 | 3 | 4
}

export default function AnalysisCardGrid({ cards, columns = 3 }: AnalysisCardGridProps) {
  const gridClass =
    columns === 2
      ? 'grid-cols-1 sm:grid-cols-2'
      : columns === 4
        ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
        : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'

  return (
    <div className={`grid gap-4 ${gridClass}`}>
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <Link
            key={card.href}
            href={card.href}
            className="group relative rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
          >
            {card.badge && (
              <span className="absolute right-4 top-4 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                {card.badge}
              </span>
            )}
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 transition-colors group-hover:bg-indigo-600 group-hover:text-white">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-900 group-hover:text-indigo-600">
              {card.title}
            </h3>
            <p className="mt-1.5 text-sm leading-relaxed text-slate-500">
              {card.description}
            </p>
          </Link>
        )
      })}
    </div>
  )
}
