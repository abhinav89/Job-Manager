import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL;

if (process.env.VERCEL && !backendUrl) {
  throw new Error("BACKEND_URL must be configured for Vercel deployments.");
}

const nextConfig: NextConfig = {
  allowedDevOrigins: process.env.NEXT_DIST_DIR ? ["127.0.0.1"] : [],
  distDir: process.env.NEXT_DIST_DIR || ".next",
  turbopack: {},
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
  transpilePackages: ["react-pdf"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl || "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
