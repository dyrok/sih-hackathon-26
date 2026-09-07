# Plan — manan (Compliance research assistant · 1st year)

> Branch: `manan` · Last updated: 2026-09-05 · Buddy: kv (anything unclear → ask kv)

## My role
I help with the **compliance side** — simple, guided tasks: collecting the exact legal text with sources, and later clicking through the app to verify the privacy flows work. The complex compliance docs are split between the seniors (DPDP/privacy-law mapping: kv; security model and RBAC matrix: neel) — I learn from them and support them.

## Files I own (nobody else edits these)

| File | Purpose |
|---|---|
| `docs/compliance/sources.md` | the statute sources pack — exact quoted sections with official links |
| `executable/manan/notes.md` | my work log — findings, questions (create it when I start) |

## My tasks (live rows: [board.md](../board.md))

| ID | Task | Due |
|---|---|---|
| PRIV-005 | Statute sources pack: copy the official text of DPDP §7(i), §4–5 and MHCA §23 with source links into [sources.md](../../docs/compliance/sources.md) | 09-10 |
| PRIV-006 | Manual privacy walkthrough: click through the app once it builds — consent given, consent withdrawn, who-viewed-my-data — record pass/fail | 09-15 |

## How I work (every task, same steps)

1. `git switch manan` — I work only on my branch. Never commit to `main`.
2. Open my `checklist.md` — pick the top task that is not done.
3. Read the doc linked in the task — that is my instruction sheet.
4. Do the task in small commits; every commit message starts with the task ID.
5. `git push`, then open a Pull Request into `main` titled `[TASK-ID] what I did`.
6. **Tell kv: "PR ready for review."**
7. kv reviews and merges to `main`. I never merge my own PR.
8. After kv merges: `git switch main && git pull`, set my board row `[x]`, done.

If a task feels too big — split it with kv. That is expected, not a failure.

## Definition of done (per task)
- [ ] PR opened and kv notified · kv merged it
- [ ] Every quoted legal text has the exact section number + official source link
- [ ] Findings written into my `notes.md`
- [ ] board.md row `[x]`

## Key docs I read (not mine — I learn from them)
[dpdp-2023-mapping](../../docs/compliance/dpdp-2023-mapping.md) · [mental-healthcare-act-2017](../../docs/compliance/mental-healthcare-act-2017.md) · [rbac-matrix](../../docs/compliance/rbac-matrix.md) · [F08 privacy architecture](../../docs/features/F08-privacy-safety-architecture.md)
