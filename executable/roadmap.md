# Roadmap — SIH 2026 anchors

> Owner: kv · Hard deadline: **idea submission 2026-09-20** ([SIH 2026 Guidelines](https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf)) · Internal college round: date TBD by SPOC — plan to be ready early.
> Evaluation weights (official): R1 idea 20% · R2 prototype progress 30% · R3 finale demo 50%.

## Phase 0 — Docs brain (Sep 5–8)
All `docs/` drafted: problem statement, PRD, architecture + ADRs, design docs, 9 feature docs, compliance, explanations, quality docs, deck outline. **Gate: docs/README.md index shows every doc with an owner.**

## Phase 1 — Prototype v1 (Sep 8–15)
Working vertical slice: HR signals → rules engine → explainable alert → counsellor console → roster swap → jawan app with who-viewed-my-data. **Gate: full demo loop runs on synthetic data.**

## Phase 2 — Demo package (Sep 15–19)
Synthetic data generator seeded (1,000 personnel, 90 days) · scripted persona demo · official-template deck (PDF) · 3-min demo video · recorded-video fallback on two devices. **Gate: PM-002 readiness check.**

## Phase 3 — Submission (Sep 19–20)
Portal submission: idea title, description, PDF deck. **Deadlines are absolute.**

## Phase 4 — Hardening (Sep 21 – Nov 30)
Mentor feedback visibly incorporated (R2 scores this) · ML-002 backtest + fairness audit · DPDP audit vs implementation · offline sync hardening. **Gate: private internal demo to faculty; feedback loop closed.**

## Phase 5 — Grand finale prep (Nov – Dec)
- Architecture pre-decided (this repo IS the decision record) — coding starts hour 1
- 3-minute demo script rehearsed 5×: 10s problem+statistic → 90s live demo on seeded data → 20s impact → 20s architecture → 10s scale
- Pre-written jury answers for the PS's six technical challenges (see [winning-strategy.md](../docs/product/winning-strategy.md))
- Offline backups: PDF deck + recorded demo on pen drive and two devices, local-run build, hotspot backup

## The three tells (what loses SIHs)
1. Beautiful slides, no working prototype → build ugly-but-working first
2. Demo dies live → recorded fallback + seeded data, never an empty dashboard
3. Vague "useful for society" → every claim carries a source or a Low/Med/High rating
