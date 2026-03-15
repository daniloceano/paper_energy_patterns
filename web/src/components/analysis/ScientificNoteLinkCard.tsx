import { FileText } from 'lucide-react'
import Link from 'next/link'

interface ScientificNoteLinkCardProps {
  title: string
  description: string
  pdfPath: string
  sourceFile?: string
}

export default function ScientificNoteLinkCard({
  title,
  description,
  pdfPath,
  sourceFile,
}: ScientificNoteLinkCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-rose-100 text-rose-600">
          <FileText className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900">{title}</h3>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <a
              href={`/api/figures?path=${encodeURIComponent(pdfPath)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
            >
              <FileText className="h-3.5 w-3.5" />
              Open PDF
            </a>
          </div>
          {sourceFile && (
            <p className="mt-2 text-xs text-slate-400">
              Generated from: <code className="rounded bg-slate-100 px-1">{sourceFile}</code>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
