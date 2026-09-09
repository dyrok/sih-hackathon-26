# F09 — Synthetic Data Generator

> Owner: neel · Status: [x] implemented (QA-001 / QA-002 — see §Implementation status) · Last updated: 2026-09-09
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

- [x] All commands in the CLI sketch work; `--dry-run` prints the persona arc table.
- [ ] TC-501…TC-505 green ([test-plan.md](../quality/test-plan.md) §3, §4); distributions signed off by neel (spec ↔ harness config cross-check). — **TC-501/502/503/504 are green** in `data/tests` (77 tests); TC-505 is not defined anywhere in test-plan.md §3, so it cannot be claimed green (kv: define it or drop the reference).
- [x] Demo seed reproduces the full runbook walkthrough on a clean database ([demo-runbook.md](../quality/demo-runbook.md)). — all 7 beats reproduce. Beat 7 ("score trend drops") was blocked by a rules-engine defect when this section was first written; kv has since fixed it (see Implementation status §5). Re-measured on generator output: score 67 → 45 → 30, tier Red (day 62) → Amber (day 68) → **Green (day 76, held through day 90)**.
- [x] No welfare table contains real-looking identity data linked to scores outside the unmask path; k ≥ 5 guard proven by a negative test.
- [ ] README gets the one-command seed snippet (jury "setup in 5 minutes" checklist, research §8). — the repo-root `README.md` is not neel-owned this round; the snippet lives in [`data/README.md`](../../data/README.md) §1 and [demo-runbook.md](../quality/demo-runbook.md) §2 already cites the command.

## Links

