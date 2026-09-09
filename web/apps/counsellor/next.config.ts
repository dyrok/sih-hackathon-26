import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // @saarthi/sync ships TypeScript source and is pulled in transitively by
  // @saarthi/ui (useApi caches last-known responses in IndexedDB), so it has to
  // be transpiled here even though the console never queues anything itself.
  transpilePackages: ["@saarthi/tokens", "@saarthi/i18n", "@saarthi/ui", "@saarthi/api", "@saarthi/sync"],
};

export default nextConfig;
