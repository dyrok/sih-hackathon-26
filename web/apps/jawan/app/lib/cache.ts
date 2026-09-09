"use client";

import { STORES, put } from "@saarthi/sync";
import type { QueueTable } from "@saarthi/sync";
import type { ConsentBundleId } from "@saarthi/api/jawan";

/**
 * Cache keys for `useApi({ cacheKey })`. Named in one place so that consent
 * withdrawal can forget exactly the reads that belong to the scope being
 * withdrawn — "no welfare data may sit in any client cache lacking a purge
 * path" (design-client-apps.md §5).
 */
export const CACHE = {
  roster: "jawan.roster",
  leave: "jawan.leave",
  payslip: "jawan.payslip",
  checkins: "jawan.checkins",
  checkinsToday: "jawan.checkins.today",
  trend: "jawan.trend",
  instruments: "jawan.instruments",
  consent: "jawan.consent",
  pulse: "jawan.pulse",
  buddy: "jawan.buddy",
  signals: "jawan.signals",
  whoViewed: "jawan.whoViewed",
  notifications: "jawan.notifications",
} as const;

/** Which queued table a consent bundle gates (mirrors the backend GATE map). */
export const BUNDLE_TABLES: Record<ConsentBundleId, QueueTable[]> = {
  checkin: ["checkin"],
  instruments: ["instrument"],
  voice: ["voice"],
  passive: ["passive"],
  unit_pulse: ["pulse"],
  buddy: [],
};

/** Which cached reads a consent bundle owns. */
export const BUNDLE_CACHE_KEYS: Record<ConsentBundleId, string[]> = {
  checkin: [CACHE.checkins, CACHE.checkinsToday, CACHE.trend],
  instruments: [CACHE.instruments],
  voice: [],
  passive: [CACHE.signals],
  unit_pulse: [CACHE.pulse],
  buddy: [CACHE.buddy],
};

/**
 * Blank a cached read. `@saarthi/sync` exposes no per-key delete, so an empty
 * envelope is written instead — `useApi` reads it back as "no data", which is
 * the behaviour that matters: after a withdrawal the screen must not still be
 * able to show what was collected under that scope.
 */
export async function forgetCache(keys: string[]): Promise<void> {
  for (const key of keys) {
    try {
      await put(STORES.cache, { v: null, at: Date.now() }, key);
    } catch {
      // No IndexedDB (private mode). Nothing was cached, so nothing to forget.
    }
  }
}
