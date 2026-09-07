# F05 — Intervention Engine

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-09, FR-10, FR-11, FR-13 in [prd.md](../product/prd.md) · [Architecture](../architecture/architecture.md)

## Purpose

**Most teams stop at prediction; we don't.** An F04 flag matters only if something humane happens next — and most of what should happen is **structural, not psychiatric**: a roster change, a leave sanction, a buddy posting, a facilitated family visit. F05 owns the response ladder, capacity-aware triage, the workload rebalancing optimiser, and outcome recording that turns welfare work into ML v2 labels ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)).

## Behavior (pipeline / logic, step by step)

1. **Case creation** — F04 Amber+ flag opens a response case; one open case per person (dedupe window); FR-08 group events open one *group* case.
2. **Ladder assignment** — by tier, with masking floor and crisis-item overrides.
3. **Triage** — rank queue by **urgency × intervenability**, enforce per-counsellor weekly alert caps (FR-10); overflow defers, never silently drops.
4. **Action** — interventions dispatched per ladder rung; **non-clinical first** (catalogue below).
5. **SLA watch** — timers track each rung (Red = counsellor contact ≤ 24 h); F04 tier changes update the open case.
6. **Outcome** — action outcome + session outcome recorded via the counsellor console (F06); Tele-MANAS handoff recorded (FR-13); outcomes export as ML v2 label rows.

## Response ladder (FR-09)

| Tier | Trigger | Response | Actor | SLA |
|---|---|---|---|---|
| Green | score 0–39 | self-help nudge (content library; i18n `ladder.green.*`) | app, automated | — |
| Amber | 40–59, or masking flag | buddy check + **informal** JCO conversation — no paperwork, nothing attributable to the individual's file | buddy + JCO | 72 h |
| Red | 60–79, or masking floor | counsellor outreach | counsellor | **≤ 24 h** |
| Critical | 80+, crisis item, or Critical group event | immediate contact + duty modification | counsellor + welfare officer; on-call path after hours | immediate |

Ladder copy/icons/colours come from the design system's care states ([design.md](../architecture/design/design.md) §2) — care language, never alarm levels.

## Intervention catalogue (non-clinical first)

| ID | Intervention | Type | Ladder |
|---|---|---|---|
| INT-ROSTER | roster change / extra rest day | structural | Amber+ |
| INT-LEAVE | facilitate review of pending / repeatedly-cancelled leave | structural | Amber+ |
| INT-BUDDY | buddy posting / pairing | structural | Amber |
| INT-FAMILY | facilitated family visit or call facility | structural | Amber/Red |
| INT-COUNSEL | counsellor session | clinical | Red+ |
| INT-TELEMANAS | 14416 handoff | clinical | Red/Critical |
| INT-GROUP | unit psychoeducation + buddy-network activation after group exposure | group-level | group flag (FR-08) |

## Capacity-aware triage (FR-10)

`priority = w_u · urgency + w_i · intervenability` (weights in config; both normalised 0–1):

- **urgency** — tier base + SLA pressure (a Red nearing its 24 h breach rises);
- **intervenability** — counsellor slot availability, welfare-officer coverage of the unit, contactability (on duty / on leave / station known).

**Caps:** per-counsellor weekly alert budget + per-week unit cap (config). Cap reached → lower-priority alerts move to a deferral queue re-ranked daily; **Critical always preempts**. Rationale: *flagging 500 people with 3 counsellors is useless* — alert fatigue kills systems, so the queue must stay readable.

**Group safety valve:** a unit-level incident (FR-08) routes to one group case + INT-GROUP — never 500 individual Red alerts.

## Workload rebalancing optimiser (FR-11)

The same engine that detects overload proposes the fix.

- **Input:** current roster (F01 duty data), qualification matrix (rank/skill), leave + rest constraints, per-person load `f(consecutive duty days, night shifts, separation)` — welfare weights used *internally only*.
- **Objective (lexicographic):** 1) minimise max individual load; 2) minimise load variance; 3) minimise number of swaps (roster stability).
- **Constraints:** qualification match, minimum rest between shifts, existing leave, unit strength floors.
- **v1 = greedy assignment** (sort by load; reassign eligible shifts from the most-loaded to the least-loaded qualified person); v2 = constraint solver (CP-SAT).
- **Output: a proposal only** — roster diff + load delta. A human approves; no auto-execution.
- **Firewall-compliant surfaces (two modes):** `workload` mode (duty-load numbers only — operational data command already owns) may be shown to command; `welfare_weighted` mode (uses risk tiers internally) is visible **only** to welfare officer + counsellor. Welfare-motivated single-person duty modifications leave the system as a welfare officer's operational rest recommendation — **no score, tier, or factor attached**; logged; visible to the subject.

## Tele-MANAS handoff (FR-13)

- Handoff = facilitated call to **14416** (national tele-mental health) or supported self-referral. v1 **records** the referral; no Tele-MANAS API integration is claimed.
- Stored: referral timestamp, pseudonym, mode, outcome status (`referred → connected → completed / declined / unreachable`), counsellor pseudonym. **No clinical content** (NFR-02, MHA 2017 §23).
- Outcome closes the loop: `intervention_outcome` rows are the label source for ML v2 (ADR-0001).

## Data model

