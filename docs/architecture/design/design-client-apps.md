# design-client-apps.md — Client Applications: Jawan App + Consoles

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-02, FR-03, FR-04, FR-12, FR-14 in [prd.md](../../product/prd.md) · [Architecture](../architecture.md) · Component spec: [design.md](design.md) · Stack: [ADR-0006](../decisions/0006-tech-stack.md)

## 1. Screen inventory (three surfaces)

**Jawan app (`mobile/`, Expo/RN — [F02](../../features/F02-jawan-app.md), [F03](../../features/F03-on-device-signals.md)):**
| Screen | Purpose | Components (design.md §10) |
|---|---|---|
| Home | roster-first: duty, leave, pay slip, canteen, grievance + check-in card | CheckInCard, SyncPill |
| Check-in sheet | 10-second emoji → slider → submit | CheckInCard, mic/waveform |
| Instrument flow | monthly validated instrument, one question/screen | InstrumentFlow |
| My trend | personal 90-day line, own baseline only | TrendLine |
| Consent panel | unbundled scopes, silent withdrawal | ConsentSheet |
| Who-viewed-my-data | access receipt timeline | WhoViewedTimeline |
| Buddy / Unit pulse | coarse buddy states; 1–5 climate ratings | UnitPulse |
| Signal settings | passive scopes, purge queue | ConsentSheet, SyncPill |
| Settings | language, voice prompts, sync | — |

**Counsellor console (`web/` — [F06](../../features/F06-counsellor-console.md)):** Case queue (ranked, capped, SLA clocks) → Case detail (evidence card, risk-trend chart, timeline) → Dual-key unmask modal → Session note form → Outcome tracker → Tele-MANAS handoff form.
**Commander dashboard (`web/` — [F07](../../features/F07-commander-dashboard.md)):** Unit heatmap (k ≥ 5) → Morale index dials → Leading/lagging columns → What-if simulator → Attrition forecast → Own check-in (mobile CheckInCard reused, `POST /v1/me/checkins`).

## 2. Navigation model
- **Mobile:** 3-tab bottom bar — `Roster` (home, default tab), `Welfare` (trend, pulse, buddy), `Me` (consent, receipts, settings). The check-in opens as a bottom sheet over any tab; instruments push full-screen with progress dots and never lose state on process death (offline-first, ADR-0005). The roster card is the daily entry habit (ADR-0004); the welfare tab is never the default landing.
- **Consoles:** sidebar nav, role-gated by route — counsellor and commander are separate route trees, not a role toggle inside one tree. Counsellor is master–detail (queue left, case right) so a case never needs back-and-forth; commander is overview-first (heatmap is the landing), simulator and forecast as full-width panels. Deep links to a case are session-scoped and expire with the session.
- No route in any nav graph navigates "down" to an individual from commander context — the structural F07 guarantee is also a routing guarantee.

Route inventory (expo-router / Next.js App Router):
- mobile: `(tabs)/roster` · `(tabs)/roster/checkin` (sheet) · `(tabs)/roster/instrument/[id]` · `(tabs)/welfare/trend` · `(tabs)/welfare/pulse` · `(tabs)/welfare/buddy` · `(tabs)/me/consent` · `(tabs)/me/receipts` · `(tabs)/me/signals` · `(tabs)/me/settings`
- counsellor: `/counsellor` (queue) · `/counsellor/case/[id]` · `/counsellor/case/[id]/unmask` (modal route) · `/counsellor/case/[id]/notes` · `/counsellor/case/[id]/outcomes` · `/counsellor/telemanas`
- commander: `/commander` (heatmap) · `/commander/morale` · `/commander/indicators` · `/commander/simulator` · `/commander/forecast`

Sync & conflict policy (mobile outbox, ADR-0005):
- every queued item carries `client_uuid`; server upserts idempotently — retries never duplicate rows.
- a re-submitted check-in for the same local day keeps the earliest capture; instruments are one-shot per month, enforced server-side.
- consent changes take effect locally first (gating capture), then reconcile server-side on next sync.
- the queue is bounded and drained opportunistically; nothing welfare-critical waits on a user action to sync.

## 3. Component reuse from design.md
Shared across surfaces: CheckInCard (jawan + commander's own check-in — identical component, same i18n keys); care-state chips (leaf/sun/hand-heart/phone) wherever a ladder state appears; SyncPill (mobile only); error/recovery copy patterns (`sync.error.recovery`). Web-only: AggregateHeatmap, MoraleIndex dials, EvidenceCard, WhatIfSimulator — Next.js components over role-scoped API calls. Deliberately **not** reused: TrendLine (personal) exists only in the jawan app — no personal-trend rendering in either console. Design tokens ship as one JSON package consumed by RN and web; Devanagari line-height, 48dp targets, and focus-ring rules are enforced in the token layer, not per-screen.

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
- The outbox queue (mobile) is the only writer of check-in/instrument/signal rows; server-side idempotency keys (`client_uuid`) make retries safe.
- Pseudonym→identity resolution exists in exactly one counsellor-path function, guarded by dual keys (F06).
- Receipts flow the opposite direction: audit log events → app sync → WhoViewedTimeline.
- The aggregation service is the sole source of every number on the commander surface; the web client cannot compute, cache-persist, or export an individual row.

## 5. Implementation layout
```
mobile/                        Expo / RN, bun (ADR-0005: API 26+, offline-first)
  app/                         expo-router: (tabs)/roster · (tabs)/welfare · (tabs)/me
  features/
    checkin/  instruments/  consent/  receipts/  pulse/  buddy/  signals/   (F03)
  db/                          expo-sqlite schema + migrations (check_in queue, consents)
  sync/                        outbox queue, idempotent client_uuid, backoff
  native/voice-prosody/        Kotlin module: extraction in-process, only the struct crosses the bridge
  i18n/                        en, hi (+ reserved regional keys), voice-prompt assets
web/                           Next.js (App Router), bun
  app/counsellor/              queue, case/[id], unmask, notes, outcomes, telemanas
  app/commander/               heatmap, morale, indicators, simulator, forecast
  components/                  design-system ports (tokens JSON → CSS vars)
  lib/api/                     typed clients per role; no cross-role imports
backend/ (context)             FastAPI: /v1/* per F02/F03/F06/F07; aggregation service (k ≥ 5)
```
Conventions: bun everywhere in JS (ADR-0006); every PR touching these trees updates the mapped F-doc in the same PR (AGENTS.md rule 1); no welfare data may sit in any client cache lacking a purge path — consent withdrawal clears the local tables.

## 6. Cross-cutting acceptance (client layer)
- [ ] All three surfaces pass the 9-state rule per control (design.md §6); offline states verified with airplane mode on a low-end device.
- [ ] Tokens JSON is the single source for color/spacing/type on both platforms; no hardcoded OKLCH values outside the token package.
- [ ] i18n keys only — no literal user-facing strings in components; `hi` renders with Devanagari line-height and no clipped matras.
- [ ] Mobile cold-start → check-in submit works with zero network; the queue drains on reconnect without duplicates or re-sent instruments.
- [ ] Role routing: the commander build cannot import counsellor API modules (enforced by a path lint rule), and vice versa.
- [ ] Consent withdrawal from the mobile app clears local scope data, purges the queue for that scope, and leaves zero command-visible trace (FR-17 integration test).
