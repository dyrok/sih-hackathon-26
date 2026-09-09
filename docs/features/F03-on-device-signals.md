# F03 — On-device signals (voice prosody + passive wellness)

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Maps to: FR-03 in [prd.md](../product/prd.md) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
Add autonomic and behavioral signal to the check-in without becoming surveillance. Voice prosody runs **entirely on the device** ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)): raw audio never leaves the phone — not even persisted on it — which upgrades "tone recognition" into a stress indicator rather than a wiretap. Passive signals (HRV, sleep, resting HR, 3 a.m. screen time) are a separate scope, opt-in, off by default, withdrawable on its own. HRV is the gold-standard autonomic stress marker; everything here is a *signal feeding per-person baselines*, not a diagnosis. **Status:** the voice half is built; the passive half is one consent bundle and a server-side table with no collector behind it yet, so read every passive claim below as design intent unless it says otherwise (screen 2 and Data model say exactly where the line falls).

## User-visible behavior (screen by screen)
1. **Voice check-in capture.** *Shipped* — `VoiceCapture` inside the check-in sheet (F02 screen 2), gated on the `voice` consent bundle. Tap the mic → live waveform → stop (or auto-stop at 30 s) → keep / discard / re-record. The indicator is honest: "Aapki awaaz phone se bahar nahi jaati" (`voice.privacy.line` / "Your voice never leaves this phone"), with `voice.explain` naming what is measured. The user-initiated check-in is the only trigger; there is no background, ambient, or scheduled recording path in the codebase. **Correction:** there is **no live transcription** and there never will be on this path — a transcript is a content artefact, and producing one would require exactly the audio buffer the design refuses to create. Read `voice.privacy.line` as the whole promise.
2. **Passive data consent card.** *Consent shipped, capture not.* `/me/consent` carries one `passive` bundle — one toggle, labelled "Rest and screen-time signals" (`consent.scope.passive`), default off, with its purpose line, data categories and retention days. The **per-signal** toggles this section described (`passive.scope.hrv/.sleep/.rhr/.screen`) do not exist, and neither does any capture surface: nothing in `apps/jawan` reads Health Connect, offers manual entry, or enqueues a `passive` row — grep for `passive` in `web/apps/jawan/app` returns only the consent-to-queue-table map. The server side is real (`POST /app/passive`, the `passive_features` table, the expiry job, the sync gate); the collector is **not implemented as of 2026-09-09**.
3. **Data settings.** *Shipped, split across two screens.* Withdrawing a scope at `/me/consent` is one tap, takes effect immediately, purges that scope's queued-but-unsynced rows on the device and blanks its cached reads; "clear saved data on this device" at `/me/settings` wipes every local store. Withdrawal is silent to command (FR-17). There is no separate "pause without withdrawing" control — pausing *is* withdrawing, and re-granting is the same one tap.
4. **Shared-data summary.** *Shipped* — `/me/signals`, from `GET /app/signals/summary`. Per scope: rows held, oldest expiry, whether the scope is on. Raw self-reports expire at 90 days; the trend persists (FR-18). The load-bearing line on the screen is `signals.noAudio`.

## Data model (fields, units, consent tags)
`voice_feature_vector` — extracted in memory during check-in, then batched into the sync queue:
| Field | Unit / range |
|---|---|
| `f0_mean`, `f0_sd` | Hz |
| `speech_rate` | syllables/sec |
| `pause_count`, `pause_total` | count / seconds |
| `voiced_ratio` | 0–1 |
| `loudness_var` | dB variance |
| `jitter`, `shimmer` | % / dB |
| `duration_s` | 5–30 s gate |
| `model_version`, `schema_version` | strings — the contract with F04 |

`voice_feature_vector` ships as the `voice_feature` table (`backend/app/models.py`), column for column as
above plus `pseudonym_id`, `recorded_at`, `expires_at`, `purged`. The exclusions below are enforced by the
absence of columns, not by convention.

