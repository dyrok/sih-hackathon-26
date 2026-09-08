# Portal submission package (PM-003)

> Owner: kv · Status: [x] current · Last updated: 2026-09-08
> Portal needs: idea title, idea description, idea presentation (PDF). Deadline **20 Sep 2026**. Max 500 ideas per PS.

## Idea title (paste into the portal)

**SAARTHI — Predictive Personnel Stress & Welfare Monitoring for Uniformed Forces**

(सारथी: the charioteer who guides.)

## Idea description (paste-ready)

SAARTHI is a welfare — not discipline — system for CAPFs and other uniformed forces. It predicts stress and burnout risk from HR signals the force already holds (leave, roster, deployment, transfers), optional self-reports, and on-device wellness features, then routes help (buddy check, counsellor, roster change, Tele-MANAS 14416) before crisis.

Individual risk scores are architecturally incapable of reaching command hierarchy, ACR, promotion or posting: commander surfaces are unit aggregates with k-anonymity >= 5; unmasking a pseudonym requires counsellor and welfare officer; every read is hash-chained and visible to the jawan as who-viewed-my-data.

v1 is a clinically grounded, explainable rules engine (no fabricated ML accuracy). ML v2 trains only from counsellor outcome labels. The prototype backend (FastAPI) already runs the 90-day scripted persona: Constable, 34, 3rd Bn — silent HR signals -> Amber -> masking flag -> Red -> dual-key unmask -> who-viewed receipt -> roster proposal.

Privacy basis: DPDP 2023 s.7(i)/s.7(d) legitimate use for HR signals; explicit unbundled consent for voluntary data; Mental Healthcare Act 2017 s.23 as the confidentiality floor. On-prem / NIC MeghRaj deployable; no foreign SaaS touches welfare data.

GitHub: https://github.com/dyrok/sih-hackathon-26

## Files in this package

| File | Use |
|---|---|
| [submission/SAARTHI-idea-presentation.pdf](submission/SAARTHI-idea-presentation.pdf) | **13-slide content PDF** — portal-shaped. Rebuild inside the official SIH template before upload (DECK-001, risa). |
| [submission/SAARTHI-idea-presentation.pptx](submission/SAARTHI-idea-presentation.pptx) | Same 13 slides, editable. |
| [submission/authorization-letter.md](submission/authorization-letter.md) | Principal letter draft — print on college letterhead. |
| [submission/build-deck.js](submission/build-deck.js) / [build-pdf.py](submission/build-pdf.py) | Regenerators. |

## Package checklist (kv, T-minus-24h)

- [x] Title + description locked in this file.
- [x] Content PDF + PPTX committed.
- [ ] Deck rebuilt **inside the official SIH template** (DECK-001, risa) — do not upload the cream content deck as the final portal file if the template is issued.
- [ ] Authorization letter signed (college letterhead).
- [ ] GitHub URL in the description (this file).
- [x] No invented statistics. One cited number: ThePrint 654 suicides / ~50,000 resignations in 5 years.

## What we will not claim

- No accuracy %, no "AI diagnosed", no facial recognition, no phone monitoring, no ACR integration.
