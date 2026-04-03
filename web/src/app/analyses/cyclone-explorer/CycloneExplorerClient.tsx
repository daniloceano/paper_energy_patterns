'use client'

import { useMemo, useState } from 'react'
import Image from 'next/image'
import type { CycloneExplorerManifest, CycloneData } from '@/lib/types'
import { ENERGY_PATTERNS } from '@/lib/constants'
import { figureUrl } from '@/lib/client-utils'

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
  featuredCases: FeaturedCase[]
}

type FieldCategory = 'synoptic' | 'dynamic'

interface FeaturedCase {
  trackId: string
  title: string
  subtitle: string
}

const DEFAULT_SYNOPTIC_PRODUCTS = [
  {
    id: 'basic',
    label: 'Synoptic fields',
    description: 'SLP, temperature, specific humidity and geopotential in a cyclone-centered panel.',
  },
]

export default function CycloneExplorerClient({ manifest, featuredCases }: CycloneExplorerClientProps) {
  const [selectedEP, setSelectedEP] = useState<'EP1' | 'EP2'>('EP1')
  const [selectedCycloneId, setSelectedCycloneId] = useState<string | null>(null)
  const [currentTimestepIdx, setCurrentTimestepIdx] = useState(0)
  const [selectedCategory, setSelectedCategory] = useState<FieldCategory>('synoptic')

  const synopticProducts = manifest.metadata.synoptic_products ?? DEFAULT_SYNOPTIC_PRODUCTS
  const dynamicProducts = manifest.metadata.dynamic_products ?? []
  const [selectedDynamicProduct, setSelectedDynamicProduct] = useState<string>(
    dynamicProducts[0]?.id ?? 'slp_pv850_wind850'
  )

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

  const handleFeaturedCaseSelect = (trackId: string) => {
    const cyclone = manifest.cyclones[trackId]
    if (!cyclone) return

    setSelectedEP(cyclone.ep_label)
    setSelectedCycloneId(trackId)
    setCurrentTimestepIdx(0)
    setSelectedCategory('synoptic')
  }

  const currentTimestep = selectedCyclone?.timesteps[currentTimestepIdx]

  const selectedProductMeta =
    selectedCategory === 'synoptic'
      ? synopticProducts[0]
      : dynamicProducts.find((p) => p.id === selectedDynamicProduct) ?? dynamicProducts[0]

  const panelPath = useMemo(() => {
    if (!selectedCyclone || !currentTimestep) return null
    if (selectedCategory === 'synoptic') {
      const synPath = currentTimestep.images?.synoptic?.basic ?? currentTimestep.panel_image
      return synPath ? figureUrl(synPath) : null
    }

    const dynPath = currentTimestep.images?.dynamic?.[selectedDynamicProduct] ?? null
    return dynPath ? figureUrl(dynPath) : null
  }, [selectedCategory, selectedCyclone, currentTimestep, selectedDynamicProduct])

  const hasAnyDynamic = useMemo(() => {
    if (!selectedCyclone) return false
    return selectedCyclone.timesteps.some((ts) => {
      if (!ts.images?.dynamic) return false
      return Object.values(ts.images.dynamic).some((v) => Boolean(v))
    })
  }, [selectedCyclone])

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

        {featuredCases.length > 0 && (
          <div className="mt-5 border-t border-slate-200 pt-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Featured cases
                </p>
                <p className="text-xs text-slate-500">
                  Quick access to representative cyclones already present in the EP1/EP2 data.
                </p>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {featuredCases.map((item) => {
                const cyclone = manifest.cyclones[item.trackId]
                const active = selectedCycloneId === item.trackId
                return (
                  <button
                    key={item.trackId}
                    type="button"
                    onClick={() => handleFeaturedCaseSelect(item.trackId)}
                    className={`rounded-xl border p-3 text-left transition-all ${
                      active
                        ? 'border-slate-800 bg-slate-900 text-white shadow-md'
                        : 'border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold">
                          {item.title}
                        </div>
                        <div className={`mt-0.5 text-xs ${active ? 'text-slate-200' : 'text-slate-500'}`}>
                          {item.subtitle}
                        </div>
                      </div>
                      <span
                        className="rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wider"
                        style={{
                          backgroundColor: cyclone ? `${ENERGY_PATTERNS[cyclone.ep_label].color}20` : undefined,
                          color: cyclone ? ENERGY_PATTERNS[cyclone.ep_label].color : undefined,
                        }}
                      >
                        {cyclone?.ep_label ?? 'EP'}
                      </span>
                    </div>
                    <div className={`mt-2 text-xs ${active ? 'text-slate-200' : 'text-slate-600'}`}>
                      {item.trackId}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}
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
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-slate-500">
                Field Category
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedCategory('synoptic')}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    selectedCategory === 'synoptic'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                    </svg>
                    Synoptic fields
                  </span>
                </button>
                <button
                  onClick={() => setSelectedCategory('dynamic')}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    selectedCategory === 'dynamic'
                      ? 'bg-purple-600 text-white shadow-md'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Dynamic fields
                  </span>
                </button>
              </div>

              <div className="mt-3 rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-600">
                  {selectedCategory === 'synoptic' ? (
                    <><strong className="text-indigo-700">Synoptic fields</strong> show the baseline meteorological environment: SLP, temperature, humidity and geopotential in cyclone-centered coordinates.</>
                  ) : (
                    <><strong className="text-purple-700">Dynamic fields</strong> reveal baroclinic and barotropic diagnostics linked to cyclone intensification: PV structure, temperature advection, AFC, KE advection and critical-region context.</>
                  )}
                </p>
              </div>

              {selectedCategory === 'dynamic' && (
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-slate-500">
                    Select Diagnostic
                  </label>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {dynamicProducts.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => setSelectedDynamicProduct(p.id)}
                        className={`rounded-lg border p-2.5 text-left text-xs transition-all ${
                          selectedDynamicProduct === p.id
                            ? 'border-purple-500 bg-purple-50 text-purple-900 shadow-sm'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <div className="font-medium leading-tight">{p.label}</div>
                      </button>
                    ))}
                  </div>
                  {!hasAnyDynamic && (
                    <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                      <p className="text-xs text-amber-800">
                        <strong>Note:</strong> Dynamic assets are not yet available for this cyclone. 
                        Assets are being progressively generated for the full dataset.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

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
                  {selectedCategory === 'synoptic' ? (
                    <span className="flex items-center gap-2">
                      <span className="inline-block h-2 w-2 rounded-full bg-indigo-500"></span>
                      Synoptic Fields
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <span className="inline-block h-2 w-2 rounded-full bg-purple-500"></span>
                      {selectedProductMeta?.label ?? 'Dynamic Fields'}
                    </span>
                  )}
                </h3>
                <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-500">
                  30°×30° cyclone-centered
                </span>
              </div>
              {panelPath ? (
                <div className="relative aspect-[10/9] w-full overflow-hidden rounded-lg bg-slate-50 shadow-inner">
                  <Image
                    src={panelPath}
                    alt={`Cyclone ${selectedCyclone.track_id} at timestep ${currentTimestepIdx} - ${selectedProductMeta?.label ?? selectedCategory}`}
                    fill
                    className="object-contain"
                    priority
                  />
                </div>
              ) : (
                <div className="flex aspect-[10/9] items-center justify-center rounded-lg bg-slate-100 text-sm text-slate-400">
                  <div className="text-center">
                    <svg className="mx-auto h-10 w-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p className="mt-2">Panel not available for this timestep</p>
                  </div>
                </div>
              )}
              <p className="mt-3 text-xs text-slate-500">
                <strong>Product:</strong> {selectedProductMeta?.label ?? 'Not available'}.
                <span className="ml-1 text-slate-400">{selectedProductMeta?.description ?? ''}</span>
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
