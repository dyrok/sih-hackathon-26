# Test Plan

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05

> Every FR/NFR in [prd.md](../product/prd.md) maps to a test-case ID below. The [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) firewall suite (§4) is a **must-pass gate**: a red case there blocks merge *and* demo.

## 1. Test strategy — what v1 must prove

1. **Signals are correct and deterministic** — F01 derives the 15+ features exactly; same input in, same features out.
2. **Explainability by construction** ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)) — no alert ships without its top contributing factors and raw values.
3. **The firewall cannot be bypassed** — tested at the architecture level (routes, DB permissions), not UI hiding; a hostile commander account must still fail.
4. **Offline-first actually works** ([ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md)) — queue, sync, resume, conflict, low-end Android.
5. **The demo loop closes** (FR-20) — the scripted persona reproduces its exact 90-day arc on demand ([F09](../features/F09-synthetic-data-generator.md)).
6. **The privacy lifecycle holds** — consent artefacts, silent withdrawal, 90-day raw-data expiry, immutable audit (NFR-01/03/08).
7. **Performance envelope** — 1,000-personnel recompute < 60 s on demo hardware (NFR-06).

Pyramid: unit (thresholds, feature math) → integration (route-level authz) → end-to-end (persona arc) → manual checklists (device, offline, demo). Layers 1–3 run in CI; layer 4 is the device lab; demo checks run at T-minus-30-min (see [demo-runbook.md](demo-runbook.md)).

ID scheme `TC-<nnn>` by layer: **1xx** signal · **2xx** inference · **3xx** intervention · **4xx** trust/privacy · **5xx** demo infra · **6xx** offline/device · **7xx** performance · **8xx** model validation.

## 2. Traceability matrix

| FR | Requirement (short) | Test cases |
|---|---|---|
| FR-01 | HR ingest CSV+API, 15+ signal features | TC-101…TC-103 |
| FR-02 | 10-s check-in + monthly instruments, hi/en | TC-201, TC-601 |
| FR-03 | On-device prosody; feature vector only | TC-202 |
| FR-04 | Offline-first queue + sync | TC-601…TC-605 |
| FR-05 | Rules engine 0–100, per-person baselines | TC-203, TC-204 |
| FR-06 | Explanation per flag | TC-205 |
| FR-07 | Masking / discrepancy flag | TC-206 |
| FR-08 | Group trauma exposure (unit-level) | TC-103 |
| FR-09 | Response ladder Green→Amber→Red→Critical | TC-301 |
| FR-10 | Capacity-aware triage + weekly caps | TC-302 |
| FR-11 | Roster-swap rebalancing | TC-303 |
| FR-12 | Counsellor console notes/outcomes | TC-304 |
| FR-13 | Tele-MANAS 14416 handoff recorded | TC-305 |
| FR-14 | Two-tier output, k ≥ 5 | TC-401…TC-403 |
| FR-15 | Who-viewed-my-data | TC-404 |
| FR-16 | Pseudonyms + dual-key unmask, logged | TC-405 |
| FR-17 | Silent consent withdrawal | TC-407 |
| FR-18 | 90-day raw-data expiry | TC-408 |
| FR-19 | Anonymous unit pulse (aggregate only) | TC-402 |
| FR-20 | Synthetic data generator | TC-501…TC-505 |

| NFR | Requirement (short) | Test cases |
|---|---|---|
| NFR-01 | DPDP 2023: consent artefacts, retention, 72h breach readiness | TC-407, TC-408, TC-409 |
| NFR-02 | MHA 2017 §23 confidentiality | TC-401, TC-405 |
| NFR-03 | Server-side RBAC, TLS, AES-256, append-only audit | TC-401, TC-409 |
| NFR-04 | Low-end Android (API 26+), icon-first, hi/en | TC-606, TC-607 |
| NFR-05 | Explainability (top factors, no black box) | TC-205, TC-803 |
| NFR-06 | 1,000-personnel recompute < 60 s | TC-701, TC-702 |
| NFR-07 | False-alarm economics, alert caps | TC-207, TC-302 |
| NFR-08 | Immutable audit + break-glass notifies subject | TC-409 |

