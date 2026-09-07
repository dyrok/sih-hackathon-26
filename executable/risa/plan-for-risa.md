# Plan — risa (Presentation lead · 1st year)

> Branch: `risa` · Last updated: 2026-09-05 · Buddy: kv (anything unclear → ask kv)

## My role
I am **dedicated to the presentation**. I build the SIH deck in the official template, collect prototype screenshots, make the demo video with tejas, and rehearse the pitch. Everything I need to know is in two docs — start there:

1. **[ppt-guide.md](../../docs/deck/ppt-guide.md)** — how to build the deck, step by step (tools, build order, visual rules, mistakes checklist)
2. **[deck-outline.md](../../docs/deck/deck-outline.md)** — what goes on each slide

## Files I own (nobody else edits these)

| File | Purpose |
|---|---|
| `docs/deck/deck-outline.md` | slide-by-slide deck spec |
| `docs/deck/ppt-guide.md` | beginner PPT guide |
| `deck/` | the actual deck + diagrams |
| `executable/risa/notes.md` | my work log (create it when I start) |

## My tasks (live rows: [board.md](../board.md))

| ID | Task | Due |
|---|---|---|
| DOCS-014 | deck-outline.md | done |
| DOCS-016 | ppt-guide.md | done |
| DECK-003 | Impact/scalability slide figures with citations | 09-17 |
| DECK-001 | Build the deck in the official SIH template | 09-17 |
| UX-003 | Collect + caption prototype screenshots (guided by neel) | 09-16 |
| DECK-004 | Presentation practice ×3 + jury cheat sheet | 09-18 |
| DECK-002 | Demo video (with tejas) | 09-18 |

## How I work (every task, same steps)

1. `git switch risa` — I work only on my branch. Never commit to `main`.
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
- [ ] Deck follows the official SIH template exactly
- [ ] Every number cited — no invented statistics
- [ ] board.md row `[x]`

## Key docs I work from
[ppt-guide](../../docs/deck/ppt-guide.md) · [deck-outline](../../docs/deck/deck-outline.md) · [winning-strategy](../../docs/product/winning-strategy.md) · [impact-and-metrics](../../docs/product/impact-and-metrics.md) · [demo-runbook](../../docs/quality/demo-runbook.md)
