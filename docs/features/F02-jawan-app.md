# F02 — Jawan App (roster-first voluntary check-in, consent, transparency)

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Maps to: FR-02, FR-04, FR-15, FR-19 in [prd.md](../product/prd.md) (FR-17 silent withdrawal surfaces here, owned by [F08](F08-privacy-safety-architecture.md)) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)
> Platform (team decision, 2026-09-08): the jawan app is a **web app** — Next.js, mobile-first, installable PWA — not a native Expo app. Offline-first is preserved via a Service Worker app shell + IndexedDB outbox queue keyed by `client_uuid` (supersedes the native/SQLite wording of ADR-0005; see ADR-0007).

## Purpose
The app personnel already open daily — duty roster, leave, pay slip — with a 10-second wellness check-in riding on that home screen ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)). Zero adoption ask; welfare data rides an existing habit. The app is never branded as therapy: framing is "fitness for duty" + "parivaar welfare". It is also where trust is demonstrated rather than promised: unbundled consent, silent withdrawal, and who-viewed-my-data receipts.

Adoption guardrails (what makes participation real rather than coerced):
- Non-participation contributes zero priority points; the app never threatens, nags, or counts streaks.
- Unit-level rewards only — no individual incentives, which would falsify data.
- Officer-first rollout: commandants take the check-in publicly before the unit is asked to.
- A 10-second daily check-in is the core loop; full instruments are monthly, never the entry price.

## User-visible behavior (screen by screen)
1. **Home (roster-first).** Cards: duty roster (`roster.view`), leave application, pay slip, canteen, grievance, family welfare schemes — F01/HRMS-backed surfaces. Below them one calm card: "Aaj kaisa laga? (10 second)" (`home.checkin.title`). No badge, no streak counter, no guilt mechanics (anti-pattern per ADR-0004).
2. **Check-in sheet.** Bottom sheet: emoji row (5 states, `checkin.emoji.*`) → one slider (0–10, `checkin.slider.label`) → submit. Optional free text with mic (voice capture path is F03). Hard budget: ≤ 3 taps, no network required (FR-04).
3. **Monthly instrument.** One validated instrument per month, rotated from the bank — PHQ-9, GAD-7, PSS-10, ISI (core per FR-02), plus Maslach Burnout and PCL-5 (bank extension; PRD FR-02 text to be extended in the same PR that lands them). One question per screen, icon + text, progress dots. Disclaimer every time: "Ye aatm-chintan ka sahara hai, nidan nahi." (`screen.disclaimer`, corrected against `en.json`/`hi.json` on 2026-09-09). **Validated instruments only — zero invented questions.** Scales are translated **and culturally adapted** (clinician-reviewed back-translation, idiom substitution, re-anchored response options, recorded voice prompts) — a literal translation of Western scales scores wrong. Hindi + English at launch; regional languages are i18n data files, not redesigns (design.md §8).
4. **My trend.** Personal 90-day TrendLine against own baseline. No peer comparison, no unit ranking, ever.
5. **Consent panel.** Unbundled scopes (`consent.scope.checkin/.instrument/.voice/.passive/.pulse/.buddy`), each with a plain-language purpose line. Withdrawal is the same tap depth as granting, takes effect immediately, and is **silent**: nothing command-visible changes (FR-17).
6. **Who viewed my data.** Receipt timeline: role chips, timestamp, purpose string from the audit log, access duration; unmask events render in the same list ("Counsellor + Welfare Officer opened your case on 12 Sep — reason: Red-tier outreach"). Header: "Aapka data. Aapka adhikar." (`receipt.header`). The most important 15 seconds of the product.
7. **Battle buddy.** Pair with one colleague; both see each other's coarse status only (`buddy.state.ok|quiet|sos`). `sos` offers one tap to the buddy's unit JCO contact and the 14416 line. Command sees neither side of any pairing.
8. **Unit pulse.** Rate command climate 1–5 on fixed facets (leadership, fairness of duties, family support, facilities). One rating per member per period; only the k ≥ 5 aggregate surfaces (FR-19), and it surfaces to commanders (F07), not back into the app.
9. **Settings.** Language, voice prompts, sync status (SyncPill), pause/withdraw each data scope.

