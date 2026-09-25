import type { ReactNode } from 'react'
import AnalysisRefreshStatus from '@/components/analysis/AnalysisRefreshStatus'

export default function AnalysesLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <AnalysisRefreshStatus />
      {children}
    </>
  )
}
