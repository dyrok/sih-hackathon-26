# Adoption Strategy — "Police wala kyu hi use karega"

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05

## The question we must survive

The team's own hard question, from the Figma board: *"India mai log therapy nahi jate — police wala kyu hi use karega?"* A named mental-health app in a uniformed force is dead on arrival: stigma makes the icon itself a social risk. So the answer is not better marketing — it is a different product shape.

**One line:** Do not ship a mental-health app. Ship the app they already need, with wellness riding inside it ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)).

## Strategy 1 — Ride inside the roster app

- v1 home screen is **duty roster, leave application, pay slip, canteen, grievance, family welfare schemes** — things opened daily because they are personally useful.
- The 10-second check-in is a calm card on that home (`home.checkin.card`): "Aaj kaisa laga? (10 second)" — no badge, no guilt streak counter ([design.md §4](../architecture/design/design.md)).
- Adoption ask = zero: the habit already exists; the check-in borrows it. Even a jawan who never taps check-in still gets value, and the HR signal layer works at **zero participation** ([FR-01](../features/F01-hr-signal-engine.md)).

## Strategy 2 — Never call it therapy

- Framing: **fitness for duty + parivaar (family) welfare**. The cultural workaround that lets a uniformed man tap the button in front of peers.
- Copy register: `state.green.label` "Sab theek" / "All good" — care language, never "risk colors"; screeners always carry "Ye jaanch salahn hai, nidan nahi" / "This is reflection support, not diagnosis" ([design.md §8](../architecture/design/design.md)).
- Ban list: "therapy", "counselling app", "mental health" in app-store-facing naming, icons, or onboarding copy.

## Strategy 3 — Officer-first rollout

- **Commandants take the assessment publicly first.** Destigmatise top-down or it does not happen: if the CO's dot fills on the trend line, the constable's tap is normalised.
- JCOs are briefed as *users*, not enforcers; the buddy tier ([FR-09](../features/F05-intervention-engine.md)) runs through peers, not through the chain of command.

## Strategy 4 — Reward units, never individuals

- Welfare budget, facility upgrades, and recognition go to **units**. Individual incentives become coercion — a reward attached to *your* score turns honest check-ins into performance.
- Unit rewards also match the unit-aggregate data tier: what command can see is what command can reward ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).

## Anti-patterns (deliberately not built)

| Anti-pattern | Why it fails |
|---|---|
| **Streak rewards** — "check-in streak gives leave priority" | Coercive; poisons data quality; every streak becomes performative "sab theek" |
| Participation leaderboards / visible ranks | Same coercion, now peer-enforced |
| Guilt counters, red missed-day badges | Punitive iconography; contradicts welfare register |
| Check-in completion reported to command | Any command-visible participation signal is a surveillance tell |

## Non-participation is costless

- Skipping the check-in contributes **zero** priority points, zero status loss, zero flags by itself ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)).
- Consent withdrawal is silent — invisible to command, or the withdrawal itself becomes the signal nobody will risk ([FR-17](prd.md#2-functional-requirements)).
- Voluntary data enriches the risk engine; it never gatekeeps anything the jawan otherwise needs (roster, leave, pay slip all work without it).

## How adoption feeds data quality

Under-reporting is the norm — "sab theek" is the default answer — so the design assumes it instead of fighting it:

1. **HR signals need no participation** — days-since-leave, circadian disruption, family separation index derive from records the force already keeps.
2. **Masking is a finding, not a failure** — "I'm fine" + 4h sleep + 60 duty days + 2 cancelled leaves raises a discrepancy flag ([FR-07](../features/F04-risk-rules-engine.md)).
3. **Per-person baselines** — thresholds compare the jawan to their own 90-day norm, not to peers ([FR-05](../features/F04-risk-rules-engine.md)).
4. Voluntary check-ins then *sharpen* an already-working loop; the loop degrades gracefully without them.

## Rollout sequence (pilot → scale)

1. **Seed unit** — one battalion, commandant onboarded first (Strategy 3); roster/leave/pay-slip screens live before any check-in promotion.
2. **Weeks 1–2** — utility only. The app earns the daily habit before it asks for wellness data.
3. **Weeks 3+** — check-in card appears on home; the commandant takes the first check-in in unit durbar; buddy tier switched on.
4. **Review points** — participation bias and the punitive-outcome question checked at every welfare review; negative findings pause promotion, they are never hidden.

## Measuring adoption honestly

- Pilot target: voluntary participation ≥ 30% of unit — a **reasoned estimate**, not evidence ([prd.md §4](prd.md#4-success-metrics-pilot--defined-upfront-no-invented-numbers)).
- Also tracked: participation bias (who checks in vs. who doesn't), consent-withdrawal rate, and the negative-outcome question — *"did anyone get punished because of this system?"* — monitored as a KPI with target **0** ([impact-and-metrics.md](impact-and-metrics.md)).

## Links

[ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [personas.md](personas.md) · [F02](../features/F02-jawan-app.md) · [F05](../features/F05-intervention-engine.md) · [usability-testing.md](../quality/usability-testing.md)