## Data model (fields, units, consent tags)
| Table | Key fields | Consent tag |
|---|---|---|
| `check_in` | `pseudonym`, `local_date`, `mood_emoji` (1–5), `stress_slider` (0–10), `free_text?`, `captured_at`, `synced_at` | `checkin` |
| `instrument_response` | `instrument` (phq9/gad7/pss10/isi/mbi/pcl5), `item_index`, `raw`, `total`, `validity_items[]`, `taken_at` | `instrument` |
| `consent_record` | `scope`, `granted_at`, `consent_version`, `withdrawn_at` | self-referential |
| `unit_pulse` | `period`, `facet`, `rating` (1–5) | `pulse` |
| `buddy_pair` | `pair_id`, `a_pseudonym`, `b_pseudonym`, `coarse_state` | `buddy` |
| `access_receipt` (server, read-only here) | `viewer_role`, `purpose_code`, `accessed_at`, `duration_s`, `unmask_event?` | n/a (transparency) |

Pseudonym is the only identifier on the wire; the pseudonym→identity map never reaches this app (F08). `free_text` would sync only under `checkin` consent — but as of 2026-09-09 the `checkins` table has **no `free_text` column** and the server drops the field (see Implementation status). There are **no voice transcripts** at any point, on device or server: producing one would require exactly the audio buffer [F03](F03-on-device-signals.md) refuses to create.

### i18n (design.md §8 — all strings ship via keys, never literals)

**Where the strings live.** The dictionary is no longer a table in this document. It is
`/Users/ns/code/sih-hackathon-26/web/packages/i18n/src/en.json` + `hi.json` — **495 keys each** as of 2026-09-09, shared by all
three apps. Two CI gates in `web/scripts/lint-boundaries.mjs` keep it honest and make it pointless to
mirror here: rule 6 fails the build if any key is present in one file and missing from the other
(en/hi parity), and rule 7 fails the build if any `t("…")` call in `apps/**` or `packages/**` names a
key that is in neither `en.json` nor a declared `packages/i18n/src/pending/<app>.json` entry. Both run
in `.github/workflows/ci.yml` before the web build.

The keys F02 itself introduced, corrected against the shipped `en.json`/`hi.json`:

| Key | `en` | `hi` |
|---|---|---|
| `home.checkin.title` | "How was today? (10 seconds)" | "Aaj kaisa laga? (10 second)" |
| `home.checkin.empty` | "First check-in — takes 10 seconds." | "Pehli baar check-in — 10 second lagenge." |
| `screen.disclaimer` | "This is reflection support, not diagnosis." | "Ye aatm-chintan ka sahara hai, nidan nahi." |
| `receipt.header` | "Your data. Your right." | "Aapka data. Aapka adhikar." |
| `sync.pill.queued` | "{n} saved, will send" | "{n} save hue, bhejenge" |
| `sync.error.recovery` | "Sync failed. Your data is safe, we'll retry." | "Sync nahi hua. Data safe hai, dobara try karenge." |
| `instrument.done` | "Done for this month" | "Is mahine ho gaya" |
| `buddy.state.ok` · `.quiet` · `.sos` | ok / quiet / need a word | theek / thoda chup / baat karo |

**One key changed meaning.** `sync.pill.queued` was "{n} check-ins saved, will send". It is now
**"{n} saved, will send"** (hi: "{n} save hue, bhejenge"), because the outbox it counts is no longer
check-ins only: `QueueTable` is `checkin | instrument | consent | pulse | passive | voice`
(`web/packages/sync/src/queue.ts`), and the pill renders `snapshot.queued`, the whole queue length.
Saying "check-ins" would have under-reported an instrument or a pulse rating still waiting to send —
the exact "you believe it was sent" failure ADR-0005 forbids.

