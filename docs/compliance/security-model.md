# Security Model — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05

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

## Residual risks (stated honestly)

1. Dual-key mitigates but does not eliminate insider threat — two colluding officers can unmask; audit visibility and oversight review are the compensating controls.
2. Air-gapping protects confidentiality, not physical custody — endpoint hardening and log integrity carry that risk.
3. k ≥ 5 suppresses direct re-identification, not inference across repeated slices — mitigated by fixed cell definitions (unit × week) and complement suppression; differential-privacy noise is future scope ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).
4. The rules engine can be wrong in both directions — a false positive is an unnecessary cup of tea with a counsellor; a false negative is a life ([PRD](../product/prd.md) NFR-07).
