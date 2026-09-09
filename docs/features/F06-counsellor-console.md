# F06 — Counsellor Console

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Maps to: FR-12 in [prd.md](../product/prd.md) (consumes FR-09/FR-10 from [F05](F05-intervention-engine.md), FR-13, FR-16 from [F08](F08-privacy-safety-architecture.md)) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
The only surface where an individual risk score exists, and only as a consent-gated, pseudonymized clinical workbench: turn explainable alerts into interventions, verify the intervention worked, and — as a deliberate by-product — generate the labeled outcomes that make ML v2 possible ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)). Every identity disclosure is dual-key and logged, and the subject can see that it happened.

## User-visible behavior (screen by screen)
1. **Case queue.** Rows ranked by urgency × intervenability (FR-10 triage from F05), with a visible weekly cap and an explicit cap-reached state (`cons.queue.capReached`) — alert fatigue kills these systems. Each row: pseudonym, care-state chip (leaf/sun/hand-heart per design.md §2 — never "risk red stamps"), top-3 factor chips ("47 consecutive duty days", "sleep −30%", "2 cancelled leaves") — never a single opaque number. Red cases carry a ≤ 24 h SLA clock (FR-09) that counts up, not down-shames.
2. **Case detail.** Full factor list with values, risk-trend chart (before/after intervention on one axis), ladder-transition timeline, intervention history. The person is a pseudonym + unit until unmask.
3. **Dual-key unmask.** Counsellor files a request with a reason code → welfare officer approves (second key) → identity resolves in-context, scoped to that case. Both keys, reason, and timestamps append to the immutable audit log (FR-16); the event surfaces in the jawan's who-viewed receipt (FR-15) within one sync cycle. Break-glass variant notifies the subject it happened (NFR-08). A half-unmasked state is impossible: keys resolve in one transaction.
4. **Session note.** Structured fields — date, modality (in-person / tele / Tele-MANAS), themes, risk re-estimate (0–100) — plus optional free text. Notes are confidential (MHA 2017 §23), autosaved as local drafts, and never exportable into any appraisal flow.
5. **Outcome tracker.** Pre/post monthly-instrument deltas (instruments from F02), ladder-state transitions, terminal outcome code: improved / unchanged / worsened / declined / no_contact. This record is the ML label for v2 (ADR-0001).
6. **Tele-MANAS handoff.** Record a 14416 referral — reason, timestamp, follow-up status. The handoff is an intervention outcome recorded in the case timeline, not a data export (FR-13).

## Data model (fields, units, consent tags)
| Table | Key fields |
|---|---|
| `response_case` | `id`, `pseudonym_id`, `unit_id`, `tier` (green/amber/red/critical), `opened_at`, `sla_hours`, `status`, `group_case`, `incident_id`, `score_id` |
| `triage_entry` | `case_id`, `priority`, `urgency`, `intervenability`, `assigned_counsellor_id`, `deferred_until`, `cap_reason` |
| `risk_factor` | `score_id`, `rule_id`, `domain`, `display_key`, `display_value`, `observed_value`, `weight` |
| `session_note` | `id`, `case_id`, `author_user_id`, `session_at`, `modality`, `themes[]`, `risk_reestimate`, `free_text?`, `created_at` |
| `intervention_outcome` | `id`, `case_id`, `action_id?`, `outcome`, `recorded_by_role`, `recorded_at`, `label_exported` |
| `unmask_request` | `id`, `pseudonym_id`, `reason`, `purpose_string`, `counsellor_user_id?`, `welfare_user_id?`, `status`, `granted_at?`, `expires_at?` |
| `break_glass_event` | `id`, `counsellor_user_id`, `pseudonym_id`, `reason`, `opened_at`, `expires_at`, `notified_subject`, `notified_welfare`, `oversight_flag` |

(Shipped table names, from `backend/app/models.py`; the earlier draft named them `case` / `alert_factor` / `outcome`.)

Reason codes for unmask — a closed enum, served as data so the console never hardcodes it
(`UNMASK_REASON_CODES`, backend/app/api/routers/counsellor.py:50, returned by `GET /interventions/catalogue`):