[FR-20](../product/prd.md) · [architecture.md](../architecture/architecture.md) (container `gen`) · [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [ADR-0006](../architecture/decisions/0006-tech-stack.md) · [test-plan.md](../quality/test-plan.md) · [demo-runbook.md](../quality/demo-runbook.md)

## Implementation status (QA-001 / QA-002 · neel · 2026-09-09)

Shipped as the top-level Python package [`data/`](../../data/) — standard library only (no numpy / pandas / faker), Python 3.9-compatible. Full operator documentation lives in [`data/README.md`](../../data/README.md).

### 1. CLI (all four sketch commands work as written)

```bash
backend/.venv/bin/python -m data.gen --seed 42 --personnel 1000
backend/.venv/bin/python -m data.gen --seed 42 --personnel 1000 --format csv --out-dir /tmp/saarthi-csv
backend/.venv/bin/python -m data.gen --seed 42 --persona-only
backend/.venv/bin/python -m data.gen --seed 42 --personnel 1000 --dry-run
```

Added beyond the sketch: `--db-url` (default `backend/saarthi.db`, or `$SAARTHI_DATABASE_URL`), `--quiet`, and `--participation` (this doc already calls participation "a parameter"; default `0.35`). `python -m data` aliases `python -m data.gen`. Exit codes: `0` success · `1` validation failure (readable report on stderr, **nothing written**) · `2` bad arguments.

### 2. Reference run (`--seed 42 --personnel 1000`)

1,000 personnel · 85 units (5 battalions × 4 companies × 3 platoons) · 89,240 roster rows · 84,568 passive rows · 23,887 check-ins · 2,500 instrument results · 1,632 leave records · 640 CSV noise rows — **208,664 rows in ≈ 3 s**. Payload SHA-256 `3979de35dae50efe4a64228d97e6c0d324a0273ad414899297cee3de1182c143`. All seven validation checks pass.

### 3. Where the tolerance table lives

`data/spec.py::TOLERANCES` — 15 entries, each tagged `declared` (target is a spec constant, so the check proves the generator obeys its own config) or `emergent` (target is the reference-run measurement, so the check is a regression guard). `--dry-run` prints measured value beside target; the table is mirrored in [`data/README.md`](../../data/README.md) §6. `spec.scaled_tolerance` widens every tolerance by `√(1000/n)` below n = 1000, because a share's standard error falls as `1/√n` — verified clean for seeds 1/7/42/99/2026 at n = 60/120/400/1000.

**Provenance:** no number in `data/spec.py` is presented as a measured statistic about CRPF or any real force; each carries a confidence note in the source. They are shape assumptions tuned against the F04 thresholds in `backend/config/rulesets/v1.yaml`. Anything a deck *claims* must come from ayush's sourced research (ML-005/006), not from here (AGENTS.md rule 7).

### 4. Tests (`backend/.venv/bin/python -m pytest data/tests -q` → 77 passed, ~15 s)

| File | Case | Proves |
|---|---|---|
| `test_determinism.py` | TC-501 | same seed ⇒ identical checksum, identical rows, byte-identical CSVs; changing `--participation` leaves every HR row untouched (stream namespacing); an AST walk proves no `datetime.now()`/`date.today()` anywhere in `data/` |
| `test_persona.py` | TC-502 | the arc table above, transcribed independently into the test, matches day for day; days 1–67 match `backend/app/seed.py` row for row; every arc claim is backed by generated rows |
| `test_kanonymity.py` | TC-504 | no unit < 5 at any headcount, at all three levels; **negative test** — a forced 4-person unit is refused and the CLI exits `1` |
| `test_distributions.py` | TC-503 | FK integrity, unique natural keys, tolerances, CSV columns asserted against the live pydantic models in `backend/app/ingest/schemas.py`, privacy properties |

TC-102's rejection path is exercised, not bypassed: on a 120-person CSV export ingested into a fresh DB, `roster` quarantined 74 of 10,777 rows, `leave` 1 of 190, `deployment` 1 of 152 — reasons `duplicate natural key` (33), `RosterIn validation error` (29), `unknown personnel_id` (13), `LeaveIn validation error` (1). Noise never reaches the DB writer.

### 5. Agreement with `backend/app/seed.py` (kv)

`DEMO-PERSONA-01` is scripted, not sampled — byte-identical for every seed. Ids (`CR-DEMO-01`/`ps_demo01`), unit `3BN`, rank, age, the three leave records, the deployment, both transfers and the `INC-3BN-01` incident are reproduced verbatim on the same natural keys; **days 1–67** of the duty/sleep/check-in series are identical row for row. Days 68–90 add the recovery half of the arc above, which `seed.py` does not model. Running the generator and `python -m app.seed` in **either order**, any number of times, converges on one row per natural key (verified). kv's ML-002 harness passes unchanged on generator-produced data: `ok: True, diffs: []` — day 30 green (24), day 62 red (67), day 64 red + masking (68), day 65 red (67).

The generated population uses its own id namespace (`CR-GEN-#####` / `ps_gen#####`, incidents `INC-GEN-<unit>-##`) so it can never collide with kv's `CR-3BN-xx` / `CR-TINY-x` fixtures — in particular the deliberate 4-person `TINY` unit the k-anonymity suppression test needs.

**Behaviour decided here that this doc did not specify (AGENTS.md rule 1):**

1. **Unit hierarchy vs `unit_id`.** Structure is battalion → company → platoon, but the `unit_id` written to the DB and the ingest CSVs is the **battalion**, because the commander aggregate surface groups on `IdentityMap.unit_id` (`backend/app/api/routers/commander.py`). Company/platoon live in the population model and `units.csv`, and are k-checked there. k ≥ 5 is enforced at all three levels.
2. **"Day 1–30: one leave taken and returned"** is modelled as a completed home leave immediately *before* day 1. A leave inside days 1–30 would break the same table's day-58–60 "60 consecutive duty days" clause. `seed.py` makes the same choice.
3. **`--persona-only` skips the k-anonymity check** and says so in the report: a persona re-seed does not materialise unit membership, so there is nothing to count.
4. **Consent `granted_at`** is `ARC_START − 1 day, 09:00` rather than wall-clock `now()` (which would break TC-501).
5. **`promotion_board_pending_months` / `inquiry_age_days` are `0`, never `NULL`** — `CareerIn` in `backend/app/ingest/schemas.py` has no empty-string coercion for optional numerics, so an empty CSV cell is a schema rejection. Emitting `0` keeps the DB payload and the CSV identical. Neither field is read by any rule in `v1.yaml`.
6. **Training courses** have no backend table; they are emitted as `rest_day=true` roster rows (which is what actually resets a duty streak) plus a reference `training.csv`.
7. **`activity_index`** is exported to `passive.csv` only — `PassiveFeature` has no column for it.

**Backend defects found while validating this (`backend/` is kv’s — neither was fixed from this task):**

- ~~`backend/app/risk/scorer.py::_downgrade_confirmations` compared each historical row against `previous`, which *is* the most recent row, so the loop broke on the first iteration and always returned `0`; combined with `hysteresis.downgrade_confirmations: 2` in `v1.yaml`, no risk tier could ever be downgraded and the arc’s "85–90 Green" was present in the data but blocked in the engine.~~ **Fixed by kv** — `RiskScore.candidate_tier` now stores the pre-hysteresis tier and the counter reads that instead of its own held output. Re-verified against generator output (persona scored on all 90 days, fresh DB): 24 green → 45 amber (day 55) → 67 red (day 62) → 45 amber (day 68) → 30 green (day 76, held to day 90). The loop closes.
- Ingesting a leave CSV with an empty `denial_reason` stores `""` rather than `NULL` (`str | None` accepts the empty string). Harmless (`leave_denial_count` treats `""` as falsy) but it is a DB/CSV divergence.

### 6. Not done

- **TC-701** (1,000-personnel full risk recompute < 60 s) is not measured here — this task produced the fixture, not the recompute benchmark; the fixture it needs now exists.
- **Repo-root `README.md`** one-command snippet — not neel-owned this round.
