# F07 — Commander Dashboard (aggregate-only welfare planning)

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Maps to: FR-14 in [prd.md](../product/prd.md) (FR-19 aggregate feeds the morale index) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
Give commanders a planning instrument, not a policing tool: unit-level aggregates (k ≥ 5, no names), leading-vs-lagging indicators, a what-if deployment simulator, and a computed morale index — so welfare decisions rest on evidence instead of guesswork, and attrition pressure becomes visible before it compounds (PS expected benefit: improved retention / organizational resilience). The architectural firewall ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)) is a property of this app's API surface: **no individual-row UI pattern exists here at all**, and no endpoint accepts a personnel ID for welfare data.

## User-visible behavior (screen by screen)
1. **Unit heatmap.** Grid of units; each cell reads its elevated-fatigue share in welfare care language — `heat.cell.label` | "{unit} · {pct}% elevated fatigue" | "{unit} · {pct}% zyada thakan" — coloured by the design.md ladder states, never violation stamps. A suppressed cell carries no number, **no bar and no tint** (a shaded bar is a value), and states why: `heat.cell.suppressed` | "Fewer than {k} people — no number is shown, by design." | "{k} se kam log — jaan-boojhkar koi number nahi dikhaya."
   - Drill-down ends at the unit; there is no person below it, in any view, ever. A cell links to that unit's morale and indicators, and nothing deeper exists to navigate to.
   - The cell metric is the share of the unit at or above Amber on the F04 ladder, not an absolute score.
2. **Morale index.** A computed 0–100 index per unit per week, assembled from the anonymous unit pulse (F02, FR-19) plus aggregate signal trends — labelled as a computed index: `morale.formula` | "A computed index, not a survey and not an opinion. Tap a component to see how it is built." | "Ye ganit se bana index hai, na survey na raay. Kaise bana, dekhne ke liye component par tap karein." Each component expands to show its own contributor count.
3. **Leading vs lagging.** Two columns that always render together — on a narrow screen they stack and keep their own headings, because a single visible column deletes the lesson: `ind.teaching` | "The left column is what you can still act on. The right column has already happened." | "Baayan column wo hai jispar aap ab bhi kaam kar sakte hain. Daayan column ho chuka hai."

   | Leading (`ind.leading`) | Lagging (`ind.lagging`) |
   |---|---|
   | `ind.lead.duty_streak` — duty streak, median days + buckets | `ind.lag.red_flags` — red flags opened (28 days) |
   | `ind.lead.leave_cancel_rate` — leave cancellation rate | `ind.lag.interventions` — interventions started |
   | `ind.lead.night_ratio` — night duty share | `ind.lag.time_to_contact_h` — median hours to counsellor contact |
   | `ind.lead.deployment_exposure` — days in high-risk posting | `ind.lag.outcomes` — recorded outcomes, by code |
4. **What-if simulator.** Pick a unit, move four validated levers, run → a projected fatigue-index delta and an elevated-share before/after, with the rules that changed and the assumption snapshot rendered beside the number. It is not ML (`sim.notMl` | "Rule-based projection, not a prediction model (ADR-0001)." | "Niyam-aadharit anuman, koi prediction model nahi (ADR-0001).") and it never touches live scores.
5. **Attrition forecast.** Unit-level forward trend of the same projected index over a 4/8/12/26-week horizon, with its drivers listed as named rules: `forecast.disclaimer` | "A rotation-planning input, not a verdict on anyone." | "Rotation planning ka input, kisi par faisla nahi."
6. **My check-in.** The commander's own private 10-second check-in — the identical `CheckInCard` from F02, under their own token. Officer-first rollout ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)) requires command to take the check-in publicly: `cmd.checkin.intro` | "Officers take the check-in first. Yours is private to you." | "Adhikari pehle check-in karte hain. Aapka aapke paas hi rehta hai."

