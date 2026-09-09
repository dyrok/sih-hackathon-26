# Handoff — for the agent picking this up

> Written by: the AI agent session working as **neel** · 2026-09-09
> Purpose: if this session ends before the branch is pushed and PR'd, read this
> file first, then `handover-to-kv.md` in this same directory (the human-facing
> summary of what shipped and why — read it too, it has the security findings).

## Where things stand right now

All 17 of neel's board tasks are **functionally complete and tested**:
APP-001…010, PRIV-002, PRIV-003, UX-001, UX-002, QA-001, QA-002, QA-003.
`executable/board.md` rows for neel are `[x]`. Checklists were just regenerated
via `python3 executable/tools/sync-checklists.py` (ran clean, no `--check`
errors expected on neel's rows).

**Everything is on the local `neel` branch, uncommitted.** Nothing has been
pushed. That is the single most important thing to finish if you are picking
this up cold.

## Immediate next steps, in order

1. **Verify the suite is green** (it was, as of the last full run — 138 backend
   tests, 77 data-generator tests, 48 web tests, 34 browser E2E checks):
   ```bash
   cd backend && .venv/bin/python -m pytest -q          # expect all passed
   cd ../data && ../backend/.venv/bin/python -m pytest tests -q   # 77 passed
   cd ../web && bun test                                  # 48 passed
   bun scripts/lint-boundaries.mjs                        # boundaries clean
   bun run typecheck                                      # exit 0 x3
   bun run build                                           # 3 apps compile
   ```
   If anything regressed, it is almost certainly because another docs-sync
   background workflow (`wf_b041a18b-ef9`, see below) touched a file
   concurrently with this session's own edits — re-read the file before
   assuming your fix is wrong.

2. **Check whether the docs-sync workflow finished.** A background Workflow
   (run id `wf_b041a18b-ef9`, script at
   `/private/tmp/claude-501/-Users-ns-code-sih-hackathon-26/00435b4b-834a-4ab3-90d2-2926fe92c44a/scratchpad/docs.js`)
   was mid-flight, updating: F02, F03, F06, F07, F09, design.md,
   design-client-apps.md, rbac-matrix.md, security-model.md, test-plan.md,
   usability-testing.md. If you see a `<task-notification>` for it, read the
   result before touching any of those files again — verify its claims the way
   the workflow's own verify-phase agents were instructed to (every fact must
   trace to a real file/line; no invented statistics; nothing outside the named
   files touched). If it did NOT finish, either wait for it or finish the sync
   yourself by hand — the prompt in `docs.js` documents exactly what changed in
   code that the docs need to catch up to.

3. **Review `git status --porcelain`** before staging. As of last check there
   were ~147 modified + ~78 untracked paths, all attributable to this session's
   own work (backend routers/models/tests, all of `web/apps/{jawan,counsellor,
   commander}`, `web/packages/*`, `data/`, `docs/`, `scripts/`, `Makefile`,
   `.github/workflows/ci.yml`). Confirm nothing unexpected is in there (no
   stray `.env`, no other member's untracked work) before `git add`.

4. **Commit.** Suggested shape — several commits by concern, not one giant
   commit, so kv's review has natural checkpoints. Every commit message must
   start with a task ID per AGENTS.md rule 4. Rough grouping that matches the
   work:
   - `[APP-001] Web-first jawan/counsellor/commander apps + shared @saarthi/* packages`
   - `[PRIV-002] RBAC/ABAC enforcement test suite (test_rbac_enforcement.py)`
   - `[PRIV-003] Security hardening: 12 findings fixed + regression tests`
   - `[QA-001] Synthetic data generator (data/) — 1000 personnel, 90 days, deterministic`
   - `[QA-003] Coverage report, perf gate (scripts/perf.py), browser E2E (web/e2e)`
   - `[UX-001] Contrast fixes (state-ink/focus/saffron-ink tokens) + lint enforcement`
   - `[UX-002] Design canvas mockups (docs/architecture/design/mockups/)`
   - docs-sync commit(s) once the workflow above is confirmed done and verified
   - `Ops: Makefile, CI workflow, .gitignore`

   Do **not** amend or squash — AGENTS.md and the base instructions both say
   create new commits, never amend published work.

5. **Push** `neel` to `origin/neel`:
   ```bash
   git push origin neel
   ```
   This branch is 27+ commits ahead of `origin/neel` already (pre-existing,
   from before this session) plus everything new above — a normal fast-forward
   push, not a force-push. Do not force-push.

6. **Open a PR into `main`**, title starting with the primary task ID (pick the
   most representative, e.g. `[APP-001] neel: web apps, security hardening,
   synthetic data, QA-003 coverage`). Body should point at
   `executable/neel/handover-to-kv.md` rather than duplicating it.

7. **Notify kv**: "PR ready for review" per the repo's branch → notify → merge
   workflow (AGENTS.md rule 5). Do not merge it yourself — only kv merges.

## Things to NOT do

- Do not merge `origin/manan` or `origin/tejas` into `main` — that's kv's call
  per AGENTS.md rule 5 (only kv merges). They were left alone deliberately.
- Do not touch `backend/` files outside what's already changed here without
  re-reading them first — kv may have committed further changes to `main`
  independently while this session ran; do a `git fetch origin` and check
  `git log origin/main` before assuming the base hasn't moved.
- Do not re-run the `/design` skill to republish the mockup canvas unless the
  artboards in `docs/architecture/design/mockups/*.dc.html` have changed since
  the last publish — the published URL is already recorded in
  `docs/architecture/design/mockups/README.md`.
- Do not hand-edit any `executable/<name>/checklist.md` — always regenerate via
  `python3 executable/tools/sync-checklists.py`.

## Key artifacts to know about

| What | Where |
|---|---|
| Human-facing summary for kv | `executable/neel/handover-to-kv.md` |
| Security findings + fixes (12 issues) | `docs/quality/security-test-cases.md` (1069 lines) |
| Threat model | `docs/quality/threat-model.md` (359 lines) |
| Coverage/perf run log | `docs/quality/coverage-report.md` |
| Browser E2E suite | `web/e2e/smoke.mjs` — run via `make e2e` (needs API + 3 dev servers up) |
| Perf gate script | `scripts/perf.py` — run via `make perf` |
| Synthetic data generator | `data/` — run via `make generate` |
| Design canvas mockups | `docs/architecture/design/mockups/` (11 `.dc.html` artboards + README with the published URL) |
| One-command entry point | `Makefile` — `make help` lists everything |
| CI | `.github/workflows/ci.yml` — firewall gate runs first, alone |

## If you are a fresh agent with zero context

Read, in order: `AGENTS.md` → `global_instructions.md` →
`executable/neel/plan-for-neel.md` → this file → `handover-to-kv.md`. Then run
`git status` and `git log --oneline -20` on the `neel` branch to see exactly
what's committed vs. what's still sitting in the working tree, and pick up from
whichever step above matches reality at the time you read this.
