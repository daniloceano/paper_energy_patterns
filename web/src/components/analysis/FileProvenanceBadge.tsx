import { FileCode2 } from 'lucide-react'

interface FileProvenanceBadgeProps {
  files: string[]
  label?: string
}

export default function FileProvenanceBadge({
  files,
  label = 'Source files',
}: FileProvenanceBadgeProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <div className="flex items-center gap-2">
        <FileCode2 className="h-4 w-4 text-slate-400" />
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </span>
      </div>
      <ul className="mt-2 space-y-1">
        {files.map((file) => (
          <li key={file}>
            <code className="text-xs text-slate-600">{file}</code>
          </li>
        ))}
      </ul>
    </div>
  )
}
