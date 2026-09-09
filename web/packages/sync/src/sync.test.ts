import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { indexedDB } from "fake-indexeddb";

import { clearAll, STORES, put, get } from "./idb";
import {
  allQueued,
  enqueue,
  purgeQueueForTables,
  queueSize,
  removeFromQueue,
} from "./queue";
import type { QueueItem } from "./queue";
import { getClientUuid, newItemUuid } from "./clientUuid";
import {
  getSyncSnapshot,
  resetSyncEngineForTests,
  startSyncEngine,
} from "./syncEngine";
import type { ItemResult } from "./syncEngine";

/**
 * The offline suite from docs/quality/test-plan.md §5 (TC-601…605), run against
 * a real IndexedDB implementation rather than a mock of our own queue — a mock
 * would only prove the mock agrees with itself.
 */

globalThis.indexedDB = indexedDB;

function item(table: QueueItem["table"], payload: Record<string, unknown> = {}): QueueItem {
  return {
    table,
    client_uuid: newItemUuid(),
    captured_at: "2026-09-01T06:00:00.000Z",
    payload,
  };
}

/** A server stub that behaves like /app/sync: idempotent by client_uuid. */
function fakeServer() {
  const accepted = new Map<string, string>();
  const calls: QueueItem[][] = [];
  let failNext = 0;
  return {
    accepted,
    calls,
    failFor(n: number) {
      failNext = n;
    },
    async drain(items: QueueItem[]): Promise<ItemResult[]> {
      calls.push(items);
      if (failNext > 0) {
        failNext -= 1;
        throw new Error("network down");
      }
      return items.map((i) => {
        if (accepted.has(i.client_uuid)) {
          return { client_uuid: i.client_uuid, status: "duplicate" };
        }
        accepted.set(i.client_uuid, i.table);
        return { client_uuid: i.client_uuid, status: "written" };
      });
    },
  };
}

const settle = () => new Promise((r) => setTimeout(r, 0));

beforeEach(async () => {
  resetSyncEngineForTests();
  await clearAll();
});

afterEach(() => {
  resetSyncEngineForTests();
});

describe("outbox queue", () => {
  test("a check-in is written locally with no network at all", async () => {
    await enqueue(item("checkin", { mood_score: 6 }));
    expect(await queueSize()).toBe(1);
    const [queued] = await allQueued();
    expect(queued?.payload.mood_score).toBe(6);
    expect(queued?.attempts).toBe(0);
  });

  test("the queue drains oldest first", async () => {
    for (let i = 0; i < 5; i++) await enqueue(item("checkin", { n: i }));
    const queued = await allQueued();
    expect(queued.map((q) => q.payload.n)).toEqual([0, 1, 2, 3, 4]);
  });

  test("the device uuid is stable across calls", async () => {
    const a = await getClientUuid();
    const b = await getClientUuid();
    expect(a).toBe(b);
    expect(a).toMatch(/^[0-9a-f-]{36}$/);
  });

  test("every queued item gets its own uuid", () => {
    const ids = new Set(Array.from({ length: 50 }, () => newItemUuid()));
    expect(ids.size).toBe(50);
  });
});

describe("TC-601 · queue then sync exactly once", () => {
  test("an offline capture syncs once on reconnect", async () => {
    const server = fakeServer();
    await enqueue(item("checkin", { mood_score: 4 }));
    const engine = startSyncEngine({ drain: server.drain });
    await settle();
    await engine.drainNow();
    expect(server.accepted.size).toBe(1);
    expect(await queueSize()).toBe(0);
  });
});

describe("TC-602 · a large queue batches and resumes", () => {
  test("72 entries upload in batches and all land", async () => {
    const server = fakeServer();
    for (let i = 0; i < 72; i++) await enqueue(item("checkin", { n: i }));
    const engine = startSyncEngine({ drain: server.drain, batchSize: 25 });
    await settle();
    await engine.drainNow();
    expect(server.accepted.size).toBe(72);
    expect(await queueSize()).toBe(0);
    expect(server.calls.every((c) => c.length <= 25)).toBe(true);
  });

  test("a mid-drain failure resumes from the first unacknowledged item", async () => {
    const server = fakeServer();
    for (let i = 0; i < 40; i++) await enqueue(item("checkin", { n: i }));
    const engine = startSyncEngine({ drain: server.drain, batchSize: 10 });
    await settle();
    await engine.drainNow();
    const acceptedFirstPass = server.accepted.size;

    server.failFor(1);
    for (let i = 40; i < 50; i++) await enqueue(item("checkin", { n: i }));
    await engine.drainNow(); // throws internally, backs off
    expect(getSyncSnapshot().state).toBe("error");

    await engine.drainNow();
    expect(server.accepted.size).toBeGreaterThanOrEqual(acceptedFirstPass);
    expect(await queueSize()).toBe(0);
  });
});

