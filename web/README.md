# SAARTHI Web (bun workspace)

Client apps per ADR-0006 (web consoles: Next.js + bun) and the team's web-first decision:

| App | Role | Port |
|---|---|---|
| `apps/jawan` | Jawan web app (mobile-first PWA, offline queue) | 3100 |
| `apps/counsellor` | Counsellor console | 3200 |
| `apps/commander` | Commander dashboard (aggregates only) | 3300 |

Shared packages: `tokens` (design tokens → CSS vars), `i18n` (en/hi dictionaries), `ui` (shared components), `sync` (IndexedDB queue + client_uuid), `api` (role-scoped typed clients).

## Commands

```bash
bun install                        # from web/
bun run --cwd apps/jawan dev       # or: bun run dev:jawan
bun run --cwd apps/jawan build
```

Backend base URL: `NEXT_PUBLIC_API_BASE` (default `http://127.0.0.1:8000`).

## Hard rules (enforced in code)

- All user-facing strings via `@saarthi/i18n` keys (en + hi). No literals.
- No hardcoded OKLCH outside `@saarthi/tokens`.
- Path lint: `apps/commander` may never import `@saarthi/api/counsellor` or `@saarthi/api/jawan`.
- Commander UI contains no individual-row component.
- TrendLine lives only in `apps/jawan` — never in the consoles.
