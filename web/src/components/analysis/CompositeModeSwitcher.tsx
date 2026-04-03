'use client'

import { useState, createContext, useContext } from 'react'

export type CompositeMode = 'full_intensification' | 'central_time'

interface CompositeModeContextType {
  mode: CompositeMode
  setMode: (mode: CompositeMode) => void
}

const CompositeModeContext = createContext<CompositeModeContextType | null>(null)

export function useCompositeMode() {
  const context = useContext(CompositeModeContext)
  if (!context) {
    throw new Error('useCompositeMode must be used within a CompositeModeProvider')
  }
  return context
}

interface CompositeModeProviderProps {
  children: React.ReactNode
  defaultMode?: CompositeMode
}

export function CompositeModeProvider({ children, defaultMode = 'full_intensification' }: CompositeModeProviderProps) {
  const [mode, setMode] = useState<CompositeMode>(defaultMode)
  return (
    <CompositeModeContext.Provider value={{ mode, setMode }}>
      {children}
    </CompositeModeContext.Provider>
  )
}

const MODE_INFO: Record<CompositeMode, { label: string; shortLabel: string; description: string }> = {
  full_intensification: {
    label: 'Full Intensification',
    shortLabel: 'Full Phase',
    description: 'Mean over all 6-hourly timesteps during the intensification phase',
  },
  central_time: {
    label: 'Central Time',
    shortLabel: 'Central',
    description: 'Single timestep at the temporal midpoint of the intensification phase',
  },
}

interface CompositeModeSwitcherProps {
  className?: string
}

export default function CompositeModeSwitcher({ className = '' }: CompositeModeSwitcherProps) {
  const { mode, setMode } = useCompositeMode()

  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Composite Method</h3>
        <span className="text-xs text-slate-400">Select temporal averaging</span>
      </div>
      
      <div className="flex gap-2">
        {(Object.keys(MODE_INFO) as CompositeMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
              mode === m
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {MODE_INFO[m].shortLabel}
          </button>
        ))}
      </div>
      
      <p className="mt-3 text-xs text-slate-500">
        <strong>{MODE_INFO[mode].label}:</strong> {MODE_INFO[mode].description}
      </p>
    </div>
  )
}

// Re-export for convenience
export { MODE_INFO }
