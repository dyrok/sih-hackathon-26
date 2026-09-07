# ADR-0005 — Offline-first, low-end Android, icon-first multilingual UI

> Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)

## Decision
The jawan app targets **low-end Android (API 26+)**, is **offline-first** (SQLite queue + opportunistic sync), uses **icon-first UI with voice input** for mixed literacy, and ships **Hindi + English** (regional languages via i18n keys later).

## Context
Deployments have bad connectivity; literacy and language vary across CAPF units. This is a real operational constraint named on the board as "real constraint, real marks" — judges reward it and competitors routinely skip it.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Offline-first RN/Expo (chosen)** | Works anywhere; matches user reality; fast on cheap phones | Sync-conflict handling needed |
| Online-only | Simpler | Unusable in deployment zones; demo hole |
| iOS parity | — | Wrong platform for CAPF demographics; skip entirely |

## Consequences
- Check-in capture must never require network; sync is invisible and resumable.
- All strings through i18n keys (`en`, `hi`); voice prompts recorded, not just text.
- Android-only for v1; iOS explicitly out of scope.
- Usability testing protocol ([usability-testing.md](../../quality/usability-testing.md)) must include low-literacy users.

## Links
[ADR-0004](0004-roster-app-first-adoption.md) · [design.md](../design/design.md) · [F02](../../features/F02-jawan-app.md)