## Data model (fields, units, consent tags)
| Table / computed object | Key fields |
|---|---|
| unit aggregate (computed, not stored) | `unit_id`, `k`, `n`, `n_suppressed`, `elevated_share`, `morale_index`, `suppressed`, `reason_key`; `cells` + `table_suppressed` only on the detailed projection |
| `unit_pulse_rating` | `pseudonym_id`, `unit_id`, `period`, `facet`, `rating` (1–5) — aggregated per facet, never read back per person by this role |
| `simulation_run` | `id`, `unit_id`, `scenario_params`, `projected_deltas`, `assumption_snapshot`, `created_by_role`, `created_at`, `expires_at` |
| attrition forecast (computed, not stored) | `unit_id`, `horizon_weeks`, `points[]`, `index_now`, `index_horizon`, `index_delta`, `drivers[]`, `assumption_snapshot` |

The unit aggregate and the forecast are **computed per request** from `identity_map` + `risk_score` + `signal_snapshot`; there is no materialised `aggregate_cell` table, so there is no stored artefact to leak or to fall out of date. `simulation_run` is the only row this feature writes, and it carries `unit_id` only — no scenario object can hold a person.

There is **no** table, view, or query path joining a pseudonym to this role. Participation is visible only as a rate, never as a list. Differential-privacy noise has a reserved home here post-v1 (ADR-0003).

**A naming caveat worth stating rather than glossing.** `n` is the count of `identity_map` rows for the unit — the **roster**, not the number of people who supplied data: `_latest_tiers` (backend/app/privacy/kanonymity.py:15-27) counts a person with no `RiskScore` as `green`. `GET /aggregates/units` publishes that value under the field name `contributor_count` (backend/app/api/routers/commander.py:123). Two consequences, both real:
- it is *why* FR-17's promise holds structurally — a consent withdrawal cannot be read out of a shrinking denominator, because the denominator never shrinks (`test_privacy.py::test_silent_withdrawal`);
- it also means a unit with low participation reads as reassuringly green, and the field name says "contributor" when the value means "posted strength". Flagged for the aggregation owner; this doc records the behaviour, not a defence of the name.

## Suppression semantics (rewritten against `backend/app/privacy/kanonymity.py`)
`k = Settings.k_anonymity`, default **5**. Four rules, in the form the code actually implements.

**1. A cell below k carries no number** — not a rounded number, not a range, not a bucket, and in the UI not a bar or a tint either. `n` itself ships only when `n >= k`; below that the response is `{"n": null, "n_suppressed": true}` and every derived figure is `null` (kanonymity.py:62-82). The same floor is applied independently on every other aggregate surface: `_cell` on the indicator means (commander.py:91-105), per-facet on the pulse (pulse.py:162-169), per weekly point on the trend (commander.py:483-497), and on `contributors` in the projection (projection.py:224).

**2. At least two cells are always hidden together — and the commander sees no cells at all.** The fix that closed TC-451/452 was structural rather than arithmetic:
- The **commander projection** (`detailed=False`) has **no per-tier frequency table**. It was removed, not suppressed. A table with one small cell is recoverable by subtraction the moment the reader knows the unit's strength, and a commander always knows their own unit's strength; suppressing cells inside the table only moved the attack around. `test_k_anonymity_3bn_ok` and `test_tc451_the_commander_projection_cannot_be_differenced` both assert `"cells" not in data`.
- The **detailed projection** (`detailed=True`, counsellor / welfare officer, who work individual cases anyway) ships its four-tier table **all or nothing**: `publishable_table` requires every tier to be either exactly 0 or two-sided-publishable, and otherwise all four cells ship as `{"n": null, "suppressed": true}` with `table_suppressed: true` (kanonymity.py:86-100). So the number of hidden cells is 0 or 4 — never 1, never 3 — and **zero-count cells are hidden with the rest**, which is precisely the hole TC-452 found (an earlier version picked its complement cell from truthy counts only, so a unit whose other tiers were empty left exactly one hidden cell beside a published total).
- The floor itself is **two-sided**: `_two_sided(count, n, k)` requires `count >= k` **and** `(n - count) >= k` (kanonymity.py:29-38). Publishing "170 of 200 are green" is fine; the same arithmetic on "199 of 200" identifies one person, and a one-sided check misses that entirely.

