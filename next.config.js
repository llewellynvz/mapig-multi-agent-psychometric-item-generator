/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Optimized for Vercel serverless deployment

  // Empty turbopack config to silence warning (Turbopack is default in Next.js 16)
  turbopack: {},
};

module.exports = nextConfig;
