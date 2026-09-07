# Plan — tejas (QA assistant & demo support · 1st year)

> Branch: `tejas` · Last updated: 2026-09-05 · Buddy: kv (anything unclear → ask kv)

## My role
I help **run the tests and support the demo** — simple, guided tasks: sweep the docs for missing stamps and broken links, execute the manual test checklist neel gives me and record results, and help risa record the fallback demo video. The complex work (test plan, synthetic data generator) is neel's; the demo runbook is kv's.

## Files I own (nobody else edits these)

| File | Purpose |
|---|---|
| `executable/tejas/notes.md` | my work log — QA sweep results, test pass/fail records, questions (create it when I start) |

## My tasks (live rows: [board.md](../board.md))

| ID | Task | Due |
|---|---|---|
| QA-005 | Docs QA sweep: every doc has Owner + Status stamp, all links resolve; report gaps to kv | 09-09 |
| QA-006 | Run the manual test checklist from [test-plan.md](../../docs/quality/test-plan.md) (guided by neel); record pass/fail per case | 09-17 |
| QA-007 | Demo rehearsal support + record the fallback video with risa | 09-18 |

## How I work (every task, same steps)

1. `git switch tejas` — I work only on my branch. Never commit to `main`.
2. Open my `checklist.md` — pick the top task that is not done.
3. Read the doc linked in the task — that is my instruction sheet.
4. Do the task in small commits; every commit message starts with the task ID.
5. `git push`, then open a Pull Request into `main` titled `[TASK-ID] what I did`.
6. **Tell kv: "PR ready for review."** — this is the "testing is over, please merge" signal.
7. kv reviews and merges to `main`. I never merge my own PR.
8. After kv merges: `git switch main && git pull`, set my board row `[x]`, done.

If a task feels too big — split it with kv. That is expected, not a failure.

## Definition of done (per task)
- [ ] PR opened and kv notified · kv merged it
- [ ] Test results recorded per case (pass/fail + one-line note) in my `notes.md`
- [ ] board.md row `[x]`

## Key docs I read (not mine — I learn from them)
[test-plan](../../docs/quality/test-plan.md) · [demo-runbook](../../docs/quality/demo-runbook.md) · [F09 synthetic data](../../docs/features/F09-synthetic-data-generator.md) · [prd](../../docs/product/prd.md)
