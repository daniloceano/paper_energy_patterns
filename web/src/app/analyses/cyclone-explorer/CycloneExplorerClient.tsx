'use client'

import { useState, useMemo } from 'react'
import Image from 'next/image'
import type { CycloneExplorerManifest, CycloneData } from '@/lib/types'
import { ENERGY_PATTERNS } from '@/lib/constants'

interface CycloneExplorerClientProps {
  manifest: CycloneExplorerManifest
}

export default function CycloneExplorerClient({ manifest }: CycloneExplorerClientProps) {
  const [selectedEP, setSelectedEP] = useState<'EP1' | 'EP2'>('EP1')
  const [selectedCycloneId, setSelectedCycloneId] = useState<string | null>(null)
  const [currentTimestepIdx, setCurrentTimestepIdx] = useState(0)

  // Filter cyclones by EP
  const cyclonesByEP = useMemo(() => {
    const ep1: CycloneData[] = []
    const ep2: CycloneData[] = []
    Object.values(manifest.cyclones).forEach((c) => {
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
            </div>
          </div>

          {/* Right: Panel + Slider */}
          <div className="lg:col-span-2 space-y-4">
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
// Track Map Component (SVG-based)
// ---------------------------------------------------------------------------

interface TrackMapProps {
  track: { lats: number[]; lons: number[] }
  timesteps: { index: number; track_point_index: number; has_panel: boolean }[]
  currentTimestepIdx: number
  epColor: string
}

function TrackMap({ track, timesteps, currentTimestepIdx, epColor }: TrackMapProps) {
  // Compute bounding box
  const minLat = Math.min(...track.lats)
  const maxLat = Math.max(...track.lats)
  const minLon = Math.min(...track.lons)
  const maxLon = Math.max(...track.lons)

  const padding = 2 // degrees padding
  const latRange = maxLat - minLat + 2 * padding
  const lonRange = maxLon - minLon + 2 * padding

  const width = 280
  const height = 200

  // Map coordinates to SVG
  const toX = (lon: number) => ((lon - (minLon - padding)) / lonRange) * width
  const toY = (lat: number) => height - ((lat - (minLat - padding)) / latRange) * height

  // Build path
  const pathD = track.lats
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

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full rounded-lg bg-slate-50"
      style={{ maxHeight: '200px' }}
    >
      {/* Grid lines */}
      {[...Array(5)].map((_, i) => {
        const lat = minLat - padding + (i + 1) * (latRange / 6)
        return (
          <line
            key={`lat-${i}`}
            x1={0}
            y1={toY(lat)}
            x2={width}
            y2={toY(lat)}
            stroke="#e2e8f0"
            strokeWidth={0.5}
          />
        )
      })}
      {[...Array(5)].map((_, i) => {
        const lon = minLon - padding + (i + 1) * (lonRange / 6)
        return (
          <line
            key={`lon-${i}`}
            x1={toX(lon)}
            y1={0}
            x2={toX(lon)}
            y2={height}
            stroke="#e2e8f0"
            strokeWidth={0.5}
          />
        )
      })}

      {/* Full track (light) */}
      <path d={pathD} fill="none" stroke="#cbd5e1" strokeWidth={1.5} />

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
        <circle cx={0} cy={0} r={3} fill="#22c55e" />
        <text x={8} y={3} fontSize={8} fill="#64748b">Start</text>
        <circle cx={40} cy={0} r={3} fill="#ef4444" />
        <text x={48} y={3} fontSize={8} fill="#64748b">End</text>
      </g>
    </svg>
  )
}
