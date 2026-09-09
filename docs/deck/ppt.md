# ppt.md — SAARTHI deck, slide by slide (visual-first build sheet)

> Owner: risa · Status: [~] drafting · Last updated: 2026-09-08
> **This is the build sheet for DECK-001.** Every slide below gives you the paste-ready title, the visual to make first, the exact on-slide words, and what to say. Spec: [deck-outline.md](deck-outline.md) · How-to: [ppt-guide.md](ppt-guide.md). Build inside the **official SIH template, unmodified**.

## 0. The method (from the research, 5 rules)

1. **Action titles, not topic titles.** Every title states the insight ("Two tiers: counsellor sees the person, command sees only crowds"), never the topic ("Architecture"). Titles are paste-ready below — do not soften them.
2. **Read-through test.** Strip every slide to its title only. Read 1→13. It must sound like one persuasive story. The titles below already pass it — keep them in order.
3. **Visual before text.** Build the exhibit (diagram / screenshot / table) first, then trim words around it. One idea per slide; the title proves it, the visual carries it.
4. **One accent per slide.** Template colours for structure; ONE emphasized element per slide (the big number, the wall on the architecture slide). No rainbow, no chart junk, nothing below 18pt.
5. **Grandma test.** Every diagram gets a plain-language caption under it. If a slide needs a data scientist to read it, fix the slide.

---

## 1 — Title  · *scores: presentation/fit*

- **Title (paste):** SAARTHI — AI-Based Predictive Personnel Stress & Welfare Monitoring System for Uniformed Forces
- **Visual:** official template title layout, nothing added. Below the title, one compact line-block: PS ID, org, theme.
- **On-slide words:** `PS ID 26186 · CRPF / Ministry of Home Affairs · MedTech/HealthTech · Team SAARTHI — 6 members, [Institute Name]`
- **Check:** ≥1 female member listed · PS ID and org copied exactly from [problem-statement.md](../product/problem-statement.md) · no slogans, no team photo.
- **Say it:** "We are Team SAARTHI. सारथी — the charioteer who guides. Problem 26186, CRPF."

## 2 — Problem  · *scores: solution approach / PS-relevance*

- **Title (paste):** Stress is caught too late — 654 CAPF personnel lost to suicide in 5 years
- **Visual:** ONE number, huge, centre: **654**. Under it, smaller line: `~50,000 resignations · 5 years`. Nothing else competes.
- **Grandma caption:** "Today, a jawan struggles in silence until they are already in crisis. Detection is manual, self-reported, and late."
- **Source line (mandatory):** `Source: ThePrint — 654 suicides, ~50,000 resignations in 5 years (theprint.in)`
- **Avoid:** second statistics, dramatic imagery, invented numbers. One cited source, full stop.
- **Say it:** "This is not a metrics problem. It is a detection problem — and stigma guarantees self-reporting fails."

## 3 — Team & roles  · *scores: teamwork*

- **Title (paste):** Six owners, six domains — every jury question has a name on it
- **Visual:** 3×2 grid of cards. Each card: name (bold) + role + one domain word. No photos, no CGPA.
- **On-slide words (cards):**
  `kv — PM · architecture & privacy law` · `neel — apps, dashboards & security` · `ayush — ML research` · `manan — compliance (DPDP 2023)` · `risa — presentation & demo` · `tejas — QA & demo support`
- **Say it:** "Each of us owns one domain and will answer for it — including the privacy architecture."

## 4 — Solution overview  · *scores: solution approach + innovation*

- **Title (paste):** Welfare signals in, help out — before crisis
- **Visual:** horizontal 4-step flow, icons + 2 words each:
  `HR signals + check-ins → explainable risk → intervention ladder → verified recovery`
  Under the flow, a thin solid bar labelled: **"Architectural firewall — individual scores never reach command."**
- **Grandma caption:** "The roster and a voluntary tap tell the system enough. Help goes out at Amber, not at the funeral."
- **Avoid:** 20-item feature lists, the phrase "AI-powered end-to-end platform".
- **Say it:** "Zero-effort HR signals for the silent majority, voluntary check-ins for the willing — both feed one explainable engine."

## 5 — Methodology / workflow  · *scores: solution approach*

- **Title (paste):** Detect → explain → intervene → verify — a loop a jawan can trust
- **Visual:** circular loop diagram (draw.io, 4 nodes with arrows); beside it, a vertical response ladder strip: `Green — self-care` / `Amber — buddy nudge` / `Red — counsellor ≤24h` / `Critical — welfare officer`.
- **Grandma caption:** "Jawan taps a button → counsellor reaches out within 24 hours → roster changes → the score trends down. The loop closes and you can see it close."
- **Avoid:** 12-box spaghetti, Gantt charts, model-training pipelines (v1 is a rules engine — say it plainly).
- **Say it:** "Every flag ships with its top-3 reasons — '47 consecutive duty days, sleep −30%'. No black box."

