import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // @saarthi/sync ships TypeScript source and reaches this build through
  // @saarthi/ui's useApi cache, so it has to be transpiled here as well.
  transpilePackages: [
    "@saarthi/tokens",
    "@saarthi/i18n",
    "@saarthi/ui",
    "@saarthi/sync",
    "@saarthi/api",
  ],
};

export default nextConfig;
