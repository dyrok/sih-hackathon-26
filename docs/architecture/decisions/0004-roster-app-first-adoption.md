# ADR-0004 — Ship inside the roster app; never call it therapy

> Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)

## Decision
Do not ship a standalone "mental health app". Ship **the app they already need** — duty roster, leave application, pay slip, canteen, grievance, family welfare schemes — with the 10-second wellness check-in sitting on that screen. Framing is **fitness-for-duty + parivaar (family) welfare** in Hindi, never "therapy".

## Context
Board section 4 answered the team's own hard question — *"india mai log therapy nahi jate, police wala kyu hi use karega"* — with the adoption answer: ride inside the roster app they open daily. Stigma in uniformed forces makes a named mental-health app dead on arrival.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Roster-app-first (chosen)** | Daily habit already exists; zero adoption ask; welfare data rides free | More app scope; needs HRMS integration story |
| Standalone wellness app | Simple | Nobody opens it; check-in data biased toward volunteers |
| Incentivised streaks | Short-term metrics | Coercive → destroys data quality (anti-pattern on board) |

## Consequences
- Unit rewards, never individual rewards (individual incentives = coercion). Welfare budget/facility upgrades go to units.
- Officer-first rollout: commandants take the check-in publicly first, destigmatising top-down.
- Non-participation contributes zero priority points; participation is visibly costless.
- v1 prototype implements the roster + leave + pay-slip screens as the app's home, with check-in embedded.

## Links
[adoption-strategy.md](../../product/adoption-strategy.md) · [F02](../../features/F02-jawan-app.md) · [ADR-0005](0005-offline-first-low-end-android.md)
