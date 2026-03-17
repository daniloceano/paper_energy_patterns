'use client'

import katex from 'katex'
import 'katex/dist/katex.min.css'

interface InlineMathProps {
  expr: string
  className?: string
}

export default function InlineMath({ expr, className }: InlineMathProps) {
  const html = katex.renderToString(expr, { throwOnError: false, displayMode: false })
  return (
    <span className={className} dangerouslySetInnerHTML={{ __html: html }} />
  )
}
