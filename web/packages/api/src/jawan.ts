import { apiFetch } from "./http";

/**
 * Jawan-role client — self-scope only.
 *
 * Every endpoint below resolves the subject from the bearer token. There is no
 * function in this file that takes a personnel id, a pseudonym, or any other
 * subject selector: the "read someone else" call does not exist to be misused
 * (F02 privacy note 4).
 *
 * Contract source of truth: backend/app/api/routers/{app_data,privacy,
 * self_service,pulse,buddy}.py.
 */

// ---------------------------------------------------------------------------
// Check-in (F02 screen 2)
// ---------------------------------------------------------------------------

/**
 * Wire format: `mood_label` from the closed set the rules engine reads, and
 * `mood_score` 0-10 where HIGHER is better. The app's slider asks "how heavy
 * did today feel", so it is inverted here — the UI keeps its own framing and
 * the engine keeps its own convention.
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
  sleep_hours?: number;
  free_text?: string;
};

export function toCheckInWire(
  moodEmoji: number,
  stressSlider: number,
  localDate: string,
  extra?: { sleep_hours?: number; free_text?: string },
): CheckInWire {
  return {
    mood_label: MOOD_LABELS[moodEmoji as keyof typeof MOOD_LABELS] ?? "ok",
    mood_score: 10 - stressSlider,
    recorded_at: localDate,
    ...(extra?.sleep_hours !== undefined ? { sleep_hours: extra.sleep_hours } : {}),
    ...(extra?.free_text ? { free_text: extra.free_text } : {}),
  };
}

export type CheckInRow = {
  date: string;
  mood_label: string | null;
  mood_score: number | null;
  sleep_hours: number | null;
  expires_at: string;
};

export type MyCheckIns = {
  as_of: string;
  checked_in_today: boolean;
  checkins: CheckInRow[];
  disclaimer_key: string;
  own_only_key: string;
};

export function getMyCheckIns(days = 90): Promise<MyCheckIns> {
  return apiFetch(`/app/me/checkins?days=${days}`) as Promise<MyCheckIns>;
}

// ---------------------------------------------------------------------------
// Offline outbox drain (ADR-0005)
// ---------------------------------------------------------------------------

export type SyncTable = "checkin" | "instrument" | "consent" | "pulse" | "passive" | "voice";

export type SyncItemWire = {
  table: SyncTable;
  client_uuid: string;
  captured_at?: string;
  payload: Record<string, unknown>;
};

export type SyncResult = {
  client_uuid: string;
  table: SyncTable;
  /** `duplicate` means the server already had it — a retry, not an error. */
  status: "written" | "duplicate" | "duplicate_day" | "already_this_month" | "already_granted" | "replaced" | "dropped_no_consent" | "rejected";
  id?: string | null;
  reason?: string;
  reason_key?: string;
};

export type SyncResponse = { results: SyncResult[]; accepted: number; received: number };

/** One request drains the whole queue; each item reports its own outcome. */
export function syncBatch(items: SyncItemWire[]): Promise<SyncResponse> {
  return apiFetch("/app/sync", {
    method: "POST",
    body: JSON.stringify({ items }),
  }) as Promise<SyncResponse>;
}

// ---------------------------------------------------------------------------
// Consent (F02 screen 5)
// ---------------------------------------------------------------------------

export type ConsentBundleId =
  | "checkin"
  | "instruments"
  | "voice"
  | "passive"
  | "unit_pulse"
  | "buddy";

export type ConsentBundle = {
  bundle_id: ConsentBundleId;
  granted: boolean;
  granted_at: string | null;
  withdrawn_at: string | null;
  consent_version: string | null;
  label_key: string;
  purpose_key: string;
  data_categories: string[];
  retention_days: number;
};

export type ConsentPanel = {
  title_key: string;
  withdraw_key: string;
  confirm_key: string;
  silent_key: string;
  bundles: ConsentBundle[];
};

export function getConsent(): Promise<ConsentPanel> {
  return apiFetch("/app/consent") as Promise<ConsentPanel>;
}

export type ConsentWire = {
  bundle_id: ConsentBundleId;
  purpose_string: string;
  data_categories: string[];
  language: "en" | "hi";
};

export function grantConsent(wire: ConsentWire): Promise<void> {
  return apiFetch("/app/consent", { method: "POST", body: JSON.stringify(wire) }) as Promise<void>;
}

/** Per-scope withdrawal. Silent to command by construction (FR-17). */
export function withdrawBundle(
  bundleId: ConsentBundleId,
): Promise<{ bundle_id: string; withdrawn: number; command_visible: boolean }> {
  return apiFetch(`/app/consent/withdraw/${bundleId}`, { method: "POST", body: "{}" }) as Promise<{
    bundle_id: string;
    withdrawn: number;
    command_visible: boolean;
  }>;
}

export function withdrawAllConsent(): Promise<{ withdrawn: number; command_visible: boolean }> {
  return apiFetch("/app/consent/withdraw", { method: "POST", body: "{}" }) as Promise<{
    withdrawn: number;
    command_visible: boolean;
  }>;
}

// ---------------------------------------------------------------------------
// Instruments (F02 screen 3)
// ---------------------------------------------------------------------------

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

export type MyInstruments = {
  instruments: string[];
  done_this_month: string[];
  done_key: string;
  history: { instrument: string; score: number; date: string }[];
  disclaimer_key: string;
};

