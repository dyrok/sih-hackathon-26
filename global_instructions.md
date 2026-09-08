# global_instructions.md — SAARTHI Global Operating Manual

> **Read this FIRST** — every team member and every AI agent. [`AGENTS.md`](AGENTS.md) is the law; this file is the map: the master roadmap, the complete work progress checklist, and the global working instructions.
> Owner: kv · Status: [~] live (kv updates §5 progress at each phase gate) · Last updated: 2026-09-08

## 1. What we are building

**SAARTHI** (SIH 2026 · PS 26186 · CRPF/MHA · MedTech) — AI-based predictive personnel stress & welfare monitoring for uniformed forces. Detect risk early from HR signals + voluntary check-ins, route help before crisis, and keep individual scores architecturally away from command hierarchy (welfare, not discipline). Hard deadline: **idea submission 2026-09-20**.

## 2. The rules (condensed — full version in [AGENTS.md](AGENTS.md))

1. `docs/` is the brain — read the feature doc before coding; update docs in the same PR.
2. One owner per file — never edit someone else's file.
3. `executable/board.md` is the single live status source; checklists are generated, never hand-edited.
4. Task IDs everywhere — PR title `[TASK-ID] summary`.
5. **Branch → notify → merge**: work only on your own branch; when a task and its testing are done, open a PR into `main` and notify kv; **only kv merges to `main`** (kv's own PRs reviewed by neel).
6. No invented statistics — cite or rate Low/Med/High.
7. Welfare, not discipline — no change may route an individual score to command (ADR-0003).
8. Task sizing — kv + neel carry the backbone; ayush, manan, risa, tejas (1st-years) get simple guided tasks; splitting a task with kv is expected.

## 3. How work happens (the loop, every task)

```
git switch <your-name>            # your branch only, never main
  → pick top non-done task in executable/<name>/checklist.md
  → read the linked docs/ file    # the task's instruction sheet
  → do the task, small commits starting with the task ID
  → push + open PR into main titled [TASK-ID] summary
  → tell kv "PR ready for review" ("testing done")
  → kv reviews + merges           # only kv merges
  → git switch main && git pull → set board row [x]
```

## 4. Where everything lives

| Path | What |
|---|---|
| [AGENTS.md](AGENTS.md) | the law — full rules |
| [executable/board.md](executable/board.md) | **live per-task status** (owners edit own rows' Status) |
| [executable/roadmap.md](executable/roadmap.md) | milestone view (§5 of this file is the master) |
| [executable/\<name\>/](executable/README.md) | per-member: plan-for-\<name\>.md · execute.md · checklist.md (generated) |
| [docs/README.md](docs/README.md) | the brain — index of all product knowledge |
| [executable/tools/sync-checklists.py](executable/tools/sync-checklists.py) | regenerates checklists from board.md (kv, daily) |

## 5. Master roadmap & complete work progress checklist

> Per-task live status: [board.md](executable/board.md). kv mirrors status into this checklist at each daily sync (PM-001) and ticks phase gates when the gate criteria are met. Legend: `[ ]` todo · `[~]` in-progress · `[x]` done.

### Progress snapshot: 35 / 66 tasks complete (53%)

| Phase | Window | Tasks | Done | Gate status |
|---|---|---|---|---|
| 0 — Docs brain | Sep 5–8 | 16 | 16 | [x] every doc has owner + stamp |
| 1 — Prototype v1 | Sep 8–15 | 19 | 9 | [~] backend demo loop merged; apps still neel |
| 2 — Theory, QA, demo package | Sep 9–19 | 26 | 5 | [ ] official-template deck + video still risa/tejas |
| 3 — Submission & hardening | Sep 18 → | 5 | 4 | [~] content PDF ready; official template + letter remain |

### Phase 0 — Documentation brain (2026-09-05 → 09-08) — COMPLETE

| Task | Owner | Due | Status |
|---|---|---|---|
| DOCS-001 architecture.md + C4 diagrams | kv | 09-06 | [x] |
| DOCS-002 ADRs 0001–0006 | kv | 09-06 | [x] |
| DOCS-003 design-hr-signal-engine + design-risk-engine | kv | 09-07 | [x] |
| DOCS-004 design.md + design-client-apps.md | neel | 09-07 | [x] |
| DOCS-005 compliance/ 4 docs | kv | 09-08 | [x] |
| DOCS-006 explanation/ 3 docs | kv | 09-08 | [x] |
| DOCS-007 personas, adoption, impact, winning-strategy | kv | 09-08 | [x] |
| DOCS-008 test-plan.md + demo-runbook.md | kv | 09-08 | [x] |
| DOCS-009 prd.md (FR/NFR) | kv | 09-06 | [x] |
| DOCS-010 F02, F03, F06, F07 feature docs | neel | 09-08 | [x] |
| DOCS-011 F01, F04, F05 feature docs | kv | 09-08 | [x] |
| DOCS-012 F08 privacy-safety-architecture.md | kv | 09-08 | [x] |
| DOCS-013 F09 synthetic-data-generator.md | kv | 09-08 | [x] |
| DOCS-014 deck-outline.md | risa | 09-09 | [x] |
| DOCS-015 usability-testing.md | neel | 09-09 | [x] |
| DOCS-016 ppt-guide.md | risa | 09-05 | [x] |

### Phase 1 — Prototype v1 (2026-09-08 → 09-15)

| Task | Owner | Due | Status |
|---|---|---|---|
| BACK-001 FastAPI + Postgres scaffold, JWT, RBAC | kv | 09-10 | [x] |
| BACK-002 Immutable audit log + break-glass | kv | 09-10 | [x] |
| BACK-003 HR ingestion + signal features | kv | 09-12 | [x] |
| BACK-004 Rules engine v1 + baselines + masking flag | kv | 09-13 | [x] |
| BACK-005 Response ladder + capacity triage | kv | 09-14 | [x] |
| BACK-006 Workload rebalancing optimiser | kv | 09-15 | [x] |
| BACK-007 k-anonymity aggregation + dual-key unmask | kv | 09-14 | [x] |
| BACK-008 Alert dispatch + Tele-MANAS record | kv | 09-15 | [x] |
| BACK-009 who-viewed-my-data logging API | kv | 09-14 | [x] |
| APP-001 Expo scaffold + SQLite offline sync | neel | 09-10 | [ ] |
| APP-002 Roster/leave/pay-slip screens | neel | 09-12 | [ ] |
| APP-003 10s check-in + instruments + validity items | neel | 09-13 | [ ] |
| APP-004 Consent flow + silent withdrawal | neel | 09-13 | [ ] |
| APP-005 who-viewed-my-data screen | neel | 09-14 | [ ] |
| APP-006 On-device voice prosody module | neel | 09-14 | [ ] |
| APP-007 Counsellor console (Next.js) | neel | 09-14 | [ ] |
| APP-008 Commander dashboard (aggregate heatmap) | neel | 09-15 | [ ] |
| APP-009 Anonymous unit pulse + battle-buddy | neel | 09-15 | [ ] |
| APP-010 What-if simulator (basic) | neel | 09-16 | [ ] |

### Phase 2 — Theory, QA, demo package (2026-09-09 → 09-19)

| Task | Owner | Due | Status |
|---|---|---|---|
| ML-001 Signal feature definitions (absorbed into F04) | kv | 09-09 | [x] |
| ML-002 Validation harness (backtest on synthetic data) | kv | 09-16 | [x] |
| ML-003 Fairness audit checklist + SHAP template | kv | 09-17 | [x] |
| ML-004 ML v2 data-collection plan | kv | 09-25 | [x] |
| ML-005 Verify links/citations in datasets-research.md | ayush | 09-10 | [ ] |
| ML-006 One-page instrument factsheet for the deck | ayush | 09-11 | [ ] |
| PRIV-001 DPDP mapping audit vs implementation | kv | 09-13 | [x] |
| PRIV-002 RBAC enforcement tests | neel | 09-14 | [ ] |
| PRIV-003 Security test cases + threat model walkthrough | neel | 09-15 | [ ] |
| PRIV-004 MHCA §23 compliance review | kv | 09-16 | [x] |
| PRIV-005 Statute sources pack (sources.md) | manan | 09-10 | [ ] |
| PRIV-006 Manual privacy walkthrough checklist | manan | 09-15 | [ ] |
| UX-001 Usability testing protocol + icon/voice review | neel | 09-15 | [ ] |
| UX-002 Figma mockups: check-in + privacy panel | neel | 09-14 | [ ] |
| UX-003 Collect + caption deck screenshots | risa | 09-16 | [ ] |
| QA-001 Synthetic data generator (1000 personnel, 90d) | neel | 09-12 | [ ] |
| QA-002 Scripted demo persona data | neel | 09-13 | [ ] |
| QA-003 E2E test execution + coverage report | neel | 09-16 | [ ] |
| QA-004 Demo rehearsal checklist + video fallback | kv | 09-17 | [x] |
| QA-005 Docs QA sweep (stamps + links) | tejas | 09-09 | [ ] |
| QA-006 Run manual test checklist, record pass/fail | tejas | 09-17 | [ ] |
| QA-007 Demo rehearsal support + record fallback video | tejas | 09-18 | [ ] |
| DECK-001 Build deck in official SIH template | risa | 09-17 | [ ] |
| DECK-002 Demo video (with tejas) | risa | 09-18 | [ ] |
| DECK-003 Impact/scalability figures with citations | risa | 09-17 | [ ] |
| DECK-004 Presentation practice ×3 + jury cheat sheet | risa | 09-18 | [ ] |

### Phase 3 — Submission & hardening (2026-09-18 → ongoing)

| Task | Owner | Due | Status |
|---|---|---|---|
| PM-001 Daily board sync + checklist regeneration | kv | daily | [~] |
| PM-002 Internal round readiness check | kv | 09-18 | [x] |
| PM-003 Portal submission package (PDF, title, description) | kv | 09-19 | [x] |
| PM-004 Mentor feedback incorporation board (R2) | kv | 09-26 | [x] |
| PM-005 Finale 36h plan + 3-min demo script | kv | 11-15 | [x] |

### Allotment summary

| Member | Tasks | Backbone share |
|---|---|---|
| kv (PM · co-backbone) | 32 | engines, architecture, privacy law, model theory, submission |
| neel (co-backbone) | 20 | apps, dashboards, design, security, RBAC, test plan, generator |
| risa (1st yr · presentation) | 7 | the entire deck + demo video + practice |
| tejas (1st yr · QA) | 3 | docs sweep, manual test execution, demo support |
| ayush (1st yr · ML research) | 2 | citation verification, instrument factsheet |
| manan (1st yr · compliance research) | 2 | statute sources pack, privacy walkthrough |

### Key dates

- **Sep 20** — SIH idea submission deadline (hard)
- Sep 18 — internal-round readiness gate (PM-002)
- Sep 26 — mentor feedback incorporated (Round 2 criteria)
- Nov 15 — finale 36h plan + 3-min demo script frozen (PM-005)
- Dec — grand finale: rehearsed 3-min demo, offline backups, architecture pre-decided (this repo)

## 6. For AI agents: session startup order

1. [AGENTS.md](AGENTS.md) — the law
2. **This file** — roadmap + complete checklist + global rules
3. `executable/<your-member>/plan-for-<name>.md` — role, ownership, tasks
4. `executable/<your-member>/execute.md` — your specific execution prompt
5. `executable/<your-member>/checklist.md` — generated task list
6. The `docs/` files linked by your tasks — the brain
