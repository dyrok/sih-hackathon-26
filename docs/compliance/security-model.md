# Security Model — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> This document states the security **design**. What the code actually enforces on 2026-09-09 is recorded per control in §Verification status below, with the full boundary-by-boundary analysis in [threat-model.md](../quality/threat-model.md) and the executable cases in [security-test-cases.md](../quality/security-test-cases.md).

## Assets & trust boundaries

| Asset | Why it matters |
|---|---|
| Identity map (pseudonym → personnel no.) | The single most sensitive table; dual-key access only |
| Raw self-reports / check-ins | Voluntary disclosure — one leak ends the programme |
| Derived scores & trends | Firewalled from command ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)) |
| Session notes | MHA §23-standard confidentiality floor ([mental-healthcare-act-2017.md](mental-healthcare-act-2017.md)) |
| Consent artefacts | The legal defensibility of every disclosure |
| Audit log | The tamper-evidence everything else leans on |

Trust boundaries: (1) the jawan device, (2) the on-prem / MeghRaj deployment perimeter, (3) the Core API service boundary where RBAC + ABAC are enforced. Nothing outside boundary (2) is trusted to hold personnel data.

## Deployment & data localisation

- **On-prem or NIC MeghRaj.** All personnel data lives in CRPF infrastructure or the Government of India cloud (MeghRaj). No third-party cloud, no SaaS dependency for data — AI inference included.
- **Air-gapped mode** for sensitive units: no outbound connectivity; updates arrive as signed offline bundles; the offline-first queue ([ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md)) makes this survivable rather than blocking.
- Stricter than the statute: DPDP §16 permits cross-border transfer subject to Central-Government restrictions — we localise by design. This is a trust decision, not a legal minimum.
- Retention copies and disaster-recovery stay inside the same perimeter; no offsite vendor without DPO approval.

## Threat model — STRIDE-lite

| STRIDE | Threat / vector | Asset at risk | Control | Link |
|---|---|---|---|---|
| **S**poofing | Stolen or shared counsellor / commander credentials | Case queue, aggregates | MFA + short-lived sessions + device binding; every action binds to a principal in the audit log | [rbac-matrix.md](rbac-matrix.md) |
| **T**ampering | Insider edits a score, a consent row, or the audit log | Scores, audit | Append-only hash-chained audit; DB grants deny UPDATE/DELETE to the application role; scores versioned with engine build id | [F08](../features/F08-privacy-safety-architecture.md) |
| **R**epudiation | "I never opened that record" | Accountability | Every read logged with its purpose string; subject-visible who-viewed feed; hash chain makes log edits detectable | [F08](../features/F08-privacy-safety-architecture.md) |
| **I**nfo disclosure | Commander endpoint leaks an individual; DB dump; transit interception | Everything | Route-level firewall — no commander endpoint accepts a personnel ID for welfare data; k ≥ 5 suppression server-side; pseudonymization; TLS 1.3; AES-256 at rest | [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) |
| **D**enial of service | Network loss; endpoint outage | Check-in continuity | Offline-first SQLite queue (data survives); API rate limiting + backpressure; degraded service over lost data | [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) |
| **E**levation of privilege | Admin self-grants counsellor role; dual-key collusion | Identity map | Role changes require approval and are logged; dual-key requires two distinct principals; admin barred from keyholding and break-glass | [rbac-matrix.md](rbac-matrix.md) |

The STRIDE-lite table above is the design summary. The full walkthrough — six trust boundaries, a data-flow diagram, the THR-01…THR-44 register with a `file:line` citation for every control, seven attacker profiles, the four "turned into a discipline tool" abuse cases, and the explicit v1 non-defences — is [threat-model.md](../quality/threat-model.md) (PRIV-003).

## Cryptography & data protection