**One key this document has always named lives elsewhere.** `instr.not_diagnosis` — cited by
[clinical-instruments.md](../explanation/clinical-instruments.md) §5 as "defined in F02" — is **not** in
the web dictionary. It is a server-side key in `backend/app/i18n.py`, returned as `disclaimer_key` by
`/app/me/checkins`, `/app/me/trend` and the counsellor case routes. The web screens use
`screen.disclaimer` for the same sentence. Two keys for one sentence is a wart, not a design; consolidating
them is unowned work as of 2026-09-09.

**Hindi convention at v1 — romanised, deliberately.** Every one of the 495 `hi` values ships in
**romanised Hindi (Hinglish)**, not Devanagari: 0 of 495 values contain a Devanagari codepoint. That is a
readability decision for a mixed-literacy audience, not an unfinished translation — a jawan comfortable in
spoken Hindi and Latin script reads "Aaj kaisa laga?" faster than "आज कैसा लगा?", and the check-in has a
10-second budget. The repo currently reads as inconsistent about this, so, plainly: the Devanagari
typography rules in [design.md](../architecture/design/design.md) §3 are **implemented and unchanged**, and
they are what makes the swap cheap:
- **The face is named.** `--sa-font-sans` is `"Noto Sans", "Noto Sans Devanagari", system-ui, sans-serif`
  (`web/packages/tokens/src/tokens.json`). Nothing is downloaded — Noto Devanagari is expected from the OS,
  where it ships by default on Android; the app pays zero bytes for it on a 2 GB device.
- **The line-height rule is live.** `web/apps/jawan/app/globals.css` carries
  `[data-locale="hi"] body { line-height: var(--sa-line-height-hi); }` — the +0.1 over the Latin
  `--sa-line-height`, applied by locale, not by string.
- **No fixed-height text containers**, so a matra has nowhere to clip (e.g. `TextArea` grows to its rows by
  construction).

So shipping a Devanagari string set is a **data-file swap of `hi.json`, not a redesign**: the font stack, the
locale attribute and the line-height token are all already in the build and would start doing visible work
the moment the glyphs change. The one place Devanagari is already authored is the server-side
`instr.not_diagnosis` value in `backend/app/i18n.py` ("यह निदान नहीं, आत्म-चिंतन का सहारा है"). Which
script the v1 pilot ships is a field decision, and it is reversible in one file.

## API surface (endpoints, role-scoped)
Role `jawan`; every endpoint resolves the subject from the auth token — **no route in this surface accepts a
personnel id, a pseudonym, or any other subject selector**, so "read someone else" has no shape to be
misused (`backend/app/api/routers/self_service.py` module docstring). The list below is the shipped
surface, read off `backend/app/api/routers/{auth,self_service,app_data,pulse,buddy,privacy}.py` on
2026-09-09; it supersedes both the earlier `/v1/*` naming and the single-endpoint sketch that stood here.
The typed client is `web/packages/api/src/jawan.ts`.

**Auth** — `POST /auth/login` (username/password → bearer; demo personas `jawan.demo` / `counsellor.a` /
`welfare.a` / `commander.3bn`) · `POST /auth/token` (OAuth2 form) · `GET /auth/me`.

**The offline outbox now drains through one batched endpoint.**
- `POST /app/sync` — body `{items: [{table, client_uuid, captured_at?, payload}]}`, where `table` is one of
  `checkin | instrument | passive | voice | pulse | consent`. **Idempotent by `client_uuid`**: an item
  already accepted is recorded in a `SyncReceipt` row and reported `duplicate` without being rewritten, so
  a retry after a lost response can never duplicate a row (TC-603). The response carries **one result per
  item** — `written | duplicate | duplicate_day | already_this_month | already_granted | replaced |
  dropped_no_consent | rejected` — so a partial failure resumes from the last checkpoint instead of
  replaying the whole queue (TC-602), and one permanently bad row never blocks the queue behind it (TC-604).
  A queued row whose scope was withdrawn while it sat offline is **dropped, not written** (the `GATE` map;
  reason key `sync.dropped.consent`) — the consent state at sync time wins over the one at capture time.

