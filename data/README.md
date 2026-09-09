# `data/` — SAARTHI synthetic data generator (F09 · QA-001 / QA-002)

> Owner: neel · Spec: [`docs/features/F09-synthetic-data-generator.md`](../docs/features/F09-synthetic-data-generator.md) · Tests: [`docs/quality/test-plan.md`](../docs/quality/test-plan.md) TC-501…TC-504, TC-701

**"Where is your data?"** is the first question every jury and every CRPF stakeholder asks.
This package answers it: one deterministic command produces ~1,000 personnel × 90 days of
realistic HR, self-report and passive-signal data — including the scripted
`DEMO-PERSONA-01` arc the demo walks through — so tests, the ML-002 validation harness and
the live demo all run on **one** fixture with **no** drift between them.

Standard library only. No numpy, no pandas, no faker. Python 3.9-compatible.

---

## 1. Run it

```bash
cd /path/to/sih-hackathon-26

# full population, 90 days, upsert into the backend database
backend/.venv/bin/python -m data.gen --seed 42 --personnel 1000

# export CSVs for the F01 ingestion path (TC-101/TC-102)
backend/.venv/bin/python -m data.gen --seed 42 --personnel 1000 --format csv --out-dir /tmp/saarthi-csv

# fast path: just DEMO-PERSONA-01 (re-seed the demo in seconds, before walking on stage)
backend/.venv/bin/python -m data.gen --seed 42 --persona-only

# print the persona arc table + row counts + validation, write nothing
backend/.venv/bin/python -m data.gen --seed 42 --personnel 1000 --dry-run
```

`python -m data` is an alias for `python -m data.gen`.

| Flag | Default | What it does |
|---|---|---|
| `--seed` | `42` | master seed. Same seed ⇒ byte-identical output. |
| `--personnel` | `1000` | population size. Units are re-allocated so k ≥ 5 always holds. |
| `--persona-only` | off | generate `DEMO-PERSONA-01` only. |
| `--format` | `db` | `db` upserts into SQLAlchemy models; `csv` writes files. |
| `--out-dir` | `out/saarthi-csv` | CSV destination. |
| `--db-url` | backend sqlite (`backend/saarthi.db`), or `$SAARTHI_DATABASE_URL` | SQLAlchemy URL. |
| `--participation` | `0.35` | voluntary check-in participation rate (F09 makes this a parameter; the PRD target is ≥ 30%). |
| `--dry-run` | off | validate and print; write nothing. |
| `--quiet` | off | suppress the run summary. Errors still go to stderr. |

**Exit codes:** `0` success · `1` a validation check failed (nothing is written; the full
report goes to stderr) · `2` bad arguments.

After a `--format db` run, the backend still owns signals and scoring:

```bash
cd backend && .venv/bin/python -m app.seed    # demo users + recompute + score
```

---

## 2. What it produces

| Payload table | Backend model (`backend/app/models.py`) | Natural key (idempotent upsert) |
|---|---|---|
| `personnel` | `IdentityMap` | `personnel_id` |
| `leave` | `HrLeaveRecord` | `pseudonym_id, applied_at, leave_type` |
| `roster` | `HrDutyRoster` | `pseudonym_id, duty_date` |
| `deployment` | `HrDeployment` | `pseudonym_id, start_date, posting_type` |
| `transfer` | `HrTransfer` | `pseudonym_id, effective_date, from_unit, to_unit` |
| `incident` | `HrIncident` | `incident_id` |
| `medical` | `HrMedical` | `pseudonym_id, visit_date, visit_type` |
| `career` | `HrCareerState` | `pseudonym_id` |
| `consent` | `ConsentArtefact` | `principal_pseudonym, bundle_id` |
| `checkin` | `CheckIn` | `pseudonym_id, recorded_at` |
| `instrument` | `InstrumentResult` | `pseudonym_id, instrument, recorded_at` |
| `passive` | `PassiveFeature` | `pseudonym_id, recorded_at` |
| `units` | *(none)* | population model only; k-checked, exported to `units.csv` |
| `training` | *(none)* | emitted as `rest_day=true` roster rows, which is what resets a duty streak |
| `csv_noise` | *(none)* | deliberate duplicate/malformed rows, CSV export only |

Reference run (`--seed 42 --personnel 1000`): 1,000 personnel · 85 units · 89,240 roster rows ·
84,568 passive rows · 23,887 check-ins · 2,500 instrument results · 1,632 leave records ·
640 CSV noise rows — 208,664 rows total, generated in ≈ 3 s.
Payload checksum `3979de35dae50efe4a64228d97e6c0d324a0273ad414899297cee3de1182c143`.

### CSV output