| Code | i18n key | en | hi |
|---|---|---|---|
| `red_outreach_24h` | `cons.unmask.reason.red_outreach_24h` | Red-tier outreach inside the 24h window | Red-tier sampark 24 ghante ke andar |
| `critical_contact` | `cons.unmask.reason.critical_contact` | Critical-tier immediate contact | Critical-tier turant sampark |
| `welfare_scheme_eligibility` | `cons.unmask.reason.welfare_scheme_eligibility` | Family welfare scheme check | Parivaar kalyan yojana jaanch |
| `subject_request` | `cons.unmask.reason.subject_request` | The person asked for contact | Vyakti ne sampark maanga |

The console renders these four as a `<Select>` and sends the *code*, never a typed sentence
(`web/apps/counsellor/app/components/UnmaskPanel.tsx:97-101`). **Server-side the enum is not yet enforced:**
`POST /privacy/unmask` validates `purpose_string` against `PURPOSE_VOCAB` and returns 400 outside it
(backend/app/api/routers/privacy.py:89-90), but takes `reason` as an unvalidated string
(backend/app/api/routers/privacy.py:40-43). "Free text is refused" is therefore true of the UI and not yet
true of the API — open item, below.

Consents: individual data is consent-gated at the query layer (FR-14) — `POST /privacy/unmask` refuses with 403
and writes an `unmask.deny` audit row when `active_consent()` is false. Raw journal text additionally requires
`checkin`-scope read consent (F08).

SLA and aging behavior (FR-09, FR-10):
- Red cases show an aging clock against the ≤ 24 h counsellor-contact target (PRD §4 metric). `GET /interventions/case/{id}` returns `hours_open` and a computed `overdue` flag (counsellor.py:169-171); the clock itself is `components/SlaClock.tsx`, ticking client-side off `useNow`.
- Cases aging past SLA surface at the top of the queue with a factual "overdue" marker — never alarm styling.
- The weekly cap defers new Amber alerts first, then oldest Ambers; Red/Critical are never deferred by the cap.
- Deferral reasons are recorded on the case (`triage_entry.cap_reason`) and rendered on the row (`cons.queue.deferred`), so "why didn't this get seen" is always answerable.

### Session notes — the longest-lived clinical text in the system
`session_note` (backend/app/models.py:567-581) is where a counsellor's own words live. Four properties, each
checked against the code:

- **Confidential under MHCA 2017 §23.** Read back in full **only by their author**: `GET /interventions/case/{id}/notes` compares `n.author_user_id == user.id` and returns `free_text: null` with `free_text_withheld: true` for anyone else (counsellor.py:335-345).
- **An assigned welfare officer sees that a session happened, not what was said.** They get date, modality, themes and the risk re-estimate; the free text is withheld by the same author check. The console states this rather than hiding it: `cons.notes.readOnly` | "A welfare officer can see that a session happened, not write one." | "Kalyan adhikari dekh sakte hain ki session hua, likh nahi sakte." The case timeline likewise emits `has_free_text: true/false` and never the text (counsellor.py:276-284).
- **There is no export route.** The full route inventory (`grep -rn '@router\.' backend/app/api/routers/`) contains no notes export, no CSV, no bulk read; `POST .../notes` answers `{"exportable": false}`. The only CSV route in the whole API is the inbound `POST /ingest/hr/csv`.
- **Notes are excluded from the 90-day TTL by design.** `expire_raw` (backend/app/privacy/expiry.py) purges `CheckIn`, `InstrumentResult`, `PassiveFeature` and `VoiceFeature`. `SessionNote` is not in that list and no other job touches it, so a note written today is still readable, in full, by its author indefinitely. That makes it the longest-lived clinical text in SAARTHI — longer-lived than the raw self-report it was written about.

> **Open item for kv (F08 owns retention, FR-18).** Session-note retention is unspecified: not a documented
> exception, not a stated period, just an absence. F08 should decide and record one of (a) a clinical-record
> retention period with its legal basis, (b) an explicit "retained for the life of the case file" exception with
> the MHCA §23 argument written out, or (c) inclusion in a longer TTL. Until then this doc records the behaviour,
> not a justification for it. Related: note reads and writes are audited (`notes.read` / `notes.write`) but those
> two actions are **not** in the `/app/who-viewed` allow-list (backend/app/api/routers/privacy.py:417-427), so a
> note does not appear in the subject's receipt the way a case read (`risk.read`) does. That is arguably correct
> under §23 confidentiality and arguably a gap under FR-15 — F08's call, not this doc's.