**The single-row writes remain, for a direct online write.**
- `POST /app/checkins` · `POST /app/instruments` · `POST /app/passive` (`app_data.py`) — one row each,
  each gated on `has_voluntary_consent`. These are the pre-outbox path; the app's own screens go through
  `/app/sync`, and `test_client_surface.py` exercises both.
- `POST /app/pulse` — a batch of facet ratings, gated on the `unit_pulse` bundle; re-rating a facet in the
  same ISO week **replaces your own answer and never creates a second contributor** (`pulse.py`).

**Self-scope reads.**
- `GET /app/roster?days=1..90` · `GET /app/leave` · `GET /app/payslip` — HRMS thin read proxies (see
  Implementation status for what each actually reads).
- `GET /app/me/checkins?days=1..365` · `GET /app/me/instruments` · `GET /app/me/trend`.
- `GET /app/signals/summary` — "what the server holds about me, per scope, with its expiry" (F03 screen 4).
- `GET /app/who-viewed` — screen 6. Reads the audit log filtered to this pseudonym and to the actions that
  constitute a view: `risk.read`, `risk.explanation`, `signals.read`, `identity.read`, `unmask.grant`,
  `break_glass.open`, `interventions.action`, `interventions.outcome`, `telemanas.referral`.
- `GET /app/notifications` — buddy SOS and the break-glass "you were told at the time" notice.
- `GET /app/pulse/me` — what *I* rated this period, so the screen can say "already rated".

**Consent (screen 5).**
- `GET /app/consent` — the panel: every bundle with granted state, `label_key`, `purpose_key`,
  `data_categories`, `retention_days`. Six bundles: `checkin`, `instruments`, `voice`, `passive`,
  `unit_pulse`, `buddy`.
- `POST /app/consent` — grant one bundle; writes a `ConsentArtefact` whose `artefact_hash` is a real sha256
  over its own content (TC-449).
- `POST /app/consent/withdraw/{bundle_id}` — per-scope silent withdrawal (FR-17). Writes only the consent
  store and the audit log; neither has a read path into any command-visible table.
- `POST /app/consent/withdraw` — withdraw every bundle at once.

**Battle buddy (screen 7).** `GET /app/buddy` · `POST /app/buddy/pair` · `DELETE /app/buddy` ·
`POST /app/buddy/state`. The buddy read returns coarse state, pseudonym and unit only — no name, no score,
no tier, ever.

**Officer-first rollout, deliberately outside `/app`.** `POST /me/checkins` · `GET /me/checkins` — self-scope
for *any* role, accepting no subject selector. This is how a commandant takes the same 10-second check-in
(ADR-0004) without the ADR-0003 middleware needing a subject-capable exception; `/me/checkins` is listed in
`firewall.COMMANDER_ALLOWED_EXACT` for exactly that reason (TC-428).

**Not this app's.** `GET /aggregates/unit/{id}/pulse` and the rest of `/aggregates/*` are the commander
surface (F07). `/app` is in `firewall.COMMANDER_DENIED_PREFIXES`, so a commander token 403s on every route
in this section — asserted route by route in `backend/tests/test_client_surface.py`.

## States (idle/loading/empty/error/offline)
- **Offline:** check-in writes to the local IndexedDB queue instantly; SyncPill: "3 saved, will send" (`sync.pill.queued`) — queued data never renders in error styling (ADR-0005). The app shell is cached by a Service Worker, so an airplane-mode reload still opens the app. Instruments run fully offline; sync resumes opportunistically.
- **Empty:** first-run teaching copy: "Pehli baar check-in — 10 second lagenge" (`home.checkin.empty`).
- **Error:** recovery paths, never blame: "Sync nahi hua. Data safe hai, dobara try karenge." (`sync.error.recovery`).
- **Already done / disabled:** instrument card shows "Is mahine ho gaya" (`instrument.done`); buddy slot empty state explains pairing in one line.
- **Conflict:** re-submitted check-in for the same local day is a no-op server-side; the client keeps the earliest capture.

