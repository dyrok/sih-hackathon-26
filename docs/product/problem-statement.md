# Problem Statement — SIH 2026 PS 26186

> Owner: kv · Status: [x] frozen (verbatim PS; interpretation reviewed 2026-09-05) · Last updated: 2026-09-05

## 1. Official statement (verbatim)

| Field | Value |
|---|---|
| Problem Statement ID | 26186 |
| Title | AI-Based Predictive Personnel Stress and Welfare Monitoring System for Uniformed Forces |
| Organization | Ministry of Home Affairs |
| Department | Central Reserve Police Force (CRPF), Police II Division |
| Category | Software |
| Theme | MedTech / BioTech / HealthTech |
| Dataset Link | Anonymized HR datasets, deployment records, leave history, wellness survey data, workload data, and simulated behavioral datasets |

### Description (verbatim)

Personnel serving in Central Armed Police Forces (CAPFs), Armed Forces, and other uniformed services operate under physically demanding, psychologically stressful, and often hazardous conditions. Extended deployments, operational pressures, separation from families, irregular working hours, and exposure to traumatic incidents can significantly impact mental well-being. Currently, stress identification largely depends on manual observation and self-reporting, which may delay timely intervention. There is a need for a proactive, technology-driven solution that can identify early indicators of stress, burnout, and psychological distress while maintaining privacy and organizational trust.

The proposed solution aims to develop an AI-powered Personnel Stress and Welfare Monitoring System capable of identifying potential indicators of stress, burnout, emotional fatigue, and welfare concerns through analysis of organizational and voluntarily provided wellness data. The system should:

- Analyze HR-related indicators such as leave patterns, deployment history, duty schedules, transfer frequency, training commitments, and workload trends.
- Support optional self-reporting and wellness assessments through a secure mobile application.
- Incorporate voluntary biometric and wellness data, where authorized and legally permissible.
- Detect behavioral patterns associated with elevated stress risk.
- Generate risk assessments and welfare recommendations for authorized welfare officers and commanders.
- Enable proactive counseling, welfare interventions, and workload balancing measures.

The system must be designed with strong privacy safeguards and focus on welfare support rather than disciplinary actions.

### Expected Solution (verbatim)

- Personnel Wellness Monitoring Dashboard.
- Mobile-based Wellness and Self-Assessment Application.
- Predictive Behavioral Analytics Engine.
- Stress and Burnout Risk Prediction Models.
- Welfare Intervention Recommendation System.
- Role-based Access Control and Privacy Management Framework.
- Automated Alerts for authorized welfare personnel.
- Data anonymization and secure storage mechanisms.

### Key Technical Challenges (verbatim)

1. Ensuring privacy and confidentiality of sensitive personnel data.
2. Preventing stigmatization of personnel identified as potentially at risk.
3. Minimizing false positives and false negatives in risk prediction.
4. Ensuring ethical and transparent AI decision-making.
5. Securing highly sensitive psychological and welfare-related information against cyber threats.
6. Building trust among personnel regarding system usage and data protection.

### Strategic Importance (verbatim)

- Enhances force readiness and personnel welfare.
- Supports evidence-based welfare management.
- Strengthens organizational resilience and operational effectiveness.
- Promotes preventive mental health care rather than reactive interventions.
- Creates an indigenous capability tailored to the unique operational and cultural environment of Indian CAPFs and Armed Forces.

## 2. Our interpretation

The PS asks for a **welfare loop, not a detection demo**: detect → explain → intervene → verify recovery. The eight expected components collapse into four subsystems (see [architecture.md](../architecture/architecture.md)):

1. **Signal layer** — HR data (zero-effort: works even if nobody opens the app) + voluntary mobile self-reports + passive wellness data.
2. **Inference layer** — clinically grounded rules engine v1, ML v2 trained on counsellor labels; per-person baselines, not absolute thresholds; every alert explainable.
3. **Intervention layer** — response ladder (self-help → buddy → counsellor → duty modification), workload rebalancing, Tele-MANAS integration.
4. **Trust layer** — two-tier output (individual → counsellor only; commander → unit aggregate only, k ≥ 5), who-viewed-my-data transparency, dual-key unmasking, immutable audit.

The six "Key Technical Challenges" are treated as **design constraints**, not afterthoughts — each maps to a documented mechanism in `docs/compliance/` and `docs/features/F08`.

## 3. Scope

**In scope (v1 prototype):**
- HR signal ingestion + risk scoring rules engine (F01, F04)
- Jawan mobile app: 10-second check-in, validated instruments, consent, who-viewed-my-data (F02, F03)
- Welfare officer console with explainable alerts + intervention tracking (F06)
- Commander dashboard: unit-aggregate heatmap, morale index (F07)
- Privacy architecture: k-anonymity ≥ 5, dual-key unmasking, audit log, 90-day raw-data expiry (F08)
- Synthetic data generator for demo (~1,000 personnel, 90-day history) (F09)
- DPDP 2023 + Mental Healthcare Act 2017 compliance mapping

**Out of scope (deliberately not built — see ADR-0001 and F08 §anti-goals):**
- Facial emotion recognition (covert or CCTV) — contested science, reads as surveillance
- Phone monitoring / relationship trackers — kills trust, likely illegal under DPDP
- Risk scores in any appraisal/ACR/promotion data flow — architectural firewall
- Clinical diagnosis or treatment decisions — screeners are reflection support, not diagnosis
- ML trained on day one — no labelled data exists; v1 is a transparent rules engine

**Post-prototype future scope:** ML v2 from counsellor labels, federated per-battalion training, differential-privacy noise on aggregates, wearables integration.
