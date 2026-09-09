# SAARTHI Design System

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Register: **Product** — the interface is an instrument, not a marketing surface. Operators (jawans, counsellors, welfare officers, commanders) open these screens daily; the design earns trust through consistency, speed, and dignity.
> Related: [design-client-apps.md](design-client-apps.md) · [ADR-0004](../decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../decisions/0005-offline-first-low-end-android.md) · [F02](../../features/F02-jawan-app.md) · [F08](../../features/F08-privacy-safety-architecture.md)

## 1. Design intent — what the pixels must prove

**Trust is the product.** Every visual decision answers one question: *does this feel like help, or does it feel like surveillance?*

- **Welfare, not discipline (ADR-0003 as a visual rule):** no red violation stamps, no "risk badge" next to a face, no punitive iconography. The response ladder is presented as care states, not alarm levels.
- **Dignity of context:** users are uniformed personnel with mixed literacy, in low-light bunkers and bad-network zones. Icons are big, text is paired with icons, and nothing important lives only in hover.
- **The uniform, not the clinic:** refuse the health-app reflex (white + teal, rounded pastel cards). The palette starts from the CRPF uniform — olive and khaki — because that is the user's identity, not ours. Category reflexes are design failure.

## 2. Color system (OKLCH)

Commitment level: **Whisper** — near-neutral surfaces, one role color doing the work, accent kept rare enough to mean something.

| Token (JSON path) | CSS custom property | OKLCH | Hex fallback | Role |
|---|---|---|---|---|
| `color.surface.base` | `--sa-color-surface-base` | `oklch(0.97 0.004 100)` | `#f7f6f2` | Warm paper background (khaki-tinted, never pure white) |
| `color.surface.raised` | `--sa-color-surface-raised` | `oklch(1 0 0)` | `#ffffff` | Cards, sheets |
| `color.ink.primary` | `--sa-color-ink-primary` | `oklch(0.25 0.02 140)` | `#2f332c` | Body text — olive-tinted near-black |
| `color.ink.secondary` | `--sa-color-ink-secondary` | `oklch(0.45 0.02 140)` | `#61635a` | Secondary text |
| `color.brand.olive` | `--sa-color-brand-olive` | `oklch(0.45 0.07 130)` | `#5a6b33` | Primary actions, active tab, brand moments (the uniform) |
| `color.brand.oliveSoft` | `--sa-color-brand-olive-soft` | `oklch(0.93 0.02 130)` | `#ecefe0` | Selected states, chips, hairline borders |
| `color.accent.saffron` | `--sa-color-accent-saffron` | `oklch(0.72 0.14 70)` | `#d98a1e` | **Rare** — one primary CTA per screen max (check-in submit, "start check-in") |
| `color.accent.saffronInk` | `--sa-color-accent-saffron-ink` | `oklch(0.25 0.02 140)` | `#2f332c` | **New 2026-09-09** — the text weight *on* the saffron fill (see the contrast fix below) |
| `color.focus` | `--sa-color-focus` | `oklch(0.65 0.13 70)` | `#bd781a` | **New 2026-09-09** — the focus ring, and any other meaningful non-text mark (trend-line markers, access dots) |

**Token names as generated.** `web/packages/tokens/src/tokens.json` is the single source; `web/packages/tokens/scripts/generate.mjs` flattens it to `web/packages/tokens/dist/tokens.css` as `--sa-<path-in-kebab-case>` — so `color.brand.oliveSoft` becomes `--sa-color-brand-olive-soft`, and `space.1 / type.md / line-height-hi / font-sans` become `--sa-space-1`, `--sa-type-md`, `--sa-line-height-hi`, `--sa-font-sans`. Nothing but that generator writes `dist/tokens.css` or `src/index.ts`; both carry a "do not edit by hand" banner.

**Hex fallback, then OKLCH — deliberately two declarations per colour.** Every colour token is emitted twice:

```css
--sa-color-brand-olive: #5a6b33;                 /* first  */
--sa-color-brand-olive: oklch(0.45 0.07 130);    /* second */
```

A browser that understands `oklch()` takes the second and discards the first; a browser that does not (Chrome < 111, and the WebViews on the API-26-class Android devices ADR-0005 targets) fails to parse the second declaration and keeps the hex. This is the CSS cascade's own fallback mechanism, not a polyfill — it costs one line per token and it means the app never renders colourless on the oldest device in the deployment. The consequence worth stating: **the hex fallbacks are what an old device actually paints, so the contrast lint measures the hex values, not the OKLCH ones** (`web/scripts/lint-boundaries.mjs`, `relLuminance()`).

