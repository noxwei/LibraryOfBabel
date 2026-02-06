/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Rewrites only work in dev mode (not static export)
  // In production, the Flask API serves both static files and /api/* routes
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5564/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
