# Mental Healthcare Act 2017 — System Mapping

> Owner: kv · Status: [x] current (PRIV-004 §23 review vs backend v1) · Last updated: 2026-09-08

## Where the Act reaches (and where it stops)

- The Act governs mental health establishments and professionals. SAARTHI is not a mental health establishment and takes **no diagnosis or treatment decisions** — screeners are reflection support, not diagnosis ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)).
- It still binds the design in three places: counsellors using the platform are Act-regulated professionals; the platform processes mental-health-adjacent records (PHQ-9 / GAD-7 / PSS-10 / ISI, check-ins, voice feature vectors); and handoffs go to Tele-MANAS 14416, which operates inside the Act's national tele-mental-health framework.
- **Engineering position:** we adopt **MHA §23 as the confidentiality floor for every welfare record**, even where the Act's letter would not reach the platform. Over-compliance here is the product — a jawan does not distinguish between statutory scopes, and neither should our schema.

## What SAARTHI must never do (Act-derived prohibitions)

1. Produce or imply a **diagnosis** — outputs are reflection support and welfare signals; the screener disclaimer is attached every time ("This is reflection support, not diagnosis").
2. Label personnel as "mentally ill" in any interface or record — scores, flags and tiers are welfare states, not conditions; the response ladder uses care language and never clinical labels ([design.md](../architecture/design/design.md) §2).
3. Let a welfare state leak into duty language — the roster rebalancer proposes load changes, never "restricted duties for stressed personnel" phrasing.
4. Treat the counsellor console as a command tool — the counsellor is the disclosure target under §23(1), never a forwarding agent to the chain of command.

## §23(1) as a pipeline invariant

Consent-gated disclosure is enforced as an ordered chain; every hop is auditable and there is no path that skips a hop:

```
consent artefact (DT-06) ──> pseudonymized case (DT-03) ──> dual-key unmask (DT-04) ──> logged disclosure (DT-07) ──> subject-visible receipt (DT-09)
```

A disclosure without a live consent artefact fails at the first hop; a disclosure without a log entry fails at the last. That is the engineering reading of §23(1) — the exception list is closed, so the code paths are closed too.

## §23 — Confidentiality of mental health records

**§23(1):** no information about mental illness, identity, diagnosis or treatment may be disclosed without the person's consent, subject to narrow statutory exceptions (the care professional; a close relative / caregiver in the person's interest; where law requires; public safety and security). **§23(2):** the person may refuse or stop further disclosure. **§23(3):** the Central Mental Health Authority is to frame confidentiality guidelines.

| §23 principle | SAARTHI mechanism | Where |
|---|---|---|
| No disclosure without consent | Individual risk surfaces only to the counsellor role, and only behind an active consent artefact — the gate is in the API, not the UI | [F08](../features/F08-privacy-safety-architecture.md) §1–2 |
| Disclosure only to the care professional | Two-tier output: the only roles that can reach an individual record are counsellor and welfare officer (assigned cases) | [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) |
| Right to refuse or stop further disclosure (§23(2)) | Consent withdrawal — silent, at the same tap depth as giving, and it halts scoring on the person's voluntary data | [F08](../features/F08-privacy-safety-architecture.md) §3 |
| Public-safety exception stays narrow | Break-glass read: time-boxed, single-actor only for imminent-harm cases, auto-logged, auto-notifies the subject and welfare officer, oversight review | [rbac-matrix.md](rbac-matrix.md) §break-glass |
| §23(3) central confidentiality guidelines | Once notified, final guidelines override anything weaker in our docs | open item below |

## Non-discrimination (§21)

§21 gives a person with mental illness the right to equality, dignity and non-discrimination. In a force context the actionable version is: **the system must never become the machinery of discrimination.**

1. **Scores never touch ACR, promotion or posting** — an architectural firewall, not a policy sentence ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)). The commander container has no endpoint that accepts a personnel ID for welfare data.
2. **Commander surface is aggregate-only (k ≥ 5)** — an aggregate cannot single anyone out; suppression also covers complements, to block subtraction inference ([rbac-matrix.md](rbac-matrix.md)).
3. **Roster rebalancing (F05) optimises load, not discipline** — proposals minimise max individual load and are auditable; they never take the form of a sanction.
4. **No automated consequences at the Critical tier** — including weapon custody; see the weapon-access protocol in [F08](../features/F08-privacy-safety-architecture.md) §anti-goals.
5. **Human review for every consequential action** — the engine recommends; a professional decides. Success metric: punitive outcomes linked to the system = 0 ([PRD](../product/prd.md) §4).

## Section-by-section map

