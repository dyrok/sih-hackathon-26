# SAARTHI Web — three apps, one bun workspace

Client layer for SAARTHI (SIH 2026 · PS 26186 · CRPF/MHA). Per ADR-0006 (Next.js + bun) and ADR-0007 (web-first: no Expo, no app-store binary), all three surfaces are Next.js apps in one bun workspace. Backend is `../backend` (FastAPI); synthetic data is `../data`.

Spec: [`docs/architecture/design/design.md`](../docs/architecture/design/design.md) (design system) · [`design-client-apps.md`](../docs/architecture/design/design-client-apps.md) (screens, routes, sync policy).

## The three apps

| App | Role | Port | What it is |
|---|---|---|---|
| `apps/jawan` | jawan | **3100** | Mobile-first installable PWA. Roster home, duty, leave, 10-second check-in sheet with voice capture, instrument flow, personal trend, unit pulse, battle buddy, consent panel, who-viewed receipts, stored-data summary, settings. Service Worker app shell + IndexedDB outbox — works with the network off. |
| `apps/counsellor` | counsellor, welfare_officer | **3200** | Console. Case queue with SLA clocks and cap state, case detail (evidence chips + risk-trend chart + timeline), dual-key unmask, break-glass, session notes, outcomes, Tele-MANAS handoff. |
| `apps/commander` | commander | **3300** | Dashboard. Unit heatmap, morale index, leading/lagging indicators, what-if simulator, attrition forecast, own check-in. **Aggregates only** — there is no individual-row shape anywhere in this build, and CI enforces that. |

Each app is a separate Next.js build. A cross-role screen is not reachable by URL because it is not in the bundle.

## The packages

| Package | What it is for |
|---|---|
| `packages/tokens` | The design system's single source of truth. `src/tokens.json` → `scripts/generate.mjs` → `dist/tokens.css` (every colour emitted twice: hex fallback first for older Android browsers, then OKLCH) and `src/index.ts` (typed export). **Never edit `dist/tokens.css` or `src/index.ts` by hand** — edit the JSON and run `bun run --cwd packages/tokens generate`. |
| `packages/i18n` | `en.json` + `hi.json` (romanised Hindi), 495 keys each, and the `useT()` hook. Every user-facing string in the product is a key here. Sets `data-locale` on `<html>`, which drives the Devanagari line-height. |
| `packages/ui` | The shared kit: `Button`, `CheckInCard`, `CareStateChip`, `SyncPill`, `BottomTabs`, `ConsoleShell`, `Sheet`/`Modal`/`ConfirmDialog`, the form primitives, `Skeleton`/`EmptyState`/`ErrorState`/`Toast`/`UndoBar`, the data-display set (`StatTile`, `SuppressedCell`, `DataTable`, `Timeline`, `FactorChip`, `Sparkline`, `Dial`, `Meter`, `Badge`), `SkipLink`, 32 icons, and the `useApi` hook. All styling is in `src/ui.css` and uses only token variables. |
| `packages/sync` | The offline outbox: IndexedDB queue, a **per-item** `client_uuid`, and a resumable idempotent drain with 5 s → 30 s → 5 min backoff. Nothing on screen ever waits for it. |
| `packages/api` | Typed HTTP clients. The root export carries only the shared surface (login, session, `getMe`); the role clients are **subpath exports only** — `@saarthi/api/jawan`, `/counsellor`, `/commander` — which is what makes the role-isolation lint enforceable. |
| `packages/instruments` | The validated screener bank (PHQ-9, GAD-7, PSS-10, ISI) with scoring, licence status and Hindi-review status. Zero invented items; ISI's item text is licence-gated and the UI says so. |

## Getting started

```bash
cd web
bun install                 # or: make setup-web  (from the repo root)
```

The apps need the backend running with demo data:

```bash
cd ..
make seed                   # deterministic demo seed
make api                    # FastAPI on :8000
```

Then, in separate terminals:

```bash
bun run dev:jawan           # http://localhost:3100    (or: make jawan)
bun run dev:counsellor      # http://localhost:3200    (or: make counsellor)
bun run dev:commander       # http://localhost:3300    (or: make commander)
```

## Commands