**3. Every derived figure over the same counts is withheld too.** `elevated_share` and `morale_index` are computed from one `publishable` flag and are therefore `null` **together**, whenever the split is not two-sided-publishable (kanonymity.py:66-68). This is the actual TC-451 exploit and it was a §4 must-pass gate failure: on the shipped demo fixture `/aggregates/unit/3BN` returned `n = 12` beside `morale_index = 0.917`, and `round(0.917 × 12) = 11` green, therefore `12 − 11 = 1` Amber — a suppressed cell of **one person**, recovered by arithmetic from a response whose own body said `suppressed: true`. A ratio over suppressed counts is the suppressed count.

**4. The response no longer names which tiers were hidden.** `suppressed_keys` — which listed the hidden tier names, and so pointed straight at the small one — is gone. `test_tc451_*` asserts `"suppressed_keys" not in d` on six hand-set tier distributions.

> **Record-keeping note.** The interim fix documented in [threat-model.md](../quality/threat-model.md) THR-17, [security-test-cases.md](../quality/security-test-cases.md) TC-451, [security-model.md](../compliance/security-model.md) and [rbac-matrix.md](../compliance/rbac-matrix.md) replaced `suppressed_keys` with a bare `suppressed_cells` **count**. The code has since gone further and removed the per-tier table from the commander projection entirely, so **no `suppressed_cells` field exists either** — those four documents are one iteration behind `kanonymity.py` and belong to other owners. Likewise `web/packages/api/src/commander.ts:34-46` still types `UnitAggregate` with `cells` and `suppressed_keys: string[]`; that type and its `getUnitAggregate()` are exported but called from no app source, so no screen renders them.

**Suppression that never lets anything through is not privacy, it is a broken screen.** A unit with both sides above the floor publishes its number: `test_tc451_a_healthy_unit_still_publishes_its_number` sets 6 green / 5 amber / 1 red and asserts `elevated_share == 0.5`, `suppressed == false`.

Composition across the other surfaces:
- **Indicators** — streak buckets smaller than k fold to `null` (a bucket of exactly 0 is kept, since it names nobody); outcome counts below k fold to `null`; `_count_cell` suppresses any count where `0 < n < k` (commander.py:268-322).
- **Trend** — each weekly point is k-filtered on its own distinct-person count, so a quiet week cannot be differenced against a busy one (commander.py:483-497).
- **Morale** — each of the three components carries its own floor; the index is the mean of whatever survives and is `null` when none do (commander.py:166-190).
- **Simulation and forecast** — suppressed whole, not per-figure, when `contributors < k`.
- `test_tc450b_every_aggregate_surface_suppresses_a_tiny_unit` sweeps `/aggregates/unit/TINY`, `.../morale`, `.../indicators`, `.../pulse`, `.../forecast` and asserts no pseudonym or name appears in any of them.

**Residual, stated plainly.** `n` is published for a unit at or above k. Because the commander projection publishes no cells at all, there is nothing to subtract it from; because the detailed table ships only when *every* tier clears the floor, `n − Σ(published)` is 0 there too. What genuinely remains is the original limit: inference across repeated slices over time is *bounded* by fixed cell definitions (unit × week) rather than prevented, and differential-privacy noise is post-v1 (ADR-0003).

