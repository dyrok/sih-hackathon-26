# DPDP Act 2023 — Obligation Mapping

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05

## Framing

- **What this is:** an engineering compliance map. Each row ties a statutory duty (section cited) to the mechanism that satisfies it and the doc that owns the implementation. **Not legal advice** — clause texts are paraphrased for traceability and must be verified against the Gazette and the final DPDP Rules once notified, before any formal legal review.
- **Roles (§2):** CRPF / the welfare cell operates SAARTHI as the **Data Fiduciary** (§2(g)); the jawan is the **Data Principal** (§2(t)). HRMS feeds are inputs the fiduciary controls; the jawan app is the consent and transparency surface.
- **Lawful-basis split — the load-bearing decision:** core HR signals (leave, duty roster, deployment, transfers, training) ride the **legitimate-use** ground — the team's anchor is **§7(i)**, read with **§7(d)** (employee / contracted-personnel data). No consent is asked for these, none is expected. Everything voluntary (check-ins, instruments, voice features, unit pulse) rides **consent** (§4(a), §6).
- We deliberately **do not invoke the State-instrumentality exemptions (§17(2))** for voluntary welfare data: it is not national-security processing, and the trust argument collapses the moment we claim it.

## Basis-per-processing table

| Processing | Basis (cite) | Consent needed? |
|---|---|---|
| Leave, roster, deployment, transfers, training ingestion | §7(i) read with §7(d) — legitimate use | No |
| Check-ins, PHQ-9 / GAD-7 / PSS-10 / ISI, voice feature vectors | §4(a) + §6 — consent | Yes — explicit, revocable, unbundled |
| Unit pulse (command-climate rating) | §4(a) + §6 — consent; aggregate-only surfacing | Yes |
| Emergency contact when harm is imminent | §7 medical-emergency legitimate use; MHA 2017 §23(1) public-safety analog | No — break-glass, notified + audited ([rbac-matrix.md](rbac-matrix.md)) |

## Obligation → mechanism map

Status legend: `[x]` decided / implemented in v1 scope · `[~]` in progress · `[ ]` planned · `[!]` open decision.

| # | Obligation (cite) | Mechanism in SAARTHI | Where implemented | Status |
|---|---|---|---|---|
| 1 | **§4(a) + §6(1)** — consent as ground; consent limited to data necessary for the specified purpose | Unbundled consent artefacts: each bundle = data categories + purpose string + retention note. No bundle-all option. | [F02](../features/F02-jawan-app.md) · [F08](../features/F08-privacy-safety-architecture.md) | [~] |
| 2 | **§5** — itemised notice; availability in the languages of the Eighth Schedule | The consent sheet **is** the notice: per-bundle itemisation, plain Hindi + English at v1 | [F02](../features/F02-jawan-app.md) · [design.md](../architecture/design/design.md) §8 | [~] |
| 3 | **§6(2)–(4)** — withdrawal anytime, as easy as giving; prior processing stays lawful | Withdrawal at the same tap depth as giving; **silent** propagation so withdrawal can never become a command signal | [F08](../features/F08-privacy-safety-architecture.md) §3 | [~] |
| 4 | **§7(i) read with §7(d)** — legitimate use for employment-scope data | HR ingestion runs on this basis; the basis split is stored in ingestion config; the app never asks consent for HR signals | [F01](../features/F01-hr-signal-engine.md) | [~] |
| 5 | **§8(1)** — security safeguards proportionate to risk | TLS 1.3 in transit, AES-256-GCM at rest, pseudonymization, RBAC + ABAC, append-only hash-chained audit | [security-model.md](security-model.md) · [rbac-matrix.md](rbac-matrix.md) | [~] |
| 6 | **§8(4)** — notify the Board and each affected Data Principal of a breach | Breach runbook with a 72-hour clock (DPDP Rules, draft 2025 — confirm against final rules); subject notification reuses the who-viewed channel | [security-model.md](security-model.md) §breach | [ ] runbook to author |
| 7 | **§8(6)–(7)** — erasure on withdrawal / purpose expiry, statutory-retention carve-outs aside | 90-day auto-expiry of raw self-reports (only the derived trend persists); erasure pipeline on consent withdrawal | [F08](../features/F08-privacy-safety-architecture.md) §lifecycle | [~] |
| 8 | **§8 (data-protection-by-design duties)** | The welfare firewall is architectural, not contractual — the route layer refuses, it does not hide | [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) | [~] |
| 9 | **§8 (accuracy duties)** — completeness, accuracy, consistency | HR signals sourced from the HRMS of record; self-reports are the subject's own words, never silently "corrected"; per-person baselines avoid stale-population drift | [F04](../features/F04-risk-rules-engine.md) | [~] |
| 10 | **§10** — Significant Data Fiduciary duties (DPO, independent data auditor, periodic due diligence / DPIA) | As-if-SDF posture from day one — see §SDF posture below | this doc | [ ] |
| 11 | **§11–§13** — access, correction / erasure, grievance | Own 90-day trend view + export (access); self-report edits are versioned; in-app grievance routes to the DPO | [F02](../features/F02-jawan-app.md) | [~] |
| 12 | **§16** — cross-border transfer restrictions | Stricter than required: all data on-prem (CRPF infra) or NIC MeghRaj; air-gapped mode for sensitive units | [security-model.md](security-model.md) §deployment | [~] |
| 13 | **§17(2)** — State exemptions (deliberately unused) | Not relied on for voluntary welfare data; documented so reviewers can challenge the choice | this doc §framing | [x] decided |
| 14 | **Schedule, Part B** — penalties up to ₹250 crore for security-safeguard failures (context only) | Engineering consequence: audit-integrity and access-control negative tests are release blockers, not nice-to-haves | [security-model.md](security-model.md) | [~] |