- **In transit:** TLS 1.3 (1.2 minimum, modern ciphers only); certificate pinning in the jawan app.
- **At rest:** AES-256 (GCM); envelope encryption for the sensitive columns (raw self-reports, session notes, identity map); keys in an on-prem KMS/HSM with documented rotation; air-gap mode uses a local KMS.
- **Pseudonymization:** analytics see surrogate UUIDs only; the identity map is a separately restricted table ([rbac-matrix.md](rbac-matrix.md)).
- **On-device:** raw audio is never persisted anywhere — not even on the phone; only the feature vector leaves it ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)); the offline SQLite queue is encrypted with a device key.
- **Audit log:** append-only with hash chaining; the verification job fails closed — a broken chain locks writes, it does not silence alerts.

## Logging taxonomy (what the audit log records)

| Event | Subject-visible in who-viewed | Notes |
|---|---|---|
| Read of individual record (consent-gated) | yes — role, when, why, duration | the receipt's core entry |
| Dual-key unmask grant / denial | yes | both keys named by role; denials logged like grants |
| Break-glass read | yes — immediately | subject + welfare officer notified |
| Consent granted / withdrawn | own panel only | silent withdrawal: nothing command-visible |
| Erasure run after withdrawal | no (command surfaces) | auditor-visible only |
| Denied access attempt | aggregate pattern only | denies are logged with the same rigour as reads |
| Admin pipeline action (expiry, grants, backups) | no | auditor-visible |
| Aggregation cell suppression | no | k-floor re-check recorded |

## Access control

RBAC + ABAC enforced **server-side** in the Core API; the UI is never trusted. Full role × data matrix, dual-key rules, k ≥ 5 rules and the break-glass protocol: [rbac-matrix.md](rbac-matrix.md). Firewall rationale: [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md).

## Demo & evaluation environment

- Demo / evaluation runs on synthetic data only ([F09](../features/F09-synthetic-data-generator.md)); no live personnel record ever leaves the production perimeter. MHA/evaluator sees the demo environment and the audit architecture ([PRD](../product/prd.md) §1).
- Notifications never leak state: a push must never say anything like "the counsellor flagged you" — strings are lock-screen safe and go through the i18n keys in [F08](../features/F08-privacy-safety-architecture.md).

## Operational hygiene

- Quarterly access review: role grants vs duty roster; orphan accounts disabled on transfer or retirement (HR-driven hook via [F01](../features/F01-hr-signal-engine.md)).
- Secrets never in code; short-lived KMS-issued credentials for service-to-service calls.
- Backups encrypted under the same AES-256 regime; a restore drill runs before the demo.
- Air-gap patching: signed offline bundles on a fixed cadence (parameter, pilot decides).

## Breach response

- **Trigger & clock:** a personal data breach must be notified to the Data Protection Board and each affected Data Principal (DPDP §8(4)); the 72-hour operational window comes from the DPDP Rules (draft 2025) — confirm against the final rules ([dpdp-2023-mapping.md](dpdp-2023-mapping.md) row 6).
- **Runbook:** `docs/quality/incident-response.md` (to be authored). This doc fixes what that runbook must encode: the 72-hour clock, Board + subject notification, audit-log snapshot preservation before remediation, and a post-mortem item for the oversight board.
- **Subject notification design:** reuse the who-viewed feed — a breach entry is an access we did not intend; it still shows in the receipt.

## Verification status (PRIV-003, 2026-09-09)

Every control this document claims, graded against what I actually read and executed in `backend/` on 2026-09-09. Three grades:

- **(a) implemented and tested** — the control exists in code *and* a test asserts it. Verified by running the API in-process against the `seed_demo` fixture, or by `curl` against a live `uvicorn`.
- **(b) implemented but untested** — the code path exists; nothing asserts it, so a refactor can silently remove it.
- **(c) documented only** — **not found in code as of 2026-09-09.** These are design intent for the pilot, not v1 behaviour, and this document previously read as if they were shipped.

Cases are in [security-test-cases.md](../quality/security-test-cases.md); threats in [threat-model.md](../quality/threat-model.md).

### Access control and the ADR-0003 firewall