`--format csv` writes 14 CSVs plus a `manifest.json` (per-file SHA-256, row counts,
payload checksum).

* **Ingest contract** — `leave.csv`, `roster.csv`, `deployment.csv`, `transfer.csv`,
  `incident.csv`, `medical.csv`, `career.csv` carry **exactly** the columns
  `backend/app/ingest/schemas.py` declares, in declaration order. A test asserts this
  against the live pydantic models, so a backend schema change breaks the generator's
  tests rather than the demo.
* **Reference only** — `personnel.csv`, `units.csv`, `training.csv`, `consent.csv`,
  `checkin.csv`, `instrument.csv`, `passive.csv`. Not an ingest contract.
  `personnel.csv` is the **identity vault** export (it carries `legal_name`), the same
  data `IdentityMap` holds; every welfare-side CSV carries pseudonyms only.

Verified round trip on a 120-person run (fresh database, identities loaded, then each CSV
posted through `app.ingest.pipeline`):

```
leave       in=190     written=189     quarantined=1
roster      in=10777   written=10703   quarantined=74
deployment  in=152     written=151     quarantined=1
transfer    in=81      written=81      quarantined=0
incident    in=3       written=3       quarantined=0
medical     in=115     written=115     quarantined=0
career      in=120     written=120     quarantined=0
quarantine reasons:  33 duplicate natural key · 29 RosterIn validation error
                     13 unknown personnel_id · 1 LeaveIn validation error
```

That non-zero quarantine count is the point: **F01's rejection path is exercised, not
bypassed** (TC-102). Noise never reaches the database writer — it lives in the payload as
`csv_noise` and is injected only at CSV write time.

---

## 3. Determinism (TC-501)

Four rules, each tested:

1. **Stable hashing.** Per-stream RNGs come from `blake2b(seed|stream|pseudonym)`
   (`data/__init__.py::stable_seed`). Python's built-in `hash()` is salted per process and
   is never used.
2. **Namespaced streams.** Each purpose gets its own stream (`"roster"`, `"leave"`,
   `"sleep"`, `"checkin"`, …), keyed on the pseudonym. Adding a parameter to one stream
   cannot reshuffle another — `test_new_parameter_does_not_reshuffle_other_streams` proves
   changing `--participation` leaves every HR row byte-identical.
3. **Seed-anchored epoch.** Day 1 is the constant `spec.ARC_START = 2026-06-04`
   (= `backend/app/seed.py::ARC_START`); day 90 = `2026-09-01` = the backend's
   `demo_as_of`. Nothing in `data/` calls `datetime.now()` or `date.today()` — enforced by
   an AST walk over the package sources, not a grep.
4. **Deterministic row ids.** `did()` produces `prefix_<12 hex>` ids shaped like the
   backend's `nid()` but reproducible. Rows that already exist keep the id that created
   them; matching is by natural key.

IST is a fixed `+05:30` offset. There is no DST anywhere in this generator.

---

## 4. k ≥ 5 by construction (TC-504 · ADR-0003)

Structure is **battalion → company → platoon**. The allocator
(`population.split_headcount`) reduces the *number* of sub-units rather than creating an
undersized one, so there is no draw that can produce a 4-person platoon at any headcount.
`validate.check_k_anonymity` then re-checks every level of the emitted payload, and
`test_kanonymity.py` includes the negative case: a forced 4-person unit is refused and the
CLI exits `1`.

`unit_id` written to the database and the ingest CSVs is the **battalion**, because the
commander aggregate surface groups on `IdentityMap.unit_id`
(`backend/app/api/routers/commander.py`). Company and platoon live in the population model
and in `units.csv`, and are k-checked there.

`--persona-only` **skips** the k check and says so in the report: a persona re-seed does
not materialise unit membership, so there is nothing to count.

---

## 5. Agreement with `backend/app/seed.py`

`DEMO-PERSONA-01` is scripted, never sampled — it is byte-identical for every seed.

* Ids (`CR-DEMO-01` / `ps_demo01`), unit (`3BN`), rank (Constable), age (34), the three
  leave records, the deployment, both transfers and the `INC-3BN-01` incident are
  reproduced **verbatim** from kv's seed, on the same natural keys.
* **Days 1–67** of the duty / sleep / check-in series are identical row for row
  (`test_days_1_to_67_reproduce_the_backend_seed_shapes`).
* **Days 68–90** add the half of the F09 arc kv's seed does not model: the approved roster
  swap gives rest days 68–70 and weekly rest thereafter, sleep trends from 4.9 h back to
  7.0 h across days 75–85, and days 85–90 sit at baseline.

