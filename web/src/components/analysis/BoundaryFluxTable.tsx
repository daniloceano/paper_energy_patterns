interface BoundaryFluxTableProps {
  title?: string
  data: {
    label: string
    north: number | string
    south: number | string
    east: number | string
    west: number | string
    unit?: string
  }[]
  caption?: string
  unit?: string
}

/**
 * Table for displaying flux values at each boundary of the 15°×15° domain.
 *
 * Domain definition:
 * - "Inside 15×15": The central 15°×15° subdomain centred on the cyclone.
 * - "Outside 15×15": The ring between the full 30°×30° domain and the inner 15°×15°.
 * - Boundaries (North, South, East, West): The four edges of the 15°×15° inner domain.
 *
 * For flux/advection diagnostics, each boundary value represents the average
 * of the diagnostic field along that boundary edge.
 */
export default function BoundaryFluxTable({
  title,
  data,
  caption,
  unit,
}: BoundaryFluxTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      {title && (
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h4 className="text-sm font-semibold text-slate-700">
            {title}
            {unit && (
              <span className="ml-2 text-xs font-normal text-slate-400">
                [{unit}]
              </span>
            )}
          </h4>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/50">
              <th className="px-4 py-3 text-left font-semibold text-slate-600">
                Pattern
              </th>
              <th className="px-4 py-3 text-right font-semibold text-slate-600">
                North
              </th>
              <th className="px-4 py-3 text-right font-semibold text-slate-600">
                South
              </th>
              <th className="px-4 py-3 text-right font-semibold text-slate-600">
                East
              </th>
              <th className="px-4 py-3 text-right font-semibold text-slate-600">
                West
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50/50">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {row.label}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {typeof row.north === 'number' ? row.north.toFixed(4) : row.north}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {typeof row.south === 'number' ? row.south.toFixed(4) : row.south}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {typeof row.east === 'number' ? row.east.toFixed(4) : row.east}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {typeof row.west === 'number' ? row.west.toFixed(4) : row.west}
                </td>
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
