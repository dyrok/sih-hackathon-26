# F07 — Commander Dashboard (aggregate-only welfare planning)

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-14 in [prd.md](../product/prd.md) (FR-19 aggregate feeds the morale index) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
Give commanders a planning instrument, not a policing tool: unit-level aggregates (k ≥ 5, no names), leading-vs-lagging indicators, a what-if deployment simulator, and a computed morale index — so welfare decisions rest on evidence instead of guesswork, and attrition pressure becomes visible before it compounds (PS expected benefit: improved retention / organizational resilience). The architectural firewall ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)) is a property of this app's API surface: **no individual-row UI pattern exists here at all**, and no endpoint accepts a personnel ID for welfare data.

## User-visible behavior (screen by screen)
1. **Unit heatmap.** Grid of battalions/companies; each cell reads "% elevated fatigue" in welfare care language — "3rd Bn, 22% elevated fatigue" (`heat.cell.label`) — colored by the design.md ladder states, never violation stamps. Cells with fewer than 5 contributors render suppressed with a quiet `k < 5` marker and a one-line explainer (`heat.cell.suppressed`).
   - Drill-down ends at company level; there is no person below it, in any view, ever.
   - The cell metric is the share of contributors above their own elevated-fatigue threshold (F04), not an absolute score.
2. **Morale index.** A computed 0–100 index per unit per week, assembled from the anonymous unit pulse (F02, FR-19) plus aggregate signal trends — labeled as a computed index, not a survey or an officer's opinion. Components (pulse mean, fatigue %, trend deltas) are visible on tap.
3. **Leading vs lagging.** Two side-by-side columns. The teaching point is acting on the left column; the columns always render together.
   | Leading (actionable now) | Lagging (outcomes) |
   |---|---|
   | Duty-streak distribution across the unit | Red flags opened this period |
   | Leave-cancel rate | Interventions started |
   | Sleep-trend deltas (aggregate only) | Median time-to-counsellor-contact |
   | Deployment-length exposure | Outcome codes from F06 (aggregate) |
