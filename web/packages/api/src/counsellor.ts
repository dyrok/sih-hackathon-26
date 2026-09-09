import { apiFetch } from "./http";

/**
 * Counsellor / welfare-officer client (F06).
 *
 * Note what is absent: there is no "list personnel", no "search by name", no
 * bulk export. A case exists only because the engine raised one, so curiosity
 * browsing has no call to make. Identity resolution lives behind two keys and
 * appears in the subject's own receipt feed.
 */

export type CareTier = "green" | "amber" | "red" | "critical";

export type QueueRow = {
  case_id: string;
  pseudonym_id: string | null;
  tier: CareTier;
  status: string;
  group_case: boolean;
  priority: number;
  urgency: number;
  intervenability: number;
  deferred_until: string | null;
  cap_reason: string | null;
  sla_hours: number | null;
};

export function getQueue(): Promise<{ queue: QueueRow[] }> {
  return apiFetch("/interventions/queue") as Promise<{ queue: QueueRow[] }>;
}

export type Catalogue = {
  ladder: Record<string, { response: string; actor: string; sla_hours: number | null; catalogue: string[] }>;
  outcome_codes: string[];
  modalities: string[];
  unmask_reason_codes: Record<string, string>;
};

export function getCatalogue(): Promise<Catalogue> {
  return apiFetch("/interventions/catalogue") as Promise<Catalogue>;
}

export type Factor = {
  rule_id: string;
  domain: string;
  display_key: string;
  display_value: string | null;
  observed_value: string | null;
  weight: number;
};

export type CaseDetail = {
  case_id: string;
  pseudonym_id: string | null;
  unit_id: string | null;
  tier: CareTier;
  status: string;
  group_case: boolean;
  incident_id: string | null;
  opened_at: string;
  closed_at: string | null;
  sla_hours: number | null;
  hours_open: number;
  overdue: boolean;
  triage: {
    priority: number;
    urgency: number;
    intervenability: number;
    deferred_until: string | null;
    cap_reason: string | null;
  } | null;
  score: {
    score: number;
    tier: CareTier;
    confidence: string;
    sources_present: string[];
    engine_version: string;
    ruleset_version: number;
    as_of: string;
    hysteresis_held: boolean;
  } | null;
  masking: boolean;
  factors: Factor[];
  top_factors: { key: string; rule_id: string; value: string; text: string; weight: number }[];
  ladder: { response?: string; actor?: string; sla_hours?: number | null; catalogue?: string[] };
  disclaimer_key: string;
};

export function getCase(caseId: string): Promise<CaseDetail> {
  return apiFetch(`/interventions/case/${caseId}`) as Promise<CaseDetail>;
}

export type TimelineEvent = {
  at: string;
  kind: string;
  key: string;
  detail: Record<string, unknown>;
};

export function getTimeline(caseId: string): Promise<{ case_id: string; events: TimelineEvent[] }> {
  return apiFetch(`/interventions/case/${caseId}/timeline`) as Promise<{
    case_id: string;
    events: TimelineEvent[];
  }>;
}

export type SessionNote = {
  note_id: string;
  session_at: string;
  modality: string;
  themes: string[];
  risk_reestimate: number | null;
  free_text: string | null;
  free_text_withheld: boolean;
  own: boolean;
};

export function getNotes(
  caseId: string,
): Promise<{ case_id: string; notes: SessionNote[]; confidential_key: string }> {
  return apiFetch(`/interventions/case/${caseId}/notes`) as Promise<{
    case_id: string;
    notes: SessionNote[];
    confidential_key: string;
  }>;
}

export type NoteDraft = {
  session_at?: string;
  modality: "in_person" | "tele" | "telemanas";
  themes: string[];
  risk_reestimate?: number | null;
  free_text?: string | null;
};

export function addNote(caseId: string, draft: NoteDraft): Promise<{ note_id: string }> {
  return apiFetch(`/interventions/case/${caseId}/notes`, {
    method: "POST",
    body: JSON.stringify(draft),
  }) as Promise<{ note_id: string }>;
}

