'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

interface MethodologyAccordionProps {
  items: {
    title: string
    content: string
  }[]
}

export default function MethodologyAccordion({ items }: MethodologyAccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div
          key={i}
          className="overflow-hidden rounded-xl border border-slate-200 bg-white"
        >
          <button
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
            className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {item.title}
            <ChevronDown
              className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${
                openIndex === i ? 'rotate-180' : ''
              }`}
            />
          </button>
          {openIndex === i && (
            <div className="border-t border-slate-100 px-4 py-3 text-sm leading-relaxed text-slate-600">
              {item.content}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
