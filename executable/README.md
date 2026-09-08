# executable/ — THE HANDS

> Owner: kv · Status: [x] current · Last updated: 2026-09-05
>
> This folder tells every team member (and their AI agents) how to execute work. The **brain** lives in [`docs/`](../docs/README.md) — every task here links to a doc there. The **master roadmap + complete work progress checklist** lives in [`global_instructions.md`](../global_instructions.md) (§5).

## The rules (memorize these)

1. **One owner per file and task.** Ownership tables live in your [plan-for-<name>.md](kv/plan-for-kv.md). Never edit someone else's file.
2. **`board.md` is the single status source.** Owners edit ONLY the `Status` column of their own rows. Only `kv` adds/removes/reassigns tasks or changes owners/dates.
3. **Checklists are generated, never hand-edited.** `python3 executable/tools/sync-checklists.py` regenerates every `checklist.md` from `board.md`. Run by `kv` daily (status `[x]` only if the script ran clean).
4. **Task IDs everywhere + branch → notify → merge.** PR title: `[BACK-003] HR signal ingestion endpoint`. Commits reference the ID. Everyone works only on their own branch (branch name = your name), never directly on `main`. When a task **and its testing** are done: push, open a PR into `main`, and **notify `kv` (maintainer): "PR ready for review"**. **Only kv merges PRs into `main`** (kv's own PRs are reviewed by neel). Never merge your own PR.
5. **Docs update in the same PR.** A code PR that should have touched `docs/` and didn't gets rejected in review.
6. **Status legend:** `[ ]` todo · `[~]` in-progress · `[x]` done · `[!]` blocked (reason + who unblocks, right in the cell).
7. **Definition of done (every task):** task + testing complete → PR opened → kv notified → kv merged → board Status `[x]` → checklist regenerated.
8. **Blocked > 24h** → `[!]` on your row with reason + who unblocks → ping `kv`. Do not silently work around another member's deliverable.
9. **No invented statistics** in any doc or deck. Impact claims are Low/Med/High or reasoned estimates with a cited source.
10. **Welfare, not discipline** — if your change can route an individual score to command hierarchy, it violates ADR-0003 and gets rejected.
11. **Task sizing.** kv + neel carry the backbone. ayush, manan, risa, tejas are 1st-years: their tasks are deliberately simple (verify, collect, copy, record, practice). If a task feels too big, split it with kv — that is expected, not a failure.

## AI-agent workflow (what you feed your agent)

Each member has three files in their folder:

| File | What it is | Who writes it |
|---|---|---|
| `plan-for-<name>.md` | Your role, ownership table, tasks with links to `docs/` | you + kv (assigns) |
| `execute.md` | The copy-paste prompt for your AI agent — context, rules, workflow | you (adapted from template) |
| `checklist.md` | **GENERATED** dated task list from the board | script only |

**Prompt your agent like this:** "Read AGENTS.md at repo root, then read my `plan-for-<name>.md` and `execute.md` in `executable/<name>/`, then the linked `docs/` files for each task. Work only on my files."

## File layout

```
executable/
├── README.md              ← you are here (rules)
├── board.md               ← single status source (kv owns structure)
├── roadmap.md             ← milestones anchored to SIH dates
├── tools/sync-checklists.py
├── kv/  neel/  ayush/  manan/  risa/  tejas/
│     ├── plan-for-<name>.md
│     ├── execute.md
│     └── checklist.md    ← generated
```
