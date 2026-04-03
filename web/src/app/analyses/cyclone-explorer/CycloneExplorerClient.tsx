'use client'

import { useState, useMemo } from 'react'
import Image from 'next/image'
import type { CycloneExplorerManifest, CycloneData } from '@/lib/types'
import { ENERGY_PATTERNS } from '@/lib/constants'

// Simplified South Atlantic coastline (lon, lat pairs for SVG rendering)
// Coverage: roughly -80°W to +50°E, -80°S to -10°S
// This is a highly simplified version for visualization purposes
const SOUTH_ATLANTIC_COASTLINE: Array<[number, number][]> = [
  // South America east coast (south to north)
  [
    [-68.3, -54.9], [-66.5, -55.0], [-65.2, -54.6], [-64.0, -53.8], [-63.7, -52.3],
    [-65.3, -51.6], [-68.4, -50.9], [-70.0, -50.7], [-72.0, -51.6], [-73.5, -51.4],
    [-74.5, -52.0], [-73.8, -53.3], [-72.3, -53.5], [-70.5, -53.0], [-69.5, -52.2],
  ],
  // Patagonia / Argentina coast
  [
    [-69.5, -52.2], [-68.5, -50.1], [-66.8, -47.0], [-65.5, -45.0], [-65.0, -43.0],
    [-64.0, -42.0], [-62.2, -38.8], [-58.5, -34.9], [-56.3, -34.9], [-53.5, -33.2],
    [-52.5, -32.0], [-51.8, -30.0], [-49.8, -28.5], [-48.5, -26.5], [-47.0, -24.5],
    [-46.0, -23.8], [-44.0, -23.0], [-43.0, -22.9], [-41.0, -22.0], [-40.0, -21.0],
    [-39.0, -18.0], [-38.5, -13.0], [-35.0, -10.0],
  ],
  // Africa west coast (south to north) - simplified
  [
    [18.4, -34.8], [17.0, -33.0], [15.5, -29.0], [14.0, -26.5], [13.0, -22.5],
    [12.0, -17.0], [11.5, -15.0], [12.5, -13.0], [13.5, -12.5],
  ],
]

interface CycloneExplorerClientProps {
  manifest: CycloneExplorerManifest
}

// Panel types available for each timestep
type PanelType = 'basic' // Currently only basic 2x2 panels are generated

const PANEL_TYPES: { id: PanelType; label: string; description: string }[] = [
  {
    id: 'basic',
    label: 'Basic Fields',
    description: 'SLP + 850 hPa winds, Temperature 850 hPa, Specific Humidity 975 hPa, Geopotential 500 hPa',
  },
]

