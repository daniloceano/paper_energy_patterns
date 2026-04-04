/**
 * Client-side image component with automatic fallback from Supabase to local assets.
 * 
 * Usage:
 *   <FallbackImage
 *     src={figureUrl('figures/ep_structure/composite_egr_central_time.png')}
 *     alt="EGR composite"
 *     width={1200}
 *     height={600}
 *     className="w-full rounded-lg"
 *   />
 * 
 * Behavior:
 * - First tries to load from Supabase (if NEXT_PUBLIC_SUPABASE_FIGURES_URL is set)
 * - On 404/error, automatically falls back to /figures/ (local public assets)
 * - Shows error state if both fail
 */

'use client'

import { useState } from 'react'
import Image, { ImageProps } from 'next/image'
import { AlertCircle } from 'lucide-react'

interface FallbackImageProps extends Omit<ImageProps, 'src' | 'onError'> {
  src: string
  alt: string
  fallbackSrc?: string
}

export default function FallbackImage({ 
  src, 
  alt, 
  fallbackSrc,
  className,
  ...props 
}: FallbackImageProps) {
  const [currentSrc, setCurrentSrc] = useState(src)
  const [hasError, setHasError] = useState(false)

  const handleError = () => {
    // If src is a Supabase URL and we haven't tried fallback yet
    if (currentSrc.includes('supabase.co') && !hasError) {
      // Extract the path: try to find pattern like "ep_structure/composite_egr_central_time.png"
      // or "cyclone_explorer/ep1/20040394/panel_t000.png"
      const pathMatch = currentSrc.match(/\/storage\/v1\/object\/public\/figures\/(.+)$/)
      const relativePath = pathMatch ? pathMatch[1] : null
      
      const localPath = relativePath ? `/figures/${relativePath}` : fallbackSrc || src
      
      console.warn(`Failed to load from Supabase: ${currentSrc}. Falling back to: ${localPath}`)
      setCurrentSrc(localPath)
    } else {
      // Both Supabase and fallback failed
      console.error(`Failed to load image: ${currentSrc}`)
      setHasError(true)
    }
  }

  if (hasError) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-red-300 bg-red-50/50 p-12 text-center">
        <AlertCircle className="mb-3 h-8 w-8 text-red-400" />
        <p className="text-sm font-medium text-red-600">
          Failed to load image
        </p>
        <p className="mt-1 text-xs text-red-400">
          {alt}
        </p>
        <p className="mt-2 text-xs font-mono text-red-300">
          Tried: {src}
        </p>
      </div>
    )
  }

  return (
    <Image
      {...props}
      src={currentSrc}
      alt={alt}
      onError={handleError}
      className={className}
      unoptimized
    />
  )
}
