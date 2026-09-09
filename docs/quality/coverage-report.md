# Coverage report — QA-003

> Owner: neel · Status: [x] complete for this run · Last updated: 2026-09-09
> Run log for [test-plan.md](test-plan.md). Security cases live in
> [security-test-cases.md](security-test-cases.md); their threat analysis in [threat-model.md](threat-model.md).

## 1. What was run, and on what

| | |
|---|---|
| Machine | Apple M4 · 16 GB · macOS 26.6.2 (arm64) |
| Python | 3.9.6 (`backend/.venv`) |
| Bun | 1.4.0 |
| Fixture | `data.gen --seed 42 --personnel 1000` (90 days), plus `app.seed` for the scripted persona |
| Command | `make test` · `make coverage` · `make perf` |

One command reproduces the whole thing: `make check` runs the boundary lint, the
typecheck, all three suites and the production build.

## 2. Results

| Suite | Command | Tests | Result |
|---|---|---|---|
| Backend API + engines | `make test-backend` | 132 | pass |
| Synthetic data generator | `make test-data` | 77 | pass |
| Web (offline queue, instruments, wire format) | `make test-web` | 48 | pass |
| **Total** | `make test` | **257** | **pass** |

Backend suites, by file:

| File | Tests | What it holds |
|---|---|---|
| `test_rbac_enforcement.py` | 35 | PRIV-002 — every RBAC/ABAC matrix cell, route enumeration per role, token integrity |
| `test_security_hardening.py` | 30 | PRIV-003 — one regression test per closed security finding |
| `test_privacy_paths.py` | 17 | the refusal, retention and masking branches that only run on a bad day |
| `test_privacy.py` | 8 | k-anonymity, dual-key, break-glass, silent withdrawal, audit chain, expiry |
| `test_firewall.py` | 7 | ADR-0003 must-pass gate |
| `test_risk_pure.py` | 7 | scoring arithmetic, domain caps, hysteresis, masking |
| `test_signals.py` | 7 | signal derivation against hand-computed values |
| `test_persona_and_harness.py` | 6 | the scripted 90-day arc and the ML-002 harness |
| `test_hysteresis_release.py` | 5 | the recovery half of the ladder — the arc has to be able to close |
| `test_ingest.py` | 5 | CSV/JSON ingest, quarantine, group scoping |
| `test_interventions.py` | 4 | queue, triage caps, Tele-MANAS, rebalance visibility |
| `test_client_surface.py` | 1 | end-to-end sweep of every client-facing route in all four roles |

## 3. Coverage against the §7 gates

Backend overall: **90%** (3,567 statements, 351 uncovered).

| Gate | Target | Measured | |
|---|---|---|---|
| Backend overall | ≥ 80% | **90%** | pass |
| Firewall routes (`firewall.py`) | ≥ 90% | **96%** | pass |
| Firewall routes (`privacy/kanonymity.py`) | ≥ 90% | **100%** | pass |
| Caseload scoping (`authz.py`) | ≥ 90% | **98%** | pass |
| Rules engine (`risk/evaluator.py`) | ≥ 90% | **100%** | pass |
| Rules engine (`risk/masking.py`) | ≥ 90% | **100%** | pass |
| Rules engine (`risk/ruleset.py`) | ≥ 90% | **100%** | pass |
| Rules engine (`risk/scorer.py`) | ≥ 90% | **93%** | pass |
| Rules engine (`risk/aggregator.py`) | ≥ 90% | **93%** | pass |
| Retention (`privacy/expiry.py`) | ≥ 90% | **100%** | pass |
| Sync-queue logic (`web/packages/sync`) | ≥ 80% | every exported function exercised by `sync.test.ts` | pass |

Modules materially below the overall figure, and why — recorded rather than
rounded away:

| Module | Cov | What is uncovered |
|---|---|---|
| `api/routers/self_service.py` | 73% | the per-table branches of `POST /app/sync` that the demo path does not take (passive, several rejection reasons) |
| `ingest/pipeline.py` | 74% | per-dataset row mappers for datasets the demo does not ingest |
| `signals/domain/health.py` | 67% | medical-visit signals; the demo persona has no medical events |
| `ml/harness.py` | 72% | report-formatting branches |

None of these sit on the firewall, the consent gate or the retention path.

## 4. Performance envelope (NFR-06)

`make perf` — `scripts/perf.py --gate`:

| Case | Gate | Measured | |
|---|---|---|---|
| TC-701 · 1,000-personnel signal + risk recompute | < 60 s | **12.93 s** (signals 9.43 s + risk 3.49 s) | pass |
| TC-702 · commander aggregate query, p95 | < 2 s | **93 ms** over 40 units | pass |
| Fixture generation + write (context) | — | 6.29 s | — |

Guard: CI fails the build if either gate is missed. The recorded numbers are the
baseline a >20% regression is measured against; re-record them here when the
machine changes, because 12.93 s means nothing without the machine beside it.

## 5. What is verified elsewhere

- The **ADR-0003 firewall suite** (test-plan §4) runs as its own CI job, before
  anything else, so a failure there is unmissable rather than buried.
- **Architectural boundaries** are a lint, not a test: `web/scripts/lint-boundaries.mjs`
  fails the build on a cross-role API import, an individual-shaped string in the
  commander app, a personal trend line in a console, a hardcoded colour, a
  user-facing literal, an unknown i18n key, or an en/hi key that lost its pair.
- **ML-002** replays the scripted persona arc (`make harness`) and must diff to
  zero against the F09 day table.

## 6. Not covered by this run

Honest gaps, so nobody reads a green suite as more than it is:

- **No device lab.** TC-606/TC-607 (API-26-class Android, 200% zoom, 320px
  reflow, screen-reader walkthrough) are manual and unrun. The protocol for them
  is in [usability-testing.md](usability-testing.md).
- **No browser-level E2E.** The three apps are covered by typecheck, production
  build, the boundary lint and unit tests over the offline queue, the instrument
  bank and the wire format — not by a driven browser. The check-in-to-counsellor
  loop is exercised end to end at the API layer (`test_client_surface.py`), and
  by hand from the [demo-runbook](demo-runbook.md).
- **No load test.** TC-701 measures a single-process recompute, not concurrency.
- **Encryption at rest, TLS termination and key management** are deployment
  concerns, unverified here — see security-model.md's verification status.
