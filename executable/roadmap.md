# Roadmap — milestone view

> Owner: kv · **The master roadmap and the complete work progress checklist live in [`global_instructions.md`](../global_instructions.md) (§5).** Live per-task status: [board.md](board.md). This file keeps the quick milestone view.
> Hard deadline: **idea submission 2026-09-20** ([SIH 2026 Guidelines](https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf)) · Internal college round: date TBD by SPOC — plan to be ready early.
> Evaluation weights (official): R1 idea 20% · R2 prototype progress 30% · R3 finale demo 50%.

| Phase | Window | Gate | Status |
|---|---|---|---|
| 0 — Docs brain | Sep 5–8 | every doc has owner + stamp | [x] |
| 1 — Prototype v1 | Sep 8–15 | full demo loop runs on synthetic data | [ ] |
| 2 — Demo package | Sep 15–19 | deck PDF + video + rehearsal done | [ ] |
| 3 — Submission | Sep 19–20 | portal submission | [ ] |
| 4 — Hardening | Sep 21 – Nov 30 | mentor feedback visibly incorporated | [ ] |
| 5 — Finale prep | Nov – Dec | 3-min script rehearsed 5×, offline backups | [ ] |

## Phase summaries

- **0 — Docs brain**: all `docs/` drafted — problem statement, PRD, architecture + ADRs, design docs, 9 feature docs, compliance, explanations, quality docs, deck outline + PPT guide.
- **1 — Prototype v1**: working vertical slice — HR signals → rules engine → explainable alert → counsellor console → roster swap → jawan app with who-viewed-my-data.
- **2 — Demo package**: synthetic data seeded (1,000 personnel, 90 days) · scripted persona demo · official-template deck (PDF) · 3-min demo video · recorded-video fallback on two devices.
- **3 — Submission**: portal submission — idea title, description, PDF deck. Deadlines are absolute.
- **4 — Hardening**: mentor feedback visibly incorporated (R2 scores this) · ML-002 backtest + fairness audit · DPDP audit vs implementation · offline sync hardening.
- **5 — Grand finale prep**: architecture pre-decided (this repo IS the decision record) — coding starts hour 1 · 3-minute demo script rehearsed 5× · pre-written jury answers ([winning-strategy.md](../docs/product/winning-strategy.md)) · offline backups: PDF deck + recorded demo on pen drive and two devices, local-run build, hotspot backup.

## The three tells (what loses SIHs)
1. Beautiful slides, no working prototype → build ugly-but-working first
2. Demo dies live → recorded fallback + seeded data, never an empty dashboard
3. Vague "useful for society" → every claim carries a source or a Low/Med/High rating
