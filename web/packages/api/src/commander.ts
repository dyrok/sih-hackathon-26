import { apiFetch } from "./http";

/**
 * Commander client (F07) — aggregates only.
 *
 * Every path in this file is under `/aggregates` or `/me`, and not one function
 * takes a personnel or pseudonym identifier. There is no type in this module
 * that can hold an individual: `UnitCell`, `Morale`, `Indicators`, `Projection`
 * and `Forecast` are all unit-shaped. That is the F07 guarantee expressed in
 * the type system, on top of the server-side firewall.
 */

export type UnitCell = {
  unit_id: string;
  k: number;
  contributor_count: number | null;
  suppressed: boolean;
  elevated_share: number | null;
  label_key: string;
  reason_key: string | null;
};

export type UnitsOverview = {
  as_of: string;
  k: number;
  units: UnitCell[];
  stale_key: string;
};

export function getUnits(): Promise<UnitsOverview> {
  return apiFetch("/aggregates/units") as Promise<UnitsOverview>;
}

export type UnitAggregate = {
  unit_id: string;
  k: number;
  n: number | null;
  n_suppressed: boolean;
  cells: Record<string, { n: number | null; suppressed: boolean }>;
  elevated_share: number | null;
  morale_index: number | null;
  suppressed_keys: string[];
};

export function getUnitAggregate(unitId: string): Promise<UnitAggregate> {
  return apiFetch(`/aggregates/unit/${unitId}`) as Promise<UnitAggregate>;
}

export type MoraleComponent = {
  value: number | null;
  n: number | null;
  suppressed: boolean;
  label_key: string;
  facets?: string[];
};

export type Morale = {
  unit_id: string;
  week: string;
  k: number;
  score: number | null;
  suppressed: boolean;
  reason_key: string | null;
  computed_not_survey: boolean;
  components: Record<string, MoraleComponent>;
  formula_key: string;
};

export function getMorale(unitId: string): Promise<Morale> {
  return apiFetch(`/aggregates/unit/${unitId}/morale`) as Promise<Morale>;
}

export type IndicatorCell = {
  key: string;
  n?: number | null;
  value: number | Record<string, number | null> | null;
  buckets?: Record<string, number | null>;
  suppressed: boolean;
  reason_key?: string | null;
};

export type Indicators = {
  unit_id: string;
  as_of: string;
  k: number;
  contributor_count: number | null;
  leading: IndicatorCell[];
  lagging: IndicatorCell[];
  teaching_key: string;
};

export function getIndicators(unitId: string): Promise<Indicators> {
  return apiFetch(`/aggregates/unit/${unitId}/indicators`) as Promise<Indicators>;
}

export type PulseAggregate = {
  unit_id: string;
  period: string;
  k: number;
  contributor_count: number | null;
  suppressed: boolean;
  reason_key: string | null;
  facets: Record<string, { n: number | null; mean: number | null; suppressed: boolean }>;
};

export function getPulseAggregate(unitId: string, period?: string): Promise<PulseAggregate> {
  const q = period ? `?period=${encodeURIComponent(period)}` : "";
  return apiFetch(`/aggregates/unit/${unitId}/pulse${q}`) as Promise<PulseAggregate>;
}

export type TrendPoint = {
  week_end: string;
  n: number | null;
  elevated_share: number | null;
  suppressed: boolean;
};

export function getUnitTrend(unitId: string, weeks = 12): Promise<{ unit_id: string; k: number; points: TrendPoint[] }> {
  return apiFetch(`/aggregates/unit/${unitId}/trend?weeks=${weeks}`) as Promise<{
    unit_id: string;
    k: number;
    points: TrendPoint[];
  }>;
}

// ---------------------------------------------------------------------------
// What-if (F07 screen 4)
// ---------------------------------------------------------------------------

export type Lever = {
  unit: string;
  min: number;
  max: number;
  default: number;
  affects: string[];
  explain_key: string;
};