ML v2 label contract (ADR-0001): each closed case emits one label row — `pseudonym_id`, `outcome`, `tier_at_open`,
`exported` (the shape returned by `POST /interventions/{case_id}/outcome`). Notes and free text are **not** label
inputs; labels are structured only.

## API surface (endpoints, role-scoped)
Roles `counsellor` and `welfare_officer`. A commander token is refused twice on every route below: once by the
ADR-0003 middleware on the `/interventions`, `/risk` and `/privacy/unmask` prefixes
(`COMMANDER_DENIED_PREFIXES`, backend/app/firewall.py:17-30), and again by `forbid_commander()` in the handler.

**Console-owned** — `backend/app/api/routers/counsellor.py`:

| Route | Line | Guards after role check | Refusal |
|---|---|---|---|
| `GET /interventions/catalogue` | :125 | role only | 403 (wrong role / commander) |
| `GET /interventions/case/{case_id}` | :138 | `forbid_commander` → `_case_or_404` → `_assert_assigned` | 404 `case not found`; 403 `case is assigned to another counsellor` / `case is outside your assigned units`, each with a `case.deny` audit row |
| `GET /interventions/case/{case_id}/timeline` | :228 | same three | same |
| `GET /interventions/case/{case_id}/notes` | :316 | same three, then per-note author filter | same; free text withheld rather than refused |
| `POST /interventions/case/{case_id}/notes` | :360 | `require_roles("counsellor")` (welfare officers cannot write), `forbid_commander`, modality enum, `_assert_assigned` | 400 `modality must be one of …`; 400 on a non-ISO `session_at`; 403/404 as above |
| `GET /risk/{pseudonym_id}/trend` | :407 | `forbid_commander` → **`authz.assert_subject_scope`** | 403 `no case assigns this subject to you (subject is not on this principal's caseload)` + `scope.deny` audit row; 404 `no score history` |

**Also called by the console, owned elsewhere:**

| Route | File:line | Guard |
|---|---|---|
| `GET /interventions/queue` | interventions.py:50 | caseload filter inside the handler (skips rows, does not 403) |
| `POST /interventions/{case_id}/actions` | interventions.py:85 | `authz.assert_case_scope` |
| `POST /interventions/{case_id}/outcome` | interventions.py:124 | `authz.assert_case_scope`; outcome enum → 400 |
| `POST /interventions/{case_id}/telemanas` | interventions.py:177 | `require_roles("counsellor")` + `authz.assert_case_scope` |
| `POST /privacy/unmask` | privacy.py:82 | purpose vocabulary + `active_consent` → 403 + `unmask.deny` |
| `POST /privacy/unmask/{request_id}/approve` | privacy.py:129 | two distinct principals → 403; a key already held by someone else → 409 |
| `GET /privacy/unmask/{request_id}/identity` | privacy.py:198 | grant must exist, be unexpired, and the caller must be one of the two keyholders → 403 `no active unmask grant` / `not a keyholder on this grant` |
| `POST /privacy/break-glass` | privacy.py:235 | `require_roles("counsellor")`; weekly cap → 429 |

There is no "list personnel" route, no search-by-name, no bulk export: `web/packages/api/src/counsellor.ts`
has no function that takes a name, and the server has no route that accepts one. The identity resolution path
(`/privacy/unmask/{id}/identity`) is the only place `legal_name` leaves the database for this role, and it needs
two distinct human principals plus an unexpired grant.

## Caseload scoping (the fix that made "curiosity browsing is structurally impossible" true)
Until 2026-09-09 that sentence was an *assertion*. The queue was filtered by caseload
(interventions.py:58-66) but the item routes were not, so any counsellor holding a `case_id` or a
`pseudonym_id` could open another counsellor's case, read the risk trend, add an action and record the outcome
that closed it. That is the classic IDOR shape and it was found as TC-418/419/420/420b.

