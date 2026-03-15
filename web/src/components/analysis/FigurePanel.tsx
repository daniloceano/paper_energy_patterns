'use client'

import { useState } from 'react'
import { Maximize2, X } from 'lucide-react'

interface FigurePanelProps {
  src: string
  alt: string
  caption?: string
  source?: string
  className?: string
}

export default function FigurePanel({
  src,
  alt,
  caption,
  source,
  className = '',
}: FigurePanelProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <figure
        className={`group relative overflow-hidden rounded-xl border border-slate-200 bg-white ${className}`}
      >
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt={alt}
            className="w-full cursor-zoom-in object-contain"
            loading="lazy"
            onClick={() => setIsOpen(true)}
          />
          <button
            onClick={() => setIsOpen(true)}
            className="absolute right-2 top-2 rounded-lg bg-black/50 p-1.5 text-white opacity-0 transition-opacity group-hover:opacity-100"
            aria-label="Enlarge figure"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
        {(caption || source) && (
          <figcaption className="border-t border-slate-100 px-4 py-3">
            {caption && (
              <p className="text-sm leading-relaxed text-slate-600">{caption}</p>
            )}
            {source && (
              <p className="mt-1 text-xs text-slate-400">
                Source: <code className="rounded bg-slate-100 px-1">{source}</code>
              </p>
            )}
          </figcaption>
        )}
      </figure>

      {/* Lightbox modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 p-4"
          onClick={() => setIsOpen(false)}
        >
          <button
            onClick={() => setIsOpen(false)}
            className="absolute right-4 top-4 rounded-lg bg-white/10 p-2 text-white hover:bg-white/20"
            aria-label="Close"
          >
            <X className="h-6 w-6" />
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt={alt}
            className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  )
}