`passive_daily` — *this is the design target, not what shipped.* The intended row is `date`,
`hrv_rmssd_ms?`, `resting_hr_bpm?`, `sleep_min?`, `screen_time_night_min?`, `unlock_count_night?`, `source`
(health_connect / manual / watch), with manual entry range-validated server-side (implausible values
rejected with a friendly retry, never silently coerced). **As of 2026-09-09 the `passive_features` table
carries `pseudonym_id`, `recorded_at` and a single `sleep_hours_proxy` float** — no HRV, no resting HR, no
screen-time, no `source`, and no range validation beyond the Pydantic float. Nothing writes to it from the
app (see screen 2) — the rows that exist come from `app/seed.py`. Treat every HRV claim in this document as
a hypothesis about a signal that is not yet collected.

**Consumption, so nobody over- or under-claims the loop.** `PassiveFeature.sleep_hours_proxy` **is** read by
the rules engine: `app/risk/scorer.py` merges it with self-reported `sleep_hours` into one sleep series for
the per-person baseline, and the presence of any passive row adds `"passive"` to the score's `sources` list,
which is what raises triangulation confidence. `VoiceFeature` rows, by contrast, are **written, shown back
to the person via `/app/signals/summary`, and expired — and read by nothing else**. No scorer, no rule and
no aggregate touches them as of 2026-09-09. That is consistent with ADR-0002's "weighted low in v1", but
"low" currently means zero, and saying so is better than implying the loop is closed.

Consent tags: `voice` and `passive` are separate unbundled scopes (F02 consent model). No audio file, transcript-audio pair, or raw waveform is ever stored anywhere; the sync payload is the vector only. No fine-grained timestamps beyond the owning check-in (limits re-identification).

What is deliberately **not** in the vector (identity- and content-capable fields are excluded by schema, not by convention):
- no speaker-embedding or voice-print column (blocks voice biometrics even accidentally);
- no transcript text, no word counts, no content-derived features — content was to live only in the F02 free-text field under `checkin` consent, and as of 2026-09-09 that field is not persisted at all (F02 Implementation status), so no free-text content exists on the server either;
- no device fingerprint, no location, no fine timestamps;
- no cross-check-in accumulation on the device beyond the unsynced outbox queue.

## API surface (endpoints, role-scoped)
Role `jawan`; subject = the token's own pseudonym — no route here accepts a subject selector. The `/v1/signals/*`
sketch that stood in this section is **superseded**: F03 has no endpoints of its own any more. Both signal
kinds ride F02's one batched outbox drain, which is what makes "queued offline, sent later, never
duplicated" a single mechanism rather than three. Verified against
`backend/app/api/routers/{self_service,app_data,privacy}.py` and `web/packages/api/src/jawan.ts` on 2026-09-09.

- **Voice feature vectors** → `POST /app/sync` with `table: "voice"`. The payload *is* the vector
  (`f0_mean`, `f0_sd`, `speech_rate`, `pause_count`, `pause_total`, `voiced_ratio`, `loudness_var`,
  `jitter`, `shimmer`, `duration_s`, `model_version`, `schema_version`, `recorded_at`). Idempotent by
  `client_uuid`; gated on the `voice` consent bundle at **sync** time, so a row captured before a withdrawal
  is reported `dropped_no_consent` and never written. Handler: `self_service.py` `_apply_voice`.
- **Passive daily rows** → `POST /app/sync` with `table: "passive"`, or `POST /app/passive` for a direct
  online write (`app_data.py`). Both gated on the `passive` bundle, both day-granular.
- **"What does the server hold about me"** → `GET /app/signals/summary`. Per scope: `rows_held`,
  `oldest_expiry`, whether the scope is currently granted, plus `raw_ttl_days` and two flags that are
  hard-coded `false` because the schema makes them unrepresentable — `raw_audio_held` and
  `transcripts_held`. Rendered at `/me/signals` in the jawan app, under the line
  `signals.noAudio` ("No recording and no transcript is stored anywhere.").
- **Withdrawal** → `POST /app/consent/withdraw/{bundle_id}` with `bundle_id` `voice` or `passive`, plus a
  **device-side purge**: `/me/consent` calls `purgeQueueForTables(BUNDLE_TABLES[id])`
  (`web/apps/jawan/app/lib/cache.ts` maps `voice → ["voice"]`, `passive → ["passive"]`) and blanks the
  cached `/app/signals/summary` read. There is no `DELETE /v1/signals/{scope}`; withdrawal stops future
  ingestion and clears the device, and the 90-day expiry job takes care of what the server already holds.