export function getLevers(): Promise<{ levers: Record<string, Lever> }> {
  return apiFetch("/aggregates/simulations/levers") as Promise<{ levers: Record<string, Lever> }>;
}

export type Projection = {
  fatigue_index_before: number;
  fatigue_index_after: number;
  fatigue_index_delta: number;
  fatigue_index_delta_pct: number | null;
  elevated_share_before: number;
  elevated_share_after: number;
  elevated_share_delta: number;
};

export type SimulationResult = {
  run_id: string;
  unit_id: string;
  suppressed: boolean;
  k: number;
  contributor_count: number | null;
  scenario: Record<string, number>;
  projection?: Projection;
  rule_deltas?: { rule_id: string; before: number; after: number; delta: number }[];
  assumption_snapshot: Record<string, unknown>;
  reason_key?: string;
};

export function runSimulation(
  unitId: string,
  scenario: Record<string, number>,
): Promise<SimulationResult> {
  return apiFetch("/aggregates/simulations", {
    method: "POST",
    body: JSON.stringify({ unit_id: unitId, scenario }),
  }) as Promise<SimulationResult>;
}

export type Forecast = {
  unit_id: string;
  suppressed: boolean;
  k: number;
  horizon_weeks?: number;
  contributor_count?: number | null;
  points?: { week: number; as_of: string; index: number; elevated_share: number }[];
  index_now?: number;
  index_horizon?: number;
  index_delta?: number;
  drivers?: { rule_id: string; before: number; after: number; delta: number }[];
  assumption_snapshot?: Record<string, unknown>;
  disclaimer_key?: string;
  reason_key?: string;
};

export function getForecast(unitId: string, horizonWeeks = 8): Promise<Forecast> {
  return apiFetch(`/aggregates/unit/${unitId}/forecast?horizon_weeks=${horizonWeeks}`) as Promise<Forecast>;
}

// ---------------------------------------------------------------------------
// The commander's own check-in (F07 screen 6, officer-first rollout)
// ---------------------------------------------------------------------------

export type OwnCheckIn = {
  as_of: string;
  checked_in_today: boolean;
  checkins: { date: string; mood_score: number | null }[];
  self_scope?: boolean;
};

export function getOwnCheckIns(days = 30): Promise<OwnCheckIn> {
  return apiFetch(`/me/checkins?days=${days}`) as Promise<OwnCheckIn>;
}

export function submitOwnCheckIn(body: {
  mood_label: string;
  mood_score: number;
  recorded_at: string;
}): Promise<{ status: string; self_scope: boolean }> {
  return apiFetch("/me/checkins", { method: "POST", body: JSON.stringify(body) }) as Promise<{
    status: string;
    self_scope: boolean;
  }>;
}

/** Officer's own duty log. Self-scope — no one else's rows, no unit score. */
export type Sitrep = {
  id: string;
  duty_date: string;
  transcript: string;
  work_summary: string;
  work_bullets: string[];
  tone_label: "calm" | "strained" | "flat" | string;
  mood_label: string;
  mood_score: number;
  wellness_summary: string;
  flags: string[];
  answers?: { id: string; answer: string }[] | null;
  duration_s?: number | null;
  pause_count?: number | null;
  pause_total?: number | null;
  heuristic: boolean;
  self_scope: boolean;
  questions?: string[];
};

export type SitrepList = {
  self_scope: boolean;
  as_of: string;
  sitreps: Sitrep[];
};

export function getOwnSitreps(days = 90): Promise<SitrepList> {
  return apiFetch(`/me/sitreps?days=${days}`) as Promise<SitrepList>;
}

export function submitOwnSitrep(body: {
  transcript: string;
  duration_s?: number;
  rms_mean?: number;
  rms_var?: number;
  pause_count?: number;
  pause_total?: number;
  answers?: { id: string; answer: string }[];
}): Promise<Sitrep> {
  return apiFetch("/me/sitreps", { method: "POST", body: JSON.stringify(body) }) as Promise<Sitrep>;
}
