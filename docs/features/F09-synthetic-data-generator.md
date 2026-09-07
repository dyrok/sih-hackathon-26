# F09 — Synthetic Data Generator

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-20 in [prd.md](../product/prd.md) · Spec source: ayush (distributions/realism) · [Architecture](../architecture/architecture.md)

## Purpose

"**Where is your data?**" is the first question every judge and every CRPF stakeholder will ask. The PS ships anonymized HR/deployment/wellness datasets, but a live demo needs a working system seeded *today* with realistic Indian data — names, battalions like 3rd Bn, rosters, leave patterns — or we demo an empty dashboard. The generator also feeds the test suite ([TC-501…505](../quality/test-plan.md)) and ayush's model-validation harness (ML-002) with one deterministic fixture, so tests, demos and model evaluation all run on the same data.

## Design

### Population model (~1,000 personnel)

- 4–6 battalions (3rd Bn featured); each battalion splits into companies/platoons. **No unit is ever smaller than 5 personnel** — this guarantees every commander-visible aggregate passes k ≥ 5 ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).
- Ranks (Constable → Head Constable → ASI/SI → Inspector), age 22–50, tenure correlated with rank; marital status / dependents drive the family-separation index feature (F01).
- One fixed pseudonym namespace; the identity map is generated but stored only for unmasking demo flows.

### HR event streams (90 days per personnel)

- **Leaves**: applications, approvals, cancellations — 2 cancelled leaves are a deliberate feature of the demo arc; base population sees occasional cancellations.
- **Duty rosters**: shift patterns, night-shift ratio, rotation speed (drives the circadian-disruption score), consecutive-duty stretches; normal populations hover at short stretches.
- **Deployments**: field/CI postings with varying separation length; transfers between units.
- **Training courses**: short offline events that reset duty streaks.

### Self-report series (voluntary, consent-gated)

- Daily 10-s check-ins (emoji/slider) and monthly full instruments (PHQ-9, GAD-7, PSS-10, ISI) with validity-scale items — value ranges mirror the instrument specs in [F02](F02-jawan-app.md).
- Participation is a parameter (default aligned to the PRD's ≥ 30% voluntary-adoption target); non-participants generate HR/passive signals only — the dashboard must still look alive.

### Passive-signal series

- Derived feature vectors only (sleep proxy, activity) — **never raw audio or raw device data** ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)).

### Noise & realism rules

- Missing days (bad connectivity per ADR-0005), weekend/holiday gaps on an Indian calendar, occasional duplicate CSV rows (exercises F01's rejection path, TC-102), timezone jitter around IST.
- **Distributions are specified and validated by neel; the research inputs (ML-005/006) are gathered by ayush.** Any constant, distribution or correlation in this doc must appear in the harness config — no magic numbers in code that aren't in the spec.
- A low background rate of naturally-occurring Amber trajectories so dashboards look organic, not staged.

## The scripted persona (deterministic seed, exact 90-day arc)

Persona `DEMO-PERSONA-01`: Constable, 34, 3rd Bn. Script-driven, not sampled — flag days are part of the contract the rules engine must hit ([ADR-0001 validation](../architecture/decisions/0001-rules-engine-v1-not-ml.md)).

| Day | Event | Expected system behaviour |
|---|---|---|
| 1–30 | Normal roster; one leave taken and returned | Green; baselines established |
| 31 | Leave application **cancelled** (#1) | silent HR signal |
| 40–50 | Rotation to night-heavy duty | circadian score rises |
| 55 | Leave cancelled **(#2)** | silent HR signal |
| 58–60 | 60 consecutive duty days; sleep proxy −30% vs baseline | baseline breach accumulates |
| 62 | **Amber flag** → buddy nudge + JCO informal check | first visible intervention (F05) |
| 64 | Voluntary check-in says "I'm fine" despite signals | **masking flag** (FR-07) |
| 65 | **Red flag** with explanation factors | counsellor outreach task, ≤ 24 h SLA |
| 66 | Dual-key unmask (counsellor + welfare officer) — logged | subject sees it in who-viewed-my-data |
| 68–70 | Roster swap proposed & approved; duty load drops | intervention recorded (F06) |
| 75–85 | Trend down; check-ins stabilize | risk trend decreases |
| 85–90 | Green | **loop closed** — arc printed in the run summary |

## CLI surface (sketch — Python per [ADR-0006](../architecture/decisions/0006-tech-stack.md))

```bash
python -m data.gen --seed 42 --personnel 1000            # full population, 90 days, writes to DB
python -m data.gen --seed 42 --personnel 1000 --format csv   # export CSVs for the ingestion path (TC-101)
python -m data.gen --seed 42 --persona-only              # fast path: just DEMO-PERSONA-01 (demo re-seed)
python -m data.gen --seed 42 --personnel 1000 --dry-run  # row counts + persona arc preview, no writes
```

Exit non-zero with a readable report on any validation failure (FK violations, k < 5 unit, persona-arc mismatch).

## Data schema (tables it seeds)

| Table | Contents |
|---|---|
| `personnel` | pseudonym id, rank, age band, battalion/unit FKs (never names in welfare tables) |
| `hr_events` | leave / duty / deployment / transfer / training events, typed + dated |
| `roster_slots` | shift assignments per day, night flag, unit |
| `checkins` | daily 10-s check-ins (consent-gated rows only) |
| `instrument_results` | PHQ-9/GAD-7/PSS-10/ISI scores + validity items |
| `passive_features` | derived vectors (sleep proxy, activity) |
| `consent_events` | grant/withdraw artefacts incl. the silent-withdrawal fixture for TC-407 |
| `unit_incidents` | group-exposure events for FR-08 / TC-103 |

## Determinism & reseeding

- Fixed seed → byte-identical output across runs and machines (TC-501). Dates are computed from a seed-anchored epoch, **not wall-clock time**.
- Per-personnel RNG streams derived from the master seed, so adding a parameter does not silently reshuffle everyone.
- The persona arc is scripted independently of the population seed but equally deterministic — `--seed 42` always yields the same arc.
- Re-seeding is idempotent upsert on deterministic IDs; `--persona-only` exists so a demo can be re-seeded in minutes before walking on stage ([runbook](../quality/demo-runbook.md)).

## Edge cases

- Units with < 5 members are never emitted (generator-level k-anonymity guard).
- Leave spanning the arc boundary; consecutive-duty accounting across training days; cancelled-leave must not reset the duty streak (that's the point of the persona).
- Duplicate/malformed CSV rows must survive the export path (F01 rejection is tested, not bypassed).
- Non-participating personnel (no check-ins at all) must render sanely on every dashboard.
- Month-end/leap-day handling for the 90-day window; no DST (IST is fixed-offset).

## Definition of done

- [ ] All commands in the CLI sketch work; `--dry-run` prints the persona arc table.
- [ ] TC-501…TC-505 green ([test-plan.md](../quality/test-plan.md) §3, §4); distributions signed off by neel (spec ↔ harness config cross-check).
- [ ] Demo seed reproduces the full runbook walkthrough on a clean database ([demo-runbook.md](../quality/demo-runbook.md)).
- [ ] No welfare table contains real-looking identity data linked to scores outside the unmask path; k ≥ 5 guard proven by a negative test.
- [ ] README gets the one-command seed snippet (jury "setup in 5 minutes" checklist, research §8).

## Links

[FR-20](../product/prd.md) · [architecture.md](../architecture/architecture.md) (container `gen`) · [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [ADR-0006](../architecture/decisions/0006-tech-stack.md) · [test-plan.md](../quality/test-plan.md) · [demo-runbook.md](../quality/demo-runbook.md)