| Control as claimed here | Grade | Evidence |
|---|---|---|
| Server-side RBAC, UI never trusted | **(a)** | `backend/app/security.py:73-79`; roles resolved from the DB row, not the token (`security.py:67`). TC-414, TC-416, TC-417 |
| Route-level commander firewall (middleware) | **(a)** | `backend/app/firewall.py:70-104`, deny prefixes `:16-26`; `backend/tests/test_firewall.py`. TC-426, TC-429 |
| Handler-level firewall, independent of middleware | **(a)** as of this task | `firewall.py:52-67`; verified in isolation with the middleware bypassed. TC-427 — previously (b), no test asserted the handler alone |
| Trap route `GET /welfare/personnel/{id}` always 403 + audited | **(a)** | `backend/app/api/routers/privacy.py:405-421`; `test_firewall.py:13-16`. TC-430 |
| Commander scoped to own unit chain | **(a)**, with one caveat | `privacy.py:63-64`, `_guard_unit` (`commander.py:57-59`) and `_units` (`commander.py:62-67`) cover all seven aggregate routes; verified `commander.tiny` → every `/aggregates/unit/3BN*` = 403, and `/aggregates/units` returns only the caller's own unit. Caveat: every guard is conditional on `user.unit_id` being non-null, so a commander seeded without a unit is unscoped. TC-421 |
| Deny-by-default with denied attempts audited | **(a)** | `firewall.py:55-63`, `:88-97`; `require_roles` `security.py:75-76` |
| **ABAC: `consent(subject).active == true` gate on individual reads** | **(a) as of 2026-09-09 ~02:20** (was **(c)** at ~02:00) | Promised by [rbac-matrix.md](rbac-matrix.md) DT-02. At ~02:00 `GET /risk/{id}`, `GET /risk/{id}/trend` and `GET /signals/{id}` checked **role only** — `counsellor.a` read three unrelated pseudonyms with 200s. **Fixed:** the subject-scope helpers in the new `backend/app/authz.py` (`may_read_subject`, `assert_subject_scope`) are now called from all three routes. Re-verified: `counsellor.a` against `ps_3bn05`, `ps_3bn07`, `ps_tiny2` returns **403 on all three routes**. Regression cover `test_security_hardening.py::test_tc418_*`, `::test_tc419_*`. TC-418, TC-419 |
| **ABAC: `case.assignee == principal` (caseload scoping)** | **(a) as of 2026-09-09 ~02:20** (was (a) on the newer routes, (c) on the older ones) | `_assert_assigned` enforces assignment and audits `case.deny` on `/interventions/case/{id}`, `/timeline`, `/notes`. At ~02:00 the older `/interventions/{id}/actions`, `/outcome` and `/telemanas` still fetched by id with no check, and two narrow gaps fell open on the guarded path (an unassigned case, an empty `assigned_units`). **Fixed:** `assert_case_scope` (`authz.py`) is now called by the older routes too, and both fall-open cases now deny. Regression cover `test_security_hardening.py::test_tc420_*`, `::test_tc420b_*`. TC-420, TC-420b |
| Admin holds no read grant on individual data | **(a)** | Explicit deny `signals.py:46-47`; `test_firewall.py:88-91`. TC-417 |
| Auditor is content-blind | **(a)** as of this task | `audit_api.py:29-40` projects no `reason`, `payload` or `subject_pseudonym_id`. TC-444 |
| MFA, short-lived sessions, device binding | **(c)** | Password-only login (`security.py:55-59`), 12 h token (`config.py:18`). No MFA, no device binding, **no login rate limit or lockout**. TC-457 |
| Role changes require approval and are logged | **(c)** | No router writes `User.role`; role changes are direct DB writes with no approval workflow and no audit hook |
| Quarterly access review, orphan-account disable on transfer | **(c)** | Process control; `User.is_active` exists (`models.py:36`) but nothing drives it from HR |

### Pseudonymization, dual-key and k-anonymity