### Semantic ladder (welfare states — never "risk colors")

The response ladder (F05) maps to care language, and **never color alone** — every state carries an icon + text label (accessibility floor). Each state now carries **two** colours: the ladder colour (the fill) and a matching ink (the text and border weight). Why is in the contrast fix below.

| State | Fill — `--sa-color-state-*` | Ink — `--sa-color-state-ink-*` | Icon + i18n key | en \| hi | Says |
|---|---|---|---|---|---|
| green | `oklch(0.62 0.13 150)` `#4a8a55` | `oklch(0.54 0.11 150)` `#3e7447` | `leaf` · `care.chip.green` | All good \| Sab theek | self-help nudge tier |
| amber | `oklch(0.75 0.14 80)` `#e0a020` | `oklch(0.51 0.10 80)` `#8e6514` | `sun` · `care.chip.amber` | A little care \| Thoda dhyan do | buddy + informal check tier |
| red | `oklch(0.55 0.17 25)` `#c04535` | `oklch(0.53 0.16 25)` `#b64232` | `hand-heart` · `care.chip.red` | Talk it out \| Baat karo | counsellor outreach ≤ 24h |
| critical | `oklch(0.45 0.15 25)` `#8f2f25` | `oklch(0.45 0.15 25)` `#8f2f25` | `phone` · `care.chip.critical` | Right now \| Turant | immediate contact + duty change |

`state/critical` is dark enough already, so its ink is deliberately the *same* value — a token exists for every state so `.sa-chip--<state>` can be written once, not so four different colours had to be invented.

Rules: 60-30-10 holds (olive 60 / warm neutrals 30 / saffron 10). Chroma clamps at lightness extremes. The ladder colors are colorblind-simulated (deuteranopia/protanopia) — leaf/sun/hand-heart icons carry the distinction, lightness separates them in every filter. Implementation: `CareStateChip` (`web/packages/ui/src/CareStateChip.tsx`) renders icon + `t(key)` and never colour alone.

### The contrast fix (2026-09-09) — a ladder colour is a *fill* colour

The UX-001 icon/voice review measured the shipped palette against this document's own floors (§9: 4.5:1 for text, §6: 3:1 for a focus ring) and found **three failing patterns across seven measured pairs**. All are now fixed in `web/packages/tokens/src/tokens.json`. Ratios below are computed on the **hex fallbacks** — the values an older Android browser paints — by the same function CI runs.

| Measured | Before | After | Fix |
|---|---|---|---|
| green care-chip label on its own 15% tint (`#e4ede6`) | 3.47:1 ✗ | **4.63:1** ✓ | `--sa-color-state-ink-green` |
| amber care-chip label on its own 15% tint (`#faf1de`) | **2.03:1** ✗ | **4.65:1** ✓ | `--sa-color-state-ink-amber` |
| red care-chip label on its own 12% tint (`#f7e9e7`) | 4.29:1 ✗ | **4.66:1** ✓ | `--sa-color-state-ink-red` |
| critical care-chip label on its own 12% tint (`#f2e6e5`) | 6.62:1 ✓ | 6.62:1 ✓ | already passing; token added for symmetry |
| white text on the saffron CTA | **2.76:1** ✗ | **4.66:1** ✓ | `--sa-color-accent-saffron-ink` (ink, not white, on the saffron fill) |
| focus ring on a card / on warm paper / on the olive tint | 2.76 / 2.55 / **2.37**:1 ✗ | **3.58 / 3.31 / 3.07**:1 ✓ | `--sa-color-focus` — same hue family, one step darker |

**The rule this encodes:** *a ladder colour is a fill colour and needs a separate text weight.* A label rendered in the ladder colour inside a 12–15% tint **of itself** can never reach 4.5:1 — the two are the same hue at almost the same lightness, so the ratio is bounded by how much white the tint lets through. Amber is the proof: at 2.03:1 it was the worst contrast in the product precisely because it is the *lightest* ladder colour, i.e. the one a designer feels safest about. The fix is structural, not a nudge: **the ladder colours themselves are unchanged**, so the chip fills, the heatmap cells and every meaning attached to green/amber/red/critical are exactly what they were. What moved onto the ink token is the text — and the chip *border*, which is a meaningful non-text mark and so owes 3:1 rather than 4.5:1; it now measures 5.22:1 (amber) to 8.07:1 (critical) against the card.

