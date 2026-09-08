import { del, getAll, put, STORES } from "./idb";

export type QueueTable = "checkin" | "instrument" | "consent" | "pulse";

export type QueueItem = {
  id?: number;
  table: QueueTable;
  client_uuid: string;
  captured_at: string;
  payload: Record<string, unknown>;
};

/**
 * Append-only outbound queue. Writes are instant and local — the network is
 * never on the critical path for a check-in (ADR-0005).
 */
export async function enqueue(item: QueueItem): Promise<number> {
  const key = await put(STORES.queue, item);
  return key as number;
}

export async function peekQueue(limit = 50): Promise<QueueItem[]> {
  const all = (await getAll<QueueItem>(STORES.queue)).sort(
    (a, b) => (a.id ?? 0) - (b.id ?? 0),
  );
  return all.slice(0, limit);
}

export async function queueSize(): Promise<number> {
  const all = await getAll<QueueItem>(STORES.queue);
  return all.length;
}

export async function removeFromQueue(id: number): Promise<void> {
  await del(STORES.queue, id);
}
