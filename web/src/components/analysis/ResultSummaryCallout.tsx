import { Lightbulb, AlertTriangle, Info } from 'lucide-react'

interface ResultSummaryCalloutProps {
  type?: 'info' | 'result' | 'warning'
  title?: string
  children: React.ReactNode
}

const STYLES = {
  info: {
    bg: 'bg-blue-50 border-blue-200',
    icon: Info,
    iconColor: 'text-blue-600',
    titleColor: 'text-blue-800',
  },
  result: {
    bg: 'bg-emerald-50 border-emerald-200',
    icon: Lightbulb,
    iconColor: 'text-emerald-600',
    titleColor: 'text-emerald-800',
  },
  warning: {
    bg: 'bg-amber-50 border-amber-200',
    icon: AlertTriangle,
    iconColor: 'text-amber-600',
    titleColor: 'text-amber-800',
  },
}

export default function ResultSummaryCallout({
  type = 'result',
  title,
  children,
}: ResultSummaryCalloutProps) {
  const style = STYLES[type]
  const Icon = style.icon

  return (
    <div className={`rounded-xl border ${style.bg} p-5`}>
      <div className="flex gap-3">
        <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${style.iconColor}`} />
        <div>
          {title && (
            <h4 className={`font-semibold ${style.titleColor}`}>{title}</h4>
          )}
          <div className="mt-1 text-sm leading-relaxed text-slate-700">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