Same shape for the other two: the saffron CTA keeps its saffron fill (so "one rare saffron CTA per screen" survives) and swaps white ink for `#2f332c`; the focus ring stops borrowing the accent — a ring is a non-text mark that must clear 3:1 on *every* ground it can land on, and `--sa-color-accent-saffron` cleared it on none of the three.

Six new custom properties in three groups: `--sa-color-state-ink-{green,amber,red,critical}`, `--sa-color-accent-saffron-ink`, `--sa-color-focus`. Eighteen pairs in all — these and the ones that already passed — are re-measured on every CI run (§11, rule 7).

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
- **Voice input:** voice is an equal input path, not an accessibility bolt-on (mixed literacy is a primary constraint). As shipped (`web/apps/jawan/app/components/VoiceCapture.tsx`) the check-in offers "Speak instead of typing" (`voice.start` \| Speak instead of typing \| Likhne ki jagah boliye); a live canvas replaces the keyboard, and on stop the user keeps (`voice.keep`) or discards (`voice.discard`) — with a re-record path from either. **Correction to an earlier version of this line: it does not transcribe.** There is no speech recognition in the file at all, and that is the point — only a numeric prosody vector leaves the device, which is exactly what the screen says while recording: `voice.privacy.line` \| "Your voice never leaves this phone." \| "Aapki awaaz phone se bahar nahi jaati." and `voice.explain` \| "The phone measures pace and pauses on this device and sends only those numbers." \| "Phone isi device par raftaar aur ruknay ko naapta hai, sirf wahi numbers bhejta hai." A mic affordance on *every* text input is likewise still aspirational — today it is on the check-in note.

## 7. Motion

- Low-end Android default: **reduced motion**. Transitions are 100–150ms fades/slides, `transform`/`opacity` only, no springs, no stagger cascades, no parallax. The demo can enable standard motion on a fast device.
- One signature motion: the check-in completion — the day's dot fills on the person's own 90-day trend line. That single animation is the product's heart (the loop closing), so it gets a 250ms ease-out; everything else stays quiet.
- `prefers-reduced-motion` respected in web consoles.

**Status: implemented as specified.** The signature motion is `@keyframes sa-trend-dot` in `web/apps/jawan/app/globals.css` (lines ~668–689), applied only to `.trendline__dot--today` — the newest point on the personal trend line, which `TrendLine` marks as the last date in the series:

```css
.trendline__dot--today { transform-box: fill-box; transform-origin: center;
                         animation: sa-trend-dot 250ms ease-out; }
@keyframes sa-trend-dot { from { transform: scale(0.2); opacity: 0.2; }
                          to   { transform: scale(1);   opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .trendline__dot--today { animation: none; } }
```

250ms ease-out, `transform` + `opacity` only, and reduced-motion-guarded — so on a device that asks for stillness the dot is simply *there*, with nothing lost but the flourish.

Everything else in the system stays under the 150 ms ceiling and is written the other way round — `@media (prefers-reduced-motion: no-preference)`, so **motion is opt-in and stillness is the default**, which is the correct polarity for a low-end fleet. There are exactly four such blocks in `web/packages/ui/src/ui.css`: button opacity (120 ms), the segmented-control background (120 ms), the dialog entrance (140 ms, `sa-dialog-in`) and the meter fill (150 ms). `web/apps/commander/app/globals.css` adds a `prefers-reduced-motion: reduce` block for its heatmap-cell hover. `web/apps/counsellor/app/globals.css` contains **no** animation, transition or keyframe at all — nothing to guard, which is the cheapest way to respect the setting.

## 8. Copy rules (welfare register)

- One verb per button, sentence case, no exclamation points, no em dashes. "Baat karo" not "HELP NEEDED!"
- Errors are recovery paths, never blame: "Sync nahi hua. Data safe hai, dobara try karenge." / "Sync failed. Your data is saved, we'll retry."
- Screeners carry the disclaimer every time: "Ye jaanch salahn hai, nidan nahi" / "This is reflection support, not diagnosis."
- All strings via i18n keys (`en`, `hi`); regional languages are a data file, not a redesign (F02).
- Never brand as therapy: "Fitness for duty" + "Parivaar welfare" framing (ADR-0004).

## 9. Accessibility floor (HIGH on sight, no averaging down)

Native-first components (real buttons/links, no div-onClick) · visible labels · keyboard-walkable console flows · screen-reader names for every icon-only control (icon-only controls exist only where the icon is unambiguous + has an aria-label) · 200% zoom and 320px reflow survival · minimum contrast 4.5:1 for text · hit areas ≥ 48dp.