export type TrendPoint = { as_of: string; score: number; tier: CareTier; confidence: string };
export type TrendMarker = { at: string; kind: string; label_key: string; detail: string };

export function getRiskTrend(
  pseudonymId: string,
): Promise<{ pseudonym_id: string; points: TrendPoint[]; markers: TrendMarker[] }> {
  return apiFetch(`/risk/${pseudonymId}/trend`) as Promise<{
    pseudonym_id: string;
    points: TrendPoint[];
    markers: TrendMarker[];
  }>;
}

export function addAction(caseId: string, catalogueId: string): Promise<{ action_id: string }> {
  return apiFetch(`/interventions/${caseId}/actions`, {
    method: "POST",
    body: JSON.stringify({ catalogue_id: catalogueId }),
  }) as Promise<{ action_id: string }>;
}

export function recordOutcome(
  caseId: string,
  outcome: string,
  actionId?: string,
): Promise<{ outcome_id: string; label: Record<string, unknown> }> {
  return apiFetch(`/interventions/${caseId}/outcome`, {
    method: "POST",
    body: JSON.stringify({ outcome, action_id: actionId ?? null }),
  }) as Promise<{ outcome_id: string; label: Record<string, unknown> }>;
}

export function telemanasHandoff(
  caseId: string,
  mode: string,
  outcomeStatus = "referred",
): Promise<{ referral_id: string; outcome_status: string; clinical_content: null }> {
  return apiFetch(`/interventions/${caseId}/telemanas`, {
    method: "POST",
    body: JSON.stringify({ mode, outcome_status: outcomeStatus }),
  }) as Promise<{ referral_id: string; outcome_status: string; clinical_content: null }>;
}

// ---------------------------------------------------------------------------
// Dual-key unmask (F06 screen 3 / FR-16)
// ---------------------------------------------------------------------------

export type UnmaskReasonCode =
  | "red_outreach_24h"
  | "critical_contact"
  | "welfare_scheme_eligibility"
  | "subject_request";

export function requestUnmask(
  pseudonymId: string,
  reasonCode: UnmaskReasonCode,
  purpose = "case_review",
): Promise<{ request_id: string; status: string }> {
  return apiFetch("/privacy/unmask", {
    method: "POST",
    body: JSON.stringify({ pseudonym_id: pseudonymId, reason: reasonCode, purpose_string: purpose }),
  }) as Promise<{ request_id: string; status: string }>;
}

/** The second key. One principal supplying both is refused server-side. */
export function approveUnmask(
  requestId: string,
): Promise<{ request_id: string; status: string; expires_at: string | null }> {
  return apiFetch(`/privacy/unmask/${requestId}/approve`, { method: "POST", body: "{}" }) as Promise<{
    request_id: string;
    status: string;
    expires_at: string | null;
  }>;
}

export type Identity = {
  personnel_id: string;
  legal_name: string;
  rank: string;
  unit_id: string;
  session_expires_at: string;
};

export function readIdentity(requestId: string): Promise<Identity> {
  return apiFetch(`/privacy/unmask/${requestId}/identity`) as Promise<Identity>;
}

export function breakGlass(
  pseudonymId: string,
  reason: string,
): Promise<{
  break_glass_id: string;
  expires_at: string;
  notified_subject: boolean;
  notified_welfare: boolean;
  identity: { personnel_id: string | null; legal_name: string | null };
}> {
  return apiFetch("/privacy/break-glass", {
    method: "POST",
    body: JSON.stringify({ pseudonym_id: pseudonymId, reason }),
  }) as Promise<{
    break_glass_id: string;
    expires_at: string;
    notified_subject: boolean;
    notified_welfare: boolean;
    identity: { personnel_id: string | null; legal_name: string | null };
  }>;
}

export function proposeRebalance(
  unitId: string,
  mode: "workload" | "welfare_weighted" = "welfare_weighted",
): Promise<Record<string, unknown>> {
  return apiFetch("/roster/rebalance", {
    method: "POST",
    body: JSON.stringify({ unit_id: unitId, mode }),
  }) as Promise<Record<string, unknown>>;
}