4. **What-if simulator.** Pick a unit, adjust scenario inputs (extend deployment, grant a leave block, rebalance night duties) → projected fatigue-index delta: "Extend Coy B deployment by 30 days → projected fatigue index +18%" (illustrative demo line). Projection re-runs the rules engine's own factor math on the scenario; assumptions and weights render alongside the result. It is not ML (ADR-0001) and it never touches live scores.
5. **Attrition forecast.** Unit-level forward trend of the composite indicator with its drivers listed (fatigue, leave denial, family-separation index) — a rotation-planning input, not a verdict on anyone (PS expected benefit #6: improved retention).
6. **My check-in.** The commander's own private 10-second check-in — the identical CheckInCard from F02, under their own token. Officer-first rollout ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)) requires command to take the check-in publicly; commanders' aggregate is also k ≥ 5.

## Data model (fields, units, consent tags)
| Table | Key fields |
|---|---|
| `aggregate_cell` | `unit_id`, `period`, `contributor_count` (k), `pct_elevated_fatigue`, `mean_stress_slider`, `sleep_trend`, `leave_cancel_rate` — null/suppressed when k < 5 |
| `morale_index` | `unit_id`, `week`, `score` (0–100), `components` (pulse_mean, fatigue_pct, signal_trends) |
| `simulation_run` | `run_id`, `unit_id`, `scenario_params`, `projected_deltas`, `assumption_snapshot`, `created_by`, `expires_at` |
| `attrition_forecast` | `unit_id`, `horizon_weeks`, `index`, `drivers[]` |

There is **no** table, view, or query path joining a pseudonym to this role. Aggregates are computed in the aggregation service from pseudonymized data; differential-privacy noise has a reserved home here post-v1 (ADR-0003). Participation is visible only as a rate, never as a list.

Suppression semantics (enforced in the aggregation service; mirrored here for testers):
- any cell with `contributor_count < 5` returns a `k < 5` state and no numbers — no interpolation;
- suppression composes: differencing two allowed aggregates can never reconstruct a suppressed cell;
- participation smoothing (FR-17): withdrawal cannot be read out of a shrinking denominator;
- suppression applies identically to heatmap, morale components, indicators, forecast, and any export.

Demo-loop usage (ties to the architecture runtime view): the scripted persona's Red flag plays out in the counsellor console (F06); the commander screen simultaneously shows only "3rd Bn, 22% elevated fatigue" — the same event, two tiers, zero leak. That juxtaposition is the firewall, demonstrated live.

## API surface (endpoints, role-scoped)
Role `commander`. The firewall is server-side: route-level rejection (HTTP 404 + audit entry) of any request that parameterizes a personnel ID against welfare data.
- `GET /v1/commander/units/{unit_id}/aggregate` — k ≥ 5 enforced in the aggregation service, not the client
- `GET /v1/commander/units/{unit_id}/indicators` — leading/lagging pair
- `GET /v1/commander/units/{unit_id}/morale` · `GET /v1/commander/attrition-forecast`
- `POST /v1/commander/simulations` — returns deltas + persisted assumption snapshot
- `POST /v1/me/checkins` — commander's own check-in (same F02 endpoint, own-token scoped)

## States (idle/loading/empty/error/offline)
- **Empty/suppressed:** `k < 5` cells render their explainer state — never styled as an error.
- **Loading:** per-cell skeletons; the grid stays navigable during refresh.
- **Error/stale:** last-known aggregates shown with "data as of <timestamp>" (`aggregate.stale`); a failed simulation never mutates the live heatmap.
- **Offline/LAN:** on-prem deployable (NFR-03); a brief outage = reconnect banner with last-known aggregates, no blank screen.
- **Simulation edge:** scenario inputs outside the engine's validated ranges are rejected with the valid range shown; no silently clamped nonsense projections.
- **Refresh:** aggregates recompute on a fixed period, not on poll — the UI states its data age rather than pretending to be live.

## Privacy notes (what this feature must never do)
- Never render, store, cache, or export an individual name, pseudonym, or score — aggregate export only, k-filtered server-side before anything leaves the API.
- Never expose participation or non-participation identities; participation rate is the only participation datapoint.
- Never let silent consent withdrawal (FR-17) change what commanders see — aggregate denominators are smoothed so withdrawal cannot be inferred from a shrinking cell.
- Never alert commanders about individuals — alerts route to the counsellor console (F06) only.
- Never attach simulation or forecast output to a person; scenario objects carry unit IDs exclusively.
- Never repurpose this surface for readiness scoring that feeds ACR/appraisal, and never order unit ranks such that the bottom unit reads as a punishment list — framing stays welfare-planning (F08 anti-goals).

## Out of scope / non-goals
Person-level drill-down of any kind; real-time "live ops" monitoring; individual alerting; ML-based forecasts (v1 is rule-based projection); differential-privacy noise (reserved, post-v1); commander-vs-commander comparison; mobile app for commanders in v1 (web console only; their own check-in lives in the mobile app).

## Definition of done
- [ ] Fuzz test: every commander endpoint called with a personnel-ID parameter returns 4xx and writes an audit entry; the codebase contains no individual-row component for this role (checked by component inventory).
- [ ] All cells with k < 5 suppressed server-side across heatmap, morale, indicators, forecast, and aggregate export.
- [ ] What-if simulator reproduces the rules-engine projection function within stated assumptions; assumption snapshot persisted with each run.
- [ ] Demo loop shows the "3rd Bn, 22% elevated fatigue" line with zero names on any screen, at any zoom level of the demo.
- [ ] Morale index components documented and rendered — computed index, not a survey.
- [ ] Commander's own check-in recorded under their own token and invisible to everyone else (receipt visible only to the commander).

## Links
[ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [F01](F01-hr-signal-engine.md) · [F02](F02-jawan-app.md) · [F05](F05-intervention-engine.md) · [F08](F08-privacy-safety-architecture.md) · [rbac-matrix.md](../compliance/rbac-matrix.md) · [security-model.md](../compliance/security-model.md) · [design-client-apps.md](../architecture/design/design-client-apps.md)