## 3. Per-feature test cases (given/when/then)

- **F01 HR signal engine** (FR-01, FR-08)
  - **TC-101** Given a 90-day roster/leave CSV for one personnel, when ingestion runs, then days-since-leave, consecutive-duty, circadian-disruption and family-separation match hand-computed values exactly.
  - **TC-102** Given duplicate/malformed rows, when import runs, then rows are rejected with a row-level report and nothing partial is written.
  - **TC-103** Given a unit-tagged casualty/incident, when signals recompute, then the exposure flag attaches to the group record — never to named individuals.
- **F02 Jawan app** (FR-02, FR-15) — **TC-201** Given the app in Hindi, when a 10-s check-in completes, then the entry renders from `checkin.*` i18n keys and is visible in "my data". **TC-404** Given a counsellor opened a record, when the jawan opens who-viewed-my-data, then role, timestamp and reason are shown.
- **F03 On-device signals** (FR-03) — **TC-202** Given a voice check-in, when recording finishes, then a network-monitor assertion proves zero audio bytes leave the device; only the feature vector queues.
- **F04 Risk rules engine** (FR-05…FR-07, NFR-07)
  - **TC-203** Given per-person baseline breached (e.g. 60 consecutive duty days), when scoring runs, then risk crosses Amber at the specified threshold and identical inputs yield identical scores.
  - **TC-204** Given triangulated HR + self-report + passive inputs, when scoring runs, then the composite 0–100 score equals the documented weighted formula (reference values in the unit fixture).
  - **TC-205** Given any flag ≥ Amber, when the alert renders, then top contributing factors with values are present ("47 consecutive duty days, sleep −30%" shape).
  - **TC-206** Given "I'm fine" + 4 h sleep + 60 duty days + 2 cancelled leaves, when discrepancy rules run, then the masking flag fires ("the faking is the finding").
  - **TC-207** Given alert volume above the counsellor weekly cap, when triage applies caps, then suppression is logged with reason — nothing silently vanishes (NFR-07).
- **F05 Intervention engine** (FR-09…FR-11) — **TC-301** Given the demo persona at Amber, when thresholds promote it, then buddy nudge + JCO informal check fire; at Red, a counsellor-outreach task is created with the ≤ 24 h SLA. **TC-302** Given N urgent cases, when ranked by urgency × intervenability, then order and caps match spec. **TC-303** Given a Red case, when swaps are proposed, then max individual load strictly decreases and the swap remains a proposal until the welfare officer approves.
- **F06 Counsellor console** (FR-12) — **TC-304** Given a saved session note and outcome, when the case is opened, then the before/after risk trend renders.
- **F07 Commander dashboard** (FR-14) — covered by the firewall suite (§4).
- **F08 Privacy & safety architecture** (FR-14…FR-18) — covered by the firewall suite (§4).
- **F09 Synthetic data generator** (FR-20)
  - **TC-501** Given `--seed 42 --personnel 1000`, when generation runs twice, then outputs are byte-identical (checksum match).
  - **TC-502** Given defaults, when seeding completes, then the persona "Constable, 34, 3rd Bn" exists with the exact scripted 90-day arc from [F09](../features/F09-synthetic-data-generator.md).
  - **TC-503** Given a fresh database, when seeding runs, then all FK constraints pass and aggregate distributions fall within neel's specified tolerances.
  - **TC-504** Given the commander dashboard on seeded data, when aggregates render, then no visible cell has < 5 contributors.

## 4. ADR-0003 firewall test suite — MUST-PASS GATE

Run on every PR merge and before every demo. Any failure blocks release — escalate to kv per AGENTS.md rule 8.