## Retention schedule (what §8(6)–(7) looks like as a table)

| Data | Retention | Deletion trigger | Carve-out note |
|---|---|---|---|
| Raw self-reports / check-ins | 90 days rolling | scheduled TTL job | none — only the derived trend persists |
| Derived risk trend + intervention outcomes | service life | account closure + statutory period | welfare-performance record |
| Consent artefacts | service life + statutory limitation period | DPO retention review | evidence of lawful basis must outlive the data |
| Session notes | counsellor-record practice (open item `[!]`) | never automated | MHA §23 territory |
| HR signals | per HRMS of record | outside system scope | §7(i)/§7(d) basis — retention follows employment records, not consent |
| Audit log | permanent | never (integrity-checked) | §8(7)-style compliance retention |

## Purpose-limitation spine (how §6(1) is enforced, not just stated)

```
consent bundle (purpose string)  ──>  audit log "why" field (every read)  ──>  who-viewed-my-data feed
```

The purpose string is the join key across three subsystems. If a read cannot name the purpose string of a live consent bundle, the API refuses to log it — and an unloggable read is refused by design.

## Consent artefact (the §4 / §6 evidence)

Fields: `consent_id` · `principal_pseudonym` · `bundle_id` · `purpose_string` · `data_categories` · `language` · `consent_version` · `granted_at` · `withdrawn_at` · `artefact_hash`. The audit log references `consent_id`, so disclosure without a live artefact is impossible by construction, not by convention.

## Data we do not process at all

(§6(1) necessity test: if it is not necessary for the welfare purpose, it is not collected.)

- Phone contents: SMS, call logs, contacts, browsing, app-usage history.
- Location tracking (beyond duty-roster data the jawan already has via the roster app).
- Camera or CCTV imagery; no facial analysis ([F08](../features/F08-privacy-safety-architecture.md) §anti-goals).
- Relationship or social-graph inference.

## Significant Data Fiduciary posture (as-if, ahead of any designation)

- **§10** lets the Central Government prescribe additional duties for Significant Data Fiduciaries — Data Protection Officer, independent data auditor, periodic due diligence / audit / impact assessment. At CRPF scale, designation is plausible; we build as-if from day one.
- DPO role named at pilot; grievance contact published in-app (§8 grievance duty).
- DPIA triggers: any new signal source · any threshold change that widens alert scope · any change to the identity map ([rbac-matrix.md](rbac-matrix.md)).
- Independent audit gate before any scale-up beyond the pilot battalion.

## Open items

- [ ] Verify clause-by-clause text against the Gazette and final Rules (paraphrases above, not quotes).
- [!] Session-note retention — counsellor records sit outside the 90-day self-report TTL; needs DPO + MHA-professional input ([mental-healthcare-act-2017.md](mental-healthcare-act-2017.md)).
- [ ] Consent-manager interplay: a force environment has no consumer consent-manager equivalent — the CRPF welfare cell plays that role; record it in the incident runbook ([security-model.md](security-model.md)).
- [ ] Multilingual notice expansion: Hindi + English at v1; further Eighth Schedule languages land as data files, not redesigns ([F02](../features/F02-jawan-app.md) · [design.md](../architecture/design/design.md) §8).
