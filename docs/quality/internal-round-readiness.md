# Internal-round readiness check (PM-002)

> Owner: kv · Status: [x] current · Last updated: 2026-09-08
> Depends on: DECK-001, QA-004. Hard idea-submission deadline: **2026-09-20**.
> This file **is** the readiness check. Re-run the table at each standup (PM-001).

## Gate criteria

| # | Artefact | Owner | Status | Notes |
|---|---|---|---|---|
| 1 | Working backend demo loop (seed + score + unmask + who-viewed) | kv | [x] | `backend/` on `main` |
| 2 | Firewall tests green | kv | [x] | `cd backend && pytest -q` — 44 passed |
| 3 | Jawan app screens (check-in, consent, who-viewed) | neel | [ ] | APP-001…005 |
| 4 | Counsellor console | neel | [ ] | APP-007 |
| 5 | Commander dashboard (aggregates) | neel | [ ] | APP-008 — API ready |
| 6 | Official SIH-template deck PDF | risa | [ ] | DECK-001 — content PPTX exists in `docs/product/submission/` (PM-003); **must be rebuilt inside the official template** |
| 7 | 3-min demo video + fallback file on two devices | risa / tejas | [ ] | DECK-002 / QA-007 |
| 8 | Five clean rehearsals logged | kv | [ ] | [demo-runbook.md](demo-runbook.md) §5 |
| 9 | Repo clones and runs in one command | kv | [x] | `backend/README.md` + `docker-compose.yml` |
| 10 | Authorization letter (college letterhead) | SPOC / kv | [ ] | draft: [authorization-letter.md](../product/submission/authorization-letter.md) |

## Verdict (2026-09-08)

| Round surface | Verdict | Why |
|---|---|---|
| Internal faculty panel, **backend-only** | **GO** | Seeded persona + OpenAPI + live 403 on commander lookup. Script below. |
| Internal faculty panel, **full product demo** | **NO-GO** | Rows 3–8 open. |
| National portal idea submission | **CONTENT-GO / TEMPLATE-WAIT** | Title + description + 13-slide content deck ready (PM-003). Official SIH PPT template not in repo — risa pastes, does not restyle. |

Flip this file's header Status to stay `[x]` (the *check* is done). Do not claim the *round* is won until rows 3–8 move.

## Faculty walkthrough (backend-only, 3 minutes)

Laptop: `cd backend && python -m app.seed && uvicorn app.main:app --port 8000`. Open http://127.0.0.1:8000/docs.

| Clock | Say | Do |
|---|---|---|
| 0:00–0:10 | One cited number: ThePrint — 654 CAPF suicides, ~50,000 resignations in 5 years. | Title in the browser tab: SAARTHI. |
| 0:10–0:25 | Login `counsellor.a` / `saarthi`. GET `/risk/ps_demo01/explanation`. | Read top-3 factors aloud. |
| 0:25–0:40 | Login `commander.3bn`. GET `/aggregates/unit/3BN`. | Point: k ≥ 5, **no names**. |
| 0:40–0:55 | Same commander token, GET `/welfare/personnel/CR-DEMO-01`. | **403**. "That is architecture, not a promise." |
| 0:55–1:10 | Dual-key: counsellor opens `/privacy/unmask`, welfare.a approves. | |
| 1:10–1:25 | Login `jawan.demo`, GET `/app/who-viewed`. | Pause. This is the 15-second receipt. |
| 1:25–1:40 | POST `/roster/rebalance` as welfare, GET as commander — workload numbers only. | |
| 1:40–2:00 | Impact: individual scores reaching command = **0**. | |
| 2:00–2:20 | Stack: FastAPI, rules v1 not ML, on-prem. | architecture.md C4. |
| 2:20–2:30 | "Apps and official-template deck are the next 7 days — the engine already runs." | Stop. |

If the API is down: play nothing; do not debug on stage. This walkthrough **is** the fallback until QA-007 records video.

## 36-hour feasibility pointer

Finale hour plan: [finale-36h-plan.md](finale-36h-plan.md). Internal-round pitch uses the 3-minute script in the runbook, not the 36h plan.