It is now enforced in one shared module, `backend/app/authz.py`, deliberately used by `/risk`, `/signals` and
every `/interventions` item route so the rule cannot drift between them:

- **Read — `may_read_subject` / `assert_subject_scope`** (authz.py:50, :78). A **counsellor** may read a subject who has at least one case that is assigned to them **or still unassigned** — the shared pool the engine raised. An unassigned case is a real work item, not a browsing hole: it exists only because a rule fired. A **welfare officer** may read a subject only if one of their cases sits in a unit on `user.assigned_units`. A subject with **no case at all** is unreadable by everyone: `_cases_for` returns empty and the function returns `False` before any role branch.
- **Write — `assert_case_scope`** (authz.py:90). Scoped to the *specific case*, not to the subject: a counsellor is refused a case whose `triage_entry.assigned_counsellor_id` is another counsellor, and a welfare officer is refused a case outside `assigned_units`. Note the exact boundary, because it is narrower than "only your own": an **unassigned** case can still be acted on by any counsellor (`assignee not in (None, user.id)` is the deny condition, authz.py:99). Picking up an unclaimed case is the intended workflow; taking one off a named colleague is not.
- **An empty `assigned_units` means NO units** — never all of them (authz.py:71-73, and the same rule restated in counsellor.py:96-101 and interventions.py:63-66). "Unset" widening into "unrestricted" is exactly how a scoping bug becomes a privacy incident, so the empty list is written out explicitly at all three sites and covered by `test_tc420b_empty_assigned_units_means_none_not_all`.
- **Every refusal is audited and the audit survives the refusal.** `_deny` calls `audit.write_deny` (which commits in its own transaction, so a rolled-back request no longer discards its own denial record) and then raises 403. Refused reads land as `scope.deny`, refused case opens as `case.deny`, commander hits as `firewall.deny`.

Regression cover: `backend/tests/test_security_hardening.py::test_tc418_tc419_counsellor_cannot_browse_an_unrelated_subject`,
`::test_tc418_the_assigned_subject_is_still_readable`, `::test_tc418_a_refused_browse_is_audited`,
`::test_tc420_a_counsellor_cannot_act_on_another_counsellors_case`, `::test_tc420b_empty_assigned_units_means_none_not_all`,
plus `test_rbac_enforcement.py::test_abac_counsellor_cannot_open_another_counsellors_case` and
`::test_abac_welfare_officer_confined_to_assigned_units`. `authz.py` measures 98% line coverage
([coverage-report.md](../quality/coverage-report.md) §3).

## States (idle/loading/empty/error/offline)
- **Empty queue:** honest copy, no celebration — `queue.empty.audit` | "No open cases. Verify thresholds and participation before assuming all-clear." | "Koi khula case nahi. Sab theek maanne se pehle thresholds aur bhagidari jaanchein."
- **Loading:** row skeletons; the trend chart renders a span placeholder. Queue rows fetch their factor chips three at a time and fill in as evidence arrives (`components/QueueRail.tsx:30-70`).
- **Error:** unmask approval failures are explicit and retryable (403 → `cons.unmask.denied`, 409 → `cons.unmask.keyTaken`); a failed transaction leaves no partial identity resolution. A queue row whose detail will not load keeps its tier and clock rather than disappearing.
- **Offline/LAN:** console runs on-prem (NFR-03); a brief outage shows `ReconnectBanner`; in-progress notes autosave to `localStorage` on every keystroke and are restored on return (`cons.notes.draftRestored` | "An unsent draft from this computer was restored." | "Is computer se ek bina bheja draft wapas laaya gaya.").
- **Cap reached:** `cons.queue.capReached` | "Cap reached — oldest Amber deferred to next week. Deferred is not dismissed." | "Seema poori — sabse purana Amber agle hafte. Taala gaya matlab band nahi."

