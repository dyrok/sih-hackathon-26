# F01 — HR Signal Engine

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-01, FR-08 in [prd.md](../product/prd.md) · [Architecture](../architecture/architecture.md)

## Purpose

The **zero-effort layer — and deliberately the strongest engine**. HR data already exists (leave, roster, deployment, transfers); SAARTHI derives stress-relevant signals from it without the jawan doing anything. **The system works even if nobody ever opens the app.** Voluntary app data (F02/F03) enriches the picture; HR signals are the floor that exists for every person on the roster.

Framing rule: every signal below is existing organisational data read with a welfare lens. It is not new surveillance — it is a new *purpose* for records the force already keeps.

## Behavior (pipeline / logic, step by step)

1. **Ingest** — HRMS CSV import or service-account REST push for six datasets (leave, duty roster, deployment/posting, transfers, unit incidents, medical visits). Batch-idempotent.
2. **Pseudonymize** — `personnel_id → pseudonym_id` at the ingest boundary; no name ever enters the signal layer (F08 identity vault).
3. **Validate & stage** — schema check, natural-key dedupe; bad rows go to quarantine with a batch report. Never a partial write.
4. **Compute** — windowed signal functions (table below); each is a pure function of (records, window, config).
5. **Persist** — upsert `signal_snapshot` keyed (pseudonym_id, signal_key, window_end); group flags upsert keyed (unit_id, signal_key).
6. **Emit** — dirty pseudonym set ∪ incident-exposed units handed to F04 as a recompute event (events, never pushed scores).
7. **Audit** — every batch and every read logged append-only (NFR-08).

Engineering detail (pipeline stages, job model, recompute strategy): [design-hr-signal-engine.md](../architecture/design/design-hr-signal-engine.md).

## Data model (tables, fields, units)

| Table | Key fields | Notes |
|---|---|---|
| `hr_leave_record` | pseudonym_id, leave_type (enum from config), home_leave (bool), applied_at, sanctioned_from, sanctioned_to, cancelled_at, denial_reason, actual_return_date | natural key (pseudonym, applied_at, leave_type) |
| `hr_duty_roster` | pseudonym_id, unit_id, duty_date, shift_code (day/evening/night per config), rest_day (bool) | `rest_day` is explicit — a roster gap is not a rest day |
| `hr_deployment` | pseudonym_id, unit_id, posting_type (enum; `high_risk` flagged in config), start_date, end_date, distance_km | **derived** distance only — home address never stored |
| `hr_transfer` | pseudonym_id, from_unit, to_unit, effective_date, reason_code | |
| `hr_incident` | incident_id, unit_id, incident_type (casualty/riot/other per config), severity_band, incident_date, exposure_window_days | unit-scoped; feeds FR-08 group flags |
| `hr_medical` | pseudonym_id, visit_date, visit_type (sick_report/pt_excuse/injury), injury_flag | visit metadata only — no diagnosis text |
| `signal_snapshot` | pseudonym_id, signal_key, value, window_start, window_end, computed_at, engine_version, source_batch | the F04 input cache |
| `signal_group_flag` | unit_id, signal_key, value, incident_id, valid_from, valid_until | FR-08 exposure flags |
| `ingest_batch` | batch_id, source, dataset, rows_in, rows_quarantined, status, received_at | one row per import |

## API surface (role-scoped)

| Endpoint | Method | Role | Purpose |
|---|---|---|---|
| `/ingest/hr/csv?dataset=leave` | POST (multipart) | `hr_ingest` service account | bulk CSV import (FR-01) |
| `/ingest/hr/{dataset}` | POST (JSON array) | `hr_ingest` service account | push API per dataset |
| `/signals/{pseudonym_id}?window=90d` | GET | counsellor (pseudonymized), welfare officer (assigned cases) | signal evidence behind a case |
| `/signals/group/{unit_id}/exposure` | GET | internal (F04), welfare officer | active group flags |
| `/signals/recompute` | POST | admin / cron | full or dirty-set recompute |

**No commander-accessible endpoint exists.** The router layer rejects commander identity for any individual-data route (ADR-0003 firewall, automated test).

Request sketch (`POST /ingest/hr/leave`):

```json
{"batch_id": "hr-2026-09-05-01", "rows": [
  {"personnel_id": "CR-88231", "leave_type": "home_leave", "applied_at": "2026-08-12",
   "sanctioned_from": "2026-09-01", "sanctioned_to": "2026-09-14",
   "cancelled_at": "2026-08-28", "denial_reason": "op_commitment"}
]}
```

Response: `{batch_id, rows_in, rows_written, rows_quarantined, quarantine_report_url}`.

## Signal definitions (each signal: formula, unit, legal basis)

Windows default to trailing 90 days unless noted. All legal bases: DPDP Act 2023 **legitimate use (§7(i))** per NFR-01 / [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) — these are HR records processed for employment-welfare purposes.