### 9a. Structurally enforced — these cannot regress without something failing

| Floor item | How it is held | Where |
|---|---|---|
| Real buttons and links, never `div onClick` | every interactive primitive in the kit is a native element: `<button>` (`Button`, `.sa-tab`, `.sa-dialog__close`, `.sa-table__rowbtn`), `<a>` (`ConsoleShell` nav, `SkipLink`), `<input type="radio">` (`Segmented`), `<input type="range">` (`Slider`), `<input type="checkbox">` (`Checkbox`), `<select>` (`Select`) | `web/packages/ui/src/*.tsx` |
| Focus rings, `:focus-visible`, never `outline: none` | every focusable control in the kit carries one (16 `:focus-visible` occurrences in `ui.css`), all `2px solid var(--sa-color-focus)` at a 2px offset; `outline: none` appears in **no** stylesheet in `web/` | `web/packages/ui/src/ui.css` |
| Focus ring contrast ≥ 3:1 | `--sa-color-focus` measured on card / paper / olive tint every CI run | §11 rule 7 |
| Text contrast ≥ 4.5:1 | 11 text pairs measured every CI run, on the hex fallbacks | §11 rule 7 |
| Labels always visible | `Field` renders a real `<label htmlFor>`; `Slider`, `Checkbox` and `Segmented` carry their own; placeholders are format examples only (`Select.placeholderKey` is `disabled`) | `Field.tsx`, `Slider.tsx`, `Checkbox.tsx` |
| Icon-only controls have accessible names | there are exactly three in the kit — the dialog close, the toast dismiss, the undo dismiss — and all three carry `aria-label={t("a11y.close")}` (`a11y.close` \| Close \| Band karein). Every icon in `Icons.tsx` is `aria-hidden` by default in its shared `base()` props, so a decorative glyph cannot leak into the accessible name by accident. The tab bar is *not* icon-only: each tab renders `.sa-tab__label` text under its icon | `BaseDialog.tsx:63`, `Toast.tsx:32`, `UndoBar.tsx:35`, `Icons.tsx:12` |
| Skip link before the nav | `SkipLink` (`a11y.skipToContent` \| Skip to content \| Content par jaayein), rendered by `ConsoleShell` on both consoles and by the jawan tab layout | `SkipLink.tsx`, `ConsoleShell.tsx:49`, `apps/jawan/app/(tabs)/layout.tsx:50` |
| Dialog focus trap, Escape, focus restore | native `<dialog>` + `showModal()` — the platform's behaviour, not a re-implementation | `BaseDialog.tsx` |
| A value is never position-only | `Slider` prints its number as text beside the thumb; `Dial` and `Meter` carry `role="meter"` + `aria-valuenow`; `Sparkline`, `TrendLine` and `RiskTrendChart` all ship an `sr-only` text summary next to a decorative SVG | `Slider.tsx`, `Dial.tsx`, `Meter.tsx`, `Sparkline.tsx` |
| Hit areas ≥ 48dp | `min-height: 48px` on buttons, inputs, selects, segmented options, slider row, console nav links; 44px on the secondary dismiss/undo affordances and the checkbox row | `ui.css` |
| Wide content scrolls in its own box, not the page | `DataTable` wraps every table in `.sa-table-scroll` (`overflow-x: auto`, focusable, `role="region"`) | `DataTable.tsx` |
| Devanagari never clips | `--sa-line-height-hi: 1.6` applied at `[data-locale="hi"]`; `TextArea` grows to its rows, no fixed-height text container | `globals.css`, `ui.css`, `TextArea.tsx` |
| Loading / empty / error are announced, not implied | `Skeleton` (`role="status"`, `aria-busy`), `Toast` and `UndoBar` (`role="status"`, polite), `ErrorState` (`role="status"`) | `ui.css` components |

### 9b. Still needs a human — UX-001's session plan

A machine can measure a ratio; it cannot tell you a screen is usable. These are open and belong to UX-001's manual pass, **not** to CI:

