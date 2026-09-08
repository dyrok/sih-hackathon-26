# docs/ — THE BRAIN

> Owner: kv (index) · Status: [~] current · Last updated: 2026-09-08
>
> All product knowledge lives here. Every implementation decision traces to one of these files. One owner per file — never edit someone else's doc.
> Status legend: `[ ]` todo · `[~]` drafting · `[x]` frozen/current · `[!]` stale (needs review)
> The task system lives in [`executable/`](../executable/README.md) — this folder is referenced by it, never the other way around.

## Product — why (judges read these)

| Doc | Owner | Status | One line |
|---|---|---|---|
| [problem-statement.md](product/problem-statement.md) | kv | [x] | PS 26186 verbatim + our interpretation + scope |
| [prd.md](product/prd.md) | kv | [x] | FR-01…20 / NFR-01…08, numbered and testable |
| [personas.md](product/personas.md) | neel | [~] | Jawan, counsellor, welfare officer, commander, evaluator |
| [adoption-strategy.md](product/adoption-strategy.md) | neel | [~] | "Police wala kyu use karega" — the answer |
| [impact-and-metrics.md](product/impact-and-metrics.md) | neel | [~] | Pilot KPIs, honest impact framing |
| [winning-strategy.md](product/winning-strategy.md) | kv | [x] | SIH rubric-mapped jury strategy |
| [submission-package.md](product/submission-package.md) | kv | [x] | PM-003 portal title, description, PDF |
| [research-sih-2026.md](product/research-sih-2026.md) | kv | [x] | Raw research: judging criteria, rounds, tactics (source material) |

## Architecture — how

| Doc | Owner | Status | One line |
|---|---|---|---|
| [architecture.md](architecture/architecture.md) | kv | [x] | arc42-lite + C4-1/C4-2 + demo loop sequence |
| [design/design.md](architecture/design/design.md) | neel | [~] | Design system: color, type, states, trust moment |
| [design/design-client-apps.md](architecture/design/design-client-apps.md) | neel | [~] | Screen inventory + app/web implementation layout |
| [design/design-hr-signal-engine.md](architecture/design/design-hr-signal-engine.md) | kv | [x] | Ingestion pipeline engineering design |
| [design/design-risk-engine.md](architecture/design/design-risk-engine.md) | kv | [x] | Rules engine engineering design |
| [decisions/0001-rules-engine-v1-not-ml.md](architecture/decisions/0001-rules-engine-v1-not-ml.md) (then 0002–0006) | kv | [x] | 6 MADR ADRs — never delete |

## Features — comprehensive per-feature specs

| Doc | Owner | Status | FRs |
|---|---|---|---|
| [F01-hr-signal-engine.md](features/F01-hr-signal-engine.md) | kv | [x] | FR-01, FR-08 |
| [F02-jawan-app.md](features/F02-jawan-app.md) | neel | [~] | FR-02, FR-04, FR-15, FR-17, FR-19 |
| [F03-on-device-signals.md](features/F03-on-device-signals.md) | neel | [~] | FR-03 |
| [F04-risk-rules-engine.md](features/F04-risk-rules-engine.md) | kv | [x] | FR-05, FR-06, FR-07 |
| [F05-intervention-engine.md](features/F05-intervention-engine.md) | kv | [x] | FR-09, FR-10, FR-11, FR-13 |
| [F06-counsellor-console.md](features/F06-counsellor-console.md) | neel | [~] | FR-12 |
| [F07-commander-dashboard.md](features/F07-commander-dashboard.md) | neel | [~] | FR-14 (commander tier) |
| [F08-privacy-safety-architecture.md](features/F08-privacy-safety-architecture.md) | kv | [x] | FR-14, FR-16, FR-17, FR-18, NFR-01/02/08 |
| [F09-synthetic-data-generator.md](features/F09-synthetic-data-generator.md) | neel | [~] | FR-20 |

## Compliance — non-negotiable for MedTech submission

| Doc | Owner | Status | One line |
|---|---|---|---|
| [dpdp-2023-mapping.md](compliance/dpdp-2023-mapping.md) | kv | [x] | DPDP Act 2023 obligation → mechanism map |
| [mental-healthcare-act-2017.md](compliance/mental-healthcare-act-2017.md) | kv | [x] | §23 confidentiality + non-discrimination |
| [security-model.md](compliance/security-model.md) | neel | [~] | Threat model, encryption, on-prem deployment |
| [rbac-matrix.md](compliance/rbac-matrix.md) | neel | [~] | Role × data matrix, dual-key, k ≥ 5 |

## Explanation — why it works

| Doc | Owner | Status | One line |
|---|---|---|---|
| [model-explainer.md](explanation/model-explainer.md) | kv | [x] | Rules v1 → ML v2, SHAP, fairness |
| [fairness-audit-checklist.md](explanation/fairness-audit-checklist.md) | kv | [x] | ML-003 fairness audit + SHAP form |
| [shap-report-template.md](explanation/shap-report-template.md) | kv | [x] | v2 SHAP one-pager |
| [ml-v2-data-collection-plan.md](explanation/ml-v2-data-collection-plan.md) | kv | [x] | ML-004 label protocol |
| [datasets-research.md](explanation/datasets-research.md) | neel | [~] | WESAD, SWELL-KW, NCRB, SPIR 2019 |
| [clinical-instruments.md](explanation/clinical-instruments.md) | neel | [~] | PHQ-9/GAD-7/PSS-10/MBI/ISI/PCL-5 |

## Quality — how to verify & demo

| Doc | Owner | Status | One line |
|---|---|---|---|
| [test-plan.md](quality/test-plan.md) | neel | [~] | TC-### traceable to every FR/NFR |
| [demo-runbook.md](quality/demo-runbook.md) | kv | [x] | 3-min script, seeded data, fallbacks, QA-004 |
| [internal-round-readiness.md](quality/internal-round-readiness.md) | kv | [x] | PM-002 go/no-go |
| [finale-36h-plan.md](quality/finale-36h-plan.md) | kv | [x] | PM-005 hour plan |
| [usability-testing.md](quality/usability-testing.md) | neel | [~] | Mixed-literacy, offline, low-end device protocol |

## Deck

| Doc | Owner | Status | One line |
|---|---|---|---|
| [deck-outline.md](deck/deck-outline.md) | risa | [~] | Slide-by-slide deck spec (13-slide official SIH structure) |
| [ppt-guide.md](deck/ppt-guide.md) | risa | [x] | Beginner step-by-step PPT build guide |

## Rules that govern this folder

1. Diátaxis routing: product (why) / architecture+features (how) / quality (how-to) / explanation (why-it-works). Never mix.
2. Every doc carries `> Owner: · Status: · Last updated:` — no owner, no merge.
3. Docs update in the same PR as the code they describe.
4. Diagrams are committed mermaid text (diffable), C4 levels 1–2.
5. No invented statistics — cite or rate Low/Med/High.
