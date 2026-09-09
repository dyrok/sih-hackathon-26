# ADR-0007 (DRAFT — for kv to review/commit) — Web-first client apps: no native binaries

> **Status: IMPLEMENTED (still a draft as a document) — the decision below is now live in code: three Next.js apps in `web/` (`apps/jawan`, `apps/counsellor`, `apps/commander`), no Expo or React Native anywhere in the tree, and offline-first carried by a Service Worker app shell plus an IndexedDB outbox. kv owns `docs/architecture/decisions/`, so this file stays here until kv commits it as `docs/architecture/decisions/0007-web-first-clients.md`; until then the *decision* is implemented and the *ADR* is unratified.**
> Drafted: neel, 2026-09-08, from the team meeting decision of 2026-09-08. Implementation verified against the tree: neel, 2026-09-09.
>
> **What changed since drafting:** nothing in the decision — the shipped tree matches this draft as written, plus two additions it did not anticipate: a `packages/instruments` screener bank, and `web/scripts/lint-boundaries.mjs`, which makes the role-isolation and no-individual-shape claims below into build-failing CI checks rather than conventions.
> Supersedes: the mobile portions of ADR-0005 (offline-first, low-end Android) and ADR-0006 (tech stack — the "Mobile: Expo/React Native" line and the `mobile/` repo layout line). ADR-0004 (roster-first) is unaffected.

## Context

The team meeting on 2026-09-08 decided the production clients are web applications, not native apps: "react wrapped inside the web browser" — a website, not a native build. Rationale discussed in the meeting:

- Zero-install rollout for uniformed personnel: a URL works on any phone, including shared/rugged devices with locked-down app stores.
- One codebase and one design system for all three surfaces (jawan, counsellor, commander), with bun tooling already mandated for the consoles.
- For the SIH prototype window (submission 2026-09-20), a web app demos faster than Expo toolchains on every judge laptop and phone.
- Native pros (on-device voice inference via Kotlin, tighter OS integration) are deferred; the web platform covers the prototype scope.

## Decision

All three client surfaces ship as Next.js web apps in one bun-workspace monorepo at `web/`:

- `web/apps/jawan` — mobile-first installable PWA (the jawan app: roster, check-in, consent, receipts). Offline-first is preserved with a Service Worker app shell + an IndexedDB outbox queue keyed by `client_uuid`.
- `web/apps/counsellor` — counsellor console.
- `web/apps/commander` — commander dashboard (aggregates only).
- Shared packages: `tokens` (design tokens JSON → CSS vars), `i18n` (en/hi dictionaries), `ui`, `sync` (queue engine), `api` (role-scoped typed clients, path-lint-enforced no cross-role imports), and — added during implementation — `instruments` (the validated screener bank).

No Expo/React Native code ships; there is no app-store binary. `data/` (synthetic data generator) is unaffected (Python).

## Consequences

- ADR-0005's "low-end Android (API 26+) + SQLite" becomes "works offline in a phone browser on a low-end Android-class device + IndexedDB + Service Worker". Its icon-first, i18n-only, voice-input, usability-testing consequences carry over unchanged.
- ADR-0006's repo layout becomes `backend/` + `web/` + `data/` (no `mobile/`). The "native modules for on-device audio" line is dropped for v1; voice capture in the browser uses Web Audio/Web Speech, and ADR-0002's "raw audio never leaves the device" still holds.
- Deferred to v2 if ever needed: on-device Kotlin prosody extraction, OS-level wearable pairing, app-store distribution. A future decision would re-litigate a native build only with concrete deployment evidence.
- Offline demo acceptance: cold-start check-in works with zero network after a first online load; airplane-mode reload serves the SW shell; queue drains idempotently on reconnect.
