import { get, put, STORES } from "./idb";

const KEY = "client_uuid";

function uuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Older WebViews on API-26-class devices lack randomUUID. getRandomValues is
  // still present, so we build a v4 by hand rather than fall back to Math.random.
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6]! & 0x0f) | 0x40;
  bytes[8] = (bytes[8]! & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/**
 * Stable per-device key. Generated once, persisted in IndexedDB, reused for the
 * lifetime of this browser profile. It carries no PII — it exists only so the
 * server can recognise a retry.
 */
export async function getClientUuid(): Promise<string> {
  const existing = await get<string>(STORES.meta, KEY);
  if (existing) return existing;
  const value = uuid();
  await put(STORES.meta, value, KEY);
  return value;
}

/** Per-item idempotency key. The device key alone would collapse two different
 * check-ins into one, so every queued row gets its own. */
export function newItemUuid(): string {
  return uuid();
}
