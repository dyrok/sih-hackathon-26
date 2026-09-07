# Impact & Metrics — SAARTHI pilot

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05

## Honest framing (non-negotiable)

Per [AGENTS.md](../../AGENTS.md) rule 6: **no invented statistics**. Cited numbers below are the only externally sourced figures; every target is labelled a *reasoned estimate* or a *directional target*. We will not claim "lives saved", rupee ROI, or model accuracy until outcomes and evaluation exist ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)).

## The cited problem baseline

One source, used everywhere the problem is stated (deck slide 2, demo opener):

- **654 CAPF suicides and ~50,000 resignations in 5 years** — ThePrint: [the crisis stalking India's CAPFs](https://theprint.in/india/654-suicides-50000-resignations-in-5-years-the-crisis-stalking-indias-capfs/1787191/).

CRPF-specific breakdowns (281 suicides, 2025 the worst year) exist in [research-sih-2026.md §7](research-sih-2026.md#7-ps-26186-specific-strategy-risks--preemptions) and are cited to their own sources there, never bundled into one invented "average".

## Pilot KPI table (defined upfront — [prd.md §4](prd.md#4-success-metrics-pilot--defined-upfront-no-invented-numbers))

| KPI | Target | Target type | How measured |
|---|---|---|---|
| Voluntary participation | ≥ 30% of unit | Reasoned estimate (roster-first adoption) | Check-in accounts ÷ assigned personnel, weekly |
| Time from Red flag → counsellor contact | ≤ 24 h | Design target ([FR-09](../features/F05-intervention-engine.md)) | Flag timestamp → first logged contact |
| Post-intervention risk-trend reduction | Directionally negative at 4 weeks | Directional target | Counsellor outcome tracker, before/after trend ([FR-12](../features/F06-counsellor-console.md)) |
| Punitive outcomes linked to the system | **0** | Monitored trust signal | Open question in pilot reviews + grievance channel |
| Individual scores reaching command | **0** | **Architectural guarantee** ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)) | Route-level rejection tests + audit log; not a policy claim |
| Sick-leave days (unit aggregate) | Downward trend vs. pilot baseline | Directional target (aggregate, k ≥ 5) | HR records, unit-level only |
| Attrition | Tracked directionally; **no pilot-period claim** | Directional target | Resignation data over years — too slow for a pilot; we say so |

## Expected PS benefits → measurable proxies

The PS's Strategic Importance claims must each land on something observable:

| PS claim (verbatim) | Measurable proxy in pilot |
|---|---|
| "Enhances force readiness" | Duty-days lost to welfare incidents; workload-rebalance proposals accepted ([FR-11](../features/F05-intervention-engine.md)) |
| "Supports evidence-based welfare management" | Welfare actions logged with explainable evidence cards; command decisions citing unit aggregates |
| "Strengthens organisational resilience" | Time-to-flag on group trauma exposure (group-level, [FR-08](../features/F01-hr-signal-engine.md)); post-incident recovery trend |
| "Promotes preventive mental health care" | Flags surfaced at Amber before Red; share of interventions that are informal (buddy/JCO) tier |
| "Indigenous capability" | On-prem/air-gap deployment checklist passes inside force perimeter; zero foreign SaaS touching welfare data |

## Scalability ratings (with reasoning, not adjectives)

| Dimension | Rating | Reasoning |
|---|---|---|
| Technical scale | **High** | Rules engine is trivially fast — 1,000-personnel recompute < 60 s on modest hardware ([NFR-06](prd.md#3-non-functional-requirements)); stateless services scale with the force |
| Adoption scale | **Med** | Rides existing HRMS integration and unit rollout discipline; roster-first lowers the ask, but each unit needs officer-first buy-in ([adoption-strategy.md](adoption-strategy.md)) |
| Outcome-evidence scale | **Low → Med over time** | Credible ML v2 needs counsellor-labelled outcomes that accrue over months; a 90-day pilot proves the loop, not the epidemiology |
| Language & accessibility scale | **Med–High** | All strings via i18n keys (`en`, `hi`); regional languages are a data file, not a redesign ([design.md §8](../architecture/design/design.md)); voice + icon UI for mixed literacy |
| Deployment scale | **High** | On-prem, air-gappable, Android-only footprint on API 26+; no consumer cloud dependency |

## Measurement caveats (say them before the jury does)

- **Participation bias** — check-in data over-represents the willing; no conclusion rests on self-report alone, because HR signals cover the silent majority ([adoption-strategy.md](adoption-strategy.md)).
- **Novelty effect** — early participation is inflated; the 30% target is judged at week 4+, not week 1.
- **Attribution** — operations, seasons, and roster policy all move wellbeing; the pilot proves the loop works, not causal impact on the cited baseline.
- **Aggregate-only reporting** — unit-level KPIs respect k ≥ 5 suppression ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)); no cell is published below the threshold, including in pilot reports.

## Negative-outcome monitoring (the trust signal)

- The pilot review asks, out loud: **"Did anyone get punished because of this system?"** — tracked as a KPI with target 0, not as a hope.
- Saying you measure this *is* the trust signal: jawans hear the question asked in their unit, and the answer is auditable via the who-viewed-my-data log ([FR-15](prd.md#2-functional-requirements)).
- Any punitive linkage is a stop-ship finding: system paused, incident reviewed, results reported — before participation is asked to continue.

## What we will not claim

- No "X% reduction in suicides" — the cited baseline has no causal comparison.
- No accuracy percentage for the rules engine until evaluated against counsellor outcomes ([model-explainer.md](../explanation/model-explainer.md)).
- No ROI in rupees — welfare value is measured in the KPI table above.

## Links

[prd.md](prd.md) · [impact twins](adoption-strategy.md) · [F05](../features/F05-intervention-engine.md) · [F08](../features/F08-privacy-safety-architecture.md) · [winning-strategy.md](winning-strategy.md)
