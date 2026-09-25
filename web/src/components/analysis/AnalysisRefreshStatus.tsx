'use client'

import { CheckCircle2, Clock3, RefreshCw } from 'lucide-react'
import { usePathname } from 'next/navigation'

const REFRESHED_ANALYSES = ['/analyses/cluster']

export default function AnalysisRefreshStatus() {
  const pathname = usePathname()
  const isOverview = pathname === '/analyses'
  const isRefreshed = REFRESHED_ANALYSES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  )

  const Icon = isOverview ? RefreshCw : isRefreshed ? CheckCircle2 : Clock3
  const classes = isOverview
    ? 'border-indigo-200 bg-indigo-50 text-indigo-900'
    : isRefreshed
      ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
      : 'border-amber-200 bg-amber-50 text-amber-950'

  return (
    <div className="mx-auto max-w-5xl px-4 pt-6 sm:px-6 lg:px-8">
      <div className={`flex gap-3 rounded-xl border px-4 py-3 text-sm ${classes}`}>
        <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <p>
          {isOverview
            ? 'Corrected LEC refresh in progress: analyses are being recomputed and reviewed one at a time.'
            : isRefreshed
              ? 'Updated from the complete corrected LEC rerun and ready for scientific review.'
              : 'Pending corrected rerun: this page still represents the previous Energy Pattern classification and should not yet be compared with the updated cluster results.'}
        </p>
      </div>
    </div>
  )
}
