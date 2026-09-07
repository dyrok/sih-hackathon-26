# SAARTHI Design System

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Register: **Product** — the interface is an instrument, not a marketing surface. Operators (jawans, counsellors, welfare officers, commanders) open these screens daily; the design earns trust through consistency, speed, and dignity.
> Related: [design-client-apps.md](design-client-apps.md) · [ADR-0004](../decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../decisions/0005-offline-first-low-end-android.md) · [F02](../../features/F02-jawan-app.md) · [F08](../../features/F08-privacy-safety-architecture.md)

## 1. Design intent — what the pixels must prove

**Trust is the product.** Every visual decision answers one question: *does this feel like help, or does it feel like surveillance?*

- **Welfare, not discipline (ADR-0003 as a visual rule):** no red violation stamps, no "risk badge" next to a face, no punitive iconography. The response ladder is presented as care states, not alarm levels.
- **Dignity of context:** users are uniformed personnel with mixed literacy, in low-light bunkers and bad-network zones. Icons are big, text is paired with icons, and nothing important lives only in hover.
- **The uniform, not the clinic:** refuse the health-app reflex (white + teal, rounded pastel cards). The palette starts from the CRPF uniform — olive and khaki — because that is the user's identity, not ours. Category reflexes are design failure.

## 2. Color system (OKLCH)

Commitment level: **Whisper** — near-neutral surfaces, one role color doing the work, accent kept rare enough to mean something.

| Token | OKLCH | Role |
|---|---|---|
| `surface/base` | `oklch(0.97 0.004 100)` | Warm paper background (khaki-tinted, never pure white) |
| `surface/raised` | `oklch(1 0 0)` | Cards, sheets |
| `ink/primary` | `oklch(0.25 0.02 140)` | Body text — olive-tinted near-black |
| `ink/secondary` | `oklch(0.45 0.02 140)` | Secondary text |
| `brand/olive` | `oklch(0.45 0.07 130)` | Primary actions, active tab, brand moments (the uniform) |
| `brand/olive-soft` | `oklch(0.93 0.02 130)` | Selected states, chips |
| `accent/saffron` | `oklch(0.72 0.14 70)` | **Rare** — one primary CTA per screen max (check-in submit, "start check-in") |

### Semantic ladder (welfare states — never "risk colors")

The response ladder (F05) maps to care language, and **never color alone** — every state carries an icon + text label (accessibility floor):

| State | OKLCH | Icon + label | Says |
|---|---|---|---|
| `state/green` | `oklch(0.62 0.13 150)` | `leaf` "Sab theek" / "All good" | self-help nudge tier |
| `state/amber` | `oklch(0.75 0.14 80)` | `sun` "Thoda dhyan do" / "Check in more" | buddy + informal check tier |
| `state/red` | `oklch(0.55 0.17 25)` | `hand-heart` "Baat karo" / "Let's talk" | counsellor outreach ≤ 24h |
| `state/critical` | `oklch(0.45 0.15 25)` | `phone` "Turant" / "Now" | immediate contact + duty change |

Rules: 60-30-10 holds (olive 60 / warm neutrals 30 / saffron 10). Chroma clamps at lightness extremes. The ladder colors are colorblind-simulated (deuteranopia/protanopia) — leaf/sun/hand-heart icons carry the distinction, lightness separates them in every filter.

## 3. Typography

- **Face:** Noto Sans (Latin) + Noto Sans Devanagari — bundled on Android, free, complete for `hi` + `en`. No custom font on the mobile app; system fonts are legitimate for product UI and cost zero bytes on a 2 GB device.
- **Devanagari needs room:** line-height +0.1 over the Latin equivalent in every `hi` string; no fixed-height text containers (they clip matras).
- **Scale (1.3 ratio, product minimum):** 12 / 16 / 21 / 27 / 35. Body 16sp on mobile (reading-distance equation for a handheld device); titles 21–27sp; one 35sp moment per screen max.
- **Hierarchy rule of 3:** every screen has hook (screen title) → bridge (one-line guidance) → detail (content). Never a 4th level.
- **Reading measure:** consoles 60–76ch; mobile app is full-width with 16dp gutters.

## 4. Layout & spacing (1-4-9 rhythm)

- Spacing only in multiples of **4dp** (1 unit), **16dp** (4 units), **36dp** (9 units). No in-betweens.
- **Thumb zone:** the bottom 25% of the phone holds primary actions (check-in submit, sync status). Destructive actions (withdraw consent) sit in the hard-to-reach top zone *and* use the confirm pattern (see §6).
- **3-plane depth:** background (warm paper, never interactive) → content (cards, lists) → attention (bottom sheets for check-in, unmask approvals). Sheets animate from the trigger's edge.
- **The roster-app-first home (ADR-0004):** the app opens on duty roster / leave / pay-slip. The check-in is a calm card on that home — "Aaj kaisa laga? (10 second)" — not a notification badge, not a guilt streak counter (anti-pattern, F05 adoption).
- **Commander dashboard:** moderate density, aggregate heatmap of India-style unit map + morale index dials + leading/lagging indicator columns. **No component in this surface can render an individual name** — enforced server-side (F08) and by design: there is no individual-row pattern defined for this app at all.
- **Counsellor console:** case queue ranked by urgency × intervenability (F05 triage), each case as an evidence card: top-3 factor chips ("47 duty days", "sleep −30%", "2 cancelled leaves"), never a single opaque number.

