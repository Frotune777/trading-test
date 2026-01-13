import type { NextConfig } from "next";

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

// Default to backend service name for Docker, or localhost for local dev if overridden
const INTERNAL_API_URL = process.env.INTERNAL_API_URL || 'http://quad_backend:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: true,

  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Experimental features
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },

  // API Proxy Rewrites
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${INTERNAL_API_URL}/api/:path*`, // Use Docker service name
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
