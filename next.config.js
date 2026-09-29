/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Optimized for Vercel serverless deployment

  // Empty turbopack config to silence warning (Turbopack is default in Next.js 16)
  turbopack: {},

  // Inlined at build time so src/lib/api.ts can default to same-origin on Vercel
  // (VERCEL=1 is set in Vercel build containers) and localhost:8000 elsewhere.
  env: {
    MAPIG_ON_VERCEL: process.env.VERCEL ? '1' : '',
  },
};

module.exports = nextConfig;
