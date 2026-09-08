import { get, put, STORES } from "./idb";

const KEY = "client_uuid";

/**
 * Stable per-device idempotency key. Generated once (crypto.randomUUID),
 * persisted in IndexedDB, reused for the lifetime of this browser profile.
 * Never sent with PII — it only guarantees the server can de-duplicate.
 */
export async function getClientUuid(): Promise<string> {
  const existing = await get<string>(STORES.meta, KEY);
  if (existing) return existing;
  const uuid = crypto.randomUUID();
  await put(STORES.meta, uuid, KEY);
  return uuid;
}
