# design-client-apps.md — Client Applications: Jawan App + Consoles

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Maps to: FR-02, FR-03, FR-04, FR-12, FR-14 in [prd.md](../../product/prd.md) · [Architecture](../architecture.md) · Component spec: [design.md](design.md) · Stack: [ADR-0006](../decisions/0006-tech-stack.md)
> Platform (team decision, 2026-09-08): all three surfaces are **web apps** in one Next.js monorepo. The jawan app is a mobile-first installable PWA (`web/apps/jawan`); counsellor and commander are consoles (`web/apps/counsellor`, `web/apps/commander`). Native/Expo wording in ADR-0005/0006 is superseded by ADR-0007.

## 1. Screen inventory (three surfaces, as shipped 2026-09-09)

**Jawan app (`web/apps/jawan`, Next.js mobile-first PWA — [F02](../../features/F02-jawan-app.md), [F03](../../features/F03-on-device-signals.md)):**

| Screen | Route | Purpose | Components (design.md §10) |
|---|---|---|---|
| Login | `/login` | username + password → token + session in `localStorage` (a private-mode write failure is caught: the app still works for the session, just not across reloads) | Button + app-local `.field-label` / `.field-input` — the login form predates the kit's `Field`/`TextInput` and should adopt them |
| Home | `(tabs)/roster` | roster-first: next duty, leave balance, pay-slip month + the check-in card | CheckInCard, SyncPill, Skeleton, UndoBar |
| Check-in sheet | *(no route — a `Sheet` over the roster home)* | 10-second emoji ladder → slider → save; voice capture optional | CheckInSheet, Sheet, Slider, VoiceCapture |
| Duty roster | `(tabs)/roster/duty` | 14-day window; an unrecognised shift code is shown as the roster wrote it | SubScreen, Badge, Skeleton |
| Leave | `(tabs)/roster/leave` | balance + applications with status | SubScreen, StatTile, Badge, EmptyState |
| Welfare hub | `(tabs)/welfare` | four rows: trend, instruments, pulse, buddy | — |
| My trend | `(tabs)/welfare/trend` | personal 90-day line, own baseline only | **TrendLine** (jawan-only, design.md §10c) |
| Instrument picker | `(tabs)/welfare/instrument` | the bank, with "done this month" and licence state per instrument | SubScreen, Badge |
| Instrument flow | `(tabs)/welfare/instrument/[id]` | one question per screen with a progress line; a PHQ-9 item-9 endorsement replaces the flow with the safety protocol (`aria-live="assertive"`, a `tel:14416` call link, and a "reach a counsellor" button that force-drains the outbox rather than waiting for the next opportunistic pass) | Button, ErrorState + an app-local `role="radiogroup"` option list and the `safety` phase |
| Unit pulse | `(tabs)/welfare/pulse` | one 1–5 rating per facet; aggregate-only surfacing, k = 5 stated on screen | SubScreen, Button, Toast + app-local `<fieldset>`/`<legend>` per facet |
| Battle buddy | `(tabs)/welfare/buddy` | pair, coarse state (ok / quiet / …), unpair | SubScreen, Segmented, ConfirmDialog |
| Me hub | `(tabs)/me` | four rows: consent, receipts, signals, settings | — |
| Consent panel | `(tabs)/me/consent` | unbundled scopes; grant and withdraw are one tap from the same place | ConfirmDialog, Toast |
| Who-viewed-my-data | `(tabs)/me/receipts` | audit receipts + notifications, §5 receipt design | — (own list, same visual language as `Timeline`) |
| Stored-data summary | `(tabs)/me/signals` | what is held per scope and when it expires | SubScreen, Badge |
| Settings | `(tabs)/me/settings` | language, the outbox contents item by item, clear queue, sign out | LanguageToggle, ConfirmDialog |

**Did not ship as separate screens, and should be read as absent rather than deleted:** the pay slip is a *card* on the roster home showing the month, not its own screen; and the **canteen, grievance and welfare-schemes** service cards render as placeholders with `coming.soon` ("Coming soon" \| "Jald aa raha hai"). They are on the home grid because ADR-0004's adoption argument depends on the roster app being the daily habit — but they are not implemented, and the UI says so rather than pretending.