## 6 — Tech stack  · *scores: technical feasibility*

- **Title (paste):** Built to run inside the force perimeter — nothing exotic
- **Visual:** two-column table, "Built by us" vs "Off the shelf", plus one on-prem badge:

| Built by us | Off the shelf |
|---|---|
| Transparent rules engine v1 (no black box) | FastAPI + PostgreSQL backend |
| Explainable evidence cards | Expo / React Native — offline-first on SQLite, Android API 26+ |
| Two-tier privacy layer (ADR-0003) | Standard RBAC, AES-256 |

- **Avoid:** AI + Blockchain + IoT together; iOS (Android-only, say so honestly).
- **Say it:** "An honest engine beats an unverifiable 99%. Everything runs on-prem; no foreign SaaS touches welfare data."

## 7 — Architecture / data flow  · *scores: innovation + feasibility*

- **Title (paste):** Two tiers by architecture: the counsellor sees the person, command sees only crowds
- **Visual — the money diagram.** Left→right: `HRMS + app data` → `Pseudonymisation` → `Risk engine (top-3 factors)` → **splits into two boxes with a visible wall between them**: `Counsellor — individual, consent-gated` ⟷ `Commander — unit aggregates only, k ≥ 5, no names`. Draw the wall thick. Add `dual-key unmask · who-viewed-my-data receipt` as a small tag under the wall.
- **Grandma caption:** "No arrow ever goes from a person's name to the commander's screen — the API physically rejects it."
- **Avoid:** any arrow from a name to the commander box. This one diagram is the whole trust story ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).
- **Say it:** "This is not a policy promise. It is enforced in code — route-level rejection, append-only audit."

## 8 — Innovation & differentiation  · *scores: innovation*

- **Title (paste):** Structural differences, not a nicer UI
- **Visual:** comparison table, 4 columns (`SAARTHI / wellness apps / HRIS / EAP`), 5 rows with ✓/✗:

| | SAARTHI | Wellness apps | HRIS | EAP |
|---|---|---|---|---|
| DPDP-aligned, on-prem | ✓ | ✗ | partial | ✗ |
| Offline-first (API 26+) | ✓ | ✗ | ✗ | ✗ |
| Hindi + regional, voice & icons | ✓ | ✗ | ✗ | ✗ |
| Tele-MANAS (14416) integration | ✓ | ✗ | ✗ | partial |
| Scores architecturally out of command | ✓ | n/a | ✗ | ✗ |

- **Avoid:** "first ever" claims; trashing named competitors.
- **Say it:** "Consumer apps lose on compliance and connectivity. We are indigenous, force-specific, and privacy-first by construction."

## 9 — Prototype / demo  · *scores: prototype progress + usability + demo clarity*

- **Title (paste):** Working today — real screens, real seeded data
- **Visual:** 2×2 grid of REAL screenshots (get from neel): ① roster home with check-in card ② who-viewed-my-data receipt ③ counsellor evidence card ④ commander heatmap. Data visible: "3rd Bn, 22% elevated fatigue". QR + short link for the demo video, top-right.
- **Caption every screenshot** (uncaptioned = decoration): `① daily check-in, one tap` · `② the jawan sees who viewed their record` · `③ every flag shows its top-3 factors` · `④ commander sees crowds, never names`.
- **Avoid:** mockups, empty dashboards, design-system screenshots.
- **Say it:** "Offline demo, on this laptop, on seeded Indian-context data. [Then play the loop from demo-runbook.md.]"

## 10 — 36-hour implementation timeline  · *scores: the dedicated 36-hour criterion*

- **Title (paste):** 36 hours, six owners — every block has hours and a name
- **Visual:** horizontal bar, 6 segments sized to hours, each labelled `hours · owner`:
  `0–4 setup + data seeding (all)` · `4–12 signal layer + rules engine (kv)` · `12–20 jawan app: check-in, consent, who-viewed (neel)` · `20–28 consoles + privacy layer (neel + kv)` · `28–34 integration + 90-day persona (all)` · `34–36 demo dry-run (risa + tejas)`.
- **Avoid:** week-long plans, "sprint" language, unnamed owners.
- **Say it:** "Architecture is pre-decided before hour 0 — read it straight: [winning-strategy.md §6]."

## 11 — Impact & scalability  · *scores: market readiness / impact*

- **Title (paste):** We measure trust, not promises — zero scores to command, zero punitive outcomes
- **Visual:** compact KPI table (targets labelled honestly) + one-line scalability strip:

