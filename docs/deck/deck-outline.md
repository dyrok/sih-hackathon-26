# Deck Outline — 13 slides, official SIH template

> Owner: risa · Status: [~] drafting · Last updated: 2026-09-05
> Deliverable spec for the idea-presentation PDF (portal deadline 20 Sep 2026) and the finale deck. Source: [research-sih-2026.md §6](../product/research-sih-2026.md#6-slide-deck-structure-official-template-discipline--recommended-flow).

## Template discipline (rules before content)

- **Use the official SIH PPT template unmodified** — fonts, background, colours stay as issued. Do not restyle it; the template is a compliance artefact, and judges notice restyling. Export PDF.
- ~10–13 slides; we commit to 13, mapped 1:1 to the three-round rubric.
- **Video-demo link embedded** on slide 9; prototype screenshots mandatory (differentiator even though not formally required).
- Every diagram passes the **grandma test**: a plain-language caption under each flowchart ("Jawan taps a button → counsellor gets an alert within 24 hours — and no score ever reaches the commander"). If a slide needs a data scientist to read it, it is wrong.
- No wall-of-text slides; one idea per slide; one statistic per problem slide, cited.

## The 13 slides

### 1 — Title
- **Purpose:** identity and compliance in one glance.
- **Beats:** PS ID **26186**, project name SAARTHI, team of 6 (**≥ 1 female member mandatory**), institute, PS org **CRPF / Ministry of Home Affairs**, theme MedTech/HealthTech.
- **Not on it:** template redesign, team photo collage, slogans.

### 2 — Problem
- **Purpose:** prove we own the problem in our own words.
- **Beats:** manual observation + self-reporting delay intervention (PS verbatim, rephrased); **one cited statistic** — ThePrint: 654 CAPF suicides, ~50,000 resignations in 5 years (linked); stigma makes a named mental-health app dead on arrival.
- **Not on it:** five statistics, invented numbers, dramatic imagery.

### 3 — Team & roles
- **Purpose:** show the winning role split (evaluators score teamwork from R1).
- **Beats:** six names; who owns data/models, app/UI, backend, compliance/privacy, docs/demo — each member answers their own domain in viva.
- **Not on it:** CGPAs, filler bios, "all-rounder" for everyone.

### 4 — Solution overview
- **Purpose:** the whole idea in 2–3 lines.
- **Beats:** HR signals (zero-effort) + voluntary check-ins → explainable risk scores → intervention ladder → verified recovery — with an architectural firewall that keeps individual scores away from command ([prd.md](../product/prd.md)).
- **Not on it:** a 20-item feature list; the words "AI-powered end-to-end platform".

### 5 — Methodology / workflow
- **Purpose:** roadmap a non-expert can follow.
- **Beats:** the welfare loop diagram (detect → explain → intervene → verify), grandma-captioned; response ladder Green→Amber→Red→Critical.
- **Not on it:** 12-box spaghetti; Gantt charts; model-training pipelines we don't have (v1 is rules).

### 6 — Tech stack
- **Purpose:** feasibility, honestly stated.
- **Beats:** FastAPI + PostgreSQL backend; Expo/React Native offline-first on SQLite (API 26+ Android); transparent rules engine v1; on-prem deployable. Say what is off-the-shelf vs built.
- **Not on it:** buzzword bingo — no AI+Blockchain+IoT together ([winning-strategy.md](../product/winning-strategy.md)); iOS.

### 7 — Architecture / data flow
- **Purpose:** show the trust layer *as architecture*.
- **Beats:** HRMS signals + app data → pseudonymization → risk engine (explainable factors) → role-scoped outputs: counsellor (individual, consent-gated) vs commander (aggregates, k ≥ 5) → alerts. Draw the two-tier split visibly ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).
- **Not on it:** any arrow from a person's name to the commander's box — the one diagram that would undo us.

### 8 — Innovation & differentiation
- **Purpose:** answer "what exists, and why yours".
- **Beats:** comparison table vs consumer wellness apps / HRIS / EAPs: compliance, offline-first, Hindi + regional languages, Tele-MANAS integration, on-prem sovereignty. Not "better UI" — structural differences ([winning-strategy.md §5](../product/winning-strategy.md)).
- **Not on it:** "first ever" claims; trashing named competitors.

### 9 — Prototype / demo
- **Purpose:** credibility — what works today.
- **Beats:** 3–4 real screenshots (roster home with check-in card, who-viewed-my-data receipt, counsellor evidence card, commander heatmap) + **embedded video link**; offline demo shown.
- **Not on it:** mockups presented as working; empty dashboards; screenshots of the design system instead of the app.

### 10 — 36-hour implementation timeline
- **Purpose:** R1 criterion #5 is scored on this — hours attached.
- **Beats:** hour 0–4 setup + data seeding (architecture pre-decided); 4–12 signal layer + rules engine; 12–20 jawan app (check-in, consent, who-viewed); 20–28 consoles (counsellor, commander) + privacy layer; 28–34 integration + synthetic 90-day persona; 34–36 demo dry-run. Role split beside the timeline.
- **Not on it:** week-long plans; "sprint" language; unnamed owners.

### 11 — Impact & scalability
- **Purpose:** measurable outcomes, no invented numbers.
- **Beats:** pilot KPI table (participation ≥ 30% reasoned estimate; flag-to-contact ≤ 24 h; punitive outcomes = 0 monitored; individual-scores-to-command = 0 architectural guarantee); Low/Med/High scalability ratings with reasoning ([impact-and-metrics.md](../product/impact-and-metrics.md)).
- **Not on it:** "saves X crores", "lives saved", accuracy percentages we haven't measured.

### 12 — Future scope / out-of-scope
- **Purpose:** progression potential *and* maturity.
- **Beats:** future — ML v2 from counsellor labels, regional languages, wearables, differential privacy on aggregates. Out-of-scope slide: facial emotion recognition, phone monitoring, scores in ACR flows, clinical diagnosis — "what we deliberately did not build" reads as maturity.
- **Not on it:** promises without owners; "everything in v2".

### 13 — Conclusion
- **Purpose:** one number the jury repeats afterwards.
- **Beats:** the memorable number — **0: individual scores that can reach command, guaranteed by architecture** — plus one line of team strength and the repo/video links.
- **Not on it:** thank-you filler; a second statistic; a QR code graveyard.

## Pre-submission checklist

- [ ] Official template untouched · PDF exported · ≤ 13 slides
- [ ] Video link embedded + tested on another device · screenshots real, not mockups
- [ ] Every statistic carries a citation; every target labelled estimate/directional
- [ ] Timeline slide has hours + owners · each member can present any slide in viva
- [ ] Backup: pen drive + email + [demo-runbook.md](../quality/demo-runbook.md) fallbacks
