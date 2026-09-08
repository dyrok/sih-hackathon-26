# F08 — Privacy & Safety Architecture (Trust Layer)

> Owner: kv · Status: [x] implemented in `backend/` (BACK-002/007/009) · Last updated: 2026-09-08
> Traces: [FR-14 – FR-18](../product/prd.md) · NFR-01/02/03/08 · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · AGENTS.md rule 8

## Purpose

The PS's hardest constraints — privacy, stigmatization, trust — are answered here, in architecture, not in a promise. In a force with ACR culture, "we promise not to misuse your data" is worthless; "you can watch us try, and it will fail" is a feature. That is the whole trust layer:

**An individual risk score is physically incapable of reaching command hierarchy, ACR, promotion or posting decisions.** There is no endpoint, no read path, and no export that can carry it there ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).

## Architecture mechanisms

### 1. Two-tier output — the architectural firewall (FR-14)

- Individual risk → counsellor only, consent-gated. Commander → unit aggregates only, k ≥ 5, no names.
- The commander container has **no API endpoint that accepts a personnel ID** for welfare data — enforced at the route level, not by UI convention ([architecture.md](../architecture/architecture.md) §4).
- The judge's attack — "an admin can just query the database" — is pre-answered: the admin role holds no read grant on individual data ([rbac-matrix.md](../compliance/rbac-matrix.md)), out-of-band reads land in the audit log, and DB grants match the matrix.

### 2. Pseudonymization + dual-key re-identification (FR-16)

- Analytics run on surrogate pseudonyms; the identity map is a separately restricted table.
- Unmasking (pseudonym → identity) requires counsellor **and** welfare officer — two distinct humans — with an active consent artefact and a reason string. No single principal, including admin, can unmask.
- Every unlock is logged and surfaces in the subject's who-viewed feed; unmasked views are session-scoped.

### 3. Silent consent withdrawal (FR-17)

- If withdrawing is visible to command, withdrawal itself becomes a signal, and nobody will ever withdraw. So: withdrawal writes only to the consent store and the audit log; no command-visible surface has a read path from the consent store — the schema makes the silent path the only path.
- Scoring excludes the person's voluntary data from the next cycle; the erasure pipeline starts ([dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) row 7). Aggregate floors are re-checked so a deletion can never single out a contributor.

### 4. 90-day raw-data expiry (FR-18)

- Raw self-reports auto-expire at 90 days; only the derived risk trend and intervention outcomes persist. The welfare value lives in the trend, not the raw journal.
- Session notes are deliberately **excluded** from this TTL — a counsellor-record decision under MHA §23 territory (open item in [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md)).

### 5. Who-viewed-my-data + break-glass notification (FR-15, NFR-08)

- The jawan's app shows who opened their record, when, why, and for how long — designed as a receipt, not a warning ([design.md](../architecture/design/design.md) §5). This turns surveillance into accountability: the demo's most memorable 15 seconds and the best differentiator.
- Break-glass (imminent-harm single-actor read) auto-notifies the subject and the welfare officer, expires in 24 h, and queues for oversight review. Protocol: [rbac-matrix.md](../compliance/rbac-matrix.md) §break-glass.

### 6. Governance — independent oversight board

- Ethics oversight with **a serving jawan on it**, not only officers. Reviews break-glass cases, threshold changes that widen alert scope, and DPIA outcomes; minutes are published to participants.
- This is the human control that backs the technical ones — without it, the audit log is just a nice database.

## Data lifecycle

| Stage | What happens | Retention | Access | Where |
|---|---|---|---|---|
| Ingest | HR signals from HRMS (CSV/API, legitimate use); app syncs over TLS via the offline-first queue; voice check-ins derive features on-device — raw audio never leaves the phone | HR rows per HRMS of record; app data pending sync | subject; ingestion pipeline | [F01](../features/F01-hr-signal-engine.md) · [F03](../features/F03-on-device-signals.md) |
| Identity split | Personnel no. isolated in the identity map; all analytics keyed on pseudonym | indefinite, restricted | dual-key only | [rbac-matrix.md](../compliance/rbac-matrix.md) |
| Derive | Rules engine scores risk from triangulated signals with per-person baselines; every flag ships its top-3 factors | derived trend persists | counsellor (consent-gated) | [F04](../features/F04-risk-rules-engine.md) |
| Persist | Raw self-reports stored under a 90-day TTL; trend + intervention outcomes persist | 90 days raw | subject; scoring | this doc §4 |
| Aggregate | k ≥ 5 service; cells and complements suppressed | aggregates | commander surface | [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) |
| Expire / erase | Scheduled TTL purge; on withdrawal, erasure propagates silently | — | pipeline only | [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) row 7 |
| Audit | Every read/write — including denied attempts — appended and hash-chained; the subject-visible slice is who-viewed | permanent, integrity-checked | subject (own), auditor (all), admin (append only) | [security-model.md](../compliance/security-model.md) |

## Anti-goals (deliberately not built — judges attack these otherwise)

