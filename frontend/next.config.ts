import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    allowedDevOrigins: ["192.168.1.176", "localhost:3000"]
  }
};

export default nextConfig;