Coverage: `backend/app/privacy/kanonymity.py` measures **100%** ([coverage-report.md](../quality/coverage-report.md) §3). Regression cover: `backend/tests/test_security_hardening.py::test_tc451_the_commander_projection_cannot_be_differenced` (6 distributions), `::test_tc452_the_detailed_table_never_leaves_one_cell_derivable`, `::test_tc451_a_healthy_unit_still_publishes_its_number`, `::test_tc450b_every_aggregate_surface_suppresses_a_tiny_unit`; plus `test_privacy.py::test_k_anonymity_3bn_ok`, `::test_counsellor_tier_table_is_all_or_nothing`, `::test_k_anonymity_tiny_unit_suppressed`, `::test_silent_withdrawal`.

Demo-loop usage (ties to the architecture runtime view): the scripted persona's Red flag plays out in the counsellor console (F06); the commander screen simultaneously shows only the unit's elevated-fatigue share via `heat.cell.label` — the same event, two tiers, zero leak. That juxtaposition is the firewall, demonstrated live.

## What-if simulator — what it actually computes
`backend/app/simulate/projection.py`, exposed as `POST /aggregates/simulations`.

**It re-runs the live engine, not a model of it.** For each person in the unit, `_score` (projection.py:167-171) calls `evaluate_rules(signals, ruleset)` and `aggregate(factors, ruleset)` and `tier_for(...)` — the *same functions* `app/risk/` uses to produce a real score — once on the person's actual signal vector and once on a scenario-modified copy. The difference between the two unit aggregates is the projection. Nothing is approximated and no coefficients are re-fit; it is not ML (ADR-0001).

**HR signals only, and structurally so.** `_hr_signals` (projection.py:123-130) reads `SignalSnapshot` rows for `window_end == as_of`. That table is written by exactly one function, `signals/snapshot.py::upsert_signals`, from HR records alone — leave, duty, deployments, transfers, medical and career rows. No check-in, instrument, passive or voice value ever reaches it. (The three `life_event_*` keys are gated off entirely and return `None` pending compliance sign-off, and `_hr_signals` drops nulls.) Voluntary self-report is therefore excluded by construction rather than by a filter that could be forgotten, and the assumption snapshot says so out loud: `signals_used: "hr_only"`, `voluntary_self_report_excluded: true`. A scenario can never become a channel for individual welfare data.

**The four levers, their validated ranges, and what each one moves** (`LEVERS`, projection.py:32-66; `apply_levers` :132-165):

| Lever | i18n label key | Unit | Range | Signals it moves |
|---|---|---|---|---|
| `extend_deployment_days` | `sim.lever.extend_deployment` | days | 0–180 (default 0) | `days_in_high_risk_posting` (+extend, capped at 90), `consecutive_duty_days` (+extend), `family_separation_index` (+ posting distance km × extend/30) |
| `grant_leave_block_days` | `sim.lever.leave_block` | days | 0–60 (default 0) | `days_since_home_leave` → 0, `consecutive_duty_days` → 0, for those in the block |
| `leave_block_coverage_pct` | `sim.lever.leave_coverage` | percent of unit | 0–100 (default 100) | selects who is in the leave block |
| `night_duty_rebalance_pct` | `sim.lever.night_rebalance` | percent reduction | 0–100 (default 0) | `night_shift_ratio` and `circadian_disruption_score`, scaled by (1 − pct) |

Leave-block membership is **deterministic**: the first N% of the unit by sorted pseudonym (projection.py:191-194). Rotating it randomly would make two runs of the same scenario disagree, which would make the projection untrustworthy.

**An out-of-range lever is refused with its range, never silently clamped.** `validate_scenario` (projection.py:86-107) raises `ScenarioError` for an unknown lever (listing the valid ones), for a non-numeric value, and for a value outside `[min, max]` — the message names the value, the range and the unit. `run_simulation` turns it into **HTTP 400** with that message, and the console renders the server's words verbatim (`sim.outOfRange` is literally `{message}`) rather than re-implementing the ranges. The form itself is built from `GET /aggregates/simulations/levers`, so when the engine's ranges move the screen moves with them.

