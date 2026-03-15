'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface SidebarItem {
  label: string
  href: string
}

interface AnalysisSidebarProps {
  items: SidebarItem[]
  title?: string
}

export default function AnalysisSidebar({ items, title }: AnalysisSidebarProps) {
  const pathname = usePathname()

  return (
    <aside className="hidden w-64 shrink-0 lg:block">
      <nav className="sticky top-24 space-y-1">
        {title && (
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </h3>
        )}
        {items.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-50 font-medium text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
