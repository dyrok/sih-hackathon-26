import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: [
    "@saarthi/tokens",
    "@saarthi/i18n",
    "@saarthi/ui",
    "@saarthi/sync",
    "@saarthi/api",
  ],
};

export default nextConfig;