**Assumptions are snapshotted with every run and rendered beside the result.** `ASSUMPTIONS` (projection.py:70-79) states eight modelling choices in plain terms — including `extend_deployment_adds_duty_days`, `leave_block_resets_home_leave_clock`, `night_rebalance_scales_circadian_linearly` and `no_person_row_is_returned` — and each run stamps them with `ruleset_version`, `engine_version`, `as_of`, `k_anonymity` and the full lever specs. The snapshot is persisted on `simulation_run.assumption_snapshot` and re-served by `GET /aggregates/simulations/{run_id}`, so an old projection can always be re-read against the rules it used. The UI renders it **open by default** (`AssumptionPanel ... defaultOpen`, `apps/commander/app/simulator/page.tsx`): the assumptions are what make the projection defensible, so they sit next to the number rather than behind a click a reader can decline to make.

**Nothing is written against a person.** The whole path writes exactly one row, `SimulationRun`, keyed by `unit_id`. No `RiskScore` is written, no per-person result is returned, and the output is a unit aggregate behind the same k floor (`contributor_count`, fatigue index before/after/delta/delta-%, elevated share before/after/delta, and `rule_deltas` — how many people each *rule* fires for, before and after). A failed or suppressed run changes nothing else on the screen.

## Attrition forecast — rule-based extrapolation, not ML
`attrition_forecast` (projection.py:288-346), served by `GET /aggregates/unit/{unit_id}/forecast?horizon_weeks=1..26`.

It is the same projection function run once per week across the horizon with `extend_deployment_days = min(180, week × 7)` and nothing else changed — i.e. it extrapolates the duty and deployment clocks that keep ticking on their own, through the live rules engine, and reports where the unit's fatigue index lands. `points[]` carries `week`, `as_of`, `index` and `elevated_share`; `index_now`, `index_horizon` and `index_delta` summarise it. **The drivers are named rules**, taken from the horizon run's `rule_deltas` (rule id, count before, count after, delta) — not feature importances and not a black box. If any run in the sweep falls below k, the whole forecast returns suppressed. There is no model, no training set, and no coefficient anywhere in the path.

Cost note, unmeasured: a 26-week horizon re-scores the whole unit 29 times (27 weekly runs plus a baseline and a horizon run for the drivers). `scripts/perf.py` gates recompute (TC-701) and the aggregate p95 (TC-702), **not** the forecast, so its latency is unbenchmarked as of 2026-09-09.

## API surface (endpoints, role-scoped)
Every commander-visible route lives under `/aggregates` — the one prefix `path_denied_to_commander` lets a commander token through (backend/app/firewall.py:46-48) — plus the self-scope `/me/checkins`. **None of them accepts a personnel or pseudonym identifier**; there is no individual-row response shape defined anywhere in `backend/app/api/routers/commander.py`. That is the structural guarantee, not a filter.

| Route | File:line | Roles | Notes |
|---|---|---|---|
| `GET /aggregates/units` | commander.py:108 | commander, counsellor, welfare_officer, auditor | the heatmap grid; a commander with a `unit_id` sees only their own unit (`_units`) |
| `GET /aggregates/unit/{unit_id}` | privacy.py:61 | same four | the raw aggregate; `detailed=True` **only** for counsellor / welfare_officer |
| `GET /aggregates/unit/{unit_id}/morale` | commander.py:148 | same four | 0–100 computed index + three components |
| `GET /aggregates/unit/{unit_id}/indicators` | commander.py:229 | same four | leading/lagging pair, always both |
| `GET /aggregates/unit/{unit_id}/trend` | commander.py:451 | same four | `weeks` 1–52, each point k-filtered on its own |
| `GET /aggregates/unit/{unit_id}/forecast` | commander.py:430 | same four | `horizon_weeks` 1–26 |
| `GET /aggregates/unit/{unit_id}/pulse` | pulse.py:135 | same four | k ≥ 5 **per facet** |
| `GET /aggregates/simulations/levers` | commander.py:363 | same four | the validated ranges the form is built from |
| `POST /aggregates/simulations` | commander.py:372 | **commander, welfare_officer only** | `ScenarioError` → 400 with the range in the message |
| `GET /aggregates/simulations/{run_id}` | commander.py:410 | same four | 404 if unknown; unit-guarded |
| `POST /me/checkins` · `GET /me/checkins` | self_service.py:804, :829 | **any authenticated role** | self-scope; see below |