- **200% browser zoom** on all three surfaces — the console sidebar collapses to a top bar below 900px, which is the right behaviour but is unverified at zoom rather than at width.
- **320px reflow** — asserted by the e2e smoke script (`web/e2e/smoke.mjs` resizes to 320px) but not yet walked screen by screen for clipped controls and two-line buttons.
- **Screen-reader walkthrough** (TalkBack on Android, NVDA/VoiceOver on the consoles) of the four flows that matter: check-in, instrument + safety protocol, dual-key unmask, and the who-viewed receipt. Reading order and announcement quality are the point; no lint can stand in for it.
- **Colour-blind simulation of the shipped build.** The ladder was designed under deuteranopia/protanopia simulation, but the new `state-ink` colours have not been re-simulated as rendered.
- **Low-light / gloved / one-handed use** on a real device, which is the actual deployment context and the reason the touch targets are 48dp in the first place.

Nothing in 9b is claimed as done. As of 2026-09-09 they are **not implemented as verified checks** — they are scheduled work.

**Two known gaps, recorded rather than left to be discovered by a judge.** Neither is this document's file to fix; both are small.

1. The i18n lint (§11, rule 5) reads JSX *text*, not JSX *attributes*, so an accessible name passed as an attribute can be a literal and pass. There is exactly one such string in the tree today — `aria-label="Primary"` on the tab bar (`web/packages/ui/src/BottomTabs.tsx:21`) — which means a Hindi-first TalkBack user hears an English word there.
2. **`<html lang>` never changes with the locale.** All three layouts hardcode `lang="en"`, and `I18nProvider` sets `document.documentElement.dataset.locale` (which drives the Devanagari line-height) but not `.lang`. So a screen reader announces romanised Hindi in an English voice. The line-height half of "Devanagari needs room" is handled; the language-announcement half is not, and it is one line in `packages/i18n/src/index.tsx`.

## 10. Component inventory (as shipped, 2026-09-09)

Read this section as three layers: what is **shared** (`@saarthi/ui`, importable by all three apps), what is **app-local** (deliberately not shared, and in one case forbidden from being shared), and what the v1 list above turned into.

### 10a. `@saarthi/ui` — the shared kit

Every one of these is exported from `web/packages/ui/src/index.ts` and styled entirely from tokens in `web/packages/ui/src/ui.css` (no literal colour appears in that file). "Surfaces" is measured, not intended — it is where the symbol is actually imported today.

**Product components**

| Component | Surfaces | State |
|---|---|---|
| `CheckInCard` | jawan roster home · commander `/checkin` | **shipped.** v1's "CheckInCard (10s)". Three states, not two: first-run (`home.checkin.empty`), daily ask (`home.checkin.title`), done-today (`home.checkin.doneToday`) — the third steps the button back from saffron to quiet so the screen stops nagging someone who already answered. Same component and same i18n keys on both surfaces, which is the point (§3 of design-client-apps). |
| `CareStateChip` | counsellor case header + queue rows · commander heatmap + Tele-MANAS picker | **shipped.** v1's "care-state chips". Icon + `t(key)`, never colour alone. **Not used in the jawan app at all** — a person is not shown a tier for themselves; the jawan surface shows their own trend, not a rating of them. |
| `SyncPill` | jawan tab shell | **shipped.** Reads `@saarthi/sync`'s snapshot directly. Queued data is never error-styled; only a genuine failure shows `sync.error.recovery`. |
| `BottomTabs` | jawan tab layout | **shipped.** Roster / Welfare / Me. |
| `ConsoleShell` | counsellor · commander | **new since v1.** Sidebar + `<main id="content">` + `SkipLink`; collapses to a horizontally-scrolling top bar below 900px rather than a hamburger. |
| `AppBar` | none | **shipped but unused.** The jawan app renders its own `.app-topbar` in `globals.css`. Either adopt it or delete it — an exported component nobody imports is how a kit starts lying. |

**Primitives** — the 9-state rule (§6) lives here rather than in each screen

| Component | Surfaces | State |
|---|---|---|
| `Button` | all three | shipped. `primary` / `secondary` / `quiet`; 48px min-height, `:focus-visible` ring. |
| `Sheet` · `Modal` (both over `BaseDialog`) | Sheet: jawan, commander · Modal: counsellor | shipped. Native `<dialog>` + `showModal()`; Sheet is bottom-anchored (thumb zone), Modal is centred. |
| `ConfirmDialog` | jawan (consent withdrawal, clear queue) · counsellor (break-glass) | shipped. **The only confirm pattern in the product**; everything reversible uses `UndoBar` instead. |
| `UndoBar` | jawan (check-in undo, 8 s) | shipped. "Undo beats confirm" made concrete. |
| `Toast` | all three | shipped. `role="status"`, polite. |
| `Field` · `TextInput` · `TextArea` · `Select` · `Segmented` · `Slider` · `Checkbox` | Field/TextInput/TextArea: jawan + counsellor · Select: counsellor · Segmented: jawan + counsellor · Slider: all three · Checkbox: jawan | shipped. All native elements; label always visible. |
| `Skeleton` · `EmptyState` · `ErrorState` | all three | shipped. Skeleton is shimmer-free by design (§7). Empty states teach; errors are recovery paths. |
| `LanguageToggle` | all three | shipped. A real 2-option radio group over `Segmented`. |
| `SkipLink` | jawan tab layout · both consoles via `ConsoleShell` | **new since v1.** |

