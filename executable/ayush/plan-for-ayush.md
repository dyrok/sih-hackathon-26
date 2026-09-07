# Plan — ayush (ML research assistant · 1st year)

> Branch: `ayush` · Last updated: 2026-09-05 · Buddy: kv (anything unclear → ask kv)

## My role
I help with the **research side of the ML/theory work** — simple, guided tasks: verifying citations, collecting facts, summarizing what I read. The complex engine work (rules engine, validation harness, fairness audit) is kv's; I learn from it and support it.

## Files I own (nobody else edits these)

| File | Purpose |
|---|---|
| `executable/ayush/notes.md` | my work log — findings, questions, dead links (create it when I start) |

## My tasks (live rows: [board.md](../board.md))

| ID | Task | Due |
|---|---|---|
| ML-005 | Verify every link + citation in [datasets-research.md](../../docs/explanation/datasets-research.md); list dead links for neel | 09-10 |
| ML-006 | One-page instrument factsheet (PHQ-9/GAD-7/PSS-10/ISI: items, bands, source) from [clinical-instruments.md](../../docs/explanation/clinical-instruments.md) for the deck | 09-11 |

## How I work (every task, same steps)

1. `git switch ayush` — I work only on my branch. Never commit to `main`.
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
- [ ] Every claim has a working source link — no invented statistics
- [ ] Findings written into my `notes.md`
- [ ] board.md row `[x]`

## Key docs I read (not mine — I learn from them)
[model-explainer](../../docs/explanation/model-explainer.md) · [datasets-research](../../docs/explanation/datasets-research.md) · [clinical-instruments](../../docs/explanation/clinical-instruments.md) · [F04 risk engine](../../docs/features/F04-risk-rules-engine.md)
