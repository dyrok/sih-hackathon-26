/** Minimal IndexedDB promise wrapper — no external deps. */

export const DB_NAME = "saarthi-offline";
export const DB_VERSION = 1;
export const STORES = {
  meta: "meta", // key/value (client_uuid etc.)
  queue: "queue", // outbound sync queue
  checkIns: "checkIns", // local copies of check-ins (trend cache, later)
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
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
    req.onblocked = () => reject(new Error("IndexedDB blocked"));
  });
  return dbPromise;
}

export function tx<T>(store: string, mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
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