**Data display**

| Component | Surfaces | State |
|---|---|---|
| `StatTile` | jawan (leave) · commander (morale, indicators) | new since v1. Shows the suppression explainer where the number would be. |
| `SuppressedCell` | commander (heatmap, indicators, simulator, forecast) | **new since v1, and load-bearing.** One component so every surface suppresses identically: an em-dash plus `common.suppressed` ("Too few people to show a number" \| "Number dikhane ke liye log kam hain"). No error colour, no warning icon — suppression is the design, not a failure. |
| `Timeline` | counsellor (case timeline) | shipped — this is what v1 called `WhoViewedTimeline`, generalised. The jawan receipts screen renders its own list against the same visual language. |
| `FactorChip` | counsellor (evidence) | shipped — v1's "factor chips". "47 duty days", "sleep −30%", with an optional weight rule. Never a single opaque number. |
| `Dial` | commander (morale index) | shipped — v1's "MoraleIndex dials". `role="meter"`, number always present as text as well as as an arc. |
| `Meter` | counsellor · commander (indicators) | new since v1. Olive fill only — a proportion is not a severity, so it never changes colour with its value. |
| `Sparkline` | commander (forecast, own check-in) | **new since v1 — see 10c.** Generic small line, `aria-hidden` SVG + `sr-only` summary. |
| `Badge` | all three | new since v1. Deliberately has no alarm variant. |
| `DataTable` | none | **shipped but unused.** Built for a console table that has not landed; same call as `AppBar`. |
| `useApi` hook | all three | new since v1. One loading/error/stale-cache path for every screen, so nobody re-invents it. |
| `Icons` (32 glyphs) | all three | shipped. `aria-hidden` by default, `currentColor` stroke. |

### 10b. App-local components

| Component | Lives in | Surfaces | State |
|---|---|---|---|
| `TrendLine` | `apps/jawan/app/components/TrendLine.tsx` | jawan `/welfare/trend` **only** | shipped — v1's "TrendLine (personal, 90-day)". See 10c. |
| `CheckInSheet` | `apps/jawan/app/(tabs)/roster/CheckInSheet.tsx` | jawan | shipped. Emoji ladder → slider → save, over `Sheet`. |
| `VoiceCapture` | `apps/jawan/app/components/VoiceCapture.tsx` | jawan check-in | **new since v1.** Only numbers leave the device: no `MediaRecorder`, no Blob, no object URL anywhere in the file — a ~30 Hz numeric envelope reduced to one feature vector on stop. |
| `SubScreen` | `apps/jawan/app/components/SubScreen.tsx` | jawan sub-routes | new since v1. Back link + rule-of-3 header. |
| `QueueRail` · `SlaClock` · `UnmaskPanel` · `CaseContext` · `LoadError` | `apps/counsellor/app/components/` | counsellor | shipped — v1's "CaseQueue" and the dual-key unmask CTA, split into a rail, a clock, and the identity panel (request → approve → read, plus break-glass). |
| `RiskTrendChart` | `apps/counsellor/app/components/RiskTrendChart.tsx` | counsellor case detail | **new since v1.** See 10c. |
| `ScreenHead` · `AsOf` · `DataNotice` · `RuleDeltaList` · `AssumptionPanel` · `careStateFor` | `apps/commander/app/parts.tsx` | commander | new since v1. Everything in the file is unit-shaped or has no subject at all. |
| `UnitsProvider` / `useUnits` | `apps/commander/app/units.tsx` | commander | new since v1. **The only identifier the commander client holds is a unit id** — the F07 firewall written in the shape of the client state. |

### 10c. The three-way trend split — why, and how it is held

v1 listed one component called `TrendLine`. It became three, and the split is the single most important line in this inventory:

