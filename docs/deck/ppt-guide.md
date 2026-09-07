# SIH PPT Guide — how risa builds the presentation

> Owner: risa · Status: [x] current · Last updated: 2026-09-05
> This is a beginner's step-by-step guide. Follow it top to bottom. Companion doc: [deck-outline.md](deck-outline.md) (what goes on each slide, slide by slide).

## 0. The one rule that outranks everything

**Download the official SIH template from the SIH portal when it is issued and build inside it. Do not restyle fonts, colors, or layouts.** SIH submissions are judged partly on "details in the prescribed format" — a prettier non-template deck scores *worse*. If the portal template allows a fixed number of slides (recent editions: idea deck is compact, ~6 slides), respect that limit; our [deck-outline.md](deck-outline.md) 13-slide structure is the extended internal-round version — cut, never add.

## 1. Tools (all free)

| Need | Use | Notes |
|---|---|---|
| Deck editor | Google Slides or PowerPoint | PowerPoint preferred if the official template is a .pptx — open it directly, don't copy-paste into another tool |
| Diagrams (architecture, data flow) | draw.io (diagrams.net) or excalidraw | Export as PNG at 2x; keep sources in `deck/diagrams/` so kv/neel can edit later |
| Screenshots | The running prototype on a clean seeded account | Never a Figma mockup if a real screen exists — judges can tell |
| Icons | Free icon sets (iconoir, lucide) or none | No emoji as UI "screenshots" |
| Export | PDF, exactly as required by the portal | PDF export is mandatory for SIH submission |

## 2. Build order (do it in this sequence)

1. **Read first**: [winning-strategy.md](../product/winning-strategy.md) (what evaluators score) → [deck-outline.md](deck-outline.md) (slide-by-slide content) → this guide (how to make it look right).
2. **Skeleton first**: open the official template, drop the slide titles from deck-outline into every slide. One working session, no content yet.
3. **One statistic slide done properly**: the problem slide gets exactly one cited number (ThePrint: 654 CAPF suicides, ~50,000 resignations in 5 years — link in [impact-and-metrics.md](../product/impact-and-metrics.md)). Big font, source at the bottom.
4. **Diagrams before text**: architecture and flow diagrams from draw.io. Every diagram must pass the "grandma test" — kv checks this.
5. **Text last, and little**: max ~30 words per slide outside titles. Judges read slides in seconds; you speak the rest.
6. **Prototype screenshots** (ask neel for the running app, kv for the console): real seeded data visible — "3rd Bn, 22% elevated fatigue", never an empty dashboard.
7. **The memorable slide**: the anti-goals/"what we did NOT build" slide (F08 §anti-goals) and the closing number: **0 — individual scores that can reach command, guaranteed by architecture**.
8. **PDF export + review with kv** before any deadline. Then rehearse (see §5).

## 3. Visual rules (simple, non-negotiable)

- **One font family** (whatever the template uses), two weights max.
- **Contrast**: dark text on light background; nothing below 18pt on a projector.
- **Every image gets a caption or label** — an uncaptioned screenshot is decoration, not evidence.
- **Consistent icon style**, consistent color use. No rainbow bullets, no transitions/animations except plain appear.
- **Cite on-slide**: small source line under every number and image. No invented statistics (AGENTS.md rule 6) — if you can't cite it, delete it or rate it Low/Med/High.
- **No text walls**. If a slide has a paragraph, it's a document — split or cut it.
- More pictures + fewer words; keep every slide scannable in 5 seconds.

## 4. Common mistakes that lose points (check before export)

- [ ] Styled beyond the official template (fonts/colors changed)
- [ ] Wrong PS ID or team details on the title slide (PS 26186, CRPF/MHA, MedTech — copy exactly from [problem-statement.md](../product/problem-statement.md))
- [ ] Mockup screenshots instead of real prototype screens
- [ ] Uncited statistics
- [ ] Missing the video-demo link (embed/QR on the prototype slide)
- [ ] Missing team roles slide (≥1 female member is an SIH requirement — verify with kv)
- [ ] Exported as .pptx when the portal wants .pdf
- [ ] Slide count over the template's limit

## 5. Presentation practice (internal round + finale)

- Who presents: **risa drives the deck**, kv/neel handle live demo; everyone speaks at least once (judges score teamwork; one speaker + five silent teammates is a known elimination cause).
- Rehearse the 3-minute script from [demo-runbook.md](../quality/demo-runbook.md) five times, timed, out loud, with the deck advancing.
- Prepare the jury answers (winning-strategy.md §six challenges) — risa keeps the printed cheat sheet.
- After every rehearsal, note the slide that ran long and fix the slide, not the speaker.

## 6. Sources for this guide

- [SIH 2026 PPT Template: exact format, slides, and what evaluators score — Reskilll](https://reskilll.com/blogs/sih-2026-ppt-template-exact-format-slides-evaluators-score/)
- [SIH 2026 PPT template guidelines — TheNewViews](https://thenewviews.com/sih-2026-ppt-template/)
- [SIH2026 IDEA Presentation Format (official template copy) — Scribd](https://www.scribd.com/presentation/1077930858/SIH2026-IDEA-Presentation-Format)
- [How to build a hackathon pitch deck judges remember — InkNarrates](https://www.inknarrates.com/post/hackathon-pitch-deck)
- [How to create a winning hackathon pitch in 5 steps — TAIKAI](https://taikai.network/en/blog/how-to-create-a-hackathon-pitch)
- [SIH 2026 official guidelines (deadlines, submission rules)](https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf)