| Control as claimed here | Grade | Evidence |
|---|---|---|
| Analytics keyed on pseudonyms; identity map separately restricted | **(a)** | `identity_map` table `models.py:39-50`; reachable only via `privacy.py:193-227` |
| Dual-key requires two distinct principals | **(a)** | `privacy.py:136-149`, `:161-174`; self-approval leaves status `pending`. TC-431, TC-433 |
| Admin can never be a keyholder | **(a)** | `require_roles("counsellor","welfare_officer")` `privacy.py:128`; `test_privacy.py:62-71` |
| Unmask requires an active consent artefact + purpose vocabulary | **(a)** | `privacy.py:86-97`, `:30-36`, `:84-85`. TC-434, TC-435 |
| Unmasked view is session-scoped and expires | **(b)** | Guard exists (`privacy.py:204-205`, expiry set `:178`); no test drives the clock past `expires_at`. TC-436 |
| **Dual-key resists one human holding two accounts** | **(c)** | The guards compare `user.id` only; `User.role` is scalar (`models.py:30`) so a second account is indistinguishable from a second person. Verified: a sock-puppet welfare account supplied the second key and the legal name was disclosed. TC-432 — accepted residual, see §Residual risks item 1 |
| k ≥ 5 enforced in the aggregation service, not the UI | **(a)** | `backend/app/privacy/kanonymity.py:26-69`, `k` from `config.py:20`; `test_privacy.py:12-32`. TC-450 |
| **Complement suppression blocks subtraction inference** | **(a) as of 2026-09-09 ~02:20** (was **(c)** at ~02:00) | At ~02:00 cell and complement suppression were implemented but `morale_index` / `elevated_share` were still published from **raw** counts beside `n`: `/aggregates/unit/3BN` returned `n=12`, `morale_index=0.917` with `green`+`amber` suppressed → `amber = 1` recoverable. **Fixed.** Both ratios are now withheld whenever any cell is suppressed; the complement is chosen from all remaining tiers including zero-count ones; and `suppressed_keys` is replaced by a bare `suppressed_cells` count. Re-verified: the same request returns `morale_index: null`, `elevated_share: null`, `suppressed_cells: 2`. Residual: `n − Σ(published)` still reveals the *combined* size of the hidden tiers (1), but not which tier — the designed limit of complement suppression. Regression cover `test_security_hardening.py::test_tc451_*`, `::test_tc452_*`. TC-451, TC-452 |
| Removal events re-check the k-floor before recomputation | **(b)** | k is re-evaluated on every request because the aggregate is computed on read (`kanonymity.py:12-23`), not cached — correct by construction, but nothing tests the withdrawal→recompute path |
| Commander has no ad-hoc slicing API | **(a)** | One route, one unit: `privacy.py:57-74`. No list-units, no sort, no filter |

### Break-glass, audit and transparency

| Control as claimed here | Grade | Evidence |
|---|---|---|
| Append-only hash-chained audit | **(a)** | `backend/app/audit.py:17-19`, `:27-70`, verify `:73-93`; DB triggers `backend/app/db.py:45-69`. TC-440, TC-441 |
| Verification job fails closed on a broken chain | **(b)** | `GET /audit/verify` reports `{"ok": false, "broken_at": n}` (`audit.py:90-91`) — verified — but nothing **locks writes** on a broken chain; it is a report, not an interlock. This document's "a broken chain locks writes" is aspirational |
| **Hash chain covers the whole entry** | **(a) as of 2026-09-09 ~02:20** (was **(c)** at ~02:00) | `at` was excluded from the hashed body and from `verify_chain`'s recomputation, so rewriting `at` to `2020-01-01` left the chain reporting `ok: true` — a DBA could forge *when* an access happened. **Fixed:** `at` and `seq` are both inside the hashed body and recomputed on verify. Re-verified with both append-only triggers dropped: rewriting `at` now returns `{"ok": false, "broken_at": 1, "reason": "entry_modified"}`. TC-442 |
| Audit log resists deletion | **(a)** against the application, **(b)** against a superuser (was **(c)** at ~02:00) | Triggers block UPDATE/DELETE from the app connection. A superuser can still `DROP TRIGGER`, but tail truncation no longer passes verification: an `AuditCheckpoint` row carries `entry_count` + `head_hash`, advanced on every write, and `verify_chain` compares both — a removed tail returns `entry_count_mismatch`, a rewritten head `head_mismatch`. This is **detection, not prevention**, and the checkpoint lives in the same DB, so a sufficiently careful superuser could rewrite it too; an external/offsite anchor remains future scope. TC-443 |
| Every read logged with its purpose string | **(a)** | `risk.py:59-68`, `signals.py:53-62`, `privacy.py:211-220`, `interventions.py:104-113` |
| Denied attempts logged with the same rigour as reads | **(a)** in the log, **(c)** in the receipt | Written with `denied=True` (`firewall.py:55-63`) but filtered **out** of the subject's who-viewed feed (`privacy.py:362`). TC-459 |
| Subject-visible who-viewed feed | **(a)** | `privacy.py:351-392`; `test_privacy.py:54-59`, `:85-88`. TC-437 |
| Who-viewed is complete | **(b)** | Whitelist of nine action names (`privacy.py:363-375`) capped at 100 rows (`:379`): a future read action is invisible by default. TC-459 |
| Break-glass notifies subject + welfare officer, 24 h, oversight queue | **(a)** for notification and flag; **(c)** for the window | `privacy.py:239-272`; but `expires_at` is never re-checked — the identity is returned in the POST response itself (`privacy.py:284-294`), so 24 h is a *review* window, not an access window. Break-glass is also un-throttled and not consent-gated. TC-437, TC-438, TC-439 |

