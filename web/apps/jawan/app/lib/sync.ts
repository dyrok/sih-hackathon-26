"use client";

import { startSyncEngine } from "@saarthi/sync";
import type { ItemResult, QueueItem } from "@saarthi/sync";
import { syncBatch } from "@saarthi/api/jawan";
import type { SyncItemWire } from "@saarthi/api/jawan";

/**
 * One outbox engine per browser tab.
 *
 * The engine itself is a singleton inside `@saarthi/sync`; this module owns the
 * drain function so that any screen can ask for an immediate send (the safety
 * protocol does) without re-declaring how the queue reaches the server.
 */
let engine: ReturnType<typeof startSyncEngine> | null = null;

function toWire(items: QueueItem[]): SyncItemWire[] {
  return items.map((item) => ({
    table: item.table,
    client_uuid: item.client_uuid,
    captured_at: item.captured_at,
    payload: item.payload,
  }));
}

async function drain(items: QueueItem[]): Promise<ItemResult[]> {
  const response = await syncBatch(toWire(items));
  return response.results;
}

export function ensureSyncEngine(): ReturnType<typeof startSyncEngine> {
  if (!engine) engine = startSyncEngine({ drain });
  return engine;
}

export function stopSyncEngine(): void {
  engine?.stop();
  engine = null;
}

/**
 * Send whatever is queued right now instead of waiting for the next
 * opportunistic drain. Used by the instrument safety screen: a PHQ-9 item 9
 * endorsement is the one queued row that should not sit on the device.
 */
export async function drainNow(): Promise<void> {
  await ensureSyncEngine().drainNow();
}
