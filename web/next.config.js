/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: false,
  },
  // Allow reading figures and data from parent directories
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
}

module.exports = nextConfig