### Cryptography, deployment and data lifecycle

| Control as claimed here | Grade | Evidence |
|---|---|---|
| TLS 1.3 in transit; certificate pinning in the app | **(c)** | Terminated by the deployment, not by the app; nothing in `backend/` configures or asserts it. Pilot deployment item |
| **AES-256-GCM at rest; envelope encryption of sensitive columns; on-prem KMS/HSM** | **(c)** | Not found in code as of 2026-09-09. `identity_map.legal_name` is a plaintext column (`models.py:49`); the dev store is a SQLite file (`config.py:16`). TC-460 |
| Passwords stored safely | **(a)** | PBKDF2-HMAC-SHA256, 120k rounds, per-password salt, constant-time compare (`backend/app/passwords.py:7-26`) |
| Secrets never in code | **(c) — currently violated** | `jwt_secret` defaults to the literal `"saarthi-dev-secret-change-me-32b+"` (`config.py:17`). Env override exists (`SAARTHI_` prefix, `config.py:14`) but nothing fails closed if it is unset. TC-415 |
| Raw audio never persisted; only the feature vector leaves the device | **(b)** server-side | `POST /app/passive` stores only `sleep_hours_proxy` and returns `raw_audio: false` (`app_data.py:112-120`). The device-side guarantee is APP-006 and is not yet testable |
| 90-day raw-data expiry, idempotent, trend preserved | **(a)** for check-ins and instruments | `backend/app/privacy/expiry.py:11-27`; verified 1+1 purged then 0+0. TC-453 |
| …covering the whole voluntary bundle | **(c)** | `PassiveFeature` rows are never purged (`expiry.py:8` imports only `CheckIn`, `InstrumentResult`) — verified surviving two runs. And `expires_at` derives from a **client-supplied** `recorded_at` (`app_data.py:43-48`, `:67`), so a future date makes a row immortal. TC-454, TC-455 |
| Scheduled expiry | **(c)** | Admin-triggered only (`privacy.py:395-402`); no scheduler in the repo — already conceded in [dpdp-2023-mapping.md](dpdp-2023-mapping.md) row 7 |
| Consent artefact is the §4/§6 evidence | **(b)** | Artefact rows written and audited (`privacy.py:307-328`), but `artefact_hash` is a random id (`privacy.py:316`), not a digest of the artefact — it cannot prove *what* was agreed. TC-449 |
| Silent withdrawal has no command-visible read path | **(a)** | `consent.py:36-47`, `privacy.py:332-348`; the aggregate reads only `identity_map` + `risk_score` (`kanonymity.py:12-23`). `test_privacy.py:91-101`. TC-448 |
| Consent gate on every voluntary-bundle write | **(a)** | `app_data.py:57-58`, `:81-82`, `:109-110` via `consent.py:23-33`; all three verified 403 after withdrawal. TC-445…447 |
| On-prem / MeghRaj, air-gapped mode, data localisation | **(c)** | Deployment posture; nothing in `backend/` enforces or detects it |
| API rate limiting and backpressure | **(c)** | No rate limiting anywhere in `backend/app/`. `POST /ingest/hr/csv` also reads the entire upload into memory with no cap (`ingest.py:35`). TC-457, TC-458 |
| Backups encrypted; restore drill | **(c)** | Process control, not yet exercised |
| CORS restricted to the console origins | **(c) — currently the opposite** | `allow_origins=["*"]` **with** `allow_credentials=True` (`backend/app/main.py:42-48`); verified live that an `OPTIONS` preflight from `https://evil.example` is answered with that origin reflected and credentials allowed. TC-456 |
| Session notes held to the MHA §23 floor | **(a)** for access, **(c)** for confidentiality at rest | `GET/POST /interventions/case/{case_id}/notes` (`counsellor.py:304-393`) are guarded by `_assert_assigned`, refused to commanders by the middleware and to auditors by role — verified 403/403/200. But notes are deliberately excluded from the 90-day TTL ([F08](../features/F08-privacy-safety-architecture.md) §4), so `session_note.free_text` (`models.py:573`) is the **longest-lived unencrypted clinical text in the system**. TC-420b, TC-460 |