export function getMyInstruments(): Promise<MyInstruments> {
  return apiFetch("/app/me/instruments") as Promise<MyInstruments>;
}

// ---------------------------------------------------------------------------
// Trend, receipts, stored-data summary (F02 screens 4, 6 · F03 screen 4)
// ---------------------------------------------------------------------------

export type TrendPoint = { as_of: string; score: number; tier: string };

export function getMyTrend(): Promise<{ disclaimer_key: string; trend: TrendPoint[] }> {
  return apiFetch("/app/me/trend") as Promise<{ disclaimer_key: string; trend: TrendPoint[] }>;
}

export type WhoViewedEntry = { role: string; when: string; why: string | null; action: string };
export type WhoViewed = { title_key: string; entries: WhoViewedEntry[] };

export function getWhoViewed(): Promise<WhoViewed> {
  return apiFetch("/app/who-viewed") as Promise<WhoViewed>;
}

export type SignalScope = {
  bundle_id: string;
  label_key: string;
  rows_held: number;
  oldest_expiry: string | null;
  granted: boolean;
};

export type SignalsSummary = {
  raw_ttl_days: number;
  explain_key: string;
  scopes: SignalScope[];
  raw_audio_held: boolean;
  transcripts_held: boolean;
};

export function getSignalsSummary(): Promise<SignalsSummary> {
  return apiFetch("/app/signals/summary") as Promise<SignalsSummary>;
}

// ---------------------------------------------------------------------------
// Roster-first home (F02 screen 1)
// ---------------------------------------------------------------------------

export type RosterDay = { date: string; shift_code: string; rest_day: boolean; unit_id: string };
export type Roster = {
  as_of: string;
  next_duty: { date: string; shift_code: string; unit_id: string } | null;
  days: RosterDay[];
  source: string;
};

export function getRoster(days = 14): Promise<Roster> {
  return apiFetch(`/app/roster?days=${days}`) as Promise<Roster>;
}

export type LeaveApplication = {
  leave_type: string;
  home_leave: boolean;
  applied_at: string;
  from: string | null;
  to: string | null;
  cancelled_at: string | null;
  status: "applied" | "sanctioned" | "cancelled";
};

export type Leave = {
  balance_days: number;
  entitlement_days: number;
  taken_days: number;
  applications: LeaveApplication[];
  source: string;
};

export function getLeave(): Promise<Leave> {
  return apiFetch("/app/leave") as Promise<Leave>;
}

export type Payslip = {
  month: string;
  rank: string | null;
  available: boolean;
  reason_key: string;
  source: string;
};

export function getPayslip(): Promise<Payslip> {
  return apiFetch("/app/payslip") as Promise<Payslip>;
}

// ---------------------------------------------------------------------------
// Unit pulse (F02 screen 8) — write-only from here; the aggregate is F07's
// ---------------------------------------------------------------------------

export type PulseFacet = "leadership" | "fairness" | "family_support" | "facilities";

export type MyPulse = {
  period: string;
  facets: PulseFacet[];
  mine: Partial<Record<PulseFacet, number>>;
};

export function getMyPulse(): Promise<MyPulse> {
  return apiFetch("/app/pulse/me") as Promise<MyPulse>;
}

export function submitPulse(
  ratings: { facet: PulseFacet; rating: number }[],
): Promise<{ recorded: unknown[]; aggregate_only: boolean }> {
  return apiFetch("/app/pulse", {
    method: "POST",
    body: JSON.stringify({ ratings }),
  }) as Promise<{ recorded: unknown[]; aggregate_only: boolean }>;
}

// ---------------------------------------------------------------------------
// Battle buddy (F02 screen 7)
// ---------------------------------------------------------------------------

export type BuddyStateName = "ok" | "quiet" | "sos";

export type Buddy = {
  paired: boolean;
  pair_id?: string;
  my_state: BuddyStateName;
  empty_key?: string;
  helpline: string;
  buddy?: {
    pseudonym_id: string;
    unit_id: string | null;
    state: BuddyStateName;
    state_key: string;
  };
  sos?: { helpline: string; helpline_key: string; jco_key: string } | null;
};

export function getBuddy(): Promise<Buddy> {
  return apiFetch("/app/buddy") as Promise<Buddy>;
}

export function pairBuddy(buddyPseudonym: string): Promise<{ pair_id: string; paired: boolean }> {
  return apiFetch("/app/buddy/pair", {
    method: "POST",
    body: JSON.stringify({ buddy_pseudonym: buddyPseudonym }),
  }) as Promise<{ pair_id: string; paired: boolean }>;
}

export function unpairBuddy(): Promise<{ paired: boolean }> {
  return apiFetch("/app/buddy", { method: "DELETE" }) as Promise<{ paired: boolean }>;
}

export function setBuddyState(state: BuddyStateName): Promise<{ state: string; helpline: string }> {
  return apiFetch("/app/buddy/state", {
    method: "POST",
    body: JSON.stringify({ state }),
  }) as Promise<{ state: string; helpline: string }>;
}

// ---------------------------------------------------------------------------
// Notifications (break-glass told-you-at-the-time, buddy sos)
// ---------------------------------------------------------------------------

export type AppNotification = {
  id: string;
  kind: string;
  body_key: string;
  payload: Record<string, unknown> | null;
  created_at: string;
  read: boolean;
};

export function getNotifications(): Promise<{ notifications: AppNotification[] }> {
  return apiFetch("/app/notifications") as Promise<{ notifications: AppNotification[] }>;
}
