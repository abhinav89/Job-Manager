import type { NextConfig } from "next";

const isBuild = process.env.npm_lifecycle_event === "build";

const nextConfig: NextConfig = {
  ...(isBuild ? { output: "export" } : {}),
  trailingSlash: false,
  images: { unoptimized: true },
  distDir: process.env.NEXT_DIST_DIR || ".next",
  turbopack: {},
  webpack: config => {
    config.resolve.alias.canvas = false;
    return config;
  },
  transpilePackages: ["react-pdf"],
  ...(!isBuild
    ? {
        async rewrites() {
          return [
            {
              source: "/api/:path*",
              destination: "http://127.0.0.1:8005/api/:path*",
            },
            {
              source: "/workspace",
              destination: "http://127.0.0.1:8005/workspace",
            },
            {
              source: "/preferences",
              destination: "http://127.0.0.1:8005/preferences",
            },
          ];
        },
      }
    : {}),
};

export default nextConfig;
