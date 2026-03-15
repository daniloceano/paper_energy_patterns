import type { Reference } from '@/lib/types'

interface ReferenceListProps {
  references: Reference[]
  title?: string
}

export default function ReferenceList({ references, title }: ReferenceListProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      {title && (
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h4 className="text-sm font-semibold text-slate-700">{title}</h4>
        </div>
      )}
      <ul className="divide-y divide-slate-100 px-4">
        {references.map((ref) => (
          <li key={ref.id} className="py-3">
            <p className="text-sm text-slate-700">
              <span className="font-medium">{ref.authors}</span> ({ref.year}).{' '}
              <em>{ref.title}</em>. {ref.journal}.
              {ref.doi && (
                <>
                  {' '}
                  <a
                    href={`https://doi.org/${ref.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:underline"
                  >
                    doi:{ref.doi}
                  </a>
                </>
              )}
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}