- **Not a route:** nothing in this feature reads another principal's signals. Counsellor access to a
  subject's signals goes through `GET /signals/{pseudonym_id}`, which is caseload-scoped by
  `authz.assert_subject_scope` and audited (F06/F08), and appears back in F02 screen 6 as a receipt.

## Model & performance constraints

**Superseded: there is no Kotlin native module and no RN bridge.** The team's web-first decision
(2026-09-08, ADR-0007; see the F02 header) removed the native app, and with it the TFLite-class model and
the "feature struct crosses the bridge" argument. Extraction now runs **in the browser, with Web Audio**,
in `/Users/ns/code/sih-hackathon-26/web/apps/jawan/app/components/VoiceCapture.tsx`. What follows is read off that file.

**What it actually computes.** `getUserMedia({audio: true})` → `AudioContext` → `AnalyserNode`
(`fftSize` 2048, `smoothingTimeConstant` 0), sampled once per animation frame (~30–60 Hz depending on the
device). Per frame it keeps exactly three numbers — timestamp, frame dB (from RMS) and an f0 estimate — and
on stop reduces that envelope to one vector:

| Feature | How it is computed | Honest name for it |
|---|---|---|
| `f0_mean`, `f0_sd` | mean / SD of per-frame f0 over voiced frames; f0 by normalised **time-domain autocorrelation** on a 4× decimated buffer, searching 70–350 Hz, rejected as unvoiced when the best peak is under 0.3 of frame energy | frame-rate pitch track, not a pitch-synchronous one |
| `jitter` | mean absolute period difference between **adjacent voiced frames**, as a percentage of the mean period | frame-to-frame period perturbation — clinical jitter is cycle-to-cycle |
| `shimmer` | mean absolute dB difference between adjacent voiced frames | frame-to-frame amplitude perturbation, in dB, not the usual percentage |
| `loudness_var` | variance of frame dB over voiced frames | as named |
| `pause_count`, `pause_total` | unvoiced runs ≥ 250 ms that are **interior** to the utterance (a leading silence is not a pause) | as named |
| `speech_rate` | peaks in the 3-frame-smoothed dB envelope above `max(mean+2 dB, peak−12 dB)` and ≥ 120 ms apart, divided by duration | syllable-**nucleus** proxy, not a syllable count |
| `voiced_ratio` | voiced frames ÷ total frames | as named |
| `duration_s` | first to last frame timestamp | as named |

These are **approximations** of the named prosody measures, chosen for what a browser can do cheaply on a
2 GB phone — not a validated prosody model. `jitter` and `shimmer` in particular are frame-rate analogues of
cycle-synchronous clinical measures and should not be compared against published clinical norms. This is
precisely why [ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) weights voice low.
The wire contract is `model_version` (`"web-prosody-v1"`) + `schema_version` (`"v1"`), so swapping in a real
extractor changes that one file and bumps those two strings.

**The architectural guarantee the design actually rests on is not the model — it is the absence of an audio
path.** There is no `MediaRecorder`, no `Blob`, no `File`, no `URL.createObjectURL`, and no audio buffer
that outlives a single analyser frame anywhere in `VoiceCapture.tsx`. The analyser is deliberately **not**
connected to `context.destination`, so there is no playback path either; "re-record" discards and starts
over rather than replaying anything. What survives a frame is a ~30 Hz stream of three numbers, from which
neither speech nor a speaker can be reconstructed, and that envelope is dropped on stop before the vector is
shown. `releaseHardware()` stops every `MediaStreamTrack` and closes the `AudioContext` on stop, on discard,
on error and on unmount — unconditionally, because that is what turns the OS recording indicator off. A
reviewer can check this claim by grepping the file for those five API names; a lint or CI grep gate for them
is **not implemented as of 2026-09-09** (the F02 boundary lint covers roles, colour and i18n, not this).

**What the server rejects, and where** — `backend/app/api/routers/self_service.py`, `_apply_voice`:
- **unknown `schema_version`** → 400, never silently accepted. The allow-list is
  `VOICE_SCHEMA_VERSIONS = {"v1"}` at module scope.
