# F03 — On-device signals (voice prosody + passive wellness)

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-03 in [prd.md](../product/prd.md) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
Add autonomic and behavioral signal to the check-in without becoming surveillance. Voice prosody runs **entirely on the device** ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)): raw audio never leaves the phone — not even persisted on it — which upgrades "tone recognition" into a stress indicator rather than a wiretap. Passive signals (HRV, sleep, resting HR, 3 a.m. screen time) are separate, opt-in, off by default, individually withdrawable. HRV is the gold-standard autonomic stress marker; everything here is a *signal feeding per-person baselines*, not a diagnosis.

## User-visible behavior (screen by screen)
1. **Voice check-in capture.** Every text input carries a mic affordance (design.md §6). Tap → live waveform replaces the keyboard → live transcription → keep / re-record. The indicator is honest: "Aapki awaaz phone se bahar nahi jaati" (`voice.privacy.line` / "Your voice never leaves this phone"). The user-initiated check-in is the only trigger; there is no background, ambient, or scheduled recording path in the codebase.
2. **Passive data consent card.** Lists exactly what is collected and from where: HRV (RMSSD, ms) and resting HR (bpm) via Health Connect where present, else manual entry; sleep duration (min); 3 a.m.–5 a.m. screen time (min) via the user-granted OS usage-stats permission. Each row is its own consent toggle (`passive.scope.hrv/.sleep/.rhr/.screen`), default off.
3. **Data settings.** Pause collection, withdraw a scope, purge queued-but-unsynced features. Withdrawal is instant and silent to command (FR-17).
4. **Shared-data summary.** What the server currently holds per scope, with expiry: raw self-reports auto-expire at 90 days; only derived features/trends persist (FR-18).

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

`passive_daily` — one row per local day per scope: `date`, `hrv_rmssd_ms?`, `resting_hr_bpm?`, `sleep_min?`, `screen_time_night_min?`, `unlock_count_night?`, `source` (health_connect / manual / watch). Manual entry is range-validated server-side (implausible values rejected with a friendly retry, not silently coerced).
Consent tags: `voice` and `passive` are separate unbundled scopes (F02 consent model). No audio file, transcript-audio pair, or raw waveform is ever stored anywhere; the sync payload is the vector only. No fine-grained timestamps beyond the owning check-in (limits re-identification).

What is deliberately **not** in the vector (identity- and content-capable fields are excluded by schema, not by convention):
- no speaker-embedding or voice-print column (blocks voice biometrics even accidentally);
- no transcript text, no word counts, no content-derived features — content lives only in the F02 free-text field under `checkin` consent;
- no device fingerprint, no location, no fine timestamps;
- no cross-check-in accumulation on the device beyond the unsynced outbox queue.

## API surface (endpoints, role-scoped)
Role `jawan`; subject = token's own pseudonym.
- `POST /v1/signals/voice-features` — batch, idempotent by `client_uuid`, schema-validated server-side (unknown `schema_version` rejected, never silently accepted)
- `POST /v1/signals/passive` — batch daily rows, day-granular only
- `GET /v1/signals/summary` — what the server holds per scope (feeds F02 screens 3–4 and the receipt page)
- `DELETE /v1/signals/{scope}` — withdrawal + purge of the device queue (FR-17 companion); stops ingestion for that scope

## Model & performance constraints
- Prosody extractor: small on-device model (TFLite-class), inference bounded inside the 10-second check-in budget on a 2 GB RAM / API 26 device; extraction must never block submit.
- Extraction happens in a Kotlin native module that never hands audio bytes over the RN bridge — only the feature struct crosses.
- Voice features enter the rules engine (F04) weighted low in v1 — no clinical validation in this population — and that is stated in the product, not hidden ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)).
- Passive signals feed F04's per-person rolling baselines; absolute thresholds are never used on them (F04).

How each signal is expected to move the baseline (hypotheses, deliberately conservative — F04 owns weights):
- HRV (RMSSD): sustained downward deviation from the person's own 14-day baseline is the primary autonomic flag.
- Sleep duration + resting HR trend: multi-day drift combined with duty-load signals (F01) raises triangulated weight.
- 3 a.m. screen time: a proxy for sleep disruption — weighted lowest, never used alone.
- Voice features: directionally informative, weighted low per ADR-0002; never sufficient on their own to raise a tier.

## States (idle/loading/empty/error/offline)
- **Idle:** quiet status line on the consent card; no HRV/burnout numbers are shown back to the user in v1 (self-served biofeedback invites gaming and anxiety — a v2 question).
- **Loading:** waveform "analysing" state bounded to the check-in budget; passive card shows last-synced day.
- **Empty:** Health Connect absent → manual-entry fallback row with a one-line explanation (`passive.empty.manual`).
- **Error:** model or sensor failure degrades to a text-only check-in; the check-in itself never fails because a signal failed.
- **Offline:** everything queues locally with the F02 SyncPill; extraction is fully offline by design (ADR-0005).

## Privacy notes (what this feature must never do)
- **No ambient or passive listening, ever.** Mic opens only inside a user-initiated check-in — enforced structurally (native module exposes a single record API called from the check-in flow) and reviewed, not just by policy.
- No audio persisted on-device or server-side; no voice biometrics or speaker-identification features — the vector carries no identity-capable columns.
- No camera, screen capture, keystroke, or app-usage lists; the night screen-time signal is an aggregate minute count behind an explicit OS permission.
- No continuous monitoring, no streaming analysis, no location signals in v1.
- Withdrawing `voice` or `passive` purges the device queue and stops ingestion with zero command-visible change (FR-17).
- Crash logs and CI must never contain audio bytes or raw waveforms (lint rule + grep gate).

## Out of scope / non-goals
Server-side prosody (rejected — ADR-0002); facial emotion recognition (F08 anti-goal — contested science, surveillance optics); voice-to-identity matching; wearable SDK integrations beyond Health Connect in v1; real-time streaming analysis; continuous background monitoring; showing biofeedback numbers back to the user; deriving standalone alerts from voice features alone in v1.

## Definition of done
- [ ] On an API 26 low-end (2 GB RAM class) device, a 10-second check-in with voice completes offline; only the feature vector appears in the sync queue (verified by payload inspection in tests).
- [ ] Feature-vector schema documented and consumed by F04 behind a `model_version` guard; unknown versions rejected server-side.
- [ ] Voice scope off → zero `voice_feature_vector` rows created; scope on then off → device queue purge verified; passive scopes behave identically.
- [ ] No test, log, or crash-report path writes audio bytes to disk (lint rule + CI grep).
- [ ] Passive rows are day-granular only; signal-ingestion events appear in F02's who-viewed receipt timeline.
- [ ] Extraction latency bounded within the check-in budget on the reference low-end device.

## Links
[ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [F02](F02-jawan-app.md) · [F04](F04-risk-rules-engine.md) · [F08](F08-privacy-safety-architecture.md) · [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) · [security-model.md](../compliance/security-model.md)
