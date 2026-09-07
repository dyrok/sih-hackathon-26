# Plan — kv (Project Manager + Backend/Engine lead)

> Branch: `kv` · Last updated: 2026-09-05 · Review partner: neel

## Role
PM (board, assignments, integration) + co-backbone with neel (equal split): backend engines — ingestion, rules engine, intervention engine, privacy enforcement APIs — plus architecture and kv's half of the docs.

## Files I own (nobody else edits these)

| File | Purpose |
|---|---|
| `executable/board.md` (structure), `executable/roadmap.md`, `executable/README.md` | task system |
| `docs/architecture/architecture.md`, design-hr/risk docs, all ADRs | architecture |
| `docs/features/F01, F04, F05, F08` | engine + privacy features |
| `docs/compliance/dpdp-2023-mapping.md`, `mental-healthcare-act-2017.md` | privacy law mapping |
| `docs/explanation/model-explainer.md` | model theory |
| `docs/product/problem-statement.md`, `prd.md`, `winning-strategy.md`, `research-sih-2026.md` | product core + jury strategy |
| `docs/quality/demo-runbook.md` | demo script |
| `backend/` | implementation |

## My tasks (live rows: [board.md](../board.md))

| ID | Task | Due |
|---|---|---|
| DOCS-001…002, 009, 011 | architecture, ADRs, PRD, F01/F04/F05 (complete) | done |
| BACK-001…009 | backend: scaffold, audit, ingestion, rules engine, intervention, unmask, alerts | 09-10 → 09-15 |
| ML-002 | Validation harness: backtest rules engine on synthetic data | 09-16 |
| ML-003 | Fairness audit checklist + SHAP report template | 09-17 |
| ML-004 | ML v2 data-collection plan | 09-25 |
| PRIV-001, PRIV-004 | DPDP audit, MHCA review | 09-13 / 09-16 |
| QA-004 | Demo rehearsal checklist + recorded video fallback | 09-17 |
| PM-001…005 | board sync, readiness, submission, feedback, finale plan | per board |

## Maintainer duties (in addition to PM duties)
- **Only kv merges PRs into `main`** — review each member's PR: task-ID title, tests green, docs updated in same PR, no ADR-0003 violation. Merge, then tell the author.
- Juniors (ayush, manan, risa, tejas) get simple guided tasks; when they report "PR ready", review kindly and fast.
- Daily: run `python3 executable/tools/sync-checklists.py`, unblock `[!]` rows, 10-min standup.

## Work split with neel (equal backbone)
neel owns the mirror image: all client apps + dashboards, design system, security-model, rbac-matrix, test-plan, synthetic-data generator (F09), datasets/instruments docs, personas/adoption/impact. If kv is blocked, neel is the fallback owner and vice versa — agree the handover on the board first.

## PM duties (daily)
- Run `python3 executable/tools/sync-checklists.py`
- Review all PRs: task-ID title, docs updated in same PR, no ADR-0003 violations
- Unblock `[!]` rows; reassign if a member is > 24h behind (add/remove/reassign is PM-only)
- Daily 10-min standup: each member says status + blockers only

## Definition of done (per task)
- [ ] PR with `[TASK-ID]` title merged
- [ ] Tests green
- [ ] Affected `docs/` file updated in same PR
- [ ] board.md Status `[x]` · checklist regenerated

## Key docs I work from
[architecture.md](../../docs/architecture/architecture.md) · [prd.md](../../docs/product/prd.md) · [F04](../../docs/features/F04-risk-rules-engine.md) · [rbac-matrix](../../docs/compliance/rbac-matrix.md) · [test-plan](../../docs/quality/test-plan.md)