| | `Sparkline` | `TrendLine` | `RiskTrendChart` |
|---|---|---|---|
| Lives in | `@saarthi/ui` (shared) | `apps/jawan` **only** | `apps/counsellor` |
| Subject | a unit, or your own check-ins | **you** | a case |
| Axis | caller-supplied min/max | 0–10 mood, 90 days, ends today | fixed 0–100 risk score |
| Carries | one line, nothing else | the person's own mean as the only baseline, plus follow-up ticks | care-state dot colours + intervention markers on the same axis |
| Comparison offered | none | **only with yourself** — no peer series, no unit mean, no ranking, no band | none between people |

**Why the split exists.** A personal trend is a private artefact. The moment the same component can render in a console, someone will pass it a colleague's series, and the difference between "your own 90 days" and "a person's chart on an officer's screen" collapses into a prop. So it is not a shared component with a policy attached — it is a file that physically does not exist in the console builds.

**It is a lint rule, not a convention.** `web/scripts/lint-boundaries.mjs` fails the build on the identifier `TrendLine` appearing anywhere under `apps/counsellor` or `apps/commander` (rule `trendline-jawan-only`). A convention survives until the first busy afternoon; this one survives a copy-paste. The two consoles get `Sparkline` and `RiskTrendChart` instead, which is why those exist at all.

### 10d. What happened to the rest of the v1 list

| v1 entry | Outcome |
|---|---|
| CheckInCard (10s) | **shipped** as `@saarthi/ui/CheckInCard` + `CheckInSheet`. |
| InstrumentFlow (PHQ-9/GAD-7/PSS-10/ISI) | **shipped, not as a component.** It is a route (`/welfare/instrument`, `/welfare/instrument/[id]`) composed from kit primitives, over the `@saarthi/instruments` bank. ISI ships flow + scoring but **not its item text** — it is copyrighted and gated behind `licence: "licence_pending"`, and the UI says so. |
| ConsentSheet | **shipped, renamed and re-shaped.** It is the `/me/consent` page, not a sheet: granting and withdrawing are one tap from the same place, and withdrawal goes through `ConfirmDialog` (one of exactly two irreversible actions). |
| WhoViewedTimeline | **shipped, split.** The generic rail became `@saarthi/ui/Timeline`; the receipt screen is `/me/receipts` (audit events + notifications). §5's design is intact. |
| SyncPill | **shipped** unchanged. |
| TrendLine (personal, 90-day) | **shipped, and now the subject of a lint rule** — see 10c. |
| CaseQueue + EvidenceCard | **shipped, renamed.** `QueueRail` + the case-detail route; "EvidenceCard" is a composition of `FactorChip` + `Meter` + `RiskTrendChart` + `Timeline`, not one component. |
| SessionNote + OutcomeTracker | **shipped as routes** (`/case/[id]/notes`, `/case/[id]/outcomes`) built from `Field` / `TextArea` / `Segmented` / `Slider`. |
| AggregateHeatmap + MoraleIndex | **shipped, renamed.** The heatmap is the `/` grid over `UnitsProvider` (cells are `<a>` elements, suppressed cells render `SuppressedCell` and are not links); MoraleIndex is `Dial` + `StatTile`. |
| WhatIfSimulator | **shipped** as `/simulator`. The form is built from `getLevers()` — no lever is hardcoded in the client, so when the engine's validated ranges move the screen moves with them. |
| UnitPulse (anonymous rating) | **shipped** as `/welfare/pulse`, aggregate-only, k-filtered per facet server-side. |
| *(not in v1)* Attrition forecast | **new.** `/forecast`, using `Sparkline` + `SuppressedCell`. |
| *(not in v1)* Commander's own check-in | **new.** `/checkin`, reusing `CheckInCard`. |

**No individual-row component exists in the commander build**, and that is checked rather than asserted — see §11, rule 2.

## 11. How the rules are enforced

This is the part of a design system that usually rots. A palette drifts because nobody re-measures it; a boundary rule ("the personal trend never renders in a console") survives exactly until the first afternoon somebody is in a hurry. So the rules in this document are executable.

`web/scripts/lint-boundaries.mjs` runs as the **first web step in CI**, before typecheck, tests and build (`.github/workflows/ci.yml`, job `web`), and locally via `bun run lint:boundaries`, `bun run check` or `make lint`. It walks every `.ts` / `.tsx` / `.mjs` / `.css` under `web/apps` and `web/packages` and exits non-zero with a list of violations. It needs no framework and no config; it reads files.

