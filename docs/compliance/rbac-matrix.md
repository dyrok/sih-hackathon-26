# RBAC + ABAC Matrix — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> This matrix is the **target** access model. Which cells the Core API actually enforces on 2026-09-09 is recorded in §Enforcement status below and, control by control, in [security-model.md](security-model.md) §Verification status.

## Model

- **RBAC** maps role → capability. **ABAC** narrows it by attributes: `subject == principal` (own data), `unit(principal) == unit(subject)` (assignment), `case.assignee == principal` (caseload), `consent(subject).active == true` (consent gate on **voluntary data**, see DT-02 below), time-boxed session grants.
- Enforcement is server-side in the Core API at three layers: **route** (does this endpoint exist for this role at all), **service** (attribute conditions), **row** (which rows). The UI is never trusted; the commander dashboard defines **no individual-row pattern at all** ([design.md](../architecture/design/design.md) §4).
- Deny-by-default: every endpoint and every row is denied until granted, and denied attempts are audited.

### ABAC condition: caseload scoping

One helper carries this rule for every individual-data route, so it cannot drift between them: `backend/app/authz.py`. Role alone never authorises a subject read — the principal must have a **live reason** to see that person, and the reason is a case the engine raised (F06). Two guards, deliberately asymmetric:

| Guard | Applies to | Rule |
|---|---|---|
| `may_read_subject` / `assert_subject_scope` (`authz.py:48-84`) | **reads** — `GET /risk/{id}`, `/risk/{id}/explanation`, `/risk/{id}/trend`, `/signals/{id}` | counsellor: a `ResponseCase` exists for the subject and is assigned to them **or is still unassigned**; welfare officer: a case exists and its `unit_id` is in their `assigned_units`. No case at all → denied for everyone. |
| `assert_case_scope` (`authz.py:88-121`) | **writes** — `POST /interventions/{case_id}/actions`, `/outcome`, `/telemanas` | counsellor: the case must be assigned to them or unassigned; welfare officer: the case's unit must be in their `assigned_units`. Any other role: denied. |

Three properties worth stating because each was a bug before it was a rule:

1. **An unassigned case is readable, not writable.** Reading one is triage — it is a real work item that exists only because the engine raised it, and someone has to pick it up. Closing it, recording an outcome, or filing a Tele-MANAS referral against it is an intervention on another counsellor's subject, so the write guard refuses.
2. **An empty `assigned_units` means NO units, never all of them.** "Unset" must never read as "unrestricted"; that is how a scoping bug becomes a privacy incident.
3. **Every refusal is audited before it is raised.** `authz._deny` writes a `scope.deny` row with `denied=true` through `audit.write_deny`, which commits — a refusal that is rolled back with the request is not a record.

## Data types

| Code | Data type |
|---|---|
| DT-01 | Raw self-report / check-in (voluntary) |
| DT-02 | Derived risk score + 90-day trend |
| DT-03 | Case queue (pseudonymized) |
| DT-04 | Identity map (pseudonym → personnel no.) |
| DT-05 | Unit aggregates (k ≥ 5) |
| DT-06 | Consent artefacts |
| DT-07 | Audit log (append-only) |
| DT-08 | Session notes (counsellor records) |
| DT-09 | Who-viewed-my-data feed |
| DT-10 | Raw HR signals (leave, roster, deployment, transfers) |
| DT-11 | System config & role grants |

## Matrix (R = read · W = write · — = denied)

| Data type | Jawan | Counsellor | Welfare officer | Commander | Admin | Auditor |
|---|---|---|---|---|---|---|
| DT-01 Raw self-report | R/W own | — (derived evidence only) | — | — | — | — |
| DT-02 Score & trend | R own | R pseudonymized, **caseload-scoped** (see note) | R assigned units, post-unmask | — (aggregate only) | — | — |
| DT-03 Case queue | — | R own caseload | R assigned cases | — | — | — |
| DT-04 Identity map | — | via dual-key only | via dual-key only | — | — (never a keyholder) | events only |
| DT-05 Unit aggregates | R unit-pulse aggregate only | R | R | R own unit chain | — | — |
| DT-06 Consent artefacts | R/W own | R (gate check) | R | — | W (pipeline) | R |
| DT-07 Audit log | R own entries | — | — | — | W (append only) | R read-only |
| DT-08 Session notes | R on request | R/W own-written | R assigned | — | — | — (content-blind) |
| DT-09 Who-viewed feed | R own | — | — | — | — | — |
| DT-10 Raw HR signals | R own (roster app) | — | — | — | — (pipeline only) | — |
| DT-11 Config & grants | — | — | — | — | W (with approval) | R |

Notes on the surprising cells:

