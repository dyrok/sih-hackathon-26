# F06 — Counsellor Console

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-12 in [prd.md](../product/prd.md) (consumes FR-09/FR-10 from [F05](F05-intervention-engine.md), FR-13, FR-16 from [F08](F08-privacy-safety-architecture.md)) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
The only surface where an individual risk score exists, and only as a consent-gated, pseudonymized clinical workbench: turn explainable alerts into interventions, verify the intervention worked, and — as a deliberate by-product — generate the labeled outcomes that make ML v2 possible ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)). Every identity disclosure is dual-key and logged, and the subject can see that it happened.

## User-visible behavior (screen by screen)
1. **Case queue.** Rows ranked by urgency × intervenability (FR-10 triage from F05), with a visible weekly cap and an explicit "cap reached — oldest Amber deferred to next week" state (alert fatigue kills these systems). Each row: pseudonym, care-state chip (leaf/sun/hand-heart per design.md §2 — never "risk red stamps"), top-3 factor chips ("47 consecutive duty days", "sleep −30%", "2 cancelled leaves") — never a single opaque number. Red cases carry a ≤ 24 h SLA clock (FR-09) that counts up, not down-shames.
2. **Case detail.** Full factor list with values, risk-trend chart (before/after intervention on one axis), ladder-transition timeline, intervention history. The person is a pseudonym + unit until unmask.
3. **Dual-key unmask.** Counsellor files a request with a reason code → welfare officer approves (second key) → identity resolves in-context, scoped to that case. Both keys, reason, and timestamps append to the immutable audit log (FR-16); the event surfaces in the jawan's who-viewed receipt (FR-15) within one sync cycle. Break-glass variant notifies the subject it happened (NFR-08). A half-unmasked state is impossible: keys resolve in one transaction.
4. **Session note.** Structured fields — date, modality (in-person / tele / Tele-MANAS), themes, risk re-estimate (0–100) — plus optional free text. Notes are confidential (MHA 2017 §23), autosaved as local drafts, and never exportable into any appraisal flow.
5. **Outcome tracker.** Pre/post monthly-instrument deltas (instruments from F02), ladder-state transitions, terminal outcome code: improved / unchanged / worsened / referred / resolved. This record is the ML label for v2 (ADR-0001).
6. **Tele-MANAS handoff.** Record a 14416 referral — reason, timestamp, follow-up status. The handoff is an intervention outcome recorded in the case timeline, not a data export (FR-13).

## Data model (fields, units, consent tags)
| Table | Key fields |
|---|---|
| `case` | `case_id`, `personnel_pseudonym`, `unit_id`, `ladder_state` (green/amber/red/critical), `opened_at`, `sla_deadline`, `status`, `assigned_counsellor` |
| `alert_factor` | `case_id`, `factor_key`, `value`, `human_string_i18n_key` (counsellor locale) |
| `session_note` | `note_id`, `case_id`, `session_at`, `modality`, `themes[]`, `risk_reestimate`, `free_text?` |
| `outcome` | `outcome_id`, `case_id`, `outcome_code`, `pre_score`, `post_score`, `measured_at`, `label_for_ml` (bool) |
| `unmask_request` | `request_id`, `case_id`, `counsellor_key_at?`, `welfare_key_at?`, `reason_code`, `expires_at` |

Reason codes for unmask (closed enum — free-form reasons are rejected):
| Code | Use |
|---|---|
| `red_outreach_24h` | Red-tier outreach inside the SLA window |
| `critical_contact` | Critical-tier immediate contact |
| `welfare_scheme_eligibility` | Family-welfare scheme check for the parivaar |
| `subject_request` | The jawan asked for contact through the app |

Consents: individual data is consent-gated at the query layer (FR-14); raw journal text additionally requires `checkin`-scope read consent (F08).

SLA and aging behavior (FR-09, FR-10):
- Red cases show an aging clock against the ≤ 24 h counsellor-contact target (PRD §4 metric).
- Cases aging past SLA surface at the top of the queue with a factual "overdue" marker — never alarm styling.
- The weekly cap defers new Amber alerts first, then oldest Ambers; Red/Critical are never deferred by the cap.
- Deferral reasons are recorded on the case, so "why didn't this get seen" is always answerable.