### What this means

At ~02:00 on 2026-09-09 this section recorded two demo blockers — the aggregate differencing leak (TC-451) and the audit timestamp gap (TC-442) — and three pilot blockers: the missing consent/caseload gate on individual reads (TC-418/419), the CORS policy (TC-456), and encryption at rest (TC-460).

**As of ~02:20, all of those except encryption at rest have been fixed in `backend/` and carry regression tests** in `backend/tests/test_security_hardening.py`; the [test-plan.md](../quality/test-plan.md) §4 gate is **GREEN** and the backend suite is `110 passed`. The ranked list, now annotated with per-item closure status, is [security-test-cases.md](../quality/security-test-cases.md) §3. What remains open is TC-415 (dev secret — a deployment check), TC-424, TC-432 (accepted), TC-439 and TC-459 (both need a decision, not code), and TC-460 (pre-pilot infrastructure).

The honest summary for a jury: **the architectural firewall is real and holds under attack — two independent layers, a trap route, and an audit row for every refusal — and the cryptographic layer around it was adversarially tested, found wanting in eleven specific places, and then fixed, with a regression test per finding.** What is still design intent rather than running code is encryption at rest and the key-management story around it. That is a normal place for a 15-day prototype to be; claiming otherwise is what would fail a security review.

## Residual risks (stated honestly)

1. Dual-key mitigates but does not eliminate insider threat — two colluding officers can unmask; audit visibility and oversight review are the compensating controls. **Sharper than we first wrote it:** the code compares principal *ids*, and nothing links a human to their accounts, so **one person holding a counsellor account and a welfare-officer account is two keys as far as the system is concerned** (verified 2026-09-09, [security-test-cases.md](../quality/security-test-cases.md) TC-432). Accepted for v1; the compensating controls are unchanged, and account-to-human linkage is a pilot requirement.
2. Air-gapping protects confidentiality, not physical custody — endpoint hardening and log integrity carry that risk.
3. k ≥ 5 suppresses direct re-identification, not inference across repeated slices — mitigated by fixed cell definitions (unit × week); differential-privacy noise is future scope ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)). **Correction and closure, 2026-09-09:** at ~02:00 this row wrongly credited complement suppression as a working mitigation — it was implemented but ineffective, because `morale_index` and `elevated_share` were published from raw counts alongside `n`, making a suppressed cell recoverable by arithmetic from a single response ([threat-model.md](../quality/threat-model.md) THR-17, TC-451). **Fixed at ~02:20 and re-verified:** both ratios are withheld whenever any cell is suppressed. Single-query re-identification of a *named* tier cell is closed. What genuinely remains residual is the original claim: `n` is still published, so a reader learns the combined size of the suppressed tiers, and inference across repeated slices over time is bounded by fixed cell definitions rather than prevented — differential-privacy noise is future scope.
4. The rules engine can be wrong in both directions — a false positive is an unnecessary cup of tea with a counsellor; a false negative is a life ([PRD](../product/prd.md) NFR-07).