Running the generator and `python -m app.seed` in **either order**, any number of times,
converges on one row per natural key — verified. kv's ML-002 harness
(`app.ml.harness.persona_arc`, which asserts days 30 / 62 / 64 / 65) passes unchanged on
generator-produced data:

```
kv harness ok: True   diffs: []
  day 30  score= 24 tier=green
  day 62  score= 67 tier=red      (>= amber required)
  day 64  score= 68 tier=red      masking=True
  day 65  score= 67 tier=red
```

The population uses its own id namespace (`CR-GEN-#####` / `ps_gen#####`, incidents
`INC-GEN-<unit>-##`) so it can never collide with kv's hand-written `CR-3BN-xx` /
`CR-TINY-x` fixtures — in particular the deliberate 4-person `TINY` unit that the
k-anonymity suppression test needs stays exactly as kv wrote it.

### Documented deviations

| Deviation | Why |
|---|---|
| F09's arc says days 1–30 include "one leave taken and returned"; the generator places that completed home leave immediately **before** day 1. | A leave inside days 1–30 would break the same table's day-58–60 "60 consecutive duty days" clause. `backend/app/seed.py` makes the same choice. |
| Consent `granted_at` is `ARC_START − 1 day, 09:00` rather than `datetime.now()`. | Wall-clock values break TC-501. |
| `promotion_board_pending_months` and `inquiry_age_days` are `0`, never `NULL`. | `CareerIn` in `backend/app/ingest/schemas.py` has no empty-string coercion for optional numerics, so an empty CSV cell is a schema rejection. Emitting `0` keeps the DB payload and the CSV identical. Neither field is read by any rule in `v1.yaml`. |
| The identity vault export carries synthetic Indian names. | `IdentityMap.legal_name` is `nullable=False`; these are generated identities and never appear in a welfare table. |

### Known backend gaps found while building this (kv owns those files)

* **FIXED by kv — kept here as the regression it guards.**
  `backend/app/risk/scorer.py::_downgrade_confirmations` used to compare each historical
  row against `previous`, which *is* the most recent row, so the loop broke immediately
  and always returned `0`. With `hysteresis.downgrade_confirmations: 2` in `v1.yaml`,
  `apply_hysteresis` therefore never allowed a downgrade: the persona's **score** fell
  67 → 45 → 30 across days 66–90 (30 is inside the Green band 0–39) while the **tier**
  stayed `red`, so the F09 arc's "85–90 Green" was present in the data and blocked in the
  engine. `RiskScore.candidate_tier` now records the pre-hysteresis tier and the counter
  reads that instead of its own held output. Re-verified on generator output (persona-only
  seed into a fresh DB, scored on all 90 days): green 24 → amber 45 (day 55) → red 67
  (day 62) → amber 45 (day 68) → **green 30 (day 76, held through day 90)**.
* Ingesting a leave CSV with an empty `denial_reason` stores `""` rather than `NULL`
  (`str | None` accepts the empty string). Harmless — `leave_denial_count` treats `""` as
  falsy — but it is a DB/CSV divergence.

---

## 6. Tolerance table (TC-503)

Source of truth: `data/spec.py::TOLERANCES`. `--dry-run` prints the measured value beside
each target.

* **declared** — the target is a spec constant, so the check proves the generator obeys its
  own configuration.
* **emergent** — the target is the value measured on the reference run
  (`--seed 42 --personnel 1000`); the check is a regression guard, not a claim about the
  world.

| Metric | Target | ± | Kind | Reference run |
|---|---|---|---|---|
| `share.rank.Constable` | 0.62 | 0.06 | declared | 0.6310 |
| `share.rank.Head Constable` | 0.20 | 0.05 | declared | 0.1940 |
| `share.rank.ASI` | 0.08 | 0.04 | declared | 0.0850 |
| `share.rank.SI` | 0.07 | 0.04 | declared | 0.0570 |
| `share.rank.Inspector` | 0.03 | 0.03 | declared | 0.0330 |
| `share.participants` | 0.35 | 0.06 | declared | 0.3510 |
| `share.cohort.amber` | 0.06 | 0.035 | declared | 0.0600 |
| `share.posting.high_risk` | 0.22 | 0.06 | declared | 0.2040 |
| `share.passive_days` | 0.94 | 0.05 | declared | 0.9396 |
| `rate.csv_duplicate` | 0.004 | 0.004 | declared | 0.0038 |
| `rate.csv_malformed` | 0.003 | 0.004 | declared | 0.0030 |
| `mean.age` | 33.0 | 2.5 | emergent | 33.3720 |
| `mean.roster_rows_per_person` | 89.2 | 1.5 | emergent | 89.2400 |
| `mean.night_shift_ratio` | 0.21 | 0.06 | emergent | 0.2073 |
| `share.checkin_days_of_participants` | 0.75 | 0.08 | emergent | 0.7562 |

