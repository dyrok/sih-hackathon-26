import { apiFetch } from "./http";

/**
 * Jawan-role client (self-scope only).
 *
 * NOTE: response shapes are v1 assumptions — kv's backend is the source of
 * truth (http://127.0.0.1:8000/docs). Fields are tolerated loosely (unknown)
 * until shapes are confirmed; adjust here, not in the app.
 */

export type LoginResult = {
  token: string;
  role: string;
  username: string;
};

export async function login(username: string, password: string): Promise<LoginResult> {
  const body = (await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })) as Record<string, unknown>;

  const token = (body["access_token"] ?? body["token"]) as string | undefined;
  if (!token) throw new Error("No token in login response");
  return {
    token,
    role: String(body["role"] ?? "jawan"),
    username: String(body["username"] ?? username),
  };
}

export type ConsentScope = "checkin" | "instrument" | "voice" | "passive" | "pulse" | "buddy";

export async function grantConsent(scope: ConsentScope): Promise<void> {
  await apiFetch("/app/consent", { method: "POST", body: JSON.stringify({ scope, granted: true }) });
}

export async function withdrawConsent(scope: ConsentScope): Promise<void> {
  await apiFetch("/app/consent/withdraw", { method: "POST", body: JSON.stringify({ scope }) });
}

export type CheckInPayload = {
  client_uuid: string;
  captured_at: string;
  local_date: string;
  mood_emoji: number; // 1–5
  stress_slider: number; // 0–10
  free_text?: string;
};

/** Batch, idempotent by client_uuid (F02). */
export async function submitCheckins(items: CheckInPayload[]): Promise<void> {
  await apiFetch("/app/checkins", {
    method: "POST",
    body: JSON.stringify({ client_uuid: items[0]?.client_uuid, items }),
  });
}

export async function submitInstrument(payload: Record<string, unknown>): Promise<void> {
  await apiFetch("/app/instruments", { method: "POST", body: JSON.stringify(payload) });
}

export async function getMyTrend(): Promise<unknown> {
  return apiFetch("/app/me/trend");
}

export async function getWhoViewed(): Promise<unknown[]> {
  const body = (await apiFetch("/app/who-viewed")) as unknown;
  return Array.isArray(body) ? body : [];
}