- **DT-02 is caseload-scoped, and consent gates the person's *data*, not the person.** This cell used to read "consent-gated", which is imprecise enough to be wrong, so state it exactly:
  - The **access** condition on `GET /risk/{id}` and `GET /signals/{id}` is the caseload rule above (`authz.assert_subject_scope`, called at `backend/app/api/routers/risk.py:57`, `:96`, `signals.py:48`, `counsellor.py:416`). Withdrawing consent does **not** make these routes 403.
  - The **consent** condition operates one layer down, inside the scorer: `has_voluntary_consent` (`backend/app/consent.py:23-33`) is read at `risk/scorer.py:143`, and when it is false the person's check-ins, instrument results, passive features and sleep baseline are all excluded from the score (`scorer.py:55-66`, `:145`, `:179-184`, `:219`). The HR-derived signals — duty streak, leave cancellations, circadian disruption — still score, because they were never voluntary disclosure.
  - **This is deliberate, and it is the whole point of FR-17.** FR-17 says "scoring excludes the person's **voluntary data**", not "excludes the person". Gating the derived score on consent would mean that withdrawing consent removes you from welfare routing — the person most likely to withdraw would become the person nobody is allowed to help, and withdrawal would carry a penalty. Consent controls what the model may learn from you; it does not control whether the system is allowed to notice that you have worked 60 days straight.
  - Consent *is* a hard precondition on **identity disclosure**: `POST /privacy/unmask` refuses without an active artefact (`privacy.py:86-97`). Break-glass is the stated exception (below).
- **Commander sees `—` on every individual surface.** That is not a cell in a table; it is the architectural firewall — no endpoint exists to serve them one ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).
- **Admin cannot read DT-01–DT-04.** Admins operate pipelines (expiry jobs, grants, backups) with no content access. The dual-key design requires this: no single technical role can unmask.
- **Auditor is content-blind** on DT-01/02/08: they see access events, purposes and outcomes, never the content — that is what makes the audit trustworthy to the jawan.

## Special rules

### Dual-key unmasking (FR-16)

1. Requires **two distinct human principals**: counsellor + welfare officer. One person holding both roles ≠ two keys. Admin can never be a keyholder.
2. Preconditions: active consent artefact (DT-06) and a reason string from the allowed purpose vocabulary.
3. The unmasked view is session-scoped and expires with the session.
4. Every event — grant **and** denial — lands in DT-07 and surfaces in the subject's DT-09 feed.

### k ≥ 5 aggregation (FR-14, [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md))

1. Enforced in the aggregation service, not the UI — a cell with fewer than 5 contributors never leaves the service.
2. **Complement suppression:** when a cell is suppressed, its complement in the same breakdown is suppressed too, to block subtraction inference.
3. Fixed cell definitions (unit × week) limit slice-and-dice re-identification; the commander role has no ad-hoc slicing API.
4. Removal events (withdrawal, expiry) re-check the k-floor before recomputation, so a deletion can never single out a contributor.

### Break-glass (NFR-08)

1. **Single-actor counsellor override** exists only for imminent-harm cases — waiting for a second key can be the costlier failure. It auto-notifies the subject (in-app) and the welfare officer, expires in 24 h, and lands in the oversight-board review queue.
2. Every other emergency read uses the dual-key path.
3. Admin can neither trigger nor approve break-glass.
4. Break-glass maps to the narrow public-safety exception in MHA 2017 §23(1) and the medical-emergency legitimate use in DPDP §7 — see [mental-healthcare-act-2017.md](mental-healthcare-act-2017.md) and [dpdp-2023-mapping.md](dpdp-2023-mapping.md).

### Silent consent withdrawal (FR-17)

1. Withdrawal writes to DT-06 and DT-07 only. No command-visible table or dashboard has a read path from the consent store — the schema makes the silent path the **only** path.
2. Scoring excludes the person's voluntary data from the next cycle; the erasure pipeline starts ([F08](../features/F08-privacy-safety-architecture.md) §data-lifecycle).

## Enforcement status (PRIV-003, 2026-09-09)

Verified by driving the Core API against the seeded demo fixture. Cases in [security-test-cases.md](../quality/security-test-cases.md); threat analysis in [threat-model.md](../quality/threat-model.md).

