'use client'

import { useState } from 'react'
import FigurePanel from './FigurePanel'

interface FigureCompareProps {
  leftSrc: string
  rightSrc: string
  leftLabel: string
  rightLabel: string
  leftAlt: string
  rightAlt: string
  caption?: string
}

export default function FigureCompare({
  leftSrc,
  rightSrc,
  leftLabel,
  rightLabel,
  leftAlt,
  rightAlt,
  caption,
}: FigureCompareProps) {
  const [mode, setMode] = useState<'side-by-side' | 'overlay'>('side-by-side')

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          Compare Mode
        </span>
        <div className="flex rounded-lg border border-slate-200">
          <button
            onClick={() => setMode('side-by-side')}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              mode === 'side-by-side'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-600 hover:bg-slate-100'
            } rounded-l-lg`}
          >
            Side by Side
          </button>
          <button
            onClick={() => setMode('overlay')}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              mode === 'overlay'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-600 hover:bg-slate-100'
            } rounded-r-lg`}
          >
            Toggle
          </button>
        </div>
      </div>

      {mode === 'side-by-side' ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <span className="mb-2 inline-block rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-semibold text-red-700">
              {leftLabel}
            </span>
            <FigurePanel src={leftSrc} alt={leftAlt} />
          </div>
          <div>
            <span className="mb-2 inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
              {rightLabel}
            </span>
            <FigurePanel src={rightSrc} alt={rightAlt} />
          </div>
        </div>
      ) : (
        <ToggleView
          leftSrc={leftSrc}
          rightSrc={rightSrc}
          leftLabel={leftLabel}
          rightLabel={rightLabel}
          leftAlt={leftAlt}
          rightAlt={rightAlt}
        />
      )}

      {caption && (
        <p className="text-center text-sm text-slate-500">{caption}</p>
      )}
    </div>
  )
}

function ToggleView({
  leftSrc,
  rightSrc,
  leftLabel,
  rightLabel,
  leftAlt,
  rightAlt,
}: Omit<FigureCompareProps, 'caption'>) {
  const [showLeft, setShowLeft] = useState(true)

  return (
    <div className="space-y-2">
      <div className="flex justify-center gap-2">
        <button
          onClick={() => setShowLeft(true)}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            showLeft
              ? 'bg-red-600 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          {leftLabel}
        </button>
        <button
          onClick={() => setShowLeft(false)}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            !showLeft
              ? 'bg-blue-600 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          {rightLabel}
        </button>
      </div>
      <FigurePanel
        src={showLeft ? leftSrc : rightSrc}
        alt={showLeft ? leftAlt : rightAlt}
      />
    </div>
  )
}