- **TC-401** **Route-level rejection** — Given a commander-role JWT, when `GET /welfare/personnel/{id}` is called, then the request is rejected at the route level (403/404). Assert on the role-filtered OpenAPI route list, not on UI hiding.
- **TC-402** **k-anonymity ≥ 5** — Given every commander-visible aggregate, when rendered, then it asserts ≥ 5 distinct contributors; a crafted 4-person unit produces a suppressed cell.
- **TC-403** **No covert path** — Given a commander token, when every API route is enumerated and scraped, then zero responses contain a pseudonym↔identity link or an individual score.
- **TC-405** **Dual-key unmask** — Given a single approval, when unmask is attempted, then it is rejected; given counsellor **and** welfare-officer approval, then the unlock succeeds, is written to the append-only audit log, and appears in the subject's who-viewed-my-data.
- **TC-407** **Silent consent withdrawal** — Given the jawan withdraws consent, when command-facing views refresh, then nothing changes visually (no de-selection, no gap, no absence signal); the withdrawal is visible only to the jawan.
- **TC-408** **90-day expiry job** — Given raw self-reports older than 90 days, when the expiry job runs, then raws are purged, derived risk trends persist, and a re-run is idempotent.
- **TC-409** **Audit immutability + break-glass** — Given a DB-level UPDATE/DELETE on the audit log, then it is rejected by trigger/permission; given break-glass access, then it succeeds **and notifies the subject** immediately, flagged in audit (NFR-08).

## 5. Offline sync test cases (ADR-0005)

- **TC-601** Given airplane mode, when a check-in is submitted, then it queues in local SQLite; on reconnect it syncs exactly once (no duplicate).
- **TC-602** Given 72 queued entries, when sync runs, then batch upload completes and partial failure resumes from the last checkpoint.
- **TC-603** Given the same check-in retried, when sync runs, then the idempotency key collapses it to one server record.
- **TC-604** Given a conflicting local/server edit of a monthly instrument, when sync resolves, then per-field last-write-wins with a conflict flag — never silent data loss.
- **TC-605** Given the app killed mid-sync, on relaunch the queue resumes without corruption.
- **TC-606** Given an Android API 26 emulator with a 1 GB RAM profile, when the check-in flow runs, then it completes on the icon-first UI.
- **TC-607** Given language toggle en↔hi, when every screen renders, then all strings resolve from i18n keys (lint-enforced; no hardcoded literals).

## 6. Performance checks (NFR-06)

- **TC-701** Seed 1,000 personnel × 90 days ([F09](../features/F09-synthetic-data-generator.md)); full risk recompute < 60 s. Record actual seconds + machine spec in the run log before the demo.
- **TC-702** Cold-start commander aggregate query < 2 s p95 on seeded data.
- Guard: CI re-runs TC-701 weekly; a > 20% regression fails the build.

## 7. Coverage reporting

- `pytest --cov` gates: rules engine + firewall routes ≥ 90% line coverage; backend overall ≥ 80%; sync-queue logic ≥ 80%.
- Any uncovered line under `firewall/`/authz paths requires a PR comment naming ADR-0003 explicitly.
- Coverage summary posted in the repo README badge and logged per sprint in this file's run log.

## 8. Model validation harness plug-in (ML-002, kv)

- the ML-002 validation harness (kv) consumes the **same F09 fixture (seed 42)** the tests use — one dataset, one truth, no drift between tests and model evaluation.
- **TC-801** Threshold sweep vs FP/FN economics (NFR-07): harness reports per-threshold flags so tuning is documented, not vibes.
- **TC-802** Persona-arc reproduction: harness re-runs the scripted 90-day arc and diffs actual vs scripted flag days (must be zero diff — mirrors ADR-0001's validation clause).
- **TC-803** v2-readiness probe: counts counsellor-outcome labels accumulated (ADR-0001 human-in-the-loop) and reports when ML v2 training becomes defensible; until then v1 rules stay the product.
- Harness output lands in this repo's run log; failures open a `[ML-002]` task on the board, not a silent skip.