- **any identity- or content-capable field present in the payload** → 400 naming the offending keys. The
  forbidden set is `{audio, audio_b64, waveform, transcript, speaker_embedding, voice_print}`. The
  `voice_feature` table has no column for any of them either, so the exclusion is enforced twice — by schema
  and by an explicit check. Asserted in `backend/tests/test_client_surface.py` (a `voice` item carrying
  `audio` comes back `rejected`, and the rest of the batch still drains).
- **`duration_s` outside 5–30 s** → 400. The client enforces the same window: `MIN_SECONDS = 5` /
  `MAX_SECONDS = 30`, with a sub-5-second capture refused on-device (`voice.tooShort`) and a 30-second one
  auto-stopped.

**Retention.** Voice and passive rows are now covered by the 90-day expiry job — they were not. `expire_raw`
(`backend/app/privacy/expiry.py`) nulls every prosody column on a `VoiceFeature` older than `raw_ttl_days`
and marks it `purged`, and **deletes** `PassiveFeature` rows outright. The job is idempotent and reports
`voice_purged` / `passive_purged` alongside the check-in and instrument counts; TC-454 in
`backend/tests/test_security_hardening.py` covers the passive path including the second, zero-count run. A
client-supplied `recorded_at` is clamped to the plausible offline window (`clock.clamp_capture_date`,
TC-455), so a device cannot post a future date to mint a row that never expires.

**Still true, unchanged:**
- Voice features are specified to enter the rules engine (F04) weighted low in v1 — no clinical validation in this population — and that is stated in the product, not hidden ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)). **Today "low" is zero:** nothing in `app/risk/` reads `VoiceFeature` (Data model above).
- Passive signals feed F04's per-person rolling baselines; absolute thresholds are never used on them (F04). This one is live for the single shipped column — `scorer.py` folds `sleep_hours_proxy` into the sleep baseline.
- Extraction must never block submit: the check-in sheet saves whether or not a voice vector exists, and a
  browser without `getUserMedia`/`AudioContext` degrades to the text-only sheet (`voice.unsupported`).

How each signal is expected to move the baseline (hypotheses, deliberately conservative — F04 owns weights):
- HRV (RMSSD): sustained downward deviation from the person's own 14-day baseline is the primary autonomic flag.
- Sleep duration + resting HR trend: multi-day drift combined with duty-load signals (F01) raises triangulated weight.
- 3 a.m. screen time: a proxy for sleep disruption — weighted lowest, never used alone.
- Voice features: directionally informative, weighted low per ADR-0002; never sufficient on their own to raise a tier.

## States (idle/loading/empty/error/offline)
- **Idle:** quiet status line on the consent card; no HRV/burnout numbers are shown back to the user in v1 (self-served biofeedback invites gaming and anxiety — a v2 question).
- **Loading:** live waveform with an "analysing" status line and an elapsed-second counter (`voice.analysing`), auto-stopping at 30 s.
- **Empty:** `/me/signals` renders `signals.none` for a scope holding no rows. The Health-Connect-absent → manual-entry fallback and its `passive.empty.manual` string are **not implemented as of 2026-09-09** — the key is in neither `en.json` nor `hi.json`, because the passive collector does not exist (screen 2).
- **Error:** a browser without `getUserMedia`/`AudioContext` shows `voice.unsupported` and the sheet stays text-only; a denied mic permission shows `voice.denied`; a capture under 5 s shows `voice.tooShort` and offers re-record. The check-in itself never fails because a signal failed — `save()` in `CheckInSheet.tsx` does not read the voice state at all.
- **Offline:** everything queues locally with the F02 SyncPill; extraction is fully offline by design (ADR-0005).

## Privacy notes (what this feature must never do)
- **No ambient or passive listening, ever.** The mic opens only inside a user-initiated check-in. Structurally: `getUserMedia` is called from exactly one place in the app — `VoiceCapture.start()`, behind a tap — and `releaseHardware()` stops every track on stop, discard, error and unmount, so the OS recording indicator goes out with the component. (The "native module exposes a single record API" wording is superseded with the native app; the single-call-site property is the same argument in the web build.)
- No audio persisted on-device or server-side; no voice biometrics or speaker-identification features — the vector carries no identity-capable columns, and `_apply_voice` refuses a payload that names one.
- No camera, screen capture, keystroke, or app-usage lists. The night screen-time signal is specified as an aggregate minute count behind an explicit OS permission and is **not implemented as of 2026-09-09**.
- No continuous monitoring, no streaming analysis, no location signals in v1.
- Withdrawing `voice` or `passive` purges the device queue and stops ingestion with zero command-visible change (FR-17).
- Crash logs and CI must never contain audio bytes or raw waveforms. The property holds by construction; the **lint rule and grep gate that would keep it holding are not implemented as of 2026-09-09** (see Definition of done).

