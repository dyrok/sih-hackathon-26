# Datasets & Research — Evidence Base for SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Rule (AGENTS.md #6): no invented statistics. Every number below carries its source; anything without one is a reasoned estimate and is labelled as such.

## 1. Why this page exists

PS 26186 supplies both a **crisis context** and a **data bundle**. The engineering challenge is using each for what it can honestly support — and refusing to claim more. This page separates: (a) evidence that frames the problem, (b) public datasets that pretrain passive-signal models, (c) the PS-offered datasets that drive the prototype, (d) our own synthetic data.

### The crisis context (cited reporting — real, not illustrative)

- **654 CAPF suicides and ~50,000 resignations in 5 years** — ThePrint, "the crisis stalking India's CAPFs" (Sources below).
- **CRPF recorded 281 suicides in 5 years, with 59 in 2025** — RNA Media / Uttam Hindu reporting (Sources below).
- **Police suicides** — the NCRB *Accidental Deaths & Suicides in India* (ADSI) annual reports publish suicides by police personnel.
- **Workload & rest** — *Status of Policing in India Report 2019* (Common Cause) documents duty hours exceeding statutory norms and weekly offs routinely unavailable to police personnel.
- **CAPF suicides** — MHA replies to Parliament questions are the government's own accounting of the toll.

These figures justify urgency in the deck and the demo. They are **not** model inputs.

## 2. Dataset table — what each can and cannot be used for

| Dataset | What it is | Can be used for | Cannot be used for |
|---|---|---|---|
| **WESAD** (Schmidt et al. 2018) | 15 participants, lab stress protocol (TSST), chest+wrist multimodal signals (ECG, EDA, TEMP, ACC…) | Pretraining and validating **passive-signal feature models** — HRV/EDA/temperature feature encodings for stress classification ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) adjacent) | Any deployment decision; any claim of validity on Indian uniformed personnel (n=15, civilian, laboratory) |
| **SWELL-KW** (Koldijk et al. 2014) | 25 office workers; computer-usage + body signals across happy/neutral/stressed/interrupted conditions | Pretraining behavioural/workload signal models; feature-engineering head start for passive v2 signals | Force-population claims — the context (desk knowledge work) is nothing like duty rotations |
| **PS-offered datasets** (PS 26186 dataset link) | Anonymized HR datasets, deployment records, leave history, wellness survey data, workload data, simulated behavioral datasets | Schema modelling ([F01](../features/F01-hr-signal-engine.md)), rules-engine backtesting (ML-002), grounding demo data in realistic shapes | Clinical-validation claims — provenance, sampling frame and labelling quality are not under our control |
| **NCRB ADSI** | Annual official suicide statistics, incl. police personnel | Problem framing, needs assessment, aggregate benchmarks | Model training — aggregates only, no per-person features |
| **SPIR 2019** (Common Cause) | Survey report on police adequacy and working conditions | Grounding workload/rest signals in documented national reality | Deriving numerical thresholds — survey-based, not per-person clinical data |
| **MHA / Parliament answers** | Government replies on CAPF suicide counts | Crisis framing; tracking the trajectory the system must help bend | Training; statistical inference on small aggregates |

## 3. Transfers and their limits (why pretraining ≠ validation)

Pretraining passive-signal models on WESAD/SWELL-KW buys a **feature-encoding head start**, not validated thresholds. Two domain shifts intervene:

- **Population shift** — lab civilians vs deployed uniformed personnel (fitness, sleep debt, operational arousal differ).
- **Context shift** — controlled stressor protocols vs chronic, ambiguous field stress.

So: pretrained encoders may seed v2 passive-signal models; **every threshold that reaches the rules engine must still come from the instrument/citation chain in [clinical-instruments.md](clinical-instruments.md)**, not from a public dataset's labels.

## 4. Licensing & ethics notes

- **WESAD / SWELL-KW** — research-use datasets with citation obligations (Schmidt et al. 2018; Koldijk et al. 2014). Obtain via their official request forms/portals; no commercial use implied; used only to pretrain passive-signal *feature* models — no force data is touched.
- **No CAPF personnel data** enters training or evaluation in v1. Any future collection requires explicit consent under DPDP 2023 ([dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md)). NCRB/MHA/SPIR material is used at aggregate level only — no de-anonymization attempts.
- **Simulated stays labelled simulated.** The PS-offered *simulated behavioral datasets* are marked "simulated" in every artifact and on the deck — the demo always says what is simulated vs real.
- Welfare-not-discipline boundary ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)) applies to any dataset: nothing here may feed appraisal or disciplinary flows.

## 5. Synthetic data — the demo strategy (F09)

The prototype's ~1,000-personnel unit with a 90-day history is **generated, not collected**: [F09](../features/F09-synthetic-data-generator.md) defines the personas, roster/leave/deployment patterns and the scripted escalation persona ("Constable, 34, 3rd Bn"). Rationale:

- A welfare system for a uniformed force must never rely on (or imply) real personnel records in a public demo.
- Synthetic data lets the rules engine be **backtested deterministically** (ML-002, [test-plan.md](../quality/test-plan.md)) — the scripted 90-day escalation must reproduce exactly.
- Realistic Indian-context seeded data was a losing demo's failure mode and a winner's tactic; F09 makes it systematic.

## 6. Open questions

- PS-offered dataset access mechanics and actual schema — confirm at the finale; until then [F01](../features/F01-hr-signal-engine.md) models the HRMS schema on published MHA/CRPF structures.
- A Hindi/Hinglish-validated passive-signal (voice prosody) corpus does not exist to our knowledge; unless one surfaces, voice features stay weighted low ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)) — this is a reasoned estimate about the literature, flagged for verification with the clinical advisor.

## 7. Deck-claim discipline (what the evidence lets us say)

| Claim we may make | Evidence it rests on |
|---|---|
| "654 CAPF suicides and ~50,000 resignations in 5 years" | ThePrint (Sources) |
| "CRPF: 281 suicides in 5 years, 59 in 2025" | RNA Media / Uttam Hindu (Sources) |
| "Duty hours exceed statutory norms; weekly offs routinely unavailable" | SPIR 2019 (Common Cause) |
| "No labelled stress-outcome data exists for CAPF personnel" | Reasoned claim — absence of public labelled datasets; team-reviewed 2026-09-05 |
| "Passive-signal pretraining reduces feature-engineering risk" | Reasoned estimate — no force-specific corpus exists to verify it |

Every impact number on a slide must resolve to a row here, to the crisis context in §1, or to [model-explainer.md](model-explainer.md). If a judge asks "where is that from?", the answer is one click away.

## Sources

- ThePrint — 654 suicides, 50,000 resignations in 5 years: https://theprint.in/india/654-suicides-50000-resignations-in-5-years-the-crisis-stalking-indias-capfs/1787191/
- RNA Media — CRPF suicides rising, 59 in 2025: https://www.rnamedia.in/top-story/crpf-faces-sharp-rise-in-suicides-as-59-personnel-die-in-2025/19636
- Uttam Hindu — CRPF records 281 suicides in 5 years: https://www.theuttamhindu.com/india/crpf-records-281-suicides-554304
- NCRB — Accidental Deaths & Suicides in India (annual): https://ncrb.gov.in
- Common Cause — Status of Policing in India Report 2019: https://www.commoncause.in
- Schmidt P et al. (2018) — WESAD, ACM IMWUT 2(3), Art. 119.
- Koldijk S et al. (2014) — The SWELL Knowledge Work Dataset, ACM ICMI.
