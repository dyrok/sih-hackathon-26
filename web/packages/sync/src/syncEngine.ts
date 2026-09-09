import { allQueued, markAttempt, queueSize, removeFromQueue } from "./queue";
import type { QueueItem } from "./queue";

export type SyncState = "idle" | "syncing" | "offline" | "error";
export type SyncSnapshot = {
  state: SyncState;
  queued: number;
  lastError: string | null;
  lastSyncedAt: string | null;
  /** Items the server accepted but did not write (same-day, already-this-month). */
  conflicts: number;
};

/** One item's verdict from the server. Anything not `written`/`duplicate` is
 * still an acknowledgement — the item leaves the queue, with its reason kept. */
export type ItemResult = {
  client_uuid: string;
  status: string;
  reason?: string;
  reason_key?: string;
};

type Drainer = (items: QueueItem[]) => Promise<ItemResult[]>;

type SyncEngineOptions = {
  /** Posts a batch and returns one result per item, in any order. */
  drain: Drainer;
  /** Batch size. 25 keeps a request small enough for a 2G link to finish. */
  batchSize?: number;
};

type Listener = (snap: SyncSnapshot) => void;

const RETRY_DELAYS_MS = [5_000, 30_000, 300_000];
const ACCEPTED = new Set([
  "written",
  "duplicate",
  "duplicate_day",
  "already_this_month",
  "already_granted",
  "replaced",
  "dropped_no_consent",
]);
const CONFLICT = new Set(["duplicate_day", "already_this_month"]);

let snapshot: SyncSnapshot = {
  state: "idle",
  queued: 0,
  lastError: null,
  lastSyncedAt: null,
  conflicts: 0,
};
const listeners = new Set<Listener>();
let engine: { stop: () => void; drainNow: () => Promise<void> } | null = null;

function emit() {
  for (const l of listeners) l(snapshot);
}

function patch(next: Partial<SyncSnapshot>) {
  const merged = { ...snapshot, ...next };
  const changed = (Object.keys(merged) as (keyof SyncSnapshot)[]).some(
    (k) => merged[k] !== snapshot[k],
  );
  if (!changed) return;
  snapshot = merged;
  emit();
}

async function refreshQueued() {
  patch({ queued: await queueSize() });
}

/**
 * Opportunistic, resumable sync (ADR-0005).
 *
 * Drains oldest-first in batches. Every item carries a `client_uuid`, so the
 * server collapses a retry into the row it already has (TC-603) — which means
 * a lost response can never duplicate data. An item is removed only once the
 * server has acknowledged it, so killing the app mid-drain loses nothing
 * (TC-605) and the next run resumes from the first unacknowledged item
 * (TC-602). Failures back off 5s → 30s → 5min and retry forever: queued data
 * is never dropped, and never rendered in error styling.
 */
export function startSyncEngine(opts: SyncEngineOptions): { stop: () => void; drainNow: () => Promise<void> } {
  if (engine) return engine;
  const batchSize = opts.batchSize ?? 25;
  let stopped = false;
  let retryIndex = 0;
  //: The drain in flight, if any. Callers join it instead of starting a second
  //: pass — two concurrent drains would race on the same queue rows, and a
  //: caller that returned early while a drain was still running could not tell
  //: whether the queue had actually been sent.
  let inflight: Promise<void> | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const scheduleRetry = (ms: number) => {
    if (stopped) return;
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => void drain(), ms);
  };

  const pass = async (): Promise<void> => {
    if (stopped) return;
    try {
      let pending = await allQueued();
      if (pending.length === 0) {
        patch({ state: "idle", queued: 0, lastError: null });
        return;
      }
      // Only an *explicit* false means offline. `navigator.onLine` is absent in
      // some WebViews and in non-browser runtimes, and treating "unknown" as
      // offline would silently park the queue forever — the one failure mode
      // offline-first must not have.
      if (typeof navigator !== "undefined" && navigator.onLine === false) {
        patch({ state: "offline", queued: pending.length });
        return; // the `online` event wakes us; no timer needed
      }
      patch({ state: "syncing", queued: pending.length });

      let conflicts = snapshot.conflicts;
      while (pending.length > 0 && !stopped) {
        const batch = pending.slice(0, batchSize);
        const results = await opts.drain(batch);
        const byUuid = new Map(results.map((r) => [r.client_uuid, r]));
        let progressed = false;
        for (const item of batch) {
          const result = byUuid.get(item.client_uuid);
          if (result && ACCEPTED.has(result.status)) {
            if (item.id !== undefined) await removeFromQueue(item.id);
            if (CONFLICT.has(result.status)) conflicts += 1;
            progressed = true;
          } else if (result && result.status === "rejected") {
            // A permanently bad row must not block the queue behind it, but it
            // must not vanish either: keep it, flag it, and move on.
            await markAttempt(item, result.reason ?? "rejected");
            progressed = true;
          } else {
            await markAttempt(item);
          }
        }
        if (!progressed) break;
        pending = pending.slice(batch.length);
        await refreshQueued();
      }

      retryIndex = 0;
      patch({
        state: "idle",
        lastError: null,
        lastSyncedAt: new Date().toISOString(),
        conflicts,
      });
      await refreshQueued();
    } catch (err) {
      patch({ state: "error", lastError: err instanceof Error ? err.message : String(err) });
      scheduleRetry(RETRY_DELAYS_MS[Math.min(retryIndex++, RETRY_DELAYS_MS.length - 1)]!);
    }
  };

  /** Start a drain, or join the one already running. Never two at once. */
  const drain = (): Promise<void> => {
    if (inflight) return inflight;
    inflight = pass().finally(() => {
      inflight = null;
    });
    return inflight;
  };

  const onOnline = () => void drain();
  const onOffline = () => patch({ state: "offline" });
  const onVisibility = () => {
    if (document.visibilityState === "visible") void drain();
  };

  if (typeof window !== "undefined") {
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    document.addEventListener("visibilitychange", onVisibility);
  }

  void refreshQueued();
  void drain();

  engine = {
    stop: () => {
      stopped = true;
      if (timer) clearTimeout(timer);
      if (typeof window !== "undefined") {
        window.removeEventListener("online", onOnline);
        window.removeEventListener("offline", onOffline);
        document.removeEventListener("visibilitychange", onVisibility);
      }
      engine = null;
    },
    drainNow: drain,
  };
  return engine;
}

export function getSyncSnapshot(): SyncSnapshot {
  return snapshot;
}

export function subscribeSync(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Optimistic bump so the pill updates the instant an item is queued; the
 * IndexedDB count reconciles right after. */
export function notifyQueueChanged(): void {
  patch({ queued: snapshot.queued + 1 });
  void refreshQueued();
}

/** Test/reset seam — the module holds a singleton so the app cannot start two. */
export function resetSyncEngineForTests(): void {
  engine?.stop();
  engine = null;
  snapshot = { state: "idle", queued: 0, lastError: null, lastSyncedAt: null, conflicts: 0 };
  listeners.clear();
}
