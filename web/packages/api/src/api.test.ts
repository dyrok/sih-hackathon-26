import { describe, expect, test } from "bun:test";

import { ApiError } from "./http";
import { MOOD_LABELS, toCheckInWire } from "./jawan";

/**
 * The wire contract, pinned. These are the conversions where a silent
 * off-by-one changes what the rules engine believes about a person.
 */

describe("check-in wire format", () => {
  test("the stress slider is inverted into the engine's mood_score", () => {
    // The UI asks "how heavy did today feel" (0 light … 10 heavy); the engine
    // reads mood_score where HIGHER is better. If this inversion is ever lost,
    // every check-in reports the opposite of what the person said.
    expect(toCheckInWire(5, 0, "2026-09-01").mood_score).toBe(10);
    expect(toCheckInWire(1, 10, "2026-09-01").mood_score).toBe(0);
    expect(toCheckInWire(3, 4, "2026-09-01").mood_score).toBe(6);
  });

  test("every emoji maps to a label from the closed set the engine reads", () => {
    const labels = Object.values(MOOD_LABELS);
    for (let emoji = 1; emoji <= 5; emoji++) {
      expect(labels).toContain(toCheckInWire(emoji, 5, "2026-09-01").mood_label);
    }
  });

  test("the two labels the masking rule keys on are reachable", () => {
    // detect_masking treats fine/good/great as "I'm fine". If the top of the
    // scale stopped producing one of those, the demo's masking beat dies.
    expect(toCheckInWire(5, 0, "2026-09-01").mood_label).toBe("fine");
    expect(toCheckInWire(4, 2, "2026-09-01").mood_label).toBe("good");
  });

  test("an out-of-range emoji degrades to the neutral label, never to undefined", () => {
    expect(toCheckInWire(99, 5, "2026-09-01").mood_label).toBe("ok");
  });

  test("the local date passes through untouched", () => {
    expect(toCheckInWire(3, 5, "2026-08-14").recorded_at).toBe("2026-08-14");
  });

  test("optional fields are omitted rather than sent as null", () => {
    const bare = toCheckInWire(3, 5, "2026-09-01");
    expect("sleep_hours" in bare).toBe(false);
    expect("free_text" in bare).toBe(false);

    const full = toCheckInWire(3, 5, "2026-09-01", { sleep_hours: 5.5, free_text: "long night" });
    expect(full.sleep_hours).toBe(5.5);
    expect(full.free_text).toBe("long night");
  });

  test("an empty note is not sent", () => {
    const wire = toCheckInWire(3, 5, "2026-09-01", { free_text: "" });
    expect("free_text" in wire).toBe(false);
  });
});

describe("ApiError", () => {
  test("status 0 means the network is gone, not that the server refused", () => {
    const offline = new ApiError(0, "network unreachable");
    expect(offline.forbidden).toBe(false);
    expect(offline.status).toBe(0);
  });

  test("403 is flagged so the UI can explain instead of retrying", () => {
    expect(new ApiError(403, "commander identity cannot access…").forbidden).toBe(true);
    expect(new ApiError(404, "not found").forbidden).toBe(false);
  });

  test("it is a real Error, so it survives a catch chain", () => {
    const err = new ApiError(500, "boom");
    expect(err instanceof Error).toBe(true);
    expect(err.name).toBe("ApiError");
    expect(err.message).toBe("boom");
  });
});

describe("role isolation is a module boundary, not a convention", () => {
  test("the shared entry point exposes no role-specific call", async () => {
    const shared = await import("./index");
    const names = Object.keys(shared);
    for (const roleOnly of [
      "getQueue",
      "getCase",
      "requestUnmask",
      "breakGlass",
      "getUnits",
      "runSimulation",
      "getMyTrend",
      "submitPulse",
    ]) {
      expect(names).not.toContain(roleOnly);
    }
    // …while the calls every surface needs are there.
    for (const shared of ["login", "getMe", "apiFetch", "getToken", "clearSession"]) {
      expect(names).toContain(shared);
    }
  });
});