## Privacy notes (what this feature must never do)
- Never display or export an identity without both keys — tested, not asserted (`test_privacy.py::test_dual_key_requires_two_distinct_principals` asserts 403 on the counsellor's own read before the second key, 200 after, and that the subject's receipt feed carries the event).
- **Caseload scoping is enforced, not asserted.** See the section above: a counsellor's reach is the set of cases the engine raised and left unclaimed or assigned to them; a welfare officer's is `assigned_units`, and an empty list means none. Refusals are 403 with a `scope.deny` / `case.deny` audit row.
- Never leak case data toward command, ACR, posting, or appraisal flows; no endpoint serves data consumable by the commander role (ADR-0003 firewall — middleware plus per-handler `forbid_commander`).
- Never bulk-export named case lists — no CSV, no clipboard-friendly pseudonym+identity join table, and no notes export.
- Never treat non-participation or consent withdrawal as a case signal (FR-17).
- Raw self-report payloads expire at 90 days (FR-18); the console works on derived trends and notes after expiry, by design. Session notes are **not** covered by that job — see the open item above.
- Every case read is audit-logged and receipted to the subject (NFR-08) — including browsing reads. `GET /interventions/case/{id}` writes `risk.read`, which is in the `/app/who-viewed` allow-list, so opening a queue row to read its factor chips is visible to the person it is about.

### Unmask and break-glass
- **Dual key = two people.** `approve_unmask` refuses when the second key would come from the principal who supplied the first (403 `two distinct human principals required`, with a `unmask.deny` audit row), and `admin` is not a keyholder role at all. A grant expires after `unmask_session_hours` (default 8).
- **Break-glass stays reachable.** It is never hard-blocked — waiting for a second key can be the costlier failure when harm is imminent — but it is no longer the cheap path. `settings.break_glass_weekly_cap` (default **3**) counts a counsellor's own events in the trailing 7 days. At or above the cap the request is refused **429** unless it carries *both* `acknowledge_oversight: true` and a reason of at least 20 characters; the refusal itself is audited as `break_glass.throttled` with `{used, cap}` (privacy.py:251-279). Below the cap one welfare officer is notified; above it, **every** welfare officer is (privacy.py:301-303). The subject is notified in both cases, and the grant expires after `break_glass_hours` (default 24). Cover: `test_security_hardening.py::test_tc438_break_glass_is_capped_then_demands_oversight`, `::test_tc438_the_throttle_is_audited`.
- The console surfaces the cap honestly rather than retrying: `cons.breakglass.capped` | "The weekly emergency-access limit is reached. Use the two-key path, or ask welfare oversight." | "Saptahik aapatkalin pahunch ki seema poori ho gayi. Do-chaabi raasta lein, ya kalyan nigrani se poochhein."

## Out of scope / non-goals
ML triage (v1 ranking is the transparent F05 formula); chat/video tooling (Tele-MANAS 14416 is the channel); diagnosis or prescription recording beyond outcome codes; assigning workloads or roster edits (F05 proposes, welfare officer executes); viewing personnel without an open case — curiosity browsing is structurally impossible because cases exist only when the engine raises one, **and because `authz.py` now checks that on every individual route rather than only on the queue**.

## Implementation status (as of 2026-09-09)
Backend router `backend/app/api/routers/counsellor.py`; app `web/apps/counsellor` (Next.js, bun workspace).

| # | Screen | Shipped as | Routes it calls | Status |
|---|---|---|---|---|
| 1 | Case queue | `app/components/QueueRail.tsx` (master rail, always visible) + `(console)/(workbench)/page.tsx` | `GET /interventions/queue`, then `GET /interventions/case/{id}` per row for factor chips | **done** — ranking, SLA clock, deferral reason, cap banner |
| 2 | Case detail | `(console)/(workbench)/case/[id]/page.tsx` + `layout.tsx` | `GET /interventions/case/{id}`, `.../timeline`, `GET /risk/{pid}/trend`, `GET /interventions/catalogue` | **done** — evidence card, factor chips, `RiskTrendChart` with intervention markers, timeline, ladder actions |
| 3 | Dual-key unmask | `app/components/UnmaskPanel.tsx` | `POST /privacy/unmask`, `.../approve`, `GET .../identity`, `POST /privacy/break-glass` | **done** — reason code from the catalogue, pending state, second-key hint, break-glass behind a `ConfirmDialog` |
| 4 | Session note | `(console)/(workbench)/case/[id]/notes/page.tsx` | `GET`/`POST /interventions/case/{id}/notes` | **done** — modality, themes, re-estimate slider, free text, localStorage draft, withheld-content rendering |
| 5 | Outcome tracker | `(console)/(workbench)/case/[id]/outcomes/page.tsx` | `GET /interventions/catalogue`, `POST /interventions/{id}/outcome` | **partial** — terminal outcome code and the ML label row ship; **pre/post instrument deltas are not rendered on this screen** |
| 6 | Tele-MANAS handoff | `(console)/telemanas/page.tsx` | `GET /interventions/queue`, `POST /interventions/{id}/telemanas` | **done** — mode picker, timeline row, deep link back to the case |

