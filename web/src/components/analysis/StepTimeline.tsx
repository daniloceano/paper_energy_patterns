import Link from 'next/link'
import { CheckCircle, Circle, ArrowRight } from 'lucide-react'

interface Step {
  number: number
  title: string
  shortTitle: string
  href: string
  completed?: boolean
}

interface StepTimelineProps {
  steps: Step[]
  currentStep?: number
}

export default function StepTimeline({ steps, currentStep }: StepTimelineProps) {
  return (
    <div className="space-y-1">
      {steps.map((step, index) => {
        const isCurrent = currentStep === step.number
        const isCompleted = step.completed ?? (currentStep ? step.number < currentStep : false)
        return (
          <Link
            key={step.number}
            href={step.href}
            className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
              isCurrent
                ? 'bg-indigo-50 font-medium text-indigo-700'
                : isCompleted
                  ? 'text-slate-500 hover:bg-slate-50'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <span
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                isCurrent
                  ? 'bg-indigo-600 text-white'
                  : isCompleted
                    ? 'bg-emerald-100 text-emerald-600'
                    : 'bg-slate-200 text-slate-500'
              }`}
            >
              {isCompleted ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                step.number
              )}
            </span>
            <span className="flex-1">{step.shortTitle}</span>
            {isCurrent && <ArrowRight className="h-4 w-4" />}
          </Link>
        )
      })}
    </div>
  )
}