| # | Rule (id) | What it does | What it prevents |
|---|---|---|---|
| 1 | `role-isolation` | an app may reference only its own role's API subpath — `@saarthi/api/counsellor` inside `apps/commander` fails | the leak ADR-0003 exists to stop. `@saarthi/api` deliberately does **not** re-export the role clients from its root, so the only way to reach one is the subpath the lint watches |
| 2 | `commander-no-individual` | the strings `pseudonym_id`, `PersonRow`, `IndividualRow`, `legal_name`, `personnel_id` may not appear anywhere under `apps/commander` | the F07 firewall as a *client* guarantee. The commander build has no shape that can address a person — so there is no component to accidentally render one, and no route to navigate "down" to |
| 3 | `trendline-jawan-only` | the identifier `TrendLine` may not appear outside `apps/jawan` | a personal trend rendering on an officer's screen (§10c) |
| 4 | `tokens-only` | `oklch(` may not appear in any file outside `packages/tokens` | a one-off colour that the contrast check has never seen and the dark-hallway test has never survived |
| 5 | `i18n-keys-only` | JSX text that is a word rather than punctuation/digits fails | an English literal shipping to a Hindi-first user. Known limit: it reads JSX *text*, not attributes (§9b) |
| 6 | `unknown-i18n-key` + en/hi parity | every `t("key")` must resolve in `en.json` or in a declared `packages/i18n/src/pending/<app>.json` entry; and every key must exist in **both** `en.json` and `hi.json` | a missing translation falling back to English silently in the field, and a typo'd key rendering as itself. The pending directory exists because three apps editing two shared JSON files is the one place parallel work reliably collides; `bun scripts/merge-pending-i18n.mjs` folds them in |
| 7 | contrast floors | 11 text pairs measured against 4.5:1 and 7 non-text pairs against 3:1 — 18 in all, computed on the **hex fallbacks** (what an old Android browser paints) | exactly what happened before 2026-09-09: this document stated a 4.5:1 floor for two weeks while the amber care chip sat at 2.03:1. A floor nobody measures is a wish |

Current state, from a real run: `✓ boundaries clean — 18 contrast pairs, 495 i18n keys (+0 pending), 226 referenced statically`.

Two honest notes about the script. Its header comment numbers seven rules but the file contains eight checks — the key-resolution block is labelled `7` a second time, a numbering slip, not a missing check. And rules 1–5 are substring and regex matches over source text: they are deliberately blunt, because a blunt check that runs on every push beats a precise one that needs a parser nobody maintains. The failure mode is a false positive, which is loud and cheap; the failure mode of having no check is a privacy incident, which is neither.

**What is *not* enforced here:** the k ≥ 5 suppression itself, the role firewall, and every access-control rule are enforced **server-side** and covered by the backend's own suites (`backend/tests/test_firewall.py`, `test_privacy.py`, `test_rbac_enforcement.py`, `test_security_hardening.py`), which run as CI's first job of all. The client rules above are a second wall, not the wall. A client-side check is a design guarantee; it is never a security guarantee.

## 12. UX-002 — the mockups are generated, not drawn

`docs/architecture/design/mockups/` holds eleven artboards — the 10-second check-in flow (home → sheet → saved-with-undo) and the privacy panel (consent, who-viewed receipts), each in English and romanised Hindi, plus a design-notes page (palette, type ramp, and the eight rules the screens exist to test). The check-in sheet artboard carries a **State** lever (idle / picked / error) so the 9-state rule (§6) can be inspected without three more frames. See [mockups/README.md](mockups/README.md) for the published canvas link and the source/output split.

The thing that makes them worth keeping: **they are generated from the running design system, not drawn beside it.** `scripts/build-mockups.py` reads every colour, size, radius, control height and line-height out of `web/packages/tokens/dist/tokens.css`, `web/packages/ui/src/ui.css` and `web/apps/jawan/app/globals.css` — no rounding, no 8px-grid snapping — and looks up every string by key in `web/packages/i18n/src/{en,hi}.json`.

So a renamed i18n key **breaks the generator** instead of silently ageing the mockup, and a token whose value changes moves the artboards on the next `python3 scripts/build-mockups.py`. Where a mockup and the app disagree, one of them is a bug; the mockup cannot quietly become "the old design". That is the whole argument for generating them: a design file's normal failure mode is being wrong without anyone noticing, and this one cannot fail that way.

The `.dc.html` artboards and `canvas.json` are source and committed; the ~2 MB published canvas HTML is build output and git-ignored.

Figma source of truth lives on the team board; this file is the binding spec — where Figma and this file disagree, this file wins and Figma gets updated. Where **this file and the code** disagree, the code wins and this file gets updated in the same PR (AGENTS.md rule 1).
