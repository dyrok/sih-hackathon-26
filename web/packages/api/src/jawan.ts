import { apiFetch } from "./http";

/**
 * Jawan-role client (self-scope only).
 * Contract source of truth: kv's backend (backend/app/api/routers/app_data.py,
 * privacy.py) — verified live on 2026-09-08.
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

/**
 * Check-in wire format (kv): mood_label from a closed set the rules engine
 * reads ("fine"|"good"|"great" → fine), mood_score 0–10 where HIGHER is
 * better, recorded_at as a local YYYY-MM-DD. The app's stress slider is
 * inverted here so UI framing stays "how heavy did today feel".
 */
export const MOOD_LABELS = {
  1: "rough",
  2: "low",
  3: "ok",
  4: "good",
  5: "fine",
} as const;

export type CheckInWire = {
  mood_label: string;
  mood_score: number;
  recorded_at: string;
};

export function toCheckInWire(moodEmoji: number, stressSlider: number, localDate: string): CheckInWire {
  return {
    mood_label: MOOD_LABELS[moodEmoji as keyof typeof MOOD_LABELS] ?? "ok",
    mood_score: 10 - stressSlider,
    recorded_at: localDate,
  };
}

/** One POST per check-in (kv's /app/checkins takes a single row). */
export async function submitCheckin(wire: CheckInWire): Promise<void> {
  await apiFetch("/app/checkins", { method: "POST", body: JSON.stringify(wire) });
}

export type ConsentBundle = "checkin" | "instruments" | "passive" | "unit_pulse";

export type ConsentWire = {
  bundle_id: ConsentBundle;
  purpose_string: string;
  data_categories: string[];
  language: "en" | "hi";
};

/** Not idempotent server-side — grant once per bundle per device. */
export async function grantConsent(wire: ConsentWire): Promise<void> {
  await apiFetch("/app/consent", { method: "POST", body: JSON.stringify(wire) });
}

/** Withdraws ALL bundles (kv's semantics), silent to command. */
export async function withdrawAllConsent(): Promise<{ withdrawn: number; command_visible: boolean }> {
  return (await apiFetch("/app/consent/withdraw", { method: "POST", body: "{}" })) as {
    withdrawn: number;
    command_visible: boolean;
  };
}

export type InstrumentWire = {
  instrument: string;
  score: number;
  item_9?: number;
  validity_fail?: boolean;
  straight_lining?: boolean;
  too_fast?: boolean;
  all_max?: boolean;
  recorded_at?: string;
};

export async function submitInstrument(wire: InstrumentWire): Promise<void> {
  await apiFetch("/app/instruments", { method: "POST", body: JSON.stringify(wire) });
}

export type TrendPoint = { as_of: string; score: number; tier: string };

export async function getMyTrend(): Promise<{ disclaimer_key: string; trend: TrendPoint[] }> {
  return (await apiFetch("/app/me/trend")) as { disclaimer_key: string; trend: TrendPoint[] };
}

export type WhoViewedEntry = {
  role: string;
  when: string;
  why: string;
  action: string;
};

export type WhoViewed = {
  title_key: string;
  entries: WhoViewedEntry[];
};

export async function getWhoViewed(): Promise<WhoViewed> {
  return (await apiFetch("/app/who-viewed")) as WhoViewed;
}
