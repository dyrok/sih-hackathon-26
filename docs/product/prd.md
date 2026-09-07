# PRD — SAARTHI v1 (prototype)

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05
> Discipline: every requirement numbered, unambiguous, testable (IEEE 830 distilled — no full SRS). Map: FR → feature docs → test cases in `docs/quality/test-plan.md`.

## 1. Users & roles

| Role | Sees | Never sees |
|---|---|---|
| Jawan (personnel) | Own data, own check-ins, consent panel, who-viewed-my-data | Anyone else's data |
| Counsellor | Individual pseudonymized risk + explainable evidence (after dual-key unmask) | Command hierarchy, appraisal data |
| Welfare officer | Individual evidence for assigned cases, intervention tracker | Raw journal text without consent |
| Commander | Unit aggregates only (k ≥ 5), morale index, leading indicators | Any individual name or score |
| MHA/evaluator | Demo environment, audit architecture | Live personnel data |

## 2. Functional requirements

### Signal layer
- **FR-01** — System ingests HR records (leave, duty roster, deployment, transfers, training) via CSV import + REST API and derives 15+ signal features (days-since-leave, circadian disruption score, family separation index, career friction…). → [F01](../features/F01-hr-signal-engine.md)
- **FR-02** — Jawan app supports a daily 10-second check-in (emoji/slider) and monthly full instruments (PHQ-9, GAD-7, PSS-10, ISI) with validity-scale items, in Hindi + English. → [F02](../features/F02-jawan-app.md)
- **FR-03** — Voice check-ins run prosody analysis **on-device**; only the derived feature vector leaves the phone. → [F03](../features/F03-on-device-signals.md)
- **FR-04** — App is offline-first: check-ins queue in local SQLite and sync when connectivity returns. → [F02](../features/F02-jawan-app.md)

### Inference layer
- **FR-05** — Rules engine v1 scores risk 0–100 from triangulated sources (HR + self-report + passive), using **per-person baselines** and clinically grounded thresholds. → [F04](../features/F04-risk-rules-engine.md)
- **FR-06** — Every flag ships an explanation: top contributing factors with values ("47 consecutive duty days, sleep −30%"). → [F04](../features/F04-risk-rules-engine.md)
- **FR-07** — Discrepancy detection: "I'm fine" + 4h sleep + 60 duty days + 2 cancelled leaves → masking flag (the faking is the finding). → [F04](../features/F04-risk-rules-engine.md)
- **FR-08** — Group trauma exposure: a unit-level casualty/incident auto-flags the whole exposed group, not individuals. → [F01](../features/F01-hr-signal-engine.md)

### Intervention layer
- **FR-09** — Response ladder: Green (self-help nudge) → Amber (buddy + JCO informal check) → Red (counsellor outreach ≤ 24h) → Critical (immediate contact + duty modification). → [F05](../features/F05-intervention-engine.md)
- **FR-10** — Capacity-aware triage: alerts ranked by urgency × intervenability, capped per counsellor-week. → [F05](../features/F05-intervention-engine.md)
- **FR-11** — Workload rebalancing: engine proposes roster swaps minimising max individual load. → [F05](../features/F05-intervention-engine.md)
- **FR-12** — Counsellor console: session notes, outcome tracking, risk-trend before/after. → [F06](../features/F06-counsellor-console.md)
- **FR-13** — Tele-MANAS (14416) handoff recorded as an intervention outcome. → [F05](../features/F05-intervention-engine.md)

### Trust layer
- **FR-14** — Two-tier output: individual risk → counsellor only (consent-gated); commander → unit aggregate with k-anonymity ≥ 5, no names. → [F08](../features/F08-privacy-safety-architecture.md)
- **FR-15** — Jawan app shows exactly who opened their record, when, and why. → [F02](../features/F02-jawan-app.md)
- **FR-16** — Analytics run on pseudonyms; unmasking requires counsellor + welfare officer (dual key); every unlock logged. → [F08](../features/F08-privacy-safety-architecture.md)
- **FR-17** — Silent consent withdrawal: withdrawing consent is invisible to command. → [F08](../features/F08-privacy-safety-architecture.md)
- **FR-18** — Raw self-report data auto-expires at 90 days; only derived risk trend persists. → [F08](../features/F08-privacy-safety-architecture.md)
- **FR-19** — Anonymous unit pulse: personnel rate command climate; only the aggregate surfaces. → [F02](../features/F02-jawan-app.md)

### Demo infrastructure
- **FR-20** — Synthetic data generator: ~1,000 personnel, realistic 90-day roster/leave/deployment patterns + one scripted persona ("Constable, 34, 3rd Bn") for the demo loop. → [F09](../features/F09-synthetic-data-generator.md)

## 3. Non-functional requirements

- **NFR-01 Privacy (DPDP Act 2023)** — consent artefacts, purpose limitation, 72h breach readiness; legal-basis split: §7(i) legitimate use for core HR signals, explicit consent for voluntary data. → [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md)
- **NFR-02 Confidentiality (MHA 2017 §23)** — mental-health records confidentiality + non-discrimination. → [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md)
- **NFR-03 Security** — RBAC/ABAC enforced server-side, TLS in transit, AES-256 at rest, immutable audit log, on-prem/air-gap deployable. → [security-model.md](../compliance/security-model.md)
- **NFR-04 Accessibility** — low-end Android (API 26+), offline, icon-first UI for mixed literacy, Hindi + English (regional languages later). → [design.md](../architecture/design/design.md)
- **NFR-05 Explainability** — no black-box alerts; every score lists top-3 factors (SHAP in v2). → [model-explainer.md](../explanation/model-explainer.md)
- **NFR-06 Performance** — risk recompute for a 1,000-personnel battalion < 60 s on modest hardware (rules engine is trivially fast; this guards the demo).
- **NFR-07 False-alarm economics** — thresholds tuned for "false positive = one cup of tea with a counsellor; false negative = a life"; alert caps prevent fatigue.
- **NFR-08 Auditability** — every read/write of welfare data is logged immutably; break-glass access notifies the subject.

## 4. Success metrics (pilot — defined upfront, no invented numbers)

| Metric | Target (reasoned estimate) |
|---|---|
| Voluntary participation | ≥ 30% of unit (adoption strategy rides roster app) |
| Time from Red flag to counsellor contact | ≤ 24 h |
| Post-intervention risk-trend reduction | directionally negative at 4 weeks |
| Individual scores reaching command | **0 — architectural guarantee** |
| Punitive outcomes linked to system | 0 (monitored — trust signal) |