ML v2 label contract (ADR-0001): each closed case emits one label row — `pseudonym`, `features_snapshot_id` (frozen input features at flag time), `outcome_code`, `pre_score`, `post_score`, `label_for_ml`. Notes and free text are **not** label inputs; labels are structured only.

## API surface (endpoints, role-scoped)
Role `counsellor`, scoped to assigned cases; the welfare-officer role only reaches the approval endpoint.
- `GET /v1/counsellor/cases` — ranked queue + weekly-cap state
- `GET /v1/counsellor/cases/{case_id}` — evidence, trend, timeline (pseudonymized)
- `POST /v1/counsellor/cases/{case_id}/session-notes`
- `GET /v1/counsellor/cases/{case_id}/risk-trend`
- `POST /v1/counsellor/cases/{case_id}/outcomes`
- `POST /v1/counsellor/telemanas-handoffs`
- `POST /v1/counsellor/unmask-requests` · `POST /v1/welfare/unmask-requests/{id}/approve`
The server refuses any case the token is not assigned to, and refuses identity resolution without both keys — there is no single-key code path.

## States (idle/loading/empty/error/offline)
- **Empty queue:** honest copy, no celebration: "No open cases. Verify thresholds and participation before assuming all-clear" (`queue.empty.audit`).
- **Loading:** row skeletons; trend chart renders a span placeholder.
- **Error:** unmask approval failures are explicit and retryable; a failed transaction leaves no partial identity resolution.
- **Offline/LAN:** console runs on-prem (NFR-03); a brief outage shows a reconnect banner; in-progress notes autosave locally and sync on reconnect.
- **Cap reached:** new alerts queue for next week with the deferral reason visible — deferred ≠ dismissed (FR-10).

## Privacy notes (what this feature must never do)
- Never display or export an identity without both keys — tested, not asserted.
- Never leak case data toward command, ACR, posting, or appraisal flows; no endpoint serves data consumable by the commander role (ADR-0003 firewall).
- Never bulk-export named case lists — no CSV, no clipboard-friendly pseudonym+identity join table.
- Never treat non-participation or consent withdrawal as a case signal (FR-17).
- Raw self-report payloads expire at 90 days (FR-18); the console works on derived trends and notes after expiry, by design.
- Every case read is audit-logged and receipted to the subject (NFR-08) — including browsing reads.

## Out of scope / non-goals
ML triage (v1 ranking is the transparent F05 formula); chat/video tooling (Tele-MANAS 14416 is the channel); diagnosis or prescription recording beyond outcome codes; assigning workloads or roster edits (F05 proposes, welfare officer executes); viewing personnel without an open case — curiosity browsing is structurally impossible because cases exist only when the engine raises one.

## Definition of done
- [ ] Queue ranks by urgency × intervenability, enforces the weekly cap, and shows Red SLA clocks against the 24 h target (success metric in PRD §4).
- [ ] Dual-key unmask: unit test proves one key alone cannot resolve identity; every unlock appends to the immutable log and appears in the subject's receipt within one sync.
- [ ] Outcome records produce clean label rows (`pseudonym, features_snapshot_id, outcome_code, pre/post`) consumable by the v2 trainer.
- [ ] Risk-trend chart renders pre/post intervention deltas from F04 score history.
- [ ] Tele-MANAS handoff recorded and surfaced in the intervention timeline (FR-13).
- [ ] All case surfaces render factor chips with i18n'd factor strings — never a bare score; counsellor locale switchable `en`/`hi`.

## Links
[ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [F04](F04-risk-rules-engine.md) · [F05](F05-intervention-engine.md) · [F08](F08-privacy-safety-architecture.md) · [rbac-matrix.md](../compliance/rbac-matrix.md) · [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md) · [security-model.md](../compliance/security-model.md) · [design-client-apps.md](../architecture/design/design-client-apps.md)
