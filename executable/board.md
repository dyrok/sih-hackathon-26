# Board — single status source

> Owner: kv · Status: [~] live (updated daily) · Last updated: 2026-09-08
>
> Structure owned by kv (PM). Owners edit ONLY the Status column of their own rows.
> Legend: `[ ]` todo · `[~]` in-progress · `[x]` done · `[!]` blocked (reason + who unblocks)
> **Task sizing:** kv + neel carry the backbone. ayush, manan, risa, tejas are 1st-years — their tasks are deliberately simple (verify, collect, copy, record, practice). If a junior task feels too big, split it with kv — that is expected, not a failure.

## Phase 0 — Documentation brain (2026-09-05 → 09-08)

| ID | Task | Owner | Depends on | Due | Status |
|---|---|---|---|---|---|
| DOCS-001 | architecture.md + C4-1/C4-2 diagrams | kv | — | 2026-09-06 | [x] |
| DOCS-002 | ADRs 0001–0006 (MADR format) | kv | — | 2026-09-06 | [x] |
| DOCS-003 | design-hr-signal-engine.md + design-risk-engine.md | kv | DOCS-001 | 2026-09-07 | [x] |
| DOCS-004 | design.md + design-client-apps.md | neel | DOCS-001 | 2026-09-07 | [x] |
| DOCS-005 | compliance/ 4 docs (DPDP, MHCA, security, RBAC) | kv | DOCS-001 | 2026-09-08 | [x] |
| DOCS-006 | explanation/ 3 docs (model, datasets, instruments) | kv | DOCS-001 | 2026-09-08 | [x] |
| DOCS-007 | personas, adoption-strategy, impact-and-metrics, winning-strategy | kv | DOCS-001 | 2026-09-08 | [x] |
| DOCS-008 | test-plan.md + demo-runbook.md | kv | DOCS-009 | 2026-09-08 | [x] |
| DOCS-009 | prd.md (FR/NFR numbered + testable) | kv | — | 2026-09-06 | [x] |
| DOCS-010 | F02, F03, F06, F07 feature docs | neel | DOCS-004 | 2026-09-08 | [x] |
| DOCS-011 | F01, F04, F05 feature docs | kv | DOCS-003 | 2026-09-08 | [x] |
| DOCS-012 | F08 privacy-safety-architecture.md | kv | DOCS-005 | 2026-09-08 | [x] |
| DOCS-013 | F09 synthetic-data-generator.md | kv | DOCS-006 | 2026-09-08 | [x] |
| DOCS-014 | deck-outline.md (risa's deck spec) | risa | DOCS-007 | 2026-09-09 | [x] |
| DOCS-015 | usability-testing.md (review + own) | neel | DOCS-004 | 2026-09-09 | [x] |
| DOCS-016 | ppt-guide.md (beginner PPT guide) | risa | DOCS-014 | 2026-09-05 | [x] |

## Phase 1 — Prototype v1 (2026-09-08 → 09-15)

| ID | Task | Owner | Depends on | Due | Status |
|---|---|---|---|---|---|
| BACK-001 | FastAPI + Postgres scaffold, JWT auth, RBAC middleware | kv | DOCS-011 | 2026-09-10 | [x] |
| BACK-002 | Immutable audit log + break-glass flow | kv | BACK-001 | 2026-09-10 | [x] |
| BACK-003 | HR ingestion (CSV+API) + signal feature derivation | kv | BACK-001 | 2026-09-12 | [x] |
| BACK-004 | Rules engine v1: per-person baselines + masking flag | kv | BACK-003 | 2026-09-13 | [x] |
| BACK-005 | Intervention engine: response ladder + capacity triage | kv | BACK-004 | 2026-09-14 | [x] |
| BACK-006 | Workload rebalancing optimiser (greedy v1) | kv | BACK-005 | 2026-09-15 | [x] |
| BACK-007 | k-anonymity aggregation + dual-key unmask endpoints | kv | BACK-002 | 2026-09-14 | [x] |
| BACK-008 | Alert dispatch + Tele-MANAS handoff record | kv | BACK-005 | 2026-09-15 | [x] |
| BACK-009 | who-viewed-my-data logging API | kv | BACK-002 | 2026-09-14 | [x] |
| APP-001 | Expo app scaffold + SQLite offline sync | neel | DOCS-010 | 2026-09-10 | [ ] |
| APP-002 | Roster/leave/pay-slip screens (roster-app-first) | neel | APP-001 | 2026-09-12 | [ ] |
| APP-003 | 10-second check-in + instruments + validity items | neel | APP-001 | 2026-09-13 | [ ] |
| APP-004 | Consent flow + silent withdrawal | neel | APP-001 | 2026-09-13 | [ ] |
| APP-005 | who-viewed-my-data screen | neel | APP-004 | 2026-09-14 | [ ] |
| APP-006 | On-device voice prosody module | neel | APP-001 | 2026-09-14 | [ ] |
| APP-007 | Counsellor console (Next.js) | neel | BACK-005 | 2026-09-14 | [ ] |
| APP-008 | Commander dashboard: aggregate heatmap + morale index | neel | BACK-007 | 2026-09-15 | [ ] |
| APP-009 | Anonymous unit pulse + battle-buddy pairing | neel | APP-001 | 2026-09-15 | [ ] |
| APP-010 | What-if simulator (basic) | neel | APP-008 | 2026-09-16 | [ ] |

## Phase 2 — Theory, QA, demo package (2026-09-09 → 09-19)

| ID | Task | Owner | Depends on | Due | Status |
|---|---|---|---|---|---|
| ML-001 | Signal feature definitions + clinical thresholds (absorbed into F04 + model-explainer) | kv | DOCS-006 | 2026-09-09 | [x] |
| ML-002 | Validation harness: backtest rules engine on synthetic data | kv | QA-001, BACK-004 | 2026-09-16 | [x] |
| ML-003 | Fairness audit checklist + SHAP report template | kv | ML-001 | 2026-09-17 | [x] |
| ML-004 | ML v2 data-collection plan from counsellor labels | kv | ML-002 | 2026-09-25 | [x] |
| ML-005 | Verify every link + citation in datasets-research.md; list dead links for neel | ayush | DOCS-006 | 2026-09-10 | [ ] |
| ML-006 | One-page instrument factsheet (PHQ-9/GAD-7/PSS-10/ISI: items, bands, source) for the deck | ayush | DOCS-006 | 2026-09-11 | [ ] |
| PRIV-001 | DPDP 2023 mapping audit vs implementation | kv | DOCS-005 | 2026-09-13 | [x] |
| PRIV-002 | RBAC enforcement tests | neel | BACK-001 | 2026-09-14 | [ ] |
| PRIV-003 | Security test cases + threat model walkthrough | neel | DOCS-005 | 2026-09-15 | [ ] |
| PRIV-004 | MHCA 2017 section 23 compliance review | kv | DOCS-005 | 2026-09-16 | [x] |
| PRIV-005 | Statute sources pack: copy official text of DPDP §7(i), §4–5 and MHCA §23 with source links into docs/compliance/sources.md | manan | DOCS-005 | 2026-09-10 | [ ] |
| PRIV-006 | Manual privacy walkthrough: simple click-through checklist (consent, withdrawal, who-viewed) once the app builds; record pass/fail | manan | APP-004 | 2026-09-15 | [ ] |
| UX-001 | Usability testing protocol + icon/voice review | neel | DOCS-015 | 2026-09-15 | [ ] |
| UX-002 | Figma mockups: check-in + privacy panel | neel | DOCS-004 | 2026-09-14 | [ ] |
| UX-003 | Collect + caption prototype screenshots for the deck (guided by neel) | risa | QA-002 | 2026-09-16 | [ ] |
| QA-001 | Synthetic data generator (1000 personnel, 90 days) | neel | DOCS-013 | 2026-09-12 | [ ] |
| QA-002 | Scripted demo persona data (Constable, 34, 3rd Bn) | neel | QA-001 | 2026-09-13 | [ ] |
| QA-003 | E2E test execution + coverage report | neel | QA-002 | 2026-09-16 | [ ] |
| QA-004 | Demo rehearsal checklist + recorded video fallback | kv | QA-003 | 2026-09-17 | [x] |
| QA-005 | Docs QA sweep: every doc has Owner + Status stamp, links resolve; report gaps to kv | tejas | — | 2026-09-09 | [~] |
| QA-006 | Run the manual test checklist from docs/quality/test-plan.md (guided by neel); record pass/fail per case | tejas | QA-003 | 2026-09-17 | [ ] |
| QA-007 | Demo rehearsal support + record the fallback video with risa | tejas | QA-004 | 2026-09-18 | [ ] |
| DECK-001 | Build the deck inside the official SIH template following docs/deck/ppt-guide.md | risa | DOCS-014, DECK-003 | 2026-09-17 | [ ] |
| DECK-002 | Demo video (with tejas) | risa | QA-007 | 2026-09-18 | [ ] |
| DECK-003 | Impact/scalability slide figures with citations (source: impact-and-metrics.md) | risa | DOCS-007 | 2026-09-17 | [ ] |
| DECK-004 | Internal-round presentation practice ×3 + printed jury cheat sheet | risa | DECK-001 | 2026-09-18 | [ ] |

## Phase 3 — Submission & hardening (2026-09-18 → ongoing)

| ID | Task | Owner | Depends on | Due | Status |
|---|---|---|---|---|---|
| PM-001 | Daily board sync + checklist regeneration | kv | — | daily | [~] |
| PM-002 | Internal round readiness check (deck+demo+repo) | kv | DECK-001, QA-004 | 2026-09-18 | [x] |
| PM-003 | Portal submission package (PDF, title, description) | kv | PM-002 | 2026-09-19 | [x] |
| PM-004 | Mentor feedback incorporation board (Round 2 criteria) | kv | PM-003 | 2026-09-26 | [x] |
| PM-005 | Finale 36h execution plan + 3-min demo script | kv | PM-004 | 2026-11-15 | [x] |