## Out of scope / non-goals
Server-side prosody (rejected — ADR-0002); facial emotion recognition (F08 anti-goal — contested science, surveillance optics); voice-to-identity matching; wearable SDK integrations beyond Health Connect in v1; real-time streaming analysis; continuous background monitoring; showing biofeedback numbers back to the user; deriving standalone alerts from voice features alone in v1.

## Definition of done
- [x] Only the feature vector appears in the sync queue. — `VoiceCapture.keep()` enqueues exactly the
      `Prosody` object plus `recorded_at`; the queue row is `{table, client_uuid, captured_at, payload}` and
      the payload has no audio-capable field to carry. The server refuses one anyway
      (`_apply_voice` forbidden-key check, asserted in `test_client_surface.py`). **Split from the original
      line:** the "on an API 26 / 2 GB device" half is unticked below — no device lab
      (coverage-report.md §6).
- [x] Feature-vector schema documented and consumed behind a version guard; unknown versions rejected
      server-side. — The vector is documented in Data model above and in the Model & performance table;
      `VOICE_SCHEMA_VERSIONS = {"v1"}` rejects anything else with a 400, and every row stores both
      `model_version` and `schema_version`. **Caveat:** F04 does not yet read `VoiceFeature` rows, so
      "consumed by F04 behind a `model_version` guard" is true of the contract and not yet of a consumer.
- [x] Voice scope off → zero rows created; scope on then off → device queue purge verified. — Off: the
      `VoiceCapture` component renders a consent prompt instead of a mic when the bundle is not granted, and
      the server's `GATE` drops a queued `voice` item as `dropped_no_consent` if the scope was withdrawn
      while it sat offline. Purge: `/me/consent` calls `purgeQueueForTables(["voice"])` on withdrawal, and
      `sync.test.ts` proves the purge drops exactly that scope's rows and leaves the others. Passive behaves
      identically *by the same code paths* — but with no passive capture surface there is nothing to purge
      in practice.
- [ ] No test, log, or crash-report path writes audio bytes to disk (**lint rule + CI grep**). — The
      property holds by construction today (no `MediaRecorder`/`Blob`/`File`/`createObjectURL`/
      `context.destination` anywhere in `VoiceCapture.tsx`), but the *gate* does not exist:
      `web/scripts/lint-boundaries.mjs` has no rule for it. A property nobody enforces is one refactor from
      being false — this is the cheapest open item in the feature.
- [~] Passive rows are day-granular only; signal-ingestion events appear in F02's who-viewed receipt
      timeline. — Day-granular: **yes**, `recorded_at` is a `Date` column and `clamp_capture_date` reduces
      any client timestamp to a day. Receipts: **no**. `/app/who-viewed` filters the audit log to *viewing*
      actions (`risk.read`, `signals.read`, `identity.read`, `unmask.grant`, `break_glass.open`,
      intervention and referral actions); the subject's own `app.sync` write is audited but deliberately not
      listed, because the screen answers "who looked at my data", not "what did I send". If ingestion events
      are wanted on that timeline, that is a product decision to make explicitly, not a bug to quietly fix.
- [ ] Extraction latency bounded within the check-in budget on the reference low-end device. — **Unmeasured.
      No device lab.** The extraction is deliberately cheap (per-frame RMS plus a decimated autocorrelation
      over a 2048-sample window; the reduction to a vector is a single pass over the envelope) and it runs
      *after* stop, never on the submit path — but "cheap by inspection" is not a latency measurement on an
      API-26 / 2 GB handset, and this line stays unticked until TC-606/TC-607 are actually run
      ([usability-testing.md](../quality/usability-testing.md), coverage-report.md §6).

## Links
[ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [F02](F02-jawan-app.md) · [F04](F04-risk-rules-engine.md) · [F08](F08-privacy-safety-architecture.md) · [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) · [security-model.md](../compliance/security-model.md)