export default function CycloneExplorerClient({ manifest }: CycloneExplorerClientProps) {
  const [selectedEP, setSelectedEP] = useState<'EP1' | 'EP2'>('EP1')
  const [selectedCycloneId, setSelectedCycloneId] = useState<string | null>(null)
  const [currentTimestepIdx, setCurrentTimestepIdx] = useState(0)
  const [selectedPanelType, setSelectedPanelType] = useState<PanelType>('basic')

  // Filter cyclones by EP - only include those with at least one panel
  const cyclonesByEP = useMemo(() => {
    const ep1: CycloneData[] = []
    const ep2: CycloneData[] = []
    Object.values(manifest.cyclones).forEach((c) => {
      // Only include cyclones that have at least one panel available
      const hasAnyPanel = c.timesteps.some(t => t.has_panel)
      if (!hasAnyPanel) return
      
      if (c.ep_label === 'EP1') ep1.push(c)
      else if (c.ep_label === 'EP2') ep2.push(c)
    })
    return { EP1: ep1, EP2: ep2 }
  }, [manifest])

  const currentCyclones = cyclonesByEP[selectedEP]
  const selectedCyclone = selectedCycloneId ? manifest.cyclones[selectedCycloneId] : null

  // Reset selection when EP changes
  const handleEPChange = (ep: 'EP1' | 'EP2') => {
    setSelectedEP(ep)
    setSelectedCycloneId(null)
    setCurrentTimestepIdx(0)
  }

  const handleCycloneChange = (trackId: string) => {
    setSelectedCycloneId(trackId)
    setCurrentTimestepIdx(0)
  }

  const currentTimestep = selectedCyclone?.timesteps[currentTimestepIdx]
  const panelPath = selectedCyclone && currentTimestep?.has_panel
    ? `/figures/cyclone_explorer/${selectedCyclone.ep_label.toLowerCase()}/${selectedCyclone.track_id}/panel_t${String(currentTimestep.index).padStart(3, '0')}.png`
    : null

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-end gap-4">
          {/* EP Selector */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-500">
              Energy Pattern
            </label>
            <div className="flex gap-2">
              {(['EP1', 'EP2'] as const).map((ep) => (
                <button
                  key={ep}
                  onClick={() => handleEPChange(ep)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    selectedEP === ep
                      ? 'text-white shadow-md'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                  style={{
                    backgroundColor: selectedEP === ep ? ENERGY_PATTERNS[ep].color : undefined,
                  }}
                >
                  {ep} ({cyclonesByEP[ep].length})
                </button>
              ))}
            </div>
          </div>

          {/* Cyclone Selector */}
          <div className="flex-1">
            <label className="mb-1.5 block text-xs font-medium text-slate-500">
              Select Cyclone
            </label>
            <select
              value={selectedCycloneId || ''}
              onChange={(e) => handleCycloneChange(e.target.value)}
              className="w-full max-w-xs rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">-- Choose a cyclone --</option>
              {currentCyclones.map((c) => (
                <option key={c.track_id} value={c.track_id}>
                  {c.track_id} ({c.metadata.n_timesteps} timesteps, {c.metadata.duration_hours}h)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main content */}
      {selectedCyclone ? (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left: Track + Metadata */}
          <div className="space-y-4">
            {/* Metadata card */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-slate-900">
                Cyclone {selectedCyclone.track_id}
              </h3>
              <dl className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <dt className="text-slate-500">Energy Pattern</dt>
                  <dd
                    className="font-medium"
                    style={{ color: ENERGY_PATTERNS[selectedCyclone.ep_label].color }}
                  >
                    {selectedCyclone.ep_label}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Start</dt>
                  <dd className="font-mono text-slate-700">
                    {selectedCyclone.metadata.intensification_start}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">End</dt>
                  <dd className="font-mono text-slate-700">
                    {selectedCyclone.metadata.intensification_end}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Duration</dt>
                  <dd className="text-slate-700">{selectedCyclone.metadata.duration_hours}h</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Timesteps</dt>
                  <dd className="text-slate-700">{selectedCyclone.metadata.n_timesteps}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Center (lat, lon)</dt>
                  <dd className="font-mono text-slate-700">
                    {selectedCyclone.metadata.center_lat.toFixed(2)}°,{' '}
                    {selectedCyclone.metadata.center_lon.toFixed(2)}°
                  </dd>
                </div>
              </dl>
            </div>

            {/* Track visualization */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-slate-900">Track</h3>
              <TrackMap
                track={selectedCyclone.track}
                timesteps={selectedCyclone.timesteps}
                currentTimestepIdx={currentTimestepIdx}
                epColor={ENERGY_PATTERNS[selectedCyclone.ep_label].color}
              />
              <p className="mt-2 text-xs text-slate-500">
                The track shows the full cyclone trajectory. The colored segment highlights the
                intensification phase. The current timestep position is marked with a larger circle.
              </p>
            </div>
          </div>

          {/* Right: Panel + Slider */}
          <div className="lg:col-span-2 space-y-4">
            {/* Panel type selector (for future expansion) */}
            {PANEL_TYPES.length > 1 && (
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <label className="mb-2 block text-xs font-medium text-slate-500">
                  Diagnostic Panel
                </label>
                <div className="flex flex-wrap gap-2">
                  {PANEL_TYPES.map((pt) => (
                    <button
                      key={pt.id}
                      onClick={() => setSelectedPanelType(pt.id)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                        selectedPanelType === pt.id
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                      title={pt.description}
                    >
                      {pt.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Temporal slider */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-500">
                  Timestep {currentTimestepIdx + 1} of {selectedCyclone.timesteps.length}
                </span>
                {currentTimestep && (
                  <span className="text-xs font-mono text-slate-600">
                    {currentTimestep.time}
                  </span>
                )}
              </div>
              <input
                type="range"
                min={0}
                max={selectedCyclone.timesteps.length - 1}
                value={currentTimestepIdx}
                onChange={(e) => setCurrentTimestepIdx(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
              <div className="flex justify-between mt-1 text-xs text-slate-400">
                <span>Start</span>
                <span>End</span>
              </div>
            </div>

            {/* Panel image */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">
                  Atmospheric Fields
                </h3>
                <span className="text-xs text-slate-500">
                  30°×30° domain centered on cyclone
                </span>
              </div>
              {panelPath ? (
                <div className="relative aspect-[10/9] w-full overflow-hidden rounded-lg bg-slate-50">
                  <Image
                    src={panelPath}
                    alt={`Cyclone ${selectedCyclone.track_id} at timestep ${currentTimestepIdx}`}
                    fill
                    className="object-contain"
                    priority
                  />
                </div>
              ) : (
                <div className="flex aspect-[10/9] items-center justify-center rounded-lg bg-slate-100 text-sm text-slate-400">
                  Panel not available for this timestep
                </div>
              )}
              <p className="mt-3 text-xs text-slate-500">
                <strong>Panel fields:</strong> SLP + 850 hPa wind vectors (top-left), 
                Temperature 850 hPa (top-right), Specific humidity 975 hPa (bottom-left), 
                Geopotential 500 hPa (bottom-right). Dashed box shows the 15°×15° LEC domain.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 p-12 text-center">
          <p className="text-slate-500">
            Select an Energy Pattern and cyclone to begin exploring.
          </p>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Track Map Component (SVG-based with coastline)
// ---------------------------------------------------------------------------

interface TrackMapProps {
  track: { lats: number[]; lons: number[] }
  timesteps: { index: number; track_point_index: number; has_panel: boolean }[]
  currentTimestepIdx: number
  epColor: string
}

function TrackMap({ track, timesteps, currentTimestepIdx, epColor }: TrackMapProps) {
  // Compute bounding box with padding
  const minLat = Math.min(...track.lats)
  const maxLat = Math.max(...track.lats)
  const minLon = Math.min(...track.lons)
  const maxLon = Math.max(...track.lons)

  const padding = 5 // degrees padding
  const latRange = maxLat - minLat + 2 * padding
  const lonRange = maxLon - minLon + 2 * padding
  
  // Compute actual bounds for coastline clipping
  const viewMinLon = minLon - padding
  const viewMaxLon = maxLon + padding
  const viewMinLat = minLat - padding
  const viewMaxLat = maxLat + padding

  const width = 280
  const height = 220

  // Map coordinates to SVG
  const toX = (lon: number) => ((lon - viewMinLon) / lonRange) * width
  const toY = (lat: number) => height - ((lat - viewMinLat) / latRange) * height

  // Build track path
  const trackPathD = track.lats
    .map((lat, i) => {
      const x = toX(track.lons[i])
      const y = toY(lat)
      return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
    })
    .join(' ')

  // Current position from timestep
  const currentTs = timesteps[currentTimestepIdx]
  const currentTrackIdx = currentTs?.track_point_index ?? 0
  const currentX = toX(track.lons[currentTrackIdx] ?? track.lons[0])
  const currentY = toY(track.lats[currentTrackIdx] ?? track.lats[0])

  // Intensification points (first and last timestep track indices)
  const firstIntTs = timesteps[0]
  const lastIntTs = timesteps[timesteps.length - 1]

  // Build coastline paths (filter to visible region)
  const coastlinePaths = SOUTH_ATLANTIC_COASTLINE.map((segment) => {
    // Filter points that are roughly within view bounds (with some margin)
    const visiblePoints = segment.filter(
      ([lon, lat]) =>
        lon >= viewMinLon - 10 &&
        lon <= viewMaxLon + 10 &&
        lat >= viewMinLat - 10 &&
        lat <= viewMaxLat + 10
    )
    if (visiblePoints.length < 2) return null
    return visiblePoints
      .map(([lon, lat], i) => {
        const x = toX(lon)
        const y = toY(lat)
        return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
      })
      .join(' ')
  }).filter(Boolean)

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full rounded-lg bg-gradient-to-b from-slate-50 to-slate-100"
      style={{ maxHeight: '220px' }}
    >
      {/* Background ocean color */}
      <rect x={0} y={0} width={width} height={height} fill="#e8f4fc" />

      {/* Grid lines */}
      {[...Array(5)].map((_, i) => {
        const lat = viewMinLat + (i + 1) * (latRange / 6)
        return (
          <line
            key={`lat-${i}`}
            x1={0}
            y1={toY(lat)}
            x2={width}
            y2={toY(lat)}
            stroke="#cad5e0"
            strokeWidth={0.5}
            strokeDasharray="2,2"
          />
        )
      })}
      {[...Array(5)].map((_, i) => {
        const lon = viewMinLon + (i + 1) * (lonRange / 6)
        return (
          <line
            key={`lon-${i}`}
            x1={toX(lon)}
            y1={0}
            x2={toX(lon)}
            y2={height}
            stroke="#cad5e0"
            strokeWidth={0.5}
            strokeDasharray="2,2"
          />
        )
      })}

      {/* Coastline */}
      {coastlinePaths.map((d, i) => (
        <path
          key={`coast-${i}`}
          d={d as string}
          fill="none"
          stroke="#8b9cad"
          strokeWidth={1.2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}

      {/* Full track (light) */}
      <path d={trackPathD} fill="none" stroke="#94a3b8" strokeWidth={1.5} />

      {/* Intensification segment (highlighted) */}
      {firstIntTs && lastIntTs && (
        <path
          d={track.lats
            .slice(firstIntTs.track_point_index, lastIntTs.track_point_index + 1)
            .map((lat, i) => {
              const actualIdx = firstIntTs.track_point_index + i
              const x = toX(track.lons[actualIdx])
              const y = toY(lat)
              return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
            })
            .join(' ')}
          fill="none"
          stroke={epColor}
          strokeWidth={2.5}
          strokeLinecap="round"
        />
      )}

      {/* Start of intensification */}
      {firstIntTs && (
        <circle
          cx={toX(track.lons[firstIntTs.track_point_index])}
          cy={toY(track.lats[firstIntTs.track_point_index])}
          r={4}
          fill="#22c55e"
          stroke="white"
          strokeWidth={1.5}
        />
      )}

      {/* End of intensification */}
      {lastIntTs && (
        <circle
          cx={toX(track.lons[lastIntTs.track_point_index])}
          cy={toY(track.lats[lastIntTs.track_point_index])}
          r={4}
          fill="#ef4444"
          stroke="white"
          strokeWidth={1.5}
        />
      )}

      {/* Current position marker */}
      <circle
        cx={currentX}
        cy={currentY}
        r={7}
        fill={epColor}
        stroke="white"
        strokeWidth={2}
        className="transition-all duration-200"
      />
      <circle
        cx={currentX}
        cy={currentY}
        r={12}
        fill="none"
        stroke={epColor}
        strokeWidth={2}
        opacity={0.4}
        className="transition-all duration-200"
      />

      {/* Legend */}
      <g transform="translate(8, 12)">
        <rect x={-4} y={-8} width={90} height={18} fill="white" fillOpacity={0.85} rx={3} />
        <circle cx={0} cy={0} r={3} fill="#22c55e" />
        <text x={8} y={3} fontSize={8} fill="#64748b">Start</text>
        <circle cx={40} cy={0} r={3} fill="#ef4444" />
        <text x={48} y={3} fontSize={8} fill="#64748b">End</text>
      </g>

      {/* Coordinate labels */}
      <text x={width - 5} y={height - 5} fontSize={7} fill="#94a3b8" textAnchor="end">
        {viewMinLon.toFixed(0)}°W – {viewMaxLon.toFixed(0)}°W
      </text>
    </svg>
  )
}