| Table | Key fields |
|---|---|
| `response_case` | id, pseudonym_id (null for group cases), score_id, tier, opened_at, closed_at, status (open/deferred/closed), group_case, incident_id |
| `triage_entry` | case_id, urgency, intervenability, priority, deferred_until, assigned_counsellor_pseudonym |
| `alert_budget_ledger` | counsellor_pseudonym, week, alerts_used, cap |
| `intervention_action` | id, case_id, catalogue_id, actor_role, initiated_at, due_at, status |
| `roster_swap_proposal` | id, unit_id, mode (workload/welfare_weighted), input_roster_version, proposed_swaps (JSON), max_load_before/after, status (proposed/approved/rejected/expired), approved_by_role |
| `telemanas_referral` | id, case_id, referred_at, mode, outcome_status, updated_at |
| `intervention_outcome` | id, case_id, action_id, outcome (improved/unchanged/worsened/declined/no_contact), recorded_by_role, recorded_at, label_exported |

## API surface (role-scoped)

| Endpoint | Method | Role | Notes |
|---|---|---|---|
| `/interventions/cases` | POST | internal (F04 event) | case creation |
| `/interventions/queue` | GET | counsellor (own queue, pseudonymized), welfare officer (assigned units) | triage-ranked |
| `/interventions/{case_id}/actions` | POST | counsellor, welfare officer | dispatch/record an action |
| `/interventions/{case_id}/outcome` | POST | counsellor, welfare officer | outcome enum only |
| `/interventions/{case_id}/telemanas` | POST | counsellor | referral record |
| `/roster/rebalance` | POST | welfare officer, roster admin | body includes `mode` |
| `/roster/rebalance/{id}` | GET | requester + commander (workload mode only) | welfare_weighted proposals 403 to commander |
| `/roster/rebalance/{id}/approve` | POST | commander (workload mode), welfare officer | operational authority on rosters |

Request sketch (`POST /roster/rebalance`): `{"unit_id": "3BN-C-D", "mode": "workload", "horizon_days": 14}` → response: `{"proposal_id", "swaps": [{"from": "...", "to": "...", "shift": "..."}], "max_load_before": 24, "max_load_after": 19, "infeasible_shifts": []}` (load units = duty-days; welfare fields absent by construction).

## Edge cases

- **Zero counsellor capacity** (leave/transfer) → queue defers with an explicit capacity-0 state; escalates to the next configured pool; SLA breach surfaces as a system-health alert, never hidden.
- **Cap reached mid-week** → deferral queue re-ranks daily; Critical preempts; nothing is silently dropped.
- **Duplicate flags, one person** → single open case; new scores update it instead of multiplying it.
- **Mass exposure (FR-08)** → group case path first; if many individuals are also individually Red, capacity mode leads with INT-GROUP.
- **Intervention declined** → recorded as declined; no punitive trace; re-offer cadence from config; declining never raises the score.
- **Critical out of hours** → on-call contact path; the SLA clock does not pause.
- **Infeasible rebalance** → engine returns best-effort + infeasibility reasons; it never emits an invalid roster.
- **Stale proposal** (roster edited meanwhile) → proposal expires, regenerate.
- **Consent withdrawn mid-case** → case continues as duty of care, but actions based on voluntary-signal data stop; F08 owns the consent state.

## Privacy notes (what this must never do)

- **No individual score, tier, or factor ever renders on a command-facing surface** (ADR-0003). Roster proposals carry workload numbers only.
- Amber's "informal JCO check" must not produce a written record attributable to the individual — binding constraint on F06 exports.
- Tele-MANAS referral stores logistics, never session content (MHA 2017 §23).
- Outcomes are the enum only; session notes live in F06 under consent rules.
- Every intervention on a person's record appears in their who-viewed-my-data timeline (FR-15 path).
- Alert budgets/deferral stats are aggregate system-health data — no individual content.

## Out of scope / non-goals

- Automatic roster execution — propose + human approve, always.
- Tele-MANAS API integration — v1 records the handoff; no API is claimed to exist.
- Clinical treatment or therapy content — counsellor console (F06) and Tele-MANAS deliver care; SAARTHI routes.
- Any punitive workflow — none exists; a PR adding one is rejected (AGENTS rule 8).
- Pay/compensation processing.

## Definition of done

- FR-09: all four rungs demonstrable; Red → contact ≤ 24 h enforced by SLA timer in the demo loop (architecture.md §6).
- FR-10: caps enforced in tests; deferral queue re-ranks daily; group-case path proven on a mass-exposure fixture.
- FR-11: greedy rebalance produces a valid roster on F09's synthetic 90-day data; diff + load delta shown; approval flow works.
- FR-13: Tele-MANAS referral recorded end-to-end with outcome status.
- `intervention_outcome` exports as documented ML v2 label rows.
- Automated test: zero welfare fields reachable from any command-facing route.

## Links

- [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) outcome labels · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) firewall · [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) adoption
- Related: [F04](F04-risk-rules-engine.md) (upstream flags) · [F01](F01-hr-signal-engine.md) (roster data) · [F06](F06-counsellor-console.md) (console) · [F08](F08-privacy-safety-architecture.md) (consent, audit) · [F09](F09-synthetic-data-generator.md) (data)
- Compliance: [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md) · [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md)
