# Ayush's Work Log & Research Notes

> Owner: ayush (ML research assistant · 1st year) · Branch: `ayush`  
> Purpose: Single location for research verification findings, factsheets, and requests for KV.  
> Non-negotiable rule (AGENTS.md): No invented statistics · Every claim must carry a source link · Do not edit other members' files.

---

## Task ML-005 — Link & Citation Verification: `docs/explanation/datasets-research.md`

- **Task ID**: `ML-005`
- **Assigned to**: ayush (ML research support)
- **Target document inspected**: [`docs/explanation/datasets-research.md`](../../docs/explanation/datasets-research.md) (Owned by `neel`)
- **Verification Date**: 2026-09-08
- **Status**: Completed (Merged into `main` via PR #1)

### 1. Verification Summary Table

| # | Item / Reference in Document | Classification | Live Verified Target / Alternative | Notes & Findings |
|---|---|---|---|---|
| 1 | **ThePrint Article** (§1, §7, §Sources)<br>`https://theprint.in/india/654-suicides-50000-resignations-in-5-years-the-crisis-stalking-indias-capfs/1787191/` | **Working** | `https://theprint.in/india/654-suicides-50000-resignations-in-5-years-the-crisis-stalking-indias-capfs/1787191/` | Live HTTP 200. Headline: *"654 suicides & 50,000 resignations in 5 years — the crisis stalking India’s CAPFs"*. Confirms 654 CAPF suicides and ~50,000 resignations in 5 years. |
| 2 | **RNA Media Article** (§1, §7, §Sources)<br>`https://www.rnamedia.in/top-story/crpf-faces-sharp-rise-in-suicides-as-59-personnel-die-in-2025/19636` | **Working** | `https://www.rnamedia.in/top-story/crpf-faces-sharp-rise-in-suicides-as-59-personnel-die-in-2025/19636` | Live HTTP 200. Headline: *"CRPF faces sharp rise in suicides as 59 personnel die in 2025"*. Confirms 59 CRPF suicide deaths in 2025 and 5-year peak. |
| 3 | **The Uttam Hindu Article** (§1, §7, §Sources)<br>`https://www.theuttamhindu.com/india/crpf-records-281-suicides-554304` | **Working** | `https://www.theuttamhindu.com/india/crpf-records-281-suicides-554304` | Live HTTP 200. Headline: *"CRPF records 281 suicides in five years, 2025 sees highest number of cases"*. Confirms breakdown: 57 (2021), 43 (2022), 57 (2023), 46 (2024), 59 (2025), plus 19 to July 2026 = 281 total (237 non-gazetted). |
| 4 | **National Crime Records Bureau (NCRB)** (§1, §2, §Sources)<br>`https://ncrb.gov.in` | **Working** *(General domain)* | Base: `https://ncrb.gov.in`<br>Direct report: `https://ncrb.gov.in/accidental-deaths-suicides-in-india-adsi.html` | Live HTTP 200. Base portal is up. Accurate for official *Accidental Deaths & Suicides in India (ADSI)* reports covering police and security suicides. |
| 5 | **Common Cause (SPIR 2019)** (§1, §2, §7, §Sources)<br>`https://www.commoncause.in` | **Working** *(General domain)* | Base: `https://www.commoncause.in`<br>Report: *Status of Policing in India Report 2019: Police Adequacy and Working Conditions* | Live HTTP 200. Base portal up. SPIR 2019 (joint with CSDS/Lokniti, survey of 11,834 police across 20+ states) directly substantiates the claim that duty hours exceed statutory limits and weekly offs are routinely unavailable. |
| 6 | **Schmidt P et al. (2018) — WESAD** (§2, §4, §Sources)<br>Doc: `ACM IMWUT 2(3), Art. 119` | **Citation Correction Needed** | **Proceedings of the 20th ACM International Conference on Multimodal Interaction (ICMI '18)** | Paper content matches: 15 participants, TSST laboratory stress protocol, chest/wrist multimodal signals (ECG, EDA, EMG, TEMP, ACC, Resp). **Venue Error**: The paper was published in *ACM ICMI '18* (pp. 400–408, DOI: `10.1145/3242969.3242985`), not *ACM IMWUT*. |
| 7 | **Koldijk S et al. (2014) — SWELL-KW** (§2, §4, §Sources)<br>Doc: `ACM ICMI` | **Working** | **16th ACM International Conference on Multimodal Interaction (ICMI 2014)** | Exact match: *The SWELL Knowledge Work Dataset for Stress and User Modeling Research*, ACM ICMI 2014, pp. 291–298, DOI: `10.1145/2663204.2663257`. 25 knowledge workers across neutral, stress, and interruption conditions. |
| 8 | **PS-offered datasets** (§2, §6)<br>`PS 26186 dataset link` | **Unclear / Needs Manual Review** | SIH 2026 Portal Link | Linked to SIH 26186 problem statement bundle. Access to the raw files requires portal login; properly handled in docs as schema guidance rather than clinical ground truth. |
| 9 | **MHA / Parliament Answers** (§1, §2) | **Working** *(Official Record)* | Lok Sabha & Rajya Sabha Question Archives | Official parliamentary replies on CAPF suicide and resignation statistics. |

---

### 2. Suggested Updates for Neel (Owner of `docs/explanation/datasets-research.md`)

When Neel next updates `docs/explanation/datasets-research.md`, the following corrections and improvements are recommended:

1. **Fix WESAD Citation in Section Sources (Line 79)**:
   - *Current*: `Schmidt P et al. (2018) — WESAD, ACM IMWUT 2(3), Art. 119.`
   - *Proposed*: `Schmidt P, Reiss A, Duerichen R, Marberger C, Van Laerhoven K (2018) — Introducing WESAD, a Multimodal Dataset for Wearable Stress and Affect Detection. In Proceedings of the 20th ACM International Conference on Multimodal Interaction (ICMI '18), pp. 400–408. DOI: 10.1145/3242969.3242985.`

2. **Add Deep Links to Publication Sources**:
   - For NCRB ADSI: Replace `https://ncrb.gov.in` with `https://ncrb.gov.in/accidental-deaths-suicides-in-india-adsi.html`
   - For SWELL-KW: Add DOI link: `https://doi.org/10.1145/2663204.2663257`
   - For WESAD: Add DOI link: `https://doi.org/10.1145/3242969.3242985`

---

### 3. Requests / Questions for KV (PM & Maintainer)

- **Q1 (PS Dataset bundle confirmation)**: Once portal access is opened for the team, can we confirm the exact column names for the simulated HR/leave/deployment dataset so we can verify consistency with [`docs/features/F01-hr-signal-engine.md`](../../docs/features/F01-hr-signal-engine.md)?
- **Q2 (Promotion of citation fixes)**: Should the WESAD citation fix be batched with Neel's next feature doc update, or would you prefer a separate doc-fix PR after ML-006?

---

## Task ML-006 — One-Page Clinical Instrument Factsheet

- **Task ID**: `ML-006`
- **Assigned to**: ayush (ML research support)
- **Primary Source Document**: [`docs/explanation/clinical-instruments.md`](../../docs/explanation/clinical-instruments.md) (Owner: `neel`)
- **Status**: Completed

### 1. Four Core Clinical Instruments Factsheet

| Instrument | Primary Purpose / Function | Number of Items | Score Range | Scoring Bands / Cutoffs | Important Scoring Notes | Source / Citation |
|---|---|---|---|---|---|---|
| **PHQ-9** | Depressive symptom severity screening (mirrors DSM-IV MDD criteria) | **9** | **0–27** | • `0–4`: Minimal<br>• `5–9`: Mild<br>• `10–14`: Moderate<br>• `15–19`: Moderately severe<br>• `20–27`: Severe<br>• **Positive Screen**: `≥10` | • **Human Safety Protocol**: Item 9 (thoughts of self-harm) triggers immediate human safety protocol (Counsellor / Tele-MANAS `14416` routing), never app-only triage.<br>• Validated for brief administration and widely translated (including Hindi). | Kroenke K, Spitzer RL, Williams JBW (2001) — PHQ-9, *J Gen Intern Med* 16(9):606–613. |
| **GAD-7** | Generalized anxiety symptom severity screening | **7** | **0–21** | • `0–4`: Minimal<br>• `5–9`: Mild<br>• `10–14`: Moderate<br>• `15–21`: Severe<br>• **Positive Screen**: `≥10` | • Designed specifically for rapid repeat administration.<br>• Powers intra-individual longitudinal trend measurement (velocity tracking). | Spitzer RL, Kroenke K, Williams JBW, Löwe B (2006) — GAD-7, *Arch Intern Med* 166(10):1092–1097. |
| **PSS-10** | Perceived situational stress over the past month | **10** | **0–40** | • **No diagnostic clinical cutoff** in the literature.<br>• Interpreted against population norms and personal baseline trajectory. | • **Reverse Scoring**: Items 4, 5, 7, and 8 are reverse-scored.<br>• Evaluates situational/duty stressors (roster rotations, separation) as baseline deviations in the rules engine. | Cohen S, Kamarck T, Mermelstein R (1983) — PSS, *J Health Soc Behav* 24(4):385–396. |
| **ISI** | Insomnia & sleep disruption severity screening | **7** | **0–28** | • `0–7`: None (absence of insomnia)<br>• `8–14`: Subthreshold insomnia<br>• `15–21`: Moderate insomnia<br>• `22–28`: Severe insomnia<br>• **Positive Screen**: `≥15` (clinically significant) | • Core signal for duty-rotated forces.<br>• Triangulated with roster-derived circadian disruption score and on-device voice features. | Bastien CH, Vallières A, Morin CM (2001) — ISI, *Sleep Medicine* 2(4):297–307. |

---

### 2. Relevant System Boundaries & Guardrails (Explicitly Documented)

1. **Mandatory Bilingual Disclaimer (§5)**:
   - Every instrument view must visibly display: **यह निदान नहीं, आत्म-चिंतन का सहारा है — reflection support, not diagnosis** (i18n: `instr.not_diagnosis`).
   - The system never outputs clinical diagnoses and never gates operational duty assignments on instrument scores.
2. **Cadence Pairing (§6)**:
   - **Monthly Full Battery**: Provides validated anchor scores with population-level meaning (~5 min total).
   - **Daily Check-in**: 10-second emoji/slider check-in captures velocity/trend between monthly anchors (not a diagnostic tool).
3. **Response-Pattern Defences (§4)**:
   - Identifies straight-lining, all-max responses, and completion speeds too fast to read questions.
   - Flagged patterns raise the masking flag (FR-07) to route support rather than applying penalties.

---

### 3. Open Points & Clarifications Flagged for KV

- **Open Point 1 (Hindi Version Clinical Sign-Off)**: While validated Hindi translations exist in Indian psychiatric research, the exact dialect and phrasing must be formally signed off by the clinical advisor prior to deployment (owner: ML-001).
- **Open Point 2 (PSS-10 Risk Engine Thresholds)**: Because PSS-10 has no universal diagnostic cutoff in clinical literature, the rules engine interprets it via intra-individual delta / $Z$-score deviations rather than a fixed cutoff number.