## Privacy notes (what this feature must never do)
- Never expose an individual risk score, badge, or ranking to anyone in the command chain — no such endpoint exists (ADR-0003 firewall; see F07).
- Never gamify or incentivise individually — unit rewards only; a coerced check-in is a falsified data point.
- Never reveal who withdrew consent, via any endpoint, aggregate denominator, or participation count.
- Never let one token address another jawan's data — self-scope is the only query shape.
- Never brand anything as therapy, counseling, or "problem detection" in copy or screenshots.
- Raw free text is visible to no one in the chain; counsellor access requires consent + dual key (F06/F08) and is receipted.
- No PII (name, service number) travels with wellness payloads; screenshots for demo decks must use synthetic data (F09).

## Out of scope / non-goals
Diagnosis or treatment; clinician chat; social feed or peer ranking; streaks/leaderboards; native app binaries for any OS (web-first per team decision 2026-09-08 — the PWA installs to the home screen but ships no app-store build); wearable pairing (F03 owns the surface); ambient listening (F03/ADR-0002 anti-goal); regional language translation at v1 (keys reserved); HR workflow authoring (leave approval stays in existing HRMS).

## Implementation status (as of 2026-09-09)
The app is `/Users/ns/code/sih-hackathon-26/web/apps/jawan` — a Next.js app-router PWA in the `web` bun workspace, three bottom
tabs (`roster` / `welfare` / `me`, `app/(tabs)/layout.tsx`). Screen numbers are the ones in
"User-visible behavior" above.

| Screen | Route in the app | Server route(s) | Status |
|---|---|---|---|
| 1 · Home (roster-first) | `/roster` | `GET /app/roster`, `/app/leave`, `/app/payslip`, `/app/me/checkins?days=1` | **Shipped.** Duty, leave and pay-slip cards plus the calm check-in card. Canteen / grievance / family-welfare render as `coming.soon` tiles — placeholders, not adapters. |
| 2 · Check-in sheet | `/roster` → `CheckInSheet.tsx` | outbox → `POST /app/sync` (`table: "checkin"`) | **Shipped.** Emoji row (5), 0–10 slider, optional sleep hours, optional free text, `VoiceCapture`. Grants the `checkin` bundle inline on first use (queued as a `consent` item ahead of the check-in if offline, so the server sees consent before the row it gates). Confirmation is an 8 s undo bar, not a modal. |
| 3 · Monthly instrument | `/welfare/instrument`, `/welfare/instrument/[id]` | outbox → `POST /app/sync` (`table: "instrument"`); `GET /app/me/instruments` | **Shipped, four instruments.** The bank is PHQ-9, GAD-7, PSS-10, ISI (`web/packages/instruments/src/bank.ts`); the backend `INSTRUMENTS` tuple matches. MBI and PCL-5 named in screen 3 above are **not** in the shipped bank. ISI ships scoring, bands and the flow but **no item text** (licence-gated). One question per screen, progress dots, draft persisted to IndexedDB on every answer so an offline reload mid-flow loses nothing. PHQ-9 item 9 routes to a non-dismissable human-contact screen. See [clinical-instruments.md](../explanation/clinical-instruments.md) "Implementation status". |
| 4 · My trend | `/welfare/trend` | `GET /app/me/checkins?days=90`, `GET /app/me/trend` | **Shipped.** The line is the person's own `mood_score` series. The engine's tier trend is used for **markers only** — a tick on days outreach was due; no score and no tier is rendered. `TrendLine` is lint-fenced to `apps/jawan`. |
| 5 · Consent panel | `/me/consent` | `GET /app/consent`, `POST /app/consent`, `POST /app/consent/withdraw/{bundle_id}` | **Shipped.** Six unbundled scopes, purpose line, data categories and retention days per card; grant and withdraw are the same one tap from the same place. Withdrawal additionally purges that scope's queued rows (`purgeQueueForTables`) and blanks its cached reads (`BUNDLE_TABLES` / `BUNDLE_CACHE_KEYS` in `app/lib/cache.ts`). |
| 6 · Who viewed my data | `/me/receipts` | `GET /app/who-viewed`, `GET /app/notifications` | **Shipped.** Role chip, timestamp, purpose string; `unmask.grant` / `identity.read` / `break_glass.open` get their own sentence. Notifications render above the timeline. **Access duration is not rendered** — the audit event carries no duration field. |
| 7 · Battle buddy | `/welfare/buddy` | `GET/POST/DELETE /app/buddy`, `POST /app/buddy/state` | **Shipped.** Pair by buddy code, coarse state segmented control, unpair behind a confirm. SOS notifies the buddy and surfaces 14416. |
| 8 · Unit pulse | `/welfare/pulse` | `POST /app/pulse`, `GET /app/pulse/me` | **Shipped.** Four fixed facets, 1–5, one rating per member per ISO week. The aggregate is not readable from this app at all — `GET /aggregates/unit/{id}/pulse` is the commander surface. |
| 9 · Settings | `/me/settings` | none (local) | **Shipped.** Language toggle, sync status (queued / offline / synced / last-synced / conflicts / rejected-with-reason), helpline, clear-this-device, sign out. Voice prompts are **not** a setting — no recorded prompts exist to toggle. |

