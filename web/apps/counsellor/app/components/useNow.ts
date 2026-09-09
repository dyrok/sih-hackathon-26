"use client";

import { useEffect, useState } from "react";

/**
 * A clock that ticks so the SLA counter ages on screen without a reload.
 *
 * It starts at `null` and only takes a value after mount: the server render and
 * the first client render have to agree, and "now" never does. Callers treat
 * `null` as "no elapsed time yet" and render the static parts.
 */
export function useNow(intervalMs = 60_000): number | null {
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return now;
}
