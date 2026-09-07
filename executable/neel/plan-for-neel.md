# Plan — neel (Client, Design & Platform lead · co-backbone)

> Branch: `neel` · Last updated: 2026-09-05 · Review partner: kv

## Role
Co-backbone with kv (equal work split). All user-facing surfaces: jawan mobile app (Expo/RN, offline-first, Hindi+English), counsellor console, commander dashboard, design system. Plus neel's half of the complex docs: security model, RBAC matrix, test plan, synthetic data generator, datasets/instruments research, personas/adoption/impact.

## Files I own (nobody else edits these)

| File | Purpose |
|---|---|
| `docs/architecture/design/design.md`, `design-client-apps.md` | design system + app designs |
| `docs/features/F02, F03, F06, F07, F09` | client features + synthetic data |
| `docs/compliance/security-model.md`, `rbac-matrix.md` | neel's compliance half |
| `docs/explanation/datasets-research.md`, `clinical-instruments.md` | research docs |
| `docs/product/personas.md`, `adoption-strategy.md`, `impact-and-metrics.md` | product docs |
| `docs/quality/test-plan.md`, `usability-testing.md` | quality docs |
| `mobile/`, `web/`, `data/` (all code) | implementation |

## My tasks (live rows: [board.md](../board.md))

| ID | Task | Due |
|---|---|---|
| APP-001…010 | Expo app, roster screens, check-in, consent, who-viewed, voice, consoles, dashboard | 09-10 → 09-16 |
| QA-001 | Synthetic data generator (1000 personnel, 90 days) | 09-12 |
| QA-002 | Scripted demo persona data | 09-13 |
| QA-003 | E2E test execution + coverage report | 09-16 |
| PRIV-002 | RBAC enforcement tests | 09-14 |
| PRIV-003 | Security test cases + threat model walkthrough | 09-15 |
| UX-001 | Usability testing protocol + icon/voice review | 09-15 |
| UX-002 | Figma mockups: check-in + privacy panel | 09-14 |

## Definition of done (per task)
- [ ] PR with `[TASK-ID]` title merged (kv reviews) · tests green
- [ ] Affected `docs/` file updated in same PR
- [ ] board.md Status `[x]` · checklist regenerated
- [ ] UI strings via i18n keys (`en`, `hi`) — no hardcoded strings

## Work split with kv (equal backbone)
kv owns the mirror image: backend/engines, architecture, ADRs, privacy-law mapping, model theory, demo runbook, jury strategy. If neel is blocked, kv is the fallback owner and vice versa — agree the handover on the board first.

## Key docs I work from
[design.md](../../docs/architecture/design/design.md) · [ADR-0004](../../docs/architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../../docs/architecture/decisions/0005-offline-first-low-end-android.md) · [F02](../../docs/features/F02-jawan-app.md) · [F09](../../docs/features/F09-synthetic-data-generator.md) · [rbac-matrix](../../docs/compliance/rbac-matrix.md) · [test-plan](../../docs/quality/test-plan.md)