`_guard_unit` (commander.py:57-59) refuses a commander who addresses a unit other than their own: **403 `commander may only view own unit chain`** (cover: `test_rbac_enforcement.py::test_dt05_commander_confined_to_own_unit_chain`, `::test_dt05_commander_units_list_shows_only_own_unit`). Every read writes an audit row (`aggregates.units.read`, `aggregates.morale.read`, `aggregates.indicators.read`, `aggregates.forecast.read`, `simulation.run`). Anything outside the allow-list is refused by the middleware with **403** and a `firewall.deny` audit entry before the handler is reached — `/signals`, `/risk`, `/interventions`, `/ingest`, `/privacy/unmask`, `/privacy/break-glass`, `/app`, `/welfare`, `/admin`, `/jobs`, `/audit`.

### `POST /me/checkins` is not an exception to the firewall
The ADR-0003 middleware denies a commander token the **whole `/app` prefix**, which is where every jawan self-service route lives. So the commander's own check-in was given a route outside it, `/me/checkins` (backend/app/api/routers/self_service.py:804), listed in `COMMANDER_ALLOWED_EXACT` with the reason written next to it (firewall.py:30-41): it is **self-scope only and takes no subject selector**, so there is no shape in which it could express a request for anyone else. `own_checkin` resolves the subject from the token via `_self_pseudonym(db, user)` and never from the body.

`_self_pseudonym` (self_service.py:99-111) mints a pseudonym on first write for any principal that lacks one — `ps_self_<user id>`. Because **no `IdentityMap` row exists for a minted self-pseudonym**, and every aggregate walks the unit through `IdentityMap` (`_pids`, `_latest_tiers`), the commander's own check-in never enters a unit aggregate, never moves a morale index, and is invisible to everyone including themselves on any other surface. The seeded commanders (`commander.3bn`, `commander.tiny`) carry no `pseudonym_id` and no `personnel_id`, so this is the path they actually take.

## Component-level guarantee (the firewall as a build rule)
The server rule is backed by a build rule. `web/scripts/lint-boundaries.mjs` walks every `.ts`/`.tsx`/`.mjs`/`.css` file under `apps/commander` and **fails the build** if any of them contains the string `pseudonym_id`, `personnel_id`, `legal_name`, `PersonRow` or `IndividualRow` (rule `commander-no-individual`, lint-boundaries.mjs:61-66). The same script also enforces role isolation — the commander build importing `@saarthi/api/counsellor` is exactly the leak ADR-0003 exists to prevent — and confines the personal 90-day `TrendLine` to `apps/jawan`, which is why the forecast screen draws its own plain `Sparkline` instead of reusing it. It runs first in CI (`.github/workflows/ci.yml`) and via `make lint` / `make check`.

That is a stronger claim than "we reviewed the components": a commander-side individual row cannot be merged, because naming a person's identifier anywhere in that app is a red build.

## States (idle/loading/empty/error/offline)
- **Empty/suppressed:** `k < 5` cells render `heat.cell.suppressed` with no number, bar or tint — never styled as an error. A unit list with nothing in it renders `units.none` | "No units are visible to this account." | "Is account ko koi unit nahi dikhti."
- **Loading:** per-cell skeletons; the grid stays navigable during refresh.
- **Error/stale:** last-known aggregates are served from the `useApi` cache with `aggregate.stale` | "Data as of {when}" | "{when} tak ka data"; a failed simulation never mutates the live heatmap, and the previous projection is left exactly as it was rather than being half-updated.
- **Offline/LAN:** on-prem deployable (NFR-03); a brief outage = reconnect notice with last-known aggregates, no blank screen.
- **Simulation edge:** scenario inputs outside the engine's validated ranges are rejected with the valid range shown, in the server's own words; no silently clamped nonsense projections.
- **Refresh:** aggregates are computed per request, and the UI states its data age (`as_of`) rather than pretending to be live.

