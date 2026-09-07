# Winning Strategy — SIH 2026, PS 26186

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05
> Distilled from [research-sih-2026.md](research-sih-2026.md) (official Guidelines + Evaluation Guideline PDFs, winner accounts). This is the team's working strategy — the raw research stays the source of truth.

## 1. How SIH scores us (official rubric)

Final score = **Round 1 (20%) + Round 2 (30%) + Round 3 (50%)**, 3 independent evaluators, each criterion scored 1–20:

| Round | Weight | Criteria |
|---|---|---|
| R1 — Idea | 20% | Presentation/fit · Innovation · Solution approach · Technical feasibility · **36-hour execution timeline** |
| R2 — Prototype | 30% | Prototype progress · **Improvement on evaluator/mentor feedback** · Integration · Usability · Teamwork |
| R3 — Finale demo | 50% | Functionality/PS-relevance · Demo clarity & persuasiveness · UX/aesthetics · Market readiness/impact · Future scope |

Implications: the finale is half our score, but the **internal college round is the steepest cut** (60–80% of teams die there) — a 10-second clickable mockup, clean role split, and hours-attached timeline clear it. R2 punishes ignoring mentor feedback; R3 punishes a demo that never runs. Every deck beat maps 1:1 to a criterion — unmapped-but-beautiful loses to mapped ([deck-outline.md](../deck/deck-outline.md)).

## 2. The six PS technical challenges → six pre-written jury answers

The PS names its own attacks; each is answered before the jury asks:

| PS challenge | Our answer (pre-written) |
|---|---|
| 1. Privacy/confidentiality of sensitive data | **DPDP Act 2023 split**: §7(i) legitimate use for core HR signals (leave, deployment, duty rosters — no consent needed); explicit, unbundled, revocable consent for voluntary self-reports; 72-hour breach readiness; Significant Data Fiduciary duties at CRPF scale ([dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md)) |
| 2. Stigmatization | **Architectural firewall, not a promise** ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)): individual scores physically cannot reach command — two-tier output, k ≥ 5 aggregates, dual-key unmask, who-viewed-my-data receipt; verifiable in code |
| 3. False positives / false negatives | **Cost-of-error economics** ([NFR-07](prd.md#3-non-functional-requirements)): FP = one cup of tea with a counsellor; FN = a life. Human-in-the-loop welfare-officer sign-off, per-person baselines, alert caps against fatigue, honest failure cases shown |
| 4. Ethical, transparent AI | **Rules engine v1, no black box** ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)): every flag ships top-3 factors with source labels ("47 consecutive duty days, sleep −30%"); ML v2 only once counsellor labels exist — an honest engine beats an unverifiable 99% |
| 5. Security of psychological data | **On-prem/air-gapped sovereignty** ([security-model.md](../compliance/security-model.md)): RBAC enforced server-side, AES-256 at rest, immutable audit log, no foreign SaaS ever touches welfare data |
| 6. Trust of personnel | **Adoption design** ([adoption-strategy.md](adoption-strategy.md)): roster-app-first, never-therapy framing, non-participation costless, silent consent withdrawal, punitive-outcome monitoring = 0 |

## 3. The 3-minute demo script — one persona, 90 days

**One story beats ten features.** [FR-20](prd.md#3-scope) seeds a scripted persona: *Constable, 34, 3rd Bn*.

| Time | Beat |
|---|---|
| 0:00–0:10 | Problem + the one cited statistic (ThePrint: 654 CAPF suicides, ~50,000 resignations in 5 years) |
| 0:10–1:40 | **Live loop on the persona**: silent HR signals accumulate (duty days, cancelled leaves) → Amber → buddy nudge → voluntary check-in → counsellor reaches out ≤ 24 h → roster change proposed → score trends down. The loop closes. |
| ~mid | **The most memorable 15 seconds**: the who-viewed-my-data panel on the jawan's phone — a receipt, not a warning ([design.md §5](../architecture/design/design.md)) |
| 1:40–2:00 | Impact: pilot KPI table, punitive outcomes = 0 monitored ([impact-and-metrics.md](impact-and-metrics.md)) |
| 2:00–2:20 | Tech depth: one architecture slide, the two-tier split visible |
| 2:20–2:40 | Scale + deployment: on-prem, offline-first, Hindi + regional languages; buffer to 3:00 |

Rules: practiced 5× minimum; the 5-minute limit is enforced ruthlessly — never get cut before the demo runs; offline/local run + recorded demo on two devices as insurance.

## 4. The anti-goals slide — "what we deliberately did not build"

Reads as maturity; preempts "what will you NOT build?" (a known jury question):

- No facial emotion recognition or CCTV scanning — contested science, reads as surveillance.
- No phone/relationship monitoring — trust-killing and likely unlawful under DPDP.
- No risk scores in any appraisal/ACR/promotion flow — the firewall is architectural.
- No ML on day one — no labelled data exists; transparent rules v1 instead.
- No clinical diagnosis — screeners are "reflection support, not diagnosis".

## 5. "Why yours?" — the answer that is not "better UI"

Consumer wellness apps and generic HRIS lose here. Our differentiation is structural: **ministry-specific compliance** (DPDP + MHA 2017 mapping, on-prem), **offline-first** on low-end Android, **Hindi + regional languages** with voice/icon UI for mixed literacy, **Tele-MANAS (14416) integration** as a recorded intervention outcome, indigenous capability in the force's own cultural register (roster-first, fitness-for-duty framing). Competitors' visible baseline ([research §7](research-sih-2026.md#competition-intel)) is a rules prototype — we beat it on offline mobile, languages, force-grade auth, and honest evaluation, not on a longer feature list.

## 6. Internal-round survival kit (the steepest cut)

- Demo the **10-second clickable mockup** live, not described; a working prototype beats a working pitch ([research §4](research-sih-2026.md#4-round-by-round-jury-expectations-from-official-docs--winner-accounts)).
- Each member answers their own domain; no silent standing members; never argue defensively — "we'll incorporate that in Phase 2" beats arguing with the panel.
- No AI + Blockchain + IoT combo claims; be straight about what is built vs. off-the-shelf ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)).
- The 36-hour feasibility plan with hours attached is read out verbatim from [deck-outline.md slide 10](../deck/deck-outline.md#10--36-hour-implementation-timeline).
- Carry backup: video link, PDF, GitHub — never bet the round on one laptop.

## 7. Operational insurance (from winner accounts)

Architecture pre-decided before hour 0 ([architecture.md](../architecture/architecture.md)) · role split with a dedicated docs/demo owner · seeded Indian-context synthetic data, never an empty dashboard · PDF slides + recorded demo on pen drive and two devices · mentor feedback visibly incorporated (an R2 criterion) · repo runs on any machine in one command.

## Links

[research-sih-2026.md](research-sih-2026.md) · [deck-outline.md](../deck/deck-outline.md) · [demo-runbook.md](../quality/demo-runbook.md) · [impact-and-metrics.md](impact-and-metrics.md)
