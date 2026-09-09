"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { STORES, get, put } from "@saarthi/sync";

export type UseApiResult<T> = {
  data: T | null;
  error: Error | null;
  loading: boolean;
  /** True while `data` is the last-known cached copy rather than a fresh read. */
  stale: boolean;
  reload: () => void;
};

export type UseApiOptions = {
  /** When set, the last successful response is kept in the IndexedDB `cache` store. */
  cacheKey?: string;
};

type CacheEnvelope<T> = { v: T; at: number };

/**
 * Read an `ApiError`'s status without importing the api package — 0 means the
 * network is gone, 403 means the server refused on privacy grounds and must not
 * be retried (design-client-apps.md §4).
 */
export function apiErrorStatus(error: unknown): number | null {
  if (error && typeof error === "object" && "status" in error) {
    const status = (error as { status: unknown }).status;
    if (typeof status === "number") return status;
  }
  return null;
}

/**
 * The one data hook for all three apps, so nobody re-invents loading state.
 *
 * With `cacheKey` it shows the last-known response from IndexedDB first and
 * then reconciles — an offline open shows yesterday's aggregates with a stale
 * flag instead of a blank screen (design-client-apps.md §2). It never throws
 * into render: every failure, including a browser with IndexedDB switched off,
 * ends up in `error` or is swallowed as a cache miss.
 */
export function useApi<T>(fn: () => Promise<T>, deps: unknown[], opts?: UseApiOptions): UseApiResult<T> {
  const cacheKey = opts?.cacheKey;

  const fnRef = useRef(fn);
  fnRef.current = fn;

  const generation = useRef(0);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const [state, setState] = useState<Omit<UseApiResult<T>, "reload">>({
    data: null,
    error: null,
    loading: true,
    stale: false,
  });

  const run = useCallback(async () => {
    const mine = ++generation.current;
    const current = () => mine === generation.current && mounted.current;

    setState((s) => ({ ...s, loading: true, error: null }));

    if (cacheKey) {
      try {
        const cached = await get<CacheEnvelope<T>>(STORES.cache, cacheKey);
        if (cached && current()) {
          setState({ data: cached.v, error: null, loading: true, stale: true });
        }
      } catch {
        // No IndexedDB (private mode, quota, blocked upgrade). A cache miss is
        // not something to tell the user about.
      }
    }

    try {
      const fresh = await fnRef.current();
      if (!current()) return;
      setState({ data: fresh, error: null, loading: false, stale: false });
      if (cacheKey) {
        try {
          await put(STORES.cache, { v: fresh, at: Date.now() } satisfies CacheEnvelope<T>, cacheKey);
        } catch {
          // Writing the cache is best-effort; the screen already has its data.
        }
      }
    } catch (err) {
      if (!current()) return;
      const error = err instanceof Error ? err : new Error(String(err));
      // Keep whatever is on screen. Losing the last-known numbers because the
      // network blinked is the blank-screen failure this hook exists to avoid.
      setState((s) => ({ data: s.data, error, loading: false, stale: s.data !== null }));
    }
  }, [cacheKey]);

  useEffect(() => {
    void run();
    // The caller owns `deps`; `run` only changes with `cacheKey`.
  }, [...deps, run]);

  const reload = useCallback(() => {
    void run();
  }, [run]);

  return { ...state, reload };
}