1. **No facial emotion recognition.** The science is contested — Barrett et al. 2019 (*Psychological Science in the Public Interest*) finds expression-to-emotion inference does not hold across people or cultures — and in a forces context it reads as covert surveillance. Demoted to: optional **on-device, self-initiated** check-in analysis only, the same posture as voice ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)). Never CCTV, never covert, never server-side.
2. **No phone monitoring, no relationship tracker.** Kills trust permanently, is almost certainly illegal under DPDP (data not necessary for the specified purpose, §6(1)), and adds nothing the HR signals do not already carry.
3. **No scores in ACR / promotion / posting.** The firewall is architectural, not a policy promise; the success metric is "individual scores reaching command = 0" ([PRD](../product/prd.md) §4).
4. **Feature discipline.** More features = cognitive overload for users who check in in 10 seconds. v1 ships three things that work: voluntary check-in → explainable counsellor loop; who-viewed transparency; aggregate command view. Everything else waits for evidence.

### Weapon-access protocol (the hard question)

**Q: a Critical-tier flag lands on an armed jawan — does the system restrict weapon access?**
**A: never automated. Counsellor-recommended, commander-discretion, through the existing fitness-for-duty channel.**

1. Critical tier triggers counsellor outreach ≤ 24 h (FR-09). The counsellor may issue a **duty-fitness recommendation** — exactly what a manual referral produces today, in duty-focused language only ("temporary modification of duty and equipment assignment").
2. The recommendation reaches the commander as a **counsellor-signed letter through the existing welfare / fitness channel**. The commander acts on existing authority — they never see a score, the case, or a flag list, so the firewall holds.
3. The decision — including weapon custody — stays with the commander, on the counsellor's recommendation. **An automated revocation would make a false positive a punishment** (stripping an armed soldier of his weapon is not a "false-alarm cost"), would poison participation, and would turn the engine into a disciplinary actor.
4. The outcome is logged as an intervention outcome, visible to the subject in who-viewed; the oversight board reviews every such case.

## Compliance cross-links

| Claim / duty | Document |
|---|---|
| DPDP: consent artefacts, §7(i)/§7(d) basis split, breach clock, SDF posture | [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) |
| MHA 2017: §23 confidentiality floor, §21 non-discrimination | [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md) |
| Threat model (STRIDE), TLS / AES-256, on-prem / MeghRaj / air-gap, breach runbook | [security-model.md](../compliance/security-model.md) |
| Role × data matrix, dual-key, k ≥ 5, break-glass rules | [rbac-matrix.md](../compliance/rbac-matrix.md) |
| Container-level firewall and data flows | [architecture.md](../architecture/architecture.md) §4 |

## i18n keys (AGENTS rule 7 — all strings in `en` + `hi`)

`consent.sheet.title` · `consent.bundle.data.label` · `consent.bundle.purpose.label` · `consent.bundle.retention.label` · `consent.withdraw.action` · `consent.withdraw.confirm` · `whoViewed.title` · `whoViewed.entry.line` (role · when · why · how long) · `whoViewed.unmask.line` · `whoViewed.breakglass.line` · `expiry.explain` · `trend.ownonly`

## Implementation (BACK-002 / BACK-007 / BACK-009, 2026-09-08)

| Piece | Path |
|---|---|
| Hash-chained append-only audit + triggers | `backend/app/audit.py` · table `audit_events` |
| Break-glass | `POST /privacy/break-glass` |
| k ≥ 5 + complement suppression | `backend/app/privacy/kanonymity.py` · `GET /aggregates/unit/{id}` |
| Dual-key unmask | `POST /privacy/unmask` · `.../approve` · `.../identity` |
| Who-viewed | `GET /app/who-viewed` (subject-visible slice of the audit log) |
| 90-day TTL | `POST /jobs/expire-raw` |
| Firewall middleware | `backend/app/firewall.py` |
| Tests | `backend/tests/test_firewall.py` · `test_privacy.py` |

## Definition of done

- [x] Negative test: a commander-role request for welfare data by personnel ID is refused at the route **and** writes an audit entry — no UI-only guard.
- [x] k ≥ 5 test passes, including the complement-suppression case (TINY unit, n=4).
- [x] Dual-key tests: counsellor alone denied; admin cannot be a keyholder; two distinct principals granted, logged, visible in who-viewed.
- [x] Silent-withdrawal test: command-visible payload has no consent/withdrawal field; scoring excludes voluntary data.
- [x] Expiry job purges raw self-reports; derived trend survives.
- [x] Break-glass: subject + welfare-officer notifications land, 24 h expiry, oversight flag set.
- [x] Audit log: append-only enforced; hash-chain tamper test fails closed.
- [x] Passive ingest stores feature vectors only (`raw_audio: false` on `POST /app/passive`). Device-side audio is APP-006 (neel).
- [x] All i18n keys above exist in `en` + `hi` (`backend/app/i18n.py`).
- [x] Negative tests in `backend/tests/` (trace TC-401…409); this doc updated in the same change.