| ID | Signal | Formula | Unit | Source |
|---|---|---|---|---|
| L1 | days_since_home_leave | today − max(end_date of completed home leave) | days | leave |
| L2 | leave_cancel_count | count(applied → cancelled) in window | count/90d | leave |
| L3 | leave_denial_count | count(denied applications) in window | count/90d | leave |
| L4 | early_return_days | Σ(sanctioned_days − actual_return_days) | days | leave |
| D1 | consecutive_duty_days | longest run of duty dates with no `rest_day`, ending at as_of | days | roster |
| D2 | night_shift_ratio | night shifts / total shifts (30d) | ratio 0–1 | roster |
| D3 | rotation_speed_direction | shift-code changes / week (30d); sign: forward (day→eve→night) vs backward | changes/week | roster |
| D4 | circadian_disruption_score | norm(night_ratio) × norm(rotation_speed) × direction_weight (backward weighted higher per shift-work literature; weight = config) | index 0–1 | roster |
| E1 | days_in_high_risk_posting | cumulative days in `high_risk` posting (window) | days | deployment |
| E2 | family_separation_index | distance_km × months_away (continuous months at current station) | km·months | deployment |
| E3 | deployment_count_12m | distinct deployments | count | deployment |
| C1 | transfer_count_12m | transfers in 12 months | count | transfer |
| C2 | promotion_board_pending | months since eligibility with board pending | months | transfer/HR |
| C3 | inquiry_court_pending | boolean + age of pending inquiry/court case | bool, days | transfer/HR |
| C4 | denied_training_count | denied course/training requests in 12 months | count | HR |
| T1 | unit_incident_exposure | whole unit roster at incident_date flagged within `exposure_window_days` | flag (unit-scoped) | incidents |
| T2 | days_since_unit_incident | today − incident_date | days | incidents |
| H1 | sick_report_freq | sick reports / 30d | rate | medical |
| H2 | pt_absence_unexplained | PT absences with no matching medical record (30d) | count | medical+roster |
| H3 | medical_visit_trend | slope of monthly visit rate | visits/month Δ | medical |
| H4 | days_since_injury | today − last recorded injury (null if none) | days | medical |

**Life events — GATED, feature-flag OFF** (legal position not settled; blocked behind **kv's compliance sign-off**; must not compute or display until signed off — see [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md)):

| ID | Signal | Source | Gate |
|---|---|---|---|
| V1 | bereavement (days since, HR family records) | HR | compliance review |
| V2 | marital_status_change (bool) | HR | compliance review |
| V3 | salary_advance_requests (count/90d) | pay records | compliance review |

This gives 20 active signals + 3 gated — clears FR-01's "15+".

## Edge cases

- **Missing home station** → E2 is null, never 0 (a silent 0 would zero out the index and hide the person).
- **Overlapping / conflicting leave records** → dedupe by natural key; conflicts quarantine, never auto-resolve.
- **Retroactive cancellation** (leave cancelled after sanction) → backdated record widens the dirty-window recompute.
- **Course/training attendance** → roster gaps are not rest days; only explicit `rest_day` counts.
- **Unit re-organisation** → group flags apply to roster membership at `incident_date`, not current membership.
- **Late-arriving incident records** → retroactive group flag triggers unit-wide recompute (FR-08 must still fire).
- **CSV re-imports** → idempotent via natural key + batch hash; duplicates are a no-op.
- **Date-only data, no timezone** → all arithmetic in unit-local calendar dates.
- **New joiner** → signals null, not zero (F04 cold-start handles baselines).

## Privacy notes (what this must never do)

- **No names**: pseudonym-only end to end; identity mapping lives in the F08 vault.
- **No commander path**: no route accepts a personnel ID with a commander role — enforced server-side, tested (ADR-0003).
- **Never join with ACR / appraisal / disciplinary data.** Architectural firewall — a PR that adds such a join is rejected (AGENTS rule 8).
- **Purpose limitation**: welfare only. Reusing a signal in promotion/posting decisions is a compliance violation, not a feature (NFR-01).
- **No home address** — only derived `distance_km` is stored.
- **No diagnosis text** — medical data is visit metadata only.
- **V1–V3 stay off** until compliance sign-off; the gate is in code, not a comment.
- Every read appears in the subject's who-viewed-my-data (F02/F08).

## Out of scope / non-goals

- Wearables / passive device signals → F03. Self-report and instruments → F02.
- Scoring, thresholds, masking → F04 (F01 delivers features only).
- Interventions / notifications → F05. Commander aggregation → F07/F08.
- Any HRMS *write* (sanctioning leave, editing rosters) — SAARTHI reads, never writes.
- ML over signals → v2 only (ADR-0001).

## Definition of done

- CSV + REST ingest for all six datasets; batch-idempotent; quarantine + report (FR-01).
- All 20 active signals implemented, unit-tested against fixtures, formulas matching this doc.
- Group trauma flag propagates to F04 for the exposed unit roster (FR-08 test case).
- F09's 1,000-person × 90-day synthetic dataset ingests and recomputes < 60 s on modest hardware (NFR-06).
- Demo persona's signal values match the scripted expectations (test-plan).
- Zero individual-data routes reachable with commander role (automated route-level test).
- Append-only audit on every read/write (NFR-08).

## Links

- [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) two-tier firewall · [ADR-0006](../architecture/decisions/0006-tech-stack.md) stack · [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) ML-later
- Engineering design: [design-hr-signal-engine.md](../architecture/design/design-hr-signal-engine.md)
- Consumers: [F04](F04-risk-rules-engine.md) (scoring) · [F05](F05-intervention-engine.md) (roster data for rebalancing)
- Related: [F08](F08-privacy-safety-architecture.md) (vault, audit) · [F09](F09-synthetic-data-generator.md) (demo feed) · [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) (legal basis)
