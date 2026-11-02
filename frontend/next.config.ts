import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  output: "export", trailingSlash: true, images: { unoptimized: true },
  distDir: process.env.NEXT_DIST_DIR || ".next", turbopack: {},
  webpack: config => { config.resolve.alias.canvas = false; return config; },
  transpilePackages: ["react-pdf"],
};
export default nextConfig;
