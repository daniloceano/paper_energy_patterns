interface Column {
  key: string
  label: string
  align?: 'left' | 'center' | 'right'
  format?: (value: unknown) => string
}

interface StatsTableProps {
  title?: string
  columns: Column[]
  rows: Record<string, unknown>[]
  caption?: string
  highlightColumn?: string
}

export default function StatsTable({
  title,
  columns,
  rows,
  caption,
  highlightColumn,
}: StatsTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      {title && (
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h4 className="text-sm font-semibold text-slate-700">{title}</h4>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 font-semibold text-slate-600 ${
                    col.align === 'right'
                      ? 'text-right'
                      : col.align === 'center'
                        ? 'text-center'
                        : 'text-left'
                  }`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50/50">
                {columns.map((col) => {
                  const value = row[col.key]
                  const formatted = col.format
                    ? col.format(value)
                    : String(value ?? '—')
                  const isHighlighted = highlightColumn === col.key
                  return (
                    <td
                      key={col.key}
                      className={`px-4 py-3 ${
                        col.align === 'right'
                          ? 'text-right'
                          : col.align === 'center'
                            ? 'text-center'
                            : 'text-left'
                      } ${
                        isHighlighted
                          ? 'font-semibold text-indigo-700'
                          : 'text-slate-700'
                      }`}
                    >
                      {formatted}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {caption && (
        <div className="border-t border-slate-100 px-4 py-2">
          <p className="text-xs text-slate-400">{caption}</p>
        </div>
      )}
    </div>
  )
}