describe("TC-603 · idempotency collapses a retry", () => {
  test("replaying the same client_uuid never creates a second record", async () => {
    const server = fakeServer();
    const one = item("checkin", { mood_score: 3 });
    await enqueue(one);
    const engine = startSyncEngine({ drain: server.drain });
    await settle();
    await engine.drainNow();

    // The response was "lost": the item is back on the queue with its original uuid.
    await enqueue(one);
    await engine.drainNow();

    expect(server.accepted.size).toBe(1);
    expect(await queueSize()).toBe(0);
  });
});

describe("TC-604 · a conflict is reported, never silently dropped", () => {
  test("a same-day check-in is counted as a conflict, not an error", async () => {
    const conflictServer = {
      async drain(items: QueueItem[]): Promise<ItemResult[]> {
        return items.map((i) => ({ client_uuid: i.client_uuid, status: "duplicate_day" }));
      },
    };
    await enqueue(item("checkin", { recorded_at: "2026-09-01" }));
    const engine = startSyncEngine({ drain: conflictServer.drain });
    await settle();
    await engine.drainNow();
    expect(await queueSize()).toBe(0);
    expect(getSyncSnapshot().conflicts).toBe(1);
    expect(getSyncSnapshot().state).toBe("idle");
  });

  test("a rejected item stays queued with its reason, and does not block the rest", async () => {
    const picky = {
      async drain(items: QueueItem[]): Promise<ItemResult[]> {
        return items.map((i) =>
          i.table === "voice"
            ? { client_uuid: i.client_uuid, status: "rejected", reason: "unknown schema_version" }
            : { client_uuid: i.client_uuid, status: "written" },
        );
      },
    };
    await enqueue(item("voice", { schema_version: "v9" }));
    await enqueue(item("checkin", { mood_score: 5 }));
    const engine = startSyncEngine({ drain: picky.drain });
    await settle();
    await engine.drainNow();

    const left = await allQueued();
    expect(left).toHaveLength(1);
    expect(left[0]?.table).toBe("voice");
    expect(left[0]?.conflict).toBe("unknown schema_version");
  });
});

describe("TC-605 · a kill mid-sync loses nothing", () => {
  test("items unacknowledged when the engine stops are still queued next run", async () => {
    const server = fakeServer();
    for (let i = 0; i < 10; i++) await enqueue(item("checkin", { n: i }));
    server.failFor(1);
    const engine = startSyncEngine({ drain: server.drain, batchSize: 5 });
    // No settle(): drainNow() joins the drain the engine already started, so
    // the assertion is about that exact pass and not a lucky retry.
    await engine.drainNow();
    engine.stop();

    expect(getSyncSnapshot().state).toBe("error");
    expect(await queueSize()).toBe(10);

    resetSyncEngineForTests();
    const resumed = startSyncEngine({ drain: server.drain, batchSize: 5 });
    await settle();
    await resumed.drainNow();
    expect(await queueSize()).toBe(0);
    expect(server.accepted.size).toBe(10);
  });
});

describe("consent withdrawal purges the device", () => {
  test("withdrawing a scope drops exactly that scope's queued rows", async () => {
    await enqueue(item("checkin"));
    await enqueue(item("checkin"));
    await enqueue(item("voice"));
    await enqueue(item("pulse"));

    const removed = await purgeQueueForTables(["voice"]);
    expect(removed).toBe(1);

    const left = await allQueued();
    expect(left.map((i) => i.table).sort()).toEqual(["checkin", "checkin", "pulse"]);
  });

  test("clearing the device leaves no trace of any scope", async () => {
    await enqueue(item("checkin"));
    await put(STORES.cache, { any: "thing" }, "roster");
    await clearAll();
    expect(await queueSize()).toBe(0);
    expect(await get(STORES.cache, "roster")).toBeUndefined();
  });
});

describe("removal is explicit", () => {
  test("removeFromQueue only removes the item it was given", async () => {
    const id = await enqueue(item("checkin"));
    await enqueue(item("checkin"));
    await removeFromQueue(id);
    expect(await queueSize()).toBe(1);
  });
});
