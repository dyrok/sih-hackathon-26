# Internal-round readiness check (PM-002)

> Owner: kv · Status: [~] in progress · Last updated: 2026-09-08
> Depends on: DECK-001, QA-004. Hard idea-submission deadline: **2026-09-20**.

## Gate criteria (all must be `[x]` before we walk into the internal round)

| # | Artefact | Owner | Status | Notes |
|---|---|---|---|---|
| 1 | Working backend demo loop (seed + score + unmask + who-viewed) | kv | [x] | `backend/` on branch `kv` |
| 2 | Firewall tests green | kv | [x] | `backend/tests/test_firewall.py` |
| 3 | Jawan app screens (check-in, consent, who-viewed) | neel | [ ] | APP-001…005 |
| 4 | Counsellor console | neel | [ ] | APP-007 |
| 5 | Commander dashboard (aggregates) | neel | [ ] | APP-008 — API is ready |
| 6 | Official SIH-template deck PDF | risa | [ ] | DECK-001 |
| 7 | 3-min demo video + fallback file on two devices | risa / tejas | [ ] | DECK-002 / QA-007 |
| 8 | Five clean rehearsals logged | kv | [ ] | [demo-runbook.md](demo-runbook.md) §5 |
| 9 | Repo clones and runs in one command | kv | [x] | `backend/README.md` + `docker-compose.yml` |
| 10 | Authorization letter (college letterhead) | SPOC / kv | [ ] | outside repo |

## Go / no-go

**No-go for a full product demo** until rows 3–8 move. **Go for a backend-only faculty walkthrough** (OpenAPI + seeded persona + firewall live-fail) as of 2026-09-08.

Re-run this table at the daily standup (PM-001). Flip this file to `[x]` only when every row is `[x]` or explicitly waived in writing.

## 36-hour feasibility pointer

Finale hour plan: [finale-36h-plan.md](finale-36h-plan.md). Internal-round pitch uses the 3-minute script in the runbook, not the 36h plan.
