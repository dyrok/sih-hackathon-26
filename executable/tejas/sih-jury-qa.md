# SIH 2026 Jury Defense & Viva Guide — 50 High-Yield Questions & Answers

> **Project:** SAARTHI (PS ID: 26186 · CRPF / Ministry of Home Affairs · MedTech/HealthTech)  
> **Target Audience:** All team members (Tejas, KV, Neel, Risa, Ayush, Manan) for Internal College Viva, National Screening, and 36-Hour Grand Finale  
> **Owner:** tejas (QA & Demo Support) · **Status:** [x] frozen · **Last updated:** 2026-09-09  
> **Core Anchors:** [docs/product/winning-strategy.md](../../docs/product/winning-strategy.md) · [docs/product/research-sih-2026.md](../../docs/product/research-sih-2026.md) · [docs/quality/demo-runbook.md](../../docs/quality/demo-runbook.md)

---

## Quick Navigation
- [1. Problem Statement & Domain Context (Q1–Q7)](#1-problem-statement--domain-context-q1q7)
- [2. AI, Model Theory & Rules Engine v1 vs ML v2 (Q8–Q15)](#2-ai-model-theory--rules-engine-v1-vs-ml-v2-q8q15)
- [3. Privacy, Firewall & Legal Compliance (Q16–Q24)](#3-privacy-firewall--legal-compliance-q16q24)
- [4. Software Architecture, Security & Offline-First (Q25–Q32)](#4-software-architecture-security--offline-first-q25q32)
- [5. User Adoption, Stigma & Jawan UX (Q33–Q38)](#5-user-adoption-stigma--jawan-ux-q33q38)
- [6. Interventions, Triage & Workload Optimization (Q39–Q44)](#6-interventions-triage--workload-optimization-q39q44)
- [7. Competition, Feasibility & 36-Hour Hackathon Plan (Q45–Q50)](#7-competition-feasibility--36-hour-hackathon-plan-q45q50)

---

## 1. Problem Statement & Domain Context (Q1–Q7)

### Q1: What is the exact problem you are solving, and why is it critical right now?
**Answer:**  
We are addressing **Smart India Hackathon Problem Statement 26186** by the Central Reserve Police Force (CRPF) / Ministry of Home Affairs: *AI-Based Predictive Personnel Stress & Welfare Monitoring System for Uniformed Forces*.  
Uniformed personnel endure prolonged deployments, high operational tempo, sleep disruption, and extended family separation. Currently, stress detection is **reactive**—it is identified only after suicides, fratricides, breakdowns, or premature resignations. Between 2019 and 2024, CAPFs recorded **654 suicides** and nearly **50,000 voluntary resignations**, with CRPF alone reporting **281 suicides** (2025 recording 59 deaths). SAARTHI transforms this into a **predictive, welfare-first system** that detects operational fatigue and distress patterns weeks before a crisis occurs.

### Q2: Why can't existing military medical and psychiatric annual checks solve this?
**Answer:**  
Annual Medical Examinations (AME) happen once every 12 months in a sterile hospital setting. Acute stress, burnout, and acute marital/family crises develop over 30 to 90 days. Furthermore, walking into a military psychiatric clinic carries severe social and career stigma in uniformed units. SAARTHI provides continuous, non-intrusive monitoring using objective operational signals already generated in the daily duty roster (leave denials, consecutive duty hours, circadian rhythm disruption).

### Q3: What is the scope of your v1 solution?
**Answer:**  
As defined in our PRD (`docs/product/prd.md`), v1 delivers a closed-loop system:
1. **Signal Layer (F01):** Ingestion of 15+ HR/operational features from duty rosters and leave records.
2. **Jawan App (F02 & F03):** Roster access with an optional 10-second check-in and on-device acoustic prosody features.
3. **Inference Engine (F04):** Clinically grounded Rules Engine v1 with personal change-point baselines and masking flags.
4. **Intervention Engine (F05):** Response ladder (Green/Amber/Red/Critical), capacity triage, and workload rebalancing.
5. **Trust Layer (F08):** Architectural firewall guaranteeing $k \ge 5$ anonymity, dual-key unmasking, and "Who Viewed My Data" receipts.

### Q4: Are these suicide and resignation figures verified, or did your team estimate them?
**Answer:**  
They are official, verified public records cited in `docs/product/research-sih-2026.md` §7 and `docs/product/winning-strategy.md` §3. Sources include Government of India Ministry of Home Affairs statements in Parliament, ThePrint's investigation (*"654 suicides & 50,000 resignations in 5 years"*), and published CRPF records. Per AGENTS.md Rule 7, we never invent statistics; any unmeasured metric is explicitly labelled a reasoned estimate or Low/Med/High rating.

### Q5: Who is the primary target end-user within the force?
**Answer:**  
There are four distinct user roles, separated by architectural access boundaries (`docs/product/personas.md`):
1. **Jawan / Constable:** Uses the mobile app to view rosters, check leave balances, and take voluntary 10-second check-ins.
2. **Unit Welfare Officer / Subedar Major:** Reviews aggregated unit fatigue and approves non-punitive workload rebalancing.
3. **Unit Counsellor:** Reviews anonymized high-risk alert factors and initiates clinical outreach.
4. **Company/Battalion Commander:** Views strictly aggregated heatmaps ($k \ge 5$) to adjust operational deployment tempo.

### Q6: What does the name SAARTHI stand for?
**Answer:**  
SAARTHI (सारथी) translates to *the charioteer or trusted guide* (derived from the historic archetype of guidance without coercion). In our system, SAARTHI acts as a non-punitive digital companion that protects the jawan and routes help before exhaustion leads to catastrophe, while keeping individual health data completely shielded from commanders.

### Q7: What makes this a MedTech/HealthTech project rather than just an HR system?
**Answer:**  
HRMS records events (leave taken, shifts assigned); HealthTech interprets the biological and psychological toll of those events. SAARTHI models survival analysis curves for burnout, maps cumulative sleep debt and circadian disruption, screens using validated psychometric instruments (PHQ-9, GAD-7, PSS-10, ISI), and integrates directly with Tele-MANAS (14416), India's National Tele-Mental Health Programme.

---

## 2. AI, Model Theory & Rules Engine v1 vs ML v2 (Q8–Q15)

### Q8: Is SAARTHI using "real" Machine Learning, or is it just a set of if-else rules?
**Answer (Key SIH Question — ADR-0001):**  
In v1, we **deliberately implemented a clinically grounded, deterministic Rules Engine (ADR-0001)**. In defence and clinical healthcare, unexplainable black-box models trained on scraped or synthetic data are dangerous and irresponsible. On Day One, **zero labeled stress data exists for Indian CAPF personnel**. Claiming 99% accuracy with an XGBoost or deep learning model would be fabricated.  
Our v1 rules engine is transparent, fully auditable, and grounded in clinical psychiatric thresholds. It acts as the data-collection foundation: once professional counsellor session outcomes accumulate as verified ground-truth labels, **ML v2 trains via survival analysis ("time-to-burnout event")** as documented in `docs/explanation/ml-v2-data-collection-plan.md`.

### Q9: How do you explain the algorithm's decisions to a counsellor or commander?
**Answer:**  
By construction, every flag issued by SAARTHI includes its **Top-3 contributing factors with actual observed values** (`test-plan.md` TC-205). For example, an alert does not output a vague "Risk Score 82"; it explicitly states:  
*"Amber Alert: 47 consecutive duty days (baseline: 21), 2 consecutive cancelled leaves, sleep duration -30% vs baseline."*  
When ML v2 is introduced, SHAP (SHapley Additive exPlanations) values will be required on every inference (`docs/explanation/shap-report-template.md`).

### Q10: How do you handle false positives and false negatives?
**Answer:**  
We evaluate false alarms through **Cost-of-Error Economics** (`docs/product/winning-strategy.md` §2):
- **Cost of a False Positive:** A jawan has an informal, confidential cup of tea with a unit counsellor or peer buddy.
- **Cost of a False Negative:** Severe distress goes unnoticed, potentially resulting in suicide or operational loss of life.  
To prevent counsellor burnout from alert fatigue, we enforce **weekly triage caps** (TC-207) and prioritize alerts by *Urgency $\times$ Intervenability* (`test-plan.md` TC-302). Furthermore, **no automated action is taken without human counsellor sign-off**.

### Q11: What if a jawan fakes their daily check-in and always marks "I am feeling great"?
**Answer:**  
This is specifically handled by our **Discrepancy / Masking Flag (FR-07, TC-206)**. In uniformed forces, personnel often mask distress due to fear of stigma. If the HR signals show 60 consecutive duty days, 2 cancelled leaves, and severe sleep disruption, but the jawan submits *"I feel perfect"*, the discrepancy engine fires a masking warning:  
**"The faking is the finding."** The system detects the statistical anomaly between objective operational strain and self-reported wellness.

### Q12: Where did you get your testing and validation data?
**Answer:**  
We engineered an enterprise-grade **Synthetic Data Generator (F09, `data.gen`)** that generates 1,000 personnel over 90 days with deterministic seeding (`--seed 42`). It mathematically models real CAPF battalion rosters, deployment rotations, leave rejections, and includes our benchmark validation persona (*Constable, 34, 3rd Battalion*). It is backed by clinical distributions from published defense psychology research (WESAD, SWELL-KW, NCRB).

### Q13: What specific signals do you extract from HR and roster records?
**Answer:**  
F01 derives 15+ deterministic features across 4 clinical domains (`docs/features/F01-hr-signal-engine.md`):
1. **Duty Intensity:** Consecutive days on duty, double-shift occurrences, weekly overtime hours.
2. **Leave Friction:** Days since last earned leave, rejected leave applications, emergency leaves cancelled.
3. **Circadian Disruption:** Frequent night-shift to day-shift rotations within 48 hours.
4. **Isolation & Environment:** Distance from home state, high-altitude/counter-insurgency zone tenure.

### Q14: How does on-device voice analysis work without violating privacy?
**Answer (ADR-0002):**  
The jawan app records an optional 5-second voice check-in. **Zero audio bytes ever leave the device.** An on-device edge model extracts acoustic prosody features: pitch variance, vocal jitter, shimmer, harmonic-to-noise ratio (HNR), and speaking rate. Only this non-reconstructible mathematical vector ($< 1\text{ KB}$) is uploaded. No speech recognition, transcription, or raw audio is ever transmitted or stored.

### Q15: What psychometric instruments does SAARTHI support?
**Answer:**  
As documented in `docs/explanation/clinical-instruments.md`, SAARTHI supports shortened, validated clinical instruments:
- **PHQ-9 / PHQ-2:** Depression screener.
- **GAD-7 / GAD-2:** Generalized anxiety screener.
- **PSS-10:** Perceived Stress Scale.
- **ISI:** Insomnia Severity Index.  
Every test screen explicitly renders the disclaimer: *"Reflection support, not clinical diagnosis."*

---

## 3. Privacy, Firewall & Legal Compliance (Q16–Q24)

### Q16: How does SAARTHI comply with the Digital Personal Data Protection (DPDP) Act 2023?
**Answer:**  
SAARTHI implements a **strict legal dual-track basis (ADR-0003 & `docs/compliance/dpdp-2023-mapping.md`)**:
1. **Section 7(i) "Legitimate Use for Employment":** Applies strictly to operational duty rosters, attendance, and official leave logs. No consent is required for the force to analyze its own duty assignments.
2. **Sections 4 & 5 "Explicit, Revocable Consent":** Applies to all voluntary self-reports, psychometric surveys, and voice check-ins. Consent notices are multilingual, unbundled, unconditional, and provide single-tap withdrawal.
3. **Significant Data Fiduciary (SDF):** CRPF-scale deployment triggers SDF obligations, including Data Protection Officer (DPO) logging and 72-hour breach notification readiness.

### Q17: Can a Battalion Commander view an individual jawan's stress score?
**Answer (The Architectural Firewall — Non-Negotiable):**  
**No. Under no circumstances can a commander view an individual score.**  
This is enforced by our **Architectural Firewall (ADR-0003)** at the database and API routing level, not through UI hiding. If a commander JWT calls `/welfare/personnel/{id}`, the API returns a hard HTTP 403/404 rejection (`test-plan.md` TC-401). Commanders receive **only aggregated heatmaps** of units with $k \ge 5$ personnel. Stress data is strictly a welfare asset, never an appraisal, disciplinary, or promotion input.

### Q18: What is $k$-anonymity, and how does your system enforce it?
**Answer:**  
$k$-anonymity ensures that any data displayed represents at least $k$ distinct individuals, preventing re-identification. In SAARTHI, $k \ge 5$ (TC-402). If a specialized squad or outpost has only 4 personnel, the commander dashboard suppresses the individual cell and marks it *"Insufficient cohort size for aggregation"*. A commander can never isolate an individual's distress by filtering down to tiny units.

### Q19: What is "Dual-Key Unmasking," and when is it allowed?
**Answer (FR-16, TC-405):**  
All individual profiles are pseudonymous (`ps_xxxxxxxx`). To unmask a pseudonym in an acute, life-threatening psychiatric emergency, **two independent keys are required**:
1. The Unit Clinical Counsellor.
2. The Gazetted Welfare Officer.  
If either attempts to unmask alone, the API rejects the request. When both approve, the unmasking event is written to an immutable audit log, and an automated push receipt is sent to the jawan's phone.

### Q20: What is "Who Viewed My Data," and why is it important?
**Answer (FR-15, TC-404):**  
It is an access-transparency log on the jawan's mobile app. Whenever a counsellor opens an intervention record, the jawan's phone displays an immutable receipt showing:  
- Role of person who accessed it (e.g., "Unit Counsellor").
- Date and exact timestamp.
- Official clinical purpose.  
This builds institutional trust—jawans know their officers cannot secretly spy on their wellness data.

### Q21: What happens if a jawan withdraws their consent?
**Answer (FR-17, TC-407):**  
SAARTHI supports **Silent Consent Withdrawal**. When a jawan toggles off consent, their self-report and voice modules stop processing immediately. To prevent peer harassment or commander questioning, **the commander view does not change or display a "revoked" icon**. The withdrawal is completely silent to the command hierarchy.

### Q22: What is your data retention and purge policy?
**Answer (FR-18, TC-408):**  
We enforce a **90-Day Raw Data Expiry Cron Job**. Raw self-report questionnaire answers and voice vectors older than 90 days are permanently purged from the database. Only anonymized, derived longitudinal statistical trend markers are retained.

### Q23: How does SAARTHI comply with Section 23 of the Mental Healthcare Act 2017?
**Answer:**  
Section 23 of MHCA 2017 guarantees strict confidentiality of mental health records and explicitly forbids releasing psychiatric status to employers without informed consent or court order. By isolating clinical records from military command via ADR-0003, SAARTHI ensures legal compliance with national mental healthcare mandates.

### Q24: What stops a database administrator from tampering with the audit logs?
**Answer (NFR-08, TC-409):**  
The audit log is implemented as an **append-only ledger** at the PostgreSQL database engine level using strict row-level security and triggers that forbid `UPDATE` and `DELETE` queries. Any administrative break-glass invocation triggers an automated notification to the subject and is flagged in the system audit stream.

---

## 4. Software Architecture, Security & Offline-First (Q25–Q32)

### Q25: What is the full technology stack of SAARTHI?
**Answer (ADR-0006):**  
- **Backend:** Python 3.11+, FastAPI (asynchronous, OpenAPI-native), SQLAlchemy 2.0 ORM, PostgreSQL.
- **Mobile Client:** React Native / Expo with offline SQLite database.
- **Web Consoles:** Next.js, Tailwind CSS, Recharts for aggregate visualizations.
- **Security:** PyJWT with role-based access control (RBAC), bcrypt password hashing, TLS 1.3, AES-256 database encryption.

### Q26: How does SAARTHI work in remote border outposts with zero internet connectivity?
**Answer (ADR-0005 — Offline-First):**  
Personnel in Jammu & Kashmir, Northeast outposts, or Bastar jungle camps often operate under complete network blackout. The jawan mobile app uses **local SQLite storage with an idempotent sync queue (TC-601–605)**. A jawan can complete check-ins completely offline. When the device returns to base or connects to a local mesh/intranet, the queue automatically syncs using idempotency keys to prevent duplicate records.

### Q27: Can SAARTHI be deployed on-premise without foreign cloud dependencies?
**Answer:**  
**Yes, 100% on-premise and air-gappable.** Defense regulations strictly forbid hosting active CAPF operational personnel data on commercial public SaaS clouds (AWS, Google Cloud, Azure US). SAARTHI is packaged as self-contained Docker containers deployable on CRPF's private intranet servers (National Informatics Centre / MHA server perimeter).

### Q28: What is your database schema and architecture pattern?
**Answer:**  
We follow the **arc42-lite and C4 Model (Level 1 Context, Level 2 Container)** documented in `docs/architecture/architecture.md`. Data is strictly segregated into three relational schemas:
1. `hr_core`: Roster, deployment, leave records.
2. `welfare_clinical`: Pseudonymous check-ins, instrument responses, counsellor clinical notes.
3. `audit_ledger`: Immutable access receipts and security logs.

### Q29: What is the system's performance and scalability envelope?
**Answer (NFR-06, TC-701 & TC-702):**  
- Full risk recalculation for a standard battalion of **1,000 personnel over a 90-day window executes in under 60 seconds** on standard laptop hardware.
- Cold-start commander aggregate heatmap queries execute in under **200 milliseconds** (well under the 2-second SLA).

### Q30: How do you prevent SQL injection, broken authentication, and unauthorized scraping?
**Answer:**  
- **SQL Injection:** 100% parameterized queries via SQLAlchemy 2.0 ORM; no raw SQL concatenation.
- **Authentication:** Scoped JWT tokens with short expiry, cryptographic signature verification, and granular RBAC middleware.
- **Scraping Prevention:** Rate-limiting via middleware and route enumeration guards tested via `test_firewall.py` (TC-403).

### Q31: How does your synthetic data generator ensure byte-identical reproducibility?
**Answer (TC-501):**  
The generator (`backend/app/seed.py` / `data.gen`) uses deterministic pseudo-random seeding (`seed=42`). Running the seed generation twice produces identical database states, identical foreign key relationships, and identical risk escalation days for our test personas.

### Q32: What happens if an app process is killed in the middle of an offline synchronization?
**Answer (TC-605):**  
The mobile sync manager wraps batch uploads in atomic SQLite transactions. If the process is terminated mid-upload, unacknowledged payloads remain in the `PENDING` queue state. Upon relaunch, sync resumes from the last confirmed checkpoint without data duplication or database corruption.

---

## 5. User Adoption, Stigma & Jawan UX (Q33–Q38)

### Q33: "Police wala kyu use karega?" (Why would a jawan actually use this app daily?)
**Answer (Key Winning Strategy — ADR-0004):**  
If you give a soldier a "Mental Health Questionnaire App", they will delete it or ignore it.  
Instead, SAARTHI uses a **Roster-App-First Strategy (ADR-0004 & `docs/product/adoption-strategy.md`)**. Jawans check the app every day because it is their primary tool to view their **duty shifts, upcoming patrol assignments, leave status, and digital pay-slips**. The wellness check-in is an unobtrusive, 10-second optional slider integrated into the screen they already use.

### Q34: How do you eliminate the stigma associated with mental health in the barracks?
**Answer:**  
1. **Language:** We ban psychiatric jargon. We do not use words like "depression", "psychiatric disorder", or "mental illness". We use operational wellness terms: *Fatigue index, rest deficit, operational readiness, recovery*.
2. **Never-Therapy Framing:** Framed as physical and operational stamina support.
3. **No Coercion:** Non-participation contributes zero penalty points.
4. **Peer Support:** Jawans can opt into a peer "Battle-Buddy" check-in system rather than a medicalized doctor visit.

### Q35: How does the UI cater to jawans with mixed literacy or regional backgrounds?
**Answer (NFR-04, TC-606 & TC-607):**  
- **Icon-First Design:** Visual mood dials, emoji sliders, and audio-prompt support designed for low-literacy usage.
- **Full Localization:** Hindi and English natively supported with zero hardcoded literals; all text resolves from `i18n` resource files.
- **Low-End Android Optimization:** Verified on Android API 26 (Android 8.0) with 1 GB RAM hardware profiles.

### Q36: What is the 10-Second Daily Check-in?
**Answer (FR-02, TC-201):**  
A micro-interaction consisting of three rapid visual sliders:
1. Sleep hours and sleep quality icon.
2. Physical exhaustion dial.
3. Mood / energy rating.  
The flow takes less than 10 seconds to complete and queues locally if offline.

### Q37: What is the "Battle-Buddy" pairing feature?
**Answer (FR-19, APP-009):**  
Uniformed forces operate on buddy pairs (दोस्त / साथी). If a jawan's indicators enter the Amber threshold, SAARTHI can send a gentle nudge to their designated barracks buddy: *"Your buddy has had 5 straight night shifts. Grab a cup of chai together."* This leverages natural military camaraderie before formal clinical escalation.

### Q38: Can a jawan use SAARTHI to correct their own data?
**Answer:**  
Yes. Under the DPDP Act 2023 Right to Correction, jawans have full transparency to review their historical voluntary logs and submit dispute requests if an entry was made erroneously.

---

## 6. Interventions, Triage & Workload Optimization (Q39–Q44)

### Q39: What is the "Response Ladder," and how do cases progress?
**Answer (FR-09, TC-301):**  
SAARTHI implements a 4-tier Response Ladder (`docs/features/F05-intervention-engine.md`):
- **Green (Normal):** Self-help resources, leave countdowns, sleep hygiene tips.
- **Amber (Elevated Strain):** Peer buddy nudge, informal JCO check-in, voluntary rest recommendation.
- **Red (Acute Distress / Discrepancy):** Unit counsellor outreach task initiated with a mandatory **$\le 24$-hour SLA**; workload rebalancing proposed.
- **Critical (Imminent Danger / Crisis):** Immediate dual-key unmasking, commanding officer safety notification (without medical details), and Tele-MANAS medical handoff.

### Q40: What is the Workload Rebalancing Optimizer?
**Answer (FR-11, TC-303):**  
When personnel cross into Red status due to consecutive night duties or extended deployments, SAARTHI's greedy optimization algorithm scans unit rosters for qualified peers in the same company who have low cumulative duty hours. It generates an **automated swap proposal** that reduces peak individual fatigue. Crucially, **the swap remains a proposal until the Welfare Officer reviews and approves it**.

### Q41: How does SAARTHI integrate with Tele-MANAS?
**Answer (FR-13, TC-305):**  
Tele-MANAS (14416) is the Government of India's 24/7 free tele-mental health helpline. For personnel requiring external clinical consultation or remote specialized care, SAARTHI generates a secure referral record, logs the handoff, and records the session outcome for recovery tracking.

### Q42: How do you prevent clinical counsellors from being overwhelmed by alert fatigue?
**Answer (FR-10, TC-207 & TC-302):**  
In large battalions, hundreds of personnel face hard conditions. If 200 alerts fire at once, counsellors experience alert fatigue and miss critical cases. SAARTHI applies a **Triage Capacity Cap**:
- Alerts are mathematically ranked by **Urgency $\times$ Intervenability**.
- Caseloads are capped at a maximum of 15 active high-priority investigations per counsellor per week.
- Suppressed lower-priority alerts are logged with explicit reasoning rather than vanishing silently.

### Q43: How do you verify that an intervention actually worked?
**Answer (FR-12, TC-304):**  
When a counsellor closes an outreach case, they log a standardized session outcome: *Resolved, Follow-up Scheduled, Roster Adjusted, Medical Leave Recommended*. SAARTHI tracks the longitudinal risk trend post-intervention. In our demo persona (*Constable, 34, 3rd Bn*), approved roster adjustments cause the composite fatigue score to drop from 78 (Red) down to 32 (Green) over 14 days, mathematically proving loop closure.

### Q44: Can an officer penalize a jawan based on an intervention recommendation?
**Answer:**  
No. Workload rebalancing proposals are legally framed as **medical duty rest recommendations**, not disciplinary actions. Under our compliance charter, using an intervention recommendation to lower an Annual Confidential Report (ACR) grade is an explicit violation of force policy.

---

## 7. Competition, Feasibility & 36-Hour Hackathon Plan (Q45–Q50)

### Q45: Why can't the CRPF simply purchase commercial off-the-shelf software like Headspace, Practo, or corporate Employee Assistance Programs (EAPs)?
**Answer (Key Strategic Differentiator):**  
Commercial EAPs completely fail in military environments (`docs/product/winning-strategy.md` §5):
1. **Security & Air-Gapping:** Foreign cloud-hosted SaaS violates Indian defense data classification guidelines.
2. **Operational Fit:** Corporate apps do not ingest military duty rosters, weapon handling rosters, or outpost deployment logs.
3. **Connectivity:** Commercial wellness apps require constant 4G/5G broadband; SAARTHI works 100% offline.
4. **Cultural Register:** Jawans will not respond to western corporate mindfulness apps; SAARTHI speaks in the jawan's language and operational reality.

### Q46: What did your team deliberately choose NOT to build? (The "Anti-Goals")
**Answer (High-Maturity Answer — `docs/product/winning-strategy.md` §4):**  
- **No Facial Emotion Recognition / CCTV Scanning:** Pseudoscience in unconstrained environments; perceived as intrusive mass surveillance.
- **No WhatsApp, SMS, or Phone Call Tapping:** Highly invasive, trust-destroying, and unconstitutional under Indian privacy law.
- **No Predictive Machine Learning on Day One:** No ground-truth labels exist; deploying an unverified black box is dangerous.
- **No Disciplinary / Appraisal Integrations:** The firewall is architectural.

### Q47: What is your exact 36-Hour Implementation Plan for the SIH Grand Finale?
**Answer (`docs/deck/deck-outline.md` Slide 10 & `docs/quality/finale-36h-plan.md`):**  
- **Hours 0–4 (Environment & Data Seeding):** Pre-configured Docker compose stack setup; seed 1,000 synthetic personnel with seed 42.
- **Hours 4–12 (Signal Engine & Rules Core):** Verify 15+ HR signal calculations, threshold triggers, and discrepancy detection.
- **Hours 12–20 (Jawan Client Flow):** Roster view, offline 10-second check-in, consent toggle, and "Who Viewed My Data" screen.
- **Hours 20–28 (Dual Consoles & Privacy Firewall):** Counsellor explainability console, commander $k \ge 5$ aggregate heatmap, dual-key unmask endpoint.
- **Hours 28–34 (Full E2E Persona Loop Integration):** Walkthrough of Constable 34's 90-day arc; verify automated pytest firewall suite.
- **Hours 34–36 (Buffer, Demo Dry-Run & Rehearsal):** 5 full rehearsals against the 3-minute script; test offline video fallbacks.

### Q48: Who pays for this system after the hackathon? What is the business and deployment model?
**Answer:**  
SAARTHI is commissioned by the **Ministry of Home Affairs for the Central Armed Police Forces (CRPF, BSF, CISF, ITBP, SSB)**. Funding is allocated under existing MHA Central Armed Police Forces Welfare and IT Modernization budgets. Once piloted in a single CRPF sector, deployment scales nationally across state police forces and disaster response forces (NDRF).

### Q49: How will you conduct an initial pilot to prove the system works?
**Answer (`docs/product/impact-and-metrics.md`):**  
We propose a **90-day single-battalion pilot (1,000 personnel)** with pre-defined, honest success metrics:
- Voluntary check-in participation rate $\ge 30\%$ (reasoned estimate).
- Red alert-to-counsellor contact time $\le 24\text{ hours}$.
- Zero individual score leaks to commanding officers (architectural verification: 0).
- Zero punitive actions linked to wellness records (monitored: 0).

### Q50: If our live demo fails on stage right now, what is your fallback?
**Answer (`docs/quality/demo-runbook.md` §4 & §7):**  
We follow our strict **Demo Doctrine**:
1. We have our complete backend running locally in an air-gapped container (`docker compose` / local SQLite).
2. If the laptop or projector fails, we immediately play our pre-recorded **1080p 6-shot fallback video (`SAARTHI-demo-fallback-YYYYMMDD.mp4`)** stored on two independent USB pen drives and backup mobile devices.
3. We will never debug on stage or say *"it usually works"*; our video fallback covers every beat of the 90-day persona walkthrough in under 90 seconds.
