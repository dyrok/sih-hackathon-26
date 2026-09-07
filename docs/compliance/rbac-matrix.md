# RBAC + ABAC Matrix — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05

## Model

- **RBAC** maps role → capability. **ABAC** narrows it by attributes: `subject == principal` (own data), `unit(principal) == unit(subject)` (assignment), `case.assignee == principal` (caseload), `consent(subject).active == true` (consent gate), time-boxed session grants.
- Enforcement is server-side in the Core API at three layers: **route** (does this endpoint exist for this role at all), **service** (attribute conditions), **row** (which rows). The UI is never trusted; the commander dashboard defines **no individual-row pattern at all** ([design.md](../architecture/design/design.md) §4).
- Deny-by-default: every endpoint and every row is denied until granted, and denied attempts are audited.

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
| DT-02 Score & trend | R own | R pseudonymized, consent-gated | R assigned cases, post-unmask | — (aggregate only) | — | — |
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

## Change control

- Adding a role or widening a matrix cell requires: an ADR, an audit entry, and updated negative tests.
- Any change touching DT-04 or the commander surface re-runs the firewall tests before merge (AGENTS.md rule 8). "Reject the change" is the documented default.