**Counsellor console (`web/apps/counsellor` — [F06](../../features/F06-counsellor-console.md)):** Login → case queue (`/`, ranked, capped, SLA clocks) → case detail (`/case/[id]`: evidence chips, risk-trend chart, timeline) → session notes (`/case/[id]/notes`) → outcomes (`/case/[id]/outcomes`) → Tele-MANAS handoff (`/telemanas`). The **dual-key unmask did not ship as its own route** — it is `UnmaskPanel`, mounted in the case *layout* so the sealed-name state never leaves the screen while a counsellor works; request, approve, read and break-glass all happen in place through `Modal` + `ConfirmDialog`.

**Commander dashboard (`web/apps/commander` — [F07](../../features/F07-commander-dashboard.md)):** Login → unit heatmap (`/`, k ≥ 5) → morale index (`/morale`) → leading/lagging indicators (`/indicators`) → what-if simulator (`/simulator`) → attrition forecast (`/forecast`) → own check-in (`/checkin`, reusing `CheckInCard` and the same 1–5 emoji ladder, so one person's check-in means the same thing whatever rank they hold). Own check-in was **not** in the v1 inventory; everything else was. It posts to `POST /me/checkins` — the self-scope route, which takes no subject selector and is therefore explicitly allowed through the commander firewall — **not** `/app/checkins` as this document previously said.

## 2. Navigation model
- **Jawan web app:** 3-tab bottom bar — `Roster` (home, default tab), `Welfare` (trend, instruments, pulse, buddy), `Me` (consent, receipts, signals, settings). Each tab's landing is a hub of rows; sub-screens push and come back via `SubScreen`'s back link. The check-in opens as a bottom `Sheet` **from the roster home only** — not from any tab, as this document previously said; the card is the entry point and there is deliberately no global "+" button. Instruments push full-screen and persist their draft — answers, current index, elapsed time — into **IndexedDB** (`STORES.meta`, keyed per instrument), so the flow survives an offline page reload rather than only a re-render. The roster card is the daily entry habit (ADR-0004); the welfare tab is never the default landing. `/` redirects to `/roster`. On desktop the app renders as a centred 430px column (`.app-shell`).
- **Consoles:** sidebar nav (`ConsoleShell`), role-gated by route — counsellor and commander are separate Next.js **builds**, not a role toggle inside one tree, so a cross-role screen cannot be reached by URL because it is not in the bundle. Counsellor's sidebar has two entries (queue, Tele-MANAS); the case detail is reached from the queue rail, which stays on screen beside it (master–detail, so a case never needs back-and-forth). Commander is overview-first (heatmap is the landing) with simulator and forecast as full-width panels. Below 900px both sidebars become a horizontally-scrolling top bar — no hamburger, because a hidden nav is a nav an operator cannot scan.
- **Deep links.** A deep link to `/case/<id>` without a valid console session, or with a token for another role, clears the session and redirects to `/login` (`apps/counsellor/app/(console)/layout.tsx`). With a valid session, the server still refuses a subject outside the caseload (`backend/app/authz.py`, `assert_case_scope`) — the UI is never trusted, and that cuts both ways.
- No route in any nav graph navigates "down" to an individual from commander context — the structural F07 guarantee is also a routing guarantee, and there is no individual shape in that build to navigate *to* (design.md §11, rule 2).

Route inventory (Next.js App Router; each app is its own build, so paths are app-relative):
- **jawan** (`web/apps/jawan/app`): `/login` · `/` → redirect `/roster` · `(tabs)/roster` · `(tabs)/roster/duty` · `(tabs)/roster/leave` · `(tabs)/welfare` · `(tabs)/welfare/trend` · `(tabs)/welfare/instrument` · `(tabs)/welfare/instrument/[id]` · `(tabs)/welfare/pulse` · `(tabs)/welfare/buddy` · `(tabs)/me` · `(tabs)/me/consent` · `(tabs)/me/receipts` · `(tabs)/me/signals` · `(tabs)/me/settings`
  *Corrections against the previous inventory:* there is no `(tabs)/roster/checkin` route (the check-in is a sheet, not a page); the instrument flow is under **welfare**, not roster — `(tabs)/welfare/instrument/[id]`; and `roster/duty`, `roster/leave`, `welfare`, `welfare/instrument` and `me` (the two hubs and the picker) were not listed before.
- **counsellor** (`web/apps/counsellor/app`): `/login` · `/` (queue + detail workbench) · `/case/[id]` · `/case/[id]/notes` · `/case/[id]/outcomes` · `/telemanas`
  *Corrections:* routes are **not** prefixed `/counsellor` — that prefix belonged to a single-app plan; each console is its own build on its own port. `/case/[id]/unmask` **did not ship as a route**; unmask is a panel in the case layout.
- **commander** (`web/apps/commander/app`): `/login` · `/` (heatmap) · `/morale` · `/indicators` · `/simulator` · `/forecast` · `/checkin`
  *Corrections:* no `/commander` prefix, for the same reason; `/checkin` is new.

### Sync & conflict policy (jawan outbox, ADR-0005)

The v1 wording said "server upserts idempotently". That is not what the implementation does, and the difference matters — an upsert would let a replay silently overwrite an earlier answer. What actually happens:

**Identity.** Two different uuids do two different jobs. `getClientUuid()` (`packages/sync/src/clientUuid.ts`) is a stable **per-device** key persisted in IndexedDB; `newItemUuid()` mints a **per-item** `client_uuid` for every queued row. The comment in that file states the reason plainly: the device key alone would collapse two different check-ins into one. The `client_uuid` on the wire is always the per-item one.

**The drain.** `startSyncEngine` (`packages/sync/src/syncEngine.ts`) drains oldest-first in batches of 25 — small enough for a 2G link to finish — through one call to `POST /app/sync` per batch, and the server answers with **one result per item**, matched back by `client_uuid`. A single in-flight drain is enforced (a second caller joins the first rather than racing it on the same rows). An item is removed from the queue only once the server has acknowledged it, so killing the app mid-drain loses nothing (TC-605) and the next run resumes from the first unacknowledged item (TC-602). Failures back off 5 s → 30 s → 5 min and retry forever; the engine also drains on `online` and on tab visibility. `navigator.onLine === false` is the *only* thing treated as offline — "unknown" is treated as online, because parking the queue forever is the one failure mode offline-first must not have.

**Per-item verdicts.** The server (`backend/app/api/routers/self_service.py`) returns a status the client acts on:

| status | Meaning | Client behaviour |
|---|---|---|
| `written` | the row was created | dequeue |
| `duplicate` | a `SyncReceipt` already exists for this `client_uuid` — this is a replay after a lost response, and the row is **not** rewritten (TC-603) | dequeue |
| `duplicate_day` | a check-in (or passive row) already exists for that local day — **the earliest capture wins**, never a silent overwrite and never a second row | dequeue, count as a conflict |
| `already_this_month` | that instrument was already taken this calendar month — **one instrument per month, enforced server-side** | dequeue, count as a conflict |
| `replaced` | a unit-pulse rating for the same period + facet was updated (a pulse is an opinion you may change; a check-in is a record of a day, which is why they differ) | dequeue |
| `dropped_no_consent` | the scope gating that table has no active consent, so the row was refused with `sync.dropped.consent` ("Not sent — you had turned this permission off." \| "Nahi bheja — aapne ye permission band kar di thi.") | dequeue |
| `rejected` | the row is permanently bad (unknown table, unknown instrument, unknown voice schema version, rating out of range) | **kept in the queue with its reason recorded** via `markAttempt(item, reason)`, and the drain moves on |

That last row is the deliberate one: a permanently bad item must not block the queue behind it, but it must not vanish either. `attempts` and `conflict` are stored on the queue row, and `/me/settings` surfaces both — the conflict count (`settings.conflicts`) and a list of every queued row carrying a rejection reason (`settings.rejected`) — so a stuck row is never invisible to the person whose data it is.

**Consent.** Consent state is authoritative server-side. Granting is offline-safe in a specific way worth writing down: if the online `grantConsent()` call fails, the check-in sheet enqueues the grant *before* the check-in row it gates, so the FIFO drain hands the server consent first and the row second — the row is never refused because its own permission was still in the queue behind it. The local `saarthi.consented.checkin` flag exists only so the sheet knows the state on a cold offline open; a private-browsing failure to write it is caught and ignored, because the server copy is authoritative.

Withdrawal runs the opposite direction and is immediate: `/me/consent` calls `withdrawBundle(id)` and then `purgeQueueForTables(tables)` (`packages/sync/src/queue.ts`) — **every queued row captured under the withdrawn scope is deleted from the device**, not just stopped from being sent. Nothing is left behind to drain later. `/me/settings` additionally offers a `clearAll()` behind a grave-toned `ConfirmDialog` for the whole local store.

**One more thing that is not a conflict policy but reads like one:** `useApi` can serve a screen from its last-known IndexedDB response while it revalidates, so opening the app offline shows yesterday's aggregates marked stale rather than a blank screen. That cache is a read cache; the outbox is the only writer.

## 3. Component reuse from design.md
Shared across surfaces: CheckInCard (jawan + commander's own check-in — identical component, same i18n keys); care-state chips (leaf/sun/hand-heart/phone) wherever a ladder state appears; SyncPill (jawan app only); error/recovery copy patterns (`sync.error.recovery`). Console-only: the heatmap grid, the morale dials, the evidence composition and the what-if simulator — these shipped as *routes composed from kit primitives*, not as the single named components v1 imagined; design.md §10d maps each old name to what it actually became. Deliberately **not** reused: `TrendLine` (personal) exists only in the jawan app — no personal-trend rendering in either console, and since 2026-09-09 that is a build-failing lint rule rather than a convention (design.md §10c). Design tokens ship as one JSON package (`@saarthi/tokens`) consumed by all three web apps; Devanagari line-height, 48dp targets, and focus-ring rules are enforced in the token layer, not per-screen.

## 4. Data flow (app → API → engines → consoles)
```
Jawan app ──sync queue──▶ Core API ──▶ HR ingestion (F01) ──▶ Rules engine (F04)
   ▲ voice/passive: feature vectors only (F03, ADR-0002)         │ scores + factors
   │                                                             ▼
   │ who-viewed receipts ◀── audit log (append-only, F08) ◀── Intervention engine (F05)
   │                                                             │ ranked cases, caps
Consoles (web) ◀── role-scoped read APIs ◀───────────────────────┘
   counsellor: pseudonymized cases → dual-key unmask → outcomes (ML v2 labels, ADR-0001)
   commander: aggregation service only — k ≥ 5 suppression server-side, no ID parameters
```
- Consent state is authoritative server-side; the app caches it for offline gating and revalidates on every sync.
- The outbox queue (jawan app, IndexedDB) is the only writer of check-in/instrument/signal rows; server-side idempotency keys (`client_uuid`) make retries safe.
- Pseudonym→identity resolution exists in exactly one counsellor-path function, guarded by dual keys (F06).
- Receipts flow the opposite direction: audit log events → app sync → WhoViewedTimeline.
- The aggregation service is the sole source of every number on the commander surface; the web client cannot compute, cache-persist, or export an individual row.

## 5. Implementation layout (the real tree, 2026-09-09)

```
web/                              bun workspace: workspaces = ["apps/*", "packages/*"]  (ADR-0006; web-first per ADR-0007)
  package.json                    dev:jawan|counsellor|commander · build · lint · lint:boundaries
                                  · typecheck · test · check · e2e
  tsconfig.base.json
  apps/
    jawan/                        mobile-first PWA, port 3100
      app/
        layout.tsx                fonts + tokens.css + ui.css + globals.css, I18nProvider, SW registration
        page.tsx                  redirect → /roster
        login/page.tsx
        (tabs)/layout.tsx         SkipLink · AppBar-equivalent topbar · SyncPill · BottomTabs · sync engine
        (tabs)/roster/            page.tsx · CheckInSheet.tsx · duty/ · leave/
        (tabs)/welfare/           page.tsx · trend/ · instrument/ · instrument/[id]/ · pulse/ · buddy/
        (tabs)/me/                page.tsx · consent/ · receipts/ · signals/ · settings/
        components/               TrendLine · VoiceCapture · SubScreen
        lib/                      cache (IndexedDB read-cache keys) · format · mock-hr · sync (drain wiring)
      public/sw.js                Service Worker app-shell cache — API calls are never cached
    counsellor/                   console, port 3200
      app/
        (console)/layout.tsx      ConsoleShell + the door (wrong role ⇒ clearSession + /login)
        (console)/(workbench)/    page.tsx (queue) · case/[id]/{layout,page,notes,outcomes}
        (console)/telemanas/
        components/               QueueRail · SlaClock · UnmaskPanel · RiskTrendChart · CaseContext
                                  · LoadError · session · format · useNow
    commander/                    dashboard, port 3300 — aggregates only
      app/                        page.tsx (heatmap) · morale/ · indicators/ · simulator/ · forecast/
                                  · checkin/ · login/ · Frame.tsx · units.tsx · parts.tsx
  packages/
    tokens/                       src/tokens.json (single source) → scripts/generate.mjs →
                                  dist/tokens.css (hex fallback + OKLCH) + src/index.ts
    i18n/                         src/{en,hi}.json (495 keys each, parity enforced) · index.tsx (useT)
                                  · src/pending/<app>.json staging area for new keys
    ui/                           the shared kit: 30+ components + Icons + useApi, styled from ui.css
    sync/                         idb · queue · clientUuid · syncEngine  (IndexedDB outbox)
    api/                          http (API_BASE, session) + subpath exports ./jawan ./counsellor
                                  ./commander — the root deliberately does NOT re-export role clients
    instruments/                  the validated screener bank (PHQ-9, GAD-7, PSS-10, ISI) + scoring
                                  + types. Zero invented items; ISI item text is licence-gated.
  scripts/
    lint-boundaries.mjs           the 8 architectural checks (design.md §11) — first web step in CI
    merge-pending-i18n.mjs        folds packages/i18n/src/pending/*.json into en.json + hi.json
    test-setup.ts                 fake-indexeddb, so the queue tests run against a real IndexedDB API
  e2e/smoke.mjs                   playwright-core: offline check-in, drain-on-reconnect, receipts,
                                  cross-role refusal, no individual in the commander DOM, 320px, Hindi
backend/ (kv)                     FastAPI: /auth/* /app/* /me/* /interventions/* /privacy/* /aggregates/*
data/ (neel)                      synthetic data generator (F09)
```

**Two things that are not in this tree and are not oversights.** There is no `apps/jawan/features/` directory — the feature split lives in the route folders themselves, which is the App Router's own grain and one fewer indirection to keep in sync. And there is no `mobile/`: no Expo or React Native code ships, the PWA installs to the home screen, and there is no app-store binary (ADR-0007).

**`packages/instruments` is new since this document was last written**, and it is the reason the instrument flow is a route rather than a component: the bank, its scoring, its licence status and its Hindi-review status are data, and the screen is a thin renderer over them.

Conventions: bun everywhere in JS (ADR-0006); every PR touching these trees updates the mapped F-doc in the same PR (AGENTS.md rule 1); no welfare data may sit in any client cache lacking a purge path — consent withdrawal clears the local tables and purges the outbox for that scope.

## 6. Cross-cutting acceptance (client layer)

Each line now names the check that holds it. `[x]` means something fails if it regresses; `[~]` means partly automated with a stated remainder; `[ ]` means still a human's job.

- [~] **The 9-state rule per control (design.md §6).** The states are components rather than per-screen improvisation — `Skeleton` (loading), `EmptyState` (empty), `ErrorState` (error), `:disabled` and `:focus-visible` in `ui.css` — so a screen gets them by using the kit. *Remainder:* nothing asserts that every screen actually renders all nine, and the airplane-mode pass on a real low-end Android-class device has not been run. Read the offline half of this line as covered by the tests below, and the visual half as open.
- [x] **Tokens JSON is the single source for colour.** `bun scripts/lint-boundaries.mjs`, rule `tokens-only` — `oklch(` outside `packages/tokens` fails the build. Spacing and type are token variables by convention in the same stylesheets, which is *not* separately linted; only colour is.
- [x] **Contrast floors are measured, not asserted.** Same script, rule 7: 11 text pairs against 4.5:1 and 7 non-text pairs against 3:1, computed on the hex fallbacks. This is what caught the amber care chip at 2.03:1 (design.md §2).
- [x] **i18n keys only, and en/hi parity.** Same script: `i18n-keys-only` (literal JSX word text fails), `unknown-i18n-key` (every `t("…")` must resolve), and a two-way parity check between `en.json` and `hi.json` — 495 keys each today. *Known gap:* the literal check reads JSX text, not attributes, so `aria-label="Primary"` in `BottomTabs.tsx:21` currently slips through (design.md §9b).
- [~] **Devanagari renders correctly.** `--sa-line-height-hi: 1.6` is applied at `[data-locale="hi"]` in every app's `globals.css` and in `ui.css` for inputs; `TextArea` grows to its rows and no text container is fixed-height. *Remainder:* "no clipped matras" is a visual judgement and still needs the manual pass in design.md §9b — and `<html lang>` stays `"en"` in all three apps regardless of locale, so a screen reader announces Hindi in an English voice (design.md §9b, gap 2).
- [x] **Cold-start → check-in with zero network; the queue drains on reconnect without duplicates or re-sent instruments.** `bun test` — `web/packages/sync/src/sync.test.ts` runs TC-601 (queue then sync exactly once), TC-602 (72 entries batch, and a mid-drain failure resumes from the first unacknowledged item), TC-603 (replaying a `client_uuid` never creates a second record), TC-604 (a same-day check-in is a *conflict*, not an error; a rejected item stays queued with its reason and does not block the rest) and TC-605 (a kill mid-sync loses nothing) against a real IndexedDB via `fake-indexeddb`. 48 web tests pass as of 2026-09-09. `web/e2e/smoke.mjs` covers the same path in a real browser with the network toggled off.
- [x] **Role routing: the commander build cannot import counsellor API modules, and vice versa.** `lint-boundaries.mjs` rule `role-isolation`, made enforceable by `@saarthi/api` exposing role clients only as subpath exports and deliberately not re-exporting them from its root. Reinforced by rule `commander-no-individual`: the strings `pseudonym_id`, `legal_name`, `personnel_id`, `PersonRow`, `IndividualRow` may not appear anywhere in `apps/commander`.
- [x] **The personal trend never renders in a console.** Rule `trendline-jawan-only`. New since this document was last written; previously a convention.
- [x] **Consent withdrawal purges the device.** `withdrawBundle()` then `purgeQueueForTables()`, covered by `sync.test.ts` ("withdrawing a scope drops exactly that scope's queued rows", "clearing the device leaves no trace of any scope", "removeFromQueue only removes the item it was given").
- [x] **Withdrawal leaves zero command-visible trace (FR-17).** Server-side, `backend/tests/test_privacy.py::test_silent_withdrawal` — the commander aggregate is compared before and after a withdrawal and must contain no consent or withdrawal field and the same `k`. The masking engine has the matching rule in `test_privacy_paths.py`: withdrawal must never look like concealment.
- [ ] **200% zoom, 320px reflow walked screen by screen, screen-reader walkthrough, colour-blind simulation of the shipped build, low-light/gloved device use.** Open. These belong to UX-001's manual session plan (design.md §9b) and no automated check stands in for them.

All the `[x]` lines above run in CI on every push (`.github/workflows/ci.yml`, job `web`: boundaries → typecheck → `bun test` → production build), behind the backend firewall gate which runs first of all.
