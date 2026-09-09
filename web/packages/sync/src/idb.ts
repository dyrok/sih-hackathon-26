/** Minimal IndexedDB promise wrapper — no external deps (a 2 GB phone pays for
 * every kilobyte of dependency, ADR-0005). */

export const DB_NAME = "saarthi-offline";
export const DB_VERSION = 2;
export const STORES = {
  meta: "meta", // key/value (client_uuid, last drain, cached reads)
  queue: "queue", // outbound sync queue
  checkIns: "checkIns", // local echo of own check-ins (offline trend)
  cache: "cache", // last-known server reads, so an offline open is not blank
} as const;

let dbPromise: Promise<IDBDatabase> | null = null;

function open(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORES.meta)) db.createObjectStore(STORES.meta);
      if (!db.objectStoreNames.contains(STORES.queue)) {
        const queue = db.createObjectStore(STORES.queue, { keyPath: "id", autoIncrement: true });
        queue.createIndex("by_table", "table");
      }
      if (!db.objectStoreNames.contains(STORES.checkIns)) {
        const checkIns = db.createObjectStore(STORES.checkIns, { keyPath: "client_uuid" });
        checkIns.createIndex("by_local_date", "local_date");
      }
      if (!db.objectStoreNames.contains(STORES.cache)) db.createObjectStore(STORES.cache);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
    req.onblocked = () => reject(new Error("IndexedDB blocked"));
  });
  return dbPromise;
}

export function tx<T>(
  store: string,
  mode: IDBTransactionMode,
  fn: (s: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return open().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const t = db.transaction(store, mode);
        const req = fn(t.objectStore(store));
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }),
  );
}

export function getAll<T>(store: string): Promise<T[]> {
  return tx(store, "readonly", (s) => s.getAll() as IDBRequest<T[]>);
}

export function put(store: string, value: unknown, key?: IDBValidKey): Promise<IDBValidKey> {
  return tx(store, "readwrite", (s) => s.put(value, key));
}

export function get<T>(store: string, key: IDBValidKey): Promise<T | undefined> {
  return tx(store, "readonly", (s) => s.get(key) as IDBRequest<T | undefined>);
}

export function del(store: string, key: IDBValidKey): Promise<undefined> {
  return tx(store, "readwrite", (s) => s.delete(key) as IDBRequest<undefined>);
}

export function clearStore(store: string): Promise<undefined> {
  return tx(store, "readwrite", (s) => s.clear() as IDBRequest<undefined>);
}

/** Wipe every local table. Used by consent withdrawal and "clear this device". */
export async function clearAll(): Promise<void> {
  await Promise.all(Object.values(STORES).map((s) => clearStore(s)));
}