**Offline machinery.** `web/packages/sync` — IndexedDB (`saarthi-offline`, stores `meta` / `queue` /
`checkIns` / `cache`), append-only outbox, per-item `client_uuid`, batches of 25, oldest-first, backoff
5 s → 30 s → 5 min retrying forever, one engine per tab. Only an *explicit* `navigator.onLine === false`
counts as offline, because an absent `onLine` in an old WebView would otherwise park the queue silently.
Service worker registers in **production builds only** (`app/sw-register.tsx`); dev unregisters any SW a
production session left behind. 48 web tests pass, including TC-601…605 against a real IndexedDB
(`fake-indexeddb`), not a mock of our own queue.

**Stubs and thin spots — what a demo must not claim.**
- **Pay slip is a demo stub.** `GET /app/payslip` returns `{available: false, source: "demo_stub",
  reason_key: "roster.demoNote"}` with the previous month and the person's rank — no amount, no
  breakdown, because there is no pay proxy behind it. The home card renders `roster.payslip.unavailable`
  ("Pay slip comes with the HRMS release" / "Pay slip HRMS release ke saath aayegi") rather than the
  server's `reason_key`, which the screen currently ignores. The response *shape* is real so APP-002 swaps
  the adapter, not the screen (`self_service.py` `my_payslip`).
- **Roster and leave are real reads of kv's ingest tables, not of an HRMS.** `GET /app/roster` and
  `GET /app/leave` query `HrDutyRoster` and `HrLeaveRecord` directly — the tables the F09 generator and the
  CSV ingest fill — and label themselves `source: "hrms_proxy"`. Leave entitlement is a hard-coded 30 days
  and the balance is derived from sanctioned rows; there is no live HRMS behind either.
- **`app/lib/mock-hr.ts` is a degraded-mode fallback, not the adapter this document used to describe.** It
  is used for exactly one case: a first run that has never reached the server and so has nothing cached.
  The screen prints `roster.demoNote` whenever it is on screen.