**Small populations.** Every share's standard error falls as `1/√n`, so a 60-person run is
legitimately noisier than the 1,000-person reference. `spec.scaled_tolerance` widens each
tolerance by `√(1000 / n)` below `n = 1000` and never tightens it above. Verified clean for
seeds 1 / 7 / 42 / 99 / 2026 at n = 60 / 120 / 400 / 1000.

### Provenance discipline (AGENTS.md rule 7)

**None of the numbers in `data/spec.py` is a measured statistic about CRPF or any real
force.** Each carries a confidence note in the source. They are shape assumptions chosen so
a demo dataset behaves plausibly against the F04 thresholds in
`backend/config/rulesets/v1.yaml`. Anything that needs to be *claimed* in the deck must come
from ayush's sourced research (ML-005 / ML-006), not from here. The three holiday dates used
to create realistic self-report gaps are marked the same way: `2026-08-15` is certain, the
two lunar-calendar entries are approximate and are used for gap shape only.

---

## 7. Privacy properties baked into the generator

* **Derived features only** (ADR-0002). `spec.FORBIDDEN_FIELD_SUBSTRINGS` bans `audio`,
  `waveform`, `pcm`, `raw_voice`, `recording`, `transcript` … from *every* emitted column
  name, and `spec.PASSIVE_ALLOWED_FIELDS` allow-lists what a passive row may carry.
  `validate.check_no_raw_signals` enforces both, so "we accidentally shipped raw audio" is
  a test failure rather than a code review.
* **Consent-gated self-report.** A non-participant gets no consent artefact, no check-in
  and no instrument result — but *does* get HR and passive series, so the dashboards stay
  alive (F09) while the backend's `has_voluntary_consent` gate keeps those rows out of a
  risk score.
* **Silent withdrawal fixture** (TC-407): ~4% of participants withdraw mid-arc. Their
  artefacts carry `withdrawn_at`, their earlier rows stay put, and their series simply
  stops — no gap marker, no absence signal.
* **Group exposure is unit-scoped** (FR-08 / TC-103). Incidents attach to a `unit_id`,
  never to a person.
* **No individual score is generated at all.** This package writes signals and raw inputs;
  scoring is the backend's job behind its own firewall (ADR-0003).

---

## 8. Tests

```bash
backend/.venv/bin/python -m pytest data/tests -q     # 77 tests, ~15 s
```

| File | Case | Proves |
|---|---|---|
| `test_determinism.py` | TC-501 | same seed ⇒ identical checksum, identical rows, byte-identical CSVs; parameter isolation; no wall clock |
| `test_persona.py` | TC-502 | the F09 arc table, transcribed independently, matches day for day; days 1–67 match `backend/app/seed.py`; every arc claim is backed by generated rows |
| `test_kanonymity.py` | TC-504 | no unit < 5 at any headcount; **negative test** — a forced 4-person unit is refused and the CLI exits 1 |
| `test_distributions.py` | TC-503 | FK integrity, unique natural keys, tolerances, CSV column contract vs the live pydantic models, privacy properties |

The suite runs from the repo root with `pythonpath=.`; `data/tests/conftest.py` also puts
`backend/` on the path so the persona and CSV-contract tests can assert against kv's real
modules (they `skip`, not fail, if the backend is not importable).

---

## 9. Module map

| File | Responsibility |
|---|---|
| `__init__.py` | determinism primitives (`stable_seed`, `rng_for`, `did`, `checksum`) and the `Dataset` payload container |
| `spec.py` | **every** distribution, constant, correlation and tolerance, named and annotated — F09's "no magic numbers in code that aren't in the spec" |
| `population.py` | battalion/company/platoon allocation (k ≥ 5 by construction) and per-person attributes |
| `events.py` | 90-day HR streams: roster, leave, deployment, transfer, training, medical, career, unit incidents |
| `passive.py` | derived sleep proxy + activity index (never raw signals) |
| `selfreport.py` | consent artefacts, daily check-ins, monthly PHQ-9/GAD-7/PSS-10/ISI with validity items |
| `persona.py` | the scripted `DEMO-PERSONA-01` arc and its evidence |
| `validate.py` | FK integrity, natural keys, k ≥ 5, persona arc, no-raw-signals, date window, distributions |
| `writer_db.py` | idempotent natural-key upsert into the backend models |
| `writer_csv.py` | ingest-contract CSVs + reference CSVs + deterministic noise + manifest |
| `gen.py` / `__main__.py` | the CLI |
