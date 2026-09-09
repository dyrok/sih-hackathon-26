import { del, getAll, put, STORES } from "./idb";

export type QueueTable = "checkin" | "instrument" | "consent" | "pulse" | "passive" | "voice";

export type QueueItem = {
  id?: number;
  table: QueueTable;
  client_uuid: string;
  captured_at: string;
  payload: Record<string, unknown>;
  /** Attempts so far — surfaced in settings so a stuck item is never invisible. */
  attempts?: number;
  /** Set when the server accepted the row but did not write it (same-day
   * check-in, instrument already taken this month). Never silent data loss. */
  conflict?: string;
};

/**
 * Append-only outbox. Writes are instant and local — the network is never on
 * the critical path for a check-in (ADR-0005). An item leaves this queue only
 * when the server has acknowledged it by `client_uuid`.
 */
export async function enqueue(item: QueueItem): Promise<number> {
  const key = await put(STORES.queue, { attempts: 0, ...item });
  return key as number;
}

export async function peekQueue(limit = 50): Promise<QueueItem[]> {
  const all = (await getAll<QueueItem>(STORES.queue)).sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
  return all.slice(0, limit);
}

export async function allQueued(): Promise<QueueItem[]> {
  return (await getAll<QueueItem>(STORES.queue)).sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
}

export async function queueSize(): Promise<number> {
  return (await getAll<QueueItem>(STORES.queue)).length;
}

export async function removeFromQueue(id: number): Promise<void> {
  await del(STORES.queue, id);
}

export async function markAttempt(item: QueueItem, conflict?: string): Promise<void> {
  if (item.id === undefined) return;
  await put(STORES.queue, {
    ...item,
    attempts: (item.attempts ?? 0) + 1,
    ...(conflict ? { conflict } : {}),
  });
}

/**
 * Consent withdrawal must leave nothing behind on the device (F02 DoD):
 * drop every queued row captured under the scope being withdrawn.
 */
export async function purgeQueueForTables(tables: QueueTable[]): Promise<number> {
  const set = new Set(tables);
  const all = await allQueued();
  let removed = 0;
  for (const item of all) {
    if (set.has(item.table) && item.id !== undefined) {
      await del(STORES.queue, item.id);
      removed += 1;
    }
  }
  return removed;
}
