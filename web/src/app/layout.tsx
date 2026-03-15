import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'Energy Patterns — South Atlantic Cyclones',
    template: '%s | Energy Patterns',
  },
  description:
    'Interactive exploration of energetic patterns of extratropical cyclones in the Southwestern Atlantic, based on Lorenz Energy Cycle diagnostics and ERA5 reanalysis composites.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css"
          crossOrigin="anonymous"
        />
      </head>
      <body className={`${inter.className} flex min-h-screen flex-col bg-white text-slate-900 antialiased`}>
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