| Provision | Principle | SAARTHI mechanism | Where |
|---|---|---|---|
| §18(4) | Care in a manner acceptable to and in a language understood by the person | Hindi + English at v1, icon-first UI for mixed literacy, more languages as data files | [design.md](../architecture/design/design.md) |
| §21 | Equality, non-discrimination, dignity | Firewall + aggregate-only command surface + no automated punitive consequences | [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) |
| §22 | Right to information | Who-viewed-my-data feed: who, when, why, how long — exceeds the Act's minimum; transparency as accountability | [F08](../features/F08-privacy-safety-architecture.md) §5 |
| §23 | Confidentiality of mental health records | Pseudonyms, dual-key unmask, TLS 1.3 / AES-256 at rest, append-only audit | [security-model.md](security-model.md) |
| §24 | Right to access basic medical records | Own 90-day trend line + export in the jawan app | [F02](../features/F02-jawan-app.md) |
| Tele-MANAS (14416) | Access to national tele-mental-health | Handoff recorded as an intervention outcome; no record export without consent | [F05](../features/F05-intervention-engine.md) |

## Counsellor console obligations

- The counsellor sees **pseudonymized cases plus derived evidence**, never raw journal text — the individual's own words stay theirs unless the case is unmasked ([F06](../features/F06-counsellor-console.md)).
- Session notes are counsellor records: written and read under professional-practice confidentiality, not command visibility, and excluded from the 90-day self-report TTL (open item below).
- Every disclosure act on the console (open case, unmask, Tele-MANAS handoff) is logged and appears in the subject's who-viewed feed — §23 compliance is demonstrated to the jawan, not asserted to an auditor.

## Interaction with DPDP 2023

- MHA §23 is stricter and more specific than DPDP for mental-health-adjacent data; where they conflict, **the stricter rule wins** (e.g. retention: DPDP erasure duties are met by the 90-day raw-data expiry, but session notes follow the MHA-standard professional-record practice — see open item).
- Breach notification is governed by DPDP (§8(4) + rules clock, [dpdp-2023-mapping.md](dpdp-2023-mapping.md) row 6); the notification copy for mental-health-record breaches must still respect §23 framing — reviewed by the DPO and a counsellor, never auto-generated copy.

## Open items

- [ ] Track §23(3) confidentiality guidelines from the Central Mental Health Authority; reconcile with the DPDP breach clock and with retention practice.
- [!] Session-note retention is a counsellor-record decision — deliberately **excluded** from the 90-day self-report TTL; needs DPO + MHA-professional input.
- [ ] Review the notification copy shown when a §23(1) public-safety break-glass occurs — oversight board owns the wording.
- [ ] Confirm the professional-registration requirements for counsellors onboarded to the console (out of system scope, but the runbook must reference it).
- [x] Negative tests for §23 behaviours (no consent → no disclosure; withdrawal stops further disclosure) live in `backend/tests/test_privacy.py` (also listed in [test-plan.md](../quality/test-plan.md) TC-401/405/407).

## PRIV-004 — §23 compliance review (2026-09-08)

Review of the engineering reading of **Mental Healthcare Act 2017 §23** against the v1 API. Not legal advice; Central Mental Health Authority §23(3) guidelines are not yet notified (still an open item).

| §23 requirement | Backend mechanism | Evidence | Residual risk |
|---|---|---|---|
| No disclosure of mental-health-adjacent info without consent §23(1) | Unmask requires a live `ConsentArtefact`; counsellor sees **pseudonyms** without it; identity is a second hop | `POST /privacy/unmask` 403 without consent | Counsellor can still see a **score** on a pseudonym (duty of care / HR-legitimate-use triangulation). Raw journal is not in v1 counsellor payload. |
| Disclosure only to the care professional | Commander has **no** individual endpoint (ADR-0003). Admin has no read grant on DT-01–04. | `test_firewall.py`, `test_admin_cannot_read_individual_signals` | A DB superuser is a deployment control (security-model), not an API hole. |
| Right to refuse / stop further disclosure §23(2) | Silent withdrawal nulls voluntary sources on the next score; masking cannot fire on nulls; commander views have no consent column | `test_silent_withdrawal`, `test_masking_suppressed_after_withdrawal` | Open cases continue as duty of care on **HR** signals only (F05) — documented, not a leak of voluntary data. |
| Public-safety exception stays narrow | Break-glass: counsellor only, 24 h, auto-notify subject + welfare, oversight flag. Admin cannot trigger. | `test_break_glass_notifies_subject` | Copy of the in-app notification is i18n keys, not yet counsellor-legal-reviewed. |
| No diagnosis, no "mentally ill" label | Tiers are care states (`green/amber/red/critical`); instruments carry `instr.not_diagnosis` | i18n + F04 | Console UI (F06, neel) must not relabel. |
| Tele-MANAS handoff stores logistics, never session content | `telemanas_referral.outcome_status` enum only; API returns `clinical_content: null` | `test_queue_and_telemanas_and_outcome` | none |
| Weapon / duty restriction not automated | No endpoint revokes arming; roster proposals are load numbers | F08 weapon-access protocol | Operational letter stays out of band. |

**Verdict:** §23 is met as a pipeline invariant in v1 for the hops we own (API + audit + firewall). Session-note retention remains `[!]` — excluded from the 90-day TTL, needs DPO + MHA-professional input. §23(3) guidelines, once notified, override anything weaker here.

**Disclaimer:** engineering compliance mapping, not legal advice. Sections are cited for traceability; paraphrases are not quotations.