| Command | What it does |
|---|---|
| `bun install` | Install the workspace (run from `web/`). |
| `bun run dev:jawan` \| `dev:counsellor` \| `dev:commander` | Dev server for one app, on its port above. |
| `bun run build` | Production build of all three apps. |
| `bun run typecheck` | `tsc --noEmit` across all three apps. |
| `bun test` | Unit tests: the offline queue (TC-601…605) against a real IndexedDB via `fake-indexeddb`, the instrument bank + scoring, and the API wire format. 48 tests. |
| `bun run lint` | `next lint` in each app. |
| `bun run lint:boundaries` | **The architectural lint.** See "Hard rules" below. |
| `bun run check` | `lint:boundaries` → `typecheck` → `bun test` → `build`. Run this before pushing. |
| `bun run e2e` | Browser smoke across all three surfaces (needs the backend and all three dev servers up). Screenshots land in `e2e/shots/`. |
| `bun scripts/merge-pending-i18n.mjs` | Fold `packages/i18n/src/pending/*.json` into `en.json` + `hi.json`. |
| `bun run --cwd packages/tokens generate` | Regenerate `dist/tokens.css` + `src/index.ts` from `src/tokens.json`. |

## Configuration

| Env var | Default | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `http://127.0.0.1:8000` | Base URL of the FastAPI backend (`packages/api/src/http.ts`). Set it per app when the API is not local. |

## Demo logins

All demo accounts use the password **`saarthi`** (`backend/app/seed.py`). Seed with `make seed` from the repo root.

| Username | Role | Use it on |
|---|---|---|
| `jawan.demo` | jawan | :3100 — the DEMO-PERSONA-01 arc (Constable, 3rd Bn, 90 days of history) |
| `jawan.tiny` | jawan | :3100 — a jawan in the deliberately under-k `TINY` unit |
| `counsellor.a` | counsellor | :3200 |
| `welfare.a` | welfare_officer | :3200 — scoped to `3BN`; the second key in a dual-key unmask |
| `commander.3bn` | commander | :3300 |
| `commander.tiny` | commander | :3300 — the unit where every cell suppresses, so you can see k ≥ 5 working |
| `admin` / `auditor` / `hr.ingest` | admin / auditor / hr_ingest | API only — no console ships for these roles |

## Hard rules, and the command that enforces each

`bun run lint:boundaries` (`scripts/lint-boundaries.mjs`) runs as the **first web step in CI**, before typecheck, tests and build. It exits non-zero with a list of violations. These are not style preferences — each one is a rule that would be expensive to catch in review and, in three cases, catastrophic to get wrong.

| Rule | What fails | Why |
|---|---|---|
| **Role isolation** | an app importing another role's API subpath — e.g. `@saarthi/api/counsellor` inside `apps/commander` | the exact leak ADR-0003 exists to prevent |
| **No individual shape in the commander build** | `pseudonym_id`, `PersonRow`, `IndividualRow`, `legal_name` or `personnel_id` appearing anywhere under `apps/commander` | the F07 firewall as a client guarantee: there is no component that can render a person and no route that can navigate to one |
| **`TrendLine` is jawan-only** | the identifier `TrendLine` appearing outside `apps/jawan` | a personal 90-day trend is a private artefact. Consoles use `Sparkline` or `RiskTrendChart` instead |
| **Tokens are the only source of colour** | `oklch(` anywhere outside `packages/tokens` | a one-off colour is a colour the contrast check has never seen |
| **i18n keys only** | literal word text in JSX | an English string shipping to a Hindi-first user |
| **en/hi parity + every key resolves** | a key in one dictionary but not the other, or a `t("…")` that resolves in neither `en.json` nor a declared `pending/` entry | a missing translation must fail the build, not fall back to English silently in the field |
| **Contrast floors** | any of 11 text pairs below 4.5:1, or any of 7 non-text pairs below 3:1 — measured on the **hex fallbacks**, which is what an older Android browser actually paints | this check found the amber care chip at 2.03:1 while `design.md` claimed a 4.5:1 floor. A floor nobody measures is a wish |

Two conventions the lint cannot check, so they are on you:

- **New strings go in `packages/i18n/src/pending/<app>.json`**, shaped `{ "my.key": { "en": "…", "hi": "…" } }`, not straight into the shared dictionaries — three apps editing two JSON files is the one place parallel work reliably collides. The owner merges them with `merge-pending-i18n.mjs`. A pending key counts as declared; anything in neither place is a typo and still fails.
- **Every PR touching these trees updates the mapped doc in the same PR** (AGENTS.md rule 1). Where this README and the code disagree, the code wins and this file gets fixed.

Security itself is enforced **server-side** — k ≥ 5 suppression, the role firewall, caseload scoping, audit. The rules above are a second wall, not the wall. A client-side check is a design guarantee; it is never a security guarantee.