| KPI | Target | Type |
|---|---|---|
| Voluntary participation | ≥ 30% of unit | reasoned estimate |
| Red flag → counsellor contact | ≤ 24 h | design target |
| Punitive outcomes linked to system | **0** | monitored |
| Individual scores reaching command | **0** | **architectural guarantee** |
| Risk trend after intervention | down at 4 weeks | directional |

  Scalability strip: `Technical High · Deployment High · Adoption Med · Languages Med–High · Outcome evidence Low→Med` — each with its one-word reason from [impact-and-metrics.md](../product/impact-and-metrics.md).
- **Avoid:** "saves X crores", "lives saved", accuracy % we haven't measured.
- **Say it:** "We published what we will NOT claim. The zero-zero row is the trust signal — measured, not hoped."

## 12 — Future scope / out-of-scope  · *scores: future scope*

- **Title (paste):** What we build next — and what we deliberately refuse to build
- **Visual:** two columns, equal weight:
  - **Next:** `ML v2 trained on counsellor-labelled outcomes · regional languages (i18n data files, not a redesign) · wearables (voluntary) · differential privacy on aggregates`
  - **Never:** `facial emotion recognition · phone monitoring · scores in ACR/appraisal · clinical diagnosis`
- **Grandma caption:** "The 'never' column is the point — maturity means deciding what NOT to build."
- **Say it:** "Contested science and trust-killing features are out, regardless of how impressive they'd look."

## 13 — Conclusion  · *scores: demo clarity & persuasiveness*

- **Title (paste):** 0 — individual scores that can reach command, guaranteed by architecture
- **Visual:** ONE giant **0**, centre. Beneath: one line of team strength + links.
- **On-slide words:** `Not a policy. A firewall you can read in the code. · repo: github.com/… · demo video: …`
- **Avoid:** thank-you filler, a second statistic, a QR graveyard.
- **Say it:** "When you ask 'will this be used against me?' — our answer is the only one that can be verified: zero, by architecture."

---

## Read-through test (verify before building anything)

> Read only the titles, in order — they must tell the whole story alone. (Slide 1 is the title slide; its title is the project name itself, so it is not listed.)

1. Stress is caught too late — 654 CAPF personnel lost to suicide in 5 years
2. Six owners, six domains — every jury question has a name on it
3. Welfare signals in, help out — before crisis
4. Detect → explain → intervene → verify — a loop a jawan can trust
5. Built to run inside the force perimeter — nothing exotic
6. Two tiers by architecture: the counsellor sees the person, command sees only crowds
7. Structural differences, not a nicer UI
8. Working today — real screens, real seeded data
9. 36 hours, six owners — every block has hours and a name
10. We measure trust, not promises — zero scores to command, zero punitive outcomes
11. What we build next — and what we deliberately refuse to build
12. 0 — individual scores that can reach command, guaranteed by architecture

## Build order (DECK-001 — follow top to bottom)

1. Download official SIH template from the portal → drop the 13 titles above in. No content yet.
2. Slide 2: the 654 slide, done properly (huge number + source line).
3. Diagrams: slides 4, 5, 7 in draw.io → export PNG 2× → keep sources in `deck/diagrams/`.
4. Tables: slides 6, 8, 10, 11 — plain template tables, one accent element each.
5. Screenshots (UX-003, ask neel) → slide 9 grid + captions → video QR (DECK-002, with tejas).
6. Trim every slide to ≤ ~30 words outside titles. Cut, never add.
7. PDF export → review with kv → rehearse ×3 (DECK-004, [ppt-guide.md §5](ppt-guide.md)).

## Pre-export checklist

- [ ] Official template untouched · ≤ 13 slides · PDF exported
- [ ] Every title is the action title from this file (read-through passes aloud)
- [ ] Every number carries its source line; every target labelled estimate/directional
- [ ] Every screenshot captioned; video link embedded + tested on another device
- [ ] No slide below 18pt · one accent element per slide · no transitions except plain appear
- [ ] Each member can present any slide in viva (backup stats for viva: [research-sih-2026.md §7](../product/research-sih-2026.md))

## Sources for the method above

- [McKinsey Presentation Framework — Pyramid Principle, Action Titles, Ghost Deck (A1 Slides, 2026)](https://a1slides.com/mckinsey-presentation-framework/)
- [Presentation Design Trends 2026 — ultra-minimal, one idea per slide, accessibility-first (SketchBubble)](https://www.sketchbubble.com/blog/presentation-design-trends-2026-the-ultimate-guide-to-future-ready-slides/)
- [2026 research: visual-first, one idea per slide slides score higher engagement (NEN)](https://nen.wfglobal.org/highlights/presentation-slide-best-practices-research-2026-138971)
- Plus the deck sources already curated in [ppt-guide.md §6](ppt-guide.md) (SIH template format + evaluator scoring).
