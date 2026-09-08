import { peekQueue, queueSize, removeFromQueue } from "./queue";
import type { QueueItem } from "./queue";

export type SyncState = "idle" | "syncing" | "offline" | "error";
export type SyncSnapshot = {
  state: SyncState;
  queued: number;
  lastError: string | null;
};

type SyncEngineOptions = {
  apiBase: string;
  getToken: () => string | null;
  /** Batch endpoint for check-ins; other tables go to their own endpoints. */
  endpoints: Partial<Record<QueueItem["table"], string>>;
};

type Listener = (snap: SyncSnapshot) => void;

const RETRY_DELAYS_MS = [5_000, 30_000, 300_000];

let snapshot: SyncSnapshot = { state: "idle", queued: 0, lastError: null };
const listeners = new Set<Listener>();
let engine: { stop: () => void } | null = null;

function emit() {
  for (const l of listeners) l(snapshot);
}

async function refreshQueued() {
  const queued = await queueSize();
  if (queued !== snapshot.queued) {
    snapshot = { ...snapshot, queued };
    emit();
  }
}

function setState(state: SyncState, lastError: string | null = null) {
  if (state === snapshot.state && lastError === snapshot.lastError) return;
  snapshot = { ...snapshot, state, lastError };
  emit();
}

async function postJson(url: string, token: string | null, body: unknown): Promise<Response> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}

/**
 * Opportunistic, resumable sync (ADR-0005): drains the queue oldest-first,
 * idempotent via client_uuid on every payload. Check-ins batch to one POST;
 * other tables flush one item per request. Never clears an item unless the
 * server accepted it. Failures back off 5s → 30s → 5min and retry forever —
 * queued data is never dropped, never error-styled.
 */
export function startSyncEngine(opts: SyncEngineOptions): { stop: () => void } {
  if (engine) return engine;
  let stopped = false;
  let retryIndex = 0;
  let running = false;

  const { apiBase, getToken, endpoints } = opts;
  const queueEndpoint = (table: QueueItem["table"]) => endpoints[table] ?? `/app/${table}s`;

  const drain = async () => {
    if (running) return;
    running = true;
    try {
      const items = await peekQueue();
      if (items.length === 0) {
        setState("idle");
        return;
      }
      if (!navigator.onLine) {
        setState("offline");
        scheduleRetry(RETRY_DELAYS_MS[0]!);
        return;
      }
      setState("syncing");
      const token = getToken();

      // kv's endpoints take one item per request (POST /app/checkins is a
      // single row). Drain oldest-first; only a 2xx removes an item, so
      // retries can never duplicate (client_uuid is carried for audit).
      for (const item of items) {
        await postJson(`${apiBase}${queueEndpoint(item.table)}`, token, {
          ...item.payload,
          client_uuid: item.client_uuid,
          captured_at: item.captured_at,
        });
        await removeFromQueue(item.id!);
      }

      retryIndex = 0;
      setState("idle");
      await refreshQueued();
    } catch (err) {
      setState("error", err instanceof Error ? err.message : String(err));
      scheduleRetry(RETRY_DELAYS_MS[Math.min(retryIndex++, RETRY_DELAYS_MS.length - 1)]!);
    } finally {
      running = false;
    }
  };

  let timer: ReturnType<typeof setTimeout> | null = null;
  const scheduleRetry = (ms: number) => {
    if (stopped) return;
    if (timer) clearTimeout(timer);
    timer = setTimeout(drain, ms);
  };

  const onOnline = () => void drain();
  const onOffline = () => {
    setState("offline");
  };
  const onVisibility = () => {
    if (document.visibilityState === "visible") void drain();
  };

  window.addEventListener("online", onOnline);
  window.addEventListener("offline", onOffline);
  document.addEventListener("visibilitychange", onVisibility);

  void refreshQueued();
  void drain();

  engine = {
    stop: () => {
      stopped = true;
      if (timer) clearTimeout(timer);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
      document.removeEventListener("visibilitychange", onVisibility);
      engine = null;
    },
  };
  return engine;
}

export function getSyncSnapshot(): SyncSnapshot {
  return snapshot;
}

export function subscribeSync(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function notifyQueueChanged(): void {
  // Optimistic bump so the SyncPill updates the moment an item is queued;
  // refreshQueued reconciles with the real IndexedDB count.
  snapshot = { ...snapshot, queued: snapshot.queued + 1 };
  emit();
  void refreshQueued();
}
