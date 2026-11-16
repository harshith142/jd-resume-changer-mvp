// next.config.js
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['lh3.googleusercontent.com', 'avatars.githubusercontent.com'],
  },
  output: 'standalone',
  // Disable worker threads to fix Windows EPERM error
  experimental: {
    workerThreads: false,
    cpus: 1,
  },
  // Skip TypeScript type checking during build (run separately via 'npm run type-check')
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Ensure NEXTAUTH_URL is available during build for static generation
  env: {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL || 'http://localhost:3000',
  },
  webpack: (config, { isServer, dev }) => {
    // Limit workers to 1 for Windows compatibility
    if (!dev && !isServer) {
      config.parallelism = 1;
    }
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
