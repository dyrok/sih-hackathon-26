"use client";

import { useEffect } from "react";

/**
 * Service worker registration — production builds only.
 * In dev the SW poisons iteration: it caches `_next/static` chunks forever,
 * so hot reloads/rebuilds serve stale chunks and the page breaks with
 * "Cannot find module" errors. Dev also self-heals any SW a production
 * session may have left behind.
 */
export function SwRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    if (process.env.NODE_ENV !== "production") {
      navigator.serviceWorker
        .getRegistrations()
        .then((regs) => Promise.all(regs.map((r) => r.unregister())))
        .catch(() => {
          /* best-effort cleanup */
        });
      return;
    }

    navigator.serviceWorker.register("/sw.js").catch(() => {
      /* registration is best-effort; the app works without it */
    });
  }, []);
  return null;
}