## 5. The trust moment — "who viewed my data"

This panel is the most memorable 15 seconds of the demo (winning-strategy). Design it like a **receipt, not a warning**:

- Timeline of accesses: who (role, not just name), when, why (the purpose string from the audit log), how long.
- Calm, factual, monospace-adjacent numerals for timestamps; olive role chips; zero alarm colors.
- Header line: "Aapka data. Aapka adhikar." / "Your data. Your right." — sentence case, no exclamation marks, ever.
- The unmask entry (dual-key approval, F08) renders here too: "Counsellor + Welfare Officer opened your case on 12 Sep — reason: Red-tier outreach". Turning surveillance into accountability is the design goal.

## 6. Interaction & states

- **9 states for every control:** idle, hover (web only), active, focused, loading, empty, error, disabled, overflow. A layout that only works in state 1 is a sketch.
- **Touch targets:** 48×48dp minimum (Android comfortable), hit area larger than visual.
- **Focus rings:** 2dp, offset, 3:1 contrast — `:focus-visible`, never bare `:focus`, never `outline: none`.
- **Undo beats confirm** for check-in edits, buddy status, tracker notes. Confirm only for irreversible actions: consent withdrawal and break-glass unmask.
- **Labels always visible;** placeholders only show format examples and disappear on focus.
- **Offline-first states (ADR-0005):** a persistent, quiet sync pill — "3 check-ins saved, will send" — with no red error styling for queued data. Empty states teach ("Pehli baar check-in — 10 second lagenge").
- **Voice input:** every text input has a mic affordance; the waveform replaces the keyboard visually, transcribes live, and lets the user keep or re-record. Voice is an equal input path, not an accessibility bolt-on (mixed literacy is a primary constraint).

## 7. Motion

- Low-end Android default: **reduced motion**. Transitions are 100–150ms fades/slides, `transform`/`opacity` only, no springs, no stagger cascades, no parallax. The demo can enable standard motion on a fast device.
- One signature motion: the check-in completion — the day's dot fills on the person's own 90-day trend line. That single animation is the product's heart (the loop closing), so it gets a 250ms ease-out; everything else stays quiet.
- `prefers-reduced-motion` respected in web consoles.

## 8. Copy rules (welfare register)

- One verb per button, sentence case, no exclamation points, no em dashes. "Baat karo" not "HELP NEEDED!"
- Errors are recovery paths, never blame: "Sync nahi hua. Data safe hai, dobara try karenge." / "Sync failed. Your data is saved, we'll retry."
- Screeners carry the disclaimer every time: "Ye jaanch salahn hai, nidan nahi" / "This is reflection support, not diagnosis."
- All strings via i18n keys (`en`, `hi`); regional languages are a data file, not a redesign (F02).
- Never brand as therapy: "Fitness for duty" + "Parivaar welfare" framing (ADR-0004).

## 9. Accessibility floor (HIGH on sight, no averaging down)

Native-first components (real buttons/links, no div-onClick) · visible labels · keyboard-walkable console flows · screen-reader names for every icon-only control (icon-only controls exist only where the icon is unambiguous + has an aria-label) · 200% zoom and 320px reflow survival · minimum contrast 4.5:1 for text (ladder colors checked in OKLCH) · hit areas ≥ 48dp.

## 10. Component inventory (v1 scope)

| Component | Surfaces | Notes |
|---|---|---|
| CheckInCard (10s) | mobile home | emoji row → 1 slider → done; saffron submit |
| InstrumentFlow (PHQ-9/GAD-7/PSS-10/ISI) | mobile | one question per screen, icon+text, progress dots |
| ConsentSheet | mobile | unbundled consents, withdrawal = same tap depth as giving |
| WhoViewedTimeline | mobile | §5 receipt design |
| SyncPill | mobile | offline-first states |
| TrendLine (personal, 90-day) | mobile | own baseline, no peer comparison ever |
| CaseQueue + EvidenceCard | counsellor console | factor chips, unmask CTA (dual-key) |
| SessionNote + OutcomeTracker | counsellor console | feeds ML v2 labels (kv's ML-004 plan) |
| AggregateHeatmap + MoraleIndex | commander | k ≥ 5 enforced; no individual pattern exists |
| WhatIfSimulator | commander | "Extend Coy B by 30 days → projected fatigue +18%" |
| UnitPulse (anonymous rating) | mobile | aggregate-only surfacing |

Figma source of truth lives on the team board; this file is the binding spec — where Figma and this file disagree, this file wins and Figma gets updated.