- **Free text is captured and then dropped server-side.** The sheet collects an optional note and
  `toCheckInWire` puts it on the wire as `free_text`, but the `checkins` table has no such column and
  `_apply_checkin` never reads the field. So the promise "raw free text is visible to no one in the chain"
  holds trivially today — nothing is stored. Either persist it under `checkin` consent with the F06 access
  path, or stop collecting it; leaving a field that silently evaporates is the worst of the three.
- **No passive-signal capture UI exists.** The `passive` consent bundle, the `passive` queue table, the
  purge path and `POST /app/passive` all exist, but nothing in `apps/jawan` ever enqueues a `passive` row —
  see [F03](F03-on-device-signals.md) Implementation status.
- **Canteen, grievance and family-welfare cards are `coming.soon` labels** with no route behind them.

## Definition of done
- [x] 10-second check-in completes offline; queued sync verified with zero duplicates. — `sync.test.ts`
      TC-601…605 pass against a real IndexedDB: queue-then-sync-once, 72-item batched resume, replayed
      `client_uuid` never creating a second row, conflict reported not dropped, kill-mid-drain losing
      nothing. The server half is asserted in `test_client_surface.py` (replayed batch → all `duplicate`).
      **Not yet verified on a physical low-end Android device or across a real airplane-mode toggle** — no
      device lab (coverage-report.md §6). The claim proven is the logic, not the handset.
- [ ] All instruments ship with adapted `hi`/`en` strings + **recorded voice prompts**; adaptation review
      signed off. — Not done, and not close. Every instrument is `adaptation: "review_pending"`; the §3
      pipeline in clinical-instruments.md has not been run; there are no recorded voice prompts of any kind
      in the repo. Also note the target is four instruments, not six.
- [x] Unbundled consent works end to end. — Six bundles grant and withdraw through `/app/consent*`, and
      `test_privacy.py::test_silent_withdrawal` asserts the commander payload after a withdrawal carries no
      consent or withdrawal field. **Partial:** that test checks one commander surface, not "zero
      command-visible trace on every F08 endpoint"; the stronger sweep is unwritten.
- [x] Access receipts render every real audit event (including unmask). — `/app/who-viewed` reads the audit
      log itself and `/me/receipts` renders `unmask.grant`, `identity.read` and `break_glass.open` with
      their own sentences. The "within one sync cycle" latency is untimed.
- [x] Unit pulse aggregate suppresses cells with < 5 contributors server-side. — `unit_pulse_aggregate`
      returns `{n: null, mean: null, suppressed: true}` per facet below `settings.k_anonymity`, with no
      interpolation and no partial mean; a tiny unit stays suppressed in
      `test_security_hardening.py` (TC-450b) and `test_rbac_enforcement.py`.
- [x] All strings via i18n keys. — Enforced in CI by `lint-boundaries.mjs` rules 5–7 (no user-facing JSX
      literal, en/hi parity across 495 keys, every `t()` key resolves).
- [ ] Devanagari line-height rule holds (design.md §3). — The rule **ships**
      (`[data-locale="hi"] body { line-height: var(--sa-line-height-hi) }` in `globals.css`, plus the Noto
      Devanagari font stack in the tokens), but it is **unexercised**: `hi.json` contains no Devanagari, so
      nothing in the running app puts a matra on screen for it to hold. Unticked because "the CSS exists" is
      not the same claim as "it holds" — it becomes verifiable the moment a Devanagari string set lands (see
      the Hindi convention note above).
- [ ] Check-in measured at ≤ 3 taps in a phone browser. — The steady-state path is card → emoji → submit,
      three taps by inspection of `CheckInSheet.tsx`; the **first ever** check-in adds a fourth, the inline
      consent checkbox, which is deliberate (consent before capture). Nobody has measured either on a
      handset. Unticked until someone does.

## Links
[ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [F03](F03-on-device-signals.md) · [F04](F04-risk-rules-engine.md) · [F05](F05-intervention-engine.md) · [F08](F08-privacy-safety-architecture.md) · [adoption-strategy.md](../product/adoption-strategy.md) · [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) · [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md)