## Privacy notes (what this feature must never do)
- Never render, store, cache, or export an individual name, pseudonym, or score — aggregate export only, k-filtered server-side before anything leaves the API, and unnameable client-side by the lint rule above.
- Never expose participation or non-participation identities; participation rate is the only participation datapoint.
- Never let silent consent withdrawal (FR-17) change what commanders see — structurally true here, because the aggregate denominator is the unit roster from `identity_map` rather than a count of respondents (`test_privacy.py::test_silent_withdrawal` asserts the commander payload carries no consent or withdrawal field at all, before or after a withdrawal).
- Never alert commanders about individuals — alerts route to the counsellor console (F06) only.
- Never attach simulation or forecast output to a person; scenario objects carry unit IDs exclusively, and no `RiskScore` is written by any path in this feature.
- Never repurpose this surface for readiness scoring that feeds ACR/appraisal, and never order unit ranks such that the bottom unit reads as a punishment list — framing stays welfare-planning (F08 anti-goals).

## Out of scope / non-goals
Person-level drill-down of any kind; real-time "live ops" monitoring; individual alerting; ML-based forecasts (v1 is rule-based projection); differential-privacy noise (reserved, post-v1); commander-vs-commander comparison; mobile app for commanders in v1 (web console only; their own check-in lives on the console's sixth screen).

## Implementation status (as of 2026-09-09)
Backend router `backend/app/api/routers/commander.py` (+ `privacy.py`, `pulse.py`, `self_service.py`); engine `backend/app/simulate/projection.py`; app `web/apps/commander` (six routes, one per screen).

| # | Screen | Shipped as | Routes it calls | Status |
|---|---|---|---|---|
| 1 | Unit heatmap | `app/page.tsx` + `app/units.tsx` (one shared units fetch for the whole console) | `GET /aggregates/units` | **done** — suppressed cells carry no number, bar or tint; care-state legend; drill-down to morale |
| 2 | Morale index | `app/morale/page.tsx` | `GET /aggregates/unit/{id}/morale`, `.../pulse` | **done** — 0–100 dial, three expandable components with their own counts, pulse facets |
| 3 | Leading vs lagging | `app/indicators/page.tsx` | `GET /aggregates/unit/{id}/indicators` | **done** — both columns in every state, folded sub-k buckets shown as suppressed |
| 4 | What-if simulator | `app/simulator/page.tsx` | `GET /aggregates/simulations/levers`, `POST /aggregates/simulations` | **done** — form built from the server's ranges, verbatim 400 message, rule deltas, assumptions open by default |
| 5 | Attrition forecast | `app/forecast/page.tsx` | `GET /aggregates/unit/{id}/forecast` | **done** — 4/8/12/26-week horizons, plain `Sparkline`, named rule drivers, assumption snapshot |
| 6 | My check-in | `app/checkin/page.tsx` | `POST` / `GET /me/checkins` | **done** — same emoji ladder and inverted heaviness slider as F02, own-token history sparkline |

Known gaps and loose ends, stated rather than rounded away:

- **`GET /aggregates/unit/{unit_id}/trend` is shipped and unused by the console.** The route and the `getUnitTrend` client both exist; no commander screen calls them. The forecast screen renders forward projection, not backward history.
- **`UnitAggregate` / `getUnitAggregate` in `web/packages/api/src/commander.ts` are stale** — they still type `cells` and `suppressed_keys`, neither of which the commander projection returns. Unused by any app source, so nothing renders them, but the type is wrong. Not mine to edit; flagged for the api-package owner.
- **`simulation_run.expires_at` is set from `Settings.jwt_expire_hours` and nothing ever reads it.** No job purges expired runs (`expire_raw` covers check-ins, instruments, passive and voice rows only). Runs are unit-scoped and hold no personal data, so this is housekeeping rather than a privacy hole — but the field currently promises a lifecycle that does not exist. Not implemented as of 2026-09-09.
- **Forecast latency is unbenchmarked** — see the cost note above.
- **No per-router coverage figure** for `commander.py` or `simulate/projection.py` is recorded in [coverage-report.md](../quality/coverage-report.md); the gates it does report that bear on this feature are `privacy/kanonymity.py` **100%**, `firewall.py` **96%**, backend overall **90%**, and TC-702 aggregate p95 **93 ms** against a 2 s gate.

## Definition of done
- [x] Fuzz test: every commander endpoint called with a personnel-ID parameter returns 4xx and writes an audit entry; the codebase contains no individual-row component for this role. — `test_firewall.py::test_tc401_personnel_lookup_always_403`, `::test_commander_denied_individual_risk`, `::test_tc403_commander_scrape_has_no_individual_score`; `test_security_hardening.py::test_tc429_path_mutations_never_leak` (traversal and encoded variants); and `test_rbac_enforcement.py::test_tc403_commander_scrape_reveals_no_individual`, which enumerates **every** route from the live OpenAPI table, substitutes the persona's `pseudonym_id` / `personnel_id` into each path parameter, calls it with a commander token and scrapes every 200 body for `legal_name`, the persona name or the pseudonym. Its sibling `::test_no_route_returns_a_server_error_for_any_role` runs the same sweep per role asserting no 5xx, because an unguarded code path is how a filter gets bypassed. The component half is enforced by `lint-boundaries.mjs` rule `commander-no-individual`, in CI.
- [x] All cells with k < 5 suppressed server-side across heatmap, morale, indicators, forecast, pulse and aggregate export. — `test_tc450b_every_aggregate_surface_suppresses_a_tiny_unit`; `kanonymity.py` at 100% coverage.
- [x] Differencing closed: derived ratios withheld whenever any contributing cell is suppressed, at least two cells hidden together (in practice the whole table), and the hidden tiers unnamed. — TC-451/452, §4 gate green.
- [x] What-if simulator reproduces the rules-engine projection function within stated assumptions; assumption snapshot persisted with each run. — it *is* the rules-engine functions (`evaluate_rules` + `aggregate`), and `simulation_run.assumption_snapshot` is written on every run and re-served by `GET /aggregates/simulations/{run_id}`.
- [x] Demo loop shows the unit's elevated-fatigue line with zero names on any screen, at any zoom level of the demo. — the commander build cannot contain a person-identifier string at all.
- [x] Morale index components documented and rendered — computed index, not a survey. — three components, each with its own contributor count and its own k floor; `morale.formula` says so on screen.
- [x] Commander's own check-in recorded under their own token and invisible to everyone else. — `POST /me/checkins`, self-scope, no subject selector; a minted self-pseudonym has no `IdentityMap` row and so never enters an aggregate.
- [ ] Forecast latency measured against a stated gate. — not benchmarked as of 2026-09-09.
- [ ] `simulation_run` retention implemented or the `expires_at` field removed. — open.

## Links
[ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [F01](F01-hr-signal-engine.md) · [F02](F02-jawan-app.md) · [F05](F05-intervention-engine.md) · [F06](F06-counsellor-console.md) · [F08](F08-privacy-safety-architecture.md) · [rbac-matrix.md](../compliance/rbac-matrix.md) · [security-model.md](../compliance/security-model.md) · [security-test-cases.md](../quality/security-test-cases.md) · [threat-model.md](../quality/threat-model.md) · [coverage-report.md](../quality/coverage-report.md) · [design-client-apps.md](../architecture/design/design-client-apps.md)