Known gaps, stated rather than rounded away:

- **Server-side unmask reason enum.** `POST /privacy/unmask` does not validate `reason` against `UNMASK_REASON_CODES`. The closed enum is a UI constraint today. Not implemented as of 2026-09-09.
- **Above-cap break-glass is unreachable from the console.** `web/packages/api/src/counsellor.ts:229-249` never sends `acknowledge_oversight`, so past the weekly cap the console can only show `cons.breakglass.capped` and point at the dual-key path. The oversight-acknowledged path exists and is tested at the API, but has no UI. Not implemented as of 2026-09-09.
- **Pre/post instrument deltas** (screen 5's "outcome tracker" half) are not built; there is no route serving a paired instrument delta for a case.
- **Backend `disclaimer_key: "instr.not_diagnosis"`** is returned by `/interventions/case/{id}` and `/risk/{id}/trend` but has no entry in `packages/i18n/src/en.json` or `hi.json`; the console renders `screen.disclaimer` instead. Cosmetic, but it is a key the API promises and the bundle cannot resolve.
- **No per-router coverage figure** for `counsellor.py` is recorded in [coverage-report.md](../quality/coverage-report.md); the gates it does report that bear on this feature are `authz.py` 98% and backend overall 90%.

## Definition of done
- [x] Queue ranks by urgency × intervenability, enforces the weekly cap, and shows Red SLA clocks against the 24 h target (success metric in PRD §4). — `interventions/triage.py` ranking + `QueueRail`/`SlaClock`; `test_interventions.py` covers queue and triage caps.
- [x] Dual-key unmask: test proves one key alone cannot resolve identity; every unlock appends to the immutable log and appears in the subject's receipt. — `test_privacy.py::test_dual_key_requires_two_distinct_principals` (403 before the second key, `unmask.grant` / `identity.read` in `/app/who-viewed` after).
- [x] Caseload scoping enforced on every individual route, not only the queue. — `backend/app/authz.py`, TC-418/419/420/420b regression tests, 98% coverage.
- [~] Outcome records produce clean label rows consumable by the v2 trainer. — the row ships (`pseudonym_id`, `outcome`, `tier_at_open`, `exported`); `features_snapshot_id` and `pre_score`/`post_score` are **not** part of it.
- [x] Risk-trend chart renders pre/post intervention deltas from F04 score history. — `GET /risk/{pid}/trend` returns points + action/outcome markers; `components/RiskTrendChart.tsx`.
- [x] Tele-MANAS handoff recorded and surfaced in the intervention timeline (FR-13). — `POST /interventions/{id}/telemanas` → `timeline.telemanas` event; response carries `clinical_content: null`.
- [x] All case surfaces render factor chips with i18n'd factor strings — never a bare score; counsellor locale switchable `en`/`hi`. — enforced in CI by `web/scripts/lint-boundaries.mjs` rules 5–7 (no literal JSX text, en/hi parity, every `t()` key resolves).
- [ ] Session-note retention has a stated basis. — open item for kv / F08; notes currently have no TTL.
- [ ] The unmask reason enum is enforced server-side. — client-side only today.

## Links
[ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [F04](F04-risk-rules-engine.md) · [F05](F05-intervention-engine.md) · [F08](F08-privacy-safety-architecture.md) · [rbac-matrix.md](../compliance/rbac-matrix.md) · [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md) · [security-model.md](../compliance/security-model.md) · [security-test-cases.md](../quality/security-test-cases.md) · [coverage-report.md](../quality/coverage-report.md) · [design-client-apps.md](../architecture/design/design-client-apps.md)
