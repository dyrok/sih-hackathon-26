# ADR-0002 — On-device voice inference; raw audio never leaves the phone

> Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)

## Decision
Prosody/voice-tone analysis runs **entirely on the device** inside a user-initiated check-in. Only the derived feature vector (no raw audio) is synced. No server-side audio storage. No passive/ambient listening.

## Context
The team's original brainstorm included "tone recognition from voice". Server-side audio analysis would be a wiretap in a surveillance-sensitive force context and likely illegal under DPDP 2023 purpose limitation. The board explicitly noted this upgrade path: *"This upgrades the tone recognition idea into something that is not a wiretap."*

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **On-device, opt-in, check-in only (chosen)** | No audio leaves phone; consent is genuine; works offline | Small models on low-end Android; feature-set limited |
| Server-side prosody | Richer features | Wiretap optics; DPDP purpose-limitation violation; transport risk |
| Camera/FER (rejected anti-goal) | — | Contested science (Barrett et al. 2019); covert-surveillance optics — see [F08 anti-goals](../../features/F08-privacy-safety-architecture.md) |

## Consequences
- Raw audio is never persisted, even on device; feature vectors are ephemeral in memory until sync.
- Feature vector schema (pitch variance, speech rate, pauses) documented in [F03](../../features/F03-on-device-signals.md).
- Voice features enter the rules engine weighted low in v1 (no clinical validation in this population) — honesty about this is a trust signal.

## Links
[ADR-0003](0003-two-tier-output-k-anonymity.md) · [F03](../../features/F03-on-device-signals.md) · [dpdp-2023-mapping.md](../../compliance/dpdp-2023-mapping.md)
