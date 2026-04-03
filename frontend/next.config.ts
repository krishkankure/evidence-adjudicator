import type { NextConfig } from 'next';

const backendOrigin = process.env.API_BASE_URL ?? 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendOrigin}/:path*`,
      },
    ];
  },
};

export default nextConfig;