| Cell / rule | Enforced today? | Where |
|---|---|---|
| Commander `—` on every individual surface | **yes**, at three independent layers | middleware `backend/app/firewall.py:70-104`, handler `firewall.py:52-67`, trap route `backend/app/api/routers/privacy.py:405-421`. TC-426, TC-427, TC-430 |
| Commander `R own unit chain` on DT-05 | **yes** | `privacy.py:63-64` — but the guard is conditional on `user.unit_id` being set; a commander seeded without a unit is unscoped (same caveat applies to every route in the row below). TC-421 |
| Admin `—` on DT-01…DT-04 | **yes** | explicit deny `backend/app/api/routers/signals.py:46-47`; admin absent from every individual-read `require_roles`. TC-417 |
| Auditor content-blind on DT-01/02/08 | **yes** | `backend/app/api/routers/audit_api.py:29-40` returns no `reason`, `payload` or `subject_pseudonym_id`. TC-444 |
| **Counsellor DT-02 "R pseudonymized, consent-gated"** | **no — role check only** | `risk.py:49-83`, `counsellor.py:395-403` (`/risk/{id}/trend`) and `signals.py:39-67` authorize on role alone: verified that one counsellor read three unrelated pseudonyms. The consent gate that `privacy.py:86-97` already applies to unmask is absent here. TC-418, TC-419 · abuse case AC-4 |
| **Counsellor DT-03 "R own caseload"** | **yes on the newer routes, no on the older ones** | `_assert_assigned` (`backend/app/api/routers/counsellor.py:72-99`) enforces assignment and audits `case.deny` on `/interventions/case/{id}`, `/timeline` and `/notes`; the queue is filtered (`interventions.py:59-61`); the older per-case action / outcome / Tele-MANAS routes are still unguarded (`interventions.py:81-199`). Narrow gaps on the guarded path: an unassigned case and an empty `assigned_units` both fall open. TC-420, TC-420b |
| **Counsellor / welfare DT-08 "session notes"** | **yes** | `GET/POST /interventions/case/{case_id}/notes` (`counsellor.py:304-393`): assigned counsellor 200, welfare officer read-only (`counsellor.py:353` restricts POST to `counsellor`), commander 403 by middleware, auditor 403 — content-blindness holds. TC-420b |
| Commander DT-05 on the new dashboard surfaces | **yes** | `_guard_unit` (`commander.py:57-59`) and `_units` (`commander.py:62-67`) scope all seven aggregate routes; `/aggregates/units` returns only the caller's own unit for a commander. Same null-`unit_id` caveat as above. TC-421, TC-450b |
| Dual-key: two distinct principals, admin never a keyholder | **yes for one account per human** | `privacy.py:136-149`, `:161-174`, `:128`. TC-431, TC-433 — but see the two-accounts case, TC-432, which succeeds |
| Dual-key preconditions: active consent + purpose vocabulary | **yes** | `privacy.py:86-97`, `:30-36`. TC-434, TC-435 |
| Unmask session-scoped, expires | **yes (untested)** | `privacy.py:178`, `:204-205`. TC-436 |
| **k ≥ 5 with complement suppression** | **yes, as of 2026-09-09 ~02:20** (was "suppression yes, subtraction blocking no" at ~02:00) | `kanonymity.py` suppressed cells but then published `morale_index` / `elevated_share` from raw counts beside `n`, from which a suppressed cell was recoverable (TC-451, a red case on the [test-plan.md](../quality/test-plan.md) §4 gate). **Fixed:** both ratios are withheld whenever any cell is suppressed, the complement is chosen from all remaining tiers including zero-count ones, and `suppressed_keys` is replaced by a bare `suppressed_cells` count. Re-verified by execution; §4 gate GREEN. Residual: `n − Σ(published)` still reveals the combined size of the hidden tiers, not which tier. TC-451, TC-452 |
| Break-glass: single-actor, notifies subject + welfare, oversight queue | **yes** | `privacy.py:239-272`. TC-437 |
| Break-glass: "expires in 24 h" | **as a review window, not an access window** | identity is returned in the POST response; nothing re-checks `expires_at`. **No longer un-throttled** — a weekly cap now returns 429 and demands an explicit `acknowledge_oversight` past the cap (TC-438, fixed ~02:20). The window semantics are unchanged and still a documentation defect: TC-439 needs a policy decision, not a code change |
| Silent withdrawal: no command-visible read path from the consent store | **yes, structurally** | `backend/app/consent.py:36-47`; the aggregate reads only `identity_map` + `risk_score` (`kanonymity.py:12-23`). TC-448 |
| Consent gate on every voluntary-bundle write | **yes** | `app_data.py:57-58`, `:81-82`, `:109-110`. TC-445…447 |
| "Role changes require approval and are logged" | **no** | no router writes `User.role`; changes are direct DB writes with no approval path and no audit hook |
| Deny-by-default with denied attempts audited | **yes in the log**; **not in the subject's receipt** | `firewall.py:55-63`; who-viewed filters `denied` out (`privacy.py:362`). TC-459 |

## Change control

- Adding a role or widening a matrix cell requires: an ADR, an audit entry, and updated negative tests.
- Any change touching DT-04 or the commander surface re-runs the firewall tests before merge (AGENTS.md rule 8). "Reject the change" is the documented default.
